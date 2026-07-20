#!/usr/bin/env python3
"""citable_ids.py — the ONE resolver for every citable-ID namespace, BY DEFINING FORM.

Citable IDs are how this knowledge base cross-references itself: `H21`, `M8`, `Class 51`, `AR-15`,
`T4`, `D-394`, `TECH_DEBT-249`, `PARITY-038`. Until 2026-07-19 nothing verified that an ID means
exactly one thing, and it didn't — `M9` was claimed by two disciplines, and `D-1`..`D-13` by two
decision logs with **genuinely opposite content** (`D-7` = ImGui stays vs hard-deprecated).

**This is H21 transposed to the doc plane.** H21 says a persistence/wire identifier is append-only
and immutable because an un-updated reader carries the OLD meaning of a reused slot. A citable ID
has exactly the same failure mode with a human as the reader: cite `M9` and you get whichever of
two disciplines the reader happens to find first.

## BY DEFINING FORM, NEVER BY MENTION — the whole point

The predecessor resolver built its TECH_DEBT and CLASS membership by scanning raw ledger TEXT for
`TECH_DEBT-(\\d+)`. **A set that admits anything it has SEEN cannot go red**: cite a nonexistent
`TECH_DEBT-999` in the same file that defines the set, and it resolves. That is why CI never saw
the 8 dangling citations D-389 found — the guard's membership was downstream of the thing it was
supposed to check (Class-51, in the resolver itself).

So every namespace here is parsed from the form that DEFINES an entry — a table row, a `###`
heading, a sentinel, a filename — never from a prose mention. The distinction is not pedantry: it
is the difference between a guard that can fail and one that cannot.

⚠️ The temptation while EXTENDING this is to add a namespace "by grepping for it". Don't. If a
namespace has no defining form, it has no SSoT, and the correct move is to give it one (or leave
it existence-unchecked and say so) rather than to fake membership from mentions.

## Scope collisions are NOT this module's business

`M1`-`M9` are meta-disciplines globally but MEDIUM finding-IDs inside an audit report; `B12`-`B17`
are blindspot pillars globally but work-item IDs in one synthesis. A checker cannot tell scopes
apart, and forcing it produces exactly the noise that gets guards ignored (AR-14 § false-positive
surface). The fix for that is prefixing finding IDs (`F-M1`) at template level — a convention, not
a mechanism. This module resolves GLOBAL namespaces only.
"""
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from foxroots import ENGINE, WORKSPACE   # noqa: E402  (the ONE repo-root resolver — D-375)

CLAUDE_MD          = ENGINE / "CLAUDE.md"
TOOLS_CLAUDE_MD    = WORKSPACE / "tools" / "CLAUDE.md"
DESIGN_PHILOSOPHY  = WORKSPACE / "DOCS" / "DESIGN_PHILOSOPHY.md"
ANTIPATTERN_INDEX  = WORKSPACE / "DESIGN_SPECS" / "meta-disciplines" / "meta-anti-pattern-index.md"
BLINDSPOT_TAXONOMY = WORKSPACE / "DESIGN_SPECS" / "meta-disciplines" / "implementation-layer-blindspot-taxonomy.md"
CLASS_SUBFILE_DIR  = WORKSPACE / "DOCS" / "recurring-bug-patterns"
PARITY_DOC         = WORKSPACE / "DOCS" / "PARITY_ISSUES.md"
PLANS_DIR          = WORKSPACE / "plans"
TECHDEBT_FILES     = [WORKSPACE / "DOCS" / "TECH_DEBT.md",
                      WORKSPACE / "DOCS" / "tech-debt" / "open.md",
                      WORKSPACE / "DOCS" / "tech-debt" / "in-flight.md",
                      WORKSPACE / "DOCS" / "tech-debt" / "closed.md"]


def _read(p):
    try:
        return Path(p).read_text(encoding="utf-8", errors="replace")
    except (IOError, OSError):
        return ""


# ── the defining-form spec now lives in DATA ─────────────────────────────────────────────────
# tools/lib/citable_id_namespaces.json. Promoted out of this module 2026-07-20 (operator call):
# the plan declares ONE RESOLVER, THREE CONSUMERS — the CI gate, the tag system, and the plugin's
# 0.4 [REFERENCE] doc-viewer. A spec living as a Python list forces the Lua side to re-implement
# it, which is the Class-18 mirror this whole ship exists to close.
#
# The file is DECLARATIVE and REGEX-FREE by construction (anchor kind + literal prefix + flags),
# so `foxtag`'s hand-parser can read it without a regex engine. That constraint is why D-393 pt 4
# refuted a shared registry for the ref-index — a shared file carrying regexes CREATES parity risk
# rather than removing it. Matching below is startswith() + a digit scan; no `re` on the defining
# path at all.
NAMESPACE_REGISTRY = Path(__file__).absolute().parent / "lib" / "citable_id_namespaces.json"


