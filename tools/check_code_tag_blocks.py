#!/usr/bin/env python3
"""check_code_tag_blocks.py — validates in-code [CATEGORY] tag-blocks (the E.1.2.A schema).

The code-side sister of check_doc_metadata.py: same ONE vocabulary (reused via
load_vocabulary), applied to C++ comment tag-blocks per
`DESIGN_SPECS/doc-disciplines/in-code-documentation-schema.md`.

This is the FIRST increment (the pilot keystone). It implements the structural +
vocab checks that are stable against the current grammar:
  1. CATEGORY validity — every tag-line's token[0] is in the closed CATEGORY set.
  2. Closer matching    — every [FUNCTION]/[STRUCT]/[REGISTRY]/[CODE] has a matching,
                          same-named [END_*] (the fold-range / cursor-tracking contract).
  3. [TAG] vocab        — [TAG] values resolve in doc-tag-vocabulary (UPPER_SNAKE↔lower-hyphen).
  4. One-category-per-line — token[0] is the only top-level CATEGORY on the line.
  5. Graceful degrade   — a malformed bracket / non-tag comment is skipped, never a crash.
DEFERRED to the next increment (need grammar-final / generators): ladder-order,
[REFERENCE]-resolution, DERIVED-vs-ground-truth drift, the prose-vs-DERIVED codegen lint
(spec § CI-enforcement items 3 + 5).

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
from check_doc_metadata import load_vocabulary, ENGINE, WORKSPACE  # noqa: E402

# The innermost-bracket parse rule (spec § "The three invariants" #1). Non-innermost
# list-grouping [[a] [b]] is skipped for free → token[0]=CATEGORY, rest=values.
BRACKET_RE = re.compile(r"\[([^\[\]]+)\]")
# A structured tag-line: a // comment whose first non-space payload is a bracket token.
TAG_LINE_RE = re.compile(r"^\s*//\s*(\[.*)$")

# Closed top-level CATEGORY set (spec § Category set + this session's D-308..D-313 folds).
# Grammar is locked; VALUES (under [TAG]/[REFERENCE]/[DERIVED]) grow in the vocab, not here.
OPENERS = {"FUNCTION", "STRUCT", "REGISTRY", "CODE"}  # require a matching [END_*] (stable structural set)
SCHEMA_PATH = WORKSPACE / "DESIGN_SPECS" / "doc-disciplines" / "in-code-documentation-schema.md"


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


def _line_tokens(payload):
    """Innermost-bracket tokens on a line, in order. token[0] is the CATEGORY."""
    return [m.group(1).strip() for m in BRACKET_RE.finditer(payload)]


def validate_file(path, categories, concern_vocab, surface_vocab):
    """Return (violations, blocks_seen) for one source file. Graceful: never raises."""
    violations = []
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except (IOError, OSError):
        return [f"UNREADABLE: {path}"], 0

    open_stack = []          # (category, name, lineno) awaiting [END_category]_[name]
    blocks_seen = 0
    for lineno, raw in enumerate(text.split("\n"), 1):
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
            # Unknown token[0]: only flag if it LOOKS like a category (ALL_CAPS, no lowercase) —
            # else it's an inline value/prose bracket. Keeps a half-converted tree quiet.
            if cat.replace("_", "").isupper() and cat.isascii() and any(c.isalpha() for c in cat):
                violations.append(f"{path}:{lineno}  UNKNOWN category [{cat}]")
            continue

        # (1)+(4) one-category-per-line: no OTHER token may be a top-level CATEGORY.
        for extra in toks[1:]:
            if extra in categories and not extra.startswith("END_"):
                violations.append(
                    f"{path}:{lineno}  TWO categories on one line ([{cat}] + [{extra}]) — split them")
                break

        # (2) closer bookkeeping
        if cat in OPENERS:
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
// [SCHEMA]_[v1]
//======================================================================
// [CODE]
template <unsigned F> inline int Regime_Classify() { return 0; }
// [END_CODE]
//======================================================================
// [END_FUNCTION]_[Regime_Classify]
""", None),
    ("unknown category", "// [FUNCTON]_[typo]\n", "UNKNOWN category"),
    ("two categories one line", "// [FUNCTION]_[X] [TAG]_[[HOT_PATH]]\n", "TWO categories"),
    ("missing closer", "// [FUNCTION]_[Orphan]\n", "no matching [END_FUNCTION]"),
    ("name mismatch", "// [FUNCTION]_[A]\n// [END_FUNCTION]_[B]\n", "name mismatch"),
    ("bad tag value", "// [TAG]_[[NOT_A_REAL_SURFACE_TAG]]\n", "not in doc-tag-vocabulary"),
    ("end with no open", "// [END_STRUCT]_[X]\n", "no open [STRUCT]"),
]


def run_selftest(categories, concern_vocab, surface_vocab):
    import tempfile, os
    ok = True
    for label, src, expect in _SELFTEST:
        fd, p = tempfile.mkstemp(suffix=".hpp")
        os.write(fd, src.encode()); os.close(fd)
        viols, _ = validate_file(p, categories, concern_vocab, surface_vocab)
        os.unlink(p)
        hit = expect is None and not viols
        hit = hit or (expect is not None and any(expect in v for v in viols))
        print(f"  {'✅' if hit else '❌'} {label}: {len(viols)} violation(s)"
              + ("" if hit else f"  EXPECTED ~'{expect}', GOT {viols}"))
        ok = ok and hit
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paths", nargs="*")
    ap.add_argument("--selftest", action="store_true", help="prove the checker catches each violation class")
    args = ap.parse_args()

    concern_vocab, surface_vocab = load_vocabulary()
    categories = load_categories()
    if concern_vocab is None or categories is None:
        print("ERROR: doc-tag-vocabulary or the spec's category-set SSoT not loadable", file=sys.stderr)
        return 2

    if args.selftest:
        print(f"check_code_tag_blocks --selftest ({len(categories)} categories from spec; non-vacuity):")
        return 0 if run_selftest(categories, concern_vocab, surface_vocab) else 2

    if args.paths:
        files = [Path(p) for p in args.paths]
    else:
        files = []
        for d in ("CoreFrameworks", "Strategies", "ML_Headers", "FixedPoint",
                  "MemHeaders", "DataStream", "GUI", "Backtest"):
            files.extend((ENGINE / d).rglob("*.hpp"))
            files.extend((ENGINE / d).rglob("*.cpp"))

    all_v, blocks, checked = [], 0, 0
    for f in files:
        if not f.exists():
            continue
        checked += 1
        v, b = validate_file(f, categories, concern_vocab, surface_vocab)
        all_v.extend(v); blocks += b

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
