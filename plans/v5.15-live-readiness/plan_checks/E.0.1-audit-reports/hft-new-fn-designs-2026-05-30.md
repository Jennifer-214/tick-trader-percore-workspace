---
type: audit-report
audit: /hft-audit (Layer 2 — design gate on NEW function designs, pre-implementation)
target: plans/v5.15-live-readiness/subplans/2026-05-30-v5.15.5.F.4d.1.E.0.1-new-function-designs.md
ship: v5.15.5.F.4d.1.E.0.1 (+ .E.0.3 for the tt:: family)
date: 2026-05-30
engine_head: 0b841b3
lens: path-calibration verify/refute + DOD/H11/latency/alloc + honest "branchless?" + cargo-cult avoidance
verdict_summary: path calibration CONFIRMED (all 4 cold) — no design auto-proceeds; operator triages
---

# /hft-audit — `.E.0.1`/`.E.0.3` new-function DESIGNS (pre-implementation gate)

**Scope note:** these are DESIGNS of functions that do not exist yet. This audit judges the
designs for HFT/DOD soundness + path-correct optimization posture BEFORE coding. It does NOT
recommend proceeding to code — Caramel triages.

---

## 0. PATH-CALIBRATION VERDICT (the headline lens)

The plan body's central claim — *"every function here is on a boot / stamp-time / parse path,
NOT the 500ns branchless hot path → H11+DOD apply but H7-strict-branchless does NOT"* — is
**INDEPENDENTLY CONFIRMED for all four designs.** Evidence walked below.

| Design | Claim | Verdict | Evidence |
|---|---|---|---|
| D1 `Fingerprint_CanonicalizeConfig` | stamp/model-save time | **CONFIRMED COLD** | Replaces `Fingerprint_Compute` (Backtest/Fingerprint.hpp:174); the ONLY caller in the whole repo is `BacktestPanels.hpp:3157` — offline backtest/training, GUI thread, and it walks data **files** via `Fingerprint_HashFile` (fopen/fread full-file I/O). File-I/O-bound, not even slow-path. |
| D2 `tt::parse_*_checked` family | replay/cfg/boot/REST parse | **CONFIRMED COLD** | Every existing `parse_double_fast*` caller: ModelInference (stamp load), CoreModelZoo (model-bundle parse), StampBoundModelConstRegistry (stamp parse), BanditLearning (JSON state load), Reconcile (REST/recovery), CfgFieldDispatch (cfg parse), BinanceOrderAPI (REST order resp), GUI TradeReader/TradeHistoryPanel (display thread). **ZERO** in OrderGates/ExecutionCore. |
| D3 boot-pin placement | `main`/SDL-init/backtest-entry | **CONFIRMED COLD** | Boot-time `setlocale`; runs once at process start. Not a per-tick construct. |
| D4 `check_locale_determinism.py` | grep-CI tool | **CONFIRMED COLD (off-engine)** | Python pre-commit/CI grep. Not engine code; no latency surface at all. |

### Hot-path negative-proof (the strongest evidence)
- `rg parse_|from_chars|Canonicaliz|atof|strtod|sha256` over **OrderGates.hpp + ExecutionCore.hpp → EMPTY.** BG_Evaluate / SG_Evaluate / ExecutionCore do no parsing or hashing whatsoever.
- The ONE genuinely per-tick parse site (BinanceCrypto producer ingestion, the documented "only per-tick site") **does not use the `tt::parse_*` family at all** — BinanceCrypto.hpp:744-745 calls `FPN_FromString<F>` directly and derives the TUI double via `FPN_ToDouble` (deliberately, to save a parse per tick + kill a parity hazard; see the v5.11.19 comment). **So D2's `_checked` family touches zero per-tick code by construction.**

**No HOT-PATH-FOUND. H7-strict-branchless correctly does NOT apply to any of the four.**
Open-question #3 ("anything secretly latency-sensitive I mis-classified?") answer: **No.**

---

## 1. The honest "branchless?" answer (per the operator's explicit ask)

> Operator wants: *branchless? bit-ops? as-fast-as-possible? — but calibrated to PATH.*

