---
name: capture-audit
description: Mechanical drift-check verifying that decisions/memories/skills/plan-amendments made in the current session have been propagated to all places they need to be. Catches "I decided X but never updated Y" failure mode. Runs as pre-commit gate (via /sync-workspace) + pre-handoff gate (via /handoff) + standalone. Fast (~30 sec). Checks MEMORY.md index sync, plan body frontmatter completeness (audit_tier + sister_specs), decision-log artifact existence + sentinel matching, handoff doc currency (PENDING items vs git log), Stage 6 promotion candidates, skill-in-CLAUDE.md-suite linkage, every NEW skill→memory→DESIGN_SPECS cross-ref completeness.
type: skill
concern: workflow
audit_cadence: per-commit + per-handoff + per-version-bump
tags: [meta-discipline, doc-discipline, framework-discipline, structural-fix]
surface: [doc-pipeline, plan-pipeline, skill-pipeline, memory-index]
sister_skills: [/handoff, /sync-workspace, /readiness, /plan-check, /metadata-audit]
loads_dynamically: [MEMORY.md, CLAUDE.md, CLAUDE.local.md, DOCS/DESIGN_PHILOSOPHY.md]
applies_meta_discipline: M7 (structural-enforcement-when-memory-insufficient)
established: 2026-05-26
first_canonical_application: .B.4 v1.7.4 ship-close addendum cycle
---

# /capture-audit — Mechanical drift-check for decision-capture completeness

## Why this skill exists

Per `feedback_structural_enforcement_when_memory_insufficient` (M7 meta-discipline; codified at .B.4 v1.7.4): when memory codification + audit cycles prove insufficient for cognitive-load-amplifier surfaces, escalate to STRUCTURAL ENFORCEMENT.

Decision-capture drift is a textbook M7 application:
- Caramel goes deep on planning (per `user_adhd_deferred_reward_discipline`)
- New findings during planning hijack attention
- Prior decisions silently age out as new findings get addressed
- After many amendment cycles: plan body has accumulated decisions but some get DROPPED without record

Memory + manual discipline + audit cycles miss this. CI-style mechanical check catches it deterministically.

## What this skill checks (sequential)

### Check 1: MEMORY.md index sync

For every `memory/feedback_*.md` / `user_*.md` / `project_*.md` / `reference_*.md`:
- Has corresponding entry in `MEMORY.md` index
- Index entry uses `[Title](filename.md)` link format with description after `—`

**Orphans** (files with no index entry) → WARNING
**Stale entries** (index entry but file missing) → WARNING
**Format violations** (no — separator, wrong link format) → INFO

### Check 2: Plan body frontmatter completeness

For every plan body in `plans/<active-sprint>/subplans/*.md` modified within last 7 days (or all on `--wide`):
- `audit_tier:` field present (Check 34 enforcement)
- `sister_specs:` field present if Stage 3+ DESIGN_SPECS referenced
- `established:` date present
- `risk:` field present
- `effort_estimate:` field present
- `hot_path:` declaration present (UNTOUCHED / TOUCHED with rationale)

**Missing required fields** → BLOCK (with `--strict`) or WARN (default)
**Tier-vs-risk mismatch** (e.g., LOW-RISK declared but plan touches hot path) → WARN

### Check 3: Decision-log artifact existence

For current in-flight plan body version (extract from `**Status:** vX.Y.Z` line):
- Decision log exists at `plans/<sprint>/decision-logs/<plan-name-stem>-v<version>.md`
- If missing: propose creation with template structure
- If exists but stale (no entries since last plan body amendment): WARN

### Check 4: Decision sentinel matching

Grep plan body for `<!-- D: <id> -->` decision markers:
- Each must have matching `<!-- STATUS: pending|landed|dropped|deferred -->` marker
- Unmatched markers → DROPPED decision suspect; flag for operator review
- `<!-- STATUS: pending -->` older than 3 amendments → STALE; flag

### Check 5: Handoff doc currency

For each handoff doc in `plans/<sprint>/handoffs/*.md`:
- Scan for "PENDING" / "What's PENDING" / "STILL PENDING" sentinels
- Cross-check each PENDING item against git log + current artifact state
- PENDING items now landed → STALE handoff; suggest addendum

### Check 6: Stage 6 promotion candidates (per M7)

