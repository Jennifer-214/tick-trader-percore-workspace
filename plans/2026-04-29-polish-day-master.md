# Polish Day Master Plan — 2026-04-29

Closes outstanding work from yesterday's strategy-fix arc + pre-live
hardening + navigation cleanup, in dependency order. Each item is sized
for a single session.

## Today's scope (no soak needed)

These don't depend on overnight soak data — can ship in any order, but
the listed sequence respects dependencies + closure value.

### 1. `/dust` first validation run (~5 min)

The skill was written but never invoked. Validate it before depending
on it for future cleanup work.

- Run `/dust quick` (or invoke the SKILL.md instructions manually)
- Read the output — does it produce a useful punch list?
- If output is too noisy / too sparse: tweak SKILL.md scan patterns
- Acceptance: at least one item in the punch list that's a genuine
  cleanup candidate (not false-positive)

**Why first**: every later item benefits from knowing the audit tool
works. Cheapest validation pass available.

### 2. Strategy profitability Phase 3 — runtime BUY_BLOCKED gate (~1h)

Closes yesterday's strategy-fix arc with a runtime guard that catches
**dynamic** TP collapse (EMA's stddev-based TP shrinking when stddev
is low), not just static cfg misconfig (which v5.1.3 already warns at
boot).

- Edit `Strategies/StrategyParameters.hpp` dispatcher: after each
  strategy emits `out->sg_take_profit_price`, compute
  `tp_dist_pct = (sg_take_profit_price - bg_price_threshold) / bg_price_threshold`.
- If `tp_dist_pct < 3 × cfg.fee_rate_taker`: `out->flags |= GATE_FLAG_BUY_BLOCKED`.
- Log once per slow-path cycle when blocked (not per tick).
- Tests: 4-6 assertions in controller_test verifying the guard fires
  when expected and doesn't fire when TP is wide enough.

Ships as **v5.1.9**. Mechanical, low-risk.

### 3. Strategy profitability Phase 4 — sizing audit (~30 min)

Walk the actual per-trade notional path:
`Strategy_BuildParameters` → `out->trade_size` → `OMS_PushSubmit` → `fill_qty`.
Document what produces $750 notional with `risk_pct=10%` / 4 cores.
Identify if the math is right or if we're under-sizing relative to fee
budget.

- May not need code changes — just verification + documentation.
- If under-sizing found: cfg knob `core_N_min_notional` (deferred to
  v5.2.x; document only).

Ships as part of v5.1.9 (no behavior change, doc + maybe one cfg field).

### 4. `DOCS/CODE_MAP.md` — auto-generated navigation index (~1h)

Highest-leverage long-term nav win. Cold pickups go from 30min hunting
to "read CODE_MAP.md, jump straight in."

- Write `tools/gen_code_map.sh` script:
  - Walk `*.hpp` files
  - Extract `Pattern_FunctionName` definitions via regex
  - Group by subsystem directory
  - Output markdown table: `function — file:line — one-line purpose
    (from preceding comment if present)`
- Output `DOCS/CODE_MAP.md` with sections per directory
- Add to build.sh: regenerate on every `./build.sh test` (cheap)
- Commit the script + initial CODE_MAP.md

Ships independently (could be v5.1.9 or its own commit on the same
release).

### 5. `tests/INVARIANTS_MAP.md` — invariant-to-test mapping (~30 min)

Walk `DOCS/CLAUDE_INVARIANTS.md` invariant by invariant. For each, find
the test in `controller_test.cpp` that covers it (grep for the
invariant name or the function it constrains).

- Output: markdown table `Invariant — Tests covering it — Last verified
  date`
- Flag invariants WITHOUT tests as gaps
- Doc-only commit; no code changes

Ships with v5.1.9.

### 6. Held-out gate Phase 1 — stamp format + boot check (~2-3h)

Pre-live hardening. See `plans/2026-04-29-held-out-gate.md` Phase 1.

- New stamp format (JSON-ish, sha256 model hash + sha256 signature)
- `verify_model_stamp()` in `ML_Headers/ModelInference.hpp`
- Gate `CoreModelZoo_LoadAll()` on stamp verify
- New cfg fields: `held_out_stamp_secret`, `held_out_gate_strict`
- New CLI tool: `tools/stamp_model.cpp`
- Tests: 8-12 assertions for verify + tamper detection

Ships as **v5.2.0** (minor bump because it changes what model files
are accepted). Strict-off escape hatch (`held_out_gate_strict=0`)
keeps existing model loading working until you re-stamp.

### 7. Live reconciliation Phase 1 — boot reconcile (~1h)

Pre-live hardening. See `plans/2026-04-29-live-reconciliation.md` Phase 1.

- `OrderManager_Reconcile()` entry point
- REST `account` + `openOrders` + `myTrades` calls (use existing
  `BinanceOrderAPI`)
