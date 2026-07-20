#!/usr/bin/env python3
"""check_struct_alignment.py — guard: over-aligned (alignof>16) structs must be allocated alignment-honoring.

Knight/H21-class structural guard (TECH_DEBT-157). An `alignas(64)` struct allocated via bare
malloc/calloc/realloc — which only guarantee `alignof(max_align_t)` == 16 — lands MISALIGNED. Member
access is then UB, and aligned-SIMD / false-sharing isolation (the whole point of the alignas) silently
break. The normal -O3 build tolerates it (x86 permits misaligned scalar stores), so it hides until a
sanitizer or a real AVX-512 aligned op trips on it. Surfaced during Ship-A: RollingStats (arena malloc
fallback) + EventLoopState (test malloc) both did exactly this; both were caught only by ubsan's
first-ever run. This guard turns that convention ("allocate over-aligned types alignment-aware") into a
mechanical, no-thought check — a guard protects the whole class forever; the fix is one instance.

(a) PRIMARY (fails the build): for every `alignas(N>16)` struct/class X — declared either at struct level
    (`struct alignas(64) X`) or via an over-aligned member (`alignas(64) int head;`) — there is NO bare
    malloc/calloc/realloc allocation of X. Use aligned_alloc(alignof(X), sizeof(X)) / posix_memalign /
    C++17 `new X` (over-aligned new IS honored) / an arena allocator that takes an alignment argument.
(b) ADVISORY: each such X should carry a co-located `static_assert(alignof(X) == N)` so a future layout
    change that breaks the alignment fails to compile (generalizes the R1 offsetof asserts to alignof).
(c) PRIMARY (fails the build): byte-serialization SIZE-PIN COVERAGE (H9 wire-preservation / H12
    byte-equivalence). A type whose size is wire/persist/compare-load-bearing — it appears as `sizeof(T)`
    inside a raw byte op (`fwrite`/`fread`/`memcmp`/`SHA256`/`HMAC`) — MUST carry a `static_assert`
    mentioning `sizeof(T)`, so a silent layout change is a compile error at the pin (forcing a snapshot
    VERSION bump per H21) rather than a runtime wire/persist corruption. ENFORCES (b)'s recommendation for
    the wire/persist surface; mirrors `gen_code_map --byte-context`'s detection, but ENUMERATES the
    serialized types + verifies each is pinned (the coverage gen_code_map does not do). Only in-tree-DEFINED
    types (struct/class/using) are demanded — template params (StampT) + array consts (FEATURE_LOOKBACKS)
    have no definition and are skipped. NOT covered here (honest scope): SIMD-over-alignment, by-value-ABI,
    atomic-alignment sensitivities → see DESIGN_SPECS/meta-disciplines/struct-change-cascade-impact-tooling.md.
    The "catch what I forget when I change a core struct" guard (D-202).

Engine root via Path(__file__).absolute() — NOT .resolve() (the symlink trap; LANDMINES 5/7: tools/ is a
workspace symlink, and .resolve() would hunt for engine source under the workspace).

Exit 0 = clean; 1 = (a) violation(s). Run: python3 tools/check_struct_alignment.py
"""
import os
import re
import sys
from pathlib import Path

# .absolute() (NOT .resolve()) keeps the engine symlink path; FOXML_ENGINE override lets the teeth-proof
# self-test point the scan at a temp tree (LANDMINES 5/7).
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from foxroots import ENGINE as _FOXROOTS_ENGINE   # noqa: E402  (the ONE repo-root resolver)
# MIGRATED 2026-07-20 to the foxroots SSoT (D-375). A hand-rolled walk-up from __file__
# resolves to the WORKSPACE through the `tools/` DIRECTORY SYMLINK; foxroots adds the
# Version.hpp MARKER check + sibling recovery that makes it correct from either path.
ENGINE = _FOXROOTS_ENGINE
SCAN_DIRS = ["CoreFrameworks", "ML_Headers", "Strategies", "FixedPoint", "MemHeaders",
             "DataStream", "Backtest", "GUI", "tests"]
MAX_ALIGN_T = 16  # what malloc/calloc/realloc guarantee

STRUCT_ALIGNAS = re.compile(r'(?:struct|class)\s+alignas\s*\(\s*(\d+)\s*\)\s+(\w+)')
STRUCT_DECL = re.compile(r'(?:^|[\s;}])(?:struct|class)\s+(\w+)\b\s*(?:final\b\s*)?[:{]')
MEMBER_ALIGNAS = re.compile(r'\balignas\s*\(\s*(\d+)\s*\)')

