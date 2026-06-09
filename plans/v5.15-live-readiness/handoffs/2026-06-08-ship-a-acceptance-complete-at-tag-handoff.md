---
type: handoff
status: active
ship_tag: "#11 Ship-A 16B storage flip — SHIPPED + GPG-tagged v5.15.5.F.4d.1.E.0.7 (the STOP-before-money boundary, D-130). NEXT = A.5 rename → Ship B money"
plan_type: refactor (16B binary-core compaction)
sprint: v5.15-live-readiness
phase: ".E.0 FOUNDATIONAL — money is many ships away (see § Where this sits)"
sprint_end_goal: make the codebase more maintainable for future development; correctness-true foundation before the .E.1 rename + multi-exchange
decision_log: plans/v5.15-live-readiness/decision-logs/v5.15.5.F.4d.1.E-architecture-v2.md (D-97..D-160; Session-11 addendum = D-154..D-160, this session)
engine_head: f52d874 (feat/v5.15-live-readiness; SIGNED tag v5.15.5.F.4d.1.E.0.7 + PUSHED to origin)
workspace_head: 5598d68 (pushed)
predecessor_handoff: handoffs/2026-06-02-post-cleanup-ship-a-flip-handoff.md (the pre-pickup state)
pickup: /accept-handoff <this doc>
required_reading: [this doc, the decision-log Session-11 addendum (D-154..D-160), the Ship-A plan body acceptance criteria]
---

# Ship-A 16B flip — SHIPPED + GPG-tagged v5.15.5.F.4d.1.E.0.7 (2026-06-08, Session 11)

