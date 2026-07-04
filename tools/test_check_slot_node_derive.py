#!/usr/bin/env python3
"""Negative self-test (teeth) for check_slot_node_derive.py (D-137).

Proves the guard: (1) goes RED + names the site on an injected open-coded slot→node
derive; (2) stays GREEN when the derive routes through Sharded_SlotNode; (2b) GREEN on a
`// SLOT_DERIVE_OK` grandfather marker; (3) goes RED on a vacuous 0-file scan (the symlink
trap). A guard that is only ever GREEN could be silently broken.

Drives the guard against a throwaway CoreFrameworks tree via the FOXML_ENGINE override.
"""
import os
import subprocess
import sys
import tempfile
import pathlib

GUARD = pathlib.Path(__file__).absolute().parent / "check_slot_node_derive.py"


def run(engine_dir):
    return subprocess.run(
        [sys.executable, str(GUARD)],
        env={**os.environ, "FOXML_ENGINE": str(engine_dir)},
        capture_output=True, text=True,
    )


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        cf = root / "CoreFrameworks"
        cf.mkdir()
        inj = cf / "inject.hpp"

        inj.write_text("inline int f(int slot,int p){ int node_id = slot >> 1; return node_id; }\n")
        r = run(root)
        assert r.returncode == 1, f"(1) expected RED on injected derive, got {r.returncode}\n{r.stdout}{r.stderr}"
        assert "inject.hpp" in r.stdout, f"(1) guard did not name the violating file\n{r.stdout}"
        print("  ✓ (1) RED + names the file on injected `slot >> 1`")

        inj.write_text("inline int f(int slot,int p){ int node_id = Sharded_SlotNode(slot,p); return node_id; }\n")
        r = run(root)
        assert r.returncode == 0, f"(2) expected GREEN on routed derive, got {r.returncode}\n{r.stdout}{r.stderr}"
        print("  ✓ (2) GREEN when routed through Sharded_SlotNode")

        inj.write_text("inline int f(int slot,int p){ int node_id = slot >> 1;  // SLOT_DERIVE_OK: test\n return node_id; }\n")
        r = run(root)
        assert r.returncode == 0, f"(2b) expected GREEN on marked derive, got {r.returncode}\n{r.stdout}{r.stderr}"
        print("  ✓ (2b) GREEN on `// SLOT_DERIVE_OK` grandfather")

    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        (root / "CoreFrameworks").mkdir()  # empty → 0 *.hpp
        r = run(root)
        assert r.returncode == 1, f"(3) expected RED on vacuous scan, got {r.returncode}\n{r.stdout}{r.stderr}"
        assert "VACUOUS" in (r.stdout + r.stderr), f"(3) guard passed vacuously\n{r.stdout}{r.stderr}"
        print("  ✓ (3) RED on vacuous 0-file scan")

    print("✅ check_slot_node_derive teeth verified (RED on violation · GREEN on clean/marked · RED on vacuous)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as e:
        print(f"✘ SELF-TEST FAILED: {e}", file=sys.stderr)
        sys.exit(1)
