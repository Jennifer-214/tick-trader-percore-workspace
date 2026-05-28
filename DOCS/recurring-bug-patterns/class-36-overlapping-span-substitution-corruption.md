---
type: ledger-template
class_id: 36
title: Overlapping-span substitution corruption in bulk text-rewrite tooling
parent_index: DOCS/RECURRING_BUG_PATTERNS.md
established: 2026-05-28
surface_tags: [ci-tooling, bulk-rename, text-substitution, doc-sweep, code-rename, regex-substitution]
severity: high
recurrence_count: 1
first_instance: 2026-05-28 (v5.15.5.F.4d.1.D.1 Phase A — tools/check_doc_rename_classification.py --apply: token `PER_CORE` matches as a substring INSIDE `FOREACH_PER_CORE_CFG_FIELD`; both produced overlapping substitution spans on the same text)
closure_mechanism: Overlap resolution before applying — collect candidate substitutions, sort by (start asc, span-length desc), greedily accept only non-overlapping spans (longer/outer match wins; inner substring skipped), then apply right-to-left. Regression test tools/test_check_doc_rename_classification.py::test_apply_no_overlap_corruption locks it.
sister_classes: [33]
sister_memories: [feedback_avoid_substring_replace_all_on_member_access]
---

# Class 36 — Bulk text-rewrite tooling renames/corrupts what it should not

Umbrella for failure modes of NAIVE bulk text substitution (terminology sweeps, mass renames) that lack scope-awareness. Two sub-shapes found at the same surface:
- **Sub-shape A — Overlapping-span substitution corruption** (one token a substring of another → double-sub).
- **Sub-shape B — Stable-identifier / file-path rename** (renaming a token inside a path/filename/slug breaks links).

**Detected:** 2026-05-28 at v5.15.5.F.4d.1.D.1 Phase A — sub-shape A at apply-preview (before write); sub-shape B at post-write verification (write landed, broken-link scan caught it, reverted).

## Sub-shape A — Overlapping-span substitution corruption
**Severity:** HIGH — SILENT data corruption when replacement lengths differ. LATENT-MASKED when the overlapping replacements happen to be equal-length (the `.D.1` instance was `PER_CORE`→`PER_NODE`, both 8 chars, so it did not visibly corrupt — masking the bug until a length-differing token would have triggered it). The masking is what makes this HIGH: a passing test on equal-length tokens gives false confidence.

## Recurring symptom

A tool applies MULTIPLE token substitutions to the same line/text. Two matched tokens have OVERLAPPING spans — typically one token is a substring of another. Naive position-based application substitutes both, double-editing the overlapping region and corrupting output.

```python
# WRONG — collect every match as a sub, apply right-to-left, NO overlap check:
subs = []
for token in tokens:
    for m in re.finditer(re.escape(token), line, re.IGNORECASE):
        subs.append((m.start(), m.end(), RENAME_MAP[m.group()]))
for start, end, repl in sorted(subs, key=lambda s: -s[0]):   # right-to-left
    line = line[:start] + repl + line[end:]
```

Worked instance: line contains `FOREACH_PER_CORE_CFG_FIELD`.
- Token `FOREACH_PER_CORE_CFG_FIELD` matches span (0, 26) → sub → `FOREACH_PER_NODE_CFG_FIELD`.
- Token `PER_CORE` (also in the token list, case-insensitive) matches the inner substring at span (8, 16) → sub → `PER_NODE`.
- Two overlapping spans (0,26) and (8,16). Right-to-left applies (8,16) first, then (0,26) on the now-mutated string. Equal-length replacements happened to land correctly here; any length difference (e.g. a token whose replacement is longer/shorter) shifts positions mid-apply and corrupts (`PER_NODEORE`, truncated tails, doubled fragments).

## Detection signature

Any tool performing **multi-token, position/regex-based string substitution** without overlap resolution. Grep tooling for substitution loops:

```bash
rg -n "finditer|re\.sub|\.replace\(" tools/*.py        # candidate multi-sub tooling
# then inspect: does it collect multiple (start,end,repl) and apply without
# checking that accepted spans are mutually non-overlapping?
```

The smell: a `tokens` list where one token is a substring of another (`PER_CORE` ⊂ `FOREACH_PER_CORE_CFG_FIELD`; `core` ⊂ `core_strategy`; `MAX_CORES` etc.) + a position-based apply loop.

## Closure mechanism (the fix)

Resolve overlaps BEFORE applying. Prefer the longer (outer) match; skip any candidate whose span overlaps an already-accepted one:

