---
type: readiness-report
subtype: layer-cohesion + code-readiness
target: subplans/2026-06-15-v5.15.5.F.4d.1.E.1.2-nodestate-soa-layout.md
engine_head: b10e778
date: 2026-07-03
verdict: RED (cohesion) · GREEN (code-readiness)
scope: COHESION pass on a heavily-amended plan — design NOT re-litigated (11-agent investigation settled it); this checks whether the 4 LAYERS cohere and whether every cited symbol exists at HEAD.
consult_before_coding: yes — operator triages; no auto-proceed
---

# E.1.2 — layer-cohesion + code-readiness readiness report

## Verdict

- **Cohesion: RED.** The plan gives a coder OPPOSITE instructions on its central deliverable. The primary coding body (frontmatter + ship-goal + acceptance criteria + "RE-GROUNDED" design-shape + Phases A.0→G + Scope) is uniformly **pre-reversal** (192B / SoA / store `owner_node_id` / bump PORTFOLIO). The `## ⏩ AMENDMENTS` block (items 1-8) + D-292/D-294 **reverse all of it** (128B / AoS / derive / retire PORTFOLIO) but were appended at the bottom WITHOUT striking the superseded layers. A coder executing top-to-bottom builds the wrong ship. The DESIGN is settled — this is a consolidation (documentation-cohesion) failure, not a rescope, but it is blocking: the body a coder follows is superseded end-to-end.
- **Code-readiness: GREEN.** Every cited symbol/file/line exists at HEAD `b10e778`. No fabrications. `Sharded_SlotNode` is correctly ABSENT (the plan adds it). The two adversarial-found bugs (`:856` ungated shift, `_pad_pos` H12 hole) are code-accurate.

---

## (a) Stale-layer contradictions — each with the exact consolidation edit

Every row: a coder following the LEFT builds the superseded design; the RIGHT is current.

| # | Surface | Primary body (SUPERSEDED) | Current (amend/decision) | Consolidation edit |
|---|---|---|---|---|
| **K1** | **Position size** | **192B** — ship-goal `:42`, RE-GROUNDED `:57-73` (esp `:61-64`), Phase B `:80`, accept-crit `:49` (`==192`) | **128B stays** — item 8, D-292, D-294 | Mark **Phase B `:80` SUPERSEDED → "see AMENDMENTS item 8"**; rewrite ship-goal `:42`, the RE-GROUNDED design-shape `:57-73`, accept-crit `:49` to 128B. This is the headline: the coder MUST NOT grow Position. |
| **K2** | `peak` (16B Money) | **reserve at E.1.2** — `:42`, `:62`, `:64` | **DEFER to D-206 (parked)** — item 8, D-292 | strike `peak` from the RE-GROUNDED shape + Phase B; reserving a 3rd cache line for a parked feature contradicts grow-leaf-by-leaf. |
| **K3** | `owner_node_id` | **STORE** (`uint16_t`, PERSIST) — `:42`, `:63` | **DERIVE via `Sharded_SlotNode`** — item 8, D-294 | strike the stored field; replace with the `Sharded_SlotNode(slot,partial_on)` add + 6-site route (see completeness gap C1). |
| **K4** | PORTFOLIO version | **bump 7→8** — Phase G `:92`, accept-crit `:48` | **RETIRE, don't bump** (BLK-2 `:192`) — D-294 (no version bump, Position unchanged) | strike "Bump PORTFOLIO 7→8" from Phase G + `:48`; Phase G = **retire `PORTFOLIO_SNAPSHOT_VERSION` + add the SHARDED-keyed size→version guard (BLK-3, closes TD-180)**. **SHARDED 10→11 SURVIVES** (partner_pending_pnl adds a per-node persisted field → wire changes) — keep that half of `:48`/`:92`, drop the PORTFOLIO half. Also reconcile the `controller_test.cpp` 4-version assert (`:54`) to "SHARDED bumps, PORTFOLIO retired". |
| **K5** | **SoA / H10 AVX** | **SoA relayout + "first real SoA AVX kernel"** — frontmatter `ship_kind:5`, `hot_path:18`, accept-crit `:50`, Scope item 1 `:113`, §4 H10 row `:136`, INBOUND seam `:142` | **STRIKE SoA/H10 → re-home `.E.6/.E.7`; E.1.2 is AoS** (BLK-4 `:192`) | strike EVERY SoA/H10 mention (frontmatter + `:50` + `:113` + `:136` + `:142`); redefine the determinism gate as a **populated multi-node Save→Load byte-compare** (BLK-4), not an AVX scalar-parity check. Pervasive — the plan's title itself still says "SoA/`Money` relayout". |
| **K6** | NodeContext serializer shape | **"NOT a flat `FOREACH_NODE_PERSIST_FIELD`"** — Phase C `:83` | **flat `FOREACH_NODE_PERSIST_FIELD` + compose-sub-registry delegates (HYBRID) + OMS count-lock** — Amendment 1, gate BLK-1 | reword Phase C `:83` to the hybrid. **This is a silent-bug trap**: a coder following the "delegates-only" `:83` wording reintroduces exactly the BLK-1 ~24-flat-field drop (D-110 silent-zero-on-restore) the gate caught. Add the OMS-precedent count-lock (`FOREACH_*_PERSIST_COUNT` static_assert). |
| **K7** | `node_dd_pct` | **reserve wire-locked** — Phase F `:90` | **DROP from persist (recompute-on-load)** — Amendment 4, Phase C `:84` | strike `node_dd_pct` from the Phase F `:90` reserve list (Amendment 4 says so, but the `:90` text was never struck → the internal Phase C `:84`-drop vs Phase F `:90`-reserve contradiction is still LIVE in the body). Same for `drawdown_max`/`drawdown_current` (drop). |