def _registry():
    import json
    try:
        return json.loads(NAMESPACE_REGISTRY.read_text(encoding="utf-8"))
    except (IOError, OSError) as e:
        raise SystemExit(f"FATAL: citable-id namespace registry unreadable at {NAMESPACE_REGISTRY}: {e}")
    except json.JSONDecodeError as e:
        raise SystemExit(f"FATAL: citable-id namespace registry is not valid JSON: {e}")


def _subst(s):
    return str(s).replace("$ENGINE", str(ENGINE)).replace("$WORKSPACE", str(WORKSPACE))


def _digits_at(s, i):
    """Longest digit run starting at i, or None. The hand-parser primitive."""
    j = i
    while j < len(s) and s[j].isdigit():
        j += 1
    return (s[i:j], j) if j > i else (None, i)


def _match_defining(line, spec):
    """Return the id this line DEFINES per `spec`, else None. startswith/scan only — no regex."""
    anchor = spec.get("anchor")
    prefixes = spec.get("prefix_any") or ([spec["prefix"]] if "prefix" in spec else [])

    if anchor == "table-row":
        if not line.startswith("|"):
            return None
        rest = line[1:].lstrip()
        bold = spec.get("bold", "optional")
        starred = rest.startswith("**")
        if bold == "required" and not starred:
            return None
        if starred:
            rest = rest[2:]
        for pre in prefixes:
            if rest.startswith(pre):
                num, k = _digits_at(rest, len(pre))
                if not num:
                    continue
                tail = rest[k:]
                if tail.startswith("**"):
                    tail = tail[2:]
                need = spec.get("requires_after")
                if need and not tail.lstrip().startswith(need):
                    continue
                return pre + num
        return None

    if anchor == "heading":
        hashes = "#" * int(spec.get("heading_level", "3")) + " "
        if not line.startswith(hashes):
            return None
        rest = line[len(hashes):].lstrip()
        for pre in prefixes:
            if rest.startswith(pre):
                num, _ = _digits_at(rest, len(pre))
                if num:
                    return pre + num
        return None

    if anchor == "field":
        fp = spec["field_prefix"]
        if line.startswith(fp):
            num, _ = _digits_at(line, len(fp))
            return fp + num if num else None
        return None
    return None


def _norm(spec, raw):
    if spec.get("id_type") == "int":
        d = "".join(c for c in raw if c.isdigit())
        return int(d) if d else raw
    return raw


def defining_index():
    """{namespace: {id: [(path, lineno)]}} — every entry, with EVERY site that defines it.

    The value is a LIST, not a single location, precisely so a double-definition is representable.
    A resolver storing one location per id would silently pick a winner and hide the exact defect
    (`M9` claimed twice) this module exists to surface."""
    reg = _registry()["namespaces"]
    idx = {ns: {} for ns in reg}

    for ns, spec in reg.items():
        anchor = spec.get("anchor")

        if anchor == "filename":
            d = Path(_subst(spec["directory"]))
            pre = spec["filename_prefix"]
            if d.is_dir():
                for p in sorted(d.glob(pre + "*")):
                    num, _ = _digits_at(p.name, len(pre))
                    if num:
                        idx[ns].setdefault(_norm(spec, num), []).append((str(p), 1))
            continue

        if anchor == "html-sentinel":
            base = Path(_subst(spec["directory_glob"]).replace("/*/decision-logs", ""))
            opens = spec.get("sentinel_open_any") or [spec["sentinel_open"]]
            cl = spec["sentinel_close"]
            pres = spec.get("prefix_any", [])
            exact = spec.get("id_exact") == "true"
            for log in sorted(base.glob("*/decision-logs/*.md")):
                for lineno, line in enumerate(_read(log).splitlines(), 1):
                    for op in opens:
                        i = line.find(op)
                        if i == -1:
                            continue
                        j = line.find(cl, i)
                        if j == -1:
                            continue
                        rid = line[i + len(op):j].strip()
                        # SHAPE-VALIDATE: prefix + digits, and (if id_exact) nothing after.
                        # Without this, `DD-1` / `F-2-AMEND` / `P-1` were admitted as decision
                        # ids and would be reported as dangling citations forever.
                        if pres:
                            good = False
                            for pre in pres:
                                if rid.startswith(pre):
                                    num, k = _digits_at(rid, len(pre))
                                    if num and (not exact or k == len(rid)):
                                        good = True
                                        break
                            if not good:
                                continue
                        if rid:
                            idx[ns].setdefault(rid, []).append((str(log), lineno))
                        break
            continue

        sources = spec.get("sources") or [spec.get("source")]
        for src in sources:
            if not src:
                continue
            path = Path(_subst(src))
            for lineno, line in enumerate(_read(path).splitlines(), 1):
                rid = _match_defining(line, spec)
                if rid:
                    idx[ns].setdefault(_norm(spec, rid), []).append((str(path), lineno))
    return idx


