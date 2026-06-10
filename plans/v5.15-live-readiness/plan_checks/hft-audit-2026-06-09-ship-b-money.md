# /hft-audit — Ship-B (decimal money) latency-path impact — 2026-06-09

**Scope:** `scoped` — Ship-B REMAINING work of `subplans/2026-05-30-v5.15.5.F.4d.1.E-money-numeric-core-foundation.md` (v0.3), latency-path focus areas (a)-(g). Engine HEAD `0e48150` (v5.15.5.F.4d.1.E.0.8). DECIDED items (hot_path frontmatter claim mechanics, divmul D-140 proof) taken as settled; this audit VERIFIES them against HEAD code and audits the remaining seams.
**Exclusions honored:** `GEMINI_FINDINGS/MASTER_SORTED_BACKLOG.md` (98 + phases 11-17) loaded; known items NOT re-reported — relevant-adjacent ones listed at bottom.
**Method:** direct code reads + compile probe (`g++ -O2` offsetof/sizeof at HEAD) + `rg` sweeps (`__udivti3`, native `/`/`%` on `.v`, FromDouble sites, cadence context).

---

## Per-area verdicts

| Area | Verdict |
|---|---|
| (a) hot-path UNTOUCHED-at-per-tick-cost claim | **VERIFIED, 1 load-bearing condition (F1) + B4 latency ruling (F2)** |
| (b) D-103 cast placement / producer per-tick ops | **PASS — net per-tick ops ≤ today (likely negative delta)** |
| (c) decimal reduce + no `__udivti3` | **PASS — with one design gap on general Div (F5)** |
| (d) seqlock GateParameters / ParameterSlot | **PASS — byte-identical sizes** |
| (e) SPSC Tick ring layout | **PASS — unchanged 64B** |
| (f) branchless `to_binary()`/`to_decimal()` | **CONDITIONAL — branchless-by-construction available; not yet an acceptance criterion (F7)** |
| (g) cache layout / ExecutionCore asserts | **PASS — asserts GREEN at HEAD; one doc-drift residue (F8)** |

---

## (a) The "hot path UNTOUCHED at per-tick cost" claim — verified against HEAD

**Steady path per tick** (`ExecutionCore_Tick_Impl`): `BG_Evaluate` (`GateParameters.hpp:171-184`) = 2 price compares + 1 volume compare + masks; SG leg A (`ExecutionCore.hpp:420-431`) = `FPN_Max` ×2 + `FPN_GreaterThanOrEqual`/`FPN_LessThanOrEqual` on `tick.price`; leg B branch-gated (`:443-463`). Every FPN operand here is **money-domain** (tick.price/volume, bg thresholds, TP/SL, ratchets) → under the plan these all become `FixedPoint<10,8>`. So the per-tick path **is type-touched; cost-neutrality rests on compare-cost identity**:

- At HEAD: `FPN_LessThanOrEqual<64>` = `a.v <= b.v` (`FixedPointN.hpp:1509`), `fp2_max` = scalar ternary→CMOV on register-resident values (`:1330`). Bare `__int128` compares.
- A scaled signed integer compare is **radix-agnostic and order-preserving** → `FixedPoint<10,8>` compare CAN be the byte-identical machine op. CONFIRMED: `<10,8>` compare cost == `<2,64>` compare cost — **provided the decimal bodies are written that way** (see F1).

**The 3 hot money-muls** (`ExecutionCore.hpp:543/549/570`): confirmed inside `if (__builtin_expect(can_enter | can_exit_a | can_exit_b, 0))` (`:504`) — rare entry/exit branch, <1% ticks. Decimal mul = same 128×128→256 product + divmul_pow10 reduce (~+10-15cyc vs binary `>>64`) on the rare branch only → steady p99 unaffected; entry-tick delta ≈ +10-15ns ≪ the 2µs p99.99 row. Claim **stands**.

**Types under the plan:** `tick.price`/`tick.volume` → `FixedPoint<10,8>` (D-102 ring carry-through); `live_tp`/`live_sl`/`entry_price` + all 10 `GateParameters` FPN fields (`bg_price_threshold`, `bg_volume_threshold`, `sg_take_profit_price`, `sg_stop_loss_price`, `tp_pct`, `sl_pct`, `tp_pct_b`, `trade_size`, `ratchet_sl`, `ratchet_tp` — `GateParameters.hpp:88-136`) → decimal money cohort. All 16B → no layout movement.

