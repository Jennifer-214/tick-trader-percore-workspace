---
type: data-discipline
stage: 3-first-canonical
version: 1.0
established: 2026-06-13
tags: [data-oriented-design, scale-invariance, per-node-purity, capital-safety, framework-discipline, future-expansion]
surface: [slow-path, hot-path, cfg-flow, oms-drainer, persistence, live-trading]
sister_specs:
  - per-node-position-ownership-model.md
registry_id: H22
canonical_instance: A1 (.E.0.10 warm-restart read global take_profit_pct vs the per-strategy override — CLOSED) + A24 (.E.0.10 RebuildOneCore mutates flat resolved_cfg; per-node consumer reads the cores[slot] slice — LANDED .E.0.10 engine f2ef5d6, D-211 option c + Check-11 guard)
living_spec: true
---

# H22 — Per-node purity + scale-invariance

> The discipline doc for Hard Invariant **H22** (CLAUDE.md). The invariant is the premise the whole sharded
> architecture (and the `.E.1` multi-exchange / multi-cluster expansion) rests on; this spec is the WHY +
> the violation taxonomy + the structural close + the mechanical guard.

## The invariant

**Every design works INDEPENDENTLY and scales horizontally across N nodes and N clusters. A node's (and a
cluster's) trading state + logic is a PURE FUNCTION of its OWN local inputs** — its resolved cfg (including
`core_N_*` overrides), its positions, its strategy/model, its cluster's shared resources — with **NO coupling
to other shards or to flattened-global state on the sharded path.**

### The operational test (the one-line check)

**Adding the (N+1)th node — or the (N+1)th cluster — requires ZERO change to existing per-shard logic.**

If adding a node forces you to touch existing per-shard code, or if a shard's behavior changes when a *different*
shard's state changes, the design coupled a shard to something non-local. That coupling is the H22 violation.
A node is a self-contained strategy unit (a pinned CPU running one strategy on one symbol with its own
slow+hot thread pair, its own resolved cfg, its own position slot, its own capital allocation); its outputs
must depend only on its own inputs.

## Why this is load-bearing (not a style preference)

1. **Horizontal scaling is the product.** The engine's reason-for-being is per-node risk-sharding: drop in
   another pinned node and get another independent strategy unit. A shard that reads global/flattened state
   doesn't scale — the (N+1)th node would inherit or corrupt shared state.
2. **Determinism.** A shard reading cross-shard or flattened-global state introduces a dependence on
   scheduling / other shards' timing → non-reproducible (violates the determinism premise that gates live).
3. **Capital safety.** A per-node risk control (kill-switch, sizing, exit price) that silently reads a GLOBAL
   value instead of the node's resolved override fires at the wrong threshold for that node — a wrong-capital
   action. (A1: a restored position exited at the global TP, not the node's per-strategy override.)
4. **`.E.1` is built on it.** The Core→Node rename + per-node data layout + the multi-exchange `FOREACH_EXCHANGE`
   registry + the per-cluster aggregator all assume per-node purity. Breaking H22 now makes `.E.1` a re-traversal
   instead of a 1-row-style add.

## The violation taxonomy (how H22 breaks — each is a catalogued anti-pattern)

| Shape | Class | What it looks like |
|---|---|---|
| Cross-node iteration / global consumer reading a per-core field (or an unindexed-global read) | **26** | a loop over all nodes, or a consumer that reads `cfg.field` (flat) where it should read `cfg.cores[slot].field` |
| Scalar cfg-mirror — a single flat value caching what should be per-instance | **27** | one `last_X` scalar shared across nodes instead of `cores[slot].X` |
| Scope-erosion — a per-node consumer fn taking the full cfg | **25** | `fn(const ControllerConfig<F>*)` instead of `fn(const PerCoreCfg<F>*)` → the body can read a flat field |
| Reconstruct/replay path reads a DIFFERENT source than the forward path | **45** | **A1** — restore re-derived `live_tp` from global `take_profit_pct`, not the node's `ResolvePerFillTpPct` override |
| Torn cross-thread read of flattened money state | (torn-read class, `.E.1`) | a shard reads a 16B `Money`/`Position` from the OMS cluster bare → tears |
| Per-node adaptation written to / gated by a flat field no per-node consumer reads | **44** (cfg-mutation/cfg-flag) | **A24** — `RebuildOneCore` mutates flat `resolved_cfg.volume_multiplier`; the consumer reads `cores[slot]` |

## Canonical instances

- **A1 (CLOSED, `.E.0.10`):** warm-restart recomputed `live_tp`/`live_sl` from the GLOBAL `take_profit_pct`,
  ignoring the node's per-strategy override (`simpledip/mr/emacross_tp_pct`) → a restored position exited at a
  DIFFERENT price than while live. **Fix:** single-source the per-node resolution (`ResolvePerFillTpPct/SlPct`)
  for BOTH entry and restore — the node's own resolved value, both paths. (Also a Class-45 instance — same
  field, different source.)
