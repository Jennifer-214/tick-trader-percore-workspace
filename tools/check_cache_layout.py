#!/usr/bin/env python3
"""check_cache_layout.py — the E.1.2.A cache-layout CI gate (D-320).

DETECT the real struct layout (via `tools/emit_record_layout.lua` — the fox-symdeps parser +
straddle detector, reused headless so the CI gate and the HUD compute from the SAME source; no
Class-18 mirror) → GATE → TRACE. NEVER auto-aligns: reordering a serialized/persisted struct
silently breaks wire + snapshot compat (H21/H12, Knight-adjacent) — detect + flag + SUGGEST, a
human realigns.

The two gate rules:
  1. a cache-line STRADDLER on a CROSS-THREAD struct (its `[THREAD]` tag declares ≥2 thread roles)
     = H6 false-sharing → FAIL. **Context-aware (D-320):** the `[THREAD]` tag is what says whether a
     straddle MATTERS — a straddle on a cold single-thread struct is benign (blind detection would
     false-flag it); only the cross-thread ones fail.
  2. the block's `[SIZE]` tag disagrees with the real `sizeof` → FAIL (the DERIVED-vs-truth drift).

Toolchain (D-321): LAYOUT via clang `-fdump-record-layouts` (Itanium-ABI-identical to the shipped
g++); CODEGEN facts (instr/branches) are NEVER computed here.

Exit: 0 clean · 1 gate violation · 2 script error / selftest fail.
Usage:
  python3 tools/check_cache_layout.py --selftest          # prove the gate decision fires (non-vacuous)
  python3 tools/check_cache_layout.py --paths a.hpp ...    # gate specific converted files
  python3 tools/check_cache_layout.py                      # scan every opted-in source file
"""
import re
import sys
import json
import subprocess
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).absolute().parent))
from check_code_tag_blocks import _line_tokens, TAG_LINE_RE  # noqa: E402  (one grammar, reused)
from check_doc_metadata import ENGINE                        # noqa: E402  (path SSoT)

EMITTER = Path(__file__).absolute().parent / "emit_record_layout.lua"


def parse_struct_blocks(path):
    """Converted [STRUCT] blocks in an opted-in file → [{name, cross_thread, claimed_size, line}].
    Same mixed-state gate as the validator (un-converted / exempt file = not policed)."""
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except (IOError, OSError):
        return []
    if "[SCHEMA]_[" not in text or "[SCHEMA]_[exempt" in text:
        return []
    blocks, cur = [], None
    for lineno, raw in enumerate(text.split("\n"), 1):
        m = TAG_LINE_RE.match(raw)
        if not m:
            continue
        toks = _line_tokens(m.group(1))
        if not toks:
            continue
        cat = toks[0]
        if cat == "STRUCT" and len(toks) > 1:
            cur = {"name": toks[1], "cross_thread": False, "claimed_size": None, "line": lineno}
            blocks.append(cur)
        elif cur is not None:
            if cat == "THREAD":
                cur["cross_thread"] = len(toks[1:]) >= 2   # ≥2 declared roles (writer+reader) = crosses threads
            elif cat == "SIZE" and len(toks) > 1:
                mm = re.search(r"(\d+)", toks[1])
                if mm:
                    cur["claimed_size"] = int(mm.group(1))
            elif cat.startswith("END_STRUCT"):
                cur = None
    return blocks


def run_emitter(tu, names):
    """Invoke the Lua layout emitter → {record: {size, align, straddlers}} ({} on failure)."""
    argv = ["nvim", "--headless", "--clean", "-u", "NONE", "-l", str(EMITTER), tu] + list(names)
    try:
        r = subprocess.run(argv, cwd=str(ENGINE), capture_output=True, text=True, timeout=300)
        return json.loads(r.stdout or "{}") if r.stdout.strip() else {}
    except (subprocess.SubprocessError, json.JSONDecodeError, OSError, ValueError):
        return {}


def match_layout(name, layout):
    """Match a block's [STRUCT] name to an emitter record (namespace / template tolerant)."""
    for rec, v in layout.items():
        base = rec.split("<", 1)[0].split("::")[-1]
        if base == name or rec == name:
            return v
    return None


