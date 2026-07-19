#!/usr/bin/env python3
"""check_code_tag_blocks.py — validates in-code [CATEGORY] tag-blocks (the E.1.2.A schema).

The code-side sister of check_doc_metadata.py: same ONE vocabulary (reused via
load_vocabulary), applied to C++ comment tag-blocks per
`DESIGN_SPECS/doc-disciplines/in-code-documentation-schema.md`.

This is the FIRST increment (the pilot keystone). It implements the structural +
vocab checks that are stable against the current grammar:
  1. CATEGORY validity — every tag-line's token[0] is in the closed CATEGORY set.
  2. Closer matching    — every FULL-block opener ([FUNCTION]/[STRUCT]/[REGISTRY]/[ENUM]/
                          [TYPE]/[STRATEGY]) + [CODE] has a matching, same-named [END_*]
                          (the fold-range / cursor-tracking contract). LIGHT units
                          ([MACRO]/[TEST]/[ASSERT]) + the orient-only [FILE] carry no closer.
  3. [TAG] vocab        — [TAG] values resolve in doc-tag-vocabulary (UPPER_SNAKE↔lower-hyphen).
  4. One-category-per-line — token[0] is the only top-level CATEGORY on the line.
  5. Graceful degrade   — a malformed bracket / non-tag comment is skipped, never a crash.
Increment 2 ADDS [REFERENCE]-resolution (spec § reference-subcats): every
[REFERENCE]/[FUTURE_WORK]/[SUPPORTING_DOCS] id resolves against a frozen, workspace-rooted
index (specs / memories / decisions / invariants / tech-debt / classes / plans / parity);
subcat MEMBERSHIP is DERIVED from the spec's ```reference-subcats``` fence (fold a row there
= tracked here automatically); AUDIT/SOURCE/URL are existence-unchecked (never red).
Decoupled from the block-parse loop by design (D-317).
DEFERRED still (need generators): ladder-order, DERIVED-vs-ground-truth drift, the
prose-vs-DERIVED codegen lint (spec § CI-enforcement items 3 + 5).

The parse rule is the ONE innermost-bracket regex, exactly as the plugin's tagadapter
will use — so this validator and the plugin read the same grammar (unified surface).

Exit: 0 = clean · 1 = violations · 2 = script error / vocab missing / selftest failed.
Usage:
  python3 tools/check_code_tag_blocks.py --selftest        # prove it catches violations
  python3 tools/check_code_tag_blocks.py --paths a.hpp ...  # check specific files
  python3 tools/check_code_tag_blocks.py                    # scan the engine source dirs
"""
import re
import sys
import argparse
from pathlib import Path

# Reuse the SHARED vocab loader + engine root — one grammar, validated on docs AND code.
sys.path.insert(0, str(Path(__file__).absolute().parent))
from check_doc_metadata import load_vocabulary, ENGINE, WORKSPACE, MEMORY_DIR  # noqa: E402

# The innermost-bracket parse rule (spec § "The three invariants" #1). Non-innermost
# list-grouping [[a] [b]] is skipped for free → token[0]=CATEGORY, rest=values.
BRACKET_RE = re.compile(r"\[([^\[\]]+)\]")
# A structured tag-line: a // comment whose first non-space payload is a bracket token.
TAG_LINE_RE = re.compile(r"^\s*//\s*(\[.*)$")
# A ==== major bar closes a freeform content-region ([COMMENT]/[DIAGRAM] body).
MAJOR_BAR_RE = re.compile(r"^\s*//=+\s*$")

# Closed top-level CATEGORY set (spec § Category set + this session's D-308..D-313 folds).
# Grammar is locked; VALUES (under [TAG]/[REFERENCE]/[DERIVED]) grow in the vocab, not here.
# FULL-block unit types per the locked v1.0 node model (D-339/D-340/D-346): each requires a
# matching, same-named [END_*]. LIGHT units ([MACRO]/[TEST]/[ASSERT]) + the orient-only
# [FILE] carry no closer, so they are NOT openers. [CODE] is the nameless body delimiter.
OPENERS = {"FUNCTION", "STRUCT", "REGISTRY", "ENUM", "TYPE", "STRATEGY", "CODE"}
# Unit types a block can open with (node model + LIGHT units + [FILE]) — the code-tag-index
# inventory set (collect_file_tags); closers are enforced only for the OPENERS subset above.
UNIT_TYPES = {"FILE", "STRUCT", "FUNCTION", "REGISTRY", "ENUM", "TYPE", "MACRO", "TEST",
              "STRATEGY", "ASSERT"}