# (c) byte-serialization size-pin coverage. The raw byte ops whose correctness depends on a type's exact
# layout (mirrors gen_code_map --byte-context's op set); the sizeof(TypeName) capture is leading-uppercase
# so sizeof(int)/sizeof(buf) primitives + lowercase locals are skipped.
BYTE_OP = re.compile(r'\b(?:fwrite|fread|memcmp|SHA256_Update|SHA256_Final|HMAC|EVP_DigestUpdate)\s*\(')
SIZEOF_TYPE = re.compile(r'\bsizeof\s*\(\s*((?:\w+::)*[A-Z]\w*)\b')
# in-tree type DEFINITIONS (struct/class/using) — a serialized name with NO definition is a template param
# or external/array const, which we do NOT demand a size-pin for. The optional alignas(...) skip is load-
# bearing: `struct alignas(64) Position` must capture "Position", not "alignas" (else an alignas wire-struct
# is a silent false-negative — caught by the by-context verification of the (c) coverage set).
TYPE_DEF = re.compile(r'\b(?:struct|class)\s+(?:alignas\s*\([^)]*\)\s+)?(\w+)\b|\busing\s+(\w+)\s*=')


def iter_files():
    for d in SCAN_DIRS:
        base = ENGINE / d
        if base.exists():
            for ext in ("*.hpp", "*.cpp", "*.h"):
                yield from sorted(base.rglob(ext))


def collect_overaligned(files):
    """name -> (N, decl_file, decl_line). Catches struct-level AND member-level alignas(>16)."""
    over = {}
    for f in files:
        try:
            lines = f.read_text(errors="replace").splitlines()
        except Exception:
            continue
        cur = None  # nearest enclosing struct/class name (heuristic; good enough for the alloc-site set)
        for i, raw in enumerate(lines, 1):
            line = raw.split("//", 1)[0]  # strip // line-comments — don't match alignas/struct in prose
            ms = STRUCT_ALIGNAS.search(line)
            if ms:
                cur = ms.group(2)
                if int(ms.group(1)) > MAX_ALIGN_T:
                    over.setdefault(cur, (int(ms.group(1)), f, i))
                continue
            md = STRUCT_DECL.search(line)
            if md:
                cur = md.group(1)
            mm = MEMBER_ALIGNAS.search(line)
            if mm and cur and int(mm.group(1)) > MAX_ALIGN_T:
                over.setdefault(cur, (int(mm.group(1)), f, i))
    return over


def collect_byte_serialized(files):
    """type base-name -> [(file, line, snippet)] for sizeof(T) on a raw-byte-op line. Mirrors
    gen_code_map --byte-context detection; here we ENUMERATE the serialized types (its coverage gap)."""
    ser = {}
    for f in files:
        try:
            lines = f.read_text(errors="replace").splitlines()
        except Exception:
            continue
        for i, raw in enumerate(lines, 1):
            line = raw.split("//", 1)[0]  # ignore commented-out / prose byte-ops
            if not BYTE_OP.search(line):
                continue
            for m in SIZEOF_TYPE.finditer(line):
                t = m.group(1).split("::")[-1]  # base name, drop namespace qualifier
                ser.setdefault(t, []).append((f, i, raw.strip()))
    return ser


def collect_defined_types(files):
    """Set of type names DEFINED in-tree (struct/class/using). A serialized name absent here is a template
    param (StampT) or an array/const (FEATURE_LOOKBACKS) — not a wire struct, so no size-pin is demanded."""
    defined = set()
    for f in files:
        try:
            text = f.read_text(errors="replace")
        except Exception:
            continue
        for m in TYPE_DEF.finditer(text):
            defined.add(m.group(1) or m.group(2))
    return defined


def has_sizeof_pin(name, full):
    """Any static_assert mentioning sizeof(name) counts (== N / % 64 == 0 / <= N / persist-bytes arithmetic).
    An explicit name-level pin is the robust form (see the Money pin at FixedPoint/FixedPointN.hpp)."""
    rx = re.compile(r'static_assert\s*\([^;]*\bsizeof\s*\(\s*(?:\w+::)*' + re.escape(name) + r'\b')
    return any(rx.search(t) for t in full.values())


