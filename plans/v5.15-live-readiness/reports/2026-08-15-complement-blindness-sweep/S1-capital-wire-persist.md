---
type: agent-report
status: FROZEN — verbatim agent output, saved at receipt
directive: S-1 — complement-blindness sweep, shard 1/5: the CAPITAL / WIRE PERSIST family
agent_class: i-class
delivered: 2026-08-15
ground: engine HEAD 7240f3d, branch feat/v5.15-live-readiness
headline: F-1 CRITICAL, PROVEN BY EXECUTION — ic.actuals.count/head unpersisted while ic.predictions.* are; a perfectly-correlated predictor reads IC = -0.5238 after warm restart + 6 trades, and that IC drives an auto-kill capital control
operator_decision_owed: OQ-1 (F-1 fix shape — (a) mirror in commit tail = NO version bump; (b) 2 registry rows = v11→v12; (c) restructure RollingIC = removes the class)
sister_reports: S2-cfg-surface.md · S3-stamp-hmac-ml.md · S4-nodectx-state-bitflags.md · S5-emit-display-and-set-closure.md
---

# S-1 — COMPLEMENT-BLINDNESS sweep, shard 1/5: the CAPITAL / WIRE PERSIST family

**Ground:** engine `/home/caramel/code/FoxML_Trader_v2`, HEAD `7240f3d` (verified `git rev-parse`), branch `feat/v5.15-live-readiness`. Read-only pass; nothing edited. One probe binary was compiled into `build/` to prove F-1 and then removed; `git status` is byte-identical to session start.

**Headline:** two genuinely-unaccounted items, one of them **CRITICAL and mechanically proven by execution**: `ConfidenceScorer::ic.actuals.count/head` have no registry row, and their omission rests on a stated reason (*"predictions + actuals stay in lockstep"*) that the persist path itself **falsifies**. A perfectly-correlated predictor (IC = 1.0000) reads **IC = −0.5238** after a warm restart plus 6 trades — and that IC drives an auto-kill capital control. Second: the ONE complement check that exists anywhere in this shard, cited by name in a registry comment and in a Stage-3 DESIGN_SPEC's "Canonical applications" table, **does not exist on disk**.

---

## 0. Method + corroboration

Every struct field set was derived **twice** — text read + clang `-fdump-record-layouts` — and the two agreeing is what proves no macro-injected members. Registry rows were extracted **mechanically** (comment-stripped X-macro body parse), never eyeballed.

| Struct | clang members | `sizeof` | Text agrees? |
|---|---|---|---|
| `tt::NodeContext<64>` | **49** | 7168 | yes (matches prior art I-4 exactly) |
| `tt::OrderManagerState<64>` | **51** | 260928 | yes |
| `Position<64>` | **10** | 128 | yes (9 registry-generated + `_pad_pos`) |
| `Portfolio<64>` | **4** | 2112 | yes |
| `ConfidenceScorer` | **7** top-level / **21** flattened leaves | 1792 | yes |
| `RegimeState<64>` | **9** | 48 | yes |
| `RegressionFeederX<64>` | **3** | 144 | yes |
| `RollingWindow<double,64>` | **4** (`count`/`head`/`window`/`samples`) | 528 | yes |

**Mechanical tools run** (per SUBAGENT_ARMING § 3), all RC captured directly (no pipe-swallow):

| Tool | RC | Verdict |
|---|---|---|
| `tools/node_persist_layout.py` | 0 | GREEN — 46 flattened wire rows match the frozen golden |
| `tools/check_meta_registry.py` | 0 | 68/68 registries enrolled; H15/H19 clean |
| `tools/check_struct_alignment.py` | 0 | GREEN; **only 2 in-tree byte-serialized types detected** — `Portfolio` is not one (see F-3) |
| `tools/check_identifier_retirement.py` | 0 | GREEN — 47 wire identifiers match the ledger |
| `tools/check_capital_adversarial_audit.py` | 0 | OK |

**Every guard in this shard is GREEN, and none of them can see F-1, F-2 or F-3.** That is the meta-pattern, confirmed.

---

## A. PER-REGISTRY VERDICT TABLE

