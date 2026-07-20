#!/usr/bin/env python3
"""test_check_tools_inventory.py — NEGATIVE self-test: does the tool-rot guard have TEETH?

Proves check_tools_inventory.py goes RED on each violation it exists to catch — not a green-on-clean
no-op (the determinism-net §3 lesson generalized: a gate verified only by GREEN-on-clean is NOT verified).
Every injection is sandboxed + self-reverting. Per the verify-every-tool-catches-its-target discipline.

Run: python3 tools/test_check_tools_inventory.py   (exit 0 = guard has teeth).
"""
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from foxroots import ENGINE as _FOXROOTS_ENGINE   # noqa: E402  (the ONE repo-root resolver — D-375)
# FIXED 2026-07-20 (import-from-core lint widened to the os.path spelling): a hand-rolled
# walk-up from __file__ resolves to the WORKSPACE through the `tools/` DIRECTORY SYMLINK.
# This one happened to still work because it only reads workspace-side files, but it is the
# same latent shape that broke three sibling tools outright — so it migrates rather than
# getting grandfathered (the baseline is meant to SHRINK).
REPO = str(_FOXROOTS_ENGINE)
GUARD = os.path.join(REPO, "tools", "check_tools_inventory.py")
fail = 0


def run(env_extra=None):
    env = dict(os.environ)
    if env_extra:
        env.update(env_extra)
    return subprocess.run([sys.executable, GUARD], capture_output=True, text=True, env=env).returncode


def expect(label, want_red, setup, teardown, env_extra=None):
    global fail
    setup()
    try:
        red = run(env_extra) != 0
        if red == want_red:
            print(f"  ✅ {label} — guard {'RED' if red else 'GREEN'} as expected")
        else:
            print(f"  ❌ {label} — guard {'RED' if red else 'GREEN'}, expected {'RED' if want_red else 'GREEN'}")
            fail = 1
    finally:
        teardown()


print("=" * 60)
print(" check_tools_inventory SELF-TEST (does the rot-guard catch its violations?)")
print("=" * 60)

# (0) baseline — a clean tree must be GREEN, else the injections prove nothing
expect("(0) baseline clean", False, lambda: None, lambda: None)

# (1) CHECK 1 — an unenrolled tool on disk must go RED
probe = os.path.join(REPO, "tools", "_zz_selftest_unenrolled.sh")
expect("(1) unenrolled tool", True,
       lambda: open(probe, "w").close(),
       lambda: os.path.exists(probe) and os.remove(probe))

# (2) CHECK 2 — a skill citing a nonexistent tool must go RED (via a temp workspace the guard scans)
tmp = {}
_tmpdir = tempfile.mkdtemp()
try:
    skdir = os.path.join(_tmpdir, "claude-skills", "zz")
    os.makedirs(skdir)
    with open(os.path.join(skdir, "SKILL.md"), "w") as f:
        f.write("Step: run `python3 tools/_zz_ghost_nonexistent.py` to check.\n")
    red = run({"FOXML_WORKSPACE": _tmpdir}) != 0
    print(f"  {'✅' if red else '❌'} (2) broken skill->tool reference — guard {'RED' if red else 'GREEN'} as expected")
    if not red:
        fail = 1
finally:
    shutil.rmtree(_tmpdir, ignore_errors=True)

# (3) CHECK 2 via build.sh — a build.sh tool-ref to a nonexistent/untracked tool must go RED
#     (gate R2 / TD-175a: closes the build.sh:271 `[ -f tools/X.py ]` silent-skip — a renamed tool whose
#      build.sh ref isn't followed would otherwise commit GREEN; the rename-cascade apparatus-currency net).
_repo = tempfile.mkdtemp()
try:
    os.makedirs(os.path.join(_repo, "tools"))
    os.makedirs(os.path.join(_repo, "DOCS"))
    with open(os.path.join(_repo, "DOCS", "TOOLS.md"), "w") as f:
        f.write("# TOOLS\n\n| Tool | Disposition | Purpose |\n|---|---|---|\n")
    with open(os.path.join(_repo, "build.sh"), "w") as f:
        f.write('if [ -f tools/_zz_ghost_buildref.py ]; then python3 tools/_zz_ghost_buildref.py; fi\n')
    red = run({"FOXML_REPO_ROOT": _repo}) != 0
    print(f"  {'✅' if red else '❌'} (3) broken build.sh->tool reference — guard {'RED' if red else 'GREEN'} as expected")
    if not red:
        fail = 1
finally:
    shutil.rmtree(_repo, ignore_errors=True)

print()
print(" GREEN — tool-rot guard HAS TEETH." if not fail
      else " RED — the guard missed an injected violation (NO TEETH).")
sys.exit(fail)
