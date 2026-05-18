# Failure-attribution buffer pattern

**Established:** 2026-05-17 (v5.15.5.F.4d.1.B.3 planning — codified Stage 2 DRAFT after `.B.3` audit-cycle codebase scan surfaced 3 existing canonical applications across distinct subsystems; first canonical reference at `.B.3` ship close)
**Status:** **Stage 2 DRAFT v1.0** (Stage 1 problem identified at `.B.2` Discovery 10 — drift walker reason buffer preservation; codebase scan at `.B.3` audit cycle found 3 existing canonical applications + Decision B at `.B.3` is the 4th canonical → Stage 2 DRAFT warranted per `pattern-codification-lifecycle.md`)
**Tags:** failure-attribution, caller-allocated-buffer, framework-discipline, surface-g-discipline-sister; serves operator-UX preservation under framework refactoring; closes recurring shape across drift / overfit-detection / reconciliation / parser / scaler validation surfaces

**Cross-references:**
- Sister: `autopopulate-pattern-for-production-caller-class.md` (production-caller field population — close shape but distinct concern; autopopulate populates STRUCT FIELDS; this pattern populates ATTRIBUTION BUFFER)
- Sister: `wire-format-byte-preservation-discipline.md` Layer 6 Surface G (parser tolerance for absent fields — sister discipline for back-compat at parse layer)
- Sister: `canonical-sister-extension-discipline.md` (the discipline-of-checking-existing-patterns that surfaced this codification)
- Closes: drift-walker reason preservation under framework refactoring (Class 18 mirror risk at attribution layer if pattern not codified)
- CLAUDE.md item 31 (framework-driven extensibility meta-principle — applies to attribution shape)

---

## Problem statement

When a function detects a failure condition that operator needs to act on (drift detected at model load; overfit detected during training; order reconciliation refusal; parser error; scaler validation failure), the function must communicate:
1. **WHAT failed** — categorical failure mode (drift / refuse / parse-error)
2. **WHY it failed** — specific attribution (which field; which value; which constraint)

Communication via return code suffices for (1) but loses (2). Communication via global error state (errno-style) breaks under multi-threading + multi-failure scenarios.

