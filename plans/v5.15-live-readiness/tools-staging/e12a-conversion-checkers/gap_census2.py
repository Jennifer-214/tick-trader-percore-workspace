import subprocess, re
conv = subprocess.run(["grep","-rl","^// \\[FILE\\]_\\[","CoreFrameworks","Strategies","ML_Headers","MemHeaders","DataStream","Backtest","GUI","FixedPoint"],capture_output=True,text=True).stdout.split()
conv = [f for f in conv if "RegimeDetector" not in f]
tot_a = tot_h = tot_d = tot_c = tot_r = 0
rows = []
for f in sorted(conv):
    lines = open(f).read().split("\n")
    text = "\n".join(lines)
    in_code = []
    icd = 0
    for l in lines:
        if re.match(r'^\s*//\s*\[CODE\]', l): icd += 1
        in_code.append(icd > 0)
        if re.match(r'^\s*//\s*\[END_CODE\]', l): icd = max(0, icd - 1); in_code[-1] = True
    a = 0
    for i, l in enumerate(lines):
        if re.match(r'^\s*static_assert\s*\(', l) and not in_code[i]:
            if "[ASSERT]" not in "\n".join(lines[max(0,i-3):i]): a += 1
    h = 0
    thin = re.compile(r'^\s*//-{8,}\s*$')
    for i in range(1, len(lines)-1):
        if thin.match(lines[i-1]) and thin.match(lines[i+1]):
            mid = lines[i].strip()
            if mid.startswith("//") and not re.match(r'^//\s*\[', mid) and mid != "//" and len(mid) > 4:
                h += 1
    d = 0
    for m in re.finditer(r'^// \[STRUCT\]_\[([^\]]+)\]', text, re.M):
        nm = m.group(1)
        tail = re.search(r'\[END_CODE\](.*?)\[END_STRUCT\]_\[' + re.escape(nm) + r'\]', text[m.start():], re.S)
        if tail and "[DERIVED]" not in tail.group(1): d += 1
    c = 0
    for m in re.finditer(r'^// \[REGISTRY\]_\[([^\]]+)\]', text, re.M):
        orient = text[m.start():m.start()+2500].split("[CODE]")[0]
        if "[COLUMN]" not in orient: c += 1
    n_defs = 0
    for i, l in enumerate(lines):
        if re.match(r'^#define FOREACH_[A-Z_0-9]+\(X\)', l) and not in_code[i]: n_defs += 1
    r = max(0, n_defs)
    tot_a += a; tot_h += h; tot_d += d; tot_c += c; tot_r += r
    if a+h+d+c+r: rows.append((a+h+d+c+r, f, a, h, d, c, r))
rows.sort(reverse=True)
print(f"{'TOT':>4} {'assert':>6} {'heading':>7} {'noDER':>5} {'noCOL':>5} {'orphREG':>7}  file")
for t, f, a, h, d, c, r in rows[:20]: print(f"{t:>4} {a:>6} {h:>7} {d:>5} {c:>5} {r:>7}  {f}")
print(f"... ({len(rows)} files with gaps; {len(conv)-len(rows)} clean)")
print(f"\nTRUE totals: file-scope untagged asserts {tot_a} · bare headings {tot_h} · structs w/o DERIVED {tot_d} · registries w/o COLUMN {tot_c} · unblocked FOREACH {tot_r}")
