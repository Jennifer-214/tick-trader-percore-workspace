---
type: audit-synthesis
audit: E-umbrella hot-path forward audit (Workflow wcth0c1i6, 2026-06-30, 85 agents, 5:5 / 7:7)
raw: plans/v5.15-live-readiness/plan_checks/raw/2026-06-30-E-umbrella-85agent-workflow-raw.txt  # durable copy (2549 lines, preserved 2026-06-30 from the session-temp workflow wcth0c1i6.output); THIS doc is the distillate
purpose: enumerate what every remaining E leaf needs from the E.1.2 frozen layout, so E.1.2 freezes ONCE — hot path as priority lens
related:
  - subplans/2026-06-15-v5.15.5.F.4d.1.E.1.2-nodestate-soa-layout.md  # the freeze being informed
  - _future/2026-06-30-hot-slow-path-optimization-architecture-and-futures.md  # the optimization-leaf futures
  - decision-logs/v5.15.5.F.4d.1.E-architecture-v2.md  # D-282+ (the decisions this informs, pending greenlight)
status: synthesized; A-class adversarial pass + operator greenlight pending before E.1.2 formalization/code
---

# E.1.2-freeze forward audit — synthesis

## Headline (the de-risking insight everything rests on)

**Only `Position` + the cluster cap-symbols are a determinism epoch to re-touch.** `Position` is the SOLE raw struct-image `fwrite(sizeof(Position<F>))` (`ShardedSnapshotPersist.hpp:169`). `NodeState`/`ClusterState`/`AggregatorState` are **NOT wire-serialized** — the snapshot field-projects per-node state one field at a time (`:172-254`); `ClusterState` is pure runtime. So growing the runtime clusters later = a recompile + size-pin bump, **NOT** a snapshot epoch. → **HARD-freeze `Position` + the cap-symbols; SOFT-freeze the runtime clusters.** This collapses "freeze the whole layout perfectly forever" to a small, bounded surface.

## Per-leaf verdicts (all YELLOW-conditional — over-reserved/over-claimed urgency, not "broken")

- **E.1.3** (aggregator/coherence): YELLOW — the Money-not-FPN cluster typing is load-bearing + negative-cost; the only genuine wire freeze (Position + owner_node_id) is clear; but cap-symbols don't exist yet + several layout forks open (D-206 peak, balance home, kill-eval scope). Runtime clusters re-open cheap.
- **E.1.4** (fill-completeness): YELLOW — Position half is GREEN (fill adds ZERO Position fields). `owner_node_id` NOT required by E.1.4 (decodable from `order_id>>60`). The H4 sketch-money fix + the Position AoS→SoA serializer rewrite are the real gates.
- **E.1.5** (per-cluster purity): YELLOW — hot-path-inert; the surviving frozen set is small + byte-cheap (owner in pad, Money-typing, BUY_BLOCKED reuse). The leaf-map OVER-reserved (per-symbol slab etc., refuted). A34 → PULL not push.
- **E.1.6** (multi-exchange): YELLOW — zero per-tick branches; its whole NodeState/ClusterState substrate is forward-created by E.1.2, never re-touched. Sketch bakes an H22 violation (`per_cluster[NUM_EXCHANGES]` / `cluster_id≡ExchangeEnum`) — decouple before freeze.
- **OPT** (optimization leaf): YELLOW — layout-INERT + wire-free; all branch/compute reduction homes here, post-freeze. The sketch's "RollingStats pointer-held or it re-opens NodeState" is a refuted phantom.
- **D-206** (exit trailing-profit): YELLOW — the D1 call. Position NOT yet safe to freeze: peak-vs-FLOOR-channel is genuinely contested (route give-back through the existing persisted `stop_loss_price` `Money_Max` floor → Position stays 128B, vs reserve a 16B peak).

## Hot-path baseline (the H7/H20 branch picture)