**D1 canonicalizer + D2 parser: branchless would be CARGO-CULT. Do NOT force it.**
A canonicalizer is inherently a sequence of `memcpy`-appends + length-prefixed string copies +
a constant-trip `cores[]` walk; a checked parser is `from_chars` + a 2-term validity AND. The
only branches are (a) the `from_chars` error check and (b) per-site halt/skip/default on `!ok`.
Both are **correctness branches on a cold path** — eliminating them buys nothing measurable and
would obscure the error semantics that are the entire point of `.E.0.3`. This matches H20's own
exception list (`if constexpr` / genuine binary predicate / boot-time-only) and CLAUDE.md's
"hand-wave 'branch predictor handles it' is anti-pattern" — but inverted: forcing branchless on
a cold error-handling path is the *opposite* anti-pattern (cargo-cult). **The designs already
make the right call** — the plan-body's own framing ("forcing them branchless would be
cargo-cult") is correct and should be honored.

**Where the design IS already optimal (keep as-is):**
- D2 `from_chars` core = the locale-immune fast path (no `strlen` when `n` is passed). Correct.
- D2 by-value `ParseD{double; bool}` / `ParseI<T>{T; bool}` returns in a register pair (SysV ABI:
  a `{≤8-byte scalar, bool}` POD ≤16 bytes returns in RAX:RDX / XMM0:RAX, **no stack spill, no
  out-param aliasing**). DOD-correct; confirmed against the ABI. This is strictly better than
  `bool + T* out` (which forces an address-taken store the optimizer can't always elide).

**Where a real (non-cargo-cult) micro-refinement exists — D2 validity test:**
The two-term check `(r.ec == errc{}) && (r.ptr == s+n)` is fine. If a branch-free `ok` is ever
wanted it's a pure data computation (`(r.ec==errc{}) & (r.ptr==s+n)` with `&` not `&&`) — but
this is a **LOW / optional** nicety, not a requirement: the `&&` short-circuit on a cold path is
free and clearer. Flag it only as "available, not needed." No bit-op trick beats `from_chars` here.

---

## 2. D1 latency / alloc / correctness (within the <50μs stamp-emit budget)

**Latency: comfortably inside budget. No O(n²), no hidden alloc.**
- Alloc-free: caller-provided `uint8_t* buf, size_t cap` — confirmed no `new`/`malloc` (H1).
- The body is: K `memcpy`-appends (each O(field-size)) + per-string one `strnlen(s, MAX_CFG_STR)`
  (bounded linear, O(string-len), NOT O(cap²)) + a single `cores[]` walk. Total is O(total config
  bytes) — strictly linear in the struct it serializes. **No accidental O(n²)** (no nested
  re-scan; each field touched once). The replaced `Fingerprint_Compute` additionally does full
  file SHA over data files — D1 is *cheaper* than what it replaces on the config portion.
- vs the current raw-struct `SHA256_Update(&s, cfg_ptr, cfg_size)` (Fingerprint.hpp:180): the
  current code hashes uninitialized tail/inter-field padding → non-deterministic across runs.
  D1's field-wise emit is the correct H12 fix. **This is a genuine correctness upgrade, not just
  a perf-neutral rewrite.**

**DOD `put_fpn` layout claim — VERIFIED CORRECT (with a caveat to double-check at impl).**
- `ControllerConfig<F>` uses the **templated** `FPN<F>` from `FixedPoint/FixedPointN.hpp`:
  `{ uint64_t w[N]; int32_t sign; }` (line 45-46). D1's `put(v.w, sizeof v.w); put(&v.sign, ...)`
  matches the real members exactly. ✅ (Note: there is also a *non-templated* `FP64`
  `{__uint128_t magnitude; int32_t sign;}` in FixedPoint64.hpp — D1 does NOT touch that one;
  ControllerConfig is `FPN<F>`, so the design's `v.w` is right.)
- **Why this matters for determinism:** `FPN<64>` is 24 bytes = `w[2]` (16B) + `sign` (4B) +
  **4B tail padding**. D1's field-wise `put(w)` + `put(sign)` deliberately **excludes that 4B
  pad** from the hash — which is exactly the H12 point. Serializing the FPN as a raw blob would
  re-introduce the padding bug. The field-wise choice is load-bearing, not stylistic. ✅
- Raw-limbs-vs-ToDouble (plan decision d): **raw limbs is correct** — `FPN_ToDouble` is lossy +
  involves FP combination; raw `w[]` is exact + bit-deterministic. ✅

**Coverage-sentinel design (the real open question #1):**
- The proposed `static_assert(sizeof(ControllerConfig<64>) == EXPECTED_CFG_SIZE)` is **necessary
  but NOT sufficient.** sizeof is invariant under field **reordering** and under a **type-swap of
  equal size** (e.g., `int32_t a` → `int32_t b`, or two adjacent same-size fields transposed):
  the canonicalizer's field list would silently disagree with the struct while sizeof stays equal.
  **Recommendation (MEDIUM): pair sizeof with a field-by-field _offset_ sentinel** — a block of
  `static_assert(offsetof(ControllerConfig<F>, fee_rate) == EXPECTED_OFF_FEE_RATE)` per
  serialized field (or at minimum the first + last + each FPN/string field). Offsets catch
  reorder + insertion + type-size-preserving swaps that sizeof misses. A field-COUNT alone is
  weaker than offsets and is subsumed by them. This is the one substantive design gap.
- `EXPECTED_CFG_SIZE` / `MAX_CFG_STR` / `NUM_CORES` do **not exist yet** (grep-empty) — fine for a
  design, but two naming reconciliations at impl: (i) the loop should bound on the real constant
  **`MAX_EXECUTION_CORES` (=16, `Limits.hpp:19`, compile-time `#define`)**, not the non-existent
  `NUM_CORES`; (ii) `EXPECTED_CFG_SIZE`/`MAX_CFG_STR` must be introduced as named constants.
- DESIGN_SPEC to extend (open-q #1): the referenced `struct-padding-determinism-pattern.md`
  **does not exist as a file** in DESIGN_SPECS (fd-empty). Either it's mis-named (verify the real
  spec name before citing) or this canonicalizer + offset-sentinel discipline is itself the
  first canonical instance worth codifying. Flag for the doc-capture step, not a code blocker.

**H11 (constant-iter, branchless within reductions) on the `cores[]` walk — CORRECT discipline.**
The walk is `for (i=0; i<MAX_EXECUTION_CORES; ++i)` — `MAX_EXECUTION_CORES` is a compile-time
`#define` (16), so the trip count is constant and the compiler fully unrolls (same property
FixedPointN.hpp relies on for its `w[N]` loops). H11 is satisfied. There is no *reduction* here
(it's a serialization append, not a sum), so "branchless within reductions" is vacuously fine —
the relevant H11 sub-property is **constant-iteration**, which holds. ✅ Minor note: if any core
is "inactive," the canonicalizer should still serialize all `MAX_EXECUTION_CORES` slots
unconditionally (constant work, no data-dependent `if (core_active)` branch) so the byte image is
position-stable — confirm the impl does NOT early-break on active-count.

---

## 3. D2 parse latency / alloc / DOD

- **Alloc-free**, no `std::string`, `from_chars` over a caller span — H1/H5 clean. ✅
- `from_chars` is THE fast locale-immune core; passing explicit `n` skips the `strlen` the
  NUL-terminated `parse_double_fast` pays. Contract-wise `n` (explicit length) is the **right
  choice** for slice parsing (JSON spans, REST field extents) — matches the existing
  `parse_double_fast_n` precedent. (open-q c answer: `n` is correct; keep a NUL-terminated
  convenience overload only if a caller genuinely lacks the length.)
- by-value struct return: **DOD-correct, register-pair, no spill** (confirmed §1). ✅
- `from_chars<integer>` does signed + range checking natively (returns `result_out_of_range`) —
  the design's claim is accurate; `ParseI<T>` for int32/int64/uint32/uint64 is sound. ✅
- **`from_chars` does NOT support `bool`** — the skill prompt mentioned `ParseDbool`/`parse_bool`
  but the design body does NOT propose one (only double + integer). Good — a bool variant would
  need its own `"0"/"1"/"true"/"false"` matcher, NOT `from_chars`. If a checked bool parse is
  wanted later, it's a separate small function; do not try to route bool through `from_chars`.

**Open-q #2 (deprecate `parse_double_fast` unchecked, or keep both?):**
**KEEP BOTH — the evidence forces it.** The unchecked `parse_double_fast` family is the
already-validated-cursor fast path; its only per-tick-adjacent consumer (BinanceCrypto) actually
bypasses even that via `FPN_FromString`, but other already-validated internal cursors (stamp
fields the writer just emitted, etc.) legitimately want no error branch. The `_checked` family is
for **untrusted external input** (cfg files, REST responses, replay logs) where silent-0 is money
corruption. These are two different contracts, not redundancy — keeping both is SSoT-clean
(distinct semantics, document the "validated → fast / untrusted → checked" rule at the call
sites). Deprecating the unchecked one would force needless error-handling onto trusted cursors.
Migration is a *call-site policy* (untrusted sites → `_checked`), not a wholesale replace.

**`_checked_advance` (open-q d):** yes — if the unchecked `parse_double_fast_advance`
(BanditLearning.hpp:576 uses it) parses untrusted multi-value streams, it needs a `_checked`
peer for symmetry (return `{value, bytes_consumed, ok}` or `{ParseD, const char* next}`). LOW
priority; add only where an untrusted advancing cursor actually exists (BanditLearning JSON state
load qualifies — it's external file input).

---

## 4. D3 / D4 (cold by construction — HFT lens trivially satisfied)

- **D3** boot-pin: one-time `setlocale` at process start. No latency surface. The GUI
  "after SDL_Init" placement is the correct hazard call (windowing libs reset `LC_*`). The
  tests-not-pinned choice is right (they flip `de_DE` to prove immunity). No HFT concern. ✅
- **D4** Python grep-CI: off-engine. The "shrinking allowlist of current 62 float + 132 int raw
  sites + new-raw-call-outside-allowlist = red build" is the correct golden-master-style standing
  gate (sister to feedback_golden_master_over_reimplemented_oracle + feedback_close_the_class_vs_
  migrate_every_site — close the class via the guard, migrate sites at a paced cadence). No HFT
  lens applies; placement in pre-commit grep (compile-free) over a CI step is the cheaper correct
  choice (open-q a/b answers: explicit committed allowlist file ✓; pre-commit grep ✓).

---

## 5. Over-engineering / cargo-cult watch (the AVOID list)

- ✅ Designs correctly DO NOT force branchless on the parser/canonicalizer. Hold that line.
- ✅ by-value POD returns over out-params — right DOD call, not over-engineering.
- ⚠ Do NOT add SIMD/AVX to D1 — config canonicalization is a one-shot stamp-time serialize of a
  few KB; H10 (SIMD-with-scalar-fallback) is irrelevant here and would be pure complexity.
- ⚠ Do NOT pre-resolve / fn-pointer-table the per-site `!ok` halt/skip/default (Class 28 is a
  HOT/SP-path discipline; these are cold error branches). Branchless-dispatch here = cargo-cult.

---

## SUMMARY (for operator triage — nothing auto-proceeds)

- **Path calibration: CONFIRMED COLD for all 4.** No HOT-PATH-FOUND. H7-strict does NOT apply;
  H11 constant-iter + DOD/alloc-free DO. The plan-body's framing is correct.
- **"Branchless?" honest answer:** already-optimal where it should be (from_chars core, by-value
  register-pair returns); branchless on the error/parse branches would be **cargo-cult** — the
  designs rightly avoid it. One *optional* LOW nicety (`&` vs `&&` for a branch-free `ok`), not
  required.
- **Latency/alloc:** both D1 + D2 are alloc-free, linear (no O(n²)), inside their cold budgets;
  D1 is a correctness upgrade over the padding-hashing status quo.
- **Real findings (not blockers — design refinements):**
  1. **MEDIUM — D1 coverage sentinel insufficient:** `sizeof==EXPECTED` misses field reorder /
     same-size type-swap. Pair with per-field `offsetof` static_asserts (catches reorder +
     insert + size-preserving swap). This is the one substantive gap.
  2. **LOW — naming:** design's `NUM_CORES` → real `MAX_EXECUTION_CORES` (Limits.hpp:19);
     `EXPECTED_CFG_SIZE`/`MAX_CFG_STR` must be defined.
  3. **LOW — doc:** cited `struct-padding-determinism-pattern.md` does not exist (fd-empty);
     verify real spec name or codify this canonicalizer+offset-sentinel as first canonical.
  4. **D2 open-qs resolved:** keep BOTH parse families (distinct trusted/untrusted contracts);
     `n`-explicit is the right contract; `from_chars` has no `bool` (don't route bool through it);
     add `_checked_advance` only where an untrusted advancing cursor exists (BanditLearning).
- **`FPN<F>` `.w[N]`/`.sign` layout in D1 `put_fpn`: VERIFIED CORRECT** against FixedPointN.hpp;
  field-wise emit correctly excludes the 4B tail padding (load-bearing for H12 determinism).
