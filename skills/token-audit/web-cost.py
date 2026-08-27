"""Where a session tree's WebFetch and WebSearch calls actually went.

usage: python web-cost.py <session-id-prefix>
"""
import json, os, sys, glob, collections

ROOT = os.path.expanduser("~/.claude/projects")
SESS = sys.argv[1]
COST = lambda u: ((u.get("cache_read_input_tokens") or 0) * 0.1
                  + (u.get("cache_creation_input_tokens") or 0) * 1.25
                  + (u.get("output_tokens") or 0) * 5
                  + (u.get("input_tokens") or 0)) * 5 / 1e6

rows = []
tot_fetch = tot_search = 0
for fp in glob.glob(os.path.join(ROOT, "**", "*.jsonl"), recursive=True):
    p = fp.replace("\\", "/")
    if SESS not in p:
        continue
    cost = 0.0
    calls = fetch = search = 0
    writes = collections.Counter()
    first_prompt = ""
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
        if not first_prompt and d.get("type") == "user" and isinstance(c, str):
            first_prompt = c[:150].replace("\n", " ")
        if isinstance(c, list):
            for b in c:
                if not (isinstance(b, dict) and b.get("type") == "tool_use"):
                    continue
                nm = b.get("name")
                if nm == "WebFetch":
                    fetch += 1
                elif nm == "WebSearch":
                    search += 1
                elif nm in ("Write", "Edit", "MultiEdit"):
                    fpath = (b.get("input") or {}).get("file_path", "")
                    if fpath:
                        writes[os.path.basename(fpath)] += 1
        u = m.get("usage") or {}
        if not u:
            continue
        mid = m.get("id") or d.get("uuid")
        if mid in seen:
            continue
        seen.add(mid)
        cost += COST(u)
        calls += 1
    tot_fetch += fetch
    tot_search += search
    if fetch + search > 0:
        rows.append((fetch + search, fetch, search, cost, calls,
                     ", ".join(f for f, _ in writes.most_common(3)), first_prompt))

rows.sort(reverse=True)
print(f"total across tree: {tot_fetch} webfetch, {tot_search} websearch, "
      f"in {len(rows)} agents")
print(f"{'fetch':>6}{'srch':>6}{'$':>7}{'calls':>7}  wrote / brief")
web_cost = 0.0
for tot, f, s, cost, calls, wrote, prompt in rows[:22]:
    web_cost += cost
    print(f"{f:>6}{s:>6}{cost:>7.0f}{calls:>7}  {wrote[:44] or '-'}")
    print(f"{'':25}  {prompt[:110]}")
print(f"\ncost of all {len(rows)} web-using agents: ${sum(r[3] for r in rows):,.0f}")
