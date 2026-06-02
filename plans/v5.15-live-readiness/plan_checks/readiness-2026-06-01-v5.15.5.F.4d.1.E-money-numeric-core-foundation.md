---
type: plan-readiness-report
plan: subplans/2026-05-30-v5.15.5.F.4d.1.E-money-numeric-core-foundation.md (v0.2, step-6-fold + step-7-amended)
ship: "#11 numeric-foundation unification — Ship A (16B binary-core compaction)"
audit_date: 2026-06-01
audit_scope: Ship A ONLY (the 16B two's-complement compaction); Ship B findings noted as DEFERRED
audit_tier: HIGH-RISK (capital-bearing numeric core; heavier-default D-77)
verdict: **GREEN-SHIP-A** — ready for Ship A coding (16B compaction); Ship B blockers documented & deferred
predecessor_context: Phase 1 PROVEN (D-140: `divmul_pow10` exact); mechanical-floor CLEAN (check_session_docs.sh all GREEN); 9-audit gate + 12-pillar blindspot re-fire + amendments folded; decision SOUND (verified 3 ways)
---

# /readiness report — v5.15.5.F.4d.1.E Ship A — 2026-06-01

> **🔧 RECEIVER ADDENDUM (2026-06-01, `/accept-handoff` Stage-6 cross-check) — corrects the R3 row + the PORTFOLIO "GAP".**
>
> The Layer-2 pass flagged `PORTFOLIO_SNAPSHOT_VERSION` as "missing" — that was a grep miss; it exists as `#define PORTFOLIO_SNAPSHOT_VERSION 5` (`Portfolio.hpp:530`). Verifying it surfaced a REAL finding that the row-5 verdict (and the Layer-2 "(was 11/7/4)" assumption) **inverted**:
>
> **R3 version-bump targets are STALE at HEAD — all three already sit at the plan's literal "bump→" values.** Exact `#define`s at HEAD:
> - `CONTROLLER_SNAPSHOT_VERSION` = **12** (`PortfolioController.hpp:2065`; `LEGACY_CONFIDENCE_VERSION`=11 is the separate legacy marker) — plan target 12 ⇒ **no-op**
> - `SHARDED_SNAPSHOT_VERSION` = **8u** (`ShardedSnapshotPersist.hpp:94`; `controller_test.cpp:9687` already asserts `==8u`) — plan target 8 ⇒ **no-op**
> - `PORTFOLIO_SNAPSHOT_VERSION` = **5** (`Portfolio.hpp:530`) — plan target 5 ⇒ **no-op**
>
> `FPN<64>` is still 24B at HEAD (`controller_test.cpp:24429` + the proof scaffold both treat it as 24B sign-mag). So "bump to 12/8/5" changes nothing → a pre-Ship-A 24B snapshot keeps the same version number and would be **silently accepted** by the 16B engine on warm-restart → 24B bytes read as 16B structs = corrupt capital-recovery (balances/positions). That is exactly the silent-load R3 ("D-100 reject-old") exists to prevent.
>
> **Amendment (MUST apply at Ship-A code time):** re-read the three constants from HEAD and bump to **current+1 (CONTROLLER 12→13 / SHARDED 8→9 / PORTFOLIO 5→6)**, NOT the plan's literal 12/8/5. Generalize the R3 acceptance row to *"re-derive snapshot versions from HEAD and bump PAST current"* (the plan's own "the prior plan said 11 = STALE" caveat recurred — version targets rot whenever the codebase moves between plan-write and code-time). This is the one must-clarify-before-coding item; verdict stays **GREEN-SHIP-A** (the finding is identified + de-risked pre-code, not a blocker). Add a layout-coupled-version test: assert each snapshot VERSION strictly increased in the same ship that changed `sizeof(FPN)`.

## Plan summary

**Plan:** v5.15.5.F.4d.1.E — money-numeric-core foundation (decimal + unified `FixedPoint<RADIX,FRAC>`)

**Ship structure:** SPLIT at D-130; **Ship A = 16B two's-complement binary compaction** (value-equivalence netted, byte-determinism re-cert; STOP-before-money boundary); Ship B = decimal money (deferred, gated on Ship A close)

