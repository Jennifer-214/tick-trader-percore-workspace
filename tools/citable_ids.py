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


_REGISTRY_CACHE = None


def _registry():
    """The namespace registry, parsed once per process. The ONLY memo in this module.

    Safe to cache because the registry is a RULES artifact — "what ARE the rules", edited when
    the rule changes — and NO tool writes it (swept across Python, C++ and Lua). Editing it
    mid-run means restarting the tool, so a process-lifetime key is exactly right here.

    `defining_index()` is deliberately NOT memoized, and that asymmetry is the whole point. Its
    inputs are the CORPUS — ledgers, decision logs, specs — which four tools and every working
    session actively mutate; `check_tech_debt --close` rewrites open.md and rebuild_doc_indexes
    writes CLAUDE.md, both inside its read-set. A process-lifetime cache there would hand out
    (path, lineno) pointing into a file that has since moved, and that wrong fact fans out to
    every consumer. The fix for an N-calls-in-a-loop caller is to call ONCE and pass the value
    (check_capture_audit.py:442 already does) — not to hide a cache inside a pure function, and
    not an explicit invalidate(), whose correctness would depend on every future writer
    remembering to call it, including writers in other languages and writers not yet written.

    Recovered here: ~0.07 ms x 853 ids = ~59 ms via active_sites(), which is 2.5x
    defining_index()'s own ~24 ms — the larger cost, and the one that is unambiguously safe.

    Caches on SUCCESS ONLY: both failure paths raise before the assignment, so a broken registry
    can never be memoized into a process-long lie.
    """
    global _REGISTRY_CACHE
    if _REGISTRY_CACHE is not None:
        return _REGISTRY_CACHE
    import json
    try:
        _REGISTRY_CACHE = json.loads(NAMESPACE_REGISTRY.read_text(encoding="utf-8"))
    except (IOError, OSError) as e:
        raise SystemExit(f"FATAL: citable-id namespace registry unreadable at {NAMESPACE_REGISTRY}: {e}")
    except json.JSONDecodeError as e:
        raise SystemExit(f"FATAL: citable-id namespace registry is not valid JSON: {e}")
    return _REGISTRY_CACHE


def verified_namespaces():
    """Namespaces whose CITATIONS are mechanically verifiable (registry `citations_verifiable`).

    Exported so consumers read the registry through THIS module instead of re-opening the JSON.
    A second reader is a Class-18 mirror, and the two that existed had both grown a bare
    `except Exception` fallback to a HARDCODED list — a guard silently degrading to a
    hand-written rule set is precisely what T2 forbids. A registry that cannot be read is FATAL
    (SystemExit above), never a quiet downgrade.
    """
    return [ns for ns, s in _registry()["namespaces"].items()
            if s.get("citations_verifiable") == "true"]


def frozen_record_paths():
    """Path segments whose citations are FROZEN RECORDS, not claims about the present (D-390).

    Same single-reader rationale as `verified_namespaces()`. The mirror this replaces had ALREADY
    DRIFTED: it listed four segments against the registry's five, omitting `/capture-audit-reports/`
    — so on any read failure the guard would have stopped treating its own historical reports as
    frozen and begun manufacturing findings over them. Measured, not hypothesised.
    """
    return tuple(_registry().get("frozen_record_paths", []))


def _subst(s):
    return str(s).replace("$ENGINE", str(ENGINE)).replace("$WORKSPACE", str(WORKSPACE))


def _digits_at(s, i):
    """Longest digit run starting at i, or None. The hand-parser primitive."""
    j = i
    while j < len(s) and s[j].isdigit():
        j += 1
    return (s[i:j], j) if j > i else (None, i)


