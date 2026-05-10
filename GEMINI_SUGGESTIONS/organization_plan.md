# Workspace Organization Plan

Based on the root directory contents and the strict design philosophy in `CLAUDE.md` and `CLAUDE.local.md`, here is a proposed organization plan to streamline the project structure and align with established workflows:

## Current State Observations
The workspace is currently divided into:
- **Core Guidelines:** `CLAUDE.md`, `CLAUDE.local.md`, `GEMINI.md`, `STRATEGY_AND_CODING_RULES.md`, `LATENCY_OPTIMIZATION_AUDIT.md`
- **Documentation & Debt:** `DOCS/`, `DESIGN_SPECS/`
- **Execution Plans:** `plans/`
- **Skills/Agents:** `claude-skills/`
- **Audit Findings:** `GEMINI_FINDINGS/`

## Proposed Organization Plan

1. **Integrate Findings into the Master Ledger (`DOCS/TECH_DEBT.md` & `DOCS/PARITY_ISSUES.md`)**
   - **Rationale:** As explicitly stated in `CLAUDE.local.md`: *"deferred items must be queryable, not buried."* Leaving findings in a separate `GEMINI_FINDINGS/` directory makes them "transient audit reports" which get "re-discovered as noise." The single source of truth must be the ledger.
   - **Action:** Process the items in `GEMINI_FINDINGS/MASTER_SORTED_BACKLOG.md`. Auto-write legitimate architectural debt into `DOCS/TECH_DEBT.md`, and any engine/parity bugs into `DOCS/PARITY_ISSUES.md`. Once migrated, the `GEMINI_FINDINGS` directory should be deprecated or used strictly as temporary scratch space for agent runs prior to ledgering.

2. **Consolidate Architecture and Design Specs**
   - **Rationale:** `DESIGN_SPECS/` is functioning excellently as the reusable pattern library. However, high-level invariants are currently split across `CLAUDE.md`, `DOCS/CLAUDE_INVARIANTS.md`, and `STRATEGY_AND_CODING_RULES.md`.
   - **Action:** Ensure that any newly crystallized patterns from resolving `GEMINI_FINDINGS` are formalized as `DESIGN_SPECS/<pattern-name>.md` and cross-referenced in `CLAUDE.md` (following the "codify design principles" rule in `CLAUDE.local.md`). Do not create new top-level markdown files if they belong in `DESIGN_SPECS/` or `DOCS/`.

3. **Align Planning Directories**
   - **Rationale:** `plans/` effectively holds date-prefixed execution plans. The rules "prefer boundary-stable refactors" and "cold-pickup completeness" apply here.
   - **Action:** Keep `plans/` as the authoritative source for upcoming work sprints, ensuring each plan clearly references a `TECH_DEBT` entry if it is addressing deferred work.

4. **Agent Skill Orchestration**
   - **Rationale:** The `claude-skills/` directory holds tools for agents. Per `TECH_DEBT-018`, a Layer 1 orchestrator like `/precoding-audit` coordinates these skills.
   - **Action:** Retain skills within this directory, but document the orchestrator pipeline clearly so that both Claude and Gemini invoke the exact same pre-flight audit steps, maintaining uniformity across agents.
