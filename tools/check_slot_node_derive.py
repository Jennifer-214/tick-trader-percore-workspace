#!/usr/bin/env python3
"""check_slot_node_derive.py — close the slot→node derive class (D-294/D-295/D-296, Y1).

The logical node that owns a portfolio slot is derived by `Sharded_SlotNode(slot, partial_on)`
(CoreFrameworks/ControllerEventLoop.hpp). Open-coding that derive — `slot>>1`, `slot>>partial`,
`idx>>1`, `partial ? (slot>>1) : slot` — is the drift class that produced the :856 bug (an
ungated `slot>>1` that HALVED the node in single-position mode). Routing every site through the
single accessor closes the class; this guard keeps it closed — a NEW open-coded slot→node derive
in the engine core is a build-time failure. Use `Sharded_SlotNode`.

Scope: CoreFrameworks/ (the engine spine). GUI/ is OUT of scope — its display-only derives are
grandfathered pending the E-series GUI decouple (D-295); route them through the accessor when
that ship rewrites them.

Sanctioned (skipped): any line marked `// SLOT_DERIVE_OK` (the accessor's own definition +
any documented exception); comment text.

Exit 0 = clean; exit 1 = a new open-coded derive, a vacuous scan, or a failed self-test.
"""
import os
import re
import sys
import pathlib

# Engine root via .absolute() — NOT .resolve(): tools/ is a symlink to the workspace, so
# .resolve() would follow it to the stub CoreFrameworks and vacuously pass (LANDMINES 5/7).
# FOXML_ENGINE override lets an out-of-tree caller point at the engine explicitly.
ENGINE = pathlib.Path(os.environ.get("FOXML_ENGINE") or pathlib.Path(__file__).absolute().parent.parent)
SCAN_DIRS = ["CoreFrameworks"]
OK_MARK = "SLOT_DERIVE_OK"

# a slot/idx-named var right-shifted by 1 or by a `partial*` flag = a slot→node derive.
# keys on the VAR NAME (…slot / …idx) so unrelated `x >> n` bit-ops don't false-positive.
DERIVE = re.compile(r'\b\w*(?:slot|idx)\b\s*>>\s*(?:1\b|\(u?int\d+_t\)\s*partial\w*|partial\w*)',
                    re.IGNORECASE)


def strip_comment(line: str) -> str:
    i = line.find("//")
    return line if i < 0 else line[:i]


def main() -> int:
    # non-vacuity self-test 1 (Class-51 self-defense): the regex MUST detect the canonical forms…
    for probe in ("slot >> (uint32_t)partial_on", "idx >> 1", "partial_on ? (slot >> 1) : slot"):
        if not DERIVE.search(probe):
            print(f"✘ SLOT-DERIVE self-test FAILED — regex cannot detect `{probe}`", file=sys.stderr)
            return 1
    # …and MUST NOT trip on unrelated right-shifts of non-slot/idx vars (false-positive teeth).
    for clean in ("order_id >> 60", "flags >> 2", "hash >> 32"):
        if DERIVE.search(clean):
            print(f"✘ SLOT-DERIVE self-test FAILED — regex false-positives on `{clean}`", file=sys.stderr)
            return 1

    fails = []
    scanned_files = 0
    for d in SCAN_DIRS:
        for f in sorted((ENGINE / d).rglob("*.hpp")):
            scanned_files += 1
            for n, raw in enumerate(f.read_text(errors="replace").splitlines(), 1):
                if OK_MARK in raw:
                    continue
                if DERIVE.search(strip_comment(raw)):
                    fails.append((f.relative_to(ENGINE), n, raw.strip()))

    # non-vacuity self-test 2: scanning zero files means a broken path (the symlink trap), NOT clean.
    if scanned_files == 0:
        print(f"✘ SLOT-DERIVE guard VACUOUS — 0 files under {ENGINE}/CoreFrameworks "
              f"(symlink/path bug?). Refusing to pass.", file=sys.stderr)
        return 1

    if fails:
        print(f"✘ SLOT-DERIVE guard: {len(fails)} open-coded slot→node derive(s) in the engine core "
              f"— use Sharded_SlotNode(slot, partial_on):")
        for path, n, txt in fails:
            print(f"    {path}:{n}  {txt}")
        print("  (a legit exception carries a trailing `// SLOT_DERIVE_OK: <reason>`.)")
        return 1

    print(f"✅ SLOT-DERIVE guard clean — {scanned_files} CoreFrameworks headers scanned; "
          f"all slot→node derives route through Sharded_SlotNode.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
