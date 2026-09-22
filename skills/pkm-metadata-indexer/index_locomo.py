"""LoCoMo corpus adapter for the pkm indexer's pluggable `collect=` scanner.

This is an *enrichment-as-data* layer, not a fork of the indexer. It maps a
LoCoMo conversation into the same (notes, sections, links, errors) contract
`collect_index_data` returns, so the daemon indexes conversation turns exactly
as it indexes vault notes — one note per turn (keyed by its `dia_id`), one
section per turn carrying the turn text, and *synthetic wikilinks* from each
turn to the concepts it mentions.

Three of the vault's signals map onto a conversation:

  wikilinks  -> concept co-reference. Each turn links to the proper-noun
               concepts it mentions; two turns that cite the same rare concept
               share a wikilink neighbour, which is exactly what the
               Adamic-Adar term in `/similar?fusion=1` rewards.
  git time   -> turn timestamp. Each turn inherits its session's date/time;
               we inject that map by replacing `recency.build_creation_dates`
               (process-local, see MONKEYPATCH below) so `&recency=1`/`&fusion=1`
               can see conversation time without any git history.
  co-commit  -> session/speaker co-membership. Deferred: co_commit lives in a
               separate git-derived db keyed by vault name; a unique corpus
               name means zero co-commit rows, so that term degrades to 0.

Usage (isolated daemon, never the live one on 44771):

  searchd.py --port 44781 --db <ISOLATED> \
    --corpus /abs/index_locomo.py:scan_locomo=locomo=<ROOT>=<ISOLATED_DB>

where <ROOT> is a directory holding one JSON file per LoCoMo conversation
(the raw conversation dict from locomo10.json).
"""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

import index_pkm_meta as pkm
import recency_prior_experiment as recency

# ---------------------------------------------------------------------------
# Timestamp injection seam.
#
# searchd's Vault.creation_index() calls recency.build_creation_dates(root)
# once per process, lazily, and only if creation_dates is still None. We
# populate this module-global while scanning (which runs at index build, before
# any query) and hand the daemon a function that returns it. Keyed by the same
# relative_path used for the note records.
# ---------------------------------------------------------------------------
_CREATION_DATES: dict[str, str] = {}


def _inject_creation_dates(_root: Path) -> dict[str, str]:
    return dict(_CREATION_DATES)


# MONKEYPATCH: replace the git-derived builder with our conversation clock.
# Import-time, so it is in force the moment --corpus imports this module.
recency.build_creation_dates = _inject_creation_dates


# ---------------------------------------------------------------------------
# Concept extraction -> synthetic wikilinks.
# ---------------------------------------------------------------------------
# Capitalized single- or multi-word runs are our cheap proper-noun proxy. Words
# that only get a capital by starting a sentence are the noise this must reject,
# hence the stopword gate on the *first* token of a run.
_CONCEPT_RE = re.compile(r"\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\b")

_SENTENCE_STARTERS = {
    "i", "the", "a", "an", "and", "but", "so", "or", "if", "we", "you", "he",
    "she", "it", "they", "my", "your", "his", "her", "our", "their", "this",
    "that", "these", "those", "there", "here", "when", "where", "what", "who",
    "how", "why", "do", "did", "does", "is", "are", "was", "were", "have",
    "has", "had", "will", "would", "can", "could", "should", "yes", "no",
    "oh", "ok", "okay", "hi", "hey", "hello", "thanks", "thank", "well",
    "yeah", "sure", "maybe", "just", "now", "then", "also", "not", "im",
    "let", "get", "got", "good", "great", "nice", "really", "wow", "haha",
}


def _concept_key(phrase: str) -> str:
    """Stable identifier for a concept, so two turns citing it match."""
    return re.sub(r"\s+", "_", phrase.strip().lower())


def extract_concepts(text: str, max_concepts: int = 12) -> list[str]:
    concepts: list[str] = []
    seen: set[str] = set()
    for match in _CONCEPT_RE.finditer(text):
        phrase = match.group(1)
        first = phrase.split()[0].lower()
        # A lone capitalized word that is a common sentence-starter is noise;
        # a multi-word run ("New York") is kept even if it starts with one.
        if " " not in phrase and first in _SENTENCE_STARTERS:
            continue
        if len(phrase) < 3:
            continue
        key = _concept_key(phrase)
        if key in seen:
            continue
        seen.add(key)
        concepts.append(key)
        if len(concepts) >= max_concepts:
            break
    return concepts


# ---------------------------------------------------------------------------
# Timestamp parsing. LoCoMo session stamps look like "1:56 pm on 8 May, 2023".
# ---------------------------------------------------------------------------
_WHEN_FORMATS = (
    "%I:%M %p on %d %B, %Y",
    "%I:%M %p on %d %B %Y",
)


