---
type: agent-report
agent: a-class (adversarial, independent)
directive: /decision-check — REFUTE the relative-order proposal
run_date: 2026-08-17
engine_head: cddd8f6
verdict: REFUTED
status: VERBATIM — saved by the orchestrator at receipt; agent was read-only
---

> Saved verbatim per `feedback_save_agent_reports_verbatim`. Orchestrator verification of each
> load-bearing claim lives in this directory's README, NOT inline here.

---

# A-CLASS ADVERSARIAL VERDICT — `stamp-key` ledger semantics: positional ordinal vs. name-set + relative order

**Target:** the D-426 "Candidate fix" (open decision (i)) — replace `("stamp-key", …, {"prefix": "", "value": "positional"})` at `tools/check_identifier_retirement.py:157-158` with name-set membership + relative order.

**VERDICT: REFUTED.** Two measured counterexamples where positional REDS and the proposal goes silent, on an HMAC-signed body. The stated motivation is misdiagnosed at the wrong layer — the real mechanism producing "one true signal buried" is a `tail -12` in the pre-commit hook, which I measured truncating the true signal out entirely. And the change would delete the only remaining mechanical lock on the emit order of the model-const half of the signed body.

**Everything below is measured**, not reasoned. Experiments ran against a copy of the source tree at `~/.cache/cir_lab/tree` via `FOXML_REPO_ROOT` + a ledger copy via `IDENTIFIER_LEDGER`. `tools/identifier_ledger.txt` md5 `9adc0132fed895e72e5d8c8c6d56ca10` unchanged; `git status --porcelain` shows only the four pre-existing untracked operator files; `--update` never invoked.

## 0. Baseline (both tools RUN)

```
python3 tools/check_identifier_retirement.py
  -> rc=0  "GREEN — 94 persisted/wire identifiers match the ledger"
bash tools/check_identifier_retirement_selftest.sh
  -> rc=0  PASS, 6 legs, incl. "stamp-key non-vacuity -> 46 wire keys resolved from the live registry"
```

Ledger composition: `stamp-key` 46 · `enum:ShaltCode` 20 · `enum:NodeStateFlag` 6 · `enum:BanditAlgorithm` 5 · `enum:RegimeId` 5 · `enum:StrategyId` 5 · `version` 5 · `wire-const` 2.

Registry shape: PRE_CFG `:344` = **22** rows -> ordinals 0-21; POST_CFG `:462` = **24** rows -> ordinals 22-45; union `:561-563`. Emit walk (`ModelInference.hpp`): fixed header `:2249-2274` -> PRE_CFG `:2291-2298` -> `cfg_derived::populate_stamp_cfg_from_derived` `:2313-2317` -> POST_CFG `:2324-2331` -> `tt::hmac_sha256_hex` `:2352`.

## 1. The claim, clause by clause

> *"relative-order is not a weakening — drop still reds, reorder still reds, and only mid-INSERT differs, where positional wasn't protecting anything anyway because an insert changes signed bytes wherever it lands and additions are already info-only."*

| Clause | Verdict | Measurement |
|---|---|---|
| "drop still reds" | **TRUE** | E1 delete ordinal 0 -> proposal: `violations=1 (REMOVED)`, RED. Positional: 46 violations, RED. |
| "reorder still reds" | **TRUE for a pure permutation** | E7 adjacent swap -> proposal RED (1 REORDERED); positional RED (2 RENUMBERED). |
| "**only** mid-INSERT differs" | **FALSE** | A **duplicate key emission** also differs (2.2). The quantifier is wrong — M9 applies: the set was not enumerated. |
| "positional wasn't protecting anything [at mid-insert]" | **FALSE** | 2.1 — it is a hard `OVERALL_FAIL=1` commit block today, and mid-insert is the exact operation the governing spec names as HMAC-chain-breaking. |
| "an insert changes signed bytes **wherever it lands**" | **FALSE as stated** | `wire-format-byte-preservation-discipline.md:214` distinguishes them explicitly; the registry does too (`:519-523`, `:539-541`). |
| "additions are already info-only" | **True but circular** | It is info-only *because the ordinal shift is what converts a dangerous add into a violation*. Remove the ordinal and the premise becomes self-fulfilling. |

## 2. Counterexamples — measured

### 2.1 [HIGH] C1 — mid-INSERT: hard RED -> silent GREEN, on the one operation the spec forbids