def _suffix_at(s, i):
    """ONE ASCII lowercase letter at i, or None — the GRANDFATHERED split-id form (D-409).

    ASCII-explicit rather than `str.isalpha()`/`islower()`, which are Unicode-aware: a homoglyph
    (`TECH_DEBT-175` + U+03B1) would otherwise resolve as a distinct id, minting a slot nobody can
    type. Sister primitive to `_digits_at` — same startswith/scan shape, so `foxtag`'s hand-parser
    can mirror it (T2 / `_why_NO_REGEXES`).

    The FORM IS CLOSED going forward: a split takes a fresh int id + `split_from:` (D-409). This
    exists so the one grandfathered instance (`TECH_DEBT-175a`, minted by D-240) RESOLVES instead of
    silently collapsing onto its parent — the collapse that caused F-1 (false `defined-twice` on
    `-175`), F-4 (`_entry_block` over-running 4295 bytes into `-175a`) and F-5 (uncaught ValueError).
    """
    if i < len(s) and "a" <= s[i] <= "z":
        return (s[i], i + 1)
    return (None, i)


def _norm_int_id(raw):
    """`TECH_DEBT-016` -> 16 · `TECH_DEBT-175a` -> `'175a'`. ONE normalizer, both id surfaces.

    Shared by the DEFINING side (`_norm`) and the CITATION side (`_NORM`) deliberately: a defining
    form and a citation form that normalise differently IS the two-meanings-for-one-id defect this
    module exists to close, one layer in. They were two implementations until D-409; the citation
    side could not even express `175a` (`\\bTECH_DEBT-(\\d+)\\b`), so an id could be defined,
    golden-pinned, and structurally un-citable at the same time.

    Zero-pad stripping is preserved (`-016` IS `-16`, ~37% of headings are padded). A suffix makes
    the id a distinct STRING key, so `175` and `175a` can never collide.
    """
    digits = "".join(c for c in raw if c.isdigit())
    if not digits:
        return raw
    sfx = raw[-1] if raw and "a" <= raw[-1] <= "z" else ""
    return f"{int(digits)}{sfx}" if sfx else int(digits)


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
                num, k = _digits_at(rest, len(pre))
                if num:
                    sfx, _ = _suffix_at(rest, k)
                    return pre + num + (sfx or "")
        return None

    if anchor == "field":
        fp = spec["field_prefix"]
        if line.startswith(fp):
            num, k = _digits_at(line, len(fp))
            if not num:
                return None
            sfx, _ = _suffix_at(line, k)
            return fp + num + (sfx or "")
        return None
    return None


def _norm(spec, raw):
    if spec.get("id_type") == "int":
        return _norm_int_id(raw)
    return raw


_SUPERSEDED_CACHE = {}


def is_superseded(path):
    """True when a doc's frontmatter marks it `status: superseded`.

    Read from the FRONTMATTER rather than a path/name convention: a superseded log keeps its
    filename, so any name-based guess would be wrong the moment a log is superseded in place.
    Only the first 40 lines are scanned — frontmatter is at the top by definition, and a body
    mention of the word (`this supersedes D-7`) must NOT mark the whole file."""
    key = str(path)
    if key not in _SUPERSEDED_CACHE:
        hit = False
        for line in _read(Path(path)).splitlines()[:40]:
            s = line.strip()
            if s.startswith("status:") and "superseded" in s:
                hit = True
                break
        _SUPERSEDED_CACHE[key] = hit
    return _SUPERSEDED_CACHE[key]


def active_sites(ns, sites):
    """Drop defining sites in SUPERSEDED docs, provided at least one live site survives.

    WHY this is not a loosened check. An id defined in both a superseded log and its successor
    is not two competing meanings — it is one meaning that MOVED, which is the correct outcome
    of superseding a log. Reporting it is a Class-51 inversion: the guard fires on conformance,
    the operator learns the corpus is noise, and the real collisions get ignored with it.

    The `at least one live site survives` clause is load-bearing. If EVERY site is superseded the
    id has no live home, which is a genuine defect and stays reported — silence there would be
    the opposite failure. Exemption is opt-in per namespace (`supersede_exempt`) so it can never
    silently widen to a namespace whose sources have no supersede lifecycle."""
    spec = _registry()["namespaces"].get(ns, {})
    if spec.get("supersede_exempt") != "true" or len(sites) < 2:
        return sites
    live = [(s, l) for s, l in sites if not is_superseded(s)]
    return live if live else sites


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


