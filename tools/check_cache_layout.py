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
from check_code_tag_blocks import (_line_tokens, TAG_LINE_RE,       # noqa: E402  (one grammar, reused)
                                   validate_file, load_categories)  # (selftest round-trip: writer output re-parses clean)
from check_doc_metadata import ENGINE, load_vocabulary             # noqa: E402  (path SSoT + [TAG] vocab)

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


def run_emitter_nvim(tu, names):
    """The original Lua layout emitter (headless nvim) → {record: {size, align, straddlers}}."""
    argv = ["nvim", "--headless", "--clean", "-u", "NONE", "-l", str(EMITTER), tu] + list(names)
    try:
        r = subprocess.run(argv, cwd=str(ENGINE), capture_output=True, text=True, timeout=300)
        return json.loads(r.stdout or "{}") if r.stdout.strip() else {}
    except (subprocess.SubprocessError, json.JSONDecodeError, OSError, ValueError):
        return {}


def run_emitter(tu, names, backend="auto"):
    """Layout facts via the chosen backend. `auto` (default) = the foxtag CORE when its binary
    is built, else the Lua emitter — the PARITY-GATED cutover (D-352): foxtag became eligible
    when tools/foxtag/parity_check.sh §4 passed straddler-exact on the 204-record census
    (D-350); the Lua stays as the fallback so a foxtag-less checkout keeps the gate alive.
    ONE Python↔core seam: the foxtag call routes through tools/foxtag_client.py."""
    if backend != "nvim":
        try:
            from foxtag_client import layout as foxtag_layout, core_available
            if backend == "foxtag" or core_available():
                return foxtag_layout(tu, names)
        except ImportError:
            if backend == "foxtag":
                return {}
    return run_emitter_nvim(tu, names)


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
_LAYOUT_AXES = ("SIZE", "ALIGN", "CACHE_LINES", "STRADDLE")   # canonical order (schema § STRUCT [DERIVED] axis-set)


def _fmt_straddle(straddlers):
    return "none" if not straddlers else " · ".join(f"{s['name']}@{s['off']}" for s in straddlers)


