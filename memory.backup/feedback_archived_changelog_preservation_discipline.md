---
name: feedback-archived-changelog-preservation-discipline
description: "DO NOT modify archived `DOCS/changelogs/<old-date>-*.md` files OR archived rows in `DOCS/CHANGELOG.md` even when removing the feature they describe. Archived history is TIMELESS — records what shipped at each version. Rewriting violates timeless-doc principle. Only CURRENT CHANGELOG.md gets NEW row at ship close; archived stays untouched."
metadata:
  node_type: memory
  type: feedback
  originSessionId: f7bb757d-2b7c-4ba6-9c4a-1c7d60bff493
  sister_specs: [feedback_operator_facing_doc_cohort_at_cfg_deletion.md, feedback_categorical_triggers_over_hardcoded_refs.md, feedback_claude_md_guidelines_not_stuff_to_do.md, feedback_multi_surface_deletion_ordering_discipline.md, feedback_terminology_evolution_bridge_not_history_rewrite.md, feedback_verify_symbol_existence_at_plan_drafting_time.md]
  tags: [deletion-discipline, migration-discipline, ledger-discipline]
---

**Archived changelogs are TIMELESS HISTORY.** They record what shipped at each version — what features existed, what cfg fields applied, what architectural decisions were made AT THAT POINT IN TIME. When subsequently deleting those features, **the archived changelog stays untouched**. Rewriting violates the timeless-doc principle.

**Discipline:** at every feature deletion / refactor / cleanup, archived changelog files (`DOCS/changelogs/<old-date>-*.md` + archived rows in `DOCS/CHANGELOG.md`) LEAVE as-is. Only CURRENT CHANGELOG.md gets NEW row at ship close describing the deletion. Future readers grepping for the deleted feature in archived changelogs FIND it (correctly) as historical context — not stale doc.