### F1 [MED·acceptance-gap] Decimal compare/max bodies are Ship-B-NEW — pin their codegen shape
`FixedPoint<RADIX,FRAC>` is **declaration-only** at HEAD (`FixedPointN.hpp:82`); only `<2,64>` is specialized. There is no generic body for `<10,8>` to fall back to (good — no word-loop hazard), but it means EVERY decimal op is fresh code and the hot-path-neutrality claim is only as true as those bodies. **Amendment:** add an acceptance row — "decimal compare/min/max/IsZero are bare single-`.v`-compare bodies (the `fp2_*` shapes); hot-path codegen verified via the A.5-style A/B objdump oracle on `ExecutionCore_Tick_Impl` pre/post." Cheap, reuses the Ship-A.5 oracle apparatus, and converts the claim from asserted to gated (H7/H8; DESIGN_PHILOSOPHY §4 — mispredict/byte-cost anchors).

### F2 [HIGH·design-decision] B4 price-domain fork: only option (i) is latency-compatible — rule it on the budget axis
Plan B4 leaves OPEN: (i) price-stats stay binary + thresholds cast to money at gate-build (egress, slow cadence) vs (ii) `tick.price` casts to binary at compare. **Option (ii) puts a per-tick fixed-cost cast (~20-25cyc) ×2-4 compare operands INSIDE the ≤500ns steady path** — strictly worse than (i)'s slow-cadence egress casts (≤100µs budget, trivially absorbed), and it would re-introduce a per-tick inexact dec→bin conversion on the SAME value every tick (determinism-noise surface). Audit ruling: **resolve B4 = option (i)** before Ship-B code; record hot-path budget as the deciding axis. (Latency-paths discipline: per-tick > per-event > cadence — the cast belongs at the lowest-cadence seam, which is gate-build.)

---

## (b) D-103 cast placement — producer per-tick op count

**Today at HEAD** (per-tick, producer thread): `BinanceCrypto.hpp:744-745` `FPN_FromString` (binary; digit-accumulate + POW10 scaling) → `:759-760` `FPN_ToDouble` ×2 (TUI doubles) → fan_out `Async.hpp:179-180` `FPN_FromDouble` ×2 **re-derive from the lossy double** (D-102 confirmed live — the exact parsed FPN is dropped, the ring gets the double round-trip). EMA block `:261-266`: `FPN_Sub` + `FPN_FromDouble(1.0)` + `FPN_Mul` ×2 + `FPN_Add` + `FPN_IsZero` (binary feature domain — stays).

**Under Ship B** (D-102/D-122/D-124): parse-to-decimal #5 (digit-accumulate into the 10⁸ int — CHEAPER than today's binary FromString, no POW10_RECIP apparatus) → decimal carried into the `Tick` ring (the `:179-180` FromDouble pair DELETED) → **+1 per-tick op: `to_binary(price)`** feeding the binary EMA (fixed-cost mul+shift ≈ 20-25cyc ≈ 5-8ns). TUI doubles derive from decimal at the same site (display-only, H4-exempt).

**Count:** removed ≈ 2× FromDouble (~30-60cyc) + binary-parse scaling; added ≈ 1× to_binary (~20-25cyc) + cheaper parse. **Net per-tick delta ≤ 0.** Producer budget (<100ns p50 / ≤200ns p99 per fan_out) — **PASS with margin**.

**Egress sweep:** gate-build cluster `StrategyParameters.hpp:244-334` + `PortfolioController.hpp:1021-1023/838-855/1554-1566` = slow cadence ✓. Checked for accidentally-per-tick casts: `Async.hpp:357` (cfg hot-reload block) + `:383` `mtm_price` FromDouble (slow-path cadence block) + `:854-865` (drainer, per-event) + `:246-247` (GUI drag, rare branch) — **none on the per-tick steady path**.

### F3 [LOW·optimization] Hoist the per-tick `FPN_FromDouble<F>(1.0)` (`Async.hpp:261`)
Existing waste — a full double-decompose every tick to make the constant 1.0. Ship B touches this exact block (EMA ingress cast); fold the hoist in (constant or precomputed `one_minus_alpha` alongside `ema_alpha`).

### F4 [LOW·enumeration] `Async.hpp:246-247` GUI-drag writes money (`Position.take_profit_price/stop_loss_price`) via `FPN_FromDouble` — not in the D-103 ~12-site inventory
O-1 strong-typing red-builds it anyway (self-surfacing), and it's a rare branch (drag-just-happened) so latency-irrelevant — but the D-103 enumeration claims completeness; add the site (operator-input double→decimal boundary, same family as B-γ GUI display boundary but in the WRITE direction).

