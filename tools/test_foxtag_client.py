#!/usr/bin/env python3
"""test_foxtag_client.py — NEGATIVE self-test (teeth, D-137) for foxtag_client.py.

Proves the ONE Python↔core seam DISCRIMINATES (never a vacuous pass-through): valid core
output decodes; INVALID output (garbage JSON / malformed rows / a missing binary) degrades to
the documented empty/None shapes — gracefully, never a crash, never a fabricated dict. Runs
hermetically against stub "binaries" (in-repo temp — /tmp may be noexec, LANDMINE 7).
"""
import os
import stat
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).absolute().parent))
import foxtag_client  # noqa: E402


def _stub(dirpath, body):
    p = Path(dirpath) / "foxtag"
    p.write_text("#!/bin/sh\n" + body + "\n")
    p.chmod(p.stat().st_mode | stat.S_IEXEC)
    return p


def main():
    ok = True
    engine = Path(__file__).absolute().parent.parent
    real_bin = foxtag_client.FOXTAG_BIN

    def check(label, cond):
        nonlocal ok
        print(f"  {'✅' if cond else '❌'} {label}")
        ok = ok and cond

    with tempfile.TemporaryDirectory(dir=engine) as td:
        # 1. missing binary → core_available False; every call degrades to a REFUSAL (None) —
        #    never fabricated-empty facts (D-413/F2 rc-honesty: a failed run is not facts)
        foxtag_client.FOXTAG_BIN = Path(td) / "no_such_binary"
        check("missing binary → core_available() False", not foxtag_client.core_available())
        check("missing binary → layout() is None (refusal, not empty facts)",
              foxtag_client.layout("main.cpp") is None)
        check("missing binary → inventory() is None (refusal, not empty corpus)",
              foxtag_client.inventory() is None)
        check("missing binary → unit_at() is None", foxtag_client.unit_at("x.hpp", 1) is None)

        # 2. GARBAGE output → graceful empty/None, never a fabricated result (the RED tooth)
        foxtag_client.FOXTAG_BIN = _stub(td, "echo 'not json at all {['")
        check("garbage JSON → layout() is None (not a crash, not fabricated facts)",
              foxtag_client.layout("main.cpp") is None)
        check("garbage rows → inventory() skips them", foxtag_client.inventory() == ([], []))
        check("garbage → unit_at() is None", foxtag_client.unit_at("x.hpp", 1) is None)

        # 3. VALID output → decoded exactly (the GREEN tooth — proves 2 wasn't vacuous)
        foxtag_client.FOXTAG_BIN = _stub(
            td, "echo '{\"tt::X<64>\":{\"size\":64,\"align\":64,\"straddlers\":[]}}'")
        got = foxtag_client.layout("main.cpp")
        check("valid JSON → layout() decodes (size=64)",
              got.get("tt::X<64>", {}).get("size") == 64)

        foxtag_client.FOXTAG_BIN = _stub(
            td, "printf 'U|/e/a.hpp|STRUCT|Foo|12\\nT|/e/a.hpp|SLOW_PATH\\nBOGUS|row\\n'")
        units, tags = foxtag_client.inventory()
        check("inventory() parses U|/T| rows + drops malformed",
              units == [("/e/a.hpp", "STRUCT", "Foo", 12)] and tags == [("/e/a.hpp", "SLOW_PATH")])

        foxtag_client.FOXTAG_BIN = _stub(td, "echo 'null'; exit 1")
        check("core 'null' + rc!=0 → unit_at() is None", foxtag_client.unit_at("x.hpp", 1) is None)

        # 4. nonzero-exit codegen → None (the RC-E contract surfaces as None, never a dict)
        foxtag_client.FOXTAG_BIN = _stub(td, "echo 'VACUOUS' >&2; exit 2")
        check("codegen probe-fail/VACUOUS (exit 2) → None",
              foxtag_client.codegen("h.hpp", "int a", "f(a)") is None)

    foxtag_client.FOXTAG_BIN = real_bin
    print(f"test_foxtag_client: {'ALL OK' if ok else 'FAILURES'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
