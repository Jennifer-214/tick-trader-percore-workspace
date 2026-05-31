# /parity-check report — 2026-05-31 — money-numeric-core foundation (`.E` #11)

## Plan summary
- **Target:** `subplans/2026-05-30-v5.15.5.F.4d.1.E-money-numeric-core-foundation.md` (v0.1 DRAFT; decision SETTLED D-97/D-99..D-110).
- **Engine HEAD:** `3f415a0` (`.E.0.1` determinism-net ship, tag E.0.6), branch `feat/v5.15-live-readiness`. Tests 3241/0 (last clean build).
- **Audit scope:** stamp/wire-format + train↔serve identity (FOCUS 1-5). Read-only; no engine/workspace files written except this report.
- **Cross-check baseline:** post-`.E.0.1` protections — `Fingerprint` zero-init ctor (PARITY-035 CLOSED), `cfg_drift_compare` H12 static_assert (StampT), determinism CI (`check_determinism.sh` → pre-commit Check F), HMAC stamp body via `cfg_emit_field`.
- **Methodology:** Section M (claim→evidence): every finding cites file:line + the load-bearing excerpt, read this session.

---

## Per-focus-area verdict

| # | Focus | Verdict |
|---|---|---|
| 1 | Stamp body reshape / `%.17g` emit / StampT memcmp | **YELLOW** |
| 2 | `Fingerprint.hpp:181` raw SHA-256 over cfg struct (PARITY-035 home) | **GREEN** (with one acceptance-criterion gap) |
| 3 | HMAC verify post-retrain | **GREEN** |
| 4 | M5: binary `<2,64>` byte-identical to `.E.0.1` golden (red-build gate) | **GREEN** |
| 5 | One-time retrain — every stamped/fingerprint consumer covered | **YELLOW** |

**Overall: YELLOW** — design is sound and the M5 gate is correctly named; two material wire-format seams are under-specified in the plan body (not wrong, but not enumerated as the actual money-emit hazard). No CRITICAL. No ship-blocker that survives the plan's own pre-coding gate, *provided* the two YELLOW findings below are folded into the plan before coding.

---

## Findings by severity

### HIGH

**1. [HIGH] Money emit/compare/populate route through `FPN_ToDouble` at THREE sites; plan names only the memcmp branch (`:471`).**
The plan's stamp row (blast-radius table, line 154) cites `CfgFieldDispatch.hpp:471` (`StampT` memcmp) + "emit `%.17g`". But the LIVE money path into the HMAC-signed body is the registry-driven `tt::cfg_emit_field<T>` which for FPN does:
- `CfgFieldDispatch.hpp:348` — `snprintf(buf, cap, "%s=%.17g\n", name, FPN_ToDouble(src))` — **the actual stamp-body money emit.**
- `CfgFieldDispatch.hpp:466` — `cfg_drift_compare`: `return stamp_val != FPN_ToDouble(cfg_val)` — drift detection in double-space.
- `CfgFieldDispatch.hpp:423` — `cfg_populate_inf_field`: `inf_dst = gate ? FPN_ToDouble(cfg_src) : DstT{}` — populates `StampInferenceCfgInputs` for emit.

