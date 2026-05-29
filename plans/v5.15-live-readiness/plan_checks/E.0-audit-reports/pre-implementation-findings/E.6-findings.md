---
type: pre-implementation-findings
scope: E.6
engine_head: ce2173b (v5.15.5.F.4d.1.D.1 WIP)
date: 2026-05-28
source: codebase-deep-sweep-5x9 (49-agent skill-driven sweep) + pass1/pass2 + round-0
status: provisional (49 findings need runtime confirmation; marked inline)
codification: DEFERRED until .D.1 ships (Classes 37+, DESIGN_SPECS, CI tools, ledgers)
---

# Pre-implementation findings — E.6

**2 findings** ({'CRITICAL': 1, 'LOW': 1}). Deduped vs prior passes + TECH_DEBT/PARITY. NEEDS-RUNTIME-CONFIRM = provisional.

### [CRITICAL] `live-bc-1` — User-data WS points at Binance GLOBAL (stream.binance.com) while orders + listen key use Binance US (api.binance.us) — real-time fills never arrive in non-testnet live
*grep-verified · **NEEDS-RUNTIME-CONFIRM*** · section `live-binance` · fix: .E.6 (exchange adapter) primarily; .E.5 (creds/host wiring) — derive all three hosts (order REST, user-data WS, market-data) from one FOREACH_EXCHANGE row per property so they cannot diverge
- **Where:** CoreFrameworks/EngineSharded/Run.hpp live setup: rest_host = bcfg.use_testnet ? "testnet.binance.vision" : "api.binance.us" (~line 586 for order adapter; ~line 762 for user-data REST) vs ws_host = bcfg.use_testnet ? "testnet.binance.vision" : "stream.binance.com" (~line 760-761). UserData listen key obtained via s->rest_api (api.binance.us) in ud_obtain_listen_key (DataStream/BinanceUserData.hpp ~243-275), then ud_ws_thread connects WSS to stream.binance.com/ws/<listenKey> (~line 416, 428).
- **What:** For non-testnet live, the adapter and the user-data REST instance are initialized against api.binance.us (Binance US), so the listen key is created on the Binance US account. The user-data websocket then connects to stream.binance.com (Binance Global). Listen keys are account/exchange-property-specific — a Binance US listen key is not authenticated by Binance Global's /ws/<listenKey> endpoint (and the correct US WS host is stream.binance.us). main.cpp:386-388 confirms the REST=api.binance.us choice is intentional, but the user-data WS host was left at the Global endpoint. There is also no validation tying use_real_money / use_testnet / use_binance_us to the three independently-hardcoded host selections (order REST, user-data WS, market-data depth), so a single live run can straddle three different Binance properties.
- **Why:** If the WS listen key is rejected (or streams a different/empty account), no CMD_WS_FILL ever reaches the OMS in production live mode. Adapter REST returns ACK-only (fill_qty=0 -> ORDER_ACKNOWLEDGED) whenever ws_active is set (BinanceAdapter.hpp:212-214; Run.hpp:768 sets ws_active=1 on WS start), so the order stays open forever waiting for a WS fill that never comes: positions are never booked, SL/TP/time exits never fire on an unbooked position, and the engine relies solely on the boot-time REST reconcile. This is a silent, total failure of the live fill path on the production (non-testnet) endpoint — exactly where it matters most.
- **⚠ Don't carry forward (.E.1 rewrite):** In the .E.1 Core->Node + FOREACH_EXCHANGE rewrite, do NOT carry forward three independently-hardcoded host ternaries. Each exchange row must expose order_rest_host / userdata_ws_host / marketdata_ws_host as columns so REST and user-data WS are guaranteed same-property; add a boot assert that the user-data WS host belongs to the same exchange property as the order REST host.
- **CI check:** Grep/AST check: flag when distinct host string literals for the same exchange are selected by separate ternaries in the same live-setup function without a shared exchange descriptor; or assert userdata_ws_host and order_rest_host share a registry-declared exchange id
- **Test to add:** Add a test that, for each (use_testnet, use_binance_us) combination, asserts the order REST host and the user-data WS host belong to the same Binance property (testnet/US/Global) — would have caught the Global-vs-US split immediately
- **Anti-pattern:** Independently-hardcoded endpoint hosts for cooperating subsystems (orders vs fill-stream) of the SAME logical exchange account, with no single-source-of-truth tying them together -> silent cross-property mismatch

### [LOW] `live-12` — BinanceAdapter_GetBalancesImpl swaps base/quote outputs (latent — vtable get_balances has no production caller, but bites at adapter generalization)
*grep-verified* · section `live-binance` · fix: .E.6 (adapter framework generalization)
- **Where:** CoreFrameworks/BinanceAdapter.hpp BinanceAdapter_GetBalancesImpl (~lines 384-390): signature `(ctx, double* base_out, double* quote_out)` calls `BinanceOrderAPI_GetBalances(&workers_api[0], quote_out, base_out)`; BinanceOrderAPI_GetBalances signature is `(api, usdt_out, btc_out)` (DataStream/BinanceOrderAPI.hpp:793)
- **What:** ExchangeAdapter.get_balances is contracted as (base_out, quote_out) (ExchangeAdapter.hpp:94). For BTC/USDT, base=BTC and quote=USDT. The impl passes base_out into BinanceOrderAPI_GetBalances's usdt_out slot and quote_out into its btc_out slot — i.e. base_out receives USDT and quote_out receives BTC, swapped relative to the contract. It is currently latent because the vtable get_balances pointer is only assigned (BinanceAdapter.hpp:426) and never invoked anywhere in production; all real balance reads call BinanceOrderAPI_GetBalances directly with the correct (usdt,btc) order.
- **Why:** Harmless today (dead indirection) but it is a correctness trap that will silently swap base/quote balances the moment the exchange-adapter abstraction is actually exercised — exactly what the .E.6 adapter-framework-generalization ship does. Worth fixing now so the abstraction is correct when first used.
- **⚠ Don't carry forward (.E.1 rewrite):** When the ExchangeAdapter vtable becomes the real call path, ensure each adapter's get_balances maps (base,quote) correctly; add a unit test through the vtable, not just the concrete function.
- **Test to add:** Add a test that calls get_balances THROUGH the ExchangeAdapter<F> vtable and asserts base_out==BTC, quote_out==USDT.
- **Anti-pattern:** An abstraction-layer adapter function has an argument-order bug that is masked because callers bypass the abstraction and call the concrete function directly — the bug surfaces only when the abstraction is first used.

