---
title: Control-plane / data-plane separation — housekeeping + validation off the node trading cores
type: future-direction
status: draft-direction
established: 2026-06-15
origin: v5.15.5.F.4d.1.E.0.10 A6 corruption-guard design (operator-raised, pair-programming session)
sisters: [decoupling-endgoal-roadmap, per-node-purity-scale-invariance]
codification_target: DESIGN_SPEC (once the cluster/controller architecture is concrete, .E.1+)
---

# Control-plane / data-plane separation for housekeeping + validation

## The principle (operator-raised, A6 design 2026-06-15)

Non-trading **housekeeping** — model load + validation (corruption / drift / stamp-verify),
config management, health monitoring, hot-swap orchestration — belongs on a **CONTROL tier**
(cluster / controller cores), NOT on the **node trading cores** (which run the latency-critical
hot + slow paths). The node cores should spend clock cycles on TRADING, not validation.

This is the classic **control-plane / data-plane split**:

- **DATA PLANE (node cores):** hot path (tick→trade, ≤500ns p99), slow path (param rebuild,
  ≤100μs p99), per-node trading state. Keeps ONLY the cheap last-line sanity checks
  (e.g. the A6 *egress* per-cycle barrier range-check — one branchless compare).
- **CONTROL PLANE (controller / cluster cores):** the heavy/bursty/rare housekeeping —
  load + validate artifacts, detect corruption, verify stamps, run drift checks, manage config,
  orchestrate hot-swaps, monitor health — and hand the data plane a VALIDATED, ready-to-use
  artifact via a clean atomic/seqlock handoff, so the node just trades.

## Why it matters

- **Latency / determinism (H7/H8):** validation work (model load, corruption scan, drift check)
  is bursty + variable-cost. Running it on the node slow path injects JITTER into the trading
  cadence. Pushing it to the control plane keeps the node's slow-path budget (≤100μs) clean and
  the hot path (≤500ns) untouched.
- **Scale-invariance (H22):** the control plane prepares per-node artifacts; each node stays a
  PURE FUNCTION of its (already-validated) local inputs. The split *reinforces* per-node purity —
  it does not couple nodes (the controller fans validated artifacts out, one per node).
- **The decoupling endgoal:** this is the SAME separation the headless-runtime + multi-viewer +
  controller architecture rests on. → cross-ref `plans/_future/2026-05-12-decoupling-endgoal-roadmap.md`.

## How A6 already aligns (and where the general principle extends)

A6's corruption detection is **LOAD-time** (boot) + **rare hot-swap** — already off the per-tick
trading path. The SHALT state is a single bit read on the slow path (cheap). The egress per-cycle
barrier-range check is the cheap last-line on the node. So **A6 is already control-plane-aligned**
by accident of *where model-load happens* — it does NOT need to change for this principle.

The general principle makes this EXPLICIT + extends it: as the cluster architecture lands (.E.1+),
the **controller cores should OWN** model load + validation (incl. the A6 corruption scan + the
hot-swap shadow-load), handing nodes validated `ezoo` artifacts. The node keeps only the egress
sanity-check. The hot-swap shadow-load (today on the node's slow path, rare) is the first concrete
candidate to migrate to the control plane.

## Live corruption vs load corruption (the boundary — answers an operator question)

- **Corruption** (NaN / garbage barrier) is a **LOAD-time** event: a corrupt on-disk artifact at
  boot or hot-swap. Models do NOT spontaneously corrupt in-memory during execution — the
  `ModelHandle` is read-only post-load (ML invariant), barriers fixed at load.
- The A6 **EGRESS** per-cycle range-check IS the node's cheap defense against ANY barrier going bad
  at emit (from any cause, incl. a hypothetical mid-execution bit-flip) — it re-validates every
  rebuild. So the node retains a per-cycle last-line; the control plane owns the heavy load-time scan.
  → This is why the control-plane idea does NOT lose mid-execution safety: the cheap last-line stays
  on the node, the heavy scan moves off.
- **Degradation** (staleness / drift — the model getting LESS ACCURATE as regime shifts) is DISTINCT
  from corruption, handled separately (`model_max_age` + drift gates). A live-degradation MONITOR,
  if desired, is ALSO a control-plane concern.

## Codification path (deserves design-spec treatment + cross-doc updates)

- Land as a **DESIGN_SPEC** (control-plane/data-plane separation; what belongs where; the validated-
  artifact handoff contract) once the cluster/controller architecture is concrete (.E.1+).
- Sisters: `per-node-purity-scale-invariance.md` (H22), the decoupling-endgoal-roadmap.
- Updates likely needed across: `CoreFrameworks/CLAUDE.md` (thread/concurrency model — name the
  control vs data tiers), the decoupling roadmap, possibly a `DESIGN_PHILOSOPHY` section or a new
  H-invariant on the split.

## Open questions (to resolve at codification time)

- The exact control/data boundary per housekeeping class (load-validation → control; per-cycle
  sanity → data; health-monitoring → control; drift-detection → ?).
- The handoff contract: how the control plane hands a VALIDATED artifact to a node atomically
  (the existing hot-swap seqlock/atomic is the model).
- Does this need a NEW thread tier, or do the existing global threads (producer / drainer / async)
  absorb the control-plane role? (Likely the controller cores in the cluster architecture.)
