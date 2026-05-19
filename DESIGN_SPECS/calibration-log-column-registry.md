---
type: framework-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-10
tags: [framework-discipline, wire-format, structural-fix]
surface: [registry, wire-format]
sister_specs: [registry-tuple-as-single-source-of-truth.md, wire-format-byte-preservation-discipline.md, curve-registry-pattern.md, x-macro-registry-with-presence-dispatch.md]
applies_at_skills: []
---

# Calibration log column registry pattern (FOREACH_<LOGNAME>_COL — auto-generated CSV header + row)

**Established:** 2026-05-10 (v5.14.10.D — FOREACH_CALIB_LOG_COL refactor of OrderManager_HandleFill calibration log writer)
**Status:** ACTIVE
**Cross-references:**
- First application: `DataStream/CalibLogColRegistry.hpp` + `CoreFrameworks/OrderManager.hpp:991-1019` (refactored row emit) + `:1293-1295` (refactored header emit)
- Sister pattern: `registry-tuple-as-single-source-of-truth.md` (this is a specific application of registry-tuple-SSOT to log columns)
- Sister pattern: `wire-format-byte-preservation-discipline.md` (CSV format byte preservation across refactor)
- Sister pattern: `curve-registry-pattern.md` (registry-driven dispatch; same X-macro shape)
- TECH_DEBT-010 (closed by v5.14.10.D — first application proves pattern)
- CLAUDE.md item 13 (X-macro registry for multi-site additions)

---

## Problem statement

Log writers (CSV, JSONL, structured event logs) accumulate columns over time. Each new column requires updates at THREE sites in lockstep:

1. **Header constant** — declares the column position + name in the CSV header row
2. **Row writer** — fprintf format string + value expression for the per-row emit
3. **Reader / parser** — operator-side analyzer that reads the CSV (often Python pandas with `read_csv`)

When a new column is added:
- Forget to update the header → CSV malformed (operator parsers misalign columns)
- Forget to update the row writer → CSV missing the value (default 0 / empty / NaN downstream)
- Wrong fprintf format → silent data loss (e.g., `%d` instead of `%.4f` for a price)
- Reorder existing columns → operator parsers break silently (column index ≠ name)

This is the same N-site bug class as cfg fields, has_* flags, snapshot fields. The X-macro registry pattern solves it for log columns.

**Worked example: TECH_DEBT-010 (v5.14.10.D close).** The OrderManager calibration log had 9 hand-coded columns at 3 sites:
- `OrderManager.hpp:1293-1295` — header literal `"timestamp_us,slot,exit_predicted_flag,...\n"`
- `OrderManager.hpp:1008-1013` — row fprintf `"%llu,%d,%u,%.6f,..."`
- Operator-side parser (Python pandas) reads the 9 columns by position

Adding a 10th column required 3-site update plus operator parser update. The /merge-scan finding M2 identified that v5.14.10.D's cfg=2 telemetry would add 3+ columns — exactly the trigger for converting to a registry.

---

## When does it apply? (Trigger conditions)

Apply this pattern when ALL of the following hold:

1. **CSV / structured log format** — output is column-based with a header row + per-row tuples
2. **≥3 columns** — single-column logs don't need a registry; 2-3 columns is borderline; ≥3 columns benefit
3. **Operator-side parsers depend on column ORDER + NAME** — wire format byte preservation matters
4. **Future column additions expected** — registry pays off when ≥1 future column lands; if format is frozen, manual is fine
5. **Row write site has access to all column values** — getter expressions must compile in the caller's scope

---

## The pattern (concrete shape)

### Step 1: Define the registry tuple

