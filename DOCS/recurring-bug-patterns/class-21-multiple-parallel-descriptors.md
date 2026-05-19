---
type: ledger-template
class_id: 21
title: Multiple parallel descriptors for similar surfaces (cross-file drift)
parent_index: DOCS/RECURRING_BUG_PATTERNS.md
established: 2026-05-18
---

## Class 21 — Multiple parallel descriptors for similar surfaces (cross-file drift)

**Surface:** any subsystem where multiple structurally-similar descriptors exist (e.g., separate per-cfg-file descriptors: CfgFieldDescriptor + BacktestCfgFieldDescriptor + ControllerCfgFieldDescriptor; or multiple per-field metadata tables side-by-side).

**Symptom:** adding a feature to one descriptor (e.g., new metadata bit like RESTART_REQUIRED, new tt:: dispatch specialization for a new Kind) requires updating N parallel descriptors. Forgetting any = inconsistent behavior across surfaces (e.g., backtest cfg has SAFETY_CRITICAL modals but live cfg doesn't, or vice versa). Same Class 18 mirror shape at the descriptor level.

**Root cause:** historical organic growth — each cfg file got its own descriptor when introduced. As features accrue (RESTART_REQUIRED, SAFETY_CRITICAL, IS_SECRET, categorical applicability, etc.), each must be added to N descriptors. Drift accumulates.

**Detection:**
```bash
# Find multiple structurally-similar descriptor types:
rg "struct\s+\w+Descriptor" CoreFrameworks/ ML_Headers/ MemHeaders/
# Compare field lists; if 2+ descriptors share ~70% of fields, candidate for consolidation via discriminator pattern.

# Find consumers that switch on descriptor TYPE:
rg "switch\s*\(.*descriptor\.type|\.kind\s*==.*Descriptor" .
```

**Known instances:**
- 2026-05-14: surfaced during v5.15.5.F.4 design discussion. Pre-design considered separate BacktestCfgFieldDescriptor / ControllerCfgFieldDescriptor / SecretsCfgFieldDescriptor / TrainingCfgFieldDescriptor for the 5 cfg files; rejected in favor of ONE CfgFieldDescriptor + `lives_in_struct` discriminator + extension points (metadata bits, Kind enum values, sidecar tables). Per `DESIGN_SPECS/framework-patterns/universal-cfg-field-registry-pattern.md` + `DESIGN_SPECS/framework-patterns/categorical-tag-applicability-pattern.md` § "Cross-file cfg unification".
- **v5.15.5.F.4d planning (2026-05-14 — structural closure at the drift-detection surface)**: original Option D framing kept `FOREACH_CFG_DRIFT_CHECK` wide variant (19 entries) as a PARALLEL registry alongside `FOREACH_CFG_FIELD` post-derived-filter — preserving Class 21 risk at the drift-detection surface. Re-examined during operator consult; replaced wide-variant with **sidecar override pattern** (`FOREACH_DRIFT_OVERRIDE` ~5 entries indexed by FIELD_IDX; CFG_DRIFT_AUTOPOPULATE walks STAMP_BOUND derived filter + dispatches via override lookup). Single auto-flow path; per-field customization via small sparse sidecar; wide-variant CfgDriftCheckRegistry deprecated. Class 21 structurally closed at the auto-flow-with-overrides surface. Pattern codified in `DESIGN_SPECS/framework-patterns/sidecar-override-pattern-for-registry-auto-flows.md` (DRAFT v1.0 pending .F.4d ship); generalizable to 6 future surfaces (per-strategy custom gating, per-feature custom validation, custom cfg rendering, custom INT_ENUM parsing, per-failure-mode escalation, per-slow-path-gate evaluation). Per `DESIGN_PHILOSOPHY.md` § 1.5 (Framework discipline meta-principle) + CLAUDE.md item 31.

**Prevention:**
- **Single descriptor + discriminator pattern:** ONE descriptor type + an enum field (e.g., `LivesInStruct`) that routes data to the appropriate underlying struct. Adding a new "kind" of data = new enum value; descriptor unchanged.
- **Extension points:** metadata bitmap for feature flags; Kind enum for type-specific handling; sidecar tables for sparse per-entry data that doesn't fit the common descriptor.
- **Sidecar override pattern for auto-flowed registries** (added 2026-05-14 from .F.4d planning): when a registry has standard-case auto-flow PLUS custom-semantics cases, use a sidecar override table indexed by parent registry's FIELD_IDX + CI cross-check; NEVER a parallel wide-variant registry. See `DESIGN_SPECS/framework-patterns/sidecar-override-pattern-for-registry-auto-flows.md`. Aligns with H17 (pending invariant at .F.4d ship).
- **`/merge-scan` extension:** flag parallel descriptors with ≥70% field overlap as consolidation candidates. Extended to flag parallel registries-over-same-parent.
- CLAUDE.local.md "Going-forward rule: cross-file cfg surfaces use lives_in_struct (set 2026-05-14)" + "Framework discipline over ad-hoc (set 2026-05-14)".

**Related classes:**
- Class 18 (Mirror-incomplete plans) — same shape at function level
- Class 19 (Hardcoded instance names) — both are "N parallel things drift" — different layer
- Class 22 (Runtime cfg gating in code paths) — sibling drift class within cfg surface