def _is_next_entry_preamble(line):
    """Does this trailing line belong to the NEXT entry rather than the one being bounded?

    Shape-based, not anchor-based, and that is the point: declaring an `entry_start` ANCHOR in
    the registry would make PARITY's `### PARITY-NNN` headings a second defining form, and 32 of
    its 41 entries carry BOTH a heading and an `id:` field — so all 32 would become 2-site and
    fire `defined-twice`. Trimming by shape adds no defining form, so that failure is structurally
    unreachable rather than merely avoided.
    """
    s = line.strip()
    return (not s) or s == "---" or s.startswith("#") or s.startswith("```")


def _is_entry_own_preamble(line):
    """Does this line ABOVE the defining anchor belong to the SAME entry?

    Only a fence opener or a heading — never a blank or a `---`, which are the separators BETWEEN
    entries. Deliberately narrower than `_is_next_entry_preamble`: over-reaching backwards would
    annex the previous entry's tail, and a block that quietly contains its neighbour is the exact
    defect (F-4) this API exists to fix, mirrored.
    """
    s = line.strip()
    return s.startswith("```") or s.startswith("#")


def entry_blocks(idx, ns, rid):
    """[(path, start_lineno, end_lineno, text)] — the body of EVERY defining site of `rid`.

    DERIVED from the index this module already builds: the defining sites are known, so a block
    is just [my line, the next site's line in the same file), with the next entry's preamble
    trimmed back off. There is no second grammar to keep in sync with `_match_defining`, no regex,
    and nothing a `foxtag` hand-parser could not mirror (T1/T2).

    Why this exists — and why it is not a port of `check_forward_promise_audit._entry_block`:
    that function terminates on `^<spelling>TECH_DEBT-(\\d+)\\b`, and `\\b` cannot hold between a
    digit and a letter, so a SUFFIXED sibling heading is invisible to it as a terminator. Measured:
    `_entry_block('TECH_DEBT', 175, open.md)` runs 4295 bytes past the end of `-175`, swallowing
    the whole `TECH_DEBT-175a` entry. The derived block terminates correctly because `175a` is a
    real site in the index (post-D-409). The incumbent is the buggy side; this is a fix wearing a
    refactor's clothes, not the reverse.

    Returns a LIST because a citable id may legitimately be defined at several sites (7 TECH_DEBT
    ids are 2-site today: the open/closed split-brain cohort). `_entry_block` returns one block and
    silently picks whichever the regex hit first — a cardinality difference callers must handle,
    not a drop-in.
    """
    sites = (idx.get(ns) or {}).get(rid) or []
    if not sites:
        return []
    # every defining lineno per file for THIS namespace — these are the block terminators
    by_file = {}
    for _rid, ss in (idx.get(ns) or {}).items():
        for p, ln in ss:
            by_file.setdefault(p, []).append(ln)
    for p in by_file:
        by_file[p].sort()

    out = []
    for path, ln in sites:
        lines = _read(Path(path)).splitlines()
        prev = max([x for x in by_file.get(path, []) if x < ln], default=0)
        nxt = next((x for x in by_file.get(path, []) if x > ln), len(lines) + 1)
        start, end = ln, nxt - 1          # 1-based, inclusive

        # Walk BACK to the entry's real start. A namespace whose defining anchor is a FIELD
        # (PARITY: `id: PARITY-NNN`) declares the id INSIDE the entry, below its heading and
        # its ```yaml fence — so anchoring the block at the defining line alone would return
        # each entry stripped of its own title. Measured: 31 of PARITY's 41 entries. Harmless
        # for today's four needles (none live in a heading) but wrong for any consumer that
        # RENDERS an entry, which the 0.4 doc-viewer will. Bounded by the previous defining
        # site, so it can never walk into the entry above.
        probe, best = start, start
        while probe - 1 > prev:
            above = lines[probe - 2].strip()
            if above.startswith("```"):
                probe -= 1
                best = probe                     # the entry's own fence
            elif above.startswith("#"):
                probe -= 1
                best = probe                     # the entry's own heading — the real start
                break
            elif not above:
                probe -= 1                       # PROVISIONAL: a blank is only annexed if a
                                                 # heading turns up above it. Committing blanks
                                                 # eagerly would annex the gap between entries.
            else:
                break
        start = best

        # The last entry in a file legitimately runs to EOF — that is its body, not an over-run.
        while end > start and _is_next_entry_preamble(lines[end - 1]):
            end -= 1
        out.append((path, start, end, "\n".join(lines[start - 1:end])))
    return out


