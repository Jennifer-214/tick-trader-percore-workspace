import subprocess, re, sys
conv = subprocess.run(["grep","-rl","^// \\[FILE\\]_\\[","CoreFrameworks","Strategies","ML_Headers","MemHeaders","DataStream","Backtest","GUI","FixedPoint"],capture_output=True,text=True).stdout.split()
bar = re.compile(r'^\s*//[=\-~]{8,}\s*$'); tag = re.compile(r'^\s*//\s*\[')
codeish = re.compile(r'^(template|inline|struct|static|constexpr|typedef|using|#define|#include|extern|void|int|uint|bool|Money|FPN|enum|union|alignas|class )')
opener = re.compile(r'^\s*//\s*\[(FUNCTION|STRUCT|REGISTRY|ENUM|TYPE|STRATEGY)\]_\[([^\]]+)\]')
top_unit, top_other, mid = [], [], []
for f in sorted(conv):
    if "RegimeDetector" in f: continue   # her pilot WIP — never touch
    lines = open(f).read().split("\n")
    cur_unit = None; in_code = False; fence_start = None; seen_code_in_fence = False
    for idx, l in enumerate(lines):
        m = opener.match(l)
        if m and not in_code: cur_unit = m.group(2)
        if re.match(r'^\s*//\s*\[CODE\]', l): in_code = True; seen_code_in_fence = False; continue
        if re.match(r'^\s*//\s*\[END_CODE\]', l): in_code = False; continue
        if not in_code: continue
        if codeish.match(l): seen_code_in_fence = True
    # second pass: enumerate runs with position info
    cur_unit = None; in_code = False; seen_code = False
    i = 0
    while i < len(lines):
        l = lines[i]
        m = opener.match(l)
        if m and not in_code: cur_unit = m.group(2)
        if re.match(r'^\s*//\s*\[CODE\]', l): in_code = True; seen_code = False; i += 1; continue
        if re.match(r'^\s*//\s*\[END_CODE\]', l): in_code = False; i += 1; continue
        if in_code and l.startswith("//") and not bar.match(l) and not tag.match(l):
            j = i
            while j < len(lines) and lines[j].startswith("//") and not bar.match(lines[j]) and not tag.match(lines[j]): j += 1
            k = j
            while k < len(lines) and (not lines[k].strip() or bar.match(lines[k])): k += 1
            nxt = lines[k] if k < len(lines) else ""
            if j-i >= 2 and codeish.match(nxt):
                unit_sig = cur_unit and (cur_unit in nxt or (k+1 < len(lines) and cur_unit in lines[k+1]) or (k+2 < len(lines) and cur_unit in lines[k+2]))
                rec = (f, i+1, j-i, cur_unit, lines[i][:64], nxt[:48])
                if not seen_code:
                    (top_unit if unit_sig else top_other).append(rec)
                else:
                    mid.append(rec)
            i = j
            continue
        if in_code and codeish.match(l): seen_code = True
        i += 1
print(f"== TOP-OF-FENCE, next code IS the unit signature (RELOCATE candidates): {len(top_unit)} ==")
for r in top_unit: print(f"  {r[0]}:{r[1]} run={r[2]} unit={r[3]}\n      {r[4]}")
print(f"\n== TOP-OF-FENCE, next code is a DIFFERENT sub-part (default STAY): {len(top_other)} ==")
for r in top_other: print(f"  {r[0]}:{r[1]} run={r[2]} unit={r[3]} next={r[5]}\n      {r[4]}")
print(f"\n== MID-BODY (STAY per D-326): {len(mid)} across {len(set(r[0] for r in mid))} files ==")
