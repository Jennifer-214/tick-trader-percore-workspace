---
type: refactor-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-13
tags: [framework-discipline, structural-fix]
surface: [parser, cfg-flow, bitmap-packed]
sister_specs: [universal-cfg-field-registry-pattern.md, cfg-section-parser-state-machine.md, bitmap-flag-api.md]
applies_at_skills: []
---

# Post-parse normalize with explicit-key bitmap pattern

**Status:** SHIPPED v5.15.4.A (first application: `ControllerConfig_NormalizeForMode<F>`)
**Date opened:** 2026-05-12

---

## Problem

Config files have many fields with sensible per-mode defaults. Live mode
wants stricter defaults than paper mode (e.g., `model_verify_strict=1`
for live, `0` for paper). But the operator must be able to override
either default by explicitly setting the field — silent auto-tightening
that surprises the operator is worse than the original default.

Naïve approaches fail:
- **Static defaults by mode:** can't be done at struct-init time because
  `trading_mode` is itself parsed from the cfg file. Default-by-mode
  requires post-parse logic.
- **Always-apply if value matches default:** can't distinguish "operator
  set it to the default value explicitly" from "operator left it default."
  Both look identical at parse end.
- **Per-key sentinel value:** requires a magic value that's distinct from
  any legitimate setting; fragile for numeric fields where every value is
  legal.

## Pattern

A **bitmap of "operator set this key explicitly"** flags, set at
parser time per-key, consulted by a **post-parse normalize pass** that
applies mode-specific overrides only when the bit is unset.

```cpp
// 1. Per-key MASK_CFG_KEY_<NAME> constants (file scope or inside struct)
constexpr uint16_t MASK_CFG_KEY_MODEL_VERIFY_STRICT = 1u << 0;
constexpr uint16_t MASK_CFG_KEY_RECONCILE_MODE      = 1u << 1;
// ... reserve remaining bits for future tracked keys

// 2. Bitmap field on cfg struct
struct ControllerConfig {
    // ... existing fields
    uint8_t  trading_mode;        // discriminator (parsed normally)
    uint16_t cfg_keys_explicit;   // 0 = no keys explicit
    // ... more fields
};

// 3. Parser sets bit on explicit parse
if (strcmp(key, "model_verify_strict") == 0) {
    cfg.model_verify_strict = atoi(val);
    cfg.cfg_keys_explicit  |= MASK_CFG_KEY_MODEL_VERIFY_STRICT;
    continue;
}
// (back-compat keys that imply a tracked key also set the bit)
if (strcmp(key, "reconcile_dry_run") == 0) {
    // Translates legacy dry_run → reconcile_mode + marks RECONCILE_MODE explicit
    int dry_run = atoi(val);
    cfg.reconcile_mode    = dry_run ? 1 : 0;
    cfg.cfg_keys_explicit |= MASK_CFG_KEY_RECONCILE_MODE;
    continue;
}

// 4. Post-parse normalize applies mode-specific rules
template <unsigned F>
void ControllerConfig_NormalizeForMode(ControllerConfig<F>& cfg) {
    if (cfg.trading_mode != TRADING_MODE_LIVE) return;

    if (!(cfg.cfg_keys_explicit & MASK_CFG_KEY_MODEL_VERIFY_STRICT) &&
        cfg.model_verify_strict == 0) {
        cfg.model_verify_strict = 1;
        fprintf(stderr,
            "[live_normalize] trading_mode=live: model_verify_strict 0→1. "
            "Set explicitly in cfg to override.\n");
    }
    // ... more flip rules
}

// 5. Call from production cfg-load chain (e.g., engine boot)
ControllerConfig<F> cfg = ControllerConfig_Load<F>(path);
ControllerConfig_NormalizeForMode<F>(cfg);
// (later) LiveReadiness_Verify<F>(cfg, state);   // sees normalized values
```

## Properties this gives you

- **Explicit override semantics by default.** Operator's chosen value is
  ALWAYS respected; auto-flip only fires when key unset.
- **No magic sentinels.** Every value is legitimate; the bit tracks
  whether-it-was-set, not what-it-was-set-to.
