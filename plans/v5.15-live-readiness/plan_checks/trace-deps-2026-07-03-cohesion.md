---
type: audit-report
subtype: trace-deps-cohesion
skill: /trace-deps
target: subplans/2026-06-15-v5.15.5.F.4d.1.E.1.2-nodestate-soa-layout.md
scope: the "## ⏩ AMENDMENTS" block + item 8 (deliverables; supersede the reformalized body on conflict)
engine_head: b10e778
date: 2026-07-03
verdict: YELLOW  # no fabrication that breaks a chain; all chains hold; ONE completeness gap on the "closes the class" claim + doc-hygiene staleness
decision_log: D-291..D-294
informed_by:
  - plan_checks/2026-07-03-E.1.2-serializer-scope-forward-sweep.md
  - plan_checks/2026-07-03-E.1.2-owner-node-id-investigation.md
---

# /trace-deps cohesion report — E.1.2 NodeState relayout — 2026-07-03

COHESION pass on a heavily-amended plan. Design validated upstream (D-294 3-I+3-A);
this trace does NOT re-litigate the DERIVE-not-store decision. It verifies (1) every
cited symbol EXISTS at HEAD b10e778, (2) the amended deliverables CHAIN without a broken
dependency, (3) the E.1.2→E.1.3 seam is consistent.

## Summary
- Symbols verified: 24 cited file:line anchors + 4 registries + 4 serializers.
- PASS (exists, cite exact): 22 / 24 anchors.
- GAP-benign (cited but absent; a "drop" no-op, not a depended-on callee): `drawdown_max`, `drawdown_current`.
- Broken dependency chains: **NONE**.
- Completeness finding (YELLOW): the "6 sites" enumeration undercounts → "closes the class" at risk.

## 1. Symbol-existence (FOCUS 1) — all PASS except two benign absences

