---
name: phased-pre-rework-correctness-foundation
description: "Before a high-risk multi-ship restructure, lay the correctness foundation in phases; the minimal pre-rework engine-fix scope = what the verification NET is meaningless without (not the whole findings bucket)"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a5882276-85a9-4550-a78d-e4ab42ed7eaf
---

Before a high-risk multi-ship restructure (e.g. a ~5,000-site rename + concurrency-model change), lay the correctness foundation in PHASES, and bound the pre-rework engine-fix scope **precisely**.

**The phases (D-73):** 0 Bedrock (validate the audit instrument + runtime-confirm the evidence + land the foundational fixes the net depends on) → 1 Lock current behavior (characterization tests + codified anti-pattern classes + CI checks on the CURRENT engine, BEFORE the rework) → 2 root-plan to GREEN first (the DAG-root plan stabilizes alone before downstream dives — everything assumes its substrate) → 3 rolling-window sweep of the rest → 4 GREEN gate → THEN code the rework. A per-ship audit gate STILL fires during coding (defense-in-depth).

**Three load-bearing refinements:** (1) **the no-reintroduction guarantee is the NET, not the audits** — push every guard to its highest tier (compile-time/CI/test > sweep); build the machine-enforced net on the current engine so a reintroduced bug is a red build, not a missed audit. (2) **Bedrock before the sweep** — the per-plan dives trust confirmed findings + a calibrated instrument, so validate-instrument + confirm-evidence precede the systematic sweep, else false GREENs. (3) **Two-phase net** — Net-1 = characterization tests for already-stable surfaces; Net-2 = the engine fixes the net *depends on* (a separate pre-rework ship), because a characterization test atop a non-deterministic / UB / locale-fragile input is a false floor.

**How to apply — net-gating scoping (the crux):** the minimal pre-rework fix scope = the findings the verification net is *meaningless without* (deterministic-input prerequisites: FP-determinism, replay-determinism, parity-oracle truth) — NOT the whole findings bucket. Ask "is the net trustworthy without fixing this?" → no = net-gating (fix first); a cleanup the net doesn't depend on = defer to the broad correctness ship. Bounding to *precisely* the gating set makes the net real, fast to stand up, and undiluted — over-scoping dilutes + delays; under-scoping leaves a false floor.

Surfaced `.E.0` 2026-05-29 (D-73/D-74). Sister: [[golden-master-over-reimplemented-oracle]] (the net's verification model); promotes to `meta-disciplines/audit-driven-sub-sprint-trajectory-verification.md` v1.1 + the D-70 enforcement-ladder/verifiability-triad spec.