| # | Registry | Kind | Generation direction | Authoritative domain (file:line) | Complement check exists? | Complement | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | `FOREACH_NODE_PERSIST_FIELD` `MemHeaders/NodeCtxPersistRegistry.hpp:67` | **COVERAGE** | struct→registry | `tt::NodeContext<F>` — `CoreFrameworks/ControllerEventLoop.hpp:315-614`, 49 members | **NO** | 22 fields (21 with a stated reason + `drift_history` with none) | prior art **CONFIRMED** — see § B.5 |
| 2 | `FOREACH_CONFIDENCE_PERSIST_FIELD` `ML_Headers/ConfidenceScore.hpp:1413` | **COVERAGE** | struct→registry | `ConfidenceScorer` — `ConfidenceScore.hpp:725-739`; flattened leaf domain = **21** | **NO** | **14 leaves**, incl. `ic.actuals.count` + `ic.actuals.head` | ⚠ **F-1 CRITICAL** |
| 3 | `FOREACH_REGIME_PERSIST_FIELD` `Strategies/RegimeDetector.hpp:638` | **COVERAGE** | struct→registry | `RegimeState<F>` — `RegimeDetector.hpp:584-599`, 9 fields | **NO** (count-lock `==7` only, `:684`) | **2** — `last_trending_score`, `last_volatile_score`, both with stated reason `:596` | **CLEAN** — prior art confirmed |
| 4 | `FOREACH_FEEDER_PERSIST_FIELD` `ML_Headers/LinearRegression3X.hpp:102` | **COVERAGE** | struct→registry | `RegressionFeederX<F>` — `LinearRegression3X.hpp:69-73`, 3 fields | **NO** (count-lock `==3`, `:141`) | **∅ — empty** | **CLEAN** — the only fully-covered registry in the shard |
| 5 | `FOREACH_POSITION_FIELD` `MemHeaders/PositionFieldRegistry.hpp:35` | **SOURCE-OF-TRUTH** | **registry→struct** (H17-shaped) | n/a — the registry *is* the source; `Position<F>` body is X-macro-only at `CoreFrameworks/Portfolio.hpp:67-68` | **N/A by construction** | 1 manual member `_pad_pos[7]` (`Portfolio.hpp:75`), deliberate H12 padding | **CLEAN** — do NOT report as a gap |
| 6 | `FOREACH_POSITION_FIELD_SKIP_PERSIST` `PositionFieldRegistry.hpp:77` | **EMPTY / DEAD** | none (no expansion site exists) | — | n/a | — | ⚠ **F-4 MED** — zero expansion sites |
| 7 | `FOREACH_OMS_FIELD` `MemHeaders/OmsFieldRegistry.hpp:227` | **COVERAGE** (scoped to *scalars*, `:21-22`) | struct→registry | `tt::OrderManagerState<F>` — `CoreFrameworks/OrderManager.hpp:295-700`, 51 members | **NO** (count-lock `>=30` `:409` + PERSIST `==10` `:433`) | 17 members; of the **scalars**, 3 fn pointers + 4 pads | ⚠ **F-3 HIGH** (`portfolio`) + **F-5 MED** (fn ptrs) |
| 8 | `FOREACH_OMS_PER_SLOT_FIELD` `OmsFieldRegistry.hpp:372` | **COVERAGE** | struct→registry | `\w+[MAX_PORTFOLIO_POSITIONS]` arrays on `OrderManagerState<F>` — **6** exist | **CLAIMED, ABSENT** | **1** — `last_exit_predicted_meta` (`OrderManager.hpp:524`), stated reason `OmsFieldRegistry.hpp:461-463` | **substantively CLEAN**, but ⚠ **F-2 HIGH** (phantom guard) |
| 9 | `FOREACH_OMS_META_SLOT` `MemHeaders/OmsExitPredictorMetaRegistry.hpp:88` | **SOURCE-OF-TRUTH** | registry→constants | the registry *defines* the byte encoding; no external set | **N/A** — no complement exists | 1 bit (bit 7), explicitly `reserved` `:98-99, :113` | **CLEAN** |

**Clean results, stated explicitly:** registries **3, 4, 5, 9** have no gap. #4 (`feeder`) is the only one with a genuinely empty complement; #5 and #9 are SOURCE-OF-TRUTH so no complement exists by construction; #3's 2-member complement is fully reasoned in code.

---

## B. THE UNACCOUNTED ITEMS, RANKED BY BLAST RADIUS

### ⚠ F-1 — CRITICAL — `ic.actuals.count` + `ic.actuals.head`: a stated-but-FALSE exclusion reason silently corrupts the ML risk-control input on every warm restart

**The gap.** `FOREACH_CONFIDENCE_PERSIST_FIELD` (`ML_Headers/ConfidenceScore.hpp:1413-1420`) has 7 rows. The flattened leaf domain of `ConfidenceScorer` is **21**. Among the 14 uncovered leaves, two are load-bearing and asymmetric:

