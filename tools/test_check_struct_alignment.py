#!/usr/bin/env python3
"""test_check_struct_alignment.py — NEGATIVE self-test (teeth-proof) for check_struct_alignment.py.

Proves the guard has TEETH: (a) goes RED + names the type on a real violation (an alignas(64) struct
allocated via bare malloc), and stays GREEN when the allocation honors alignment; AND (c) goes RED + names
the type on a byte-serialized struct with NO sizeof static_assert pin, and stays GREEN when pinned (the
"catch what I forget when I change a core struct" coverage guard, D-202). A guard that only ever shows
GREEN on the real tree could be silently broken (a typo in the regex, an empty scan set) and nobody would
know — this is the standing proof it actually catches both bug classes. TECH_DEBT-157 (a) + D-202 (c).

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

# (c) coverage: a byte-serialized struct (fwrite of sizeof(T)) with NO static_assert(sizeof(T)==N) — the
# guard MUST catch it (a silent layout change would be a wire/persist break, H9/H12).
VIOLATION_C = """\
#pragma once
#include <cstdio>
struct WireRecordTeethC { long long a; long long b; };
inline void persist(WireRecordTeethC* r, FILE* f) {
    fwrite(r, sizeof(WireRecordTeethC), 1, f);   // serialized but unpinned -> (c) MUST go RED
}
"""

CLEAN_C = """\
#pragma once
#include <cstdio>
struct WireRecordTeethC { long long a; long long b; };
static_assert(sizeof(WireRecordTeethC) == 16, "wire size pinned -> (c) MUST stay GREEN (no false positive)");
inline void persist(WireRecordTeethC* r, FILE* f) {
    fwrite(r, sizeof(WireRecordTeethC), 1, f);
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

        # (3) check (c): byte-serialized struct with NO sizeof pin -> RED + names the type
        f.write_text(VIOLATION_C)
        rc, out = run(root)
        if rc != 1 or "WireRecordTeethC" not in out:
            print(f"  FAIL: (c) did NOT catch the unpinned byte-serialized struct (rc={rc}, expected 1)\n{out}")
            fails += 1
        else:
            print("  PASS: (c) goes RED + names WireRecordTeethC on the unpinned byte-serialized struct")

        # (4) check (c): same struct WITH a sizeof pin -> GREEN (no false positive)
        f.write_text(CLEAN_C)
        rc, out = run(root)
        if rc != 0:
            print(f"  FAIL: (c) false-positived on the pinned byte-serialized struct (rc={rc}, expected 0)\n{out}")
            fails += 1
        else:
            print("  PASS: (c) stays GREEN on the pinned byte-serialized struct")

    print(("PASS" if not fails else "FAIL") + f" -- check_struct_alignment teeth-proof ({fails} failure(s))")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
