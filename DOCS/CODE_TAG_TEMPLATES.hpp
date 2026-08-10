// Copyright (c) 2026 Jennifer Lewis. All rights reserved.
// Licensed under the GNU Affero General Public License v3.0 (AGPL-3.0).
// See LICENSE file in the project root for full license text.

//======================================================================================================
// [CODE-TAG TEMPLATE CORPUS — copy-paste source for E.1.2.A tag-block conversions]
//======================================================================================================
//
// One VALIDATOR-GREEN block per unit type of the locked [SCHEMA]_[v1.0]
// (DESIGN_SPECS/doc-disciplines/in-code-documentation-schema.md — the frozen contract).
// This file is [SCHEMA]-opted-in, so `tools/check_code_tag_blocks.py` polices it in
// standing CI: the templates can never silently rot against the grammar/vocab.
//
// HOW TO USE (converting a real unit, or writing a new one):
//   1. Copy the block for your unit type; replace names / [TAG] values / prose.
//   2. Code-local comments STAY inside [CODE] verbatim (D-326) — only unit-level WHY
//      moves to [COMMENT]; preserve the author's voice VERBATIM when relocating.
//   3. Leave [DERIVED] values to the TOOLS (cache-gate --fix / :FoxSymdepsDerived!) —
//      NEVER hand-write a derived fact into real code (anti-Class-18).
//   4. Prove it: python3 tools/check_code_tag_blocks.py --paths <your-file>
//
// ⚠ The [DERIVED] numbers below are ILLUSTRATIVE placeholders on toy code — they show the
//   SHAPE. The cache-layout gate skips DOCS/ for exactly this reason. Do not copy values.
// ⚠ The schema doc's § Worked examples predate the lock in places (Unicode bars, multi-
//   category lines, pre-vocab [TAG] values); THIS file is the validator-green rendering.
// ⚠ TEMPLATE SPECIALIZATIONS — name the block by the REAL identifier, NOT an underscore alias:
//   e.g. [STRUCT]_[FixedPoint<2,64>] / [FUNCTION]_[Foo<64>]. The parser accepts the <...> (it sits
//   INSIDE the value brackets — the innermost-bracket rule captures `FixedPoint<2,64>` whole), and
//   check_cache_layout matches it template-tolerantly (splits the record name on `<`), so the
//   layout DERIVED still resolves. First canonical: FixedPoint/FixedPointN.hpp (P6.128).
//
//======================================================================================================
#pragma once

//======================================================================
// [FILE]_[DOCS/CODE_TAG_TEMPLATES.hpp]
//----------------------------------------------------------------------
// [TAG]_[[DEV_PLANE] [DOC_DISCIPLINE]]
// [SCHEMA]_[v1.0]
// [OVERVIEW]_[per-type tag-block template corpus — one conforming block per unit type; standing-CI-policed]
// [CONTAINS]
//   - [FUNCTION]_[Regime_Classify]           (function — slow-path kernel shape)
//   - [STRUCT]_[ExecutionCore]               (layout-critical struct shape)
//   - [STRUCT]_[CfgFieldDescriptor]          (nested child block + [ASSERT] guards)
//   - [REGISTRY]_[FOREACH_GLOBAL_CFG_FIELD]  (X-macro registry + [COLUMN]/[ROW])
//   - [ENUM]_[OrderState]                    (persisted/wire CODE enum + [VALUE])
//   - [TYPE]_[Money]                         (foundational typedef + assert trio)
//   - [MACRO]_[BITMAP_IS_SET]                (LIGHT unit — no closer)
//   - [TEST]_[test_config_parser]            (LIGHT unit — suite navigation)
//   - [STRATEGY]_[<Name>]                    (strategy unit — /strategy-template pulls this)
//   - [FUNCTION]_[ud_parse_execution_report] (wire-parser + [WIRE_FIELD] field-map)
// [REFERENCE]_[DESIGN_SPEC]_[in-code-documentation-schema]
//======================================================================


