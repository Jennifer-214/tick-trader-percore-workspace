# /ml-audit — cfg↔ML surface exposure audit (verified)

**Date:** 2026-05-14
**Engine HEAD:** `82a9004` (post-v5.15.5.F.4c)
**Scope:** cfg/Settings/HMAC-stamp surface exposure gaps (narrow audit; skips parity / train-serve identity / scaler drift)
**Source:** /ml-audit Explore agent (`a105ab6c3bbe08cae`) + operator-verification pass against current code

---

## Executive summary

The "buy/sell side axis" Caramel raised post-`.F.4c` paper-test has two
possible interpretations. The audit ground out which the architecture
supports today:

- **Interpretation A — entry vs exit roles in a long-only engine:** FULLY
  SUPPORTED. The model zoo already separates roles (`buy_signal`, `barrier`,
  `regime`, `exit_predictor`) per horizon. Operators can load per-role models
  via `core_N_model_dir`. The "side" mismatch is at the cfg-SURFACE level
  (some fields are invisible / not stamp-bound), not the architecture level.
- **Interpretation B — long/short entry (true side bifurcation):** NOT
  SUPPORTED. Zero short-entry logic in the codebase; the engine is long-only.
  Adding this is a sprint-class effort (portfolio + risk + execution + OMS
  refactor), not a sub-ship.

If Caramel meant A, the fix is small (add registry rows + maybe stamp-bind a
few fields). If B, separate sprint.

