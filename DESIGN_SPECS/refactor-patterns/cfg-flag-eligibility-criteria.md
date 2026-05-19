---
type: refactor-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-10
tags: [framework-discipline, structural-fix, pattern-codification]
surface: [cfg-flow]
sister_specs: [universal-cfg-field-registry-pattern.md, categorical-tag-applicability-pattern.md, cfg-scope-discipline.md]
applies_at_skills: []
---

# Cfg-flag eligibility criteria — when a boolean is a cfg-flag candidate (and when it's not)

**Established:** 2026-05-10 (v5.14.9.F step 0 — `lat_enabled` rejection)
**Status:** ACTIVE
**Cross-references:**
- Decision framework: `heterogeneous-registry-pattern.md` (DOMAIN SPLIT — which domain does the flag belong to?)
- Mechanism: `bitmap-flag-api.md` (what a cfg-flag becomes after migration)
- Sister doc: `audit-driven-pre-coding-gate.md` (where eligibility audit happens pre-coding)
- First trigger: TECH_DEBT-023 (`lat_enabled` cautionary tale)
- CLAUDE.md item 18 (slow-path latency reduction — compile-time elision wins)

---

## Problem statement

The cfg-flag bitmap pattern (`FOREACH_<DOMAIN>_CFG_FLAG` + uint8/16 storage + BITMAP_IS_SET reads) is a powerful abstraction for engine-wide boolean toggles. But it's not universal — applying it to the wrong boolean PESSIMIZES the code:

**Cautionary tale (v5.14.9.F step 0):**

A pre-coding audit subagent flagged `lat_enabled` as a candidate for migration to `FOREACH_OMS_CFG_FLAG`. Verification revealed:

- `lat_enabled` is a per-Tick LOCAL variable, not a runtime cfg field
- It's set via `template <bool LAT_ENABLED>` template parameter
- Template + `if constexpr` eliminates the entire latency-tracking codepath at compile time when disabled
- Disabled state: ZERO instructions emitted (compile-time elision)
- Migration would replace this with a runtime `BITMAP_IS_SET` check at every hot-path read site
- Result: +1-2ns per tick perpetually, even when disabled

**Migration was REJECTED.** The eligibility criteria were codified in TECH_DEBT-023 to prevent recurrence.

This doc captures the criteria + the cautionary tale + decision algorithm.

---

## Five eligibility criteria

A boolean is a **cfg-flag candidate** iff ALL FIVE criteria hold:

### Criterion 1 — Runtime-mutable (boot-or-cfg-reload-time)

The flag's value is determined by `engine.cfg` (operator config) at boot OR at cfg-reload events. NOT compile-time-fixed.

**Pass:** `partial_exit_enabled` (operator sets in engine.cfg; engine reads at boot).
**Fail:** `LAT_ENABLED` template parameter (compile-time choice; disabled state elides codepath).
**Fail:** `__has_feature(address_sanitizer)` (compile-time intrinsic).

### Criterion 2 — Engine-wide scope (NOT hot-path-per-tick runtime state)

The flag describes a property of the ENGINE configuration, not per-tick / per-position runtime state. Per-core overrides are OK (those resolve to engine-wide-config-overridden-per-core, still cfg-driven).

**Pass:** `confidence_enabled` (engine-wide cfg; per-core override supported).
**Fail:** `Position.is_buyer_maker` (per-position runtime flag from fill event — use per-record bool or atomic flag).
**Fail:** `OrderManager.has_pending_order` (per-OrderManager runtime state — use struct field).

### Criterion 3 — Hot-path-tolerant cost

The flag is read on the slow path OR on the hot path but the `BITMAP_IS_SET` cost (~1-2ns memory load + AND + compare) is acceptable at the read site.

**Pass:** any slow-path cfg flag (slow path budget 100µs; 1-2ns is rounding error).
**Pass:** hot-path cfg flag IF the read happens once per tick AND adding 1-2ns is acceptable.
**Fail:** hot-path cfg flag that would gate a BRANCH (predictable + cmov-friendly) → branch is cheaper than memory load.
**Fail:** hot-path cfg flag that fires per-bit-per-position (40 positions × 1-2ns = significant).

