---
type: ledger-template
class_id: 49
title: Distinguishing signal collapsed upstream of the branch that must distinguish it (a lossy state-merge before the discriminating decision)
parent_index: DOCS/RECURRING_BUG_PATTERNS.md
established: 2026-06-15
surface_tags: [capital-safety, slow-path, ml-inference, ssot, state-machine]
severity: high
recurrence_count: 1
first_instance: 2026-06-15 (v5.15.5.F.4d.1.E.0.10 A6 INGRESS design — a CORRUPT model and a MISSING model both collapse into the single `MODEL_LOAD_FAILED` CoreState bit at `EngineCommon.hpp:361`, and the runtime branch meant to distinguish them [`StrategyParameters.hpp:801`, corrupt→SHALT vs missing→SimpleDip] runs AFTER the merge — so a corrupt model silently degrades to SimpleDip, the exact failure the design was built to prevent. PREVENTED — caught by the 3-I→3-A adversarial swarm + orchestrator code-read BEFORE the ingress was coded.)
closure_mechanism: detect + RECORD the distinction at the site where the cases are STILL DISTINGUISHABLE (upstream — here, at the barrier-load `ezoo_set_per_arm_barrier`, where "corrupt barrier" is a distinct condition from "no model"), and carry it forward as an EXPLICIT, separate signal (a distinct `MODEL_CORRUPT` state bit, never folded into the generic `MODEL_LOAD_FAILED`) to the branch that needs it. NEVER let a downstream branch read a state field that an upstream step has already mapped both cases onto. Detection — HEURISTIC: a branch B distinguishes cases {C1, C2} by reading a field F; trace F's writers — if an upstream writer maps BOTH C1 and C2 to the same value of F, the distinction is destroyed before B and B is structurally blind. The fix is always "split the signal at the source," not "branch harder downstream."
sister_classes: [47, 2, 43, 45, 44]
sister_memories: [feedback_single_source_of_truth_discipline, feedback_adversarial_framing_default_for_checks]
---

# Class 49 — Distinguishing signal collapsed upstream of the branch that must distinguish it

A downstream branch must tell two (or more) cases apart — `corrupt` vs `missing`, `partial` vs `complete`, `degraded` vs `absent` — and act differently on each. But an **upstream step has already merged those cases into a single generic state value** before the branch ever runs. The branch reads the merged value, cannot recover the distinction, and silently takes the wrong arm for one of the cases. It **compiles, runs, and is correct for the case the author tested** — the failure is for the *other* case, whose signal was destroyed upstream.

This is an **information-loss** sibling of the SSoT family (Class 43/45/47): not a divergent value (43), not a wrong source (45), not two authorities (47) — it is a **decision starved of the bit it needs because a prior step flattened the input space.**

## The canonical instance (A6 corrupt-vs-missing, prevented 2026-06-15)

D-220 ratified: a CORRUPT model (NaN/garbage barrier) → **SHALT-the-node** (refuse to trade + sticky retrain alert), DISTINCT from a MISSING model → **SimpleDip degrade**. The register prescribed "branch corrupt-vs-missing at `StrategyParameters.hpp:801`." But:

- Both a corrupt load AND an absent model set the **same** `MODEL_LOAD_FAILED` CoreState bit at `EngineCommon.hpp:361` (`if (!loaded && !ensemble_loaded)`).
- The runtime fallback at `StrategyParameters.hpp:800` (`if (!zoo || !CoreModelZoo_HasAny(zoo))`) early-returns to SimpleDip **before** reaching `:801`.

So by the time control reaches the branch that was supposed to distinguish corrupt from missing, the distinction is **gone** — both look like "load failed" — and the corrupt model degrades to SimpleDip, the precise silent-capital-strategy-swap D-220 was created to forbid. The branch is not buggy; it is **structurally blind**, because the discriminating bit was merged two layers upstream.

## The fix (structural)

Detect + record the distinction **where the cases are still separable** — at the barrier-load chokepoint (`ezoo_set_per_arm_barrier`), where "this barrier is corrupt" is a different event from "there is no model" — and carry it as an **explicit, separate signal**: a distinct `MASK_CORE_STATE_MODEL_CORRUPT` bit, never folded into `MODEL_LOAD_FAILED`. The downstream branch then *reads two distinct bits* and the distinction survives. Split the signal at the source; do not branch harder at the sink.

## Recurring symptom

- A branch needs to act differently on case A vs case B, but the state it reads was set by an upstream step that treats A and B identically.
- "It handles the missing case fine, but the corrupt case silently does the missing-case thing."
- A newly-added case (corrupt) is bolted onto an existing generic failure flag (load-failed) instead of getting its own signal — and inherits the generic flag's downstream handling.

## False-positive surface (M3)

- A branch that legitimately does NOT need the distinction — the upstream merge is intentional because both cases SHOULD be handled identically downstream. The class fires only when a downstream consumer genuinely needs a distinction the merge destroyed.
- A merge that happens DOWNSTREAM of every branch that needs the distinction — fine; the merge is after all decisions.
- Adding a case that truly is a sub-kind of the existing flag (no different action) — not this class.

## Canonical reference

`E.0.10-finding-disposition-register.md` § "A6 PRE-CODING GATE" + decision-log **D-221** (the reshape) + the 3-I→3-A / 1-I→1-A swarm that caught it. Code: the merge site `EngineCommon.hpp:361`, the blind branch `StrategyParameters.hpp:800-819`, the correct detect-at-source `ezoo_set_per_arm_barrier` (`CoreModelZoo.hpp:1123`). Sister: Class 47 (split-brain — two authorities for one control), Class 43/45 (SSoT-value family), Class 2 (display↔execution), Class 44 (bound-but-dead consumer — the inverse: a signal with no reader, vs Class 49's reader with no signal). [[feedback_single_source_of_truth_discipline]] · [[feedback_adversarial_framing_default_for_checks]].
