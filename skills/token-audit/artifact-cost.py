"""Attribute subagent cost to the file each agent wrote.

usage: python artifact-cost.py <session-id-prefix> <output-dir> [path-substring-filter]
"""
import json, os, sys, glob, collections

ROOT = os.path.expanduser("~/.claude/projects")
SESS = sys.argv[1]
FILTER = sys.argv[3] if len(sys.argv) > 3 else ""
COST = lambda u: ((u.get("cache_read_input_tokens") or 0) * 0.1
                  + (u.get("cache_creation_input_tokens") or 0) * 1.25
                  + (u.get("output_tokens") or 0) * 5
                  + (u.get("input_tokens") or 0)) * 5 / 1e6

per_doc = collections.defaultdict(lambda: {"cost": 0.0, "calls": 0, "fetch": 0,
                                           "search": 0, "agents": 0, "words": 0})
research_agents = 0

for fp in glob.glob(os.path.join(ROOT, "**", "*.jsonl"), recursive=True):
    p = fp.replace("\\", "/")
    if SESS not in p or "subagents" not in p:
        continue
    cost = 0.0
    calls = fetch = search = 0
    docs = set()
    seen = set()
    for line in open(fp, "r", encoding="utf-8", errors="replace"):
        if len(line) < 2:
            continue
        try:
            d = json.loads(line)
        except Exception:
            continue
        m = d.get("message") or {}
        c = m.get("content")
        if isinstance(c, list):
            for b in c:
                if not (isinstance(b, dict) and b.get("type") == "tool_use"):
                    continue
                nm = b.get("name")
                if nm == "WebFetch":
                    fetch += 1
                elif nm == "WebSearch":
                    search += 1
                if nm in ("Write", "Edit", "MultiEdit"):
                    fpath = (b.get("input") or {}).get("file_path", "")
                    if FILTER in fpath.replace("\\", "/"):
                        docs.add(os.path.basename(fpath))
        u = m.get("usage") or {}
        if not u:
            continue
        mid = m.get("id") or d.get("uuid")
        if mid in seen:
            continue
        seen.add(mid)
        cost += COST(u)
        calls += 1
    if not docs:
        continue
    research_agents += 1
    share = 1.0 / len(docs)
    for doc in docs:
        e = per_doc[doc]
        e["cost"] += cost * share
        e["calls"] += calls * share
        e["fetch"] += fetch * share
        e["search"] += search * share
        e["agents"] += 1

REPO = sys.argv[2]
print(f"{'doc':44} {'$':>7} {'calls':>7} {'fetch':>6} {'srch':>5} {'agents':>6} {'words':>7}")
tot = 0.0
for doc, e in sorted(per_doc.items(), key=lambda x: -x[1]["cost"]):
    w = ""
    fp = os.path.join(REPO, doc)
    if os.path.exists(fp):
        w = len(open(fp, encoding="utf-8", errors="replace").read().split())
    else:
        w = "GONE"
    tot += e["cost"]
    print(f"{doc:44} {e['cost']:>7.0f} {e['calls']:>7.0f} {e['fetch']:>6.0f} "
          f"{e['search']:>5.0f} {e['agents']:>6} {str(w):>7}")
print(f"\n{research_agents} agents wrote a matching file; attributed total ${tot:,.0f}")
