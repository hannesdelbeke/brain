"""Rank claude code sessions by cost.

usage: python session-cost.py [name=session-id-prefix ...]
"""
import json, os, sys, glob, collections
root = os.path.expanduser("~/.claude/projects")
tot = collections.Counter()
sess_cost = collections.Counter(); sess_turns = collections.Counter(); sess_cwd = {}
for fp in glob.glob(os.path.join(root, "**", "*.jsonl"), recursive=True):
    seen=set(); key=fp
    for line in open(fp,"r",encoding="utf-8",errors="replace"):
        if len(line)<2: continue
        try: d=json.loads(line)
        except Exception: continue
        if d.get("cwd") and key not in sess_cwd: sess_cwd[key]=d["cwd"]
        m=d.get("message") or {}; u=m.get("usage") or {}
        if not u: continue
        mid=m.get("id") or d.get("uuid")
        if mid in seen: continue
        seen.add(mid)
        for k in ("input_tokens","output_tokens","cache_read_input_tokens","cache_creation_input_tokens"):
            tot[k]+=u.get(k) or 0
        sess_cost[key]+=(u.get("cache_read_input_tokens") or 0)*0.1+(u.get("cache_creation_input_tokens") or 0)*1.25+(u.get("output_tokens") or 0)*5+(u.get("input_tokens") or 0)
        sess_turns[key]+=1

print("=== LIFETIME, deduped by message.id ===")
for k,v in tot.most_common(): print(f"  {k:32} {v:>15,}")
c = tot["cache_read_input_tokens"]*0.1 + tot["cache_creation_input_tokens"]*1.25 + tot["output_tokens"]*5 + tot["input_tokens"]
print(f"  base-input-equivalents {c:,.0f}   ~${c*5/1e6:,.0f}")
print(f"  shares: read {100*tot['cache_read_input_tokens']*0.1/c:.0f}%  create {100*tot['cache_creation_input_tokens']*1.25/c:.0f}%  output {100*tot['output_tokens']*5/c:.0f}%  input {100*tot['input_tokens']/c:.0f}%")
print(f"  total API calls: {sum(sess_turns.values()):,}   avg $/call {c*5/1e6/sum(sess_turns.values()):.4f}")

print("\n=== TOP SESSIONS (main only) ===")
mains = {k:v for k,v in sess_cost.items() if "subagents" not in k}
for fp,v in sorted(mains.items(), key=lambda x:-x[1])[:8]:
    t=sess_turns[fp]
    print(f"  ${v*5/1e6:>7,.0f}  calls={t:>6,}  $/call={v*5/1e6/max(t,1):.3f}  {os.path.basename(fp)[:8]}  {sess_cwd.get(fp,'?')}")

if len(sys.argv) > 1:
    print("\n=== TARGET TREES (main + subagents) ===")
for spec in sys.argv[1:]:
    name, _, pref = spec.partition("=")
    pref = pref or name
    tc=sum(v for k,v in sess_cost.items() if pref in k)
    tt=sum(v for k,v in sess_turns.items() if pref in k)
    print(f"  {name:11} ${tc*5/1e6:>7,.0f}   API calls={tt:>7,}   $/call={tc*5/1e6/max(tt,1):.4f}")
