---
name: decision-check
description: Combined investigate→adversarially-refute gate for a single design/fix DECISION before committing. Fires an INVESTIGATIVE agent (map the surface/options/blast-radius + recommend) THEN an independent ADVERSARIAL agent (FIND/REFUTE the recommendation — prove it wrong, find the simpler/safer option, name the cascade), then CROSS-CHECKS the two and flags their DISAGREEMENT for the operator to resolve by code-read. The lightweight DECISION-level sibling of /precoding-audit-gate (the heavyweight PLAN gate). Closes the gap /second-opinion (adversarial-only, no investigative-first) + /finding-analyzer (investigative-only, no refute) each leave. Anti-self-attestation; honors consult-before-coding — returns synthesis, never auto-proceeds.
type: skill
concern: pre-coding-gate
audit_cadence: ad-hoc
tags: [audit-methodology, adversarial-default, decision-gate, operator-collaboration]
surface: [registry, cfg-flow, hot-path, slow-path, wire-format]
sister_skills: [/second-opinion, /finding-analyzer, /precoding-audit-gate, /dependency-chain-trace, /trace-deps, /blindspot-scan]
loads_dynamically: [DESIGN_SPECS/audit-methodologies/adversarial-multi-agent-audit-methodology.md, DESIGN_SPECS/meta-disciplines/skill-knowledge-consultation-and-auto-routing.md, DOCS/DESIGN_PHILOSOPHY.md]
skill_kind: judgment
consult_mode: broad
associated_anti_patterns: [DOCS/RECURRING_BUG_PATTERNS.md, DESIGN_SPECS/meta-disciplines/meta-anti-pattern-index.md]
associated_decisions: [plans/<active-sprint>/decision-logs/]
associated_ledgers: [DOCS/TECH_DEBT.md, DOCS/PARITY_ISSUES.md]
trigger_heuristics: ["about to commit to a non-trivial design/fix DECISION (esp. one proposing infrastructure / relocation / a new pattern / a structural change) -> SUGGEST /decision-check"]
---

# /decision-check — investigate + adversarially refute a DECISION before committing

## Why this exists

A specific design/fix DECISION (which of N options? relocate or pass-in? new helper or extend the existing one?) is exactly where the **proposer's frame misses its own blind spot** — and an investigative pass alone *shares that frame* (it can independently endorse the same blind spot). The remedy is the binding adversarial-default ([[feedback_adversarial_framing_default_for_checks]]), but at the DECISION surface it kept getting **momentum-skipped**: the investigative half ran, the recommendation felt settled, and the adversarial half didn't fire until operator pushback.