# ── citation forms (how an ID is REFERENCED in prose/code, as opposed to defined) ─────────────
# Deliberately looser than the defining forms: a citation is any mention. `\b` guards keep short
# ids (H4, M8, T1) from matching inside longer tokens.
_CITE = {
    "INVARIANT":   re.compile(r"\b(H(?:1[0-9]|2[0-9]|[1-9]))\b"),
    "META":        re.compile(r"\b(M(?:1[0-9]|[1-9]))\b"),
    "TOOLCHAIN":   re.compile(r"\b(T(?:1[0-9]|[1-9]))\b"),
    "ANTIPATTERN": re.compile(r"\b((?:AR|WH|PL|CP)-\d+)\b"),
    "BLINDSPOT":   re.compile(r"\b(B(?:1[0-9]|[1-9]))\b"),
    # `[a-z]?` admits the GRANDFATHERED split suffix (D-409). Without it `\d+\b` cannot match
    # `TECH_DEBT-175a` at all — `\b` fails between `5` and `a`, both word chars — so every citation
    # of a suffixed id was invisible and could never be verified against its definition. That was
    # the asymmetry, not a cosmetic gap: the DEFINING side over-accepted (collapsing `175a` onto
    # `175`) while the CITATION side under-accepted (seeing neither). Backtracking handles the
    # unsuffixed case: `[a-z]?` yields empty and `\b` holds after the digits.
    "TECH_DEBT":   re.compile(r"\bTECH_DEBT-(\d+[a-z]?)\b"),
    "PARITY":      re.compile(r"\bPARITY-(\d+[a-z]?)\b"),
    "CLASS":       re.compile(r"\bClass 0*(\d+)\b"),
}
# _norm_int_id, not int(): ONE normalizer across the defining + citation surfaces (D-409).
# `int` here would raise on the suffixed form the widened patterns above now capture.
_NORM = {"TECH_DEBT": _norm_int_id, "PARITY": _norm_int_id, "CLASS": _norm_int_id}


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
        # Apply the D-400 supersede exemption here TOO. This summary previously counted RAW
        # double-definitions while check_capture_audit's findings path applied active_sites(),
        # so the two tools the handoff tells you to run gave OPPOSITE answers on (f)'s worklist:
        # 23 DECISION collisions here, zero there. A reader taking this number as the worklist
        # would re-open a fork D-400 settled. One exemption, two consumers -> one call site.
        dupes = sum(1 for v in idx[ns].values() if len(active_sites(ns, v)) > 1)
        raw = sum(1 for v in idx[ns].values() if len(v) > 1)
        exempt = raw - dupes
        total += n
        note = f"   ⚠️ {dupes} DOUBLE-DEFINED" if dupes else ""
        if exempt:
            note += f"   ({exempt} supersede-exempt, D-400)" if dupes else \
                    f"   ({exempt} double-defined, ALL supersede-exempt per D-400)"
        print(f"  {ns:<12} {n:>4} ids" + note)
    print(f"  {'TOTAL':<12} {total:>4}")
    # non-vacuity: an index that resolves nothing is a broken resolver, not an empty corpus.
    sys.exit(0 if total > 50 else 2)
