#!/usr/bin/env python3
"""
check_cfg_key_prefix_drift.py — cfg-file key ∩ parser-recognized-prefix drift guard.

WHY THIS EXISTS (the structural close of a rename-completeness gap):
  An architecture-wide rename (the ② Core→Node rename, v5.15.5.F.4d.1.E.1.1) flips the
  PARSER to a new key prefix. The compiler red-build is a perfect oracle for the CODE
  tokens (rename-ship-methodology.md Phase 4) — but cfg DATA files, operator-facing
  example strings, and copyable docs have NO compiler oracle. So a rename can leave a
  cfg key on the OLD prefix that the new parser silently drops → the operator's per-node
  config is silently ignored (engine_sharded.cfg `core_1_strategy=momentum` → parser is
  `node_`-only → node 1 silently runs the SIMPLE_DIP default). Zero CI signal caught it.
  This guard is that signal: it diffs the keys present in shipped cfg files against the
  parser's currently-recognized per-node prefix, and against the retired-key ledger.

  Sister to tools/scan_class_44_cfg_orphan.py (which checks registry FLAGS vs readers,
  NOT cfg-file KEYS vs the parser prefix — the exact blind spot that let this accrue).
  The runtime complement is ③'s clean-break unknown-key HARD-REFUSE (parser-side); this
  is the build-time guard for the SHIPPED cfgs specifically.

DISCIPLINE: extend the two tables below when a future rename retires a per-node prefix or
a cfg key. The parser ground-truth (the accepted per-node prefix) is asserted against the
source so this guard can't itself drift (Class-51 vacuously-green self-defense).
"""

import argparse
import os
import re
import sys
import tempfile

ENGINE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The parser's CURRENT accepted per-node key prefix + the source site that defines it.
# Asserted live (see verify_parser_ground_truth) so this guard fails LOUD if the parser
# prefix changes again without this table being updated — not silently vacuously-green.
PARSER_PER_NODE_PREFIX = "node_"
PARSER_SITE = "CoreFrameworks/ControllerConfig.hpp"
PARSER_SITE_PATTERN = re.compile(r'strncmp\(key,\s*"node_",\s*5\)')

# RETIRED per-node prefixes: a cfg key on one of these is residue the live parser drops.
#   old_prefix -> (new_prefix, retiring_ship)
RETIRED_PER_NODE_PREFIXES = {
    "core_": ("node_", "v5.15.5.F.4d.1.E.1.1 (② Core→Node rename)"),
}

# RETIRED cfg KEYS: deleted from the code entirely (not a prefix-rename). The cfg line is
# dead text → DELETE it (the key name is not recycled, so H21-clean; tombstoning is for
# persisted/wire identifiers, not a no-longer-parsed operator cfg key).
RETIRED_KEYS = {
    "engine_arch": "deleted at v5.15.5.F.4d.1.B.x (single_core arch removal); REMOVE the line (do not rename)",
}

# match `key=...` (active) or `# key=...` / `#key=...` (commented example), capturing key.
_ACTIVE_RE = re.compile(r'^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=')
_COMMENT_RE = re.compile(r'^\s*#\s*([A-Za-z_][A-Za-z0-9_]*)\s*=')
_PER_NODE_KEY_RE = re.compile(r'^([a-z]+_)([0-9]+)_')   # e.g. core_0_ / node_3_

# Operator-facing STRING-literal references to a retired per-node prefix — the strings that TELL the
# operator to use the dropped key (fprintf/WARN/fix_hint/tooltip/deploy-hint/README). The cfg-key scan
# above catches cfg DATA; this catches the misleading STRINGS. Matches core_<N>_ / core_N_ / core_0_
# (placeholder or digit). In SOURCE we require the token INSIDE a double-quoted literal so code COMMENTS
# (PRESERVE-as-history per glossary §15) and legit CPU-core identifiers are not flagged; in MARKDOWN
# (README — all operator-facing) we flag any occurrence.
_RETIRED_PER_NODE_TOKEN = r'core_(?:[0-9]+|<N>|N)_'
_RETIRED_IN_STRING_RE = re.compile(r'"[^"\n]*\b' + _RETIRED_PER_NODE_TOKEN + r'[^"\n]*"')
_RETIRED_IN_MD_RE = re.compile(r'(?<![A-Za-z])' + _RETIRED_PER_NODE_TOKEN)
SOURCE_DIRS = ["CoreFrameworks", "Strategies", "ML_Headers", "Backtest",
               "DataStream", "FixedPoint", "MemHeaders", "GUI"]
SOURCE_EXTS = (".hpp", ".cpp", ".h", ".cc")


def find_cfg_files(root):
    out = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=True):
        # skip build dirs + .git
        dirnames[:] = [d for d in dirnames if not d.startswith("build") and d != ".git"]
        for fn in filenames:
            if fn.endswith(".cfg"):
                out.append(os.path.join(dirpath, fn))
    return sorted(out)


