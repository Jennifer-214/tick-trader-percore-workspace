# Class 55 — Dual-source storage with split readers (a value stored twice, read inconsistently)

> Codified 2026-06-29 at v5.15.5.F.4d.1.E.1.1 (the ③ config-compiler ship-close codification slate, D-271/D-280). Per-class file per file-size-split-discipline. **H-promotion deferred to Stage 5** per pattern-codification-lifecycle.

## Shape

A single logical value lives in **TWO storage locations** — a legacy parallel array `node_risk_pct[16]` AND the resolved `nodes[c].risk_pct`; a flat global AND a per-node mirror — populated by different code and read by **DIFFERENT consumers**. Two failure modes follow:

- **Dead mirror** — one storage is written but has ZERO live readers; the consumers all read the OTHER. The dead one drifts silently (anyone who later trusts it gets a stale value). Pre-B-merge, `ResolveForCore` never merged the legacy arrays into `nodes[c]`, so `nodes[c].risk_pct` was a DEAD MIRROR (= the global) while the live allocator / kill-switch read the ARRAYS.
- **Stale shadow / split-read** — a validation or sweep reads ONE storage but the live consumer reads the OTHER (or falls back to it). The check passes on the storage it can see while the consumer uses the value it can't. Item-4 F1: post-B-merge the sweep reads `nodes[c]` (which carries `0=inherit`), but for an inheriting node the consumer FALLS BACK to the global flat — the sweep over `nodes[c]` reads 0 and passes while the allocator uses the un-swept global `risk_pct=999`.

The unifying hazard: **there is no single authoritative read that both the consumers and the validators share**, so a guarantee proven on one storage does not hold for the value actually used.

## Detection heuristic

Flag any value with **2+ storage members** for the same logical datum:
- a legacy parallel array + a struct field (`node_<x>[16]` + `nodes[c].<x>`);
- a flat global + a per-node copy;
- a cfg field + a runtime-mutated `resolved` mirror.

Then enumerate the **READERS of each storage**:
- if different consumers read different storages → split-read (does a validator cover the one the live consumer uses?);
- if one storage has ZERO live readers → dead mirror (will it be trusted later?);
- if a sweep/validation reads storage A but the consumer's effective value can come from storage B (a fallback / inherit sentinel) → stale-shadow.

Discriminator: *is there ONE authoritative read that every consumer AND every validator goes through?* If not, it's this class.

## Structural fix

**Single-source the storage — one authoritative read.** Merge the dual sources so consumers and validators share it:
- the **B-merge**: raw-copy the legacy array into `nodes[c]` (0=inherit PRESERVED, last-wins over the copy-walker) so `nodes[c]` is the ONE authoritative per-node read; consumers keep their two-branch divided-vs-direct math (can't collapse — FP non-assoc + the `0→$1` default-node) but read the merged field.
- where a fallback/inherit sentinel means the resolved field can still be 0 (the array channel), add an explicit check of the **fallback source** (the global flat) so the validator covers the value the consumer actually uses (item-4's global-flat leg).
- make the merge **deletable-by-construction** ([[D-278]] / Class-40 family): the merge sidecar rides a registry (`FOREACH_PER_NODE_ARRAY_OVERRIDE`) that auto-dissolves when the legacy storage is deleted (E.1.2) — no stale dual-source left behind.

## Known instances

| Dual storage | Failure | Fix |
|---|---|---|
| `node_risk_pct[16]` / `node_max_drawdown_pct[16]` vs `nodes[c].{risk_pct,max_drawdown_pct}` | DEAD MIRROR (`nodes[c]` = global, consumers read the arrays) | the B-merge (item-4 step 1, `9c93d1d`) |
| post-B-merge: `nodes[c]==0` inherit vs the global flat the allocator/kill falls back to | STALE-SHADOW (the `nodes[c]` sweep misses the global) | item-4 F1 global-flat leg (`6981c85`) |

## False-positive surface (per M3)

NOT this class: a **deliberate read-optimized cache or published snapshot** (a hot-path copy of a slow-path value with a DEFINED sync point — a seqlock-published param, a TUISnapshot) — that is intentional dual storage with a single reconciliation contract, not a split-reader. The pattern requires that consumers read DIFFERENT sources WITHOUT a single authoritative reconciliation. Nor two fields that merely share a name but are different data (`per_node_risk_pct` GUI `float[]` vs the cfg `node_risk_pct[]` array — distinct).

## Closure mechanism

The `check_per_node_registry_integrity.py` UNINDEXED-GLOBAL / paired-access detectors (Class 25/26 slices) catch the per-core split-read shape; the merge + single-authoritative-read discipline + the deletable-cascade sidecar are the structural close. Sister: Class 26 (per-core scope), Class 27 (scalar cfg-mirror), Class 40 / D-278 (deletable retirement of the legacy source).