```text
X(ic.predictions.samples, double, 64)   X(ic.actuals.samples, double, 64)
X(ic.predictions.count,   int,     1)   <-- ic.actuals.count   NO ROW
X(ic.predictions.head,    int,     1)   <-- ic.actuals.head    NO ROW
```

`RollingIC` is a pair of **independent** `RollingWindow` rings, each with its **own** `count`/`head`/`window` (`ConfidenceScore.hpp:202-205` + `:96-108`, clang-confirmed). One ring's cursor is restored; the other's is not.

**Why the audit trail terminates here (this is the important part).** The omission carries an explicit reason:

```text
//   ic.count       → ic.predictions.count (predictions + actuals stay in lockstep
//                    via RollingIC_Push; canonically read from predictions)
```
— `/home/caramel/code/FoxML_Trader_v2/ML_Headers/ConfidenceScore.hpp:1540-1541`

The lockstep premise is true of `RollingIC_Push` (`:277-280`) and true of `RollingIC_Compute`, which reads only `predictions.*` metadata (`:318-334`). **It is false across the persist boundary** — because the persist path is precisely the thing that sets one cursor without the other. A "deliberately-excluded WITH a stated reason" classification is *worse* than a missing one here: it is a green light that closes the question.

**Mechanism.** `EngineCommon_BootPerCore` → `ConfidenceScorer_Init` (`CoreFrameworks/EngineCommon.hpp:430`, via `EngineSharded/Run.hpp:1031`) runs **before** `ShardedSnapshot_Load` (`Run.hpp:1069`). Load commits exactly the 7 rows via `ConfidenceScorer_CommitPersistedFields` (`ConfidenceScore.hpp:1452-1462`, reached through `NPF_COMMIT_COMMIT_DELEGATE`, `NodeCtxPersistRegistry.hpp:209-210` + row `:108`). Post-commit: `predictions.head = H`, `actuals.head = 0`. Every subsequent `RollingIC_Push` writes `predictions.samples[H%W]` and `actuals.samples[0%W]` — a **permanent** offset of `H mod W`, since both advance by 1 forever.

**PROVEN BY EXECUTION** (compiled against the real headers, `-O0`, window=8):

```text
LIVE  after 20 pushes: pred.head=20 pred.cnt=8 | act.head=20 act.cnt=8 | IC=1.0000
RESTORED (post-commit):  pred.head=20 pred.cnt=8 | act.head=0  act.cnt=0 | IC=1.0000
LIVE     after 6 more: IC=1.0000  (expected 1.0000)
RESTORED after 6 more: IC=-0.5238  <-- pairing check
RESTORED act.head=6 vs pred.head=26  (offset=20)
RESTORED acts ring:  20 21 22 23 24 25 14 15
RESTORED preds ring: 24 25 18 19 20 21 22 23
```

Note the post-commit IC reads a **correct** 1.0000 — the corruption starts on the first post-restart push and never self-heals. Any test that loads and immediately asserts passes.

**Blast radius — this reaches a capital control, not just a display.** `ControllerEventLoop.hpp:1855-1916`:
- `:1864` `ConfidenceScorer_UpdateAndMark` → the corrupted push;
- `:1879-1880` `ic_now = ConfidenceScorer_ComputeICVariant(...)` → `:1881` `DriftHistory_Push` → `:1884` `DriftHistory_CheckBreach(..., drift_floor, ...)`;
- `:1906-1909` on breach with `drift_auto_kill`: **`NODE_STATE_FLAG_SET(KILL_TRIPPED)` + `node_ks_trips_total++`**.

So a **correctly-performing ML node is auto-killed** within `drift_window_seconds` of resuming from a snapshot. Independently, the confidence factor feeds ML sizing (`ControllerEventLoop.hpp:3006`, `ml_ctx.out_confidence_factor`), so entry sizing is corrupted even with `drift_floor = 0`.

**Trigger conditions (stated adversarially, not hidden):** `ctx.strategy_id == STRATEGY_ML` (`:1855`) · warm restart with `predictions.head % window != 0` (i.e. `(W−1)/W` of restarts) · ≥ `CONFIDENCE_MIN_SAMPLES = 5` (`ConfidenceScore.hpp:74`) for `Compute` to return non-zero · additionally `drift_floor > 0` + `drift_auto_kill` for the kill path specifically.