# ── citation forms (how an ID is REFERENCED in prose/code, as opposed to defined) ─────────────
# Deliberately looser than the defining forms: a citation is any mention. `\b` guards keep short
# ids (H4, M8, T1) from matching inside longer tokens.
_CITE = {
    "INVARIANT":   re.compile(r"\b(H(?:1[0-9]|2[0-9]|[1-9]))\b"),
    "META":        re.compile(r"\b(M(?:1[0-9]|[1-9]))\b"),
    "TOOLCHAIN":   re.compile(r"\b(T(?:1[0-9]|[1-9]))\b"),
    "ANTIPATTERN": re.compile(r"\b((?:AR|WH|PL|CP)-\d+)\b"),
    "BLINDSPOT":   re.compile(r"\b(B(?:1[0-9]|[1-9]))\b"),
    "TECH_DEBT":   re.compile(r"\bTECH_DEBT-(\d+)\b"),
    "PARITY":      re.compile(r"\bPARITY-(\d+)\b"),
    "CLASS":       re.compile(r"\bClass 0*(\d+)\b"),
}
_NORM = {"TECH_DEBT": int, "PARITY": int, "CLASS": int}


def citations_in(text):
    """{namespace: {id: [lineno]}} for one document's body. Mentions, not definitions.

    Kept as N explicit passes rather than one combined alternation. A combined-regex version WAS
    written and reverted: extracting the id BODY from an alternation of wrapped groups changed the
    results (145 -> 141 findings) while barely moving the clock once the inner capture had to be
    re-matched. Correctness of a guard beats its speed, and a perf change that alters findings is
    a behaviour change wearing a perf costume.

    The ONE optimisation kept is provably behaviour-preserving: every citable id ends in digits,
    so a line containing no digit cannot contain a citation."""
    out = {}
    for lineno, line in enumerate(text.splitlines(), 1):
        if not any(c.isdigit() for c in line):
            continue
        for ns, rx in _CITE.items():
            for m in rx.finditer(line):
                rid = _NORM.get(ns, str)(m.group(1))
                out.setdefault(ns, {}).setdefault(rid, []).append(lineno)
    return out


def sequence_gaps(idx, ns):
    """Missing integers inside a namespace's observed range — candidate un-tombstoned slots.

    A GAP is not automatically a defect: an id may have been retired with a tombstone, which is
    the H21-correct outcome. This reports candidates; the caller decides by looking for tombstone
    language. Reporting a gap as a violation outright would flag every correct retirement."""
    keys = []
    for k in idx.get(ns, {}):
        m = re.search(r"(\d+)", str(k))
        if m:
            keys.append(int(m.group(1)))
    if len(keys) < 2:
        return []
    return [n for n in range(min(keys), max(keys) + 1) if n not in set(keys)]


if __name__ == "__main__":
    idx = defining_index()
    print("citable_ids — defining-form index (BY DEFINITION, never by mention):")
    total = 0
    for ns in sorted(idx):
        n = len(idx[ns])
        dupes = sum(1 for v in idx[ns].values() if len(v) > 1)
        total += n
        print(f"  {ns:<12} {n:>4} ids" + (f"   ⚠️ {dupes} DOUBLE-DEFINED" if dupes else ""))
    print(f"  {'TOTAL':<12} {total:>4}")
    # non-vacuity: an index that resolves nothing is a broken resolver, not an empty corpus.
    sys.exit(0 if total > 50 else 2)
