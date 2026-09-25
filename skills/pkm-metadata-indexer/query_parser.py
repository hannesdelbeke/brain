"""Split a query into independent facets, so a multi-concept string can be searched.

A cross-encoder scores a whole query against a whole section, which is the right
thing to do when the query is a question and the wrong thing when it is a pile of
concepts. `stroke fatigue dopamine coding hyperfocus` scored 0.007 against every
section in this vault, because no single paragraph is about all five and the model
penalises multi-topic sprawl rather than rewarding partial coverage. The note that
answers such a query is the one that covers four of the five in four different
sections, and no whole-query scorer can see that.

So the query is cut into facets and each facet is matched on its own. What comes
back is not a score but a count -- four facets out of five, and the line each one
was found on -- which is the thing the semantic track structurally cannot report.

Facets are built here and consumed by `dual_track.py`. This module does no I/O
beyond one read-only pass over `notes` for alias expansion, and holds no model.
"""

from __future__ import annotations

import re
from pathlib import Path

# Words that carry no retrieval signal but would each become their own facet and
# then match most of the vault, dragging every note's coverage count up by one and
# flattening the ranking this whole module exists to sharpen. The list is the one
# in the specification plus nothing: a longer stop list starts eating real query
# terms, and `over` in `over-engineering` is already a borderline call.
STOP_WORDS = frozenset({
    "and", "the", "in", "with", "for", "or", "about", "from", "over", "into",
})

# Above this many facets the FTS pass stops being cheap -- it is one query per
# facet -- and the coverage count stops discriminating, because a 12-facet query
# separates 3/12 from 2/12 and neither is an answer. Terms past the cap are kept
# in `dropped` and reported rather than silently discarded.
MAX_FACETS = 8

# How many alias or tag synonyms a single facet may absorb. Unbounded expansion
# is what makes coverage counts meaningless: a facet that has quietly become 24
# OR'd names matches nearly every note, every note then scores N/N, and the
# ranking is flat again. Four is enough for `fatigue -> tired, exhaustion` and
# too few to turn a facet into a topic.
MAX_SYNONYMS_PER_FACET = 4

_QUOTED = re.compile(r"\"([^\"]+)\"|'([^']+)'")
# Terms keep their hyphens, so `post-stroke` stays one term and reaches FTS5 as the
# phrase "post stroke" rather than as two facets.
_WORD = re.compile(r"[\w'-]+", re.UNICODE)
# Tokens do not, because this is the emptiness test. With the hyphen in the class a
# run of dashes tokenized to itself, survived as a facet, and reached FTS5 as
# `MATCH "---"` -- a term the tokenizer reduces to nothing, which matches nothing
# and contributes a facet nobody can ever cover.
_TOKEN = re.compile(r"[\w']+", re.UNICODE)


def _tokens(text: str) -> set[str]:
    return {token.casefold() for token in _TOKEN.findall(text or "")}


def fts_literal(term: str) -> str:
    """Quote a term for an FTS5 MATCH expression.

    Everything goes inside double quotes, which is what makes a phrase a phrase
    and also what stops a term like `OR` or `NEAR` being read as an operator. An
    internal double quote is doubled, per the FTS5 string-literal rule; the older
    `fast_fts_search` strips them instead, which silently changes the term.
    """
    return '"' + term.replace('"', '""') + '"'


def facet_expression(terms: list[str]) -> str:
    """OR a facet's terms into one MATCH expression, or return '' if nothing survives.

    A term that tokenizes to nothing -- punctuation, a lone hyphen -- has to be
    dropped rather than quoted, because `MATCH ""` is an FTS5 syntax error and
    would take down the whole facet pass with it.
    """
    literals = [fts_literal(term) for term in terms if _tokens(term)]
    if not literals:
        return ""
    if len(literals) == 1:
        return literals[0]
    return "(" + " OR ".join(literals) + ")"


def split_terms(query: str) -> tuple[list[str], list[str]]:
    """Return the query's content terms and the quoted ones, in reading order.

    A quoted substring is atomic: `"stroke recovery"` is one facet that has to
    appear as a phrase, not two facets that each match half the vault. So the
    quoted runs are lifted out first and the remainder is tokenized, which is the
    only order that works -- tokenizing first destroys the quotes.
    """
    verbatim: list[str] = []

    def lift(match: re.Match) -> str:
        phrase = (match.group(1) or match.group(2) or "").strip()
        if phrase:
            verbatim.append(phrase)
        return " "

    remainder = _QUOTED.sub(lift, query or "")
    plain = [
        token for token in _WORD.findall(remainder)
        if token.casefold() not in STOP_WORDS and len(token) > 1
    ]
    return plain, verbatim


def parse_query_facets(query: str, db_path: str | Path | None = None,
                       override: list[str] | None = None) -> dict:
    """Cut `query` into facets and expand each one with its own aliases.

    Returns a dict rather than a list because the caller needs three decisions out
    of one parse: the facets to match, whether this is a single-entity query (one
    term, so the graph track leads and the FTS track is a title lookup), and which
    terms were dropped, so the output can admit it rather than quietly answering a
    narrower question than the one asked.

    Expansion is deliberately narrower than `entity_expansion.expand_query`, which
    also pulls in path components and the names of every outbound link. Those are
    right for widening a single-entity lookup and wrong inside a facet, where every
    added name raises the chance the facet matches a note that is not about it --
    and a facet that matches everything contributes a constant to every coverage
    count, which is the same as not existing.
    """
    if override:
        # An explicit facet list skips tokenizing and skips the stop list, because
        # the caller asking for `--facets "stroke,for,fatigue"` has already decided
        # that `for` is a facet here. It still gets the cap and the expansion.
        verbatim = [term.strip() for term in override if term.strip()]
        ordered = verbatim
    else:
        plain, verbatim = split_terms(query)
        ordered = verbatim + plain
    kept, dropped = ordered[:MAX_FACETS], ordered[MAX_FACETS:]

    synonyms: dict[str, list[str]] = {}
    if db_path is not None and kept:
        from entity_expansion import expand_facets

        synonyms = expand_facets(kept, db_path, per_facet_limit=MAX_SYNONYMS_PER_FACET)

    facets = []
    for term in kept:
        extra = [name for name in synonyms.get(term, []) if name.casefold() != term.casefold()]
        terms = [term, *extra]
        expression = facet_expression(terms)
        if not expression:
            continue
        facets.append({
            "term": term,
            "terms": terms,
            "expression": expression,
            "verbatim": term in verbatim,
        })

    return {
        "query": query,
        "facets": facets,
        "single_entity": len(facets) == 1,
        "dropped": dropped,
    }