```python
subs.sort(key=lambda s: (s[0], -(s[1] - s[0])))   # start asc, then longer span first
accepted, last_end = [], -1
for start, end, repl in subs:
    if start >= last_end:          # non-overlapping → accept
        accepted.append((start, end, repl))
        last_end = end
    # else: overlaps a longer/earlier accepted sub → skip (it is an inner substring)
for start, end, repl in sorted(accepted, key=lambda s: -s[0]):   # apply right-to-left
    line = line[:start] + repl + line[end:]
```

Regression-locked at `tools/test_check_doc_rename_classification.py::test_apply_no_overlap_corruption`.

## Sub-shape B — Stable-identifier / file-path rename (broken links)

A terminology sweep renames the target token INSIDE a file path, filename slug, or other stable identifier. The referenced file keeps its old name (filenames rename only when the FILE is deliberately renamed), so the reference becomes a broken link.

Worked instance (`.D.1` Phase A, post-write): the doc-rename `--write` renamed `per-core`→`per-node` inside ~28 file-path references, e.g.:
- `DOCS/recurring-bug-patterns/class-25-scope-erosion-per-core-consumer.md` → `…-per-node-consumer.md` — but the actual file is still named `…-per-core-consumer.md` → broken link.
- `DESIGN_SPECS/framework-patterns/type-erased-per-core-resource-handle-pattern.md` → `…per-node…` → broken link.

The narrative renames in those same files were CORRECT; only the path/slug renames were wrong. Caught by a post-write broken-link scan (grep for introduced `per-node…\.md` paths whose `per-core` original exists as a file), reverted, tool fixed.

**Detection signature:** after any bulk doc rename, scan for renamed tokens inside path-like strings:
```bash
git diff --no-color | grep -E "^\+.*<newtok>[A-Za-z0-9_/-]*\.(md|hpp|cpp|py)"  # introduced path refs
# for each, check if the <oldtok> filename still exists → broken link
```

**Closure mechanism:** classify a token match as `file-path-reference` (LEAVE) when it sits inside a path-like token — expand to the maximal `[A-Za-z0-9_./-]+` run around the match; it is a path/slug if that run contains `/` OR ends in a known file extension. Stable identifiers (file paths, filename slugs, catalog IDs) rename ONLY when the file/identifier itself is deliberately renamed, never in a terminology sweep. Implemented as `is_in_path_like_token()` in `tools/check_doc_rename_classification.py`; regression test `test_file_path_reference_left`.

**False-positive surface:** a genuine prose mention that happens to contain `/` (rare; e.g. "and/or") — the file-extension check + `/`-in-token heuristic is conservative; manual TSV review catches edge cases.

## Forward relevance — v5.15.5.F.4d.1.E.1 Core→Node code rename (~5,000 sites)

`.E.1` renames `Core`→`Node` across the engine. ANY regex/sed-based substitution there faces THIS class at scale: `core` is a substring of `core_strategy`, `core_risk_pct`, `MAX_CORES`, `CoreContext`, `num_execution_cores`, `score`, `record`, etc. **Preferred mitigation for `.E.1`: AST-aware `clang-rename` (handles token boundaries + overlaps natively).** If any sed/regex fallback is used, it MUST apply overlap resolution per this class + word-boundary anchoring (sister: `feedback_avoid_substring_replace_all_on_member_access`).

## False-positive surface (per M3 discipline)

- **Non-overlapping multi-sub is fine** — no resolution needed when no token is a substring of another; the class only fires when spans can overlap.
- **Single-token substitution is fine** — only one match family, no overlap possible.
- **AST-based rename tools (clang-rename, libclang, tree-sitter)** handle this natively — they operate on tokens/symbols not raw spans; flagging them is a false positive.
- **Word-boundary-anchored single-token sed** (`s/\bcore\b/node/g`) does not overlap with itself, but DOES still risk the sister Class (member-access substring mangling) — different failure mode; see sister memory.

## Sister references

- Sister memory `feedback_avoid_substring_replace_all_on_member_access` — the `replace_all` member-access mangling hazard (`config.X` mangles `ctrl->config.X`). Both are bulk-rewrite substring hazards; Class 36 is the OVERLAPPING-SPAN axis, the memory is the UNANCHORED-SUBSTRING axis.
- Sister Class 33 (consumer-enumeration undercount on deletion) — sibling bulk-operation-on-many-sites hazard.
- Sister memory `feedback_proactive_rename_candidate_surfacing` — the rename-candidate-tracking discipline this tooling serves.