**Ship A is SHIPPED — GPG-tagged `v5.15.5.F.4d.1.E.0.7` ("Good signature from Caramel"), both repos pushed.** This session RESUMED the flip from a cut-off state (executed-but-uncommitted-and-unverified; the prior session couldn't even build the tests), de-risked it, fixed the blocker, ran the full acceptance (3246/0 + asan + ubsan + gui), closed the surfaced tech-debt (157/158), and shipped the tag. An independent deliverable review at close returned **SHIP-CLEAN**. **NEXT pickup = Ship-A.5** (the cosmetic `FPN`→`FPN_Binary` clang-rename against the now-stable 16B anchor).

## Where this sits (carry this session-to-session)
**We are in the `.E.0` FOUNDATIONAL phase. Money is many ships away.** The pipeline before any live capital:
```
.E.0.1  determinism net ............................. ✅ shipped (v5.15.5.F.4d.1.E.0.6)
#11 Ship-A : 16B binary compaction (this) .......... ✅ acceptance complete; AT THE TAG  ◀── here
#11 Ship-A.5: rename FPN -> FPN_Binary (cosmetic) .. next
#11 Ship-B : decimal money (FixedPoint<10,8>) ...... the actual money-correctness change
.E.1   Core->Node rename + per-node drainer + multi-exchange registry
.E.2+  headless + configs + docs -> WS-API -> sub-accounts -> Alpaca -> strategy hot-reload
```
The flip is the **STOP-before-money tagged boundary**: a complete, value-equivalent 16B binary core with NO money yet. Do not treat "Ship-A done" as "near live."

## State at pickup (verify — `/accept-handoff` does this)
- **Engine HEAD `7f1704e`**, **workspace `fadacf3`**, branch `feat/v5.15-live-readiness`, **NOT pushed** (tag pending).
- **Gate GREEN: controller_test 3246/0 · build.sh gui · build.sh asan 3246/0 · build.sh ubsan 3246/0** (UB-clean).
- `Version.hpp` still `5.15.5.F.4d.1.E.0.6` (the flip is NOT tagged yet — the tag is the next + final step).
- Working tree: clean except untracked `build_probe/` (leave it).

## What landed this session (commits, both repos)
Flip: engine `7304f21` (+ build-fix `655f33f`), workspace `d2814b9` (+ `b1e73e8`). Acceptance hardening: engine `097a1f2` (fp2_mul INT_MIN guard + malloc-align). Sanitizer close-out: engine `ab7fa94` (3 asan no_sanitize + build.sh FOXML_SANITIZER_BUILD). Tool: workspace `2179b75` + `3b41f67` (check_struct_alignment.py + teeth-proof + refinement). Tests/ledger: workspace `81c04d9`. Docs: engine `7f1704e`, decision log `fadacf3`. Ship ritual: engine `f52d874` + **GPG tag `v5.15.5.F.4d.1.E.0.7`**, workspace `bccd8fc`/`e4a33dc`.

**Post-ship (same session, doc-currency):** operator caught that the flip left a STALE DOC COHORT — ~15 docs still described `FPN<64>` as 24B / sign-magnitude `w[2]`+sign+padding / PERSIST-184 / versions-5/8/12. Completed a **1:1 sweep** (size + representation + PERSIST/versions — the last made RELATIVE since Ship-B changes them again) → workspace `aab2753` + `00b0e77`. Also fixed the stale **privacy-boundary recap** (CLAUDE.md/tests/DOCS were listed public; they're gitignored-private). NEW self-healing guard **`tools/check_fpn_doc_size_currency.py`** (teeth-proofed + `check_session_docs` HARD-7) parses the canonical `sizeof(FPN<64>)` from the code → flags any doc byte-size drift (caught 1 the hand-sweep missed). The struct **re-pack optimization** (exploit the 8B/field headroom) = DEFERRED-for-merit → **TECH_DEBT-159**, gated on Ship-B (same surface as the D-157 refreeze).

## What's DONE (acceptance)
- FPN<64> = 16B `FixedPoint<2,64>`; `.w[]`/`.sign` ports (OrderGates hot compares branchless `a.v>=b.v` — net latency reduction, D-133); R1 layout asserts → 16B; R3 versions 13/9/6; F=128 trait test retired; is_FPN_v unified.
- NEW acceptance tests: R2 saturate-not-wrap, D-144 version-monotonic, D-147 INT_MIN guard (all pass).
- 16B run-to-run + cross-opt determinism VERIFIED (golden refreeze DEFERRED per D-157 — numeric core in flux pre-Ship-B; the determinism pre-commit gate is bypassed-with-rationale until the core stabilizes).
- Build regression (LANDMINE 7 — symlink `../`-include) FIXED. Slice cohort retired.
- **TECH_DEBT-157** (struct-alignment guard `tools/check_struct_alignment.py`) BUILT + wired pre-commit **Check K** + teeth-proofed (`test_check_struct_alignment.py`). **TECH_DEBT-158** (pre-existing asan AVX-512 FPs + ubsan timing flake) CLOSED.

## What's LEFT — Ship A is DONE; next is A.5
Ship A is shipped + GPG-tagged + pushed; the meta-harvest postmortem is authored; the ledger tidy (157/158 → `closed.md`) is done; the independent close-review returned SHIP-CLEAN. Remaining:
1. **Ship-A.5 (the next pickup):** the cosmetic `FPN`→`FPN_Binary` clang-rename against the now-stable 16B anchor (D-143 deferred it here). Plan it → then **Ship B** (decimal money — the B1-B6 findings + the D-100 oracle gate + golden regen + un-bypass Check F) → `.E.1` Core→Node rename + multi-exchange.
2. **One standing note (NOT a blocker):** TECH_DEBT-157 (b) alignof-locks — 12 over-aligned structs could add `static_assert(alignof==N)`; the (a) guard (pre-commit Check K) is the structural close + surfaces (b) on every relevant commit (tracked-by-tooling). Leave as advisory. (If ever hard-locking: per-type qualified `tt::`/`fox_ml::mem::`/template-args — NO `using namespace tt`, it leaks globally + breaks the file.)
3. **When the numeric core stabilizes (post-Ship-B):** refreeze the 16B golden + un-bypass pre-commit Check F (D-157).

## Decisions this session (decision-log SSoT: D-154..D-160)
D-154 flip resumed + the build-regression was the true blocker (LANDMINE 7) · D-155 first-ever-sanitizer-run surfaced a BATCH of pre-existing bugs (close, don't conflate with the change) · D-156 alignment guard built now + teeth-proofed · D-157 verify run-to-run, defer the refreeze · D-158 F4 keep (metrics-only) · D-159 operator meta-stance: close-out-now over defer · D-160 ship-close meta-harvest slate (canonical code proven; author at postmortem).

## Operator norms
Address Caramel as Caramel/she/her; no AskUserQuestion modals (inline); evaluate on robustness+latency+design not time; correctness + planning over speed; **consult before the GPG tag** (STOP-before-money); branchless preferred; MED/LOW findings get a disposition; **close-out-now over defer for small in-flight finds** (D-159); no live models (D-131). When a session does a lot, CAPTURE decisions/findings/state as you go — this handoff exists because the last pickup had none.

## First action
`/accept-handoff <this doc>` → verify the gate is still green (3246/0) + the tag is live → then plan + start **Ship-A.5** (the cosmetic `FPN`→`FPN_Binary` rename; D-143). Still `.E.0` foundational — money is many ships away.
