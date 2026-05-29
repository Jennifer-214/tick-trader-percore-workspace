---
name: tiered-audit-discipline-per-plan-scope
description: Audit cycle scope MUST tier by plan risk + spec amendment substantiveness. HIGH-RISK ships get 5-parallel-agent comprehensive audits + re-audit at every substantive amendment. MED-RISK gets 3-agent + re-audit at material amendments only. LOW-RISK gets 2-agent + skip re-audit for mechanical-only. TRIVIAL gets code+tests-pass. Avoids both under-auditing (silent bugs ship) AND over-auditing ritual (planning paralysis). Sister to feedback_iteration_spiral_signals_audit_meta_gap (WHEN-TO-STOP companion) and feedback_proportionate_response_to_audit_findings (response sizing companion); THIS RULE is WHEN-TO-START + WHAT-DEPTH.
metadata: 
  node_type: memory
  type: feedback
  originSessionId: fc2542a7-8662-4b21-a393-f1598d05e50b
---

The audit cycle has cost. 5-parallel-agent comprehensive audit takes ~10-15 min wall + amendment cycles take ~60-120 min focused work. Blanket-applying full audit discipline to every plan = planning paralysis. Skipping audits for substantive refactors = silent bug ship risk. The discipline needs TIERING based on plan risk + amendment scope.

**Why:** Codified 2026-05-26 at `.B.4` v1.7.3 cycle after pattern emerged across multiple ship cycles:
- `.B.4` v1.5 → v1.6 → v1.7 → v1.7.1 → v1.7.2 → v1.7.3: substantive amendment cycles each triggered re-audit; cross-methodology catches surfaced critical bugs
- `.B.3` v1.X cycles: structural extract; full audit discipline; multiple critical catches
- `.B.5-.B.11` queued plans: file-size split ships (mechanical reorgs); per `/plan-context-sweep` only need light verification, NOT full 5-agent comprehensive
- Pre-`.B.4` ships: more ad-hoc audit application; sometimes over-applied to mechanical work; sometimes under-applied to substantive work

Per `feedback_motivated_collaborator_for_caramel` + `feedback_plan_right_not_fast`: best-software path requires SCOPE-APPROPRIATE audit depth. Too little = bugs ship. Too much = planning ritual.

**How to apply — TIERED audit discipline:**

| Plan tier | Trigger conditions | Initial audit | Amendment-cycle re-audit | Targeted re-fire |
|---|---|---|---|---|
| **HIGH-RISK** | Hot path touched / cross-cutting (≥3 surfaces) / framework-level (new registry/macro/pattern) / multi-day effort / paper-test-blocking | `/precoding-audit-gate` (5-audit orchestrator) + `/blindspot-scan` + `/bug-check` parallel | At EVERY SUBSTANTIVE spec amendment: 5-parallel-agent comprehensive (plan-context-sweep + trace-deps + dod-audit + readiness + bug-check) | After every amendment cycle to verify |
| **MED-RISK** | Single-cohort extension (sister-pattern application) / new helper extract / new cfg field with cohort siblings / 1-2 day effort | `/readiness` + `/dod-audit` + `/bug-check` parallel (3 agents) | At MATERIAL amendments only (signature change / new decision / scope expansion) | After CRITICAL fixes |
| **LOW-RISK** | Mechanical refactor / file split / doc-only / sister-pattern application with established discipline / sub-day effort | `/readiness` + `/bug-check` (2 agents) | Skip re-audit for mechanical-only follow-ups | Skip unless new findings surface |
| **TRIVIAL** | Typo fix / comment update / single-line config / version bump | Skip audit cycle | N/A | Code + tests pass only |

**Substantiveness gate for re-audit at amendment:**

- **SUBSTANTIVE** = signature change / new decision / scope expansion / new META-discipline candidate / > 50 LOC plan body delta / cross-cutting concern surfaces / NEW CRITICAL finding → triggers re-audit at next-version spec
- **MECHANICAL-ONLY** = typo fix / citation drift correction / line range adjustment / wording clarity / cosmetic cleanup → no re-audit needed; document at next version close

When in doubt: err toward re-audit. Per `feedback_motivated_collaborator_for_caramel` cost-of-bug-shipping > cost-of-audit-cycle.

**Recognition markers (when this rule is being violated):**

- Heavy audit applied to mechanical file-split ship (over-auditing)
- No audit applied to hot-path-touching ship (under-auditing)
- Skipping re-audit after CRITICAL finding amendment ("we already audited this once")
- Running full /precoding-audit-gate for typo fix
- Plan body has no `audit_tier` field in frontmatter (audit discipline undeclared)
- Same audit type fired 4+ times in succession with no new substantive findings (iteration spiral signal — pivot to inflection check per `feedback_iteration_spiral_signals_audit_meta_gap`)

**Sister memories:**

