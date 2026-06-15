---
type: meta-discipline
stage: 3-first-canonical
version: 1.0
established: 2026-06-12
tags: [audit-methodology, meta-discipline, session-continuity, structural-fix, future-expansion]
surface: [session-pickup, ci-tooling, test-infrastructure]
sister_specs:
  - adversarial-multi-agent-audit-methodology.md
  - implementation-layer-blindspot-taxonomy.md
  - structural-enforcement-when-memory-insufficient.md
  - post-implementation-verification-v-class.md
canonical_instance: v5.15.5.F.4d.1.E.0.10 A25 close — F1 AUTO-core bug + stale trackers + untested A28 rode to "closed"; the armed deep-check caught them
registry_id: M8
---

# M8 — Definition-of-Done contract + armed scout-first subagent verification

**Established:** 2026-06-12 (v5.15.5.F.4d.1.E.0.10 A25 close). **Status:** ACTIVE — the close-out completeness discipline for any fix-ship / ship-close.

## The failure this closes: the never-terminating find-gap → fix-gap loop

A ship gets declared "closed"; a check finds gaps; they get fixed; another check finds more. It feels endless. Two joined root causes — **both** must be fixed, or the loop continues:

### Root 1 — no enumerated Definition of Done → every close is a SUBSET

"Closed" gets declared on whatever was thought of, which is always a subset, so the tail is whatever wasn't. The completeness criteria are otherwise **implicit + discovered-as-you-go** (each gap teaches a new dimension), which is exactly why it never terminates. Make them an explicit, enforceable **checklist**.

### Root 2 — verification subagents fire BLIND → they catch a subset

A freshly-spawned subagent boots with **nothing** but its prompt — no CLAUDE.md / MEMORY / invariants / TOOLS.md / nav-infra / domain skill. Its accuracy is hard-capped by what the orchestrator happened to load. A thin prompt ("verify these 5 assertions") produces a confident, narrow, *blind* pass. A blind subagent is a confident subagent — the dangerous kind.

## The Definition of Done (fix-ship close contract)

A fix-ship / ship-close is DONE only when EVERY row is green. Treat unchecked rows as OPEN, not absent. (Rows born from real gaps; extend as new dimensions surface.)

| Dimension | Done means |
|---|---|
| **Code** | the fix lands AND the PRODUCER path is verified, not just the consume/test path (F1 hid in the producer the char-test bypassed) |
| **Test-per-fix** | EACH landed fix has its own 3-lens char-test (not just the headline fix); non-vacuous + hand-derived |
| **Sanitizers** | `run_all_tests.sh --full` (asan/ubsan over any struct-grow / memory-reset), not just `build.sh test` |
| **Trackers flipped** | every disposition row (register + routing map) + the sprint MASTER banner + the handoff pointer flipped to LANDED — the SSoT, at fix-time |
| **Parity** | a PARITY_ISSUES entry for any live↔replay / train↔serve / backtest↔live divergence (the auto-write contract) |
| **Promises honored** | every "owed at close" / forward-promise in the decision log + register actually done (or re-dispositioned) |
| **Spawned obligations homed** | every follow-up a fix SPAWNS (torn-read enrollment, sibling sites, downstream notes) homed in TECH_DEBT / a future plan / the register |
| **Docs indexed** | `rebuild_doc_indexes` run; `check_doc_metadata` clean for the touched docs (scoped, not truncated) |
| **Meta codified** | any new bug class / meta-lesson surfaced this ship is in RBP / a DESIGN_SPEC / memory |
| **Mechanical floor** | `check_session_docs.sh` green (the index/sentinel/skill-linkage floor — necessary, NOT sufficient: it does not check the semantic rows above) |

The mechanical floor passing is the AR-8 trap: **mechanical-green ≠ semantically-complete.** The semantic rows are what a scout-pass verifies.

## The armed scout-first subagent discipline (the M8 core)

When firing any audit/verify subagent, the orchestrator MUST transfer the relevant slice of its own awareness into the prompt. **Load → scout → THEN execute:**

- **Load (parity on FACTS + TOOLS):** the surface's reference docs + invariants; the **mechanical toolchain to RUN** (the `check_*.py`, grep patterns, `calls_graph_diff` — not just "read the code"); the **nav-infra** (CODE_MAP / the DAG); the **domain skill** matching the material (`/accounting-audit` money · `/hft-audit` hot-path · `/trace-deps`+`/dod-audit` cfg/registry · `/ml-audit` · `/parity-check` train-serve).
- **Scout:** before executing the narrow directive, map the surface — what's adjacent, what feeds in, what reads out — so the agent doesn't tunnel-vision the directive and miss the surroundings (how F1's producer was missed by a consume-side directive).
- **Execute** the directive against the loaded context.

**The one exception — independence on the VERDICT.** Withhold the orchestrator's CONCLUSION/recommendation from ADVERSARIAL agents. Parity on the ground truth + tooling; independence on the judgment — else the agent inherits the orchestrator's blind spot (the entire reason an independent adversarial pass exists).

**Separation of concerns:** one agent per concern (code-correctness · discipline-completeness · parity · …), not a lump — each scouts + reports ALL findings in its lane, severity-classified, never top-N.

## The terminating procedure (stop the trickle)

1. **Run ONE armed, scout-first comprehensive pass** against the DoD checklist — full workspace + reference docs + toolchain loaded — that enumerates the COMPLETE remaining set in a single shot. Never trickle-discover.
2. **Home ALL of it** — finish the cheap rows now; hand off the rest with corrected state + the homed list.
3. **STOP at a clean boundary.** Extending instead of defining-done-and-stopping IS the loop. A clean stop with a complete, homed remaining-list is DONE; a "looks closed" with an unenumerated tail is not.

## Enforcement (where it lives, so it doesn't recur)

- **Skills (operational):** `/decision-check` Stage 2.5 (arm + scout-first) · `adversarial-multi-agent-audit-methodology.md` (the canonical agent-arming step) · `/close-session` + `/handoff` fire the armed DoD scout-pass before declaring close.
- **Mechanical (M7-grade backstop, candidate):** a `check_close_out_completeness.py` that verifies the enumerable DoD rows (every cited fix has a test marker · register/MASTER LANDED-flipped · handoff pointer current · forward-promises honored) — the structural close of the AR-8 recurrence. Until built, the armed scout-pass is the floor.

## Canonical instance — v5.15.5.F.4d.1.E.0.10 A25 close

A25 landed + committed + "closed" + handed off. An operator-prompted armed deep-check (2 scout-first agents: code-correctness + discipline, mechanical-tool-armed) then found: **F1** (a real capital bug — the producer resolved `tp_pct` from the configured `strategy_id`, AUTO→global, not `resolved_strategy_id`; the char-test bypassed the producer so it was structurally invisible); **stale trackers** (register + MASTER not flipped to LANDED; MASTER pointed to the superseded handoff); **A28 untested** (no char-test); a dropped torn-read enrollment; a missing PARITY entry; two unhonored forward-promises. None would have ridden to "closed" had the DoD been enumerated and a single armed scout-pass run. This spec is that fix.

## Cross-references

[[feedback_define_done_and_arm_scout_subagents]] (the memory) · `adversarial-multi-agent-audit-methodology.md` (§ nav-infra arming) · `implementation-layer-blindspot-taxonomy.md` (M4 — the implementation-detail layer F1 lived in) · `structural-enforcement-when-memory-insufficient.md` (M7 — the AR-8 recurrence escalation) · the meta-anti-pattern-index AR-8 (mechanical-green ≠ semantically-verified). Registry: DESIGN_PHILOSOPHY § 11.5 (M8).
