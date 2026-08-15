#!/usr/bin/env python3
"""
check_node_ctx_partition.py — the NodeContext PERSIST-PARTITION guard (D-421 step 2).

WHY THIS EXISTS — complement blindness
--------------------------------------
`FOREACH_NODE_PERSIST_FIELD` is a COVERAGE registry, not a source-of-truth one:
`NodeContext<F>` is hand-declared at `CoreFrameworks/ControllerEventLoop.hpp:315`, so the
registry describes a SUBSET of a struct that exists independently of it. Every guard we had
pointed the same direction — rows-forward:

  - the compile-time count-lock pins the registry at 29 rows
  - `node_persist_layout.py` freezes the flattened wire LISTING against a golden
  - `check_identifier_retirement.py` pins the version + enforces the paired bump

All three answer "are the rows we have correct?". **None answers "are these all the rows there
should be?"** A field added to `NodeContext` and never enrolled is invisible to every one of
them — they stay green, because nothing they read ever mentions it. That is the shape this
tool exists to close, and it is not hypothetical:

  - `node_gross_wins` / `node_losses` / `idle_cycles` were added at v4.7.25 and silently never
    persisted. Stats read $0.00 after every restart until v5.4.3 caught it — the founding
    instance (TECH_DEBT-196), and the reason the ordered registry was built at all.
  - `ic.actuals.{count,head}` (E.1.2, 2026-08-15): unpersisted while its sibling
    `ic.predictions.{count,head}` was persisted. A perfectly-correlated predictor measured
    IC = -0.5238 after warm restart, and that IC drives an auto-kill capital control. It had a
    stated reason — "the two rings advance in lockstep", documented in the header — and the
    reason was TRUE of Push and FALSE across the persist boundary. Fixed at engine 564f099.

That second one is why this tool demands a CATEGORY and not just a checkbox. **A reason that is
merely written down is a hypothesis.** The discriminator that actually found the bug was
structural: two sibling fields of the same type treated asymmetrically. So the exemption
registry names a category, and the categories are chosen to be the kind of claim a reviewer can
falsify from code (`DERIVED_EACH_PASS` says "find me the unconditional write"), not the kind
that merely sounds reasonable ("it's transient").

WHAT THIS OWNS
  Three directions, all RED, because each fails differently:
    1. UNACCOUNTED  — a member with neither a persist row nor an exemption. The silent-drop
                      class above.
    2. STALE-EXEMPT — an exemption naming something that is no longer a member. The field was
                      renamed or deleted and the exemption now protects nothing; worse, it
                      makes the partition LOOK fully accounted while covering a ghost. A
                      vacuity in the guard's own input.
    3. CONTRADICTION— a member both persisted AND exempted. One of the two is a lie and the
                      tool cannot tell which, so it refuses to guess.

WHAT IT DELIBERATELY DOES NOT DO
  - judge whether an exemption's REASON is true. A checker cannot verify "recomputed before
    every read" — that is a code-reading judgment, and pretending to mechanize it would produce
    exactly the false confidence the `ic.actuals` case is made of. What the tool CAN enforce is
    that a human wrote a falsifiable claim next to a named field, and that the claim's subject
    still exists. Verification of the claims themselves rides the pre-coding audit cascade.
  - compute byte offsets or sizes. Wire bytes belong to `node_persist_layout.py` + the runtime
    byte-golden; this tool is about SET MEMBERSHIP only.

rc contract: 0 = partition fully accounted · 1 = finding (named members) · 2 = REFUSAL
(cannot read the struct / cannot read a registry) — a broken parse is NEVER an empty-set pass
(Class 57 / Class 51).
"""
import os
import re
import sys
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from foxroots import ENGINE                                          # noqa: E402  (D-375 root resolver)
from node_persist_layout import (_macro_body_resolved, _rows, _args,  # noqa: E402  (shared parser SSoT)
                                 _strip_comments, _strip_comments_text)
from check_cache_layout import run_emitter_nvim, EmitterUnavailable   # noqa: E402  (shared emitter seam)

RECORD = "NodeContext<64>"
TU = "main.cpp"
REGISTRY_REL = "MemHeaders/NodeCtxPersistRegistry.hpp"
PERSIST_MACRO = "FOREACH_NODE_PERSIST_FIELD"
EXEMPT_MACRO = "FOREACH_NODE_CTX_PERSIST_EXEMPT"

