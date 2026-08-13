#!/usr/bin/env python3
"""check_toolio_kind_parity.py — the TD-258 repo-floor tooth: toolio payload kinds ⇄ plugin consumers.

The Python-side truth is tools/lib/toolio_schemas.json (toolio.py reads it, never hardcodes —
D-380/D-384). The plugin-side truth is toolio_kinds.lua's M.consumed/M.exempt tables (the
fox-symdeps consumed-kind registry; load-bearing at runtime via assert_consumed). This tool
asserts the two sets match AT THE FLOOR — so a new producer kind with no plugin surface (or a
plugin row for a kind the registry dropped) REDs a commit instead of waiting for someone to run
:checkhealth (TD-258 / the advertised-capability-never-exercised shape).

Tri-state honest (Class 57): an unreadable/unparseable side is a REFUSAL (rc 2) with the reason
named — NEVER an empty-set pass. The Lua parse is deliberately STRICT (a `M.consumed = {` /
`M.exempt = {` block closed by a `}` line at column 0, one `["kind/N"]` key per line); a
reshaped table is a parse-refusal naming this contract, not a silent zero.

Exit: 0 = parity holds · 1 = drift findings · 2 = refusal (a side could not be read).
Escape hatch for producer-first development: add the kind to M.exempt with the reason
("view rides 0.5") — the exemption is itself parity-checked (stale exemptions flag as drift).
"""
import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).absolute().parent))  # .absolute() NOT .resolve() (Landmine 5: tools/ is a symlink)
from foxroots import ENGINE  # SSoT root resolver (D-375; the import-from-core lint enforces this)

SCHEMAS_REL = Path("tools/lib/toolio_schemas.json")
KINDS_LUA_REL = Path("tools/plugins/fox-symdeps.nvim/lua/fox-symdeps/toolio_kinds.lua")


class Refusal(Exception):
    """A side could not be read/parsed — surfaced as rc 2, never an empty-set pass."""


def load_registry_kinds(root: Path):
    p = root / SCHEMAS_REL
    if not p.is_file():
        raise Refusal(f"registry unreadable: {p}")
    try:
        data = json.loads(p.read_text())
    except (ValueError, OSError) as e:
        raise Refusal(f"registry undecodable: {p} ({e})")
    if not isinstance(data, dict):
        raise Refusal(f"registry is not an object: {p}")
    return sorted(k for k in data if not k.startswith("_"))


def _lua_block_keys(text: str, marker: str, path: Path):
    """Keys of `<marker> = { ... }` closed by a bare `}` line at column 0. Strict by contract."""
    m = re.search(rf"^{re.escape(marker)}\s*=\s*\{{\s*$", text, re.MULTILINE)
    if not m:
        raise Refusal(f"{path.name}: `{marker} = {{` block not found — the strict-parse contract "
                      f"(one [\"kind/N\"] key per line, closing }} at column 0) may have been reshaped")
    tail = text[m.end():]
    end = re.search(r"^\}", tail, re.MULTILINE)
    if not end:
        raise Refusal(f"{path.name}: `{marker}` block has no closing `}}` at column 0")
    return re.findall(r'\["([^"]+)"\]', tail[:end.start()])


def load_plugin_kinds(root: Path):
    p = root / KINDS_LUA_REL
    if not p.is_file():
        raise Refusal(f"plugin kind registry unreadable: {p}")
    text = p.read_text()
    consumed = _lua_block_keys(text, "M.consumed", p)
    exempt = _lua_block_keys(text, "M.exempt", p)
    if not consumed:
        raise Refusal(f"{p.name}: M.consumed parsed to ZERO keys — refusing the empty set "
                      f"(the plugin consumes at least grammar/1; this is a parse failure, not parity)")
    return consumed, exempt


def compare(registry_kinds, consumed, exempt):
    reg = set(registry_kinds)
    findings = []
    for k in sorted(reg - set(consumed) - set(exempt)):
        findings.append(f"MISSING-CONSUMER: registry kind '{k}' has no plugin row — a producer "
                        f"with no surface (add its toolio_kinds.lua consumed row, or an exempt "
                        f"row with the reason if its view rides a later increment)")
    for k in sorted(set(consumed) - reg):
        findings.append(f"UNKNOWN-KIND: plugin consumes '{k}' but toolio_schemas.json does not "
                        f"carry it — plugin-side drift")
    for k in sorted(set(exempt) - reg):
        findings.append(f"STALE-EXEMPT: exemption for '{k}' but the registry no longer carries "
                        f"it — drop the exempt row")
    return findings


