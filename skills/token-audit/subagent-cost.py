"""Cost per subagent under one session tree.

usage: python subagent-cost.py <session-uuid>
"""
import json, os, sys, glob, collections, datetime as dt
ROOT = os.path.expanduser("~/.claude/projects")
sess = sys.argv[1]
files = glob.glob(os.path.join(ROOT, "*", sess + ".jsonl")) + sorted(
    glob.glob(os.path.join(ROOT, "*", sess, "subagents", "*.jsonl")))

par = collections.Counter(); costs = collections.Counter(); ncalls = collections.Counter()
read_tok = collections.Counter(); read_hits = collections.Counter(); read_uniq = {}
tool_tok = collections.Counter(); tool_n = collections.Counter()
bash_cmd = collections.Counter(); bash_tok = collections.Counter()
imgs = 0; agent_rows = []; think = 0; prose = 0
gaps5 = 0; gapcc = 0; ts = []

for fp in files:
    tag = "MAIN" if fp.endswith(sess+".jsonl") else os.path.basename(fp)[:20]
    seen=set(); seen_tr=set(); id2={}; inputs={}
    c=0; n=0; edits=0; ctxs=[]; last=None; brief=None
    for line in open(fp,"r",encoding="utf-8",errors="replace"):
        if len(line)<2: continue
        try: d=json.loads(line)
        except Exception: continue
        m=d.get("message") or {}; u=m.get("usage") or {}
        cn=m.get("content")
        if d.get("type")=="user" and brief is None:
            if isinstance(cn,str): brief=cn[:130]
            elif isinstance(cn,list):
                for b in cn:
                    if isinstance(b,dict) and b.get("type")=="text": brief=b.get("text","")[:130]; break
        if isinstance(cn,list):
            for b in cn:
                if not isinstance(b,dict): continue
                if b.get("type")=="tool_use":
                    id2[b["id"]]=b.get("name"); inputs[b["id"]]=b.get("input") or {}
                elif b.get("type")=="tool_result":
                    tid=b.get("tool_use_id")
                    if tid in seen_tr: continue
                    seen_tr.add(tid)
                    nm=id2.get(tid,"?"); inp=inputs.get(tid,{}); ct=b.get("content"); k=0
                    if isinstance(ct,str): k=len(ct)
                    elif isinstance(ct,list):
                        for cb in ct:
                            if not isinstance(cb,dict): continue
                            if cb.get("type")=="text": k+=len(cb.get("text",""))
                            elif cb.get("type")=="image": imgs+=1
                    k//=4; tool_tok[nm]+=k; tool_n[nm]+=1
                    if nm=="Read":
                        p=(inp.get("file_path") or "?").lower(); read_tok[p]+=k; read_hits[p]+=1
                        read_uniq[p]=max(read_uniq.get(p,0),k)
                    elif nm=="Bash":
                        cmd=" ".join((inp.get("command") or "").split())[:60]
                        bash_cmd[cmd]+=1; bash_tok[cmd]+=k
                    elif nm in ("Edit","Write"): edits+=1
        if not u or d.get("type")!="assistant": continue
        mid=m.get("id") or d.get("uuid")
        if mid in seen: continue
        seen.add(mid)
        cost=(u.get("cache_read_input_tokens") or 0)*0.1+(u.get("cache_creation_input_tokens") or 0)*1.25+(u.get("output_tokens") or 0)*5+(u.get("input_tokens") or 0)
        c+=cost; n+=1
        ctxs.append((u.get("cache_read_input_tokens") or 0)+(u.get("cache_creation_input_tokens") or 0)+(u.get("input_tokens") or 0))
        t=d.get("timestamp")
        if t:
            try: cur=dt.datetime.fromisoformat(t.replace("Z","+00:00"))
            except Exception: cur=None
            if cur:
                ts.append(cur)
                if last and (cur-last).total_seconds()>300:
                    gaps5+=1; gapcc+=u.get("cache_creation_input_tokens") or 0
                last=cur
    # count parallel tool_use per message id. second pass on purpose: the blocks of one
    # response are split across lines, so this must not skip repeated ids the way the
    # usage loop above does, only dedupe the tool_use ids themselves.
    byid=collections.Counter()
    for line in open(fp,"r",encoding="utf-8",errors="replace"):
        if len(line)<2 or '"tool_use"' not in line: continue
        try: d=json.loads(line)
        except Exception: continue
        if d.get("type")!="assistant": continue
        m=d.get("message") or {}; mid=m.get("id")
        for b in (m.get("content") or []):
            if isinstance(b,dict) and b.get("type")=="tool_use": byid[(mid,b["id"])]=1
    per=collections.Counter()
    for (mid,_) in byid: per[mid]+=1
    for mid,k in per.items(): par[k]+=1
    agent_rows.append((tag,n,c,max(ctxs) if ctxs else 0,sum(ctxs)/max(len(ctxs),1),edits,brief))

