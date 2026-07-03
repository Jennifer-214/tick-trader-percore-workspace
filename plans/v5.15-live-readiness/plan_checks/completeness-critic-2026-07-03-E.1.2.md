# Completeness-critic — E.1.2 pre-coding gate (STANDING pass, /precoding-audit-gate Stage 3.5)

**Date:** 2026-07-03 · **Engine HEAD:** `b10e778` (byte-identical to E.1.1 `0ee277a`/`0ee277a`) · **Target:** `plans/v5.15-live-readiness/subplans/2026-06-15-v5.15.5.F.4d.1.E.1.2-nodestate-soa-layout.md` (reformalized v1.0, 2026-07-02).
**Role:** find the surface NO formal audit (parity/dod/trace-deps/accounting/blindspot) covered + verify the freeze happens ONCE. Raw findings; no auto-proceed. Auditing for Caramel.

All `file:line` are HEAD `b10e778`, grep/read-verified (not recalled).

---

## (B) FREEZE-ONCE completeness — the highest-value mandate

### F-1 [HIGH for freeze-once] — D-274 / GAP-2 strategy-state UNION is HOMELESS across every E.1 leaf
- **Synthesis frozen-item #7** (`plan_checks/2026-06-30-E-umbrella-hotpath-forward-audit-synthesis.md:40`) explicitly **"re-homed to E.1.2"** a *"D-274 strategy-state UNION — pre-sized to max(StrategyState) + a strategy_state_kind dispatcher guard — closes the GAP-2 SimpleDip→Momentum 384B OOB overread (#15)."*
- **BUT:** the reformalized E.1.2 Phase F (`…E.1.2…:90`) is **SILENT** on it — it reserves mode / the 5 Money fields / intended_* pack / fill-owner, but NOT the strategy-state union. The only strategy-state mention is the *live_vol_mult* convergence note (`:164`, TECH_DEBT-189/D-211), a DIFFERENT concern.
- **AND** D-274's own decision-log title (`decision-logs/v5.15.5.F.4d.1.E-architecture-v2.md:1755`) says **"homed to E.1.3+"** — and E.1.3 / E.1.4 / E.1.5 / E.1.6 / E.1-foundation plan bodies ALL contain **NONE** (grep-verified). It is homeless.
- **Why it's the freeze-once shape:** `strategy_state` is a `void*` (`ControllerEventLoop.hpp:292`), pointer-held/arena-allocated (`StrategyLifecycle.hpp:148`). D-274 offers **option A (inline pre-sized UNION → a NodeState layout change)** OR **option B (arena-aware re-init + kind guard → pointer-held, ZERO layout change)**. Frozen-item #7's "UNION" language points at **option A**. If option A is adopted after E.1.2, it re-touches the "FINAL" NodeState the E.1.3 INBOUND seam relies on (*"The struct is FINAL … never re-touches it"*, `…E.1.2…:145`) — the exact failure this ship exists to prevent.
- **Nuance (honest):** NodeState is SOFT-freeze (runtime, not wire-serialized — synthesis headline `…synthesis:17`), so an inline-union later is a *recompile + size-pin bump*, NOT a determinism/snapshot epoch. So this breaks the **zero-re-touch CONTRACT + "open once" premise**, not a wire invariant. Severity is HIGH *for the freeze-once mandate*, MED in absolute capital terms.
- **Fix (one sentence in Phase F):** RESOLVE the D-274 A-vs-B fork at the freeze — record **"option B (keep `void*`, arena re-init + `strategy_state_kind` guard on `Strategy_BuildParameters`), NOT the inline union → no NodeState reserve"** (the pointer-held default is free and legitimate per D-274 title), so frozen-item #7's "UNION" cannot later re-open the struct. OR, if the union is genuinely wanted, reserve the `max(sizeof StrategyState)` slot NOW. Silence leaves a live instruction to inline.

