#!/usr/bin/env python3
"""mine_reference_tags.py — lift EXISTING in-span id mentions into `[REFERENCE]` tags (0.4).

The docview/[REFERENCE] surface only fires on units that CARRY the tag; the operator asked for
a tool that applies it corpus-wide. The law (D-413/D-414, the fabrication arc): **MINE, NEVER
INVENT** — [REFERENCE] content is SEMANTIC, so this tool only aggregates what a human already
wrote inside the unit's span (inline `per D-142` / `H4` / `Class 51` / `TECH_DEBT-249` /
`PARITY-038` mentions), validates every id against the SAME membership index the validator
reds on (`check_code_tag_blocks.load_reference_index` — one resolver, never a second parser),
and writes ONLY on `--fix` (D-374 write-vs-verify: dry-run is the default; the git diff is the
review surface). Additive merge — an existing hand-written id is NEVER removed or reordered.
Idempotent by construction: mined ids land on tag-shaped lines, and tag-shaped lines are
excluded from mining (2nd run = 0-diff).

Subcat scope = the fenced subcats that have a membership index (INVARIANT / DECISION /
TECH_DEBT / CLASS / PARITY). Unfenced namespaces (M/AR/T/B) would be a vocab RED; index-less
subcats (AUDIT/SOURCE/URL) are unverifiable — both excluded by design, stated here.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from check_code_tag_blocks import (TAG_LINE_RE, UNIT_TYPES, _line_tokens,      # noqa: E402
                                   engine_source_files, load_reference_index,
                                   load_ref_subcats, _ref_resolves)

# mention-pattern → (subcat, canonical id writer). ID-FORMS per the schema's reference-subcats
# fence: H<n> · D-<n> (C-/F- resolve via the union) · TECH_DEBT-<n> · CLASS bare int · PARITY-<n>.
MENTION_PATTERNS = [
    ("INVARIANT", re.compile(r"\bH(\d{1,2})\b"),             lambda m: f"H{int(m.group(1))}"),
    ("DECISION",  re.compile(r"\b([DCF]-\d{1,4})\b"),        lambda m: m.group(1)),
    ("TECH_DEBT", re.compile(r"\bTECH_DEBT-0*(\d{1,4})\b"),  lambda m: f"TECH_DEBT-{int(m.group(1))}"),
    ("CLASS",     re.compile(r"\bClass\s+0*(\d{1,3})\b"),    lambda m: str(int(m.group(1)))),
    ("PARITY",    re.compile(r"\bPARITY-0*(\d{1,4})\b"),     lambda m: f"PARITY-{int(m.group(1))}"),
]

_ID_NUM = re.compile(r"(\d+)")


def _id_sort_key(rid):
    m = _ID_NUM.search(rid)
    return (rid[:m.start()] if m else rid, int(m.group(1)) if m else 0)


def _units(lines):
    """[(type, name, opener_idx0, closer_idx0)] for CLOSABLE units. Light units (ASSERT/FILE/
    MACRO — openers with no END) are discarded by the pop-through on END so they can't poison
    the stack."""
    out, stack = [], []
    for i, raw in enumerate(lines):
        m = TAG_LINE_RE.match(raw)
        if not m:
            continue
        toks = _line_tokens(m.group(1))
        if not toks:
            continue
        cat = toks[0]
        if cat.startswith("END_"):
            want = cat[4:]
            if want not in UNIT_TYPES:
                continue                     # [END_CODE]/[END_...]-section closers are NOT unit closers
            while stack:
                ty, nm, op = stack.pop()
                if ty == want:
                    out.append((ty, nm, op, i))
                    break
        elif cat in UNIT_TYPES and len(toks) > 1 and toks[1]:
            stack.append((cat, toks[1], i))
    return out


def _existing_ref_ids(lines, op, code_idx):
    """{subcat: (line_idx, [ids-as-written])} for [REFERENCE] lines in the unit's banner."""
    out = {}
    for i in range(op, code_idx if code_idx is not None else op):
        m = TAG_LINE_RE.match(lines[i])
        if not m:
            continue
        toks = _line_tokens(m.group(1))
        if len(toks) >= 3 and toks[0] == "REFERENCE":
            out[toks[1]] = (i, [t for t in toks[2:] if t])
    return out


