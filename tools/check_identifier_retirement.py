#!/usr/bin/env python3
"""
check_identifier_retirement.py — the tombstone CI guard (Knight-Capital defense).

WHY THIS EXISTS
---------------
Persistence/wire-visible identifiers — snapshot/format VERSION numbers, and the
integer CODES of persisted/logged/wire-emitted enum registries — must NEVER be
renumbered, value-reused, or silently removed. An OLD persisted file, an OLD
wire/HMAC message, or an un-updated node can carry the OLD meaning of a reused
identifier and silently activate the WRONG code path. That is the Knight Capital
failure mode ($440M / 45 min, 2012): a dormant identifier ("Power Peg") reused
for new behavior while old code keyed to it was still compiled in, on a node
that didn't get the deploy. Three ingredients — dead code left in, an identifier
repurposed, deploy/state skew — and a trading firm died.

This guard freezes the current identifier->value map in a golden ledger
(tools/identifier_ledger.txt) and FAILS on any RENUMBER, VALUE-REUSE, or silent
REMOVAL. ADDING a new identifier is fine (append-only) — record it with --update.
RETIRING one is fine too — but you TOMBSTONE the slot (RESERVED / LEGACY_ /
DEPRECATED comment, never reassign the number), and the ledger keeps the row.

The codebase ALREADY practices this informally (BanditAlgorithm "OPTION C
wire-byte preservation"; "RESERVED (was PER_NODE_OK ...)"; LEGACY_CONFIDENCE_VERSION;
StrategyInterface.hpp's "IDs are append-only — never reorder or remove. Persisted
snapshots and trade logs reference these by integer."). This tool MECHANIZES that
existing-but-unenforced convention. Golden-master, not a reimplemented oracle
(feedback_golden_master_over_reimplemented_oracle): the ledger is the frozen REAL
state. See DESIGN_SPECS/meta-disciplines/dead-code-and-identifier-retirement-discipline.md.

COVERAGE (v1): snapshot/format VERSION #defines + STAMP_FORMAT_VERSION_CURRENT +
the persisted ENUM registries (BanditAlgorithm / StrategyId / RegimeId). Bitmap
bit-assignments + cfg-field name keys enroll next — add a SOURCES row (paced
enrollment; the discipline is complete, coverage grows — sister to the H15
meta-registry enrollment pattern).

USAGE
  check_identifier_retirement.py            verify code matches ledger (CI; exit 1 on violation)
  check_identifier_retirement.py --update   regenerate the ledger from current code (after an intentional ADD/tombstone)
  check_identifier_retirement.py --print    print the parsed current map; do not compare

Machine-portable: the engine root comes from the `foxroots` SSoT
(feedback_machine_portable_resolver_for_committed_tool_paths).
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from foxroots import ENGINE   # noqa: E402  (the ONE repo-root resolver — D-375)

# ⚠️ FIXED 2026-07-20 — this was:
#     REPO_ROOT = os.environ.get("FOXML_REPO_ROOT") or os.path.abspath(
#         os.path.join(os.path.dirname(__file__), ".."))
# which is Landmine-5 verbatim: `tools/` is a DIRECTORY SYMLINK, so walking up from this file's
# location lands in the WORKSPACE, which has no CoreFrameworks/. Invoked through the workspace
# path the tool died with FileNotFoundError on the very first source it tried to parse — i.e. the
# H21 Knight-Capital guard was BROKEN on one of its two reachable paths.
#
# It hid because pre-commit Check H only fires when a matching file is STAGED
# (`^(CoreFrameworks/|ML_Headers/|Strategies/|MemHeaders/|tools/(identifier_ledger\.txt|
# check_identifier_retirement\.py))`), and engine-side commits resolve the engine root correctly.
# The failure needed a WORKSPACE-side commit touching this tool — which is exactly what closing
# TECH_DEBT-255 produced. A guard reachable two ways and tested one way.
#
# foxroots adds what the hand-rolled version lacked: a `Version.hpp` MARKER shape-check plus
# sibling recovery, so it resolves correctly through the symlink from either repo.
REPO_ROOT = os.environ.get("FOXML_REPO_ROOT") or str(ENGINE)
# IDENTIFIER_LEDGER overrides the ledger path — used ONLY by the negative self-test, so it can
# plant defects in a throwaway COPY instead of mutating the tracked golden in place. The previous
# selftest edited the real file and restored it via an EXIT trap; that works until it doesn't
# (a SIGKILL mid-run leaves a corrupted H21 golden in the working tree), and the risk is exactly
# what kept the selftest out of the standing sweep — which is how its version-decrease tooth sat
# broken unnoticed. Removing the mutation makes it safe to wire.
LEDGER = os.environ.get("IDENTIFIER_LEDGER") or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "identifier_ledger.txt")

# Enrolled identifier sources. Add a row to enroll a new registry.
#   (category, file_relative_to_repo_root, kind, name_or_macro, opts)
# kind: "define"    -> #define NAME <int>
#       "constexpr" -> static constexpr <type> NAME = <int>
#       "foreach"   -> #define MACRO(X) X(name, ...) X(name, ...) ...
#                       opts: prefix, value="explicit"|"positional", value_col (explicit only)
# H21 name-tombstones: identifiers whose LEDGER rows were removed at format
# retirement. The regenerated ledger has no memory of removed names — without
# this set, a re-introduced #define of a burned name would classify as a fresh
# "ADD (ok)" instead of the Knight-Capital-shaped violation it is.
RETIRED_NAMES = {
    "CONTROLLER_SNAPSHOT_VERSION",   # E.1.2/D-289 — controller snapshot format retired (was version=14)
    # E.1.2/D-421 step 6 Tier 0 (2026-08-16) — the `fees` stamp group was DELETED, not tombstoned in
    # code: two of its rows emitted zeros into an HMAC-signed body. Every H21 condition was checked
    # against a named search space and no live referent survives (one hit tree-wide, the tombstone
    # comment at StampBoundModelConstRegistry.hpp:553). Burning the names here is what makes that
    # deletion ENFORCED rather than narrated — without these entries a re-introduced `STAMP_BIT_fees`
    # classifies as a fresh "ADD (ok)" instead of the Knight-Capital-shaped reuse it would be.
    #
    # ⚠️ These burns are NOT a substitute for coverage. This guard has NO `SOURCES` row for
    # `FOREACH_STAMP_BOUND_MODEL_CONST`, so it never inspected the registry these names came from —
    # a GREEN here says nothing about the stamp wire body. See TECH_DEBT (stamp-registry enrollment)
    # and D-425; enrolling it is a prerequisite to the Tier-2 emit-side deletion, not a follow-up.
    "STAMP_BIT_fees",
    "inference_cfg_fee_rate_maker",
    "inference_cfg_fee_rate_taker",
}

SOURCES = [
    ("version", "CoreFrameworks/ShardedSnapshotPersist.hpp", "define",    "SHARDED_SNAPSHOT_VERSION",    {}),
    # CONTROLLER_SNAPSHOT_VERSION row REMOVED at E.1.2/D-289 (format retired, macro
    # deleted). The NAME is burned — see RETIRED_NAMES above (H21: a deleted wire
    # identifier must never silently reappear as a fresh "ADD (ok)").
    ("version", "CoreFrameworks/Portfolio.hpp",              "define",    "PORTFOLIO_SNAPSHOT_VERSION",  {}),
    ("version", "ML_Headers/ModelInference.hpp",             "define",    "MODEL_FORMAT_VERSION",        {}),
    ("version", "ML_Headers/BanditLearning.hpp",             "define",    "BANDIT_STATE_FORMAT_VERSION", {}),
    ("version", "ML_Headers/ModelInference.hpp",             "constexpr", "STAMP_FORMAT_VERSION_CURRENT",{}),
    ("enum:BanditAlgorithm", "ML_Headers/BanditAlgorithmRegistry.hpp", "foreach", "FOREACH_BANDIT_ALGORITHM",
        {"prefix": "BANDIT_ALGO_", "value": "explicit", "value_col": 1}),
    ("enum:StrategyId", "Strategies/StrategyInterface.hpp", "foreach", "FOREACH_STRATEGY",
        {"prefix": "STRATEGY_", "value": "positional"}),
    ("enum:RegimeId",   "Strategies/StrategyInterface.hpp", "foreach", "FOREACH_REGIME",
        {"prefix": "REGIME_", "value": "positional"}),
    # v5.15.5.E.0.10 A6 (D-221) — SHALT codes are trade-log-visible (StrategyInterface :242-243:
    # "IDs are append-only; existing trade logs reference numeric values") → Knight-Capital tracked.
    ("enum:ShaltCode",  "Strategies/StrategyInterface.hpp", "foreach", "FOREACH_SHALT",
        {"prefix": "SHALT_", "value": "positional"}),
    # NodeContext state-flag bit positions (NODE_STATE_FLAG_<name>); append-only per H21.
    # NOTE: FOREACH_FAILURE_MODE's lowercase row-names (ml_model_load_failed) are skipped by the
    # _parse_foreach ^[A-Z0-9_]+$ filter → it enrolls in the paced bit-assignment pass once the
    # parser handles lowercase; meanwhile protected by static_assert(FAILURE_BIT_COUNT<=16) + append-only.
    # HOMED: TECH_DEBT-152 (paced identifier-guard enrollment; "Known un-enrolled instance" bullet) —
    # the durable tracker + re-enrollment trigger; this comment is the code-side pointer to it.
    ("enum:NodeStateFlag", "MemHeaders/NodeStateFlagRegistry.hpp", "foreach", "FOREACH_NODE_STATE_FLAG",
        {"prefix": "NODE_STATE_FLAG_", "value": "positional"}),
    # E.1.2 D-305 (a-class R3-b) — persist-wire WIDTH constants. The layout listing keeps
    # the delegate arrays' count TOKENS verbatim (ROLLING_IC_MAX_WINDOW / MAX_WINDOW), so a
    # WIDTH change is listing-invisible while it changes the wire by 3×8B×delta. Enrolling
    # the VALUES here makes a width change a Check-H red (non-monotonic category ⇒ any change
    # = RENUMBERED violation; a deliberate epoch accepts it via the TTY-gated --update) instead
    # of waiting for the runtime byte-golden at ./build.sh test.
    ("wire-const", "ML_Headers/ConfidenceScore.hpp",    "define", "ROLLING_IC_MAX_WINDOW", {}),
    ("wire-const", "ML_Headers/LinearRegression3X.hpp", "define", "MAX_WINDOW",            {}),
]

# Categories whose values are monotonic-non-decreasing (a DROP is also a violation).
MONOTONIC = {"version"}


def _read(rel):
    with open(os.path.join(REPO_ROOT, rel)) as f:
        return f.read()


def _parse_define(text, name):
    m = re.search(r'^\s*#\s*define\s+' + re.escape(name) + r'\s+(\d+)', text, re.M)
    return {name: int(m.group(1))} if m else {}


def _parse_constexpr(text, name):
    m = re.search(r'constexpr\s+\w+\s+' + re.escape(name) + r'\s*=\s*(\d+)', text)
    return {name: int(m.group(1))} if m else {}


# E.1.2 D-305 — the FOREACH-macro parse helpers (_macro_body / _rows / _args) moved
# to node_persist_layout.py (the library tier) so the layout audit and this guard
# share ONE implementation (single-source; one-direction dependency — that module
# never imports this one).
from node_persist_layout import (_macro_body, _rows, _args,              # noqa: E402
                                 _expand_nested, _strip_comments, _strip_comments_text)


def _parse_foreach(text, macro, opts, base_dir=None):
    # E.1.2 complement-blindness sweep — THREE parse corrections, all of which were
    # SILENT under-counts of an enrolled registry (worse than a missing registry: the
    # ledger category exists, so the surface reads as covered):
    #   1. comment-strip. This guard never stripped, while its sibling consumer of the
    #      same library did — so a `/* ... X(...) ... */` doc block could fabricate a
    #      phantom row, and a commented-out row could be counted as live.
    #   2. _expand_nested. A row reaching the registry via a nested `FOREACH_<NAME>(X)`
    #      was invisible: `FOREACH_STRATEGY`'s 5th row arrives that way
    #      (`Strategies/StrategyInterface.hpp:143`), which is why the golden ledger has
    #      carried FOUR StrategyId rows while the enum has five real strategies —
    #      STRATEGY_EMA_CROSS was outside the reach of the H21 guard that exists to stop
    #      persisted-ID reuse.
    #   3. base_dir. The nested macro is `__has_include`-conditional, so resolving it
    #      needs the including file's directory; without it we would take the populated
    #      branch even in a tree where the header is absent.
    # NOTE the pre-existing `^[A-Z0-9_]+$` filter below was the compensating skip for (2)
    # — it discarded the nested invocation token rather than expanding it. With expansion
    # in place it now only rejects genuine non-row tokens.
    text = _strip_comments_text(text)
    body = _macro_body(text, macro, base_dir)
    if body is None:
        return {}
    body = _strip_comments(_expand_nested(text, body, base_dir))
    out, idx = {}, 0
    for inner in _rows(body):
        args = _args(inner)
        name0 = args[0] if args else ""
        if not re.match(r'^[A-Z0-9_]+$', name0):
            continue  # non-row token (nested invocations are expanded above, not skipped)
        full = opts["prefix"] + name0
        if opts.get("value") == "explicit":
            try:
                val = int(args[opts["value_col"]])
            except (ValueError, IndexError):
                continue
        else:
            val = idx
        out[full] = val
        idx += 1
    return out


def parse_current():
    """Return {category: {identifier_name: int_value}} parsed from the live source."""
    result = {}
    for category, rel, kind, name, opts in SOURCES:
        text = _read(rel)
        if kind == "define":
            got = _parse_define(text, name)
        elif kind == "constexpr":
            got = _parse_constexpr(text, name)
        elif kind == "foreach":
            # base_dir = the registry file's own directory, so an `__has_include("p")`
            # guard resolves against the same path the preprocessor would use.
            got = _parse_foreach(text, name, opts,
                                 os.path.dirname(os.path.join(REPO_ROOT, rel)))
        else:
            sys.exit(f"unknown source kind: {kind}")
        if not got:
            sys.exit(f"PARSE ERROR: found nothing for {category} ({kind} {name}) in {rel} "
                     f"— the source moved/renamed; update SOURCES in {os.path.basename(__file__)}.")
        result.setdefault(category, {}).update(got)
    return result


def load_ledger():
    frozen = {}
    if not os.path.exists(LEDGER):
        return None
    with open(LEDGER) as f:
        for line in f:
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            cat, name, val = line.split("|")
            frozen.setdefault(cat, {})[name] = int(val)
    return frozen


def ledger_lines(current):
    """The ledger's full desired content, as lines. Split out from the writer so the SAME lines
    can be handed to the shared bless helper for a diff-and-confirm instead of being written
    unconditionally (TECH_DEBT-255)."""
    lines = [
        "# identifier_ledger.txt — the tombstone golden (check_identifier_retirement.py).",
        "# Persistence/wire-visible identifier -> value. NEVER renumber/reuse/drop a row;",
        "# tombstone retired slots (RESERVED/LEGACY_/DEPRECATED) and keep the row. ADD = append.",
        # NOTE: do NOT add header lines here casually. This list IS the blessed content, so any
        # change to it drifts the golden and can then only be cleared by an interactive re-bless
        # (D-394). A comment is not worth making a human sit through a confirmation prompt.
        "# Regenerate after an intentional ADD/tombstone: tools/check_identifier_retirement.py --update",
        "# format: category|identifier|value",
        "",
    ]
    for cat in sorted(current):
        for name in sorted(current[cat], key=lambda n: (current[cat][n], n)):
            lines.append(f"{cat}|{name}|{current[cat][name]}")
        lines.append("")
    return lines


def write_ledger(current):
    with open(LEDGER, "w") as f:
        f.write("\n".join(ledger_lines(current)).rstrip() + "\n")


def compare(frozen, current):
    """Violations = renumber / value-reuse / silent removal / version-decrease.
       Additions (new identifier) + version bumps (monotonic increase) are OK — info only."""
    violations, additions, bumps = [], [], []
    for cat, names in frozen.items():
        cur = current.get(cat, {})
        monotonic = cat in MONOTONIC          # versions bump up legitimately; enums never change value
        cur_by_val = {}
        if not monotonic:
            for n, v in cur.items():
                cur_by_val.setdefault(v, []).append(n)
        for name, val in names.items():
            if name not in cur:
                violations.append(
                    f"REMOVED  {cat} :: {name} (was {val}) — a persisted/wire identifier vanished. "
                    f"Old state/messages still reference {val}; TOMBSTONE the slot (RESERVED/LEGACY_), do not drop the row.")
            elif monotonic:
                if cur[name] < val:
                    violations.append(
                        f"DECREASED {cat} :: {name} {val} -> {cur[name]} — a format version went BACKWARDS; "
                        f"old-layout state/messages would silently reload into new code (Knight-Capital stale-state).")
                elif cur[name] > val:
                    bumps.append(f"{cat} :: {name} {val} -> {cur[name]} (version bump)")
                # equal -> unchanged, fine
            elif cur[name] != val:
                violations.append(
                    f"RENUMBERED {cat} :: {name} {val} -> {cur[name]} — a persisted enum code is immutable "
                    f"(Knight-Capital reuse). Allocate a NEW identifier for the new meaning; never re-stamp an old one.")
            else:
                # name held its value; check nobody ELSE grabbed that value (reuse via drop+re-add)
                holders = [n for n in cur_by_val.get(val, []) if n != name]
                if holders:
                    violations.append(
                        f"VALUE-REUSE {cat} :: value {val} now also held by {holders} (frozen owner: {name}).")
    for cat, names in current.items():
        for name, val in names.items():
            if name not in frozen.get(cat, {}):
                additions.append(f"{cat} :: {name} = {val}")
    return violations, additions, bumps


# The dirs a resurrected wire identifier could plausibly land in — the same
# surface set as the pre-commit Check H trigger.
RETIRED_SCAN_DIRS = ("CoreFrameworks", "ML_Headers", "MemHeaders",
                     "Strategies", "FixedPoint", "DataStream")


def retired_name_check():
    """H21 name-tombstone sweep — SOURCES-independent BY NECESSITY.

    A retired name has no SOURCES row, so parse_current() never looks for it: a
    resurrected `#define CONTROLLER_SNAPSHOT_VERSION 1` would be INVISIBLE to
    compare() entirely (not even an ADD). Witnessed vacuity of the naive
    additions-loop placement, 2026-08-14 planted-control run — hence this
    dedicated tree sweep. Line-anchored `#define` match only; a commented
    tombstone mention ("CONTROLLER_SNAPSHOT_VERSION=14" in prose) is the
    DESIRED way to keep the number and never matches."""
    if not RETIRED_NAMES:
        return []
    violations = []
    pats = {n: re.compile(r"^\s*#\s*define\s+" + re.escape(n) + r"\b")
            for n in RETIRED_NAMES}
    for d in RETIRED_SCAN_DIRS:
        root = os.path.join(REPO_ROOT, d)
        for dirpath, _dirnames, filenames in os.walk(root):
            for fn in filenames:
                if not fn.endswith((".hpp", ".h", ".cpp")):
                    continue
                fp = os.path.join(dirpath, fn)
                try:
                    with open(fp, encoding="utf-8", errors="replace") as fh:
                        for i, line in enumerate(fh, 1):
                            for n, pat in pats.items():
                                if pat.match(line):
                                    rel = os.path.relpath(fp, REPO_ROOT)
                                    violations.append(
                                        f"RETIRED-NAME-REUSE :: #define {n} at {rel}:{i} — this "
                                        f"identifier was retired WITH its format (ledger row removed); "
                                        f"the NAME is burned per H21. A new meaning needs a NEW identifier.")
                except OSError:
                    pass
    return violations


def paired_bump_check(frozen, current, layout_cur=None, layout_gold=None):
    """E.1.2 D-305 — the golden↔version PAIRED-BUMP rule (the D-208 M7 close).

    The per-node persist LAYOUT (the flattened FOREACH_NODE_PERSIST_FIELD walk,
    delegate-internal rows included) is frozen as a named-row golden
    (tools/goldens/node_persist_layout.txt). If the layout moved and
    SHARDED_SNAPSHOT_VERSION did NOT bump in the same tree, that is the exact
    hole the count-locks + byte-golden are structurally blind to (a
    size-neutral, count-neutral row swap — the triple-vacuity) → violation.
    A layout delta WITH a version bump is the legitimate epoch path — surfaced
    as info; the golden then re-blesses via node_persist_layout.py --bless
    (D-394 TTY flow, same contract as this ledger's --update). A REFUSAL
    (unparseable registry) is a violation, never a silent pass — a guard that
    cannot see is not green.

    layout_cur/layout_gold injectable for the positive-control teeth ONLY;
    production callers pass neither and get the live parse + real golden.
    """
    import node_persist_layout as npl
    violations, bumps = [], []
    try:
        if layout_cur is None:
            # REPO_ROOT (not npl's default ENGINE) so a FOXML_REPO_ROOT override
            # keeps version-parse and layout-parse on the SAME tree (a-class R5).
            layout_cur = npl.listing_lines(npl.parse_layout(REPO_ROOT))
        if layout_gold is None:
            layout_gold = npl.load_golden()
        if layout_gold is None:
            violations.append(
                "PERSIST-LAYOUT golden MISSING (tools/goldens/node_persist_layout.txt) — "
                "establish via node_persist_layout.py --emit-initial.")
            return violations, bumps
        layout_diff = npl.diff_lines(layout_gold, layout_cur)
        if layout_diff:
            frozen_sv = frozen.get("version", {}).get("SHARDED_SNAPSHOT_VERSION")
            cur_sv = current.get("version", {}).get("SHARDED_SNAPSHOT_VERSION")
            if cur_sv == frozen_sv:
                violations.append(
                    "PERSIST-LAYOUT differs from its golden while SHARDED_SNAPSHOT_VERSION "
                    f"is unchanged vs the ledger (both {cur_sv}) — the paired-bump rule "
                    "(D-305/D-302): a wire-layout delta and its version bump ride the SAME "
                    "commit. (If the bump already landed in an earlier commit, the layout "
                    "golden is STALE — re-bless via node_persist_layout.py --bless.) Row delta:\n"
                    + "\n".join(f"      {x}" for x in layout_diff))
            else:
                bumps.append(
                    f"persist-layout :: {len(layout_diff)} row change(s) ride the SHARDED "
                    f"bump {frozen_sv} -> {cur_sv} (re-bless the layout golden via "
                    "node_persist_layout.py --bless + regen/RENAME the byte-golden)")
    except npl.LayoutRefusal as e:
        violations.append(f"PERSIST-LAYOUT audit REFUSED (cannot parse the registry): {e}")
    return violations, bumps


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    current = parse_current()

    if arg == "--print":
        for cat in sorted(current):
            for name in sorted(current[cat], key=lambda n: current[cat][n]):
                print(f"{cat}|{name}|{current[cat][name]}")
        return 0

    if arg == "--update":
        # TECH_DEBT-255 CLOSED. This used to be `write_ledger(current); return 0` — the H21
        # tombstone golden rewritten with NO diff and NO confirmation. So the tool enforcing
        # "never renumber, never reuse, never silently drop a persistence/wire identifier" — the
        # Knight-Capital discipline, $440M in 45 minutes — could have its own record
        # rubber-stamped by any caller, including a delegated agent that "fixed the red by
        # re-baselining". That is the failure this guard exists to prevent, applied to the guard.
        #
        # Now routed through the ONE shared bless path (D-394), the same one the corpus golden
        # uses: a TTY is required, the per-file diff is SHOWN with what the ledger currently
        # holds and how many rows would be REMOVED, a typed confirmation is demanded, and a
        # non-interactive caller is HARD-REFUSED rc=2. Per D-385/M10 that makes a delegated agent
        # structurally incapable of re-blessing this ledger.
        #
        # It also inherits no-op ⇒ NO WRITE (D-369): `--update` on an unchanged ledger now leaves
        # the file byte-identical instead of rewriting it every time, so a "run the producer,
        # expect 0-diff" currency check finally means something here.
        #
        # SAFE TO TIGHTEN — callers enumerated first (the enumerate-before-flipping discipline):
        # `--update` has NO automated caller. `.githooks/pre-commit:360` only PRINTS it as an
        # instruction, the ledger header mentions it in a comment, and
        # check_identifier_retirement_selftest.sh manipulates the ledger directly with cp/sed
        # rather than invoking it. It is operator-invoked only, which is exactly the usage the
        # TTY gate is built for.
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import bless as bless_mod
        return bless_mod.bless(LEDGER, ledger_lines(current), "identifier-ledger")

    frozen = load_ledger()
    if frozen is None:
        print(f"[identifier-retirement] NO LEDGER at {LEDGER} — run --update once to establish the golden.", file=sys.stderr)
        return 1

    violations, additions, bumps = compare(frozen, current)
    pb_violations, pb_bumps = paired_bump_check(frozen, current)
    violations += pb_violations
    bumps += pb_bumps
    violations += retired_name_check()

    for a in additions:
        print(f"[identifier-retirement] ADD (ok; run --update to record): {a}")
    for b in bumps:
        print(f"[identifier-retirement] BUMP (ok; run --update to record): {b}")
    if violations:
        print("\n=== IDENTIFIER-RETIREMENT VIOLATION (Knight-Capital tombstone guard) ===", file=sys.stderr)
        for v in violations:
            print(f"  ✗ {v}", file=sys.stderr)
        print("\nPersisted/wire-visible identifiers are append-only + immutable. To retire one, tombstone the\n"
              "slot (RESERVED/LEGACY_/DEPRECATED, keep the number) — never renumber or reuse it. If this change\n"
              "is intentional + safe, re-run with --update to re-freeze the ledger.\n", file=sys.stderr)
        return 1

    total = sum(len(v) for v in current.values())
    print(f"[identifier-retirement] GREEN — {total} persisted/wire identifiers match the ledger; no renumber/reuse/drop.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