The audit surfaced ~15 ML cfg fields that exist as ControllerConfig struct
fields but are NOT in `FOREACH_CFG_FIELD` (so GUI-invisible). These cleanly
fit `.F.4c.1` as an additive cohort. One audit finding ("per-core ML cfg
flag override parser not wired") was **falsified by direct grep** — the
parser IS wired via the `PER_CORE_OVERRIDE_BITMAP_DOMAINS` auto-flow at
`ControllerConfig.hpp:2686-2715`.

---

## Buy/sell side axis — interpretation matrix

| Interpretation | Architecture support today | Cfg surface gap | Severity | Effort to close |
|---|---|---|---|---|
| **A: entry vs exit roles (long-only)** | FULL — 4-role `CoreModelZoo` (buy_signal / barrier / regime / exit_predictor) per horizon in `ML_Headers/CoreModelZoo.hpp:75/970+`. `core_N_model_dir` loads role-specific models from one directory; multi-horizon ensemble per role | Some ML cfg fields (bandit / Thompson / ridge / confidence-capacity / ensemble-eta) GUI-invisible. Some stamp-bind tagging may be incomplete (needs full audit; see Findings table) | MED (small cohort of additive registry rows + targeted stamp-bind audit) | `.F.4c.1` polish + optional `.F.4d.x` stamp-bind cohort |
| **B: long/short entry (true side bifurcation)** | NONE. Zero `is_short` / `SELL_TO_OPEN` / `short_entry` / `position_side` references; `Portfolio` + `OrderGates` + `OMS` all long-only | Entire portfolio + risk + execution + OMS layer (not just cfg surface) | HIGH (architectural; 3+ ships) | Dedicated sprint post-v5.15 — out of `.F.4` umbrella scope |

**Operator decision needed:** which interpretation did the original ISSUE-2 mean? Likely A given the engine architecture, but confirm before any work loads.

---

## Findings — verified surface gaps

### HIGH severity — ML cfg fields exist in struct but NOT in FOREACH_CFG_FIELD (GUI-invisible)

Each is operator-tunable in principle (could be hand-edited in engine.cfg with `cfg.bandit_algorithm=1` etc., parser exists) but Settings panel does not render them. Adding 1 row each to `FOREACH_CFG_FIELD` per the `.F.4c` bitmap-dispatcher framework makes them auto-flow through GUI render + tooltip + per-edit persistence + per-core override.

| Field | Type | Current location | Stamp-bound? | Cohort |
|---|---|---|---|---|
| `bandit_algorithm` | int (enum: 0=EXP3, 1=THOMPSON, 2=BOTH) | `ControllerConfig.hpp:1228` | YES (`StampBoundCfgRegistry.hpp` line 99-176 region per session summary) | Bandit |
| `thompson_mu_prior` | FPN<F> | `:1229` | likely YES | Bandit |
| `thompson_precision_prior` | FPN<F> | `:1230` | likely YES | Bandit |
| `thompson_*_obs` (precision_obs etc.) | FPN<F> | nearby | likely YES | Bandit |
| `ensemble_bandit_eta` | double | `:1166` | likely YES | Bandit |
| `ridge_lambda` | FPN<F> | `:715` | YES | Ridge |
| `ridge_cost_penalty` | FPN<F> | nearby | YES | Ridge |
| `ridge_min_ic_floor` | FPN<F> | nearby | YES | Ridge |
| `confidence_freshness_tau_secs` | FPN<F> | per session summary | YES | Confidence |
| `confidence_capacity_target_dollars` | FPN<F> | per session summary | YES | Confidence |
| `confidence_capacity_kappa` | FPN<F> | per session summary | YES | Confidence |
| `confidence_rmse_baseline` | FPN<F> | per session summary | YES | Confidence |
| `winsor_pct_low` | FPN<F> | per session summary | YES | Ridge |
| `winsor_pct_high` | FPN<F> | per session summary | YES | Ridge |

(14 listed; estimate is ~15 once the full audit walks each.)

**Recommended ship:** `.F.4c.1` polish ship — add 14-15 rows to `FOREACH_CFG_FIELD`. Mechanical via the `.F.4c` bitmap-dispatcher framework — each row is `KIND_DOUBLE` or `KIND_INT_ENUM` with clamp + default + tooltip + categorical-applicability + STAMP_BOUND metadata bit (the `.F.4d` STAMP_BOUND derived filter will pick up the STAMP_BOUND-flagged subset automatically — no parallel registry needed).

**These overlap with the `.F.4d` STAMP_BOUND cohort already planned (14 fields + 4 bitmap-bools).** The original `.F.4d` plan lists 11 FPN<F> doubles + 3 ints + 4 bitmap-bools matching this list. Question: are they the SAME cohort, just timing-shifted from `.F.4d` to `.F.4c.1`? If yes, that's the cleanest move — ship them as GUI-rendered rows in `.F.4c.1`, then `.F.4d` applies the STAMP_BOUND derived filter on top. If no, this is a separate additive cohort that ships alongside `.F.4d`.

### MEDIUM severity — Stamp-bind tagging gaps for parity-critical fields

Audit flagged `confidence_enabled`, `ml_tp_pct`, `ml_sl_pct` as potentially-not-stamp-bound. Operator-verification found:

- `confidence_enabled` is a **bitmap bit** in `ml_cfg_flags` (`MlCfgFlagRegistry.hpp:53`), not a standalone struct field. Audit misclassified. Its parity-binding routes through the ml_cfg_flags bitmap-bit emit at stamp-time (the `.F.4d` two-source variant covers this).
- `ml_tp_pct` / `ml_sl_pct` — `StampBoundCfgRegistry.hpp:178` references them in a comment but their actual stamp-bind status needs careful audit (the parity-binding may route through `barrier_blend_mode` enum + per-horizon serving paths added at `v5.15.5.A`, OR may be a real gap).

**Recommended ship:** defer to `.F.4d` audit gate — the wire-format framework should make this verifiable systematically (every flagged STAMP_BOUND row's emit path is exercised; gaps surface as Layer 5b hash discrepancies or v5.14 fixture round-trip failures).

### LOW severity — Settings panel display gaps for per-core ML cfg flag overrides

The PARSER for per-core ML cfg flag overrides IS WIRED (verified at `ControllerConfig.hpp:2686-2715` via `_PARSE_OV_BITMAP_DOMAIN`); the `ml` domain at `:250` participates in auto-flow). What may be missing: Settings panel rendering of per-core ML flag overrides in the per-core tabs. Need GUI verification (operator-visible inspection) — code-only audit can't confirm without paper-test.

**Recommended ship:** verify at `.F.4c.1` paper-test; if gap real, add Settings panel rows for per-core ML flag override controls.

---

## Audit corrections (claims falsified by verification)

| Audit claim | Status | Evidence |
|---|---|---|
| "Per-core ML cfg flags override NOT WIRED (HIGH)" | **FALSE** | `ControllerConfig.hpp:2706` defines `_PARSE_OV_BITMAP_ROW_ml`; `:2712` expands `PER_CORE_OVERRIDE_BITMAP_DOMAINS` over all 5 domains including `ml`. Parser auto-flows per-core ML flag overrides. |
| "confidence_enabled NOT stamp-bound (MEDIUM)" | **MISCLASSIFIED** | confidence_enabled is bitmap bit in ml_cfg_flags (`MlCfgFlagRegistry.hpp:53`), not standalone field. Stamp-binding routes through ml_cfg_flags bitmap-bit emit (handled by `.F.4d` two-source variant). |

The audit's other findings remain CONFIRMED on direct grep:
- bandit_algorithm + thompson_* + ridge_* + ensemble_bandit_eta fields exist in ControllerConfig.hpp but NOT in CfgFieldRegistry.hpp (verified via paired greps)

---

## Recommended ship sequence

### `.F.4c.1` polish ship (current next ship — small, bounded)

**Now adds three concerns:**

1. **ImGui widget-ID label collision structural fix** (already drafted in `.F-paper-test-fixes.md` ISSUE-1 section): `tt::cfg_render_field<T>` wrap with `PushID(desc.cfg_field_name)`. Closes the runtime regression that's blocking paper-test verification.
2. **Add 14-15 missing rows to `FOREACH_CFG_FIELD`** (bandit / Thompson / ridge / confidence-capacity / ensemble-eta cohort). Mechanical via the `.F.4c` framework. Reset+Modified UI from the bundled items list lights up these rows automatically (cfg_assign / cfg_diff already shipped).
3. **Bundled items from `.F.4c` deferrals:** `reconcile_dry_run` HAS_SIDE_EFFECT tagging, `use_real_money` custom render hook design (or defer that single item to `.F.4d` sidecar pattern).

Effort estimate: small structural fix + 14-15 additive registry rows. Risk: LOW.

### `.F.4d` wire-format framework (unchanged)

Plan body already covers the STAMP_BOUND derived filter cohort migration. If the 14-15 rows added at `.F.4c.1` are STAMP_BOUND-flagged at registration time (via the metadata bit), `.F.4d`'s derived filter framework picks them up automatically — no double-work, no parallel registry.

**Decision deferred to `.F.4d` audit gate:** whether to also add stamp-bind rows for `ml_tp_pct`/`ml_sl_pct` if the careful audit confirms a gap (or whether they're already routed via barrier_blend_mode / per-horizon serving path).

### NO `.F.4d.1` for the side axis after all (under Interpretation A)

Per the interpretation matrix above, if Caramel meant Interpretation A (entry vs exit roles), the architecture already supports it. The "side axis" is really "make the existing per-role models GUI-visible + cfg-tunable + stamp-bound" — which the `.F.4c.1` + `.F.4d` work already does.

If Caramel meant Interpretation B (long/short entries), a dedicated sprint post-v5.15 close is needed. Out of scope for current `.F.4` umbrella.

---

## Process discipline — preventing the cfg↔ML mismatch class going forward

Per CLAUDE.md item 19 + 31 + `DESIGN_PHILOSOPHY.md` § 1.5 (Framework discipline meta-principle):

### Proposed Class 24 entry in `DOCS/RECURRING_BUG_PATTERNS.md`

```
Class 24 — Capability-cfg surface mismatch.

ML capability exists in code but cfg / Settings / stamp / drift-check
surface doesn't expose it. Operator can't configure, observe, or verify.

Detection: grep capability mentions in ML_Headers/ + Strategies/ against
FOREACH_CFG_FIELD rows. Each ML capability should have:
  (a) cfg parse — operator-settable key (engine.cfg + per-core override)
  (b) Settings render — GUI row via tt::cfg_render_field<T>
  (c) HMAC stamp — STAMP_BOUND metadata bit if parity-relevant
  (d) Per-core override — wired via PER_CORE_OVERRIDE_BITMAP_DOMAINS or
      core_<name>[] array if scalar

Prevention: framework discipline meta-principle (item 31) — every
ML capability is a registry row; downstream surfaces auto-flow. New
going-forward rule below makes the discipline explicit at PR-review time.

History:
- v5.15.5.F.4c paper-test surfaced bandit / Thompson / ridge /
  confidence-capacity cohort missing from FOREACH_CFG_FIELD (operator-
  invisible despite struct fields existing)
```

### Proposed going-forward rule for `CLAUDE.local.md`

```
- **Cfg↔ML surface-alignment audit at every ML feature add** (set 2026-05-14).
  → DOCS/RECURRING_BUG_PATTERNS.md Class 24; DESIGN_PHILOSOPHY.md § 1.5.
  Trigger: any new ML capability (model role, ensemble dim, bandit algo,
  blender, confidence component, regime knob) → answer four columns: cfg
  parse? Settings render? Stamp tag? Per-core override? Any "no" without
  documented exemption = feature not done. Fire /ml-audit at sub-ship close
  for any ship touching ML capability.
```

### Optional new skill: `/cfg-ml-alignment`

Lightweight scan that for a given ML capability (passed as argument or
auto-derived from recent git diff in `ML_Headers/`), checks all four
columns. Reports gaps as YELLOW with file:line refs. Lighter than `/ml-audit`
(narrow scope, no parity/train-serve sweep).

Defer skill creation until after second ML feature add — verify the rule
fires correctly before automating it.

---

## NOT a finding (verified-safe)

- Per-core ML cfg flag override parser — wired via `PER_CORE_OVERRIDE_BITMAP_DOMAINS` auto-flow (audit false positive)
- `confidence_enabled` stamp-bind — routed via ml_cfg_flags bitmap-bit emit (audit misclassified)
- 4-role CoreModelZoo (buy_signal / barrier / regime / exit_predictor) — operator-loadable via `core_N_model_dir`; role-aware discovery at `CoreModelZoo.hpp:626-690`
- Multi-horizon ensemble per-core overrides (`core_N_horizon_list`, `core_N_ensemble_blend_mode`, `core_N_disabled_horizons`) — exist in cfg + struct; per `ControllerConfig.hpp:1027-1029`

---

## Next actions (pending operator greenlight)

- [ ] Caramel confirms buy/sell interpretation = A (entry vs exit roles)
- [ ] If A confirmed: `.F.4c.1` plan section in `.F-paper-test-fixes.md` extended with the 14-15 missing-row cohort (currently only has ImGui fix + bundled items)
- [ ] If B confirmed: separate post-v5.15 sprint scoped (out of current umbrella)
- [ ] `CLAUDE.local.md` going-forward rule added
- [ ] `DOCS/RECURRING_BUG_PATTERNS.md` Class 24 entry added
- [ ] `/cfg-ml-alignment` skill — defer; revisit after second ML feature add