//======================================================================
// [FUNCTION]_[Regime_Classify]
//----------------------------------------------------------------------
// [TAG]_[[SLOW_PATH] [ML_INFERENCE]]
// [SCHEMA]_[v1.0]
// [OVERVIEW]_[score-based regime classify — each signal +1, highest wins]
// [DIAGRAM]
//   RegimeSignals {slope, R2, ROR, vol, var}
//          |
//          v
//     trend / vol score  --highest-->  hysteresis  -->  regime
//======================================================================
// [CODE]
//======================================================================
template <unsigned F>
inline int Regime_Classify(RegimeState<F>* state, const RegimeSignals<F>* sig,
                           const ControllerConfig<F>* cfg) {
    if (sig->short_count < 64) return state->current_regime;   // cold start — code-local comments STAY (D-326)
    //------------------------------------------------------------
    // [SECTION]_[signal scoring]
    //------------------------------------------------------------
    // (phase body — its step-comments stay inline, at the line they explain)
    //------------------------------------------------------------
    // [SECTION]_[hysteresis + commit]
    //------------------------------------------------------------
    return 0;
}
//======================================================================
// [END_CODE]
//======================================================================
// [COMMENT]
//~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
// [[2026-04-01] [v5.7.1]]
//----------------------------------------------------------------------
// each signal +1 to a trending/volatile score, highest wins; hysteresis
// (hold N cycles) stops it flapping, RANGING is the default. extend by
// adding a RegimeSignals field + one compare here — the whole surface.
// [SUPPORTING_DOCS]
//   - [INVARIANT]_[H4]
//   - [INVARIANT]_[H8]
//   - [AUDIT]_[latency-conformance-kernel]
//======================================================================
// [DERIVED]   (tool-refreshed — do NOT hand-edit; values here ILLUSTRATIVE)
//----------------------------------------------------------------------
// [BUILD]_[-O3 -march=x86-64-v3]
// [INSTANTIATION]_[[F=64]]
// [SIZE]_[~480 instr]
// [SIMD]_[none]
// [FLOAT]_[18 · H4-exempt feature-math]
// [BRANCHES]_[0 data-dependent-warm]
// [UPSTREAM]_[[RegimeSignals] [ControllerConfig]]
// [CONSUMERS]_[[EventLoop_RebuildOneCore] [StrategyParameters_Dispatch]]
//   body: 1x [LAT_EXEMPT] env-gated cold-debug fprintf
//======================================================================
// [END_FUNCTION]_[Regime_Classify]
//======================================================================


//======================================================================
// [STRUCT]_[ExecutionCore]
//----------------------------------------------------------------------
// [TAG]_[[HOT_PATH] [DATA_ORIENTED_DESIGN] [CONCURRENCY]]
// [SCOPE]_[CORE]
// [THREAD]_[[HOT_WRITER] [SLOW_READER]]
// [STRADDLE_EXEMPT]_[<field>]_[<reason + decision-ref — CURATED, field-level ONLY (never blanket-struct); silences the H6 gate verdict for that field, the FACT still gets written by --fix>]   <-- optional; D-413/D-414
// [SCHEMA]_[v1.0]
// [OVERVIEW]_[per-node hot execution state — layout-by-access-pattern, H6]
// [DIAGRAM]
//   line0: [active:1][active_b:1][pad:6][live_tp:24][live_sl:24][pad:8] = 64B
//   line2: [permission:1][pad:63]   <- false-sharing isolated
//======================================================================
// [CODE]
//======================================================================
template <unsigned F> struct alignas(64) ExecutionCore {
    //---- [SECTION]_[hot reads, line 0] ----
    // fields ... per-field inline comments STAY in place (D-326)
    //---- [SECTION]_[cross-thread, own line per H6] ----
    // fields ...
};
//======================================================================
// [END_CODE]
//======================================================================
// [COMMENT]
//~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
// [[2026-05-11] [v5.11.1.5]]
//----------------------------------------------------------------------
// moved live_tp/live_sl into line 0 so the steady CMOV reads both in one
// cache line — cut a tick from 2 loads to 1. permission sits cross-CPU so
// it gets its own line (false-sharing isolation).
// [SUPPORTING_DOCS]
//   - [DESIGN_SPEC]_[cache-line-discipline]
//   - [INVARIANT]_[H6]
//======================================================================
// [DERIVED]   (tool-refreshed — do NOT hand-edit; values here ILLUSTRATIVE)
//----------------------------------------------------------------------
// [SIZE]_[192B]
// [ALIGN]_[64]
// [CACHE_LINES]_[3]
// [STRADDLE]_[none]
// [ALIGNED_CONSUMERS]_[[ControllerEventLoop] [OrderManager]]
//======================================================================
// [END_STRUCT]_[ExecutionCore]
//======================================================================


