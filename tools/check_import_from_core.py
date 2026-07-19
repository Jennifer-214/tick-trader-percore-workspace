#!/usr/bin/env python3
"""check_import_from_core.py — the import-from-core lint (E.1.2.B 0.1 / D-372/D-375).

The "one core, no reinvention" discipline made mechanical: a `tools/*.py` that needs a repo
root MUST `from foxroots import ENGINE/WORKSPACE/MEMORY_DIR` (the SSoT resolver, with the
Version.hpp shape-check + Landmine-5 sibling recovery) instead of rolling its OWN
`Path(__file__)...parent.parent` or hardcoding a `Path("/home/...")` absolute. A roll-your-own
root is the exact anti-pattern behind the 2026-07-19 `check_meta_registry` false-`exit 2` +
the portability-dead `check_conversion_completeness` HARD gate.

Closes the straggler CLASS structurally (feedback_close_the_class_vs_migrate_every_site): a NEW
roller is a build error immediately; the existing rollers are grandfathered in
`tools/lib/import_from_core_baseline.txt` as KNOWN-PENDING (shrink the file as each migrates).

Exit codes: 0 = clean (or only baselined KNOWN-PENDING) · 1 = a NEW (non-baselined) violation · 2 = error.
Usage:
  python3 tools/check_import_from_core.py            # scan tools/
  python3 tools/check_import_from_core.py --selftest # non-vacuity teeth (planted-bad REDs, good passes)
"""
import re
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).absolute().parent))  # so `from foxroots import` resolves (Landmine 5)
from foxroots import ENGINE  # dogfood: the lint itself reads the ONE core it enforces

TOOLS_DIR = ENGINE / "tools"
BASELINE = TOOLS_DIR / "lib" / "import_from_core_baseline.txt"

# Exempt: foxroots.py DEFINES the resolver; this lint itself carries the anti-pattern strings as its
# docstring example + selftest fixtures (it imports foxroots for its real root — dogfood). check_doc_metadata
# imports foxroots + re-exports for compat (not exempt — it has no roll-own-root line to trip on).
SELF_EXEMPT = {"foxroots.py", "check_import_from_core.py"}

# VIOLATION 1 — deriving a repo-ROOT var from __file__ (…/parent.parent). Matches ENGINE / WORKSPACE /
# ROOT / REPO / MEMORY (+ _ENGINE / ENGINE_ROOT …). Does NOT match a bare `Path(__file__).parent`
# (own-dir / sys.path setup — legit).
ROLL_OWN_ROOT = re.compile(
    r"^\s*_?[A-Za-z]*(?:ENGINE|WORKSPACE|ROOT|REPO|MEMORY)[A-Za-z_]*\s*=.*Path\(\s*__file__\s*\).*parent\s*\.\s*parent"
)
# VIOLATION 2 — a hardcoded absolute repo path ($HOME-baked → dies on any clone / grid node).
HARDCODED_ABS = re.compile(r"""Path\(\s*['"]/(?:home|Users|root)/""")


def load_baseline():
    if not BASELINE.is_file():
        return set()
    return {
        ln.strip()
        for ln in BASELINE.read_text().splitlines()
        if ln.strip() and not ln.lstrip().startswith("#")
    }


def scan_file(path):
    """Return list of (lineno, kind, text) violations for one file."""
    out = []
    try:
        lines = path.read_text(errors="replace").splitlines()
    except OSError:
        return out
    for i, ln in enumerate(lines, 1):
        if ROLL_OWN_ROOT.search(ln):
            out.append((i, "roll-own-root", ln.strip()))
        elif HARDCODED_ABS.search(ln):
            out.append((i, "hardcoded-absolute", ln.strip()))
    return out


def scan_tools(tools_dir, baseline):
    """Return (new_violations, known_pending, stale_baseline)."""
    new_v, known, seen = {}, {}, set()
    for py in sorted(tools_dir.glob("*.py")):
        if py.name in SELF_EXEMPT:
            continue
        v = scan_file(py)
        if not v:
            continue
        seen.add(py.name)
        (known if py.name in baseline else new_v)[py.name] = v
    stale = sorted(baseline - seen)  # baselined files that NO LONGER violate → shrink the baseline
    return new_v, known, stale


def run():
    baseline = load_baseline()
    new_v, known, stale = scan_tools(TOOLS_DIR, baseline)
    if known:
        print(f"KNOWN-PENDING (grandfathered — migrate to `from foxroots import`): {len(known)} tool(s)")
        for name in sorted(known):
            print(f"  · {name} ({len(known[name])} site)")
    if stale:
        print(f"BASELINE STALE — these migrated; remove from {BASELINE.name}: {', '.join(stale)}")
    if new_v:
        print(f"\n❌ NEW roll-your-own-root violation(s) — import from foxroots instead:")
        for name in sorted(new_v):
            for lineno, kind, text in new_v[name]:
                print(f"  {name}:{lineno}  [{kind}]  {text}")
        return 1
    print(f"✅ import-from-core: no NEW violations ({len(known)} KNOWN-PENDING, {len(baseline)} baselined).")
    return 0


def selftest():
    """Non-vacuity: a planted roll-own-root + a hardcoded-abs must FLAG; a foxroots-importer passes."""
    import tempfile
    ok = True
    bad_root = "ENGINE = Path(__file__).absolute().parent.parent\n"
    bad_abs = 'WORKSPACE = Path("/home/someone/repo")\n'
    good = "from foxroots import ENGINE\nsys.path.insert(0, str(Path(__file__).absolute().parent))\n"
    with tempfile.TemporaryDirectory() as d:
        dp = Path(d)
        (dp / "planted_root.py").write_text(bad_root)
        (dp / "planted_abs.py").write_text(bad_abs)
        (dp / "clean_good.py").write_text(good)
        new_v, _, _ = scan_tools(dp, baseline=set())
        for want in ("planted_root.py", "planted_abs.py"):
            hit = want in new_v
            print(f"  {'✅' if hit else '❌'} planted-bad {want} is FLAGGED")
            ok = ok and hit
        clean = "clean_good.py" not in new_v
        print(f"  {'✅' if clean else '❌'} foxroots-importer clean_good.py PASSES (not flagged)")
        ok = ok and clean
    return 0 if ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.exit(selftest() if a.selftest else run())
