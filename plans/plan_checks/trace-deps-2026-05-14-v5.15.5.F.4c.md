# /trace-deps report — v5.15.5.F.4c INT/INT_ENUM/BOOL migration — 2026-05-14

**Plan:** `plans/v5.15-live-readiness/subplans/2026-05-13-v5.15.5.F.4c-int-int_enum-bool-migration.md`
**Audit subagent:** Layer-2 trace-deps under /precoding-audit-gate
**Engine HEAD:** `160da10` (v5.15.5.F.4b shipped)
**Plan amendment authority:** lines 15-66 of plan body (operator-authored 2026-05-14)

---

## Summary

- Focus areas audited: 5
- NEW symbols / fns analyzed: ~18 (parser/save/render specializations, derived filter, payload macros, label arrays)
- PASS: 8
- DRIFT: 3
- GAP: 5
- DRIFT-RISK: 0
- **Exit verdict: YELLOW** — plan amendment covered the largest API-drift cases; 3 specific gaps remain in the plan body that survive the amendment (cfg_render_field still labeled "implemented in T12" but no implementation lands at .F.4c; INT_ENUM range clamp design unspecified; STAMP_BOUND derived filter mechanism unproven).

---

## Focus area 1 — FOREACH_STAMP_BOUND_CFG callsite enumeration

**Verdict: PASS / YELLOW with one open mechanism question**

Callsites enumerated (all updated through v5.14.x):

1. **Drift check at model load** — `ML_Headers/CoreModelZoo.hpp:242` (post-`verify_model_stamp` X-macro walk; compares stamp body vs cfg per row).
2. **Stamp body struct generation (parse side)** — `ML_Headers/ModelInference.hpp:1198` (`ModelStampResult.has_<name>` + value fields).
3. **Stamp body struct generation (emit side)** — `ML_Headers/ModelInference.hpp:1642`, `:1787` (StampInferenceCfgInputs).
4. **Parser branches in verify_model_stamp** — `ML_Headers/ModelInference.hpp:1400`.
5. **Auto-populate macro** — `ML_Headers/StampBoundCfgRegistry.hpp:223-250` (`STAMP_CFG_AUTOPOPULATE` / `STAMP_CFG_AUTOPOPULATE_ONE` / `HANDLE_STAMP_EMIT_DIRECT_FIELD` / `HANDLE_STAMP_EMIT_BITMAP_BIT`).
6. **Stamp helper walker** — `ML_Headers/StampHelper.hpp:150`.
7. **Field count test instrumentation** — `tests/controller_test.cpp:23333-23351` + `:3843` + `:23321` + others.
8. **Surface-context drift-check registry** — `ML_Headers/CfgDriftCheckRegistry.hpp:190` declares "stamp body itself is defined by FOREACH_STAMP_BOUND_CFG" + each X entry reads `h-><name>` (Surface G forward-compat).

**The plan's "derived filter cutover" (Step 5 / T20):** Plan refers to `FOREACH_STAMP_BOUND_CFG_DERIVED(X)` as new infrastructure that filters `FOREACH_CFG_FIELD` by the `STAMP_BOUND` metadata bit, producing a stamp-body subset macro. **No such filter exists today** — grep returns zero hits for the symbol. The only filtering mechanism in the codebase that pivots an X-macro by a column value is the `STAMP_CFG_AUTOPOPULATE_ONE` token-paste dispatch (`HANDLE_STAMP_EMIT_##emit_source` at `StampBoundCfgRegistry.hpp:237`), which dispatches per-row but does NOT filter rows in/out of the macro's preprocessor expansion.

**GAP-A (preprocessor feasibility):** C/C++ preprocessor cannot conditionally include/exclude rows by an enum-value test. The plan's "derived filter" almost certainly cannot be a `FOREACH_STAMP_BOUND_CFG_DERIVED(X)` at preprocessor time. Two viable shapes:
  - **Runtime filter:** at stamp emit time / drift check time, `FOREACH_CFG_FIELD(X)` expands fully; `X` body tests `if (g_cfg_field_descriptors[FIELD_IDX_<name>].metadata_flags & STAMP_BOUND)` and conditionally emits/checks.
  - **Token-paste dispatch:** `FOREACH_CFG_FIELD_FOR_STAMP(X)` expansion routes each row to `HANDLE_STAMP_<KIND>` or `HANDLE_STAMP_SKIP` based on a NEW per-row token column ("STAMP_YES"/"STAMP_NO"), mirroring `emit_source` discipline. Cleanest precedent in codebase.

