# Categorical triggers in always-loaded docs

**Established:** 2026-05-18 (v5.15.5.F.4d.1.B.3 doc-layer refresh — codified after Caramel surfaced that hardcoded refs in skills/docs were the root cause of finding-issues; structural skill audit found ~50 sites across 22 skills duplicating canonical lists)
**Status:** **Stage 2 DRAFT v1.0** (first canonical application: skill structural audit closure under TECH_DEBT-112; subsequent applications: amendments to /readiness + /parity-check + /handoff + /ship + /dust + /strategy-template + /dod-audit etc.)
**Tags:** doc-layer-discipline, framework-driven, drift-prevention, audit-methodology; serves CLAUDE.md § Design philosophy (Maintenance gradient) + doc-layer separation rule; companion to `pattern-codification-lifecycle.md`

**Cross-references:**
- Sister: `pattern-codification-lifecycle.md` (when content matures from on-demand DESIGN_SPEC → always-loaded CLAUDE.md headline; this spec governs WHAT SHAPE triggers take after promotion)
- Sister: `structural-fix-preferred-decision-framework.md` (defer-to-registry IS the structural fix for canonical-list duplication drift)
- Sister: `wire-format-byte-preservation-discipline.md` Layer 7 (cross-tool emit-site enumeration — same defer-to-source-of-truth shape applied to wire format)
- Memory: `feedback_categorical_triggers_over_hardcoded_refs.md` (the going-forward rule)
- Memory: `feedback_claude_md_guidelines_not_stuff_to_do.md` (companion: doc-layer separation; WHERE content goes; this spec is WHAT SHAPE)
- Memory: `feedback_tech_debt_skill_drift_pragmatic_triage.md` (predecessor TECH_DEBT-109 sprint-phrasing-level closure; this spec addresses structural layer below)
- CLAUDE.md § Design philosophy (Maintenance gradient — "Categorical triggers > hardcoded refs in always-loaded content")
- CLAUDE.local.md going-forward rule: "Categorical triggers > hardcoded refs in always-loaded content" (2026-05-18)

---

## Problem statement

Always-loaded docs (CLAUDE.md, CLAUDE.local.md, MEMORY.md, SKILL.md files) accumulate hardcoded references over time: specific function names, specific TECH_DEBT-NNN entries, specific file paths, specific sprint version markers, specific canonical-list enumerations.

The drift is invisible until accumulation reaches a finding-issues threshold. Caramel surfaced 2026-05-18: "i'm worried that instead of generalized stuff we made hardcoded references, which is why we're having so many issues finding stuff right?"

**Root cause:** Always-loaded content gets retrieved via pattern-match ("does this discipline apply to what I'm doing?"), not ID-lookup ("does this work touch TECH_DEBT-105?"). Hardcoded refs force ID-lookup retrieval, which defeats the purpose of always-loaded content.

**Sister drift class:** Canonical-list duplication — trigger bodies list 5-10 fields/files/functions that ALSO live in a registry or ledger (FOREACH_* X-macro / DOCS/HOT_PATH_CHANGELOG.md / DOCS/CLAUDE_ML_INVARIANTS.md). The list drifts; the registry stays correct; the skill body becomes wrong.

**Recurrence count:** ≥50 sites surfaced by 2026-05-18 structural audit (TECH_DEBT-112). TECH_DEBT-109 (predecessor; closed 2026-05-18 prior) addressed sprint-phrasing-level drift; this spec addresses the STRUCTURAL layer below.

---

## The discipline

In always-loaded content, every reference falls into one of 3 buckets:

### A. KEEP — stable catalog IDs (designed-stable references)

| Catalog | Where | Examples |
|---|---|---|
| Anti-pattern class IDs | `DOCS/RECURRING_BUG_PATTERNS.md` | Class 18, Class 21, Class 27 |
| Hard invariants | `CLAUDE.md` § Hard Invariants table | H6, H13, H20 |
| Meta-disciplines | `DOCS/DESIGN_PHILOSOPHY.md` § 11.5 | M1, M4 |
| Pattern bodies | `DESIGN_SPECS/<name>.md` | `structural-fix-preferred-decision-framework.md` |
| X-macro registries | `*Registry.hpp` files | `FOREACH_STAMP_BOUND_DERIVED`, `FOREACH_REGISTRY` |
| Canonical doc paths | tracked DOCS/ | `DOCS/HOT_PATH_CHANGELOG.md`, `DOCS/CLAUDE_ML_INVARIANTS.md` |
| Canonical anchors | TECH_DEBT-NNN that genesis-anchors a skill | `TECH_DEBT-018 → /precoding-audit-gate` |
| CLI tool paths | `tools/check_*.py`, `tools/*.sh` (CI-stable) | `tools/calls_graph_diff.sh` |