//======================================================================
// [STRUCT]_[CfgFieldDescriptor]
//----------------------------------------------------------------------
// [TAG]_[[ENGINE] [DATA_ORIENTED_DESIGN]]
// [SCHEMA]_[v1.0]
// [OVERVIEW]_[per-field metadata record the 13-col X-macro materializes into; GUI+parser+validation]
// [CONTAINS]
//   - [ENUM]_[MetadataFlag]
//======================================================================
// [CODE]
//======================================================================
struct CfgFieldDescriptor {
    //==================================================================
    // [ENUM]_[MetadataFlag]
    //------------------------------------------------------------------
    // [TAG]_[[ENGINE] [BITMAP_PACKED]]
    // [SCHEMA]_[v1.0]
    // [OVERVIEW]_[metadata bits — rich NESTED unit gets its OWN block, sited at its real location, D-340]
    //==================================================================
    // [CODE]
    //==================================================================
    enum MetadataFlag : uint16_t { IS_BOOT_ONLY = 1u << 0 /* ... */ };
    //==================================================================
    // [END_CODE]
    //==================================================================
    // [END_ENUM]_[MetadataFlag]
    //==================================================================
    enum Kind : uint8_t { KIND_INT, KIND_BOOL };   // trivial nested enum -> terse inline, NO block (proportionality)
    //---- [SECTION]_[Header, 8 bytes] ----
    // Kind kind; uint16_t metadata_flags; uint16_t _reserved = 0;   // H12 explicit pad
    //---- [SECTION]_[Payload union, 32 bytes] ----
    // union { ... } payload;
};
//======================================================================
// [END_CODE]
//======================================================================
// [DERIVED]   (tool-refreshed — do NOT hand-edit; values here ILLUSTRATIVE)
//----------------------------------------------------------------------
// [SIZE]_[128B]
// [ALIGN]_[8]
// [CACHE_LINES]_[2]
// [STRADDLE]_[none]
//======================================================================
// [END_STRUCT]_[CfgFieldDescriptor]
//======================================================================

// [ASSERT]_[LAYOUT_LOCK]_[sizeof(CfgFieldDescriptor) <= 128]
// [WHY]_[2 cache lines; GUI 60Hz cache-warm — the assert ENFORCES the bound, the DERIVED size line REPORTS the value]
static_assert(sizeof(CfgFieldDescriptor) <= 128, "CfgFieldDescriptor grew past 2 cache lines");
// [ASSERT]_[BITMAP_OVERFLOW]_[HIGHEST_FLAG_BIT < 1u<<16]
// [WHY]_[MetadataFlag must fit uint16; the assert MESSAGE carries the remediation — widen to uint32 at the top bit]
static_assert(CfgFieldDescriptor::IS_BOOT_ONLY < (1u << 16), "widen metadata_flags to uint32");


//======================================================================
// [REGISTRY]_[FOREACH_GLOBAL_CFG_FIELD]
//----------------------------------------------------------------------
// [TAG]_[[ENGINE] [FRAMEWORK_DISCIPLINE]]
// [SCHEMA]_[v1.0]
// [OVERVIEW]_[47 global cfg fields — operator sets once engine-wide; add a field = 1 row]
// [COLUMN]_[STORAGE_T]_[C storage type]                     (listing order = tuple ordinal, D-339)
// [COLUMN]_[KIND_TOKEN]_[GUI-metadata kind]_[[KIND_INT] [KIND_BOOL] [KIND_DOUBLE] [KIND_STRING]]
// [COLUMN]_[name]_[cfg identifier -> ControllerConfig member, H17]
// [COLUMN]_[label]_[GUI display string]
// [COLUMN]_[section]_[GUI bucket]
// [COLUMN]_[meta]_[CfgFieldDescriptor OR-flags]_[[IS_BOOT_ONLY] [WARN_ON_CLAMP]]
// [COLUMN]_[payload]_[ctor matching KIND_TOKEN]
// [COLUMN]_[tooltip]_[operator help - nullptr = inherit GUI field_defs]
//======================================================================
// [CODE]
//======================================================================
#define FOREACH_GLOBAL_CFG_FIELD(X)                                               \
    /* === System / Operational (5) === */                                        \
    X(uint16_t, KIND_INT, num_execution_nodes, "Execution Nodes", "Operational",  \
      IS_BOOT_ONLY | WARN_ON_CLAMP, INT(1, 1, 16), "Number of shards.")           \
    /* === Engine timing (5) === */                                               \
    X(uint32_t, KIND_INT, poll_interval, "Poll Interval", "Engine Timing",        \
      WARN_ON_CLAMP, INT(100, 1, 1000000), "Ticks between slow-path runs.")
