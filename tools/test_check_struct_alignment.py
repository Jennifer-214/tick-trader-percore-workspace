#!/usr/bin/env python3
"""test_check_struct_alignment.py — NEGATIVE self-test (teeth-proof) for check_struct_alignment.py.

Proves the alignment guard has TEETH: it goes RED + names the type on a real violation (an alignas(64)
struct allocated via bare malloc), and stays GREEN when the same allocation honors alignment. A guard
that only ever shows GREEN on the real tree could be silently broken (a typo in the regex, an empty scan
set) and nobody would know — this is the standing proof it actually catches the bug class. TECH_DEBT-157.

Run: python3 tools/test_check_struct_alignment.py   (exit 0 = teeth confirmed)
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

TOOL = Path(__file__).absolute().parent / "check_struct_alignment.py"

VIOLATION = """\
#pragma once
#include <cstdlib>
struct alignas(64) TeethProofViolator { char pad[64]; };
inline void f() {
    // BARE malloc of an alignas(64) type -> 16B alignment -> misaligned (UB). The guard MUST catch this.
    TeethProofViolator* p = (TeethProofViolator*)malloc(sizeof(TeethProofViolator));
    (void)p;
}
"""

CLEAN = """\
#pragma once
#include <cstdlib>
struct alignas(64) TeethProofViolator { char pad[64]; };
inline void f() {
    // Honors the alignment -> the guard MUST stay GREEN (no false positive).
    TeethProofViolator* p =
        (TeethProofViolator*)aligned_alloc(alignof(TeethProofViolator), sizeof(TeethProofViolator));
    (void)p;
}
"""


def run(root):
    env = dict(os.environ, FOXML_ENGINE=str(root))
    r = subprocess.run([sys.executable, str(TOOL)], env=env, capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def main():
    fails = 0
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "CoreFrameworks").mkdir()  # a real SCAN_DIR name so the tool scans it
        f = root / "CoreFrameworks" / "teeth.hpp"

        # (1) violation -> RED + names the type
        f.write_text(VIOLATION)
        rc, out = run(root)
        if rc != 1 or "TeethProofViolator" not in out:
            print(f"  FAIL: guard did NOT catch the bare-malloc violation (rc={rc}, expected 1)\n{out}")
            fails += 1
        else:
            print("  PASS: guard goes RED + names TeethProofViolator on the bare-malloc violation")

        # (2) clean (aligned_alloc) -> GREEN (no false positive)
        f.write_text(CLEAN)
        rc, out = run(root)
        if rc != 0:
            print(f"  FAIL: guard false-positived on the aligned_alloc clean case (rc={rc}, expected 0)\n{out}")
            fails += 1
        else:
            print("  PASS: guard stays GREEN on the aligned_alloc clean case")

    print(("PASS" if not fails else "FAIL") + f" -- check_struct_alignment teeth-proof ({fails} failure(s))")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
