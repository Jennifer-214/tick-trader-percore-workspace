---
type: audit-report
audit: completeness-critic (Stage 3.5, standing per D-119)
target: plans/v5.15-live-readiness/subplans/2026-05-30-v5.15.5.F.4d.1.E-money-numeric-core-foundation.md (v0.3)
date: 2026-06-09
engine_head: 0e48150 (v5.15.5.F.4d.1.E.0.8)
question: what money-touching surface did NO auditor cover?
verdict: 3 REAL gaps (2 HIGH-for-plan-completeness, 1 MED) + 2 LOW pins; all other checklist rows NO MATERIAL GAP
---

# Completeness-critic report — Ship B (decimal money)

Method: 8-row edge checklist, every candidate grep-confirmed at HEAD. Findings exclude
everything in the 11-auditor covered set (stamp/HMAC + CfgFieldDispatch 8 entry points, fee
sites, commission, snapshots/versioning, Reconcile, SymbolFilters, producer/Tick ring, D-103
casts, TradeReader, TickRecorder, LabelFunctions, etc.).

---

## GAP 1 [HIGH] — GUI cfg money WRITE path bypasses the dispatcher family entirely

The B3 net (decimal branch in the 3 wire dispatchers + `check_storage_t_coverage.py`
both-branch extension) covers `CfgFieldDispatch.hpp`. The GUI has a SEPARATE cfg writer it
never sees — `cfg_write_field` text-splice (`GUI/SettingsPanel.hpp:711-769`) fed by three
value sources:

- **(a) Legacy `field_defs[]` CFG_FLOAT money rows — FULL bypass, SILENT at flip.**
  `fee_rate_maker` / `fee_rate_taker` (`SettingsPanel.hpp:292/:297`, fmt `"%.3f"`).
  Round-trip: `Settings_Load` parses cfg with `(float)atof` (`:899`) → ImGui `InputFloat` on
  `float float_vals[]` (`:1045`) → `snprintf(v, 32, fd->fmt, float)` → `cfg_write_field`
  (`:1043-1049`). Owns its own float copies — touches NO typed field → **nothing red-builds
  at the decimal flip**. The comment at `:289-291` says tp/sl/fee_rate "migrated to
  FOREACH_CFG_FIELD" and the residual cohort is "KIND_STRING / KIND_FILE_PATH (.F.4e scope)"
  — but fee_rate_maker/taker are CFG_FLOAT residuals that did NOT migrate.
- **(b) `per_core_fields[]` float table money rows — FULL bypass, SILENT at flip.**
  `fee_floor_mult` `"%.1f"` (`:559`), `simpledip/mr/emacross/ml`_`tp_pct`/`sl_pct` `"%.2f"`
  (`:573-599`), saved at `:1646-1654`; `per_core_risk_pct` `"%.2f"` (`:1317-1324`). Parse =
  `(float)atof` (`:918/:934`). State comment `:683-684`: "Floats only — every per-core
  override is FPN_Binary<F> in the cfg" — i.e. these ARE money-typed cfg keys on the engine
  side.
- **(c) `tt::cfg_render_field<T>`** — the GUI-side 3rd sister of cfg_parse/save_field lives
  in `SettingsPanel.hpp:60-94`, NOT in CfgFieldDispatch.hpp. Its family `static_assert`
  (`:61-64`, `is_fp_binary_v||float||integral||array`) red-builds for decimal (good), but the
  binary branch's value path is `FPN_ToDouble → float vf → SliderFloat → FPN_FromDouble`
  (`:84-93`) — if the Ship-B decimal branch replicates that shape, every GUI edit quantizes
  money through float32 even though `cfg_save_field` then emits an "exact" decimal string of
  the quantized value.

