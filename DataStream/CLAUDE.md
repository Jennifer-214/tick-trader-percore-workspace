# Working in DataStream/ — venue-ingest + parser surface orientation

> On-demand: loads when you read/edit a file in `DataStream/`. CONCATENATES with the always-loaded
> root `CLAUDE.md` (universal core) — this is the DataStream SLICE, not a replacement. Universal rules
> (H1–H21, priority gradients, collaboration norms) are already loaded from root; this carries the
> venue-boundary detail. Edit this workspace file, not the engine symlink.

## What this dir does

The **venue boundary** — every byte that crosses from Binance into the engine, and every recorder that
writes ticks/depth/trades back out. Three sub-surfaces:

- **WS/REST parsers** — `BinanceCrypto`/`BinanceDepth` (market data: trade + `@depth5@100ms`),
  `BinanceUserData` (the **executionReport** fill stream), `BinanceOrderAPI` (REST order place/query +
  `exchangeInfo` filters), `FauxFIX` (FIX 4.4 test parser). All are JSON/tag inner loops on a network thread.
- **Sister parser surface (NOT in this dir):** `CoreFrameworks/Reconcile.hpp` — the **myTrades** replay
  parser (`Reconcile_ParseMyTrades` → `ApplyMissedFills` → `HandleFill`). Same venue-decimal contract;
  audit the two TOGETHER — a fix on the WS path that skips reconcile leaves the data-loss bug live (A4).
- **Recorders + ingest plumbing** — `TickRecorder`/`DepthRecorder` (CSV capture, daily rotation, gap
  markers), `MockGenerator`, `WebSocketUtil`, the `ExchangeAdapter` contract these feed.

Async-thread cadence (Binance WS / depth / recorders): non-trading-path, p99 <100μs — but the parsers feed
the OMS + capital paths, so **correctness here is a capital concern**, not just a latency one.

## Surface rules (load-bearing in DataStream/)

- **H5 — NO scalar JSON in parser inner loops.** No `strstr`/`atof`/`atoi`/hand `strtod`. Use
  `tt::parse_double_fast` / `parse_double_fast_n` (`CoreFrameworks/ParseFast.hpp` — `std::from_chars`,
  **locale-immune**, no `LC_NUMERIC` dependency) and `simdjson`/`fast_float` where wired. `atof` reads the
  locale decimal point and silently corrupts every price under a non-`C` locale (the reason ParseFast exists).
- **D-123 venue-ingest-decimal contract.** Venue decimal STRINGS → exact decimal `Money` via
  **`Money_FromString`** (`FixedPoint/FixedPointN.hpp:1788`), **NEVER through `double`**. Carry decimal on
  `OrderResult` (no `cum_quote/exec_qty` double-division — that diverges from the WS `"L"` exact value). Book
  the venue-REPORTED commission **source-exact**, including `commissionAsset` (`"N"`) — never substitute a
  recomputed `notional×rate`. **CURRENT STATE:** the live path still bridges through
  `binance_json_extract_double` + `money_from_double_payload` (exact only for ≤8dp via `llround`); the
  string-direct `Money_FromString` rework rides `.E.1`/`.E.3` (D-176/D-178..D-180 landed the decimal core +
  the casts; the call-site swap is pending). Treat the double bridge as KNOWN-TEMPORARY — do not add new
  `double`-typed venue money fields.
- **Recorder emit is locale-pinned + lossless.** CSV writers use `std::to_chars` (PARITY-036/F-054) — never
  `snprintf("%f")` / `%g` (locale-sensitive + lossy). Daily rotation + gap markers are the audit contract;
  don't drop the `# GAP` semantics (`last_update_id` backward / WS-silence) when touching `DepthRecorder`.
- **Wire/persisted identifiers are append-only + immutable (H21).** `executionReport` field keys, persisted
  enum CODES, recorder CSV column order, snapshot/format VERSIONs — tombstone, never renumber/reuse
  (Knight-Capital). HMAC-signed bodies preserve bytes (H9).
- **Money math = `Money`** (decimal) for prices/qtys/fees/balances; **features = `FPN_Binary<F>`** (depth
  `BookSnapshot`, `ema_price` ingress); crossings only at named `Money_ToBinary`/`Money_FromBinary` seams (H4).
- **SPSC contract on the fill ring.** WS thread = sole producer of `CMD_WS_FILL`; drainer = sole consumer via
  `OrderManager_Tick` (H1–H3 — lock-free; no mutex, no `sleep_for` on the data path beyond reconnect backoff).

