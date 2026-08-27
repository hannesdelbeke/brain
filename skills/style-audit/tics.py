"""Build an n-gram frequency database from assistant prose in local Claude Code transcripts.

Counts only assistant `text` blocks, deduped on (message.id, block text), with code / urls / paths stripped.
Deduping on message.id alone is wrong here: the repeated lines carry different blocks, not copies.
Writes sqlite. Re-run with --since to get a window and diff the rates.
"""
import argparse, collections, glob, json, os, re, sqlite3, sys

AP = argparse.ArgumentParser()
AP.add_argument("--root", default=os.path.expanduser(r"~\.claude\projects"))
AP.add_argument("--out", default="tics.db")
AP.add_argument("--since", default="", help="YYYY-MM-DD lower bound on message timestamp")
AP.add_argument("--until", default="", help="YYYY-MM-DD upper bound")
AP.add_argument("--maxn", type=int, default=5)
AP.add_argument("--minc", type=int, default=3, help="drop n-grams below this final count")
AP.add_argument("--limit", type=int, default=0, help="stop after N files, for a smoke test")
A = AP.parse_args()

FENCE = re.compile(r"```.*?```", re.S)
INLINE = re.compile(r"`[^`]*`")
URL = re.compile(r"https?://\S+|\bwww\.\S+")
WINPATH = re.compile(r"[A-Za-z]:[\\/][^\s,;:'\"]+")
POSIXPATH = re.compile(r"(?:\.{0,2}/[\w.\-]+){2,}")
FILEISH = re.compile(r"\b[\w.\-]+\.(?:py|ts|tsx|js|jsx|md|json|jsonl|cs|java|go|rb|php|yaml|yml|toml|ini|cfg|sh|bat|ps1|html|css|scss|sql|txt|png|jpg|svg)\b")
XMLTAG = re.compile(r"<[^>\n]{1,80}>")
WORD = re.compile(r"[a-z][a-z']*")
SENT = re.compile(r"[.!?;:]+\s|\n+|\s[-*•]\s|\s\d+\.\s")


def clean(s):
    s = FENCE.sub(" \n ", s)
    s = INLINE.sub(" ", s)
    s = URL.sub(" ", s)
    s = WINPATH.sub(" ", s)
    s = POSIXPATH.sub(" ", s)
    s = FILEISH.sub(" ", s)
    s = XMLTAG.sub(" \n ", s)
    return s.lower().replace("’", "'").replace("‘", "'")


grams = [collections.Counter() for _ in range(A.maxn + 1)]   # index = n
opens = [collections.Counter() for _ in range(A.maxn + 1)]   # sentence-initial
per_month_words = collections.Counter()
seen = set()
stats = collections.Counter()


def prune(force=False):
    """Bound memory. Rare n-grams cannot be tics, so drop the long tail as we go."""
    for n in range(2, A.maxn + 1):
        c = grams[n]
        if force or len(c) > 4_000_000:
            floor = 2 if not force else A.minc
            for k in [k for k, v in c.items() if v < floor]:
                del c[k]


files = sorted(glob.glob(os.path.join(A.root, "**", "*.jsonl"), recursive=True))
if A.limit:
    files = files[: A.limit]
print(f"{len(files)} transcript files", file=sys.stderr)

for i, fp in enumerate(files):
    if i % 50 == 0:
        print(f"  [{i}/{len(files)}] msgs={stats['msgs']:,} words={stats['words']:,}", file=sys.stderr)
        prune()
    try:
        fh = open(fp, "r", encoding="utf-8", errors="replace")
    except OSError:
        continue
    with fh:
        for line in fh:
            if len(line) < 2 or '"assistant"' not in line:
                continue
            try:
                d = json.loads(line)
            except Exception:
                continue
            if d.get("type") != "assistant":
                continue
            msg = d.get("message") or {}
            mid = msg.get("id")
            if not mid:
                continue
            ts = (d.get("timestamp") or "")[:10]
            if A.since and ts and ts < A.since:
                continue
            if A.until and ts and ts > A.until:
                continue
            content = msg.get("content")
            if not isinstance(content, list):
                continue
            # claude code writes one jsonl line per content block and repeats the same
            # message.id on each, so dedupe on (id, block) rather than on id alone.
            parts = []
            for b in content:
                if not isinstance(b, dict) or b.get("type") != "text":
                    continue
                t = b.get("text", "")
                key = (mid, hash(t))
                if t.strip() and key not in seen:
                    seen.add(key)
                    parts.append(t)
            if not parts:
                continue
            text = " \n ".join(parts)
            stats["msgs"] += 1
            month = ts[:7]
            for chunk in SENT.split(clean(text)):
                if not chunk:
                    continue
                w = WORD.findall(chunk)
                if not w:
                    continue
                stats["words"] += len(w)
                per_month_words[month] += len(w)
                for n in range(1, A.maxn + 1):
                    if len(w) >= n:
                        opens[n][" ".join(w[:n])] += 1
                    g = grams[n]
                    for j in range(len(w) - n + 1):
                        g[" ".join(w[j:j + n])] += 1

prune(force=True)
print(f"done: {stats['msgs']:,} messages, {stats['words']:,} words", file=sys.stderr)

if os.path.exists(A.out):
    os.remove(A.out)
db = sqlite3.connect(A.out)
db.executescript("""
CREATE TABLE ngram (text TEXT, n INT, count INT, opens INT, per_million REAL);
CREATE TABLE corpus (month TEXT, words INT);
CREATE INDEX ix_n ON ngram(n, count DESC);
CREATE INDEX ix_t ON ngram(text);
""")
total = max(stats["words"], 1)
rows = []
for n in range(1, A.maxn + 1):
    floor = A.minc if n > 1 else 1
    o = opens[n]
    for t in set(grams[n]) | {k for k, v in o.items() if v >= floor}:
        c = max(grams[n].get(t, 0), o.get(t, 0))
        if c >= floor:
            rows.append((t, n, c, o.get(t, 0), c * 1e6 / total))
db.executemany("INSERT INTO ngram VALUES (?,?,?,?,?)", rows)
db.executemany("INSERT INTO corpus VALUES (?,?)", sorted(per_month_words.items()))
db.commit()
print(f"wrote {len(rows):,} rows to {A.out}", file=sys.stderr)

for n in (1, 2, 3, 4, 5):
    if n > A.maxn:
        break
    print(f"\n=== top {n}-grams by sentence-opening count ===")
    for t, c in opens[n].most_common(15):
        print(f"  {c:>7,}  {grams[n].get(t,0):>8,} total   {t}")