- Cancel pre-shutdown live orders; replay missed fills; refuse boot on
  CRITICAL local-vs-exchange disagreement
- Cfg: `reconcile_interval_sec`, `reconcile_dry_run`
- Tests: mock exchange responses, 8-12 assertions

Ships as **v5.2.1** (or part of v5.2.0 alongside held-out gate — both
are pre-live; logical to bundle).

## Tomorrow (soak-data dependent)

These need overnight v5.1.7 soak data first:

### A. Soak post-mortem (~30 min)

- Pull `logging/btcusdt_order_history.csv` from overnight run
- Grep `engine.log` for `[exit-diag]` lines (v5.1.6 diagnostic output)
- Verify: do "TP" exits at +0.097% disappear after v5.1.7 fee-floor
  guard? Or do they persist (= H1 wrong, H2 or H3 was the actual cause)?
- Update `plans/2026-04-29-strategy-profitability-master.md` with the
  Phase 1 evidence and confirmed/refuted hypothesis

### B. Strategy profitability Phase 5 — regime fit audit (~2-3h)

- Per (strategy, regime) pair: compute on a tick day → entries, win
  rate, net P&L, avg hold time
- Output: ranking of which strategies have edge in which regimes
- Decision: prune dead combinations from AUTO routing

### C. Merge `feat/strategy-fixes` → `experiment/per-core-sharding` (~5 min)

Only after soak validates v5.1.7 actually fixed the +0.1% bleed.

### D. Held-out gate Phase 2 — foxml_suite UI integration (~1-2h)
### E. Live reconciliation Phase 2 — WS reconnect reconcile (~1h)

## Later this week

### F. Public release v2 (Path B) decision + initial push

After today's polish stabilizes the engine. See
`plans/2026-04-29-public-release-v2-strategy.md`.

### G. Strategy profitability Phase 6 — ML route

Train + walk-forward + held-out + stamp + deploy ML model to a core.

## Order of attack today

```
1. /dust validate              5 min  ← warm up
2. Strategy P3 (runtime gate)  1 h    ← close yesterday's arc
3. Strategy P4 (sizing audit)  30 min ← finish profitability close-out
   ───────────────────── ship as v5.1.9 ─────────────────────
4. CODE_MAP.md                 1 h    ← navigation polish
5. INVARIANTS_MAP.md           30 min ← test discipline
   ───────────────────── ship as v5.1.10 (docs) ────────────
6. Held-out gate P1            2-3 h  ← pre-live hardening
   ───────────────────── ship as v5.2.0 ─────────────────────
7. Live reconcile P1           1 h    ← pre-live hardening
   ───────────────────── ship as v5.2.1 ─────────────────────
```

Total: **6-7 hours of focused work**. Realistic for a polish day.

## Polish day done state

End of today:
- v5.1.9 ships (strategy profitability close-out)
- v5.1.10 ships (nav docs: CODE_MAP + INVARIANTS_MAP)
- v5.2.0 ships (held-out gate)
- v5.2.1 ships (live reconcile boot phase)
- 4 active plans become 2 (strategy + reconcile have remaining phases for tomorrow; held-out has UI phase remaining)
- Pre-live hardening foundational work done
- Engine on `feat/strategy-fixes` ready to soak overnight v5.2.1 binary

## Risk register

| Risk | Mitigation |
|---|---|
| Strategy P3 runtime gate prevents legit entries during low-vol periods | The gate fires only when TP < fee floor; legit entries with sane TP unaffected |
| Held-out gate refuses to load existing models (no stamps yet) | v5.2.0 ships with `held_out_gate_strict=0` default; strict mode opt-in |
| Live reconcile triggers on testnet residue | `reconcile_dry_run=1` cfg for first deploy — log what would change without applying |
| Time budget overrun — running into evening | Stop after item 5 (CODE_MAP + INVARIANTS_MAP) and ship the smaller set; held-out + reconcile move to tomorrow |
| /dust skill produces noise — useless punch list | Adjust SKILL.md scan patterns; doesn't block other work |

## Rollback story

Each ship gets its own pre-tag:
- `pre-v5.1.9-strategy-close` before Phase 3
- `pre-v5.1.10-docs` before CODE_MAP
- `pre-v5.2.0-held-out` before stamp work
- `pre-v5.2.1-reconcile` before reconcile

Branch stays on `feat/strategy-fixes`. Merge to main only after
overnight soak validates v5.2.1 (a full day from now).

## What this is NOT

- Not strategy alpha hunting (that's Phase 5+ tomorrow, and the ML route)
- Not the public release work (that's Path B decision + push, this week)
- Not multi-exchange / API key UI (deferred per future-directions doc)
- Not refactoring `EngineSharded_Run` size (the elephant — leave it)
