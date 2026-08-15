---
type: agent-report
status: FROZEN — verbatim agent output, saved at receipt
directive: I-4 — the NodeContext PARTITION; every field classified persisted / deliberately-unpersisted / UNACCOUNTED (input to E.1.2 item F's struct↔registry partition guard)
agent_class: i-class
delivered: 2026-08-15
ground: engine HEAD 7240f3d, branch feat/v5.15-live-readiness
consumed_by: the E.1.2 close-gate partition guard + Class-58 codification
headline: 49 top-level members verified 3 independent ways; U-1 the BIT-row name trap (breaks a naive guard on day one) + U-2 drift_history is in NO registry with NO stated reason — the only DU field without one, and the only real finding
operator_decision_owed: OQ-1 (drift_history disposition — option (a) needs no version bump; (b)/(c) force v11→v12)
---

# I-4 — The `NodeContext` PARTITION: every field classified persisted / deliberately-unpersisted / UNACCOUNTED

**Ground:** engine `/home/caramel/code/FoxML_Trader_v2`, HEAD `7240f3d` (verified `git rev-parse`), branch `feat/v5.15-live-readiness`. Read-only pass; nothing edited.
**Struct under audit:** `tt::NodeContext<F>` — `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/ControllerEventLoop.hpp:315-614`.

---

## 0. Method + independent corroboration (why the field set is trustworthy)

The field enumeration was derived **three independent ways** and all three agree on **49 top-level members**:

| Derivation | Result | Evidence |
|---|---|---|
| Text extraction over the struct body (lines 316-613) | 49 | script run this session |
| **clang `-fdump-record-layouts`** on `tt::NodeContext<64>` | **49** (50 dump entries − the struct header row), same order, `sizeof=7168, dsize=7168, align=64` | `clang++ -std=c++20 -Xclang -fdump-record-layouts`, RC=0 |
| Sister **Init** registry coverage arithmetic | 40 registry rows + 6 helper-Inits + 1 telemetry cluster + 1 arena alloc = 48, residual = `gate_state` → **49** | `/home/caramel/code/FoxML_Trader_v2/MemHeaders/NodeCtxInitRegistry.hpp:98-145` (rows) + `:300-325` (`NODE_CTX_INIT_AUTOPOPULATE` Layers 2-4) |

The clang/text agreement at 49 is the load-bearing anti-fabrication check: **it proves there are no macro-injected members, no base classes, and no vtable pointer** in `NodeContext` today.

Mechanical tools run (per SUBAGENT_ARMING § 3): `tools/node_persist_layout.py` → **RC=0, "GREEN — 46 flattened wire rows match the frozen golden"**; `tools/check_meta_registry.py` → **RC=0**, 68/68 registries enrolled, H15/H19 clean.

---

## A. THE COMPLETE FIELD TABLE — 49 members, one bucket each

Buckets: **P** = persisted (row in `FOREACH_NODE_PERSIST_FIELD`) · **DU** = deliberately unpersisted (reason cited) · **UNACC** = in neither (§ C).

### A.1 HOT cluster (27 fields)

| # | Line | Type | Name | Bucket | Evidence |
|---|---|---|---|---|---|
| 1 | 330 | `SlowPathGateState` | `gate_state` | **DU** — cfg-derived cache | Struct is a bare `uint16_t flags` (`CoreFrameworks/SlowPathGateRegistry.hpp:184-186`); repopulated **every slow-path entry** by `SLOW_PATH_GATE_AUTOPOPULATE_PER_NODE` (`ControllerEventLoop.hpp:2685`, declared `:323-329`). Not even boot-init'd — it has no Init-registry row and no AUTOPOPULATE layer. |
| 2 | 331 | `ExecutionCore<F>*` | `core` | **DU** — pointer/handle | Restoring = dangling pointer. Init row `NodeCtxInitRegistry.hpp:100` (`nullptr`). |
| 3 | 338 | `NodeSlowState<F>*` | `slow_state` | **DU** — pointer/handle | Heap/arena-allocated per boot (`NodeCtxInitRegistry.hpp:224-236`); ~272 KB pointee (`ControllerEventLoop.hpp:332-337`). Restoring = dangling. **See HAZ-3** — the *pointee* is out of this partition's reach. |
| 4 | 339 | `void*` | `model_handle` | **DU** — pointer/handle | Init `NodeCtxInitRegistry.hpp:101`. |
| 5 | 340 | `void*` | `ensemble_handle` | **DU** — pointer/handle | Init `NodeCtxInitRegistry.hpp:102`. |
| 6 | 356 | `void*` | `strategy_state` | **DU** — pointer/handle **+ documented leak history** | `ControllerEventLoop.hpp:353-355` ("only `strategy_state_kind` is persisted; on load `Strategy_InitPerCore` reallocates"); the v5.11.15 leak note at `NodeCtxPersistRegistry.hpp:57-61`. |
| 7 | 357 | `uint8_t` | `strategy_id` | **P** | Row 1 — `SCALAR / NO_COMMIT` (`NodeCtxPersistRegistry.hpp:69`); comes from cfg at boot. |
| 8 | 358 | `uint8_t` | `resolved_strategy_id` | **P** | Row 2 — `SCALAR / COMMIT` (`:70`). |
| 9 | 365 | `uint8_t` | `node_state_flags` | **PARTIAL — 1 of 6 bits** | Only `KILL_TRIPPED` is on the wire, via BIT row `node_kill_tripped` (`:97`). **See § C.0 — this is the counting trap.** |
| 10 | 366 | `uint8_t` | `strategy_state_kind` | **P** | Row 3 — `SCALAR / NO_COMMIT` (`:71`). |
| 11 | 376 | `RegimeState<F>` | `regime_state` | **P — DELEGATE** | Row 24 (`:101`), `DELEGATE / COMMIT`, walker prefix `RegimeState`. **Sub-struct, see § B.** |
| 12 | 393 | `ConfidenceScorer` | `confidence` | **P — DELEGATE** | Row 29 (`:108`), `DELEGATE / COMMIT`. **Sub-struct, see § B.** |
| 13 | 395 | `GateParameters<F>` | `pending_params` | **DU** — ephemeral (rebuilt per cycle) | Staged then pushed: `ControllerEventLoop.hpp:2367` (stage + DIRTY), `:2479-2480` (rebuild→push flow). Boot-init'd by `GateParameters_Init` (`NodeCtxInitRegistry.hpp:308`). |
| 14 | 397 | `Money` | `intended_tp` | **DU** — recomputed pre-use | Rewritten from `pending_params` every rebuild at `ControllerEventLoop.hpp:3465`. |
| 15 | 398 | `Money` | `intended_sl` | **DU** — recomputed pre-use | `:3466`. |
| 16 | 399 | `Money` | `intended_qty` | **DU** — recomputed pre-use | `:3467`. Consumed only at entry-submit (`:2184-2210`), which cannot fire before a rebuild pushes params. |
| 17 | 400 | `Money` | `allocated_balance` | **P** | Row 5 — `SCALAR / COMMIT` (`:73`). |
| 18 | 407 | `uint8_t` | `halt_reason` | **DU** — ephemeral | Per-cycle gate verdict; init `HALT_OK` (`NodeCtxInitRegistry.hpp:113`). Named in the prior-art M3 allowlist. |
| 19 | 413 | `uint8_t` | `strategy_halt_reason` | **DU** — ephemeral | Init `SHALT_OK` (`:114`). |
| 20 | 415 | `double` | `staged_prediction` | **P** | Row 26 (`NodeCtxPersistRegistry.hpp:104`) — the D-110 interleave. |
| 21 | 416 | `double` | `active_prediction` | **P** | Row 27 (`:105`). Correctly persisted: spans the entry→exit window (`ControllerEventLoop.hpp:387-390`), cleared at exit `:1867`. |
| 22 | 417 | `double` | `last_confidence` | **P** | Row 28 (`:106`). |
| 23 | 425 | `double` | `last_confidence_factor` | **DU** — recomputed per ML rebuild | Init-registry group header: *"reset every cycle by RebuildOneCore; init for cold-boot safety"* (`NodeCtxInitRegistry.hpp:115`, row `:119`). |
| 24 | 431 | `double` | `last_exit_prediction` | **DU** — recomputed per cycle | `ControllerEventLoop.hpp:430` ("Reset each cycle"); init row `:120`. |
| 25 | 432 | `int` | `last_exit_dominant_horizon` | **DU** — recomputed per cycle | Init row `:121` (`-1`). |
| 26 | 437 | `int` | `last_buy_dominant_horizon` | **DU** — recomputed per cycle | Init row `:122` (`-1`). |
| 27 | 438 | `uint8_t` | `last_barrier_mode_used` | **DU** — recomputed per cycle | Init row `:123`. |

### A.2 WARM cluster (21 fields)

| # | Line | Type | Name | Bucket | Evidence |
|---|---|---|---|---|---|
| 28 | 444 | `uint64_t` | `entries_processed` | **P** | Row 6 (`:78`). `alignas(64)` cluster anchor. |
| 29 | 445 | `uint64_t` | `exits_processed` | **P** | Row 7 (`:79`). |
| 30 | 452 | `Money` | `last_entry_price` | **P** | Row 17 (`:90`). |
| 31 | 453 | `uint64_t` | `last_entry_tick` | **P** | Row 18 (`:91`). |
| 32 | 457 | `uint64_t` | `last_entry_wall_us` | **DU** — superseded by a *persisted* source | Explicit in-code: *"Fall back to `NodeContext.last_entry_wall_us` (per-core, NOT persisted)"*; the display now prefers `Position.entry_timestamp_us`, which **is** persisted in the Position blob — `ShardedSnapshot.hpp:279-292`. The pre-v5.11.65 restart bug ("Hold column showed 0m forever") is documented as **already fixed**. |
| 33 | 462 | `uint32_t` | `sl_cooldown_remaining` | **P** | Row 19 (`:92`). |
| 34 | 472 | `uint32_t` | `idle_cycles` | **P** | Row 16 (`:88`). Class-4 history rides this row (`:63-66`). |
| 35 | 479 | `Money` | `node_realized` | **P** | Row 8 (`:80`). |
| 36 | 480 | `Money` | `node_fees` | **P** | Row 9 (`:81`). |
| 37 | 481 | `uint32_t` | `node_wins` | **P** | Row 11 (`:83`). |
| 38 | 482 | `uint32_t` | `node_losses` | **P** | Row 12 (`:84`). |
| 39 | 492 | `Money` | `partner_pending_pnl` | **P — ADDED at v11 (D-420)** | Row 15 (`:87`); rationale block `:75-77`. Its sibling `partner_pending_bitmap` lives on `EventLoopState` and is re-derived on load — never a wire row. |
| 40 | 504 | `Money` | `node_gross_wins` | **P** | Row 13 (`:85`). **The Class-58 founding instance** (`:63-66`). |
| 41 | 505 | `Money` | `node_gross_losses` | **P** | Row 14 (`:86`). |
| 42 | 520 | `Money` | `node_open_notional` | **P** | Row 10 (`:82`). |
| 43 | 535 | `Money` | `node_peak_balance` | **P** | Row 20 (`:96`). |
| 44 | 536 | `Money` | `node_dd_pct` | **DU — DROPPED at v11 (D-420)**, recompute-on-load | Drop rationale `NodeCtxPersistRegistry.hpp:93-95`. **Verified**: recomputed at `ControllerEventLoop.hpp:3280-3286`, then read by the trip evaluation at `:3297` **in the same pass**. The D-420 drop is sound. |
| 45 | 541 | `uint32_t` | `node_ks_trips_total` | **P** | Row 23 (`:99`). |
| 46 | 548 | `RegressionFeederX<F>` | `pnl_feeder` | **P — DELEGATE** | Row 25 (`:102`). **Sub-struct, see § B.** |
| 47 | 554 | `RollingTurnover` | `turnover` | **DU** — ephemeral diagnostic **+ cfg-owned sizing** | Self-documented ephemeral at `ControllerEventLoop.hpp:549-551` and `ML_Headers/RollingTurnover.hpp:23`. Its `window`/`topk` are re-init'd **from cfg** at boot, explicitly overriding the Init-registry defaults — `CoreFrameworks/EngineCommon.hpp:445-451`. Same reason-class as `confidence.window`. |
| 48 | 559 | `DriftHistory` | `drift_history` | **UNACC → see § C.1** | The payload. |

### A.3 COLD cluster (1 field)

| # | Line | Type | Name | Bucket | Evidence |
|---|---|---|---|---|---|
| 49 | 600 | `SlowPathTelemetry` | `sp_telemetry` | **DU** — cross-thread atomics / session-scoped liveness | 4 `std::atomic` members zeroed at boot (`NodeCtxInitRegistry.hpp:317-320`); written by the slow thread (`EngineSharded/Run.hpp:1747-1764`), read by TUI (`DataStream/EngineTUI.hpp:2060-2066`). Persisting a liveness timestamp across a restart is a category error. |

---

## B. THE DELEGATE BOUNDARY — where a naive parser miscounts

**Four `NodeContext` members are sub-structs, not scalars.** Three are walked by a DELEGATE row; one is not on the wire at all. A parser that counts persist rows against struct fields must treat these correctly or it will both over- and under-count.

| `NodeContext` member | On the wire as | Sub-struct field count | Sub-fields persisted | Sub-fields UNPERSISTED (and why) |
|---|---|---|---|---|
| `regime_state` (`:376`) | 1 DELEGATE row (`NodeCtxPersistRegistry.hpp:101`) → **7** flattened SUB rows (golden idx 024-030) | **9** (`Strategies/RegimeDetector.hpp:584-599`) | 7 | **2** — `last_trending_score`, `last_volatile_score`. In-code citation: *"Never persisted (snapshot re-derives on warmup)"* — `RegimeDetector.hpp:596`. |
| `pnl_feeder` (`:548`) | 1 DELEGATE row (`:102`) → **3** SUB rows (idx 032-034) | **3** (`ML_Headers/LinearRegression3X.hpp:69-73`) | 3 | **0 — full coverage.** |
| `confidence` (`:393`) | 1 DELEGATE row (`:108`) → **7** SUB rows (idx 039-045) | **7 top-level** (`ML_Headers/ConfidenceScore.hpp:725-739`) | reaches into only **2** (`ic`, `rmse`), and only partially | `last_confidence` (per-call cache, rewritten at `:943`/`:984`), `freshness_tau` (cfg-owned at Init), `freshness`, `capacity`, `rmse_baseline`. Registry: `FOREACH_CONFIDENCE_PERSIST_FIELD`, `ConfidenceScore.hpp:1413-1420`. `confidence.window` cfg-owned per `ShardedSnapshotPersist.hpp:201`. |
| `pending_params` (`:395`) | **not on the wire** | — | — | Ephemeral; rebuilt per cycle. A parser that sees a sub-struct and assumes a delegate exists will wrongly flag it. |
| `gate_state` / `turnover` / `drift_history` / `sp_telemetry` | **not on the wire** | — | — | Sub-structs with no delegate. Same trap. |

**The boundary rule the guard needs:** a DELEGATE row asserts coverage of the *member*, **not** of the member's fields. The delegate-internal partition is a **second-level** question policed by three separate sub-registry tripwires (`regime ==7 · feeder ==3 · confidence ==7`, cited at `NodeCtxPersistRegistry.hpp:119-120`), which are **count**-locks, not **coverage**-locks — i.e. the second level has exactly the same Class-58 exposure the first level has. Sizing that residual: **6 delegate-internal fields are off the wire** (2 regime + 5 confidence-top-level minus the 2 partially-covered), each with a stated reason but **none in any allowlist registry**.

---

## C. ⚠ UNACCOUNTED — THE PAYLOAD

The mechanical name-diff (49 fields vs the 29 persist rows) returns **23 unaccounted**. Twenty-two of those resolve to **DELIBERATELY UNPERSISTED** with the citations given in § A. **Two items are genuine findings.**

### C.0 — FINDING U-1 (HIGH for the guard's correctness; MED as a doc defect): `node_state_flags` is a **false positive by construction**, and the registry's own column doc is wrong about it

`node_state_flags` (`ControllerEventLoop.hpp:365`) appears UNACCOUNTED to any name-matching check, because the persist row that covers it is named **`node_kill_tripped`** — the *staging* name, not the struct field name:

```text
X(node_kill_tripped,      uint8_t,              BIT,      KILL_TRIPPED,       COMMIT)
```
— `/home/caramel/code/FoxML_Trader_v2/MemHeaders/NodeCtxPersistRegistry.hpp:97`

The `NAME` column is documented as:

```text
// [COLUMN]_[NAME]_[NodeContext field name == NodeSnap staging field name (unified; PAD rows use scratch, no staging field)]
```
— `NodeCtxPersistRegistry.hpp:47`

**That claim is FALSE for the BIT row.** `node_kill_tripped` *is* a `NodeSnap` staging field (`CoreFrameworks/ShardedSnapshotPersist.hpp:381`, `uint8_t node_kill_tripped;`) but it is **not** a `NodeContext` field — the `NodeContext` side is `node_state_flags` + the `KILL_TRIPPED` mask. The doc carves out PAD rows but not the BIT row. Any guard that trusts this column doc will mis-partition. The resolution rule: for `STORAGE_KIND == BIT`, coverage attaches to the **containing bitmap field**, resolved via the `STORAGE_MASK` token.

**Second-order fact (this one is a real partial-coverage gap, and it is benign):** `node_state_flags` carries **6** bits, of which **exactly 1** is persisted. The other five are each independently re-derived:

| Bit | Persisted? | Re-derivation evidence |
|---|---|---|
| `DIRTY` | no | per-cycle staging flag (`ControllerEventLoop.hpp:2367`) |
| `KILL_TRIPPED` | **yes** | persist row `:97` |
| `MODEL_LOAD_FAILED` | no | set at boot model-load |
| `CFG_DRIFT_STRICT_REFUSED` | no | set by boot-time cfg-vs-stamp validation |
| `WARMUP_LOG_EMITTED` | no | explicitly **per-session** edge-trigger (`MemHeaders/NodeStateFlagRegistry.hpp:98-100`) — re-emitting after restart is *correct* |
| `MODEL_CORRUPT` | no | **verified set at boot**, single-threaded: `CoreFrameworks/EngineCommon.hpp:385-387` (plus hot-swap `EngineSharded/Run.hpp:1907/:1943`) |

The commit projection is a **read-modify-write of one bit** (`NPF_COMMIT_COMMIT_BIT`, `NodeCtxPersistRegistry.hpp:204-208`) — it sets or clears only `KILL_TRIPPED` and leaves the other five as boot set them. **No clobber. This design is correct.**

**Stale comment (MINOR, but it misleads exactly the guard author):** `ControllerEventLoop.hpp:359` states *"5 boolean flags bit-packed into uint8_t node_state_flags"*. The registry has **6** rows and its own `[OVERVIEW]` says *"6 BIT_FLAG rows"* (`MemHeaders/NodeStateFlagRegistry.hpp:67`). `MODEL_CORRUPT` was added later (D-221) and never folded into the struct comment. Per SUBAGENT_ARMING § 2.5 the **code is truth**; suggested correction: *"6 boolean flags bit-packed into uint8_t node_state_flags"* + append `model_corrupt (D-221)` to the "Replaces:" list.

### C.1 — FINDING U-2 (MED, and the one real "value that silently zeroes"): `drift_history` — a **risk-control detector's state** is off the wire while both its *input* and its *output* are on it

`DriftHistory drift_history;` — `ControllerEventLoop.hpp:559`. **In no registry at all**: not in `FOREACH_NODE_PERSIST_FIELD`, not in `FOREACH_NODE_CTX_FIELD`, not in `FOREACH_NODE_CTX_SUMMARY_FIELD`. Its only lifecycle touch is `DriftHistory_Init` at boot (`NodeCtxInitRegistry.hpp:312`). It carries **no in-code "not persisted" note** — unlike `turnover` (`:549-551`), `last_entry_wall_us` (`ShardedSnapshot.hpp:281`), the regime score ints (`RegimeDetector.hpp:596`), and `confidence.window` (`ShardedSnapshotPersist.hpp:201`), **all of which self-document their exclusion**. It is the only member of the DU set with no stated reason anywhere.

Struct: `struct alignas(64) DriftHistory { int count; int head; uint8_t drift_state_flags; DriftSample samples[DRIFT_HISTORY_CAPACITY]; }` — `ML_Headers/ConfidenceScore.hpp:1272-1282`, `sizeof == 4160` (pinned `:1317`).

**The coherence gap.** Around this detector:
- its **input** — the IC ring `confidence.ic` — **is persisted** (golden rows 039-042), so `ConfidenceScorer_ComputeICVariant` yields a meaningful `ic_now` immediately post-restart (`ControllerEventLoop.hpp:1879-1880`);
- its **output** — `KILL_TRIPPED` and `node_ks_trips_total` — **is persisted** (rows 20, 23);
- its **own state** — the sample ring **and the two latch bits** — **is not**.

**Concrete operator-visible consequence (unconditional).** The drift flags are exported to the display every publish:
```text
if (BITMAP_IS_SET(state->nodes[i].drift_history.drift_state_flags, MASK_DRIFT_BREACHED))     STATE_FLAG_SET(snap->per_node[i], DRIFT_BREACHED);
if (BITMAP_IS_SET(state->nodes[i].drift_history.drift_state_flags, MASK_DRIFT_KILL_TRIPPED)) STATE_FLAG_SET(snap->per_node[i], DRIFT_KILL_TRIPPED);
snap->per_node[i].drift_n_samples = (uint16_t)state->nodes[i].drift_history.count;
```
— `CoreFrameworks/ShardedSnapshot.hpp:525-538`

So after a warm restart a node that was **auto-killed by drift** displays `NODE_KILL_TRIPPED = 1` (persisted) alongside `DRIFT_BREACHED = 0`, `DRIFT_KILL_TRIPPED = 0`, `drift_n_samples = 0`, `drift_avg_ic = 0.0`. **The operator loses the attribution for why a capital control is engaged.**

**Adversarial bounds I applied to my own finding (do not skip these):**
1. **The trip-counter double-count is UNREACHABLE while the node stays killed.** The re-trip path (`ControllerEventLoop.hpp:1906-1909`) would re-increment `node_ks_trips_total` because the `MASK_DRIFT_KILL_TRIPPED` latch was zeroed — but reaching it needs ≥5 fresh in-window samples, and `DriftHistory_CheckBreach` hard-returns 0 at `if (n < 5) return 0;` (`ConfidenceScore.hpp:1385`). Samples only arrive on **exit fills**, and a killed node takes no new entries, so it can produce at most its ≤2 open legs. **Not a live double-count.** After a *manual* kill reset, a re-trip is arguably a legitimate second episode.
2. **The breach-math loss is bounded by restart duration.** `CheckBreach` walks backwards and breaks at `samples[idx].ts <= cutoff` (`ConfidenceScore.hpp:1381`), so for any downtime ≥ `drift_window_seconds` the persisted ring would have been discarded anyway — **persisting buys nothing** in that regime. It matters only for restarts shorter than the window.
3. **Cost is non-trivial:** the full ring is **4160 B/node** — persisting it would materially change the per-node block (currently 1944 B). The 1-byte `drift_state_flags` alone is the cheap subset, and it is where the unconditional loss (attribution) actually lives.

**Verdict.** Not the Class-58 founding shape (no money value silently zeroes to `$0.00`). It **is** a real, currently-undocumented coherence gap on an ML risk control, and the v11 wire was just frozen — so it is a **live wire-correctness question, not a cleanup item**. I am **flagging and stopping**, per the directive. This is a decision for Caramel: (a) leave off-wire + add the missing "deliberately unpersisted because…" citation, (b) persist the 1-byte `drift_state_flags` only, or (c) persist the whole ring. **I make no recommendation on which** — but note (a) is the only option that does **not** require a v11→v12 bump.

### C.2 — The full 23-row diff, for the record

Mechanically produced this session (49 struct fields ∖ 29 persist-row names), annotated with sister-registry membership:

```text
gate_state                  (in NEITHER sister registry)   DU  cfg-derived, repopulated per SP entry
core                        INIT                           DU  pointer
slow_state                  (NEITHER)                      DU  pointer (arena-allocated at boot)
model_handle                INIT                           DU  pointer
ensemble_handle             INIT                           DU  pointer
strategy_state              INIT                           DU  pointer + documented leak history
node_state_flags            INIT                           ⚠ U-1  FALSE POSITIVE (covered by BIT row, different name)
pending_params              (NEITHER)                      DU  ephemeral, rebuilt per cycle
intended_tp                 INIT                           DU  recomputed :3465
intended_sl                 INIT                           DU  recomputed :3466
intended_qty                INIT                           DU  recomputed :3467
halt_reason                 INIT+SUMMARY                   DU  ephemeral
strategy_halt_reason        INIT+SUMMARY                   DU  ephemeral
last_confidence_factor      INIT                           DU  per-cycle ML output
last_exit_prediction        INIT                           DU  per-cycle ML output
last_exit_dominant_horizon  INIT                           DU  per-cycle ML output
last_buy_dominant_horizon   INIT                           DU  per-cycle ML output
last_barrier_mode_used      INIT                           DU  per-cycle ML output
last_entry_wall_us          INIT                           DU  superseded by persisted Position.entry_timestamp_us
node_dd_pct                 INIT+SUMMARY                   DU  D-420 drop; recompute-then-read verified same pass
turnover                    (NEITHER)                      DU  ephemeral diagnostic + cfg-owned sizing
drift_history               (NEITHER)                      ⚠ U-2  THE FINDING
sp_telemetry                (NEITHER)                      DU  cross-thread atomics, session liveness
```

Also mechanically confirmed: **`init rows NOT struct fields: []`** and **`summary rows NOT struct fields: []`** — both sister registries are 100% resolvable against the struct (no phantom rows). Only the persist registry has non-field row names, and exactly three: `_pad_ids`, `node_kill_tripped`, `_pad_kill`.

---

## D. COUNT RECONCILIATION — 49 / 29 / 46, stated in the right units

All three numbers close. **The units differ and the guard must not conflate them.**

**29 = registry rows = wire ops at the parent level** (pinned `NodeCtxPersistRegistry.hpp:127-132`):
```text
29 parent rows
 = 20 SCALAR + 1 BIT + 2 PAD + 3 DELEGATE + 3 interleave doubles   [self-description at :46]
```
Decomposed against the struct:
```text
29 rows
 −  2  PAD rows          (_pad_ids, _pad_kill — no struct field by design)
 =  27 rows with a struct correspondence
 −  1  BIT row           (node_kill_tripped → resolves to node_state_flags via STORAGE_MASK)
 =  26 rows naming a NodeContext field directly
 + the 1 bitmap field the BIT row resolves to
 =  27 DISTINCT NodeContext fields with persist coverage   (26 full + 1 partial)
```

**49 = struct top-level members** (text + clang + Init-registry, § 0):
```text
49 struct fields
 − 27 with persist coverage
 = 22 fields with NO persist coverage
   (a name-only matcher reports 23 — the extra is node_state_flags, § C.0)
```

**46 = flattened wire rows in the layout golden** (`/home/caramel/code/tick-trader-percore-workspace/tools/goldens/node_persist_layout.txt`, indices 000-045; tool GREEN at HEAD):
```text
46 flattened rows
 = 29 parent rows
 + 17 delegate-internal SUB rows
      = 7 regime_state/*   (idx 024-030)
      + 3 pnl_feeder/*     (idx 032-034)
      + 7 confidence/*     (idx 039-045)
```
17 matches the three sub-registry tripwires exactly (`regime ==7 · feeder ==3 · confidence ==7`, `NodeCtxPersistRegistry.hpp:119-120`).

**The assertion units a future guard must choose between — these are NOT interchangeable:**

| Unit | Value | Statement it can make | Blind to |
|---|---|---|---|
| Parent rows | 29 | "the parent wire is 29 ops" | field coverage; count-neutral swaps (the v10→v11 `node_dd_pct`↔`partner_pending_pnl` swap was **exactly** this vacuity — `NodeCtxPersistRegistry.hpp:113-115` says so explicitly) |
| Flattened rows | 46 | "the byte layout by name+order+type" | struct fields that have **no** row (the Class-58 shape) |
| **Struct fields** | **49 = 27 covered + 22 exempt** | **"every field is in exactly one bucket"** | value correctness (a wrong-but-present row) |

**Nothing is un-closable.** All three reconcile. The one arithmetic subtlety worth carrying forward is that **29 and 46 are both *registry-internal* counts** — neither can see the struct — so the "49 = covered + exempt" identity is genuinely new information that no landed guard currently asserts.

**Corroborating negative result:** `FOREACH_NODE_PERSIST_FIELD` has exactly **four** referencing files — the registry itself, `ML_Headers/ConfidenceScore.hpp` (prose), `CoreFrameworks/MetaRegistry.hpp:105` (the H15 row), and `CoreFrameworks/ShardedSnapshotPersist.hpp` (the serializer). **No test references it.** The only cross-check outside the compiler is `node_persist_layout.py`, which reaches it by **text-parsing the macro body** (its `PARENT` constant, `tools/node_persist_layout.py:70`). This confirms prior-art **OPEN-3**: the struct↔registry coverage checker is genuinely un-landed.

---

## E. SISTER-REGISTRY DISAGREEMENTS (independent partitions of the same field set — disagreements are themselves findings)

| # | Disagreement | Sev | Evidence |
|---|---|---|---|
| **E-1** | **The Init registry declares 5 sub-structs "load-bearing across reset"; the persist registry keeps 3 of them and drops 2.** The NORST rationale names *"confidence / pnl_feeder / regime_state / turnover / drift_history — resetting those would destroy drift-detection / adaptive-feedback / regime-hysteresis state"* (`NodeCtxInitRegistry.hpp:182-186`). Of those five, `confidence`, `pnl_feeder`, `regime_state` are DELEGATE rows; **`turnover` and `drift_history` are not on the wire at all.** So a *paper reset* deliberately preserves them, while a *warm restart* silently destroys them. `turnover` is defensible (display-only, cfg-owned sizing); `drift_history` is § C.1. | **MED** | as cited |
| **E-2** | **The Init registry's group comment is imprecise for a persisted field.** `staged_prediction` / `active_prediction` / `last_confidence` sit under the header *"ML decision state (reset every cycle by RebuildOneCore)"* (`NodeCtxInitRegistry.hpp:115-118`), yet all three **are** persisted, and `active_prediction` is explicitly **not** per-cycle — it spans the entry→exit window (`ControllerEventLoop.hpp:387-390`) and is cleared at exit (`:1867`). A guard author reading only the Init registry would conclude these three need no persistence. The persist registry is right; the Init grouping label is loose. | **LOW** (doc) | as cited |
| **E-3** | **The Summary registry emits a field the wire deliberately drops.** `node_dd_pct` is row `NodeCtxSummaryFieldRegistry.hpp:195` (`"dd_pct"` in `summary.json`) but was dropped from the wire at v11. Benign — summary.json is emitted from live state — but it means `node_dd_pct` sits in **2 of 3** registries and a partition tool keyed on "any registry" would mis-bucket it. | **LOW** | as cited |
| **E-4** | **The persist registry's `NAME` column doc is wrong for the BIT row** — § C.0. This one is load-bearing for the guard. | **MED** | `NodeCtxPersistRegistry.hpp:47` vs `:97` |
| **E-5** | **Duplicate `last_confidence` storage.** `NodeContext.last_confidence` (`:417`, persisted, row 28) and `ConfidenceScorer.last_confidence` (`ConfidenceScore.hpp:727`, **not** persisted). Verified benign: the scorer's copy is a per-call cache rewritten at `:943`/`:984` and never read across a restart. Noted only because it is Class-55-adjacent (dual-source storage) and a partition tool walking nested names will see the collision. | **LOW** | as cited |

---

## F. EXTRACTION TRACTABILITY — facts, no verdict

**Headline:** for *this* struct *today*, text extraction is **sufficient for the name set** — text and clang agree exactly at 49. That agreement is a **property of the current struct, not a guarantee**; the census below is what a naive regex would have to survive.

### F.1 Awkward-construct census (mechanical, over struct-body lines 316-613)

| Category | Count | Members / severity |
|---|---|---|
| **Comments containing `;`** | **39** | **The dominant hazard by an order of magnitude.** A regex scanning raw lines for `type name;` matches inside prose. Worst case is a **phantom-field** generator: `:494` reads `// (v5.14.9.G; 1 bit per core in single uint16_t bitmap)` — comment text for a **removed** field (`partner_pending_active`), containing both `uint16_t` and `;`. Mitigation is mandatory comment-stripping first. Nine of the 39 also contain `uint*_t`/`double`/`Money` tokens. |
| `alignas(N)` on a member | **2** | `:376 alignas(64) RegimeState<F> regime_state;` · `:444 alignas(64) uint64_t entries_processed;`. Defeats any `^\s*<type>\s+<name>;` anchor. Both are **cluster anchors** locked by `static_assert(offsetof(...) % 64 == 0)` (`:634`, `:644`) — so they are load-bearing, not incidental. |
| Templated member types | **5** | `ExecutionCore<F>*` `:331` · `NodeSlowState<F>*` `:338` · `RegimeState<F>` `:376` · `GateParameters<F>` `:395` · `RegressionFeederX<F>` `:548`. `<` `>` breaks naive tokenizing; nested template args would be worse (none here). |
| Pointer members | **5** | `:331 :338 :339 :340 :356`. The `*` may bind either side (`void*    model_handle` vs `ExecutionCore<F>* core`) — both styles present. |
| **Multi-declarator lines (`double a, b;`)** | **0** | none present |
| **`#ifdef`-conditional members** | **0** | none present |
| **Macro-expanded members** | **0** | none — **and clang independently proves it** (§ F.3) |
| **Nested struct/union/enum definitions in the body** | **0** | the 4 sub-struct members are all *named types defined elsewhere* |
| Array members | **0** | none at top level (arrays live inside the sub-structs) |

### F.2 What the existing toolchain does and does not already do

- **`tools/node_persist_layout.py` parses registry MACRO BODIES, not struct bodies.** `PARENT = ("MemHeaders/NodeCtxPersistRegistry.hpp", "FOREACH_NODE_PERSIST_FIELD")` (`:70`); `_macro_body` anchors on `#\s*define\s+<MACRO>\s*\(\s*X\s*\)` (`:89-91`), `_rows`/`_args` (`:102`,`:123`), with `_strip_comments` (`:139-143`) and a **newline-preserving** block-comment stripper (`:153`). **It has no struct-member parser.** Struct-side extraction is a capability the toolchain does not currently have.
- **`tools/check_cache_layout.py` already owns a clang backend.** `parse_struct_blocks` (`:45`) parses only the **`[STRUCT]` tag blocks** (orient metadata: name, `[THREAD]`, `[SIZE]`, `[STRADDLE_EXEMPT]`) — **not** members. The per-field offsets come from clang `-fdump-record-layouts` via `run_emitter` / `isolate_layouts` (`:105`, `:540`), with `_struct_is_template` (`:519`) handling the `<F>` templates and `_isolate_probe_source` (`:529`) building probe TUs. **So a clang-based member extractor has an existing precedent + plumbing in-tree; a text-based one does not.**
- Per-file toolchain rule (D-321, SUBAGENT_ARMING § 2.6): **LAYOUT facts = clang**; codegen facts = g++ only.

### F.3 What clang sees that the text does not

Verified by running it (RC=0, `sizeof=7168, dsize=7168, align=64`):

1. **Proof of no macro-injected members** — clang's 49 == text's 49. A text-only extractor can never *prove* this; the two agreeing is the check.
2. **No base classes, no vptr** — the dump has no base rows and offset 0 is `gate_state`. Confirms H2-clean and that `offsetof` is well-defined here.
3. **Compiler-inserted padding, invisible in the text** — 6 inter-scalar gaps totalling **53 B**: after `strategy_state_kind` @51 → 12 B; `strategy_halt_reason` @2177 → 6 B; `last_barrier_mode_used` @2232 → 7 B; `idle_cycles` @2292 → 8 B; `node_losses` @2340 → 8 B; `node_ks_trips_total` @2448 → 12 B. (Plus larger alignment gaps around the `alignas(64)` sub-structs.) Relevant because H12 governs explicit padding in byte-equivalence contexts — and `ControllerEventLoop.hpp:675-679` records the audit finding that **`NodeContext` is deliberately NOT in a byte-equivalence path** (field-by-field fwrite; "CLAUDE.md item 27 explicitly NOT in scope"), which is why implicit padding is acceptable here.
4. **Typedefs and template params are RESOLVED — this is the sharp edge for a clang-based matcher.** Clang prints `struct FixedPoint<10, 8> intended_tp` where the registry TYPE column says `Money`; `ExecutionCore<64U>` where the text says `ExecutionCore<F>`; `RegimeState<64>` where the registry row says `RegimeState<F>`. **A clang-based guard matching the registry's TYPE column needs a typedef/instantiation name-mapping layer that a text-based one gets for free.**

### F.4 The two extraction routes, as facts

| | Text extraction | clang `-fdump-record-layouts` |
|---|---|---|
| Proves no macro-injected members | no | **yes** |
| Sees padding | no | yes |
| Names match the registry TYPE column verbatim (`Money`, `<F>`) | **yes** | no — needs a mapping layer (§ F.3.4) |
| Must survive 39 semicolon-bearing comments | **yes** | n/a |
| Must survive 2 `alignas` + 5 templated + 5 pointer members | **yes** | n/a |
| Existing in-tree precedent | none for struct members | `check_cache_layout.py` (`:105`, `:519`, `:529`, `:540`) |
| Needs a compilable TU + clang in CI | no | yes (`check_cache_layout.py:637-640` degrades to **advisory** when clang/nvim/TU are unavailable — a **Class-51 vacuity surface** if a coverage gate inherits that posture) |

---

## HAZARDS

- **HAZ-1 (blocks a naive guard):** the BIT row's `NAME` is the staging name, not the struct field name, and the registry's own `[COLUMN]` doc asserts otherwise (`NodeCtxPersistRegistry.hpp:47` vs `:97`). Any coverage check written to that doc reports a false positive on `node_state_flags` on day one — and the natural "fix" (allowlist it) would **wrongly** mark a genuinely-persisted field as exempt.
- **HAZ-2 (live wire question):** `drift_history` — § C.1. The v11 wire is frozen; options (b)/(c) there require a v12 bump + golden regen/rename riding the same commit (H21 paired-bump, `NodeCtxPersistRegistry.hpp:116-118`). Option (a) does not.
- **HAZ-3 (the partition's outer edge):** classifying `slow_state` as "accounted — pointer" silently exempts the **~272 KB** `NodeSlowState<F>` pointee (`ControllerEventLoop.hpp:332-337`) from **any** persistence discipline. The accepted model is re-warm-from-ticks — the codebase states it for the regime scores (*"snapshot re-derives on warmup"*, `RegimeDetector.hpp:596`) — but a `NodeContext`-scoped guard will read as more complete than it is. Its scope boundary should be stated explicitly.
- **HAZ-4 (second-level Class-58 remains open):** the three delegate sub-registries are protected by **count**-locks (`==7 / ==3 / ==7`), not **coverage**-locks. Six delegate-internal fields are off-wire with reasons stated only in prose. A `NodeContext`-only partition guard leaves this level exactly as exposed as level 1 was.
- **HAZ-5 (Class-51 vacuity, inherited):** if a coverage gate reuses `check_cache_layout.py`'s clang backend, note that backend degrades to **advisory-not-hard-fail** when clang/nvim/TU are missing (`:637-640`). A partition gate that silently no-ops in a deps-less CI env is a vacuously-green guard.
- **HAZ-6 (stale comment misleads the guard author):** `ControllerEventLoop.hpp:359` says "5 boolean flags"; the registry has 6 (`NodeStateFlagRegistry.hpp:67`, rows `:74-111`).

---

## SPOTS MOST WORTH AN ADVERSARIAL REFUTE (for the paired a-class)

1. **U-2 / `drift_history` — attack it from both sides.** (a) *Refute the finding:* argue the time-windowed `break` at `ConfidenceScore.hpp:1381` plus the `n < 5` floor at `:1385` makes persistence worthless for any realistic downtime, so the only real loss is a GUI badge. (b) *Refute my hedge:* construct the sub-`drift_window_seconds` restart (a crash-loop / fast operator restart) where the ring **does** carry, and price the detection-latency gap on a live ML risk control. Both readings are defensible from the code — I could not settle it without a downtime-distribution assumption I do not have.
2. **My "unreachable double-count" claim (C.1 bound 1).** I asserted `node_ks_trips_total` cannot double-count while the node is killed, because ≥5 exits are needed and a killed node takes no new entries. **Try to break it:** is there any path that pushes drift samples without an exit fill? Any path where a killed node still opens? Under partials, can a node hold >2 legs? If any holds, the finding escalates from forensics-loss to **persisted-counter corruption**.
3. **The `node_state_flags` partial-coverage dismissal.** I cleared all 5 unpersisted bits as re-derived, and I verified `MODEL_CORRUPT`'s boot-set site (`EngineCommon.hpp:385-387`). **Probe the ordering:** does the snapshot commit run before or after boot model validation, and is there any config where `MODEL_CORRUPT` / `CFG_DRIFT_STRICT_REFUSED` is set **only** on the hot-swap path (`EngineSharded/Run.hpp:1907/:1943`) and never re-derived at boot? Note the commit is a single-bit RMW so a clobber is not the risk — a *missing re-derivation* is.
4. **`intended_tp/sl/qty` benignity.** I argued no entry can fire before the first post-restart rebuild rewrites them (`:3465-3467`), because the hot path needs pushed params and the push is DIRTY-gated. **Refute by finding an entry path that reads `ctx->intended_qty` (`:2184-2210`) on a TradeEvent produced from pre-existing/replayed hot-path state.** Cross-check `EngineSharded/Run.hpp:1516`.
5. **The 46 vs 29 vs 49 units claim (§ D).** Verify independently that the 3 sub-registry tripwires are **count**-locks and not coverage-locks — if any one already asserts field coverage, HAZ-4 shrinks and the second-level exposure is smaller than I stated.
6. **§ F.1's "0 macro-expanded / 0 `#ifdef` / 0 multi-declarator".** I proved this two ways (regex census + clang/text count agreement). **Attack the generality:** these are facts about `NodeContext` at `7240f3d`, not about the sibling structs a guard might later cover (`OrderManagerState`, `Portfolio`, `ExecutionCore`) — per `feedback_dont_generalize_substrate_before_input_space_known`, run the same census on those before any claim that text extraction "works".
7. **E-1's asymmetry.** Refute by arguing paper-reset and warm-restart have *legitimately different* semantics (reset = deliberate session boundary; restart = continuity), so a field can rationally be NORST-preserved yet wire-dropped. If that holds, E-1 downgrades from a disagreement to a documented design distinction — but then it needs to be *written down*, because nothing in-code states it.

---

## OPEN QUESTIONS (for Caramel)

- **OQ-1:** `drift_history` — (a) leave off-wire + add the missing exclusion citation (no version bump), (b) persist the 1-byte `drift_state_flags` only, or (c) persist the 4160 B ring? (b)/(c) force v11→v12 + golden regen/rename in the same commit.
- **OQ-2:** Should the partition be stated over **fields** (49) or over **fields + bitmap bits** (49 + 5 extra bit-level entries)? The `node_state_flags` case is the only member where those differ today, but the codebase has ≥4 bitmap-packed cohorts and the choice sets the precedent.
- **OQ-3:** Does the exempt-side allowlist need a **reason column** (`POINTER / EPHEMERAL / RECOMPUTED / CFG_OWNED / SUPERSEDED_BY_<field> / DIAGNOSTIC`)? Every DU field in § A has a reason in prose; **`drift_history` was the only one with none — and it was the only real finding.** That correlation is itself the argument for the column.
- **OQ-4:** Scope — `NodeContext` only, or does the partition extend to the delegate-internal level (HAZ-4, 6 more off-wire fields)?
- **OQ-5:** Fix the two stale docs now or fold them into the guard's ship? `ControllerEventLoop.hpp:359` ("5" → "6" flags) and `NodeCtxPersistRegistry.hpp:47` (the `NAME` column claim, which needs a BIT-row carve-out alongside the existing PAD carve-out).

---

**Key files:** `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/ControllerEventLoop.hpp` · `/home/caramel/code/FoxML_Trader_v2/MemHeaders/NodeCtxPersistRegistry.hpp` · `/home/caramel/code/FoxML_Trader_v2/MemHeaders/NodeCtxInitRegistry.hpp` · `/home/caramel/code/FoxML_Trader_v2/MemHeaders/NodeCtxSummaryFieldRegistry.hpp` · `/home/caramel/code/FoxML_Trader_v2/MemHeaders/NodeStateFlagRegistry.hpp` · `/home/caramel/code/FoxML_Trader_v2/MemHeaders/PerNodeStateFlagsRegistry.hpp` · `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/ShardedSnapshotPersist.hpp` · `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/ShardedSnapshot.hpp` · `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/SlowPathGateRegistry.hpp` · `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/EngineCommon.hpp` · `/home/caramel/code/FoxML_Trader_v2/ML_Headers/ConfidenceScore.hpp` · `/home/caramel/code/FoxML_Trader_v2/ML_Headers/RollingTurnover.hpp` · `/home/caramel/code/FoxML_Trader_v2/ML_Headers/LinearRegression3X.hpp` · `/home/caramel/code/FoxML_Trader_v2/Strategies/RegimeDetector.hpp` · `/home/caramel/code/tick-trader-percore-workspace/tools/node_persist_layout.py` · `/home/caramel/code/tick-trader-percore-workspace/tools/goldens/node_persist_layout.txt` · `/home/caramel/code/tick-trader-percore-workspace/tools/check_cache_layout.py` · `/home/caramel/code/FoxML_Trader_v2/plans/v5.15-live-readiness/reports/2026-08-14-ui-position-settings-mismatch/i-class-close-gate-surface.md`
