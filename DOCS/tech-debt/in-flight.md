---
type: ledger-template
parent_index: DOCS/TECH_DEBT.md
covers: IN-FLIGHT-status TECH_DEBT entries (being addressed in an active sub-ship)
established: 2026-05-18
---

# TECH_DEBT — IN-FLIGHT entries

Sub-file for TECH_DEBT entries with `IN-FLIGHT` or `IN PROGRESS` status — actively being addressed by the in-flight sub-ship. Entries here should flip to CLOSED (and move to `closed.md`) at sub-ship close.

External cross-refs use canonical ID format `TECH_DEBT-NNN`. The ID is preserved across sub-files; `rg "TECH_DEBT-NNN"` finds the canonical entry in the appropriate sub-file automatically.

---

## Issues

### TECH_DEBT-063 — SettingsPanel.hpp `field_defs[]` full elimination (in-progress)

- **Created:** 2026-05-14 by v5.15.5.F.4c session (operator UX considerations conversation)
- **Severity:** LOW (each removal is mechanical; cumulative impact is significant GUI bloat reduction)
- **Surface:** `GUI/SettingsPanel.hpp` lines 48-274 — currently ~213 entries hand-maintained in `field_defs[]` array; `.F.4a/.F.4b` removed ~40 (KIND_DOUBLE/_PCT cohort migrated to FOREACH_CFG_FIELD); `.F.4c` removes ~50-60 (INT/INT_ENUM/BOOL cohort); `.F.4e` removes the remaining ~110 (STRING/FILE_PATH cohort).
- **What's deferred:** as each cohort migrates to `FOREACH_CFG_FIELD`, the corresponding `field_defs[]` entries delete (Step 4 of each migration ship). Target: `field_defs[]` = 0 entries post-`.F.4e`; entire array + supporting `CfgFieldDef` struct + manual render loop deleted; replaced by `FOREACH_CFG_FIELD` walker via `tt::cfg_render_field<T>` dispatch.
- **Why deferred (not effort-avoidance):** sequencing is forced — `field_defs[]` entry deletion happens IN the same ship that migrates the corresponding field to `FOREACH_CFG_FIELD`. Not a separate effort; embedded in cohort migration work.
- **Cost estimate:** ~5 min per cohort batch (mechanical deletion in Step 4 of each ship).
- **Trigger:** progresses with `.F.4c`/`.F.4e` migration cohorts. Verified zero at `.F.4e` ship via test: `static_assert(sizeof(field_defs) == 0)` or `field_defs` declaration deletion + grep verification.
- **Status:** IN PROGRESS — `.F.4a` removed initial ~40 (KIND_DOUBLE/_PCT cohort); `.F.4c` in flight will remove ~50-60 more (KIND_INT/_ENUM/_BOOL scalar Kinds via bitmap-dispatch walker replacing parallel-array indirection — see `.F.4c` plan body amendment + DESIGN_SPECS/framework-patterns/universal-registry-bitmap-dispatcher-pattern.md); `.F.4e` removes the remaining ~110 (KIND_STRING/_FILE_PATH). After `.F.4e` ships: field_defs[] = 0; `CfgFieldDef` struct + manual render loop + parallel-array layer all delete; SettingsState shrinks to model-scan + per-core override structures only.
- **Cross-ref:** sister to `.F.4c` (KIND_INT/_ENUM/_BOOL migration; bitmap-dispatch walker replaces field_defs[] auto-extender for scalar Kinds); `.F.4e` (KIND_STRING/_FILE_PATH migration; final field_defs[] elimination); `DESIGN_SPECS/framework-patterns/universal-registry-bitmap-dispatcher-pattern.md` (codifies the dispatcher pattern; first canonical application at `.F.4c`); `plans/_future/2026-05-14-headless-first-orientation.md` (deferred option).

---

### TECH_DEBT-092 — X_GEN_* namespace collision CI check (FOREACH_METADATA_BIT vs FOREACH_LIVES_IN_STRUCT lname overlap protection)

- **Created:** 2026-05-17 (at v5.15.5.F.4d.1.A Path γ+ v2 triage — Finding 6 from `plan_checks/2026-05-16-v5.15.5.F.4d.1-tech-debt-audit-findings.md` + D2 audit recommendation)
- **Severity:** LOW (future-protection; doesn't fire at HEAD — no overlap today between the 11 FOREACH_METADATA_BIT lnames + 5 FOREACH_LIVES_IN_STRUCT lnames; protects against future addition that accidentally creates collision)
- **Surface:** `CoreFrameworks/CfgFieldRegistry.hpp` — co-locate with existing static_asserts at lines 212 (bitmap-overflow) + ~220 (H16 compile-time enrollment per Path γ at `.A` Step 5). Compile-time static_assert that no `lname` token appears in BOTH `FOREACH_METADATA_BIT` (line 1064-1075) AND `FOREACH_LIVES_IN_STRUCT` (line 1101-1106). Mechanism: hash-based comparison via constexpr string-hash X-macro reduction + compile-time uniqueness check.
- **What's deferred:** Implement the static_assert + accompanying test. Path γ+ v2 LOCKED scope at `.A` adds this static_assert per Caramel triage 2026-05-17 (it's part of Step 5 H16 + extension scope) — so technically NOT deferred; lands at `.A`. Entry exists as TECH_DEBT for accounting + cross-ref. **Status MOVE TO IN-FLIGHT at `.A` coding; CLOSED at `.A` ship close.**
- **Why deferred (not effort-avoidance):** Lands at `.A`; this entry tracks the work for audit + ledger accounting.
- **Cost estimate:** ~10-15 min at `.A` Step 5 (compile-time static_assert + 1 CI test verifying current state). LOW risk (compile-time only; no runtime).
- **Trigger:** **`.F.4d.1.A` ship — IN-FLIGHT now. CLOSED at `.A` ship close.**
- **Status:** **IN-FLIGHT at `.F.4d.1.A` Path γ+ v2 implementation 2026-05-17** (originally OPEN at logging; promoted to IN-FLIGHT per Path γ+ v2 LOCKED scope per Caramel triage)
- **Cross-ref:** `plan_checks/2026-05-16-v5.15.5.F.4d.1-tech-debt-audit-findings.md` Finding 6 + Path γ+ v2 LOCKED scope (origin); `plan_checks/d2-foreach-lives-in-struct-verification-2026-05-16.md` (Phase 2 D2 audit finding); `CfgFieldRegistry.hpp:212` (bitmap-overflow static_assert precedent); `CfgFieldRegistry.hpp:1064-1075` (FOREACH_METADATA_BIT — 11 enrolled bits; +1 STAMP_BOUND_CFG_DERIVED at `.A`); `CfgFieldRegistry.hpp:1099-1133` (FOREACH_LIVES_IN_STRUCT — 5 enum values); TECH_DEBT-087 (sister general-purpose consumer-existence enforcement); CLAUDE.md item 31 (framework-driven extensibility); H15 + H16 (sister discipline at namespace-collision layer).