//======================================================================
// [END_CODE]
//======================================================================
// [ROW]_[num_execution_nodes]_[cap 16 = the shard ceiling per H22 + Limits.hpp, not arbitrary]
// [ROW]_[TOMBSTONE]_[retired-id-example — retired slot kept, never reused, H21]
//   (SPARSE — most rows carry their per-row help in the tooltip column, not a [ROW])
//======================================================================
// [COMMENT]
//~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
// [[2026-06-11] [v5.15.5.F.4d.1.E.1.1]]
//----------------------------------------------------------------------
// the engine-wide half of the cfg-field split; the per-node half is
// FOREACH_PER_NODE_CFG_FIELD. one X-macro row -> parser + GUI render +
// tooltip + validation all auto-flow (H17). group dividers stay verbatim;
// the plugin derives the section TOC from them.
// [SUPPORTING_DOCS]
//   - [DESIGN_SPEC]_[universal-cfg-field-registry-pattern]
//   - [DESIGN_SPEC]_[registry-tuple-as-single-source-of-truth]
//   - [INVARIANT]_[H17]
//   - [INVARIANT]_[H15]
//======================================================================
// [DERIVED]   (tool-refreshed — do NOT hand-edit; values here ILLUSTRATIVE)
//----------------------------------------------------------------------
// [ROW_COUNT]_[47]
// [ENROLLED]_[MetaRegistry.hpp]
// [CONSUMERS]_[[ControllerConfig_Load] [PerCoreCfg] [SettingsPanel] [CfgFieldDispatch]]
//======================================================================
// [END_REGISTRY]_[FOREACH_GLOBAL_CFG_FIELD]
//======================================================================


//======================================================================
// [ENUM]_[OrderState]
//----------------------------------------------------------------------
// [TAG]_[[ENGINE] [OMS_DRAINER] [PERSISTENCE]]
// [SCHEMA]_[v1.0]
// [OVERVIEW]_[order lifecycle state — packed into Order.flags_packed bits 2-5; codes are wire/persist-visible]
// [REFERENCE]_[INVARIANT]_[H21]
//======================================================================
// [CODE]
//======================================================================
enum OrderState : uint8_t {
    //---- [SECTION]_[working] ----
    ORDER_PENDING = 0,  // submitted to OMS, not yet on exchange   <- inline name=code meaning STAYS (D-326)
    ORDER_SUBMITTED = 1, ORDER_ACKNOWLEDGED = 2, ORDER_PARTIAL = 3,
    //---- [SECTION]_[terminal] ----
    ORDER_FILLED = 4, ORDER_REJECTED = 5, ORDER_CANCELED = 6, ORDER_TIMEOUT = 7,
    //---- [SECTION]_[recovery] ----
    ORDER_UNKNOWN = 8,  // lost tracking, needs reconciliation
};
//======================================================================
// [END_CODE]
//======================================================================
// [VALUE]_[ORDER_UNKNOWN]_[the only non-terminal recovery sink — a reconcile pass resolves it]
// [VALUE]_[TOMBSTONE]_[retired-state-example]_[the form if a state retires — code never reused, H21]
//======================================================================
// [DERIVED]   (tool-refreshed — do NOT hand-edit; values here ILLUSTRATIVE)
//----------------------------------------------------------------------
// [ROW_COUNT]_[9]
// [SIZE]_[uint8]
// [CONSUMERS]_[[Order.flags_packed] [OMS] [Reconcile]]
//======================================================================
// [END_ENUM]_[OrderState]
//======================================================================


//======================================================================
// [TYPE]_[Money]
//----------------------------------------------------------------------
// [TAG]_[[ENGINE] [CAPITAL_BEARING] [DECIMAL] [DETERMINISM]]
//   (wire-format-ness lives in the H9 [REFERENCE] below — the [WIRE_FORMAT] token is a fence
//    CATEGORY, so it cannot appear as a [TAG] value; v1.1 vocab-alias candidate, see D-347)
// [SCHEMA]_[v1.0]
// [OVERVIEW]_[the money-domain alias = FixedPoint<10,8> — exact decimal at venue 8dp; op family Money_*]
// [REFERENCE]_[DECISION]_[[D-176] [D-181]]
// [REFERENCE]_[INVARIANT]_[[H4] [H9] [H12] [H21]]
//======================================================================
// [CODE]
//======================================================================
using Money = FixedPoint<10, 8>;   // ALIASES the FixedPoint<10,8> specialization
//======================================================================
// [END_CODE]
//======================================================================
// [DERIVED]   (tool-refreshed — do NOT hand-edit; values here ILLUSTRATIVE)
//----------------------------------------------------------------------
// [SIZE]_[16B]
// [ALIGN]_[16]
//======================================================================
// [END_TYPE]_[Money]
//======================================================================