The CANONICAL shape across the codebase: **caller-allocated character buffer** passed by pointer; **callee writes first-failure attribution** via snprintf into the buffer; **first-failure-wins** semantic (subsequent failures don't overwrite — preserves the earliest signal which is usually the root cause).

When migrating manual failure-detection code to framework-driven walkers (e.g., drift_check_from_derived consuming master cfg registry instead of legacy FOREACH_STAMP_BOUND_CFG inline walk), the framework signature must preserve the attribution shape — else operator UX regresses to "drift detected" with no WHICH-field detail.

This pattern codifies the shape so future framework refactoring at any of the 4+ existing surfaces can preserve attribution mechanically.

---

## Design space explored

### Option A — Return code only (no attribution)

Function returns success/failure code. No attribution buffer. Caller decides UX via return code alone.

**Rejected.** Loses (2). Operator sees "load failed" without WHICH field drifted. Debugging requires re-load with verbose logging or manual inspection.

### Option B — Global error state (errno-style)

Function sets thread-local global on failure. Caller reads after call.

**Rejected.** errno-style breaks under nested failure scenarios. Multi-failure (multi-field drift) loses info. Thread-local imposes coordination overhead under per-core sharding.

### Option C — Failure-record array (multi-failure)

Function fills caller-allocated array of structured failure records (struct with field_name + stamp_value + cfg_value + severity per record). Caller iterates post-call.

**Rejected for THIS shape.** Over-engineering for the canonical case where first-failure-wins suffices. Existing 4 codebase surfaces all use the simpler char-buffer shape. Adopt structured array shape ONLY when a future surface genuinely needs multi-failure attribution (e.g., a validation pipeline that aggregates errors).

### Option D — Caller-allocated char buffer + framework writes first-failure attribution (CHOSEN)

```cpp
// Caller:
ModelStampResult sr{};  // sr.reason is char[256] caller-allocated
verify_model_stamp(path, secret, gap, version, ..., &sr);
if (sr.valid <= 0) {
    fprintf(stderr, "Refused: %s\n", sr.reason);  // operator sees WHICH field
}

// Callee:
inline void framework_drift_check(..., char* reason_buf, size_t reason_cap) {
    for (each drift instance) {
        if (drifted) {
            failure_flags |= FAILURE_MASK_X;
            if (reason_buf && reason_buf[0] == '\0') {
                snprintf(reason_buf, reason_cap, "<field> drift: stamp=%s cfg=%s", ...);
            }
        }
    }
}
```

Three structural properties:
- **Caller-allocated**: framework writes to operator-provided buffer; framework holds no per-call state. Compatible with H1 (no malloc) + H3 (no shared mutex).
- **First-failure-wins**: snprintf only if buf is empty. Subsequent drifts don't overwrite. Preserves earliest signal.
- **Nullable opt-in**: framework checks `reason_buf != nullptr` — caller can opt out (passing nullptr) when attribution isn't needed.

**Chosen as canonical pattern** for failure-attribution at framework refactoring boundaries.

---

## The pattern (concrete shape)

### Per-call shape

```cpp
// Function signature pattern:
inline ReturnT framework_<verb>(
    /* primary inputs */,
    /* output struct */ OutputT* out,
    char* reason_buf,          // caller-allocated; nullable
    size_t reason_cap          // sizeof caller buffer
);

// First-failure-wins snprintf idiom:
if (failure_detected) {
    *out.failure_flags |= FAILURE_MASK_X;
    if (reason_buf && reason_buf[0] == '\0') {
        snprintf(reason_buf, reason_cap, "<attribution format>", ...);
    }
}
```

### Buffer sizing convention

- **256 bytes** for long-form attribution (drift detail with field name + stamp value + cfg value formatted) — matches `ModelStampResult.reason` + `Reconcile.refusal_reason`
- **128 bytes** for medium-form (e.g., overfit detection categorical attribution) — matches `OverfitDetection.reason`
- **32 bytes** for short categorical (REJECTED/RECONCILED) — matches `OrderEventLog.reason`; different shape (categorical labels, NOT free-form attribution); not this pattern

This pattern targets the 128-256 byte free-form attribution shape.

### Framework-extension shape (canonical at `.B.3`)

```cpp
// MemHeaders/CfgGateRegistry.hpp — cfg_derived::drift_check_from_derived
template <unsigned F, typename HandleT>
inline void drift_check_from_derived(
    uint64_t& failure_flags,
    bool stamp_has_inference_cfg,
    uint64_t failure_mask,
    const HandleT& handle,
    const ControllerConfig<F>& cfg,
    int& drift_count,
    char* reason_buf,          // NEW at .B.3
    size_t reason_cap          // NEW at .B.3
) {
    // ... framework walker ...
    if (_drifted) {
        BITMAP_SET(failure_flags, failure_mask);
        drift_count++;
        if (reason_buf && reason_buf[0] == '\0') {
            snprintf(reason_buf, reason_cap,
                "%s drift: stamp=%g cfg=%g",
                cfg_field_name, stamp_value, cfg_value);
        }
    }
}
```

Caller (`CoreModelZoo.hpp:225-247`) provides `sr.reason` + `sizeof(sr.reason)`.

---

## Trade-offs + when to apply

### Apply when:
- Function detects failures that operator needs to act on
- First-failure-wins attribution is acceptable (vs multi-failure aggregation)
- Function is migrating from manual inline detection to framework-driven walker
- The legacy code uses caller-allocated char buffer + snprintf attribution

### Skip when:
- Failure attribution must include multiple records (use structured array pattern instead)
- Categorical labels suffice (use short-fixed-size buffer per `OrderEventLog.reason` shape; different concern)
- Failures are programmer errors (use assert/SANITIZER, not operator-facing attribution)

### Cost:
- 2 args added to framework signature (~30 LOC total across signature + caller migration)
- Buffer space: caller-allocated, typically 128-256 bytes per struct
- snprintf overhead at failure: ~50-100ns slow-path/load-time only; not hot path

### Win:
- Operator UX preserved across framework refactoring boundaries
- Single attribution mechanism reusable at future surfaces (4+ existing recurrences)
- No global state; multi-threading safe
- Nullable opt-in preserves caller flexibility

---

## Reference implementations

### Existing canonical applications at HEAD (3 surfaces; identified `.B.3` audit cycle)

1. **`ML_Headers/ModelInference.hpp:1166`** — `ModelStampResult.reason[256]` for stamp verification failure attribution. ~8 snprintf write sites covering missing-file / empty-file / engine-version-mismatch / format-version-mismatch / gap-threshold / drift-detected / HMAC-mismatch / load-refused.

2. **`Backtest/OverfitDetection.hpp:50`** — `OverfitResult.reason[128]` for overfit detection. 9 snprintf write sites covering walk-forward / held-out / paired-bootstrap / cross-validation / DSR / variance-explained / IS-OOS-gap / clean-pass.

3. **`CoreFrameworks/Reconcile.hpp:387`** — `ReconcileResult.refusal_reason[256]` for order reconciliation refusal. 1 snprintf write site (per-call detail).

### Stage 3 first reference (this pattern's first explicit application via codified shape)

**`v5.15.5.F.4d.1.B.3` — framework `drift_check_from_derived` extension** (Decision B at `.B.3` plan body):
- File: `MemHeaders/CfgGateRegistry.hpp:315+`
- Extends signature with `char* reason_buf, size_t reason_cap`
- Caller migration: `ML_Headers/CoreModelZoo.hpp:225-247` provides `sr.reason + sizeof(sr.reason)`
- Preserves operator UX from legacy inline drift walker

### Future application catalog

- Scaler validation failure attribution (when refactored to framework consumer)
- Parser error attribution (when parser X-macro patterns extended with attribution buffer)
- Snapshot load failure attribution (when snapshot loader migrates to framework consumer)

---

## Lessons / gotchas

### First-failure-wins is the canonical semantic

Subsequent failures DON'T overwrite. Caller sees the EARLIEST failure which is usually the root cause (cascading failures often share a common origin). Pattern: check `buf[0] == '\0'` (empty marker) before snprintf.

If a future application needs LAST-failure-wins semantic (most-recent failure visible), use a different idiom (clear buf at start of each iteration; snprintf unconditionally). Document the choice + rationale.

### Buffer sizing is per-attribution, not per-call

Each struct (ModelStampResult / OverfitResult / ReconcileResult) sizes its own reason buffer at struct declaration. Framework signature takes the buffer pointer + cap; doesn't impose size policy. Allows different surfaces to size for their attribution detail (256 for full field-name + values; 128 for shorter categorical-style).

### Nullable opt-in is load-bearing

Framework checks `reason_buf != nullptr` BEFORE snprintf. Callers that don't need attribution pass nullptr; framework skips the snprintf overhead entirely. Important for callers that have failure detection without operator-facing UX requirements.

### snprintf locale-pin (per Layer 2)

Failure attribution buffer contents that include numeric values must honor locale-pin per `wire-format-byte-preservation-discipline.md` Layer 2 if the buffer contents become part of a wire-format chain. For pure operator-UX attribution (not wire-format), locale-pin is OPTIONAL. Document choice at caller.

### Cascading failure-flags bit + attribution write coupling

Pattern at the canonical applications:
```cpp
BITMAP_SET(failure_flags, FAILURE_MASK_X);
if (reason_buf && reason_buf[0] == '\0') {
    snprintf(reason_buf, reason_cap, "...");
}
```

The order is: SET the flag FIRST (always; deterministic), THEN write attribution conditionally. Don't gate the flag set on reason_buf presence — failure_flags must be unconditional for downstream logic.

---

## Patterns NOT used here (and why)

### Structured failure-record array

Considered as canonical multi-failure shape. Rejected for THIS pattern because:
- All 4 existing surfaces use simple char-buffer first-failure-wins
- Multi-failure attribution adds complexity for hypothetical future need
- If future surface needs multi-failure aggregation, codify SEPARATELY as `failure-record-array-pattern.md` (different shape)

### Stack-allocated thread-local buffer

Considered. Rejected because:
- Crosses thread boundaries when failure attribution propagates (drift detection at slow-path, operator reads at GUI thread)
- Caller-allocated buffer on operator-visible struct is the canonical cross-thread carrier

### Variadic format vs concrete format strings

Considered: framework takes a variadic format string + args. Rejected because:
- Concrete snprintf calls inline at each failure site are more readable
- Variadic shifts complexity into the framework signature without proportionate gain
- Failure attribution formats are USUALLY simple (1-2 field interpolation); variadic overhead not justified

---

## Pattern lifecycle (per `pattern-codification-lifecycle.md`)

- **Stage 1 (problem identification):** `.B.2` Discovery 10 — drift walker reason preservation under framework refactoring. Codebase scan at `.B.3` audit cycle surfaced 3 existing canonical applications across distinct subsystems.
- **Stage 2 (DESIGN_SPEC draft):** **THIS DOC** (2026-05-17 at `.B.3` planning)
- **Stage 3 (first reference):** `.B.3` ship — `cfg_derived::drift_check_from_derived` framework extension with `reason_buf + reason_cap` args (Decision B at `.B.3` plan body)
- **Stage 4 (cohort migration / 2nd canonical reference):** future ship that refactors scaler validation OR parser error attribution OR snapshot load failure to framework consumer
- **Stage 5+ (CLAUDE.md item promotion):** when 3+ Stage 3 framework applications exist + the pattern becomes load-bearing for cross-subsystem failure-attribution UX

---

## Cross-references

- Sister: `autopopulate-pattern-for-production-caller-class.md` (production-caller field population; close shape but distinct concern — struct fields vs attribution buffer)
- Sister: `wire-format-byte-preservation-discipline.md` Layer 6 Surface G (parser tolerance for absent fields; sister discipline for back-compat at parse layer)
- Sister: `canonical-sister-extension-discipline.md` (the discipline that surfaced this codification via cross-DESIGN_SPECS check)
- Composes with: `cfg-derived-consumer-framework.md` (the framework this pattern's first canonical extends)
- Closes recurring shape: drift / overfit / refusal / parser / scaler attribution
- CLAUDE.md item 31 (framework-driven extensibility meta-principle)

---

**End of pattern v1.0 DRAFT.** Stage 3 first reference lands at `.B.3` ship close (framework `drift_check_from_derived` reason_buf extension). Stage 4 + 5 sequenced as additional surfaces migrate to framework consumers.
