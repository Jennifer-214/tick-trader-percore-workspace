---
type: data-discipline
stage: 2-draft
version: 1.0
established: 2026-06-12
tags: [data-oriented-design, capital-safety, persistence, reconcile-recovery, scale-invariance, future-expansion]
surface: [oms-drainer, persistence, live-trading, hot-path]
sister_specs:
  - portfolio-soa-vectorization-pattern.md
  - per-node-purity-scale-invariance.md
  - cross-thread-multiword-read-consistency-discipline.md
living_spec: true
extends_when: "scaling-in/out becomes a real feature (§ Future expansion) — the full per-node sub-pool mechanism extends this spec's .E.1 foundation; do NOT build it speculatively"
---

# Per-node position ownership model (slot==core today; owner-tagged sub-pools tomorrow)

**Established:** 2026-06-12 (v5.15.5.F.4d.1.E.0.10; surfaced from the A25/A18 dialogue — the boot-reconcile collapse).
**Status:** LIVING-DRAFT. Documents (1) the CURRENT model, (2) the motivating defect, (3) the **`.E.1` foundation** to build (owner field + venue-net reconcile), and (4) the **future per-node sub-pool extension** to build *when scaling earns it*. Deliberately NOT static — § Future expansion is the planned growth, gated on need.

## The current model (slot == core, K=1)

`Portfolio<F>` = `uint16 active_bitmap` + `Position<F> positions[16]` (`CoreFrameworks/Portfolio.hpp:151`). Slot index ≈ node/core index: each pinned node owns ONE position slot (two for partial exits: legs A+B). Allocation/free is a bitmap (`__builtin_ctz`), same shape as the OrderPool. The hot-path exit gate reads `positions[node_id]` directly (O(1)); access is uniform via `& | ^` so position *order* is irrelevant at the access layer.

This is really the **K=1 special case** of a more general "K positions per node" model — simple, fast, deterministic, and adequate for today's one-net-position-per-node risk premise.

## The motivating defect: boot-reconcile collapse

On a live restart, `Reconcile_ApplyMissedFills` (`CoreFrameworks/Reconcile.hpp:205`) replays the venue's missed fills through `OrderManager_HandleFill`. Three layers stack into a data-loss bug (pinned by `tsa-live-2`; tracked as TECH_DEBT-072):

1. **Attribution loss.** A fill's owning node is recovered by searching the *in-flight order bitmap* (`Reconcile.hpp:226-245`). At boot that table is EMPTY → the search misses for every fill → all default to `origin_core_id = 0` (`:245`, a documented "operator-acceptable" boot default). The venue trade record carries no node/slot id.
2. **Overwrite, not aggregate.** Each fill → `handle_buy_fill(core_id=0)` → `Portfolio_OpenSlot(slot 0)`, which OVERWRITES. `Portfolio_AddQuantity` (`Portfolio.hpp:251`) exists for the add-to-existing case but reconcile doesn't use it → N fills collapse to 1 position, last-write-wins, N−1 fills' qty/price silently dropped.
3. **The one-net-position premise.** The per-node model wants ONE net position per node, so N buy fills on a node's symbol *should* be one net long (Σqty, weighted-avg entry), not N positions.

It is NOT primarily a memory or access-time problem — the bitmap+slot storage is already pool-like and uniform-access. It is an **attribution + reassembly-semantics** problem surfacing through the storage.

### The A18 band-aid (why it was rejected)

