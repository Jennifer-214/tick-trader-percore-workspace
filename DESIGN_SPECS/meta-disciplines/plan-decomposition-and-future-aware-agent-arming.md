---
type: meta-discipline
stage: 2-draft
version: 0.1
established: 2026-06-15
landing_ship: v5.15.5.F.4d.1.E.1 (decomposition — first application IN PROGRESS)
canonical_applications:
  - v5.15.5.F.4d.1.E.1 — first canonical (the .E.1 mega-plan decomposition; in progress)
sister_specs:
  - meta-disciplines/audit-driven-sub-sprint-trajectory-verification.md (the SEQUEL — VERIFIES the trajectory this methodology CREATES)
  - meta-disciplines/definition-of-done-and-armed-scout-verification.md (M8 — the agent-arming base this EXTENDS)
  - meta-disciplines/fix-toward-future-trajectory-not-static-state.md (the FUTURE-aware lens)
  - audit-methodologies/adversarial-multi-agent-audit-methodology.md (the I/A fan-out + nav-infra arming)
  - meta-disciplines/session-decision-log-discipline.md (the decision SSoT the C-class sweeps)
  - meta-disciplines/plan-hierarchy-and-sub-master-decomposition.md (the SIBLING — HOUSES the cut-lines this spec finds, as a sub-master tree)
tags: [audit-methodology, plan-decomposition, future-aware, agent-arming, currency-check, sub-sprint-discipline]
surface: [planning, audit-orchestration]
applies_at_skills: [/precoding-audit-gate, /readiness, /decision-check, /handoff, /accept-handoff, /plan-dive]
---

# Plan decomposition + plan/future-aware agent arming

**Intent.** Two joined disciplines that a multi-ship sub-sprint needs but M8 (armed-scout) alone doesn't give: (1) **how to FIND the correct sub-ship cut-lines** when a mega-plan is too big for one ship (the D-class), and (2) **how to arm every planning/audit/verify agent to be PLAN-aware + FUTURE-aware** — not just task-aware + current-code-aware (the arming extension + the C-class). A sub-agent armed only with its narrow task + HEAD audits a static snapshot: it can't tell a foundation-increment from a discardable patch, it re-grounds nothing, and it will happily re-litigate a decision already made (the `.E.1` tombstone slip — an agent re-proposed `core_N_*` aliasing that D-219 had already ruled against).

## 1. The two arming dimensions (BEYOND M8's nav-infra)

M8 arms an agent with refs + toolchain + nav-infra (CODE_MAP/DAG) + the domain skill. This spec adds two trajectory dimensions:

- **PLAN-AWARE (inbound-currency + the decision set).** Arm the agent with (a) what the PREDECESSOR ships ACTUALLY landed — the disposition register's CLOSED rows + the real code + the decision log — and have it VERIFY the plan's shape against that landed reality, NOT the plan's stale self-assumptions; and (b) the **already-made decisions the work must HONOR**. The `.E.1` v0.1 acceptance still listed A1/A3/A6/NEW-1 as to-do though `.E.0` closed them; an agent must reconcile against the register, not the plan body.
- **FUTURE-AWARE (fix-toward-trajectory).** Arm with the destination docs (`plans/_future/*`, the DAG, the decomposition map) + judge every proposed fix as forward-compatible-foundation-increment vs static-state-patch the rework discards (`fix-toward-future-trajectory-not-static-state.md`).

## 2. Spec-citation arming — arm each agent with the GOVERNING spec for the piece it approaches

The operator directive (2026-06-15): *"reference the appropriate spec when we run the audits, and update the sub agents to reference those when approaching specific pieces."* An agent auditing a specific surface gets that surface's **governing DESIGN_SPEC(s) + the locked decisions for it**, not just the generic invariant list (`feedback_run_dedicated_audit_skills_not_just_armed_prompts` — the spec is the checklist; the bare invariants are a hint). The surface→(spec + decision) map is built per fan-out from the plan's `sister_specs` + the decision sweep. Worked map (the `.E.1` decomposition):

