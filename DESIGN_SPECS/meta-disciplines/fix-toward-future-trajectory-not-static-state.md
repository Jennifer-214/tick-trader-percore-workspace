---
type: meta-discipline
tags: [audit-methodology, design-discipline, future-oriented, fix-scoping]
surface: [planning, audit-gate, bug-fix, refactor, live-trading]
stage: 2-draft
sister_specs: [audit-driven-pre-coding-gate, post-implementation-verification-v-class, adversarial-multi-agent-audit-methodology]
sister_memories: [feedback_design_once_maintain_forever, feedback_fold_findings_into_destination_plan, feedback_phased_pre_rework_correctness_foundation, feedback_dont_generalize_substrate_before_input_space_known, feedback_auto_pick_future_oriented]
established: 2026-06-15
origin: v5.15.5.F.4d.1.E.0.10 — TD-202 event-log UAF /precoding-audit-gate (operator-raised, pair-programming)
codification_target: CLAUDE.md priority-gradient / going-forward rule once 2nd canonical lands
---

# Fix toward the future trajectory, not the static present

## Principle

When changing capital- or architecture-bearing code that a **documented** future ship will rework, design the change as a forward-compatible **foundation increment** toward that documented destination — never a point-in-time patch against a static present that is about to change.

"Documented destination" = a concrete, written trajectory: the **E-series DAG** (`plans/<sprint>/subplans/*-dependency-graph.md`), the **`plans/_future/*`** vision docs (decoupling endgoal, control-plane/data-plane separation, per-node-purity), and the **destination plan body** that owns the surface's rework.

## Why

- **Throwaway avoidance.** A patch the rework undoes is discarded work — the effort buys nothing past the next ship.
- **Design-once (the deeper cost).** Re-traversing capital/determinism-gated code re-opens the *entire* verification surface (the [[design-once-maintain-forever]] cost): every byte-equivalence / replay / latency invariant the surface touches must be re-proven. A patch-then-rework pays that twice. An aligned increment pays it once — the increment is a strict subset the rework extends.
- **Compounding.** An aligned fix is the rework's first landed increment. Same marginal effort as the patch, but it accrues toward the destination instead of being thrown away.

## The forward-compatibility test (the discriminator)

A fix is a **foundation increment** (do-now) iff it is a strict SUBSET / precursor that the documented rework EXTENDS, never UNDOES. A fix the destination would discard or contradict is a **static-state patch** — reshape it, or home the whole thing to the destination plan.

Mechanically, at fix-design time:
1. Read the destination plan + the relevant `_future` docs + the DAG. State, in one line, *what the rework makes this surface BE.*
2. Check the proposed fix against that end-state: does the rework keep it (subset), or replace it (throwaway)?
3. If subset → land it now as the increment. If throwaway → reshape toward the end-state, or fold the whole fix into the destination plan and land only the minimal forward-compatible sliver now.
4. HOME the remainder in the destination plan (fold findings in, [[fold-findings-into-destination-plan]]). Homed-and-deferred, never unhomed.

## Boundary — do NOT over-apply (the guardrail)

This discipline is for **KNOWN, DOCUMENTED** trajectories only. It is NOT a license to:
- **Pre-build the future** — align the fix; don't construct the destination architecture early.
- **Generalize a substrate before its input space is known** ([[dont-generalize-substrate-before-input-space-known]]) — a fix proven over current consumers is not a general substrate.
- **Skip MVP for genuine unknown-unknowns** — MVP still applies where the destination is genuinely undefined (new feature, external dep). The discipline bites only where the destination is *already written down*.

So: ALIGN the fix to a documented destination; don't BUILD an undocumented one.

## Subagent lens (the audit classes consume this)

The audit subagent classes — the I/A fan-out, `/precoding-audit-gate`, `/decision-check` — carry this as **standing arming**:
- The gate's Stage-2 source-docs preload includes the destination plan + the `_future` trajectory docs + the DAG (so each Layer-2 agent measures the fix against the documented end-state, not the static present).
- Every proposed fix gets a verdict line: *foundation-increment* (forward-compatible) vs *static-state-patch* (the destination discards it) — the latter is a finding to reshape.
- This is the surface where "are we patching a static state or building a foundation?" becomes a mechanical audit question, not an after-the-fact operator catch.

## Worked example — `.E.0.10` TD-202 event-log UAF (first canonical)

The asan blocker was an OMS async-writer UAF (`OrderEventLog`). The inherited framing: "few-line, test-only `Init` harden." The gate (3-I→3-A) + the operator's trajectory question reframed it:

- **Destination (documented):** `.E.1`-foundation OWNS the OrderEventLog Init/Free/Start/Stop **lifecycle idempotency** (`.E.1-foundation.md:1926`); the **control-plane/data-plane** doc frames the async disk-writer as *housekeeping* → its end-home is a control tier, **single-owner of its `disk_file`**, handing nodes a validated artifact; **per-node-purity (H22)** makes each node's event-log a pure function of its own inputs.
- **Foundation increment (do-now, forward-compatible):** the quiesce-first `OrderEventLog_Init` guard (`StopAsyncWriter`-first when a writer runs). It is a strict subset of the lifecycle-idempotency discipline `.E.1` owns — the rework EXTENDS it (single-owner `disk_file`, race-free create→publish), never undoes it. Closes the asan gate. **Not** a static patch.
- **Homed to the destination (`.E.1`):** the single-owner-`disk_file` redesign, the production `OrderEventLog_Reset` 3-way disk race, the `LoadFromDisk` integrity gate, the writer→control-plane migration, the per-node event-log. Folded into `.E.1-foundation.md` at the gate (not left in TD-202 as a static-now problem).
- **Static-state patch REJECTED by the test:** the drainer-thread `pthread_join`-in-Reset fix — the rework's single-owner design discards it, and it independently blows the H8 drainer budget (~100×). The forward-compatibility test flags it before it's written.

The point: same surface, same bug — but the fix scopes itself toward where `.E.1` is going, so `.E.0.10` lands a stone `.E.1` builds on, not rubble `.E.1` clears.