**Why it bites at the flip:** post-Ship-B the cfg file is an exact-decimal money SOURCE
(D-106 source-fidelity; #5 exact FromString). The GUI is a WRITER of that source whose value
provenance is float32 + coarse fixed fmt — an operator edit silently rewrites a money key
float-quantized (e.g. taker fee 0.0825% → `"%.3f"` of 0.0825f → `0.083`), and STAMP_BOUND
money fields then mismatch the stamp's recorded exact value at drift-compare. Paths (a)/(b)
are invisible to the compiler AND to the B3 coverage tool.

**Disposition suggestion:** enumerate every money key riding (a)/(b) (one rg over
`field_defs[]` + `per_core_fields[]` vs the ~30 money rows in FOREACH_CFG_FIELD); migrate
them to the typed render path or route their save through `tt::cfg_save_field<T>`; design the
decimal render branch with exact-string (InputText) or double-precision input + exact
write-back; extend the B3 tool to assert no money cfg key is written outside cfg_save_field.

## GAP 2 [HIGH] — boot capital-allocation money math in double; LIVE+BACKTEST twins unenumerated

`CoreFrameworks/EngineSharded/Run.hpp:888-910` → `:950`:
`double total_balance = FPN_ToDouble(cfg.starting_balance)` · `(total*risk)/num_cores` ·
per-core override `total_balance * FPN_ToDouble(cfg.core_risk_pct[i])` (`:908`) →
`FPN_FromDouble<F>(core_balance)` (`:950`) → `EngineCommon_BootPerCore(...)`
(`EngineCommon.hpp:242`) → per-core `allocated_balance` (PERSISTED money,
`ShardedSnapshotPersist.hpp:180`). Twin: `Backtest/BacktestSharded.hpp:263-266` → `:287`.

This is the per-core capital SPLIT — money mul/div round-tripped through double on the boot
path — and it appears in NO plan inventory: not the 42-site accounting enumeration, not
D-103's ~12 casts, not D-102 (producer tick path only; the plan names `Run.hpp:653`
usdt_recovered two paragraphs away but not the allocation block). It red-builds at the flip
ONLY while decimal lacks ToDouble/FromDouble; the moment a display `to_double` exists (B-γ
grants one), this compiles silently again as double money math — the D-102 lossy-intermediate
shape on the capital-allocation path. The decimal rewrite needs a DESIGNED split (D-105
rounding; deterministic remainder rule) and the twins kept value-identical (the code itself
carries the "O2 bytewise-identical math" discipline comment — `Run.hpp:898/:905`).

**Disposition suggestion:** add both twins to the accounting-site enumeration; design the
exact decimal allocation (#4 rounding helper); add a D-100 oracle row (split values + Σ
property); train-serve M5 check on the twin.

## GAP 3 [MED] — emergency-flatten / orphan-recovery qty quantization cohort under-enumerated