Planted a new row after `model_num_outputs` (ordinal 4), inside the `xgb_hyperparams` region of PRE_CFG.

```
positional TODAY  : violations=41 (RENUMBERED), adds=1  -> rc=1  RED   (pre-commit BLOCKS)
proposed          : violations=0,               adds=1  -> rc=0  GREEN (commit proceeds)
```

Both implementation variants I simulated (deduped-map and raw-row-list) go GREEN.

> `wire-format-byte-preservation-discipline.md:214` — *"**Risk:** if a NEW field is inserted in the middle of `FOREACH_CFG_FIELD` (rather than at the end of the flagged subsequence), the derived walk produces fields in a DIFFERENT order. HMAC chain breaks for all legacy stamps."*

The registry encodes the same distinction in its two most recent POST_CFG additions:
- `StampBoundModelConstRegistry.hpp:519-523` — *"Appended AT END of POST_CFG section for HMAC chain byte preservation…"*
- `:539-541` — *"APPEND-at-end preserves HMAC chain byte equivalence for legacy stamps (Surface G forward-compat)"*

`/parity-check` SKILL.md `:380-389` (Section N, "Row-order parity") reinforces: an emit reorder must be *"annotated as intentional reorder under SOFT-bump procedure"*. Positional is the mechanical trigger that forces the human to reach that procedure. Blast radius of removing it: `.githooks/pre-commit:424-441` Check H is a hard `OVERALL_FAIL=1` firing on `^ML_Headers/`, so today a mid-insert **cannot be committed** without a TTY bless.

### 2.2 [MED-HIGH] C2 — DUPLICATE wire key: RED -> silent GREEN

Planted `X(feature_mask, …)` a second time at the tail of POST_CFG. The signed body would emit `feature_mask=…` **twice**.

```
positional TODAY                                  : violations=1 (RENUMBERED feature_mask 17 -> 46)  RED
proposed, V0 (no value column, parse-order names) : violations=0                                     GREEN
```

Mechanism: `_parse_foreach` builds a dict (`:236`, `out[full] = val`), and re-assigning an existing key does not move its insertion position. Once the ordinal is dropped, the surviving name sequence is byte-identical to the frozen one.

**A proposal that changes the guard's data structure without specifying which sequence is compared is underspecified at exactly the point where it changes behavior.**

## 3. Interrogating the premise — are the 45 "false signals"?

**No. They are true, they are not buried, and the burying that does occur has a different cause.**

**(a) They are TRUE.** Deleting ordinal 0 removes one `key=value\n` line, so the byte offset of all 45 remaining keys genuinely moves. The tool reports 45 facts, not 45 errors. M3's cry-wolf concept is about **false** positives — and the D-425 precedent shows the bar: design (1) was refuted because it *"graded `inference_cfg` GREEN (the actual CRITICAL) and `feature_mask` RED (which was benign) — inverted on both headline cases."*

**(b) They are not buried in the tool's own output.** `compare()` iterates the frozen dict in ledger order (sorted by `(value, name)`, `:293-296`), so the `REMOVED` line prints **first**:

```
  X REMOVED  stamp-key :: inference_cfg_bandit_blend_ratio (was 0) — a persisted/wire identifier vanished…
  X RENUMBERED stamp-key :: training_poll_interval 1 -> 0 …
```

**(c) The burying is real — and it is a `tail -12`.** `.githooks/pre-commit:431`:

```bash
ID_OUT=$(python3 "$ID_TOOL" 2>&1); ID_RC=$?
echo "$ID_OUT" | tail -12
```

I ran the row-0 delete and applied the hook's exact truncation. Measured: the last 12 lines are 8 `RENUMBERED` lines plus the 4-line trailer. `grep -c 'REMOVED'` on that output = **0**. The one true signal is discarded by the display, not by the semantics.

**This is the load-bearing finding of the whole audit.** Changing the comparison semantics of the Knight-Capital guard to compensate for a shell truncation is a category error — and it would leave the truncation in place, so the *next* multi-line violation on any other category is buried identically.

**(d) The proposal does not even solve the stated problem.** Measured: under the proposal, deleting ordinal 0 still yields `violations=1 (REMOVED)` -> still RED -> still `rc=1` -> still blocks the commit -> still requires the operator's TTY `--update` bless (`bless.py:110-133`). The only delta is 45 fewer printed lines on an operation that reds and requires a bless either way.

## 4. Class 51 — vacuity and teeth

