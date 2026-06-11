---
type: audit-methodology
stage: 3-first-canonical
version: 1.0
established: 2026-06-10
tags: [audit-methodology, meta-discipline, framework-discipline]
surface: [hot-path, slow-path, live-trading]
sister_specs: [audit-driven-pre-coding-gate.md]
applies_at_skills: [/precoding-audit-gate, /bug-check, /dod-audit, /accounting-audit, /hft-audit, /ml-audit, /blindspot-scan]
---

# Adversarial multi-agent audit methodology

**Established:** 2026-06-10 (v5.15.5.F.4d.1.E.0.10; operator-stated preference + 3 same-session proofs)
**Status:** ACTIVE — the DEFAULT framing when the operator says "check / audit / verify / make sure" on a capital / determinism / correctness-critical surface.

## The discipline (one line)

When checking or auditing a surface, DEFAULT to spawning multiple INDEPENDENT agents PROMPTED TO FIND/REFUTE — prove the code wrong, default to suspicion — NOT to confirm it clean; then CROSS-CHECK their findings and RESOLVE disagreement by reading the disputed code yourself. A clean verdict from agents trying to BREAK it is worth far more than a clean from agents trying to CONFIRM it.

## When this fires

- **The operator asks you to "check / audit / verify / make sure" something** — especially on a capital, determinism, or correctness-critical surface. (Operator-stated 2026-06-10: *"checks should mostly be adversarial, they seem to perform better."*)
- Any high-stakes verification: capital-path change, money math, persistence/recovery, concurrency, wire format, train↔serve parity.
- A confirmatory pass returned GREEN but the surface is high-stakes — an adversarial re-pass means more.

The trigger/preference lives in memory `feedback_adversarial_framing_default_for_checks`; the multi-agent INFRASTRUCTURE is `/precoding-audit-gate` (which today is convergence-oriented — EXTEND it to default this framing, per TECH_DEBT-164). This spec is the METHODOLOGY both point at.

## The pattern (how to run one)

1. **Frame adversarially.** Prompt each agent: *"FIND the bug / REFUTE the claim / prove the code wrong / a FALSE CLEAN is the worst outcome / default to suspicion."* NEVER *"confirm it's correct"* — a confirmatory pass rationalizes its way to GREEN; an adversarial pass hunts.
2. **Spawn ≥2-3 INDEPENDENT agents with DISTINCT lenses/scopes** — e.g. for money: accounting path / fill-ingest path / replay-backtest twin; for a single finding: correctness / security / does-it-reproduce. Independence is the point: each blind to the others.
3. **Hand cold agents the context — INCLUDING the navigation-infra slice.** Subagents start cold (DESIGN_SPECS/decisions/postmortems do NOT auto-load). Give each: the bug class being hunted, the surface + file paths, the domain rules (e.g. `Money`=decimal vs `FPN_Binary`=features), a structured output shape, and *"cite file:line; READ the actual code; do not assume."*
   **For any COMPLETENESS lens — the highest-value adversarial dimension ("is there a surface with NO coverage?") — the agent MUST be handed the institutional nav-infra so it measures against the FULL surface set, never a hand-recalled or plan-headline one:**
   - the **dependency-graph DAG** (`subplans/*-dependency-graph.md`) — the authoritative "what does this touch" map + cross-ship-invariant rows for the surface under audit;
   - the **findings-index** (`CANONICAL-FINDINGS.md` + the live disposition register) — what is already found / dispositioned, so the agent hunts NEW and knows the open set (not re-finding known items);
   - the regenerated **CODE_MAP** (`./tools/gen_code_map.sh` then `DOCS/CODE_MAP.md`) — real `Pattern_FunctionName` file:line for the symbols in scope, not recalled sites;
   - the **guard-coverage matrix** / `tests/INVARIANTS_MAP.md` when the lens is "is this invariant actually enforced (which tier)?".
   An adversarial completeness check fed only the plan's headline list re-derives a **false floor**; fed the DAG + findings-index, it measures *real* coverage. The artifact existing ≠ the artifact being used — handing it to the hunter is what makes it work.
