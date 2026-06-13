---
type: audit-methodology
stage: 3-first-canonical
version: 1.0
established: 2026-06-10
tags: [audit-methodology, meta-discipline, framework-discipline]
surface: [hot-path, slow-path, live-trading]
sister_specs: [audit-driven-pre-coding-gate.md, characterization-test-discipline.md]
applies_at_skills: [/handoff, /accept-handoff, /precoding-audit-gate, /trace-deps, /dependency-chain-trace, /bug-check, /dod-audit, /accounting-audit, /hft-audit, /ml-audit, /blindspot-scan, /registry-fit-audit, /second-opinion, /merge-scan, /parity-check, /plan-check, /plan-dive, /finding-analyzer]
---

# Adversarial multi-agent audit methodology

**Established:** 2026-06-10 (v5.15.5.F.4d.1.E.0.10; operator-stated preference + 3 same-session proofs)
**Status:** ACTIVE — the BINDING DEFAULT for judgment verification of any capital / determinism / correctness-critical surface. NOT operator-triggered: it fires whether or not anyone asks (opt-OUT, not opt-in). Self-check / a single confirmatory pass is the exception — taken operator-explicitly OR with an in-line stated reason. (Made binding 2026-06-11 per TECH_DEBT-164 + meta-anti-pattern AR-8 — opt-in adversarial lost to momentum 3× in one session, each caught only by operator pushback.)

## The discipline (one line)

When checking or auditing a surface, DEFAULT to spawning multiple INDEPENDENT agents PROMPTED TO FIND/REFUTE — prove the code wrong, default to suspicion — NOT to confirm it clean; then CROSS-CHECK their findings and RESOLVE disagreement by reading the disputed code yourself. A clean verdict from agents trying to BREAK it is worth far more than a clean from agents trying to CONFIRM it.

## When this fires

- **The operator asks you to "check / audit / verify / make sure" something** — especially on a capital, determinism, or correctness-critical surface. (Operator-stated 2026-06-10: *"checks should mostly be adversarial, they seem to perform better."*)
- Any high-stakes verification: capital-path change, money math, persistence/recovery, concurrency, wire format, train↔serve parity.
- A confirmatory pass returned GREEN but the surface is high-stakes — an adversarial re-pass means more.

The policy lives in memory `feedback_adversarial_framing_default_for_checks` (BINDING 2026-06-11); the multi-agent INFRASTRUCTURE already exists — `/precoding-audit-gate` Stage 3.5 (N=3 independent quorum) + `/second-opinion` (independent challenge, anti-self-attestation). The remaining work (TECH_DEBT-164, in progress 2026-06-11) is the WIRING: (A) the audit skills DEFAULT to this framing via the shared consult discipline, and (B) an auto-fire failsafe on the capital-work-declared-done surface (the hole `oms-ts-1` fell through). This spec is the METHODOLOGY they all point at.

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
6. **A MUTATING agent returns a CHANGE-MANIFEST.** Default-prefer read-only review agents (report findings, the orchestrator fixes). When an agent MUST mutate (e.g. a Workflow / worktree agent), its return MUST enumerate what it did — files touched · what changed · what's now OWED / needs-propagation — because a subagent's edits are out-of-the-orchestrator's-model BY DEFINITION, so without the manifest they become undocumented drift the orchestrator can't capture or propagate (`feedback_capture_and_check_are_model_bounded`).

## Nav-infra is a first-class input — pickup + the WHOLE audit / plan-check cohort (not just the completeness lens)

Step 3's "hand the hunter the nav-infra" is NOT only for a completeness lens, and NOT only for the spawned-agent case. It is the standard FIRST input for **pickup** (`/handoff` Stage 2.9 + `/accept-handoff` Stage 3.6) AND for **every audit / adversarial-audit / plan-check skill** in `applies_at_skills` — run inline or fanned-out. Two purposes, both first-class:

1. **Completeness surface-set** — measure coverage against the REAL set (DAG + findings-index), never a plan-headline or hand-recalled one (the false-floor close — worked example 4 below).
2. **Per-edit downstream-impact + data-flow** — *before judging or editing a function: what does touching it hit DOWNSTREAM, and where does its data flow IN from?* The CODE_MAP (`./tools/gen_code_map.sh`; `--byte-context`/`--composition` for type edits) + `/dependency-chain-trace` (`chain:<symbol>` → write/read sites by thread+cadence + the data-flow graph of which writes feed which reads + blast radius) + `/trace-deps` (call-sequence + mirror-data-flow) answer it; the path-discipline docs (`DESIGN_PHILOSOPHY.md` families + `latency-path-discipline.md` + `STRATEGY_AND_CODING_RULES.md`) say which rules the surface is held to. (Operator-stated 2026-06-11: this is the line of reasoning the audits should carry — "how we proceed when making edits to individual functions to determine the impact downstream, and how the data flows into it.")

