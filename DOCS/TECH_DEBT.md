# Tech Debt — running ledger of deferred architectural items

**Established 2026-05-09 (v5.14.2.E.3).** Workspace-private (symlinked into engine repo as `DOCS/TECH_DEBT.md`).

## Purpose

Append-only ledger of known-deferred architectural cleanups + their triggers. Same shape as `PARITY_ISSUES.md` (proven mechanism) but for items that aren't bugs (operator policy: not a parity finding, not a known issue, not a recurring class). Just architectural debt that needs to live somewhere queryable.

## Why this exists

Caramel's pushback 2026-05-09 (v5.14.2.E review): "what if I forget about that stuff, like doesn't addressing the deferred items now make future maintenance easier?"

The answer is: address now if architecturally bounded; defer if separate concern. But deferred items hidden in code comments / postmortems / chat memory get forgotten. This ledger surfaces them.

`/readiness` Check 25 enforces: before declaring a ship complete, scan TECH_DEBT.md for items in the ship's surface area. If any apply, decide explicitly — address now OR refresh the entry with current cost estimate. Don't silently leave it stale.

## Format per entry

```
### TECH_DEBT-NNN — <one-line title>

- **Created:** YYYY-MM-DD by <ship that surfaced it>
- **Severity:** LOW / MEDIUM / HIGH (impact if NEVER addressed)
- **Surface:** which subsystem / file path
- **What's deferred:** 1-3 sentence description
- **Why deferred (not effort-avoidance):** explicit rationale (e.g., "wider scope than ship; operator-edge; orthogonal concern")
- **Cost estimate:** hours; LOC; risk
- **Trigger:** specific event that should prompt addressing (e.g., "next time stamp body schema changes", "before v5.X release", "when count > 5")
- **Status:** OPEN / IN-FLIGHT / CLOSED / NOT-A-BUG
- **Cross-ref:** related PARITY entries, code locations, plans

Status transitions:
- OPEN → IN-FLIGHT when ship starts addressing
- IN-FLIGHT → CLOSED when shipped
- OPEN → NOT-A-BUG if review determines it's not actually debt
```

## Status definitions

- **OPEN** — known debt, not yet scheduled
- **IN-FLIGHT** — ship in progress is addressing
- **CLOSED** — fixed in a specific ship (cite commit/tag)
- **NOT-A-BUG** — review determined this isn't actually debt

## Auto-write contract (set 2026-05-09)

When `/readiness` Check 25, `/merge-scan`, `/parity-check`, or any other audit identifies a deferral candidate, the agent **MUST** auto-write the entry here. Don't defer to "operator copies after review" — the ledger is single source of truth. Same discipline as PARITY_ISSUES.md auto-write contract (CLAUDE.local.md).

A finding that exists only in a transient audit report or chat memory gets re-discovered as noise.

## Cross-references

- `DOCS/PARITY_ISSUES.md` — sister ledger for parity findings (different class)
- `DOCS/RECURRING_BUG_PATTERNS.md` — bug class catalog
- `CLAUDE.md` item 19 — "Structural fix > direct patch when bug class can recur" (philosophy)
- `CLAUDE.local.md` — going-forward rules including this auto-write contract

## Issues

### TECH_DEBT-001 — Replace `tools/stamp_model.sh` bash CLI with thin C++ wrapper binary

- **Created:** 2026-05-09 by v5.14.2.E.3 (initial population; debt accrued since v5.10.0a.G.2)
- **Severity:** MEDIUM
- **Surface:** `tools/stamp_model.sh` (operator-side bash CLI; ~382 LOC of shell)
- **Class:** Same shape as v5.9.5b production-caller class — parallel implementation that drifts. Bash CLI duplicates the LOGIC of `stamp_write_for_model` (canonical body construction + HMAC computation + `.stamp` write) in shell, instead of CALLING the C++ function directly.
- **What's deferred:** Replace bash CLI with thin C++ wrapper binary `stamp_writer_cli` that:
  1. Parses command-line args (model_path, secret, role, etc.)
  2. Constructs `StampInferenceCfgInputs` from args
  3. Calls `tt::stamp_write_for_model` (same code path as C++ suite Train Model)
  4. Reports success/failure via exit code

  This eliminates the parallel implementation. Single source of truth in C++. Adding a new stamp body field auto-flows through:
  - C++ X-macro / manual emit code (already in place)
  - C++ wrapper binary (one CLI flag added; calls existing function)
  - Python trainers (call binary instead of bash CLI)