def _axis_value(cat, rec):
    """The WRITTEN value for one layout axis from a matched emitter record (the D-327 WRITTEN set —
    Itanium-ABI-fixed; NEVER the volatile codegen quartet instr/SIMD/BRANCHES)."""
    return {
        "SIZE": f"{rec['size']}B",
        "ALIGN": str(rec.get("align", "")),
        "CACHE_LINES": str(-(-rec["size"] // 64)),          # ceil(size / 64)
        "STRADDLE": _fmt_straddle(rec.get("straddlers")),
    }[cat]


def refresh_derived(text, layout):
    """REWRITE-or-INSERT each covered [STRUCT] block's LAYOUT DERIVED tags — `[SIZE]`/`[ALIGN]`/
    `[CACHE_LINES]`/`[STRADDLE]` — to match the real layout.
      - A tag ALREADY present in the block's `[DERIVED]` is REWRITTEN in place (the original behavior).
      - A tag ABSENT from it is INSERTED (canonical order) right under the `[DERIVED]` line — so an
        EMPTY `[DERIVED]` gets FILLED, not silently skipped (the D-363 reason `--fix` used to fill 0).
    IDEMPOTENT: once inserted an axis is present, so a 2nd run rewrites-in-place = a no-op (guards the
    FPN non-idempotent-`--apply` class — .E.0.8 postmortem). PURE (unit-testable with mock layout).
    Only the DERIVED (tool-owned) COMMENT tags are touched — NEVER a curated tag, NEVER a code line
    (H21/H12: layout is reported; fields are never reordered). COVERAGE-BOUNDED (D-363): a struct
    absent from `layout` has cur=None → neither rewritten nor inserted (never writes empty/garbage
    facts for an un-probed struct — that stays a C4 emitter-coverage gap, not a wrong fact).
    Returns (new_text, n_changed)."""
    lines, changed = text.split("\n"), 0
    cur = None                       # matched layout rec for the open [STRUCT], else None (coverage gate)
    d_anchor, d_lead, seen = None, "", set()   # open block's [DERIVED] line idx / its indent / axes present
    inserts = []                     # (anchor_idx, [new_lines]); applied AFTER the walk, bottom-up (index-stable)

    def _close_block():
        """Queue the missing-axis inserts for the [DERIVED] block we're leaving."""
        nonlocal changed
        if cur is not None and d_anchor is not None:
            missing = [a for a in _LAYOUT_AXES if a not in seen]
            if missing:
                inserts.append((d_anchor, [f"{d_lead}// [{a}]_[{_axis_value(a, cur)}]" for a in missing]))
                changed += len(missing)

    for i, raw in enumerate(lines):
        m = TAG_LINE_RE.match(raw)
        if not m:
            continue
        toks = _line_tokens(m.group(1))
        if not toks:
            continue
        cat = toks[0]
        if cat == "STRUCT" and len(toks) > 1:
            _close_block()                                   # defensive (a well-formed block closes at END_STRUCT)
            cur, d_anchor, seen = match_layout(toks[1], layout), None, set()
        elif cat.startswith("END_STRUCT"):
            _close_block()
            cur, d_anchor, seen = None, None, set()
        elif cur is not None and cat == "DERIVED":
            d_anchor, d_lead, seen = i, raw[:len(raw) - len(raw.lstrip())], set()   # anchor + match its indent
        elif cur is not None and d_anchor is not None and cat in _LAYOUT_AXES:
            seen.add(cat)                                    # present → rewrite in place (idempotent no-op if equal)
            new = re.sub(r"(\[" + cat + r"\]_\[)[^\]]*(\])",
                         r"\g<1>" + _axis_value(cat, cur) + r"\g<2>", raw, count=1)
            if new != raw:
                lines[i] = new
                changed += 1
    _close_block()                                           # EOF safety (malformed / missing END_STRUCT)

    for anchor_idx, new_lines in sorted(inserts, reverse=True):   # bottom-up so earlier indices stay valid
        lines[anchor_idx + 1:anchor_idx + 1] = new_lines
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
    # refresh (the 4th verb): calibration corpus for the REWRITE + INSERT paths (golden-broken →
    # must change; golden-complete → must be a no-op). Non-vacuity per calibration-corpus-discipline.
    import tempfile, os
    mock = {"X": {"size": 64, "align": 64, "straddlers": []}}   # ceil(64/64)=1 cache line; no straddle
    # (a) REWRITE — a COMPLETE [DERIVED] with STALE values → all 4 corrected IN PLACE, 0 inserted
    #     (each axis stays single — proves rewrite doesn't duplicate a present tag)
    rewrite_fx = ("// [SCHEMA]_[v1]\n// [STRUCT]_[X]\n// [DERIVED]\n"
                  "// [SIZE]_[999B]\n// [ALIGN]_[8]\n// [CACHE_LINES]_[9]\n// [STRADDLE]_[bogus]\n"
                  "// [END_STRUCT]_[X]\n")
    rw, n_rw = refresh_derived(rewrite_fx, mock)
    rw_ok = (n_rw == 4 and "[SIZE]_[64B]" in rw and "[ALIGN]_[64]" in rw
             and "[CACHE_LINES]_[1]" in rw and "[STRADDLE]_[none]" in rw
             and rw.count("[SIZE]_[") == 1 and rw.count("[STRADDLE]_[") == 1)
    # (b) INSERT — an EMPTY [DERIVED] gets the full quartet inserted (the D-363 fill-0 fix)
    empty_fx = "// [SCHEMA]_[v1]\n// [STRUCT]_[X]\n// [DERIVED]\n// [END_STRUCT]_[X]\n"
    ins, n_ins = refresh_derived(empty_fx, mock)
    ins_ok = (n_ins == 4 and "[SIZE]_[64B]" in ins and "[ALIGN]_[64]" in ins
              and "[CACHE_LINES]_[1]" in ins and "[STRADDLE]_[none]" in ins)
    # (c) IDEMPOTENCY — a 2nd --fix on the filled output is a NO-OP (the FPN non-idempotent-apply guard)
    ins2, n_ins2 = refresh_derived(ins, mock)
    idem_ok = (n_ins2 == 0 and ins2 == ins)
    # (d) COVERAGE-BOUNDEDNESS (D-363) — a struct ABSENT from layout is neither rewritten nor filled
    absent, n_absent = refresh_derived(empty_fx, {"OTHER": {"size": 32, "align": 8, "straddlers": []}})
    cov_ok = (n_absent == 0 and absent == empty_fx)
    # (e) ROUND-TRIP — the writer's output must re-parse CLEAN through the validator (no malformed grammar
    #     silently emitted into the corpus — the one-producer-N-consumers correctness gate)
    cats = load_categories()
    cv, sv = load_vocabulary()
    fd, p = tempfile.mkstemp(suffix=".hpp"); os.write(fd, ins.encode()); os.close(fd)
    rt_viols = validate_file(p, cats, cv, sv)[0] if cats else ["categories unloadable"]
    os.unlink(p)
    rt_ok = not rt_viols
    r_ok = rw_ok and ins_ok and idem_ok and cov_ok and rt_ok
    print(f"  {'✅' if rw_ok else '❌'} refresh REWRITE: stale [SIZE]/[STRADDLE] → truth ({n_rw} changed)")
    print(f"  {'✅' if ins_ok else '❌'} refresh INSERT: empty [DERIVED] → quartet filled ({n_ins} inserted)")
    print(f"  {'✅' if idem_ok else '❌'} refresh IDEMPOTENT: 2nd --fix is a no-op ({n_ins2} changed)")
    print(f"  {'✅' if cov_ok else '❌'} refresh COVERAGE-BOUND: un-probed struct untouched ({n_absent} changed)")
    print(f"  {'✅' if rt_ok else '❌'} refresh ROUND-TRIP: inserted quartet re-parses clean ({len(rt_viols)} violation(s))")
    # --- (f) ISOLATE helpers (D-363 step-2): the probe-source generator + template detection (PURE) ---
    iso_src = _isolate_probe_source("Backtest/LabelFunctions.hpp",
                                    [{"name": "Plain", "is_template": False},
                                     {"name": "Tmpl", "is_template": True}])
    iso_ok = ('#include "Backtest/LabelFunctions.hpp"' in iso_src and "using namespace tt;" in iso_src
              and "#include <cmath>" in iso_src and "sizeof(Plain)]" in iso_src
              and "sizeof(Tmpl<64>)]" in iso_src)               # non-template bare · template at F=64
    fd, tp = tempfile.mkstemp(suffix=".hpp")
    os.write(fd, b"namespace tt {\ntemplate<unsigned F> struct Tmpl { int x; };\nstruct Plain { int y; };\n}\n")
    os.close(fd)
    tmpl_ok = bool(_struct_is_template(tp, "Tmpl")) and not _struct_is_template(tp, "Plain")
    os.unlink(tp)
    r_ok = r_ok and iso_ok and tmpl_ok
    print(f"  {'✅' if iso_ok else '❌'} isolate probe-source: prelude + using-tt + sizeof(Plain)/sizeof(Tmpl<64>)")
    print(f"  {'✅' if tmpl_ok else '❌'} isolate template-detect: Tmpl=template · Plain=not")
    return ok and r_ok


# --- ISOLATE (D-363 step-2): materialize EVERY converted [STRUCT] via per-header sizeof-forcing probes.
#     `main.cpp` only lays out the structs it USES/instantiates; an isolated per-header TU with a `sizeof`
#     forcer per struct lays them ALL out — 1:1 with the binary by ABI determinism (D-321). `using namespace
#     tt;` resolves global AND tt:: names uniformly; templates instantiate at F=64 (extra params ride
#     defaults). Reuses run_emitter (one producer, D-337). ---
_ISOLATE_PRELUDE = "#include <cmath>\n#include <cstdint>\n#include <cstddef>\n"


def _struct_is_template(path, name):
    """True if `name`'s C++ decl in `path` is a template (needs <64> args to be sizeof-able)."""
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except (IOError, OSError):
        return False
    return bool(re.search(r"template\s*<[^;{]*>\s*(?:inline\s+)?(?:struct|class)\s+"
                          + re.escape(name) + r"\b", text))


def _isolate_probe_source(rel_header, structs):
    """The per-header isolated TU: prelude (RC-B std-dep hygiene) + the header + `using namespace tt;`
    + one `sizeof`-forcer per [STRUCT] (templates at F=64). sizeof forces layout with no ctor needed."""
    out = [_ISOLATE_PRELUDE, f'#include "{rel_header}"', "using namespace tt;"]
    for i, s in enumerate(structs):
        qual = f"{s['name']}<64>" if s.get("is_template") else s["name"]
        out.append(f"char _fox_probe_{i}[sizeof({qual})];")
    out.append("int main() { return 0; }")
    return "\n".join(out) + "\n"


def isolate_layouts(files, backend="auto"):
    """Materialize every converted [STRUCT] via per-header isolated sizeof-forcing probes (D-363 step-2) —
    covers the structs main.cpp under-instantiates. Returns the merged {record: {size, align, straddlers}}.
    The probe TU lives at the engine root (quoted includes + the compile_commands symlink resolve there;
    flags fall back to main.cpp's via flags_for db[1])."""
    by_header, eng = {}, ENGINE.resolve()
    for f in files:
        p = Path(f)
        if not p.exists():
            continue
        try:
            rel = str(p.resolve().relative_to(eng))
        except ValueError:
            continue                                    # outside the engine tree (schema_golden etc.) — skip
        for b in parse_struct_blocks(f):
            b["is_template"] = _struct_is_template(f, b["name"])
            by_header.setdefault(rel, []).append(b)
    merged, probe = {}, ENGINE / "_fox_isolate_probe.cpp"
    try:
        for rel_header, structs in sorted(by_header.items()):
            probe.write_text(_isolate_probe_source(rel_header, structs), encoding="utf-8")
            merged.update(run_emitter(str(probe), [s["name"] for s in structs], backend=backend) or {})
    finally:
        if probe.exists():
            probe.unlink()
    return merged


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true", help="prove the gate decision fires (non-vacuity)")
    ap.add_argument("--tu", default="main.cpp", help="the TU to dump record layouts from")
    ap.add_argument("--backend", choices=["auto", "nvim", "foxtag"], default="auto",
                    help="layout fact source: the foxtag core (parity-gated cutover, D-352) "
                         "or the Lua emitter; auto = foxtag when built, else nvim")
    ap.add_argument("--paths", nargs="*")
    ap.add_argument("--fix", action="store_true",
                    help="REFRESH mode — write the real [SIZE]/[ALIGN]/[CACHE_LINES]/[STRADDLE] into the blocks "
                         "(the tool-owned DERIVED tags only; NEVER reorders fields — H21/H12)")
    ap.add_argument("--isolate", action="store_true",
                    help="materialize EVERY converted [STRUCT] via per-header sizeof-forcing probes "
                         "(D-363 step-2: covers structs main.cpp under-instantiates), instead of --tu")
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

    layout = (isolate_layouts(files, backend=args.backend) if args.isolate
              else run_emitter(args.tu, [b["name"] for b in blocks], backend=args.backend))
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