def main():
    files = list(iter_files())
    full = {f: f.read_text(errors="replace") for f in files if f.exists()}
    rel = lambda p: p.relative_to(ENGINE)

    # --- (a) over-aligned bare-malloc + (b) alignof-lock advisory (only when alignas(>16) types exist) ---
    over = collect_overaligned(files)
    names = sorted(over)
    violations, missing = [], []
    if over:
        alt = "|".join(re.escape(n) for n in names)
        # bare alloc of an over-aligned type: malloc(... sizeof(T) ...) OR (T*)malloc(...)
        sizeof_alloc = re.compile(r'\b(?:malloc|calloc|realloc)\s*\([^;{]*\bsizeof\s*\(\s*(?:\w+::)*(' + alt + r')\b')
        cast_alloc = re.compile(r'\(\s*(?:\w+::)*(' + alt + r')\s*(?:<[^>;{]*>)?\s*\*\s*\)\s*(?:malloc|calloc|realloc)\s*\(')
        for f in files:
            try:
                lines = f.read_text(errors="replace").splitlines()
            except Exception:
                continue
            for i, raw in enumerate(lines, 1):
                line = raw.split("//", 1)[0]  # ignore commented-out allocations
                if not any(a in line for a in ("malloc", "calloc", "realloc")):
                    continue
                m = sizeof_alloc.search(line) or cast_alloc.search(line)
                if m:
                    violations.append((f, i, m.group(1), raw.strip()))
        has_assert = {}
        for n in names:
            rx = re.compile(r'static_assert\s*\([^;]*\balignof\s*\(\s*(?:\w+::)*' + re.escape(n) + r'\b')
            has_assert[n] = any(rx.search(t) for t in full.values())
        missing = [n for n in names if not has_assert[n]]

    # --- (c) byte-serialization size-pin coverage (H9/H12) — ENFORCING; runs even with no alignas types ---
    serialized = collect_byte_serialized(files)
    defined = collect_defined_types(files)
    in_tree = [t for t in serialized if t in defined]
    uncovered = sorted(t for t in in_tree if not has_sizeof_pin(t, full))

    # --- report ---
    print(f"check_struct_alignment: scanned {len(files)} files; {len(names)} alignas(>16) type(s); "
          f"{len(in_tree)} in-tree byte-serialized type(s).")
    if violations:
        print(f"\n  (a) VIOLATIONS — over-aligned struct via bare malloc/calloc/realloc ({len(violations)}):")
        for f, i, t, snip in violations:
            print(f"    {rel(f)}:{i}  {t} is alignas({over[t][0]}) but malloc/calloc only gives {MAX_ALIGN_T}B -> misaligned (UB)")
            print(f"        {snip}")
        print("    FIX: aligned_alloc(alignof(T), sizeof(T)) | posix_memalign | C++17 `new T` | arena-with-align")
    if missing:
        print(f"\n  (b) ADVISORY — alignas(>16) type(s) without a static_assert(alignof==N) lock ({len(missing)}):")
        for n in missing:
            N, df, dl = over[n]
            print(f"    {rel(df)}:{dl}  {n} (alignas {N}) -> add: static_assert(alignof({n}) == {N});")
    if uncovered:
        print(f"\n  (c) VIOLATIONS — byte-serialized in-tree type(s) with NO sizeof static_assert pin ({len(uncovered)}):")
        for t in uncovered:
            f0, l0, snip = serialized[t][0]
            extra = f" (+{len(serialized[t]) - 1} more site(s))" if len(serialized[t]) > 1 else ""
            print(f"    {rel(f0)}:{l0}{extra}  {t} is byte-serialized but unpinned -> a silent layout change = wire/persist break (H9/H12)")
            print(f"        {snip}")
        print(f"    FIX: add a co-located static_assert(sizeof({uncovered[0]}) == <N>) -> a layout change becomes a compile error HERE (then bump the snapshot VERSION per H21).")

    if violations or uncovered:
        print(f"\nRED - {len(violations)} over-aligned bare-malloc + {len(uncovered)} unpinned byte-serialized type(s).")
        return 1
    if not over and not in_tree:
        print("check_struct_alignment: 0 alignas(>16) + 0 in-tree byte-serialized types — nothing to guard (scan dirs missing?)")
        return 0
    print(f"\nGREEN - no over-aligned bare-malloc; all {len(in_tree)} in-tree byte-serialized type(s) size-pinned. "
          f"((b) advisory: {len(missing)} alignof lock(s) suggested.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