```cpp
// FOREACH_<LOGNAME>_COL — column name, printf fmt, value expression
//   col_name    — bare identifier; used for CSV header AND macro-generated names
//   printf_fmt  — per-column printf format string (e.g. "%llu", "%.4f")
//   value_expr  — expression read at row-write time; MUST be valid in caller scope

#define FOREACH_CALIB_LOG_COL(X)                                                              \
    X(timestamp_us,        "%llu",  (unsigned long long)ts_us)                                \
    X(slot,                "%d",    (int)pslot)                                               \
    X(exit_predicted_flag, "%u",    (unsigned)pred_flag)                                      \
    X(predicted_p,         "%.6f",  pred_p)                                                   \
    X(entry_price,         "%.4f",  entry_d_calib)                                            \
    X(exit_price,          "%.4f",  exit_d_calib)                                             \
    X(gain_pct,            "%.6f",  gain_pct)                                                 \
    X(realized_pnl_bps,    "%.4f",  pnl_bps)                                                  \
    X(was_win,             "%d",    (int)oms->last_fill[pslot].was_win)
```

**ORDER MATTERS.** Existing operator parsers read by column position. NEVER reorder existing columns; APPEND new columns at the end.

### Step 2: Caller scope contract

Document explicitly what variables the row-write expansion needs in scope:

```cpp
// CALLER SCOPE CONTRACT (HandleFill body):
//   uint64_t ts_us, int pslot, uint8_t pred_flag, double pred_p,
//   double entry_d_calib, double exit_d_calib, double gain_pct, double pnl_bps,
//   OrderManagerState<F>* oms
```

Without this contract documented, future contributors will write registry entries that fail to compile in the caller scope.

### Step 3: Header emitter (function — single fixed implementation)

```cpp
inline void CalibLog_EmitHeader(FILE* f) {
    if (!f) return;
    int first = 1;
    #define X_GEN_CALIB_LOG_HEADER(name, fmt, expr) \
        do { fprintf(f, first ? "%s" : ",%s", #name); first = 0; } while (0);
    FOREACH_CALIB_LOG_COL(X_GEN_CALIB_LOG_HEADER)
    #undef X_GEN_CALIB_LOG_HEADER
    fprintf(f, "\n");
}
```

The `#name` stringification turns the bare identifier into a string literal at compile time. Comma separator added by ternary; first column has no leading comma.

### Step 4: Row emitter (macro — caller-scoped expansion)

```cpp
#define CALIB_LOG_EMIT_ROW(file_handle)                                       \
    do {                                                                       \
        int _calib_first = 1;                                                  \
        FILE* _calib_f = (file_handle);                                        \
        if (_calib_f) {                                                         \
            FOREACH_CALIB_LOG_COL(X_GEN_CALIB_LOG_ROW)                         \
            fprintf(_calib_f, "\n");                                           \
        }                                                                       \
    } while (0)

#define X_GEN_CALIB_LOG_ROW(name, fmt, expr)                                   \
    do {                                                                        \
        fprintf(_calib_f, _calib_first ? fmt : "," fmt, (expr));                \
        _calib_first = 0;                                                       \
    } while (0);
```

Why a MACRO (not a function): the value_expr in each registry entry must execute in CALLER scope (where local variables like `ts_us`, `pslot` are defined). A function would require a 9-arg signature passing all values — which defeats the registry point.

The internal `_calib_first` + `_calib_f` are macro-local locals to avoid clashing with caller variables.

### Step 5: Caller refactor (drop hand-coded fprintf)

Before:
```cpp
fprintf(oms->calibration_log_file,
    "%llu,%d,%u,%.6f,%.4f,%.4f,%.6f,%.4f,%d\n",
    (unsigned long long)ts_us, (int)pslot,
    (unsigned)pred_flag, pred_p, entry_d_calib, exit_d_calib,
    gain_pct, pnl_bps, (int)oms->last_fill[pslot].was_win);
```

After:
```cpp
CALIB_LOG_EMIT_ROW(oms->calibration_log_file);
```

Same byte output; one-line caller; future column additions = 1 row in the registry.

---

## Trade-offs + when to apply

### Apply when:
- Log has ≥3 columns
- Future column additions expected (within reasonable horizon)
- Operator parsers depend on byte-format byte preservation
- Caller scope can declare all column values (or pass them via a struct)

### Skip when:
- Single-column or 2-column log (registry overhead not justified)
- Format is frozen (no expected future additions)
- Caller scope can't expose all column values cleanly (refactor first)
- Output is binary (registry is for printf-style fmt; binary needs different shape)