### Reserves that ARE covered (verified-present — so the orchestrator knows the clean set)
- **intended_* OWN seqlock pack (A22)** — RESERVED, Phase F `:90`. ✓
- **16-bit fill-record owner** — RESERVED, Phase F `:90`. ✓
- **NodeState.hot.mode (D-284)** — RESERVE-not-delete, Phase F `:90` + D-284 `:1814`. ✓
- **5 wire-locked Money fields (A-3)** — named Phase F; all 5 confirmed persisted as `sizeof(Money)`: `node_gross_wins/losses` (`ShardedSnapshotPersist.hpp:202-203`), `last_entry_price` (`:207`), `node_dd_pct` (`:213`), `pnl_feeder.price_samples` (`:239`). ✓
- **per_cluster[] aggregate slots** — named (Scope.3 `:115` / Design-shape `:153` / OUTBOUND `:145`); E.1.3 INBOUND need satisfied. ✓
- **peak(16B) + owner_node_id(2B)** — RESERVED Phase B `:62-64`; Position headroom 128→192 = 64B amply covers peak16+owner2+fill-owner2+flags (~22B ≤ 64B). ✓
- **AggregatorState Money fields** — NOT an E.1.2 reserve: `AggregatorState` is 0-hit, E.1.3-CREATED, runtime-SOFT (synthesis headline). E.1.2 lands only the Money-typing DISCIPLINE (Phase F slow_account "ALL Money, never FPN<F>"). Not a gap.

### F-2 [LOW] — exact ~48B Position reserve sub-layout deferred to Phase B
Plan says *"exact sub-layout of the reserved ~48B = a Phase-B call"* (`:64`). Audit can't verify sufficiency from plan text; my tally fits, but **Phase B must tally ALL reservees (peak/owner/fill-owner/riding-flags) against the 64B headroom BEFORE finalizing offsetof asserts** — a missed one at offset-finalize = the re-touch.

