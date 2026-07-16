#!/usr/bin/env python3
"""foxtag_client.py — the ONE Python↔foxtag-core seam (D-337 "CI via the Python binding"; D-352).

Every Python tool that consumes the C++ core imports THIS module — never spawns the binary
directly — so binary discovery, transport, JSON decoding, and error semantics live in exactly
one place. TRANSPORT v0 = subprocess + JSON (the core's CLI); if in-process speed is ever
needed, pybind11 slots in BEHIND this same API without touching any consumer (the seam is the
function signatures below, not the transport).

MIGRATION CONTRACT (D-349): the Python implementations stay CI-authoritative until
tools/foxtag/parity_check.sh passes for the relevant producer — consumers use `core_available()`
+ fall back to their Python path, so a foxtag-less checkout keeps every gate alive.

Consumers today: check_cache_layout.py (layout backend, D-352) · rebuild_doc_indexes.py
(code-tag inventory backend, D-352). See tools/foxtag/README.md for the core itself.
"""
import json
import subprocess
from pathlib import Path

FOXTAG_BIN = Path(__file__).absolute().parent / "foxtag" / "foxtag"
_ENGINE = Path(__file__).absolute().parent.parent   # tools/foxtag_client.py -> engine root
                                                    # (.absolute() NOT .resolve() — Landmine 5)


def core_available():
    """True when the built core binary exists (build: `bash tools/foxtag/build.sh`)."""
    return FOXTAG_BIN.exists()


def _run(args, timeout=300):
    """Run the core; return (stdout, returncode) — ('' , None) on any spawn failure."""
    try:
        r = subprocess.run([str(FOXTAG_BIN)] + args, cwd=str(_ENGINE),
                           capture_output=True, text=True, timeout=timeout)
        return r.stdout, r.returncode
    except (subprocess.SubprocessError, OSError):
        return "", None


def layout(tu, names=()):
    """LAYOUT facts: {record: {size, align, straddlers:[{name,off,size}]}} ({} on failure).
    Same JSON shape as emit_record_layout.lua (parity-proven straddler-exact, D-350)."""
    out, _ = _run(["layout", str(tu)] + list(names))
    try:
        return json.loads(out) if out.strip() else {}
    except json.JSONDecodeError:
        return {}


def codegen(headers, params, call, flags=None, prelude=None):
    """CODEGEN facts (RC-A anchored probe): {instructions, branches{...}, floats, simd{...}, ...}
    or None on probe failure / RC-E vacuous (the core refuses a verdict — never green-on-nothing).
    NOTE: D-327 LIVE-PREVIEW class — pin `flags` ([BUILD]) before ever persisting these."""
    args = []
    for h in (headers if isinstance(headers, (list, tuple)) else [headers]):
        args += ["--header", h]
    args += ["--params", params, "--call", call]
    if flags:
        args += ["--flags", flags if isinstance(flags, str) else " ".join(flags)]
    if prelude:
        args += ["--prelude", prelude]
    out, rc = _run(["codegen"] + args)
    if rc != 0 or not out.strip():
        return None
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return None


def unit_at(file, line):
    """The innermost enclosing tag-block unit at file:line (the plugin-keystone query), or None."""
    out, rc = _run(["unit", str(file), str(line)])
    if rc != 0 or not out.strip() or out.strip() == "null":
        return None
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return None


def inventory():
    """The converted-unit/tag inventory as (units, tags): units=[(file, type, name, line)],
    tags=[(file, tag)] — decoded from the core's sorted parity-dump rows (identical to the
    Python collector's output; parity §2)."""
    out, rc = _run(["parity-dump"])
    units, tags = [], []
    if rc is None:
        return units, tags
    for row in out.splitlines():
        parts = row.split("|")
        if len(parts) == 5 and parts[0] == "U":
            units.append((parts[1], parts[2], parts[3], int(parts[4])))
        elif len(parts) == 3 and parts[0] == "T":
            tags.append((parts[1], parts[2]))
    return units, tags
