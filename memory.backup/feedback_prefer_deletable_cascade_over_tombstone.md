---
name: feedback_prefer_deletable_cascade_over_tombstone
description: "Default to deletable-by-construction internally (registry/compiler-cascaded so deleting a part auto-propagates); reserve H21 tombstoning for the irreducible wire/persistence surface + minimize that surface"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 38ff0058-1602-47c0-af7c-627a3a4357a4
  sister_specs: [feedback_backwards_compat_not_default_concern.md, feedback_guards_compound_enforcement_is_leverage.md, feedback_structural_fix_for_recurring_class.md]
  tags: []
---

Default to DELETABLE-BY-CONSTRUCTION: structure internal designs (X-macro registries, derived masks, non-persisted fields) so deleting a "part" — a registry row, a field — cascades through every consumer automatically (the compiler regenerates them, or the dependent code vanishes with the row). Reserve H21 tombstoning for the IRREDUCIBLE wire/persistence surface ONLY, and actively minimize that surface.

**Why:** tombstones are permanent cruft — every retired-but-kept identifier (RESERVED / LEGACY_ / DEPRECATED) is forever-carried weight. H21 forces them ONLY where external visibility makes clean deletion impossible: a persisted snapshot VERSION, a persisted/wire enum CODE, an HMAC body field, an operator's cfg key — old state / un-updated nodes / signed messages carry the old meaning (Knight Capital). Everything ELSE (internal, non-persisted) CAN be clean-deleted, and a registry/compiler cascade makes that deletion auto-propagate with zero hand-cleanup. So the fewer things cross the wire/persist line, the fewer tombstones ever accrue. Operator directive (2026-06-28): *"incorporate designs going forward that dont require tombstoning, like stuff where we can just delete the associated 'part' and easily update throughout whatever the cascade is."*

**How to apply:** at design time ask *"when this gets deleted later, does the cascade auto-update?"* Internal identifier → make deletion structural (drive consumers off the registry that DEFINES it; a compile-time guard enforces coverage). If it MUST cross the wire/persist line → that's the H21 minority: tombstone it, but first ask whether it needs to be wire-visible at all (keep that boundary small + explicit). First canonical: item-4's global-flat capital checks ride `FOREACH_PER_NODE_ARRAY_OVERRIDE` (internal, non-persisted) → when E.1.2 deletes the legacy arrays, the checks vanish FOR FREE (the cascade goes the GOOD direction). COMPOSES with H21 (which governs the external surface); does not override it. Decision log D-278; design-time complement in `dead-code-and-identifier-retirement-discipline.md`.

Sisters: [[feedback_backwards_compat_not_default_concern]] (cleanest-deletion default) · [[feedback_structural_fix_for_recurring_class]] (registry + compile-time enforcement) · [[feedback_guards_compound_enforcement_is_leverage]] (the coverage guard that makes deletion safe).
