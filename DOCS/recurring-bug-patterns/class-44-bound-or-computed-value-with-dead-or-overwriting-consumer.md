---
type: ledger-template
class_id: 44
title: Bound/computed value with a dead or overwriting consumer (silent no-op — the value is produced but its intended effect is nullified)
parent_index: DOCS/RECURRING_BUG_PATTERNS.md
established: 2026-06-12
surface_tags: [decision-time-binding, capital-safety, hot-path, slow-path, dead-code, migration-discipline]
severity: high
recurrence_count: 8
first_instance: 2026-06-12 (v5.15.5.F.4d.1.E.0.10 adversarial exit-chain audit — A9 slippage_pct bound-but-unread + A11/A12 bandit producer-orphan + A10 Momentum stddev-TP computed-but-overwritten; a 4-instance cohort across 2 migration ships)
later_instances: 2026-06-13 (.E.0.10 Round-2 cfg-surface sweep, D-211) — A24 (Sub-B cfg-mutation: D6/D10/spike adaptation computed into the flat resolved_cfg field no consumer reads) + the NEW cfg-flag-orphan sub-variant A35/A36/A37 (operator-settable flag, no live sharded reader; A13/A14 cross-listed). Round-2 swept the class → BOUNDED (producer + in-flight lanes clean; cfg-flag surface the hot spot).
closure_mechanism: a "write-with-no-LIVE-read" AND "read-with-no-LIVE-write" sweep (a struct field written-but-read-nowhere OR read-but-written-nowhere is a candidate); at ANY field/feature migration, enumerate BOTH ends of every producer→consumer pair + verify each re-wired (sister to Class 33); an unconditional downstream overwrite of a computed value must be GATED or documented-precedence. **Candidate CI (Agent-1 sweep): flag (a) any field written at a `*_BindPreResolved` seam with no live read, (b) any `MBS_*Set*` accessor with zero call sites, (c) any `FOREACH_*_PER_SLOT_FIELD` row whose only non-init reference is a read; (d) any operator-settable `MASK_*_CFG_*` flag read ONLY on the dead centralized `PortfolioController.hpp` / display-only path (no live sharded `Strategy_BuildParameters`/`BG_Evaluate`/slow-path reader) — the A35/A36/A37 cfg-flag-orphan sub-variant.** The Round-2 sweep (2026-06-13) confirmed NO existing tool catches any of (a)-(d) — building this detector is the structural close (the H22 `check_per_core_registry_integrity.py` Check-10 extension is its cfg-flag slice; the codebase-wide field-level version is the endgame, point 5 below). ✅ **(d) BUILT 2026-06-14 — `tools/scan_class_44_cfg_orphan.py`** (the standalone full-scan sibling of Check 11's cfg-MUTATION, mirroring Class 27's Check 7 + `scan_class_27_full.py`): enumerates the flag universe from the `FOREACH_*_CFG_FLAG` registries (SSoT, so no `MASK_*_CFG_##name` macro-paste artifact) + flags any with no live reader; **oracle PASS** (the A13/A14/A35/A36/A37 cohort caught) + the class is **BOUNDED** (0 unknown orphans across 30 flags incl. ML). Wired into `/bug-check` Step 3 + `DOCS/TOOLS.md`. (a)/(b)/(c) + the full produce/consume tracker (point 5) remain TECH_DEBT-175.
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

**cfg-flag sub-variant — operator-settable flag with no live sharded reader (the `.E.0.10` Round-2 cfg-surface cohort, 2026-06-13):** the same orphan on the cfg-FLAG surface — an operator-settable `MASK_*_CFG_*` flag (often GUI-rendered + badged) read ONLY on the dead centralized `PortfolioController.hpp` / display-only path, with NO live sharded consumer. The operator flips it; nothing changes (and the GUI often advertises it as active — a Class-2 overlap). **Detected (Round-2 sweep):** **A35** `GATE_EMA_ENABLED` (settable + GUI-rendered; sharded EmaCross uses the EMA unconditionally via `state->prev_ema`, never the flag); **A36** `BREAKEVEN_ON_PARTIAL` (**DEFAULT-ON** risk ratchet "move SL to breakeven after TP1", read only at dead `PortfolioController.hpp:682`, no sharded reader); **A37** `SESSION_FILTER_ENABLED` (gates NOTHING — the session vol-mult runs unconditionally). Cross-listed siblings: **A13** (`NO_TRADE_BAND`), **A14** (`VOL_SIZING`, a legacy-synonym of the live `FOXML_VOL_SCALING`). Origin: the per-core cfg-registry migration shipped the flag + its GUI surface but left the consumer on the dead centralized path.

## Sub-shape B — Overwritten output (computed-but-discarded)

A value computed by one stage is **unconditionally overwritten or ignored** by a downstream stage, so the computing stage's effect silently collapses. The computation runs, produces a correct value, and is thrown away.

**Detected (A10, MED):** Momentum computes a stddev-scaled take-profit (`Strategies/Momentum.hpp:280-282` → `sg_take_profit_price`), but `CoreFrameworks/ExecutionCore.hpp:542-545`'s flat-`tp_pct` branch overwrites `live_tp` with `fill×(1+tp_pct)` whenever `tp_pct != 0` (reachable on default cfg), **discarding the stddev target**. The dual-arm TP collapsed to flat-only; the strategy's volatility-scaled arm is dead.