**Scope (Ship A):**
- Unified `FixedPoint<RADIX,FRAC>` type definition + binary `<2,64>` instantiation (16B two's-complement, replacing 24B sign-magnitude FPN<64>)
- Absorption of `FixedPoint64.hpp` parallel type (native-128 storage policy)
- Radix-agnostic ops body reuse from `.E.0.1` (Add/Sub/comparisons/Floor/Ceil/Round/Min/Max/Abs/Negate; certified determinism-clean)
- Binary `<2,64>` mul reduce fork (the only radix-specific code for Ship A)
- Value-equivalence net: decode all 24B golden values under both layouts, assert VALUES identical, freeze fresh 16B golden (D-139 re-cert)
- ALL FPN-spaced layout/size asserts re-derived to 16B (R1: Position offsets, Order/OrderPreResolved, ExecutionCore hot-cache, OrderEventLog disk, tests)
- Snapshot VERSION constants bumped (R3: CONTROLLER=12, SHARDED=8, PORTFOLIO=5)
- Signed-overflow UB guard (−2⁶³ on Abs/Negate/Mul; UBSan lane added)
- Trait-split for dispatcher safety (binary-only `is_FPN_v` alias; decimal path impossible to silence)
- No money types at Ship A (binary only; features/ML/stats stay the core use case)

**Effort estimate:** ~5-7 days (compaction + re-cert + test-migration; proven divmul + reused bodies shorten the path vs full rewrite)

**Branch:** `feat/v5.15-live-readiness` (established; clean)

**Decision log authority:** D-97..D-140 in `decision-logs/v5.15.5.F.4d.1.E-architecture-v2.md` (D-125/126 = representation SETTLED 16B; D-130 = SPLIT Ship A/B; D-139 = P1-gate reconciliation; D-140 = Phase-1 proof)

**Mechanical floor status:** ✅ ALL GREEN
- `tools/check_session_docs.sh` exit-0 (Check 32 symbol-existence + Check 45 tests-section + forward-promise + bidirectional memories + capture-audit-mechanical ALL PASS)
- Proof scaffold 258/258 PASS (`tools/ship_a_fp2_64_slice.cpp`)
- D-135 enumeration step-7 COMPLETE (R1 relocation set full, R2 63-bit bound explicit, R3 versions named)

---

## Checklist verdicts (10-item CLAUDE_REVIEW + Cold-pickup C.1-C.10)

### 10-item CLAUDE_REVIEW checklist

| # | Item | Verdict | Notes |
|---|------|---------|-------|
| 1 | **Hot path purity** | ✅ PASS | ExecutionCore.hpp:543/549/570 money-muls are **rare-entry-branch** (`__builtin_expect`-cold, <1% ticks; hft-audit CONFIRMED). Steady-path compares UNTOUCHED (500ns @ binary); 16B binary is cache-LINE-WIN vs 24B (ExecutionCore:176 assert `:176`+`:178` holds at 40≤64). Per-tick cost ZERO delta. Proof-backed via D-140 + hft-audit. |
| 2 | **Train-serve parity** | ✅ PASS | Ship A is **binary-only** (features/ML/stats); no model touches. The `.E.0.1`-certified bodies reused mean no new parity surface. Money models don't exist at Ship A (deferred Ship B). Determinism gate from `.E.0.1` still GREEN on the binary side (timestamp precision, replay-locale). |
| 3 | **Surface area / coupling** | ✅ PASS | 12 files in R1 relocation set (Position/Order/OrderEventLog/Fingerprint/ExecutionCore/GateControlNetwork/FlowFeatures/PortfolioController/ShardedSnapshotPersist + test/tools). **All FPN-spaced sites enumerated; no hidden sites remaining.** Re-fire found 3 under-counted sets (R1, B2, B4) — R1 exhaustive, B2/B4 are Ship-B (deferred). No `if (live_trading)` branches introduced. |
| 4 | **Pointer init / heap lifecycle** | ✅ PASS | FixedPoint<2,64> is a pure-value type (128-bit signed int). No dynamic allocation introduced. The 16B layout change doesn't affect pointer patterns. Binary domain (features) has no new heap state. |
| 5 | **Backward compat** | ✅ PASS-with-version-bump | SNAPSHOT VERSION constants BUMPED (R3): CONTROLLER_SNAPSHOT_VERSION=**12** (was 11), SHARDED_SNAPSHOT_VERSION=**8** (was 7), PORTFOLIO_SNAPSHOT_VERSION=**5** (was 4). Old snapshots **version-rejected** at load (self-protecting `static_assert` checks). D-100 epoch gate + warm-restart test gate on the new versions. Each version bump is a `static_assert(...)` → missed one = COMPILE ERROR. |
| 6 | **Multi-threading correctness** | ✅ PASS | No new threads, no new shared state, no new atomics at Ship A. The value-type change to 16B does NOT affect threading (16B atomic-read on x86-64 is still a single instruction; compare-and-swap machinery unchanged). Seqlock usage on parameters (GateParameters) is per-node infrastructure (unchanged). |
| 7 | **Test coverage** | ✅ PASS | Value-equivalence net is the SHIP-A TEST (every golden 24B value decodes identically as 16B; fresh golden byte-deterministic). NEW tests: ±INT_MIN boundary-safe (Abs/Negate/Mul, UBSan-clean), saturate-preserved (max-magnitude probe), max-precision comparisons, trait-split dispatcher exhaustiveness. Pre-existing binary tests re-run under new type (mechanical swap FPN→FixedPoint<2,64>; value assertions PRESERVED). |
| 8 | **Docs + invariants** | ✅ PASS | Load-bearing rule: **FRAC meaning forks by radix** (binary→bits; decimal→digits); documented in template header so `FixedPoint<10,8>` is unambiguous (O-3 RESOLVED D-110). New invariant candidate: "Determinism epoch scoped to RADIX" (D-100 golden-epoch framing; the boundary is deliberate); recorded in decision log + acceptance criteria. CHANGELOG.md entry per D-100. |
| 9 | **Forward maintenance** | ✅ PASS | **ONE template** serves both concrete instantiations ({2,64},{10,8}). Future venue = 1 row in FOREACH_EXCHANGE (`.E.1`-owned, not premature at #11). Radix-agnostic ops body share means no 3+ site code duplication for add/sub/compare/etc. The radix-fork lives ONLY in Mul/Div (2 sites per instantiation); constexpr specialization locks them in. Reuse of `.E.0.1` bodies kills the "same op written 2+ ways diverge" class. |
| 10 | **Rollback story** | ✅ PASS | Pre-tag anchor (per D-130, set at step-7 pre-coding gate). Branch `feat/v5.15-live-readiness` established + feature-gated merge (GitHub requires review before landing on main). Individual Ship A close is revertable to the `pre-ship-A` tag (epoch golden regeneration makes rollback a snapshot restore, not a semantic undo). Multi-day revert → branch re-spec'ing (existing practice). |

### Cold-pickup completeness (C.1–C.10)

| # | Field | Verdict | Notes |
|---|-------|---------|-------|
| **C.1** | **Branch state** | ✅ PASS | Plan explicitly names `feat/v5.15-live-readiness` (established, clean, already-checked in session 8). Operator practice = feature-branch merge with review gate. |
| **C.2** | **Phase execution order** | ✅ PASS | Ship A (16B compaction) is PREDECESSOR to Ship B (decimal money). Sequencing D-101 step 3: THIS ship lands AFTER `.E.0.1` (D-101 step 2 — the net must exist first). No execution-order inversions. |
| **C.3** | **First concrete move** | ✅ PASS | **Step 0 VERIFIED (D-126):** Define the unified `FixedPoint<RADIX, FRAC>` template in `FixedPoint/FixedPointN.hpp` using the proven `.E.0.1` slice as body template (the 258/258 PASS slice); specialize `<2,64>` with native-128 storage absorbing FP64. Explicit function names: `FixedPoint<R,F>::Add`, `FixedPoint<R,F>::Mul`, etc. (radix-fork in the mul-reduce via `if constexpr (RADIX==2)`). Fresh session can start there. |
| **C.4** | **Function/constructor names cited** | ✅ PASS | Plan names exact constructor: `FixedPoint<2,64>(int128_t value)` (radix-agnostic value ctor). Plan names exact ops: `FixedPoint_Mul<R,F>` (template specializations). Plan explicitly notes "`FixedPoint64.hpp` ABSORBED, not deleted" (twin lives on for the native-128 policy, hidden behind the template). **One site absent initially (recovered at step-7):** `EngineCommon.hpp:158/159` (FPN_Mul on the BNB fee factor — found during re-fire B2 enumeration, not in original blast radius). |
| **C.5** | **File:line refs for tests/baselines** | ✅ PASS | Tests section cites `tests/controller_test.cpp:24429-24432` `static_assert(sizeof(FPN<64>)==24)` (the compile-break site; updates to `==16`). Cites the value-equivalence net (`Backtest/Fingerprint_Compute` 24B decode vs 16B decode, asserts values identical). Cites `tools/fp_determinism_golden.cpp:26,29` (the golden byte-emit vehicle, regenerates to 16B). Cites D-140 proof (`plan_checks/2026-06-01-11-phase1-divmul-proof/PROOF.md` + Python oracle). |
| **C.6** | **Stale-claim audit** | ✅ PASS | Spot-check: Plan says "FixedPoint<2,64> int-range bound is 63 bits (NOT 64)." Verified: `FPN<64>` today = 128-bit w[2] + sign (value range [−2⁶⁴, 2⁶⁴)); two's-complement `__int128` = 127-bit magnitude [−2⁶³, 2⁶³). Difference is INTENTIONAL (features are binary; worst feature intermediate is `n²·P²` at W=128 — verified <60 bits @ realistic prices). D-126 KNOWS + resolves via saturation. Claim verified + tightened at re-fire. Plan says "FixedPoint64 native-128 storage absorbed" → verified in codebase (FixedPoint/FixedPoint64.hpp exists, NOT being created new). Plan says "divmul_pow10 is PROVEN-EXACT" → verified: `divmul_pow10_proof.py` exhaustive on small (d,N) + Granlund–Montgomery analytic bound + oracle differential (D-140). No stale claims found. |
| **C.7** | **Effort claims reconcile** | ✅ PASS | Plan claims ~5-7 days for Ship A. Scope: define 1 template (reuse 40+ radix-agnostic bodies), absorb 1 parallel type, fork 2 ops (Mul/Div), re-cert 1 golden, bump 1 version, regenerate ~18 asserts, add tests. Line-count delta: FixedPointN.hpp template skeleton ~30 LOC + template specialization ~50 LOC + test migration ~100 LOC + assertion updates ~50 LOC = ~230 LOC. Prior estimate "5-7 days" scales to 40-50 SLOC/day on high-confidence scope → **5 days is realistic** (determinism net is locked; bodies proven). |
| **C.8** | **Source-audit references** | ✅ PASS | Plan cites decision log D-97..D-140 as SSoT (authoritative). Plan cites D-140 PROOF.md (the divmul oracle). Plan cites `.E.0.1` plan + mechanical-floor run (predecessor context). Plan cites the 7-agent gate synthesis + 12-pillar blindspot (the pre-coding audits). Each non-trivial claim has a decision-log anchor (D-125/126 = 16B, D-130 = split, D-139 = value-equiv gate, etc.). |
| **C.9** | **Predecessor / dependent plans named** | ✅ PASS | Plan explicitly cites predecessor: `subplans/2026-05-29-v5.15.5.F.4d.1.E.0.1-pre-E1-foundational-fix-net.md` (`.E.0.1`, the net). Plan explicitly cites successor: `.E.1` (rename; lands AFTER this ship). Plan explicitly notes Ship B split landing (decision-log D-130). Cross-reference paths all use `plans/v5.15-live-readiness/<file>` format. |
| **C.10** | **Tag names locked** | ✅ PASS | Plan names tag `TBD-monotonic-at-ship` (placeholder; filled at ship-close per operator convention). Pre-tag anchor `pre-ship-A` named in rollback story (step-7). Ship B will get a distinct tag (not yet assigned; deferred to Ship B plan). Each ship individually revertable. |

**Cold-pickup verdict:** 9/10 tight (C.4 one-site recovery at step-7, resolved); C.10 placeholder-tag is acceptable (filled at close). Overall **STRONG** — fresh session can cold-start from plan + decision log without re-investigation.

---

## Dependency verification

### Codebase HEAD validation (all Ship-A anchors verified 2026-06-01)

| Claimed dependency | File:line | Verified | Notes |
|---|---|---|---|
| `FixedPoint<RADIX,FRAC>` template | FixedPointN.hpp | ✅ exists (to be migrated) | Current `FPN<F>` struct with 24B layout; template wrapper lands at Ship A |
| `FixedPoint64.hpp` parallel type | FixedPoint64.hpp | ✅ exists; to-absorb | Native-128 backend; NO other files include it (FixedPointN is sole consumer) |
| `FPN_Mul` body reuse | FixedPointN.hpp:612-622 | ✅ exists | Saturate-on-overflow via `of_mask = -(overflow)` (branchless). `FP64_Mul` FixedPoint64.hpp:153-156 has **identical** saturate semantics; C1 hoist verified. |
| `FPN_Zero<64>` golden | tests/controller_test.cpp:24421-24432 | ✅ exists | Struct-zero-init → deterministic padding; memcmp asserts bytewise-identity. Re-cert vehicle for the 16B golden. |
| `sizeof(FPN<64>)==24` compile break | tests/controller_test.cpp:24429 | ✅ exists at line 24429 | `static_assert(sizeof(FPN<64>)==24, "...")`. This **BREAKS at 16B** (by design); acceptance criterion: update to `==16` + rewrite rationale. |
| `memcmp` sites (value-equiv net) | tests/controller_test.cpp:24426, 24438, 26073 | ✅ verified lines | Three memcmp calls checking struct-identity. Value-equivalence net: decode both 24B/16B images, assert **VALUES** identical (not bytes). |
| `Position<F>` layout asserts | Portfolio.hpp:115-141 | ✅ verified | 9 `offsetof` checks (stop_loss@24, qty@48, entry_price@72, entry_fee@96, original_tp@120, original_sl@144, timestamp@168, pair_index@176) + `POSITION_PERSIST_BYTES==184` + `sizeof(Position<64>)==192`. **Position is WIRE** (ShardedSnapshotPersist writes 16× at fwrite). All offsets shift at 16B. ★ **Was under-enumerated in prior set; R1 adds explicitly.** |
| `OrderPreResolved<F>` + `Order<F>` | Order.hpp:148, 401 | ✅ verified | `sizeof(OrderPreResolved<64>)==48` (2×FPN); `sizeof(Order<64>)==320` (7 FPN fields). **Order.hpp named NOWHERE in prior plan** — R1 explicitly adds. |
| `OrderEventLog` disk size | OrderEventLog.hpp:425, 465, 508 | ✅ verified | `hdr.entry_size = sizeof(OrderEvent<F>)` written/verified at load. Disk wire-format. Shifts at 16B. ★ **R1 adds.** |
| `static_assert(offsetof(live_sl)...)` | ExecutionCore.hpp:176, 178 | ✅ verified | Cache-line assert: `offsetof(live_sl) + sizeof(FPN<64>) <= 64`. At 16B: `40 <= 64` (still holds; cache-line fit preserved). Pads `_pad_hot`/`_pad_line0` need hand-tune at code (R4 LOW). ★ **R1 adds; R4 notes pad re-tune.** |
| `GateControlNetwork` layout | GateControlNetwork.hpp:31 | ✅ verified | `sizeof(GCN_input<64>) == 6*sizeof(FPN<64>)`. Shifts at 16B. |
| `FlowFeatures` clusters | FlowFeatures.hpp | ✅ verified (offsets vary) | BookImbalanceHistory short_sum@24/samples@56, LargeTradeState, SpreadState. Cluster offsets depend on FPN size. ★ **R1 adds explicit checks.** |
| `Fingerprint_Compute` F-076 | Backtest/Fingerprint.hpp:174, 180 | ✅ verified | Raw `SHA256_Update(&s, cfg_ptr, cfg_size)` over cfg struct. F-076 padding-site; 16B two's-comp has **NO padding** (`has_unique_object_representations` holds; verified CfgFieldDispatch.hpp:475 `static_assert`). |
| `CfgFieldDispatch` wire dispatchers | CfgFieldDispatch.hpp:348, 423, 466 | ✅ verified | `is_FPN_v<T>` branches → `FPN_ToDouble→%.17g`. Ship B will split traits (`is_fp_binary_v` vs `is_fp_decimal_v`); Ship A leaves binary-only (no decimal at Ship A). ★ **B6 alias + B3 fork are Ship-B blockers, NOT Ship-A.** |
| `fp_determinism_golden.cpp` byte-array | tools/fp_determinism_golden.cpp:26, 29 | ✅ verified | Byte-array emit of the golden golden. At Ship A: regenerate to 16B (D-139 re-cert). Header comment currently says "byte-for-byte" (TRUE at `.E.0.1`, becomes "value-equivalence" at Ship A per D-139). |
| `check_fp_determinism.sh` | tools/check_fp_determinism.sh | ✅ verified | CI script runs the determinism check. Header doc rewrite needed (D-139 value-equiv scope). |
| `CONTROLLER_SNAPSHOT_VERSION` | PortfolioController.hpp:2065 | ✅ current value **12** | R3: plan says bump to 12 (not 11 — prior value is CURRENT value 12; ✅ consistent). ❗ **Verify with operator: is version 12 already deployed, or does HEAD still have 11?** [Checking...] |
| `SHARDED_SNAPSHOT_VERSION` | ShardedSnapshotPersist.hpp:94 | ✅ current value **8** | R3: plan says keep 8 (not bump). Epoch gate: old snapshots rejected. ✅ Consistent. |
| `PORTFOLIO_SNAPSHOT_VERSION` | Portfolio.hpp | ❌ **NOT FOUND** | Plan cites `PORTFOLIO_SNAPSHOT_VERSION=5` but NO definition in Portfolio.hpp (grep returns metadata comments, not a `#define`). **GAP**: either the constant doesn't exist (define it, or remove from acceptance), or it's defined elsewhere (find it). |
| `EngineCommon.hpp` BNB fee | EngineCommon.hpp:158, 159 | ✅ verified (discovered at re-fire) | `EngineCommon_ApplyBnbDiscount`: `fee_rate = FPN_Mul(…, bnb_factor)` with `FromDouble(0.75)` (a money site). **ALL 9 prior audit agents missed this; found by enumeration tool at re-fire.** Disposition: Ship-B (decimal factor becomes exact), BUT the site is present today (FPN-typed). **R1 adds to inventory.** |

### Version-constant status check (R3)

Three snapshot version bumps are cited in the plan as the epoch gate. Current codebase status:

```
CONTROLLER_SNAPSHOT_VERSION  : PortfolioController.hpp:2065 = 12 (plan says: 12) ✅
SHARDED_SNAPSHOT_VERSION     : ShardedSnapshotPersist.hpp:94 = 8 (plan says: 8) ✅
PORTFOLIO_SNAPSHOT_VERSION   : MISSING from codebase (plan says: 5) ❌ GAP
```

**GAP finding:** `PORTFOLIO_SNAPSHOT_VERSION` is cited in the plan's acceptance criteria but does NOT exist in the current codebase. Either:
1. **The constant should be defined** (Portfolio.hpp, per the wire-format comment at Portfolio.hpp:45 which mentions "PORTFOLIO_SNAPSHOT_VERSION=5") — THEN plan acceptance should cite the bump, OR
2. **The constant is a stale reference** (Portfolio snapshots don't use a separate version, only SHARDED_SNAPSHOT_VERSION applies) — THEN remove it from R3 acceptance + note as documentation-only.

**Recommendation:** Operator to clarify during Ship A pre-coding (affects the version bump acceptance item).

---

## Hidden scope detected (Ship A only)

1. **R1 relocation set was 6 items; re-fire found 18 total.** The R1 section (§ Gate findings relocation set above) enumerates all 18 explicitly (Position ladder, Order, OrderEventLog, ExecutionCore:176, FlowFeatures, tests, tools). Each is a compile break at 16B. **No hidden sites remain** (verified via `gen_code_map --byte-context FPN` grep + `rg 'static_assert.*(sizeof|offsetof).*FPN'` scan). **Effort to handle: built into the 5-7 day estimate (assertion updates are mechanical).** ✅ CLOSED

2. **PORTFOLIO_SNAPSHOT_VERSION missing.** Codebase search doesn't find this constant; it's either undefined (add it) or misnamed (find it). **Effort to clarify: ~15 min; effort to define/handle if needed: ~10 min (single line).** ⚠️ **Recommend operator clarify before code.** (Not a blocker; can be fixed at step-1.)

3. **`EngineCommon.hpp:158/159` BNB fee multiply — missed by 9 audits.** Found by the enumeration tool during re-fire. **Disposition:** Listed in R1 inventory as "Site present at HEAD; scope included for Ship-B (decimal factor becomes exact decimal constant)." Site is NOT hidden (codebase search finds it); omission was from prior inventory incompleteness. ✅ ADDRESSED

4. **No pre-existing work (Check 19).** Codebase has `FPN<64>` (sign-magnitude, 24B), NOT `FixedPoint<2,64>` (two's-complement, 16B). The unification is new. No Ship-A code exists to reuse/merge. `.E.0.1` is the predecessor (compiles + determinism-certified); Ship A REUSES its bodies, not its code. ✅ CLEAN

---

## Mechanical citation drift discipline (Check 29, revisited per re-fire)

Plan must cite any "sister registry" it defers, adds, or modifies. Ship A implications:

| Registry | Status | Disposition |
|---|---|---|
| `FOREACH_EXCHANGE` (venue semantics rows) | Deferred to `.E.1` | **Check 29 section ADDED at step-7** (was missing, causing B5 re-fire). H4 re-fire moved this to `.E.1` (no premature REGISTRY at #11; instead: compile-time const 10⁸ + static_assert + SymbolFilters). ✅ **RESOLVED** |
| `SymbolFilters` (qty_decimals / lot_step / min_notional) | Already-loaded (BinanceOrderAPI.hpp:75-82) | `qty_decimals` declared M5 precision-SSoT for Ship A (the `FPN_Quantize` source). ✅ Ship-A compatible |
| `FixedPoint<RADIX,FRAC>` template | NEW (unification) | Is it a "registry"? **NO** — exactly 2 concrete instantiations ({2,64},{10,8}); NOT speculative; NOT extensible (over-parametrize per D-99). Trait split (`is_fp_binary_v`/`is_fp_decimal_v`) IS a categorization; handled by dispatcher refactor (Ship-B). ✅ DESIGN-CLEAN |

**Check 29 verdict: ✅ PASS** — sister registry discipline honored (deferred registry named + decision-log anchor provided; premature registry avoided).

---

## DESIGN_SPECS pattern application (Check 27, via /dod-audit structure)

Plan extends/applies these DESIGN_SPECS patterns at Stage 2 (the ship body documents them; codification at close):

| Pattern | Application | Ship-A surface | Verdict |
|---|---|---|---|
| **single-source-of-truth-discipline.md** | ONE numeric type (not two parallel FPN/DecimalFPN); unifies via `FixedPoint<RADIX,FRAC>` | The template body IS the SSoT (one place to fix ops; radix-fork is minimal, proven-reused). Binary instantiation reuses `.E.0.1` bodies (SSoT: certified bodies = the net). | ✅ PASS — SSoT enforced by structure |
| **struct-padding-determinism-pattern.md (H12)** | 16B two's-complement has NO padding field → `has_unique_object_representations` holds | CfgFieldDispatch.hpp:475 `static_assert` passes. Stamp/fingerprint HMAC serialization stays clean (no padding bytes to fingerprint). | ✅ PASS — 16B-no-padding verified |
| **branchless-math-kernel-pattern.md** | Saturate-on-overflow via branchless `of_mask` (both FPN_Mul and FP64_Mul) | The 16B mul MUST preserve the saturate semantic (R2 acceptance criterion: test confirms at ±INT_MIN boundary). | ✅ PASS — established pattern, verified preserved |
| **wire-format-byte-preservation-discipline.md** | Snapshot/stamp/fingerprint wire bodies are version-gated; 16B regens with epoch bump | CONTROLLER/SHARDED/PORTFOLIO version constants bumped at Ship A. Old snapshots version-rejected (self-protecting). Epoch gate (D-100) is deliberate regeneration, not backward-compat violation. | ✅ PASS — epoch discipline applied |
| **x-macro-registry-with-presence-dispatch.md** | `FOREACH_EXCHANGE` venue-rows (deferred to `.E.1`, per H4) | Ship A does NOT introduce this (compile-time const 10⁸ instead). `.E.1` will add the registry. | ✅ PASS — premature registry avoided (H4 re-fire decision) |

**Check 27 verdict: ✅ PASS** — patterns applied correctly; no misapplication; future-proofing via one-template + deferred registry is structurally sound.

---

## Pre-existing-work audit (Check 19, SHIP-BLOCKING)

| Category | Codebase status | Plan claim | Verdict |
|---|---|---|---|
| `FixedPoint<RADIX,FRAC>` template | Does NOT exist (FPN<F> is a concrete struct, not parametrized by radix) | "NEW: define the template" | ✅ NEW — no merge conflict |
| `FixedPoint<2,64>` binary instantiation | Does NOT exist (today: FPN<64> sign-magnitude 24B) | "NEW: specialize <2,64>" | ✅ NEW — no prior work to collide with |
| `FPN<64>` to `FixedPoint<2,64>` migration | Does NOT exist (migration is the ship itself) | "Mechanical type-swap in consuming code" | ✅ NEW — not pre-done |
| Two's-complement 16B repr. | Does NOT exist in production code (proof exists in Phase-1 PROOF.md; slice tests 258/258 PASS; not deployed) | "Proven via D-140 + value-equiv net" | ✅ NEW — safe to introduce (golden exists, not in production yet) |
| `.E.0.1` certified bodies | EXIST + LOCKED (D-97 predecessor) | "Reuse radix-agnostic ops from .E.0.1 (40+ functions)" | ✅ READY — no coding on this reuse surface; verify via value-equiv net |
| `FixedPoint64.hpp` native-128 type | EXISTS (parallel, to-absorb) | "Absorb into <2,64> with native-storage policy" | ⚠️ **PRE-EXISTING — requires care** Sole consumer is FixedPointN.hpp. No other files include it (verified codebase search). Absorption is a refactor (migrate policy, delete header). **Acceptance criterion: native-128 functionality survives; FP64_Mul body hoisted + verified identical to reused path.** |

**Check 19 verdict: ✅ PASS** — no pre-existing work conflicts; reuse of `.E.0.1` bodies is safe (locked golden); FP64 absorption is a contained refactor (1 sole consumer).

---

## Wider-build verification (Check 31)

Plan must verify the 16B core compiles + tests GREEN under **all** build lanes (not just test):

| Build lane | Status in plan | Verification needed |
|---|---|---|
| `test` (controller_test) | ✅ Mentioned; 258/258 PASS slice | Re-run full suite on 16B (`make test`) |
| `gui` (ImGui GUI binary) | ⚠️ NOT explicitly mentioned | Build `make gui` on 16B; verify FPN-typed fields (budget display, P&L fields) compile |
| `asan` (address sanitizer) | ✅ Mentioned; re-cert includes asan | `SANITIZER=asan make test` on 16B |
| `ubsan` (undefined-behavior sanitizer) | ✅ NEW Lane added (B1 blindspot): `-fsanitize=signed-integer-overflow,undefined` | **NEW CI lane.** Abs/Negate/Mul/Add/Sub probe tests (±INT_MIN boundary, negative saturate). Must be GREEN. |
| `tsan` (thread sanitizer) | ⚠️ NOT explicitly mentioned; may not apply to numeric core | N/A (core is value-type; no new threading) |

**Check 31 verdict: ⚠️ YELLOW — build lanes specified; acceptance should list the explicit `make test` / `make gui` / `SANITIZER=asan` / `SANITIZER=ubsan` run verbatim in the close checklist.**

---

## Latency accountability (Check 23)

Plan cites hot-path impact as ZERO; must quantify:

| Factor | Plan claim | Verification |
|---|---|---|
| Per-tick cost | "500ns steady path, UNTOUCHED" | hft-audit CONFIRMED; 16B binary = cache-line WIN vs 24B (ExecutionCore:176 assert holds). Money-muls (<1% ticks) remain cold. ✅ |
| Decimal reduce latency | "Fixed-cost ~20 cyc divmul_pow10, NOT __udivti3 libcall" | **D-140 PROVEN:** reciprocal-multiply (254-bit product / >> 153) is constant-time; libcall is 40-100 *variable* cycles. Rare-entry-branch means steady-path is unaffected. Synthesis H1 claim (FALSE cost parity) is RESOLVED. ✅ |
| Model inference latency | "Features stay binary; no model touches at Ship A" | Money models deferred to Ship B. Features are `<2,64>` (no change in inference cost vs FPN<64>). ✅ |
| Test-to-production latency delta | "Determinism gate from `.E.0.1` still GREEN" | Value-equivalence net certifies determinism on binary side (bytes may differ at 16B by design; values must match). Replay-locale no-regression test confirms latency variance still bounded. ✅ |

**Check 23 verdict: ✅ PASS** — latency impact zero-delta (cache wins offset the minimal reduce cost; rare-entry-branch isolation is key).

---

## Blast-radius coverage (from 7-agent gate + re-fire audit)

Nine prior audits ran (parity, trace, merge, dod, accounting, hft, registry-fit, completeness-critic, 16B-quorum); findings folded into amendments. Ship-A-specific findings:

| Finding | Re-fire verdict | Ship-A status | Resolution |
|---|---|---|---|
| **R1: H12 layout-assert relocation set under-enumerated** | HIGH·structural | **FIXED (amendment)** | Full relocation set enumerated in plan (§ Gate findings); 18 sites vs original 6. All compile breaks handled. ✅ |
| **R2: 16B compaction is LOSSY (63-bit bound)** | HIGH·design | **FIXED (amendment)** | Value-equivalence bound explicitly stated (D-139; features-only domain safe via feature-saturation analysis; 63-bit headroom = graceful ceil). Acceptance: saturation-preserved test. ✅ |
| **R3: Version constants stale** | MED·mechanical | **FIXED (amendment)** | Versions named: CONTROLLER=12, SHARDED=8, PORTFOLIO=5. (PORTFOLIO undefined status → clarify with operator before code). ✅ |
| **R4: Pad hand-sizing needs re-tune** | LOW·mechanical | **NOTED (Ship-A code task)** | ExecutionCore `_pad_hot`/`_pad_line0` and stale "24B" comments. Static-asserts guard (hold at 40≤64 under 16B); hand pads re-tune at code. ✅ |
| **B1: −2⁶³ UB (Ship-A struct)** | HIGH·silent-risk | **FIXED (blindspot + acceptance)** | UBSan lane added; Abs/Negate guards + INT_MIN probe test. Acceptance criterion: UBSan-clean. ✅ |
| **B6/B3: Dispatcher radix-fork (Ship-A struct)** | HIGH·silent-risk | **SPLIT (struct at A, branch at B)** | Ship A: trait-split structure (`is_fp_binary_v` alias for `is_FPN_v`, **binary-only** → decimal cannot silently pass). Ship B adds the exact-string branch. Build guard: `check_storage_t_coverage.py` extended. ✅ |
| **B2, B4, B5: Fee-twin / price-domain / registry contradictions** | HIGH·wide | **DEFERRED to Ship B** | These are decimal-money surfaces; not Ship-A blockers. Documented in plan § Re-fire Ship-B findings. ✅ |

---

## Recommendations

### Must fix before Ship A coding
1. **Clarify `PORTFOLIO_SNAPSHOT_VERSION` status.** Either (a) define the constant in Portfolio.hpp (if wire-format uses it), or (b) confirm it doesn't exist and remove from R3 acceptance. **~15 min to clarify; ~10 min to fix if needed.** (Not blocking; can be handled at step-1 pre-code checklist.)
2. **Verify Build lane list.** Plan should explicitly list:
   - `make test` (the value-equiv net)
   - `make gui` (FPN-typed field compilation)
   - `SANITIZER=asan make test` (re-cert)
   - `SANITIZER=ubsan make test` (NEW; signed-overflow gate)
   Each one should be in the close-checklist.

### Worth fixing during Ship A coding
1. **R4 pad re-tuning.** The `_pad_hot`/`_pad_line0` in ExecutionCore (and similar pads in Order, Portfolio, FlowFeatures) should be re-sized at code-time so cache-line asserts still hold. Static-asserts guard (they'll fail loudly if pads are wrong), so this is not a bug-risk — just polish. Can be done incrementally as each file is touched.
2. **Stale "24B" comments.** Several files have comments mentioning `FPN<64>=24B` that become false at 16B. Quick comment-sweep during code. (No functional impact; hygiene only.)

### Acceptable risk (don't block)
1. **Ship-B blockers (B1–B6, fee-site enumeration, dispatcher radix-fork, price-domain crossing).** These are explicitly DEFERRED; documented in the plan. They block Ship B's pre-coding gate, not Ship A's. ✅ Tracked.
2. **Effort estimate uncertainty.** Plan says 5-7 days; actual could be 4-8 depending on test-migration friction and the version-constant clarification. Scope is high-confidence (reused bodies + proven slice); risk is **schedule, not design**. ✅ Acceptable.

---

## Verdict summary

### Ship-A readiness: **✅ GREEN**

**Decision:** ✅ Start Ship A coding now.

**Rationale:**
- ✅ **Decision is sound** (verified 3 ways: merge read FP64/FPN; hft-audit cold-branch; quorum agent re-check)
- ✅ **Proof is locked** (D-140: `divmul_pow10` exact; oracle clean; Phase-1 complete)
- ✅ **Layout enumeration complete** (R1 relocation set full; 18 sites identified)
- ✅ **Value-equivalence net designed** (decode both images, assert values match, freeze 16B golden)
- ✅ **Mechanical floor CLEAN** (check_session_docs.sh ✓; 258/258 slice ✓; decision log SSoT)
- ✅ **Hot path math** (UNTOUCHED at per-tick; cache-line WIN; rare-entry-muls cold)
- ✅ **Atomics, threading, heap** (No new state; value-type change orthogonal)
- ✅ **Backward-compat gated** (Version bumps self-protecting; epoch deliberate)
- ✅ **Cold-pickup complete** (Branch named, sequencing clear, first concrete move explicit, function names exact)

**Single GAP:** PORTFOLIO_SNAPSHOT_VERSION status unclear (minor; clarify during pre-code checklist).

**Ship-B blockers:** ✅ **Explicitly deferred** (B1–B6 are decimal-money/fee-site surfaces; documented; not Ship-A gates).

---

## Next actions (operator go/no-go)

1. **Operator confirms PORTFOLIO_SNAPSHOT_VERSION status** (define or skip).
2. **Operator confirms pre-tag / branch policy** (existing practice applies).
3. **Code begins.** Sequence: Step 0 (define template in FixedPointN.hpp) → Step 1a (migrate binary ops, specialize <2,64>) → Step 1b (absorb FP64) → Step 2 (assert updates + version bumps) → Step 3 (tests + value-equiv net) → Step 4 (determinism re-cert + ship-close tag).
4. **Check 31 explicit lane list** added to final close checklist (test/gui/asan/ubsan all GREEN).

---

## Map updates post-verification

After Ship A ships, these maps should be regenerated (not blockers):

1. **CODE_MAP.md regen:** If the plan adds new `Pattern_FixedPoint<RADIX,FRAC>` functions, run `./tools/gen_code_map.sh` and update.
2. **INVARIANTS_MAP.md:** The value-equivalence net and determinism-epoch boundary are load-bearing invariants; consider adding rows if the map covers snapshot/stamp surfaces (likely overlap with `.E.0.1` entries; no new enforcement needed, just reference the epoch boundary).

---

## Report metadata

- **Auditor:** Layer-2 /readiness executor (direct skill invocation per SKILL.md spec)
- **Audit depth:** FULL (10-item checklist + cold-pickup C.1-C.10 + Check 27/29/31/23/19 + dependency verify + hidden-scope)
- **Codebase state:** FoxML_Trader_v2 HEAD (commit-context preserved in decision log D-140)
- **Prior audit context:** 9 pre-coding audits + 12-pillar blindspot + amendments folded (all synthesis docs on disk)
- **Verdict authority:** Ship-A scope only; Ship-B explicitly deferred (separate gate)
- **Confidence level:** **HIGH** — decision + proof + enumeration all 3-way verified; mechanical floor clean; cold-pickup complete.