- **Why this is better than "catch up bash":** Catching up bash CLI is recurring debt — every new stamp body field requires bash editing in lockstep. Replacing bash CLI eliminates the class. Same philosophy as STAMP_CFG_AUTOPOPULATE (eliminate the bug class structurally).
- **Why deferred (not effort-avoidance):** Operator-edge tooling — most operators already use C++ suite Train Model button (which has full coverage). Bash CLI is for advanced users stamping Python-trained models outside the suite. The replacement requires:
  - New CMakeLists.txt target for `stamp_writer_cli` binary
  - ~150 LOC C++ wrapper (arg parse + StampInferenceCfgInputs build + call + result handling)
  - Python trainer scripts updated to call binary instead of bash
  - Documentation update (operator migration)
  - Bash CLI eventually deletable

  Cleaner long-term but requires C++ build for users who currently run the bash standalone. Defer because the C++ suite path is the primary recommended workflow.
- **Cost estimate:** ~3-4h (vs ~2h for catch-up); ELIMINATES recurring class. LOW risk (additive binary; bash stays as deprecation path).
- **Trigger:** Address when (a) operator reports CLI-stamped model rejected by engine due to missing field, OR (b) v5.X+ adds another stamp body field (would otherwise compound bash catch-up), OR (c) Python trainer scripts get refactored.
- **Bash catch-up alternative (not recommended):** ~2h of mechanical bash editing for ~18 missing fields:
  - v5.10.0a.G.2: `grid_member_count`, `grid_member_idx`
  - v5.11.41: `label_lookahead_ticks`, `label_tp_pct`, `label_sl_pct`, `xgb_train_nthread`
  - v5.14.1.B.3: 5 Ridge cfg fields, 5 composite cfg fields
  - v5.14.1.D: 2 winsor cfg fields
  - v5.14.1.E: `exit_blender_mode`
  - v5.14.2.E.2.A: `ml_buy_threshold`, `gap_acceptable_threshold`
  - v5.14.2.E.2.B: 4 architectural fields
  Recurring debt class survives.
- **Status:** OPEN
- **Cross-ref:** v5.14.1 post-mortem; v5.14.2.E.2.B commit message; CLAUDE.md item 19 (structural fix > direct patch when bug class can recur) — applies here: replace bash CLI structurally vs catching up the parallel implementation.

---

### TECH_DEBT-002 — Centralized engine `ControllerEventLoop` removal

- **Created:** 2026-05-09 by v5.14.2.E.3
- **Severity:** LOW
- **Surface:** `CoreFrameworks/ControllerEventLoop.hpp` + boot dispatch
- **What's deferred:** Legacy single_core LIVE engine path is deprecated (warns at boot per CLAUDE.md preamble). Code still exists. Legacy backtest already wraps sharded path. Removing centralized engine would clean up the codebase but requires:
  - Audit all references to centralized path
  - Update CLAUDE.md to remove centralized references
  - Migration guide for any users still on centralized path
  - Potentially breaking changes if any cfg fields were centralized-only
- **Why deferred (not effort-avoidance):** Already warned at boot; no active operator known to be using it; removal is its own ship; no architectural pressure to remove now. Path is stable + ignored, not actively maintained.
- **Cost estimate:** ~3h; MEDIUM risk (might break edge cases); should land its own dedicated ship.
- **Trigger:** Address when (a) operator complains about deprecated path warning frequency, OR (b) v6.X major-version cleanup, OR (c) maintaining centralized code blocks a refactor.
- **Status:** OPEN
- **Cross-ref:** CLAUDE.md preamble; v5.14.2.E.1 audit (confirmed: zero ensemble/single-zoo post-load code in centralized path = nothing to refactor in current scope).

---

### TECH_DEBT-003 — `verify_model_stamp` parser refactor to data-driven dispatch