SCHEMA_PATH = WORKSPACE / "DESIGN_SPECS" / "doc-disciplines" / "in-code-documentation-schema.md"

# --- [REFERENCE]-resolution (increment 2): frozen canonical ref-source paths ------------------
# The directory layout is frozen (operator, 2026-07-05: "use path resolvers"), so every ref
# source resolves from a WORKSPACE-rooted canonical path — NOT a bare find under ENGINE. WHY:
# the engine-side DOCS/ symlinks in only individual files (TECH_DEBT.md yes, the tech-debt/
# SUBDIR no), and DESIGN_SPECS/plans are whole-dir symlinks → a symlink-blind walk under ENGINE
# silently misses sources. check_doc_metadata owns ENGINE/WORKSPACE/MEMORY_DIR (the path SSoT);
# these derive the rest. A layout move = a one-line edit here (path-resolver discipline).
CLAUDE_MD        = ENGINE / "CLAUDE.md"                        # Hard-Invariants table (symlinked from workspace)
DESIGN_SPECS_DIR = WORKSPACE / "DESIGN_SPECS"
PLANS_DIR        = WORKSPACE / "plans"
CLASS_DOC        = WORKSPACE / "DOCS" / "RECURRING_BUG_PATTERNS.md"
CLASS_SUBFILE_DIR = WORKSPACE / "DOCS" / "recurring-bug-patterns"             # per-class subfiles (class-NN-*.md, file-size-split Stage-3)
TECHDEBT_FILES   = [WORKSPACE / "DOCS" / "TECH_DEBT.md",
                    *sorted((WORKSPACE / "DOCS" / "tech-debt").glob("*.md"))]  # the split ledger lives ONLY here
PARITY_DOC       = WORKSPACE / "DOCS" / "PARITY_ISSUES.md"                    # "id: PARITY-<n>" rows (D-345)

# Subcats that MUST be non-empty in a healthy repo: a vacuous load (0 ids) = a BROKEN source path,
# NOT "no refs exist" — refusing to scan avoids the Class-51 false-green where every ref of a subcat
# passes because its index silently loaded empty. AUDIT/SOURCE/URL are legitimately None
# (existence-unchecked per the spec's reference-subcats table).
REF_MUST_POPULATE = ("DESIGN_SPEC", "MEMORY", "DECISION", "INVARIANT", "TECH_DEBT", "CLASS", "PLAN", "PARITY")


def load_ref_subcats():
    """DERIVE [REFERENCE] subcat MEMBERSHIP from the spec's ```reference-subcats``` fence (col 1
    of each row) — single-source per the spec: folding a subcat the resolver already handles =
    one row THERE, zero edits here (the validator lagging the D-345 PARITY/SOURCE/URL widening
    is the drift class this closes). Resolution BEHAVIOR per subcat stays code
    (load_reference_index — the source SHAPES differ); a fenced subcat with no index there is
    existence-unchecked (never red). Returns None if the fence is unloadable (main() errors,
    exactly like the category-set load)."""
    try:
        text = SCHEMA_PATH.read_text(encoding="utf-8")
    except (IOError, OSError):
        return None
    m = re.search(r"```reference-subcats\n(.*?)```", text, re.DOTALL)
    if not m:
        return None
    subs = set()
    for row in m.group(1).split("\n"):
        row = row.split("#")[0].strip()
        if row:
            tok = row.split()[0]
            if re.fullmatch(r"[A-Z][A-Z_]*", tok):
                subs.add(tok)
    return subs or None


def load_categories():
    """DERIVE the closed CATEGORY set from the spec's ```category-set``` SSoT block
    (single-source — the validator READS the grammar, never mirrors it; folding a
    disposition category = one token in the spec, zero validator edits). [END_*]
    closers are validated by prefix, not listed."""
    try:
        text = SCHEMA_PATH.read_text(encoding="utf-8")
    except (IOError, OSError):
        return None
    m = re.search(r"```category-set\n(.*?)```", text, re.DOTALL)
    if not m:
        return None
    cats = set()
    for row in m.group(1).split("\n"):
        for tok in row.split("#")[0].split():
            if re.fullmatch(r"[A-Z][A-Z_]*", tok):
                cats.add(tok)
    return cats or None


