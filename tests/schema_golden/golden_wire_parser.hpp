// Copyright (c) 2026 Jennifer Lewis. All rights reserved.
// Licensed under the GNU Affero General Public License v3.0 (AGPL-3.0).
// See LICENSE file in the project root for full license text.
//
// DOGFOOD FIXTURE (E.1.2.A phase 3) — real unit, copied + converted, NEVER compiled.
// Source: DataStream/BinanceUserData.hpp:292-383 @ engine d4812de (2026-07-15 copy).
// Shape exercised: WIRE-PARSER with a JSON venue field-map (survey C flagship; the D-345
// grounding unit for [WIRE_FIELD] itself) + within-fn section phases on real code.
// Lossless accounting: zero drops — the banner's "Relevant fields from the Binance docs"
// legend becomes the tier-2 [WIRE_FIELD] lines (key + meaning VERBATIM, one per line);
// every body step-comment stays inline (D-326). ADDITIVE (not in the source, from the
// D-345 dry-run + the .E.0.10 hunt): [EXCLUDED]_[z] surfacing the A2 partial-fill gap.

//======================================================================
// [FUNCTION]_[ud_parse_execution_report]
//----------------------------------------------------------------------
// [TAG]_[[ENGINE] [PARSER] [OMS_DRAINER] [CAPITAL_BEARING]]
// [SCHEMA]_[v1.0]
// [OVERVIEW]_[extracts fill data from a Binance executionReport JSON event — returns 1 if this is a fill event (x == "TRADE"), 0 otherwise]
// [REFERENCE]_[SOURCE]_[Binance WS executionReport docs]
// [REFERENCE]_[INVARIANT]_[[H5] [H21]]
// ---- the venue field-map (tier-2 [WIRE_FIELD] members, key-addressed; meanings verbatim from the source banner) ----
// [WIRE_FIELD]_[e]_[event type ("executionReport")]
// [WIRE_FIELD]_[x]_[execution type (TRADE = fill)]
// [WIRE_FIELD]_[X]_[order status ("FILLED")]
// [WIRE_FIELD]_[c]_[clientOrderId (our idempotency key, "oms_123")]
// [WIRE_FIELD]_[i]_[exchange orderId]
// [WIRE_FIELD]_[L]_[last executed price]
// [WIRE_FIELD]_[l]_[last executed quantity]
// [WIRE_FIELD]_[n]_[commission amount]
// [WIRE_FIELD]_[N]_[commission asset ("BNB")]
// [WIRE_FIELD]_[t]_[trade ID (for deduplication)]
// [WIRE_FIELD]_[T]_[transaction time (ms)]
// [WIRE_FIELD]_[m]_[maker flag — bare true/false; first-char check, missing -> taker (conservative)]
// [EXCLUDED]_[z]_[cumulative filled qty — CURRENTLY UNPARSED; the A2 partial-fill gap made visible]
// [FUTURE_WORK]_[TECH_DEBT]_[TECH_DEBT-169]
//======================================================================
// [CODE]
//======================================================================
static inline int ud_parse_execution_report(const char* json, int len,
                                             Command* cmd_out,
                                             uint64_t* trade_id_out) {
    (void)len;
    //------------------------------------------------------------
    // [SECTION]_[event-type gates]
    //------------------------------------------------------------
    // check event type
    char event_type[32] = {};
    binance_json_extract_str(json, "e", event_type, sizeof(event_type));
    if (strcmp(event_type, "executionReport") != 0) return 0;

    // check execution type — only "TRADE" is a fill
    char exec_type[16] = {};
    binance_json_extract_str(json, "x", exec_type, sizeof(exec_type));
    if (strcmp(exec_type, "TRADE") != 0) return 0;

    //------------------------------------------------------------
    // [SECTION]_[order identity + fill data]
    //------------------------------------------------------------
    // extract clientOrderId — should be "oms_<id>"
    char client_oid[64] = {};
    binance_json_extract_str(json, "c", client_oid, sizeof(client_oid));
    uint64_t oms_order_id = 0;
    if (strncmp(client_oid, "oms_", 4) == 0) {
        oms_order_id = strtoull(client_oid + 4, NULL, 10);
    }

    // extract exchange orderId
    char exchange_oid[32] = {};
    binance_json_extract_str(json, "i", exchange_oid, sizeof(exchange_oid));

    // fill data
    double fill_price = binance_json_extract_double(json, "L");
    double fill_qty   = binance_json_extract_double(json, "l");
    *trade_id_out     = (uint64_t)binance_json_extract_double(json, "t");

    //------------------------------------------------------------
    // [SECTION]_[phase-8 fields — maker/taker + order status + commission]
    //------------------------------------------------------------
    // Phase 8 — maker/taker + order status + commission.
    // "m": Binance encodes booleans as bare true / false in JSON. The
    // existing extract_str returns the literal text — we check the first char.
    // Defensive default: missing "m" → is_maker=0 (taker, slightly overstates
    // fees, conservative) per master plan.
    char m_str[8] = {};
    binance_json_extract_str(json, "m", m_str, sizeof(m_str));
    int is_maker = (m_str[0] == 't' || m_str[0] == 'T') ? 1 : 0;

    // "X": order status. "FILLED" → terminal; anything else (including
    // "PARTIALLY_FILLED") is non-terminal. Defensive default: missing "X"
    // → order_complete=0 (assume partial — keeps order alive in OMS,
    // worst case we wait for next event to confirm).
    char order_status[24] = {};
    binance_json_extract_str(json, "X", order_status, sizeof(order_status));
    int order_complete = (strcmp(order_status, "FILLED") == 0) ? 1 : 0;

    // Commission: "n" amount + "N" asset. Recorded for audit; not the
    // authoritative fee number (Fee_Compute computes from cfg rates).
    double commission_amt = binance_json_extract_double(json, "n");
    char comm_asset[8] = {};
    binance_json_extract_str(json, "N", comm_asset, sizeof(comm_asset));

    //------------------------------------------------------------
    // [SECTION]_[build the Command]
    //------------------------------------------------------------
    memset(cmd_out, 0, sizeof(*cmd_out));
    cmd_out->type     = CMD_WS_FILL;
    cmd_out->order_id = oms_order_id;
    cmd_out->result.success        = 1;
    cmd_out->result.avg_fill_price = fill_price;
    cmd_out->result.fill_qty       = fill_qty;
    cmd_out->result.error_code     = 0;
    strncpy(cmd_out->result.exchange_id, exchange_oid,
            sizeof(cmd_out->result.exchange_id) - 1);
    // Phase 8 fields
    cmd_out->result.is_maker       = (uint8_t)is_maker;
    cmd_out->result.order_complete = (uint8_t)order_complete;
    cmd_out->result.commission     = commission_amt;
    strncpy(cmd_out->result.commission_asset, comm_asset,
            sizeof(cmd_out->result.commission_asset) - 1);

    return 1;
}
//======================================================================
// [END_CODE]
//======================================================================
// [COMMENT]_[venue contract notes]
//----------------------------------------------------------------------
// Extracts fill data from a Binance executionReport JSON event.
// Returns 1 if this is a fill event (x == "TRADE"), 0 otherwise.
// (The "build the Command" section carries the memset + field fill — kept inline
//  with the code it explains; the original one-line "// build the Command" step
//  comment became that section's label, same text made machine-navigable.)
//======================================================================
// [END_FUNCTION]_[ud_parse_execution_report]
//======================================================================