### F-3 [MED] — peak's warm-restart CONSUMER (ratchet re-arm) is E.1.3-deferred → D-110 test for peak is byte-only at E.1.2
The `:643-679` re-activation recomputes live_tp/live_sl but does NOT read `peak` to re-arm the D-206 ratchet (that consumer is E.1.3, like owner_node_id's). The plan states owner_node_id's consumer-deferral (`:163`) but NOT peak's. State it, so the peak persist-round-trip test is scoped to BYTES-only at E.1.2.

---

## (A) EDGE checklist — surfaces the core-path audits skip

### E-1 [MED] — D-110 recovery round-trip test is byte-only → BLIND to the re-derive (the real nightmare surface)
- Acceptance criterion (`:47`) + test-change (c) (`:97`) = a **golden-master byte-compare of Save→Load**. But the D-110 nightmare ("silently recovering a slightly-wrong value") lives in the **re-activation RE-DERIVE** (`ShardedSnapshotPersist.hpp:643-679`): `live_tp/live_sl` are RECOMPUTED from `entry × (1±pct)` (via `ResolvePerFillTpPct/SlPct`), NOT byte-restored — they're **derived-at-load, never serialized** (v3 NOTE `:262-267`).
- A pure wire-byte round-trip is **GREEN-blind** to a wrong re-derived live_tp/live_sl/peak-ratchet, because those bytes aren't IN the wire image. The D-110 test MUST assert the **RE-ACTIVATED in-memory ExecutionCore state** (post-`:643-679`) equals the pre-save live state — a SEMANTIC assertion, not just file-byte equality.
- Compounding: **grep confirms tests/ has ZERO existing `ShardedSnapshot_Save/_Load` coverage today** — the D-110 class is currently UNTESTED; the plan's NEW test is the first, so its adequacy is load-bearing.

### E-2 [MED] — ControllerConfig ③-fold items (a)+(b) are STALE (re-ground residue from pre-E.1.1-ship)
Plan Phase F `:90` (the ③ D-247/D-256 fold) says *"(a) include the 4-byte gate-summary in the size-pinned final layout; (b) ADD the `static_assert(sizeof(ControllerConfig)==N)` it currently LACKS (F-I — Check-K gap)."* Both are STALE at HEAD:
- The `static_assert(sizeof(ControllerConfig<64>) == 53056, …)` **EXISTS** at `ControllerConfig.hpp:1323` (D-254, landed in E.1.1's ③ arc — E.1.1 has shipped). NOT missing.
- `cfg_load_fault_flags` (uint32, 4B) is **already in the struct** at `ControllerConfig.hpp:582`, so the 53056 pin already accounts for it. Item (a) is moot (E.1.2 does not grow ControllerConfig — it holds no Position).
- **Only item (c) is genuinely open:** NO `Fingerprint_Compute` call site asserts `cfg_load_fault_flags==0` today (the 2 sites: `Backtest/Fingerprint.hpp:174` def + `Backtest/BacktestPanels.hpp:3157` call; the only `==0` is inside `cfg_compile_ok` itself, `:1335`). Per arming §2.5, a stale "it LACKS X" that actually exists misdirects the coder toward a duplicate pin + under-weights the load-bearing (c). **Corrected wording:** "(b) DONE — pin at `ControllerConfig.hpp:1323`; E.1.2's only ③ action = (c) the guaranteed-0 assert at the `Fingerprint_Compute` site(s), + UPDATE 53056 IF the final layout grows (it does not today)."

### E-3 [LOW] — real 30Hz-vs-60Hz publish-cadence COMMENT drift; not in Phase-B sweep
`ControllerEventLoop.hpp:195` ("~30Hz × 16 cores") + `:630` ("publisher thread at ~30 Hz") vs ~7 sites saying 60Hz (`ShardedSnapshot.hpp:171,377` / `OrderManager.hpp:545,751` / `GuiThread.hpp:387` / `EngineTUI.hpp:1309` / `CfgFieldRegistry.hpp:217,220`). No runtime observability GAP found (publisher is field-by-field, cadence is a call-frequency question). But Phase B's stale-comment sweep (`:79`) covers only VERSION comments — the cadence drift is out of scope. LOW; fold into the sweep opportunistically. New reserved fields (peak) are NOT wired to the per_node display publisher — acceptable for reserves, note explicitly.

### Edges VERIFIED-CLEAN (no gap — report so the orchestrator can close them)
- **External-tooling snapshot consumers: CLEAN.** No python/sh parses `.snapshot`/SHD0; only `tools/identifier_ledger.txt:56` + `check_identifier_retirement.py:57` track the VERSION symbol. The 10→11 bump needs only `--update` (Phase D/G covers). No hidden external decoder to break.
- **GUI display path does NOT break on relayout.** The per_node publisher (`ShardedSnapshot.hpp:352-497`) reads NodeContext **field-by-field by NAME** (`Money_ToDouble(state->nodes[i].node_realized)` etc.), layout-agnostic; E.1.1 froze the names. The SoA/192B relayout is display-INERT. (#15 GAP-2 is a SEPARATE strategy-swap type-confusion, not a display-of-relayout break — see F-1.)
- **Warm-restart / version-reject operator migration: STATED + acceptable.** Plan `:162` has the Operator-migration SECTION (old snapshots version-rejected → in-flight recovery won't load; acceptable epoch boundary, no live models). Covered.
- **order-submit / quantization:** touched only via the F-096 leg-split (`Async.hpp:842`, Phase E). Conservation assert is at the SPLIT (`legA+legB==intended`, exact by `Money_Sub` construction) — see a-class spot below.

---

## Spots most worth an ADVERSARIAL REFUTE (for the paired a-class)

1. **Refute F-1 needs ANY E.1.2 action.** `strategy_state` is pointer-held (`void*`) → option-B is free and defer-to-E.1.3+ is legitimate (D-274 title). Is there ANY downstream consumer that NEEDS the *inline* union (vs the pointer)? If none, F-1 downgrades to "record the decision" (LOW) — but the plan STILL must record it (else frozen-item #7's "UNION" stays a live re-touch instruction).
2. **Refute E-1 (D-110 byte-vs-semantic).** Are the re-derive INPUTS (`entry_price` + resolved cfg pct) themselves fully byte/pin-round-tripped? If `entry_price` round-trips AND the cfg is fingerprint-pinned, is the re-derived live_tp deterministic enough that a byte-compare + a cfg-pin IS sufficient? Code-read `ResolvePerFillTpPct/SlPct` inputs. If all inputs are pinned, E-1 weakens to LOW.
3. **Refute E-2 (ControllerConfig untouched).** Confirm E.1.2 adds NO field into `ControllerConfig` (cluster/mode go to NodeState/Limits, not ControllerConfig). If it does grow it, item (a) becomes live and the 53056 pin UPDATE is real work, not stale.
4. **Refute the leg-split conservation scope.** The Phase-E assert is at the split (exact); does downstream venue lot/tick QUANTIZATION of each leg independently break `legA+legB==intended` at submit? Likely out-of-E.1.2-scope (accounting-audit surface), but confirm the assert is placed pre-quantize by design.

---

## Verdict
Freeze-once is **~90% complete** — the HARD wire surface (Position 192B + cap-symbols) is well-covered and Position headroom is sufficient. **One named frozen-item (D-274 strategy-state UNION, #7) is homeless** (F-1) and must be dispositioned at the freeze so it can't re-touch NodeState. The edge findings (E-1 D-110 test adequacy, E-2 stale ③-fold) are plan-currency/test-scope defects a layout-focused formal audit misses. No auto-proceed — consult Caramel.