def verify_parser_ground_truth():
    """Non-vacuity self-defense: the parser site must actually use PARSER_PER_NODE_PREFIX.
    If the parser prefix changed without this guard's table, FAIL LOUD (Class-51)."""
    site = os.path.join(ENGINE_ROOT, PARSER_SITE)
    try:
        with open(site, "r", errors="replace") as fh:
            body = fh.read()
    except OSError as e:
        return False, f"cannot read parser site {PARSER_SITE}: {e}"
    if not PARSER_SITE_PATTERN.search(body):
        return False, (f"parser ground-truth LOST: {PARSER_SITE} no longer matches "
                       f"`strncmp(key, \"node_\", 5)` — the per-node prefix changed; "
                       f"update PARSER_PER_NODE_PREFIX + RETIRED_PER_NODE_PREFIXES.")
    return True, "parser ground-truth OK (node_ prefix confirmed at the parse site)"


def scan_file(path):
    """Return (hard, warn) lists of (lineno, key, kind, msg)."""
    hard, warn = [], []
    rel = os.path.relpath(path, ENGINE_ROOT)
    try:
        with open(path, "r", errors="replace") as fh:
            lines = fh.readlines()
    except OSError:
        return hard, warn
    for i, line in enumerate(lines, 1):
        active = _ACTIVE_RE.match(line)
        comment = None if active else _COMMENT_RE.match(line)
        key = active.group(1) if active else (comment.group(1) if comment else None)
        if key is None:
            continue
        is_active = active is not None

        # retired whole-key (engine_arch)
        if key in RETIRED_KEYS:
            entry = (i, key, "active" if is_active else "commented", RETIRED_KEYS[key])
            (hard if is_active else warn).append(entry)
            continue

        # retired per-node prefix (core_N_ -> node_N_)
        m = _PER_NODE_KEY_RE.match(key)
        if m:
            prefix = m.group(1)
            if prefix in RETIRED_PER_NODE_PREFIXES:
                new_prefix, ship = RETIRED_PER_NODE_PREFIXES[prefix]
                msg = (f"per-node key on RETIRED prefix `{prefix}` — parser is "
                       f"`{PARSER_PER_NODE_PREFIX}`-only ({ship}); rename to "
                       f"`{new_prefix}{key[len(prefix):]}`")
                entry = (i, key, "active" if is_active else "commented", msg)
                # ACTIVE retired-prefix key = parser silently drops it = HARD (live regression).
                # COMMENTED = copyable wrong-key example = WARN (operator uncomments → instant regression).
                (hard if is_active else warn).append(entry)
    return hard, warn


def scan_source_strings():
    """Flag operator-facing string-literal references to a retired per-node prefix in the PUBLIC source
    (string-literals only — comments are PRESERVE-as-history) + README (any occurrence). Returns a list
    of (relpath, lineno, snippet). These are the strings that instruct the operator to use a key the
    parser now drops — same rename-completeness gap as the cfg-key drift, on the no-oracle string surface."""
    hits = []
    for d in SOURCE_DIRS:
        base = os.path.join(ENGINE_ROOT, d)
        if not os.path.isdir(base):
            continue
        for dp, dn, fns in os.walk(base, followlinks=True):
            dn[:] = [x for x in dn if not x.startswith("build") and x != ".git"]
            for fn in fns:
                if not fn.endswith(SOURCE_EXTS):
                    continue
                p = os.path.join(dp, fn)
                rel = os.path.relpath(p, ENGINE_ROOT)
                try:
                    with open(p, "r", errors="replace") as fh:
                        for i, line in enumerate(fh, 1):
                            if _RETIRED_IN_STRING_RE.search(line):
                                hits.append((rel, i, line.strip()[:110]))
                except OSError:
                    pass
    readme = os.path.join(ENGINE_ROOT, "README.md")
    if os.path.isfile(readme):
        with open(readme, "r", errors="replace") as fh:
            for i, line in enumerate(fh, 1):
                if _RETIRED_IN_MD_RE.search(line):
                    hits.append(("README.md", i, line.strip()[:110]))
    return hits