def run(root: Path) -> int:
    try:
        reg = load_registry_kinds(root)
        consumed, exempt = load_plugin_kinds(root)
    except Refusal as e:
        print(f"REFUSAL (not a clean pass): {e}")
        return 2
    findings = compare(reg, consumed, exempt)
    if findings:
        for f in findings:
            print(f"  ✗ {f}")
        print(f"toolio-kind parity: {len(findings)} finding(s) "
              f"({len(reg)} registry kinds vs {len(consumed)} consumed + {len(exempt)} exempt)")
        return 1
    print(f"toolio-kind parity OK: {len(reg)} registry kinds, every one consumed-or-exempt "
          f"({len(consumed)} consumed, {len(exempt)} exempt)")
    return 0


# ── selftest (T5: the guard proves its own non-vacuity; every tooth plants the drift it claims to catch) ──

_GOOD_JSON = {"_comment": "fixture", "grammar/1": {"tables": {}}, "findings/1": {"table": []}}
_GOOD_LUA = """local M = {}
M.consumed = {
  ["grammar/1"] = { consumer = "nodemodel", what = "fixture" },
}
M.exempt = {
  ["findings/1"] = "envelope-level",
}
return M
"""


def _plant(tmp: Path, json_obj, lua_text):
    (tmp / SCHEMAS_REL).parent.mkdir(parents=True, exist_ok=True)
    (tmp / KINDS_LUA_REL).parent.mkdir(parents=True, exist_ok=True)
    (tmp / SCHEMAS_REL).write_text(json.dumps(json_obj))
    (tmp / KINDS_LUA_REL).write_text(lua_text)


def selftest() -> int:
    teeth, failed = 0, 0

    def tooth(name, got, want):
        nonlocal teeth, failed
        teeth += 1
        if got != want:
            failed += 1
            print(f"  ✗ tooth {name}: rc {got}, wanted {want}")

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        _plant(tmp, _GOOD_JSON, _GOOD_LUA)
        tooth("clean fixture passes", run(tmp), 0)

        planted = dict(_GOOD_JSON); planted["new_kind/1"] = {"tables": {}}
        _plant(tmp, planted, _GOOD_LUA)
        tooth("planted registry kind with no consumer FIRES", run(tmp), 1)

        ghost_lua = _GOOD_LUA.replace('["grammar/1"] = { consumer = "nodemodel", what = "fixture" },',
                                      '["grammar/1"] = { consumer = "nodemodel", what = "fixture" },\n'
                                      '  ["ghost/1"] = { consumer = "nobody", what = "planted" },')
        _plant(tmp, _GOOD_JSON, ghost_lua)
        tooth("planted plugin-side ghost kind FIRES", run(tmp), 1)

        stale_lua = _GOOD_LUA.replace('["findings/1"] = "envelope-level",',
                                      '["findings/1"] = "envelope-level",\n  ["gone/1"] = "stale",')
        _plant(tmp, _GOOD_JSON, stale_lua)
        tooth("stale exemption FIRES", run(tmp), 1)

        _plant(tmp, _GOOD_JSON, _GOOD_LUA.replace("M.consumed", "M.reshaped"))
        tooth("mutilated Lua block = REFUSAL rc2, never empty-pass", run(tmp), 2)

        _plant(tmp, _GOOD_JSON, _GOOD_LUA)
        (tmp / SCHEMAS_REL).unlink()
        tooth("missing registry json = REFUSAL rc2", run(tmp), 2)

    print(f"check_toolio_kind_parity selftest: {teeth - failed}/{teeth} teeth pass")
    return 1 if failed else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", type=Path, default=ENGINE,
                    help="repo root (default: the foxroots ENGINE; overridden by the selftest fixtures)")
    ap.add_argument("--selftest", action="store_true",
                    help="prove non-vacuity: planted drift fires, mutilated inputs refuse (rc-checked)")
    args = ap.parse_args()
    sys.exit(selftest() if args.selftest else run(args.root))


if __name__ == "__main__":
    main()
