---
type: readiness-report
plan_audited: subplans/2026-05-29-v5.15.5.F.4d.1.E.0.1-pre-E1-foundational-fix-net.md
audited_date: 2026-05-30
engine_head: 0b841b3 (v5.15.5.F.4d.1.E.0.5)
branch: feat/v5.15-live-readiness
audit_tier: HIGH-RISK
verdict: GREEN
fired_by: /accept-handoff Stage 6 (post-.E.0.5 close handoff pickup)
---

# /readiness report — `.E.0.1` pre-`.E.1` foundational-fix net (Net-2) — 2026-05-30

**Verdict: 🟢 GREEN — ready to start coding.** All core + cold-pickup + drift + hardening
checks pass; dependencies verified extant; prerequisites GREEN; amendment v0.2 incorporates
the hardened-gate audit synthesis (D-86). No must-fix items.

Audited at engine HEAD `0b841b3` — **byte-untouched since the plan was authored 2026-05-29**
(only Version.hpp + CHANGELOG changed across all `.E.0.x` ships, all META), so every cited
file:line anchor still holds.

## Plan summary
- **Ship:** `.E.0.1` — Net-2 of the two-phase pre-`.E.1` determinism/characterization net (D-73).
- **Scope:** 5 net-gating engine-correctness fixes across 2 clusters + 1 completeness-critic change:
  - **FP-determinism:** F-056 (delete native sqrt spec → deterministic NR), F-057 (tests build `USE_NATIVE_128` → tested==shipped), F-058 (`memcpy` not pointer-pun → strict-aliasing UB removal).
  - **Replay-determinism:** F-054/F-055 (`strtod` → `tt::parse_double_fast_advance` in BacktestEngine + DepthReplayState).
  - **Completeness-critic (v0.2):** recorder emit `%.8f` → `std::to_chars` (TickRecorder + DepthRecorder) — closes the write side of the replay loop. → PARITY-036.
- **Surface:** 6 files (FixedPointN.hpp, FixedPoint64.hpp, BacktestEngine.hpp, DepthReplayState.hpp, CMakeLists.txt, build.sh) + 2 recorder files. No hot path; no cfg fields; no new structs/persistence; no new threads.
- **Gates:** `.E.1` (Core→Node rename) is BLOCKED until this net is GREEN.

## Checklist verdicts (summary)

| Dimension | Result |
|---|---|
| Core 10-item checklist | 10/10 PASS |
| Cold-pickup C.1–C.10 | 10/10 PASS (C.9 minor hygiene only — D.1 plan path not named at line 7) |
| Drift audit (8 categories) | 8/8 PASS; **Category 8 build-flag drift = DRIFT-SAFE + intentional** |
| Hardening checks | All PASS / N-A (no atomicity / GUI-blocking / cleanup hazards) |
| Dependency verification | All extant; no hidden scope |
| Check 31 (wider build) | PASS — predecessor code-bearing close (`.B.8`) built all 5 binaries clean |
| Check 34 (audit_tier) | PASS — `HIGH-RISK` declared; scope matches |
| Check 45 (tests-changed) | PASS — section present; N/A engine `tests/` source (CI gates live in tools/+tests/) |

## Hot-path purity (the load-bearing claim)
**CONFIRMED UNTOUCHED.** Zero `FPN_Sqrt` / `_to_fp64` / `_from_fp64` callers on
ExecutionCore_Tick / BG_Evaluate / SG_Evaluate. `FPN_Sqrt` callers are all slow-path/feature-only
(FlowFeatures stddev, FeatureRegistry denom, RidgeBlender/ModelInference). FP determinism is
load-bearing for ML train-serve parity (M5), not hot-path latency.

## Drift Category 8 (build-flag) — the ship's axis
DRIFT-SAFE + intentional: F-057 makes `controller_test`/`parity_harness` build `USE_NATIVE_128`
so the suite exercises the **shipped** native path (production already builds it). The determinism
CI gate is `tested==shipped` + sqrt-scoped ±native diagnostic (RED→GREEN after F-056) +
cross-run/cross-binary byte-identity — **NOT** blanket all-ops native==generic. R1 (FromDouble/ToDouble
differ) is empirically refuted at F=64 except sqrt and is moot post-F-057. Read side (F-054/55) +
write side (recorder-emit `to_chars`) close the replay loop symmetrically; goldens regenerate fresh
(no byte-compat constraint).

## Dependency verification (all ✅ at HEAD 0b841b3)
- F-056: `FixedPointN.hpp:1254` sqrt native spec · `FP64_Sqrt` `FixedPoint64.hpp:313`
- F-058: `FixedPointN.hpp:1221-1226` `_to_fp64`/`_from_fp64` pointer-pun
- F-054/55: `strtod` `BacktestEngine.hpp:88-96` + `DepthReplayState.hpp:224-227` · `tt::parse_double_fast_advance` `ParseFast.hpp:78`
- F-057: `USE_NATIVE_128` `CMakeLists.txt:21` · `controller_test`/`parity_harness` targets (no native def yet)
- Recorder emit: `TickRecorder.hpp:186` + `DepthRecorder.hpp:249` `fprintf("%.8f")`

**Symbol-existence tool (Check 32):** 2 flagged "fabrications" (lines ~146/~150) are FALSE POSITIVES —
the F-058 before/after `_to_fp64` snippets fail *standalone* compile (`'FP64' was not declared`) because
`FP64` is defined in `FixedPoint64.hpp`. All referenced symbols are real. Classified ACCEPTED, not GAP.

## Recommendations
**Must fix before coding:** NONE.
**Worth fixing during coding:**
1. (C.9 hygiene) name the D.1 plan body path explicitly at plan line 7.
2. Add a discrete recorder-emit round-trip unit test (`to_chars` shortest-form ≡ parse-back identity) for Phase C.
**Acceptable risk (don't block):** R1 pre-disposition (harness confirms at Phase B); F-076 conditional fold (Phase A observation → `.E.0.3` route per amendment).

## Next action (per handoff §6 — NOT run by /readiness)
Fire the coding-time **`/precoding-audit-gate` (HIGH-RISK, HEAVIER-default per D-77 — money-bearing)** +
**`/blindspot-scan`** (touches FP struct-layout + a build-flag change), consult, THEN code Phase A.
This is also the live calibration bench for the hardened gate shipped at `.E.0.5` (Piece 4).
