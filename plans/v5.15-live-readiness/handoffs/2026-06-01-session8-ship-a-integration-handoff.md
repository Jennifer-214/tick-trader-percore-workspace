---
type: handoff
ship_tag: "Session-8 close — #11 pre-coding DONE + Ship-A proof scaffold DONE; next = Ship-A PRODUCTION INTEGRATION (the 16B binary compaction). No version bump this session (pre-coding + proof scaffold; no engine behavior change)."
plan_type: refactor (16B binary core compaction; the unified FixedPoint<RADIX,FRAC> foundation)
sprint: v5.15-live-readiness
sprint_end_goal: make the codebase more maintainable for future development (MVP → professional; .E is the foundational rework)
ship_end_goal: "Ship A — compact the binary numeric core FPN<64> (24B sign-magnitude) → FixedPoint<2,64> (16B two's-complement), VALUE-equivalently (D-139), reusing the .E.0.1-certified bodies; tag as the STOP-before-money boundary (D-130). Ship B (decimal money) follows."
coding_status: pre-coding-complete + Ship-A-proof-scaffold-complete (the integration is the next coding phase)
predecessor_handoff: handoffs/2026-06-01-v5.15.5.F.4d.1.E-session7-tools-run-and-11-resume-handoff.md
decision_log: plans/v5.15-live-readiness/decision-logs/v5.15.5.F.4d.1.E-architecture-v2.md (D-97..D-141; SSoT)
engine_head: 575a31c (feat/v5.15-live-readiness; PUSHED to origin) — 3 tooling commits this session (e9244de Session-7 tools + 3d0e1df enumeration-guard+ubsan + 575a31c Ship-A proof scaffold); NO behavior change, NO version bump.
workspace_head: 6e82046 (PUSHED) + this handoff's own commit on top.
pickup: /accept-handoff <this doc>
---

# Session-8 handoff — #11 Ship-A production integration (the 16B binary compaction)

**Created 2026-06-01.** This session resumed #11 at Phase 1, ran the WHOLE pre-coding pipeline (proof → fold → 9-audit gate re-fire → blindspot → amendments), built the session's meta-tooling, and de-risked Ship A end-to-end with a PROVEN proof scaffold. The next work is the **Ship-A production integration** — mechanical-ish (apply the proven slice pattern to the real header + migrate sites), best done with fresh context. Everything is committed + pushed (both repos).

## 1. State (verify at pickup — `/accept-handoff` does this)
- **Engine HEAD `575a31c`** (`feat/v5.15-live-readiness`, pushed). 3 tooling commits this session; no engine behavior change, no version bump. Working tree has pre-existing untracked `.E.2` doc drafts + `build_probe/` (from before this session — unrelated; leave them).
- **Workspace HEAD `6e82046`** (pushed) + this handoff on top.

## 2. THE NEXT WORK — Ship-A production integration (task #20)