For each memory file:
- Check `worked_examples` section for ≥2 instances of same bug class
- Check if bug class has compile-detectable signature (parseable from description)
- Cross-check CLAUDE.md H invariants + RECURRING_BUG_PATTERNS Class N catalog
- Surface candidates for Stage 6 escalation per M7

### Check 7: DESIGN_SPECS Stage promotion eligibility

For each `DESIGN_SPECS/**/*.md` with `stage: 2-draft`:
- Check `first_canonical_application` field for landed reference (cross-check workspace git log)
- If landed: propose Stage 2 → Stage 3 promotion at next ship close

### Check 8: Skill-in-CLAUDE.md-suite linkage (recursive trust anchor)

For every `claude-skills/*/SKILL.md`:
- Verify skill name appears in CLAUDE.md `## Skill suite` table
- Verify skill name appears in CLAUDE.md `## How to ...` table (when applicable)
- New skill → automatically flagged for CLAUDE.md amendment if linkage missing

### Check 9: Memory file → DESIGN_SPECS sister cross-ref

For each memory file at Stage 3+ codification:
- Check for sister DESIGN_SPECS doc referenced in body
- Verify sister DESIGN_SPECS exists at cited path
- Bidirectional check: DESIGN_SPECS doc back-references the memory

### Check 10: CLAUDE.local.md going-forward rules currency

For each entry in CLAUDE.local.md `## Going-forward rules (index)`:
- Verify cited canonical-doc pointer exists
- Verify memory file referenced exists (if `feedback_*` cited)
- Skill referenced exists (if `/skillname` cited)

### Check 11: Forward-promised auto-write at prior ship close verification (NEW v5.15.5.F.4d.1.B.8)

Per `feedback_forward_promise_auto_write_verification` — when a ship close promises an auto-write (PARITY entry / TECH_DEBT / catalog amendment / DESIGN_SPEC Stage promotion / Stage 6 escalation candidate / next-ship-deferred work), verify at next-ship-time that the promised auto-write actually landed at the expected ledger location.

**Scope:** scan prior N ships (default: last 3 ships from `git log`) for forward-promise sentinels.

**Sentinels (regex patterns):**
- `forward advisory` / `Forward advisory`
- `DOCUMENTED-RISK entry at \.[A-Z\d.]+ close`
- `Stage 6 escalation candidate at \.[A-Z\d.]+`
- `auto-write at ship close: `
- `queued for \.[A-Z\d.]+`
- `deferred to \.[A-Z\d.]+`
- `promise.*landed.*at next.*ship`

**Scan locations:**
- `DOCS/recurring-bug-patterns/*.md` (Class catalog Worked Examples sections; e.g., `.B.7` Class 26 catalog line 98 promised DOCUMENTED-RISK PARITY entry)
- `plans/<sprint>/postmortems/*.md` (postmortem cross-references + lessons captured sections)
- `plans/<sprint>/subplans/*-postmortem.md` (per-ship postmortem cross-refs)
- Plan body close-out sections within `plans/<sprint>/subplans/*.md`
- `DESIGN_SPECS/**/*.md` Stage promotion forward-references

**Verification per sentinel:**
For each promised auto-write found, verify it landed at the expected ledger location:
- `DOCUMENTED-RISK PARITY entry` → grep `DOCS/PARITY_ISSUES.md` for matching entry
- `TECH_DEBT-NNN entry` → grep `DOCS/TECH_DEBT.md` / `DOCS/tech-debt/{open,closed,in-flight}.md` for entry
- `Catalog amendment` → grep referenced catalog file for amendment
- `Stage promotion` → grep DESIGN_SPECS frontmatter for promoted stage
- `Stage 6 escalation` → grep `tools/check_*.py` for the new check OR `claude-skills/*/SKILL.md` for the skill amendment

**Output:** list of UNFULFILLED forward-promises with:
- Prior ship reference + sentinel location
- Expected ledger location
- Suggested closure path (retroactive landing at current ship OR explicit re-defer with rationale)

**Invocation modes:**
- Included in `--deep` mode (default for pre-handoff): runs Check 11 against last 3 ships
- NOT in `--quick` mode (skipped for performance)
- `--check 11` to run only this check
- `--since <git-ref>` to scope to ships since reference