The plan must commit to ONE shape before coding (current plan body is silent on which).

---

## Focus area 2 — 11 int-typed STAMP_BOUND fields enumeration

**Verdict: PASS** (7 int-typed, not 11; orchestrator brief overcounts — caller should verify the 11 number)

Enumeration of `int`-typed rows in `FOREACH_STAMP_BOUND_CFG` (`ML_Headers/StampBoundCfgRegistry.hpp:99-176`):

| Row | Type | Maps to cfg field | Cfg field decl | Migration candidate? |
|---|---|---|---|---|
| `ridge_within_horizon` | int | `cfg.ml_cfg_flags` bit | bitmap (uint8_t) | NO — bitmap-resident, FOREACH_ML_CFG_FLAG owns it |
| `ridge_across_horizons` | int | `cfg.ml_cfg_flags` bit | bitmap | NO — same |
| `confidence_composite_enabled` | int | `cfg.ml_cfg_flags` bit | bitmap | NO — same |
| `exit_blender_mode` | int | `cfg.ml_cfg_flags` bit | bitmap | NO — same |
| `risk_degradation_curve` | int | `cfg.risk_degradation_curve` | `int` at ControllerConfig.hpp:619 | YES — KIND_INT_ENUM (4 modes: OFF/LINEAR/EXP/STEP) |
| `bandit_algorithm` | int | `cfg.bandit_algorithm` | `int` at ControllerConfig.hpp:1228 | YES — KIND_INT_ENUM (3 modes: EXP3/THOMPSON/BOTH) |
| `trading_mode` | int | `cfg.trading_mode` | `uint8_t` at ControllerConfig.hpp:917 | YES — KIND_INT_ENUM (PAPER/LIVE/SHADOW per v5.15.2) |