**The cohort REFERENCES this — it does not paste a copy** (parallel-descriptor / Class-21 avoidance; categorical-trigger discipline). The single inheritance point is `skill-knowledge-consultation-and-auto-routing.md` Stage 0 item 6 — every judgment skill that already cites that shared Stage 0 (17 of the cohort at codification) inherits the nav-infra consult automatically; `/handoff` + `/accept-handoff` carry it via their own pickup stages. No skill restates it.

**Structural enforcement (M7 — convention/memory under-delivered; the operator had to hand-nudge the nav-infra in every session).** Textbook M7 surface: the artifacts exist (DAG, CODE_MAP, the trace skills) but nothing routed the cohort through them, so the discipline depended on the human remembering to enforce it — and "you can only do so much" by hand. The structural close: a mechanical check (`tools/check_navinfra_cohort_reference.py`, wired into `check_session_docs.sh` + `/capture-audit`) verifies every skill in this spec's `applies_at_skills` reaches the nav-infra consult (via the shared Stage 0 citation OR a direct pointer); a skill that drops it fails the check. That takes the human OUT of the manual-enforcement loop — the discipline self-perpetuates instead of depending on each session (or each operator nudge) to re-establish it.

## Reachability before severity — a confirmed PATH is not a reachable BUG (the A7/A5/A6 lesson)

Adversarial agents OVER-RATE (step 5) for a specific structural reason: they confirm the **PATH** (the bad sequence exists in code) and rate it real the moment they see it. But **a finding's severity is a property of its REACHABILITY, not its path** — and reachability is a property of the **data-flow INTO the trigger**, which is invisible at the finding's own line. Before rating ANY finding, trace the trigger's inflow: *where does the triggering value come from, and can it actually take the triggering value?*

**The discipline — ask "PATH or BUG?":** a PATH is "this code does X if input is Y." A BUG is "input CAN be Y." Confirm the second by tracing Y's inflow to ground (cfg clamps, registry validation, upstream structural invariants, what the caller actually passes). If the inflow structurally cannot produce Y → the finding is MOOT-UNREACHABLE (`feedback_moot_unreachable_disposition`), not a bug: downgrade, don't fix, and pin the guarantee that keeps it unreachable.

**Earned by 3 instances in one sub-sprint (`.E.0.10`), all rated MED by a hunt that confirmed the path and stopped:**
- **A7** (FlattenAll `price≤0` wipeout): path real; trigger unreachable — backtest gap=0 so the flatten can't fire, gate off-by-default, pre-warmup guarded, price = last-known-positive. → MOOT.
- **A5** (fill side not cross-checked): path real; the claimed *intra-process* "slot-decode slip" is unreachable — the fill→order match is a full 64-bit exact-id equality + bitmap-presence + dedup. The real (narrower) residual is a venue-side / future-LIMIT mismatch — a dormant tripwire, not the rated live Knight bug.
- **A6** (ML blend unclamped → negative SL): path real; unreachable from any *in-engine* computation — cfg pcts are walker-clamped ≥0, Ridge weights clip non-negative, bandit weights are softmax. The only inflow to a negative is an unvalidated negative `label_sl_pct` in an on-disk stamp. → real but LOW (a stamp-ingest gap), not MED.

**The mechanical fix:** hand every adversarial agent the nav-infra (above) AND the explicit mandate — *"trace the trigger's inflow; rate REACHABILITY, not the path; default to suspicion the finding is over-rated."* Meta-anti-pattern *path-confirmed-severity-inflated* — harvested to `meta-anti-pattern-index.md` at `/close-session`.

## Worked examples (this session — 4 proofs in one day)