**Canonical mechanical invocation (per .D Phase F.2 deterministic-integration; M7 7th canonical structural enforcement landing):**

```bash
# Direct deterministic invocation — replaces LLM-orchestrated logic interpretation:
python3 /home/caramel/code/FoxML_Trader_v2/tools/check_forward_promise_audit.py \
    --since "${SINCE_REF:-HEAD~5}" \
    ${STRICT:+--strict} \
    ${JSON_OUT:+--json}
```

Sister to existing CI tool invocation patterns:
- `tools/check_per_core_registry_integrity.py` (Check 9 + Check 10)
- `tools/check_plan_body_symbol_existence.py` (B-Plus)
- `tools/check_meta_registry.py` (registry coverage)

LLM-orchestrated invocation (the legacy path before `.D` Phase F.2) had non-determinism risk: LLM could fail to invoke correct check, misinterpret output, forget to run at the right cadence. Replacing with explicit shell invocation locks the behavior + makes pre-commit hook integration trivial (sister to B-Plus shape).

**Sister disciplines:**
- `memory/feedback_forward_promise_auto_write_verification.md` (operator-collaboration rule)
- `memory/feedback_structural_enforcement_when_memory_insufficient.md` (M7 parent; Check 11 IS structural enforcement)
- `DESIGN_SPECS/meta-disciplines/sister-cohort-amendment-completeness-discipline.md` (sister at AMENDMENT layer; both catch silent drift)

**Worked example dogfood (NEW v5.15.5.F.4d.1.B.8 Phase G Step G.7):** fire Check 11 against `.B.8`'s OWN forward-promises (Stage 2 → 3 promotion candidates for `sister-cohort-amendment-completeness-discipline` + `forward-promise-auto-write-verification` disciplines + Check 11 self-verification at next-ship pickup) — verify each `.B.8` forward-promise tracked at expected ledger location OR documented as "deferred to next-ship-time per discipline". Ship codifying the discipline dogfoods the codified discipline.

### Check 12: Amendment-cascade propagation (NEW v5.15.5.F.4d.1.E.0.2)

Enforces **CP-1** (cascade-not-propagated) from the meta-anti-pattern-index — the mechanical member of the meta-error-tracking subsystem. When a decision / spec / definition is amended in ONE place, sibling docs that reference it can be left citing the stale form. This is the M7 mechanical escalation of `feedback_sister_cohort_amendment_completeness` (cascade-misses recurred at `.E.0.1` close → manual propagation; the gate-def change had to be cascaded to handoff/A2/D-74 by hand).

**Detection (resolves Decision C from the `.E.0.2` plan):**
1. **Diff-detect amended blocks** since the last sync/commit: changed `<!-- D/C/F: <id> -->` decision blocks (decision-logs), changed `## `/`### ` heading blocks (specs/plans), changed frontmatter `name:`/`version:`/`stage:` fields (DESIGN_SPECS).
2. **Extract key terms** from each amended block: the decision ID, the spec `name:`, distinctive noun-phrases / renamed symbols / changed definitions.
3. **Grep the corpus** (`plans/**`, `handoffs/**`, `decision-logs/**`, `memory/**`, `DESIGN_SPECS/**`) for those terms.
4. **Flag refs in UN-amended files** — a reference to the amended term living in a file NOT touched by the same amendment → candidate stale-cascade.

**False-positive surface (CP-1; load-bearing):** a term legitimately referenced in many places that does NOT need updating — a HISTORICAL-RECORD citation (postmortem / shipped-changelog / handoff describing the old state truthfully) must NOT be flagged. Distinguish "stale forward-looking reference" (update) from "truthful historical record" (preserve). Sister: `feedback_archived_changelog_preservation_discipline` + `feedback_terminology_evolution_bridge_not_history_rewrite`. Heuristic: refs in `postmortems/` / `changelogs/` / shipped-tag-dated docs default PRESERVE; refs in active plan bodies / current handoff / `CLAUDE*`/`MEMORY` default UPDATE-CANDIDATE.

**Mechanization (per `.E.0.2` R2 — start semi-mechanical, mechanize incrementally):**
- Semi-mechanical NOW: the check walks the git-diff → extract → grep → classify procedure above + flags candidates for operator review.
- Full tool (CANDIDATE — **not yet built**): `tools/check_amendment_cascade.py` (diff-detect + term-extract + corpus-grep + historical-record filter); wire into `--deep` + pre-commit once built. **Do NOT cite a `python3 tools/check_amendment_cascade.py` invocation as runnable until the file exists** (per heavier-default verify-mechanically; no fabricated tool refs).

