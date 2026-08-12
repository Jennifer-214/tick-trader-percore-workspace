---
type: agent-report
status: FROZEN — verbatim agent output, saved at receipt
directive: E.1.2 engine-plan currency re-ground before its pickup session
agent_class: c-class
delivered: 2026-08-11 (the same overnight session)
consumed_by: the E.1.2 pickup session (amendment-9 banner + the 11-item punch-list below are its FIRST act, before coding)
---

# CURRENCY RE-GROUND — E.1.2 NodeState-relayout plan vs engine HEAD `a71b893` — VERBATIM

**HEADLINE:** the plan is not merely line-drifted — it is **one full supersession layer behind**. After the 2026-07-03 AMENDMENTS block was written, E.1.2 coding **started and partially shipped** (2026-07-04, engine `2c11922`+`84d73e0`+`8648e27`: D-294/295/296/297 + D-302/304/305 — Position close-out, the `FOREACH_NODE_CTX_FIELD` unify, the frozen v10 byte-golden, the regime/feeder persist delegates), then the **E.1.2.A/E.1.2.B info-infrastructure campaign** (D-306..D-418, 2026-07-05 → 2026-08-10) was inserted under the E.1.2 tag namespace. The plan body records none of D-297..D-305. The Phase-C remainder SSoT at pickup is the D-305 sub-step order + the MASTER s14/s15 banners, not the plan's Phase C text.

## § 1. Cite currency
Tool summary: 40 line-anchors checked; 0 FABRICATIONS; net **2 RESOLVED · ~30 DRIFTED (corrected-anchor table in the session record) · 1 MISSING-AS-CITED (Fingerprint_Compute → Backtest/Fingerprint.hpp:232) · 3 RESHAPED** (ControllerEventLoop:856 Class-18 bug → FIXED by D-296, flip cite to done-record · Reconcile.hpp:245 region → the tagged branchless Reconcile_ApplyMissedFills unit, D-209/E.1.3 OUTBOUND premise doubly stale · the old :1120 legs-open site moved — AM-4 must re-locate its evidence).
Key corrected anchors: Position struct Portfolio.hpp:58 · sizeof==128 pin :152 · PERSIST pins :188/:191 · PORTFOLIO_SNAPSHOT_VERSION 7 :800 · Portfolio_Save/_Load (D-289 delete targets, STILL PRESENT) :836/:890 · SHARDED_SNAPSHOT_VERSION 10u ShardedSnapshotPersist.hpp:109 · sole live blob dump :185 · save loop :188+ / load :432-437/:458/:513/commit :564-586 · TICK refuse-magic :352-358 (PRESERVE stands) · CONTROLLER_SNAPSHOT_VERSION 14 PortfolioController.hpp:2181 · dead serializers :2185/:2260 (still present) · F-096 double legs Async.hpp:859/:872/:877-881/:926 (STILL double — genuinely open) · ConfidenceScore delegate region :1400-1490 · 4-version assert controller_test.cpp:27013-27014 **+ two the plan doesn't know: a second SHARDED pin :11588 and the version-NAMED golden tests/sharded_snapshot_v10_golden.hpp (regen at the 10→11 bump)** · OMS count-lock precedent OmsFieldRegistry.hpp:423-433 · Sharded_SlotNode NOW EXISTS :995/:1375 · ControllerConfig void*-hasher :1445-1447 · INBOUND SlowPath read+clear :125-126, OMS_PushExitForSlot :156.

## § 2. Decided-vs-open contradictions
1. **Amendment 8 ~fully DELIVERED but reads as future work** (D-295/D-296, engine 2c11922): Sharded_SlotNode accessor + 6 engine sites routed (4 GUI grandfathered) + the :856 bug fixed + CI guard LIVE (check_slot_node_derive.py, pre-commit **Check O**) + `_pad_pos[7]` H12 DMI (Portfolio.hpp:76) + registry-driven Position_Reset (:363-365); the "shifts harmlessly" comments GONE.
2. **Phase C superseded TWICE and PARTIALLY EXECUTED** — remaining = **D-305's tail**: ordered `FOREACH_NODE_PERSIST_FIELD` (grep-ZERO today) → count-locks + paired-bump + Python layout-audit tool → REC-A fold + D-304 doc-fixes; then Steps 3-5 (layout-hash · v11 delta + SHARDED 10→11 + retire/delete cascade · D-289 · F-096 · AM-4) + the close-gate. SSoTs: the two 2026-07-04 plan_checks + MASTER s14/s15.
3. **TD-227 DECIDED** (D-291/AM-4: persist `partner_pending_pnl` at E.1.2, re-derive bitmap by parity; fields live :488/:901) — Phase-C prose still reads open; ledger entry correctly awaits the ship.
4. **The D-232-conditional INBOUND bullet is OBSOLETE** — D-233: H8 shipped as the static ASM conformance analyzer at E.1.0 (tool + budgets + Check N live); only the no-regression criterion remains here.
5. **Phase F ③ fingerprint-safety DELIVERED by E.1.1/D-254**: the static_assert(53056) EXISTS (ControllerConfig.hpp:1448) + cfg_compile_ok() boot gate (:1459-1461) + cfg_load_fault_flags (:682). Stale prose.
6. Amendment 5 NOT executed (E.1.3 frontmatter still carries TD-196/TD-197 in td_closed:15 + body :43-44).
7. Frontmatter/status stale (gate RAN; coding started; plan_version needs bump).
8. Rollback tag `pre-v5.15.5.F.4d.1.E.1.2` @ b10e778 PREDATES the shipped Step-1/2 work — fresh `pre-E.1.2-resume` tag at pickup HEAD; do not move the old tag.
9. Reverse-check holds: drawdown_* 0-hit · NodeState/MAX_NODES_PER_CLUSTER/NUM_EXCHANGES/MAX_CLUSTERS 0-hit (Phase F pending) · TD-189 flag open :3144 · TD-167/TD-196 open :2984/:3196.