- **Back-compat-key support.** Deprecated/aliased keys can mark the
  canonical key as explicit (e.g., `reconcile_dry_run` → marks
  `reconcile_mode` explicit; ensures operator's legacy intent honored
  even mid-migration).
- **Operator observability.** Stderr logs each auto-flip with an
  actionable hint ("Set explicitly in cfg to override"). Operators
  see what changed + why at every boot.
- **Cheap.** uint16_t = 2 bytes per cfg + 1 OR per parser-site + 1 mask-AND
  per normalize check. Boot-only cost.

## When to use

- Multi-mode cfg with mode-specific safety/operational defaults
- Operator overrides must be honored (cannot silently auto-tighten)
- Cohort of 3+ tracked keys per mode (otherwise direct check on field
  value is simpler — but the bitmap scales cleanly when the cohort
  grows; per CLAUDE.md item 20 bitmap-flag-api, bit-pack from start)
- Back-compat alias keys exist (where one key sets another)

## When NOT to use

- Single mode (no per-mode defaults)
- Defaults are operator-set per-deployment via separate file/env (no
  in-process flip rule needed)
- Cfg field value space includes a distinguished sentinel (e.g.,
  `-1 = "use mode default"`) — sentinel can substitute

## Bitmap cohort discipline

Per CLAUDE.md item 20 + CLAUDE.local.md cohort-audit rule
(2026-05-11): bit-pack from start when ≥3 tracked keys are expected.
v5.15.4 had only 2 (model_verify_strict + reconcile_mode) but the
cohort is the type "operator-tunable strict-mode keys" which has many
candidates — bit-pack avoids retrofit when next key joins.

Width selection (CLAUDE.md item 20):
- `uint8_t` for ≤8 keys
- `uint16_t` for 9-16 keys (v5.15.4 choice; 14 bits headroom)
- `uint32_t` for 17-32 keys
- `uint64_t` for 33-64 keys

## Anti-patterns

### Anti-pattern 1: Mutate at parse time

```cpp
// WRONG — flips before trading_mode is known
if (strcmp(key, "model_verify_strict") == 0) {
    cfg.model_verify_strict = atoi(val);
    if (cfg.trading_mode == TRADING_MODE_LIVE) cfg.model_verify_strict = 1;
    continue;
}
```

`trading_mode` is parsed as a separate cfg line; might appear AFTER
`model_verify_strict` in the file. Parser sees the field in
file-textual order, not logical order. Post-parse normalize is the
only correct point.

### Anti-pattern 2: Auto-flip without observability

```cpp
// WRONG — silent flip surprises operator
if (cfg.trading_mode == LIVE && !(cfg.cfg_keys_explicit & MASK_X)) {
    cfg.X = strict_value;
    // No fprintf! Operator can't tell their cfg changed.
}
```

Always log the flip with operator-actionable next-step text. Operator
should be able to read stderr + understand exactly what was tightened
without having to compare cfg-as-written to cfg-as-running.

### Anti-pattern 3: Normalize from un-trustworthy source

Don't call `NormalizeForMode` until cfg parse is fully complete (all
keys seen). Calling it during parse risks the source key not being
seen yet.

## Cross-references

- **CLAUDE.md item 20** — bitmap-flag-api (storage discipline)
- **CLAUDE.md item 13** — X-macro registry (companion when many keys
  accumulate; future option to generate the bit declarations + parser
  hooks via X-macro)
- **CLAUDE.local.md cohort-audit rule (2026-05-11)** — bit-pack from
  start when cohort eligible
- **DESIGN_SPECS/refactor-patterns/cfg-flag-eligibility-criteria.md** — sister pattern
  (when to bit-pack BOOLEAN cfg flags; distinct from
  explicit-tracking bitmap)

## Promotion criteria to CLAUDE.md

Promote when:
- ≥ 2 applications (currently 1: `ControllerConfig_NormalizeForMode<F>`)
- AND broad applicability (multi-mode cfg discipline; many candidates
  in the codebase if/when more cfg-mode-specific rules emerge)

Next application: a future v5.X mode that gates a different cfg field
based on operator-explicit-set status. AUTO_SYNC mode flipping
reconciliation-interval defaults, SHADOW mode skipping certain checks,
etc. — each adds 1 bit + 1 flip rule + reuses the same NormalizeForMode
infrastructure.