def _upper_snake_to_vocab(tok):
    """Code renders tags UPPER_SNAKE ([SLOW_PATH]); the vocab stores lower-hyphen
    (slow-path). Deterministic map (D-306)."""
    return tok.strip().lower().replace("_", "-")


def _basenames(paths):
    """The set of file stems (basename minus .md) for a path iterable."""
    return {p.stem for p in paths}


def load_reference_index():
    """Load-once membership sets for [REFERENCE]/[FUTURE_WORK]/[SUPPORTING_DOCS] id-resolution
    — one per subcat, from the FROZEN workspace paths (spec § reference-subcats). Each value is
    a set of valid ids (already normalized to its subcat's form); AUDIT → None (existence-
    unchecked, never red). A subcat whose source fails to load also maps to None, so it is
    SKIPPED rather than flagging every id as a false-dangling (graceful — mirrors validate_file)."""
    def _read(p):
        try:
            return Path(p).read_text(encoding="utf-8", errors="replace")
        except (IOError, OSError):
            return ""
    idx = {}
    # INVARIANT — the leading H<n> cell of each Hard-Invariants table row in CLAUDE.md (H1..H22).
    idx["INVARIANT"] = set(re.findall(r"^\|\s*\*{0,2}(H\d+)", _read(CLAUDE_MD), re.M)) or None
    # DECISION — the DEFINING sentinels across the decision-log UNION (D-numbers restart per
    # log, so resolve against the union; the C/F correction family resolves too). Membership only.
    decisions = set()
    for log in PLANS_DIR.glob("*/decision-logs/*.md"):
        decisions.update(re.findall(r"<!--\s*[DCF/]+\s*:\s*([DCF]-\d+)\s*-->", _read(log)))
    idx["DECISION"] = decisions or None
    # DESIGN_SPEC / MEMORY — kebab / snake basenames.
    idx["DESIGN_SPEC"] = _basenames(DESIGN_SPECS_DIR.rglob("*.md")) or None
    idx["MEMORY"]      = (_basenames(MEMORY_DIR.glob("*.md")) if MEMORY_DIR else None) or None
    # TECH_DEBT — padding-normalized ints (TECH_DEBT-005 ≡ TECH_DEBT-5); split ledger under WORKSPACE.
    td = set()
    for f in TECHDEBT_FILES:
        td.update(int(n) for n in re.findall(r"TECH_DEBT-(\d+)", _read(f)))
    idx["TECH_DEBT"] = td or None
    # CLASS — bare ints, zero-pad-insensitive. UNION of the main catalog's inline "Class <n>" mentions
    # AND the per-class subfile names (recurring-bug-patterns/class-NN-*.md, the file-size-split Stage-3
    # structure): a subfile-only class (e.g. 23) is NOT spelled in the main doc, so globbing the subfile
    # numbers is what makes every [CLASS]_[N] resolve — else corpus-wide false-dangling.
    class_nums = {int(n) for n in re.findall(r"\bClass 0*(\d+)\b", _read(CLASS_DOC))}
    for _p in CLASS_SUBFILE_DIR.glob("class-*.md"):
        _m = re.match(r"class-(\d+)", _p.name)
        if _m:
            class_nums.add(int(_m.group(1)))
    idx["CLASS"] = class_nums or None
    # PLAN — basenames (a "/"-bearing id is resolved as a path at check-time instead).
    idx["PLAN"] = _basenames(PLANS_DIR.rglob("*.md")) or None
    # PARITY — padding-normalized ints from the parity ledger ("id: PARITY-<n>"; D-345 widening).
    idx["PARITY"] = {int(n) for n in re.findall(r"^id:\s*PARITY-(\d+)", _read(PARITY_DOC), re.M)} or None
    idx["AUDIT"] = None    # existence-unchecked (no single audit ledger)
    idx["SOURCE"] = None   # external repo / venue docs / .py:line provenance — existence-unchecked (D-345)
    idx["URL"] = None      # external http(s) link — existence-unchecked (D-345)
    return idx


