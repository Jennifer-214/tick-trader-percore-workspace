import subprocess, difflib, sys
files = sys.argv[1:]
fail = 0
for F in files:
    orig = subprocess.run(["git","show",f"HEAD:{F}"],capture_output=True,text=True).stdout
    new = open(F).read()
    cl = lambda t:[l.split("//")[0].rstrip() for l in t.split("\n") if l.split("//")[0].strip()]
    d = [x for x in difflib.unified_diff(cl(orig),cl(new),lineterm="",n=0) if x[0] in "+-" and x[:3] not in ("+++","---")]
    print(f"{F}: LOSSLESS {'PASS' if not d else 'FAIL '+str(len(d))}")
    for x in d[:6]: print("  ", x[:130])
    fail += bool(d)
sys.exit(1 if fail else 0)
