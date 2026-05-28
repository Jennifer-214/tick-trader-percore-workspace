---
type: future-roadmap
established: 2026-05-28
status: idea-captured (not-actionable-yet)
horizon: v6.X+ (sister to docs-as-meta-code; both are doc-system architectural evolution)
sister_docs:
  - plans/_future/2026-05-28-docs-as-meta-code-roadmap.md
  - plans/_future/2026-05-12-decoupling-endgoal-roadmap.md
tags: [doc-pipeline, always-loaded-discipline, context-aware, long-term-vision]
surface: [claude-md, claude-local-md, memory-system, skill-discovery]
---

# Context-aware CLAUDE.md loading roadmap (long-term vision)

**Operator directive captured 2026-05-28:** Long-term, replace the single monolithic CLAUDE.md + CLAUDE.local.md with multiple specialized files loaded based on context of work at hand. Sister to the docs-as-meta-code vision; both close the doc-system architectural evolution gap.

**Status:** Idea captured; NOT actionable at v5.X timescale. Document for future-self + future-contributors + sister roadmap cross-link.

---

## The vision

Current state (2026-05-28):

```
~/.claude/projects/<engine>/   .claude/skills/<name>/SKILL.md
   memory/                       (auto-loaded on skill invocation)
   - MEMORY.md (index)
   - feedback_*.md
   - user_*.md                  CLAUDE.md (~640 lines)
   - project_*.md                 (always-loaded; UNION of ALL orientation)
   - reference_*.md             CLAUDE.local.md (~250 lines)
                                  (always-loaded; UNION of operator overlay)

State: ONE always-loaded orientation file (CLAUDE.md + CLAUDE.local.md union)
       loaded regardless of current task context.
       Operator-orientation context is the SAME whether working on:
         - C++ engine hot path math
         - Python CI tool development
         - ML training pipeline
         - GUI panel refactoring
         - Doc-system maintenance
         - Plan body drafting
       Even though the relevant subset of orientation differs substantially.
```

Target state (v6.X+):

```
CLAUDE.md (~100-150 lines)              CLAUDE.<context>.md (each ~150-250 lines)
  - Purpose + meta-pointer index          - CLAUDE.cpp.md (hot-path/slow-path/branchless/FPN)
  - Loading discipline                    - CLAUDE.python.md (CI tools/scripts/test harness)
  - Universal invariants H1-H20           - CLAUDE.ml.md (training/inference/scaler/registries)
  - Skill suite categorical index         - CLAUDE.gui.md (Dear ImGui/panels/snapshots)
                                          - CLAUDE.docs.md (frontmatter/file-size/find-recipes)
                                          - CLAUDE.tests.md (controller_test patterns)
                                          - CLAUDE.deploy.md (live-readiness/secrets/env)

CLAUDE.local.md (~50-100 lines)         CLAUDE.<context>.local.md (each ~50-150 lines)
  - Sprint state INDEX                    - sprint-specific overlays per context
  - Privacy boundary                      - operator preferences per surface
  - Universal going-forward rules         - context-specific going-forward rules

State: harness or skill detects context from user message or task surface;
       loads relevant CLAUDE.<context>.md as overlay on top of universal CLAUDE.md.
       Context can be inferred from:
         - Files in current working set
         - Recent git history scope
         - Slash command invoked
         - Operator directive language
```

---

## Why this matters

1. **Context-load efficiency** — Claude doesn't burn token budget on irrelevant orientation. Working on Python tools? Don't need 200 lines of hot-path discipline.

