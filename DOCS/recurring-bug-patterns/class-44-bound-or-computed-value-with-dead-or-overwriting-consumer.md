---
type: ledger-template
class_id: 44
title: Bound/computed value with a dead or overwriting consumer (silent no-op — the value is produced but its intended effect is nullified)
parent_index: DOCS/RECURRING_BUG_PATTERNS.md
established: 2026-06-12
surface_tags: [decision-time-binding, capital-safety, hot-path, slow-path, dead-code, migration-discipline]
severity: high
recurrence_count: 4
first_instance: 2026-06-12 (v5.15.5.F.4d.1.E.0.10 adversarial exit-chain audit — A9 slippage_pct bound-but-unread + A11/A12 bandit producer-orphan + A10 Momentum stddev-TP computed-but-overwritten; a 4-instance cohort across 2 migration ships)
closure_mechanism: a "write-with-no-LIVE-read" AND "read-with-no-LIVE-write" sweep (a struct field written-but-read-nowhere OR read-but-written-nowhere is a candidate); at ANY field/feature migration, enumerate BOTH ends of every producer→consumer pair + verify each re-wired (sister to Class 33); an unconditional downstream overwrite of a computed value must be GATED or documented-precedence. **Candidate CI (Agent-1 sweep): flag (a) any field written at a `*_BindPreResolved` seam with no live read, (b) any `MBS_*Set*` accessor with zero call sites, (c) any `FOREACH_*_PER_SLOT_FIELD` row whose only non-init reference is a read.**
sister_classes: [29, 26, 27, 40, 18]
sister_memories: [feedback_enumerate_consumers_before_registry_row_deletion, feedback_close_the_class_vs_migrate_every_site, feedback_single_source_the_computation_not_just_the_mode]
---

# Class 44 — Bound/computed value with a dead or overwriting consumer (silent no-op)

A value is **produced** (a field is bound, or a stage computes a result) but its **intended effect never happens** — the consumer that should act on it is dead, missing on the live path, or unconditionally overwritten downstream. It **compiles and runs clean** (no error, no crash), so the loss is silent: the engine behaves as if the value were never produced. On a capital path this silently drops execution-cost modeling, a strategy's computed target, or a per-node parameter.

This is the *opposite end* of Class 29 (which is the value never BOUND → silent zero). Here the value IS produced; the **consumption** is the hole.

## Sub-shape A — Orphaned consumer (bound-but-unread)

A field is bound/written (often migrated to a new home) but **read at zero LIVE sites** — its consumer was never wired, or wired only in a dead/legacy path. The producer dutifully sets it; nothing acts on it.

**Detected (A9, HIGH):** `OrderPreResolved::slippage_pct` is bound at `Order_BindPreResolved` (`CoreFrameworks/Order.hpp:363`) but **read at zero live sites** — paper/backtest slippage is silently absent, P&L systematically optimistic. Root: commit `0119551` migrated `fee_rate` + `slippage_pct` into `OrderPreResolved`, wired the FEE consumer (`OrderManager_HandleFill` reads `pre_resolved.fee_rate`) but **orphaned the slippage consumer** — a half-wired migration. The only "reads" of slippage are the legacy centralized `PortfolioController.hpp` (a different field, `ctrl->config.slippage_pct`) and the mode-0-dead `EventLoop_OnEvent` body.

**Inverse orphan — producer-orphaned (read-live, write-absent):** the SAME shape flips when a ship lands the CONSUMER and orphans the PRODUCER. **Detected (A11/A12, HIGH):** the `.F.4d` bandit reward-attribution consumer `real_on_exit_calibration` shipped and reads the `flags_packed` bandit bits + `bandit_reward_bps[]`, but the producers were never wired — `MBS_OrderSetBanditContext` is defined yet called nowhere (`Order.hpp:294`), and `bandit_reward_bps[]` has no value-write (only the registry zero-init). Both read a deterministic `0` → the entire reward-attribution feature silently logs zeros (the offline ML dataset is corrupt). The tell is identical to A9 — a producer→consumer pair where one ship landed one side; here the missing side is the WRITE, not the read.

## Sub-shape B — Overwritten output (computed-but-discarded)

A value computed by one stage is **unconditionally overwritten or ignored** by a downstream stage, so the computing stage's effect silently collapses. The computation runs, produces a correct value, and is thrown away.

**Detected (A10, MED):** Momentum computes a stddev-scaled take-profit (`Strategies/Momentum.hpp:280-282` → `sg_take_profit_price`), but `CoreFrameworks/ExecutionCore.hpp:542-545`'s flat-`tp_pct` branch overwrites `live_tp` with `fill×(1+tp_pct)` whenever `tp_pct != 0` (reachable on default cfg), **discarding the stddev target**. The dual-arm TP collapsed to flat-only; the strategy's volatility-scaled arm is dead.

## Recurring symptom

- A struct field with write-site(s) but **zero live read-sites** (Sub-shape A) — esp. after a field migration where some consumers were wired and one was missed.
- A computed value immediately followed by an **unconditional overwrite** of its target field (Sub-shape B) — esp. a per-fill/per-tick default that clobbers a per-strategy/per-regime computed value.
- "It compiles, the tests are green, but the configured behavior doesn't happen" (the field is set, the effect is absent).

## Closure (structural)

1. **Write-with-no-live-read sweep:** a field written but read at zero LIVE sites (excluding dead/legacy/mode-0 paths) is a candidate. CI: a grep sweep of struct-field writes vs reads.
2. **Migration consumer-enumeration (Class 33 sister):** when a field moves to a new home, enumerate ALL of its consumers and verify EACH re-wired — a half-wired migration (fee wired, slippage orphaned) is this class's commonest origin.
3. **Gate or document the overwrite (Sub-shape B):** an unconditional overwrite of a *computed* value is a smell — gate it (precedence flag), or document the precedence AND verify the computing stage knows it's overridden (don't compute-then-silently-discard).
4. **Live-vs-dead consumer discipline (Class 40/26 sister):** a consumer in a dead/legacy/mode-0 path is NOT a live consumer — the live path needs its own.

## False-positive surface

- A field **genuinely write-only by design** — a debug/telemetry counter, a `RESERVED`/tombstoned field, a value emitted only for a wire/snapshot reader (the read is cross-process, not in-tree). Verify there's no in-tree consumer EXPECTED.
- A **documented default-then-override** where the override IS the intent (a base value deliberately replaced by a more-specific one) — Class 44-B is the *silent/unintended* discard, not every overwrite. The tell: the computing stage believes its value is used.
- A value **carried-then-consumed-elsewhere** (decision-time binding, Class 27's correct form) — the read is just at a different site; grep confirms a live read exists.

## Canonical reference

`E.0.10-finding-disposition-register.md` A9/A10; Class 29 (the bind-side sibling — value not bound → zero); Class 26 (global-vs-per-core consumer scope); Class 40 (dead code — the consumer in a dead path); Class 18 (mirror missing data-flow); AR-7 (structural-pattern false-completeness); `DESIGN_SPECS/subsystem-designs/exit-chain-tp-sl-design.md` (the as-built design these two divergences sit in); [[feedback_single_source_the_computation_not_just_the_mode]].