**[HIGH] The proposal deletes the category's only tooth with no drop-in replacement.**

`check_identifier_retirement_selftest.sh:89-106` (case 4) plants `stamp-key|feature_mask|9999` and asserts the output names `RENUMBERED stamp-key :: feature_mask`. That case is *unimplementable* once the value stops being compared. Its comment (`:83-87`) explains it was deliberately anchored on the CODE side — *"Anchoring them on a blessed ledger row would have made them vacuous for exactly the window in which the enrollment is new and least trusted."*

No replacement is available in the harness. `:21-29` deliberately makes the selftest mutate only a **ledger copy** and never the source. A **reorder lives in the `.hpp`** — so this harness structurally cannot plant the positive control the proposal would need.

**Could the relative-order check go quiet on more than intended?** Yes: `ledger_lines()` sorts each category by `(value, name)` (`:293-296`). Drop the value and the file sorts **alphabetically**, destroying the frozen sequence. Preserving order then requires making **line order** load-bearing in the golden — invisible in diff review, destroyed by any `sort`, unannounced by the format comment at `identifier_ledger.txt:5`. The alternative — keep the value column but stop comparing it — leaves 46 ledger rows carrying numbers nothing checks: a golden that *looks* live and is not.

## 5. Pre-existing defects found on this surface — the actual work

### [HIGH] D1 — the retired-name burns are vacuous for wire keys and enum members

`retired_name_check()` (`:352-386`) matches only `^\s*#\s*define\s+NAME\b` (`:365`). Three of four `RETIRED_NAMES` entries (`:102-104`) can never take that shape:
- `inference_cfg_fee_rate_maker` / `_taker` come back as `X(name, …)` registry rows.
- `STAMP_BIT_fees` is an **enum member** (`StampBoundModelConstRegistry.hpp:606-624`), never a `#define`.

Measured — resurrecting all three:

```
[identifier-retirement] ADD (ok; run --update to record): stamp-key :: inference_cfg_fee_rate_maker = 46
[identifier-retirement] ADD (ok; run --update to record): stamp-key :: inference_cfg_fee_rate_taker = 47
[identifier-retirement] GREEN — 96 persisted/wire identifiers match the ledger; no renumber/reuse/drop.
rc=0
```

`STAMP_BIT_fees` produced *nothing at all* — not even an `ADD`. Positive control confirms the sweep works for the `#define` shape (planting `#define CONTROLLER_SNAPSHOT_VERSION 14` fires `RETIRED-NAME-REUSE … at CoreFrameworks/Portfolio.hpp:817`).

This falsifies the tool's own comment at `:91-94`:
> *"Burning the names here is what makes that deletion ENFORCED rather than narrated — without these entries a re-introduced `STAMP_BIT_fees` classifies as a fresh 'ADD (ok)' instead of the Knight-Capital-shaped reuse it would be."*

Measured: **with** the entries present, a re-introduced `STAMP_BIT_fees` produces less than "ADD (ok)", and re-introduced fee-rate keys produce exactly the "ADD (ok)" the comment says is prevented.

**Why this outranks the ordinal question.** For a wire KEY, H21's tombstone remedy is not "keep the row" — Rule 1a forbids that, because an emitting row with no producer *"does not go dead, it goes LYING."* The remedy for a wire key **is** the name burn. So the H21-doctrinal path for queue item 2 is: delete the row -> add the name to `RETIRED_NAMES` -> bless. That burn is currently **inert**. Fixing `retired_name_check()` to also recognize `X(<name>,` rows and bare enum members is a ~10-line change and is a genuine prerequisite for item 2 in a way the ordinal semantics is not.

### [MED] D2 — the PRE_CFG/POST_CFG seam is order-blind, under BOTH designs

Moved `xgb_train_nthread` from the tail of PRE_CFG to the head of POST_CFG — relocating it in the signed body from **before** the entire cfg-derived block to **after** it.

```
positional TODAY : rc=0 GREEN
proposed (V0)    : rc=0 GREEN
```

Cause: the `SOURCES` row names the **union** macro, whose body is `PRE_CFG(X) POST_CFG(X)`. Concatenating the halves and indexing 0-45 flattens the seam; the ordinal is a **registry** ordinal, not a wire ordinal. Class 51 mode B'' (wrong-region positional scan).

This falsifies the justification comment at `:146-150`. **Fix (verified, Alt-B):** split into two `SOURCES` rows.