4. **Treat DISAGREEMENT as signal.** When agents disagree on a finding's severity or existence, that IS the finding — do NOT average it. Resolve it by READING THE DISPUTED CODE YOURSELF.
5. **Anti-self-attestation applies to the agents too.** Adversarial agents OVER-RATE (they're hunting, so they inflate). Verify every surviving finding against the actual code before acting — adversarial agents are a HUNTING tool, never a verdict.

## Worked examples (this session — 4 proofs in one day)

1. **D-190 sibling sweep.** 3 independent agents hunted the money path for OTHER parallel-derivation divergences. They (a) confirmed the gross fix complete — a clean verdict that meant more *because* they tried to break it — and (b) surfaced a genuine latent item (warm-restart replay folds ignore the stored booked fee `e.fee`) that a confirmatory pass would have rubber-stamped past.
2. **Cross-check caught an agent over-rating.** Agent 1 rated a warm-restart fee-replay HIGH (claimed `core_realized`/`realized_pnl` diverge by the full fee). Agent 3 REFUTED it by reading the actual callers (both replay folds pass a zero rate → both gross-of-fee → they agree). The DISAGREEMENT was the signal; reading the disputed code resolved it. A single agent — or a confirmatory pass — would have propagated the false-HIGH.
3. **The operator ran the lens on ME.** I over-rated `persist-8` as "capital-adjacent / major." The operator's adversarial pushback — *"are you sure it's a major issue?"* — forced a re-read that found it's paper-mode-only AND the phantom sell is guarded downstream (`OrderManager.hpp:1185` `active_bitmap` check) → LOW severity. The human running FIND/REFUTE on the agent is the same discipline, one level up.
4. **The nav-infra caught a false floor (the Net-1 completeness lens).** A characterization-net is only as good as the surface set it freezes. The `.E.0.10` money-surface completeness check, measured against the plan's 8-name *headline* list, read GREEN — but the **DAG** (`.E.1` touches the whole OMS money cluster) plus the **findings-index** (a second tier of MED OMS/fee findings sat in the register's "MED pending" row, invisible to the headline) showed money surfaces with no characterization. Adversarial framing AND the full surface set (DAG + findings-index) surfaced the false floor; either alone missed it. This is exactly why step 3 hands the hunter the nav-infra, not just the plan.

## Why it works (and why confirmatory doesn't)

A confirmatory pass ("verify X is correct") rationalizes toward GREEN — it reads the code looking for reasons it's fine, and finds them. An adversarial pass ("prove X is wrong") reads the code looking for the break, and finds those. SAME reviewer, same code, opposite framing → opposite outcomes. For capital/determinism the cost is asymmetric — a missed bug costs money, a false-positive costs minutes — so the asymmetry says HUNT, not confirm.

## Cross-references

- **Trigger / preference (memory):** `feedback_adversarial_framing_default_for_checks` ("check/audit → adversarial by default").
- **Anti-self-attestation siblings:** `feedback_passing_test_is_not_verification` (green ≠ verified; adversarially verify your OWN work), `feedback_independence_for_judgment_not_mechanical` (independent agent for judgment, deterministic tool for mechanical), `feedback_runtime_executor_mode_for_judgment_skills` ({independent|self|both}).
- **Capital posture:** `feedback_heavier_default_audit_posture_for_capital`.
- **Multi-agent infrastructure:** `audit-driven-pre-coding-gate.md` (fires N agents in parallel + synthesizes convergent/divergent — EXTEND to default this adversarial framing).
- **Scope + implementation layer:** `audit-scope-taxonomy.md`, `implementation-layer-blindspot-taxonomy.md`.
- **Structural-enforcement path:** TECH_DEBT-164 (wire this framing into the audit skills as the default — the memory codifies the preference; this spec the methodology; the skill-wiring is the remaining M7 piece).