**Reads:** the CP rows of `DESIGN_SPECS/meta-disciplines/meta-anti-pattern-index.md`.

**Invocation:** included in `--deep`; `--check 12` to run alone; `--since <ref>` to scope the diff window.

## Invocation

- `/capture-audit` — run all checks against current state; report findings; exit 0=clean / 1=findings (default WARN mode)
- `/capture-audit --strict` — BLOCK on findings (exit 1 even on WARN-level)
- `/capture-audit --quick` — run Checks 1-3 only (~5 sec; default for pre-commit hook)
- `/capture-audit --deep` — run all 12 checks (~30 sec; default for pre-handoff)
- `/capture-audit --check N` — run only Check N (target specific concern)
- `/capture-audit --since <git-ref>` — only check artifacts modified since reference

## Execution model

This is a Layer 1/2 orchestrator that DOES read/write checks (read source docs + write report). NOT spawning subagents — runs inline.

Output: structured drift report to stdout + optionally writes summary to `plans/<sprint>/capture-audit-reports/<date>-<reason>.md` (only on findings).

## Integration with sister skills

| Skill | Integration |
|---|---|
| `/sync-workspace` | Pre-commit invocation (`--quick` mode); WARN on findings; BLOCK with `--strict` env var |
| `/handoff` | Pre-handoff invocation (`--deep` mode); MUST PASS before handoff doc written |
| `/readiness` | Reference cross-check; Check 32/33/34 cite `/capture-audit` for some checks |
| `/post-ship-audit` (queued) | Will invoke `/capture-audit --deep --wide` for ship-close verification |
| `/plan-check` | Meta-audit complements; `/capture-audit` is faster mechanical layer; `/plan-check` is comprehensive |
| Pre-commit hook (`.git/hooks/pre-commit`) | B-Plus tool already runs; can additionally run `/capture-audit --quick` |

## Sister disciplines + cross-references

- `memory/feedback_structural_enforcement_when_memory_insufficient.md` — parent M7 meta-discipline
- `DESIGN_SPECS/meta-disciplines/meta-anti-pattern-index.md` — the META catalog whose CP rows Check 12 READS (CP-1 cascade-not-propagated)
- `memory/feedback_sister_cohort_amendment_completeness.md` — Check 12 is its M7 mechanical escalation
- `memory/feedback_session_decision_log_discipline.md` — Layer 2 discipline (session decision log)
- `DESIGN_SPECS/meta-disciplines/structural-enforcement-when-memory-insufficient.md` — M7 pattern body
- `DESIGN_SPECS/meta-disciplines/pattern-codification-lifecycle.md` — 6-stage progression (Check 7 uses)
- `claude-skills/handoff/SKILL.md` — Stage 1.8 invokes this skill
- `claude-skills/sync-workspace/SKILL.md` — pre-commit invokes this skill
- `tools/check_plan_body_symbol_existence.py` — B-Plus CI tool (sister structural-enforcement tool; different concern)
- `CLAUDE.md` § How to find anything — uses index this skill enforces

## When to skip

- Mid-amendment cycle to a single plan body (use after the cycle completes)
- Single-file edits with no decision-implications
- Right after previous `/capture-audit` run with no intervening changes

## Anti-patterns this prevents

- Memory file written but MEMORY.md index never updated → orphan memory invisible to future sessions
- Plan body amended but `audit_tier:` not declared → Check 34 violation
- Skill added but CLAUDE.md skill suite never updated → invisible to future skill discovery
- Handoff doc PENDING items left stale across multiple commits → cognitive load + drift
- DESIGN_SPECS Stage 2 DRAFT landing at first canonical but Stage promotion forgotten → catalog drift
- Operator-decision made mid-session but no record in plan body or decision log → DROPPED decision

## Tool maintenance

- Add new check (Check 11+) as new capture-drift surfaces are identified
- Update `CHECK_DEFINITIONS` constant when checks evolve
- Quarterly review: if Check N never finds anything → consider removing; if Check N finds repeatedly → consider auto-fix mode
