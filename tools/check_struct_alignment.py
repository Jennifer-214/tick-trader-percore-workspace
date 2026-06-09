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
ENGINE = Path(os.environ.get("FOXML_ENGINE") or Path(__file__).absolute().parent.parent)
SCAN_DIRS = ["CoreFrameworks", "ML_Headers", "Strategies", "FixedPoint", "MemHeaders",
             "DataStream", "Backtest", "GUI", "tests"]
MAX_ALIGN_T = 16  # what malloc/calloc/realloc guarantee

STRUCT_ALIGNAS = re.compile(r'(?:struct|class)\s+alignas\s*\(\s*(\d+)\s*\)\s+(\w+)')
STRUCT_DECL = re.compile(r'(?:^|[\s;}])(?:struct|class)\s+(\w+)\b\s*(?:final\b\s*)?[:{]')
MEMBER_ALIGNAS = re.compile(r'\balignas\s*\(\s*(\d+)\s*\)')


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


def main():
    files = list(iter_files())
    over = collect_overaligned(files)
    if not over:
        print("check_struct_alignment: found 0 alignas(>16) types — nothing to guard (scan dirs missing?)")
        return 0
    names = sorted(over)
    alt = "|".join(re.escape(n) for n in names)
    # bare alloc of an over-aligned type: malloc(... sizeof(T) ...) OR (T*)malloc(...)
    sizeof_alloc = re.compile(r'\b(?:malloc|calloc|realloc)\s*\([^;{]*\bsizeof\s*\(\s*(?:\w+::)*(' + alt + r')\b')
    cast_alloc = re.compile(r'\(\s*(?:\w+::)*(' + alt + r')\s*(?:<[^>;{]*>)?\s*\*\s*\)\s*(?:malloc|calloc|realloc)\s*\(')

    violations = []
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

    # (b) advisory: alignof static_assert present per type?
    full = {f: f.read_text(errors="replace") for f in files if f.exists()}
    has_assert = {}
    for n in names:
        rx = re.compile(r'static_assert\s*\([^;]*\balignof\s*\(\s*(?:\w+::)*' + re.escape(n) + r'\b')
        has_assert[n] = any(rx.search(t) for t in full.values())

    rel = lambda p: p.relative_to(ENGINE)
    print(f"check_struct_alignment: scanned {len(files)} files; {len(names)} alignas(>16) type(s).")

    if violations:
        print(f"\n  (a) VIOLATIONS — over-aligned struct via bare malloc/calloc/realloc ({len(violations)}):")
        for f, i, t, snip in violations:
            print(f"    {rel(f)}:{i}  {t} is alignas({over[t][0]}) but malloc/calloc only gives {MAX_ALIGN_T}B -> misaligned (UB)")
            print(f"        {snip}")
        print("    FIX: aligned_alloc(alignof(T), sizeof(T)) | posix_memalign | C++17 `new T` | arena-with-align")

    missing = [n for n in names if not has_assert[n]]
    if missing:
        print(f"\n  (b) ADVISORY — alignas(>16) type(s) without a static_assert(alignof==N) lock ({len(missing)}):")
        for n in missing:
            N, df, dl = over[n]
            print(f"    {rel(df)}:{dl}  {n} (alignas {N}) -> add: static_assert(alignof({n}) == {N});")

    if violations:
        print(f"\nRED - {len(violations)} over-aligned bare-malloc allocation(s).")
        return 1
    print(f"\nGREEN - no over-aligned bare-malloc allocations. ((b) advisory: {len(missing)} type(s) could add an alignof lock.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
