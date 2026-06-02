---
type: handoff
status: active
defers: 2026-06-02-post-cleanup-ship-a-flip-handoff.md   # PARKED the flip to do this; RESTORE it (deferred→active) when this arc closes
ship_tag: "skill-meta-pattern arc — knowledge-consultation + auto-routing across skills (+ finish deferred-state wiring)"
plan_type: feature (workflow/skill infrastructure)
sprint: v5.15-live-readiness
sprint_end_goal: make the codebase more maintainable for future development
ship_end_goal: "Every JUDGMENT skill auto-consults its associated specs + anti-patterns + canonical-sister (do we already have / can-extend a proven approach) BEFORE proposing; input heuristics auto-suggest (judgment) / auto-fire (mechanical) the matching skill. Uniform + frontmatter-driven (registry-style), not N ad-hoc checks. Piloted on 2-3 skills, then rolled out + template-propagated."
predecessor_handoff: null   # NEW work-line; the flip is DEFERRED not superseded (see `defers:`)
required_reading: [this doc, CLAUDE.md, CLAUDE.local.md, MEMORY.md]
engine_head: e33a702 (unchanged — this arc is workspace/skill infra, NOT engine code)
pickup: /accept-handoff
---

# Skill-meta-pattern arc — skills auto-consult institutional knowledge + auto-route

**Origin:** operator design conversation 2026-06-02 (sparked by the `.resolve` vacuous-guard catch). The
**#11 storage flip is DEFERRED** (`status: deferred`, `deferred_for: this`) — it RESUMES when this arc
closes. This is NOT a supersede; the flip is still owed + unchanged.

## The idea (validated against the real skill system)

Two layers, both already PARTIALLY present — this arc makes them UNIFORM + adds the routing layer.

### Layer A — skills consult their associated knowledge
Every JUDGMENT skill runs a standard early stage: *"consult the relevant design-specs + anti-patterns;
run the canonical-sister check — do we ALREADY have a proven approach, or can we EXTEND an existing spec,
before proposing new?"* Generalizes `/precoding-audit-gate`'s composition (`/dod-audit` specs +
`/bug-check` anti-patterns) + the `canonical-sister-extension` discipline into a uniform stage.
- Already real: `loads_dynamically` on **36/38** skills, `sister_skills` on 37, precoding-gate composes dod-audit + bug-check + 4.
- Missing: not uniform; "consult anti-patterns + canonical-sister" isn't a standard stage every judgment skill runs.

### Layer B — auto-routing by heuristic
Input matches a skill's trigger heuristic → **SUGGEST** (judgment skills, await greenlight) or **FIRE**
(mechanical/safe). "ready to end" → suggest `/close-session`; "is there something better / should we build
X" → the canonical-sister + novel-alternative check.
- Already partial: ad-hoc (agent suggested `/close-session` this session).
- Missing: a systematic heuristic→skill map so it's reliable, not vibes.

## Design calls (operator-confirmed direction)
1. **JUDGMENT skills only** (plan/design/audit) — NOT mechanical (`/ship`, `/sync`). Don't bloat them.
2. **SUGGEST + await-greenlight** for judgment; auto-FIRE only safe/mechanical. Never silently fire a judgment skill.
3. **FRONTMATTER-DRIVEN**: add `associated_specs` / `associated_anti_patterns` / `trigger_heuristics` (extend `loads_dynamically`) — a registry, not hardcoded `if`s.
4. **PILOT, don't boil the ocean**: prove on `plan-check` + `readiness` + `precoding-audit-gate`, then roll out (per `feedback_framework_layer_payoff_diminishing_returns`).

## Work-list ("what would need updating")
1. NEW meta-discipline doc — "skill knowledge-consultation + auto-routing" (the core meta thing).
2. `doc-frontmatter-convention.md` — add the `associated_anti_patterns` / `trigger_heuristics` fields.
3. Standard **"Stage 0: consult specs + anti-patterns + canonical-sister"** added to the 3 pilot skills.
4. A **heuristic→skill routing map** (extend CLAUDE.md "How to…" into agent-triggers) + a memory rule ("input matches a skill heuristic → suggest/fire").
5. `/second-opinion` skill OR a stage on `/readiness` ("is there something better / can we extend a spec?") — the canonical-sister + 4-pillar-self-audit + proactive-novel-alternative disciplines ARE its checklist.
6. **Template propagation** of all of the above.
7. ✅ **DONE (2026-06-02) — deferred-state SKILL wiring complete + hands-off:** `/handoff` Stage 6.0b defer-branch (mark prior active → `deferred` + `deferred_for`/`defers` cross-refs) · `/accept-handoff` Stage 1 resolves active + SURFACES deferred (a park isn't silently forgotten) · `/close-session` Stage 6.0 RESUME (deferred → active on detour-close) · guard deferred-aware (warns deferred+0active) · all propagated to the template.
8. **`.resolve`/vacuous-green codification (AR-4)**: codify "every guard ships a negative-self-test + fails loud on 0-items-when-the-tool-is-present" — the structural close of the vacuous-green that bit this session (`check_doc_metadata` silently scanned 0/100 memories). Add a fail-loud-on-empty to the memory guard + the landmine/meta-anti-pattern.

## What's DONE this session (the enabling pieces)
- The **`deferred` 3rd handoff state**: guard (`check_handoff_active_singleton.py` — deferred-aware + selftest), spec (`handoff-active-state-machine.md`), template — all landed + verified.
- The **`.resolve` symlink-trap class** fixed across 5 doc-CI tools (the memory guard is now REAL).

## On close: RESUME the flip
When this arc closes, flip the parked **`2026-06-02-post-cleanup-ship-a-flip-handoff.md`** from
`deferred` → `active` and this handoff → `superseded`. The guard warns if you forget (deferred + 0 active).

## First action
`/accept-handoff` (no path) → resolves here. Then start the work-list at item 1 (the meta-discipline doc)
under **plan-right-not-fast** — this is core infra (design-once-maintain-forever); **spec before implementing**.