---

## (c) Decimal reduce on slow-path fee/sizing muls — `__udivti3` audit

- `rg`/grep over `FixedPoint/` + `CoreFrameworks/`: **zero `__udivti3` references, zero native `/` or `%` on `.v`** — all division routes through `udiv_q64` (`FixedPointN.hpp:1336`), a **fixed-128-trip** MSB-first long division with CMOV conditional-subtract (fixed-trip branch = 100% predicted; H11 constant-iter ✓).
- The mul-reduce (`divmul_pow10`, D-140 PROVEN) is a constexpr reciprocal multiply+shift — fixed-cost ~20cyc, constant-time, no libcall. Fee/sizing muls live at drainer/slow cadence (`OrderManager.hpp:1160-1210`, `ControllerEventLoop.hpp:1923/:1967`, `Portfolio.hpp:205-207`, `EngineCommon.hpp:156-159` et al. per plan B2) → ≤100µs slow budget absorbs it ~5000× over. **PASS.**

### F5 [MED·design-gap] General decimal **Div** has no Ship-B design artifact — and the certified core hardcodes the binary widening
Plan §117 names decimal Div = `(n·10⁸)/d` (runtime divisor — e.g., sizing-divide `PortfolioController.hpp:1215`; #3's reciprocal trick does NOT apply, the divisor isn't constant). `udiv_q64` encodes the dividend widening as `rem_hi = a_mag >> 64, rem_lo = a_mag << 64` (`:1337`) — i.e., `a·2⁶⁴`, the BINARY scale. Decimal needs `a·10⁸` (≤155-bit) as the 256-bit dividend — a parameterized-widening variant of the same certified loop (small, mechanical), **not** in the #1-#6 design set. Hazard if unspecified: a naive `a.v * SCALE / b.v` both overflows 128b AND emits `__udivti3` (variable-latency libcall — the exact thing H1/D-140 killed for the reduce). Slow-path-only cost (~150-300cyc ≪ 100µs) so this is a **correctness/design completeness** item, not a budget one. **Amendment:** add decimal-Div to the new-function design sidecar + an acceptance line "no native `__int128` division anywhere in `<10,8>` ops (objdump/no-`__udivti3` check)".

---

## (d) Seqlock GateParameters under decimal — sizes verified by compile probe at HEAD

```
sizeof(GateParameters<64>)              = 192   (10×16B FPN + flags/pad + param_max_age_ticks, alignas(64))
sizeof(ParameterSlot<GateParameters<64>>) = 448  (seq + 2×192 buffers + pad)
```
All 10 FPN fields re-type to `FixedPoint<10,8>` = 16B each → **sizeof/copy/seqlock protocol byte-identical**; the cached-params fast path (1 acquire-load + 1 compare, `ExecutionCore.hpp:111-132`) unaffected; the `:112` "192-byte memcpy" comment is in sync at HEAD. **PASS.** (Known ParameterSlot fence/pad findings — backlog #22/#24/phase-14 #124 — pre-existing, unchanged by a same-size type swap; excluded.)

---

## (e) SPSC Tick ring layout — probe-verified

`sizeof(Tick<64>) = 64, alignof = 64` (16+16 price/volume + 8+8 ts/seq + 1+7 flag/pad = 56 → alignas(64)). Decimal price+volume stay 2×16B → **ring slot layout, density, and per-push copy cost unchanged**. **PASS.**

### F6 [LOW·type-design] The `<F>` template parameter on money-carrying structs goes vestigial
`Tick<F>`/`TradeEvent<F>`/`GateParameters<F>`/`ExecutionCore<F>` are parameterized on the BINARY F while their members become `FixedPoint<10,8>` under option (i). Latency-neutral, but the plan should name the disposition (keep `<F>` for the residual binary members / re-parameterize / de-template) BEFORE the mechanical re-type — this is the B4 note ("governs `RollingStats<F>`/`GateParameters<F>`") extended to Tick/TradeEvent/ExecutionCore.

---

## (f) Branchless casts — `to_binary()`/`to_decimal()`

Construction check: `to_binary` = `v_dec·2⁶⁴ / 10⁸` → 128×128→256 product (the #2 hoisted primitive) + divmul_pow10-family reduce; `to_decimal` = `v_bin·10⁸ >> 64` → product + high-end grab. **Both compose ALREADY-EXISTING branchless fixed-cost primitives** (~20-25cyc) — branchless is achievable by construction, and the saturate idiom to copy is the mask-derived one in `fp2_mul`/`fp2_div` (`:1300-1356` — no compile-constant for GCC to convert into a conditional load).

### F7 [MED·acceptance-gap] The plan requires casts "named, deterministic" — never **branchless**
The ingress cast is **per-tick** (producer EMA, area b). If D-106 flag-loud validation lands in it as a data-dependent branch, that's a per-tick mispredict surface (30-100ns class, DESIGN_PHILOSOPHY §4). **Amendment:** acceptance row — "`to_binary`/`to_decimal` are branchless fixed-cost (mask-select saturate; any flag-loud is `__builtin_expect`-rare or a mask-accumulated counter, H20-sanctioned error-path only)". Also pin the dec→bin **rounding rule** once (10⁻⁸ has no exact binary form — truncate vs RNE must be single-sourced; B6's two-`ema_price`-impls/M5 note covers the parity side, the rule itself is unpinned). #5 `FromString` `(value, ok)` validation branches sit at the WS-parse boundary = same H20 error-path class as the existing `fp2_from_double` guard (`:1381`) — acceptable as long as the ok-path stays straight-line.

---

## (g) Cache layout — ExecutionCore asserts, probe-verified at HEAD

```
offsetof: live_tp=16  live_sl=32  entry_price=64  entry_price_b=80  permission=128
```
Line 0 = flags(2) + 14 pad (6 explicit + **8 implicit** — `alignof(__int128)=16` bumps live_tp from 8→16) + live_tp(16-32) + live_sl(32-48) + pad(48-64). `:176` assert `offsetof(live_sl)+sizeof(FPN_Binary<64>) = 48 ≤ 64` ✓; `permission%64==0` ✓; `entry_price` on line 1 — the comment's claim HOLDS. Money fields stay 16B at Ship B → **zero layout movement; asserts remain GREEN as-written**. **PASS.**

### F8 [LOW·doc-drift] `ExecutionCore.hpp:64-91` layout comments still describe the 24B world
"2 byte flags + 6 pad + 24 (live_tp) + 24 (live_sl) + 8 pad = 64B" / "24B at offset 8" / "24B at offset 32" — stale since the E.0.7 flip (the `7f1704e` stale-comment cohort caught RollingStats but missed this block); actuals are 16B at offsets 16/32 with implicit alignment padding (8-16, 56-64). The plan's R4 ("`_pad_hot`/`_pad_line0` re-derive") was effectively satisfied by implicit alignof padding, not re-derivation — fine functionally, but re-derive the comments (and optionally make the pads explicit per the H12-adjacent explicit-pad house style) during the Ship-B touch of these exact lines. Cosmetic sibling: when `live_sl` re-types, the `:176` assert's `sizeof(FPN_Binary<64>)` operand should become the money type (same 16 — semantic correctness only).

---

## Known/excluded (backlog overlap, NOT re-reported)
- #26 kill-switch torn multi-word balance read (producer reads drainer-written balance) — persists as a 16B/2-half tear under decimal; neither worsened nor fixed by Ship B.
- #27/#28 hot-path `active_b`/BuyGate branch findings — pre-existing; Ship B adds no new branch.
- #2/#119 BuyGate F>64 multi-word compare bug/duplication — mooted by the 16B single-`.v` core; the EC↔GateParameters gate-eval duplication (#122) still means **both** copies re-type at Ship B (keep in lockstep).
- #22/#24/#124 ParameterSlot fence/pad — orthogonal to the same-size type swap.
- Phase-14 #127 unroll-pragma i-cache — the shed-arbitrary-width 16B cores no longer word-loop; decimal inherits the non-loop shapes.

## Synthesis
**Combined: YELLOW (no architecture-killer; the hot-path claim VERIFIES against HEAD).** The per-tick steady path is money-COMPARES only (+2 branchless maxes), and a scaled-int decimal compare is machine-identical to binary — but that identity is currently an *implication*, not a *gate*: F1+F7 convert it into acceptance criteria, F2 closes the one OPEN fork (B4) on the latency axis, F5 fills the only real design hole (general decimal Div). Producer per-tick op count goes DOWN under D-102/D-122. Seqlock/ring/cache surfaces are byte-stable under the 16B→16B re-type. No `__udivti3` exists today and none is implied by the planned ops — keep it that way with the F5 acceptance line.

*Auditor: /hft-audit (Layer-2 single-pass; no subagents). Probe: g++ -std=c++17 -O2 offsetof/sizeof at HEAD 0e48150.*
