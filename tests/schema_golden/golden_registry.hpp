// Copyright (c) 2026 Jennifer Lewis. All rights reserved.
// Licensed under the GNU Affero General Public License v3.0 (AGPL-3.0).
// See LICENSE file in the project root for full license text.
//
// DOGFOOD FIXTURE (E.1.2.A phase 3) — real unit, copied + converted, NEVER compiled.
// Source: CoreFrameworks/CfgFieldRegistry.hpp:262-301 @ engine d4812de (2026-07-15 copy).
// Shape exercised: X-MACRO REGISTRY with per-row tooltip columns + group dividers threaded
// through `\`-continuations (survey B gap #1 — THE biggest hole; the [COLUMN]/[ROW] answer:
// the legend lives in the ORIENT region, the macro body stays byte-verbatim, so a schema tag
// never meets the backslash-continuation).
// Slice notes: 5 of the real 47 rows (representative — the System/Operational group + the
// Engine-timing divider); ONE deviation from byte-verbatim, documented: the trailing `\`
// line-continuation is REMOVED from the final included row so the slice is a syntactically
// complete macro. NO [ROW] rationale lines — the source carries per-row help in the tooltip
// column, and [ROW] is SPARSE by design (zero is a valid count).
// Lossless accounting: zero drops; the pre-macro NOTE + banner text relocated VERBATIM.

//======================================================================
// [REGISTRY]_[FOREACH_GLOBAL_CFG_FIELD]
//----------------------------------------------------------------------
// [TAG]_[[ENGINE] [FRAMEWORK_DISCIPLINE] [CFG_FLOW]]
// [SCHEMA]_[v1.0]
// [OVERVIEW]_[47 rows — operator sets once for the whole engine; not per-core. Add a field = 1 row; parser + GUI + tooltip + validation auto-flow, H17]
// [COLUMN]_[STORAGE_T]_[C storage type — signed/unsigned widths unified under KIND_INT; T deduced via the X-macro extractor, H13/H14]
// [COLUMN]_[KIND_TOKEN]_[GUI-metadata kind]_[[KIND_INT] [KIND_BOOL] [KIND_DOUBLE] [KIND_STRING] [KIND_INT_ENUM]]
// [COLUMN]_[name]_[cfg identifier -> ControllerConfig member, H17]
// [COLUMN]_[label]_[GUI display string]
// [COLUMN]_[section]_[GUI bucket]
// [COLUMN]_[meta]_[CfgFieldDescriptor OR-flags]_[[IS_BOOT_ONLY] [WARN_ON_CLAMP]]
// [COLUMN]_[payload]_[ctor macro matching KIND_TOKEN — DBL / INT / BOOL / INT_ENUM]
// [COLUMN]_[tooltip]_[operator help; pre-existing GUI tooltips preserved BYTE-IDENTICAL via raw strings]
// [COLUMN]_[STRAT/OP_MODE/REGIME/RISK_CAT]_[applicability filters — category tokens]
// [COLUMN]_[storage_class]_[cfg storage tier]_[[STRUCT_CFG]]
//======================================================================
// [CODE]
//======================================================================

// Payload helper macros (one per Kind family):
#define DBL(default_val, clamp_min, clamp_max) { .as_double = { (default_val), (clamp_min), (clamp_max) } }
// v5.15.5.F.4c — KIND_INT / KIND_BOOL / KIND_INT_ENUM payload macros.
// INT: signed/unsigned widths (int8/16/32/64) all unified under KIND_INT per
// H13/H14 (Kind = GUI metadata; T deduced via X-macro extractor handles width).
// Storage-width safety: per-row static_assert that clamp fits destination type's
// numeric_limits is enforced at the FOREACH_CFG_FIELD walker site.
#define INT(default_val, clamp_min, clamp_max) \
    { .as_int = { (int64_t)(default_val), (int64_t)(clamp_min), (int64_t)(clamp_max) } }
#define BOOL(default_val) { .as_bool = { (uint8_t)(default_val) } }
#define INT_ENUM(default_val, labels_array, count) \
    { .as_int_enum = { (int)(default_val), (labels_array), (uint8_t)(count) } }

