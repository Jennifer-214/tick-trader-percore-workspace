#!/usr/bin/env python3
"""
Teeth-proof selftest for check_h14_no_bitfield.py (.E.1.0).

Proves the gate is NOT a vacuously-green guard: (1) it DETECTS real C++ bitfields
(would go RED on a regression), and (2) it does NOT false-positive on the tricky
look-alikes (ternaries incl. multi-line continuations, labels, access-specifiers,
enum bases, ctor-init lists, commented-out bitfields). A1's vacuity refute named
the multi-line-ternary false-positive specifically — it's covered below.

Run: python3 tools/test_check_h14_no_bitfield.py   (exit 0 = teeth proven)
"""
import importlib.util, os, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "h14", os.path.join(HERE, "check_h14_no_bitfield.py"))
h14 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(h14)

MUST_DETECT = [
    "struct S { uint32_t flags : 3; };",
    "    uint8_t mode : 2;",
    "  unsigned int x : 1;",
    "    uint16_t a : 4;   // packed",          # trailing comment stripped, still caught
    "    int : 0;",                             # anonymous alignment bitfield
    "    uint64_t ready : 1 = 0;",              # C++20 in-class init form
    "    uint32_t n : WIDTH_CONST;",            # width as a named constant
]
MUST_NOT_DETECT = [
    "    x = cond ? a : b;",                    # single-line ternary
    "        : 0;",                             # multi-line ternary continuation (no type+name)
    "    state->rolling_short.count : 0;",      # A1's member-access ternary continuation
    "public:",
    "    private:",
    "    protected:",
    "    case FOO_BAR:",
    "    default:",
    "    goto_label:",
    "enum class E : uint8_t { A, B };",         # enum base, not a bitfield
    "struct Foo : public Bar {",                # inheritance
    "    Ctor() : a_(1), b_(2) {}",             # ctor init-list
    "    // uint32_t flags : 3;  commented-out bitfield",
    "    const char* s = \"x : 3;\";",          # bitfield-looking string literal
    "    int width = 3;",
    "    std::map<int,int> m;",
    "    for (int i = 0; i < n; ++i) {",
]


def detects(snippet):
    fd, path = tempfile.mkstemp(suffix=".hpp")
    os.close(fd)
    try:
        with open(path, "w") as f:
            f.write(snippet + "\n")
        return len(h14.scan_file(path)) > 0
    finally:
        os.unlink(path)


def main():
    fails = []
    for s in MUST_DETECT:
        if not detects(s):
            fails.append(f"MISS (should be RED): {s!r}")
    for s in MUST_NOT_DETECT:
        if detects(s):
            fails.append(f"FALSE-POSITIVE (should be GREEN): {s!r}")
    if fails:
        print("[test-h14] FAIL — the gate is not trustworthy:")
        for x in fails:
            print("  " + x)
        return 1
    print(f"[test-h14] PASS — {len(MUST_DETECT)} bitfields detected, "
          f"{len(MUST_NOT_DETECT)} look-alikes correctly ignored")
    return 0


if __name__ == "__main__":
    sys.exit(main())