## `.E.0.10` adversarial-hunt findings on THIS surface (READ before editing the parsers)

The `.E.0.10` 5-agent parser hunt found 3 capital bugs here — durable data-loss STOPs land in `.E.0.10`, the
decimal-exactness fix rides D-123. Disposition register: `plans/v5.15-live-readiness/plan_checks/E.0.10-finding-disposition-register.md`.

- **A2 (HIGH)** — **partial-fill qty dropped.** Venue `"z"` (cumulative filled qty) is **never parsed**;
  `filled_qty` is OVERWRITTEN per event, not accumulated; the slot frees on the 1st fill → later partials
  dropped → position sized at ONE leg. `BinanceUserData.hpp:339` + `OrderManager.hpp:1394,1440`. **TECH_DEBT-169.**
- **A4 (MED→HIGH on BNB)** — **non-USDT commission dropped.** BNB-pay (a common account default) → a
  fabricated `notional×rate` fee booked instead (`OrderManager.hpp:1309-1318`); AND the reconcile path drops
  the parsed `t.commission` entirely (`HandleFill` called with no commission args — `Reconcile.hpp:546`). The
  contract must carry `commission`+`"N"` source-exact through BOTH WS and reconcile. **TECH_DEBT-169.**
- **A5 (MED)** — **WS fill side never cross-checked vs venue `"S"`.** Side is taken from the local order type
  only; a slot-decode slip → buy booked as sell with no guard (Knight-shaped). `ExchangeAdapter.hpp:43` +
  `OrderManager.hpp:1330`. Fix ~5 lines: parse `"S"`, assert == local, warn/skip on mismatch. **TECH_DEBT-171.**

## Tools for this surface (slice of `DOCS/TOOLS.md`)

- `check_locale_determinism.sh` — locale-determinism guard (under `check_determinism.sh` umbrella); catches
  `atof`/`%f` reintroduction + locale-sensitive emit on the parse + recorder paths.
- `check_identifier_retirement.py` — H21 tombstone guard (pre-commit Check H) vs the golden `identifier_ledger.txt`;
  fires if a wire/persisted CODE or VERSION is renumbered/reused (Class 40).
- `check_tools_inventory.py` — every `tools/*` has a TOOLS.md row (if you add a parser/recorder helper).

## Skills for this surface

- `/accounting-audit` — commission / fee / P&L booking from fills (the A4 surface; venue-reported vs recomputed fee).
- `/hft-audit` — branchless parse-loop discipline · fixed-point edge cases · lock-free fill ring.
- `/bug-check` — recurring-bug scan (Class 41 raw-`.v`, Class 38 phantom-invariant, Class 39 setlocale).
- `/parity-check` — wire-format byte preservation on HMAC-signed bodies + recorder↔replay identity.
- `/trace-deps` — trace a parsed field (e.g. `"z"`, `commission`) through OrderResult → OMS before coding.

## Patterns + anti-patterns here

- DESIGN_SPECS: `data-disciplines/locale-determinism-discipline.md` (the `atof`/emit law) ·
  `wire-format-patterns/wire-format-byte-preservation-discipline.md` (HMAC bodies, H9) ·
  `wire-format-patterns/wire-format-canonical-body-invariants-helper.md` ·
  `meta-disciplines/dead-code-and-identifier-retirement-discipline.md` (H21) ·
  `audit-methodologies/adversarial-multi-agent-audit-methodology.md` (the `.E.0.10` fan-out methodology).
- RECURRING_BUG_PATTERNS: **Class 38** (phantom invariant — a load-bearing parse assumption asserted only in
  a comment) · **Class 39** (global `setlocale` race) · **Class 40** (identifier retirement) · **Class 41**
  (raw `.v` encoding-blind compares across dual encoding types — relevant once money fields go decimal).

## Reach for more

- Universal rules/invariants: root `CLAUDE.md` (already loaded) + `DOCS/DESIGN_PHILOSOPHY.md` § 5 (determinism) / § 2 (invariants).
- Required reading before parser/OMS-feeding code: `DOCS/STRATEGY_AND_CODING_RULES.md` (H5 inner-loop rule).
- The decimal-OrderResult rework (D-123 in flight): `plans/v5.15-live-readiness/subplans/2026-05-31-v5.15.5.F.4d.1.E-swar-parse-design-notes.md` + the architecture decision-log (D-176/D-178..D-182).
- OMS / fill-handling / reconcile changes: `DOCS/CLAUDE_INVARIANTS.md` + `CoreFrameworks/CLAUDE.md` (the OMS/drainer slice).
