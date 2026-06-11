---
type: readiness-report
plan: subplans/2026-06-10-v5.15.5.F.4d.1.E.0.10-net1-correctness-net.md
date: 2026-06-10
produced_by: /accept-handoff Stage 6 (composed /readiness pass)
verdict: GREEN (for continuing the in-flight Net-1 ship; NOT for .E.1 which is separately RED)
note: persisted by the orchestrator — the readiness subagent's own Write was sandbox-denied. The hpg-bc-1 / LegacyReferenceDriver drift finding was independently re-verified by the orchestrator (file exists at CoreFrameworks/LegacyReferenceDriver.hpp, 10840 B, not in CMakeLists.txt/build.sh; StrategyParameters.hpp:671 comment = "experiment tests").
---

# /readiness report — `.E.0.10` Net-1 pre-`.E.1` correctness net — 2026-06-10

**Plan:** `plans/v5.15-live-readiness/subplans/2026-06-10-v5.15.5.F.4d.1.E.0.10-net1-correctness-net.md`
**Register (SSoT for remaining work):** `plans/v5.15-live-readiness/plan_checks/E.0.10-finding-disposition-register.md`
**Context:** Mid-execution checkpoint pickup (composed step of `/accept-handoff`). Engine HEAD `5e65933`, branch `feat/v5.15-live-readiness`, tree clean. `audit_tier: HIGH-RISK` but the risk axis is **COMPLETENESS** (gates the riskiest ship `.E.1`), NOT code-risk — TEST/TOOLING-ONLY ship (no engine code; cannot break the hot path).

**Scope note.** This verdict is for **continuing the in-flight Net-1 ship**, NOT for `.E.1` (separately known-RED, blocked behind the torn-read class + conc-5). Mechanical floor (`check_session_docs.sh` exit 0) pre-verified this session — Checks 32/45/forward-promise/memories not re-derived.

---

## N/A check set (one line)

Checks 11-31, 33-34, 36-44, 46 are **N/A**: no new cfg field, no hot-path/branchless code, no wire-format/HMAC/stamp change, no ML feature, no SIMD, no snapshot-version bump, no registry-row deletion, no persisted-identifier change. Effort spent on cold-pickup (C.1-C.10), remaining-work surface verification, net-completeness, and acceptance reconciliation.

---

## Per-dimension verdict table