- [[iteration-spiral-signals-audit-meta-gap]] — WHEN-TO-STOP companion (3+ iterations finding smaller findings = codify META-gap; this rule is WHEN-TO-START + WHAT-DEPTH)
- [[proportionate-response-to-audit-findings]] — RESPONSE-sizing companion (audit catches finding; this rule sizes the audit; that rule sizes the response)
- [[plan-right-not-fast]] — planning depth produces functional code; this rule scopes the depth
- [[no-defer-for-effort]] — defer is last-ditch; this rule prevents both under-defer (premature unlock) AND over-defer (planning ritual extending past inflection)
- [[motivated-collaborator-for-caramel]] — best-software path requires scope-appropriate audit (not skipping for effort; not ritualizing for safety)
- [[audit-canonical-sister-before-new-infra]] — applies to AUDIT skill selection (extend /precoding-audit-gate to support tier-based dispatch vs invent new skill)
- [[lead-with-architectural-merit-not-operator-tone]] — tier classification based on architectural merit (hot path? cross-cutting? framework-level?) not operator's stress level
- [[enumerate-helper-signature-args-before-extract]] — sister M6 META-discipline (THIS rule codified concurrently at v1.7.3)
- [[feedback_heavier_default_audit_posture_for_capital]] — **REFINES this rule** (2026-05-29; D-77): for money-bearing code the DEFAULT tier is raised; LIGHT is EARNED only where a Tier-1/2 deterministic guard already covers the surface (audit weight ∝ inverse deterministic coverage). Reverse-link to its refinement.

**Structural enforcement at `.B.4` ship close (Phase D Step D.10.5 expanded scope):**

- **NEW plan template field** `audit_tier:` at `DESIGN_SPECS/plan-templates/future-oriented-plan-template.md` frontmatter — required for every NEW plan body. Values: `HIGH-RISK / MED-RISK / LOW-RISK / TRIVIAL`. Rationale comment required if borderline.
- **NEW `/readiness` Check 34** — "Audit tier declared in frontmatter + audit scope applied matches tier". Catches both under-auditing AND over-auditing at plan-time.
- **`/precoding-audit-gate` skill amendment** — auto-select audit set based on plan body `audit_tier` field. HIGH-RISK fires 5-agent comprehensive; MED-RISK fires 3-agent; LOW-RISK fires 2-agent; TRIVIAL skips.
- **NEW plan template section** "Amendment cycle log" — tracks v1.X spec versions + SUBSTANTIVE vs MECHANICAL classification + which triggered re-audit + audit verdicts. Sister to "Pre-coding triggers (audit gate) — VERIFICATION STATUS" section in `.B.4` v1.7.X plan body.
- **MEMORY.md index update** (this rule's pointer added)

Total codification effort at Phase D Step D.10.5: ~30-45 min focused work (folded with M6 codification per `feedback_proactive_novel_alternative_consideration`).

**Worked examples (for future tier-classification calibration):**

| Ship | Tier | Rationale |
|---|---|---|
| `.B.4` train-serve execution-layer parity (current) | HIGH-RISK | 5-helper structural extract; 7 PARITY closures; cross-cutting (LIVE + BACKTEST + cfg); framework-level (new FOREACH_SLOW_PATH_GATE row + AUTOPOPULATE); multi-day effort |
| `.B.3` legacy empty-out + Class 21 + cfg-derived consumer framework | HIGH-RISK | Cross-cutting (49 globals + cfg-derived consumer migration); framework-level codification; multi-day |
| `.B.5` controller_test domain split | LOW-RISK | File-size split (mechanical reorg); 24 numbered sections to per-domain split; established `feedback_file_size_split_discipline` pattern; sub-day effort |
| `.B.6` EngineSharded subfolder split | LOW-RISK | Per file-size discipline; subfolder pattern application; NO new architectural decisions |
| `.B.11` ledger re-split + Class 32 amendment + umbrella postmortem | LOW-RISK | Mechanical re-split + class amendment (NOT new class codification per /plan-context-sweep finding); sub-day effort |
| Hypothetical `.F.5.A` ML framework parity ship | HIGH-RISK | New framework + ML surface + cross-cutting train-serve |
| Hypothetical TECH_DEBT-126 versioning rework | MED-RISK | External-positioning change; Version.hpp + README + GitHub release notes; 1-2h focused |
| Hypothetical typo fix to a docstring | TRIVIAL | Code + tests-pass only |

**Codification trigger (worked examples for future):**

`.B.4` v1.5-v1.7.3 cycle (substantive amendments triggered re-audit each time; 5-agent comprehensive at substantive layer; targeted /parity-check at mechanical layer) + `.B.5-.B.11` queued plans (mechanical reorgs; per /plan-context-sweep light verification sufficient; NO need for full 5-agent comprehensive). Pattern emerged: re-audit scope tracks amendment scope. Codified PROACTIVELY at this ship per `feedback_proactive_novel_alternative_consideration` (sister to M6 codification rationale; folded into same Phase D Step D.10.5 scope).
