import subprocess, re, sys
bar_any = re.compile(r'^\s*//[=\-~]{8,}\s*$')
bar_wide = re.compile(r'^\s*//={8,}\s*$')
tagline = re.compile(r'^\s*//\s*\[')
codeish = re.compile(r'^(template|inline|struct|static|constexpr|typedef|using|#define|#include|extern|void|int|uint|bool|Money|FPN|enum|union|alignas|class )')
opener = re.compile(r'^\s*//\s*\[(FUNCTION|STRUCT|REGISTRY|ENUM|TYPE|STRATEGY)\]_\[([^\]]+)\]')
sect_start = re.compile(r'^\s*//\s*\[(COMMENT|DERIVED|REFERENCE|SUPPORTING_DOCS|END_)')

def classify(files):
    """Return {file: [(run_start0, unit)]} for TOP-of-fence runs whose next code is the unit signature."""
    out = {}
    for f in files:
        lines = open(f).read().split("\n")
        cur_unit = None; in_code = False; seen_code = False
        i = 0
        while i < len(lines):
            l = lines[i]
            m = opener.match(l)
            if m and not in_code: cur_unit = m.group(2)
            if re.match(r'^\s*//\s*\[CODE\]', l): in_code = True; seen_code = False; i += 1; continue
            if re.match(r'^\s*//\s*\[END_CODE\]', l): in_code = False; i += 1; continue
            if in_code and l.startswith("//") and not bar_any.match(l) and not tagline.match(l):
                j = i
                while j < len(lines) and lines[j].startswith("//") and not bar_any.match(lines[j]) and not tagline.match(lines[j]): j += 1
                k = j
                while k < len(lines) and (not lines[k].strip() or bar_any.match(lines[k])): k += 1
                nxt = lines[k] if k < len(lines) else ""
                if j-i >= 2 and codeish.match(nxt) and not seen_code:
                    sig = cur_unit and (cur_unit in nxt or (k+1 < len(lines) and cur_unit in lines[k+1]) or (k+2 < len(lines) and cur_unit in lines[k+2]))
                    if sig: out.setdefault(f, []).append((i, cur_unit))
                i = j
                continue
            if in_code and codeish.match(l): seen_code = True
            i += 1
    return out

def transform(f, sites, dry=False):
    lines = open(f).read().split("\n")
    report = []
    for run_start, unit in sorted(sites, reverse=True):
        # span: from run_start forward to first code or tag line (collect comments/blanks/bars)
        e = run_start
        while e < len(lines) and not codeish.match(lines[e]):
            if tagline.match(lines[e]): break
            e += 1
        if e == run_start: report.append(f"SKIP {unit}: empty span"); continue
        span = lines[run_start:e]
        # banner = comments verbatim; internal blanks -> '//'; decoration bars dropped
        items = []
        for l in span:
            if bar_any.match(l): continue
            if not l.strip(): items.append(None)
            else: items.append(l)
        while items and items[0] is None: items.pop(0)
        while items and items[-1] is None: items.pop()
        banner = ["//" if x is None else x for x in items]
        if not banner: report.append(f"SKIP {unit}: no banner content"); continue
        # remove span
        del lines[run_start:e]
        # find closer for this unit AFTER run_start
        closer_idx = None
        endre = re.compile(r'^\s*//\s*\[END_(FUNCTION|STRUCT|REGISTRY|ENUM|TYPE|STRATEGY)\]_\[' + re.escape(unit) + r'\]')
        for i2 in range(run_start, len(lines)):
            if endre.match(lines[i2]): closer_idx = i2; break
        if closer_idx is None: report.append(f"FAIL {unit}: no closer found — REVERTING file"); return None, report
        # find last [END_CODE] before closer
        endcode_idx = None
        for i2 in range(closer_idx, run_start, -1):
            if re.match(r'^\s*//\s*\[END_CODE\]', lines[i2]): endcode_idx = i2; break
        if endcode_idx is None: report.append(f"FAIL {unit}: no END_CODE before closer — REVERTING"); return None, report
        wide = lines[endcode_idx+1] if bar_wide.match(lines[endcode_idx+1]) else "//" + "="*70
        thin = wide.replace("=", "-")
        # insertion point: first section-start line after the END_CODE frame
        ins = closer_idx
        for i2 in range(endcode_idx+2, closer_idx+1):
            if sect_start.match(lines[i2]): ins = i2; break
        block = ["// [COMMENT]", thin] + banner + [wide]
        lines[ins:ins] = block
        report.append(f"OK   {unit}: moved {len(banner)} lines -> [COMMENT] @ {ins+1}")
    if not dry:
        open(f, "w").write("\n".join(lines))
    return lines, report

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    conv = subprocess.run(["grep","-rl","^// \\[FILE\\]_\\[","CoreFrameworks","Strategies","ML_Headers","MemHeaders","DataStream","Backtest","GUI","FixedPoint"],capture_output=True,text=True).stdout.split()
    conv = [f for f in conv if "RegimeDetector" not in f]
    sites = classify(conv)
    total_ok = 0
    for f in (sorted(sites) if not target else [target]):
        if f not in sites: print(f"{f}: no sites"); continue
        _, rep = transform(f, sites[f])
        print(f"== {f} ==")
        for r in rep: print("  ", r)
        total_ok += sum(1 for r in rep if r.startswith("OK"))
    print(f"\nTOTAL relocated: {total_ok}")
