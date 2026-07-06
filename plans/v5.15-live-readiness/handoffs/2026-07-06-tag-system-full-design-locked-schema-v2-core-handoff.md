---
status: active
ship: E.1.2.A
descriptor: full-design-locked-schema-v2-core-started
engine_head: d4812de
workspace_head: at-or-after-50ece69 (this close's design-docs commit)
plugin_head: e06e5d6
branch: feat/v5.15-live-readiness
plan: plans/v5.15-live-readiness/subplans/2026-07-05-E.1.2.A-comment-system-and-doc-consolidation.md
decision_log: plans/v5.15-live-readiness/decision-logs/v5.15.5.F.4d.1.E-architecture-v2.md
date: 2026-07-06
supersedes: 2026-07-06-E.1.2.A-tag-layer-built-pilot-converted-handoff.md
audit_tier: LOW
---

# E.1.2.A handoff — the in-code doc-system DESIGN is fully LOCKED · schema-v2 core BUILT · resume = the remaining schema-v2 template DESIGN, then the 6-phase build

## TL;DR — where we are

An **enormous design session** turned E.1.2.A from "tag-format proven, rest is mechanical conversion" into a **fully-designed in-house IDE toolchain** — and caught that the format was materially **incomplete** (proven on ONE comment-light file). The whole design is now **LOCKED + captured**; the schema-v2 **core is built** (the fence + the grammar-additions). What remains is **DESIGN, not mechanics** (Caramel's own correction): the detailed schema-v2 templates/sub-schemas need real grammar design, then the phased build.

**Nothing is loose.** Every decision this session is in the decision-log; every idea is in the north-star or taxonomy; the plan is re-scoped. Resume by *continuing*, never *reconstructing*.

## The two things that reframed the ship

1. **STOP the conversion — the format was incomplete (D-332).** RegimeDetector.hpp was ONE comment-light consumer; three comment-shape surveys of the real corpus (A Strategies+ML · B CoreFrameworks · C primitives/parsers/GUI; ~50 gaps) proved the v1 schema can't hold most richer-file documentation losslessly. Converting now would compress detail away + lock in a broken format. → complete the substrate BEFORE converting.
2. **The whole thing is ONE system (D-331/335/337).** Tags = the load-bearing substrate; the toolchain = ONE shared fact-producer (→ a central **C++ core**, D-337); CI = the drift-gate; the plugin = the nvim surface (the unit-**card** is its renderer). One producer, N consumers — integration is structural.

## What landed this session (all captured)

**Decision-log D-331…D-338 + the D-fmt slate** (`v5.15.5.F.4d.1.E-architecture-v2.md`):
- **D-331** integrated tag-substrate architecture · **D-332** stop-conversion/complete-substrate-first · **D-333** lossless-format requirement · **D-334** plugin rework (unit-card · HUD-vs-PANEL split (accumulate-not-replace) · graph-browser · dual-panel compare · tag-enriched/filterable/cascade trees · doc-viewer) · **D-335** the system frame (4 tool roles + the tool inventory) + code-as-queryable-graph · **D-336** toolchain root-causes (RC-A…E) + the go-forward sequence · **D-337** the central C++ toolchain core · **D-338** the version-identifier grammar (H21-safe, no history wipe).
- **D-fmt SLATE RESOLVED** (the 8 format decisions): 1 version-tags code-local + grammar · 2 ASCII 3-weight bars · 3 ASCII-UML + diagram-helper · 4 `[SECTION]_[Phase N]` label (`[REFERENCE]_[PHASE]` DROPPED; cascade → dep-tools/D-334) · 5 `[SWAR]` sub-tag of bit-packing (new **sub-tags** primitive) · 6 `[FUTURE_WORK]` + `[OUTDATED_INFO]` (manual-delete) · 7 `[DIAGRAM]_[formula]` · 8/D-338 version-grammar-forward.

**New design docs (`DESIGN_SPECS/doc-disciplines/`):**
- **`in-code-doc-system-north-star.md`** — the target IDE: 4-layer architecture · §7.5 tool inventory (✅/🟡/⬜) · the plugin-UX targets · non-goals · phased path.
- **`format-input-space-taxonomy.md`** — the schema-completion spec: all 3 surveys' ranked gap lists + the unified synthesis + the RESOLVED decisions.

**Schema v2 CORE built (`in-code-documentation-schema.md`):**
- The `\`\`\`category-set` fence now carries the v2 categories (`ROW COLUMN ASSERT OUTDATED_INFO REGION SWAR EXCLUDED SEAM` + the numeric-domain row).
- A `## v2 grammar additions` section DEFINES: sub-tags · `[OUTDATED_INFO]` · the version grammar · `[SECTION]` generalization · ASCII bars · `[DIAGRAM]_[formula]` · `[ROW]`/`[COLUMN]`.

**Plan re-scoped** — the `## ⏸ REASSESSMENT` section supersedes "mechanical conversion" with the **6-phase build**: schema-complete → propagation+templates (D-325) → dogfood corpus → toolchain (C++ core + RC-A…E) → plugin rework → convert.

## NEXT ACTION (start here) — the remaining schema-v2 DESIGN

The v2 CORE is in; the detailed **templates/sub-schemas are genuine design** (the surveys gave exemplars, not grammar):
1. **`[ROW]`/`[COLUMN]` registry sub-schema** — how a per-row annotation survives a `\`-continuation; the column tuple-legend grammar. (Survey gap #1, the biggest.)
2. **Labeled `[COMMENT]_[<label>]`** sub-sections (nesting grammar).
3. **The concurrency block** — file-narrative + cluster `Writer=/Reader=` + per-field `producer:/consumer:` (3 granularities).
4. **`[ASSERT]`** unit template (layout-lock / epoch-tripwire / remediation-message families).
5. **Wire/persist completeness** — per-field ordinals + `[EXCLUDED]` (documented-absent fields).
6. **Widened `[REFERENCE]`** prefix-zoo (PARITY / SOURCE / finding-IDs / external URLs) — needs a resolver code path per new subcat.
7. **ASCII-bar fix** in the existing v1 templates (the Unicode `——` `[COMMENT]` separators → ASCII).
8. **Version grammar** exact spec (D-338 — still an open sub-decision: structure vs terseness).
9. **`[SCHEMA]` v1 → v2 bump** once the above land.

Then the 6-phase build (phase 2 = propagate to templates + the 3-surface alignment D-325; phase 4 = the C++ core D-337).

## Homed items (NOT this close)
- **Engine `RegimeDetector.hpp` `[STATE]`/`[INIT]` banners** (:543/:627) — un-converted bare banners fail the tag-block scan → convert to `[SECTION]_[…]` when finishing the pilot conversion. (The file is the operator's uncommitted WIP; left untouched this close.)
- **Toolchain tasks #8–18** (RC-A…E · compile-DB · branchtag safety · m/M keybind · the plugin-found 128B cache-align struct) — phase 3/4 work.
- **Task #13** — the Check-P false-RED (workspace-context ENGINE/MEMORY_DIR resolution); fix so future workspace commits don't false-RED.

## Critical pickup-time reads
- `DESIGN_SPECS/doc-disciplines/in-code-doc-system-north-star.md` — the target system (read FIRST).
- `DESIGN_SPECS/doc-disciplines/format-input-space-taxonomy.md` — the schema-completion spec (the gap list to design against).
- `DESIGN_SPECS/doc-disciplines/in-code-documentation-schema.md` — v2 core done; grow the templates.
- decision-log `v5.15.5.F.4d.1.E-architecture-v2.md` — **D-331…D-338 + D-fmt SLATE RESOLVED** (this session's arc).
- the plan's `## ⏸ REASSESSMENT` + 6-phase build.

## Capture-completeness + TaskList (close verification)

**Decisions captured:** D-331…D-338 + D-fmt SLATE RESOLVED (decision-log). **New docs:** north-star + taxonomy (DESIGN_SPECS, indexed). **Schema:** v2 fence + grammar-additions. **Plan:** re-scoped to 6-phase. **Memories:** none new (all captures were decisions/design). **Independent review:** fired at close (deliverable-completeness + clobber-check across the 5 heavily-edited docs).

| # | status | task |
|---|---|---|
| 1 | in_progress | E.1.2.A umbrella — in-code documentation system |
| 19 | in_progress | Complete the schema against the taxonomy (phase 1 — the NEXT action above) |
| 8-18 | pending | toolchain (RC-A..E, compile-DB, branchtag safety, keybind, cache-align) + Check-P fix (#13) |

**PENDING (next session):** the schema-v2 template DESIGN (NEXT ACTION) → the 6-phase build.

## Pickup command
```
/accept-handoff plans/v5.15-live-readiness/handoffs/2026-07-06-tag-system-full-design-locked-schema-v2-core-handoff.md
```