2. **Cognitive scope alignment** — operator preferences in different surfaces differ (e.g., "branchless > branched" applies to HP/SP code; doesn't apply to Python). Per-context CLAUDE.X.md keeps the right discipline surfaced.

3. **Drift containment** — a CLAUDE.cpp.md update doesn't risk breaking other surfaces. Operator-tweakable per-context without cascading changes.

4. **Codebase growth scaling** — as v5.X → v6.X adds more surfaces (Python tools, multi-language, decoupled viewer, etc.), the union-CLAUDE.md grows unboundedly. Per-context split bounds each file.

5. **AI session boundary discipline** — when a session is bounded to a specific work axis, loading just the relevant orientation reduces noise + context-switching cost.

---

## Sister precedents in this codebase

This is already happening at small scale:

1. **Skill SKILL.md auto-loaded only on invocation** — `/dod-audit` SKILL.md only loads when `/dod-audit` is invoked. Other skills don't pollute context. **Per-context loading IS the discipline at skill layer.**

2. **`DOCS/CLAUDE_INTEGRATION.md` / `CLAUDE_INVARIANTS.md` / `CLAUDE_ML_INVARIANTS.md` / `CLAUDE_REVIEW.md` etc.** — on-demand portal docs at `DOCS/`. Each focused on a specific concern. **The split exists; just isn't auto-loaded contextually.**

3. **`DESIGN_SPECS/<axis>/` subdirectories** — refactor-patterns / framework-patterns / meta-disciplines / etc. organized by axis. **The directory layout is the "context" key.**

The vision is: **extend skill-style per-context loading to the always-loaded orientation layer**.

---

## Specific axes for evolution

### A. Context detection mechanism

Options:
- **Harness-side**: Claude Code harness reads working files + injects appropriate CLAUDE.<context>.md.
- **Skill-side**: NEW skill `/context-load` invoked early in session OR auto-invoked based on heuristics.
- **Tag-side**: User message contains a `:context cpp` or similar marker; harness routes to CLAUDE.cpp.md.
- **Inferred**: Recent git activity on `Strategies/` files → load CLAUDE.cpp.md + CLAUDE.ml.md (overlap).

Recommend: **harness-side with skill-side override** + inferred default. Harness uses file working-set as default signal; operator can override with `/context <name>` if needed.

### B. CLAUDE.md split candidates

| Context | Source content (from current CLAUDE.md) |
|---|---|
| `CLAUDE.cpp.md` | Hot-path discipline (H7/H8/H20) + branchless/FPN/MBS/BITMAP_* / Concurrency model summary / Latency + Memory budgets / "Code Conventions" section |
| `CLAUDE.ml.md` | Subset of ML invariants from DOCS/CLAUDE_ML_INVARIANTS.md elevated to always-loaded when working on ML / FeatureRegistry / scaler / stamp boundaries |
| `CLAUDE.docs.md` | "How to find anything" search recipes + doc-frontmatter convention + file-size discipline + categorical triggers |
| `CLAUDE.tests.md` | Test file size discipline + controller_test patterns + test-specific invariants |
| `CLAUDE.deploy.md` | Live-readiness boot gate + secrets/.cfg discipline + paper-test prep |
| `CLAUDE.gui.md` | Dear ImGui panels + TUISnapshot + display↔execution invariant |
| `CLAUDE.md` (root) | Purpose + Skill suite categorical index + Universal H1-H20 table + Loading-discipline pointer |

### C. CLAUDE.local.md split candidates

| Context | Source content (from current CLAUDE.local.md) |
|---|---|
| `CLAUDE.local.md` (root) | Sprint state INDEX (1-line pointer to MASTER) + Privacy boundary + Universal operator-collaboration rules |
| `CLAUDE.cpp.local.md` | Going-forward rules specific to engine code (structural-fix-preferred / framework-discipline / type-trait dispatch / multi-bit state encoding / branchless dispatch / decision-time data binding / cohort-audit / bitmap overflow / etc.) |
| `CLAUDE.docs.local.md` | Going-forward rules specific to doc-system (categorical triggers / file-size split / doc-frontmatter / metadata audit cadence) |
| `CLAUDE.process.local.md` | Going-forward rules specific to ship-process (audit re-fire at amendment / mid-sprint audits / sub-plan sidecar / each DESIGN_SPECS doc has cross-ref / etc.) |

### D. Loading order discipline

If multiple contexts apply (e.g., editing both C++ and Python in same session), need merge discipline:
- Universal CLAUDE.md ALWAYS loads first
- Context-specific overlays APPEND (no field replacement; only addition)
- Conflicts surface as warnings; operator-resolvable
- Skill load contracts unchanged (skills load on invocation regardless of context)

---

## Why NOT now (scoping discipline)

Per `feedback_overengineering_boundary_when_future_easier` + `feedback_framework_layer_payoff_diminishing_returns`:

- v5.X codebase still mostly single-context (C++ engine + supporting Python tools); union-CLAUDE.md still tractable
- Token budget pressure not yet severe; modern Claude (1M context) handles 640-line CLAUDE.md trivially
- Context-detection mechanism would need design + harness integration; substantial infra investment
- Current single-file approach works for current scope; split = future-optimization

Wait until:
- v6.0+ post-decoupling sprint (engine + viewer + Python ML training pipeline all distinct surfaces)
- CLAUDE.md union grows past ~1200 lines (current: ~640; growth slowing post `.D` reductions)
- Operator workflow involves frequent context-switching that becomes friction
- Token budget pressure emerges (long sessions hitting context limits)

---

## Sister long-term vision: docs-as-meta-code roadmap

This roadmap pairs with `plans/_future/2026-05-28-docs-as-meta-code-roadmap.md`:

- **docs-as-meta-code** = make doc content STRUCTURED so tools can consume it
- **context-aware-CLAUDE.md** = make doc LOADING context-aware so AI sessions see relevant subset

Both target the same architectural axis (doc-system evolution from human-narrative-only → AI-friendly + tool-friendly) at different layers (content layer vs loading layer).

When v6.X+ rollout happens, do both in same sub-sprint OR consecutively.

---

## Concrete steps when the time comes (v6.X+)

1. **Stage 1**: Identify the highest-leverage context boundary (likely C++ vs Python vs docs). Split CLAUDE.md into `CLAUDE.md` (universal) + `CLAUDE.cpp.md` first. Measure operator-friction impact.

2. **Stage 2**: If Stage 1 successful, extend to `CLAUDE.docs.md` + `CLAUDE.tests.md` + others. Codify a `DESIGN_SPECS/doc-disciplines/context-aware-claude-md-pattern.md`.

3. **Stage 3**: Build harness-side context detection (default = file working-set; override = `/context <name>`).

4. **Stage 4**: Skill amendment cohort — all skills that reference CLAUDE.md sections need to reference the appropriate split file.

5. **Stage 5**: Migrate CLAUDE.local.md split similarly.

---

## Operator-collaboration note

Captured during `.D` ship close (`v5.15.5.F.4d.1.D`) 2026-05-28 PM. Operator articulated the vision in passing: "i also had an idea to keep multiple different ones for different purposes that get loaded based on context of the work at hand".

Captured here per `feedback_motivated_collaborator_for_caramel` quality-bar long-term thinking; surfaced when CLAUDE.md + CLAUDE.local.md cleanup is being scoped.

---

## Cross-references

- `plans/_future/2026-05-28-docs-as-meta-code-roadmap.md` (sister long-term roadmap; same architectural axis at content layer)
- `plans/_future/2026-05-12-decoupling-endgoal-roadmap.md` (sister runtime decoupling roadmap)
- `DESIGN_SPECS/doc-disciplines/file-size-split-discipline.md` (file-size discipline; sister at size-bound layer)
- `DESIGN_SPECS/doc-disciplines/categorical-triggers-in-always-loaded-docs.md` (always-loaded discipline; precursor to context-aware loading)
- `feedback_claude_md_guidelines_not_stuff_to_do` (timeless-vs-ephemeral discipline; doesn't yet address multi-file split)
- Operator directive 2026-05-28 PM (this doc's establishment trigger)

---

**End of future-roadmap v0.1 (2026-05-28 PM).** Updated when v6.X+ post-decoupling timing + context-switching friction reach inflection.