### Cost:
- ~50-100 LOC for registry + header emitter + row emitter macro
- ~10 LOC per existing column to migrate (mechanical)
- 1 line per future column added (registry append)

### Win:
- Adding a new column = 1 row in registry; auto-flows to header + row emit
- Operator parsers see consistent column order (registry IS the source of truth)
- Format strings co-located with column definition (less drift risk)
- Rename column = 1 site change (registry entry); not 3 sites
- Reorder columns = 1 registry rearrangement (BUT operator parsers break — never do this in shipping code)

---

## Wire-format byte preservation

When refactoring an EXISTING log writer (operator parsers depend on the format), the registry emit MUST produce byte-identical output to the pre-refactor code. Validation:

1. **Construct a test fixture** with known input values
2. **Capture pre-refactor output** by running the old code
3. **Refactor** to use the registry
4. **Capture post-refactor output** by running the new code
5. **memcmp** the two outputs — must match byte-for-byte

If they differ, the registry tuple has wrong fmt OR wrong value_expr OR wrong column order. Bisect to find the offending entry.

For v5.14.10.D, the refactor is mechanical: same fmt + same value expressions + same column order. Byte-format preservation is automatic IF the registry is constructed faithfully from the prior hand-coded literal.

---

## Reference applications

| Application | Registry | Site | Notes |
|---|---|---|---|
| v5.14.10.D | FOREACH_CALIB_LOG_COL | `DataStream/CalibLogColRegistry.hpp` + `CoreFrameworks/OrderManager.hpp:991-1019` | First application; 9 cols; fprintf-direct emit; 1 writer (HandleFill) |
| v5.14.10.F | FOREACH_TRADE_LOG_COL | `CoreFrameworks/TradeLogColRegistry.hpp` + `CoreFrameworks/ShardedTradeLog.hpp:200-270` | Second application; 11 cols; snprintf-to-buffer + fwrite (P8.3 truncation guard pattern); 2 writers (RecordEntry, RecordExit) sharing single row shape via caller-scope variable population |

(Future ships extending the pattern: append rows here.)

---

## Pattern variants

### Variant A — fprintf direct (single writer; small log)

Used by FOREACH_CALIB_LOG_COL (v5.14.10.D). Writer body uses a row-emit
MACRO that walks the registry and calls `fprintf` per-column to the file
handle directly. Caller scope contract: file handle in scope; all column
value variables in scope.

Pros: simple; minimal stack usage.
Cons: each `fprintf` is a separate syscall (buffered by libc; ~free) but
not single-write-atomic.

### Variant B — snprintf to buffer + fwrite (multi-writer, atomic-write requirement)

Used by FOREACH_TRADE_LOG_COL (v5.14.10.F). Writer body uses a row-emit
MACRO that walks the registry and calls `snprintf` per-column appending
to a stack buffer. Caller then `fwrite`s the entire buffer once
(atomic-per-row); truncation guard via `n >= bufsz`. Caller scope contract:
buffer + bufsz + out_n_ptr in scope; all column value variables in scope.

Pros: atomic per-row write; truncation guard via snprintf bounded behavior;
preserves P8.3-style logging discipline.
Cons: stack buffer (1KB typical); slightly more complex macro expansion.

### Choosing between Variants

- Single writer + fprintf-buffered logging OK → Variant A (simpler)
- Multiple writers OR atomic-row requirement OR truncation-guard requirement → Variant B
- Mixed row shapes (e.g., MetricsLog SlowPath vs Event with different column
  populations per writer) → DEFER (registry pattern doesn't cleanly fit;
  use per-writer hand-coded emit OR design a 2-stage approach where each
  writer sets caller-scope variables to "blank-marker" sentinels for
  un-populated columns)

---

## Future application candidates

