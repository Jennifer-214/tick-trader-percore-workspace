# Working in Backtest/ — backtest + train→serve surface orientation

> On-demand: loads when you read/edit a file in `Backtest/`. CONCATENATES with the always-loaded
> root `CLAUDE.md` (universal core) — this is the Backtest SLICE, not a replacement. Universal rules
> (H1–H21, priority gradients, collaboration norms) are already loaded from root; this carries the
> surface detail that makes a backtest edit safe. Edit this workspace file, not the engine symlink.

## What this dir does

The simulated-fill / model-training half of the engine. `Backtest_Run` is now a **thin wrapper**
around `BacktestSharded_Run` — the legacy `PortfolioController_Tick`-driven body is GONE
(`BacktestEngine.hpp:811-851`). The sharded path runs the SAME per-core architecture as live
(`CoreFrameworks/ShardedBacktestDriver.hpp`), single-threaded, against historical aggTrades.

```
Backtest_Run  ──wraps──▶  BacktestSharded_Run        (dispatcher: BacktestEngine.hpp peeks engine_mode)
  HistoricalTick (double, recorder ingress)  ──▶  Tick<F>  ──▶  per-core slow+hot cycle (shared OMS)
  exit → OMS HandleFill → realized_pnl  ──▶  stats (P&L / win-rate / drawdown) + equity_curve
  post-pass: Features_PackAll matrix + LabelFunctions forward-scan  ──▶  train data → stamp → serve
```

- **Feature/label collection** (`collect_features=1`) feeds model training; `Features_PackAll`
  (`FeatureRegistry.hpp`) is load-bearing for **train-serve parity** — same packer the live slow path uses.
- **Labels** = `FOREACH_TARGET` X-macro registry (`LabelFunctions.hpp`); forward-scan post-pass over the
  full tick array. APPEND-ONLY — reordering/removing a row flips `LABEL_REGISTRY_HASH()` → stamp refusal.
- **Walk-forward / purged CV** (`ValidationSplit.hpp`): expanding-window folds with a lookback-aware
  **purge gap** = `max(horizon, max_feature_lookback) + buffer` (prevents temporal leakage; t+1 label contract).
- **Held-out** (`HeldOutSplit.hpp`): final-test partition locked behind a friction token (FNV-1a, not crypto)
  so accidental peeking is impossible / intentional peeking auditable. `OverfitDetection.hpp` = 4 threshold gates.
- **Fingerprint** (`Fingerprint.hpp`): SHA-256 over (cfg struct + data) for reproducibility — same cfg+data ⇒ same hash.

## Surface rules (load-bearing in Backtest/)

- **Backtest↔live ACCOUNTING PARITY is the prime rule.** Exit-P&L / fee / fill math MUST compute
  BYTEWISE-IDENTICAL to the live path or the golden the engine trains against diverges from what it serves.
  Backtest reaches parity by **construction**: it runs the SAME OMS (`event_log_mode=1` HandleFill + FillRecord
  + DrainPostFill pipeline, `BacktestSharded.hpp:162-190`), so realized P&L routes through the live
  **`Money_FillGross` SSoT (D-190)** — NEVER open-code a price-diff gross (`round(exit*qty)-round(entry*qty)`);
  that 2-mul form diverges 1 ULP from the 1-mul books under decimal half-even (PARITY-038, Landmine 8).
- **Fees are per-core, pre-resolved.** `cfg.cores[c].fee_rate_maker/_taker` → `Order_BindPreResolved` at submit
  → `pre_resolved.fee_rate` → HandleFill (`BacktestSharded.hpp:184-186`). NO scalar OMS fee mirror (Class 27/29).
  BNB discount via the shared `EngineCommon_ApplyBnbDiscount` (LIVE + BACKTEST same helper; PARITY-030).
- **Train-serve parity (M5).** Boot + slow-path-cycle go through shared `EngineCommon_BootGlobal/_BootPerCore/
  _SlowPathCycle*` so LIVE + BACKTEST + parity_harness share the execution layer by construction (PARITY-026..032).
  Any backtest-side Init/Bind/Configure has a LIVE sister — change BOTH simultaneously, never one path alone.