# The exemption CATEGORIES. Each is phrased as a falsifiable claim so a reviewer knows what
# evidence would refute it — the `ic.actuals` lesson made concrete. Adding a category is a
# deliberate act: it widens what counts as an acceptable reason, so it belongs in review.
CATEGORIES = {
    "RUNTIME_POINTER":      "a pointer/handle re-established at boot; persisting an address across processes is meaningless",
    "REDERIVED_FROM_CFG":   "recomputed from resolved cfg on the first pass after load",
    "DERIVED_EACH_PASS":    "unconditionally overwritten every slow pass BEFORE any read",
    "RECOMPUTED_BEFORE_READ": "recomputed from a PERSISTED field within the same pass that reads it",
    "RESTORED_AT_COMMIT":   "explicitly reconstructed in the load-commit tail from persisted state "
                            "(the category RollingIC_RestoreLockstep created at D-421 step 1)",
    "TRANSIENT_INFLIGHT":   "in-flight intent that restoring would be WRONG, not merely unnecessary",
    "WALL_CLOCK":           "a host-clock stamp with no meaning across a restart",
    "DISPLAY_ONLY":         "read exclusively by TUI/GUI/log emit — never by an execution or risk path",
    "ACCEPTED_RESET":       "an accumulator knowingly reset on restart; the operator has accepted the "
                            "behaviour change and the rationale says what degrades and for how long",
}


class PartitionRefusal(RuntimeError):
    """Cannot run the audit. rc 2 — never rendered as a clean pass."""


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------
def struct_members(record=RECORD, tu=TU):
    """Real `NodeContext` members via clang -fdump-record-layouts (STRICT: absence raises)."""
    try:
        got = run_emitter_nvim(tu, [record], strict=True)
    except EmitterUnavailable as e:
        raise PartitionRefusal(str(e)) from e
    for name, rec in got.items():
        if "members" not in rec:
            raise PartitionRefusal(
                f"emitter returned {name} without a `members` key — the layout emitter is older "
                f"than this guard (needs the D-421 additive key).")
        return name, [(m["name"], m["type"], m["off"]) for m in rec["members"]]
    raise PartitionRefusal(f"no record matched {record}")


def _registry_rows(text, macro, base_dir, arity, what):
    body = _macro_body_resolved(_strip_comments_text(text), macro, base_dir=base_dir)
    if body is None:
        raise PartitionRefusal(
            f"{macro} not found in {REGISTRY_REL} — refusing to compute a complement against a "
            f"registry that is not there (an absent {what} registry would make EVERY member look "
            f"unaccounted, or with the sets swapped, every member look fine).")
    out = []
    for inner in _rows(_strip_comments(body)):
        cols = _args(inner)
        if len(cols) != arity:
            raise PartitionRefusal(
                f"{macro} row has {len(cols)} columns, expected {arity}: {inner.strip()!r}")
        out.append(cols)
    if not out:
        raise PartitionRefusal(f"{macro} parsed to ZERO rows — that is a parse failure, not an "
                               f"empty registry.")
    return out


def persisted_names(root=None):
    """Members COVERED by the wire. PAD rows name no member; a BIT row names a wire byte whose
    backing member is `node_state_flags`, so the covered NAME differs from the row NAME."""
    root = str(root or ENGINE)
    path = os.path.join(root, REGISTRY_REL)
    try:
        text = open(path).read()
    except OSError as e:
        raise PartitionRefusal(f"cannot read {REGISTRY_REL}: {e}")
    rows = _registry_rows(text, PERSIST_MACRO, os.path.dirname(path), 5, "persist")
    covered, notes = set(), []
    for name, _type, skind, _mask, _ckind in rows:
        if skind == "PAD":
            continue                                    # alignment bytes; backs no member
        if skind == "BIT":
            covered.add("node_state_flags")             # the bit's storage IS the member
            notes.append(f"{name} (BIT) -> node_state_flags")
            continue
        covered.add(name)
    return covered, notes


def validate_exempt(rows):
    """Parsed 3-col rows -> {name: (category, rationale)}; raises on an unknown category or a
    rationale too short to be falsifiable. PURE, so the teeth can reach it without a file."""
    out = {}
    for name, cat, why in rows:
        cat = cat.strip()
        if cat not in CATEGORIES:
            raise PartitionRefusal(
                f"{EXEMPT_MACRO} row {name!r} uses unknown category {cat!r}. Known: "
                f"{', '.join(sorted(CATEGORIES))}. Adding a category is a review decision — "
                f"declare it in CATEGORIES with the evidence that would refute it.")
        why = why.strip().strip('"')
        if len(why) < 12:
            raise PartitionRefusal(
                f"{EXEMPT_MACRO} row {name!r} has a rationale of {len(why)} chars. The rationale "
                f"is the whole point of the row — it must say what a reader should verify.")
        out[name] = (cat, why)
    return out