**7 int-typed entries (not 11).** Of these, only 3 are migration candidates for .F.4c registry; the other 4 already live in `FOREACH_ML_CFG_FLAG` (bitmap cohort, per the plan's explicit exclusion rule at Step 2 lines 220-228).

**DRIFT-1:** Plan/orchestrator overcount. Orchestrator brief says "11 int-typed"; actual is 7 with 3 migration-eligible. Counting discrepancy isn't blocking but invalidates the "11" claim — plan should reconcile.

**DRIFT-2:** `trading_mode` is declared `uint8_t` in cfg (ControllerConfig.hpp:917) but the StampBoundCfgRegistry entry treats it as `int` via `(int)cfg.trading_mode` cast at registry expand time. If the plan migrates `trading_mode` to a KIND_INT_ENUM row in `FOREACH_CFG_FIELD`, `tt::cfg_parse_field<uint8_t>` is the dispatch path (T deduced from `cfg.trading_mode` = `uint8_t`). The stamp side stays `int` via the existing `(int)` cast at `StampBoundCfgRegistry.hpp:175`. **No actual issue** — but plan body should note the cross-binary type mismatch + clamp range (0..2 not 0..255) so the int_enum count=3 is correct.

---

## Focus area 3 — Class 14 plan-API-drift scan

**Verdict: GREEN** for amendment-flagged symbols; **YELLOW** for one symbol the amendment missed.

**Amendment-flagged (lines 15-66) — confirmed non-existent (rg returns 0 hits each):**

- `Cfg_LoadFromString` — GAP (does not exist)
- `Cfg_Save` — GAP (does not exist)
- `Cfg_LoadFromFile` — GAP (does not exist)
- `cfg_field_offset` — GAP (does not exist; was the Class 23 anti-shape helper)
- `cfg_dispatch_target<KIND>` — GAP (does not exist; was the Class 23 anti-shape helper)
- `template<Kind K> cfg_parse_field<KIND_X>(void*, ...)` — GAP (replaced by `template<typename T> cfg_parse_field(T&, ...)` per amendment)

**Amendment correctly establishes amendment authority over plan body.** Per the amendment notice "shipped code wins over plan body" rule, Step 1 + Step 6 plan-body code samples are SCOPE INTENT only.

**Amendment missed (NEW Class 14 finding):**

**GAP-B: `tt::cfg_render_field<T>` is not yet implemented anywhere.** The CfgFieldDispatch.hpp comment at `:143` says "implemented inline in GUI/SettingsPanel.hpp at T12" — but T12 has not landed. `rg "cfg_render_field"` finds only the comment + a FixedPointN.hpp doc reference. Plan Step 5 (lines 270-302) emits an `EMIT_PANEL_RENDER` macro that calls `tt::cfg_render_field<CfgFieldDescriptor::KIND_##kind>` — that's the OLD `template <Kind>` shape AND the function doesn't exist yet. Per the amendment notice's rule "code samples STALE", this is fine for SCOPE INTENT but the plan needs an explicit "implement tt::cfg_render_field<T> (T-deduced shape) FIRST" step before any `field_defs[]` migration of INT/INT_ENUM/BOOL types can succeed. Without it, the SettingsPanel render walk for new Kinds has no dispatch target. **BLOCKING — must resolve before coding starts.**

---

## Focus area 4 — tt::cfg_parse_field signature alignment

**Verdict: PASS / YELLOW for INT_ENUM**

`CoreFrameworks/CfgFieldDispatch.hpp:47-89` defines `template<T> tt::cfg_parse_field(T& dst, const CfgFieldDescriptor& desc, const char* val)`:

- `is_FPN_v<T>` branch: parse double, PCT scaling, clamp via `desc.payload.as_double.clamp_*`, FPN convert.
- `std::is_floating_point_v<T>` branch: same, plus `static_cast<T>`.
- `std::is_array_v<T>` branch: strncpy with NUL-terminate.
- `std::is_unsigned_v<T>` branch: `strtoull` + `std::clamp(v, desc.payload.as_int.clamp_min, desc.payload.as_int.clamp_max)` + `static_cast<T>`.
- Else (signed integral): `atoi` + same clamp + `static_cast<T>`.

Plan's amendment claim "integer types already covered via std::is_integral_v / std::is_unsigned_v branches" is **TRUE for KIND_INT** (covers signed + unsigned + clamp range from `desc.payload.as_int`). The current implementation works for any signed/unsigned width — the descriptor's `as_int.clamp_min/max` are int64_t and the final `static_cast<T>` narrows to the field's declared width (int8/16/32/64, uint8/16/32/64).

**GAP-C: INT_ENUM range-clamp coverage.** Plan body lines 106-118 implement KIND_INT_ENUM with explicit `if (v < 0 || v >= desc.payload.as_int_enum.count) { v = desc.payload.as_int_enum.default_val; }` semantics. The existing `tt::cfg_parse_field` integral branches clamp to `as_int.clamp_min/max` — they DO NOT read `as_int_enum.count` or `default_val`. Two viable strategies for .F.4c:
  - **Strategy A:** Per row, set `as_int.clamp_min = 0, as_int.clamp_max = count - 1` in INT_ENUM payloads. Out-of-range silently clamps to last valid value (NOT to `default_val`). Operator-visible difference vs the legacy parser at `ControllerConfig.hpp:2048-2058` (`risk_degradation_curve` WARNs + uses 0 on invalid) and `:2063-2074` (`barrier_blend_mode` same). Behavior regression unless explicitly preserved.
  - **Strategy B:** Add a Kind-aware branch in `tt::cfg_parse_field` (`if (desc.kind == CfgFieldDescriptor::KIND_INT_ENUM)` first, before integral clamp). Reads `as_int_enum.count` + `default_val`. Preserves legacy parser semantics. Pure additive specialization. Likely correct path.

Plan body silently picks A (uses `as_int_enum.count` directly in its sample); but never reconciles the legacy parser's WARN+default-on-invalid semantics. **Plan must commit to Strategy B and add a small refinement to `tt::cfg_parse_field` Kind dispatch, OR document the behavior shift explicitly.** Operator's `risk_degradation_curve='FOO'` legacy WARN path also disappears under registry dispatch (the registry has no DegradationCurve_FromString equivalent) — that's a separate cohort defer if not addressed.

**GAP-D: String-token parsing for INT_ENUM is lost.** Both `risk_degradation_curve` and `barrier_blend_mode` accept BOTH numeric ("0".."3") AND string tokens ("OFF"/"LINEAR"/"EXP"/"STEP") via DegradationCurve_FromString / BarrierBlendMode_FromString. The registry dispatcher's `atoi` (or `strtoull`) returns 0 for any non-numeric string → silently parses "LINEAR" as 0 (OFF) without the legacy WARN. **Behavior regression.** Plan must either:
  - Extend `tt::cfg_parse_field` INT_ENUM branch to check for non-numeric val + dispatch through a per-row string→int mapping (would need a new column in the registry tuple), OR
  - Explicitly accept the behavior regression + log a deprecation notice in the migration commit, OR
  - Keep `risk_degradation_curve` + `barrier_blend_mode` on manual parser (exclude from registry), defer string-token support to .F.4d.

---

## Focus area 5 — STAMP_BOUND derived filter integration plan

**Verdict: RED** — mechanism is unproven; plan must commit + prototype before coding.

Repeating from Focus area 1, but separating because it's the highest-risk Step 5 / T20:

1. **Plan claim:** `FOREACH_STAMP_BOUND_CFG_DERIVED(X)` is a new X-macro that filters `FOREACH_CFG_FIELD` rows by the `STAMP_BOUND` metadata bit — symbol does not exist in codebase today.
2. **Plan amendment scope claim:** at .F.4c, `STAMP_BOUND` flag transitions from "documented bit" → "live filter that drives the stamp body schema".
3. **Critical risk:** today, `FOREACH_STAMP_BOUND_CFG` is the SINGLE SOURCE OF TRUTH for stamp body content + HMAC-signed wire bytes. If `.F.4c` migrates that registry to be DERIVED from `FOREACH_CFG_FIELD` + STAMP_BOUND filter, ANY mistake in the filter mechanism breaks HMAC chain on all existing models (Layer-5 wire-format-byte-preservation violation).
4. **Preprocessor cannot conditionally filter X-macro rows by metadata bit at expansion time** (no constexpr-if inside `#define` expansion). The two viable shapes (runtime filter on full FOREACH walk, OR new per-row token column) require explicit plan content decisions.
5. **Mirror of HMAC-byte-preservation:** legacy stamps emit rows in a specific order; ANY change to which rows emit + their textual format must preserve byte-identical wire output OR explicitly bump MODEL_FORMAT_VERSION (Surface G allows new optional fields, NOT reordered/changed existing).

**RED — BLOCKING.** Plan must either:
- Add a Step 5b "DESIGN_SPECS doc explaining the derived filter mechanism" with a worked example BEFORE writing code, OR
- Defer the derived filter to .F.4d / a dedicated sub-ship and keep `FOREACH_STAMP_BOUND_CFG` as the manual source-of-truth for .F.4c. **Recommended.**

---

## Mirror data-flow audit (Step 6 of skill spec)

Plan body does not contain "mirror" / "duplicate this for X" / "parallel to X" keywords. Step 6 of /trace-deps skill spec doesn't apply. Skip.

---

## Per-finding triage table

| Finding | Severity | File:line ref | Plan amendment needed | Blocking? |
|---|---|---|---|---|
| GAP-A: derived filter preprocessor feasibility | RED | `CfgFieldRegistry.hpp:66` (STAMP_BOUND flag declared but no consumer) | YES — pick runtime-filter vs per-row token | YES |
| GAP-B: `tt::cfg_render_field<T>` not implemented | RED | `CfgFieldDispatch.hpp:143` (comment only) | YES — add explicit "implement render dispatch FIRST" step | YES |
| GAP-C: INT_ENUM clamp via as_int_enum.count, NOT as_int.clamp_max | YELLOW | `CfgFieldDispatch.hpp:79-88` | YES — Strategy B (add KIND_INT_ENUM branch) | Suggested |
| GAP-D: String-token parsing regression | YELLOW | `ControllerConfig.hpp:2048-2074` legacy parser | YES — pick: extend / accept regression / defer | Suggested |
| GAP-E: STAMP_BOUND derived filter wire-format byte preservation risk | RED | `ML_Headers/StampBoundCfgRegistry.hpp:99` (existing single-source-of-truth) | YES — Defer derived filter to .F.4d (recommended) OR add prototype step | YES |
| DRIFT-1: 11 → 7 int-typed STAMP_BOUND count | LOW | `StampBoundCfgRegistry.hpp:99-176` | Documentation only | NO |
| DRIFT-2: trading_mode uint8 vs int cast | LOW | `ControllerConfig.hpp:917`, `StampBoundCfgRegistry.hpp:175` | Note in plan migration | NO |
| DRIFT-3: plan amendment correctly closes Class 14 for `Cfg_*` symbols | (resolved) | amendment lines 15-66 | Already resolved | NO |

---

## Recommended plan amendments before coding starts

1. **Insert a Step 0.5: "Design lock for derived filter mechanism"** — pick one of (a) runtime filter on full FOREACH walk; (b) new per-row STAMP_BOUND_YES/NO token column with `HANDLE_STAMP_##token` dispatch (mirrors `emit_source`); or (c) **defer to .F.4d, keep `FOREACH_STAMP_BOUND_CFG` manual for .F.4c**. Recommend (c) as least-risk.
2. **Insert a Step 0.6: "Implement `tt::cfg_render_field<T>` with T-deduced shape"** — destination-by-reference, type-family static_assert, `if constexpr` branches for is_FPN_v / is_floating_point_v / is_integral_v / is_array_v. Without this, Step 5's `field_defs[]` migration for non-DOUBLE Kinds has no dispatch target.
3. **Refine Step 1 (tt:: dispatch) to call out INT_ENUM range-clamp via `as_int_enum.count` + `default_val`** — add as a new `if (desc.kind == KIND_INT_ENUM)` branch BEFORE the existing integral clamp.
4. **Pick a policy for string-token INT_ENUM legacy parsers (`risk_degradation_curve`, `barrier_blend_mode`)** — extend / accept regression / defer per Focus area 4.
5. **Reconcile "11 int-typed STAMP_BOUND fields" claim down to 7 with 3 migration-eligible** — clarify cohort in Step 2.
6. **Per CLAUDE.local.md "no MVP for plumbing/refactor work" rule:** GAP-E shouldn't ship half-done as MVP; either commit to the design + ship cleanly OR defer to .F.4d. The plan body's silence on derived filter mechanism reads as an effort-avoidance trap.

---

## Exit verdict

**YELLOW (3 RED blockers, 2 YELLOW gaps).**

Of 3 RED blockers: GAP-B and GAP-E can both be closed by deferring scope (`tt::cfg_render_field<T>` to a dedicated step inside .F.4c; derived filter to .F.4d). GAP-A becomes irrelevant if GAP-E defers.

**Concrete minimum amendment set:**
- Step 0.5: defer STAMP_BOUND derived filter to .F.4d, keep `FOREACH_STAMP_BOUND_CFG` manual for .F.4c (closes GAP-A + GAP-E together).
- Step 0.6: implement `tt::cfg_render_field<T>` first (closes GAP-B).
- Step 1 refinement: KIND_INT_ENUM branch in `tt::cfg_parse_field` (closes GAP-C).
- Step 2 cohort decision: exclude `risk_degradation_curve` + `barrier_blend_mode` from .F.4c registry rows OR add a NEW per-row "from_string" function pointer column (closes GAP-D).

With these amendments the plan becomes GREEN-eligible. **Recommend operator consults before coding.**
