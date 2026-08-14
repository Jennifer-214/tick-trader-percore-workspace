#!/usr/bin/env python3
"""check_register_fit.py — the RC-F per-field register-fit / access-cost analyzer (D-366).

Beyond the per-STRUCT layout (size/align/straddle), a per-FIELD axis: for each field, can it be read
in a SINGLE aligned `mov`, or does it need extra ops (an unaligned load, or shift+mask for a packed
sub-word)? Cutting the access-op count is the "40→1 mov" win (Caramel's de Bruijn / `(~A&B)==B`
pattern, `Learning_cpp/projects/deep_dives`).

Rule (x86-64): a field is a **single aligned mov** iff its size is a mov width `{1,2,4,8,16,32,64}`
AND it is naturally aligned (`offset % size == 0`). Else it costs more — an unaligned/split load, or
(for a bit-packed `MBS_*`/`BITMAP_*` sub-field within a wider integer) a shift+mask.

**HONEST H14 tension (per `latency-vs-cache-decision-framework`):** the engine bit-packs DELIBERATELY
for cache footprint / L1 residency — single-mov alignment TRADES bytes for access-ops. So this tool
SHOWS the cost + flags the candidates; it NEVER auto-unpacks or auto-reorders (H21/H12: reordering a
serialized struct breaks wire/persist). The operator decides per field.

Per-field facts come from `foxtag fields` (the shared clang record-layout dump + field_size resolver —
one producer, no mirror; ADVISORY (RC-F is guidance, not a gate). Emitted for the plugin's per-field
card + operator review.

Exit: 0 (advisory — always; never a gate) · 2 selftest fail.
Usage:
  python3 tools/check_register_fit.py --selftest
  python3 tools/check_register_fit.py --paths CoreFrameworks/Order.hpp   # specific converted files
  python3 tools/check_register_fit.py                                    # every converted [STRUCT]
  python3 tools/check_register_fit.py --flagged-only                     # only fields that aren't single-mov
"""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).absolute().parent))
from check_code_tag_blocks import (engine_source_files, resolve_paths,        # noqa: E402  (corpus contract SSoT — D-393)
                                   PathResolutionError)
from check_cache_layout import (parse_struct_blocks, _isolate_probe_source,   # noqa: E402  (shared probe)
                                _struct_is_template, ENGINE)

MOV_SIZES = frozenset((1, 2, 4, 8, 16, 32, 64))    # x86-64 single-mov widths (incl. xmm 16 / ymm 32 / zmm 64)


def access_cost(off, size):
    """(verdict, note) for a field at `off` of `size` bytes. PURE — the RC-F core, unit-tested."""
    if size is None or size < 0:
        return "unknown", "size unresolved (opaque/template type)"
    if size in MOV_SIZES and off % size == 0:
        return "single-mov", None
    if size not in MOV_SIZES:
        return "multi-op", f"{size}B is not a single-mov width — split/loop load"
    return "unaligned", f"@{off} not aligned to {size} (off%{size}={off % size}) → unaligned/split load"


def isolate_fields(files):
    """Per-field facts for every converted [STRUCT] in `files` — same per-header sizeof-forcing probes
    as check_cache_layout --isolate, but through `foxtag fields` (ALL fields, not just straddlers).
    foxtag-only (the Lua emitter has no per-field mode); core_available() gates the caller."""
    from foxtag_client import fields as foxtag_fields
    by_header, eng = {}, ENGINE.resolve()
    for f in files:
        p = Path(f)
        if not p.exists():
            continue
        try:
            rel = str(p.resolve().relative_to(eng))
        except (ValueError, OSError):
            continue
        for b in parse_struct_blocks(f):
            b["is_template"] = _struct_is_template(f, b["name"])
            by_header.setdefault(rel, []).append(b)
    merged, probe = {}, ENGINE / "_fox_rcf_probe.cpp"
    try:
        for rel_header, structs in sorted(by_header.items()):
            probe.write_text(_isolate_probe_source(rel_header, structs), encoding="utf-8")
            merged.update(foxtag_fields(str(probe), [s["name"] for s in structs]) or {})
    finally:
        if probe.exists():
            probe.unlink()
    return merged


def analyze(record):
    """[(field, off, size, verdict, note)] for one foxtag `fields` record."""
    rows = []
    for f in record.get("fields", []):
        v, note = access_cost(f.get("off", 0), f.get("size"))
        rows.append((f.get("name", "?"), f.get("off", 0), f.get("size"), v, note))
    return rows


def run_selftest():
    cases = [
        ("aligned 8B @0", 0, 8, "single-mov"),
        ("aligned 4B @16", 16, 4, "single-mov"),
        ("16B Money @32", 32, 16, "single-mov"),
        ("UNALIGNED 4B @6", 6, 4, "unaligned"),      # off%4 = 2 → not single-mov
        ("UNALIGNED 8B @4", 4, 8, "unaligned"),
        ("odd 3B @0", 0, 3, "multi-op"),             # 3 not a mov width
        ("odd 48B @0", 0, 48, "multi-op"),           # a nested struct — multi-op
        ("unresolved @0", 0, -1, "unknown"),
    ]
    ok = True
    for label, off, size, expect in cases:
        v, _ = access_cost(off, size)
        hit = (v == expect)
        print(f"  {'✅' if hit else '❌'} {label}: {v} (want {expect})")
        ok = ok and hit
    return ok