TOT=sum(r[2] for r in agent_rows); TN=sum(r[1] for r in agent_rows)
if not TN: sys.exit(f"no api calls found for session {sess} under {ROOT}")
print(f"=== SESSION TREE, deduped: {TN:,} API calls, ${TOT*5/1e6:,.0f}, ${TOT*5/1e6/TN:.4f} per call ===")
if ts: ts.sort(); print(f"  span {(ts[-1]-ts[0]).total_seconds()/3600:.1f} h")
print(f"  calls after >5min gap: {gaps5}  cache_creation there {gapcc:,} tok = ${gapcc*1.25*5/1e6:,.0f}")
print(f"\n  tool_use blocks per API call: " + ", ".join(f"{k}:{v:,}" for k,v in sorted(par.items())))
tu=sum(k*v for k,v in par.items()); ac=sum(par.values())
print(f"  {tu:,} tool calls in {ac:,} API calls = {tu/max(ac,1):.2f} per call; {TN-ac:,} calls made no tool call")

print("\n=== COST PER CALL BY AGENT LENGTH ===")
subs=[r for r in agent_rows if r[0]!="MAIN"]
for lo,hi in [(1,10),(11,25),(26,50),(51,100),(101,300),(301,99999)]:
    s=[r for r in subs if lo<=r[1]<=hi]
    if not s: continue
    T=sum(r[1] for r in s); C=sum(r[2] for r in s)
    print(f"  {lo:>4}-{hi:<6} agents={len(s):>4} calls={T:>6,} ${C*5/1e6:>6,.0f}  $/call={C*5/1e6/T:.4f}  avgctx={sum(r[4]*r[1] for r in s)/T:>8,.0f}  peak={max(r[3] for r in s):,}")

print("\n=== TOOL MIX ===")
for nm,tk in tool_tok.most_common(10): print(f"  {nm:36} {tk:>9,} tok  calls={tool_n[nm]:>6}")
print(f"  images: {imgs:,}")

tr=sum(read_tok.values()); ur=sum(read_uniq.values())
print(f"\n=== READ REDUNDANCY: {tr:,} tok delivered / {ur:,} distinct = {tr/max(ur,1):.1f}x over {len(read_hits):,} paths ===")
for p,v in read_tok.most_common(8): print(f"  {read_hits[p]:>4}x {v:>8,} tok  {os.path.basename(p)}")

print("\n=== TOP AGENTS ===")
for r in sorted(subs,key=lambda x:-x[2])[:8]:
    print(f"  ${r[2]*5/1e6:>6,.1f} calls={r[1]:>4} edits={r[5]:>3} peak={r[3]:>7,}  {' '.join((r[6] or '?').split())[:110]}")
print(f"\n  MAIN: ${[r for r in agent_rows if r[0]=='MAIN'][0][2]*5/1e6:,.0f}  ({100*[r for r in agent_rows if r[0]=='MAIN'][0][2]/TOT:.0f}% of tree)")
ro=[r for r in subs if r[5]==0]; ed=[r for r in subs if r[5]>0]
print(f"  no-edit agents {len(ro)}: ${sum(r[2] for r in ro)*5/1e6:,.0f}   editing agents {len(ed)}: ${sum(r[2] for r in ed)*5/1e6:,.0f}")