def mine_file(text, ref_index):
    """PURE core: text → (proposals, dead, new_text). proposals = [(unit, subcat, [new ids])];
    dead = [(unit, subcat, id)] mentions that do NOT resolve (never written — reported);
    new_text = the text with merged/inserted [REFERENCE] lines (equal to text when nothing new).
    Mining excludes tag-shaped lines (idempotency + no self-mining) and attributes a mention to
    the INNERMOST enclosing unit."""
    lines = text.split("\n")
    units = _units(lines)
    proposals, dead = [], []
    edits = {}          # line_idx -> replacement line (merge)
    inserts = {}        # line_idx -> [new lines] (insert BEFORE this idx)

    for ty, nm, op, cl in units:
        children = [(o, c) for (t2, n2, o2, c2) in units for (o, c) in [(o2, c2)]
                    if o2 > op and c2 < cl]
        code_idx = None
        for i in range(op, cl + 1):
            m = TAG_LINE_RE.match(lines[i])
            if m and _line_tokens(m.group(1))[:1] == ["CODE"]:
                code_idx = i
                break
        mined = {}
        for i in range(op, cl + 1):
            if any(o <= i <= c for (o, c) in children):
                continue
            if TAG_LINE_RE.match(lines[i]):
                continue
            for subcat, pat, canon in MENTION_PATTERNS:
                for m in pat.finditer(lines[i]):
                    mined.setdefault(subcat, set()).add(canon(m))
        if not mined:
            continue
        existing = _existing_ref_ids(lines, op, code_idx)
        unit_label = f"{ty} {nm}"
        for subcat in sorted(mined):
            have = set()
            if subcat in existing:
                # normalize existing-as-written through the same resolver-normalization lens
                have = {rid.strip() for rid in existing[subcat][1]}
            members = ref_index.get(subcat)
            fresh = []
            for rid in sorted(mined[subcat] - have, key=_id_sort_key):
                if members is not None and not _ref_resolves(subcat, rid, members):
                    dead.append((unit_label, subcat, rid))
                    continue
                # an id already written in ANY normalization (e.g. `05` vs `5`) counts as present
                if members is not None and any(
                        _ref_resolves(subcat, h, members) and _id_sort_key(h) == _id_sort_key(rid)
                        for h in have):
                    continue
                fresh.append(rid)
            if not fresh:
                continue
            proposals.append((unit_label, subcat, fresh))
            if subcat in existing:
                idx, as_written = existing[subcat]
                merged = as_written + fresh
                edits[idx] = "// [REFERENCE]_[%s]_[%s]" % (
                    subcat, "[" + "] [".join(merged) + "]" if len(merged) > 1 else merged[0])
            else:
                if code_idx is None:
                    dead.append((unit_label, subcat, "(no [CODE] line — placement refused)"))
                    proposals.pop()
                    continue
                at = code_idx
                if at - 1 > op and set(lines[at - 1].replace("/", "").strip()) <= {"="}:
                    at = at - 1                      # insert above the //==== bar before [CODE]
                val = "[" + "] [".join(fresh) + "]" if len(fresh) > 1 else fresh[0]
                inserts.setdefault(at, []).append("// [REFERENCE]_[%s]_[%s]" % (subcat, val))

    if not edits and not inserts:
        return proposals, dead, text
    out = []
    for i, l in enumerate(lines):
        if i in inserts:
            out.extend(inserts[i])
        out.append(edits.get(i, l))
    return proposals, dead, "\n".join(out)


