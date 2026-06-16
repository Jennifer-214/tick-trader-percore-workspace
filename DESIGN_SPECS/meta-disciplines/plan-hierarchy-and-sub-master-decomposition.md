---
type: meta-discipline
stage: 2-draft
version: 0.1
established: 2026-06-15
landing_ship: v5.15.5.F.4d.1.E.1 (the .E.1 plan-tree — first canonical, IN PROGRESS)
canonical_applications:
  - v5.15.5.F.4d.1.E.1 — first canonical (the v0.1 .E.1 plan reshaped to a SUB-MASTER over 7 sub-ship leaves)
sister_specs:
  - meta-disciplines/plan-decomposition-and-future-aware-agent-arming.md (PRODUCES the tree — finds the cut-lines this pattern then HOUSES)
  - meta-disciplines/audit-driven-sub-sprint-trajectory-verification.md (VERIFIES the multi-ship trajectory the tree expresses)
  - meta-disciplines/session-decision-log-discipline.md (the decision SSoT a leaf re-grounds against)
  - plan-templates/future-oriented-plan-template.md (the leaf body template)
tags: [planning, plan-hierarchy, sub-master, rolling-window, sub-sprint-discipline, scaffold-lifecycle]
surface: [planning, plan-pipeline]
applies_at_skills: [/readiness, /handoff, /accept-handoff, /plan-dive, /precoding-audit-gate, /plan-draft]
---

# Plan hierarchy + sub-master decomposition

**Intent.** When a ship is too big for one plan and gets decomposed (via the D/A stress-test, `plan-decomposition-and-future-aware-agent-arming.md`), its plan does NOT get thrown away and it does NOT become N flat siblings — it becomes a **SUB-MASTER (umbrella)** over **N sub-ship leaves**: a *tree*. This spec codifies (1) the tree structure + the parent↔child wiring, and (2) the **scaffold↔full-body detail lifecycle** that keeps the leaves from rotting.

## 1. The tree

```
MASTER.md                                  (sprint — the root)
 └─ <sub-sprint> decision-log + DAG         (the sub-sprint SSoT + topology)
     └─ <decomposed-ship>-foundation.md     → reshaped into the SUB-MASTER (umbrella)
         ├─ <ship>.0-*.md                    (leaf — sub-ship plan)
         ├─ <ship>.1-*.md
         └─ … <ship>.N-*.md
```

- The **original (pre-decomposition) plan is RESHAPED into the sub-master, never discarded.** Its timeless content (the substrate vision + architecture deep-dive) stays as the umbrella; its now-stale phase-by-phase coding sequence moves *down* into the leaves (re-grounded per-dive). (The `.E.1` v0.1 body — 1933 lines, stale after 3 numeric-core ships — became the sub-master this way.)
- **Frontmatter wires the tree** so every traversal tool (`/handoff`, `/readiness`, the rolling-window, the DAG) walks it: the sub-master lists `children:`; each leaf names `parent:` (the sub-master) + `predecessor:`/`successor:` (its sibling order).

## 2. What the SUB-MASTER holds (and what it does NOT)

HOLDS (the timeless + the cross-cutting): the substrate vision + architecture deep-dive · the **decomposition map** (the N leaves + their order + the lock rationale) · the **cross-ship / per-seam invariants** (incl. any residual HOLE a leaf-boundary must carry — e.g. the `.E.1` E.1.3→E.1.4 stub contract) · the **TD-closure distribution** (which leaf closes which debt — so designs build around the closures) · the **guard-matrix-row distribution** (which leaf fills which rows).

Does NOT hold: coding-ready detail. That lives in the leaves (§3). The sub-master is the *map*, not the *territory*.

## 3. The scaffold↔full-body detail lifecycle (the rolling-window applied to the tree)

Each leaf has **two states** — and writing all N leaves full up front is the anti-pattern (it rots: the v0.1 lesson):

- **SCAFFOLD** (every leaf, at decomposition time) — enough to *meaningfully reason + sequence + seed the body*, NOT line-by-line codeable. Standard contents: `{ scope · spine/layer · TD-closed · locked-decisions-honored · §4-guard-rows · INBOUND seam (needs from predecessor) + OUTBOUND seam (invariant the successor relies on) · design-SHAPE (key structs/fns/folds named) · the rollback anchor }`.
- **FULL BODY** (only the in-flight leaf) — coding-ready: **re-grounded against current HEAD by a C-class pass** (the scaffold's file:line/types are stale by its dive), the phase-by-phase steps, the pre-coding gate. Expanded *when the leaf becomes the dive*, never before.

**Why two states:** a scaffold is cheap + rot-resistant (it's shape + invariants, not code samples); a full body is expensive + rots fast (code samples drift with every intervening ship). Scaffold-all + full-body-the-dive = always-meaningful, never-stale-where-it-matters.

## 4. Maintenance — the tree co-evolves as leaves ship

A leaf shipping: flips its **register** rows (disposition record) · fills its **guard-matrix** rows · its **OUTBOUND seam becomes the next leaf's INBOUND check** (the rolling-window cross-ship invariant) · the **sub-master + DAG** update if the ship moved a node. The sub-master is a *living* map maintained `.E.1`-wide, like the guard-matrix.

## First canonical + promotion

First canonical: the `.E.1` tree (`D-225`) — the reshaped v0.1 `.E.1-foundation.md` sub-master over 7 leaves (E.1.0–E.1.6). Stage-2 DRAFT; promote to Stage-3 after `.E.1` ships ≥2 leaves through the scaffold→full-body→ship lifecycle. Mechanization candidates (M7, build-when-recurs): a `children:`/`parent:` frontmatter-link integrity check; the **TD-closure-per-leaf** `/readiness` check (every leaf lists the TD it closes — structurally enforces D-224).
