---
type: plan-check
subtype: readiness
ship_tag: v5.15.5.F.4d.1.E.1.1
workstream: "③ config-compiler REMAINING (steps 4b → ship-close)"
date: 2026-06-22
head_at_audit: 03830e8
plan_audited: plans/v5.15-live-readiness/subplans/2026-06-15-v5.15.5.F.4d.1.E.1.1-core-node-rename.md
design_ssot: plans/v5.15-live-readiness/plan_checks/2026-06-22-E.1.1-config-compiler-IA-cascade-synthesis.md
decision_log: plans/v5.15-live-readiness/decision-logs/v5.15.5.F.4d.1.E-architecture-v2.md
verdict: GREEN
executed_via: /accept-handoff Stage 6 (armed general-purpose Layer-2 executor)
---

# /readiness REPORT — ③ config-compiler REMAINING (4b → close) — v5.15.5.F.4d.1.E.1.1 — 2026-06-22

> Persisted by the main session on the subagent's behalf — the Layer-2 executor's Write tool was denied (subagent permission scope); the audit content is the executor's verbatim return.

## VERDICT: 🟢 GREEN — continue coding 4b

Audited at HEAD `03830e8`, branch `feat/v5.15-live-readiness`, tree clean. **Every remaining-step seam resolves at current HEAD. No Must-fix-before-coding blocker.** The decided surface (D-247→D-254) was adversarially probed for a fake blocker and found none — every candidate "gap" resolved to a DECIDED/CLOSED item or already-landed machinery. The remaining work is mechanical execution of a fully-specified shape.

## Steps 1-3 machinery — re-verified present & correct
- `CAPITAL_BOUND_{LOSS,GAIN}` bits @ `CfgFieldRegistry.hpp:154-155` ✅ · fault vocab `CFG_FAULT_CAPITAL_{MALFORMED,OUT_OF_RANGE}` @ `:224-225` ✅ · both-active compile guard @ `:1166`/`:1247` ✅ · size-pin `static_assert(sizeof(ControllerConfig<64>)==53056)` @ `ControllerConfig.hpp:1331` ✅ · `cfg_compile_ok()` @ `:1342` ✅ · main.cpp boot-refuse @ `main.cpp:203` ✅ · fingerprint caller @ `BacktestPanels.hpp:3157` ✅.
- **The step-3 flat-path block at `CfgFieldDispatch.hpp:100-112` is the exact pattern 4b must mirror** (CAPITAL_BOUND-gated → `MALFORMED|OVERFLOW` → `CFG_FAULT_CAPITAL_MALFORMED`; EXCESS_DP→WARN; wire_context corrupt-only).

## Remaining-step seams — all GREEN
- **4b** override macro `_PARSE_OV_PCT`/`_RAW` @ `ControllerConfig.hpp:2971-2972` (inside `ControllerConfig_Load<F>`, fault field in scope) + idiom-2 legacy branches `node_risk_pct[]` write @ `:2882`, `node_max_drawdown_pct[]` write @ `:2893`. Both discard `MoneyParse.flags` today → 4b captures them.
- **4c** sweep insertion after the `_Load`-terminal `PopulateCoresFromFlat(&cfg)` @ **`:3287`**; `BARRIER_SANE_MAX_SL/TP` @ `BarrierValidation.hpp:31-32` (1.0/10.0); Finding-A flat-globals `max_exposure_pct`@528 / `kill_switch_daily_loss_pct`@529 / `kill_switch_drawdown_pct`@532 (validate flat-global directly per coverage-verify).
- **caller-wiring** backtest `BacktestSharded.hpp:119` + `BacktestEngine.hpp:2367` (abort-on-ERROR) + GUI `SettingsPanel.hpp:887` (banner, not abort). main.cpp done.
- **key clean-break** — note: the ② rename **already** converted both parsers + GUI writers to `node_` keys (engine `:2871-2934`, GUI parser `:923`, writers `:1309-1664`). Remaining = (a) the loud HARD-REFUSE fall-through (does NOT exist yet — keys silently swallow), (b) global-key refuse (`engine_mode=`/`num_execution_cores=`, 0 branches), (c) delete C-2 bricks `SettingsPanel.hpp:456`+`:669` + build NET-NEW `check_gui_engine_cfg_key_parity.py`, (d) delete walker-shadowed dead `CFG_PARSE_PCT/MONEY` *capital* branches (H21-clean — internal macros, not wire ids).
- **tests** — confirmed NO `cfg_compile_ok`/`CFG_FAULT_CAPITAL`/`CAPITAL_BOUND` test exists yet (genuinely remaining, expected).

