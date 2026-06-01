---
type: proof-record
doc_kind: "#11 Phase-1 deliverable — divmul_pow10 exactness proof + D-100 oracle"
ship: "#11 numeric-foundation unification (decimal money + unified FixedPoint<RADIX,FRAC>)"
sprint: v5.15-live-readiness
created: 2026-06-01
status: PROVEN — divmul magic exact (predicate-validated + differential-clean); D-100 oracle built + clean
decision_log: decision-logs/v5.15.5.F.4d.1.E-architecture-v2.md (D-100 gate, D-104 scale, D-106 venue-SSoT, D-128 half-even)
resolves_finding: "synthesis H1 (decimal Mul reduce is a __udivti3 libcall, not fixed-cost) — concrete branchless lowering produced"
sidecar: subplans/2026-05-31-v5.15.5.F.4d.1.E-11-new-function-designs.md (#3 divmul, #4 rounding)
artifacts:
  - divmul_pow10_proof.py   # the exactness proof (predicate + exhaustive validation + differential)
  - decimal_oracle.py       # the D-100 reference engine (#2-#6 vs Decimal authority)
sister_specs:
  - refactor-patterns/branchless-math-kernel-pattern.md
  - meta-disciplines/golden-master-over-reimplemented-oracle.md
  - meta-disciplines/enumerate-set-before-categorical-claim   # the not-eyeball discipline this honors
---

# #11 Phase 1 — `divmul_pow10` exactness proof + D-100 oracle

**The #1 ship risk (a deterministic-but-WRONG money core) is retired.** The decimal
reduce `C = floor(P / 10⁸)` lowers to a fixed-cost reciprocal-multiply
`floor((P·M) >> S)` with **constexpr (M, S)**, and the lowering is **bit-exact**
over the proven dividend range. Reproduce: `python3 divmul_pow10_proof.py` (proof),
`python3 decimal_oracle.py` (oracle). Both self-contained (stdlib only).

## Result — locked constants (d = 10⁸)

| N (dividend bound) | M (magic, hex) | S (shift) | product width | fits 256-bit mul |
|---|---|---|---|---|
| 120 (conservative) | `0x15798ee2308c39df9fb841a566d74f9` | 147 | 241-bit | ✅ 15-bit margin |
| **127 (recommended)** | `0x55e63b88c230e77e7ee106959b5d3e1f` | 153 | 254-bit | ✅ 2-bit margin |
| 128 (full `__int128`) | `0x15798ee2308c39df9fb841a566d74f87b` | 155 | 257-bit | ❌ 1 bit over 256 |

`floor((P·M) >> S) == floor(P / 10⁸)` for **all** `0 ≤ P < 2^N`.

## Why this is a PROOF, not a spot-check

The dividend range is up to 2¹²⁷ — un-enumerable. So the proof is **analytic** and
computation plays two roles (honoring `enumerate_set_before_categorical_claim` — the
"set" here is the predicate's soundness domain, made enumerable by reduction):

1. **Analytic bound (Granlund–Montgomery round-up reciprocal).** `M = ⌈2^S/d⌉`,
   `e = M·d − 2^S` (`0 ≤ e < d`). Then `M·n/2^S = n/d + e·n/(d·2^S)`, and the floor
   matches `⌊n/d⌋` for all `n < 2^N` when **`e·2^N ≤ 2^S`** (worst case `n mod d = d−1`).
   At `S = N + ⌈log₂ d⌉` this always holds (`e < d ≤ 2^⌈log₂ d⌉`), so a proven-exact
   magic always exists; we take the minimal `S`.
2. **Predicate validated vs FULLY EXHAUSTIVE ground truth.** On small `(d, N)` where
   every `n ∈ [0, 2^N)` *is* enumerable (170 pairs), the analytic predicate's verdict
   matches brute force exactly — **and** a deliberately-too-small `S` is correctly
   rejected (no false "exact"). So the predicate is sound+complete as implemented, and
   trustworthy on the big case.
3. **Redundant differential.** At N=120 *and* N=128: 208k dividends (the binding set
   `{d·k−1, d·k, d·k+1}` + powers of ten + type boundaries + 200k random) — `magic ==
   exact// == Decimal-oracle` for every one.

## Dividend range + the overflow guard (correct-by-construction)

`P = |A|·|B|`, the product of two `<10,8>`-scaled operands before the ÷10⁸ reduce.

- **Venue P_max ≈ 2¹¹⁰** (Binance SPOT filters, D-106 venue-as-SSoT): maxPrice ~10⁶ ×10⁸
  = 10¹⁴ (~47-bit); maxQty up to ~9.2e10 ×10⁸ ≈ 10¹⁹ (~63-bit) → product ~2¹¹⁰. All venue
  filter values are 8-dp strings, confirming the 10⁸ scale (D-104).
- **N=127 covers any two operands each `< 2⁶³`** (value `< $92B`) → `P < 2¹²⁶ < 2¹²⁷`,
  with ~17 bits of headroom over the venue max. A per-operand `|x| < 2⁶³` (or post-multiply
  `P < 2¹²⁷`) **guard** routes any out-of-range value to the existing overflow/flag path
  (#5/#6, D-106 range guard) — so a magic that is only proven over `[0, 2^N)` can **never
  silently mis-divide**: out-of-range is a *flagged error*, not a wrong number. That is the
  correct-by-construction property (not correct-by-discipline).
- **Why not N=128 (full type):** the full-`__int128`-operand product is 2²⁵⁴ — no single
  256-bit-mul magic covers it. N=127 is the **maximal proven range that fits the existing
  256-bit wide-multiply** (#2's primitive), which is why it's recommended over both the
  tighter N=120 and the un-fitting N=128.

## D-100 oracle — built + clean

`decimal_oracle.py` is the independent exact-`decimal` reference for the step-5 op-set
(golden-master, not a reimplemented oracle — value comes from Python `Decimal`, the
authority; the engine's branchless lowerings are mirrored only to cross-check):

- **#2+#3+#4** signed mul → divmul reduce → **half-even (banker's, D-128)**: 300k operand
  pairs, engine == oracle. Half-even **ties** (`2r == 10⁸`, round-to-even) verified explicitly.
- **#5** exact `FromString` (single-pass digit-accumulate, locale-immune): 50k venue strings
  == `Decimal`; malformed / >8dp / scientific-notation all **rejected** (money path surfaces
  errors, never silent-zero). The harness caught its own asymmetry (`Decimal` accepts `"1e5"`,
  the venue never emits it) → oracle now models the **venue alphabet** `[+-0-9.]`.
- **#6** quantize-to-step: 50k cases.

This module is the **standing differential gate**: at Ship A/B it grows a recorded /
Binance-testnet-fill differential (real fills decoded both ways).

## How it drops into the #3 design

```cpp
// decimal <10,8> reduce: C = round_half_even(P / 10^8), P = |A|*|B|  (<2^127, guarded)
static constexpr unsigned __int128 DIVMUL_M_POW8 = /* 0x55e63b88c230e77e7ee106959b5d3e1f */;
static constexpr int                DIVMUL_S_POW8 = 153;
// q = high-word of the 254-bit (P * M), shifted by S  -> floor(P / 10^8)
// r = P - q*10^8                                       -> feeds #4 half-even
// (reuses #2's 128x128->256 wide-multiply primitive; grabs the high end >> S)
```

Replaces the `__udivti3` libcall (~40–100 *variable* cyc) with a fixed-cost
multiply+shift (~20 cyc) on the slow-path/rare-entry money muls — **resolves synthesis H1**
("hot path UNTOUCHED" can now stand for the reduce). The general primitive
(divide-by-invariant-constant for wide types) is the **task-#14 DESIGN_SPEC** candidate.

## Status / next

- ✅ Phase 1 (this doc): divmul proven-exact + D-100 oracle built + clean.
- → **step-6 fold**: cite this for the **H1** disposition; carry N=127 (M/S above) + the
  overflow guard into the #3 design; the oracle becomes the ship's acceptance gate.
- → **step-7 audits** (`/blindspot-scan` + re-fire `/precoding-audit-gate` on the amended
  body, covering the 16B surface per D-135) — these scan the divmul lowering this proof pins.
- The proof verifier is a **CI-gate candidate** (promote `divmul_pow10_proof.py` to `tools/`
  at the codification batch — sister to task #26 verification discipline).