## § 3. INBOUND verification — ALL FOUR LIVE at HEAD, tag-pinned
TUISharedState ×3 `[STRADDLE]_[swap_strategy_requested@58168 · kill_reset_per_node@58184 · manual_close_requested@58248]` EngineTUI.hpp:1537 (struct :1444; fields :1493/:1498/:1504; [THREAD] armed :1441); seq@58112 by field-order arithmetic (settle with `--isolate TUISharedState` at the dive). Drainer read+clear SlowPath.hpp:125-126 → OMS_PushExitForSlot :156. ReadInto copies the SNAPSHOT plane; request flags are direct-written — both planes in the relayout. **NEW-to-the-fold: `swap_model_path_requested[16]` (~:1517-1522, __ATOMIC_RELEASE) — a fourth GUI-written request array; joins the writer-grouping.** NodeContext regime_state@56: struct :315, field :372, [DERIVED] :677-684 (SIZE 7168B · 112 lines · STRADDLE regime_state@56).

## § 4. Seam/scope currency
D-225 N=7 intact; E.1.0 ✓ E.1.1 ✓ (tag @0ee227a) · **E.1.2 IN-FLIGHT partially executed** · E.1.3★/E.1.4/E.1.5★/E.1.6; live-enable = E.1.3 ∧ E.1.5. The E.1.2.A/B namespace is NOT this plan (inserted campaign). The active handoff's NEXT ④ = this plan, resuming at the D-305 tail. Already-delivered-by-E.1.1: the ③ fold. EngineSharded/ now under CoreFrameworks/. Standing supersessions stand: BLK-4 (no SoA/H10) · D-292 (128B) · D-294 (derive) · BLK-2 (PORTFOLIO RETIRES — **the acceptance-criteria "7→8" bullet contradicts BLK-2 in the same doc; BLK-2 wins**) · SHARDED 10→11.

## § 5. Baseline-retirement list (cache_layout_baseline.txt, SHRINK-ONLY)
This ship retires EXACTLY the 4 engine keys: `false-sharing|NodeContext|regime_state` · `false-sharing|TUISharedState|swap_strategy_requested` · `|kill_reset_per_node` · `|manual_close_requested`. The 9 TrainingPanelState keys are suite-plane (foxml_suite refactor's) — do NOT retire at E.1.2 close. Re-bless minus the closed keys at close; the gate then guards the new layout permanently.

## § 6. Pickup punch-list (ordered)
1. Amendment 9 / third supersession banner: record the 2026-07-04 execution arc + declare remaining scope (the D-305 tail + Steps 3-5 + close-gate); cross-ref D-297..D-305 + the two plan_checks.
2. Mark amendment 8 LANDED (D-295/296 + Check O).
3. Mark Phase F ③ DELIVERED (E.1.1/D-254; anchors above).
4. Replace the D-232 bullet with the D-233 resolution.
5. Fix the PORTFOLIO "7→8" vs BLK-2 contradiction (BLK-2 wins).
6. Re-anchor load-bearing cites per §1; add the version-NAMED golden + the :11588 pin to § Tests.
7. Refresh frontmatter (in-flight/partially-executed; note the A/B insertion; bump version).
8. Fresh `pre-E.1.2-resume` rollback tag at pickup HEAD (old tag stays).
9. Execute amendment 5 (strip TD-196/197 from E.1.3 td_closed) — mechanical. **[EXECUTED at receipt — see post-script]**
10. Carry the genuinely-open dive questions: TD-189 · MAX_NODES_PER_CLUSTER naming · AM-4 evidence re-locate · the Reconcile re-read · the :490-496 recompute list · swap_model_path_requested in the writer-group.
11. At close: re-bless baseline minus the 4 keys · regen/rename the v10 golden at 10→11 · D-289 ledger+SOURCES lockstep.

**Refute-spots:** save/load loop END lines bounded by loop-start greps; ClusterState sketch range not re-derived; seq@58112 arithmetic-derived — `--isolate` settles it.

---
*Post-script (orchestrator, at receipt): punch item 9 executed same-hour (mechanical, agent-verified one-liner); items 1-8/10-11 are the E.1.2 pickup session's FIRST act before any coding. The full corrected-anchor table lives in this report's § 1 as delivered in-session.*
