---
name: second-opinion
description: Spawn a fresh INDEPENDENT agent to challenge a proposal / design / plan before committing — does a spec already cover this? is there a simpler or more robust approach? what alternative are we ignoring? Broad consult (ranges the full catalog, NOT a scoped slice) so it catches what the proposer's view missed. Anti-self-attestation — the proposer never grades its own proposal. Returns a challenge verdict + concrete alternatives for operator review; never auto-proceeds.
type: skill
concern: pre-coding-gate
audit_cadence: ad-hoc
skill_kind: judgment
consult_mode: broad
tags: [audit-methodology, meta-discipline, framework-discipline, operator-collaboration]
surface: []
sister_skills: [/precoding-audit-gate, /readiness, /dod-audit, /anti-spaghetti, /close-session]
loads_dynamically: [DESIGN_SPECS/meta-disciplines/skill-knowledge-consultation-and-auto-routing.md, DESIGN_SPECS/meta-disciplines/canonical-sister-extension-discipline.md, DESIGN_SPECS/README.md]
associated_anti_patterns: [DOCS/RECURRING_BUG_PATTERNS.md, DESIGN_SPECS/meta-disciplines/meta-anti-pattern-index.md]
associated_decisions: [plans/<active-sprint>/decision-logs/]
associated_postmortems: [plans/<active-sprint>/postmortems/]
associated_ledgers: [DOCS/TECH_DEBT.md, DOCS/PARITY_ISSUES.md]
trigger_heuristics: ["should we build X / is there something better / are we sure this is the right approach / is this the cleanest way -> SUGGEST /second-opinion (judgment — await greenlight)"]
---

# /second-opinion — independent challenger for a proposal

## What this does

Takes a proposal — a design, a plan, an "I'm about to build X" — and spawns a FRESH, INDEPENDENT agent whose only job is to try to **beat it**:
- Does a proven pattern / spec ALREADY cover this? (canonical-sister)
- Is there a simpler or more robust approach?
- What alternative are we NOT considering?
- Does this proposal's shape resemble something that bit us before? (postmortems / anti-patterns)

Returns a challenge verdict + concrete alternatives. **It does not decide** — consult-before-coding: the operator reviews and chooses.

## Why independent (anti-self-attestation)

The agent that PROPOSES a thing is the worst judge of whether it's the best thing — it's invested in its own framing and carries its own blind spots. A second opinion is only worth something from OUTSIDE that framing. So this ALWAYS spawns a fresh agent; never "I'll review my own idea." (Sister to `/close-session` Stage 5.5's independent reviewer; per `feedback_independence_for_judgment_not_mechanical`.)

## Broad consult — NOT a scoped slice

Unlike a focused judgment skill (which loads its narrow `associated_*` slice), the challenger MUST range broadly — scoping it to the proposer's slice would hand it the proposer's blind spots, and its whole value is finding what the author didn't think to look for. (Per `skill-knowledge-consultation-and-auto-routing.md` § Two consult modes.)

It can't preload everything, so it gets **access + a mandate, not the payload**:
- the **indices** — `DESIGN_SPECS/README.md` + `TAG_INDEX.md` (patterns) · `DOCS/RECURRING_BUG_PATTERNS.md` + `meta-anti-pattern-index.md` (code + reasoning anti-patterns) · `MEMORY.md` (rules) · the sprint's `decision-logs/` + `postmortems/` · `DOCS/TECH_DEBT.md` + `PARITY_ISSUES.md`
- Read + Grep tools
- the mandate: *"range broadly; you exist to find what the author didn't think to look for."*

Spawn it as a **general-purpose** agent (CLAUDE.md + CLAUDE.local.md + MEMORY auto-load), NOT Explore (which skips CLAUDE.md).

## Invocation

- `/second-opinion <proposal | plan-path | "the idea in one line">`
- `/second-opinion <...> [executor=independent|self|both]` — default **independent** (fresh agent). `self` = inline (operator-explicit; cheaper, loses independence). `both` = run + compare (max calibration). Per `feedback_runtime_executor_mode_for_judgment_skills`.

## The challenge checklist (what the independent agent runs)

1. **Canonical-sister** — grep the catalog: does a proven pattern / registry / skill ALREADY solve this? Could we EXTEND one instead of building new? Surface the menu (INLINE / ACCEPT / FOLD / ARCHITECT / NO-FOLD) per `canonical-sister-extension-discipline.md`.
2. **4-pillar self-audit** (per `feedback_audit_own_proposals_with_same_rigor`): DESIGN_SPECS coverage / anti-pattern exposure / operator-impact / novel-alternative.
3. **Proactive novel alternative** (per `feedback_proactive_novel_alternative_consideration`): name ≥1 genuinely different approach + its trade-off — even if the proposal wins, the alternative goes on the table.
4. **Resemblance scan** — does this proposal's shape match a past postmortem failure or a catalogued anti-pattern (code or meta)?
5. **Blast-radius / proportionality** — is the proposal's heaviness matched to the surface? (per `feedback_process_weight_by_surface_blast_radius`.)

## Output (return for operator review — NEVER auto-proceed)

- **Verdict**: SOUND-AS-IS / SOUND-WITH-TWEAKS / EXTEND-A-SISTER-INSTEAD / RECONSIDER (better alternative exists)
- **Strongest alternative** considered + why it does / doesn't win
- **Sisters found** (if any) + fold / no-fold call
- **Resemblance hits** (postmortem / anti-pattern matches)
- One concrete next step the operator can accept or reject

## When to fire (Layer B routing)

Auto-**SUGGEST** (never silently fire — it's judgment) when input matches: *"should we build X?"* / *"is there something better?"* / *"are we sure this is the right approach?"* / *"is this the cleanest way?"* / before committing to new framework infrastructure.

## What this is NOT

- Not the heavyweight gate — `/precoding-audit-gate` fans out N audits in parallel; `/second-opinion` is the lightweight SINGLE-challenger version (one fresh agent, broad-ranging).
- Not a decider — it challenges + surfaces; the operator chooses.
- Not a code reviewer — it challenges the IDEA/approach, not the implementation (that's `/code-review` / `/bug-check`).

## Sister disciplines

- `skill-knowledge-consultation-and-auto-routing.md` (parent meta-discipline; the broad-consult mode)
- `canonical-sister-extension-discipline.md` (the "do we already have this?" check)
- `/precoding-audit-gate` (heavyweight multi-agent gate; this is the lightweight single-challenger version)
- `/close-session` Stage 5.5 (independent reviewer — same anti-self-attestation shape)
- memory: `feedback_audit_own_proposals_with_same_rigor` · `feedback_proactive_novel_alternative_consideration` · `feedback_independence_for_judgment_not_mechanical` · `feedback_runtime_executor_mode_for_judgment_skills`