def exempt_rows(root=None):
    """Declared-unpersisted members: X(NAME, CATEGORY, "rationale")."""
    root = str(root or ENGINE)
    path = os.path.join(root, REGISTRY_REL)
    try:
        text = open(path).read()
    except OSError as e:
        raise PartitionRefusal(f"cannot read {REGISTRY_REL}: {e}")
    return validate_exempt(_registry_rows(text, EXEMPT_MACRO, os.path.dirname(path), 3, "exemption"))


# ---------------------------------------------------------------------------
# The classification (pure — the selftest drives THIS, hermetically)
# ---------------------------------------------------------------------------
def classify(members, covered, exempt):
    """-> (unaccounted, stale_exempt, contradiction). All three are RED; each fails differently."""
    names = [m[0] for m in members]
    nameset = set(names)
    unaccounted = [m for m in members if m[0] not in covered and m[0] not in exempt]
    stale_exempt = sorted(n for n in exempt if n not in nameset)
    contradiction = sorted(n for n in exempt if n in covered)
    return unaccounted, stale_exempt, contradiction


def report(record, members, covered, notes, exempt, out=sys.stdout):
    unacc, stale, contra = classify(members, covered, exempt)
    w = out.write
    if notes:
        for n in notes:
            w(f"  note: {n}\n")
    if unacc:
        w(f"\nUNACCOUNTED — {len(unacc)} member(s) of {record} have neither a persist row nor an "
          f"exemption:\n")
        for name, typ, off in unacc:
            w(f"    +{off:<6d} {name:<32s} {typ}\n")
        w("  Either enrol the field in FOREACH_NODE_PERSIST_FIELD (which CHANGES THE WIRE: bump\n"
          "  SHARDED_SNAPSHOT_VERSION + regen the golden in the same commit, H21), or declare it\n"
          f"  in {EXEMPT_MACRO} with a category and a rationale a reviewer can falsify.\n")
    if stale:
        w(f"\nSTALE-EXEMPT — {len(stale)} exemption(s) name something that is not a member:\n")
        for n in stale:
            w(f"    {n:<32s} category={exempt[n][0]}\n")
        w("  The field was renamed or removed. The exemption now protects nothing while still\n"
          "  making the partition read as fully accounted — delete the row, or fix the name.\n")
    if contra:
        w(f"\nCONTRADICTION — {len(contra)} member(s) are BOTH persisted and exempted:\n")
        for n in contra:
            w(f"    {n:<32s} category={exempt[n][0]}\n")
        w("  One of the two declarations is false and this tool cannot tell which. Resolve it by\n"
          "  hand: if the field is on the wire, drop the exemption; if the exemption is right,\n"
          "  removing the row is a WIRE CHANGE (bump + golden, same commit).\n")
    if not (unacc or stale or contra):
        w(f"[node-ctx-partition] GREEN — all {len(members)} {record} members accounted: "
          f"{len(members) - len(exempt)} persisted, {len(exempt)} declared-exempt.\n")
        return 0
    return 1


# ---------------------------------------------------------------------------
# Teeth
# ---------------------------------------------------------------------------
_FAILS = []


def _check(name, cond):
    print(("  ✅ " if cond else "  ❌ ") + name)
    if not cond:
        _FAILS.append(name)