**Why:** Codified 2026-05-26 PM at `.B.4` v1.7.5 WIP-12 cycle. Operator-directed `rg` sweep for `engine_arch` deletion surface revealed 6 archived changelog files at `DOCS/changelogs/2026-04-28-v5.0.*` + `v5.1.0-data-plane-decouple.md` referencing `engine_arch` (correctly — that's WHAT SHIPPED at v5.0.x). Plus 1 archived row at `DOCS/CHANGELOG.md` v5.15.2 row historical context. Initial instinct was to update these for consistency post-deletion. Operator framing: these are timeless history; don't rewrite.

**Distinction from active doc surfaces:**
- ACTIVE doc surfaces (README + QUICKSTART + cfg.example + DOCS/CHANGELOG.md NEW rows): UPDATE when feature deleted; sister `feedback_operator_facing_doc_cohort_at_cfg_deletion`
- ARCHIVED doc surfaces (DOCS/changelogs/<old-date>-*.md + CHANGELOG.md old rows): LEAVE; record historical state

## How to apply

**When deletion-cohort enumeration includes archived doc surfaces:**

1. **Classify as `archived-changelog (LEAVE)` or `current-changelog (historical-row LEAVE; new row added at ship close)`** per B-Plus v0.4 deletion-kind heuristic
2. **Do NOT modify** the archived files / historical rows
3. **Do add** NEW row to CURRENT CHANGELOG.md at ship close describing the deletion + sister architectural preservation surface (e.g., legacy single_core LIVE binary for `engine_arch=centralized` operators per Decision I)
4. **Verification post-deletion:** archived files unchanged; CURRENT CHANGELOG.md has NEW row

## Recognition markers (when this rule applies)

- File path matches `DOCS/changelogs/<YYYY-MM-DD>-<version>-*.md`
- File path matches `DOCS/changelogs/` directory
- DOCS/CHANGELOG.md row dated PRIOR to current ship's expected ship date
- Any historical reference where rewriting would change "what shipped at version X" recorded state

## Sister memories

- [[feedback_operator_facing_doc_cohort_at_cfg_deletion]] — sister at ACTIVE doc-surface layer; this rule covers ARCHIVED doc-surface layer
- [[feedback_categorical_triggers_over_hardcoded_refs]] — parent meta-rule (categorical pattern triggers > hardcoded refs); archived changelog refs ARE hardcoded historical refs that should NOT be migrated to categorical pattern
- [[feedback_claude_md_guidelines_not_stuff_to_do]] — parent meta-rule (TIMELESS doc layer separation); archived changelog IS timeless layer
- [[feedback_multi_surface_deletion_ordering_discipline]] — B14 sister; archived-changelog kind is LEAVE category in deletion-kind classification

## Worked example

`.B.4` v1.7.5 WIP-14 — `engine_arch` cfg field deletion archived doc surfaces (LEAVE):

| Archived surface | Reference | Action |
|---|---|---|
| `DOCS/changelogs/2026-04-28-v5.0.0-architectural-rewrite.md` | "**Cfg flip**: `engine_arch` default switches from `centralized` to `per_core_slow`..." | LEAVE — records v5.0.0 architectural rewrite event |
| `DOCS/changelogs/2026-04-28-v5.0.1-per-engine-slow-path-latency-display.md` | "In `engine_arch=centralized`, slow-path table shows `-`..." | LEAVE — records v5.0.1 GUI display behavior at that version |
| `DOCS/changelogs/2026-04-28-v5.0.2-pinning-and-topology.md` | "Default 0 (auto) on for `engine_arch=per_core_slow`..." | LEAVE — records v5.0.2 cfg default behavior |
| `DOCS/changelogs/2026-04-28-v5.0.3-topology-advanced.md` | Topology panel references | LEAVE |
| `DOCS/changelogs/2026-04-28-v5.0.4-parity-tests.md` | TUI_PopulateTopology engine_arch test fixture | LEAVE — records v5.0.4 parity test scope |
| `DOCS/changelogs/2026-04-28-v5.1.0-data-plane-decouple.md` | Data plane decouple references | LEAVE |
| `DOCS/CHANGELOG.md` v5.15.2 row | "Distinct from `engine_mode` (sharded/single_core architectural) and `engine_arch` (per_core_slow/centralized)..." | LEAVE — records v5.15.2 ship context |

ACTIVE doc surfaces to UPDATE (sister `feedback_operator_facing_doc_cohort_at_cfg_deletion`):
- `README.md:195` — DELETE
- `DOCS/QUICKSTART.md:174` — DELETE
- `engine.cfg.example` — DELETE 4 lines

NEW row at `DOCS/CHANGELOG.md` at `.B.4` ship close: `### v5.15.5.F.4d.1.B.4 — Train-serve execution-layer parity structural extract + B-full SHARDED centralized-arch full surface deletion` + body describing closures + migration path for `engine_arch=centralized` users (legacy single_core LIVE binary sister-architectural preservation per Decision I).

## Stage progression

- **Codification:** memory + going-forward rule at WIP-12
- **No DESIGN_SPEC inline at v1.7.5** (categorical trigger in CLAUDE.local.md + this memory sufficient; no Stage 2 DRAFT needed — covered by general timeless-history principle per `feedback_claude_md_guidelines_not_stuff_to_do`)
- **Structural enforcement:** B-Plus v0.4 `--gen-deletion-cohort` mode EXCLUDES archived changelogs by default (`-g '!DOCS/changelogs/2026-04-*'`); operator opt-in via `--include-archived` flag for inspection only (not deletion target)
- **No /readiness Check** (Check 38 candidate DROPPED per `feedback_framework_layer_payoff_diminishing_returns` — categorical trigger + sister memory sufficient; over-codification with /readiness slot premature)

## Trade-off

Discipline adds ~30 sec per deletion at planning time (check enumeration includes archived classification). Prevents rewriting timeless history. Without this rule: future contributors grep archived changelogs for context; if archived state has been retroactively modified, the "what shipped at v5.0.x" record becomes corrupted; cold-pickup analyses become unreliable.

For deletions touching NO archived surfaces (e.g., feature added + deleted within same ship cycle): this rule N/A.

## When this rule applies

Per `feedback_categorical_triggers_over_hardcoded_refs`:

- Any feature deletion where B-Plus v0.4 generator classifies sites as `archived-changelog (LEAVE)` kind
- Any file path under `DOCS/changelogs/` directory
- Any historical row in `DOCS/CHANGELOG.md` (rows dated PRIOR to current ship's expected ship date)
- Sister archived-doc surfaces (postmortems / handoffs / decision logs from prior ships) — same timeless-history principle applies
