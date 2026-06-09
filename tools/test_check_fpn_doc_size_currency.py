#!/usr/bin/env python3
"""test_check_fpn_doc_size_currency.py — NEGATIVE self-test (teeth-proof) for check_fpn_doc_size_currency.py.

Proves the FPN-doc-size guard has TEETH + the right false-positive surface: it goes RED + names the file on
a real present-tense drift (a doc stating `FPN<64> = 24B` while the code asserts 16B), stays GREEN when the
doc matches the code (`16B`), and does NOT flag a HISTORICAL line (`was 24B, now 16B`). A guard that only
ever shows GREEN on the real tree could be silently broken (a typo in a regex, an over-tight bound that
matches nothing) and nobody would know — this is the standing proof it actually catches the drift class
without false-positiving the historical record (the M3 discipline). The canonical parse + doc scan are
pointed at a hermetic temp tree via FOXML_ENGINE (LANDMINES 5/7 — .absolute() keeps the override path).

Run: python3 tools/test_check_fpn_doc_size_currency.py   (exit 0 = teeth confirmed)
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

TOOL = Path(__file__).absolute().parent / "check_fpn_doc_size_currency.py"

# Fake engine header — the SSoT the docs are checked against (canonical = 16).
HEADER = """\
#pragma once
template <unsigned FRAC_BITS> struct FPN_Binary { __int128 v; };
static_assert(sizeof(FPN_Binary<64>) == 16, "Ship A: FPN_Binary<64> is the 16B two's-complement binary core");
"""

# (a) VIOLATION — present-tense drift: states 24B for a single FPN while the code says 16B.
VIOLATION_DOC = """\
# Field layout notes

The accounting fields are fixed-point:

```cpp
struct Position {
    FPN<F> entry_price;  // 24 bytes
};
```

In prose: `FPN<F=64>` = 24B per the hot-path discipline.
"""

# (b) CLEAN — matches the canonical 16B (the guard MUST stay GREEN; no false positive).
CLEAN_DOC = """\
# Field layout notes

The accounting fields are fixed-point:

```cpp
struct Position {
    FPN<F> entry_price;  // 16 bytes
};
```

In prose: `FPN<F=64>` = 16B per the hot-path discipline.
"""

# (c) HISTORICAL — a transition line that mentions 24B but is the origin story, NOT a live claim. The guard
#     MUST NOT flag it (M3 — never flag the historical record). Exercises both the inline `was NNB` /
#     `NN→MM` markers AND the old-layout-members window.
HISTORICAL_DOC = """\
# Field layout notes (post-Ship-A)

> HISTORICAL — the original sign-magnitude layout below was 24B, now 16B (Ship-A).

```cpp
// HISTORICAL — pre-Ship-A sign-magnitude layout (superseded).
struct FPN {
    uint64_t w[N];
    int32_t  sign;
    int32_t  _padding = 0;
};
// sizeof(FPN<64>) = 24 (unchanged)
```

Prose form of the same history: `FPN<F=64>` was 24B (sign-mag → 16B __int128).
"""


def run(root):
    env = dict(os.environ, FOXML_ENGINE=str(root))
    r = subprocess.run([sys.executable, str(TOOL)], env=env, capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def write_tree(root, doc_name, doc_body):
    (root / "FixedPoint").mkdir(parents=True, exist_ok=True)
    (root / "FixedPoint" / "FixedPointN.hpp").write_text(HEADER)
    (root / "DOCS").mkdir(parents=True, exist_ok=True)
    # clear any prior doc, then write the one under test (a real SCAN_GLOB path: DOCS/**/*.md)
    for old in (root / "DOCS").glob("*.md"):
        old.unlink()
    f = root / "DOCS" / doc_name
    f.write_text(doc_body)
    return f


def main():
    fails = 0
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)

        # (1) VIOLATION -> RED + names the file
        f = write_tree(root, "layout_notes.md", VIOLATION_DOC)
        rc, out = run(root)
        if rc != 1 or "layout_notes.md" not in out:
            print(f"  FAIL: guard did NOT catch the present-tense 24B drift / didn't name the file "
                  f"(rc={rc}, expected 1)\n{out}")
            fails += 1
        else:
            print("  PASS: guard goes RED + names layout_notes.md on the present-tense 24B drift")

        # (2) CLEAN (16B) -> GREEN (no false positive)
        write_tree(root, "layout_notes.md", CLEAN_DOC)
        rc, out = run(root)
        if rc != 0:
            print(f"  FAIL: guard false-positived on the matching-16B clean doc (rc={rc}, expected 0)\n{out}")
            fails += 1
        else:
            print("  PASS: guard stays GREEN on the matching-16B clean doc")

        # (3) HISTORICAL (was 24B, now 16B) -> NOT flagged (GREEN)
        write_tree(root, "layout_notes.md", HISTORICAL_DOC)
        rc, out = run(root)
        if rc != 0:
            print(f"  FAIL: guard flagged a HISTORICAL transition line (rc={rc}, expected 0 — M3 "
                  f"never-flag-the-record)\n{out}")
            fails += 1
        else:
            print("  PASS: guard does NOT flag the HISTORICAL `was 24B, now 16B` line (M3)")

    print(("PASS" if not fails else "FAIL") + f" -- check_fpn_doc_size_currency teeth-proof ({fails} failure(s))")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
