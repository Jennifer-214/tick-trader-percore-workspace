---
type: registry-fit-audit-report
audited_plan: subplans/2026-05-30-v5.15.5.F.4d.1.E-money-numeric-core-foundation.md
audited_for: "#11 numeric-foundation unification — NEW-registry fitness (FOREACH_EXCHANGE)"
date: 2026-05-31
scope: registry:FOREACH_EXCHANGE (proposed-new in plan) + sister inspection (SymbolFilters / existing FOREACH_* catalog)
invoked_by: /precoding-audit-gate (Layer-2 subagent; read-only)
verdict: YELLOW — venue-semantics registry is correctly an X-macro, but it is NOT new (already owned by .E.1) AND seeding the FULL row + Binance row at #11 is premature
mandate: READ-ONLY (report only; no source/doc/plan edits; no git mutations)
---

# /registry-fit-audit — money-numeric-core foundation (#11) — 2026-05-31

## Summary (per-registry verdict)
- KEEP:            0
- EXTEND-SISTER:   1  (FOREACH_EXCHANGE — extend the ALREADY-DESIGNED .E.1 registry + the SymbolFilters load; do NOT author a parallel)
- RECONSIDER:      0
- DEFER-TO-.E.1:   1  (the SAME registry's TIMING — seed it where it is already owned, not at #11)

> One registry under audit (`FOREACH_EXCHANGE`), two findings on it: (1) it is a sister-EXTENSION not a new authoring; (2) its landing belongs at `.E.1`. The money type's *construction-time* need (precision/scale) is satisfiable now WITHOUT the registry.

---

## THE HEADLINE (Check 29 canonical-sister discipline)

**`FOREACH_EXCHANGE` already exists as a designed, Stage-3-first-canonical pattern owned by `.E.1` — this ship must EXTEND it, not author it new.** The plan treats it as a fresh registry it introduces (§ "Venue as SSoT" (b); acceptance criterion "✅ `FOREACH_EXCHANGE` Binance row carries…"). Ground truth:

- `DESIGN_SPECS/framework-patterns/foreach-exchange-meta-registry-pattern.md` — `stage: 3-first-canonical`, `established: 2026-05-28`, **`landing_ship: v5.15.5.F.4d.1.E.1`**. Defines the registry in `CoreFrameworks/ExchangeRegistry.hpp`, row shape `X(ENUM, AdapterT, name, sub, rate_per_min, market_hours_kind, submit_protocol)` (:48-53). **No precision / tick / lot / fee columns.**
- Already H15/H19-compliant **by design** (:108-116: Level 1, parent FOREACH_REGISTRY) and H18-sidecar-aware (:118-130). The `.E.0` handoff (`handoffs/2026-05-28-...E.0-pickup-handoff.md`) assigns its creation to ship #2 = `.E.1`.
- The money-numeric plan's NEW columns (`price_decimals` / `qty_decimals` / `tickSize` / `stepSize` / `fee_rounding` / `fee_precision`) are an **addition to a registry that does not yet exist in source** (`fd ExchangeRegistry → none`) but is already architected, spec'd, and owned one ship downstream.

**Verdict: EXTEND-SISTER (≥50% overlap → extend, per `feedback_plans_cite_sister_registry_inspection`).** This is not "build a venue registry"; it is "add columns to `.E.1`'s venue registry." That reframes the question from *should #11 have a registry* to *when does the registry land + who adds which columns*.

### Sister #2 — `SymbolFilters` (the existing runtime venue-precision struct)
`DataStream/BinanceOrderAPI.hpp:75-82` already holds `lot_step_size` / `lot_min_qty` / `lot_max_qty` / `min_notional` / **`qty_decimals`**, loaded per-SYMBOL at runtime from `/api/v3/exchangeInfo` (`BinanceOrderAPI_LoadFilters` :699-730; `qty_decimals` derived at :717). Consumed at 13+ sites (`BinanceOrderAPI.hpp:511/514/556/559`, `main.cpp:438/751/874/938/961/1061`, `ShardedLiveSafety.hpp:77/204`). The plan's own R-1 block (:138) correctly says fee_precision "extends the `SymbolFilters`/exchangeInfo load" — but the acceptance criteria and § (b) do NOT carry that extend-not-duplicate framing through. **Axis distinction (legitimate, must be stated):** `SymbolFilters` = per-SYMBOL, runtime-loaded (live source-exact); `FOREACH_EXCHANGE` = per-VENUE, compile-time semantics. These are complementary, not redundant — but `qty_decimals` lives in BOTH, so the plan must say which is SSoT for what (compile-time storage-scale guard vs runtime per-symbol quantization) to avoid a Class-21 two-sources-of-precision drift.

### Missing plan section (BLOCKING-LITE)
The plan has **no "Canonical sister registries considered" section** (Check 29 / `feedback_plans_cite_sister_registry_inspection` ship-blocker). It has a "DESIGN_SPECS extends/applies" list (:70-76) that name-drops `x-macro-registry-with-presence-dispatch.md` as the parent, but it does NOT cite `foreach-exchange-meta-registry-pattern.md` (the actual sister registry it is extending) nor `SymbolFilters`. The four exchange DESIGN_SPECS (`foreach-exchange-meta-registry-pattern` / `exchange-adapter-tt-dispatch-pattern` / `exchange-adapter-implementation-contract` / `per-exchange-submit-protocol-selection`) are invisible to this plan.

---

## Top findings

### [HIGH] FOREACH_EXCHANGE is sister-extension, not new — plan frames it as authored-here
- **File:line:** plan § "Venue as SSoT" (b) :133 + acceptance :217; vs `foreach-exchange-meta-registry-pattern.md:6` (`landing_ship: .E.1`).
- **Why:** authoring a venue registry at #11 that `.E.1` also authors = the parallel-registry trap the discipline exists to prevent. The registry's spine (enum / adapter alias / H15 enrollment / H19 topology) is `.E.1`'s deliverable.
- **Disposition:** REFRAME plan to "EXTEND `.E.1`'s `FOREACH_EXCHANGE` with precision/tick/lot/fee columns" + add the required "Canonical sister registries considered" section citing the 4 exchange specs + `SymbolFilters`.

### [HIGH] TIMING — registry premature at #11; the Binance ROW is not justified yet
- **File:line:** plan acceptance :217 ("Binance row carries {price/qty decimals, tick/lot, fee-rounding}") + § (b) "adding a venue = 1 row."
- **Why:** at #11 there is exactly ONE venue (Binance) and the registry's payoff (1-row-per-venue auto-flow, adapter dispatch) only materializes at `.E.1`+ when the multi-exchange substrate + D-3 land. A 1-row registry with no second consumer is the `<3-entries-that-haven't-grown` over-engineering shape (skill § "Anti-patterns to flag" guards against DEPRECATE-on-low-count, but this is the inverse: introducing-low-count one ship before the substrate that grows it). **What #11 actually NEEDS at construction time is the money TYPE's storage scale (10⁸) + the `static_assert(storage ≥ venue_precision)` guard — a compile-time CONSTANT, not a registry.** The plan itself says storage scale is "a fixed COMPILE-TIME constant" (:132), explicitly NOT a runtime exponent. The guard can assert against a single `BINANCE_PRICE_DECIMALS`/`BINANCE_QTY_DECIMALS` constant now; the row that holds those per-venue lands with the registry at `.E.1`.
- **Disposition:** DEFER-TO-.E.1 the registry + Binance row. At #11: a single-venue precision constant + the `static_assert` guard (D-106 fail-loud satisfied) + `FPN_Quantize` keyed off `SymbolFilters.qty_decimals` (already loaded). Fee-rounding-mode (R-1) is consumed by the accounting/paper path #11 touches — but it too can be a named constant until the venue registry exists. **Verdict: the Binance row alone does NOT justify the registry now; a single-venue constant + guard does the construction-time job, registry seeds at `.E.1` where the 2nd venue makes it pay.**

### [MED] static_assert(storage ≥ venue_precision) — shape under-specified (no row to assert over yet)
- **File:line:** plan § (c) :134 + acceptance :217; D-106 / R-1.
- **Why:** the guard is correctly conceived (compile-time, fail-loud, READ-the-invariant-from-source not ASSUME). But D-106 binds it to "**per exchange row**" — and there is no row at #11. As written it cannot be a per-row `static_assert` (the FOREACH_EXCHANGE rows don't exist until `.E.1`). Shape at #11 must be `static_assert(FixedPoint<10,8>::FRAC >= BINANCE_MAX_PRECISION)` against a constant; the per-row form (`static_assert` inside a `FOREACH_EXCHANGE(X)` expansion) is the `.E.1` form. The plan conflates the two.
- **Disposition:** at #11 assert against the single-venue constant; document that the per-row assert migrates into the registry expansion at `.E.1` (the same value, relocated — no re-decision, per "defer to source authority").

### [MED] qty_decimals dual-home (SymbolFilters runtime vs FOREACH_EXCHANGE compile-time) — SSoT not declared
- **File:line:** `BinanceOrderAPI.hpp:80` (`qty_decimals`, runtime-derived) vs plan § (b) `qty_decimals` column.
- **Why:** same datum in two homes on two axes (per-symbol runtime vs per-venue compile-time) → without an explicit SSoT statement this is a latent Class-21 drift (the live per-symbol value could disagree with the compile-time venue ceiling). The plan's venue-SSoT framing (storage scale ≥ widest venue; per-symbol is a narrower instantiation = trailing zeros, :132) actually RESOLVES this cleanly — but it is not stated as a precision-SSoT rule, only as a storage-scale rule.
- **Disposition:** state explicitly: compile-time venue scale = storage CEILING (the guard); runtime `SymbolFilters.qty_decimals` = per-symbol quantization granularity (the `FPN_Quantize` arg). Both true, non-overlapping roles. Fold into the "Canonical sister registries considered" section.

### [LOW] Untracked operator-facing DOCS already document FOREACH_EXCHANGE — render as "n" (B19 artifact)
- **File:line:** untracked (`git status ??`) `DOCS/CONTRIBUTING/add-exchange.md` (Step 5 + the metadata-column block), `DOCS/FAQ.md`, `DOCS/ARCHITECTURE_OVERVIEW.md`, `DOCS/GLOSSARY.md`, `DOCS/ROADMAP.md`, `DOCS/REPO_CLEANUP_GUIDE.md` — all render `FOREACH_EXCHANGE` as the literal token **`n`** (a prose-token rename over-render, B19 / TECH_DEBT-142 / Class 36 hazard). `add-exchange.md` Step 5 also shows the canonical row shape with NO precision/fee columns, confirming the column-collision.
- **Why:** not blocking for #11 (these are untracked, not this ship's surface), but when #11 extends the row shape these docs' row examples will be stale + the `n`-render must not be propagated. Flag for the doc cohort at whichever ship lands `FOREACH_EXCHANGE` (= `.E.1`).
- **Disposition:** out-of-scope for #11 code; note for `.E.1` operator-facing-doc cohort.

---

## Meta-registry enrollment / topology (H15 / H19) — if it lands
**Not a #11 gap** (registry defers to `.E.1`). For completeness: the spec already specifies H15 enrollment (Level 1, parent FOREACH_REGISTRY) and H19 topology (`foreach-exchange-meta-registry-pattern.md:108-116`). `MetaRegistry.hpp` currently has NO FOREACH_EXCHANGE row (:35-108) — correct, since the registry isn't authored yet. **If the operator overrides DEFER and lands the registry at #11**, then it MUST add the `FOREACH_REGISTRY` row (H15) `X(FOREACH_EXCHANGE, 1, FOREACH_REGISTRY, "…")` + the H18 `FOREACH_EXCHANGE_OVERRIDE` sidecar (never `FOREACH_EXCHANGE_FOR_FEES`) — and `tools/check_meta_registry.py` will red-build until enrolled. The fee/precision columns should still be REGULAR columns (uniform per-venue metadata), not a sidecar (sidecar is for sparse exchange-specific exceptions per H18).

---

## Bottom line
The venue-semantics-as-X-macro INSTINCT is right (matches `x-macro-registry-with-presence-dispatch` + D-106). But (1) the registry is **already designed and owned by `.E.1`** → EXTEND, don't author; and (2) at #11 the money type needs only a **compile-time precision constant + the `static_assert` guard**, which delivers D-106's fail-loud guarantee WITHOUT the registry. Seed `FOREACH_EXCHANGE` where the multi-venue substrate makes its 1-row-per-venue payoff real (`.E.1`); at #11, the single-venue constant + guard + `FPN_Quantize`-off-`SymbolFilters` is the lower-surface, correctly-scoped move. Add the missing "Canonical sister registries considered" section before code (Check 29 ship-blocker).