def parse_when(raw: str) -> str | None:
    raw = (raw or "").strip()
    for fmt in _WHEN_FORMATS:
        try:
            return datetime.strptime(raw, fmt).isoformat()
        except ValueError:
            continue
    return None


# ---------------------------------------------------------------------------
# The scanner.
# ---------------------------------------------------------------------------
_SESSION_RE = re.compile(r"^session_(\d+)$")


def _turn_path(sample_id: str, dia_id: str) -> str:
    # dia_id like "D1:3" -> a filesystem-safe virtual path. Never written to
    # disk; the grader reverses stem "D1-3" back to "D1:3".
    safe = dia_id.replace(":", "-")
    return f"{sample_id}/{safe}.md"


def _iter_conversations(vault_dir: Path):
    for path in sorted(vault_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        # A file may hold one conversation dict or a list of them.
        if isinstance(data, list):
            for item in data:
                yield path, item
        else:
            yield path, data


def scan_locomo(vault_dir: Path):
    vault_dir = Path(vault_dir)
    notes = []
    sections = []
    links = []
    errors = []
    _CREATION_DATES.clear()

    # Buffer (rel, sample_id, concepts) so we can apply a document-frequency
    # filter after the full scan. Concepts are namespaced per conversation
    # (see _emit_concept_links) so a shared concept never links two turns from
    # different conversations — that would be cross-conversation leakage, since
    # LoCoMo evidence is always scoped to a single conversation.
    turn_concepts: list[tuple[str, str, list[str]]] = []
    sample_turns: Counter[str] = Counter()

    for src, conv in _iter_conversations(vault_dir):
        conversation = conv.get("conversation", conv)
        sample_id = str(conv.get("sample_id") or src.stem)
        try:
            # Pair each session_N turn list with its session_N_date_time.
            for key in conversation:
                match = _SESSION_RE.match(key)
                if not match:
                    continue
                n = match.group(1)
                when = parse_when(conversation.get(f"session_{n}_date_time", ""))
                turns = conversation.get(key) or []
                for turn in turns:
                    dia_id = turn.get("dia_id")
                    text = (turn.get("text") or "").strip()
                    if not dia_id or not text:
                        continue
                    speaker = turn.get("speaker") or ""
                    rel = _turn_path(sample_id, dia_id)

                    notes.append((
                        rel,                       # relative_path
                        Path(rel).name,            # filename
                        "conversation",            # category
                        0.0,                       # energy
                        0.0,                       # sentiment
                        json.dumps([]),            # sentiment_label
                        json.dumps([speaker] if speaker else []),  # tags
                        text,                      # key_lines_text
                        len(text.split()),         # word_count
                    ))

                    sections.append(pkm.Section(
                        section_id=f"{rel}::0:0",
                        path=rel,
                        heading=f"{speaker} — {dia_id}",
                        start_line=1,
                        chunk_index=0,
                        sha256=pkm.get_sha256(text),
                        text=text,
                    ))

                    turn_concepts.append((rel, sample_id, extract_concepts(text)))
                    sample_turns[sample_id] += 1

                    if when:
                        _CREATION_DATES[rel] = when
        except Exception as error:  # never let one bad conv kill the index
            errors.append((sample_id, "parse", str(error)))

    links.extend(_emit_concept_links(turn_concepts, sample_turns))
    return notes, sections, links, errors


# Concept edges only help the Adamic-Adar term when a concept is SHARED
# (appears in >= _MIN_DF turns, else it links nothing) and DISCRIMINATIVE
# (not in a large fraction of the conversation, else it is noise like a
# speaker name that AA has to down-weight anyway). Both bounds are per
# conversation.
_MIN_DF = 2
_MAX_DF_FRAC = 0.5


def _emit_concept_links(turn_concepts, sample_turns):
    df: Counter[tuple[str, str]] = Counter()
    for _rel, sample_id, concepts in turn_concepts:
        for concept in set(concepts):
            df[(sample_id, concept)] += 1
    out = []
    for rel, sample_id, concepts in turn_concepts:
        cap = max(_MIN_DF, int(sample_turns[sample_id] * _MAX_DF_FRAC))
        for concept in concepts:
            if _MIN_DF <= df[(sample_id, concept)] <= cap:
                out.append(pkm.Link(
                    source_path=rel,
                    raw_target=concept,
                    # Namespaced per conversation so cross-conv turns that
                    # happen to share a concept are never linked.
                    resolved_target_path=f"_concepts/{sample_id}/{concept}.md",
                    start_line=1,
                ))
    return out


if __name__ == "__main__":
    import sys
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    n, s, l, e = scan_locomo(root)
    print(f"notes={len(n)} sections={len(s)} links={len(l)} errors={len(e)} "
          f"dated={len(_CREATION_DATES)}")
    if e:
        print("errors:", e[:3])