def _selftest():
    fx = "\n".join([
        "// [SCHEMA]_[v1.0]",
        "// [STRUCT]_[Outer]",
        "// [OVERVIEW]_[a fixture]",
        "// [REFERENCE]_[DECISION]_[D-900]",
        "//======================================================================",
        "// [CODE]",
        "// guarded per D-901 and H91 (see Class 91)",
        "// [ASSERT]_[D-902_LOCK]",
        "int x; // D-999 is dead",
        "// [FUNCTION]_[Inner_Fn]",
        "// [CODE]",
        "// child-only mention: TECH_DEBT-91",
        "// [END_CODE]",
        "// [END_FUNCTION]_[Inner_Fn]",
        "// [END_CODE]",
        "// [END_STRUCT]_[Outer]",
    ])
    ref_index = {"DECISION": {"D-900", "D-901", "D-902"}, "INVARIANT": {"H91"},
                 "CLASS": {91}, "TECH_DEBT": {91}, "PARITY": None}
    props, dead, out = mine_file(fx, ref_index)
    by = {(u, s): ids for u, s, ids in props}
    fails = []

    def ck(label, cond):
        print(f"  {'PASS' if cond else 'FAIL'}  {label}")
        if not cond:
            fails.append(label)

    ck("mines DECISION+INVARIANT+CLASS from prose", by.get(("STRUCT Outer", "DECISION")) == ["D-901"]
       and by.get(("STRUCT Outer", "INVARIANT")) == ["H91"]
       and by.get(("STRUCT Outer", "CLASS")) == ["91"])
    ck("dead id DROPPED + reported (never written into a [REFERENCE] line)",
       ("STRUCT Outer", "DECISION", "D-999") in dead
       and all("D-999" not in l for l in out.split("\n") if "[REFERENCE]_" in l))
    ck("tag-shaped line NOT mined (D-902 stays un-proposed)",
       all("D-902" not in ids for (_, s, ids) in props))
    ck("MERGE preserves hand-written id first",
       "// [REFERENCE]_[DECISION]_[[D-900] [D-901]]" in out)
    ck("INSERT lands in the banner above the bar",
       out.index("[REFERENCE]_[INVARIANT]_[H91]") < out.index("// [CODE]"))
    ck("innermost attribution (child owns its mention)",
       by.get(("FUNCTION Inner_Fn", "TECH_DEBT")) == ["TECH_DEBT-91"]
       and all(s != "TECH_DEBT" for (u, s, _) in props if u == "STRUCT Outer"))
    props2, _dead2, out2 = mine_file(out, ref_index)
    ck("IDEMPOTENT (2nd mine = zero new, 0-diff)", not props2 and out2 == out)
    fenced = load_ref_subcats() or set()
    ck("every written subcat is FENCED (vocab-legal)",
       all(s in fenced for (_, s, _) in props))
    grammar_ok = all(TAG_LINE_RE.match(l) for l in out.split("\n") if "[REFERENCE]_" in l)
    ck("written lines match the validator's own TAG_LINE_RE", grammar_ok)
    print(f"[mine_reference_tags selftest] {'ALL TEETH PASS' if not fails else f'{len(fails)} FAILURE(S): {fails}'}")
    return 0 if not fails else 1


def main():
    import argparse
    ap = argparse.ArgumentParser(description="lift existing in-span id mentions into [REFERENCE] tags")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--fix", action="store_true",
                    help="WRITE the merged/inserted lines (default = dry-run report; D-374 "
                         "flag-not-auto — the git diff is the review surface)")
    ap.add_argument("--paths", nargs="*", help="restrict to these files (default: derived_facts corpus)")
    args = ap.parse_args()
    if args.selftest:
        return _selftest()

    ref_index = load_reference_index()
    files = ([Path(p) for p in args.paths] if args.paths
             else engine_source_files(profile="derived_facts"))
    tot_units, tot_ids, tot_dead, touched = set(), 0, [], 0
    for f in files:
        if not f.exists():
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        if "[SCHEMA]_[" not in text or "[SCHEMA]_[exempt" in text:
            continue
        props, dead, out = mine_file(text, ref_index)
        tot_dead.extend((f, u, s, r) for u, s, r in dead)
        if not props:
            continue
        touched += 1
        for u, s, ids in props:
            tot_units.add((str(f), u))
            tot_ids += len(ids)
            print(f"  {f}: {u} +[{s}] {' '.join(ids)}")
        if args.fix and out != text:
            f.write_text(out, encoding="utf-8")
    verb = "WROTE" if args.fix else "would write (dry-run — re-run with --fix)"
    print(f"\nmine_reference_tags: {verb} {tot_ids} id(s) across {len(tot_units)} unit(s) "
          f"in {touched} file(s).")
    if tot_dead:
        print(f"  {len(tot_dead)} unresolved mention(s) EXCLUDED (mine-never-invent):")
        for f, u, s, r in tot_dead[:20]:
            print(f"    {f}: {u} [{s}] {r}")
        if len(tot_dead) > 20:
            print(f"    … {len(tot_dead) - 20} more")
    return 0


if __name__ == "__main__":
    sys.exit(main())