## Stale file:line the next coder WILL trip on (drift confirmed)
| Symbol | STALE (handoff) | CURRENT @ 03830e8 | Δ |
|---|---|---|---|
| idiom-2 `node_N_risk_pct` write | `:2847` | **`:2882`** | +35 |
| idiom-2 `node_N_max_drawdown_pct` write | `:2858` | **`:2893`** | +35 |
| 4c sweep insertion `PopulateCoresFromFlat` | `:3277` | **`:3287`** | +10 |
| `_PARSE_OV_PCT` macro | `:2939-2940` | **`:2971-2972`** | +32 |
| HARD-REFUSE fall-through | `:2968`/`:3099`/`:~2929` | **RE-DERIVE at dive** (recognized branches span `:2871-2959`; override block `:2959-2973`) | — |

The handoff's other cites (`cfg_compile_ok@:1342`, fault vocab `:224-225`, bits `:154-155`, `_PARSE_OV_PCT@:2971`, BARRIER `:31-32`) are all **EXACT**.

⚠️ **N-4: there are TWO `PopulateCoresFromFlat` calls** (`:1987` + `:3287`) — a grep-first-hit lands on the WRONG (partial-resolve) `:1987`; the 4c sweep MUST go after `:3287` (immediately before `return cfg;`).

## Genuinely-NEW findings (adversarial)
- **N-1 (the one real catch): the "15-field / 5 GAIN / 10 LOSS" cohort claim is STALE — the code actually has 17 tagged (11 LOSS + 6 GAIN).** The step-1 commit message says 15 but its diff tagged 17 (correctly including Finding A's 3 kill-switch/exposure fields + ml_tp/sl). This is the OPPOSITE of a coverage gap — the doc undersells. No code action; fix the doc-count at close. Verified no LOSS-side capital field is wrongly UNtagged (the untagged set — `*_mult`, `partial_exit_pct`, `momentum_min_tp_margin_pct`, `min_sl_tp_ratio`, `min_kill_loss`, `starting_balance` — is correctly excluded per the units-trap discipline).
- **N-2** `_PARSE_OV_RAW` uses bare `atof` (dead `.ec` channel colliding with `0`=inherit) — already homed as `parse_double_fast_checked` (verified NET-NEW/absent, not "restored"). Conditional on 4b touching the RAW macro; the capital fields are PCT-channel so it's not mandatory.
- **N-3** `:2619` "unknown-key error at parse" comment is FALSE (gate already flagged) — rewrite when adding the refuse.

## Punch list
- **Must-fix-before-coding: NONE.**
- **Worth-fixing-during:** (1) target `:3287` not `:1987` for 4c; (2) 4b captures `MoneyParse.flags`, CAPITAL_BOUND-gated; (3) land `parse_double_fast_checked` if touching `_PARSE_OV_RAW`; (4) RE-DERIVE the HARD-REFUSE line at dive; (5) confirm the List-B test line `controller_test.cpp:24098` (grep couldn't verify it).
- **Acceptable-risk:** N-1 doc-count fix; N-3 comment; stale TP descriptor `clamp_max=100.0` (inert for validation — sweep uses the barrier constant); C-2 brick deletes (coordinate `:669` with PARITY-006).
- **At close:** wider build (`./build.sh gui` + `suite`) — the remaining steps touch `GUI/SettingsPanel.hpp` which the test-only `build/` doesn't compile (Check 31).

Design is converged, coverage complete, scope clean, mechanism precise. Proceed to code 4b; V-class verifies behavior-neutrality at close.
