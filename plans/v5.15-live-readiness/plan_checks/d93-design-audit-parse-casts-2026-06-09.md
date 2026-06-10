# D-93 new-function design audit — cluster: #5 exact decimal FromString + D-103 cast pair (to_binary/to_decimal)

**Date:** 2026-06-09 · **Auditor:** D-93 design-audit agent (Layer 2; no subagents, no edits) · **Engine HEAD:** `0e48150` (v5.15.5.F.4d.1.E.0.8)
**Targets:** plan v0.4 `subplans/2026-05-30-v5.15.5.F.4d.1.E-money-numeric-core-foundation.md` (#5 row, § Blast radius parse rows, B3/B4/B6, S-14/S-17/S-18/S-19/S-21, D-170 row) + design sidecar `subplans/2026-05-31-v5.15.5.F.4d.1.E-11-new-function-designs.md` (#5 + the "trivial scaling pair" note).
**Method:** direct reads of both plan artifacts + decision log (D-103/D-107/D-122/D-124/D-170/D-173) + Ship-B gate synthesis + merge-scan item 6 + hft-audit (b)/F-rows + code-at-HEAD verification of every referenced site (listed in Appendix).

**Combined verdict: YELLOW — architecture sound and converged in the AUDIT artifacts, but the design SIDECAR (the D-93 artifact of record) is stale/incomplete on this cluster: the cast pair has NO design section (only a superseded "trivial scaling pair" note), the cast rounding mode is unpinned, the per-site `ok=false` table does not exist, and the #5 front-end text contradicts the S-19 share decision. Nothing re-opens a decision; everything below is sidecar additions + 3 operator decisions.**

---

## Per-question verdicts

| Q | Verdict |
|---|---|
| 1. #5 edge pins vs the live front-end | **DESIGN-GAP** — core shape right; 6 edges unpinned; sidecar accumulator shape contradicts S-19 front-end share |
| 2. Per-site `ok=false` semantics | **DESIGN-GAP (the big one)** — no per-class table anywhere; LIVE-fill degrade shape undesigned (quorum LOW confirmed at synthesis :36) |
| 3. PCT exact digit-shift (S-18) | **DESIGN-GAP** — requirement pinned (S-18/B3), mechanism hand-waved (sidecar #5 says nothing about PCT) |
| 4. `to_binary` design | **DESIGN-GAP** — divmul-route converged in merge-scan item 6 + S-19, NOT in the sidecar; rounding mode unpinned; saturation provably unreachable (should be stated, not coded blind) |
| 5. `to_decimal` design | **DESIGN-GAP** — same: mechanism converged (`round₄(umul256(\|b.v\|,10⁸)>>64)`), not in sidecar; rounding mode unpinned; divisor-2⁶⁴ tie nuance unstated; saturation REQUIRED this direction |
| 6. D-170 placement + per-tick budget | **DESIGN-OK** — egress lock verified (log :1079); hft (b) section verified net ≤0 against the actual divmul-shaped cast at HEAD sites; conditional on Q4 adoption |
| 7. Cast determinism stated | **DESIGN-GAP (minor)** — pinned at decision level (D-107 "byte-DETERMINISTIC, M5"); must be restated in the cast design + explicit D-100 oracle cast rows |

---

## Q1 — #5 edge pins, compared against the live shared front-end (`FixedPointN.hpp:1579-1607`, read at HEAD)

The live binary `FPN_FromString<64>` the design shares (per S-19: "shares the LIVE specialization front-end, forks only the scale tail") has these properties the #5 design text does not reckon with:

| Edge | Live front-end behavior (verified) | #5 design says | Pin needed |
|---|---|---|---|
| Sign | accepts `-` AND `+` (`:1585-1586`) | "sign from leading `-`" only | **YES** — `+` accepted (front-end already does) or rejected; pick one. Recommend: accept, matches shared scan |
| Garbage chars (incl. `e`/`E`) | silently SKIPPED (mask zeroes the accumulate; `"1e5"` parses as 15) | non-digit/non-`.` → `ok=false` ✓ | mechanism: shared scan must EMIT a bad-char flag bit (it has no flag plumbing today) |
| Second `.` | silently folded (`"1.2.3"` → 1.23 via `seen_dot \|=`) | NOT covered — a 2nd dot is still "`.`", so the letter of the design accepts it | **YES** — 2nd dot → `ok=false` |
| Empty / digitless (`""`, `"-"`, `"."`) | returns 0 silently | NOT covered | **YES** — at-least-one-digit required → else `ok=false` |
| Leading zeros | benign (digit-accumulate) | not addressed (fine) | only interacts with a digit-count overflow guard — count SIGNIFICANT digits |
| Overflow | uint64 accumulators WRAP silently at ≥20 digits; `nf` clamp `:1602` only guards the POW10 index, `frac_int` has already wrapped | "Overflow → D-106 range guard / ok=false, never silent-wrap" — bound + mechanism unstated | **YES** — pin bound = scaled \|mant\| ≤ 2⁶³−1 (aligns the type invariant + #3/#7 proven domains) AND the detection mechanism (significant-digit count ≥20 → `ok=false` BEFORE wrap; then 128-bit scale-adjust + compare > 2⁶³−1 → `ok=false`) |
| >8dp | n/a (binary keeps 19) | plan #5 row lists >8dp in the `(value,ok)` SURFACED set (reads as reject); sidecar says "round-via-#4 + flag, round-not-truncate" | **CONTRADICTION — operator decision #1** (see below) |
| Scientific notation | skipped → silent wrong value | rejected via the bad-char rule ✓ | covered once the flag bit exists |

**Front-end share is understated.** "Share the digit-scan, fork the scale tail" implies the scan is reusable as-is; it is not — it must be reworked to return `(int_part, frac_int, n_frac, flag_bits)` with flags OBSERVATIONAL (pure ORs; the accumulate is untouched): the binary wrapper discards flags (byte-identical output preserved — regression = the existing `fromstring_difftest` 297/0 + the frozen 16B golden), the decimal wrapper maps flags → `ok`. Without this stated, a coder either bolts `ok` on and changes binary semantics (golden break) or copies the scan (the Class-18 mirror S-19 exists to prevent).

**Sidecar accumulator-shape contradiction.** Sidecar #5 (written 2026-05-31) designs a UNIFIED accumulator (`mantissa = mantissa*10 + dig`); the live front-end (and S-19's share decision, 2026-06-09) is SPLIT `int_part`/`frac_int`. Both are correct math; only the split shape shares the live scan. Rewrite the sidecar to the split shape: decimal tail = `mant = int_part·10⁸ + frac_int·10^(8−n_frac)` in 128-bit (then bound-check), `n_frac>8` → divmod `10^(n_frac−8)` + #4. Note the >8dp rounding uses #4's GENERALIZED-divisor tie form (`2r` vs divisor, not vs SCALE) — currently named only in #7's stub; cross-ref it.

**Stale-prose (cosmetic):** "drops POW10_RECIP" (sidecar + plan parse row + hft :46) — `POW10_RECIP` no longer exists at HEAD (died in the Ship-A op-port). The true claim survives and is stronger: the live binary tail does a 128÷64 RUNTIME-divisor division (`:1603` — almost certainly `__udivti3` on the WS-parse path today); the decimal tail replaces it with one 64-bit table multiply. Update the prose.

---

## Q2 — per-site `ok=false` semantics: the table does not exist (the quorum-LOW confirmed)

Synthesis line 36: "#5 `ok=false` on LIVE fill path unspecified | LOW | CONFIRMED 2/3" — still true of plan v0.4. The plan enumerates parse SITES (#5 row, B3, B6, M1) but assigns failure BEHAVIOR to none. This is the gap with real capital shape: for a LIVE fill, the trade has already EXECUTED on the venue, so `ok=false` cannot mean "drop" (engine/venue position divergence — the same already-executed logic that drove D-173's runtime degrade arm). Required design addition — a per-class table, contract split: **the parser stays pure `(value, ok[, flags])`; the BEHAVIOR is owned by the call-site class** (one named handler per class, not per site). Proposed table (sites verified at HEAD):

| Class | Sites (verified) | Cadence | `ok=false` behavior (proposed) |
|---|---|---|---|
| 1. Tick ingest (WS producer) | `BinanceCrypto.hpp:744-745` | per-tick | DROP tick + sticky flag (S-17 word, `FailureModeRegistry` sister); persistent → existing WS-staleness machinery trips. Never a stalled retry on the producer |
| 2. Depth ingest | `BinanceDepth.hpp:163` | async | drop update + sticky flag (same shape as 1) |
| 3. **LIVE fill (`p`/`q`/`n`)** | `BinanceUserData.hpp:355-380` (fill price/qty + commission `n`, parsed as double today `:361`) → `CMD_WS_FILL` | per-fill, capital | **CANNOT drop — the trade executed.** Split by field: commission `n` malformed → book FLAGGED computed-fallback + halt-new-entries (extends the D-173 degrade arm verbatim — same canonical sister). price/qty malformed → REST re-fetch of that order (the sync-fill path `BinanceOrderAPI.hpp:533-537` / Reconcile already exists; venue is the authoritative record per D-106) → still bad → halt-new-entries + flag, exits keep managing (D-173 shape). **Operator decision #2: ratify this degrade shape** |
| 4. Boot reconcile / balance ingress | `Run.hpp:653` (`usdt_recovered`; FATAL-refuse shape already exists `:647`), `OrderManager.hpp:1424-1431`, `Reconcile.hpp:544-546` | boot / rare | boot: REFUSE to start (reuse the existing `:647` FATAL pattern — no safe default for a capital number). Runtime reconcile: skip-update + flag + halt-new-entries |
| 5. exchangeInfo filters | `BinanceOrderAPI.hpp:704-725` (today: fail → `loaded=0` → orders submit UNQUANTIZED silently) | boot | LIVE: refuse boot (can't quantize = guaranteed `-1013`s or worse — D-106 fail-loud; fixes the existing silent hole). Paper: flag + proceed |
| 6. Cfg parse (file + MANUAL_PARSER fee rows) | `cfg_assign_field` money rows; `fee_rate_maker/taker` bypass (S-18) | boot/reload | reject row + keep registry default + loud log; LIVE strict mode → boot-refuse (live-readiness gate exists). **Operator decision #3: default-and-warn vs refuse for LIVE cfg** |
| 7. Stamp wire parse | `tt::stamp_parse_field` (`StampBoundModelConstRegistry.hpp:103`) | model load | verification FAIL → hard refuse (existing stamp machinery; no new design) |
| 8. Backtest / replay recorded data | `BacktestSharded.hpp:84-85` (today FromDouble off `HistoricalTick` doubles — boundary is the recorder format), event-log replay | replay | HALT loud with file:offset — silent skip diverges replay==production (M5/determinism); corrupt recording is unusable, not skippable |
| 9. GUI typed input (S-11 typed path) | `SettingsPanel` money rows post-migration | UI | reject + keep old value + UI error; never reaches the engine |

**`(value, ok)` shape consequence:** classes need to DISCRIMINATE malformed vs overflow vs rounded->8dp (class 6 may accept a rounded human-typed value; class 3/5 must not). So the return wants `(value, flags)` with `ok = (flags & HARD_MASK)==0` — or keep `(value, ok)` + an out flag-word. Pin at the sidecar; this also resolves the Q1 plan-vs-sidecar >8dp contradiction PER CLASS instead of globally.

---

## Q3 — PCT pipeline (S-18): requirement pinned, mechanism not designed

Current code (verified): parse `v /= 100.0` in DOUBLE (`CfgFieldDispatch.hpp:76-77/:83`, cfg-file context only — `wire_context` exempt); save `v *= 100.0` + `%.2f` (`:195-196/:200-201`). S-18/B3 pin the requirement ("exact digit-shift pct, NO ÷100-in-double") — but sidecar #5 contains nothing: no PCT parameter, no >6dp rule, no egress twin. Required additions:

- **Ingress:** PCT = a `pow10_pre_shift = 2` parameter on the decimal scale tail — effective scale-adjust exponent `8 − n_frac − 2`; single rounding step (never parse-then-÷100 = double-rounding). `n_frac > 6` → divmod `10^(n_frac−6)` + #4 half-even + `rounded` flag (mirror of the >8dp rule).
- **Egress (the cfg_save twin B3 names):** `mant × 100` exact (128-bit; overflow impossible for in-range pct) then exact digit-emit. **Do NOT replicate `%.2f`** — 2dp-of-percent = 4dp-of-fraction, which truncates finer rows (e.g. a 0.075% fee) and breaks the very cfg-file→stored round-trip S-18 adds to the D-100 gate; emit full significant digits.
- **Wire context stays unscaled** (the `:76` `wire_context` exemption carries over to the decimal branch — say it, it's a silent-parity trap).
- S-14's unit normalization (registry percent-form defaults vs fraction-form manual-init) is sequencing-coupled: normalize units BEFORE the round-trip gate row is meaningful.

---

## Q4 — `to_binary` (decimal→binary, INGRESS per D-170)

**Status:** the mechanism is fully converged — in the WRONG artifact. Merge-scan item 6 (verified): `to_binary(d) = round₄(divmul_pow10-machinery on (|mant| << 64))`, dividend `< 2¹²⁷` stays inside the PROVEN D-140 `(M,S,N=127)` domain — "NO new reduce and NO new proof beyond a range note"; S-19 folds the share ("one `(q,r)` round core, five consumers"); S-21 pins branchless + single-source. The sidecar still says "trivial scaling pair, captured with #5's domain" (pre-dates the gate) — #5's domain is STRING PARSE; the casts are not in it. **The D-93 design artifact for the casts does not exist. Write the sidecar section; contents:**

- **Mechanism (adopt merge-scan item 6 verbatim):** `P = |mant| << 64` (mant ≤ 2⁶³−1 by the type invariant ⇒ `P ≤ 2¹²⁷ − 2⁶⁴ < 2¹²⁷` ✓ in-domain — state this range note); `(q,r) = divmul_pow10(P)`; round via #4 (divisor = 10⁸ = SCALE ⇒ #4 applies VERBATIM, no generalization needed this direction); sign abs-in/sign-out via `i128_abs`/`i128_cneg` mirroring #2 and the `fp2_from_double` sister (`FixedPointN.hpp:1372-1390`, verified — the named edge-handling shape: deterministic saturate, branchless sign).
- **Rounding mode — UNPINNED, operator decision #1 (shared with Q1's >8dp + Q5).** hft F-row (line 94) says it explicitly: "truncate vs RNE must be single-sourced — the rule itself is unpinned." Recommendation: **half-even via #4** for both casts — one convention engine-wide (D-105/D-128 uniformity), zero new machinery, tie-bias-free; the ~3-op cost over truncate is noise at 1/tick. Truncate is defensible (cheaper, bias 2⁻⁶⁵ avg — irrelevant to features) but breaks the one-rounding-convention story for no gain.
- **Saturation: provably UNREACHABLE this direction** — input |value| ≤ (2⁶³−1)/10⁸ ≈ 9.2×10¹⁰; binary max ≈ 9.2×10¹⁸; output magnitude < 2¹⁰¹ < 2¹²⁷. STATE the domain proof in the sidecar (a static comment + debug assert), rather than coding a dead saturate arm or leaving a reader to wonder. (S-21's "mask-select saturate" burden falls on `to_decimal`, which needs it — see Q5.)
- **Branchless:** divmul (~20cyc fixed) + #4 mask round + `i128_cneg` — fully branchless; no flag arm needed (no failure mode exists in-domain). ✓ H20.

---

## Q5 — `to_decimal` (binary→decimal, EGRESS per D-170)

Same artifact gap. Contents to pin (merge-scan item 6 + this audit's domain math):

- **Mechanism:** `round₄(umul_128x128_256(|b.v|, 10⁸) >> 64)` — consumes the S-19 extracted primitive (127-bit × 27-bit ≤ 154-bit product); `q` = product >> 64, `r` = low 64 bits.
- **Rounding:** same single mode as Q4 (operator decision #1). **Divisor nuance the sidecar must state:** this direction's divisor is 2⁶⁴, NOT SCALE — #4's literal `2r vs SCALE` compare is the WRONG constant here; the generalized form degenerates to a bit-test (`round_up = (r > 2⁶³) | ((r == 2⁶³) & (q&1))` — branchless, and `2r` must not be formed in 64-bit, it wraps). This is the same `2r`-vs-DIVISOR generalization #7's stub names; make #4's spec own it explicitly with its three divisor flavors (SCALE / runtime divisor / 2⁶⁴).
- **Saturation REQUIRED this direction:** binary values reach ~9.2×10¹⁸; decimal caps at ~9.2×10¹⁰ — overflow iff `q ≥ 2⁶³`. Branchless mask-select saturate-to-MAX + S-17 sticky-flag OR (`__atomic_fetch_or` sister), per the S-21 acceptance row. Egress inputs are price-domain stats (~10⁵) so the arm is `__builtin_expect`-rare/never — but a saturated THRESHOLD is a wrong gate decision, so the sticky flag is load-bearing, not decorative. Bound + flag stated in the sidecar.
- **Branchless:** ✓ by construction (mul + shift + mask round + mask saturate + `i128_cneg`).

---

## Q6 — placement + per-tick budget (D-170): DESIGN-OK

- **Egress lock verified** at decision log :1079 (D-170: thresholds binary→money at gate-build; `tick.price` money end-to-end; NO per-tick cross-radix cast in BG/SG) and the plan B4 row carries it. The S-21 A/B codegen oracle on `ExecutionCore_Tick` is the standing guard that no per-tick cast creeps into the cores.
- **Producer per-tick count verified at HEAD** (hft (b) section, re-checked against code this audit): today = binary `FromString` ×2 (`BinanceCrypto:744-745`, incl. the `:1603` runtime division) + `FPN_ToDouble` ×2 (`:759-760`) + `FPN_FromDouble` ×2 (`Async.hpp:179-180`, the D-102 detour) + `FPN_FromDouble(1.0)` every tick (`:261`). Ship B = decimal parse ×2 (CHEAPER tail) + decimal-ToDouble ×2 (display) + **1× `to_binary(price)`** for the EMA (D-122/D-124) ≈ 20-30cyc incl. half-even — vs the killed FromDouble pair (~30-60cyc) + killed binary-parse division + the F3 `FromDouble(1.0)` hoist (fold it; the ship touches that exact block). **Net ≤ 0 SURVIVES the actual divmul-shaped cast design — but the claim is conditional on Q4's mechanism being the one coded** (a naive `mant·2⁶⁴/10⁸` via `__udivti3` would be variable-latency on the ≤200ns fan_out). The no-`__udivti3` symbol check (already an acceptance line for #7) must cover the casts too — add them to its scope.
- **Volume:** `t.volume` re-types to money and is NOT cast per-tick (flow-feature ingress is slow-cadence, B4 cluster) — worth one sidecar sentence so nobody "symmetrizes" a second per-tick cast in.
- **Twin-site naming (M5):** both `ema_price` impls (`Async.hpp:261-266` + `PortfolioController.hpp:931-935`) + the backtest twin take the IDENTICAL single-source `to_binary` — B6 says it; the cast sidecar section should list the call sites.

---

## Q7 — determinism statement: pinned at decision level, absent at design level

D-107 (log :704) pins the constraint: casts are single-source named fns, "the decimal→binary feature cast is byte-DETERMINISTIC (train-serve M5)". Both casts are pure integer (divmul / umul + shift + mask round) ⇒ trivially byte-deterministic + locale-free — but per the audit question's own standard, **the design must SAY it**: add to the cast sidecar section (a) byte-deterministic cross-run/cross-binary/cross-locale (rides the `.E.0.1` net — no locale-sensitive call exists in either body), (b) explicit **D-100 oracle rows for both casts** (the acceptance text says "oracle for #2-#6"; the casts are only implicitly inside "#5 parse/casts" — make them explicit rows: dec→bin vs `Decimal(mant)·2⁶⁴/10⁸` rounded per the pinned mode incl. ties, bin→dec inverse incl. the saturate boundary), (c) M5 note that ema_price-derived features ride these casts ⇒ the cast is part of the train-serve surface (retrain epoch already covers it per D-100).

---

## Required before code (punch list)

**Operator decisions (3):**
1. **Cast + >8dp rounding mode** — recommend half-even via #4 everywhere (one convention; per-class flags let cfg accept-rounded while venue classes treat `rounded` as hard).
2. **LIVE-fill `ok=false` degrade shape** — ratify the class-3 row (commission → D-173-style flagged computed-fallback + halt-entries; p/q → REST re-fetch → halt-entries).
3. **LIVE cfg-parse failure** — default-and-warn vs boot-refuse in live mode (class 6).

**Sidecar additions (mechanical, no new decisions beyond the 3 above):**
4. Rewrite #5 to the SPLIT-accumulator front-end shape (S-19 share) + the flag-emitting front-end contract + binary byte-identity regression note (difftest + golden).
5. Pin the 6 unpinned #5 edges (sign `+`, second dot, digitless, overflow bound 2⁶³−1 + pre-wrap detection mechanism, >8dp per-class flag, scientific-via-badchar).
6. Add the per-class `ok=false` table (Q2) + the `(value, flags)` return-shape decision.
7. Add the PCT section (pre-shift ingress, exact ×100 full-digit egress, wire_context exemption carry-over).
8. **Write the cast pair section** — Q4/Q5 mechanisms (merge-scan item 6 verbatim + range notes + the divisor-2⁶⁴ tie nuance into #4's spec + to_decimal saturate/sticky-flag + determinism/oracle/M5 statements + call-site list + no-`__udivti3` scope extension).
9. Cosmetic: fix the stale "POW10_RECIP" prose (plan parse row + sidecar + hft echo).

---

## Appendix — code verified at HEAD `0e48150`

`FixedPointN.hpp:1579-1607` (live FromString front-end; `+` accept, garbage-skip, dot-fold, wrap, `:1603` runtime division), `:394-420` (generic, word-loop), `:1372-1395` (`fp2_from_double/to_double` sister shapes), `:1336` context (udiv_q64 binary widening per plan). `Async.hpp:134-191` (fan_out, `:179-180` FromDouble pair), `:261-266` (EMA block + `FromDouble(1.0)`). `BinanceCrypto.hpp:744-760` (parse + ToDouble pair). `BinanceUserData.hpp:355-380` (fill `n`/`N` double parse). `Reconcile.hpp:60-66/:540-550` (double fields/parse). `Run.hpp:645-656` (usdt_recovered + existing FATAL-refuse shape). `BinanceOrderAPI.hpp:70-82` (SymbolFilters doubles), `:510-514/:555-559` (round_qty + `%.*f`), `:525-545` (REST sync-fill doubles), `:704-725` (exchangeInfo load; fail ⇒ `loaded=0` silent-unquantized). `BacktestSharded.hpp:78-92` (FromDouble off HistoricalTick). `CfgFieldDispatch.hpp:49/:76-83/:195-201/:241` (PCT ÷100/×100 in double; wire_context exemption). Decision log :658 (D-103), :704 (D-107), :775 (D-122), :783 (D-124), :1079 (D-170), :1091 (D-173). Synthesis :36 (quorum LOW), :63 (S-14), :66 (S-17), :67 (S-18), :68 (S-19), :70 (S-21). Merge-scan :38/:67-69 (item 6 composition). hft-audit :14/:42-55/:63-66/:94 (net ≤0 count; unpinned rounding rule; F3/F4/F5).
