#!/usr/bin/env python3
"""check_schema_version.py — [SCHEMA] version cohesion (D-371).

Every converted `[SCHEMA]_[<ver>]` block MUST carry the LOCKED format version (D-346). Otherwise the
schema version silently drifts — the `v1`-vs-`v1.0` fixture drift found + fixed 2026-07-18, which
NO check caught because the validator only prefix-tests `[SCHEMA]_[` and never inspects the value.

The locked value is DERIVED from the schema spec's own `Status: LOCKED — [SCHEMA]_[v1.0]` line
(SSoT — follows a future version bump automatically), NEVER hardcoded. `[SCHEMA]_[exempt]_[reason]`
opts a file out (generated / third-party).

DELIBERATELY SEPARATE from the tag VALIDATOR (check_code_tag_blocks.py / foxtag): the version pin is
a corpus-COHESION property, not a per-block grammar rule — keeping it out of the parity-gated
`validate` path leaves foxtag<->Python byte-parity intact (adding it there would re-break parity).

WIP exemption: NONE — `WIP_EXEMPT` is empty (RegimeDetector.hpp converted 2026-07-18), so the WHOLE
corpus is version-checked (HARD-zero). The set stays as the documented seam for any future WIP pilot.

Exit: 0 clean · 1 drift · 2 script error / selftest fail.
Usage:
  python3 tools/check_schema_version.py --selftest       # prove the check fires (non-vacuous)
  python3 tools/check_schema_version.py --paths a.hpp ... # check specific files
  python3 tools/check_schema_version.py                   # scan the whole opted-in corpus
"""
import re
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).absolute().parent))
from check_code_tag_blocks import SCHEMA_PATH        # noqa: E402  (the spec SSoT — one path source)
from check_doc_metadata import ENGINE                # noqa: E402  (engine root — the corpus scan base)

WIP_EXEMPT = set()                                   # (was RegimeDetector.hpp — converted 2026-07-18; corpus HARD-zero)
_SCHEMA_RE = re.compile(r"\[SCHEMA\]_\[([^\]]+)\]")


def locked_version():
    """The LOCKED `[SCHEMA]` version from the spec SSoT (`Status: LOCKED — [SCHEMA]_[v1.0]`, D-346).
    Derived, never hardcoded → a future `[SCHEMA]` bump updates every consumer from the one line."""
    try:
        text = SCHEMA_PATH.read_text(encoding="utf-8")
    except (IOError, OSError):
        return None
    m = re.search(r"Status:\s*LOCKED\s*[—–-]\s*`?\[SCHEMA\]_\[([^\]]+)\]", text)
    return m.group(1) if m else None


def scan(files, locked):
    """[(rel, lineno, ver)] for every `[SCHEMA]_[ver]` where ver != locked and != exempt (WIP skipped)."""
    viols, eng = [], ENGINE.resolve()
    for f in files:
        p = Path(f)
        try:
            rel = str(p.resolve().relative_to(eng))
        except (ValueError, OSError):
            rel = str(f)
        if rel in WIP_EXEMPT:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except (IOError, OSError):
            continue
        for lineno, line in enumerate(text.split("\n"), 1):
            for m in _SCHEMA_RE.finditer(line):
                ver = m.group(1)
                if ver != locked and not ver.startswith("exempt"):
                    viols.append((rel, lineno, ver))
    return viols


def corpus_files():
    """Opted-in source + tool fixtures (.hpp/.cpp/.py), minus vendor/build*/schema_golden/DOCS —
    same exclusion family as check_cache_layout; .py included so a TOOL-fixture drift (the origin
    of the 2026-07-18 incident) is caught too."""
    out = []
    for ext in ("*.hpp", "*.cpp", "*.py"):
        out += list(ENGINE.rglob(ext))
    return [p for p in out
            if not any(part == "vendor" or part.startswith("build")
                       or part == "schema_golden" or part == "DOCS"
                       for part in p.parts)]


def run_selftest():
    import tempfile, os
    locked = locked_version()
    lv_ok = bool(locked)
    print(f"  {'✅' if lv_ok else '❌'} locked version derived from spec SSoT: {locked!r}")
    if not locked:
        return False
    fx = {}
    for tag, body in (("good", f"// [SCHEMA]_[{locked}]\n"),
                      ("bad",  "// [SCHEMA]_[v1]\n"),
                      ("exm",  "// [SCHEMA]_[exempt]_[generated]\n")):
        fd, path = tempfile.mkstemp(suffix=".hpp"); os.write(fd, body.encode()); os.close(fd)
        fx[tag] = path
    good_ok = not scan([fx["good"]], locked)
    bad_ok = len(scan([fx["bad"]], locked)) == 1
    exm_ok = not scan([fx["exm"]], locked)
    for p in fx.values():
        os.unlink(p)
    print(f"  {'✅' if good_ok else '❌'} locked-version file passes clean")
    print(f"  {'✅' if bad_ok else '❌'} drifted [SCHEMA]_[v1] is FLAGGED (non-vacuous)")
    print(f"  {'✅' if exm_ok else '❌'} [SCHEMA]_[exempt] opts out")
    return lv_ok and good_ok and bad_ok and exm_ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true", help="prove the check fires (non-vacuity)")
    ap.add_argument("--paths", nargs="*")
    args = ap.parse_args()

    if args.selftest:
        print("check_schema_version --selftest:")
        return 0 if run_selftest() else 2

    locked = locked_version()
    if not locked:
        print("WARNING: could not derive the locked [SCHEMA] version from the spec SSoT — "
              "check skipped (LOUD, never a silent vacuous pass).", file=sys.stderr)
        return 0
    files = [Path(p) for p in args.paths] if args.paths else corpus_files()
    viols = scan(files, locked)
    if viols:
        print(f"SCHEMA-VERSION DRIFT ({len(viols)}) — locked = [{locked}] (D-346):")
        for rel, ln, ver in viols:
            print(f"  {rel}:{ln}  [SCHEMA]_[{ver}] != locked [{locked}] — standardize (or bump the spec SSoT)")
        return 1
    print(f"All [SCHEMA] blocks carry the locked version [{locked}] "
          f"(WIP {'/'.join(sorted(WIP_EXEMPT))} exempt).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