def run(strict=False):
    ok, gt_msg = verify_parser_ground_truth()
    if not ok:
        print(f"[cfg-prefix-drift] SELF-CHECK FAILED — {gt_msg}", file=sys.stderr)
        return 2
    print(f"[cfg-prefix-drift] {gt_msg}")

    files = find_cfg_files(ENGINE_ROOT)
    total_hard, total_warn = 0, 0
    for path in files:
        hard, warn = scan_file(path)
        if not hard and not warn:
            continue
        rel = os.path.relpath(path, ENGINE_ROOT)
        for (ln, key, kind, msg) in hard:
            print(f"  ❌ HARD {rel}:{ln}  {key}  [{kind}]  {msg}")
        for (ln, key, kind, msg) in warn:
            print(f"  ⚠️  WARN {rel}:{ln}  {key}  [{kind}]  {msg}")
        total_hard += len(hard)
        total_warn += len(warn)

    # operator-facing string-literal drift (the strings that instruct the operator to use the dropped key)
    for (rel, ln, snippet) in scan_source_strings():
        print(f"  ❌ HARD {rel}:{ln}  operator-facing string references a RETIRED per-node prefix  |  {snippet}")
        total_hard += 1

    if total_hard == 0 and total_warn == 0:
        print("[cfg-prefix-drift] CLEAN — no cfg key / operator-string on a retired prefix / retired key.")
        return 0
    print(f"[cfg-prefix-drift] {total_hard} HARD + {total_warn} WARN finding(s).")
    # HARD = an ACTIVE key the parser silently drops (live regression) → fail.
    # WARN (commented examples / commented retired keys) → fail only under --strict.
    if total_hard > 0:
        return 1
    return 1 if (strict and total_warn > 0) else 0


def selftest():
    """Teeth: the guard MUST flag a synthesized active core_N_ key + a retired engine_arch
    key, and MUST stay clean on the node_ equivalent (positive control). Non-vacuity."""
    failures = []
    with tempfile.TemporaryDirectory() as td:
        # (1) a dirty cfg — must trip HARD on the active core_ key + the active engine_arch
        dirty = os.path.join(td, "dirty.cfg")
        with open(dirty, "w") as fh:
            fh.write("core_0_strategy=momentum\n")      # active retired prefix -> HARD
            fh.write("engine_arch=per_core_slow\n")     # active retired key -> HARD
            fh.write("# core_1_risk_pct=20.0\n")        # commented retired prefix -> WARN
        hard, warn = scan_file(dirty)
        if len(hard) != 2:
            failures.append(f"expected 2 HARD on dirty.cfg, got {len(hard)}: {hard}")
        if len(warn) != 1:
            failures.append(f"expected 1 WARN on dirty.cfg, got {len(warn)}: {warn}")
        # (2) the migrated cfg — must be CLEAN (positive control: node_ + no engine_arch)
        clean = os.path.join(td, "clean.cfg")
        with open(clean, "w") as fh:
            fh.write("node_0_strategy=momentum\n")
            fh.write("node_1_risk_pct=20.0\n")
            fh.write("num_execution_nodes=4\n")
        hard, warn = scan_file(clean)
        if hard or warn:
            failures.append(f"expected CLEAN on migrated cfg, got hard={hard} warn={warn}")
    # (3) the parser ground-truth self-check must pass against the real source
    ok, msg = verify_parser_ground_truth()
    if not ok:
        failures.append(f"ground-truth self-check failed: {msg}")

    # (4) operator-string-scan regex teeth: flag core_N_ INSIDE a string literal + in markdown;
    #     do NOT flag a // comment (PRESERVE) or a legit core_id / ExecutionCore (false-migration risk).
    str_pos = '    fprintf(stderr, "set core_<N>_strategy explicitly for all N");'
    str_pos2 = '    tip = "override via core_0_model_path in each tab";'
    comment_neg = '    // legacy parser handled core_0_strategy= (history)'
    md_pos = 'set `core_0_strategy = ml` in engine.cfg'
    legit_neg = '    int cpu = core_id;  // ExecutionCore physical core'
    if not _RETIRED_IN_STRING_RE.search(str_pos):
        failures.append("string-scan: missed core_<N>_ inside a string literal")
    if not _RETIRED_IN_STRING_RE.search(str_pos2):
        failures.append("string-scan: missed core_0_ inside a string literal")
    if _RETIRED_IN_STRING_RE.search(comment_neg):
        failures.append("string-scan: FALSE-flagged core_0_ in a // comment (must PRESERVE)")
    if not _RETIRED_IN_MD_RE.search(md_pos):
        failures.append("string-scan: missed core_0_ in markdown")
    if _RETIRED_IN_MD_RE.search(legit_neg) or _RETIRED_IN_STRING_RE.search(legit_neg):
        failures.append("string-scan: FALSE-flagged a legit core_id / ExecutionCore")

    if failures:
        for f in failures:
            print(f"  ✗ selftest: {f}", file=sys.stderr)
        print("[cfg-prefix-drift] SELFTEST FAILED", file=sys.stderr)
        return 1
    print("[cfg-prefix-drift] SELFTEST PASS — flags active core_N_ + engine_arch, "
          "clean on node_; ground-truth verified.")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="cfg-file key vs parser-prefix drift guard")
    ap.add_argument("--strict", action="store_true",
                    help="treat commented retired-prefix examples (copyable wrong-key) as failures too")
    ap.add_argument("--selftest", action="store_true", help="run the non-vacuity teeth")
    args = ap.parse_args()
    sys.exit(selftest() if args.selftest else run(strict=args.strict))
