---
type: meta-discipline
stage: 2-draft
version: 0.1
established: 2026-06-02
tags: [meta-discipline, framework-discipline, doc-discipline, operator-collaboration]
surface: [registry]
sister_specs:
  - canonical-sister-extension-discipline.md
  - structural-enforcement-when-memory-insufficient.md
  - pattern-codification-lifecycle.md
  - doc-frontmatter-convention.md
  - audit-driven-pre-coding-gate.md
  - implementation-layer-blindspot-taxonomy.md
  - meta-anti-pattern-index.md
applies_at_skills: [/plan-check, /readiness, /precoding-audit-gate]
---

# Skill knowledge-consultation + auto-routing

**Status:** Stage 2 DRAFT — first draft 2026-06-02, written for operator discussion (NOT yet locked).
**Origin:** operator design conversation 2026-06-02, sparked by the `.resolve` vacuous-guard catch — the realization that the skill system *has* the pieces (specs, anti-patterns, the canonical-sister check) but doesn't *uniformly consult them*, and that input → skill routing is currently ad-hoc ("vibes").
**Identity (resolved 2026-06-02):** its OWN meta-discipline. M1 (canonical-sister) is a SPECIAL CASE of it — "consult one store (sister patterns)" vs this "consult ALL stores before proposing." Folding the general rule under one of its examples is backwards. Gets its own § 11.5 registry number at lock; M1 listed as its first canonical instance.

---

## One-sentence statement

Every JUDGMENT skill should run a uniform early stage that **consults its associated institutional knowledge** (design-specs + anti-patterns + the canonical-sister "do we already have / can we extend a proven approach?" check) **before proposing anything new** — and operator input should **auto-route** to the matching skill (SUGGEST for judgment, FIRE for mechanical/safe), driven by **frontmatter declarations**, not hardcoded `if`s.

---

## Problem statement

The skill system already holds the right knowledge and already *fragments* of both behaviors exist — but neither is **uniform**, so both are unreliable.

**Layer A (consult-before-propose) is present but not uniform:**
- `loads_dynamically:` on **36/38** skills (each skill names the specs it pre-loads).
- `sister_skills:` on **37/38** skills.
- `/precoding-audit-gate` *composes* `/dod-audit` (specs) + `/bug-check` (anti-patterns) — but only the gate does this.
- `/readiness` has a "Stage 0 DESIGN_PHILOSOPHY preload" — but only `/readiness`.
- `canonical-sister-extension-discipline.md` defines the "do we already have this? can we extend it?" check with a full expanded menu (INLINE / ACCEPT / FOLD / ARCHITECT / NO-FOLD) — but it only fires inside `/precoding-audit-gate` + `/anti-spaghetti` + as `/readiness` Check 29.

  → **The gap:** "consult your specs + anti-patterns + run the canonical-sister check" is NOT a standard stage that *every judgment skill* runs. It's scattered across three skills in three different shapes.

**Layer B (auto-routing) is purely ad-hoc:**
- The gate auto-derives audit focus from plan keywords, and auto-fires `/blindspot-scan` on deletion keywords — so heuristic→skill routing *works* where it's hardcoded.
- But there is no systematic heuristic→skill map. "Ready to end" → should suggest `/close-session`; "is there something better / should we build X?" → should trigger the canonical-sister + novel-alternative check. Today that happens only if the agent happens to think of it.

  → **The gap:** routing is vibes, not a declared contract. It fires unreliably.

**Why this matters now (the spark):** the `.resolve` vacuous-green bug (a guard silently scanned 0/100 memories and reported clean) is the same *shape* one layer up — the system *had* the guard but it wasn't *actually consulting* the thing it claimed to. Layer A is the institutional-knowledge analogue: skills that *have* associated knowledge but don't reliably *consult* it before proposing.

This is **not new infrastructure.** It is uniformization of two behaviors that already exist in fragments, plus a handful of per-store frontmatter fields and a thin routing map. Per `feedback_framework_layer_payoff_diminishing_returns` + `feedback_audit_canonical_sister_before_new_infra`, the honest framing is: **extend `canonical-sister-extension-discipline` + the precoding-gate composition into a uniform, frontmatter-driven stage** — do not build a parallel system.

---

## The two layers

### Layer A — skills consult their associated knowledge ("Stage 0: consult before propose")

A standard early stage every JUDGMENT skill runs, *before* it proposes a design / verdict / recommendation:

