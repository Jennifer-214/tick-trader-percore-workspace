---
type: handoff
status: active
ship_tag: "#11 Ship-A 16B storage flip — ACCEPTANCE COMPLETE; at the STOP-before-money GPG tag (the only remaining step)"
plan_type: refactor (16B binary-core compaction)
sprint: v5.15-live-readiness
phase: ".E.0 FOUNDATIONAL — money is many ships away (see § Where this sits)"
sprint_end_goal: make the codebase more maintainable for future development; correctness-true foundation before the .E.1 rename + multi-exchange
decision_log: plans/v5.15-live-readiness/decision-logs/v5.15.5.F.4d.1.E-architecture-v2.md (D-97..D-160; Session-11 addendum = D-154..D-160, this session)
engine_head: 7f1704e (feat/v5.15-live-readiness; NOT pushed — flip + acceptance committed locally, tag pending)
workspace_head: fadacf3
predecessor_handoff: handoffs/2026-06-02-post-cleanup-ship-a-flip-handoff.md (the pre-pickup state)
pickup: /accept-handoff <this doc>
required_reading: [this doc, the decision-log Session-11 addendum (D-154..D-160), the Ship-A plan body acceptance criteria]
---

# Ship-A 16B flip — ACCEPTANCE COMPLETE, at the tag (2026-06-08, Session 11)

**The flip is DONE and the full gate is GREEN. The ONLY remaining step is the GPG tag** (STOP-before-money, D-130 — operator consult). This session RESUMED the flip from a cut-off state (it had been executed-but-uncommitted-and-unverified, and the prior session couldn't even build the tests), de-risked it, fixed the blocker, ran the full acceptance, and closed out the surfaced tech-debt.

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
Flip: engine `7304f21` (+ build-fix `655f33f`), workspace `d2814b9` (+ `b1e73e8`). Acceptance hardening: engine `097a1f2` (fp2_mul INT_MIN guard + malloc-align). Sanitizer close-out: engine `ab7fa94` (3 asan no_sanitize + build.sh FOXML_SANITIZER_BUILD). Tool: workspace `2179b75` + `3b41f67` (check_struct_alignment.py + teeth-proof + refinement). Tests/ledger: workspace `81c04d9`. Docs: engine `7f1704e`, decision log `fadacf3`.

## What's DONE (acceptance)
- FPN<64> = 16B `FixedPoint<2,64>`; `.w[]`/`.sign` ports (OrderGates hot compares branchless `a.v>=b.v` — net latency reduction, D-133); R1 layout asserts → 16B; R3 versions 13/9/6; F=128 trait test retired; is_FPN_v unified.
- NEW acceptance tests: R2 saturate-not-wrap, D-144 version-monotonic, D-147 INT_MIN guard (all pass).
- 16B run-to-run + cross-opt determinism VERIFIED (golden refreeze DEFERRED per D-157 — numeric core in flux pre-Ship-B; the determinism pre-commit gate is bypassed-with-rationale until the core stabilizes).
- Build regression (LANDMINE 7 — symlink `../`-include) FIXED. Slice cohort retired.
- **TECH_DEBT-157** (struct-alignment guard `tools/check_struct_alignment.py`) BUILT + wired pre-commit **Check K** + teeth-proofed (`test_check_struct_alignment.py`). **TECH_DEBT-158** (pre-existing asan AVX-512 FPs + ubsan timing flake) CLOSED.

## What's LEFT (just the tag)
1. **The ship ritual + GPG tag (operator consult — STOP-before-money):** bump `Version.hpp` (proposed `v5.15.5.F.4d.1.E.0.7`, monotonic-at-ship D-88 — confirm vs MASTER) + CHANGELOG + postmortem (AUTHOR the D-160 + D-153 meta-harvest here: value-equivalent-storage-flip methodology, branchless-guard-via-safe-compute-and-mask, the first-sanitizer-run-batch meta-pattern, no_sanitize-on-verified-AVX-512, FOXML_SANITIZER_BUILD) → 5-binary clean verify → GPG tag → push → `/sync-workspace`.
2. **Two small noted items (operator's call, NOT blockers):**
   - **TECH_DEBT-157 (b) alignof-locks** — 12 over-aligned structs lack a `static_assert(alignof==N)`. The (a) guard is the structural close + the live Check K surfaces (b) on every relevant commit (tracked-by-tooling). Recommended: leave as standing advisory. If hard-locking: do it per-type qualified (tt:: / fox_ml::mem:: / template args; NO `using namespace tt` — it leaks globally and breaks the file).
   - **Ledger tidy** — move TECH_DEBT-157 + 158 from `open.md` to `closed.md` (resolved this session).
3. **Then:** Ship-A.5 (rename) → Ship-B (decimal money, the B1-B6 findings + divmul N=127).

## Decisions this session (decision-log SSoT: D-154..D-160)
D-154 flip resumed + the build-regression was the true blocker (LANDMINE 7) · D-155 first-ever-sanitizer-run surfaced a BATCH of pre-existing bugs (close, don't conflate with the change) · D-156 alignment guard built now + teeth-proofed · D-157 verify run-to-run, defer the refreeze · D-158 F4 keep (metrics-only) · D-159 operator meta-stance: close-out-now over defer · D-160 ship-close meta-harvest slate (canonical code proven; author at postmortem).

## Operator norms
Address Caramel as Caramel/she/her; no AskUserQuestion modals (inline); evaluate on robustness+latency+design not time; correctness + planning over speed; **consult before the GPG tag** (STOP-before-money); branchless preferred; MED/LOW findings get a disposition; **close-out-now over defer for small in-flight finds** (D-159); no live models (D-131). When a session does a lot, CAPTURE decisions/findings/state as you go — this handoff exists because the last pickup had none.

## First action
`/accept-handoff <this doc>` → verify gate still green → then the ship ritual + the tag consult (propose the version, draft CHANGELOG + postmortem with the meta-harvest, then GPG-tag with operator go).
