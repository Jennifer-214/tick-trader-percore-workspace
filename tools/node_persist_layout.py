#!/usr/bin/env python3
"""
node_persist_layout.py — the E.1.2 persist-layout audit (LIBRARY + runnable).

WHY THIS EXISTS (D-302 Option B — the forcing-function architecture)
--------------------------------------------------------------------
The per-node snapshot wire is now specified by ONE ordered registry
(MemHeaders/NodeCtxPersistRegistry.hpp FOREACH_NODE_PERSIST_FIELD) plus three
delegate sub-registries (regime / feeder / confidence). The compile-time
count-locks catch row-COUNT motion, and the frozen byte-golden catches BYTE
motion — but BOTH are vacuous against the one delta this ship itself performs:
a size-neutral, count-neutral row SWAP (drop `node_dd_pct` Money, add
`partner_pending_pnl` Money = net 0 rows, net 0 bytes, and a golden regenerated
in the same commit matches by construction). That triple-vacuity is the D-208
M7 hole. The close (adversarial pass 2026-07-04, D-302): a NAME-INCLUSIVE,
ORDER-SENSITIVE listing of the full flattened wire walk — parent rows AND
delegate-internal rows — frozen as a reviewable golden, plus the PAIRED-BUMP
rule (layout changed ⟹ SHARDED_SNAPSHOT_VERSION bumped in the same commit,
else RED), which lives in check_identifier_retirement.py because that guard
already owns the version's ledger row and the D-394 bless flow.

WHAT THIS MODULE OWNS
  - parse the parent registry text -> ordered (name, type, kind, extra) rows
  - walk INTO the three delegate sub-registries at their wire positions
  - render the canonical flattened LISTING (a list of named rows — never a
    bare digest: the golden must DIFF in rows, and a count is stale the
    commit it's written; feedback_name_members_never_tallies)
  - diff current-vs-golden with named verdicts (DROPPED / ADDED / CHANGED /
    REORDERED — the count-neutral name-swap surfaces as DROPPED+ADDED pair)
  - --selftest: hermetic planted-mutation teeth + real-tree non-vacuity

WHAT IT DELIBERATELY DOES NOT DO
  - compute byte sizes. Symbolic count tokens (ROLLING_IC_MAX_WINDOW / MAX_WINDOW)
    stay verbatim in the listing — which means a WIDTH change to one of those
    constants is listing-INVISIBLE (a-class R3-b, demonstrated). That seam is
    closed elsewhere: the constants' VALUES are enrolled as `wire-const` rows in
    check_identifier_retirement.py's SOURCES (a width change REDs at Check H),
    and byte truth belongs to the runtime byte-golden test.
  - auto-bless. Rewrites of the golden route through bless.py (D-394: TTY,
    shown diff, typed confirmation); --emit-initial exists ONLY for first
    establishment and refuses if the golden already exists. Honest scope
    (a-class R3-d): these controls gate the TOOL paths — a raw
    `--print > golden` shell redirect remains physically possible; what makes
    that unprofitable is that the golden is a REVIEWED, committed artifact
    (the redirect shows as a golden diff at workspace commit) plus the
    symmetric Check-H red when a golden is edited against an unchanged
    registry. "Structurally harder + always visible", not "impossible".

USAGE
  node_persist_layout.py                 diff current layout vs the golden (rc 0 match / 1 drift / 2 refusal)
  node_persist_layout.py --print         print the current canonical listing
  node_persist_layout.py --bless         re-bless the golden via the shared D-394 flow (TTY)
  node_persist_layout.py --emit-initial  write the golden IF ABSENT (first establishment only)
  node_persist_layout.py --selftest      hermetic teeth + real-tree non-vacuity

rc contract: 0 = ok · 1 = drift (named rows) · 2 = REFUSAL (unparseable /
missing source / missing golden on verify) — a broken parse is never an
empty-set pass (Class 57).
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from foxroots import ENGINE  # noqa: E402  (the ONE repo-root resolver — D-375)

GOLDEN = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "goldens", "node_persist_layout.txt")

PARENT = ("MemHeaders/NodeCtxPersistRegistry.hpp", "FOREACH_NODE_PERSIST_FIELD")
# STORAGE_MASK delegate token -> (file, macro). The registry's DELEGATE rows
# carry the walker fn-family prefix; the same token keys this map.
DELEGATE_SOURCES = {
    "RegimeState":       ("Strategies/RegimeDetector.hpp",   "FOREACH_REGIME_PERSIST_FIELD"),
    "RegressionFeederX": ("ML_Headers/LinearRegression3X.hpp", "FOREACH_FEEDER_PERSIST_FIELD"),
    "ConfidenceScorer":  ("ML_Headers/ConfidenceScore.hpp",  "FOREACH_CONFIDENCE_PERSIST_FIELD"),
}


class LayoutRefusal(RuntimeError):
    """Parse failure — the audit CANNOT run. Callers must fail loud (rc 2),
    never render this as a clean/empty pass."""


# ---------------------------------------------------------------------------
# Macro-text parsing (the SSoT copies — check_identifier_retirement.py imports
# these three; keep them dependency-free).
# ---------------------------------------------------------------------------
def _macro_body(text, macro):
    """Return the backslash-continued body of `#define MACRO(X) ...`, or None."""
    m = re.search(r'#\s*define\s+' + re.escape(macro) + r'\s*\(\s*X\s*\)', text)
    if not m:
        return None
    lines = []
    for line in text[m.end():].splitlines():
        lines.append(line)
        if not line.rstrip().endswith('\\'):
            break
    return "\n".join(lines)


def _rows(body):
    """Split a macro body into the inner-text of each top-level `X( ... )` invocation."""
    out, i = [], 0
    while True:
        j = body.find("X(", i)
        if j < 0:
            break
        depth, k = 0, j + 1
        while k < len(body):
            if body[k] == '(':
                depth += 1
            elif body[k] == ')':
                depth -= 1
                if depth == 0:
                    break
            k += 1
        out.append(body[j + 2:k])
        i = k + 1
    return out


def _args(inner):
    """Top-level comma split (respecting nested parens)."""
    args, depth, cur = [], 0, []
    for c in inner:
        if c == '(':
            depth += 1; cur.append(c)
        elif c == ')':
            depth -= 1; cur.append(c)
        elif c == ',' and depth == 0:
            args.append("".join(cur).strip()); cur = []
        else:
            cur.append(c)
    args.append("".join(cur).strip())
    return args


def _strip_comments(body):
    """Remove /* ... */ blocks (the registry's section comments) so a comment
    containing 'X(' can never fabricate a row, and '//' tails per line."""
    body = re.sub(r'/\*.*?\*/', ' ', body, flags=re.S)
    return re.sub(r'//[^\n]*', ' ', body)


def _strip_comments_text(text):
    """Comment-strip the WHOLE FILE text before the `#define` search, PRESERVING
    newline count (backslash-continuation structure must survive). Closes the
    a-class R1-a comment-hijack vacuity: a doc block quoting a stale
    `#define FOREACH_...` ABOVE the real one would otherwise be parsed INSTEAD
    of the live registry — and every later registry edit would diff GREEN
    forever (Class-51-B″, wrong-region scan)."""
    text = re.sub(r'/\*.*?\*/', lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)
    return re.sub(r'//[^\n]*', '', text)


def _read(root, rel):
    path = os.path.join(root, rel)
    try:
        with open(path) as f:
            return f.read()
    except OSError as e:
        raise LayoutRefusal(f"cannot read {rel}: {e}")


# ---------------------------------------------------------------------------
# The layout walk
# ---------------------------------------------------------------------------
def _parse_sub(root, rel, macro):
    """Delegate sub-registry rows: X(name, type, count_token) -> [(name, type, count)]."""
    body = _macro_body(_strip_comments_text(_read(root, rel)), macro)
    if body is None:
        raise LayoutRefusal(f"{macro} not found in {rel}")
    rows = []
    for inner in _rows(_strip_comments(body)):
        a = _args(inner)
        # EXACT arity (a-class R1-c): `< 3` silently ATE the count token when a
        # future comma-bearing template type (`Pair<A,B>`) mis-split — a width
        # mutation then diffed GREEN. Symmetric with the parent's `!= 5`.
        if len(a) != 3 or not a[0]:
            raise LayoutRefusal(f"{macro}: malformed row `X({inner.strip()})` in {rel} "
                                f"(expected 3-tuple, got {len(a)} args)")
        rows.append((a[0], a[1], a[2]))
    if not rows:
        raise LayoutRefusal(f"{macro} in {rel} parsed to ZERO rows")
    return rows


def parse_layout(root=None, parent=PARENT, delegates=DELEGATE_SOURCES):
    """Flattened ordered wire walk.
    Returns [(path, type, kind, extra)] where path is `name` for parent rows and
    `parent_name/sub_name` for delegate-internal rows; extra = BIT mask token /
    PAD width / delegate count token / '' for scalars."""
    root = str(root or ENGINE)
    body = _macro_body(_strip_comments_text(_read(root, parent[0])), parent[1])
    if body is None:
        raise LayoutRefusal(f"{parent[1]} not found in {parent[0]}")
    flat = []
    for inner in _rows(_strip_comments(body)):
        a = _args(inner)
        if len(a) != 5 or not a[0]:
            raise LayoutRefusal(f"{parent[1]}: malformed row `X({inner.strip()})` — expected 5-tuple")
        name, typ, kind, mask, ckind = a
        if kind == "DELEGATE":
            if mask not in delegates:
                raise LayoutRefusal(f"DELEGATE token `{mask}` (row {name}) has no source mapping")
            flat.append((name, typ, "DELEGATE:" + ckind, mask))
            for sn, st, sc in _parse_sub(root, *delegates[mask]):
                flat.append((f"{name}/{sn}", st, "SUB", sc))
        elif kind in ("SCALAR", "BIT", "PAD"):
            flat.append((name, typ, kind + ":" + ckind, mask if kind in ("BIT", "PAD") else ""))
        else:
            raise LayoutRefusal(f"row {name}: unknown STORAGE_KIND `{kind}`")
    if not flat:
        raise LayoutRefusal(f"{parent[1]} parsed to ZERO rows")
    return flat


def listing_lines(flat):
    """Canonical golden content. Index prefix IS the order — a reorder changes
    lines even when the membership is identical."""
    lines = [
        "# node_persist_layout.txt — the frozen per-node persist WIRE LISTING (node_persist_layout.py).",
        "# NAME-inclusive + ORDER-sensitive + delegate-internal (the D-302 net over the count/size/golden",
        "# triple-vacuity: a count-neutral row SWAP diffs HERE by name). A change REQUIRES a",
        "# SHARDED_SNAPSHOT_VERSION bump in the same commit (paired-bump rule,",
        "# check_identifier_retirement.py) — re-bless via node_persist_layout.py --bless (D-394 TTY flow).",
        "# format: index|path|type|kind|extra",
        "",
    ]
    for i, (path, typ, kind, extra) in enumerate(flat):
        lines.append(f"{i:03d}|{path}|{typ}|{kind}|{extra}")
    return lines


def load_golden(path=GOLDEN):
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return [ln.rstrip("\n") for ln in f]


def _data_rows(lines):
    """golden/listing lines -> {path: (idx, type, kind, extra)} + ordered path list."""
    by_name, order = {}, []
    for ln in lines:
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        parts = ln.split("|")
        if len(parts) != 5:
            raise LayoutRefusal(f"malformed golden line: {ln}")
        idx, path, typ, kind, extra = parts
        if path in by_name:
            # a-class R2: a duplicated path would dict-collapse and mis-report as
            # REORDERED — refuse honestly instead (also hardens vs a mangled golden).
            raise LayoutRefusal(f"duplicate row path `{path}` in listing")
        by_name[path] = (int(idx), typ, kind, extra)
        order.append(path)
    return by_name, order


def diff_lines(golden_lines, current_lines):
    """Named row-level diff. Empty list = identical."""
    g, g_order = _data_rows(golden_lines)
    c, c_order = _data_rows(current_lines)
    out = []
    for path in g_order:
        if path not in c:
            out.append(f"DROPPED   {path}  (was {g[path][1]} {g[path][2]} @{g[path][0]:03d})")
    for path in c_order:
        if path not in g:
            out.append(f"ADDED     {path}  ({c[path][1]} {c[path][2]} @{c[path][0]:03d})")
    for path in c_order:
        if path in g:
            gi, gt, gk, ge = g[path]
            ci, ct, ck, ce = c[path]
            if (gt, gk, ge) != (ct, ck, ce):
                out.append(f"CHANGED   {path}  {gt}|{gk}|{ge} -> {ct}|{ck}|{ce}")
    # Reorder: same-membership rows whose relative order moved. Only meaningful
    # when membership overlaps; report position motion for surviving rows.
    shared = [p for p in g_order if p in c]
    shared_cur = [p for p in c_order if p in g]
    if shared != shared_cur:
        for p in shared:
            if g[p][0] != c[p][0] and not any(l.startswith(("DROPPED", "ADDED")) and f" {p} " in l for l in out):
                out.append(f"REORDERED {p}  @{g[p][0]:03d} -> @{c[p][0]:03d}")
    return out


# ---------------------------------------------------------------------------
# Selftest (hermetic planted-mutation teeth + real-tree non-vacuity)
# ---------------------------------------------------------------------------
_FIXTURE_PARENT = """\
#define FOREACH_TEST_PERSIST_FIELD(X)                       \\
    /* section comment with sneaky X( inside — must not parse */ \\
    X(alpha,       uint8_t,  SCALAR,   0,            COMMIT)     \\
    X(_pad_a,      uint8_t,  PAD,      3,            NO_COMMIT)  \\
    X(bravo,       Money,    SCALAR,   0,            COMMIT)     \\
    X(kill_bit,    uint8_t,  BIT,      KILL_TRIPPED, COMMIT)     \\
    X(sub_thing,   SubT<F>,  DELEGATE, SubT,         COMMIT)
"""
_FIXTURE_SUB = """\
#define FOREACH_SUB_PERSIST_FIELD(X)   \\
    X(inner_one, double, 1)            \\
    X(inner_arr, double, MAX_W)
"""


def _selftest():
    import tempfile

    fails = []

    def check(name, cond):
        print(f"  {'✅' if cond else '❌'} {name}")
        if not cond:
            fails.append(name)

    def make_tree(parent_text, sub_text):
        d = tempfile.mkdtemp(prefix="npl_selftest_")
        os.makedirs(os.path.join(d, "MemHeaders"), exist_ok=True)
        os.makedirs(os.path.join(d, "Sub"), exist_ok=True)
        with open(os.path.join(d, "MemHeaders", "P.hpp"), "w") as f:
            f.write(parent_text)
        with open(os.path.join(d, "Sub", "S.hpp"), "w") as f:
            f.write(sub_text)
        return d

    P = ("MemHeaders/P.hpp", "FOREACH_TEST_PERSIST_FIELD")
    D = {"SubT": ("Sub/S.hpp", "FOREACH_SUB_PERSIST_FIELD")}

    # clean parse: 5 parent rows -> 5 + 2 sub = 7 flattened; comment never a row
    base = make_tree(_FIXTURE_PARENT, _FIXTURE_SUB)
    flat = parse_layout(base, P, D)
    check("clean fixture parses 7 flattened rows (comment X( ignored)", len(flat) == 7)
    gold = listing_lines(flat)
    check("clean fixture diffs empty vs itself", diff_lines(gold, listing_lines(parse_layout(base, P, D))) == [])

    def mutated(parent_text=None, sub_text=None):
        t = make_tree(parent_text or _FIXTURE_PARENT, sub_text or _FIXTURE_SUB)
        return diff_lines(gold, listing_lines(parse_layout(t, P, D)))

    # DROP a parent row
    d = mutated(_FIXTURE_PARENT.replace(
        "    X(bravo,       Money,    SCALAR,   0,            COMMIT)     \\\n", ""))
    check("planted DROP fires (bravo)", any(x.startswith("DROPPED") and "bravo" in x for x in d))

    # ADD a parent row
    d = mutated(_FIXTURE_PARENT.replace(
        "    X(kill_bit,",
        "    X(charlie,     uint32_t, SCALAR,   0,            COMMIT)     \\\n    X(kill_bit,"))
    check("planted ADD fires (charlie)", any(x.startswith("ADDED") and "charlie" in x for x in d))

    # the COUNT-NEUTRAL NAME-SWAP (the triple-vacuity case): same type/kind, new name
    d = mutated(_FIXTURE_PARENT.replace("X(bravo,       Money,", "X(delta,       Money,"))
    check("count-neutral name-swap fires as DROPPED+ADDED pair",
          any("DROPPED" in x and "bravo" in x for x in d) and any("ADDED" in x and "delta" in x for x in d))

    # TYPE change
    d = mutated(_FIXTURE_PARENT.replace("X(alpha,       uint8_t,", "X(alpha,       uint32_t,"))
    check("planted TYPE change fires (alpha)", any(x.startswith("CHANGED") and "alpha" in x for x in d))

    # REORDER two rows (swap alpha and bravo blocks; membership identical)
    swapped = _FIXTURE_PARENT.replace(
        "    X(alpha,       uint8_t,  SCALAR,   0,            COMMIT)     \\\n"
        "    X(_pad_a,      uint8_t,  PAD,      3,            NO_COMMIT)  \\\n"
        "    X(bravo,       Money,    SCALAR,   0,            COMMIT)     \\\n",
        "    X(bravo,       Money,    SCALAR,   0,            COMMIT)     \\\n"
        "    X(alpha,       uint8_t,  SCALAR,   0,            COMMIT)     \\\n"
        "    X(_pad_a,      uint8_t,  PAD,      3,            NO_COMMIT)  \\\n")
    d = mutated(swapped)
    check("planted REORDER fires", any(x.startswith("REORDERED") for x in d))

    # DELEGATE-INTERNAL drop (walk-into proof)
    d = mutated(sub_text=_FIXTURE_SUB.replace("    X(inner_one, double, 1)            \\\n", ""))
    check("delegate-internal DROP fires (sub_thing/inner_one)",
          any("DROPPED" in x and "sub_thing/inner_one" in x for x in d))

    # COMMENT-HIJACK (a-class R1-a): a stale full `#define` quoted in a comment
    # ABOVE the real registry must NOT be parsed instead of it.
    hijack = ("/* stale doc copy — must be ignored:\n"
              "#define FOREACH_TEST_PERSIST_FIELD(X) X(fake_row, uint8_t, SCALAR, 0, COMMIT)\n"
              "*/\n") + _FIXTURE_PARENT
    flat_h = parse_layout(make_tree(hijack, _FIXTURE_SUB), P, D)
    check("comment-quoted stale #define cannot hijack the parse",
          len(flat_h) == 7 and flat_h[0][0] == "alpha"
          and not any(r[0] == "fake_row" for r in flat_h))

    # REFUSALS — never an empty pass
    try:
        parse_layout(make_tree(_FIXTURE_PARENT.replace("SubT,         COMMIT", "Ghost,        COMMIT"), _FIXTURE_SUB), P, D)
        check("unmapped DELEGATE token REFUSES", False)
    except LayoutRefusal:
        check("unmapped DELEGATE token REFUSES", True)
    try:
        parse_layout(make_tree("// no macro here at all\n", _FIXTURE_SUB), P, D)
        check("missing parent macro REFUSES", False)
    except LayoutRefusal:
        check("missing parent macro REFUSES", True)
    # a-class R1-c: a comma-bearing template type mis-splits a 3-tuple sub-row
    # into 4 args — exact arity must REFUSE, never silently eat the count token.
    try:
        parse_layout(make_tree(_FIXTURE_PARENT,
                               _FIXTURE_SUB.replace("X(inner_one, double, 1)",
                                                    "X(inner_one, Pair<A,B>, 1)")), P, D)
        check("comma-template sub-row REFUSES (exact arity)", False)
    except LayoutRefusal:
        check("comma-template sub-row REFUSES (exact arity)", True)

    # REAL-TREE non-vacuity: the actual registry parses, delegates resolve,
    # and the flattened walk is at least parent(29) + regime(7)+feeder(3)+confidence(7) rows.
    try:
        real = parse_layout()
        parent_rows = [r for r in real if r[2] != "SUB"]
        sub_rows = [r for r in real if r[2] == "SUB"]
        check("REAL registry: 29 parent rows", len(parent_rows) == 29)
        check("REAL registry: 17 delegate-internal rows (7+3+7)", len(sub_rows) == 17)
        # Full 5-element order (a-class R4: the [0]-only form was a Class-51-C
        # label-proxy — relocating the doubles AFTER confidence still passed it).
        check("REAL registry: interleave doubles sit between feeder and confidence",
              [r[0] for r in real if r[0] in ("staged_prediction", "active_prediction",
                                              "last_confidence", "pnl_feeder", "confidence")]
              == ["pnl_feeder", "staged_prediction", "active_prediction",
                  "last_confidence", "confidence"])
    except LayoutRefusal as e:
        check(f"REAL registry parses ({e})", False)

    print(f"node_persist_layout --selftest: {'ALL TEETH FIRE' if not fails else 'FAILURES: ' + ', '.join(fails)}")
    return 0 if not fails else 1


# ---------------------------------------------------------------------------
def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else ""

    if arg == "--selftest":
        return _selftest()

    try:
        cur = listing_lines(parse_layout())
    except LayoutRefusal as e:
        print(f"[node-persist-layout] REFUSAL — audit could not run: {e}", file=sys.stderr)
        return 2

    if arg == "--print":
        print("\n".join(cur))
        return 0

    if arg == "--bless":
        import bless as bless_mod
        return bless_mod.bless(GOLDEN, cur, "node-persist-layout")

    if arg == "--emit-initial":
        if os.path.exists(GOLDEN):
            print(f"[node-persist-layout] REFUSED — golden already exists at {GOLDEN}; "
                  f"rewrites go through --bless (D-394).", file=sys.stderr)
            return 2
        os.makedirs(os.path.dirname(GOLDEN), exist_ok=True)
        with open(GOLDEN, "w") as f:
            f.write("\n".join(cur).rstrip() + "\n")
        print(f"[node-persist-layout] initial golden established at {GOLDEN} "
              f"({sum(1 for l in cur if l and not l.startswith('#'))} rows).")
        return 0

    gold = load_golden()
    if gold is None:
        print(f"[node-persist-layout] REFUSAL — no golden at {GOLDEN}; establish via --emit-initial.",
              file=sys.stderr)
        return 2
    d = diff_lines(gold, cur)
    if d:
        print("[node-persist-layout] LAYOUT DRIFT vs the frozen golden:", file=sys.stderr)
        for x in d:
            print(f"  ✗ {x}", file=sys.stderr)
        print("A persist-layout change requires a SHARDED_SNAPSHOT_VERSION bump in the SAME commit\n"
              "(paired-bump rule, check_identifier_retirement.py) + a golden re-bless "
              "(node_persist_layout.py --bless) + regen/RENAME of the byte-golden.", file=sys.stderr)
        return 1
    rows = sum(1 for l in cur if l and not l.startswith("#"))
    print(f"[node-persist-layout] GREEN — {rows} flattened wire rows match the frozen golden.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