`binance_round_qty` caller set (full rg): def `BinanceOrderAPI.hpp:178`; `:511/:556` (the two
the plan names at B6); **`ShardedLiveSafety.hpp:204`** — FORCE-CLOSE flatten: position
quantity (money state) → `FPN_ToDouble` (`:203`) → double lot-round → `FPN_FromDouble`
(`:210`) → `OrderManager_Submit` market sell; **`ShardedLiveSafety.hpp:77`** — boot
orphan-BTC close (venue-balance double end-to-end, never enters FPN → silent at flip);
`main.cpp:438/751/938` (legacy single-core, type-migrates per B2's legacy note).

**Why it bites:** the flatten path is the INCIDENT path (kill-switch / shutdown), and B-ζ
makes it operationally live at the Ship-B epoch itself ("flatten all positions before
deploying"). `:204` red-builds at the flip, but as an un-enumerated site the mechanical fix
may preserve the double detour instead of routing through #6's `FPN_Quantize`; a mis-rounded
flatten qty = `-1013` rejection or residual position DURING an emergency. `:77` is wholly
venue-side (sell orphan dust; proceeds re-queried at reconcile) — lower stakes, but its
`GetBalances` JSON parse is a #5-cohort sister not named in the plan.

**Disposition suggestion:** fold `ShardedLiveSafety.hpp:204` (and `:77` as venue-side
documented-exempt or #5-parse member) into the #6 quantization cohort enumeration; legacy
main.cpp sites ride the B2 legacy disposition.

## LOW pins (plan-text completeness, not bugs)

- **L1 — depth domain pin.** `DepthRecorder.hpp:259-263` emits book levels via
  `FPN_ToDouble`+to_chars CSV (sister of covered TickRecorder); replay parses back
  (`BinanceDepth.hpp:163` IS in #5). Plan should pin explicitly: book bid/ask price+qty stay
  BINARY feature domain → recorder/replay untouched at Ship B. One sentence in § Blast
  radius kills the ambiguity B4 resolves for tick.price.
- **L2 — money→signal ingress naming.** `ControllerEventLoop.hpp:1681` (pnl_feeder push),
  `:1692-1695` (bandit pnl_bps), `:1748-1760` (counterfactual exit reward) convert money →
  double signal domain. All compile-caught at flip + M6 (`last_realized_return[]`
  signal-domain) is the governing precedent — recommend the D-103 enumeration absorb them as
  named signal-domain casts so the red-build fixes follow M6 deliberately.

## Checklist rows with NO MATERIAL GAP (verified)

1. **Observability:** calibration-log money derivations red-build
   (`OrderManager.hpp:683-688` `FPN_ToDouble`); emit format pinned by byte-format snapshot
   tests (`CalibLogColRegistry.hpp:36-41`); MetricsLog is legacy main.cpp-only +
   compile-caught; **Notify carries NO money formatting** (all call sites verified — kill/
   orphan bodies are textual; the one numeric body is venue-double qty at LiveSafety:84);
   HealthLog/latency logs carry no money.
2. **RunHistory** (`MemHeaders/RunHistory.hpp`): NOT HMAC-signed (append-only JSONL); carries
   NO money fields — wf_mean_val/held_out_metric/gap are validation metrics; emit already
   per-thread locale-pinned (`:90-92`). The prompt's %.17g-at-:87-89 hypothesis is false at
   HEAD (emit is %g/%.6f at `:94-116`).
3. **GUI beyond TradeReader:** TUISnapshot is strictly one-way display doubles
   (`ShardedSnapshot.hpp:60-230`, no write-back; B-γ governs); Dashboard/Chart/Candle/
   TradeHistory read it or the trade log (TradeReader covered). Exception = GAP 1.
4. **Backtest artifacts:** ValidationSplit/HeldOutSplit emit fold indices only;
   BacktestSnapshot is a TUI_CopySnapshot wrapper; PastRuns reload = historical text;
   training labels = LabelFunctions (covered); no feature/money CSV export found.
5. **Deploy/ops:** kill-switch money compares all FPN-typed (`CEL:1994/2895-2909` —
   compile-caught); ks thresholds persist under the OMS 10-PERSIST assert →
   SHARDED_SNAPSHOT_VERSION 9 gate (`OmsFieldRegistry.hpp:370-385`); recovery_until_us =
   time. Real finds here are GAPs 2/3.
6. **External tooling:** `tools/chart.py` = tolerant pandas float display parser; no other
   tools/*.py|sh consume money bytes (fp_determinism golden covered; gen_code_map = symbols).
7. **Tests infra:** parity_harness compares legacy↔sharded doubles at 1e-9 epsilon
   (`parity_harness.cpp:201`) — rides the flip; money goldens regen at epoch per the plan's
   Tests-changed section; no stray binary-money fixture files found.
8. **DataStream:** depth levels = market-data/feature domain; ingress casts covered
   (CEL:2202-2219); only L1's domain pin missing.

**Net:** the formal audits covered the engine core thoroughly; the misses cluster exactly at
the operator-touching rim — the GUI cfg writer (the one money-WRITE path with no typed
dispatcher), the boot allocation seam between cfg-money and per-core money, and the
incident-path flatten. All three are pre-coding plan amendments, none is an
architecture-killer.