| Candidate | Current state | Trigger to migrate |
|---|---|---|
| MetricsLog (engine metrics CSV) | DEFERRED v5.14.10.F — multi-writer with different row shapes (SlowPath: 26 cols populated + blank details; Event: 13 cols + blank middle + populated details). See TECH_DEBT-031. Awkward fit; no clean Variant A or B mapping without redesign. | Operator-driven cleanup ship OR major MetricsLog rework |
| TradeLog (single-core legacy CSV) | Hand-coded fprintf | Likely deprecated in v6.0+ multi-core sweep; skip migration |
| cfg=2 dual-mode telemetry columns (exp3_chosen_arm, thompson_chosen_arm, regime_id_at_pick) for FOREACH_CALIB_LOG_COL | DEFERRED v5.14.10.D — needs Order struct or OMS state extension to flow data from predict-time to fill-time. See TECH_DEBT-030. | When per-fill bandit telemetry wiring lands (likely v5.14.10.E+ or v5.14.11+) |
| Maker/taker fee bifurcation columns (FOREACH_TRADE_LOG_COL extension) | Pending v6.0 maker work | When maker order MVP ships |

---

## Lessons / gotchas

### `#name` stringification

The X-macro entries use `#name` (preprocessor stringification) to turn the bare identifier into a string literal. This is the same trick FOREACH_STAMP_BOUND_CFG uses. Standard C99/C++; works on all compilers we target.

### Macro-local variables avoid caller clashes

`_calib_first` + `_calib_f` are prefixed with underscore to avoid clashing with caller-scope variables. If the caller has a variable named `first`, the macro's `int _calib_first` doesn't collide. Always prefix macro-local names.

### Caller scope contract is brittle

If the registry's value_expr column references a variable that ISN'T in the caller's scope, the compile fails — but the error messages may be cryptic (preprocessor expansion of macros makes line numbers misleading). Document the caller scope contract IN-FILE so future contributors know what variables to declare before invoking the row emitter macro.

### Don't reorder existing columns

Shipped CSVs are read by operator parsers via column position. Reordering breaks those parsers SILENTLY (data lands in wrong column; no error message; downstream analysis corrupted). NEVER reorder existing columns; ALWAYS append new columns at the end.

### Type-correct value expressions

The fmt + value_expr must agree on type:
- `"%llu"` requires `(unsigned long long)`
- `"%d"` requires `(int)`
- `"%.4f"` requires `double` (or `float` — implicitly promoted)
- Mismatch → undefined behavior (sometimes works on x86, fails on ARM)

Always explicit-cast the value_expr to match the fmt's expected type.

### Trailing newline

The header emitter adds `\n` AFTER walking all columns. The row emitter does the same. Don't add `\n` inside individual entry fmts — would produce garbage CSV with multi-line rows.

### File handle nullable

The row emitter accepts a nullable FILE*. If `cfg.calibration_log_path` is empty, `oms->calibration_log_file` stays `nullptr`; the emitter skips silently. This matches the pre-refactor pattern (`if (oms->calibration_log_file) {...}`).

---

## Audit detection

`/dod-audit` flags missed applications by:

- Symptom: hand-coded fprintf with ≥3 column-style format strings (`"%llu,%d,%.4f,..."`) and a sibling header literal (`"col1,col2,col3,..."`) elsewhere in the same file
- Symptom: log writer recently extended with a new column via 3-site update (header + row + parser) — the next column addition triggers refactor
- Symptom: operator parser file referenced in cross-refs (e.g., `operator_calib_analyzer.py`) — confirms the format has external consumers (registry + byte preservation matter)

When detected → flag as `MISSED — calibration-log-column-registry-pattern`. Recommended fix: apply pattern Steps 1-5.

---

## Cross-references

- `registry-tuple-as-single-source-of-truth.md` — meta-pattern this is an instance of
- `wire-format-byte-preservation-discipline.md` — sister concern (preserves bytes during refactor)
- `curve-registry-pattern.md` — sister pattern (registry-driven dispatch; same X-macro shape)
- `x-macro-registry-with-presence-dispatch.md` — base X-macro pattern
- FoxML_Trader_v2 `CLAUDE.md` item 13 (X-macro registry for multi-site additions)
- FoxML_Trader_v2 `DOCS/TECH_DEBT.md` TECH_DEBT-010 (closed by v5.14.10.D — first application)
- FoxML_Trader_v2 `DataStream/CalibLogColRegistry.hpp` — reference implementation
- FoxML_Trader_v2 `CoreFrameworks/OrderManager.hpp:991-1019` — first refactored caller