- **Created:** 2026-05-09 by v5.14.2.E.3 (first noted in v5.14.1 post-mortem)
- **Severity:** LOW
- **Surface:** `ML_Headers/ModelInference.hpp` `verify_model_stamp` function (~700 LOC)
- **What's deferred:** Parser uses if-else chain over ~30 stamp body keys. Adding a new key requires manual `else if (strcmp(key, "...") == 0) { ... }` branch. Could be refactored to data-driven dispatch (table of `{key, parser_fn, has_field, value_field}`) so adding a key becomes a 1-line table entry. Same shape as FOREACH_STAMP_BOUND_CFG (which solved this for cfg-bound subset).
- **Why deferred (not effort-avoidance):** Parser is stable + works correctly. Refactor is pure cleanup, not closing bugs. v5.14.1.B.3's X-macro for cfg fields already solved the worst growth-rate subset (cfg fields). Architectural fields (4 today) added in v5.14.2.E.2.B grow slowly enough that manual is acceptable for now.
- **Cost estimate:** ~2h; MEDIUM risk (parser correctness is critical — every stamp loaded depends on it).
- **Trigger:** Address when (a) parser key count grows > 40, OR (b) operator-reports a parser bug + we want to harden the surface, OR (c) v5.X+ adds another major field family.
- **Status:** OPEN
- **Cross-ref:** v5.14.1 post-mortem; FOREACH_STAMP_BOUND_CFG (`StampBoundCfgRegistry.hpp`) shows the canonical pattern.

---

### TECH_DEBT-004 — Dual-tau cfg field naming clarity

- **Created:** 2026-05-09 by v5.14.2.E.3 (originally PARITY-006; reclassified as TECH_DEBT since not a parity issue)
- **Severity:** LOW
- **Surface:** `ControllerConfig.hpp` cfg fields `confidence_freshness_tau` (legacy IC) + `confidence_freshness_tau_secs` (composite confidence; v5.14.1)
- **What's deferred:** Two distinct cfg fields with overlapping semantics ("freshness tau"). Both have legitimate uses (one is bandit IC freshness; other is composite confidence freshness in seconds), but the names are confusable. Operator could set one when meaning the other. Either rename for clarity OR consolidate if they should genuinely be the same value.
- **Why deferred (not effort-avoidance):** Operator-facing rename is a config migration (engine.cfg files in production use the old names). Consolidation requires architectural decision (are they really the same?). Both are minor compared to other v5.X work.
- **Cost estimate:** ~3h (rename + migration code + operator notification + cfg.example update); LOW risk.
- **Trigger:** Address when (a) operator misconfigures one for the other, OR (b) v6.X major-version cfg cleanup, OR (c) someone wants to consolidate them with paired analysis.
- **Status:** OPEN
- **Cross-ref:** PARITY-006 (originally raised there); `ControllerConfig.hpp` (search for `freshness_tau`).

---

### TECH_DEBT-005 — Single-zoo hot-swap strict-mode failure handling unification

- **Created:** 2026-05-09 by v5.14.2.E.3 (surfaced during v5.14.2.E.1 design)
- **Severity:** LOW
- **Surface:** `CoreFrameworks/EngineSharded.hpp` ~line 2820 (single-zoo hot-swap validate failure handling)
- **What's deferred:** Boot does Free + null + flag on validate failure. Hot-swap does flag-only on validate failure (preserves v5.10.0c "log-and-leave" semantics; comment at 2803-2806 explicitly notes "TODO v5.10: free handle + return-from-boot to enforce refuse properly"). The asymmetry is intentional today (pre-swap state isn't snapshotted, so true rollback would require infrastructure) but ideally hot-swap would also free + null on strict refuse.
- **Why deferred (not effort-avoidance):** Pre-swap snapshotting infrastructure is significant scope (would let hot-swap properly roll back to previous model). Today's flag-only behavior is operator-tolerable + documented. v5.14.2.E.1 didn't change this; it stayed at caller level intentionally.
- **Cost estimate:** ~4-6h (snapshot infrastructure + revert logic + tests); MEDIUM risk (must not break in-flight predictions).
- **Trigger:** Address when (a) operator hits a hot-swap that breaks engine + complains about not having safe rollback, OR (b) v5.X+ ships safe-rollback infrastructure for some other purpose (could leverage), OR (c) "true safety" becomes a cfg-policy goal.
- **Status:** OPEN
- **Cross-ref:** `EngineSharded.hpp:2803-2806` comment; v5.14.2.E.1 PARITY-009.F closure (which preserved the asymmetry).

