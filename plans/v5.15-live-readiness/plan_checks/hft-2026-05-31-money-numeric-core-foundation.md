---
type: audit-report
audit: /hft-audit
scope: module:numeric-core (latency lens on the decimal money type)
target_plan: plans/v5.15-live-readiness/subplans/2026-05-30-v5.15.5.F.4d.1.E-money-numeric-core-foundation.md
date: 2026-05-31
auditor: Layer-2 /hft-audit subagent (read-only)
engine_head: 3f415a0
verdict: YELLOW — decision sound; ONE load-bearing latency claim is FALSE-as-written + 2 omitted per-tick mul surfaces
related_backlog_exclusions: [#27, #28, #92, #7, #12, #58, #59]
---

# /hft-audit — money-numeric-core foundation (decimal `FixedPoint<10,8>`) — latency lens

**Verdict: YELLOW.** The decimal decision (D-97/D-99) and the *steady-state* "hot path UNTOUCHED" claim are **correct and code-verified**. But the plan's recurring justification — *"decimal mul = same schoolbook-shift cost"* (frontmatter `hot_path:`, § Blast-radius hot-path line :159, architecture line :109) — is **factually wrong for the notional path** and the plan **omits two per-tick money-mul surfaces** from its blast-radius inventory. These are bounded (none breach H8 at steady state), but the claim as written is a hand-wave the "audit hand-waves when 'branch is fine' surfaces" rule requires flagging. Not a ship-blocker; a **plan-amendment + a designed mitigation** before coding.

This audit EXCLUDES `MASTER_SORTED_BACKLOG.md` findings #27/#28/#92/#7/#12/#58/#59 (the existing hot-path-branch, slow-divide, FP64-carry, aliasing, and truncation-bias items) — all distinct from the decimal-reduce cost analyzed here.

---

## What the plan got RIGHT (verified, not assumed)

- **Steady-state ≤500ns path is compares-only.** `ExecutionCore.hpp:355-478` (inlined BG_Evaluate + SG_Evaluate) is entirely `FPN_LessThan` / `FPN_GreaterThan` / `FPN_GreaterThanOrEqual` / `FPN_Max` / `FPN_LessThanOrEqual` + mask ops. **Zero muls in steady state.** Comparisons are radix-agnostic word-compares (`FPN_NWordGe`-style) → **bytewise-identical cost in decimal**. The "500ns steady path does money COMPARES not mul/div" claim is TRUE. (H7/H20 branchless dispatch preserved; the radix split is `if constexpr` compile-time, not a runtime data-dependent branch — H20-clean.)
- **The 3 hot money-muls ARE rare-entry-gated.** `ExecutionCore.hpp:543/549/570` sit inside `if (__builtin_expect(can_enter | can_exit_a | can_exit_b, 0))` (:504, expect-0 = cold) AND a nested `if (entry_a_pushed)` (:539). They fire only when an entry event actually queues — the "<1% ticks, rare-entry-branch" claim is TRUE.
- **H11 constant-iter preserved.** `FPN_Mul` (:583) and `FPN_DivNoAssert` (:687) are fixed-trip (`N²` unrolled / `N*64` fixed loop) and branchless internally; the decimal reduce changes the *reduce op*, not the iteration structure.

---

## Top findings (latency lens)

### 1. [HIGH] "Decimal mul = same schoolbook-shift cost" is FALSE for the notional (`u128`) path — it lowers to a 128-bit division LIBCALL, not a fixed-cost reciprocal-multiply.
**Where claimed:** plan frontmatter `hot_path:` + architecture line :109 + blast-radius :159.
**Mechanical truth (empirically verified, GCC 16.1.1 `-O2`):**
- **Binary `<2,64>` reduce** (`FPN_Mul` :610-622): product is `__uint128_t` (2N=2 words at F=64), reduce `>>FRAC_WORDS` with `FRAC_WORDS = 64/64 = 1` → `result.w[i] = p[FW+i]` (:621) = **a word-index SELECT. Zero instructions. Literally free.**
- **Decimal `<10,8>` reduce on the notional path** (`price×qty`, which the plan ITSELF mandates uses an `int128` double-width intermediate, line :109): `__uint128_t / 10^8` → GCC emits **`call __udivti3@PLT`** — a 128-bit unsigned-division **libcall** (~40-100+ cycles, non-inlined, internal branches, breaks the straight-line `#pragma unroll` model). NOT a branchless reciprocal-multiply.
- The reciprocal-multiply (`movabsq` magic + `mulq` + `shrq`, ~5-6cyc branchless) is emitted **only** for the `uint64_t / 10^8` case. The reduce is **type-driven**: because the intermediate TYPE is `u128`, the libcall is emitted even when the runtime value would fit u64 (compiler cannot prove it).
- The 3 hot muls (`price × tp_pct`) overflow u64 at high notional (e.g. `1e6` price × `0.05` pct stored = `5e20 > 1.8e19` u64-max) → they too require the u128 intermediate → libcall.

**Why it matters:** at steady state, irrelevant (no muls). But entries **cluster** (a regime flip fires entries across cores in the same window) → the entry-path libcall lands in the **p99.99 ≤2μs** tail, not the amortized p50. A `__udivti3` per leg per entry (up to 4 muls: live_tp/live_sl/live_tp_b/+notional) is bounded but is a **real, measurable, non-zero cost the plan's "same cost" framing erases**. Per H8, the entry path is still inside hot-path budget — this is a **mischaracterization, not a budget breach**.
**Disposition:** correct the plan claim to the honest form ("decimal notional mul = a 128-bit division, ~40-100cyc libcall vs binary's free word-select; bounded by the rare-entry branch + slow-path budget"). **Design a mitigation** at code-time: (a) a custom branchless `div_by_pow10_u128` (Granlund-Montgomery 128-bit reciprocal — known fixed-cost, no libcall), OR (b) keep the SCALE small enough that the post-mul intermediate fits u64 where provable, OR (c) accept the libcall explicitly with a budget note. This is exactly the `new-fn design-audit (D-93)` the plan defers to code-time — flag it as REQUIRED for `decimal-Mul`, not optional.

### 2. [HIGH] Two per-tick money-mul surfaces are MISSING from the blast-radius inventory — producer EMA (`Async.hpp:263-264`) and producer TP-distance (`Async.hpp:854`).
**Where:** `CoreFrameworks/EngineSharded/Async.hpp:263-264` — `FPN_Mul(ema_price, ema_alpha)` + `FPN_Mul(t.price, one_minus_alpha))`, run **on EVERY tick on the producer fan_out path** (≤200ns p99 budget). `t.price` and `ema_price` are price-derived. Plus `:854` `FPN_Mul(tp_dist_a, tp2_mult_eff)`.
**Why it matters:** the plan's blast-radius table (§ Blast radius, the 9-row inventory) lists parse / accounting / stamp / persistence / boundary — but **NOT the producer EMA**. If `ema_price` is classed as money `<10,8>`, this becomes **2× `u128/10^8` libcalls per tick on the producer path** = a per-tick regression that the "hot path UNTOUCHED" claim never addresses (the plan's hot-path analysis is ExecutionCore-only; the producer fan_out is a separate per-tick path with its own budget). This is also a **D-103 boundary the plan omits**: `ema_price` is seeded directly from `t.price` (money, :265) yet feeds ML features (binary; comment :255-257 "Used by ML feature pack"). Which domain owns `ema_price` is undecided in the plan — and the answer determines whether `Async.hpp:263-264` is a 0-cost binary blend or a 2-libcall-per-tick money blend.
**Disposition:** add `Async.hpp:263-264` + `:854` to the blast-radius inventory; **decide the `ema_price` domain explicitly** (recommend: `ema_price` is a *feature* → stays binary `<2,64>` → the blend stays free, and the `t.price → ema_price` seed becomes a named D-103 money→binary cast at :265). Enumerate per the O-1 strong-typing — the compiler will force this boundary, but the plan should pre-decide it so the producer path stays libcall-free.