1. **D-190 sibling sweep.** 3 independent agents hunted the money path for OTHER parallel-derivation divergences. They (a) confirmed the gross fix complete — a clean verdict that meant more *because* they tried to break it — and (b) surfaced a genuine latent item (warm-restart replay folds ignore the stored booked fee `e.fee`) that a confirmatory pass would have rubber-stamped past.
2. **Cross-check caught an agent over-rating.** Agent 1 rated a warm-restart fee-replay HIGH (claimed `core_realized`/`realized_pnl` diverge by the full fee). Agent 3 REFUTED it by reading the actual callers (both replay folds pass a zero rate → both gross-of-fee → they agree). The DISAGREEMENT was the signal; reading the disputed code resolved it. A single agent — or a confirmatory pass — would have propagated the false-HIGH.
3. **The operator ran the lens on ME.** I over-rated `persist-8` as "capital-adjacent / major." The operator's adversarial pushback — *"are you sure it's a major issue?"* — forced a re-read that found it's paper-mode-only AND the phantom sell is guarded downstream (`OrderManager.hpp:1185` `active_bitmap` check) → LOW severity. The human running FIND/REFUTE on the agent is the same discipline, one level up.
4. **The nav-infra caught a false floor (the Net-1 completeness lens).** A characterization-net is only as good as the surface set it freezes. The `.E.0.10` money-surface completeness check, measured against the plan's 8-name *headline* list, read GREEN — but the **DAG** (`.E.1` touches the whole OMS money cluster) plus the **findings-index** (a second tier of MED OMS/fee findings sat in the register's "MED pending" row, invisible to the headline) showed money surfaces with no characterization. Adversarial framing AND the full surface set (DAG + findings-index) surfaced the false floor; either alone missed it. This is exactly why step 3 hands the hunter the nav-infra, not just the plan.

## Why it works (and why confirmatory doesn't)

A confirmatory pass ("verify X is correct") rationalizes toward GREEN — it reads the code looking for reasons it's fine, and finds them. An adversarial pass ("prove X is wrong") reads the code looking for the break, and finds those. SAME reviewer, same code, opposite framing → opposite outcomes. For capital/determinism the cost is asymmetric — a missed bug costs money, a false-positive costs minutes — so the asymmetry says HUNT, not confirm.

## Mechanical green ≠ content verified

A deterministic gate (the doc-CI sweep `check_session_docs.sh`, a compiler, a frozen-golden re-run) is legitimately verified by RUNNING it — `feedback_independence_for_judgment_not_mechanical` is the opt-out for mechanical work. But a gate verifies ONLY its own scope. A consistency/index gate proves the indexes are *consistent*; it says NOTHING about whether the *content* is *correct*. So passing it is NOT a stated-reason opt-out from the adversarial CONTENT pass on a capital/correctness surface — they answer different questions:

| Gate | Verifies | Blind to |
|---|---|---|
| Mechanical sweep (consistency) | sister-symmetry, tag-vocab, index sync, broken-ref, citation *syntax* | whether a cited `file:line` is *true*, whether a claim is *correct*, whether a test is *complete* |
| Adversarial content pass | claim soundness, citation truth, coverage, value-correctness | only what it isn't pointed at — so point N independent lenses |

The trap (`.E.0.10`, the AR-8 mechanical-green sharpening): a codification's doc-CI sweep went SWEEP CLEAN, was reported as "verified," and a 3-agent panel then found 2 HIGH stale `file:line` cites the mechanical gate is structurally blind to (it checks a citation is *well-formed*, never that the line *exists* or *says what's claimed*). **"The mechanical check is green" verifies a different thing than "the content is correct" — run BOTH on a capital/correctness surface.**

## Cross-references

- **Trigger / preference (memory):** `feedback_adversarial_framing_default_for_checks` ("check/audit → adversarial by default").
- **Anti-self-attestation siblings:** `feedback_passing_test_is_not_verification` (green ≠ verified; adversarially verify your OWN work), `feedback_independence_for_judgment_not_mechanical` (independent agent for judgment, deterministic tool for mechanical), `feedback_runtime_executor_mode_for_judgment_skills` ({independent|self|both}).
- **Capital posture:** `feedback_heavier_default_audit_posture_for_capital`.
- **Multi-agent infrastructure:** `audit-driven-pre-coding-gate.md` (fires N agents in parallel + synthesizes convergent/divergent — EXTEND to default this adversarial framing).
- **Scope + implementation layer:** `audit-scope-taxonomy.md`, `implementation-layer-blindspot-taxonomy.md`.
- **Structural-enforcement path:** TECH_DEBT-164 (wire this framing into the audit skills as the default — the memory codifies the preference; this spec the methodology; the skill-wiring is the remaining M7 piece).
- **Close-out completeness (M8):** `meta-disciplines/definition-of-done-and-armed-scout-verification.md` — the armed scout-first arming THIS spec defines (Step 3 + the nav-infra section) IS M8's verification half; M8 adds the enumerated **Definition-of-Done** contract a fix-ship close must satisfy, so the arming has a checklist to measure against (the M7 escalation of AR-8 — mechanical-green ≠ semantically-complete — at the close-out surface; canonical instance = the `.E.0.10` A25 close).