---

### TECH_DEBT-006 — `FOREACH_STAMP_BOUND_MODEL_CONST` registry for architectural fields

- **Created:** 2026-05-09 by v5.14.2.E.3 (during v5.14.2.E.2.B design)
- **Severity:** LOW
- **Surface:** `ML_Headers/ModelInference.hpp` (architectural fields added manually in v5.14.2.E.2.B)
- **What's deferred:** 4 architectural fields (`expected_num_classes`, `expected_role`, `expected_num_features`, `expected_feature_format_version`) added with manual emit + parse + populator (separate from FOREACH_STAMP_BOUND_CFG which only handles cfg-bound fields). When count grows to 5+, refactor to a parallel X-macro registry `FOREACH_STAMP_BOUND_MODEL_CONST(X)` that handles training-time/build-time-derived fields.
- **Why deferred (not effort-avoidance):** Heterogeneous value sources (label_kind mapping, role string, build constants) don't fit a uniform X-macro tuple shape cleanly. 4 fields with low growth rate is manageable manually for now. Refactoring at this small scope would add complexity without proportionate benefit.
- **Cost estimate:** ~2h to design + extract registry; LOW risk (additive refactor).
- **Trigger:** Address when count of architectural fields reaches 5+. Documented in `ModelInference.hpp` near the field declarations.
- **Status:** OPEN
- **Cross-ref:** v5.14.2.E.2.B commit; `ModelInference.hpp` ~line 1290 + ~line 1940 architectural field discipline comments.

---

### TECH_DEBT-007 — Empirically verify regime_trend_strength + regime_vol_zscore add information vs existing features

- **Created:** 2026-05-09 by v5.14.5.B (mid-coding audit follow-up; Path C decision)
- **Severity:** LOW
- **Surface:** `ML_Headers/FeatureRegistry.hpp` FOREACH_FEATURE entries `regime_trend_strength` + `regime_vol_zscore`
- **What's deferred:** v5.14.5.B ships 2 features whose semantic differs from existing ones in normalization characteristics:
  - `regime_trend_strength` (regression slope normalized to [-1,1] saturating) vs `SHORT_SLOPE` (slope/avg unbounded ratio)
  - `regime_vol_zscore` (z-score: (x-mean)/stddev; sign-carrying; bounded) vs `VOL_RATIO` (short_var/long_var; positive only ratio)

  The differing normalization MAY produce complementary training signal OR may train identically (depending on operator's data + model architecture). Without empirical verification on real training runs, we don't know which.
- **Why deferred (not effort-avoidance):** Cannot static-analyze whether features add marginal information; requires actual training metrics (feature importance scores, ablation studies, marginal predictive accuracy gain). Operator-decision rather than engineering-decision.
- **Verification trigger:** After v5.14.5 first full retrain cycle:
  - Train with all features enabled → record feature_importance scores
  - If `regime_trend_strength` importance < 0.01 AND `SHORT_SLOPE` importance > 0.05 → likely redundant
  - Same check for `regime_vol_zscore` vs `VOL_RATIO`
  - If both pass redundancy check → drop in v5.X+ ship via FEATURE_REGISTRY_HASH bump (forces operator retrain to clean schema)
  - If at least one shows complementary signal → keep + document the empirical evidence
- **Cost estimate:** ~30 min training-metric review post-first-retrain; ~30 min cleanup ship if drop indicated
- **Trigger:** After v5.14.5's first full retrain cycle (operator runs Multi-Horizon training); review feature_importance dump
- **Status:** OPEN
- **Cross-ref:** v5.14.5.B commit; `ML_Headers/FeatureRegistry.hpp` Compute fn comments cite this entry; v5.14.5.B "empirical-verification discipline" section in plan

---

## Future debt findings will append here

When `/readiness` Check 25 OR `/merge-scan` OR any audit identifies deferral candidates:
1. Assign next TECH_DEBT-NNN
2. Fill in the format template above
3. Set initial status (usually OPEN)
4. Cross-link from the audit report (`plans/plan_checks/*`)
5. Reference in commit message of the closing ship
6. Move to CLOSED only after a follow-up audit confirms regression-free
