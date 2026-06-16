#!/usr/bin/env python3
"""
check_h14_no_bitfield.py — H14 grep-CI (.E.1.0 §4d guard).

H14 (CLAUDE.md Hard Invariants): NO C++ bitfield syntax (`name : N`) anywhere.
Multi-bit state uses manual SHIFT_*/MASK_* + MBS_*/BITMAP_* accessors over
uint{8,16,32,64}_t storage. C++ bitfield layout / signedness / packing-order are
implementation-defined -> conflicts with memcmp identity (H12), wire byte
preservation (H9), SIMD parity (H10), cache layout (H6).

DECIDABLE RED gate (no allowlist): the codebase is 0 bitfields today (the GREEN
start); any new one fails the build. Scans engine headers/sources, strips
comments + string/char literals, and flags member declarations of the form
    <type...> <name> : <width> [= init];   (named)
    <integral-type> : <width>;             (anonymous alignment bitfield)
excluding ternaries (`?:`, incl. multi-line continuations), labels, access-
specifiers, enum bases, and base/ctor-init lists.

Exit 0 = CLEAN. Exit 1 = bitfield found (file:line printed).

Run:      python3 tools/check_h14_no_bitfield.py
Selftest: python3 tools/test_check_h14_no_bitfield.py   (teeth-proof: inject->RED, tricky->GREEN)
"""
import os, re, sys

SCAN_DIRS = ["CoreFrameworks", "Strategies", "MemHeaders", "ML_Headers",
             "FixedPoint", "DataStream", "GUI", "Backtest"]
EXTS = (".hpp", ".cpp", ".h", ".inl")

# Named bitfield: <type-tokens> <name> : <width> [= init] ;
# Requires a TYPE token AND a field NAME before the ':' (distinguishes from
# ternary `?:` continuations, labels, access-specifiers, enum bases, init lists).
# Anchored to a statement boundary (^, {, ;) so inline-struct members ARE caught
# but mid-expression colons are not; the leading token is captured + keyword-checked
# (kills `case FOO: return "x";` which, after literal-strip, looks like a member).
_NAMED = re.compile(
    r'(?:^|[{};])\s*'
    r'(?:(?:const|volatile|unsigned|signed|struct|enum|class|mutable|register)\s+)*'
    r'(?P<type0>[A-Za-z_]\w*)(?:\s*::\s*[A-Za-z_]\w*)*(?:\s*<[^;{}()]*>)?'  # type
    r'\s+[A-Za-z_]\w*'                                                      # field name
    r'\s*:\s*(?:\d+|[A-Za-z_]\w*(?:\s*[-+]\s*\d+)?)'                        # width: literal or const
    r'\s*(?:=\s*[^;]+)?;'
)
# Anonymous bitfield: <integral-type> : <width> ;
_ANON = re.compile(
    r'(?:^|[{};])\s*(?:unsigned\s+|signed\s+)?'
    r'(?:int|char|short|long|long\s+long|bool|u?int(?:8|16|32|64)_t)'
    r'\s*:\s*\d+\s*;'
)
# Statement/keyword leads that look like a member decl after literal-strip but aren't.
_KW_BLOCK = {"case", "return", "goto", "default", "switch", "if", "else",
             "for", "while", "do", "break", "continue", "using", "typedef"}


def strip_comments(text):
    """Remove /* */ (multi-line) + // comments + string/char literals, preserving
    newlines so line numbers stay correct."""
    out = []
    i, n = 0, len(text)
    in_block = in_line = False
    in_str = None
    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ''
        if in_block:
            if c == '*' and nxt == '/':
                in_block = False; i += 2; continue
            out.append('\n' if c == '\n' else ' '); i += 1; continue
        if in_line:
            if c == '\n':
                in_line = False; out.append('\n')
            i += 1; continue
        if in_str:
            if c == '\\' and nxt:
                out.append('  '); i += 2; continue
            if c == in_str:
                in_str = None
            out.append('\n' if c == '\n' else ' '); i += 1; continue
        if c == '/' and nxt == '*':
            in_block = True; i += 2; continue
        if c == '/' and nxt == '/':
            in_line = True; i += 2; continue
        if c == '"' or c == "'":
            in_str = c; out.append(' '); i += 1; continue
        out.append(c); i += 1
    return ''.join(out)


def scan_file(path):
    hits = []
    try:
        with open(path, 'r', errors='replace') as f:
            raw = f.read()
    except OSError:
        return hits
    for lineno, line in enumerate(strip_comments(raw).splitlines(), 1):
        if '?' in line:           # any ternary on the line -> not a bitfield
            continue
        flagged = any(m.group('type0') not in _KW_BLOCK
                      for m in _NAMED.finditer(line))
        if not flagged and _ANON.search(line):
            flagged = True
        if flagged:
            hits.append((lineno, line.strip()))
    return hits


def main():
    root = os.environ.get("FOXML_ENGINE") or \
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    all_hits = []
    for d in SCAN_DIRS:
        for dirpath, _, files in os.walk(os.path.join(root, d)):
            for fn in files:
                if fn.endswith(EXTS):
                    p = os.path.join(dirpath, fn)
                    for lineno, txt in scan_file(p):
                        all_hits.append((os.path.relpath(p, root), lineno, txt))
    if not all_hits:
        print("[check-h14] CLEAN — no C++ bitfield syntax (H14)")
        return 0
    print(f"[check-h14] FAIL — {len(all_hits)} C++ bitfield(s) found "
          f"(H14 forbids `name : N`; use MBS_*/BITMAP_* over uintN_t):")
    for rel, lineno, txt in all_hits:
        print(f"  {rel}:{lineno}: {txt}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