| Dimension | Verdict | Notes |
|---|---|---|
| Cold-pickup completeness (C.1–C.10) | **PASS** | Register is an unusually complete pickup surface (per-item file:line, session-state block, 7-move close-out plan). One DRIFT (C.6) on hpg-bc-1 wording. |
| Remaining-surface: oms-ts-1 (fee-blind balance) | **PASS** | Real + locatable. Corpus finding cites `tests/controller_test.cpp:8176` — `balance_after_close > 9990.0 && < 10020.0` ($30-wide, fee-blind via `core_cfg=nullptr`→`fee_rate=0`). Work = add exact-value harness. |
| Remaining-surface: hpg-bc-1 / LegacyReferenceDriver | **DRIFT** | Plan says driver "GONE (only a comment)" — **WRONG**: live header `CoreFrameworks/LegacyReferenceDriver.hpp` (10.8KB, struct+fn defs). BUT disposition SOUND: experiment-only (included solely by `experiments/per_core_sharding/test_migration_head_to_head.cpp`, not in CMakeLists/build.sh, uses old `FPN_Binary<F>` not decimal `Money`). F-059 golden-master IS genuine net-new work. Doc-drift, not net-invalidating. |
| Remaining-surface: wfa-1 (warm-restart armed) | **PASS** | Confirmed at `ShardedSnapshotPersist.hpp:54` ("stay armed-but-inactive") + `:681` ("hot-path SG/TP/SL gates armed"). Register's "LIKELY-CLOSED" correct; remaining work is the confirmation (cheap). |
| Remaining-surface: conc-5 (submit_queue race) | **PASS** | Confirmed NO MPSC/MPMC/SPMC primitive: `SPSCRing.hpp:12` "no MPMC support, no MPSC, no SPMC"; `OrderManager.hpp:43/254` + `BinanceAdapter.hpp:49` discuss why MPSC isn't used. submit_queue is plain SPSC → conc-5 is a REAL runtime-confirm (tsan), not closeable by inspection. |
| Net completeness (false-floor risk) | **YELLOW** | 8 named targets cover the HIGH money findings. A 2nd tier of MED OMS/fee findings (partial-exit money path · maker-fee booking · FlattenAll balance) is NOT in the headline list — BUT **explicitly queued** under register line 39 ("E.1 bucket… MED/LOW + 3 detail-reads pending") + line 135 ("Phase-1 backlog re-triage"). Tracked-as-pending, not dropped. F-019 (formula divergence) is CLOSED-by-D-190. |
| Acceptance-criteria reconciliation | **PARTIAL** | 2 DONE (+1 DONE-exceeds), 2 PARTIAL, 3 OPEN. No orphan criteria. |
| Decision-log currency (D-190) | **DRIFT (LOW)** | D-190 STATUS still `<!-- STATUS: identified + fix designed (surgical); implement next at .E.0.10 -->` (log ~line 1204) but the fix LANDED this session (engine `c1a10d2`). Log lags reality. |
| GATE: TECH_DEBT-163 byte budget | **ACCEPTED (blocks owed-codifications only)** | Always-loaded budget at cap. Any owed-codification adding a memory/rule (torn-read class, `/adversarial-audit` skill) MUST do the durable restructure FIRST. Does NOT block the characterization-test work. |
| Hot-path purity (Check 1) | **PASS** | No engine code. |
| Test-change enumeration (Check 45) | **PASS** | Plan has a "Tests changed" section (NEW + AR-4 negative self-test; none broken-replaced). |

---

## Remaining-work surface verification (the high-value part)

1. **`oms-ts-1` — CONFIRMED real, locatable.** Corpus finding (`.../pre-implementation-findings/PRE-PAPER-TEST-findings.md:172-180`) points at an EXISTING test (`tests/controller_test.cpp` round-trip ~8103-8177; sole balance assertion `:8176`): `balance_after_close > 9990.0 && < 10020.0`. Fee-blind because `buy_cmd`/`sell_cmd` pass `core_cfg=nullptr` → `fee_rate=0` (entry_fee=exit_fee=$0), so the $30 window passes even if fees dropped/mis-signed. Work = exact-value harness with NON-ZERO fees asserting `oms->balance`/`realized_pnl`/`total_fees`. Plan's "±$15 fee-blind" shorthand = the $30-window/$15-half-width. **Not a stub-to-fix — a too-loose existing test to tighten.**

2. **`hpg-bc-1` / F-059 — DRIFT in plan wording; disposition SOUND.** Plan + register say `LegacyReferenceDriver` is "GONE (only a comment, `StrategyParameters.hpp:671`)". **A live header exists** at `CoreFrameworks/LegacyReferenceDriver.hpp` (10,840 bytes): `LegacyRefSlot<F>` (:69), `LegacyReferenceState<F>` (:83), `LegacyReference_Init/Tick/SlowPath` (:95/:138/:183). Included ONLY by `experiments/per_core_sharding/test_migration_head_to_head.cpp:25`; NOT in main `CMakeLists.txt`/`build.sh`; uses old `FPN_Binary<F>` for money (not decimal `Money`). The `:671` comment DOES exist. The finding's substance — the oracle validates the `SG_Evaluate` stub so byte-identity for the real per-fill TP/SL exit path is false by construction → **F-059 golden-master is genuine net-new work** — is unchanged. The "GONE (only a comment)" phrasing is imprecise and would confuse a fresh session that greps and finds the file. **[Orchestrator re-verified: file present 10840 B, not in build, StrategyParameters.hpp:671 = "experiment tests".]**