### [MED] D3 — the cited verification artifact cannot support the claim it is cited for

`:150` — *"Verified against a real artifact (models/\*\*/barrier.json.stamp) — parsed order matches the emitted key order."*

Measured across all 16 `.stamp` files: **every one is `stamp_format_version=1`.** `ModelInference.hpp:159` sets `STAMP_FORMAT_VERSION_CURRENT = 3` and `:166` sets `STAMP_FORMAT_VERSION_EPOCH_FLOOR = 3`, with a hard refuse at `:1806-1811`. The richest one opens with five keys that no longer exist, lacks 20+ current keys, and contains **zero** cfg-derived keys — so it cannot exhibit the PRE->cfg->POST interleave the claim is about.

### [MED] D4 — the ledger tracks the REGISTRY, not the EMIT

`parse_current()` parses macro bodies; it has no view of `STAMP_EMIT_CHECK_HAS_##group`. Consequence: **"don't delete the row, just remove the `STAMP_SET` line"** produces *zero* ledger output — the key vanishes from the signed body while the guard stays GREEN. That option is separately refuted by H21 Rule 1 (a dormant reactivatable row compiled in — the Power Peg shape verbatim), but the silent-guard property bounds every claim about this category: `stamp-key` is a **proxy** for the wire, not a measurement of it.

### [LOW-MED] D5 — the violation messages give the wrong remedy for this category

`:330-332` says *"Allocate a NEW identifier"* — for a wire key there is no code to allocate; the correct remedy is "don't reorder, or bump `STAMP_FORMAT_VERSION` + re-bless."
`:318-320` says *"TOMBSTONE the slot … do not drop the row"* — for a stamp key you *must* drop the row (Rule 1a). Both messages are enum-shaped. A guard that prescribes an impossible remedy trains the operator to discount it.

### [LOW-MED] D6 — wire-format invariant I5 is a tautology

`tests/wire_format_invariants.hpp:170`: `check(tname, body_len == 0 || true);  // vacuous at .A; .B extension TBD`. `wire-format-byte-preservation-discipline.md:226` advertises I5 as catching *"Walker invocation order regression."* It catches nothing.

### [LOW] D7 — Class 58 complement: the middle third of the signed body is unenrolled

36 rows carry `STAMP_BOUND_CFG_DERIVED` (31 in `CfgFieldRegistry.hpp`, 5 in `MlCfgFlagRegistry.hpp`) and emit into the same HMAC body. **Zero** are in the ledger. Coverage of the signed body's keys is 46 of ~82.

### [LOW] D8 — two stale comments

- `StampBoundModelConstRegistry.hpp:342` — *"26 entries today"*; measured **22**.
- `ModelInference.hpp:2222` — *"must match bash script + verifier byte-for-byte"*; the bash producer `tools/stamp_model.sh` was deleted at `.B.3`.

## 6. What the change would cost that the proposal did not price

**[MED-HIGH] It deletes the only order lock on the model-const half of the signed body.**
- Layer 5 (locked canonical-body hash) was **rejected** at `.F.4d.1` in favour of Layer 5b. No hash lock exists.
- Layer 5b's I1-I5 (`tests/wire_format_invariants.hpp:65-171`): I1 = line **count**; I2 = kv pattern; I3 = no comma; I4 = name **membership** via `strstr`; I5 = tautology. **None checks order.**
- The single invocation (`controller_test.cpp:29324`) passes the **cfg-derived** half, not PRE_CFG/POST_CFG.

Note the irony: I4 already *is* name-set membership. The proposal would make `stamp-key` a weaker duplicate of an existing test-layer invariant while deleting the unique property.

**[MED] It contradicts the paired-bump precedent in the same file.** `paired_bump_check()` (`:389-440`) enforces *layout delta => version bump, same commit*, built to close the D-208 triple-vacuity. `DOCS/TOOLS.md:71` records that golden as *"a LIST, never a digest — diffs name rows … order-sensitive,"* with 21 teeth including a planted count-neutral NAME-SWAP. The proposal would leave the one **HMAC-signed** body with weaker semantics than the unsigned per-node persist wire.

**[MED] Blast radius of the ledger-format edit.** Any row-format change forces a full re-bless of a 94-identifier Knight-Capital golden through `bless.py`'s TTY gate.

**[LOW-MED] Information loss.** The 46 blessed ordinals are the only surviving record of the signed body's key order (every on-disk artifact is pre-epoch, D3).