def _ref_resolves(subcat, rid, members):
    """True if id `rid` is a member of `subcat`'s set, applying that subcat's normalization."""
    rid = rid.strip()
    if subcat in ("INVARIANT", "DECISION"):
        return rid in members
    if subcat in ("DESIGN_SPEC", "MEMORY"):
        return (rid[:-3] if rid.endswith(".md") else rid) in members
    if subcat in ("TECH_DEBT", "CLASS", "PARITY"):
        m = re.search(r"(\d+)", rid)
        return bool(m) and int(m.group(1)) in members
    if subcat == "PLAN":
        if "/" in rid:                                   # path-form → existence under the tree
            return (PLANS_DIR / rid).exists() or (WORKSPACE / rid).exists()
        return (rid[:-3] if rid.endswith(".md") else rid) in members
    return True


# A [SUPPORTING_DOCS] block-item line: `//   - [SUBCAT]_[id]` (the leading `- ` sits OUTSIDE the
# brackets, so validate_file's TAG_LINE_RE — which needs `[` first — skips it; the resolver owns it).
_BLOCK_ITEM_RE = re.compile(r"^\s*//\s*-\s*\[")


def resolve_references(path, ref_index, ref_subcats):
    """Flag every [REFERENCE]/[FUTURE_WORK]/[SUPPORTING_DOCS] id that does NOT resolve to a real
    workspace artifact. DECOUPLED from validate_file's block-parse loop (spec + D-317): the
    resolver does NOT honor [COMMENT]/[DIAGRAM] prose state, because a [SUPPORTING_DOCS] block
    lives INSIDE the [COMMENT] region — the block-parser skips it as prose, so a separate pass
    must see it. Same mixed-state gate (un-converted / exempt file = not policed). Subcat
    membership = `ref_subcats` (fence-derived); an index-less member (AUDIT/SOURCE/URL) never
    reds. Graceful: never raises."""
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except (IOError, OSError):
        return []
    if "[SCHEMA]_[" not in text or "[SCHEMA]_[exempt" in text:
        return []
    viols = []
    for lineno, raw in enumerate(text.split("\n"), 1):
        if "//" not in raw:
            continue
        toks = _line_tokens(raw)
        if not toks:
            continue
        if toks[0] in ("REFERENCE", "FUTURE_WORK"):
            if len(toks) < 3:                     # need SUBCAT + ≥1 id, else malformed → skip (graceful)
                continue
            subcat, ids = toks[1], toks[2:]
        elif toks[0] in ref_subcats and _BLOCK_ITEM_RE.match(raw):
            subcat, ids = toks[0], toks[1:]
        else:
            continue
        if subcat == "AUDIT":                     # existence-unchecked (no ledger)
            continue
        if subcat not in ref_subcats:
            viols.append(f"{path}:{lineno}  UNKNOWN [REFERENCE] subcat [{subcat}]")
            continue
        members = ref_index.get(subcat)
        if members is None:                       # source unavailable → don't emit false-danglings
            continue
        for rid in ids:
            if not _ref_resolves(subcat, rid, members):
                viols.append(f"{path}:{lineno}  dangling [{subcat}]_[{rid}] — no such "
                             f"{subcat.lower().replace('_', '-')}")
    return viols


def _line_tokens(payload):
    """Innermost-bracket tokens on a line, in order. token[0] is the CATEGORY."""
    return [m.group(1).strip() for m in BRACKET_RE.finditer(payload)]


def engine_source_files():
    """Every engine source file the tag tooling scans (drift-proof — a new dir is auto-included;
    vendored deps + build outputs excluded; no hardcoded file/dir allow-list). Shared by the
    validator scan (main) AND the code-tag-index generator (rebuild_doc_indexes) — one
    file-list, never a second copy.

    PLUS the schema-golden fixture dir, added EXPLICITLY: engine `tests/` is a whole-dir
    symlink to the workspace, and ENGINE.rglob does NOT descend directory symlinks — so the
    dogfood/golden fixtures would silently escape the standing full-tree scan (caught P3
    2026-07-15: the scan count didn't move when 4 fixtures landed). The fixtures MUST stay
    policed — they are the format's canonical conversions. Index/cache-gate consumers that
    want conversions-only still exclude them by the `schema_golden` path part."""
    files = [p for p in list(ENGINE.rglob("*.hpp")) + list(ENGINE.rglob("*.cpp"))
             if not any(part == "vendor" or part.startswith("build") for part in p.parts)]
    golden = WORKSPACE / "tests" / "schema_golden"
    files += sorted(golden.glob("*.hpp")) + sorted(golden.glob("*.cpp"))
    return files


