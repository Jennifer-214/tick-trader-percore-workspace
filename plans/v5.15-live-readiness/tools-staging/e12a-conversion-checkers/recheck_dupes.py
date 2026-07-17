import subprocess, re
from collections import Counter
conv = subprocess.run(["grep","-rl","^// \\[FILE\\]_\\[","CoreFrameworks","Strategies","ML_Headers","MemHeaders","DataStream","Backtest","GUI","FixedPoint"],capture_output=True,text=True).stdout.split()
bar = re.compile(r'^\s*//[=\-~]{8,}\s*$'); tagl = re.compile(r'^\s*//\s*\[')
dupes = 0
for f in sorted(conv):
    if "RegimeDetector" in f: continue
    lines = open(f).read().split("\n")
    runs = Counter(); i = 0
    while i < len(lines):
        l = lines[i].strip()
        if l.startswith("//") and not bar.match(lines[i]) and not tagl.match(lines[i]) and len(l) > 20:
            j = i; body = []
            while j < len(lines):
                s = lines[j].strip()
                if s.startswith("//") and not bar.match(lines[j]) and not tagl.match(lines[j]) and len(s) > 20:
                    body.append(s); j += 1
                else: break
            if len(body) >= 3: runs["\n".join(body)] += 1
            i = j
        else: i += 1
    for run, c in runs.items():
        if c > 1:
            dupes += 1
            print(f"  DUPLICATED x{c} in {f}: {run.splitlines()[0][:80]}")
print(f"DUPLICATED COMMENT RUNS: {dupes}")
