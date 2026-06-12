---
type: subsystem-design
stage: 3-first-canonical
version: 1.0
established: 2026-06-12
tags: [capital-safety, data-oriented-design, structural-fix, ssot]
surface: [hot-path, oms-drainer, live-trading, paper-test]
sister_specs: []
catalogue: subsystem-designs (the first entry — as-built + intended design references, maintained as the codebase evolves)
---

# Subsystem design — per-fill exit chain (TP / SL / dual-leg / ratchet / slippage / booking)

**What this doc is.** The first entry in the **subsystem-design catalogue**: an *as-built + as-intended* reference for one subsystem, maintained as the design evolves. Unlike a pattern spec (a reusable recipe) or an anti-pattern (a bug class), a subsystem-design doc answers *"how is THIS supposed to work, and where does the code currently diverge from that?"* — so a divergence (A9/A10-class: the design says X, the code silently does Y) is **checkable against a written intent** instead of rediscovered by audit each time. Update it when the design changes; the divergences table is the live gap-list.

**Scope.** The path from an entry fill → resolving the exit triggers (`live_tp`/`live_sl`) → the per-tick SG trigger → the exit fill → P&L booking. Grounded in code 2026-06-12 (`.E.0.10` adversarial exit-chain audit). Hot path = `CoreFrameworks/ExecutionCore.hpp`; strategy targets = `Strategies/StrategyParameters.hpp` + per-strategy files; booking = `CoreFrameworks/OrderManager.hpp` + `Portfolio.hpp`.

## 0. The central design fact — the TP/SL dual-representation

Every exit trigger has **two representations** carried in `GateParameters` (`CoreFrameworks/GateParameters.hpp:91-105`):
- **Absolute** — `sg_take_profit_price` / `sg_stop_loss_price` (a `Money` price level the strategy computed).
- **Fractional** — `tp_pct` / `sl_pct` (a per-fill fraction; the live trigger = `fill × (1 ± pct)`).

**Documented precedence (the contract): a non-zero `pct` WINS; `sg_*` is used only when `pct == 0`.** The fractional form exists because it's computed off the **actual fill price** (slippage-/gap-aware), fixing a structural loss-bias the absolute-at-expected-price form had (phase-14). So for the four pct-driven strategies (SimpleDip / MeanReversion / EmaCross / Momentum), under default cfg (`take_profit_pct=3.00`, `stop_loss_pct=1.50`, both non-zero), **the fractional form drives and `sg_*` is overridden at entry**.

This is correct *and intended* for SimpleDip/MR/EmaCross — their `sg_*` is the same `entry×(1±pct)` formula at a stale price, so the override only swaps the stale entry for the real fill (benign). It is a **silent loss for Momentum** (see Divergence A10): Momentum's `sg_*` encodes a *distinct* stddev geometry, not the same pct — and the override discards it.

> **Design tension to track:** `sg_*` has become a near-vestigial second representation on the live entry path. The single-source resolution (the right end-state) is to make `pct` carry the strategy's geometry (e.g. Momentum: `tp_pct = stddev×mult / entry` at build) so the ONE per-fill path is honest for every strategy, retiring `sg_*` as a live-entry SSoT (`feedback_single_source_the_computation_not_just_the_mode`).

## 1. Entry-time trigger resolution (`ExecutionCore.hpp:541-552`)

On the entry fill, leg A resolves:
```
tp_pct != 0 → live_tp = fill × (1 + tp_pct)     ; else live_tp = sg_take_profit_price
sl_pct != 0 → live_sl = fill × (1 − sl_pct)     ; else live_sl = sg_stop_loss_price
```
Steady state (`:337-338`): `active ? live_tp : sg_take_profit_price` — once live, the resolved `live_tp` wins; `sg_*` is the inactive-core fallback.

## 2. Dual-leg / partial-exit (`ExecutionCore.hpp:566-577`)

Two legs per position when `partial_exit_enabled` / `PAIR_ACTIVE`:
- **Leg A** — `live_tp` / `live_sl` (above).
- **Leg B** — `live_tp_b = fill × (1 + tp_pct_b)` where `tp_pct_b = tp_pct × tp2_mult` (`StrategyParameters.hpp:1781-1784`); **SL is shared** (`live_sl_b = live_sl`, "shared SL").