3. **`wfa-1` — CONFIRMED.** `ShardedSnapshotPersist.hpp:54` ("…stay armed-but-inactive until live fills repopulate") + `:681` (live `fprintf` "re-activated %d ExecutionCore(s) from restored positions — hot-path SG/TP/SL gates armed"). Register "LIKELY-CLOSED" accurate; remaining work = the confirmation + optional characterization test.

4. **`conc-5` — CONFIRMED real runtime-confirm, NOT closeable by inspection.** `SPSCRing.hpp:12` "no MPMC support, no MPSC, no SPMC" — only ring primitive; `OrderManager.hpp:43` ("…The current SPSCRing breaks under…") + `:254` ("the SPSC contract — no MPSC needed") + `BinanceAdapter.hpp:49` corroborate. submit_queue pushed by ≥2 producer threads against plain SPSC = genuine lost/dup-order race; `.E.1` "CHANGES-BY-DESIGN closes it" is "LIKELY/verify"; the register correctly demands tsan on a disposable clone.

---

## Net-completeness (false-floor) assessment

The plan's OWN stated HIGH risk: "characterize every surface the `.E.1` rename TOUCHES and should keep INVARIANT" — a miss = false floor = worthless net.

- **F-019 / oms-money-6 (two non-byte-identical gross formulas, diff-then-mul vs mul-then-sub) = the D-190 bug, CLOSED-by-D-190 this session.** `Money_FillGross` (1-mul SSoT, `Portfolio.hpp:397`) routes all 5 gross sites; adversarially verified + regression-tested + pre-commit guard (`tools/check_money_gross_single_source.py`, Check L). NOT a gap.
- **Second-tier MED OMS/fee findings** (partial-exit money path untested · maker-side fee booking/coverage · FlattenAll balance untested — agents cite these as `oms-ts-5`/`oms-ts-3`/`oms-ts-4`/`oms-bc-3` and/or the E.1-findings MED set) are money/accounting surfaces the rename touches. **NOT** in the plan's 8-name headline list, BUT **explicitly queued** under register:39 ("E.1 bucket (30, incl. conc-5 CRIT) — IN-PROGRESS — HIGH targets verified; MED/LOW + 3 detail-reads pending") + register:135 ("STILL OPEN in Net-1: … the Phase-1 backlog re-triage"). All tagged MEDIUM.

**Verdict: NOT a blocking false-floor.** The second-tier money findings live inside the Phase-1 re-triage, itself a tracked remaining-work item — the net is not silently short a HIGH surface. **It IS a YELLOW**: a session executing only the plan's named target list (without drilling into the register's "MED pending" row) could under-scope Phase 2's money characterization. Worth surfacing the MED-tier OMS findings into the plan's Phase-2 surface list explicitly (characterize-or-consciously-defer the partial-exit / maker-fee / FlattenAll-balance surfaces before `.E.1`).

---

## Acceptance-criteria reconciliation (plan lines ~56-63)

| # | Acceptance item | State | Evidence |
|---|---|---|---|
| 1 | PERSIST characterization GREEN (fee/accounting · regime · parser byte-equiv · snapshot round-trip) | **PARTIAL** | regime (rsf-ts-1, `:19678+`) + snapshot round-trip (D-110, `:5749+`) DONE; fee/accounting (oms-ts-1) OPEN; parser byte-equiv (hpg-bc-1/F-059) OPEN. |
| 2 | H1–H20 CI invariant checks live for `.E.1`-touched surfaces | **OPEN** | Phase-2 not built. Adjacent money guard landed (Check L) but the H1-H20 grep/static_assert suite for the rename surface is pending. |
| 3 | D-110 probe GREEN — every money field round-trips EXACTLY (decimal) | **DONE** | `:5749+` — 9 per-core + 7 `Position<F>` money fields assert `Money_Eq` save→recover; 3343/0; probe CLEAR. |
| 4 | Live finding-register: every 141+93+5 item carries status + `.E.1`-home | **PARTIAL** | Register live + structured; fpmem + E.1-HIGH verified; **MED/LOW + 93 TECH_DEBT + 5 PARITY still PENDING-RETRIAGE** (register:39-42). |
| 5 | `conc-5` "`.E.1` closes it" VERIFIED (not inherited) | **OPEN** | "PENDING — LIKELY/verify"; tsan on disposable clone owed (register:138). |
| 6 | Disposition-tracker CI guard live (M7 close of WH-7) | **OPEN** | Not built. Gated by TECH_DEBT-163 only if it adds always-loaded content (the guard is a tool → likely fine; sister memory/rule needs restructure first). |
| 7 | Standing CI gates GREEN; suite 3285/0 | **DONE (exceeds)** | Suite 3343/0; both gates green. (Acceptance says 3285; current higher — additive.) |