#define FOREACH_GLOBAL_CFG_FIELD(X)                                                                                                                                                                                  \
    /* === System / Operational (5) === */                                                                                                                                                                            \
    X(uint16_t,             KIND_INT,        num_execution_nodes,         "Execution Nodes",      "Operational",     CfgFieldDescriptor::IS_BOOT_ONLY | CfgFieldDescriptor::WARN_ON_CLAMP, INT(1, 1, 16),                                  \
        "Number of per-node execution shards. Clamp [1, 16].",                                                                                                                                                     \
        STRAT_CAT_ALL,                                       OP_MODE_CAT_ALL, REGIME_CAT_ALL, RISK_CAT_ALL, CfgFieldDescriptor::STRUCT_CFG) \
    X(int,                  KIND_BOOL,       require_mlockall,            "Require mlockall",     "Operational",     CfgFieldDescriptor::IS_BOOT_ONLY | CfgFieldDescriptor::WARN_ON_CLAMP, BOOL(0),                                       \
        "Pin engine memory at boot via mlockall(2) — prevents swap-out under memory pressure. Requires CAP_IPC_LOCK or root. Boot-only; runtime changes ignored.",                                                  \
        STRAT_CAT_ALL,                                       OP_MODE_CAT_ALL, REGIME_CAT_ALL, RISK_CAT_ALL, CfgFieldDescriptor::STRUCT_CFG) \
    X(int,                  KIND_BOOL,       init_arena_use_hugepages,    "Use Hugepages",        "Operational",     CfgFieldDescriptor::IS_BOOT_ONLY | CfgFieldDescriptor::WARN_ON_CLAMP, BOOL(0),                                       \
        "Initialize per-node arenas with 2MB hugepages (MAP_HUGETLB). Reduces TLB pressure on hot path. Requires /sys/kernel/mm/hugepages configured. Boot-only.",                                                   \
        STRAT_CAT_ALL,                                       OP_MODE_CAT_ALL, REGIME_CAT_ALL, RISK_CAT_ALL, CfgFieldDescriptor::STRUCT_CFG) \
    X(uint8_t,              KIND_BOOL,       sharded_force_synthetic,     "Force Synthetic Ticks","Operational",     CfgFieldDescriptor::IS_BOOT_ONLY | CfgFieldDescriptor::WARN_ON_CLAMP, BOOL(0),                                       \
        "Debug/test toggle — force sharded engine to use synthetic tick generator instead of real Binance WS feed. Used for offline reproducibility tests. Boot-only.",                                              \
        STRAT_CAT_ALL,                                       OP_MODE_CAT_ALL, REGIME_CAT_ALL, RISK_CAT_ALL, CfgFieldDescriptor::STRUCT_CFG) \
    X(int,                  KIND_INT,        slow_path_pin_offset,        "Slow-Path Pin Offset", "Operational",     CfgFieldDescriptor::IS_BOOT_ONLY | CfgFieldDescriptor::WARN_ON_CLAMP, INT(-1, -1, 256),                               \
        "Slow-path CPU pin offset. -1 = disabled, 0 = auto, >0 = explicit CPU offset.",                                                                                                                             \
        STRAT_CAT_ALL,                                       OP_MODE_CAT_ALL, REGIME_CAT_ALL, RISK_CAT_ALL, CfgFieldDescriptor::STRUCT_CFG)
/* (fixture slice — the Engine-timing divider + 42 more rows continue in the real registry) */

//======================================================================
// [END_CODE]
//======================================================================
// [COMMENT]_[what it single-sources]
//----------------------------------------------------------------------
// [FOREACH_GLOBAL_CFG_FIELD — system / training / recording / engine-wide mode / ack / notify / logging]
// 47 rows. Operator sets once for the whole engine; not per-core.
//
// NOTE: tooltips for fields PRE-EXISTING in GUI/SettingsPanel.hpp:46-289 field_defs[]
// preserved BYTE-IDENTICAL via raw strings. Fields NEW to GUI (no pre-existing entry)
// have author-supplied tooltips. HIGH-6 tooltip-preservation discipline per
// plan + DESIGN_SPECS/registry-tuple-as-single-source-of-truth.md.
// [SUPPORTING_DOCS]
//   - [DESIGN_SPEC]_[registry-tuple-as-single-source-of-truth]
//   - [DESIGN_SPEC]_[universal-cfg-field-registry-pattern]
//   - [INVARIANT]_[H17]
//   - [INVARIANT]_[H15]
//======================================================================
// [DERIVED]   (tool-refreshed — do NOT hand-edit; fixture placeholders)
//----------------------------------------------------------------------
// [ROW_COUNT]_[47 in the real registry — 5 in this slice]
// [ENROLLED]_[MetaRegistry.hpp]
// [CONSUMERS]_[[ControllerConfig_Load] [PerCoreCfg] [SettingsPanel] [CfgFieldDispatch]]
//======================================================================
// [END_REGISTRY]_[FOREACH_GLOBAL_CFG_FIELD]
//======================================================================
