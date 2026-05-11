# Deep audit — v5.14.4 centralized engine + reconcile call sites

**Triggered by:** v5.14.4 initial audit YELLOW Finding 1 (TECH_DEBT-002 alignment)
**Date:** 2026-05-09
**Verdict:** **CONFIRMED-SHARDED-ONLY** — migration scope is clean

---

## Findings (6 questions answered)

### Q1: All `Reconcile_*` call sites
**Production:** 4 calls in `EngineSharded.hpp:1307-1317` (boot dispatch only):
- `Reconcile_ParseOpenOrders`, `Reconcile_ParseMyTrades`, `Reconcile_Decide` at 1307-1311
- `Reconcile_LogReport(rr, cfg.reconcile_dry_run)` at 1317

**Test:** 7 calls in `controller_test.cpp:8337-8443` (6 test functions; pure logic, no cfg).

**Legacy single-core engine (`main.cpp:362`):** Comment mentions "startup reconciliation" but ONLY calls `BinanceOrderAPI_GetBalances()` for balance check — NOT full reconcile.

### Q2: All readers of `cfg.reconcile_dry_run` + `cfg.reconcile_interval_sec`
**Definition:** `ControllerConfig.hpp:716-717` — defaults: `dry_run=1` (safe), `interval_sec=0` (boot-only)

**Readers:** ONLY 2 sites in `EngineSharded.hpp:1317, 1329`. Centralized + backtest + foxml_suite consume neither.

### Q3: Implicit OMS state-sync logic elsewhere
- **Centralized boot (main.cpp:362-377):** Calls `BinanceOrderAPI_GetBalances` once; checks `BTC > 0.000001 AND positions exist` → marks live. NOT reconciliation (no decision logic, no refusal).
- **Backtest:** Zero reconcile references (synthetic ticks; no exchange state).
- **foxml_suite (GUI):** Zero reconcile references.

### Q4: `live_trading` flag + post-reconcile semantics
- `OrderManager.hpp:484` defines `oms->live_trading` set at `EngineSharded.hpp:717` from `cfg.use_real_money`
- `ControllerEventLoop.hpp:3133` "post-reconcile flag reset" refers to `flatten_pending` (WS stale-data recovery), NOT `live_trading`
- No cross-engine dependency on reconcile completion

### Q5: `BinanceOrderAPI_CancelOrder` status
- Does NOT exist today — `DataStream/BinanceOrderAPI.hpp` lists 11 functions; cancel absent
- v5.14.4.0 plans to add it (NEW)
- No current callers to worry about

### Q6: Other reconcile cfg fields
- Only 2 fields exist (`reconcile_dry_run`, `reconcile_interval_sec`); both sharded-only consumers
- No `reconcile_strict`, `reconcile_auto_sync`, or other enums hidden anywhere

---

## TECH_DEBT-002 alignment

✅ **Verified safe:** EngineSharded is sole boot reconcile caller; legacy main.cpp has only basic balance check; cfg fields read only by sharded engine. **No cfg→enum migration work needed elsewhere.**

---

## Caveat for future-proofness

**Auditor flag:** "If v5.14.4 plan adds runtime heartbeat reconcile (Phase 3, currently deferred per `Reconcile.hpp:19-24`), verify that dispatch is also sharded-only (not added to legacy path by mistake)."

**Action for v5.14.4.B coding:** add explicit comment at boot dispatch site:
```cpp
// v5.14.4 — sharded-only path. Verified by deep audit 2026-05-09:
// centralized engine (main.cpp:362) does balance check only, NOT
// reconciliation. cfg.reconcile_mode reader count = 2 (this dispatch
// + Reconcile_LogReport). When TECH_DEBT-002 (centralized removal)
// ships, no migration step needed here. If v5.X+ adds runtime
// heartbeat reconcile (Phase 3 per Reconcile.hpp:19-24), verify the
// new dispatch is ALSO sharded-only — DO NOT add to legacy path.
```

This documents the non-overlap so future-Caramel + future-Claude don't
re-investigate.

---

## Final verdict

**CONFIRMED-SHARDED-ONLY.** v5.14.4 migration is architecturally isolated to sharded engine. Zero hidden call sites. Proceed with coding per amended plan.
