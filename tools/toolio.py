#!/usr/bin/env python3
"""toolio.py — the standardized tool-I/O envelope emit/read + schema-validate SSoT (E.1.2.B 0.1.5).

The ONE Python-side writer/reader of the tool-I/O envelope (D-376/D-382): a producer/gate emits
`{envelope, payload:{schema,rows}}` through `emit()`; a consumer walks it through `read()`. The
per-kind PAYLOAD schemas + the cross-cutting `findings/1` schema live as DATA in
`tools/lib/toolio_schemas.json` (D-380/D-384) — read here, NEVER hardcoded (a per-language hardcode
would be the Class-18 mirror this substrate exists to kill). The foxtag C++ core carries a
behavior-parallel emit reading the SAME registry (the `Version.hpp` model — two readers, one source,
D-382); `parity_check.sh` keeps them byte-honest.

Schema layers (the word "schema" is overloaded — see toolio_schemas.json):
  - a PAYLOAD kind (`grammar/1`) = `{tables:{name:[columns]}}`; EVERY payload kind is `{tables}`.
  - `findings/1` = the ENVELOPE-LEVEL `status.findings` entry schema, shared by EVERY kind (D-384);
    a `verdict` is `kind:"verdict"` + EMPTY payload + populated `status.findings`, NOT a payload kind.
Rows are positional lists in both payload tables and findings (the one uniform record-set row).

`schema_version` (the D-346-locked grammar version) is passed IN by the caller, derived from the
schema-doc SSoT (`check_schema_version.locked_version()`) — never hardcoded here (D-384).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).absolute().parent))  # .absolute() NOT .resolve() (Landmine 5: tools/ is a symlink)
from foxroots import ENGINE  # SSoT root resolver (E.1.2.B 0.1)

ENVELOPE_VERSION = "1.0"
_REGISTRY_PATH = ENGINE / "tools" / "lib" / "toolio_schemas.json"


class SchemaError(ValueError):
    """A payload/findings row that does not conform to its declared schema — FAIL LOUD."""


def load_registry():
    """The language-neutral schema registry (SSoT; read, never hardcoded)."""
    return json.loads(_REGISTRY_PATH.read_text())


def _validate_rows(rows, columns, where):
    n = len(columns)
    for i, row in enumerate(rows):
        if not isinstance(row, (list, tuple)) or len(row) != n:
            raise SchemaError(f"{where} row {i}: expected {n} columns {columns}, got {row!r}")


def emit(payload_schema_version, tables, *, producer, git_head, schema_version,
         findings=(), paths=(), reg=None):
    """Build a validated tool-I/O envelope.

    payload_schema_version : e.g. "grammar/1" (registry key; `kind` = the part before "/").
    tables                 : {table_name: [rows]}; rows are positional lists. The emitted per-table
                             `schema` is sourced FROM the registry (never a passed literal → no
                             self-describing drift).
    findings               : iterable of positional rows conforming to `findings/1` (empty for a
                             pure producer). Populated → `status.ok=False`, `code=1`.
    """
    reg = reg if reg is not None else load_registry()
    kind = payload_schema_version.split("/", 1)[0]
    if payload_schema_version not in reg:
        raise SchemaError(f"unknown payload_schema_version {payload_schema_version!r} "
                          f"(registry kinds: {[k for k in reg if not k.startswith('_')]})")
    declared = reg[payload_schema_version]["tables"]
    payload = {}
    for tname, rows in tables.items():
        if tname not in declared:
            raise SchemaError(f"{payload_schema_version}: table {tname!r} not in registry {list(declared)}")
        columns = declared[tname]
        _validate_rows(rows, columns, f"{payload_schema_version}.{tname}")
        payload[tname] = {"schema": list(columns), "rows": [list(r) for r in rows]}
    findings = [list(f) for f in findings]
    _validate_rows(findings, reg["findings/1"]["table"], "status.findings")
    return {
        "envelope_version": ENVELOPE_VERSION,
        "kind": kind,
        "schema_version": schema_version,
        "payload_schema_version": payload_schema_version,
        "producer": producer,
        "status": {"ok": not findings, "code": 0 if not findings else 1, "findings": findings},
        "target": {"paths": list(paths), "git_head": git_head},
        "payload": payload,
    }


def read(env):
    """Walk any envelope's payload uniformly — `{table: {schema, rows}}` for EVERY payload kind."""
    return env["payload"]


_DEMO_PRODUCER = {"tool": "toolio", "version": "0.1.0", "command": "selftest", "args": []}


def _selftest():
    """Class-51 non-vacuity: PROVE emit accepts a known-good AND fails loud on a planted-bad — a
    positive control + negative controls for a payload row, a findings row, and an unknown table."""
    reg = load_registry()
    passed = 0

    # positive control — a valid grammar/1 payload + a valid finding round-trips, schema sourced from registry
    env = emit("grammar/1",
               {"categories": [["HOT_PATH"], ["SLOW_PATH"]],
                "unit_types": [["FUNCTION", True], ["ASSERT", False]]},
               producer=_DEMO_PRODUCER, git_head="deadbeef", schema_version="v1.0",
               findings=[["f.hpp", 1, "error", "msg", "verdict"]], reg=reg)
    assert read(env)["categories"]["schema"] == ["name"], "payload schema not sourced from registry"
    assert read(env)["categories"]["rows"] == [["HOT_PATH"], ["SLOW_PATH"]]
    assert read(env)["unit_types"]["schema"] == ["name", "closable"]
    assert env["status"]["findings"] == [["f.hpp", 1, "error", "msg", "verdict"]]
    assert env["status"]["ok"] is False and env["status"]["code"] == 1  # findings → not-ok
    passed += 1
    print("  [pass] positive control: good payload + good finding accepted (schema from registry)")

    def _expect_red(label, **kw):
        nonlocal passed
        try:
            emit(reg=reg, **kw)
        except SchemaError:
            passed += 1
            print(f"  [pass] negative control: {label} REDs")
        else:
            print(f"  [FAIL] VACUOUS: {label} did NOT raise")

    _expect_red("bad payload-row arity",
                payload_schema_version="grammar/1", tables={"categories": [["A", "EXTRA"]]},
                producer=_DEMO_PRODUCER, git_head="d", schema_version="v1.0")
    _expect_red("bad findings-row arity",
                payload_schema_version="grammar/1", tables={"categories": [["A"]]},
                producer=_DEMO_PRODUCER, git_head="d", schema_version="v1.0",
                findings=[["only", "two"]])
    _expect_red("unknown table",
                payload_schema_version="grammar/1", tables={"not_a_table": [["x"]]},
                producer=_DEMO_PRODUCER, git_head="d", schema_version="v1.0")

    print(f"toolio --selftest: {passed}/4 controls passed")
    return passed == 4


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if _selftest() else 2)
    print(json.dumps(load_registry(), indent=2))  # default: introspect the registry
    sys.exit(0)