**Detected (A24, HIGH — the cfg-mutation variant):** `EventLoop_RebuildOneCore` computes the D6 session / D10 losing-streak-brake / spike-relaxation adaptations into the FLAT `resolved_cfg.{volume_multiplier,entry_offset_pct,spacing_multiplier}` (`ControllerEventLoop.hpp:2337/2403/2410` + a local `spacing_cfg` copy), but the live consumer reads `resolved_cfg.cores[slot]` (the per-node slice) — the computed adaptation is discarded into a field no live consumer reads (`ControllerConfig_ResolveForCore` writes the flat fields, NEVER `cores[slot]`). Regression from the per-core migration `49649b8`. The default-ON D10 safety brake is silently inert for SimpleDip/EmaCross/ML. Fix (D-211 option (c)): single-source the per-node slice + tombstone the flat field; the un-reintroducible close is the `check_per_core_registry_integrity.py` Check-10 extension (a per-shard write to a flat-with-slice field). NB: reaches SimpleDip/EmaCross/ML only — MR/Momentum read a THIRD storage `state->live_*` (TECH_DEBT-189), itself a two-competing-adaptation-architectures smell.

## Recurring symptom

- A struct field with write-site(s) but **zero live read-sites** (Sub-shape A) — esp. after a field migration where some consumers were wired and one was missed.
- A computed value immediately followed by an **unconditional overwrite** of its target field (Sub-shape B) — esp. a per-fill/per-tick default that clobbers a per-strategy/per-regime computed value.
- "It compiles, the tests are green, but the configured behavior doesn't happen" (the field is set, the effect is absent).

## Closure (structural)

1. **Write-with-no-live-read sweep:** a field written but read at zero LIVE sites (excluding dead/legacy/mode-0 paths) is a candidate. CI: a grep sweep of struct-field writes vs reads.
2. **Migration consumer-enumeration (Class 33 sister):** when a field moves to a new home, enumerate ALL of its consumers and verify EACH re-wired — a half-wired migration (fee wired, slippage orphaned) is this class's commonest origin.
3. **Gate or document the overwrite (Sub-shape B):** an unconditional overwrite of a *computed* value is a smell — gate it (precedence flag), or document the precedence AND verify the computing stage knows it's overridden (don't compute-then-silently-discard).
4. **Live-vs-dead consumer discipline (Class 40/26 sister):** a consumer in a dead/legacy/mode-0 path is NOT a live consumer — the live path needs its own.
5. **The full structural close — a struct-field produce/consume tracker.** This class is fundamentally a *data-flow* gap (a field's producer or consumer is missing/wrong). The complete M7 close is a tool that maps, per struct field, every PRODUCE (write/bind) and CONSUME (live read) site across the codebase — sister to `/dependency-chain-trace` but at FIELD granularity. It catches both orphan directions AND the overwrite shape structurally, AND doubles as the field-access-pattern map a DOD re-pack (TECH_DEBT-159) needs + a feeder for the `subsystem-designs/` catalogue. The CI-check candidate in `closure_mechanism` is the SEED; the full tracker is the endgame (operator-raised 2026-06-12; scope as a future discipline).

## Round-2 sweep — the class is BOUNDED (2026-06-13, D-211 sequence)

An operator-directed 3-lane adversarial sweep (cfg/flag · producer-orphan · in-flight-bind, each blind, M8-armed) swept the whole class. **Result: the producer-orphan + in-flight-bind lanes are CLEAN beyond the known cohort** — A9 fix confirmed-complete, A25 confirmed-consumed, A10/A11/A12 confirmed; all `pre_resolved.*`/`Order`/`SubmitCommand`/`GateParameters`/`original_*` proven-consumed; ZERO new producer-orphans (all 47 calib columns traced). **The orphan residue concentrates on the cfg-FLAG + cfg-mutation surfaces** (the new cfg-flag sub-variant A35/A36/A37 + A24), NOT the in-flight/producer surfaces — so the class is bounded, not an open-ended tail. The dead-code siblings (`ForceCloseOnShutdown` stale-API + 4 dead setters) are Class 40, not Class 44 (both ends dead → no live garbage-read) — homed TECH_DEBT-192.

## False-positive surface

- A field **genuinely write-only by design** — a debug/telemetry counter, a `RESERVED`/tombstoned field, a value emitted only for a wire/snapshot reader (the read is cross-process, not in-tree). Verify there's no in-tree consumer EXPECTED.
- A **documented default-then-override** where the override IS the intent (a base value deliberately replaced by a more-specific one) — Class 44-B is the *silent/unintended* discard, not every overwrite. The tell: the computing stage believes its value is used.
- A value **carried-then-consumed-elsewhere** (decision-time binding, Class 27's correct form) — the read is just at a different site; grep confirms a live read exists.

## Canonical reference

`E.0.10-finding-disposition-register.md` A9/A10 + the Round-2 subsection (A24/A35/A36/A37); **D-211** (the cfg-surface sweep + the A24 option-(c) decision); Class 29 (the bind-side sibling — value not bound → zero); Class 26 (global-vs-per-core consumer scope); Class 27 (single-value-cache flattens per-instance — sister to the A33 multi-storage smell); Class 40 (dead code — the consumer in a dead path; the `ForceCloseOnShutdown`/dead-setter siblings, TECH_DEBT-192); Class 18 (mirror missing data-flow); **Class 2** (display↔execution — the GUI-lie overlap on A35/A37/A32); AR-7 (structural-pattern false-completeness); `DESIGN_SPECS/subsystem-designs/exit-chain-tp-sl-design.md` (the as-built design these divergences sit in); [[feedback_single_source_the_computation_not_just_the_mode]].