**2 DONE (+1 exceeds), 2 PARTIAL, 3 OPEN.** OPEN items = exactly the register's named remaining-work; no orphan criteria.

---

## Cold-pickup completeness (C.1–C.10)

C.1 branch PASS · C.2 phase-order PASS · C.3 first-move PASS · C.4 symbol-names PASS · C.5 file:line PASS · **C.6 stale-claim DRIFT** (hpg-bc-1 "GONE" — live header exists; correct to "experiment-only, F-059 net-new") · C.7 effort PASS · C.8 source-audit PASS · C.9 predecessor/dependent PASS · C.10 tags PASS (`.E.0.10` semantic=tag re-align operator-confirm pending, flagged in Phase 0). **8.5/10 effective — GREEN on cold-pickup** (C.6 is a wording fix, not session-blocking).

---

## Punch-list

### Must-fix before continuing
- *(none)* — no blocker. All four remaining surfaces verified-real + locatable; net is not a blocking false floor.

### Worth-fixing (during this ship)
1. **Correct the hpg-bc-1 wording** in plan (~line 42/63) + register (line 63): `LegacyReferenceDriver` is NOT gone — live experiment-only header (`CoreFrameworks/LegacyReferenceDriver.hpp`, included only by `experiments/.../test_migration_head_to_head.cpp`, old `FPN_Binary`, not in build). F-059 conclusion unchanged. (Kills the C.6 DRIFT / fresh-session confusion.)
2. **Surface the MED-tier OMS/fee findings into the plan's Phase-2 target list** (partial-exit money path · maker-fee booking · FlattenAll balance) — queued under the register's "MED pending" but invisible in the plan's 8-name list. Make them explicit-IN or consciously-deferred-with-reason. (The net-completeness YELLOW.)
3. **Update the D-190 decision-log STATUS sentinel** to landed/implemented (engine `c1a10d2`); currently future-tense "implement next at .E.0.10" (log ~line 1204). LOW doc-drift.
4. **Honor TECH_DEBT-163 ordering** — RECURRING_BUG_PATTERNS torn-read class + `/adversarial-audit` skill + any sister memory must do the durable always-loaded byte-budget restructure FIRST or the byte-cap guard goes red.

### Acceptable-risk (don't block)
- conc-5 as a runtime-confirm (tsan on disposable clone) is correct + expected — it is the `.E.1` LIVE-ENABLE HARD GATE, intentionally not closed in Net-1.
- 93 TECH_DEBT + 5 PARITY re-triage PENDING — explicitly a Phase-1 remaining item; disposition-only, not a Net-1 test deliverable.
- Batch adversarial-verify of the new tests at ship close (register:135) is owed but a close-step, not a continue-blocker.

---

## Verdict: **GREEN** — continue the in-flight Net-1 ship

The four remaining characterization surfaces (oms-ts-1, hpg-bc-1/F-059, wfa-1, conc-5) are all verified-real and locatable against current code. Acceptance criteria reconcile cleanly with the register's named remaining-work (no orphans). The net is NOT a false floor: F-019 (the formula divergence) is already closed by D-190, and the second-tier MED money findings are explicitly queued under the still-open Phase-1 re-triage. The four worth-fixing items are doc-corrections + an ordering constraint — none block continuing.

GREEN is for *continuing Net-1 work*. It is NOT a statement on `.E.1`, which remains separately RED (blocked behind the torn-read class + conc-5 + the live-enable hard gate) by design.