## 7. The simpler/safer options the proposal skipped

**Alt-A — roll up the consequential lines in the REPORT. Zero semantics change. Recommended.**
1. `.githooks/pre-commit:431` — replace `tail -12` with a form that cannot discard the leading cause.
2. `compare()` — when a REMOVED/ADD induces a uniform +/-k shift across a contiguous suffix of a non-monotonic category, collapse to one line: `SHIFTED stamp-key :: 45 keys shifted -1 (…) — consequence of the REMOVED above.`

Still RED. Still `rc=1`. Still requires the bless. Operator reads 2 lines instead of 46. **Every positional tooth intact, selftest case 4 intact, ledger format untouched, no re-bless.** ~15 lines in one function.

**Alt-B — split `stamp-key` into two `SOURCES` rows (closes D2). Verified:**

```
TWO-CATEGORY enrollment vs the seam-move tree: violations=25 adds=1 -> RED
  REMOVED  stamp-key-pre :: xgb_train_nthread (was 21)
  RENUMBERED stamp-key-post :: expected_num_classes 0 -> 1
  ADD: stamp-key-post :: xgb_train_nthread = 0
```

**Alt-C — fix `retired_name_check()`'s shape blindness (closes D1).** A genuine prerequisite for queue item 2.

**Alt-D — fix the two remedy strings (closes D5).**

**Does H21's own doctrine already answer this without a tool change?** Partly. For an enum CODE the number is the persisted thing, so "keep the number" works. For a wire KEY the **name** is the persisted thing and the ordinal is a derived emit position — so H21's tombstone maps to *burn the name*. That path produces exactly the 1 REMOVED + 45 RENUMBERED, all true, and requires the same bless. The doctrine does not eliminate the 45 lines, but it also does not require the tool change. What it *does* demand, and what is missing, is Alt-C.

A tombstone-slot variant (a marker consuming an ordinal so survivors keep numbers) is **not** recommended: for a wire key the survivors' positions genuinely move, so a slot-holding tombstone would make the ordinal lie.

## 8. Proportionality

| | |
|---|---|
| Benefit | 45 fewer console lines, once, on an operation that reds and requires a TTY bless either way |
| Cost | mid-insert detection (measured RED->GREEN); duplicate-key detection (measured RED->GREEN); selftest case 4 with no expressible replacement; the only order lock on 46 signed-body keys; a full re-bless of the 94-row golden; the frozen record of the current body order |
| Correct target | `.githooks/pre-commit:431` `tail -12`, plus a roll-up in `compare()` |

Not proportionate.

## 9. Where I could be wrong (refute-spots)

1. **A sophisticated relative-order implementation could catch C2.** My V1 variant did — but V1 derives its sequence from the value, i.e. keeps positional storage and only relaxes comparison, reintroducing the dead-column problem. If the proposer means V1, that should be stated, and C2 falls while C1 stands.
2. **I did not compile-verify the wire effect of the planted mutations.** A compiled byte-probe would upgrade C1/C2 from structural to measured-in-bytes.
3. **D7 may be deliberate paced enrollment** in the spirit of `TECH_DEBT-152`; reported as a gap, not a defect.
4. **D2's severity depends on how plausible a seam-crossing move is.** It requires editing two macro bodies — but it is exactly the shape a "tidy the registry" refactor produces.
5. **I honored the D-425/D-426 record and did not re-litigate** designs (1)-(4) or the `STAMP_PUT` adoption.

## 10. Bottom line

**REFUTED.** Keep `value: "positional"`.

The 45 lines are true, and the operator never sees the one that matters because of `.githooks/pre-commit:431`, not because of the ledger. Fix the display (Alt-A). Then close the three real defects — the vacuous name burns (D1, which gates queue item 2), the seam blindness (D2, verified fix in hand), and the enum-shaped remedy strings (D5). All four are additive, none touches the ledger format, none costs a re-bless, none removes a tooth.

**Ordering recommendation:** (i) resolves as *no change + Alt-A*, which unblocks (ii) immediately — but **Alt-C should land before (ii)**, or deleting `inference_cfg_bandit_blend_ratio` burns its name into a set that cannot enforce it, which is the `fees` mistake repeated on the row three lines below it.

Experiment harness (re-runnable): `~/.cache/cir_lab/` — `tree/`, `ledger_base.txt`, `proposed.py` (V1/V2), `proposed2.py` (V0).