**Why every guard is blind:** the count-lock is `== 7` (`ConfidenceScore.hpp:1478`) — adding the 2 missing rows would *trip* it, which is correct behaviour, but it can never *demand* them. The 46-row layout golden and the whole-file byte golden both describe the emitted wire, which is by definition consistent with itself. The round-trip test **sets** `ic.actuals.head/count` (`tests/controller_test.cpp:6435-6436`, and with deliberately different values `6+c`/`11+c` at `:6309-6310`) but **asserts only `actuals.samples[1]`** (`:6587`) — it never checks the two fields, so it is silent on exactly the gap.

---

### ⚠ F-2 — HIGH — the shard's ONLY complement check is a phantom: cited by name in code and in a Stage-3 spec's canonical-applications table, absent from disk

`MemHeaders/OmsFieldRegistry.hpp:385-386` states:

```text
* NEW CI Check 8 enforces all `\w+[MAX_PORTFOLIO_POSITIONS]` arrays on OmsState are
* either enrolled here OR exempted per manual-fields-inventory-pattern.md Section C.
```

Three independent claims, **all three false at HEAD**:

1. **The tool does not exist.** `DESIGN_SPECS/framework-patterns/registry-coverage-ci-check-pattern.md:285` names it `tools/check_oms_per_slot_registry_integrity.py`, calls it "NEW at .F.4c.4", and `:321` lists it among "three canonical CI tools [that] exist at extraction time". `ls tools/check_oms_per_slot_registry_integrity.py` → **No such file**. No tool in `tools/` references `MAX_PORTFOLIO_POSITIONS`, `FOREACH_OMS_PER_SLOT_FIELD`, `FOREACH_OMS_FIELD`, `FOREACH_OMS_META_SLOT`, or `FOREACH_POSITION_FIELD` — verified by grep over the whole directory.
2. **The "Check 8" that does exist is a different check entirely.** `tools/check_per_node_registry_integrity.py:816` Check 8 is *cfg field categorization integrity*, and it is itself **PENDING** (`:834`: *"Check 8 PENDING … full impl deferred"*). Number collision.
3. **The exemption home is wrong and empty.** `DOCS/MANUAL_FIELDS_INVENTORY.md` Section C (`:74-86`) is the **Class-27 scalar-cfg-mirror** registry with **0 entries** — a different taxonomy. `last_exit_predicted_meta` has no row in any section. (The spec at `:287` actually says the exemption list lives "within the tool", contradicting the code comment — and the tool doesn't exist either way.)

The spec also cites `tools/check_per_core_registry_integrity.py` (`:263`, `:274`, `:298`) — also absent; the file is `check_per_node_registry_integrity.py` after the per-core→per-node rename.

**Substantively the registry is fine.** I computed the complement by hand: 6 arrays match `\w+[MAX_PORTFOLIO_POSITIONS]` on `OrderManagerState<64>` (clang-confirmed), 5 are enrolled, and the 1 that isn't — `last_exit_predicted_meta` (`OrderManager.hpp:524`) — has a real stated reason (dedicated `OMS_META_CLEAR` helper, `OmsFieldRegistry.hpp:461-463`, applied at `:806`). All three array constants are distinct *names* (`MAX_PORTFOLIO_POSITIONS`/`MAX_EXECUTION_NODES`/`MAX_INFLIGHT_ORDERS`, all `= 16` at `Limits.hpp:12/26/36`), so the textual regex is exact.

**Severity is HIGH because of what the false claim does to auditors, not to the binary.** This is the Class-51 shape one level up: not a vacuously-green guard, but a **guard that was never built while three documents assert it was**. Its whole function is to make a reader skip the complement computation — which is exactly the sweep this directive exists to run. It also silently breaks the spec's own § "Auto-write contract at ship close".

---

### ⚠ F-3 — HIGH — `Portfolio<F>`'s wire block is hand-written, in no registry, with **no layout guard at all**, over a 56-byte silent-insertion gap

`portfolio` is member #11 of `OrderManagerState<64>` and is **not** in `FOREACH_OMS_FIELD` (the registry's declared domain is "OMS-level scalar fields", `OmsFieldRegistry.hpp:21-22`). Its bytes are emitted by three hand-written `fwrite` calls outside every registry:

```cpp
if (fwrite(&state->oms->portfolio.active_bitmap, 2, 1, f) != 1) goto fail;
{ uint16_t pad = 0; if (fwrite(&pad, 2, 1, f) != 1) goto fail; }
if (fwrite(state->oms->portfolio.positions, sizeof(Position<F>), 16, f) != 16) goto fail;
```
— `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/ShardedSnapshotPersist.hpp:186-191` (read side `:350-352`, commit `:415-416`)

This is the **capital block** — all 16 positions, every `entry_price`/`quantity`/`entry_fee`/TP/SL.

**Coverage today is correct** (clang: `Portfolio<64>` = `active_bitmap` @0, `_pad0` @2, `_pad1` @4, `positions` @64; the two pads are pure padding). **The exposure is forward.** `positions` sits at offset **64**, not 8 — `Position<F>` is `alignas(64)`, so there is a **56-byte implicit alignment hole** between `_pad1` and `positions`. A new field dropped into that hole:

| Guard | Would it trip? | Why not |
|---|---|---|
| `static_assert(sizeof(Portfolio<...>))` | — | **Does not exist.** Broad grep over `CoreFrameworks`/`MemHeaders`/`tests`/`Backtest` returns nothing for `sizeof(Portfolio`/`offsetof(Portfolio` |
| `sizeof` change | **no** | field lands in the 56B hole; `sizeof` stays 2112 |
| whole-file byte golden (`tests/sharded_snapshot_v11_golden.hpp`, 9968 B) | **no** | the wire writes members individually — emitted bytes are unchanged. It proves the wire didn't move; it cannot prove a field reached it |
| `node_persist_layout.py` 46-row golden | **no** | per-node scope only; `Portfolio` isn't in it |
| any count-lock (`==29`/`==10`/`==9`/`==7`/`==3`) | **no** | none covers `Portfolio` |
| `check_struct_alignment.py` (c) size-pin coverage | **no** | ran GREEN at *"2 in-tree byte-serialized types"* — `Portfolio` is not detected, because the `fwrite` targets are `&portfolio.active_bitmap` and `portfolio.positions`, not `&portfolio` |
| `check_identifier_retirement.py` paired-bump | **no** | GREEN; wire layout genuinely didn't move |

Contrast `Position<F>`, which is fully pinned by hand — `static_assert(sizeof(Position<64>) == 128)` (`Portfolio.hpp:158`), `alignof == 64` (`:163`), and 9 per-field `offsetof` locks (`:166-182`). **`Portfolio`, its container and the actual wire unit, has none of that.** The `POSITION_PERSIST_BYTES` tripwire (`:192-200`) guards `Position`, not `Portfolio`.

**Blast radius:** a silently-unpersisted `Portfolio`-level field is the Class-58 founding shape aimed straight at position state — the `node_gross_wins` → `$0.00` failure, one level up in the containment tree.

---

### F-4 — MED — `FOREACH_POSITION_FIELD_SKIP_PERSIST` has **zero expansion sites**; a row added to it produces nothing

`PositionFieldRegistry.hpp:77` defines it empty; it is enrolled in the meta-registry (`MetaRegistry.hpp:98`). Grep over all source dirs finds **only three** occurrences: the definition, the meta-registry row, and a *comment* at `Portfolio.hpp:105`. Its `PERSIST_KIND_EMIT_*` dispatch (`PositionFieldRegistry.hpp:91-92`) likewise has **no consumer** — the note at `:82-87` says so, since `Portfolio_Save`/`_Load` were deleted at D-289.

Critically, the `Position<F>` body **does not expand it**: `Portfolio.hpp:77` is the comment *"SKIP_PERSIST fields would expand here. Empty today per C.5 revert."* — a comment, not a `FOREACH_POSITION_FIELD_SKIP_PERSIST(...)` call. So adding a row yields **no struct field, no compile error, no CI signal**.

This is honestly and thoroughly documented as future-extension infrastructure (`PositionFieldRegistry.hpp:60-72`, with a loud D-289 warning), so it is **not** a live hazard. It is MED because it is a registry whose first user gets silence, and because the documented tripwire for that user (`sizeof(Position) - POSITION_PERSIST_BYTES == 0`, `Portfolio.hpp:200`) **cannot fire on a row that never becomes a field**. The stated safety net is one step behind the actual failure mode.

---

### F-5 — MED — three scalar `OrderManagerState` fn pointers sit outside `FOREACH_OMS_FIELD` and are externally SET post-Init — the exact shape the registry's own FINDING A closed

`on_entry_fill_emit`, `on_exit_fill_emit`, `on_exit_calibration` (`OrderManager.hpp:683-685`) are plain scalars on OmsState — squarely inside `FOREACH_OMS_FIELD`'s declared domain ("OMS-level scalar fields") — with **no registry row and no exemption entry**. They are initialised only by C++ default member initialisers (`= &noop_fill_emit<F>`), i.e. outside all five AUTOPOPULATE layers (`OmsFieldRegistry.hpp:780-846`), and then **externally assigned after `OrderManager_Init` returns** at three sites:

- `CoreFrameworks/ControllerEventLoop.hpp:1497-1498`
- `CoreFrameworks/EngineSharded/Run.hpp:796-797`
- `CoreFrameworks/OrderManager.hpp:2022`

That is verbatim the anti-pattern the registry documents itself as having closed — **FINDING A** (`OmsFieldRegistry.hpp:78-83`): *"Pre: engine boot called `OMS_STATE_FLAG_SET(PARTIAL_EXIT_ENABLED)` externally after `OrderManager_Init` returned (Class-18 mirror at the external SET site). Post: row in registry."* Same shape, three instances, un-noted.

Consequence today is bounded: they are not persisted (correctly — function pointers), and `OMS_RESET_AUTOPOPULATE` (`:848-856`) leaves them alone, which is probably right across a paper-reset. The finding is the **discipline hole**, not a live bug.

**The other 14 uncovered `OrderManagerState` members are accounted for** and I state them explicitly so the complement is closed, not merely sampled: `_pad0`/`_pad1`/`_pad_lof[4]`/`_pad_osf[7]` (padding, `_pad_osf` documented at `OrderManager.hpp:552-558`); `orders[16]`, `result_queue`, `ws_result_queue`, `reconcile_queue`, `submit_queues[16]`, `event_log` (sub-structs/rings — outside the declared scalar domain; all initialised in AUTOPOPULATE Layers 2-5, `OmsFieldRegistry.hpp:795-845`); `last_exit_predicted_meta[16]` (per-slot registry's domain, exempt per F-2); `ezoo_refs[16]`/`node_cfg_refs[16]` (DMI `= {nullptr}`, `OrderManager.hpp:694-695`); `portfolio` (F-3).

---

### B.5 — Prior-art items: CONFIRMED, not refuted

| Prior-art claim | Verdict | Evidence |
|---|---|---|
| `NodeContext::drift_history` unaccounted | **CONFIRMED** | clang independently reproduces **49** members / `sizeof=7168`, `drift_history` among them; in none of `FOREACH_NODE_PERSIST_FIELD` / `FOREACH_NODE_CTX_FIELD` / `FOREACH_NODE_CTX_SUMMARY_FIELD` |
| `confidence` delegate reaches only 2 of 7 sub-fields | **CONFIRMED and SHARPENED** | 7 top-level → the registry touches only `ic` and `rmse`. But the load-bearing statement is at the **leaf** level: **7 of 21 flattened leaves**, and the specific missing pair is F-1 |
| `regime_state` has 2 of 9 off-wire with a stated reason | **CONFIRMED** | `RegimeDetector.hpp:596` — *"Never persisted (snapshot re-derives on warmup)"*; count-lock `:684` |
| `pnl_feeder` fully covered | **CONFIRMED** | 3 clang members = 3 rows; complement empty |

---

## C. HAZARDS

- **HAZ-1 (a stated reason can be the *most* dangerous kind).** F-1's exclusion has a citation, so the prior pass's own heuristic — *"deliberately-excluded-with-NO-stated-reason is the predictive smell"* — **classifies it as safe**. The smell that actually found it was **intra-struct asymmetry**: one of two structurally identical sibling rings persisted its cursor, the other didn't. Any partition guard built on "does it have a reason?" would have shipped F-1. Recommend the guard also flag **sibling-asymmetric coverage within one delegate**.
- **HAZ-2 (delegate count-locks are structurally as blind as the parent was).** `regime ==7` / `feeder ==3` / `confidence ==7` (`NodeCtxPersistRegistry.hpp:119-120`) are **count**-locks. F-1 lives at the second level and all three are green. The `==29` parent lock explicitly documents its own vacuity for count-neutral swaps (`:113-115`) — the delegate locks have the *same* vacuity and do **not** document it.
- **HAZ-3 (the audit-trail terminator).** F-2 means a reader of `OmsFieldRegistry.hpp:385-386` is told the complement is mechanically enforced. Three separate documents agree. Nothing in the repo contradicts them except the filesystem.
- **HAZ-4 (both goldens are wire-internal).** The byte golden and the 46-row name golden both describe *emitted bytes*. Neither can express "a field exists and is not emitted". Every finding in this shard lives in that blind spot — which is precisely why the complement must be computed from the **struct**, and why the clang dump (not a text regex) is the right source.
- **HAZ-5 (containment-tree gap).** `Position` is exhaustively layout-locked; its container `Portfolio` has zero locks (F-3). Guards were applied at the element and skipped at the aggregate. Worth checking the same shape on the other aggregates in the wire path.
- **HAZ-6 (stale behaviour comment, SUBAGENT_ARMING § 2.5).** `CoreFrameworks/OrderManager.hpp:751` asserts *"Persistence: OMS state is NOT byte-persisted."* At HEAD, 10 `FOREACH_OMS_FIELD` rows are `fwrite`-persisted (`OmsFieldRegistry.hpp:255-269`, pin `:433`) and the whole `Portfolio` block is dumped. **Code is truth.** Suggested wording: *"Persistence: 10 PERSIST-kind rows + the Portfolio block are byte-persisted via ShardedSnapshotPersist; the rest of OmsState is not. OrderEventLog persists separately as records."* This comment sits ~50 lines above the struct a persist auditor reads first.

---

## D. SPOTS MOST WORTH AN ADVERSARIAL REFUTE (for the paired a-class)

1. **F-1 — attack the reachability, not the mechanism.** The desync is proven by execution, so don't re-litigate the arithmetic. Attack the *path*: is `ShardedSnapshot_Load` reachable in any configuration where a node is `STRATEGY_ML` **and** the loaded `ic.predictions.count >= 5`? Does any boot path re-run `ConfidenceScorer_Init` **after** `Run.hpp:1069`? Is there a warmup gate that discards the restored IC ring before the first post-restart `Update`? If any holds, F-1 drops from CRITICAL to latent. **I found none, but I did not exhaustively walk every boot branch in `Run.hpp`** — that is the weakest link in my chain and the highest-value refute target.
2. **F-1's severity ceiling — argue it *self-limits*.** Once IC goes garbage and `drift_auto_kill` fires, the node stops trading, so no further `ic` pushes occur and no capital is lost to bad sizing. Under that reading the harm is "spurious auto-kill + a corrupted forensic record", not "trades on a corrupted signal". **Counter-refute:** with `drift_floor = 0` (default?) there is no kill at all, and the corrupted confidence factor feeds sizing (`ControllerEventLoop.hpp:3006`) indefinitely with nothing to stop it — arguably *worse*. Someone should settle which default configuration is live.
3. **F-1's fix shape is not obvious — pressure it.** Adding 2 rows changes the wire → v11→v12 + golden regen/rename in the same commit (H21 paired-bump, `NodeCtxPersistRegistry.hpp:116-118`). But a **zero-wire-cost** alternative exists: have `ConfidenceScorer_CommitPersistedFields` mirror `predictions.count/head` into `actuals.count/head` in its tail — precisely where `RecomputeRunningSums` already lives (`ConfidenceScore.hpp:1461`), and precisely the "derived state restored at commit" precedent (`:1483-1486`). That needs **no version bump**. Refute it: is mirroring *correct*, or does it paper over a real invariant that ought to be expressed as `RollingIC` owning one shared cursor? **I recommend the mirror-in-commit-tail** on the D-302/REC-A precedent, but I hold it loosely — the deeper fix (hoist `count`/`head`/`window` out of `RollingWindow` up into `RollingIC`) removes the whole failure class and is the structural-fix-over-patch answer. That is a design call for Caramel, not for me.
4. **F-3 — attack the forward-risk premise.** I claim a new `Portfolio` field would be silently unpersisted. Refute by finding *any* guard I missed: a `check_cache_layout.py` `[STRUCT]` tag entry for `Portfolio`, a `[SIZE]` `[DERIVED]` block that CI validates (`Portfolio.hpp:229-237` has `[SIZE]_[2112B]` — **is that tool-checked or decorative?** I did not run `check_cache_layout.py` against it; that is a genuine hole in my pass), or a test asserting `sizeof(Portfolio)`. If the `[DERIVED]` block is CI-enforced, F-3 drops to LOW.
5. **F-2 — check whether the tool ever existed and was deleted.** I checked HEAD only. If `git log --diff-filter=D` shows `check_oms_per_slot_registry_integrity.py` was deleted, this is a *retirement-without-ledger* finding (H21-adjacent, and `check_identifier_retirement.py` wouldn't see a tool file). If it never existed, it is a spec that documented an intention as a shipped fact. **Different findings, different fixes** — worth 30 seconds of `git log`.
6. **The scalar-domain boundary in F-5.** I accepted `OmsFieldRegistry.hpp:21-22`'s "OMS-level scalar fields" as the declared domain, which is what lets me exempt `orders`/`portfolio`/the rings from `FOREACH_OMS_FIELD` proper. Refute by arguing the domain is really "everything on OmsState" — in which case F-3 stops being a seam finding and becomes a straight **missing row**, and the complement grows from 3 scalars to 17 members.
7. **My `ConfidenceScorer` leaf count of 21.** I flattened by hand from the clang dumps (7 top-level → `ic`{2×4} + `rmse`{4+1} + `freshness`{2} + `capacity`{3} + 3 scalars). Recount it. If the flattening is wrong, the "7 of 21" framing in the verdict table is wrong even though F-1 itself stands on its own two named fields.
8. **Generality of the clang/text agreement.** Per `feedback_dont_generalize_substrate_before_input_space_known`: the agreement is a fact about *these eight structs at `7240f3d`*, not a licence to trust text extraction on siblings a future guard might cover. `OrderManagerState` in particular is 51 members across 260 KB with `alignas`, atomics, templates and fn-pointer types — run the same census before claiming a text parser suffices.

---

## E. OPEN QUESTIONS (for Caramel)

- **OQ-1 (F-1, blocking):** fix by (a) mirroring `predictions.count/head` → `actuals.*` in `ConfidenceScorer_CommitPersistedFields`' tail (**no version bump**, sister to the existing `RecomputeRunningSums` embed), (b) adding 2 registry rows (**forces v11→v12** + golden regen/rename in the same commit), or (c) restructuring `RollingIC` to own a single shared cursor (**removes the class**; touches `Push`/`Compute`/`Init` and the wire). (a) is the smallest correct fix; (c) is the structural one.
- **OQ-2 (F-2):** build `tools/check_oms_per_slot_registry_integrity.py` for real, or retract the three claims (`OmsFieldRegistry.hpp:385-386`, spec `:285`, spec `:321`)? Either is defensible; the current state — claimed-and-absent — is the only one that is not.
- **OQ-3 (F-3):** add `static_assert(sizeof(Portfolio<64>) == 2112)` + `offsetof(positions) == 64` now (2 lines, closes the 56-byte hole), or fold it into a broader aggregate-layout-lock sweep?
- **OQ-4 (methodology, and the one I'd most want answered):** should the partition guard's exempt-side carry a **reason column** *and* a **sibling-symmetry check**? The prior pass concluded a reason column would have caught `drift_history`. **F-1 proves a reason column alone is not sufficient — it had a reason, and the reason was false.** The discriminator that actually worked was structural asymmetry between sibling fields of the same type.
- **OQ-5 (F-4):** delete `FOREACH_POSITION_FIELD_SKIP_PERSIST` + its dead `PERSIST_KIND_EMIT_*` dispatch per the backwards-compat-not-default gradient, or wire the expansion site into `Position<F>` so the infrastructure actually works when its first user arrives?

---

**Key files:** `/home/caramel/code/FoxML_Trader_v2/ML_Headers/ConfidenceScore.hpp` · `/home/caramel/code/FoxML_Trader_v2/MemHeaders/NodeCtxPersistRegistry.hpp` · `/home/caramel/code/FoxML_Trader_v2/MemHeaders/OmsFieldRegistry.hpp` · `/home/caramel/code/FoxML_Trader_v2/MemHeaders/OmsExitPredictorMetaRegistry.hpp` · `/home/caramel/code/FoxML_Trader_v2/MemHeaders/PositionFieldRegistry.hpp` · `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/Portfolio.hpp` · `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/OrderManager.hpp` · `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/ShardedSnapshotPersist.hpp` · `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/ControllerEventLoop.hpp` · `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/EngineSharded/Run.hpp` · `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/EngineCommon.hpp` · `/home/caramel/code/FoxML_Trader_v2/Strategies/RegimeDetector.hpp` · `/home/caramel/code/FoxML_Trader_v2/ML_Headers/LinearRegression3X.hpp` · `/home/caramel/code/FoxML_Trader_v2/Limits.hpp` · `/home/caramel/code/FoxML_Trader_v2/tests/controller_test.cpp` · `/home/caramel/code/FoxML_Trader_v2/tests/sharded_snapshot_v11_golden.hpp` · `/home/caramel/code/FoxML_Trader_v2/DOCS/MANUAL_FIELDS_INVENTORY.md` · `/home/caramel/code/tick-trader-percore-workspace/DESIGN_SPECS/framework-patterns/registry-coverage-ci-check-pattern.md` · `/home/caramel/code/tick-trader-percore-workspace/DESIGN_SPECS/framework-patterns/manual-fields-inventory-pattern.md` · `/home/caramel/code/FoxML_Trader_v2/plans/v5.15-live-readiness/reports/2026-08-15-ui-consolidation/i-class-nodecontext-partition.md`