A18 proposed a "no-op a BUY on an already-active slot" guard in `handle_buy_fill` (sister to `handle_sell_fill`'s race guard). It does NOT fix the collapse — it flips last-write-wins → **first-write-wins**, which for a recovery path reconstructing *current* state is arguably worse (keeps the oldest fill). It broke `tsa-live-2` by changing the pinned surviving-fill semantics. **Reverted** at `.E.0.10`; re-homed here. A18's defensible residue is "scope the guard to the LIVE async re-entry path, not reconcile replay" — subsumed by the foundation below.

## The `.E.1` foundation (build this — proportionate)

Fix the collapse at the SEMANTIC layer + lay the cheap storage foundation, coordinated with the already-planned `.E.1` Position rework (D-55 SoA + D-206's 128→192B peak field — one struct, opened once):

1. **Venue-net reconcile.** On restart, reconstruct each node's ONE net position from the venue's *current* holding per symbol (the source of truth), not by replaying fill-by-fill. Dissolves attribution-guessing + overwrite + oldest/newest in one move. (Strategy state — `original_tp`, ratchet — still comes from the snapshot/defaults; that's the design nuance to resolve at `.E.1`.)
2. **Explicit `owner_node_id` on `Position`.** Make ownership a field, not an index implication. Cheap (1 byte), persisted (rides the D-55/D-206 version bump), and — crucially — does NOT preclude the sub-pool extension below.
3. **SoA layout (D-55).** Already planned; the owner field + masks are SoA-friendly.

This fixes the live-gating recovery defect WITHOUT a storage-model rework. **The bug alone does not justify the full mechanism.**

## § Future expansion — the per-node sub-pool model (build WHEN scaling earns it)

> **This spec is LIVING.** The model below is the planned generalization. Do NOT build it speculatively — build it when **scaling-in/out** (a node holding K>2 positions) becomes a real roadmap feature, OR when the partial-leg special-casing becomes a maintenance cost worth removing. The `.E.1` `owner_node_id` foundation makes it a small, additive change (the framework-extensibility goal), not a re-traversal.

**Generalize slot==core (K=1) → per-node sub-pools (K-per-node):**

```
each node owns a CONTIGUOUS sub-range of K slots: [node*K, (node+1)*K)
  + a per-node mask (which of its K slots are active)
  + each Position carries owner_node_id (from the foundation)
slot==core is just K=1.
```

**What it dissolves** (all four at once):
- Boot-reconcile collapse — distinct positions in the node's sub-pool, correct attribution, no overwrite, no oldest/newest.
- The partial-leg special-case — legs A+B become 2 owned positions, not a slot==core/+1 hack.
- Scaling in/out — a node holding K positions is native, not a workaround.
- A18 — moot (no overwrite to guard).

**Why per-node *sub-ranges* (not a global free pool):** keeps cache-locality (a node's positions stay contiguous — SoA-friendly), keeps determinism (allocation order is per-node, so snapshots round-trip), and keeps the risk boundary (K = the per-node position cap).

**The real costs (the future-expansion checklist — what "a ton of fields" concretely means):**

| Cost | Detail |
|---|---|
| Hot path (H7/H8) | `positions[node_id]` (O(1)) → per-node-mask walk (O(popcount), 1–2). Must stay branchless; SoA + SIMD over the active mask absorbs it. |
| New risk semantic | K>1 needs a per-node position-count cap + budget — a real new rule, not just storage. |
| Persist | `Position.owner_node_id` (foundation) + per-node masks + K → snapshot version bump (rides D-55's). |
| Fields added | `owner_node_id` (Position) · per-node `position_mask` + `position_count`/`K_cap` (NodeState) · the sub-pool allocator (per-node-range `ctz` replacing the global one). |

**When to build:** scaling-in/out on the roadmap, OR the partial-leg model's special-casing becomes a maintenance cost worth removing. Until then: foundation only.

## Build-vs-defer discipline (the proportionality this spec encodes)

- **The reconcile bug → venue-net reconcile (today's storage).** Do not rework storage for the bug.
- **`.E.1` is opening Position storage anyway** (D-55 + D-206) → add the `owner_node_id` foundation in the same cycle (`feedback_design_once_maintain_forever`): cheap, non-precluding.
- **The full sub-pool mechanism → defer to a real scaling need** (`feedback_overengineering_boundary_when_future_easier` cuts BOTH ways — pick the harder option only when the future-multiplier is real, not speculative). The foundation makes it a 1-row-style add later.

## Cross-references

- D-55 (`Portfolio/Position` AoS→SoA at `.E.1`) + `portfolio-soa-vectorization-pattern.md` — the layout axis this coordinates with.
- D-206 (exit-system trailing redesign; `Position` 128→192B peak field) — the other `.E.1` Position-storage opener.
- TECH_DEBT-072 (the boot-reconcile collapse) + TECH_DEBT-188 (this rework's home + the A18 deferral) + `tsa-live-2` (the pinning test).
- `per-node-purity-scale-invariance.md` (H22 — the per-node-purity premise this preserves) + `cross-thread-multiword-read-consistency-discipline.md` (the Position torn-read sibling).
- A25/A28 (`.E.0.10`) — the trail-anchor fixes that surfaced this; A18 (reverted band-aid, re-homed here).