// [ASSERT]_[LAYOUT_LOCK]_[sizeof(Money) == 16]
// [WHY]_[H9 wire pin — ~30 memcmp/SHA/HMAC sites; H21 snapshot-version bump on change]
static_assert(sizeof(Money) == 16, "Money wire pin");
// [ASSERT]_[PADDING_FREE]_[has_unique_object_representations_v<Money>]
// [WHY]_[H12 — memcmp/SHA/HMAC need zero padding]
static_assert(std::has_unique_object_representations_v<Money>, "Money must be padding-free");
// [ASSERT]_[EPOCH_TRIPWIRE]_[MONEY_ENCODING_EPOCH == is_fp_decimal_v<EngineMoneyT>]
// [WHY]_[a 16B-to-16B encoding flip is invisible to sizeof — the trait-keyed guard is the net]
static_assert(MONEY_ENCODING_EPOCH == 1, "encoding epoch tripwire");


//----------------------------------------------------------------------
// [MACRO]_[BITMAP_IS_SET]
// [TAG]_[[ENGINE] [BITMAP_PACKED]]
// [SCHEMA]_[v1.0]
// [OVERVIEW]_[branchless single-bit test over a bitmap field — LIGHT unit, no closer]
// [DERIVED]
// [BRANCHES]_[0 — pure mask + compare]
//----------------------------------------------------------------------
#define BITMAP_IS_SET(field, mask)  (((field) & (mask)) != 0)


//----------------------------------------------------------------------
// [TEST]_[test_config_parser]
// [TAG]_[[ENGINE] [TEST_INFRASTRUCTURE]]
// [SCHEMA]_[v1.0]
// [OVERVIEW]_[engine.cfg parse -> ControllerConfig fields + pct-to-fraction coercion + missing-file defaults]
// [REFERENCE]_[INVARIANT]_[H17]
//----------------------------------------------------------------------
static void test_config_parser() {
    // check("poll_interval parsed", cfg.poll_interval == 50);   <- check()s STAY inline (D-326)
    // check("missing file returns defaults", def.poll_interval == 100);
}


//======================================================================
// [STRATEGY]_[<Name>]
//----------------------------------------------------------------------
// [TAG]_[[ENGINE] [SLOW_PATH]]
// [SCHEMA]_[v1.0]
// [OVERVIEW]_[one-line gist — signal source + regime fit; /strategy-template instantiates this block]
// [REFERENCE]_[INVARIANT]_[H22]
//======================================================================
// [CODE]
//======================================================================
// template <unsigned F> struct <Name>State { int initialized; };
// ... the 4 lifecycle functions (Init / Adapt / BuildParameters / ExitAdjustSharded) ...
//======================================================================
// [END_CODE]
//======================================================================
// [DERIVED]   (tool-refreshed — filled by the tools at conversion; empty skeleton is correct, D-327)
//======================================================================
// [END_STRATEGY]_[<Name>]
//======================================================================


//======================================================================
// [FUNCTION]_[ud_parse_execution_report]
//----------------------------------------------------------------------
// [TAG]_[[ENGINE] [OMS_DRAINER] [CAPITAL_BEARING]]
// [SCHEMA]_[v1.0]
// [OVERVIEW]_[parse a Binance executionReport JSON fill event -> Command; returns 1 on x==TRADE]
// [REFERENCE]_[SOURCE]_[Binance WS executionReport docs]
// [REFERENCE]_[INVARIANT]_[[H5] [H21]]
// ---- the venue field-map: tier-2 [WIRE_FIELD] members, key-addressed (D-345) ----
// [WIRE_FIELD]_[e]_[event type = executionReport]
// [WIRE_FIELD]_[x]_[execution type — TRADE = fill]
// [WIRE_FIELD]_[c]_[clientOrderId — our idempotency key, oms_<id>]
// [WIRE_FIELD]_[i]_[exchange orderId]
// [WIRE_FIELD]_[L]_[last executed price]
// [WIRE_FIELD]_[l]_[last executed quantity]
// [WIRE_FIELD]_[n]_[commission amount]
// [WIRE_FIELD]_[N]_[commission asset]
// [WIRE_FIELD]_[t]_[trade id — dedup]
// [WIRE_FIELD]_[T]_[transaction time ms]
// [EXCLUDED]_[z]_[cumulative filled qty — CURRENTLY UNPARSED; the A2 partial-fill gap made VISIBLE]
// [FUTURE_WORK]_[TECH_DEBT]_[TECH_DEBT-169]
//======================================================================
// [CODE]
//======================================================================
static inline int ud_parse_execution_report(const char* json, int len,
                                            Command* cmd_out, uint64_t* trade_id_out);
//======================================================================
// [END_CODE]
//======================================================================
// [END_FUNCTION]_[ud_parse_execution_report]
//======================================================================
