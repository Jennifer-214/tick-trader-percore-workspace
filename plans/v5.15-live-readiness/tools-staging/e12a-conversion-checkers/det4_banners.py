import subprocess, re
conv = subprocess.run(["grep","-rl","^// \\[FILE\\]_\\[","CoreFrameworks","Strategies","ML_Headers","MemHeaders","DataStream","Backtest","GUI","FixedPoint"],capture_output=True,text=True).stdout.split()
bar = re.compile(r'^\s*//[=\-]{8,}\s*$'); tag = re.compile(r'^\s*//\s*\[')
opener = re.compile(r'^\s*//\s*\[(FUNCTION|STRUCT|REGISTRY|ENUM)\]_\[')
codeish = re.compile(r'^(template|inline|struct|static|constexpr|typedef|using|#define|#include|extern|void|int|uint|bool|Money|FPN|enum|union|alignas|class )')
na=0; nb=0; bfiles={}
for f in sorted(conv):
    lines = open(f).read().split("\n")
    for i in range(1, len(lines)-1):
        if bar.match(lines[i]) and i+1 < len(lines) and opener.match(lines[i+1]):
            j = i-1
            while j >= 0 and not lines[j].strip(): j -= 1
            run = 0
            while j >= 0 and lines[j].strip().startswith("//") and not bar.match(lines[j]) and not tag.match(lines[j]):
                run += 1; j -= 1
            if run >= 2: print(f"(a) {f}:{i+1-run}  run={run}"); na+=1
    in_code = False; i = 0
    cl = []
    for l in lines:
        if re.match(r'^\s*//\s*\[CODE\]', l): in_code = True; continue
        if re.match(r'^\s*//\s*\[END_CODE\]', l): in_code = False; continue
        if in_code: cl.append(l)
    while i < len(cl):
        if cl[i].startswith("//") and not bar.match(cl[i]) and not tag.match(cl[i]):
            j = i
            while j < len(cl) and cl[j].startswith("//") and not bar.match(cl[j]) and not tag.match(cl[j]): j += 1
            k = j
            while k < len(cl) and not cl[k].strip(): k += 1
            if j-i >= 2 and k < len(cl) and codeish.match(cl[k]):
                nb+=1; bfiles[f]=bfiles.get(f,0)+1
            i = j
        else: i += 1
print(f"(a) STRANDED-ABOVE-OPENER: {na} banners in {len(set())or ''}files-see-lines-above")
print(f"(b) IN-CODE RUNS: {nb} across {len(bfiles)} files; top:")
for f,c in sorted(bfiles.items(),key=lambda x:-x[1])[:8]: print(f"   {c:3d}  {f}")