> **Stage 0 — Consult institutional knowledge.**
> 1. **Specs** — load + read the design-specs this skill is associated with (`associated_specs`, generalizing `loads_dynamically`). What proven pattern already covers this surface?
> 2. **Anti-patterns** — load the recurring-bug / meta-anti-pattern classes relevant to this surface (`associated_anti_patterns`). What known failure shapes apply?
> 3. **Canonical-sister check** — run the `canonical-sister-extension-discipline` question: *do we ALREADY have a proven approach, or can we EXTEND an existing spec, before proposing new?* Surface the expanded menu (INLINE / ACCEPT / FOLD / ARCHITECT / NO-FOLD); don't auto-pick.
> 4. **Decisions** — check the decision log (`associated_decisions` / the sprint's `decision-logs/`): *did we already DECIDE this?* Don't re-litigate a `decided` item (the D-105 fake-blocker shape). Already wired at pickup (`/accept-handoff` Stage 4.6); this adds it at DESIGN time.
> 5. **Postmortems** — if this ship resembles a past one, read that ship's postmortem first (`associated_postmortems` / `plans/<sprint>/postmortems/`): *what bit us last time on this shape?*

Output of Stage 0 is a short "what we already have" preamble that the skill's later stages must reckon with. It generalizes exactly what `/precoding-audit-gate` already does by composing `/dod-audit` + `/bug-check`, and what `/readiness` Stage 0 preload already does — made uniform.

### Layer B — auto-routing by heuristic (input → SUGGEST / FIRE)

When operator input (or the current work state) matches a skill's declared trigger heuristic:
- **JUDGMENT skill matched → SUGGEST + await greenlight.** Never silently fire a judgment skill. ("ready to wrap up" → *suggest* `/close-session`; "should we build X / is there something better?" → *suggest* the canonical-sister + novel-alternative check.)
- **MECHANICAL / safe skill matched → FIRE** (or fire its underlying tool directly, per `feedback_independence_for_judgment_not_mechanical`).

Generalizes the gate's existing auto-derive-focus + deletion-auto-fire-`/blindspot-scan` into a declared, systematic map instead of per-skill hardcoded keyword lists.

---

## Knowledge stores the consult-stage covers

The gap class is uniform: a store that gets **WRITTEN but not READ when it matters** — a *write-only knowledge store* ("knowledge graveyard"), the same shape as the `.resolve` vacuous-green bug (looked like it checked; didn't). So the consult-stage covers EVERY accumulated store that has a moment-of-relevance, not just specs. **Full scope — all in this ship (operator 2026-06-02; NOT split to a "later ship"):**

| Knowledge store | Per-store frontmatter field | Read-back today | Consult-stage adds |
|---|---|---|---|
| DESIGN_SPECS (patterns) | `associated_specs` | `/dod-audit`, `loads_dynamically` | uniform consult |
| RECURRING_BUG_PATTERNS (code anti-patterns) | `associated_anti_patterns` | `/bug-check` only | uniform consult |
| Decision logs (D-NNN) | `associated_decisions` | only at pickup (`/accept-handoff` 4.6) | consult at DESIGN time |
| Postmortems | `associated_postmortems` | nothing | "ship resembles a past one → read its postmortem" |
| TECH_DEBT / PARITY (surface-scoped) | `associated_ledgers` | `/readiness` (add-side) | read OPEN debt in the surface you touch |
| meta-anti-pattern-index (reasoning mistakes) | (folds into `associated_anti_patterns`) | `/capture-audit` Check 12 | consult reasoning-level mistakes too |
| LANDMINES / FEATURE_LOOKUP | `associated_refs` | manual "remember to read" | trigger before debugging / feature work |

(These per-store fields extend the three core fields in § Mechanism.)

**Name the gap class:** "write-only knowledge store" gets a row in `meta-anti-pattern-index.md` — anything we write but never read back is a diary, not knowledge.

---

## Design calls (operator-confirmed — these are constraints, not open)

1. **JUDGMENT skills only** (plan / design / audit) — NOT mechanical (`/ship`, `/sync-workspace`, `/index-rebuild`). Don't bloat mechanical skills with a consult stage.
2. **SUGGEST + await-greenlight for judgment; auto-FIRE only safe/mechanical.** Never silently fire a judgment skill.
3. **FRONTMATTER-DRIVEN** — add `associated_specs` / `associated_anti_patterns` / `trigger_heuristics` (extending `loads_dynamically`). A registry, not hardcoded `if`s.
4. **PILOT, don't boil the ocean** — prove on `/plan-check` + `/readiness` + `/precoding-audit-gate`, then roll out + template-propagate (per `feedback_framework_layer_payoff_diminishing_returns`).

---

## Mechanism — frontmatter-driven (the registry, not `if`s)

Extend the existing `claude-skills/<skill>/SKILL.md` frontmatter (which already carries `loads_dynamically` + `sister_skills`) with:

| New field | Type | Meaning | Generalizes |
|---|---|---|---|
| `associated_specs` | list of DESIGN_SPECS paths | Specs Stage 0 consults ("what proven pattern covers this?"). May alias/subsume `loads_dynamically`. | `loads_dynamically` |
| `associated_anti_patterns` | list of Class/AR/Mn IDs or paths | Anti-pattern classes Stage 0 consults ("what failure shapes apply?"). | `/bug-check` composition in the gate |
| `trigger_heuristics` | list of input-pattern → action strings | When operator input matches, SUGGEST (judgment) / FIRE (mechanical). | gate auto-derive-focus + deletion auto-fire |
| `skill_kind` *(maybe)* | `judgment` \| `mechanical` | Drives SUGGEST-vs-FIRE (design call 2) + whether Stage 0 applies (design call 1). May reuse existing `concern:`. | `concern:` field |

The Layer B routing map is the aggregate of every skill's `trigger_heuristics` — buildable by walking frontmatter (sister to how `/index-rebuild` builds the CLAUDE.md skill table). It surfaces as an agent-facing "input → skill" section (extending CLAUDE.md "How to…") + a memory rule ("input matches a skill heuristic → suggest [judgment] / fire [mechanical]").

---

## Execution model — what a spawned subagent actually has (verified 2026-06-02)

The crux (Caramel's catch): many of these skills run as **spawned Layer-2 subagents** (`/precoding-audit-gate` fans out N general-purpose agents). A subagent starts in its OWN context — it inherits NONE of the orchestrator's conversation. So a consult-stage is only real if the executor can actually SEE the knowledge.

**Empirically verified** (general-purpose subagent introspection probe, this repo, 2026-06-02):

| Layer | In a spawned general-purpose subagent? |
|---|---|
| CLAUDE.md + CLAUDE.local.md | ✅ auto-loaded (prime directive, H1–H21, going-forward-rule index) |
| MEMORY.md (auto-memory) | ✅ auto-loaded (operator-collaboration rules) |
| DESIGN_PHILOSOPHY.md | ❌ NOT loaded — referenced only (read-on-demand) |
| DESIGN_SPECS/*.md bodies | ❌ NOT loaded — paths/titles only |
| decision-logs / postmortems / ledgers | ❌ NOT loaded |
| parent conversation | ❌ never inherited |

**So the RULES travel automatically; the deep KNOWLEDGE does not** — which is exactly why Stage 0 exists: it actively loads the read-on-demand slice. (Built-in **Explore / Plan** agents skip even CLAUDE.md per the Claude Code docs — for those, the orchestrator must inject the rules too, or not use them for judgment.)

**The mechanism that makes Stage 0 work in a cold subagent (no fragile pre-injection):**
1. The orchestrator's spawn prompt already says *"Skill spec: …/SKILL.md — READ FIRST"* (existing `/precoding-audit-gate` Stage 3 behavior).
2. The SKILL.md frontmatter carries the `associated_*` **manifest**.
3. Stage 0 in that spec says *"load your scoped slice now"* → the subagent reads the named specs / anti-patterns / decisions / postmortems / ledgers itself (it has Read/Bash).

→ Works identically whether the skill runs in the **main session** (knowledge read on demand) or as a **cold subagent** (self-loads from its own manifest). The orchestrator's only obligation is the one it already meets — ensure the subagent reads its SKILL.md. For Explore/Plan, add a rules-injection line. `/precoding-audit-gate` already injects a *"DESIGN_PHILOSOPHY family preload"* line into spawn prompts — we are **generalizing a proven mechanism**, not inventing one.

---

## Two consult modes — scoped (focused skills) vs broad (independent reviewers)

Consultation is calibrated by the skill's PURPOSE — not all of it is scoped:

- **Scoped consult (default — focused judgment skills).** A skill doing its specific job (`/readiness`, `/parity-check`) loads its declared `associated_*` slice. Relevance > breadth; avoids drowning the signal in noise. This is the "more info is good *only if scoped*" case.
- **Broad consult (independent reviewers / challengers / completeness-critics).** `/second-opinion`, the `/precoding-audit-gate` completeness-critic, the `/close-session` independent reviewer — their entire VALUE is catching what the proposer's scoped view MISSED. Scoping a challenger to the proposer's slice hands it the proposer's blind spots → it can't be a real second opinion. So it needs **any and all reference** — range across the full catalog.

These don't contradict ("avoid noise" vs "need everything") — they're per-ROLE: focused *execution* scopes; adversarial *completeness-search* ranges. For a challenger, breadth IS the job, and the extra cost buys the missed alternative.

**Mechanism for "any and all" without context blow-out:** a cold reviewer can't preload everything — give it ACCESS, not the payload:
- the **indices** — `DESIGN_SPECS/README.md` + `TAG_INDEX.md` (pattern catalog), `DOCS/RECURRING_BUG_PATTERNS.md` + `meta-anti-pattern-index.md` (code + reasoning anti-patterns), `MEMORY.md` (collaboration rules), the decision-log + postmortem dirs, the ledgers
- Read/Grep tools + the explicit mandate: *"range broadly; you exist to find what the author didn't think to look for"*
- spawn it as a **general-purpose** agent (rules auto-load), NOT Explore

The greppable, indexed doc-system is exactly what makes broad consult feasible: the reviewer pulls what it needs on demand. "Any and all reference" = ACCESS to all of it (indices + tools + mandate), not all-of-it-preloaded.

---

## Default EXECUTION framing — ADVERSARIAL by default (verification skills; binding 2026-06-11)

Distinct from the consult axis above (what KNOWLEDGE to load): this is the EXECUTION axis (how the verification RUNS). For any skill that VERIFIES / audits / checks / reviews a capital / determinism / correctness-critical surface, the DEFAULT execution is **ADVERSARIAL** — independent FIND/REFUTE agent(s) (≥2–3 with distinct lenses for a capital surface), per `adversarial-multi-agent-audit-methodology.md` — NOT a single confirmatory self-check, and the maker NEVER grades its own artifact (anti-self-attestation). This is **opt-OUT, not opt-in**: self-check / confirmatory is the exception, taken operator-explicitly OR with an in-line stated reason. The legitimate self-execution case is a genuinely MECHANICAL check — a deterministic tool or a re-run of a frozen golden — which is verified by RUNNING it, not by an agent (`feedback_independence_for_judgment_not_mechanical`); judgment surfaces (test completeness, finding-correctness, claim-soundness) are NOT. Policy: `feedback_adversarial_framing_default_for_checks` (binding); enforcement wiring: TECH_DEBT-164; error-shape it closes: meta-anti-pattern-index **AR-8** (self-attested verification — opt-in adversarial lost to momentum 3× in one session, each caught only by operator pushback).

---

## How it functions (worked walk-throughs)

**Walk-through 1 — Layer A on `/plan-check` (a judgment skill):**
1. Operator: `/plan-check <sprint>`.
2. **Stage 0 fires first.** The skill reads its `associated_specs` (e.g. cohesion / cross-plan-integration specs) + `associated_anti_patterns` (e.g. Class 18 mirror-incomplete, Class 21 parallel-descriptor) + runs the canonical-sister question against anything the plans propose to *build*.
3. Stage 0 emits a preamble: *"Existing coverage: pattern X already does this at `<file>`; Class 21 applies to plan B's proposed registry."*
4. The skill's normal cohesion checks proceed — but now any "let's build new infra" finding is automatically checked against "can we extend X?" before it's surfaced. The recommendation the operator sees already accounts for what exists.

**Walk-through 2 — Layer B routing (judgment → SUGGEST):**
1. Operator (mid-conversation): *"Hmm, should we just build a new registry for this?"*
2. The input matches a declared `trigger_heuristics` entry ("should we build X / is there something better" → canonical-sister + novel-alternative check).
3. Because the matched skill is **judgment**, the agent **SUGGESTS**: *"Before we build — want me to run the canonical-sister check? There may already be a foldable sister."* Awaits greenlight. Never silently fires.

**Walk-through 3 — Layer B routing (mechanical → FIRE):**
1. Work state reaches "all checks green, ready to commit docs."
2. Matches a mechanical trigger ("verify doc/plan correctness" → `check_session_docs.sh`).
3. Because it's **mechanical + safe**, the agent FIRES the tool directly (no greenlight needed — deterministic, read-only, per `feedback_independence_for_judgment_not_mechanical`).

---

## Relationship to existing infra (EXTEND, don't reinvent — the canonical-sister check applied to itself)

| Existing | Relationship |
|---|---|
| `canonical-sister-extension-discipline.md` (M1) | Layer A's step 3 **IS** this discipline's check, made a uniform stage instead of a 3-skill-only fire. This spec EXTENDS it (new surface axis: "skill self-consultation"), not a parallel discipline. |
| `/precoding-audit-gate` dod+bug composition | Layer A generalizes the gate's "compose specs-audit + anti-pattern-audit" into a per-skill Stage 0. The gate stays the heavyweight multi-agent version; Stage 0 is the lightweight inline version every judgment skill runs. |
| `/readiness` Stage 0 DESIGN_PHILOSOPHY preload | Proof that "Stage 0 consult" already works in one skill; this spec standardizes the shape. |
| `structural-enforcement-when-memory-insufficient.md` (M7) | If "skills should consult their knowledge" proves insufficient as convention, the Stage-6 escalation is a CI check that every `skill_kind: judgment` SKILL.md declares the three fields + has a Stage 0. |
| `doc-frontmatter-convention.md` | The home for the three new frontmatter fields (Task #2). |
| `meta-anti-pattern-index.md` | Where the routing-miss failure shape ("had the knowledge, didn't consult it") gets cataloged if it recurs. |
| `update-config` / settings.json hooks | See Open Question 3 — Layer B "FIRE mechanical" *could* be a real harness hook for fully-deterministic triggers; "SUGGEST judgment" inherently cannot (a hook can't make a judgment call). |

---

## Scope — which skills are JUDGMENT (get Stage 0) vs MECHANICAL (skip it)

Provisional partition (to confirm in discussion):

- **JUDGMENT (Stage 0 applies):** `/plan-check`, `/readiness`, `/precoding-audit-gate`, `/blindspot-scan`, `/dod-audit`, `/bug-check`, `/anti-spaghetti`, `/hft-audit`, `/ml-audit`, `/accounting-audit`, `/parity-check`, `/registry-fit-audit`, `/merge-scan`, `/trace-deps`, `/plan-dive`, `/finding-analyzer`, `/patch-planner`, `/post-ship-audit`, `/dead-code-trace`, `/dust`, `/test-strength-audit` + the scaffolding designers (`/plan-draft`, `/strategy-template`, `/doc-create`).
- **MECHANICAL (skip Stage 0; eligible for auto-FIRE):** `/ship`, `/sync-workspace`, `/sync-models`, `/index-rebuild`, `/capture-audit`, `/metadata-audit`, `/handoff`, `/accept-handoff`, `/close-session` (orchestrators — they already *compose* judgment skills; their own body is mechanical).

Edge cases to settle: `/capture-audit` + `/metadata-audit` are mechanical *detection* but feed judgment; orchestrators (`/close-session`, `/handoff`, `/accept-handoff`) compose judgment skills but are themselves mechanical. (Per `feedback_independence_for_judgment_not_mechanical`.)

---

## Sequencing — full scope, one ship (design → prove → roll out)

Scope = **all of it** (all 7 stores + routing + independent `/second-opinion` + gap-class naming + template). NOT split into "this ship / later ship" — that split would be effort-avoidance (per `feedback_no_defer_for_effort`). But we SEQUENCE it *within* the ship, because we're editing the skill system itself: an unproven consult-stage shape stamped across ~20 skills propagates any flaw 20×. Sequencing here is risk-control, not deferral.

1. **Design-complete** — THIS spec (all 7 stores) + the per-store frontmatter fields in `doc-frontmatter-convention.md`.
2. **Plan body + audit gate** — write the plan body (end-goal + acceptance criteria + this sequence); run `/precoding-audit-gate`. **Dogfood:** build this the way the discipline itself prescribes — consult-before-propose on our own change.
3. **Prove on 3 pilots** ✅ DONE (2026-06-02) — `/plan-check` + `/readiness` + `/precoding-audit-gate` carry Stage 0 (all stores); the independent `/second-opinion` is live.
4. **Roll out** ✅ DONE (2026-06-02) — ALL 39 skills classified (grep-verified, sweep green): **29 judgment** carry the full consult-stage (Stage 0 + `associated_*` + `trigger_heuristics`); **10 mechanical** carry `skill_kind: mechanical` + `trigger_heuristics` (routing only — no Stage 0, by design call 1). Layer B routing map = the union of `trigger_heuristics` + the memory rule (landed). REMAINING (close-out, not blocking): gap-class + §11.5 row (via `/close-session` harvest); AR-4 fail-loud-on-empty sliver; template propagation to `workspace-template`.
5. **Propagate** — generalized versions to `workspace-template/`; § 11.5 registry row + `/readiness` Check + bidirectional sister links.
6. **CI floor** — only if convention proves insufficient (M7); not pre-emptive.

---

## Open design questions (FOR DISCUSSION — not yet decided)

1. **Mn or framework-pattern? — RESOLVED 2026-06-02: its OWN meta-discipline.** As scope grew (decision-logs + postmortems + routing), it became the GENERAL "consult-before-propose" rule, with M1 (canonical-sister) a SPECIAL CASE of it. Folding the general under the specific is backwards → its own § 11.5 number at lock; M1 cited as first canonical instance. (Earlier lean was fold-into-M1; reversed once it outgrew the sister-check.)
2. **`/second-opinion` shape — RESOLVED 2026-06-02: a thin skill that spawns an INDEPENDENT agent.** It takes the proposed idea and tries to BEAT it (does a spec already cover this? simpler approach? ignored alternative?). Independent because the proposer shouldn't grade its own proposal (sister to `/close-session` Stage 5.5's independent reviewer + `feedback_runtime_executor_mode_for_judgment_skills`). Routable via a "is there something better?" trigger (Layer B). The checklist = canonical-sister + 4-pillar-self-audit + proactive-novel-alternative (all already codified).
3. **Who fires Layer B?** "SUGGEST judgment" is inherently agent-driven (a settings.json hook can't make a judgment call) → it's a **memory rule + the routing map I consult**. "FIRE mechanical" for fully-deterministic triggers *could* be a real harness hook (`update-config`). Do we want any Layer B trigger to be a hook, or keep all of Layer B agent-driven for now? **Leaning: all agent-driven at pilot**; revisit hooks only for a proven, fully-deterministic, high-frequency trigger.
4. **Does `associated_specs` replace or alias `loads_dynamically`?** They overlap heavily. Cleanest: `associated_specs` = the Stage-0 *consult* set; `loads_dynamically` = the *preload* set; often identical. Or merge them. Avoid two fields that drift (SSoT discipline). **Leaning: alias — `associated_specs` defaults to `loads_dynamically` unless overridden.**
5. **Enforcement floor.** Convention only at pilot, or a `check_doc_metadata` extension that warns when a `judgment` skill lacks the three fields? **Leaning: convention at pilot; CI only after rollout** (M7 — escalate when memory proves insufficient, not pre-emptively).

---

## Pattern lifecycle (per `pattern-codification-lifecycle.md`)

- **Stage 1 (problem identification):** operator design conversation 2026-06-02 (the `.resolve` spark + the "skills have knowledge but don't consult it uniformly" recognition).
- **Stage 2 (DESIGN_SPEC draft):** THIS DOC (2026-06-02, for discussion).
- **Stage 3 (first canonical):** lands when the 3 pilots carry Stage 0 + the frontmatter fields + the routing map is built.
- **Stage 4 (cohort):** rollout to remaining judgment skills + template propagation.
- **Stage 5 (CLAUDE.md):** promote when the consult-stage + routing map are load-bearing across the skill suite.
- **Stage 6 (cadence-locked):** CI check that judgment skills declare the fields (only if convention proves insufficient — M7).

---

## Cross-references

- `canonical-sister-extension-discipline.md` (M1 — Layer A's step 3 IS this check, made uniform)
- `structural-enforcement-when-memory-insufficient.md` (M7 — the Stage-6 escalation path)
- `pattern-codification-lifecycle.md` (the Stage 1→6 ladder this follows)
- `doc-frontmatter-convention.md` (home of the new frontmatter fields — Task #2)
- `audit-driven-pre-coding-gate.md` (`/precoding-audit-gate` parent — the proven composition seed)
- `implementation-layer-blindspot-taxonomy.md` (M4 — sibling meta-discipline shape)
- `meta-anti-pattern-index.md` (catalog home if the "had-knowledge-didn't-consult" miss recurs)
- DESIGN_PHILOSOPHY § 11.5 (the Mn registry + the "adding a new meta-discipline" 8-step procedure)
- memory `feedback_audit_canonical_sister_before_new_infra` / `feedback_framework_layer_payoff_diminishing_returns` / `feedback_independence_for_judgment_not_mechanical` / `feedback_no_question_boxes`

---

**End of v0.1 DRAFT.** Written for operator discussion 2026-06-02; nothing locked. Open questions in § "Open design questions" gate Stage 3.
