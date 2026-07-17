import subprocess, re
OPENERS = {"FILE","STRUCT","FUNCTION","REGISTRY","ENUM","TYPE","MACRO","TEST","STRATEGY","ASSERT"}
LIGHT = {"MACRO","TEST","ASSERT","FILE"}   # no closer expected
RANK = {"ROW":0,"VALUE":0,"FIELD":0,"WIRE_FIELD":0,"EXCLUDED":0,"COMMENT":1,"SUPPORTING_DOCS":1,"DERIVED":2,"REFERENCE":3,"FUTURE_WORK":3}
cat = re.compile(r'^\s*//\s*\[([A-Z_0-9]+)\]')
name_re = re.compile(r'^\s*//\s*\[[A-Z_0-9]+\]_\[([^\]]*)\]')
conv = subprocess.run(["grep","-rl","^// \\[FILE\\]_\\[","CoreFrameworks","Strategies","ML_Headers","MemHeaders","DataStream","Backtest","GUI","FixedPoint"],capture_output=True,text=True).stdout.split()
viol = 0
for f in sorted(conv):
    if "RegimeDetector" in f: continue
    lines = open(f).read().split("\n")
    stack = []   # [type, name, phase_rank, saw_code]
    code_depth = 0
    for i, l in enumerate(lines):
        m = cat.match(l)
        if not m: continue
        tok = m.group(1)
        if tok == "CODE": code_depth += 1;  continue
        if tok == "END_CODE":
            code_depth = max(0, code_depth - 1)
            if code_depth == 0 and stack: stack[-1][2] = -1; stack[-1][3] = True
            continue
        if code_depth > 0: continue                            # fence content (any depth) is opaque
        if tok in OPENERS:
            nm = name_re.match(l)
            if tok not in LIGHT:
                stack.append([tok, nm.group(1) if nm else "?", -2, False])   # -2 = orient phase
            continue
        if tok.startswith("END_"):
            ut = tok[4:]
            nm = name_re.match(l)
            if not stack:
                print(f"  {f}:{i+1}  [END_{ut}] with no open block"); viol += 1; continue
            t, n, _, _ = stack[-1]
            if ut != t or (nm and nm.group(1) != n):
                print(f"  {f}:{i+1}  closer [END_{ut}]_[{nm.group(1) if nm else '?'}] vs open [{t}]_[{n}]"); viol += 1
            stack.pop(); continue
        if stack:
            t, n, rank, saw_code = stack[-1]
            r = RANK.get(tok)
            if rank == -2:                                     # orient phase
                if tok in ("COMMENT","DERIVED"):
                    print(f"  {f}:{i+1}  [{tok}] in ORIENT region of [{t}]_[{n}] (belongs in tail)"); viol += 1
                continue
            if r is None: continue                             # non-section tags in tail (e.g. EDIT-ish) — ignore
            if r < rank:
                print(f"  {f}:{i+1}  ladder order: [{tok}] (rank {r}) after rank {rank} in [{t}]_[{n}]"); viol += 1
            else:
                stack[-1][2] = r
    for t, n, _, _ in stack:
        print(f"  {f}:EOF  [{t}]_[{n}] never closed"); viol += 1
print(f"LADDER/STRUCTURE VIOLATIONS: {viol}")
