"""Wall-clock and concurrency across a whole agent tree.

usage: python session-timing.py <session-id-prefix>
"""
import json, os, sys, glob, datetime, collections

ROOT = os.path.expanduser("~/.claude/projects")
SESS = sys.argv[1]
iv = []          # (start, end, name) per subagent file
main_ts = []

for fp in glob.glob(os.path.join(ROOT, "**", "*.jsonl"), recursive=True):
    if SESS not in fp.replace("\\", "/"):
        continue
    ts = []
    for line in open(fp, "r", encoding="utf-8", errors="replace"):
        if len(line) < 2:
            continue
        try:
            d = json.loads(line)
        except Exception:
            continue
        t = d.get("timestamp")
        if t:
            ts.append(datetime.datetime.fromisoformat(t.replace("Z", "+00:00")))
    if not ts:
        continue
    ts.sort()
    if "subagents" in fp.replace("\\", "/"):
        iv.append((ts[0], ts[-1], os.path.basename(fp)[:8]))
    else:
        main_ts += ts

main_ts.sort()
print(f"subagent files: {len(iv)}   main-thread events: {len(main_ts)}")
if main_ts:
    print(f"session span: {main_ts[0]:%m-%d %H:%M} -> {main_ts[-1]:%m-%d %H:%M} "
          f"= {(main_ts[-1]-main_ts[0]).total_seconds()/3600:.1f}h")

# sum of agent runtime and union busy time
tot = sum((b - a).total_seconds() for a, b, _ in iv) / 3600
ev = sorted([(a, 1) for a, b, _ in iv] + [(b, -1) for a, b, _ in iv])
busy = 0.0
n = 0
prev = None
hist = collections.Counter()
peak = 0
for t, delta in ev:
    if prev is not None and n > 0:
        busy += (t - prev).total_seconds()
        hist[n] += (t - prev).total_seconds()
    prev = t
    n += delta
    peak = max(peak, n)
busy /= 3600
print(f"sum of agent runtime: {tot:.1f}h   union busy: {busy:.1f}h   "
      f"parallelism {tot/busy if busy else 0:.2f}x   peak concurrent {peak}")
print("time at N agents running (h):")
for k in sorted(hist):
    print(f"  {k:>3}: {hist[k]/3600:>6.2f}")

# main-thread idle gaps
gaps = [(b - a).total_seconds() / 60 for a, b in zip(main_ts, main_ts[1:])]
span = (main_ts[-1] - main_ts[0]).total_seconds() / 60
for th in (2, 5, 15, 60):
    g = [x for x in gaps if x > th]
    print(f"main gaps >{th:>2}min: {len(g):>4}  total {sum(g)/60:>6.1f}h  "
          f"({100*sum(g)/span:.0f}% of span)")

# agent duration distribution
durs = sorted((b - a).total_seconds() / 60 for a, b, _ in iv)
if durs:
    import statistics
    print(f"agent duration min: median {statistics.median(durs):.1f}  "
          f"p90 {durs[int(.9*len(durs))]:.1f}  max {durs[-1]:.1f}")