def collect_file_tags(path):
    """(units, tag_values) for one opted-in file — the code-tag-index collector
    (rebuild_doc_indexes imports this). Reuses THIS module's grammar surface (TAG_LINE_RE /
    BRACKET_RE / the [SCHEMA] whitelist gate / the [COMMENT]/[DIAGRAM] prose-state walk) so the
    index and the validator read ONE grammar — never a second parser (anti-Class-18).
    units = [(unit_type, name, lineno)] for named UNIT_TYPES openers; tags = sorted unique
    [TAG] values (UPPER_SNAKE, as written in code)."""
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except (IOError, OSError):
        return [], []
    if "[SCHEMA]_[" not in text or "[SCHEMA]_[exempt" in text:
        return [], []
    units, tags = [], set()
    in_prose = False
    for lineno, raw in enumerate(text.split("\n"), 1):
        if in_prose:
            if MAJOR_BAR_RE.match(raw):
                in_prose = False
            continue
        m = TAG_LINE_RE.match(raw)
        if not m:
            continue
        toks = _line_tokens(m.group(1))
        if not toks:
            continue
        cat = toks[0]
        if cat in UNIT_TYPES and len(toks) > 1 and toks[1]:
            units.append((cat, toks[1], lineno))
        elif cat == "TAG":
            tags.update(t.strip() for t in toks[1:] if t.strip())
        if cat in ("COMMENT", "DIAGRAM"):
            in_prose = True
    return units, sorted(tags)


def validate_file(path, categories, concern_vocab, surface_vocab):
    """Return (violations, blocks_seen) for one source file. Graceful: never raises."""
    violations = []
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except (IOError, OSError):
        return [f"UNREADABLE: {path}"], 0

    # Mixed-state gate (in-file whitelist — no external list to drift): a file with NO schema
    # block is UN-CONVERTED → not policed (its pre-existing [SECTION] comments are prose, not
    # tags). A [SCHEMA]_[v1.0] (which every block, incl. the top-of-file [FILE] block, carries)
    # opts a file IN; [SCHEMA]_[exempt]_[reason] deliberately opts generated/third-party OUT.
    if "[SCHEMA]_[" not in text or "[SCHEMA]_[exempt" in text:
        return [], 0

    open_stack = []          # (category, name, lineno) awaiting [END_category]_[name]
    blocks_seen = 0
    in_prose = False         # inside a [COMMENT]/[DIAGRAM] freeform body → lines are PROSE (may
                             # contain bracketed words / byte-maps), not tags; skip until a ==== bar
    for lineno, raw in enumerate(text.split("\n"), 1):
        if in_prose:
            if MAJOR_BAR_RE.match(raw):
                in_prose = False
            continue
        m = TAG_LINE_RE.match(raw)
        if not m:
            continue
        toks = _line_tokens(m.group(1))
        if not toks:                       # a `// [` with no closable bracket → malformed, skip (graceful)
            continue
        cat = toks[0]

        # (5) graceful: a bare bracketed word that isn't a category and isn't an END_/value
        #     continuation is treated as prose, not flagged — only STRUCTURED lines are checked.
        is_end = cat.startswith("END_")
        if not is_end and cat not in categories:
            # Only flag a token with the CATEGORY FORM: single ALL_CAPS_UNDERSCORE word, no
            # spaces. A multi-word bracket ([ENTRY OFFSET], [ROR REGRESSOR]) is a pre-existing
            # section comment / prose → skipped. Keeps the un/half-converted tree quiet (graceful).
            if re.fullmatch(r"[A-Z][A-Z_]+", cat):
                violations.append(f"{path}:{lineno}  UNKNOWN category [{cat}]")
            continue

        # (1)+(4) one-category-per-line: no OTHER token may be a top-level CATEGORY.
        for extra in toks[1:]:
            if extra in categories and not extra.startswith("END_"):
                violations.append(
                    f"{path}:{lineno}  TWO categories on one line ([{cat}] + [{extra}]) — split them")
                break

        # (2) closer bookkeeping
        if cat in OPENERS and (cat == "CODE" or (len(toks) > 1 and toks[1])):
            # [CODE] is a nameless body-delimiter (always an opener); a bare [STRUCT] (no
            # _[name]) is a pre-existing SECTION marker, not a unit-opener → not pushed.
            name = toks[1] if len(toks) > 1 else ""
            open_stack.append((cat, name, lineno))
            if cat != "CODE":
                blocks_seen += 1
        elif is_end:
            end_cat = cat[len("END_"):]
            name = toks[1] if len(toks) > 1 else ""
            if not open_stack:
                violations.append(f"{path}:{lineno}  [{cat}] with no open [{end_cat}]")
            else:
                oc, on, _ = open_stack[-1]
                if oc != end_cat:
                    violations.append(
                        f"{path}:{lineno}  [{cat}] closes [{end_cat}] but innermost open is [{oc}]")
                elif on != name:
                    violations.append(
                        f"{path}:{lineno}  [{cat}]_[{name}] name mismatch — open was [{oc}]_[{on}]")
                else:
                    open_stack.pop()

        # (3) [TAG] vocab: every value resolves in concern OR surface (UPPER_SNAKE↔lower-hyphen).
        if cat == "TAG" and (concern_vocab or surface_vocab):
            for val in toks[1:]:
                v = _upper_snake_to_vocab(val)
                if v and v not in concern_vocab and v not in surface_vocab:
                    violations.append(f"{path}:{lineno}  [TAG] value [{val}] not in doc-tag-vocabulary")

        if cat in ("COMMENT", "DIAGRAM"):   # open a freeform prose body until the next ==== bar
            in_prose = True

    for oc, on, ln in open_stack:
        violations.append(f"{path}:{ln}  [{oc}]_[{on}] has no matching [END_{oc}]")
    return violations, blocks_seen