| Cited symbol / anchor | Verdict | HEAD location |
|---|---|---|
| `Sharded_LegSlot(node_id,leg,partial_exit_enabled)` | PASS (exact) | `ControllerEventLoop.hpp:1099` |
| `Sharded_NodeSlotMask(node_id,partial_exit_enabled)` | PASS (exact) | `ControllerEventLoop.hpp:1117` |
| `Sharded_SlotNode(slot,partial_on)` | CORRECTLY-ABSENT (the NEW inverse item 8 adds) | — |
| slot→node site: `SlowPath.hpp:134` | PASS `partial_on ? (slot>>1) : slot` | `EngineSharded/SlowPath.hpp:134` |
| slot→node site: `ShardedSnapshotPersist.hpp:623` | PASS `partial_exit_enabled ? (slot>>1) : slot` | :623 |
| slot→node site: `ControllerEventLoop.hpp:856` | PASS — the BUGGY ungated `int node_id = slot >> 1;` | :856 |
| slot→node site: `ControllerEventLoop.hpp:3439/3442` | PASS — :3442 correct `slot >> (uint32_t)partial_on`; :3439 = comment | :3442 |
| slot→node site: `ShardedSnapshot.hpp:219` | PASS inline `BITMAP_IS_SET(...) ? (idx>>1) : idx` | :219 |
| `FOREACH_POSITION_FIELD` + `init` column | PASS — tuple `X(name,type,init,persist_kind,doc)`; init col present | `MemHeaders/PositionFieldRegistry.hpp:49-59` |
| `Position_Reset` | PASS (exact) — hand-coded 9-field reset, does NOT zero `_pad_pos` | `Portfolio.hpp:221` |
| Position blob serializer | PASS `fwrite(...positions, sizeof(Position<F>), 16, f)` | `ShardedSnapshotPersist.hpp:169` |
| NodeContext save loop | PASS (range correct; scaffold's :176-233 WAS too narrow) | `ShardedSnapshotPersist.hpp:172-261` |
| NodeContext load loop | PASS `for (...file_num_nodes...)` | `ShardedSnapshotPersist.hpp:436-499` |
| `Portfolio_Save` / `Portfolio_Load` (D-289 delete) | PASS | `Portfolio.hpp:547 / :586` |
| `PortfolioController_SaveSnapshot/_LoadSnapshot` (D-289 delete) | PASS | `PortfolioController.hpp:2029 / :2104` |
| `CONTROLLER_SNAPSHOT_VERSION 14` (delete-with-path) | PASS (define exists) | `PortfolioController.hpp:2025` |
| F-096 leg-split still `double` | PASS `double full_qty = Money_ToDouble(...)` + `money_from_double_payload@896` | `Async.hpp:842` |
| `partner_pending_pnl` (Money) | PASS | `ControllerEventLoop.hpp:424` |
| `partner_pending_bitmap` (u16) | PASS | `ControllerEventLoop.hpp:747` |
| OMS count-lock precedent `FOREACH_OMS_FIELD_PERSIST_COUNT` static_assert | PASS | `OmsFieldRegistry.hpp:371-384` |
| item-6 instance `node_gross_wins/losses`→$0.00 | PASS (real Class-4 historical instance) | `ShardedSnapshotPersist.hpp:197-203` |
| item-4 drop target `node_dd_pct` (persisted + recompute-on-load) | PASS | persist `:213`; recompute `ControllerEventLoop.hpp:2909` |
| item-4 drop target `drawdown_max` | **ABSENT (0 hits)** | — |
| item-4 drop target `drawdown_current` | **ABSENT (0 hits)** | — |

`Portfolio.hpp:99-114` stale 192B/24B layout comment — CONFIRMED present (self-corrected at :115-116 but stale). Size-pins `sizeof==128`@:117, offsets @:122-130, PERSIST-relationship @:141/:143 — all present (item 8 KEEPS them; Position stays 128B).

### Fabrication verdict
No fabrication that breaks a chain. `drawdown_max`/`drawdown_current` do NOT exist at HEAD — item 4 (+ body Phase C) instruct "drop `drawdown_max` (0 consumers) + `drawdown_current` (derivable)"; dropping absent fields is a no-op. Benign staleness (already gone, or never existed / confused with `node_dd_pct`). The coder must not hunt for them. All DEPENDED-ON callees exist.

## 2. Dependency chains (FOCUS 2) — all hold

- **Accessor + route (item 8):** `Sharded_SlotNode` (NEW) mirrors the existing `Sharded_LegSlot`/`NodeSlotMask` family (same file, same `partial_on` source `BITMAP_IS_SET(...MASK_...PARTIAL_EXIT_ENABLED)`); all routed sites exist. Routing `:856` through it FIXES the ungated-`>>1` bug (the correct `slot >> partial_on` shift). Chain holds. **Bug is real:** partials-OFF (default) has `slot==node`, so `slot>>1` halves the node index → per-node stat misattribution on warm-restart event-log replay; the `:854-855` "shifts harmlessly otherwise" comment is FALSE. LOW today (D-294: all consumers display/persist, none gate capital), latent-MED if future per-node risk gates read it.
- **Serializer-registry (Phase C, item 1) + count-lock:** confidence delegate precedent `ConfidenceScorer_FieldwiseWrite` exists (`ShardedSnapshotPersist.hpp:260`); OMS count-lock pattern exists (`OmsFieldRegistry.hpp:371-384`). A flat `FOREACH_NODE_PERSIST_FIELD` + DELEGATE rows for regime_state/pnl_feeder/confidence + a `FOREACH_NODE_PERSIST_COUNT` static_assert is buildable off these. Chain holds. (Terminology tension — see §4.)
- **D-289 deletion vs live confidence sub-walker:** VERIFIED SAFE. `ConfidenceScorer_FieldwiseWrite/Read/Commit` are defined in `ConfidenceScore.hpp` and called from BOTH the live ShardedSnapshot path (`:260/:487/:585`) AND the dead PortfolioController path (`:2094/:2228`). Deleting `PortfolioController_*Snapshot` removes only the PortfolioController call sites; the live sub-walker keeps calling the helpers. No orphan. Only `ConfidenceScorer_ShadowLoadLegacyV1` (v11 migration, TECH_DEBT-002) becomes dead-with-PortfolioController — NOT deleted here. The `"TICK"` refuse-magic preservation is orthogonal (not touched by these deletes).
- **partner_pending (item 3):** `partner_pending_pnl` persist row → SHARDED 10→11 bump (on). `partner_pending_bitmap` RE-DERIVE on load via slot parity — needs restored active state, available (active_bitmap restored before per-node blocks). Leg-atomicity design assumption has code support (`ExecutionCore.hpp:479` pair_active "open both legs"; plan flags for code-time verify). Chain plausible.
- **Position_Reset registry-drive (AM-3):** `Position_Reset:221-231` hand-lists exactly the registry `init` column (7×`Money_Zero()`, `0`, `-1`) and SKIPS `_pad_pos` → the H12 hole item 8 targets is real; driving off the `init` column + `= {0}` DMI + memset closes the subset-zeroing class. Chain holds.

## 3. E.1.2→E.1.3 seam (FOCUS 3) — CONSISTENT in intent; one stale number

- Softened seam (item 2): wire + Position frozen at E.1.2; in-memory NodeState GROWS leaf-by-leaf E.1.3+, each add SHARDED-version-managed (bisect anchor). Sound — "never re-touch" was always a fiction (E.1.3 absorbs rings/OrderTable).
- `owner_node_id` DERIVED via `Sharded_SlotNode` (D-294), not a stored field; sub-pool DEFERRED (the `_pad_pos` bits reserved UNPOPULATED). `:856` fix is E.1.2; venue-net reconcile is E.1.3. Matches the parent's seam framing exactly.
- **Stale number:** item 2 still says "Position **192B** freeze at E.1.2" — item 8 (D-292/293/294, later) SUPERSEDES to **128B**. The seam SHAPE is sound; the seam NUMBER in item 2 is pre-item-8. Doc-hygiene only.

## 4. Findings (all YELLOW / doc-hygiene; none blocking)

- **Y1 — "6 sites" undercounts → "closes the class" at risk.** A tree grep for `(slot|idx) >> (1|partial_on)` finds a 6th ENGINE-side slot→node derive NOT in the enumeration: `ShardedSnapshot.hpp:272` (`int node_id = partial_on ? (idx >> 1) : idx;`) — identical shape, SAME FILE as the already-included `:219`. Plus 6 GUI-side sites: `ChartPanel.hpp:280/721/817/909`, `DashboardPanels.hpp:1238/1381`. The D-294 guard-gap section proposes a guard only for the H12 pad-zero class, NOT for the slot-derive class. So "closes the class" (item 8) rests entirely on routing every instance. Recommend: (a) ADD `ShardedSnapshot.hpp:272` to the routing set (same file/shape as `:219`); (b) decide GUI-site scope explicitly (display-layer decoupling may justify exclusion — but then say so); (c) add a CI guard flagging any NEW open-coded `(slot|idx)>>` node-derive, per `feedback_close_the_class_vs_migrate_every_site` (primitive + enforcing guard = KNOWN-PENDING-shrinking). Without (c), routing N instances is a patch, not a class-close.
- **Y2 — `drawdown_max`/`drawdown_current` absent** (§1). Strip from item 4 / Phase C or annotate "already absent — no-op"; the "0 consumers" note reads as if the field exists.
- **Y3 — supersession cognitive load.** The acceptance-criteria block (:46-56) + body Phase B/C carry pre-item-8 numbers (Position 192B, PORTFOLIO 7→8 bump, SoA/H10) that item 8/BLK-2/BLK-4 reverse (128B, retire-don't-bump PORTFOLIO, AoS strike-SoA). By-design layering (operator-flagged: "AMENDMENTS + item 8 supersede body on conflict"), but a coder following the body verbatim builds the wrong thing. Consider a one-line "SUPERSEDED — see item 8" stamp on the acceptance-criteria 192B/bump/SoA lines.
- **Y4 — "flat FOREACH_NODE_PERSIST_FIELD" polarity.** Body Phase C says "NOT a flat" registry; item 1 says "flat + compose-sub-registry delegates". Reconcilable (flat scalar rows + DELEGATE rows; confidence delegate is the sister precedent), but the coder must build a mixed DIRECT/DELEGATE registry — worth one clarifying sentence.
- **Y5 — `:853-855` file ambiguity (item 8).** The bare `:853-855` "shifts harmlessly" cite follows `Portfolio.hpp:99-114`; Portfolio.hpp is 642 lines, so `:853-855` is `ControllerEventLoop.hpp:853-855` (confirmed content). Clarify the filename to avoid misread.

## Verdict: YELLOW
No fabrication that breaks a chain; every depended-on callee exists at its cited line; all deliverable chains hold; the confidence sub-walker survives D-289; the seam is consistent in shape. YELLOW rests on Y1 (site-enumeration completeness vs the "closes the class" acceptance claim + no class-guard) plus doc-hygiene Y2–Y5. Recommend a plan touch-up (Y1 site + guard, Y2 strike, Y3 supersession stamps) before coding; nothing is a ship-blocker. No auto-proceed — return to Caramel for triage.