def _selftest():
    M = [("a", "int", 0), ("b", "int", 4), ("c", "int", 8)]

    # 1. the happy path is reachable at all (guards the guard against always-red)
    _check("clean partition -> 0 findings",
           classify(M, {"a", "b"}, {"c": ("DISPLAY_ONLY", "x" * 20)}) == ([], [], []))

    # 2. UNACCOUNTED fires — the founding class (a field added and never enrolled)
    u, s, c = classify(M, {"a", "b"}, {})
    _check("UNACCOUNTED fires on an unenrolled member", [x[0] for x in u] == ["c"] and not s and not c)

    # 3. STALE-EXEMPT fires — an exemption whose subject no longer exists
    u, s, c = classify(M, {"a", "b", "c"}, {"ghost": ("WALL_CLOCK", "x" * 20)})
    _check("STALE-EXEMPT fires on an exemption naming a non-member", s == ["ghost"] and not u and not c)

    # 4. CONTRADICTION fires — both persisted and exempted
    u, s, c = classify(M, {"a", "b", "c"}, {"c": ("DISPLAY_ONLY", "x" * 20)})
    _check("CONTRADICTION fires when a member is both persisted and exempt", c == ["c"] and not u)

    # 5. NON-VACUITY of the exempt set itself: exempting everything must NOT read as clean
    #    unless every name is real. This is the failure mode where somebody "fixes" a red by
    #    bulk-exempting — the stale check is what makes that visible.
    u, s, c = classify(M, set(), {"a": ("DISPLAY_ONLY", "x" * 20), "b": ("DISPLAY_ONLY", "x" * 20),
                                  "c": ("DISPLAY_ONLY", "x" * 20), "typo_d": ("DISPLAY_ONLY", "x" * 20)})
    _check("bulk-exempt with one typo still REDs (stale catches the typo)", s == ["typo_d"])

    # 6. registry parse refusals — an absent/empty registry must REFUSE, never pass empty
    for macro, arity, label in ((PERSIST_MACRO, 5, "persist"), (EXEMPT_MACRO, 3, "exemption")):
        try:
            _registry_rows("// nothing here\n", macro, "/tmp", arity, label)
            _check(f"absent {label} registry REFUSES", False)
        except PartitionRefusal:
            _check(f"absent {label} registry REFUSES", True)

    # 7. an unknown category must REFUSE — categories are a REVIEW surface, not free text.
    #    Without this, "exempt it and write something" is a one-line way to silence a real red.
    try:
        validate_exempt([("a", "MADE_UP_REASON", '"a rationale long enough to pass"')])
        _check("unknown category REFUSES", False)
    except PartitionRefusal:
        _check("unknown category REFUSES", True)

    # 7b. a rationale too short to be falsifiable must REFUSE. "transient" is not a reason.
    try:
        validate_exempt([("a", "DISPLAY_ONLY", '"transient"')])
        _check("stub rationale REFUSES", False)
    except PartitionRefusal:
        _check("stub rationale REFUSES", True)

    # 7c. ...and a WELL-FORMED row must be accepted, or 7/7b would pass vacuously by refusing
    #     everything. The positive control on the negative controls.
    try:
        ok = validate_exempt([("a", "DISPLAY_ONLY", '"read only by the TUI stats panel"')])
        _check("well-formed exemption is ACCEPTED", ok == {"a": ("DISPLAY_ONLY",
                                                                "read only by the TUI stats panel")})
    except PartitionRefusal as e:
        _check(f"well-formed exemption is ACCEPTED ({e})", False)

    # 8. REAL-TREE non-vacuity: the live struct must actually be readable, and the live
    #    registry must actually parse to rows. A tooth that only ever runs on fixtures cannot
    #    tell you the tool works on the thing it is pointed at.
    try:
        rec, members = struct_members()
        covered, _notes = persisted_names()
        _check(f"real tree: {rec} yields members (got {len(members)})", len(members) > 10)
        _check(f"real tree: persist registry yields covered names (got {len(covered)})", len(covered) > 10)
        _check("real tree: the two sets actually overlap (names are comparable, not two vocabularies)",
               len(set(m[0] for m in members) & covered) > 5)
    except PartitionRefusal as e:
        _check(f"real tree readable ({e})", False)

    print(f"{os.path.basename(__file__)} --selftest: "
          + ("ALL TEETH FIRE" if not _FAILS else "FAILURES: " + "; ".join(_FAILS)))
    return 0 if not _FAILS else 2


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true", help="hermetic teeth + real-tree non-vacuity")
    ap.add_argument("--record", default=RECORD)
    ap.add_argument("--tu", default=TU)
    args = ap.parse_args()

    if args.selftest:
        return _selftest()
    try:
        rec, members = struct_members(args.record, args.tu)
        covered, notes = persisted_names()
        exempt = exempt_rows()
    except PartitionRefusal as e:
        print(f"[node-ctx-partition] REFUSAL — {e}", file=sys.stderr)
        return 2
    return report(rec, members, covered, notes, exempt)


if __name__ == "__main__":
    sys.exit(main())