# --- self-test: PROVE the checker catches each violation class (anti Class-51 vacuity) ---
_SELFTEST = [
    # (label, source, expect_substring_in_a_violation_or_None_for_clean)
    ("clean block", """
//======================================================================
// [FUNCTION]_[Regime_Classify]
// [TAG]_[[SLOW_PATH] [ML_INFERENCE]]
// [SCHEMA]_[v1.0]
//======================================================================
// [CODE]
template <unsigned F> inline int Regime_Classify() { return 0; }
// [END_CODE]
//======================================================================
// [END_FUNCTION]_[Regime_Classify]
""", None),
    ("clean STRUCT", """
//======================================================================
// [STRUCT]_[ExecutionCore]
// [TAG]_[[HOT_PATH] [DATA_ORIENTED_DESIGN]]
// [THREAD]_[[HOT_WRITER] [SLOW_READER]]
// [SCHEMA]_[v1.0]
//======================================================================
// [CODE]
template <unsigned F> struct alignas(64) ExecutionCore { };
// [END_CODE]
//======================================================================
// [DERIVED]
// [SIZE]_[192B]
// [ALIGN]_[64]
//======================================================================
// [END_STRUCT]_[ExecutionCore]
""", None),
    ("clean REGISTRY", """
//======================================================================
// [REGISTRY]_[FOREACH_STRATEGY]
// [TAG]_[[FRAMEWORK_DISCIPLINE]]
// [SCHEMA]_[v1.0]
//======================================================================
// [CODE]
#define FOREACH_STRATEGY(X) X(MEAN_REVERSION)
// [END_CODE]
//======================================================================
// [DERIVED]
// [ROW_COUNT]_[5]
// [ENROLLED]_[MetaRegistry.hpp]
//======================================================================
// [END_REGISTRY]_[FOREACH_STRATEGY]
""", None),
    ("clean FILE (orient-only, no closer)", """
//======================================================================
// [FILE]_[ExecutionCore.hpp]
// [TAG]_[[HOT_PATH]]
// [SCHEMA]_[v1.0]
// [OVERVIEW]_[per-node hot execution state + tick kernel]
//======================================================================
""", None),
    ("clean FREEFORM ([COMMENT] prose with bracketed category-words)", """
//======================================================================
// [FUNCTION]_[freeform_ok]
// [SCHEMA]_[v1.0]
//======================================================================
// [CODE]
int freeform_ok() { return 0; }
// [END_CODE]
//======================================================================
// [COMMENT]
// this prose mentions [CODE] and [COMMENT] and [DERIVED] in brackets — it is
// freeform text, NOT tags, so it must NOT be parsed as categories.
//======================================================================
// [END_FUNCTION]_[freeform_ok]
""", None),
    ("clean ENUM (persisted codes + sparse [VALUE])", """
//======================================================================
// [ENUM]_[OrderState]
// [TAG]_[[ENGINE] [OMS_DRAINER]]
// [SCHEMA]_[v1.0]
//======================================================================
// [CODE]
enum OrderState : uint8_t { ORDER_PENDING = 0 };
// [END_CODE]
//======================================================================
// [VALUE]_[ORDER_PENDING]_[submitted, not yet on exchange]
// [END_ENUM]_[OrderState]
""", None),
    ("clean TYPE (foundational alias)", """
//======================================================================
// [TYPE]_[Money]
// [SCHEMA]_[v1.0]
//======================================================================
// [CODE]
using Money = FixedPoint<10, 8>;
// [END_CODE]
//======================================================================
// [END_TYPE]_[Money]
""", None),
    ("clean NESTED (STRUCT body holds a full ENUM child block, D-340 stack parse)", """
//======================================================================
// [STRUCT]_[Outer]
// [SCHEMA]_[v1.0]
//======================================================================
// [CODE]
struct Outer {
    // [ENUM]_[Inner]
    // [CODE]
    enum Inner : uint8_t { A = 0 };
    // [END_CODE]
    // [END_ENUM]_[Inner]
};
// [END_CODE]
//======================================================================
// [END_STRUCT]_[Outer]
""", None),
    ("unknown category", "// [FUNCTON]_[typo]\n", "UNKNOWN category"),
    ("two categories one line", "// [FUNCTION]_[X] [TAG]_[[HOT_PATH]]\n", "TWO categories"),
    ("missing closer", "// [FUNCTION]_[Orphan]\n", "no matching [END_FUNCTION]"),
    ("missing END_ENUM (variant opener enforced)", "// [ENUM]_[Orphan]\n", "no matching [END_ENUM]"),
    ("name mismatch", "// [FUNCTION]_[A]\n// [END_FUNCTION]_[B]\n", "name mismatch"),
    ("bad tag value", "// [TAG]_[[NOT_A_REAL_SURFACE_TAG]]\n", "not in doc-tag-vocabulary"),
    ("end with no open", "// [END_STRUCT]_[X]\n", "no open [STRUCT]"),
]