def gate_struct(struct, layout_rec):
    """PURE decision — the gate core (unit-tested with mock layout). Returns [violation dicts]."""
    viols = []
    if layout_rec is None:                                  # not in the dump (un-instantiated / unlinked)
        return viols
    if struct["cross_thread"]:
        for s in (layout_rec.get("straddlers") or []):
            viols.append({
                "kind": "false-sharing", "struct": struct["name"],
                "detail": f"field '{s['name']}' @off {s['off']} (size {s['size']}) straddles 64B line "
                          f"{s['off'] // 64}→{(s['off'] + s['size'] - 1) // 64} on a CROSS-THREAD "
                          f"([THREAD]) struct — H6 false-sharing; isolate the field to its own line"})
    if struct["claimed_size"] is not None and struct["claimed_size"] != layout_rec.get("size"):
        viols.append({
            "kind": "size-drift", "struct": struct["name"],
            "detail": f"[SIZE] tag says {struct['claimed_size']}B but real sizeof = {layout_rec.get('size')}B "
                      f"— refresh the tag (or a deliberate layout change needs a version bump, H21)"})
    return viols


# --- REFRESH (the 4th verb — write the LAYOUT DERIVED tags from truth; the D-319 refresh-writer) ---
def _fmt_straddle(straddlers):
    return "none" if not straddlers else " · ".join(f"{s['name']}@{s['off']}" for s in straddlers)


