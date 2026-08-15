---
type: agent-report
status: FROZEN — verbatim agent output, saved at receipt
directive: P-3 — NodeContext persist-exemption VERIFICATION, group 3/3: the three unpersisted sub-structs (turnover / drift_history / sp_telemetry)
agent_class: i-class
delivered: 2026-08-15
ground: engine HEAD 564f099, branch feat/v5.15-live-readiness
headline: All three SAFE-UNPERSISTED with cited mechanisms — but the verification found F-1, a LIVE capital-control defect on the same struct. MASK_DRIFT_KILL_TRIPPED is set at ControllerEventLoop.hpp:1909 and cleared by NOTHING except DriftHistory_Init's memset, so an operator who clears a drift kill from the GUI resumes the node with its drift auto-kill PERMANENTLY DISARMED for the rest of the process. drift_history being unpersisted is currently the ONLY mechanism that re-arms it — which INVERTS operator option (b) - persisting the flag byte would make the disarm permanent across restarts too. Also proposes option (d), a zero-wire honest-abstain that costs 0 bytes and no H21 event because CheckBreach already returns the discriminator and the caller throws it away
operator_decision_owed: F-1 (clear drift_state_flags at Async.hpp:393 and inside NODE_CTX_RESET_AUTOPOPULATE — a hard precondition before (b) or (c) could ever be safe) · the drift_history option fork, where P-3 recommends (d)+(a) and REJECTS (b) and (c) with cost math · B-1 (confidence_ic_floor is read GLOBAL at a per-node consumer, the H22 A1 shape, and Check 10's hand-list covers 4 of 88 per-node fields — the guard-coverage gap is arguably the bigger finding) · B-2 (the whole RollingTurnover feature is dead below the snapshot; render it or delete it)
sister_reports: P1-handles-lifecycle.md · P2-eval-transient-display.md
---

All probes cleaned; `git status` byte-identical to the start (`IDENTICAL_RC=0`). Here is the report.

---

# P-3 — NodeContext persist-exemption verification, group 3/3: `turnover` · `drift_history` · `sp_telemetry`

**Engine** `/home/caramel/code/FoxML_Trader_v2` · branch `feat/v5.15-live-readiness` · HEAD `564f099` (verified) · read-only, `git status` restored byte-identical.
**Method:** `/dependency-chain-trace` SKILL.md walked steps 1–7 (incl. its mandatory step-7 `gen_code_map` enumerator); mechanical tools run over grep per SUBAGENT_ARMING §3; two compiled probes built in `build/_p3probe{,2}/`, run, and removed.

---

## 1. Verdict table

| # | Field | Type / size | Accumulator or derived? | Feeds an execution/risk/capital decision? | Verdict |
|---|---|---|---|---|---|
| 1 | `turnover` | `RollingTurnover`, **280 B** (not 336 — see §2.1) | **Accumulator** (256-slot mask ring) | **NO** — and no *display* consumer either: the chain is fully dead | **SAFE-UNPERSISTED** (vacuously — nothing reads the output at all) |
| 2 | `drift_history` | `DriftHistory`, **4160 B** | **Accumulator** (256-slot AoS `(ic,ts)` ring) | **YES** — `NODE_STATE_FLAG_SET(…, KILL_TRIPPED)` at `ControllerEventLoop.hpp:1907` | **SAFE-UNPERSISTED**, mechanism cited (§3) — *but* it carries a separate **UNSAFE** defect on the same bitmap (F-1), and options (b)/(c) would make that defect permanent |
| 3 | `sp_telemetry` | `tt::SlowPathTelemetry`, **64 B** | **Derived / process-lifetime live state** (2 monotonic counters + a wall stamp + a live thread state) | **NO** — display-only, one reader | **SAFE-UNPERSISTED** — and persisting it would be *actively harmful* (§2.3) |

**Mechanical confirmation that none of the three is on the wire:** `python3 tools/node_persist_layout.py` → `RC=0`, *"GREEN — 46 flattened wire rows match the frozen golden"*; `grep -niE "turnover|drift|telemetry" tools/goldens/node_persist_layout.txt` → `RC=1` (no match). Independently, `CoreFrameworks/ShardedSnapshotPersist.hpp` contains **zero** occurrences of any of the three identifiers (grep `RC=1` over the 621-line file).

---

## 2. Evidence per field

### 2.0 Layout (probed, not read off the `[DERIVED]` tags)

Probe output (`offsetof`/`sizeof`, g++ `-O2 -std=gnu++17`, x86-64), cross-checked against `./tools/foxtag/foxtag layout main.cpp …` — both agree:

```
sizeof(NodeContext<64>)  = 7168
turnover      @ 2608   sizeof(RollingTurnover)   =  280
drift_history @ 2944   sizeof(DriftHistory)      = 4160
sp_telemetry  @ 7104   sizeof(SlowPathTelemetry) =   64
SPAN turnover..end = 4560 bytes  (63.6% of NodeContext)
```

**Correction to the brief:** the `~336 B` figure for `turnover` is the *offset span* 2608→2944; the struct is **280 B**. The extra 56 B is alignment pad ahead of `alignas(64) DriftHistory`. Total unpersisted tail = **4560 B / 7168 = 63.6%**, and `sp_telemetry` is the final member (7104 + 64 = 7168 exactly).

### 2.1 `turnover` — `RollingTurnover`

**Members** (`/home/caramel/code/FoxML_Trader_v2/ML_Headers/RollingTurnover.hpp:47-54`): `topk_mask_ring[256]` (uint8), `head`, `count`, `window`, `topk`, `last_turnover`. The ring is a **true accumulator** — a symmetric-difference history that cannot be rebuilt.

**Write sites**
| file:line | fn | thread / cadence |
|---|---|---|
| `MemHeaders/NodeCtxInitRegistry.hpp:313` | `NODE_CTX_INIT_AUTOPOPULATE` Layer 2 | boot, once — `RollingTurnover_Init(&…turnover, 100, 3)` |
| `CoreFrameworks/EngineCommon.hpp:449-451` | `EngineCommon_BootPerCore` step 5j | boot, once — **re-Init** (memset) from cfg |
| `Strategies/StrategyParameters.hpp:1265-1266` | `ML_BuildParameters` ensemble-weighted branch | slow-path, per cycle (ML + `primary_count>0` only) |

Pointer wire: `CoreFrameworks/ControllerEventLoop.hpp:3012-3013` (`ml_ctx.turnover_state` / `turnover_topk`).

**Read sites — exactly one:** `CoreFrameworks/ShardedSnapshot.hpp:622-623` → `snap->per_node[i].ml_portfolio_turnover = RollingTurnover_Compute(&state->nodes[i].turnover)`.

**Downstream enumeration (not a sample):** whole-tree grep for `ml_portfolio_turnover` returns **6 hits — 5 comments/1 declaration/1 write, and zero reads**:
`ControllerConfig.hpp:1303` (comment) · `ControllerEventLoop.hpp:552` (comment) · `ShardedSnapshot.hpp:622` (the write) · `EngineTUI.hpp:1208` (the `PerNodeSnap` declaration) · `RollingTurnover.hpp:21` (comment) · `StrategyParameters.hpp:204` (comment). A case-insensitive `turnover` sweep of `GUI/` returns **nothing**.

⇒ **The entire `RollingTurnover` chain terminates at a snapshot field nothing reads.** Persisting it would preserve a value with no consumer. See B-2 for the cost this is buying today.

### 2.2 `drift_history` — `DriftHistory`

**Members** (`/home/caramel/code/FoxML_Trader_v2/ML_Headers/ConfidenceScore.hpp:1297-1307`): HOT `count`, `head`, `drift_state_flags` (`MASK_DRIFT_BREACHED` bit0 / `MASK_DRIFT_KILL_TRIPPED` bit1, `:1234-1235`); COLD `samples[256]` of `DriftSample{double ic; uint64_t ts}`. `samples`/`count`/`head` = **accumulator**; `drift_state_flags` = **latched state derived from the accumulator** (and, for bit 1, *never cleared* — see F-1).

**Write sites**
| file:line | fn | thread / cadence |
|---|---|---|
| `MemHeaders/NodeCtxInitRegistry.hpp:312` | `NODE_CTX_INIT_AUTOPOPULATE` Layer 2 | boot — `DriftHistory_Init` = `memset` (`ConfidenceScore.hpp:1367`) |
| `CoreFrameworks/ControllerEventLoop.hpp:1881` | `EventLoop_DrainPostFillOneCore` | **drainer, once per CLOSED leg-A trade on an ML node** |
| `:1897` / `:1919` | same | `BITMAP_SET` / `BITMAP_CLR` of `MASK_DRIFT_BREACHED` |
| `:1909` | same | `BITMAP_SET` of `MASK_DRIFT_KILL_TRIPPED` — **set-only, see F-1** |

Push guard chain: `:1842 if (is_leg_a)` → `:1855 if (ctx.strategy_id == STRATEGY_ML)` → `:1872 if (drift_floor > 0.0)` → `:1881`.

**Read sites — full enumeration**
| file:line | consumer | class |
|---|---|---|
| `ControllerEventLoop.hpp:1884-1887` | `DriftHistory_CheckBreach` | **CAPITAL** — gates the branch below |
| `ControllerEventLoop.hpp:1893` | `BITMAP_IS_SET(BREACHED)` | edge-trigger for the CRITICAL log |
| **`ControllerEventLoop.hpp:1906-1909`** | `BITMAP_IS_SET(KILL_TRIPPED)` guard → **`NODE_STATE_FLAG_SET(state->nodes[node_id], KILL_TRIPPED)` at `:1907`** + `node_ks_trips_total++` at `:1908` | **CAPITAL — the per-node kill switch** |
| `ControllerEventLoop.hpp:1917` | `BITMAP_IS_SET(BREACHED)` | recovery edge |
| `ShardedSnapshot.hpp:525 / 528` | `→ STATE_FLAG DRIFT_BREACHED / DRIFT_KILL_TRIPPED` | display (`GUI/MLStatusPanel.hpp:315-324`) |
| `ShardedSnapshot.hpp:531 / 538` | `drift_n_samples` / `drift_avg_ic` | display |

**Config reality (probed):** `confidence_ic_floor = 0.02` (>0 ⇒ **the detector is ON by default**), `confidence_ic_floor_window = 86400 s`, `auto_kill_on_drift = 0` (**the kill is opt-in**). Sources: `ControllerConfig.hpp:2121/2122/2123`; bound at `EngineSharded/SlowPath.hpp:74-76`.

### 2.3 `sp_telemetry` — `tt::SlowPathTelemetry`

**Members** (`/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/ControllerEventLoop.hpp:252-257`): `atomic<uint64_t> last_tick_us`, `cycles_total`, `yield_count`, `atomic<uint8_t> state`.

**Write sites:** `MemHeaders/NodeCtxInitRegistry.hpp:317-320` (boot) · `CoreFrameworks/EngineCommon.hpp:825/827` (slow path, per cycle) · `CoreFrameworks/EngineSharded/Run.hpp:1747/1748/1755/1756/1763/1764/1769` (cadence yield / park / pause).

**Read sites — exactly one:** `DataStream/EngineTUI.hpp:2059-2066` → `PerNodeSnap.sp_{last_tick_us,cycles_total,yield_count,state}`, rendered at `GUI/DashboardPanels.hpp:2521-2548` (Engine Topology panel). Nothing else.

**Why persisting would be harmful, not merely wasteful:** `cycles_total`/`yield_count` are *process-lifetime* counters and `state` is a *live* thread state. Restoring `state = 3` would render a running node as `PAUSED`; restoring `last_tick_us` would make the panel's Δ read "this node hasn't cycled in N hours" on a node that just booted (`DashboardPanels.hpp:2531-2543` computes `now_us - sp_last_tick_us`). The `alignas(64)` + `sizeof==64` static_asserts (`:258-262`) and the `offsetof % 64 == 0` cluster anchor (`:644`) exist for cross-thread isolation, not persistence.

---

## 3. The `drift_history` operator decision — the facts each option turns on

### 3.1 Ring capacity and refill time

- Capacity **256** (`DRIFT_HISTORY_CAPACITY`, `ConfidenceScore.hpp:1227`).
- **Push cadence is one sample per CLOSED leg-A ML trade** — not per tick, not per slow-path cycle (guard chain at `ControllerEventLoop.hpp:1842/1855/1872/1881`). So a *full* ring = **256 closed trades**.
- **But the decision threshold is 5, not 256.** `ConfidenceScore.hpp:1397` (`if (dh->count < 5) return 0`) and `:1410` (`if (n < 5) return 0`). Probe D confirmed: against a maximally-broken predictor, **the first breach is possible at sample #5 ⇒ the blind window is exactly 4 closed trades.**
- At the 24 h default window, the *time* filter binds before the 256-sample cap unless a node closes >256 trades/day.

### 3.2 The crux: silent all-clear, or honest abstain?

**Structurally, at the call site, it is a SILENT ALL-CLEAR.** `DriftHistory_CheckBreach` returns the identical `int 0` for "healthy" and for "insufficient data" — the two `return 0` statements at `ConfidenceScore.hpp:1397` and `:1410`. Probe B, fresh ring:

```
count=0 (fresh) -> breach=0 avg=0.0000 n=0   NO-BREACH (indistinguishable from healthy)
```

The existing test *codifies* the conflation: `tests/controller_test.cpp:16859` asserts `b == 0` under the label *"CheckBreach < 5 samples returns 0 (insufficient)"* — bytewise the same assertion as the healthy case at `:16883`.

The consumer at `ControllerEventLoop.hpp:1884-1923` branches **only** on `breach`. `n_samples` is captured at `:1883` and used **only** inside the log format string at `:1905`.

**The load-bearing corollary:** the abstain signal already exists and is discarded. `out_samples` is a *reliable* discriminator — it is written `0` at `:1395-1396` and left `0` on both insufficient returns, and set to `n (≥5)` only at `:1413`. So `*out_samples == 0` ⟺ *insufficient data*, exactly. Turning the all-clear into an abstain costs **zero wire bytes** and ~3 lines at one call site.

### 3.3 Why the all-clear is nonetheless *bounded* — four mechanisms, each cited

1. **The capital control's OUTPUT is persisted even though its INPUT is not.** `node_kill_tripped` rides the wire as golden row `020|node_kill_tripped|uint8_t|BIT:COMMIT|KILL_TRIPPED`. A node already drift-killed **stays killed** across a restart.
2. **With auto-kill on, breach ⇒ kill is same-call** (`:1893` → `:1906-1909`). There is no durable "breaching but not yet killed" state for a restart to lose.
3. **The detector's INPUT is warm.** `ic_now` at `:1879` comes from `ConfidenceScorer_ComputeICVariant` over `RollingIC`, which **is** persisted — golden rows `039`–`042` (`ic.predictions.samples`, `ic.actuals.samples`, `ic.predictions.count/head`) — and whose lockstep is restored at `ConfidenceScore.hpp:1485` (the D-421 fix). So the **first** post-restart drift sample carries the full pre-restart IC.
4. **The verdict is a mean, so halving the sample count doesn't move it.** Probe C, same stationary IC:
   ```
   continuous: breach=1 avg=-0.3000 n=40 count=40
   restarted : breach=1 avg=-0.3000 n=20 count=20   -> verdict-equal? YES
   ```

**Answer to "what observably differs between a continuous node at N ticks and one restarted at N/2":** for the first **4 closed ML trades** after resume, `DriftHistory_CheckBreach` returns 0 regardless of truth. From trade 5 onward the verdict converges to the continuous node's, because the underlying IC statistic was never lost. During the blind window the consumers are: the CRITICAL drift log (`:1900`), the GUI `DRIFT_BREACHED` badge (`MLStatusPanel.hpp:315`), and — **only when `auto_kill_on_drift=1`** — the auto-kill at `:1907`. Under the shipping default (`auto_kill_on_drift = 0`, `ControllerConfig.hpp:2123`) the consequence is 4 trades of a missing log line and badge.

### 3.4 F-1 — the finding that decides options (b) and (c) — **UNSAFE, MED (HIGH if auto-kill is enabled)**

`MASK_DRIFT_KILL_TRIPPED` is **SET at `ControllerEventLoop.hpp:1909` and cleared nowhere but `DriftHistory_Init`'s `memset`** (`ConfidenceScore.hpp:1367`). Exhaustive grep of `drift_state_flags` across all `.hpp`/`.cpp` returns 18 sites; the single `BITMAP_CLR` is `:1919` and it clears **`MASK_DRIFT_BREACHED` only**.

Neither reset path clears it:
- Operator manual kill reset — `CoreFrameworks/EngineSharded/Async.hpp:391-397` clears `NODE_STATE_FLAG KILL_TRIPPED` + `node_peak_balance` + `node_dd_pct`, and nothing else.
- Paper reset — `NODE_CTX_RESET_AUTOPOPULATE` (`MemHeaders/NodeCtxInitRegistry.hpp:327-337`) walks the `RST` subset + clears `KILL_TRIPPED` + `partner_pending_bitmap`. `drift_history` is not a row in `FOREACH_NODE_CTX_FIELD` (`:100-145`), so the walk cannot reach it.

Demonstrated end-to-end (probe `p3b`, real `EventLoopState` + the real macro):

```
PATH 1: operator MANUAL kill reset (Async.hpp:393-395)
  node KILL_TRIPPED=0  (node resumes trading)
  drift flags=0x03  MASK_DRIFT_KILL_TRIPPED=1  <-- the AUTO-KILL RE-ARM BIT
  => can drift auto-kill fire again? NO (guard at :1906 is now permanently false)

PATH 2: PAPER RESET (NODE_CTX_RESET_AUTOPOPULATE)
  node KILL_TRIPPED=0  ks_trips=0  entries=0
  drift : count=40 flags=0x03 KILL_TRIPPED_bit=1   <-- SURVIVES the reset
  turnover: count=10 last=0.1667                   <-- SURVIVES
  sp_telem: cycles_total=123456                    <-- SURVIVES

PATH 3: WARM RESTART
  drift : count=0 flags=0x00 ; turnover count=0 ; sp cycles=0
  => drift auto-kill RE-ARMED by the restart
```

**⇒ Today, `drift_history` being unpersisted is the *only* mechanism in the codebase that re-arms the drift auto-kill.** An operator who clears a drift kill from the GUI resumes the node with its drift auto-kill permanently disarmed for the rest of the process.

**This inverts option (b).** Persisting `drift_state_flags` — the natural reading of "a single byte of summary state" — would convert a per-process one-shot into a **forever** one-shot. Option (c) inherits the same. Either must be preceded by adding a `drift_state_flags` clear at `Async.hpp:393` and inside `NODE_CTX_RESET_AUTOPOPULATE`.

Secondary, LOW: after a *restart*, the bit is 0, so a re-trip on the same underlying drift increments `node_ks_trips_total` again (`:1908`) — a forensic double-count.

### 3.5 Does `TECH_DEBT-229`'s view survive contact?

`/home/caramel/code/tick-trader-percore-workspace/DOCS/tech-debt/open.md:3430-3435`.

- **The memory half survives exactly.** 4160 B/node confirmed by two independent tools; 16 nodes = 66.5 KB; the 256/4096-node scale-forward math holds unchanged.
- **The "O(1)-computable" half is strengthened.** At one push per closed trade this is a very low-rate series; an EWMA at ~16–24 B is more than adequate for the *decision* (a 5-sample-minimum windowed mean).
- **One correction.** -229 states the sliding-time-window average *"needs raw `(ic,ts)` samples (can't summarize a moving time-window)"*. True for an exact windowed mean over arbitrary boundaries — but the decision needs only *≥5 in-window samples and their mean*, which a coarse bucketed ring (e.g. 24 hourly `{sum,count}` buckets ≈ 400 B) reproduces at ~10× reduction **without** the EWMA behaviour change -229 correctly flags as needing re-validation. That's a third design point the entry doesn't list.
- **One divergence to surface.** -229 closes with *"NOT persisted regardless (D-297/D3 = persist the kill FLAG only, not the ring)."* The flag that **is** persisted is `node_state_flags.KILL_TRIPPED` (golden row 020) — a **different bit** from `drift_state_flags.MASK_DRIFT_KILL_TRIPPED`. So D-297/D3's stated intent is half-implemented: the kill persists, its drift *attribution and re-arm* bit does not. That divergence is precisely what F-1 exploits, and it is why "persist the flag" needs disambiguating before it is actioned.
- **Location cites are stale.** -229 gives `ConfidenceScore.hpp:882` / `:930` / `:855-953`; at HEAD `564f099` the struct is at `:1297` and `CheckBreach` at `:1392`.

---

## 4. Option matrix for `drift_history` (with the novel alternative)

Per-node wire is **1944 B** at snapshot v11 (`MemHeaders/NodeCtxPersistRegistry.hpp:46/128`); `SHARDED_SNAPSHOT_VERSION = 11u` (`CoreFrameworks/ShardedSnapshotPersist.hpp:114`).

| Option | Wire cost | Fixes | Breaks / risk | Call |
|---|---|---|---|---|
| **(a)** document as deliberately unpersisted | 0 B | records the reason; no H21 event | leaves the 4-trade all-clear *implicit*; leaves F-1 open | **partial** — necessary, not sufficient |
| **(b)** persist 1 byte of summary state (`drift_state_flags`) | +1 B/node + pad → **v12 bump + golden regen** | keeps drift *attribution* across restart | **makes F-1 permanent across restarts** (§3.4); also persists a latch whose generating ring is absent — structurally the D-421 "cursor without its ring" shape | **reject as specified** |
| **(c)** persist the full ring | +4160 B/node ⇒ per-node wire **1944 → 6104 B (3.1×)**; 16 nodes 31 KB → 98 KB; v12 bump + golden regen | removes the 4-trade window | 4 KB/node of wire to buy 4 trades on a detector whose input is already warm and whose kill decision already persists; inherits F-1 permanently | **reject** — cost/benefit not close |
| **(d) NOVEL — zero-wire honest abstain** (`feedback_proactive_novel_alternative_consideration`) | **0 B, no H21 event** | Converts the silent all-clear into a *visible abstain*: consume the already-returned `n_samples` at `ControllerEventLoop.hpp:1883` and surface a `DRIFT_WARMING (n/5)` state distinct from no-breach — one `FOREACH_PER_NODE_STATE_FLAG` row (`MemHeaders/PerNodeStateFlagsRegistry.hpp:102-105` is the sibling pattern) + a `MLStatusPanel.hpp` string | none material — the discriminator is already computed and thrown away; it makes the degradation *legible* rather than pretending it isn't there | **RECOMMENDED** |
| **(e)** NOVEL sister — commit-time SEED (apply the D-421 `RollingIC_RestoreLockstep` derive-at-commit pattern) | 0 B | push the already-restored IC into the fresh ring at load-commit | needs **5** seeds to close the window ⇒ 5 fabricated samples; corrupts `drift_avg_ic` / `drift_n_samples` display (`ShardedSnapshot.hpp:531/538`) | **reject** — lies to the display to save 4 trades |

### Recommendation

1. **Adopt (d)** — the operator's own framing ("abstain is merely degraded; all-clear is a failure mode") is achievable at **zero wire cost and zero H21 cost**, because `CheckBreach` already returns the discriminator and the caller already ignores it. This is the highest-leverage row on the table.
2. **Close F-1 first, independently of any persist decision** — add the `drift_state_flags` clear at `Async.hpp:393` (manual reset) and inside `NODE_CTX_RESET_AUTOPOPULATE`. It is a live capital-control disarm today, and it is a hard precondition for (b) or (c) ever being safe.
3. **Then (a)** — record `drift_history` as deliberately unpersisted with the §3.3 four-mechanism reason in the exemption row (that reason is *verified*, not asserted — which is the bar S1's `ic.actuals` case established).
4. **Reject (b) and (c).**

**Exemption reasons to record for the CI guard:**
- `turnover` → `SAFE-UNPERSISTED: pure diagnostic accumulator; its only consumer PerNodeSnap.ml_portfolio_turnover (ShardedSnapshot.hpp:622) has zero readers tree-wide.` (Re-verify if B-2 is closed by adding a render row.)
- `drift_history` → `SAFE-UNPERSISTED: the capital OUTPUT (node_kill_tripped) is persisted at wire row 020; breach⇒kill is same-call (ControllerEventLoop.hpp:1893→1907); the detector INPUT (RollingIC) is persisted at wire rows 039-042 + lockstep-restored (ConfidenceScore.hpp:1485); CheckBreach is a mean so the verdict is sample-count-invariant. Cold-start exposure is bounded at 4 closed ML trades (ConfidenceScore.hpp:1397/1410).`
- `sp_telemetry` → `SAFE-UNPERSISTED: process-lifetime counters + live thread state; display-only via EngineTUI.hpp:2059-2066. Persisting would render a running node as PAUSED and a fresh node as stalled.`

---

## 5. Findings you did not ask about

| id | severity | finding |
|---|---|---|
| **B-1** | **MED** | **`confidence_ic_floor` is read GLOBAL at a per-node consumer — the H22 "A1" shape — and the CI guard is structurally blind to it.** The field is a `FOREACH_PER_NODE_CFG_FIELD` row (`CoreFrameworks/CfgFieldRegistry.hpp:784`) whose own tooltip says *"Per-node eligible — each node has independent ML model drift profile"*. The per-node slot is auto-generated and real (probe: `cfg.nodes[0].confidence_ic_floor = 0.0200`). **Zero sites read it** (`rg 'nodes\[[^]]*\]\.confidence_ic_floor\|node_cfg->confidence_ic_floor'` → `RC=1`). The sole consumer reads the flat global: `CoreFrameworks/EngineSharded/SlowPath.hpp:74`. `EventLoop_DrainPostFillOneCore` already receives the per-node slice (`node_cfg`, `ControllerEventLoop.hpp:1644`), so the correct read is in scope. **Why CI is green:** `tools/check_per_node_registry_integrity.py` Check 10 scans `SlowPath.hpp` but its field set `CHECK_10_PER_NODE_FIELDS_WITH_GLOBAL_SISTER` (`:458-463`) is a hand-list of **4** fields out of **88** per-node fields. "Check 10 PASS: 16 file(s) scanned" says nothing about the other 84. The guard-coverage gap is arguably the bigger finding than the field. |
| **B-2** | LOW | **The whole `RollingTurnover` feature is dead below the snapshot.** `ml_portfolio_turnover` is written (`ShardedSnapshot.hpp:622`) and read nowhere. This is not a mid-ship drop: the originating plan `plans/v5.14-foxml-port-and-maker/subplans/2026-05-09-v5.14.1.G-portfolio-turnover.md` runs Step 1 → Step 6 and **has no GUI-render step** — the render was never planned. Cost currently paid for zero visibility: 280 B/node of state, `RollingTurnover_Compute` = O(count) popcounts per node per snapshot publish (up to 255 iterations, `RollingTurnover.hpp:190-196`), a per-cycle `_Push` in the ML ensemble path, 3 boot Init calls, 2 cfg fields, 8 tests. Disposition is a real fork: add the render row it was designed for, or delete per `feedback_backwards_compat_not_default_concern`. Contradicts `GUI/CLAUDE.md`'s "every new snapshot field gets its GUI render in the SAME ship". |
| **B-3** | LOW | **`confidence_turnover_window/topk` — the registry advertises a range the code silently ignores.** Registry declares `INT(1000, 1, 100000)` and `INT(10, 1, 1000)` (`CfgFieldRegistry.hpp:674/677`); `ControllerConfig_Default` sets 100/3 (`ControllerConfig.hpp:2179-2180`); `RollingTurnover_Init` silently clamps to `MAX_WINDOW=256` / `MAX_TOPK=8` (`RollingTurnover.hpp:91/93`). Probe F: `RollingTurnover_Init(1000, 10)` → `window=256, topk=8`. The `WARN_ON_CLAMP` flag warns on the *registry* range, not the code cap, so an operator setting 1000 in the Settings panel gets 256 with no message. |
| **B-4** | LOW | **`RollingTurnover` has no compile-time size pin, unlike both its siblings.** `gen_code_map.sh --byte-context RollingTurnover` returns an **empty** `sizeof(...)` sites section, whereas `DriftHistory` (`ConfidenceScore.hpp:1342`) and `SlowPathTelemetry` (`ControllerEventLoop.hpp:261`) each carry a `static_assert`. Its `[SIZE]_[280B]` `[DERIVED]` tag is therefore locked by nothing. It is not byte-serialized (so `check_struct_alignment.py`(c) exempts it), not in `check_struct_size_budget.py`'s manifest, and not in `tools/lib/cache_layout_baseline.txt` — a manifest row would close it. |
| **B-5** | INFO (scoping) | **Every warm-restart claim here is PAPER-MODE-ONLY today.** `ShardedSnapshot_Load` is gated by `if (!live_trading)` at `CoreFrameworks/EngineSharded/Run.hpp:1065`; live boot reconciles against exchange truth instead (`:1073-1108`). The backtest path never saves or loads a snapshot (Save/Load call sites are confined to `EngineSharded/{Run,Async}.hpp`). Since v5.15 is the live-readiness sprint, *whether live gains a warm-restart path* is the single change that would re-open every verdict above. |

**Corroboration with the sister sweep:** I independently reached S4's D-3 (`plans/v5.15-live-readiness/reports/2026-08-15-complement-blindness-sweep/S4-nodectx-state-bitflags.md:233`) — the paper-reset-preserves / warm-restart-destroys asymmetry rests on one prose sentence at `NodeCtxInitRegistry.hpp:182-186` with no mechanical binding. F-1 is the concrete harm that asymmetry conceals, which S4 did not reach. S1's OQ-4 (`:241`) asks whether a reason column suffices; **F-1 is a second data point that it does not** — here the reason ("load-bearing across reset") is *true for the reset path and silently false for the restart path*, the same true-here/false-there shape as the `ic.actuals` lockstep.

---

## 6. Hypotheses the code REFUTED

| # | Hypothesis | Refutation |
|---|---|---|
| H-A | A fresh drift ring blinds the node for ~256 samples | The threshold is **5 in-window samples**, not 256 (`ConfidenceScore.hpp:1397` + `:1410`). Probe D: first breach at sample #5 ⇒ blind window = **4** pushes |
| H-B | A restarted node reads a materially different drift verdict | Probe C: 40-sample vs 20-sample histories of the same IC → identical verdict (`breach=1 avg=-0.3000`). `CheckBreach` is a mean, not a count-weighted score |
| H-C | Un-persisting `drift_history` loses the capital decision | `node_kill_tripped` rides the wire (golden row `020`); and with auto-kill on, breach⇒kill is same-call (`:1893`→`:1906`), so there is no intermediate state to lose |
| H-D | The drift detector's input is cold after a restart | `RollingIC` is persisted (golden rows `039`–`042`) and lockstep-restored (`ConfidenceScore.hpp:1485`); `ic_now` at `:1879` is warm from the first post-restart trade |
| H-E | `sp_telemetry.last_tick_us` feeds `EventLoop_CheckWsStaleness` (making it operationally load-bearing) | `CheckWsStaleness` is passed `rebuild_ts_us` directly (`EngineCommon.hpp:829`); `sp_telemetry`'s only read tree-wide is `EngineTUI.hpp:2059-2066` |
| H-F | `turnover` feeds ensemble weighting or bandit reward | `RollingTurnover_Push` at `StrategyParameters.hpp:1265` is a pure sink placed **after** `weights_buf` is finalized (`:1256-1267`); nothing reads back |
| H-G | The three sub-structs straddle cache lines / are un-guarded by the layout gate | `foxtag layout` reports `straddlers: []` for all three; `tools/lib/cache_layout_baseline.txt` (11 rows, all `TrainingPanelState`) correctly holds none of them |

---

## 7. Where the paired a-class should push hardest

1. **The "4 closed trades" figure** assumes `DriftHistory_Push` fires exactly once per trade idea via the `is_leg_a` guard (`:1842`). Under `partial_exit_enabled=1` a trade closes as two legs — construct a leg-B-only or out-of-order close and check the push cadence still holds. If it doesn't, my window figure moves.
2. **My "zero readers of `ml_portfolio_turnover`"** rests on a whole-tree grep of that identifier plus a case-insensitive `turnover` sweep of `GUI/`. I did **not** trace every downstream copy of `snap->per_node[i]` into other structs that might rename the field. Refute by following the `PerNodeSnap` copy chain.
3. **H-B holds for a *stationary* IC.** For a **non-stationary** node (healthy 20 trades, then degraded 20), the restarted node's mean omits the healthy half and would breach *earlier*. I believe that asymmetry is conservative-safe (errs toward killing), but I did **not** exhaustively prove the sign. Build the non-stationary case; if any construction makes the restarted node breach *later*, my SAFE-UNPERSISTED verdict on `drift_history` weakens.
4. **F-1's severity (MED)** is gated on `auto_kill_on_drift = 0` being the shipping default (`ControllerConfig.hpp:2123`). Check the live-readiness plans for an intent to enable it — if so, re-rate to HIGH.
5. **My claim that `EventLoopState_Init` is never re-invoked at runtime** (hence a restart is the only re-arm) rests on a call-site grep: `ControllerEventLoop.hpp:1143`, `EngineCommon.hpp:214`, `:1182` (InitLegacy/tests). Push specifically on the cfg-hot-reload path (`Async.hpp:~380`) and the strategy hot-swap path.
6. **B-1's "zero readers of the per-node slot"** used a regex over three access spellings. Push on whether `ControllerConfig_ResolveForCore` copies `confidence_ic_floor` into a `resolved_cfg` local under a spelling my regex missed — that would downgrade B-1 from a violation to a naming issue.
7. **Option (d) assumes `out_samples == 0` is an exact discriminator for insufficient-data.** I verified the three write points (`ConfidenceScore.hpp:1395-1396`, `:1413`) and the two early returns. Refute by finding any path where `n == 0` co-occurs with a *made* decision, or where `count ≥ 5` but all samples fall outside the window and the caller would mis-read the abstain as healthy.