### 3. [MED] Slow-path / accounting notional muls inherit the u128 libcall at every site (~40+ sites) — bounded by the ≤100μs budget but the plan's "same cost" claim is wrong here too.
**Where:** `OrderManager.hpp:1186` (`exit_notional = FPN_Mul(fill_price, qty_snap)`) + `:1188` fee + `Portfolio.hpp:200/201/390/429/443` (gross/fee/pnl/value muls) + `ControllerEventLoop.hpp` (25 `FPN_Mul`) + `PortfolioController.hpp` (56 `FPN_Mul`/`Div`, incl. sizing-divide :1215). Every `price×qty` notional → `u128/10^8` libcall.
**Why it matters:** the slow-path rebuild cycle has a ≤100μs p99 budget with comfortable headroom, so dozens of `__udivti3` calls (each ~40-100cyc → ~tens of ns) are **tolerable** — NOT a budget breach. But (a) the `PortfolioController.hpp:1215` **sizing-DIVIDE** is already a `(n·10^8)/d` decimal div (the plan's Div path :109) which is the EXISTING slow bit-by-bit `FPN_DivNoAssert` (:687, `N*64` iterations — backlog #92) PLUS now a scale-up; and (b) the plan's blanket "decimal mul = same schoolbook-shift cost" is contradicted at 40+ sites. Verify the aggregate slow-path cycle stays ≤100μs with the libcalls (a `bench` pass at code-time, not an assumption).
**Disposition:** document the slow-path muls honestly; add a slow-path-cycle latency-bench acceptance criterion (the plan's acceptance list has no slow-path p99 check — only `calls_graph_diff` GREEN + determinism gates). Consider routing notional muls through a shared `divmul_pow10` helper (single-source the reduce → one place to optimize, composes with the canonical-rounding-mode D-105 routing the plan already wants).

### 4. [LOW] `FixedPoint64` absorption inherits backlog #7 (FP64 mul carry bug) — re-verify it's designed out, not carried.
**Where:** plan absorbs `FixedPoint64.hpp` into `FixedPoint<2,64>` native-storage policy (line :51-52). Backlog #7 = "FP64 Multiplication Carry-Propagation Bug" + #53 (FP64 192-bit div overflow) + #69 (FP64 overflow truncation). The plan reuses the **`FPN_Mul` certified body** (:583, which DOES carry-propagate correctly :597-607), so absorbing FP64 *into* the FPN body is the right move — but the plan should explicitly state the FP64 native-128 path is REPLACED by the FPN word-loop (not aliased alongside it), closing #7/#53/#69 structurally. (Cross-ref backlog #12: the `__uint128_t*` strict-aliasing UB in FixedPointN — confirm the unified core doesn't reintroduce the pun.)
**Disposition:** add an explicit acceptance line: "FP64 `FP64_Mul`/`FP64_Div` bodies DELETED (not aliased); the `<2,64>` native-storage policy routes through the carry-correct FPN word-loop → backlog #7/#53/#69 closed." Already implied by "absorbed (deleted)" (:212) — make the carry-correctness explicit.

---

## Blocking gaps (must resolve before coding, per consult-before-coding)

- **G1 (blocks the latency claim):** the `decimal-Mul` `new-fn design-audit` (D-93) must produce a **concrete reduce lowering** (custom 128-bit reciprocal `divmul_pow10` vs accept-libcall-with-budget) BEFORE the "hot path UNTOUCHED" claim can stand. Right now the claim rests on an unverified "same cost" assertion that is empirically false for the u128 path.
- **G2 (blocks blast-radius completeness):** the `ema_price` domain (money vs feature) must be DECIDED and `Async.hpp:263-264`/`:854` added to the inventory — otherwise the producer per-tick path is an unaudited regression surface (the plan's `enumerate_set_before_categorical_claim` discipline is unsatisfied for the producer path).
- **G3 (acceptance gap):** add a **slow-path-cycle latency bench** (≤100μs p99) + a **producer-fan_out bench** (≤200ns p99) to the acceptance criteria. The current list verifies determinism + `calls_graph_diff` but NO p99 budget re-check after the type change — and H8 is a ship-blocker. `calls_graph_diff` GREEN proves call-graph shape, NOT latency.

None of these are RED (the decision is sound, the steady path is genuinely untouched, all costs are bounded within their path budgets). They are the difference between a hand-waved "same cost" and a measured, mitigated, honestly-documented latency profile — which the heavier-default-audit-posture-for-capital rule (D-77) requires for a money-bearing HIGH-RISK ship.