For decimal `FixedPoint<10,8>`, `ToDouble→%.17g→parse` re-introduces the exact binary-float imprecision the decimal type exists to eliminate (`0.1` round-trips through a double again). The wire body would carry double-imprecise money strings and drift-compare in lossy double-space. **The plan must require the decimal instantiation emit an EXACT decimal string** (the type's own `ToString` digit-walk) at all three `FPN_ToDouble` sites, not just the `:471` memcmp branch — and the `cfg_drift_compare` money branch must compare decimal-exact, not via `FPN_ToDouble`. This is the H9/wire-byte-preservation core of FOCUS 1. **Disposition: fold into plan body blast-radius (replace the single `:471` citation with `:348/:423/:466/:471`) + acceptance criterion "money emits exact decimal string at every `cfg_emit_field`/`cfg_drift_compare`/`cfg_populate_inf_field` branch".** Cross-ref: `wire-format-byte-preservation-discipline.md` Layer 3 (`fmt` column) — the decimal type needs a distinct emit branch, not the binary `%.17g`.

**2. [HIGH→accept] cfg-FILE money parse is the same convert-via-double seam as the producer D-102 — in scope but not framed as a parse-exactness fix.**
`CfgFieldDispatch.hpp:80` — `dst = FPN_FromDouble<T::F>(parse_double_fast(val))`. The plan lists `:80/242/283` as "Money cfg fields → decimal-typed" (blast-radius line 152), and correctly states the WS parse becomes exact digit-accumulate. But the cfg FILE is itself a money source (fee_rate, tp/sl_pct as authored decimals); parsing `"0.001"` via `parse_double_fast`→double→decimal loses exactness at ingest — the SAME class as D-102 (lossy intermediate in a convert path). **Disposition: plan should explicitly route the decimal cfg-parse branch through the exact `FromString` primitive (the `.E.0.3`-subsumed parse work, O-2), NOT `FromDouble`.** It's nominally covered by "decimal-typed" + O-2 subsumption, but the parse-via-double exactness hazard deserves an explicit acceptance line so it isn't silently left as `FromDouble`.

### MEDIUM

**3. [MED] Acceptance criterion for the fingerprint (FOCUS 2) asserts "padding-safe" but not the decimal type's trivially-copyable + zero-init-ctor preservation.**
`Fingerprint_Compute` (`Backtest/Fingerprint.hpp:180`) raw-hashes `ControllerConfig<F>` via `SHA256_Update(&s, cfg_ptr, cfg_size)`. PARITY-035 is CLOSED by the **constructor** `ControllerConfig() { memset(this,0,sizeof(*this)); }` (`ControllerConfig.hpp:371`) — NOT by `has_unique_object_representations` (the ledger explicitly notes the padded struct can't use that guard; a stray agent static_assert asserting it was discarded at `.E.0.1` ship-close). **Implication for this ship:** swapping ~30 money fields from `FPN<F>` (24B) to `FixedPoint<10,8>` changes the struct's size + inter-field padding profile, but the determinism survives **iff** (a) the ctor `memset` is preserved (it zeroes whatever the new layout is), and (b) `ControllerConfig<F>` stays `is_trivially_copyable` (snapshot/persist memcpy + the raw hash depend on it). Decimal `FixedPoint<10,8>` must therefore carry its own explicit `_padding=0` AND stay trivially-copyable (per `struct-padding-determinism-pattern.md`). The plan's acceptance line says "decimal struct stays zero-init/padding-safe... fingerprint stays deterministic" only implicitly via D-110/H12. **Disposition: add an explicit acceptance criterion: "`ControllerConfig` zero-init ctor preserved + `is_trivially_copyable_v<ControllerConfig<F>>` static_assert holds with decimal money fields; fingerprint determinism re-verified at epoch regen."** Cross-ref PARITY-035 closure note.

**4. [MED] FOCUS 5 — fingerprint train→serve identity: `MODEL_FORMAT_VERSION` does NOT auto-bump on the money-type reshape.**
`Fingerprint_Compute` mixes in `MODEL_FORMAT_VERSION` (`:183`) — but that constant gates the MODEL FILE serialization shape, not the cfg struct layout. The fingerprint's determinism across the epoch is fine (same cfg values → same hash post-ctor), but a model trained PRE-reshape carries a fingerprint over the OLD struct layout; a serve-time engine POST-reshape hashes the NEW layout → fingerprint mismatch. The plan's D-100 epoch + one-time retrain handles this (retrain regenerates the fingerprint), and the consumer chain (`BacktestPanels.hpp:3157` write → `ModelInference.hpp:509` read) is fully covered by retrain. **This is correct, but the plan should name the fingerprint-over-cfg-layout as one of the "every stamped/fingerprint consumer" items explicitly in the D-100 retrain checklist** so it isn't assumed. Currently the acceptance line covers stamp/model retrain + persistence but does not explicitly enumerate the `training_fingerprint` re-embed. **Disposition: add to retrain acceptance: "`training_fingerprint` re-embedded over the decimal cfg layout for every retrained model."**

### LOW

**5. [LOW] `Async.hpp:179` D-102 seam confirmed — plan citation is correct; one upstream nuance.**
Confirmed: `BinanceCrypto.hpp:744` parses `FPN_FromString<F>(price_str)` (exact), but the WS path (`Run.hpp:1374`) passes `ds.price_d` (the re-derived double) into `fan_out`, which at `Async.hpp:179` does `FPN_FromDouble<F>(price_d)` — the lossy round-trip. Plan correctly flags this (TECH_DEBT-149). Nuance: `BinanceCrypto.hpp` ALSO derives `price_d` from the FPN for TUI (line ~746 comment) — so the fix is to carry the parsed FPN/decimal straight into the `Tick` ring AND keep deriving the display double from it, not to re-parse. Plan's "carry the parsed decimal straight into the Tick ring" is the right framing. ALREADY-IN-PLAN.

---

## FOCUS 4 — M5 byte-identical gate (the load-bearing invariant): GREEN

The plan HAS the acceptance criterion (line 213): *"Binary instantiation byte-identical to `.E.0.1`'s locked golden (the net's red-build gate)."* This is enforced by the SHIPPED `.E.0.1` determinism net (`check_determinism.sh` wired as pre-commit Check F + `check_determinism_selftest.sh`; commit `3f415a0`). The gate is real, named, and continuously enforced — a binary `<2,64>` reuse that diverges from the golden = red build. **VERIFIED GREEN.** The plan's reuse-certified-bodies claim is testable by exactly this gate. No gap.

---

## Cross-cutting concern (single fix closes Findings 1+2)

Findings 1 (emit/compare via `FPN_ToDouble`) and 2 (cfg parse via `FromDouble`) are the SAME root: the radix-agnostic `tt::cfg_*_field<T>` dispatchers currently funnel ALL FPN money through binary-double conversion. The structural fix is one decision: **the decimal instantiation gets its own exact `FromString`/`ToString` branches in `cfg_parse_field` / `cfg_emit_field` / `cfg_drift_compare` / `cfg_populate_inf_field` (`if constexpr (RADIX==10)`)** — never `FromDouble`/`ToDouble` for money. This IS the O-1 strong-typing payoff: once money is a distinct type, the `is_FPN_v` branches won't match it, forcing explicit decimal branches (compile-error until written). The plan's O-1 framing already promises this; it just needs the FOUR dispatcher sites named in the blast-radius (currently only `:471` and `:80/242/283` are cited).

---

## Behavior matrix (train ↔ serve agreement, default cfg, post-reshape)

| Scenario | Trainer view | Engine (serve) view | Identical? |
|---|---|---|---|
| Money cfg value in HMAC body | `%.17g` of `ToDouble(decimal)` | parse `%.17g` → `FromDouble` → decimal | **NO (lossy)** unless Finding 1 fixed |
| cfg fingerprint over struct | raw hash, zero-init ctor, decimal layout | same ctor, same layout | **YES** (Finding 3 caveat: ctor preserved) |
| Drift compare (stamp vs runtime money) | recorded double | `!= FPN_ToDouble(cfg)` | **lossy double-space** unless Finding 1 fixed |
| `training_fingerprint` re-embed | regenerated at retrain | read at `ModelInference.hpp:509` | **YES** post-retrain (Finding 4: enumerate it) |
| Binary `<2,64>` feature bytes | `.E.0.1` golden | engine | **YES** (FOCUS 4 gate) |

---

## NOT a bug (verified-safe)
- **Fingerprint determinism across the type change** — the `memset` ctor (`ControllerConfig.hpp:371`) makes padding=0 a property of the type; ANY decimal layout stays deterministic for equal field values. PARITY-035 closure holds. (Acceptance-line gap only — Finding 3.)
- **HMAC algorithm / signature shape** — unchanged; one-time retrain at D-100 epoch is the accepted boundary (backwards-compat not a concern pre-adoption per ledger + CLAUDE.local.md). FOCUS 3 GREEN.
- **Hot-path money** — `ExecutionCore.hpp:543/549/570` muls are rare-entry-branch; decimal mul = same schoolbook-shift cost. Plan audit-confirmed; not a parity surface.

---

## Ledger note
No new `PARITY-NNN` allocated: Findings 1-4 are **plan-completeness gaps against an in-flight DRAFT** (acceptance-criterion + blast-radius enumeration), not latent code defects in HEAD — the money-decimal code does not exist yet. Per skill auto-write contract, PARITY entries are for code-resident findings; these are pre-coding plan amendments for the operator to fold. If the operator prefers a tracked ID for Finding 1 (the emit/compare double-funnel) as a ship-acceptance gate, allocate **PARITY-037** at plan-lock. Existing PARITY-035 (fingerprint) verified STILL-CLOSED; PARITY-033 (per-core fee calibration) flagged by plan for re-verify-or-paper-test — concur.