Intent: **scale-out** — take part of the position at the near TP (leg A), the rest at the far TP (leg B). **Both legs are flat-pct** (leg B is a multiple of leg A's pct), *not* one-flat-one-stddev. This is the pragmatic dual-leg the operator settled on (improved win-rate); it is NOT the same thing as the dual-*arm* (flat-vs-stddev) intent — see §6.

## 3. Trailing-ratchet — the let-run / lock-in channel (`ExecutionCore.hpp:420-427, 446-447`)

```
effective_tp = Money_Max(tp, ratchet_tp)      ; effective_sl = Money_Max(sl, ratchet_sl)
```
`ratchet_tp` / `ratchet_sl` default `FPN_Zero` (no ratchet → `Max(x,0)=x`). When driven, the higher value wins — TP/SL climb with price (lock-in / let-run). **Drivers:** `Regime_AdjustPositionsSharded` (regime trailing) + per-strategy trailing (`Momentum_ExitAdjustSharded` → `Strategy_WriteRatchetSL` writes the stddev trail into `ratchet_sl`, `Momentum.hpp:363-375`). **This is where Momentum's stddev signal actually reaches a live position** — via the ratchet trail, NOT the discarded `sg_*` entry value. So the volatility-aware "let it run" behavior is alive through this channel.

## 4. SG trigger (`ExecutionCore.hpp:429-431`)

Branchless, per tick:
```
tp_hit = Money_Ge(price, effective_tp) ; sl_hit = Money_Le(price, effective_sl)
sg_fires = (tp_enabled & tp_hit) | (sl_enabled & sl_hit)
```
TP fires when price rises to `effective_tp`; SL when price falls to `effective_sl`. Both firing the same tick → a single exit event (no double-exit). Gated on the enable flags (a zeroed/blocked strategy clears `TP_ENABLED`).

## 5. Slippage model — intended (`Portfolio.hpp:201-203`, `ControllerEventLoop.hpp:1873-1890`)

Intended paper-mode execution cost: entry books `+slip`, exit books `−slip` (`exit_price = exit_price − exit_price×slippage_pct`); live books the raw venue fill (real slippage already in it). The sign dispatch (entry `+` / exit `−`) is correct. **See Divergence A9: this is currently DEAD on the production sharded path** — the consumer was orphaned.

## 6. The intended adaptive-TP design (operator's ideal — NOT fully built)

The original goal: at the first calculated TP, read momentum direction `{rising / stable / falling}` and **take at the spike if it's a local peak**, **hold-and-run if still rising**, hold-if-stable (unless projected to fall). Current approximation: flat TP fires (take-at-peak) + the ratchet trail (§3) provides hold-and-run as price climbs. The **dual-leg** (§2) is the pragmatic settle that improved WR. The fuller adaptive version (an explicit peak-vs-continuation decision at TP-hit, volatility-scaled) is a **future strategy-enhancement** — the ingredients (flat TP + ratchet + the stddev geometry) exist; wiring them into one adaptive policy is the open design.

## 7. Exit-fill booking (`OrderManager_HandleFill` → `Portfolio_CloseSlot` → `EventLoop_DrainPostFill`)

Gross via the single `Money_FillGross` SSoT (`Portfolio.hpp:397`; Class 43); fees entry+exit into maker/taker buckets; `net = gross − fees`; `balance` / `realized_pnl` / `last_was_win` / `last_realized_return` / `ks_peak_balance` updated. Characterized by `oms-ts-1` / `oms-ts-1b` (`tests/controller_test.cpp`). The exit books at the **actual crossing tick price** (`ExecutionCore.hpp:508`), NOT `live_tp` (the trigger) — gross and realized cash use the same `fill_price` (no trigger-vs-book divergence).

## Known divergences (the live gap-list — design says X, code does Y)

| id | design intent | current code | sev | disposition |
|---|---|---|---|---|
| **A9** | paper/backtest books exit at `fill ± slip` (execution-cost modeled) | slippage is DEAD — `pre_resolved.slippage_pct` bound (`Order.hpp:363`) but read at ZERO live sites; books the raw price | HIGH | fix (regression, `0119551` orphaned the consumer); register A9 |
| **A10 / S1** | Momentum's stddev-scaled TP geometry drives the exit | the flat `tp_pct` override discards the stddev **entry-TP** (stddev *trail* survives via the ratchet §3) | MED | design: convert stddev→pct at build (single per-fill path); register A10 |
| **S2** | the MOM TP-margin quality filter gates on the real exit geometry | it inspects the flat `tp_pct`, not the stddev TP (inert by default, `margin=0`) | LOW | closed by the S1 fix; register A10/S2 |

Update this table as divergences are opened/closed. A characterization test that freezes CURRENT behavior (e.g. F-059) freezes the **code** column and flags the gap; a fix moves the code column to match the intent column + regenerates the golden.

## Cross-references

Class 44 (bound/computed-but-not-consumed — A9/A10's bug class) + Class 43 (money-computation SSoT) in `DOCS/recurring-bug-patterns/`; `characterization-test-discipline.md` (how F-059 freezes this); `single-source-of-truth-discipline.md` (the `sg_*`-vs-`pct` dual-representation retirement); `plan_checks/E.0.10-finding-disposition-register.md` A9/A10/S1/S2; `tests/controller_test.cpp` oms-ts-1/1b. Key code: `ExecutionCore.hpp:337-577`, `GateParameters.hpp:91-105`, `StrategyParameters.hpp:494-598,1666-1914`, `Momentum.hpp:280-287,363-375`.