- **`Money` (decimal) for ALL accounting** (price/qty/fee/balance), `FPN_Binary<F>` for features; crossings only
  at named `Money_ToBinary`/`Money_FromBinary` seams (H4). `HistoricalTick` is `double` at the recorder ingress
  boundary ONLY (`money_from_double_payload`) — convert to `Money` immediately, never compute on the double.
- **Determinism (H8 priority).** Cross-run / cross-binary / cross-locale byte equivalence. The post-pass label
  scan + fingerprint + stamp emit are all byte-equivalence surfaces — locale-pinned, constant-iter, no float.
- **GOLDEN-REGEN owed after any money-formula change.** Backtest goldens (`Fingerprint_Compute`, stamp HMAC bodies)
  REGENERATE at a money-encoding epoch — an accidental change is silently absorbed into the new golden. The
  `.E.0.10` D-190 fix flagged a **backtest-golden regen check still owed**: after touching fill/fee/gross math,
  regen the relevant golden + refreeze, don't assume the old one still pins the new math.

## Tools for this surface (slice of `DOCS/TOOLS.md`)

- `check_money_gross_single_source.py` — D-190/M7 guard (pre-commit Check G): realized + unrealized price-diff
  gross MUST route through `Money_FillGross`; catches a re-introduced open-coded 2-mul form.
- `check_identifier_retirement.py` — H21 tombstone guard (pre-commit Check H): snapshot/format VERSIONs +
  persisted enum CODES + `LABEL_REGISTRY_HASH` keys append-only vs the golden ledger.
- `compare_scalers.sh` / `compare_scalers.cpp` — scaler train↔serve comparison (manual CLI).
- `python3 tools/check_plan_body_symbol_existence.py <plan>.md` — Class-14 fabrication catch before a plan cites
  a backtest fn/struct field that doesn't exist (pre-commit Check A).

## Skills for this surface

- `/parity-check` — train↔serve identity audit (features / labels / scaler / stamp body / cfg / threading / build flags).
- `/ml-audit` — feature compute → model load → inference → display silent-failure + train-serve gap walk.
- `/accounting-audit` — fee / commission / P&L / balance / **backtest-accounting parity** silent-correctness hazards.
- `/trace-deps` — dependency-chain for a label / feature / fee path before coding (catches Class 18 mirror gaps).

## Patterns + anti-patterns here

- DESIGN_SPECS: `meta-disciplines/train-serve-execution-layer-parity.md` (M5) ·
  `meta-disciplines/backtest-paper-live-convergence-discipline.md` (4-step promotion) ·
  `refactor-patterns/shared-helper-extract-for-train-serve-mirror-close.md` ·
  `framework-patterns/hierarchical-config-validation-pattern.md` ·
  `framework-patterns/x-macro-registry-with-presence-dispatch.md` (FOREACH_TARGET) ·
  `wire-format-patterns/wire-format-byte-preservation-discipline.md` (stamp/fingerprint emit).
- RECURRING_BUG_PATTERNS: **Class 18** (mirror plan missing data-flow — the backtest↔live sister trap) ·
  **Class 12** (wired-but-unexercised ML paths) · **Class 24** (capability the operator can't see/configure) ·
  **Class 27 / 29** (scalar fee-mirror / silent zero-fee-rate at Order binding) · **Class 5** (paper-reset
  completeness — backtest OMS starts fresh from `starting_balance`, never inherits live state).

## Reach for more

- Universal rules/invariants: root `CLAUDE.md` (already loaded) + `DOCS/DESIGN_PHILOSOPHY.md` § 2 (invariants) / § 5 (determinism).
- Train→serve / FeatureRegistry / scaler / stamp internals: `DOCS/CLAUDE_ML_INVARIANTS.md`.
- Backtest suite (Run Control / Training / WF / Held-Out GUI): `DOCS/CLAUDE_FOXML_SUITE.md`.
- OMS / fill / HandleFill / DrainPostFill (the shared execution layer): `CoreFrameworks/CLAUDE.md` + `DOCS/CLAUDE_INVARIANTS.md`.