| Surface an agent approaches | Governing spec(s) | Locked decisions to honor |
|---|---|---|
| Aggregator | `global-aggregator-readonly-pattern` + `event-sourced-aggregator-o1-pattern` | D-34 (GLOBAL not per-cluster) · D-54 (O(1) push) |
| Cross-thread torn-read | `cross-thread-multiword-read-consistency-discipline` | D-193 (H22) · register §torn-read class |
| Core→Node rename / persisted identifiers | `dead-code-and-identifier-retirement-discipline` (H21) | D-27 · D-101 · **D-219 (reclaim-not-freeze)** · D-131 (epoch-free) |
| Money/accounting fields | `single-source-of-truth-discipline` (Money SSoT) | D-99/104/107/125/176 (Money core DONE) · H4 |
| Fill path | `fill-path-completeness-and-normalization-discipline` (RBP Class 46) | D-209 · D-212/213/214 (three spines) |
| Multi-exchange / cluster hierarchy | `foreach-exchange-meta-registry-pattern` + `cluster-node-hierarchy-filesystem-layout-pattern` | D-3 · D-15 · D-28 · D-58 (generic-framework) |
| Capital authority | `single-authority-predicate-for-mode-gating` | D-217/218 (NEW-1) · D-168 (live-OFF-till-.E) |