**Canonical failure (A25 / D-204):** the proposer recommended relocating a helper to a shared header; an investigative agent *independently endorsed* a relocate path too; only the independent adversarial pass caught it was a `DOCS/DESIGN_PHILOSOPHY.md`-forbidden 24-TU wide cascade — and it was skipped until "did you run adversarial agents?". This skill makes **investigate→refute ONE invocation** so the adversarial half cannot be skipped. It is the M7 structural close for the decision surface (sister to TECH_DEBT-164's audit-skill wiring).

Distinct from the sisters (this is the gap they leave):

| Skill | Shape | Why it's not enough for a DECISION |
|---|---|---|
| `/precoding-audit-gate` | heavyweight PLAN gate (N SHAPE audits on a plan body) | too heavy + plan-scoped, not a single decision |
| `/second-opinion` | single adversarial challenger of a proposal | NO investigative-first phase (challenges the proposal as-given) |
| `/finding-analyzer` | investigative deep-dive on a FINDING | NO adversarial refute |
| **`/decision-check`** | **investigate-options → adversarially-refute → cross-check, for a DECISION** | — (fuses the two + the conflict-flag) |

## When to use

Before committing to a non-trivial design/fix DECISION — especially one that **proposes infrastructure, a relocation, a new pattern, or a structural change** (the surfaces where a proposer's cascade hides). NOT for a trivial/obvious decision (proportionate-response). Use it on the DECISION; use `/precoding-audit-gate` for a whole plan body.

## Invocation
- `/decision-check <the decision + the option(s) + the current recommendation>` — runs the full gate.

## Workflow (Layer-1 orchestrator — composes by reference; never auto-proceeds)

### Stage 0 — CLASSIFY THE ACCEPTANCE ORACLE (M10; MANDATORY before any dispatch; added 2026-07-19)

Before firing ANY agent, state — in one line, out loud — **what would catch a wrong answer**, and classify it:

- **TOTAL** — fails on ANY deviation: byte-identity against a reference implementation, an output golden, parity of two independent implementations, a round-trip identity. → the check **is** the review; accept the delegate's work on green and spend the saved review budget making another oracle total.
- **PARTIAL** — covers a subset of "correct": unit tests, a green build, a lint/CI sweep, "the feature works". → delegation is still fine, but a **context-carrying hand-review of the diff before commit is MANDATORY**, and it must be budgeted here, not treated as optional polish. **Re-running the delegate's own commands is NOT verification** — it reproduces the blind spot exactly.

If you cannot name the oracle, you do not have one; build it before dispatching. **Assume PARTIAL until demonstrated otherwise** — in this codebase the checks are partial nearly everywhere (TECH_DEBT-245/246 are two holes in a single gate enumerator).

The discriminator is NOT test count or coverage — it is **whether the check has an independent reference to disagree with**. A thousand hand-written assertions are PARTIAL; one diff against an independently-produced artifact is TOTAL.

This applies to the orchestrator's OWN findings too: a finding reported as a *count* of matches rather than read-and-classified matches is a partial check misleading its own auditor. → `DESIGN_SPECS/meta-disciplines/acceptance-oracle-totality-before-delegation.md` (M10) · memory `feedback_delegate_on_total_oracle_handreview_on_partial` · `/readiness` Check 47 · D-385.

### Stage 1 — INVESTIGATE (map the surface, ground the options)
Fire ONE investigative agent (general-purpose; the `/dependency-chain-trace` / `/trace-deps` / `/finding-analyzer` lens): trace the decision's surface — every site/consumer touched, the blast radius, the options + their *real* cost, re-grounded against CURRENT code (AR-3: cited line numbers are hints — verify). Output: a grounded surface map + (if none was given) a recommendation.

### Stage 2 — ADVERSARIALLY REFUTE (independent; FIND/REFUTE the recommendation)
Fire an INDEPENDENT adversarial agent (the `/second-opinion` lens — broad-ranging, NOT fed the investigative agent's conclusions as truth): default to "the recommendation is WRONG." Challenge: is it a **wide cascade** the boundary-stable gradient forbids (count the blast-TUs)? a simpler/safer option? a **sister that already covers it** ([[feedback_audit_canonical_sister_before_new_infra]])? a hidden cross-consumer break? mismatched blast-radius/proportionality? Per the binding adversarial-default this half is MANDATORY — it is the whole reason the skill exists.

### Stage 2.5 — Surface-matched skill routing (MANDATORY — applies to BOTH agents; added 2026-06-12)

Both agents are general-purpose with a generic investigative/adversarial lens — so they do generic code investigation UNLESS the prompt routes them to the DOMAIN skill that matches the decision's **material**. The orchestrator MUST name the surface-matched skill(s) in each agent's prompt (the agent applies that skill's methodology), not just the `/trace-deps` / `/second-opinion` lens. (Operator-surfaced 2026-06-12 — the `.E.0.10` per-fix checks: *"do those subagents use the appropriate skills for the type of check + the material?"* — the answer was "only if I route them.")

| Decision surface (the MATERIAL) | Route the agents to |
|---|---|
| money / fee / commission / P&L / balance / kill-switch | `/accounting-audit` (+ Class 43 / `Money_FillGross` SSoT) |
| hot path / branchless / cache-alignment / SIMD | `/hft-audit` (+ H7/H8 + `latency-path-discipline`) |
| cfg-flow / per-core override / registry | `/trace-deps` + `/dod-audit` + `cfg-scope-discipline.md` (+ Class 25/26/27) |
| ML / model / scaler / bandit / calib | `/ml-audit` |
| train↔serve identity / stamp body / wire-format | `/parity-check` (+ `wire-format-byte-preservation-discipline.md`) |
| recurring-bug-class / anti-pattern | `/bug-check` (against the matched Class) |
| DOD pattern application (bit-pack / X-macro / alignment) | `/dod-audit` |

Pick by the MATERIAL, not the decision's framing. A decision can span ≥2 surfaces → route to each. If no domain skill matches (pure design/sequencing), the generic lens is the floor. This is `[[feedback_auto_route_input_to_matching_skill]]` applied INSIDE the gate.

**Full arming (M8 — `meta-disciplines/definition-of-done-and-armed-scout-verification.md`).** The domain skill is necessary but NOT sufficient — a subagent boots BLIND (no CLAUDE.md / MEMORY / invariants / TOOLS.md / nav-infra; it knows only the prompt). Arm each agent's prompt with: the surface's **reference docs + invariants**; the **mechanical toolchain to RUN** (the `check_*.py`, grep patterns, `calls_graph_diff` — "run the tool", not just "read the code"); the **nav-infra** (CODE_MAP / the DAG). And tell it to **SCOUT** its surface BEFORE executing the directive (load → scout → execute), so it doesn't tunnel-vision the narrow ask and miss the surroundings — exactly how A25's F1 producer-bug hid behind a consume-side verify directive. Parity on FACTS + TOOLS; the ADVERSARIAL agent stays independent on the VERDICT (never fed the orchestrator's conclusion — a blind subagent is a confident subagent, the dangerous kind). One agent per concern; ALL findings, severity-classified, never top-N.

### Stage 3 — CROSS-CHECK (the value-add over running the two separately)
Compare Stage 1 + Stage 2. Where they AGREE → high-confidence — **but agreement is corroboration, not proof**: independent agents that share an approach/frame CAN converge on the same wrong answer (a shared blind spot), so spot-check whether both keyed on the same assumption before banking it. Where they DISAGREE → that is **signal, not noise**: surface the conflict explicitly. The orchestrator does NOT resolve it by fiat (the agents can BOTH be wrong — anti-self-attestation applies to them too).

**Resolution rule (HARDENED `.E.0.10` 2026-06-12 — D-207 / AR-11; distinguish FACTUAL from JUDGMENT disagreement):**
- **Factual disagreement** (does the code do X? is symbol Y reachable? does path Z exist?) → the orchestrator MUST resolve it by **reading the disputed code ITSELF, now, before surfacing** — never pick the cleaner / more-convenient narrative, never trust one agent over the other ungrounded. The code-read is **MANDATORY, not advisory, not "hand it to the operator."** Picking a story instead of reading the code is **AR-11 (resolve-by-fiat)** — the exact failure that motivated this hardening (committed in the session this skill was built).
- **Judgment disagreement** (which option is better given the trade-offs?) → surface BOTH groundings to the operator; this one the operator owns.

(A25 canonical, BOTH lessons: the two agents disagreed on whether the **sharded** trail reads `original_tp`; the resolver picked the convenient narrow-fix narrative by FIAT instead of reading the code — and BOTH agents had ALSO missed the per-strategy `*_ExitAdjustSharded` dispatch (shared blind spot). The finding-register contradiction forced the deciding code-read that caught both. That is why the factual-disagreement code-read is now mandatory.)

### Stage 4 — SYNTHESIZE (consult-before-coding)
One verdict — GREEN (both align, recommendation sound) / YELLOW (minor flags) / RED (recommendation refuted OR a better option found) — plus the per-conflict resolution list. Return it for operator review. NEVER auto-proceed ([[feedback_consult_on_audit_findings]]).

## Anti-patterns this prevents
- The proposer grading their own decision (AR-8 self-attestation) — the adversarial half is independent.
- An investigative pass STANDING IN for the adversarial one — it shares the proposer's frame (the A25 lesson).
- The adversarial half being momentum-skipped — it is now one invocation, not a remember-to-also-run.
- Letting one agent "win" a disagreement — Stage 3 flags it for code-read, never rubber-stamps.

## Cross-references
- `/second-opinion` (the adversarial half) + `/finding-analyzer` (the investigative half) — this skill fuses them for a decision.
- `/precoding-audit-gate` (the heavyweight plan-gate sibling) + `/blindspot-scan` (implementation-detail layer).
- [[feedback_adversarial_framing_default_for_checks]] (the policy this enforces at the decision surface — incl. the A25 sharpening) + `DESIGN_SPECS/audit-methodologies/adversarial-multi-agent-audit-methodology.md`.
- [[feedback_audit_canonical_sister_before_new_infra]] (a recurring Stage-2 refutation) + `DOCS/DESIGN_PHILOSOPHY.md` (boundary-stable-over-wide-cascade — the A25 catch).
- [[feedback_fix_toward_future_trajectory_not_static_state]] (the DOCUMENTED-DESTINATION lens — a fix is judged as a forward-compatible foundation increment toward the documented trajectory, not a static-state patch the rework discards; arm BOTH agents with the destination plan + `plans/_future/*` + the DAG so the verdict is "increment vs patch") + `DESIGN_SPECS/meta-disciplines/fix-toward-future-trajectory-not-static-state.md`.
- Motivating instance: decision-log D-204 (A25 — motivated the skill) + **D-205 / D-207 + AR-11** (the dogfood that HARDENED Stage 3 — the resolve-by-fiat failure committed *while dogfooding this skill*, which is why the factual-disagreement code-read is now mandatory) + TECH_DEBT-178 (which this skill closes).