- **A24 (LANDED `.E.0.10`, engine `f2ef5d6`):** `EventLoop_RebuildOneCore` mutated the FLAT
  `resolved_cfg.{volume_multiplier,entry_offset_pct,spacing_multiplier}` (the D6/D10/spike adaptations) while
  the per-node consumer reads `resolved_cfg.cores[slot]` (the slice) → the per-node adaptation is silently dead
  (`ControllerConfig_ResolveForCore` writes the flat fields, never `cores[slot]`). The default-ON D10
  losing-streak brake is inert for the slice-reading strategies. **Fix:** single-source the per-node slice +
  the CI guard (below).

## The structural close

1. **Single-source the per-node view.** Every per-node value has ONE storage — the `cores[slot]` slice (or the
   `ResolvePerFill*` resolver output). NEVER a flat global with a parallel per-node shadow, and never a flat
   default + per-instance override resolved ad-hoc (that is `cfg-scope-discipline.md` Anti-pattern 1).
2. **Per-node consumer signatures.** A per-node consumer fn takes the per-node slice (`const PerCoreCfg<F>*`),
   never the full `const ControllerConfig<F>*`; genuinely-global reads are caller-resolved as scalar args
   (`cfg-scope-discipline.md` § "Consumer function signatures").
3. **Reconstruct = forward.** A restore/replay path must re-derive a value by calling the SAME resolver the
   forward path calls — never read a different (global) source field (Class 45 close).
4. **The mechanical guard (the H22 CI-check).** Flag **a per-shard READ of a global cfg field that HAS a
   `core_N_*` override**, and **a per-shard WRITE to a flat cfg field that HAS a `cores[]` slice** — the
   `tools/check_per_core_registry_integrity.py` **Check-10** extension (A24's un-reintroducible close). This is
   the mechanical enforcement of H22 at the cfg surface; it composes with the Class-44 detector (the
   codebase-wide "write-with-no-live-read" sweep).

## Scale to N clusters (the next level up)

The same purity holds one level up: a **cluster's** state + logic is a pure function of its own nodes + its own
shared resources, with no coupling to other clusters. The `.E.1` aggregator (single-writer + seqlock-published
account snapshot) is the per-cluster shared-resource boundary done right (each node publishes; the aggregator
owns the cluster view). **One known gap (TECH_DEBT-190):** the cluster's AGGREGATE exposure (N nodes long the
same symbol = N× concentration) is currently governed by nothing — per-node purity makes each node correct, but
no per-cluster layer owns the aggregate. The cluster-risk layer that closes it must ITSELF be per-cluster-pure
(a cluster's risk governance = a pure function of its own nodes), so it scales to N clusters by the same test.

## Cross-references

- **CLAUDE.md H22** (the invariant row — this spec is its discipline body; closes the dangling reference).
- `per-node-position-ownership-model.md` (the one-position-per-node model + the cluster-aggregate gap — sister).
- `refactor-patterns/cfg-scope-discipline.md` (per-node-slice-is-canonical; the consumer-signature discipline;
  Anti-pattern 1 = the flat-default+override shape H22 forbids).
- `DOCS/RECURRING_BUG_PATTERNS.md` Class 25 / 26 / 27 / 44 / 45 (the violation shapes) +
  `cross-thread-multiword-read-consistency-discipline.md` (the torn-read sibling).
- **A1** (Class 45, CLOSED) + **A24** (Class 44, fix-in-flight) — the canonical instances; **D-211** (the A24
  decision + the cfg-surface sweep); `tools/check_per_core_registry_integrity.py` Check-10 (the guard).
- TECH_DEBT-190 (cluster-aggregate exposure — the cluster-level scale-invariance gap).