The methodology codifies the discipline; the per-fan-out map is assembled at gate time (and applied in the spawned agents' prompts).

## 3. The C-class CURRENCY sweep

Before locking ANY decomposition or re-grounding, a C-class agent (or the orchestrator) does two sweeps: **(a) code-currency** — re-derive every plan claim against HEAD (file:line, types, anchors, the named-not-designed sweep); **(b) decision-currency** — sweep the decision log (D-1..D-N) for every already-made decision the work CONSTRAINS-or-honors, so the new work neither re-litigates a settled call nor contradicts one. The `.E.1` instance: a sweep of all 223 `.E` decisions caught two real mis-builds (the cluster/node hierarchy is FOUNDATIONAL layout per D-15/D-28, not a follow-on framework; snapshot/stamp epoch breaks are FREE per D-131) AND prevented re-litigating D-219. **The decision log is the SSoT; the currency sweep is how a fresh agent inherits it instead of re-deriving (or contradicting) it.**

## 4. The DECOMPOSITION methodology (the D-class)

Given a mega-plan + the guard-matrix + the DAG + the decision set, FIND the correctness-driven cut-lines. **The cut-line principles (the SSoT):**

1. **Guards before the behavior they freeze** — close the guard-matrix HOLE cluster on a surface before a rework reshapes it (two-foundations, D-82).
2. **Mechanical-rename isolated from logic-rework** — one rollback anchor per concern, so a break is bisectable.
3. **Data-layout before its consumers** — define the struct correctly (right types from the start) before the code that uses it.
4. **Capital-critical clusters isolated + gated** — the HARD live-enable gate is its own ship; never bundled with mechanical churn.
5. **Framework substrate follows the trading-flow core** — additive, lower-risk → later. (Caveat: distinguish FOUNDATIONAL layout that only LOOKS like framework — e.g. the cluster/node hierarchy IS the container the nodes live in, so it sequences EARLY, not late. The decision sweep catches this.)
6. **No HOLE left open across an outbound seam** — each sub-ship's outbound seam = the next's inbound check (the rolling-window cross-ship invariant, D-72).
7. **Count is OUTPUT, not INPUT** — take as many sub-ships as correctness needs; never a forced a/b/c (operator directive).

**The decomposition also updates the trajectory artifacts:** the DAG gains the sub-ship nodes + intra-edges + per-seam invariants; the guard-coverage matrix maps each sub-ship → the rows it closes; the register continues as the disposition record; each sub-ship gets a full re-grounded plan body (D-29).

## 5. The agent roles (PROPOSED — Stage-2; promote after this application proves them)

- **D-class (Decomposition)** — proposes cut-lines from a stated lens (blast-radius / capital-criticality / dependency-order / by-spine). The I-class specialized to "where do the ships split."
- **C-class (Currency / re-grounding)** — the §3 sweep (code + decision currency + the shape-match).
- **A-class** challenges the D-class cuts: orphaned fold · HOLE-across-seam · guards-not-actually-first · a sub-ship that can't bisect under its own anchor · a severed cross-ship invariant · a re-litigated decision.

All armed per M8 + §1 + §2. D/C **folded into the I/A/V/D/C fan-out vocab** (`feedback_a_class_i_class_fanout_vocab`) at **D-224** (2026-06-15); structurally-enforce the §2 spec-citation arming in `/precoding-audit-gate` after `.E.1` proves the shape (`feedback_dont_generalize_substrate_before_input_space_known` — don't generalize the substrate before its input space is known).

## 6. The tabula-rasa fan-out template (the codified standard)

Every fan-out agent = a **CONSTANT base-arming block** (the *tabula rasa* — identical for every agent, every class) **+ a VARIABLE directive** (the role + task, injected at fan-out time). The base is what makes a cold-booted agent not-blind (M8 — a freshly-fired agent boots with NOTHING but its prompt); the directive is the one thing that changes per agent. Assemble the base ONCE per fan-out, vary only the directive.

### The CONSTANT base-arming block (assemble once per fan-out, reuse verbatim for every agent)
- **IDENTITY + GUARDRAIL:** "You are a `<I|A|V|D|C>`-class agent — `<role>`. Layer-2; do NOT spawn subagents. *(A/V: default-skeptical.)*"
- **ENGINE STATE:** HEAD `<sha>` + branch + the CURRENT-EPOCH reality (e.g. post-Ship-B: `Money` decimal 16B for accounting / `FPN_Binary` 16B for features) + user is Caramel (she/her).
- **NAV-INFRA (grep, never fabricate file:line):** CODE_MAP (`DOCS/CODE_MAP.md`, regen'd) · the DAG · the disposition register · the guard-coverage matrix.
- **THE DECISION SET:** the locked decisions the work must HONOR / never re-litigate (the C-class currency-sweep output).
- **THE SURFACE→SPEC MAP (§2):** the governing DESIGN_SPEC(s) + locked decisions for each piece the agent approaches.
- **THE TOOLCHAIN:** the mechanical `tools/check_*.py` to RUN (from `DOCS/TOOLS.md`).
- **SHAPE-MATCH:** verify against LANDED reality (the register's CLOSED rows + real code), NOT the stale plan's self-assumptions.
- **READ-FIRST:** the surface's governing spec(s) + this methodology spec + the relevant prior synthesis.

### The VARIABLE directive (the ONLY thing that changes per agent)
- The role-specific task (I: map `<surface>` · A: refute `<claim>` · V: verify `<shipped change>` · D: cut by lens `<L>` · C: re-ground `<claim-set>`).
- The OUTPUT contract: write report to `plans/<sprint>/plan_checks/<…>.md` + return a bounded synthesis (≤N words) in the role's verdict shape.

### Why "tabula rasa"
The base block is the standard arming every agent *starts blank from* — identical, so no agent is accidentally under-armed (the M8 failure mode: a thin-prompt verify-agent structurally blind to the producer). The directive is the surgical addition. The C-class currency sweep + the surface→spec map are the base block's *inputs* — built once per fan-out, then every agent inherits them. **This is the codified standard for `/precoding-audit-gate`'s Stage-3 spawn template + every ad-hoc fan-out.** Generalizes beyond decomposition — at promotion, extract to a standalone `agent-fan-out-template.md` (or fold into M8) + structurally enforce the base block in `/precoding-audit-gate`'s spawn template. **"F-class" is NOT a role** — *foundational context IS this base block* (every class stands on it); the classes (I/A/V/D/C) are what an agent DOES with the foundation.

## Relationship to the sisters

This **FINDS** the cuts; `audit-driven-sub-sprint-trajectory-verification` **VERIFIES** the resulting multi-ship trajectory; the rolling-window seam cadence (guard-matrix §5 / D-72) **SEQUENCES** the dives; M8 **ARMS** the agents; `fix-toward-future-trajectory` is the future-aware lens this operationalizes; `session-decision-log-discipline` is the SSoT the C-class sweeps. `nav-infra-as-first-class-CI-input` (D-196) is the mechanical floor this builds the plan/future layer atop.

**Stage-2 DRAFT.** First application = the `.E.1` decomposition (in progress, 2026-06-15). Promote to Stage-3 + fold the D/C roles into the fan-out vocab + structurally enforce §2 in the gate skill at `.E.1` close, once the application proves the shape.