def corpus_files():
    """The `derived_facts` corpus, from the CONTRACT — no longer a fourth private copy of the
    walk (D-393: membership is single-sourced, never synchronized across N enumerators)."""
    return engine_source_files(profile="derived_facts")


def emit_envelope(recs, struct_filter=None):
    """ONE `register_fit/1` toolio envelope (tables: structs · fields) — the plugin card's feed
    (one producer, N consumers). A struct filter matches exact OR base-before-`<` (the card sends
    the tag name; recs key by display name incl. template args)."""
    import subprocess
    import json as _json
    import toolio
    names = sorted(recs)
    if struct_filter:
        names = [n for n in names if n == struct_filter or n.startswith(struct_filter + "<")]
    s_rows, f_rows = [], []
    for n in names:
        s_rows.append([n, recs[n].get("size", -1), recs[n].get("align", -1)])
        for name, off, size, v, note in analyze(recs[n]):
            f_rows.append([n, name, off, size if size is not None else -1, v, note or ""])
    try:
        head = subprocess.run(["git", "-C", str(ENGINE), "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True, timeout=10).stdout.strip() or "unknown"
    except (subprocess.SubprocessError, OSError):
        head = "unknown"
    env = toolio.emit("register_fit/1", {"structs": s_rows, "fields": f_rows},
                      producer={"tool": "check_register_fit", "version": "1.0",
                                "command": "json", "args": [struct_filter or "*"]},
                      git_head=head, schema_version="1")
    print(_json.dumps(env))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--paths", nargs="*")
    ap.add_argument("--flagged-only", action="store_true", help="show only fields that are NOT single-mov")
    ap.add_argument("--json", action="store_true",
                    help="emit ONE register_fit/1 toolio envelope (the plugin card's feed)")
    ap.add_argument("--struct", help="scope to one struct (exact or base-before-<)")
    args = ap.parse_args()

    if args.selftest:
        print("check_register_fit --selftest (access-cost core; PURE):")
        core_ok = run_selftest()
        # envelope leg: a synthetic rec round-trips through toolio (the card's consumption contract)
        import toolio
        recs = {"Fix<64>": {"size": 16, "align": 16, "fields": [{"name": "v", "off": 0, "size": 16}]}}
        import io as _io
        import contextlib
        buf = _io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit_envelope(recs, "Fix")
        import json as _json
        env = _json.loads(buf.getvalue())
        rt = toolio.read(env)
        env_ok = (env["payload_schema_version"] == "register_fit/1"
                  and rt["fields"]["rows"][0][4] == "single-mov"
                  and rt["structs"]["rows"][0][0] == "Fix<64>")
        print(f"  {'✅' if env_ok else '❌'} envelope: register_fit/1 round-trips (base-< struct filter + verdict row)")
        return 0 if (core_ok and env_ok) else 2

    # Explicit paths route through the contract resolver — a missing path is rc=2, not a silent
    # empty scan (C-395 #1: this branch is where the vacuous-green lived, not the enumerator).
    if args.paths:
        try:
            files = resolve_paths(args.paths, profile="derived_facts")
        except PathResolutionError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 2
    else:
        files = corpus_files()
    recs = isolate_fields(files)
    if not recs:
        if args.json:
            # a REFUSAL, not an empty envelope: the fact SOURCE is unavailable (Class 57 —
            # distinguishable from a struct that simply has no rows)
            print("REFUSAL: no per-field facts (foxtag core unavailable, or no converted [STRUCT]s in scope)",
                  file=sys.stderr)
            return 2
        print("no per-field facts (foxtag core unavailable, or no converted [STRUCT]s in scope).")
        return 0

    if args.json:
        emit_envelope(recs, args.struct)
        return 0

    tot = {"single-mov": 0, "unaligned": 0, "multi-op": 0, "unknown": 0}
    flagged = 0
    for rec in sorted(recs):
        rows = analyze(recs[rec])
        shown = [r for r in rows if (not args.flagged_only or r[3] != "single-mov")]
        for _, _, _, v, _ in rows:
            tot[v] = tot.get(v, 0) + 1
            flagged += (v not in ("single-mov", "unknown"))
        if not shown:
            continue
        print(f"\n{rec}  (size={recs[rec].get('size')} align={recs[rec].get('align')})")
        for name, off, size, v, note in shown:
            mark = "  " if v == "single-mov" else "⚠ "
            extra = f"  — {note}" if note else ""
            print(f"  {mark}@{off:<4} {str(size) + 'B':<5} {v:<11} {name}{extra}")

    print(f"\n── RC-F summary (ADVISORY) ── {sum(tot.values())} fields across {len(recs)} structs: "
          f"{tot['single-mov']} single-mov · {tot['unaligned']} unaligned · {tot['multi-op']} multi-op · "
          f"{tot['unknown']} unresolved.")
    if flagged:
        print(f"   {flagged} field(s) cost more than a single mov — REVIEW each: align for single-mov, OR "
              f"it's a deliberate bit-pack (H14 cache-footprint tension). Operator decides; the tool never "
              f"auto-unpacks/reorders (H21/H12).")
    return 0   # ADVISORY — RC-F is guidance, never a gate


if __name__ == "__main__":
    sys.exit(main())
