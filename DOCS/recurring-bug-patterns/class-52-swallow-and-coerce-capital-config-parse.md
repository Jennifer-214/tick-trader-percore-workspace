# Class 52 — Swallow-and-coerce parsing of capital/config input (malformed → valid-looking value, no diagnostic)

> Codified 2026-06-24 at v5.15.5.F.4d.1.E.1.1 (the ③ config-compiler sweep — the D-242 refuse-don't-coerce model + the capital-money + feature/int malformed-capture cohort). Per-class file per file-size-split-discipline. **H-promotion deferred to Stage 5** per pattern-codification-lifecycle.

## Shape

A **lenient parser silently turns MALFORMED or UNRECOGNIZED operator input into a VALID-LOOKING value / slot / match instead of refusing it.** The operator's intent is dropped with **NO diagnostic** — the engine boots, runs, and is wrong, and nothing tells anyone. The lenient primitives:

- **`atof` / `atoi` / `atol` / `strtod` returning 0 on non-numeric** — `stop_loss_pct=banana` → `0.0` → stop-loss silently DISABLED; `use_testnet=garbage` → `atoi` → `0` → the PRODUCTION venue.
- **`strstr` substring match** — a typo'd key `node_0_risk_pct_typo` substring-matches `node_0_risk_pct` → writes slot 0 anyway; the operator's misspelling lands on a real slot.
- **a `strcmp`-chain whose terminal `else` silently defaults to the first enum / 0** — an unrecognized mode-string falls through to enum-0 (the first, often "safe-looking" value) rather than refusing.

The common thread: **0 / empty / first-enum is treated as a legal RESULT of bad input**, indistinguishable downstream from a deliberate 0 / empty / first-enum. It is the **input-side sibling of the sentinel-collapse family** — the malformed case is collapsed onto a valid value at the PARSE boundary, before any consumer can tell them apart.

This bites hardest on **capital/config** input because a swallowed fee, a flipped venue, or a disabled stop is a direct money loss, and the operator believes they configured the opposite.

## Detection heuristic

Flag any cfg / config / operator-input parse where **bad input cannot be distinguished from a legal value at the parse site:**
- (a) `atof` / `atoi` / `atol` / `strtod` / `parse_double_fast` whose **failure (`0` / `end==begin`) is consumed as a value** with no fault-out parameter and no WARN;
- (b) a **`strstr` / substring / prefix match** used where an EXACT key match is meant (a typo'd longer key matches the shorter target);
- (c) a **`strcmp`-chain with a terminal `else`** that assigns a default ENUM/value rather than returning a refuse-sentinel;
- (d) a `Money_FromString(...).value` (or any `{value, flags}` parse result) whose **`.flags` malformed-indicator is DISCARDED**.

Discriminator: *can a downstream reader tell "the operator wrote 0" from "the operator wrote garbage"?* If not — and the field is capital/config — it is this class.

## Structural fix — REFUSE, don't COERCE (the D-242 config-compiler model)

Detect malformed → set a **fault bit** → **REFUSE boot** (the config-compiler collects ALL problems into a compiler-style ERRORS/WARNINGS readout; a clean compile GATES every fresh start). Crucially, **single-source the capture at the parse PRIMITIVE**, never per-channel bolt-ons:

- **`Money_FromString` is the SSoT for capital money** (`FixedPoint/FixedPointN.hpp:1791`) — it returns a `MoneyParse {value, flags}` result whose flags carry `MONEY_PARSE_MALFORMED` / `MONEY_PARSE_OVERFLOW` (`:1787-1788`); consumers MUST check `.flags`, never discard them. The B1 increment (commit `98267be`) decoupled the **unit-agnostic malformed-refuse** from the capital-cap bit: a malformed decimal-`Money` value FATALs regardless of whether the field carries a `CAPITAL_BOUND_{LOSS,GAIN}` bit — the cap bits then gate ONLY the out-of-range fraction-sweep.
- **`tt::parse_double_fast_checked` / `tt::parse_int_checked` for the feature / int channels** (`CoreFrameworks/ParseFast.hpp:59/74`) — locale-immune `std::from_chars`-based, REPORT malformed via a `bool *malformed_out` param (NOT a silent 0). The walker's FPN/float branches (`CfgFieldDispatch.hpp:122-135`) are the remaining HOMED gap (the feature-determinism tier — they still call the UNCHECKED `parse_double_fast` and must swap to the checked variant + use a DISTINCT `FEATURE_MALFORMED` bit, not the capital bit; see Class 49).
- **EXACT key match, not substring** — fold every `strstr`/substring key test to an exact-suffix match so a typo'd key is UNRECOGNIZED (→ refuse) rather than coerced onto a real slot.
- **Refuse-sentinel, not enum-0** — an unrecognized mode-string returns a refuse value, never the first enum: `BanditAlgorithm_FromString` returns `-1` on unrecognized (`Strategies/BanditAlgorithmRegistry.hpp:247`); the `ReconcileMode_FromString` / `ConfigField_Set` model returns a 0/1 KEY-MATCH bool (`CoreFrameworks/Reconcile.hpp:149` — `0` = no-match → caller handles the miss, not a silent enum-0 assignment). The point is a NON-coercing result on no-match, not literally `-1`.

The fix spirit: **the parse primitive is the ONE place that decides "is this input legal?"** — so a new channel inherits the refuse automatically instead of re-implementing (and re-forgetting) the check.

## Canonical cohort (the `.E.1.1` ③ sweep)

| # | Site | Symptom | Status |
|---|---|---|---|
| G1/G2 | `fee_rate_maker` / `fee_rate_taker` (`CoreFrameworks/ControllerConfig.hpp:2341/2346`) | `Money_FromString().value` taken, `.flags` discarded → malformed → silent **0% fee** | FIXED `d85b5d6` — now routes through `cfg_capture_node_money_override` (`:1365`) which checks `.flags` (`:1369`) + REFUSEs boot |
| G3/G4 | legacy per-node arrays `node_risk_pct` / `node_max_drawdown_pct` (`:1928/1930` init, `:2934/2935` parse) | malformed value coerced to 0 | FIXED `84aa790` |
| G5/G6 | `strstr` substring under-fire (`node_0_risk_pct_typo`→slot-0, the old bug noted `:2906`) + `atoi` node-idx coercion | typo'd key writes a real slot | FIXED `84aa790` (the `strstr`→exact-suffix `strcmp` fold, `:2929`, 7 sites) |
| N1 | `BinanceConfig use_testnet` (`DataStream/BinanceCrypto.hpp:901`) | `garbage`→`atoi`→`0`→ **PRODUCTION venue flip** (silent testnet-off) | FIXED `04035ae` — now via `binance_cfg_selector` (`:842`) → `tt::parse_int_checked` + REFUSE |
| C1/C2 | the walker FPN/float branches (`CoreFrameworks/CfgFieldDispatch.hpp:122-135`) | `parse_double_fast`→0 (`:125`/`:132`), NO fault-out | **HOMED** — feature-determinism tier; needs a DISTINCT `FEATURE_MALFORMED` bit (Class 49) + the `tt::parse_double_fast_checked` swap |

Founding bug (per the ③ design): `stop_loss_pct=banana` → SL silently disabled — CLOSED for the flat/global path by the parse-point malformed-capture + `cfg_compile_ok()` boot-refuse.

## False-positive surface (per M3 — from the sweep)

NOT this anti-pattern when:

- **`0` / empty is a DEFINED inherit/default sentinel that malformed CANNOT reach.** The per-node `_PARSE_OV` override channel post-fix preserves `empty = inherit` — empty is a legal, intended value there; malformed is refused separately. Distinguish "0 means inherit" (legal) from "0 because we swallowed garbage" (the bug).
- **Trusted-internal HMAC'd artifacts.** Stamp / model bodies (`ModelInference` / `NodeModelZoo`), `RunHistory`, and the sysfs sibling-list are integrity-checked or machine-emitted, not operator free-text — no coercion surface.
- **Already-de-localed DATA-path parses.** `BacktestEngine` / `DepthReplayState` via `parse_double_fast_advance` / `strtoll` (F-054/F-055) consume trusted recorded data, not operator config.
- **Already-validated-with-WARN — the GOOD pattern.** `feature_mask` / `horizon_list` / `bandit_algorithm` / `barrier_blend_mode` already WARN + name a default on unrecognized input. WARN+named-default IS the target shape, not a violation.
- **Venue-JSON REST ingest.** `BinanceOrderAPI` / `Reconcile` JSON parsing is homed to D-123 / `.E.3` (the venue-truth reconcile surface), NOT this class.
- **Refuse-sentinel / key-match returns.** `BanditAlgorithm_FromString` returns `-1` (refuse) on unrecognized input (`Strategies/BanditAlgorithmRegistry.hpp:247`); `ReconcileMode_FromString` returns a 0/1 KEY-MATCH bool (`CoreFrameworks/Reconcile.hpp:149`, `0`=no-match) — both are non-coercing on no-match, the fix shape, not the bug.

The discriminator throughout: a swallowed 0/empty/first-enum is the bug ONLY where malformed input can REACH it AND the field is operator-supplied config/capital. A defined sentinel that garbage can't produce, or a trusted/internal source, is not in scope.

## recurrence_count

**Many** — the canonical cohort above (G1–G6 + N1 + the C1/C2 HOMED feature tier), a single systemic sweep at `.E.1.1` ③.

## Distinct from / sibling of

- **Class 48 (sentinel-value-as-control)** — Class 48 = a control INTENT carried by a magic data value that inverts by direction; Class 52 = a malformed INPUT collapsed onto a valid value at the parse boundary. Both = "a value that means more than it looks like."
- **Class 43 (one value derived 2 ways)** — the SSoT family on the COMPUTE side; Class 52 single-sources the PARSE primitive (the input side of the same SSoT spirit).
- **Class 49 (distinguishing signal collapsed upstream of the branch)** — the structural reason the C1/C2 feature channel must use a DISTINCT `FEATURE_MALFORMED` bit and NOT the capital bit: folding both onto one flag re-creates Class 49 at the fault-bit layer.
- **Class 53 (rename-completeness gap on the un-compiled surface)** — the sibling at the compiler-invisible config surface; both are silent-mishandling-of-bad-config, and **refuse-don't-coerce is the shared fix spirit**.

## Closure mechanism

- The **refuse-don't-coerce parse-primitive discipline** — `Money_FromString` `{value,flags}` (capital) + `tt::parse_*_checked` (feature/int) are the single-source capture points; consumers MUST consult the fault, never discard it.
- The **D-242 config-compiler** — one validation pass collects ERRORS (block boot) / WARNINGS (proceed); `cfg_compile_ok()` gates every fresh start (live AND backtest).
- The **`cfg_load_fault_flags` bitmap** + fixed-buffer readout — the structural carrier of "which fields were malformed" from parse to the boot gate.
