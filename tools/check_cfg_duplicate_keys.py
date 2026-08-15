#!/usr/bin/env python3
"""check_cfg_duplicate_keys.py — a cfg key may appear AT MOST ONCE per file.

WHY THIS EXISTS (codified 2026-08-15, from the i-class GUI-persistence sweep):
The operator's `engine.cfg` carried THREE duplicated keys — `partial_exit_enabled`
(x3), `node_1_offset_stddev_mult` (x2), and **`node_3_stop_loss_pct` (x2)**. A
duplicated key is not cosmetic here, because the two sides of the cfg round-trip
disagree about which occurrence is authoritative:

  READER  `ControllerConfig_Load` (CoreFrameworks/ControllerConfig.hpp) walks the file
          line by line; every key-match does a plain `cfg.name = <parsed>; continue;`
          where `continue` advances to the NEXT FILE LINE. Every occurrence assigns.
          => the LAST occurrence wins.

  WRITER  `cfg_write_field` (GUI/SettingsPanel.hpp) does a line-anchored search and
          `break`s on the first hit, rewriting that line in place.
          => the FIRST occurrence is edited.

So on a duplicated key the GUI writes line N, the engine reads line M>N, and the
edit is **SILENTLY INERT**. On `node_3_stop_loss_pct` that is a capital control the
operator believes she changed and did not. Nothing detected this: the parser has no
duplicate check, the writer has none, and no CI tool covered cfg-key uniqueness
(`check_cfg_key_prefix_drift.py` covers per-node PREFIX drift, not intra-file
duplication; `check_field_name_uniqueness.py` covers registry field names, not cfg
file contents).

This guard is the detection half. It does NOT pick a winner — resolving a duplicate is
an operator decision about which VALUE was intended, and silently collapsing a
stop-loss to one of two candidate values is exactly the failure this is meant to
prevent. It reports every occurrence + which one currently wins, and fails.

Sister: feedback_guards_compound_enforcement_is_leverage (the guard protects the whole
class forever; deduping one file is a single instance). Class 2 (display <-> execution
divergence) is the shape the inert-edit produces on the GUI side.

Machine-portable (.absolute() + env override, never .resolve()) per
symlinked-tool-host-root-resolution (LANDMINE 5) — this tool is symlinked from the
private workspace into the engine host.

Teeth-proof: --selftest (positive control MUST fail, negative control MUST pass).

Wiring: tools/check_session_docs.sh calls this HARD.
"""
import os
import re
import sys
import tempfile
from pathlib import Path

# A cfg assignment line: optional leading whitespace, a key, '=', anything.
# Mirrors the engine parser's own shape (ControllerConfig.hpp: skip blank + '#'-leading,
# find the FIRST '=', key is everything left of it). Keys are [a-z0-9_] by convention;
# we stay deliberately permissive on the key charset and strict on the anchoring, so a
# prose line containing '=' inside a comment can never register as a key.
ASSIGN_RE = re.compile(r'^[ \t]*([A-Za-z_][A-Za-z0-9_]*)[ \t]*=')

# The cfg files the engine actually parses. Each is operator-editable and
# gitignored-in-place (private), so this runs against the working tree, not git.
DEFAULT_CFGS = ("engine.cfg", "backtest.cfg", "controller.cfg")


def repo_root() -> Path:
    # <repo>/tools/check_cfg_duplicate_keys.py. .absolute() NOT .resolve(): the tool is
    # symlinked from the workspace into the engine host; .resolve() would follow the
    # symlink and scan the workspace instead of the engine. Env override first.
    env = os.environ.get("FOXML_REPO_ROOT") or os.environ.get("FOXML_ENGINE")
    return Path(env) if env else Path(__file__).absolute().parent.parent


def scan_text(text: str):
    """Return {key: [(lineno, raw_line), ...]} for keys appearing more than once.

    Skips blank lines and '#'-leading comments exactly as the engine parser does, so a
    commented-out duplicate (`#partial_exit_enabled=0`) is correctly NOT a duplicate —
    the parser never sees it, so it cannot shadow anything.
    """
    seen = {}
    for lineno, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.lstrip(" \t")
        if not stripped or stripped.startswith("#"):
            continue
        m = ASSIGN_RE.match(raw)
        if not m:
            continue
        seen.setdefault(m.group(1), []).append((lineno, raw.rstrip()))
    return {k: v for k, v in seen.items() if len(v) > 1}


def scan_file(path: Path):
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return None, f"could not read {path}: {e}"
    return scan_text(text), None


