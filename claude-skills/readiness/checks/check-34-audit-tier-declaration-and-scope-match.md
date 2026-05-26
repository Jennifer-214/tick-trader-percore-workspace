---
type: skill-check
check_id: 34
parent_skill: /readiness
parent_path: claude-skills/readiness/SKILL.md
title: Audit tier declared in plan frontmatter + scope match
established: 2026-05-26
sister_checks: [check-32-plan-body-symbol-existence-verification, check-33-body-content-arg-enumeration]
---

# /readiness Check 34 — Audit tier declared in plan frontmatter + scope match (v5.15.5.F.4d.1.B.4+; tiered-audit discipline)

**When this fires:**
ALWAYS — runs at start of every /readiness audit. Verifies that the plan body frontmatter declares an `audit_tier:` field AND the audit scope actually applied to date matches the declared tier.

**Why this matters (v5.15.5.F.4d.1.B.4 lesson — tiered-audit codification trigger):**

Codified at v1.7.3 of `.B.4` as `feedback_tiered_audit_discipline_per_plan_scope` after pattern emerged across multiple ship cycles:

- `.B.4` v1.5 → v1.6 → v1.7 → v1.7.1 → v1.7.2 → v1.7.3 (HIGH-RISK ship): substantive amendment cycles each triggered re-audit; cross-methodology catches surfaced critical bugs
- `.B.5-.B.11` queued plans (LOW-RISK file-split ships): per `/plan-context-sweep` only need light verification, NOT full 5-agent comprehensive
- Pre-`.B.4` ships: more ad-hoc audit application; sometimes over-applied to mechanical work; sometimes under-applied to substantive work

Blanket 5-agent comprehensive on every plan = planning paralysis (per `feedback_plan_right_not_fast` + `feedback_motivated_collaborator_for_caramel` — scope-appropriate audit). Skipping audits for substantive refactors = silent bug ship risk.

**What to verify:**

1. **Frontmatter declares `audit_tier`:** Plan body has YAML frontmatter with `audit_tier: HIGH-RISK | MED-RISK | LOW-RISK | TRIVIAL`. Rationale comment required if borderline.

2. **Tier classification matches plan scope:**

   | Tier | Conditions |
   |---|---|
   | **HIGH-RISK** | Hot path touched / cross-cutting (≥3 surfaces) / framework-level (new registry/macro/pattern) / multi-day effort / paper-test-blocking |
   | **MED-RISK** | Single-cohort extension / new helper extract / new cfg field with cohort siblings / 1-2 day effort |
   | **LOW-RISK** | Mechanical refactor / file split / doc-only / sister-pattern application with established discipline / sub-day effort |
   | **TRIVIAL** | Typo fix / comment update / single-line config / version bump |

3. **Audit-cycle log present:** Plan body has "Amendment cycle log" section tracking v1.X spec versions + SUBSTANTIVE vs MECHANICAL classification + which triggered re-audit + audit verdicts.

4. **Audit scope applied matches tier:**

   | Tier | Initial audit | Amendment re-audit |
   |---|---|---|
   | HIGH-RISK | `/precoding-audit-gate` 5-agent orchestrator + `/blindspot-scan` + `/bug-check` | Every SUBSTANTIVE amendment |
   | MED-RISK | `/readiness` + `/dod-audit` + `/bug-check` (3 agents) | MATERIAL amendments only |
   | LOW-RISK | `/readiness` + `/bug-check` (2 agents) | Skip for mechanical-only |
   | TRIVIAL | Skip audit cycle | N/A |

5. **No tier mismatch markers:**
   - Heavy 5-agent audit on LOW-RISK file-split ship (over-auditing)
   - No audit on HIGH-RISK hot-path-touching ship (under-auditing)
   - Skipping re-audit after CRITICAL finding amendment ("we already audited this once")
   - Same audit type fired 4+ times with no new substantive findings (iteration spiral signal per `feedback_iteration_spiral_signals_audit_meta_gap`)

Verdict:
- **PASS** — frontmatter declares tier; tier matches scope; audit cycle log present; audit scope matches tier
- **GAP** — any criterion missed → add frontmatter / rebalance audit scope before next coding step
- **AMBIGUOUS** — tier classification borderline (e.g., MED-vs-HIGH); operator decision required + rationale comment in frontmatter

**Output:**

If GAP, add to the /readiness report:

```
### Audit tier declaration finding (Check 34)

Plan body <name> missing:
- [ ] `audit_tier:` field in frontmatter
- [ ] Tier matches scope classification (per criteria table)
- [ ] "Amendment cycle log" section present
- [ ] Audit scope applied matches declared tier

Risk: under-auditing (silent bug ship) OR over-auditing (planning paralysis).

Action: declare tier in frontmatter; rebalance audit cycle scope to match.
Reference: feedback_tiered_audit_discipline_per_plan_scope memory.
```

**Effort:** 30 sec at start of /readiness (frontmatter read + tier table cross-reference).

**Sister checks:**

- **Check 32** — plan-body symbol-existence verification (HIGH-RISK + MED-RISK ships should always run; LOW-RISK if plan has ≥3 ```cpp blocks)
- **Check 33** — body-content arg enumeration (HIGH-RISK + MED-RISK ships with helper extracts always run)

**Sister memories:**

- `feedback_tiered_audit_discipline_per_plan_scope` (parent rule)
- `feedback_iteration_spiral_signals_audit_meta_gap` (WHEN-TO-STOP companion)
- `feedback_proportionate_response_to_audit_findings` (response-sizing companion)
- `feedback_motivated_collaborator_for_caramel` (best-software path requires scope-appropriate audit)

**Trigger origin:** v5.15.5.F.4d.1.B.4 v1.7.3 cycle (codified after pattern across `.B.4` HIGH-RISK + `.B.5-.B.11` LOW-RISK ships needed tier-appropriate audit cadence).
