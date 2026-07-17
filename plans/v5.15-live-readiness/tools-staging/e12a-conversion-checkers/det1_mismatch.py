import subprocess, re
conv = subprocess.run(["grep","-rl","^// \\[FILE\\]_\\[","CoreFrameworks","Strategies","ML_Headers","MemHeaders","DataStream","Backtest","GUI","FixedPoint"],capture_output=True,text=True).stdout.split()
print(f"CENSUS: {len(conv)} converted files")
bar = re.compile(r'^\s*//\s*([=\-]{8,})\s*$')
n=0
for f in sorted(conv):
    lines = open(f).read().split("\n")
    for i in range(1, len(lines)-1):
        m1, m2 = bar.match(lines[i-1]), bar.match(lines[i+1])
        mid = lines[i].strip()
        if m1 and m2 and mid.startswith("//") and not bar.match(lines[i]) \
           and not re.match(r'^//\s*\[', mid) and mid != "//" \
           and m1.group(1)[0] != m2.group(1)[0]:
            print(f"{f}:{i+1}  {mid[:60]}"); n+=1
print(f"MISMATCHED-BAR SITES: {n}")