The "25 data-dependent-warm branches" decomposes as **1 real** + **7 guarded-rare** (allowlist) + **12 tool-flattening artifacts** (cold-nested under the trade-fire `__builtin_expect(,0)` gate; the flat analyzer over-counts). The 1 real = `ExecutionCore.hpp:337-338` `active ? live_tp : cached` (a real `je`; the `// CMOV verified` comment is stale — no 128-bit cmov for 16B Money). Fix = **Option C** (fold `& -active` into `sg_fires_a`, mirroring leg B) → optimization leaf, NOT E.1.2. The SoA relayout is **hot-path-inert** (the gate reads `ExecutionCore<F>`, never `Portfolio.positions[]`). Slow path: `RollingStats_Push` 14 register spills (real p99 suspect, not branches); `EventLoop_RebuildOneCore` unmetered (coverage hole). All → OPT leaf.

## Frozen-layout set — what E.1.2 must freeze (the input-space; grouped from the 24-item set)

1. **MONEY-TYPING (universal, negative-cost):** ALL `slow_account` + `drainer_state` + `AggregatorState` money fields freeze as `Money` (16B), NEVER `FPN<F>`. The v0.1 sketches type these `FPN<F>` — a **silent encoding epoch** (FPN 2^F vs Money 10^8, both 16B → size-pins can't catch it) + D-110 warm-restart corruption. **MUST-FIX before freezing the money cluster.** Enumerate the WHOLE accounting set, not just NodeState.core_fees.
2. **`owner_node_id` on Position:** byte-FREE in the existing `_pad_pos[7]`@121; NAMED `=0`-init PERSIST field, zeroed at every OpenSlot/Add/bypass site, round-tripped in BOTH serializers. (NOT "required" by E.1.4 — decodable from `order_id>>60` — but cheap + forward-useful. Width BLOCKED on the cap-symbols.)
3. **CAP-SYMBOL SSoT (HARD pre-freeze blocker):** `NUM_EXCHANGES` / `MAX_NODES_PER_CLUSTER` / `MAX_CLUSTERS` do NOT exist (`Limits.hpp` has only `MAX_EXECUTION_NODES=16`/`MAX_PORTFOLIO_POSITIONS=16`). `owner_node_id` width + every cluster-sized array can't freeze without them. Define ≤256 each → `uint16_t owner_node_id=(cluster<<8)|node`.
4. **`cluster_id` DECOUPLED from `ExchangeEnum`** (H22): dimension cluster arrays by `MAX_CLUSTERS`, never the exchange index.
5. **Seqlock pack:** `account_state_seqlock` first in `slow_account`, counter-first, whole cluster `alignas(64)`; the counter + padding must be SKIP_PERSIST.
6. **Per-node account fields** (relocations, not triple-stored): realized_pnl + open_notional + `node_peak_balance` (running Money_Max — silently OMITTED from the sketch; its consumer is the MTM kill) + allocated_balance. DROP `drawdown_max` (0 consumers) + `drawdown_current` (derivable).
7. **D-274 strategy-state UNION** (re-homed to E.1.2): pre-sized to max(StrategyState) + a `strategy_state_kind` dispatcher guard — closes the GAP-2 SimpleDip→Momentum 384B OOB overread (#15).
8. **Per-node kill latch + trips counter** (slow-owned); keep `kill_flags` as 3 separate `alignas(64)` atomics (writer-independent). NO new hot read of ClusterState/kill_flags — kill reaches hot ONLY via the existing branchless permission atomic.
9. **NOT-frozen / forward-open** (record explicitly): `FillEvent` field set (ring never serialized — design in E.1.4); per-exchange fee/precision (venue-sourced .rodata); `metadata_flags` uint16→uint32 widen (.rodata); `ClusterState` adapter = `tt::ExchangeAdapter<F>` fn-ptr table BY VALUE (never `template<AdapterT>`).
10. **D-206 16B peak — SPECULATIVE/CONTESTED (the D1 fork):** reserve-now (Position→144/192B; MUST init in the warm-restart round-trip same freeze) vs the floor-channel alternative (Position stays 128B). **Audit leans floor-channel.**
11. **HARD wire-locked:** `Position` layout is the SOLE struct-image dump; BOTH serializer fwrite sequences (`Portfolio_Save` prefix-walk `:570` + the raw blob `:165/169`) re-derived field-by-field under AoS→SoA without dropping any field (a missed SoA field = silent-zero-on-restore = D-110). The freeze enumeration is INCOMPLETE if it omits the fill read-set (entry_price/entry_fee/quantity/tp/sl) or the two serializers.

## E.1.2 recommendations (the actionable punch-list, distilled from the 22)

1. **Fix the sketch BEFORE freezing the money cluster** — retype all slow_account/drainer/AggregatorState money `FPN<F>`→`Money`; enumerate the WHOLE accounting set.
2. **Define the cap-symbol SSoT in `Limits.hpp`** (≤256 each); `owner_node_id` = `uint16_t (cluster<<8)|node`.
3. **Decouple `cluster_id` from `ExchangeEnum`**; dimension by `MAX_CLUSTERS`; carry `exchange_id` as a field.
4. **Land `owner_node_id`** in `_pad_pos` as a NAMED `=0` PERSIST field, zeroed at all sites, round-tripped in both serializers.
5. **`sizeof(Money)`-parameterize every Position size-pin** (the 8B-equity forward-compat door; ~10 literal `16`/`128` asserts in `Portfolio.hpp:117,123-130,141,143`; pin the *relationship*, not the digit).
6. **Money-ize the F-096 leg-split** (`Async.hpp:842-851`, TD-167) in the relayout: `legA=Money_Mul; legB=Money_Sub(intended,legA)` (conservation by construction) — the scaffold's "already Money-ized" claim is STALE.
7. **Thread snapshot VERSIONs:** PORTFOLIO 7→8, SHARDED 10→11 (+ tombstone + `check_identifier_retirement --update` + a `sizeof(Position)↔version` static_assert closing the silent-cascade gap). Note the 3rd: `CONTROLLER_SNAPSHOT_VERSION=14` (legacy PortfolioController) — delete the dead snapshot rather than bump (D2).
8. **Replace literal position-count `16` with `MAX_PORTFOLIO_POSITIONS`** at the serializers (pin the SYMBOL).
9. **Keep the slow_account/hot publish behind a single-designated-publisher abstraction** (cheap now; prevents a seqlock-multi-writer trap if per-task-core ever lands — the E.1.3+ logic-coupling caveat).
10. **DELETE or relocate-read-only `NodeState.hot.mode`** (0 hot readers; split-brain hazard). Keep `cfg.trading_mode` the STAMP_BOUND SSoT.
11. **Re-ground all file:line at HEAD `0ee227a`** before coding; APPEND a 4th mode state, never renumber PAPER=0/LIVE=1/SHADOW=2 (H21).

## Open decisions (the operator calls, from the 17 — D1/D2 are the load-bearing)

- **D1 (THE call):** Is `Position` FINAL at 128B? — route D-206 give-back through the existing persisted `stop_loss_price` `Money_Max` floor (no stored peak; 128B; restart-strictly-better) vs reserve a 16B peak. **Audit leans floor → Position FINAL @128B + owner_node_id free in pad.**
- **D2:** delete the legacy `PortfolioController` snapshot (CONTROLLER=14) — orphaned post-single_core-deletion, untested capital path; H21 remove-dead-code.
- **Seam-map drift:** the dependency-graph puts aggregator+torn-read at E.1.3; decision-log D (2026-06-15) puts it at E.1.4 — reconcile before either claims the torn-read close.
- Lower-stakes: A34 → PULL; per-cluster mode → keep `cfg.trading_mode` SSoT; `NodeState.hot.mode` → delete; `MAX_NODES_PER_CLUSTER` ≤ `MAX_EXECUTION_NODES`.

(Tech-debt cascade [27] + realign-risks [24] + the hot-path branch-roadmap [14] live verbatim in the raw workflow file; the load-bearing ones are folded above.)

---

## A-CLASS ADVERSARIAL VERDICTS (2026-06-30) — SUPERSEDES the audit leans above where refuted

3 a-class fired against the load-bearing claims; **ALL 3 REFUTED.** (The 85-agent audit did per-leaf I→A, but its *global synthesis* recommendations were never adversarially tested — that's the gap this pass closed. Methodology note: the synthesis stage needs its own A-pass, not just per-leaf.)

**A-1 (de-risking + cross-E completeness) — REFUTED both targets.**
- "Only `Position` is raw-imaged" is **FALSE**: `OrderEventLog.hpp:320` (live sharded write-through + replayed disk log; own magic `OMSEL`/`ORDER_EVENT_LOG_FORMAT_VERSION 2`) + the dead `PortfolioController` Position+BanditState images are also raw-image epochs. The 3 new clusters ARE soft *at HEAD* but that's a DISCIPLINE, not a guarantee, and breaks at the E.2 cross-binary decoupling → use an explicit **wire-surface LEDGER**, not a blanket soft-freeze.
- "Freeze once serves every leaf" **FALSE** — 4 holes: **(C/HIGH)** the rec to DELETE the per-node mode contradicts E.1.5 (needs `cluster.trading_mode`, D-217/D-218) + E.1.6 (needs `NodeState.hot.mode`, D-22/D-32) → **RESERVE both, don't delete**; **(A)** FillEvent/OrderEvent ARE persisted wire (E.1.4's own epoch); **(B)** the `order_id>>60` attribution is 4-bit/16-node/zero-cluster, incompatible with the 16-bit `(cluster<<8)|node` cap → reserve a **fill-record owner**; **(D)** E.1.3's `intended_*` seqlock pack is unreserved → reserve or fold into `drainer_state`.

**A-2 (D1 Position-FINAL-via-floor) — REFUTED.**
- The floor-channel (`peak = floor/(1−g)`) factors ONLY for constant `g`; D-206's charter (learned/bandit ratchet + ATR give-back + MFE reward) needs the real persisted **peak**. The precedent (`PortfolioController.hpp:684`) is the wrong engine (legacy `RecordExit`, never called sharded). The warm-restart re-arm actively **DISCARDS** the persisted SL (recompute `live_sl=entry×(1−sl_pct)`, `ShardedSnapshotPersist.hpp:661`) = the A1 class.
- → **RESERVE the 16B peak NOW: Position 128→192B** (3 cache lines; ~32B headroom absorbs `owner_node_id` + riding flags + the fill-owner). Open Position ONCE. (H21/H12: `_pad_pos` has no `=0` init but is in the persist payload → repurposing needs a version bump + explicit zero-init, NOT "free".)

**A-3 (money / determinism / coupling) — REFUTED all 3 targets.**
- Punch-list **INCOMPLETE**: 5 wire-locked `Money` fields ABSENT from the per-node enumeration (`node_gross_wins/losses` `:202-203`, `last_entry_price` `:207`, `node_dd_pct` `:213` [wire-locked — NOT a free "derive & drop"], `pnl_feeder.price_samples` `:239`) — the sketch doesn't contain them, so "retype FPN→Money" can't catch them → E.1.3 grows the "FINAL" layout. The `+7` stride literal (`Portfolio.hpp:139`) is invalidated by `owner_node_id`-in-pad AND missed by the parameterization list.
- SoA serializer determinism **UNSAFE**: `Portfolio_Save/Load` is DEAD (delete, don't bump 7→8); a THIRD dead Position serializer (`PortfolioController_SaveSnapshot:2043`) is SoA-**FORCED**-deletion (the struct is live → stops compiling) — so the LIVE re-derive surface is **ONE** serializer (`ShardedSnapshot`), not "both"; the `sizeof(Position)↔version` assert is **VACUOUS** vs a byte-reorder (sizeof stays 128B) → use a **golden-master round-trip byte-compare**; the hand field-list drops `original_tp/sl/entry_timestamp_us/pair_index` → D-110.
- Single-publisher: NOT an E.1.2 abstraction (premature — no publish code yet) NOR free-to-defer (the single seqlock counter IS a single-writer commitment frozen into the layout) → the cheap-now deliverable = a **DOCUMENTED H22 single-writer-per-node-account invariant** (H22 already mandates it).

## CONVERGENT AMENDED E.1.2 FREEZE PLAN (the real spec)

1. **Open `Position` ONCE → 192B**: reserve the 16B `peak` (Money, PERSIST) + the riding flags + `owner_node_id` (named, `=0`-init, PERSIST) in the headroom. One Position epoch.
2. **Registry-drive `Position` + its sole live serializer off `FOREACH_POSITION_FIELD`** (A-1 + A-3 converge): drop-proof gather/scatter, no hand-literals (`+7` stride / the `16` count / the field-list all auto-flow).
3. **Delete the dead serializers** (`Portfolio_Save/Load` + `PortfolioController_*Snapshot`) — SoA-forced; the live re-derive surface is ONE (`ShardedSnapshot`). Fix the stale `v11` refuse-comment (`ShardedSnapshotPersist.hpp:329`).
4. **Reserve the cross-E slots**: mode (`cluster.trading_mode` + per-node, NOT delete); the 5 missing wire-locked `Money` fields; the `intended_*` seqlock pack; the fill-record owner (16-bit).
5. **Determinism guard = golden-master byte-compare** of the live snapshot round-trip (E.1.0 `±USE_NATIVE_128`), NOT a `sizeof` assert. Update `controller_test.cpp:26819` (the 4-version assert) on the SHARDED bump.
6. **Document the H22 single-writer-per-node-account invariant** at the freeze (+ the CI-check candidate).
7. **Explicit wire-surface ledger** (Position · OrderEvent · the dead ones) replaces the blanket soft-freeze. FillEvent/OrderEvent epoch is E.1.4's.

**VERDICT: NO-GO on the audit's framing; the amended plan above is the real E.1.2 spec.** Next: formalize the amended plan → re-confirm → `/precoding-audit-gate` → code. Decisions → decision-log D-282+ on operator greenlight.

---

## 3:3 INVARIANT-VALIDATION (2026-06-30) — candidate "constraint-driven layout" (H23?)

A 3:3 (3 i-class validate + 3 a-class refute) tested whether the layout principle Caramel + orchestrator converged on should enter the always-loaded ruleset. **Outcome: NOT a new H23, NOT a new CLAUDE.md principle — but a genuinely-new NARROW core survives, capital-flavored.**

**Why not an H-row / CLAUDE.md principle (4 agents converge):**
- The "layout-as-a-solve" framing is ~90% ALREADY codified: layout = a cost-weighted DECISION (`latency-vs-cache-decision-framework`, = **CLAUDE.md item 28**) + `decision-first-cluster-layout-pattern.md`; single-owner = **H22**; registry-gen = **H17**. Re-codifying = doc-layer split-brain (the Class-47 shape).
- The flat "5-constraint set" is INCOMPLETE — misses ≥4 real forces already in specs: intra-cluster field ORDER, array-stride alignment (`sizeof%64`), SIMD lane-width, ABI padding (why `ControllerConfig==53056` is a hand-literal). So it's not a clean solve.
- "Registry-generated, never hand-maintained" is FALSE-today (the `Money`/`FPN_Binary` primitives, the wire-framing headers, the venue HMAC body, the hybrid `Order`/`ModelHandle` clusters are legitimately hand-laid) and would false-flag ~50 hand-pins + contradict the codified "manual-reorder-with-offsetof-locks" discipline.
- An H must be a DECIDABLE absolute; the load-bearing clause ("the unit it varies with") is plan-time JUDGMENT (the `cfg-field-categorization-discipline` tree). H-promotion is Stage 5; this has 0 non-cfg canonical applications today.

**The genuinely-new, NARROW core that survives (the cross-tier OWNERSHIP / REPLICA-COHERENCE model — fold into the H22 *spec* + a small Stage-2 spec, NOT an H-row):**
- **Owner = the FINEST tier of INDEPENDENT determination** (the leaf authority); coarser tiers DERIVE by aggregation, never co-write. *(Corrects "coarsest unit it varies with" — which mis-points at deployment for an aggregate like realized_pnl. Fight #5.)*
- **A replica TRACKS its owner — re-derived FROM the owner's value + kept fresh (decision-time-binding / seqlock-republish), never (a) independently re-derived from DIFFERENT inputs [drift] nor (b) a STALE unrefreshed copy [Class-27].** *(`live_tp` re-derives from `tick.price` at the signal tick → diverges from booked `take_profit_price` under slippage, `ExecutionCore.hpp:543` vs `OrderManager.hpp:1195` — Fight #4; the stale-copy form IS Class-27 scalar-cfg-mirror, which a bare "owner stays SSoT" would green-light. = D-190 + `decision-time-data-binding-pattern.md`. Capital tooth.)*
- **TWO HALVES (coverage i-class):** the CONSTRAINT-SATISFACTION discipline (owner/access/thread/tier/wire) is universal+timeless but ~already H6+H22+DOD §3+item-28; the REGISTRY-GENERATION half is a MECHANISM/gradient ("framework-driven > ad-hoc"), NOT a universal absolute — the bespoke cache-tuned hot structs (`ExecutionCore`/`GateParameters`: `permission` own-line because *another CPU* atomic-stores it; `live_tp/sl` CMOV co-residence) are CORRECTLY hand-laid. So the only NEW codification is the ownership/replica-coherence refinements above; the E.1.2 generation-application = registry-generate the MISSED `NodeContext` persist-serializer (the OMS `FOREACH_OMS_FIELD` pattern, `ShardedSnapshotPersist.hpp:176-233` hand-loop → `FOREACH_NODE_PERSIST_FIELD`).
- **Replicas may sit at ANY tier (incl. DOWNWARD coarse→fine = the H22-purity mechanism) for any of {hot-access | cross-thread-publish | per-node-locality}.** *(The kill-flag per_node/per_cluster_mirror/global_mirror; the snapshot display replicas; the cluster-id→node.binding copy. Fights #6/7/9.)*
- **Derived fields are a 3rd category** (recompute by default; if cached/persisted, name the inputs + be re-derivable on load). *(node_dd_pct: "recomputed each rebuild" yet raw-persisted. Fight #2.)*
- **Pipeline-staged values** (intended_* : Node→SubmitCommand→Order→Position) are one-authority-at-a-time handoffs, NOT duplicated authority. *(Fight #3.)*
- The 4 axes (owner ⊥ tier ⊥ thread ⊥ wire) are ORTHOGONAL: "hot AND persisted" is the NORMAL case (`take_profit_price`), not a tension.

**Validated (the owner axis genuinely works):** the three `peak`s (deployment ks_peak / node peak_balance / position D-206 peak) — distinct owners dissolve the naming collision; the GateParameters→ExecutionCore seqlock (textbook replica); the 9 registry-generated Position PERSIST fields.

**E.1.2 PAYOFF — the per-field declaration table is captured durably in the sister `2026-06-30-E.1.2-per-field-declaration-table.md`** (owner/tier/thread/wire for every Position + NodeContext + OMS + cluster field, cited; the i-class `abbfe21a8c89ddf63` output, saved before its agent temp expired). It IS the E.1.2 constraint-declaration the reformalized plan builds from; its §3 "fights" are the real design decisions, mostly E.1.3-homed: realized_pnl finest-tier-owner (= the E.1.3 O(1) aggregator: node owns, deployment derives) · live_tp copy-not-recompute (= the E.1.3 mirror↔book coherence) · trading_mode granularity (below).

**Mode question (Fight #1) — ANSWERED:** `trading_mode` is **cluster-homogeneous today** — all live consumers are deployment/boot (`LiveReadiness`/`NormalizeForMode`/`IsLiveCapital`), **no per-node override key exists** (grep clean), and a cluster = one subaccount/venue binding. The ONLY per-node wedge is **SHADOW** (live-data + simulated-fills, a per-node execution property) — but SHADOW is RESERVED/unimplemented (`ControllerConfig.hpp:43`). So: **cluster owns mode (homogeneous clusters), UNLESS you deliberately decide SHADOW needs per-node** — a capability choice, not a discovered fact. (The wording must distinguish "the unit it CAN vary with" [capability] vs "DOES vary with" [current config].)

**Codification slate (much smaller than first proposed): NO CLAUDE.md edit, NO H-row.** → (1) fold the ownership/replica-coherence model into the **H22 spec** (`per-node-purity-scale-invariance.md`) + a small Stage-2 `state-replica-coherence.md` spec; (2) the registry-serializer-generation is the E.1.2 CODE application (extends H17, via the meta-registry `SERIALIZER_GENERATED` flag — Stage-2 until ≥2 non-cfg conformers); (3) a memory for the synthesis-needs-its-own-adversarial-pass meta-discipline. **Decisions LOGGED D-282..D-286 (2026-06-30).**

---

## Downstream-leaf raw-park breadcrumbs (LOW — the raw-ONLY residue; homed here so nothing is top-N-collapsed)

An exhaustive per-item capture check (c-class `a1559876`, 2026-06-30) enumerated ALL 65 named raw items (`techDebtCascade[27]` + `realignRisks[24]` + `branchRoadmap[14]`) **+ the 63 extra-global items** (`frozenLayoutSet[24]` + `e12Recommendations[22]` + `openDecisions[17]` — the synthesis's own distillation sources, FOLDED by construction) + the per-leaf/hotPath roll-ups. **Verdict: every actionable item is FOLDED / HOMED (TD-2xx / D-entry / subplan) / or deliberately raw-parked; nothing E.1.2-freeze-load-bearing is unhomed.** These **6** were the only items living in the raw ONLY (not individually ledgered) — all LOW, all downstream-leaf (post-E.1.2). Listed individually (no collapse) so each is ledgered here + pointed at its target leaf, per the exhaustive-capture discipline:

1. **`capital_allocated` value-coupling (rr#15)** — the (N+1)th node re-divides every node's `allocated_balance` (H22 allocator-semantics). NOT a freeze-blocker. → **E.1.5** (allocator-semantics) at formalize.
2. **Per-subaccount rate-limit granularity (rr#23)** — the `SubAccountPool` needs its own rate-limit triple. → **E.1.6** (multi-exchange) at formalize.
3. **Meter the relocated kill-eval @10µs drainer budget (rr#19-half)** — the coverage-hole half is folded (`_future`); the "meter the relocated eval" half is raw-only. → **E.1.3** at formalize.
4. **`RegimeDetector:571` FPN→double→int H4-exemption refute (br#6)** — the specific per-site refute (the OPT-category is homed). → **OPT leaf** (`_future`).
5. **⚠️ A16 makes `filled_qty` cumulative → Class-38 INERT `-filled` term FLIPS LIVE in E.1.4 → §4c conservation must account (tcd#10-refinement)** — LOW-**MED**; a latent-bug-goes-live interaction. Substrate homed (D-212 + E.1-foundation); this is the E.1.4-specific angle. → **E.1.4** at formalize (the strongest breadcrumb — flag it).
6. **Class-46 edit-site correction: `ProcessFillCommand` (`:1474/1442/1450`) not `HandleFill` (tcd#9)** — seam-cite fix for the E.1.4 terminal-actions-gate-on-FILLED work. → **E.1.4** at formalize.

**Currency-drift (self-healing at the handoff-mandated `.E.1` file:line re-ground; NOT spot-fixed, to avoid re-citing a wrong line):** TD-170 ledger cites `:3443/:3424/:3441` (live ≈ `ControllerEventLoop.hpp:3450`/`:3454-5`); D-229 cites `RollingStats:187` (live ≈ `:325/334/343`); TD-135 body omits the "GUI 5-entry array vs 4-regime registry" sub-finding; and this doc's own `§ Open decisions` D1/D2 read "leans floor @128B" pre-supersession (the A-class header at the A-CLASS section supersedes → 192B). The pickup's mandated re-ground resolves these systematically.