# --- self-test for [REFERENCE]-resolution (live index; non-vacuous — a present id vs an
#     absent one PROVE the resolver discriminates, exactly as the [TAG]-vocab case does) ---
_REF_SELFTEST = [
    ("ref INVARIANT valid (H4)",          "// [REFERENCE]_[INVARIANT]_[H4]\n", None),
    ("ref INVARIANT dangling (H99)",      "// [REFERENCE]_[INVARIANT]_[H99]\n", "dangling"),
    ("ref DECISION valid (D-306)",        "// [REFERENCE]_[DECISION]_[D-306]\n", None),
    ("ref DECISION dangling (D-999999)",  "// [REFERENCE]_[DECISION]_[D-999999]\n", "dangling"),
    ("ref DESIGN_SPEC valid (self)",      "// [REFERENCE]_[DESIGN_SPEC]_[in-code-documentation-schema]\n", None),
    ("ref multi-id inline ([[H4] [H8]])", "// [REFERENCE]_[INVARIANT]_[[H4] [H8]]\n", None),
    ("ref AUDIT never reds",              "// [REFERENCE]_[AUDIT]_[no-such-audit-index]\n", None),
    ("ref PARITY valid (PARITY-001)",     "// [REFERENCE]_[PARITY]_[PARITY-001]\n", None),
    ("ref PARITY dangling (PARITY-999999)", "// [REFERENCE]_[PARITY]_[PARITY-999999]\n", "dangling"),
    ("ref SOURCE never reds (advisory, D-345)", "// [REFERENCE]_[SOURCE]_[FoxML_Core scaler.py:142]\n", None),
    ("ref CLASS valid, subfile-only (23)", "// [REFERENCE]_[CLASS]_[23]\n", None),   # guards the subfile glob
    ("ref CLASS dangling (999999)",       "// [REFERENCE]_[CLASS]_[999999]\n", "dangling"),
    ("ref unknown subcat (REGISTRY not in fence)", "// [REFERENCE]_[REGISTRY]_[FOREACH_STRATEGY]\n",
     "UNKNOWN [REFERENCE] subcat"),
    ("supporting-docs block valid",       "// [SUPPORTING_DOCS]\n//   - [INVARIANT]_[H8]\n", None),
    ("supporting-docs block dangling",    "// [SUPPORTING_DOCS]\n//   - [INVARIANT]_[H404]\n", "dangling"),
]