These are catalog references designed to be stable. Specific identifiers, not drift candidates.

### B. KEEP with framing — worked examples (canonical history)

Worked examples preserve canonical history per [[feedback-tech-debt-skill-drift-pragmatic-triage]] convention (TECH_DEBT-109 closure precedent). KEEP when explicitly framed with one of:

- `(WORKED EXAMPLE; pattern applies categorically to <shape>)`
- `e.g.,` or `Example:` or `Anti-pattern caught (vX.Y.Z YYYY-MM-DD):`
- `Codified at v5.X.Y after <event>` (history-marker framing)
- `Canonical example:` (when establishing a pattern's first reference)

If a reference would be C-bucket but already has the framing, leave it — the framing signals "this is one instance, not a categorical claim."

### C. CONVERT — drift candidates (true hardcoded refs that should be categorical)

| Drift shape | Symptom | Conversion |
|---|---|---|
| Hardcoded TECH_DEBT-NNN in trigger bodies | "When work touches TECH_DEBT-105" | "When work touches <bug-class-pattern>" (the categorical surface, not the specific entry) |
| Specific function names in WHEN sections | "When refactoring `populate_stamp_cfg_from_derived`" | "When refactoring cfg-derived consumer template fns" (pattern shape) |
| Specific file paths in WHEN sections | "When touching `MemHeaders/CfgGateRegistry.hpp`" | "When touching any file matching `MemHeaders/*Registry.hpp`" (glob) |
| Sprint version markers in trigger bodies | "(NEW post-v5.X.Y)" or "Sprint v5.X.Y has 4 sub-ships" | Remove version marker OR move to history-note framing (B-bucket) |
| Canonical-list duplication | 5-10 cfg fields enumerated inline | Defer to source-of-truth: "walk current `FOREACH_<COHORT>` rows" |
| Specific line refs | "(line ~1080)" / "lines 107-150" | Remove parenthetical OR identifier-only ("the dispatcher function") |
| Hardcoded counts | "19 docs as of v5.14.10" / "Currently 2 fields" | "count grows over sprints" / "current at HEAD" |
| Specific deprecated-path lists | "PortfolioController.hpp + SingleCoreEngine.hpp" | Defer to CLAUDE.md deprecation notes |

---

## Canonical-list duplication: the dominant C-bucket shape

Structural skill audit 2026-05-18 surfaced that ~50/50 C-bucket findings clustered around 5 canonical lists duplicated across multiple skills:

| Canonical list | Source of truth | Duplicating skills |
|---|---|---|
| Stamp-bound cfg fields | `FOREACH_STAMP_BOUND_CFG_DERIVED` registry at `MemHeaders/CfgGateRegistry.hpp` | `/parity-check`, `/readiness` Check 16, `/handoff` Stage 1.5 |
| Hot-path file enumeration | `DOCS/HOT_PATH_CHANGELOG.md` cadence tier classification | `/ship`, `/latency-track`, `/readiness` Check 23 |
| Architectural-sprint guards | `DOCS/CLAUDE_ML_INVARIANTS.md` + `INVARIANTS_MAP.md` ledgers | `/ml-audit`, `/parity-check` Section L |
| Hot-path / slow-path function lists | Per-cadence orchestrator fns (per `DOCS/CODE_MAP.md`) | `/latency-track`, `/dust` |
| Per-strategy line refs | `Strategies/StrategyInterface.hpp` FOREACH_STRATEGY + dispatchers | `/strategy-template` Step 1, 4, 5, 6 |

**Recognition:** When a skill trigger body enumerates 5-10 specific items (cfg fields, files, function names) that ALSO live in a canonical registry/ledger → that's the structural drift.

**Fix:** Defer to the source of truth. Replace inline list with categorical pointer.

```
BEFORE:
"Stamp-bound cfg fields (v5.9.2b + v5.9.4a): confidence_threshold_scale,
barrier_gate_enabled, confidence_hard_block_threshold, held_out_fraction,
freshness_tau, bandit_blend_ratio, fee_rate_maker, fee_rate_taker,
training_poll_interval, model_num_outputs"

AFTER:
"Stamp-bound cfg fields: walk current FOREACH_STAMP_BOUND_CFG_DERIVED
registry rows at MemHeaders/CfgGateRegistry.hpp. Initial cohort
(v5.9.2b + v5.9.4a baseline) was 10 fields; current set may differ."
```

---

## Audit procedure

### Periodic skill audit (quarterly + post-codification)

For each SKILL.md file:

1. **Walk every trigger body, WHEN section, WHAT section** — flag references against the 3-bucket rubric
2. **Classify each:**
   - A KEEP — catalog ID. Done.
   - B KEEP-WITH-FRAMING — worked example. Verify framing is explicit. If implicit, add "Worked example:" prefix.
   - C CONVERT — drift candidate. Propose categorical replacement.
3. **Apply C-bucket conversions** — defer to canonical registry/ledger/source-of-truth
4. **Re-run audit at next cadence** — verify zero new C-bucket drift

### Audit cadence

- Quarterly codebase-wide skill audit (sister to `/anti-spaghetti` cadence per `project_anti_spaghetti_audit_cadence.md`)
- Post-major-codification sweep (e.g., new H invariant → audit skills for trigger-body references that should cite the H invariant categorically)
- Ad-hoc when operator surfaces finding-issues ("I can't find the X discipline easily")

---

## Worked example (canonical 2026-05-18 application)

Structural skill audit fired Agent against 30 SKILL.md files (TECH_DEBT-112 closure work). Result: ~50 C-bucket findings across 22 skills. Top conversions:

**`/parity-check` Section F (stamp-bound cfg fields list):**
- BEFORE: hardcoded 10-field list (drifted across .B.1, .B.2, .B.3 incremental extension)
- AFTER: "walk current FOREACH_STAMP_BOUND_CFG_DERIVED registry rows"

**`/readiness` Check 23 (hot-path identification):**
- BEFORE: hardcoded function list `ExecutionCore_Tick / BG_Evaluate / SG_Evaluate / GateParameters / ...`
- AFTER: "consult `DOCS/HOT_PATH_CHANGELOG.md` cadence-tier classification for current canonical function set"

**`/dust` Scan 7 (factorings to not re-flag):**
- BEFORE: hardcoded `PER_CORE_OVERRIDE_FIELDS / PER_CORE_OVERRIDE_INT_FIELDS / EventLoop_*OneCore` etc.
- AFTER: "consult `CoreFrameworks/MetaRegistry.hpp` FOREACH_REGISTRY for current canonical X-macro registries"

Pattern lifecycle: Stage 1 (problem identified — finding-issues surfaced 2026-05-18) → Stage 2 (THIS DOC + memory rule) → Stage 3 (first canonical application: TECH_DEBT-112 skill audit closure 2026-05-18) → Stage 4 (cohort migration: ~50 sites converted in same sprint) → Stage 5+ (CLAUDE.md item promotion under Design philosophy + priorities; codified 2026-05-18).

---

## Trade-offs + when to apply

### Apply when:

- Writing or editing any SKILL.md / CLAUDE.md / CLAUDE.local.md / MEMORY.md content
- Adding a new categorical trigger to an existing skill
- Promoting a Stage 2 DRAFT pattern to Stage 5+ (CLAUDE.md item) — verify CLAUDE.md item content uses categorical triggers
- Auditing skills for drift (periodic + post-codification)

### Skip when:

- Writing in-flight plan body content (plans/ — ephemeral; hardcoded refs are appropriate)
- Writing handoff doc content (sprint-specific; hardcoded refs are appropriate)
- Writing TECH_DEBT / PARITY_ISSUES ledger entries (ledger entries ARE hardcoded by design)
- Writing worked examples with explicit framing (B-bucket)

### Cost:

- ~5-10 min per skill audited (3-bucket classification + C-bucket conversion proposal)
- ~30-60 min full codebase-wide skill audit (30 skills × ~5 min average)
- ~15-20 min applying C-bucket conversions per skill

### Win:

- Skills retrievable by pattern-match, not ID-lookup
- Canonical lists drift naturally in source-of-truth locations (registries / ledgers); skill bodies stay categorical
- Always-loaded content stays accurate across sprints without per-sprint updates
- Finding-issues threshold pushed out (or eliminated)

---

## Lessons / gotchas

### Canonical-list duplication is the dominant shape

The audit found ~50/50 C-bucket findings clustered around 5 canonical lists duplicated across multiple skills. Defer-to-registry pattern is the dominant fix — almost every C-bucket finding resolves by pointing at an existing canonical source of truth rather than duplicating its content inline.

### B-bucket framing is load-bearing

Worked examples without explicit framing read as categorical claims. The phrase "e.g.," or "Worked example:" or "Anti-pattern caught (vX.Y date):" makes the reference legitimate canonical history rather than drift. Pre-existing skill content often lacks framing — pre-codification convention was to add it during audit.

### Sprint-version markers in HISTORY notes are fine

"Codified at v5.X.Y after <event>" is HISTORY (B-bucket). "Currently 19 docs as of v5.14.10" is a COUNT (C-bucket). Distinguishing the two: history markers describe past events; count markers describe present state. Past events don't drift; present state does.

### Some skills are already discipline-leading

`/precoding-audit-gate` explicitly anti-patterns hardcoded TECH_DEBT references in its own body (line 303). `/anti-spaghetti` has well-framed pattern lifecycle. `/plan-draft` similarly. These skills are the gold standard for categorical-trigger discipline.

### Audit cadence matters

Without periodic audit, drift accumulates invisibly. Quarterly skill audit + post-codification sweep is the cadence that prevents accumulation past finding-issues threshold.

### Avoid the over-correction

Don't aggressively convert B-bucket worked examples into "fully categorical" prose. Worked examples have load-bearing pedagogical value — converting "Anti-pattern caught (v5.14.10): EnsembleModelZoo.hpp cited 8+ times when file is CoreModelZoo.hpp" into "Anti-pattern: file paths in plan bodies drift between draft + ship" loses the concrete teaching. Keep the worked example; verify the framing.

---

## Pattern lifecycle (per `pattern-codification-lifecycle.md`)

- **Stage 1 (audit / problem identification):** Caramel surfaced 2026-05-18 finding-issues concern; structural skill audit fired same day; ~50 C-bucket findings across 22 skills
- **Stage 2 (DESIGN_SPEC draft):** THIS DOC (2026-05-18)
- **Stage 3 (first canonical application):** TECH_DEBT-112 skill audit closure ship — apply ~50 conversions across 22 skills; verify each defer-to-registry mechanically
- **Stage 4 (cohort migration):** all 22 skills receive C-bucket conversions in single sprint; CLAUDE.md item promoted with Design philosophy + priorities section codification
- **Stage 5+ (CLAUDE.md item promotion):** ALREADY landed 2026-05-18 (concurrent with Stage 3) under CLAUDE.md § Design philosophy (Maintenance gradient)
- **Stage 6 (audit cadence locked):** quarterly skill audit + post-codification sweep — periodic enforcement

---

## Cross-references

- Sister: `pattern-codification-lifecycle.md` (this spec governs WHAT SHAPE triggers take at Stage 5+)
- Sister: `structural-fix-preferred-decision-framework.md` (defer-to-registry IS the structural fix for canonical-list-duplication drift)
- Sister: `wire-format-byte-preservation-discipline.md` Layer 7 (cross-tool emit-site enumeration; same shape applied to wire format)
- Sister: `metadata-bit-driven-derived-filter-framework.md` (defer-to-registry pattern at framework level; this spec is the documentation-level variant)
- Memory: `feedback_categorical_triggers_over_hardcoded_refs.md` (going-forward rule)
- Memory: `feedback_claude_md_guidelines_not_stuff_to_do.md` (companion: doc-layer separation)
- Memory: `feedback_tech_debt_skill_drift_pragmatic_triage.md` (predecessor TECH_DEBT-109; this spec addresses structural layer below)
- TECH_DEBT-112 (skill structural audit closure ship — Stage 3 canonical application)
- CLAUDE.md § Design philosophy (Maintenance gradient line item)

---

**End of DESIGN_SPEC v1.0 DRAFT.** Stage 3 first canonical application: TECH_DEBT-112 skill audit closure ship at this sprint.