**The risky part is DONE.** `tools/ship_a_fp2_64_slice.cpp` is the PROVEN TEMPLATE: `FixedPoint<2,64>` (16B `__int128` two's-complement) is value-equivalent to `FPN<64>` across the entire value-net op surface — **258/258**: `Mul`(C1 `FP64_Mul`-reduce hoist) `Abs` `Negate` `AddSat` `SubSat` `Sub` `Min` `Max` `Div`(long-div) `Sqrt`(NR) + sign-XOR(Mul/Div neg operands). Recompile+run it to re-confirm: `g++ -std=c++20 -O3 -march=native -DUSE_NATIVE_128 -I. tools/ship_a_fp2_64_slice.cpp -o /home/caramel/code/FoxML_Trader_v2/_x && /home/caramel/code/FoxML_Trader_v2/_x; rm -f /home/caramel/code/FoxML_Trader_v2/_x` (NOTE: `/tmp` is noexec on this box — output the binary to the repo dir, not `/tmp`).

`tools/fp_value_equivalence_golden.cpp` + `.txt` = the **D-139 value-equivalence NET**: emits the op-vector as LAYOUT-INDEPENDENT `sign + 128-bit magnitude` (not raw bytes), so 24B-sign-mag and 16B-two's-comp match IFF values match. The `.txt` (80 lines) is the frozen baseline the 16B build must reproduce = the P1 STOP-before-money gate.

**Integration sequence (the slice = the bodies):**
1. Define `FixedPoint<2,64>` in `FixedPoint/FixedPointN.hpp` — a bare 16B `__int128`, value = `v / 2^64`. The slice's `fp2_mul`/`fp2_div`/`fp2_neg`/etc. ARE the op bodies (abs-in / shared unsigned body / reduce / sign-out / saturate). Mul reuses `FP64_Mul`'s 256-bit reduce (the C1 hoist).
2. **Trait-split (B6, blindspot):** `is_fp_binary_v` (`<2,FRAC>`) vs `is_fp_decimal_v` (`<10,FRAC>`); `is_FPN_v` becomes a binary-only alias. Make every `tt::` wire dispatcher's `static_assert` exhaustive + an `always_false` final-`else` → a missing decimal branch = COMPILE ERROR (turns the silent-lossy-emit risk into a build error).
3. **−2⁶³ abs/negate guards (B1, blindspot — SILENT UB):** two's-comp `abs(INT128_MIN)`/`-INT128_MIN` overflow; the production abs/negate must saturate-or-flag. Build under the `ubsan` lane (`build.sh ubsan` exists — `-fsanitize=signed-integer-overflow,undefined`) + a `±INT_MIN` probe test; UBSan-clean is a Ship-A acceptance row.
4. **Preserve the `of_mask` saturate-on-overflow** (R2) — verified present in both `FPN_Mul:612-622` and `FP64_Mul:153-156`; the 16B mul MUST keep it. A max-magnitude probe confirms saturate-not-wrap at 2⁶³.
5. **Port the NOT-YET-proven feature-only transcendentals** (`Exp` `Log` `InvSqrt` `Sin` `Cos` `Pow`) — same abs-in/unsigned-body/sign-out pattern; not in the value-net golden, so test them separately.
6. **Migrate the ~3000 FPN sites** — simplest is to `using FPN<64> = FixedPoint<2,64>` (alias) so sites don't move; or a typedef. Decide alias-vs-rename at pickup.
7. **Re-derive the R1 layout-asserts** (the full set is in the plan body's "H12 / layout-assert relocation set" — `gen_code_map --byte-context FPN` verbatim: Position offset ladder, Order, ExecutionCore:176, GCN:31, FlowFeatures, OrderEventLog, `controller_test sizeof==24`→`==16`, `fp_determinism_golden.cpp`) + **R3 version bumps** (`CONTROLLER_SNAPSHOT_VERSION`=12, `SHARDED_SNAPSHOT_VERSION`=8, `PORTFOLIO_SNAPSHOT_VERSION`=5).
8. **Re-freeze the value-golden under the 16B build** (the harness reads the new type, output must == the frozen `.txt`) = P1 gate → **tag Ship A** (STOP-before-money, D-130).

**Then Ship B** (decimal money — `FixedPoint<10,8>`, the divmul `÷10⁸` reduce N=127 M=`0x55e63b88c230e77e7ee106959b5d3e1f` S=153 per D-140, + the B1-B6 Ship-B findings: C3 LIVE-fee, fee-sites, dispatcher, price-domain, EngineCommon).

## 3. SSoT + critical pickup reads
- **Decision log D-97..D-141** (`decision-logs/v5.15.5.F.4d.1.E-architecture-v2.md`) — the SSoT. Read **D-139** (P1-gate = value-equivalence NOT byte-identity), **D-140** (divmul proof), **D-141** (step-7 + the 3 mechanical guards + EngineCommon).
- **Plan body v0.2** `subplans/2026-05-30-v5.15.5.F.4d.1.E-money-numeric-core-foundation.md` — SSoT-aligned; the full R1-R3/B1-B6 amendments + the EngineCommon B2 fold + the blindspot guards + the relocation set.
- The Ship-A scaffold: `tools/ship_a_fp2_64_slice.cpp` (the template) + `tools/fp_value_equivalence_golden.cpp`/`.txt` (the net).
- `FixedPoint/FixedPointN.hpp` (the FPN body to port; `FP64_Mul` reduce at `FixedPoint64.hpp:134-160`) + the Phase-1 proof bundle `plan_checks/2026-06-01-11-phase1-divmul-proof/` (PROOF.md + the two .py) + `plan_checks/2026-06-01-11-refire-synthesis.md` + `plan_checks/blindspot-scan-2026-06-01-11.md`.
- Before coding: `DOCS/STRATEGY_AND_CODING_RULES.md` (H1-H20) + `plans/_cross-cutting/2026-05-06-latency-path-discipline.md`.

## 4. Session meta-tooling (surface it — it earned its keep)
- `tools/check_plan_enumeration_completeness.py` (+ self-test) — **AR-1 mechanization**: verifies a plan's claimed enumeration set ⊇ the code-intel tool's output (summarize-and-drop = red build); wired into `/precoding-audit-gate` Stage 2.5. **It caught `EngineCommon_ApplyBnbDiscount` (`EngineCommon.hpp:158/159`) — a money site (fee_rate × BNB-discount + a lossy `FromDouble(0.75)`) that ALL 9 audit agents + the blindspot scan MISSED** → folded into B2.
- `build.sh ubsan` lane (B1 mechanical guard). `is_fp_binary_v`/`is_fp_decimal_v` trait-split design (B6). Memory `feedback_paste_tool_output_dont_summarize`. Catalog: AR-1 recurrence in `meta-anti-pattern-index.md`; B1/B6 detection-guards in `implementation-layer-blindspot-taxonomy.md`.

## 5. TaskList state (recreate at `/accept-handoff` Stage 7)
| ID | Status | Subject |
|---|---|---|
| #1 | completed | .E.0.1 determinism net ship (tag E.0.6) |
| #2 | pending | Codify .E.0.6 tail (AR-4 wiring + locale-sister) |
| #3 | in_progress | #11 numeric-foundation (umbrella; Ship A/B remain) |
| #4 | pending | D-98 backlog → .E-home mapping |
| #5 | pending | .E.1 Core→Node rename (blocked by #3 + #8) |
| #6 | in_progress | SWAR parse (POST-#11) |
| #7 | pending | concern-tags |
| #8 | pending | Standing CI orphan-guard (.E.1-prep) |
| #9 | pending | Un-attributed working-tree mutation guard |
| #10 | pending | Detached-stdin hang-class remainder |
| #11 | pending | Harvest at /close-session (PL-4 tell + F-B) |
| #12 | pending | Numeric-width design space (16B DECIDED) |
| #13 | pending | Future numeric-optimization stack coherence |
| #14 | pending | DESIGN_SPEC: divide-by-invariant-constant reciprocal-multiply (the divmul generalization) |
| #15 | in_progress | gen_code_map tool (9 modes DONE; remaining = wiring) |
| #16 | pending | #11 Phase 0 — scope-truth (0a blast-radius DONE) |
| #17 | completed | #11 Phase 1 — divmul proven + D-100 oracle |
| #18 | completed | #11 Phase 2 — step-6 fold + Ship A/B decompose |
| #19 | completed | #11 Phase 3 — step-7 re-audit (gate + blindspot + amendments) |
| #20 | in_progress | **#11 Phase 4a — Ship A 16B compaction: proof scaffold DONE; PRODUCTION INTEGRATION = NEXT** |
| #21 | pending | #11 Phase 4b — Ship B (#11 decimal money) |
| #22 | in_progress | Tools-discipline (inventory + 3-way guard DONE; tail paced) |
| #23 | pending | Cascade/impact tool: clang call-graph |
| #24 | pending | Tools-run DESIGN_SPECs (incl. enumeration-tool + mechanize-the-blindspot-pillar candidate) |
| #25 | pending | Tools-run skill-wiring (Gap-2) + /tools-audit cadence |
| #26 | pending | Tool verification discipline — Check-3 LIVE; 19-tool test migration paced |

## 6. Operator norms
Address Caramel as Caramel/she/her; no AskUserQuestion modals (inline); evaluate on robustness+latency+design not time; **consult before coding** (Ship A is the capital-adjacent core — talk through the integration approach before the production header edits); MED/LOW findings get a disposition; mechanical checks > agent-judgment (the enumeration tool caught what 9 agents missed); paste tool output, don't summarize. No live models — epoch/stamp breaks free provided post-change determinism (D-131).

## 7. First action
`/accept-handoff <this doc>` → then start the Ship-A integration at step 1 (define `FixedPoint<2,64>` in the header, using the proven slice as the body template). Consult Caramel on the integration approach (alias-vs-rename for the ~3000 sites) before the production header edits.

**End of Session-8 handoff. The pre-coding pipeline + the Ship-A approach are PROVEN (258/258); the integration is the mechanical-but-careful next phase, fully de-risked + fully captured.**
