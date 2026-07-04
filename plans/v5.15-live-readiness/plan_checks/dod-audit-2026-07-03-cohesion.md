---
type: audit-report
subtype: dod-audit-cohesion-pattern-fit
target: subplans/2026-06-15-v5.15.5.F.4d.1.E.1.2-nodestate-soa-layout.md (## AMENDMENTS items 1-8)
engine_head: b10e778
date: 2026-07-03
scope: COHESION pass — pattern-fit of the amended deliverable set (design pre-validated; not re-litigated)
verdict: GREEN (pattern-fit) · 1 YELLOW cohesion/currency flag · no misapplication
mechanism: /dod-audit plan-mode, DESIGN_SPECS catalog walked + cited code read at HEAD b10e778
---

# /dod-audit report — E.1.2 amended set (cohesion / pattern-fit) — 2026-07-03

## Catalog ingested
139 DESIGN_SPECS docs walked. Patterns load-bearing for this audit:
`canonical-sister-extension-discipline` · `single-source-of-truth-discipline` ·
`multi-action-registry-walker-family` · `struct-padding-determinism-pattern` (H12) ·
`heterogeneous-registry-pattern` (COLUMN/SPLIT/HYBRID) · `registry-coverage-ci-check-pattern`
(count-lock = compile-time variant) · `running-aggregate-vs-cycle-recompute-discipline` ·
`partner-core-bitmap-pattern` · `persisted-struct-with-ephemeral-field-coexistence-pattern`.

## Summary (per-deliverable pattern verdict)

| # | Amended deliverable | Pattern claimed | Verdict |
|---|---|---|---|
| 1 | `Sharded_SlotNode(slot, partial_on)` inverse-accessor | canonical-sister + single-source-the-computation | **RIGHT** |
| 2 | Registry-driven `Position_Reset` off `init` col + `_pad_pos={0}` DMI + memset | multi-action-registry-walker (RESET) + H12 struct-padding | **RIGHT** (belt is load-bearing — see F2) |
| 3 | NodeContext serializer HYBRID (flat `FOREACH_NODE_PERSIST_FIELD` + delegates) + count-lock | heterogeneous-registry HYBRID + registry-coverage-ci-check | **RIGHT** (A1 struct-gen refutal correctly honored) |
| 4 | AM-4 persist `partner_pending_pnl` + RE-DERIVE bitmap via slot parity | running-aggregate-vs-cycle-recompute + partner-core-bitmap | **RIGHT** |
| 5 | codification owed (item 6) = bug-class + CI guard + count-lock | registry-coverage-ci-check Shape A | **RIGHT** |

## Findings

### F1 — Deliverable 1 (`Sharded_SlotNode`) — RIGHT (single-source, canonical inverse-sister)
Verified at HEAD: the `Sharded_*` slot-geometry family lives together at `ControllerEventLoop.hpp:1099`
(`Sharded_LegSlot` node→slot) / `:1117` (`Sharded_NodeSlotMask` node→mask). `Sharded_SlotNode(slot,
partial_on)` is the **genuine missing inverse** (slot→node) — same `static inline int` style, same file,
same family. This is a textbook canonical-sister extension (Option A/C in `canonical-sister-extension-
discipline.md`), NOT parallel infra. The single-source case is airtight: the derivation is **open-coded in
≥3 live sites** — `SlowPath.hpp:134` (gated, correct), `ShardedSnapshotPersist.hpp:623` (gated, correct),
`ControllerEventLoop.hpp:856` (**UNGATED `slot>>1` — the drift bug**; ignores `partial_on`, misattributes
per-node stats in single-position mode). A computation living in 3 places with **one already drifted** is the
exact `single-source-of-truth-discipline.md` trigger; routing all sites through the accessor merges the SSoT
**and** closes the Class-18 drift at `:856`. Right placement/style. No misapplication.

### F2 — Deliverable 2 (`Position_Reset` + pad) — RIGHT; the DMI+memset is the load-bearing pad-close
Verified: `Position_Reset` (`Portfolio.hpp:221-231`) hand-lists the 9 registry fields' inits but **skips
`_pad_pos`**; `_pad_pos[7]` (`:70`) is declared bare **without `={0}`** → H12 hole that reaches the wire
(`ShardedSnapshotPersist.hpp:169` fwrites all 128B in a byte-equiv context). Driving Reset off the
`FOREACH_POSITION_FIELD` `init` column (`PositionFieldRegistry.hpp:51-59`) is the correct
multi-action-registry-walker RESET action (matches OMS INIT/RESET/PERSIST views) — it auto-tracks future
rows, closing the A28/TD-182 subset-zeroing class. **Caveat (not a defect — the plan states all three
parts):** `_pad_pos` is intentionally OUTSIDE the registry, so the walker alone does NOT zero it — the
`={0}` DMI (construction paths) **and** the explicit `memset` (the in-place `Reset(Position*)` path, which
does not re-run DMIs) are the load-bearing H12 close. Keep all three; dropping the memset silently re-opens
the hole. Correct per `struct-padding-determinism-pattern.md`.

### F3 — Deliverable 3 (NodeContext serializer) — RIGHT HYBRID; OMS is the correct sibling
Verified the serializer shape at `ShardedSnapshotPersist.hpp:172-261`: ~24 flat fields (9 `Money`)
hand-fwritten (`:176-227`); `regime_state` (`:230-236`) + `pnl_feeder` (`:239-241`) hand-fwritten;
**`confidence` already a live registry-driven delegate** — `ConfidenceScorer_FieldwiseWrite` off
`FOREACH_CONFIDENCE_PERSIST_FIELD` (`:248-260`). So the plan's HYBRID = flat registry for the scalars +
compose-sub-registry delegates (confidence live; regime/pnl to convert) is the exact
`heterogeneous-registry-pattern.md` HYBRID call: NodeContext has nested sub-structs + a `void* strategy_state`
+ RAII, which X-macro `type name=init;` struct-generation **cannot express** — so A1's refutal of
born-struct-generation is correctly honored, and **OMS (`OrderManagerState`: hand-declared struct +
serializer-registry + count-lock) is the right sibling, not Position** (the flat struct-GENERATING POD =
false analogy). The count-lock is verified real at `OmsFieldRegistry.hpp:371-384`
(`FOREACH_OMS_FIELD_PERSIST_COUNT == 10` static_assert) — the compile-time variant of
`registry-coverage-ci-check-pattern.md`. Per-registry count-locks (the `*` in `FOREACH_*_PERSIST_COUNT`)
correctly self-guard each sub-registry. No misapplication.

### F4 — Deliverable 4 (AM-4 partner_pending) — RIGHT (persist non-derivable, recompute derivable)
Verified: `partner_pending_pnl` = `Money` on NodeContext (`ControllerEventLoop.hpp:424`) — an accumulated,
**non-derivable** total → persist (correct). `partner_pending_bitmap` = `uint16_t` on EventLoopState (`:747`;
per `partner-core-bitmap-pattern.md`, spec cites stale `:533`) — a per-node bit **re-derivable** from the
already-persisted `active_bitmap` via slot parity (`bit N = active(2N) XOR active(2N+1)`). Choosing
RE-DERIVE over persist-both is the correct `running-aggregate-vs-cycle-recompute-discipline.md` call (don't
persist an H21-immutable wire field for derivable state — same discipline as the `node_dd_pct` drop). The
consumer (`:1575-1577`: `BITMAP_IS_SET(...)` then `Money_Add(ctx.partner_pending_pnl, ...)`) confirms the
pnl is the authoritative accumulator and the bitmap is the gating bit — the persist/rederive split lands on
the right side of each. The XOR formula's semantic-exactness (the "can a leg open without its partner" edge)
is **appropriately gated to code-time verification with a persist-both fallback** — correctly hedged, not
hand-waved. No misapplication.

### F5 — codification (item 6) — RIGHT pattern
The owed bug-class + CI guard ("byte-serialized struct field absent from its persist registry") + count-lock,
authored WITH the guard code at ship-close, is `registry-coverage-ci-check-pattern.md` Shape A (positive
coverage) — the correct structural-enforcement (M7) shape. Non-vacuous because the guard ships with the class.

## The one cohesion/currency flag (YELLOW — doc-hygiene, not pattern)

**The reformalized BODY still carries superseded 192B / PORTFOLIO-bump language that only the AMENDMENTS
block overrides.** A coder reading top-to-bottom hits stale Phase B ("open `Position` ONCE → 192B", `:79`),
Phase G ("PORTFOLIO 7→8", `:92`), and the acceptance criteria (`:48-49`: "Position pin at 192B",
"PORTFOLIO_SNAPSHOT_VERSION 7→8") **before** reaching item 8 (Position stays 128B; BLK-2 retires — not bumps
— PORTFOLIO). Verified against code: Position **is** 128B today (`Portfolio.hpp:117`), so the body is stale,
the amendments are current. The plan flags the supersession in prose, but the body text was not struck.
Recommend a one-line STALE/SUPERSEDED marker on Phase B + Phase G + the acceptance-criteria bullets (or
strike the 192B/bump numerals) so the coding pass can't follow the stale path. Not ship-blocking; not a
pattern issue.

## Proactive novel alternative (LOW — for deliverable 2, operator's call)
`Position_Reset` could be a one-liner `*p = Position<F>{}` — value-init reuses the **same** `= init` DMIs the
registry already emits (`PositionFieldRegistry.hpp:51-59`) AND zeroes `_pad_pos` (given the `={0}` DMI) for
free, no walker + no separate memset. It is arguably MORE single-source (reuses the struct's own declared
inits rather than re-deriving them in a walker) and simpler. The chosen registry-walker RESET is
pattern-consistent with OMS's INIT/RESET/PERSIST view family — a fair defense. Both correct; flagging the
simpler option since if the walker route is kept, the memset is load-bearing (F2) and must not be dropped.

## Recommendations
- **Address before code (YELLOW):** mark/strike the stale 192B + PORTFOLIO-bump language in Phase B / Phase G
  / acceptance-criteria so the reformalized body cannot mislead the coding pass.
- **Consider (LOW):** evaluate `*p = Position<F>{}` vs the registry-walker RESET for deliverable 2.
- **Keep (verified correct):** all 5 amended deliverables apply the right DESIGN_SPECS pattern; none misapplied.

## Verdict: GREEN on pattern-fit (1 YELLOW doc-cohesion flag)
No pattern misapplication across the amended set. The 3 orchestrator over-reaches the sweep refuted
(defer-to-E.1.3, born-struct-gen, stored `owner_node_id`) stay refuted and the corrected directions apply the
canonical patterns cleanly. The only actionable item is doc-currency (stale 192B/bump body language),
not architecture. Consult before coding; no auto-proceed.