def run_selftest(categories, concern_vocab, surface_vocab):
    import tempfile, os
    ok = True

    def _run(cases, checker):
        nonlocal ok
        for label, src, expect in cases:
            fd, p = tempfile.mkstemp(suffix=".hpp")
            os.write(fd, ("// [SCHEMA]_[v1.0]\n" + src).encode()); os.close(fd)   # opt the fixture in (gate)
            viols = checker(p)
            os.unlink(p)
            hit = (expect is None and not viols) or (expect is not None and any(expect in v for v in viols))
            print(f"  {'✅' if hit else '❌'} {label}: {len(viols)} violation(s)"
                  + ("" if hit else f"  EXPECTED ~'{expect}', GOT {viols}"))
            ok = ok and hit

    _run(_SELFTEST, lambda p: validate_file(p, categories, concern_vocab, surface_vocab)[0])
    ref_subcats = load_ref_subcats()
    print(f"  {'✅' if ref_subcats else '❌'} ref-subcats fence-derived: "
          f"{sorted(ref_subcats) if ref_subcats else 'FENCE UNLOADABLE'}")
    ok = ok and bool(ref_subcats)
    ref_index = load_reference_index()
    _vac = [k for k in REF_MUST_POPULATE if not ref_index.get(k)]
    print(f"  {'✅' if not _vac else '❌'} ref-index non-vacuity: "
          f"{'all subcats populated' if not _vac else str(_vac) + ' loaded 0 ids'}")
    ok = ok and not _vac
    _run(_REF_SELFTEST, lambda p: resolve_references(p, ref_index, ref_subcats or set()))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paths", nargs="*")
    ap.add_argument("--selftest", action="store_true", help="prove the checker catches each violation class")
    args = ap.parse_args()

    concern_vocab, surface_vocab = load_vocabulary()
    categories = load_categories()
    ref_subcats = load_ref_subcats()
    if concern_vocab is None or categories is None or ref_subcats is None:
        print("ERROR: doc-tag-vocabulary or the spec's category-set / reference-subcats SSoT "
              "not loadable", file=sys.stderr)
        return 2

    if args.selftest:
        print(f"check_code_tag_blocks --selftest ({len(categories)} categories from spec; non-vacuity):")
        return 0 if run_selftest(categories, concern_vocab, surface_vocab) else 2

    if args.paths:
        files = [Path(p) for p in args.paths]
    else:
        files = engine_source_files()   # drift-proof shared file-list (also feeds the code-tag index)

    ref_index = load_reference_index()          # frozen-path membership sets, loaded once
    vacuous = [k for k in REF_MUST_POPULATE if not ref_index.get(k)]
    if vacuous:                                 # a subcat that loaded 0 ids = a broken source path
        print(f"ERROR: [REFERENCE] index vacuous — {vacuous} resolved 0 ids (broken source "
              f"path?); refusing to scan — refs of these subcats would pass vacuously", file=sys.stderr)
        return 2
    all_v, blocks, checked = [], 0, 0
    for f in files:
        if not f.exists():
            continue
        checked += 1
        v, b = validate_file(f, categories, concern_vocab, surface_vocab)
        all_v.extend(v); blocks += b
        all_v.extend(resolve_references(f, ref_index, ref_subcats))   # decoupled [REFERENCE]-resolution pass

    print(f"Scanned {checked} files; {blocks} tag-blocks; "
          f"{len(concern_vocab)} concern + {len(surface_vocab)} surface tags")
    if all_v:
        print(f"\nVIOLATIONS ({len(all_v)}):")
        for v in all_v[:50]:
            print(f"  {v}")
        if len(all_v) > 50:
            print(f"  ... and {len(all_v) - 50} more")
        return 1
    print("\nAll tag-blocks valid (or none present — mixed-state is fine).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