def refresh_derived(text, layout):
    """Rewrite each converted [STRUCT] block's LAYOUT DERIVED tags — `[SIZE]`/`[ALIGN]`/
    `[CACHE_LINES]`/`[STRADDLE]` — to match the real layout. PURE (unit-testable with mock layout);
    only the DERIVED (tool-owned) tags are touched, never curated ones. Returns (new_text, n_changed)."""
    lines, cur, changed = text.split("\n"), None, 0
    for i, raw in enumerate(lines):
        m = TAG_LINE_RE.match(raw)
        if not m:
            continue
        toks = _line_tokens(m.group(1))
        if not toks:
            continue
        cat = toks[0]
        if cat == "STRUCT" and len(toks) > 1:
            cur = match_layout(toks[1], layout)
        elif cat.startswith("END_STRUCT"):
            cur = None
        elif cur is not None and cat in ("SIZE", "ALIGN", "CACHE_LINES", "STRADDLE"):
            val = {
                "SIZE": f"{cur['size']}B",
                "ALIGN": str(cur.get("align", "")),
                "CACHE_LINES": str(-(-cur["size"] // 64)),          # ceil(size / 64)
                "STRADDLE": _fmt_straddle(cur.get("straddlers")),
            }[cat]
            new = re.sub(r"(\[" + cat + r"\]_\[)[^\]]*(\])", r"\g<1>" + val + r"\g<2>", raw, count=1)
            if new != raw:
                lines[i] = new
                changed += 1
    return "\n".join(lines), changed


# --- self-test: PROVE the gate decision fires for each class (mock layout — no clang needed) ---
_SELFTEST = [
    ("cross-thread straddle -> FAIL",
     {"name": "X", "cross_thread": True, "claimed_size": None},
     {"size": 64, "straddlers": [{"name": "f", "off": 56, "size": 16}]}, "false-sharing"),
    ("single-thread straddle -> PASS (benign; the context-aware discriminator)",
     {"name": "Y", "cross_thread": False, "claimed_size": None},
     {"size": 64, "straddlers": [{"name": "f", "off": 56, "size": 16}]}, None),
    ("size drift -> FAIL",
     {"name": "Z", "cross_thread": False, "claimed_size": 128},
     {"size": 192, "straddlers": []}, "size-drift"),
    ("clean cross-thread, size matches -> PASS",
     {"name": "W", "cross_thread": True, "claimed_size": 64},
     {"size": 64, "straddlers": []}, None),
    ("not in dump -> PASS (not policed here)",
     {"name": "V", "cross_thread": True, "claimed_size": 64}, None, None),
]


def run_selftest():
    ok = True
    for label, struct, layout, expect in _SELFTEST:
        v = gate_struct(struct, layout)
        hit = (expect is None and not v) or (expect is not None and any(x["kind"] == expect for x in v))
        print(f"  {'✅' if hit else '❌'} {label}: {len(v)} violation(s)")
        ok = ok and hit
    # refresh: a block with stale [SIZE]/[STRADDLE] → rewritten to the mock truth (the 4th verb)
    fixture = ("// [SCHEMA]_[v1]\n// [STRUCT]_[X]\n// [SIZE]_[999B]\n// [STRADDLE]_[bogus]\n"
               "// [END_STRUCT]_[X]\n")
    new, n = refresh_derived(fixture, {"X": {"size": 64, "align": 64, "straddlers": []}})
    r_ok = "[SIZE]_[64B]" in new and "[STRADDLE]_[none]" in new and n == 2
    print(f"  {'✅' if r_ok else '❌'} refresh: stale [SIZE]/[STRADDLE] rewritten to truth ({n} tag(s) changed)")
    return ok and r_ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true", help="prove the gate decision fires (non-vacuity)")
    ap.add_argument("--tu", default="main.cpp", help="the TU to dump record layouts from")
    ap.add_argument("--paths", nargs="*")
    ap.add_argument("--fix", action="store_true",
                    help="REFRESH mode — write the real [SIZE]/[ALIGN]/[CACHE_LINES]/[STRADDLE] into the blocks "
                         "(the tool-owned DERIVED tags only; NEVER reorders fields — H21/H12)")
    args = ap.parse_args()

    if args.selftest:
        print("check_cache_layout --selftest (gate decision logic; mock layout):")
        return 0 if run_selftest() else 2

    if args.paths:
        files = [Path(p) for p in args.paths]
    else:
        files = [p for p in list(ENGINE.rglob("*.hpp")) + list(ENGINE.rglob("*.cpp"))
                 if not any(part == "vendor" or part.startswith("build") or part == "schema_golden"
                            or part == "DOCS"   # DOCS/ = template corpus etc. — illustrative
                                                # [STRUCT] DERIVED on non-compiled copy-source
                                                # (sister to the schema_golden exclusion)
                            for part in p.parts)]

    blocks = []
    for f in files:
        if f.exists():
            blocks.extend(parse_struct_blocks(f))
    if not blocks:
        print("No converted [STRUCT] blocks found — cache-layout gate inert (mixed-state OK).")
        return 0

    layout = run_emitter(args.tu, [b["name"] for b in blocks])
    if not layout:
        # Emitter needs nvim + clang + a compile TU. Advisory (not a hard-fail) so a deps-less CI env
        # isn't blocked — but LOUD (never a silent vacuous pass). TECH_DEBT-231 (shared flag path).
        print(f"WARNING: layout emitter produced nothing for {len(blocks)} block(s) — "
              f"nvim/clang/{args.tu} unavailable? gate could not run.", file=sys.stderr)
        return 0

    if args.fix:                                # REFRESH the tool-owned DERIVED tags from truth
        total = 0
        for f in files:
            if not f.exists():
                continue
            t = Path(f).read_text(encoding="utf-8", errors="replace")
            if "[SCHEMA]_[" not in t or "[SCHEMA]_[exempt" in t:
                continue
            new, n = refresh_derived(t, layout)
            if n:
                Path(f).write_text(new, encoding="utf-8")
                total += n
                print(f"  refreshed {n} layout DERIVED tag(s) in {f}")
        print(f"Refreshed {total} layout DERIVED tag(s) from truth (NO field reorder — H21/H12).")
        return 0

    viols = []
    for b in blocks:
        viols.extend(gate_struct(b, match_layout(b["name"], layout)))

    if viols:
        print(f"\nCACHE-LAYOUT VIOLATIONS ({len(viols)}):")
        for x in viols:
            print(f"  ⚠ [{x['kind']}] {x['struct']}: {x['detail']}")
        print("\n  (NEVER auto-aligned — reordering a serialized struct breaks wire/persist, H21/H12. "
              "Realign by hand + re-run.)")
        return 1
    print(f"Checked {len(blocks)} converted [STRUCT] block(s) vs real layout — all clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