**Frontmatter is also stale** (a cold pickup reads it first): `ship_kind:5` ("SoA"), `hot_path:18` ("SoA relayout … H10 first real SoA AVX kernel"), `risk:17` ("bytes change → snapshot VERSION bump" — Position bytes DON'T change now; only SHARDED bumps via partner_pending). Update all three at consolidation.

**Root cause / recommended fix:** the "RE-GROUNDED (HEAD b10e778)" design-shape section (`:57-73`) is itself labeled authoritative ("SUPERSEDES the scaffold's Design-shape below" + "the 192B freeze target lives here") yet is silently reversed by the AMENDMENTS 100+ lines later. Cleanest consolidation = **fold items 1-8 UP into the body** (rewrite Phases B/C/F/G + ship-goal + accept-crit + the RE-GROUNDED shape), then collapse the AMENDMENTS block to a short audit-trail pointer. Minimum acceptable = a **"⚠ SUPERSEDED — see AMENDMENTS item N"** banner stamped at each K1-K7 site so a coder can't execute a stale instruction.

## (b) Code-readiness — all cited symbols verified at HEAD (GREEN)

| Symbol / site | Cited | Verified |
|---|---|---|
| `Sharded_LegSlot` | ControllerEventLoop.hpp:1099 | ✅ :1099 |
| `Sharded_NodeSlotMask` | ControllerEventLoop.hpp:1117 | ✅ :1117 |
| `Sharded_SlotNode` (inverse to ADD) | absent | ✅ correctly absent — to be added |
| `FOREACH_POSITION_FIELD` + `init` col | PositionFieldRegistry.hpp | ✅ MemHeaders/…:49-59, shape `X(name,type,init,persist_kind,doc)` — AM-3 registry-driven `Position_Reset` feasible |
| blob serializer | ShardedSnapshotPersist.hpp:169 | ✅ `fwrite(...positions, sizeof(Position<F>), 16, f)` @:169 |
| OMS count-lock precedent | OmsFieldRegistry.hpp:371-384 | ✅ `static_assert(FOREACH_OMS_FIELD_PERSIST_COUNT == 10 …)` @:380 |
| `Position_Reset` | Portfolio.hpp:221 | ✅ :221 — body zeroes 9 fields, **skips `_pad_pos`** → bug-2 claim accurate |
| ungated `slot>>1` (bug 1) | ControllerEventLoop.hpp:856 | ✅ `:856` `int node_id = slot >> 1;`; false "shifts harmlessly" comment `:853-855` present |
| `_pad_pos[7]` H12 hole | Portfolio.hpp:70 | ✅ `uint8_t _pad_pos[7];` no default-init; reaches wire |
| stale 192B layout block | Portfolio.hpp:99-114 | ✅ present (old 24B/192B layout) — item-8 comment-fix target |
| versions | 7 / 10u / 14 | ✅ PORTFOLIO=7 (:534), SHARDED=10u (:94), CONTROLLER=14 (:2025); stale `=6`/`=5` comments confirmed |
| F-096 `double` (bug) | Async.hpp:842 | ✅ `double full_qty = Money_ToDouble(...)` @:842; `money_from_double_payload` @:896 |
| `partner_pending_pnl` / `_bitmap` | :424 / :747 | ✅ :424 (Money) / :747 (uint16_t) |
| dead serializers (Phase D del) | Portfolio_Save:547/_Load:586; PortfolioController_SaveSnapshot:2029/_LoadSnapshot:2104 | ✅ all present |
| `"TICK"` refuse-magic (preserve) | ShardedSnapshot_Load | ✅ present (0x4B434954) |

**One loose count (non-blocking):** Amendment 8 says "route the **6** open-coded `slot>>partial_on` sites." Grep finds ~3 code sites (SlowPath.hpp:134 *gated*, CEL:856 *ungated bug*, ShardedSnapshotPersist.hpp:623 *gated*) + comments. Verify the exact set at code-time — not a cohesion blocker.

## (c) Completeness — item-8/amendment deliverables with NO coding step in Phases A.0→G

The phase structure (A.0→G) predates the reversal; Phase B was the Position-touch phase and is now void (192B). These CURRENT deliverables have **no phase home**:

- **C1** `Sharded_SlotNode(slot,partial_on)` add + route ~6 sites + fix `:856` (item 8 / D-294 bug 1). No phase owns it.
- **C2** `_pad_pos[7] = {0}` DMI + **registry-driven `Position_Reset`** off the `init` column (AM-3) + `memset` (item 8 / D-294 bug 2). No phase owns it (Phase B was the Position phase).
- **C3** Stale-comment fixes: Portfolio.hpp:99-114 (old-192B block) + `:853-855` ("shifts harmlessly"). No phase owns it.
- **C4** OMS-precedent count-lock in the NodeContext serializer (Amendment 1) — Phase C `:83` doesn't mention it.
- **C5** `partner_pending_pnl` persist + bitmap slot-parity re-derive + mid-pair reopen fixture (Amendment 3 / D-291) — Phase C `:83` only "DECIDE inclusion"; no persist/re-derive step.
- **C6** BLK-3 SHARDED-keyed size→version guard (closes TD-180) — no phase home.
- **C7** Codification owed at ship-close (Amendment 6 / task #13: drift bug-class + CI guard + count-lock) — tracked, but no phase step.

**Fix:** rewrite Phase B (Position phase) to carry C1-C3 (128B stays; DMI + registry Reset; Sharded_SlotNode + `:856`; comment sweep) and fold C4-C6 into Phases C/G. Item-8's work is real and code-accurate — it just isn't wired into the executable phase list.

## Blocking gaps (must fix before coding)

1. **K1-K7 stale-layer strikes** — the body instructs the superseded design. Blocking (esp. K1 192B, K5 SoA, K6 delegates-only-drop).
2. **C1-C3 have no phase home** — item-8 deliverables would be silently dropped by a coder following A.0→G.
3. **K6 is a latent D-110 bug** if executed as written (delegates-only serializer drops flat fields).

## Non-blocking / hygiene

- Frontmatter `ship_kind`/`hot_path`/`risk` stale (K5/K4).
- Amendment 4's node_dd_pct fix names the Phase F strike but the `:90` text is still live (K7).
- "6 sites" count to verify at code-time.

**Net:** design settled + code-readiness clean; the plan just needs a consolidation pass to make the executable body match the amendments/decisions before a coder touches it.