### Criterion 4 — No compile-time elision benefit

The flag's DISABLED state has actual work to do (or the work is so cheap that elision is irrelevant). If disabled state could be elided to ZERO instructions via template + `if constexpr`, prefer that over runtime cfg-flag.

**Pass:** `kill_switch_enabled` (when enabled, slow-path checks loss-cap; when disabled, the check is skipped via cfg-flag — but enabled-default is the common case, so elision would forbid the operator from disabling).
**Pass:** `partial_exit_enabled` (operator-toggleable; both modes are real operating modes; can't elide).
**Fail:** `LAT_ENABLED` (disabled = ZERO code; template+if-constexpr elides perfectly; cfg-flag would re-introduce the cost at every read site).
**Fail:** `DEBUG_TRACE_ENABLED` (compile-time debug toggle; disabled state should compile to zero instructions).

### Criterion 5 — Cfg-domain-coherent

The flag semantically belongs to ONE of the established domains (LIFECYCLE / GATE / ML / RISK / OPS / future domains). If it doesn't fit a domain, audit whether a new domain is justified vs forcing into a wrong-fit existing domain.

**Pass:** `kill_switch_enabled` ∈ RISK (loss-cap safety).
**Pass:** `vol_sizing_enabled` ∈ RISK (sizing strategy).
**Fail:** a flag that mixes concerns (e.g., "enable kill switch AND scale sizing") — should be 2 flags in 2 domains.
**Fail:** a flag that doesn't fit any domain — propose a new domain in the design phase; don't shoehorn.

---

## Decision algorithm

When auditing a boolean for cfg-flag migration:

```
For each candidate boolean B:
    1. Is B runtime-mutable (cfg-driven, not compile-time)?         If NO → REJECT (criterion 1)
    2. Is B engine-wide (not per-position / per-order runtime state)? If NO → REJECT (criterion 2)
    3. Is the BITMAP_IS_SET read cost acceptable at all use sites?    If NO → REJECT (criterion 3)
    4. Would compile-time elision yield ZERO disabled-state cost?    If YES → REJECT (criterion 4 — prefer template)
    5. Does B fit a domain (LIFECYCLE / GATE / ML / RISK / OPS / new)? If NO → REJECT or PROPOSE NEW DOMAIN

If all 5 pass → MIGRATE to FOREACH_<DOMAIN>_CFG_FLAG.
If any fail → DOCUMENT in TECH_DEBT (eligibility rejection w/ rationale).
```

---

## Worked examples

### `partial_exit_enabled` → MIGRATE to FOREACH_LIFECYCLE_CFG_FLAG

1. Runtime-mutable: yes (operator sets in engine.cfg). ✓
2. Engine-wide: yes (per-core override exists; resolves to cfg-driven). ✓
3. Hot-path cost: read on slow-path at dispatcher arm; ~1ns acceptable. ✓
4. No compile-time elision benefit: operator must be able to toggle at runtime; can't elide. ✓
5. Domain: LIFECYCLE (position exit mechanics). ✓

→ MIGRATE. Lives in `FOREACH_LIFECYCLE_CFG_FLAG` (v5.14.9.F).

### `kill_switch_enabled` → MIGRATE to FOREACH_RISK_CFG_FLAG

1. Runtime-mutable: yes (operator sets). ✓
2. Engine-wide: yes. ✓
3. Hot-path cost: read on slow-path at loss-cap check; acceptable. ✓
4. No compile-time elision benefit: operator must be able to toggle. ✓
5. Domain: RISK. ✓

→ MIGRATE. Lives in `FOREACH_RISK_CFG_FLAG` (v5.14.9.F.3). Default ON (safety-first).

### `LAT_ENABLED` → REJECT (compile-time elision wins)

1. Runtime-mutable: NO (compile-time template parameter via build flag). ✗

→ REJECT at criterion 1. Stays as `template <bool LAT_ENABLED>` + `if constexpr`.

Captured in `TECH_DEBT-023` for posterity. The build system uses `-DLATENCY_PROFILING=ON` to set the template parameter; disabled state has ZERO emitted instructions.

### `breakeven_on_profit` → MIGRATE BUT DORMANT

1. Runtime-mutable: yes. ✓
2. Engine-wide: yes. ✓
3. Hot-path cost: acceptable. ✓
4. No compile-time elision: yes (operator-toggleable feature). ✓
5. Domain: LIFECYCLE. ✓

→ MIGRATE. But: zero read sites in the codebase today (operator sets it, engine ignores). Migration still applies — the bit is reserved + parsed correctly. When read sites land, the bitmap is ready. Captured in `TECH_DEBT-024` (decision: wire-up vs remove deferred).

### `is_buyer_maker` (per-order field) → REJECT

1. Runtime-mutable: yes (set per fill). ✓
2. Engine-wide: NO (per-order runtime flag). ✗

→ REJECT at criterion 2. Stays as per-order struct field. Bit-packing within per-order struct is a separate pattern (per-record bitmap; rare).

---

## Trade-offs + when to apply

This is a decision framework, not an implementation pattern. The pattern itself is `bitmap-flag-api.md` (the bitmap field) + `heterogeneous-registry-pattern.md` (the domain split). This doc tells you which booleans are CANDIDATES for those patterns.

### Apply this framework when:

- Auditing existing booleans for migration candidates (v5.14.9.F-type sprint)
- Designing a new feature that proposes a boolean (decide upfront: cfg-flag or struct field or template?)
- Triaging audit-flagged candidates (pre-coding gate via /dod-audit)

### Cost:

- Per-candidate audit: ~5-10 min (run through 5 criteria)
- One TECH_DEBT entry per REJECTED candidate (documents rationale; prevents re-flagging)

### Win:

- Prevents pessimization (the lat_enabled case)
- Forces explicit reasoning before migration
- Establishes a documented decision history (TECH_DEBT entries become precedent)

---

## Reference implementations

### v5.14.9.F sprint — 22 booleans audited

5 domain registries with 21 total entries:

| Migrated | Rejected |
|---|---|
| 3 LIFECYCLE flags | `lat_enabled` (criterion 1 — template) |
| 6 GATE flags | `LATENCY_PROFILING` (criterion 1 — build flag) |
| 7 ML flags | (other compile-time toggles) |
| 3 RISK flags | (per-record fields, e.g., `is_buyer_maker`) |
| 2 OPS flags | |

REJECTED candidates documented in `TECH_DEBT-023` (lat_enabled rationale).

---

## Lessons / gotchas

### "Move it to cfg" is not always the right call

The cfg-flag pattern is attractive — it gives operators dynamic control + centralizes state + extinguishes scattered-flag tech debt. But it's not the right tool for every boolean. Compile-time toggles (template params + if-constexpr) give ZERO disabled-state cost — perpetually. Don't trade that for cfg-driven flexibility unless operator toggle-ability is the actual requirement.

### Audit subagent false positives are common

Pre-coding audits (e.g., /dod-audit) may flag candidates that fail step 0 verification. Always verify each flagged candidate's eligibility BEFORE scope-locking the migration ship.

The v5.14.9.F audit subagent's lat_enabled flag was caught at step 0 — saving the codebase from a perpetual 1-2ns/tick regression. Subsequent audits should expect ~10-20% false-positive rate.

### Default values matter — flag direction is semantic

For RISK-domain flags, default is typically `ON` (safety-first). For OPS, default is typically `OFF` (opt-in observability). For LIFECYCLE / GATE / ML, default depends on feature maturity (mature → may default ON; experimental → default OFF).

When migrating, preserve the existing default. The default isn't part of eligibility; it's part of migration mechanics.

### Per-core override capability is criterion 2 ambiguity

If a flag has per-core override (`core_0_kill_switch_enabled`), it still passes criterion 2 (engine-wide-with-per-core-override is still engine-config-driven, not per-tick runtime state). Per-bit per-core override is supported via `PER_CORE_OVERRIDE_BITMAP_DOMAINS` (see `per-bit-per-core-override-pattern.md`).

The distinguishing line:
- Per-core OVERRIDE (cfg-driven; resolved at boot or cfg-reload) → still cfg-flag-eligible
- Per-core / per-position RUNTIME STATE (changes per tick or per fill) → NOT cfg-flag-eligible (use struct field or atomic)

### "Hot-path tolerant" is fuzzy — verify per use site

Criterion 3 is the most subjective. Verify:

- Read frequency at each use site (per tick / per order / once at boot?)
- Cost amortization (is the BITMAP_IS_SET cost dwarfed by neighboring work?)
- Branch predictor friendliness (does the flag state stay stable? Predictor handles stable cfg-flags well)

If unsure, MEASURE — run `latency-tracking` builds before + after the migration. If hot-path p99 regresses by >5%, revert the migration for that flag.

### Domain ambiguity → propose a new domain

If a flag genuinely doesn't fit LIFECYCLE / GATE / ML / RISK / OPS, propose a new domain in the design phase. Don't shoehorn into a wrong-fit domain (e.g., a "DEBUGGING" flag forced into OPS).

Cost of a new domain: 1 new registry header + 1 new uint8 field on ControllerConfig + 1 new auto-extend in GUI + 1 new entry in PER_CORE_OVERRIDE_BITMAP_DOMAINS. Bounded; mechanical.

Established domains (v5.14.9 sprint):
- LIFECYCLE: position-exit mechanics
- GATE: entry/exit gates (depth, EMA, no-trade-band, cost, barrier, param-staleness)
- ML: ML/confidence/composite features
- RISK: kill-switch, sizing, dead-time-flatten
- OPS: observability / session-filter / notifications

Adding a new domain example: `MAKER` domain for v5.X maker-orders feature flags would land here when that work begins.

---

## Audit detection

`/dod-audit` flags PROPOSED-but-not-yet-evaluated candidates by:

- Symptom: `bool` field on ControllerConfig that's NOT in any FOREACH_*_CFG_FLAG registry
- Symptom: `cfg.X_enabled` member access at 2+ call sites where X isn't already migrated

Each flagged candidate → run through the 5-criteria decision algorithm above. If migrated, append to the appropriate domain registry. If rejected, document in TECH_DEBT with the failing criterion + rationale.

The /dod-audit should NOT auto-migrate — eligibility audit is operator decision (false-positive rate ~10-20%).

---

## Cohort audit when new field has siblings (v5.14.11+)

**Established:** 2026-05-11 (v5.14.11 Decision 4 — ridge_* cohort migration)

When the cfg field being audited has 2+ SIBLINGS in the same semantic family (e.g., the new field is `ridge_online_corr` and existing siblings are `ridge_within_horizon`, `ridge_across_horizons`, `exit_blender_mode`), run the 5-criteria framework on the COHORT, not just the new field.

### Why cohort matters

Running the framework on the new field alone risks creating intra-family inconsistency — itself a tech-debt class. The v5.14.11 example illustrates:

`cfg.ridge_online_corr` was proposed as a new bool ML cfg field. Framework verdict on the new field alone: all 5 criteria pass → MIGRATE to FOREACH_ML_CFG_FLAG. But codebase precedent showed 3 existing siblings (ridge_within_horizon, ridge_across_horizons, exit_blender_mode) stayed as direct int cfg fields despite v5.14.9.F.2 / v5.14.10.B migration sweeps. Root cause uncertain (possibly oversight — these passed criteria too).

Migrating ONE field of a 4-field cohort creates "1 in bitmap, 3 direct" inconsistency:
- Increases cognitive load (operators need to know which ridge_* uses which storage)
- Splits the FOREACH_STAMP_BOUND_CFG entries between DIRECT_FIELD + BITMAP_BIT emit_source
- Breaks the consistency the registry pattern is designed to provide

### Cohort audit steps

1. **Identify the family.** Grep for sibling fields by:
   - Naming convention (`ridge_*`, `confidence_*`, `bandit_*`)
   - Semantic role (entry gates, sizing modes, ML toggles, observability flags)
   - Section grouping in `engine.cfg.example`
   - Stamp-binding domain group (FOREACH_STAMP_BOUND_CFG section comments)

2. **Run the 5-criteria framework on EACH sibling.** Apply each one's eligibility criteria; classify as ELIGIBLE / INELIGIBLE.

3. **Pick the outcome:**
   - **All eligible** → migrate the cohort in the same ship (intra-family consistency)
   - **Mixed eligibility** → migrate the eligible subset; auto-write TECH_DEBT entry for ineligible siblings with per-sibling rejection rationale
   - **None eligible** → document the family-wide rejection rationale in TECH_DEBT (e.g., "all `*_threshold` fields stay direct FPN because they're scalars, not booleans"); new field stays direct alongside siblings

4. **Update FOREACH_STAMP_BOUND_CFG if any cohort member is stamp-bound.** Migrated boolean siblings flip emit_source from `DIRECT_FIELD` → `BITMAP_BIT` via Y3 dispatch. Preserves HMAC chain byte-for-byte via `BITMAP_IS_SET(...) ? 1 : 0` ternary normalization (per `wire-format-byte-preservation-discipline.md` + v5.14.10 postmortem Surprise 6).

### Cautionary tale — v5.14.11

`cfg.ridge_online_corr` audit applied framework → MIGRATE. Codebase grep revealed 3 sibling fields all direct. Without cohort-audit, v5.14.11 would have:
- Migrated 1 ridge field (ridge_online_corr) to bitmap
- Left 3 ridge fields direct (within_horizon / across_horizons / exit_blender_mode)
- Created silent intra-family inconsistency
- Likely accumulated as TECH_DEBT for some future cleanup ship to discover and resolve

Cohort-audit caught this at plan-synthesis time. Decision 4 migrated all 4 ridge_* fields in v5.14.11.C. Documented in plan synthesis + auto-wrote to TECH_DEBT-017 close trigger (ridge_across_horizons "consumer added via migration").

### Generalizes to

Same shape applies to:
- FOREACH_STAMP_BOUND_CFG migration cohorts (Y3 dispatch field-by-field audit)
- FOREACH_FEATURE additions (feature-family cohorts; e.g., regime_* features)
- FOREACH_TARGET extensions (CS target families)
- FOREACH_SLOW_PATH_GATE entries (gate-family migrations when underlying cfg fields change)
- Any registry where partial migration creates intra-family inconsistency

### Cross-references

- CLAUDE.local.md going-forward rule "cohort-audit when new cfg field has siblings (set 2026-05-11)"
- v5.14.11 plan: `plans/v5.14-foxml-port-and-maker/subplans/2026-05-08-v5.14.11-online-corr-update.md` (Decision 4 cohort migration)
- v5.14.11 audit synthesis: `plans/plan_checks/2026-05-11-v5.14.11-fresh-audits-synthesis.md` (Decision 4 tension discussion)
- `DESIGN_SPECS/framework-patterns/heterogeneous-registry-pattern.md` (DOMAIN SPLIT — where the cohort lives)
- `DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md` (HMAC preservation during emit_source migration)

---

## Patterns NOT used here (and why)

### "All booleans are cfg-flag candidates"

Naïve generalization. Ignores compile-time elision opportunities + per-record fields + atomic flags. Leads to lat_enabled-class regressions.

### "Single eligibility test based on read frequency"

E.g., "if read more than 100 times/sec, it's cfg-flag-eligible." Too narrow; ignores criterion 4 (compile-time elision can give ZERO cost even at 1M reads/sec).

### Automatic migration via /dod-audit

Tempting to have the auditor migrate flagged booleans automatically. But ~10-20% false-positive rate means automation would silently regress code. Always require human review before migration.

---

## Cross-references

- `heterogeneous-registry-pattern.md` — DOMAIN SPLIT (which domain the migrated flag goes into)
- `bitmap-flag-api.md` — BITMAP_IS_SET / BITMAP_SET (the runtime API used by migrated flags)
- `audit-driven-pre-coding-gate.md` — where eligibility audits happen
- `per-bit-per-core-override-pattern.md` — per-core override for migrated flags
- FoxML_Trader_v2 `DOCS/TECH_DEBT.md` TECH_DEBT-023 — `lat_enabled` cautionary tale
- FoxML_Trader_v2 `CLAUDE.md` item 18 — slow-path latency reduction (compile-time elision pattern)
- FoxML_Trader_v2 `DOCS/CLAUDE_INVARIANTS.md` — hot/slow path discipline
