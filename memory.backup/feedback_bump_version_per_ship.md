---
name: Bump Version.hpp on every ship
description: Every tagged ship in FoxML_Trader_v2 must include a Version.hpp bump (MINOR/PATCH + STRING). Operator caught it slipping across v5.11.0 → v5.11.16.
metadata:
  type: feedback
  originSessionId: eb96e5e5-7931-48ae-9510-0b0433c695bf
  tags: [project-state, ledger-discipline]
  sister_specs: [feedback_micro_commits_compile_gated.md]
---
Every ship that creates a `vX.Y.Z` git tag in `~/code/FoxML_Trader_v2`
must bump `Version.hpp` in the SAME commit:
- `ENGINE_VERSION_MAJOR` / `_MINOR` / `_PATCH` — keep ints in sync with tag
- `ENGINE_VERSION_STRING` — exact match to the tag minus the `v` prefix
  (e.g. tag `v5.11.17` → string `"5.11.17"`)

**Why:** `ENGINE_VERSION_STRING` is the source of truth for:
- The TUI/GUI banner ("engine v5.11.17" line that operator sees on every
  boot — most visible drift signal, which is how operator caught the gap)
- Stamp body's `engine_version` field (cross-major detection at
  `ML_Headers/ModelInference.hpp:1255-1265`)
- Cross-binary-drift WARN at boot (suppressible via cfg
  `acknowledge_cross_binary_version_drift`)

When the ship-tag and Version.hpp diverge, paper-test runs become
ambiguous ("which build was this?"), stamps stay tagged with the wrong
engine version, and the boot banner advertises a stale version that
makes "did the upgrade actually deploy" hard to verify.

**How to apply:**
1. Before staging any code change for a ship, edit `Version.hpp` to
   match the tag you're about to apply.
2. Stage `Version.hpp` along with the rest of the ship's changes.
3. Tag + push.
4. If you discover after-the-fact that prior ships missed it, fold the
   bump into the next ship and note in the commit message.

**History:** v5.11.0 through v5.11.16 (17 ships) shipped without
bumping Version.hpp — string stayed at "5.10.0e". Caught at v5.11.17
in-flight (operator screenshotted the boot banner). Fixed in v5.11.17
commit by jumping straight to "5.11.17" instead of trying to backfill
intermediate values.

## Sister discipline: rename plans when ship order diverges from plan numbering

(Folded 2026-05-26 from former `feedback_rename_plans_to_match_ship_order.md`.)

When the ORDER of shipping diverges from the plan filename's PHASE numbering
(e.g., plan `phase-3` ships before plan `phase-2`, OR plan was authored as
`vX.Y.5` but actually ships as `vX.Y.7` due to inserted intermediate ships),
**rename the plan file** so its name + the ship's git tag stay monotonic.

DO NOT rename `Version.hpp` to match — Version.hpp follows the tag (above).

Rationale: plan file naming becomes the persistent record of ship sequence;
divergence makes plan archeology painful ("phase 3 plan but it was actually
the 7th ship?"). Rename keeps `ls plans/<sprint>/subplans/ | sort` reflective
of actual shipping order.

This rule co-locates with version-bump discipline since both are about
"ship metadata consistency at the moment of tagging."