def selftest() -> int:
    """Non-vacuity proof (Class 51): the guard must FAIL on a planted duplicate and
    PASS on a clean file. A detector that cannot be made to fire is not a detector."""
    failures = []

    # (1) POSITIVE CONTROL — a planted duplicate MUST be caught.
    dup = "a=1\nb=2\na=3\n"
    got = scan_text(dup)
    if "a" not in got or len(got["a"]) != 2:
        failures.append("positive control: planted duplicate key 'a' NOT caught")
    if "b" in got:
        failures.append("positive control: single-occurrence key 'b' wrongly flagged")

    # (2) NEGATIVE CONTROL — a clean file MUST pass.
    if scan_text("a=1\nb=2\nc=3\n"):
        failures.append("negative control: clean file wrongly flagged")

    # (3) COMMENTED duplicates are NOT duplicates — the parser never sees them.
    if scan_text("a=1\n#a=2\n"):
        failures.append("comment tooth: commented-out duplicate wrongly flagged")
    if scan_text("a=1\n   # a=2\n"):
        failures.append("comment tooth: indented commented duplicate wrongly flagged")

    # (4) Leading whitespace still counts as a real assignment (the parser strips it).
    got = scan_text("a=1\n\ta=2\n")
    if "a" not in got:
        failures.append("whitespace tooth: tab-indented duplicate NOT caught")

    # (5) A '=' inside a comment must never register as a key.
    if scan_text("# note: a=1 is the default\na=1\n"):
        failures.append("prose tooth: '=' inside a comment registered as a key")

    # (6) Prefix collision must NOT merge: node_0_x and node_0_xy are distinct keys.
    if scan_text("node_0_x=1\nnode_0_xy=2\n"):
        failures.append("prefix tooth: distinct keys sharing a prefix wrongly merged")

    # (7) End-to-end on a real temp file (proves the file path, not just the parser).
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "dup.cfg"
        p.write_text("k=1\nk=2\n", encoding="utf-8")
        got, err = scan_file(p)
        if err or "k" not in (got or {}):
            failures.append(f"file tooth: end-to-end scan missed the duplicate ({err})")

    if failures:
        for f in failures:
            print(f"  [selftest] FAIL — {f}")
        print(f"[cfg-duplicate-keys] SELFTEST FAILED — {len(failures)} tooth(s) broken")
        return 1
    print("[cfg-duplicate-keys] SELFTEST PASS — 7 teeth (positive + negative + "
          "comment x2 + whitespace + prose + prefix + file round-trip)")
    return 0


def main(argv) -> int:
    if "--selftest" in argv:
        return selftest()

    root = repo_root()
    args = [a for a in argv if not a.startswith("-")]
    targets = [Path(a) for a in args] if args else [root / c for c in DEFAULT_CFGS]

    scanned = 0
    total_dups = 0
    for path in targets:
        if not path.exists():
            # A missing optional cfg is not a failure — not every deployment has all
            # three. An explicitly-named missing file IS a failure (operator typo).
            if args:
                print(f"[cfg-duplicate-keys] ERROR — named file not found: {path}")
                return 1
            continue
        scanned += 1
        dups, err = scan_file(path)
        if err:
            print(f"[cfg-duplicate-keys] ERROR — {err}")
            return 1
        for key, occurrences in sorted(dups.items()):
            total_dups += 1
            win_line, win_raw = occurrences[-1]
            print(f"\n  DUPLICATE KEY  {path.name}::{key}  ({len(occurrences)} occurrences)")
            for lineno, raw in occurrences:
                mark = "  <- WINS (parser is last-wins)" if lineno == win_line else ""
                print(f"      :{lineno}  {raw}{mark}")
            print(f"      the GUI writer edits :{occurrences[0][0]} (first-match) — "
                  f"an edit there is SILENTLY INERT")

    if total_dups:
        print(f"\n[cfg-duplicate-keys] FAIL — {total_dups} duplicated key(s) across "
              f"{scanned} cfg file(s).")
        print("  Resolve by DELETING the unwanted occurrence(s) — keep exactly one.")
        print("  Deleting all but the LAST is behavior-preserving (the parser already "
              "reads the last).")
        print("  This tool deliberately does NOT auto-pick: which value you meant is "
              "an operator decision, and a stop-loss is not a coin flip.")
        return 1

    print(f"[cfg-duplicate-keys] GREEN — no duplicated keys across {scanned} cfg file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
