# Orchestration helper with POD args pattern

**Status:** SHIPPED v5.15.3.A.1 (first application: `tt::Stamp_AssembleAndEmit<F>`)
**Promoted from:** v5.15.3.A pre-coding consult (Option A: structural fix > direct patch)
**Promotes to:** CLAUDE.md item TBD (when 2nd application surfaces — current count: 1)

---

## Problem

Three parallel production-caller sites (Backtest_RunFullValidation,
train_model_worker_fn, hypothetical future batch CLI mode) need to assemble
a complex struct (StampInferenceCfgInputs with 60+ fields) + call an
external API (stamp_write_for_model) with identical canonical-order
semantics. Class 18 mirror at the production-caller level:

- Site A (RFV) had ~200 LOC manual assembly + correct STAMP_CFG_AUTOPOPULATE call
- Site B (train_model_worker_fn) had ~95 LOC manual assembly with **missing**
  AUTOPOPULATE call → 22 cfg-bound fields silently absent from stamps
- Future Site C (batch CLI mode per TECH_DEBT-034) would re-paste the
  same shape, with the SAME risk of forgetting one piece

The autopopulate-pattern-for-production-caller-class.md companion-macro
extraction was the previous structural fix (closed PARITY-002 through -005,
-008). But that closes the *cfg-bound population* class; it doesn't close
the *manual per-call population + external call* class.

## Pattern shape

One level above autopopulate companion macro:

- **Companion macro (FUNCTION):** walks ONE registry; replaces 1 manual
  block at each caller (~30-100 LOC → 1 call). Closes "did caller call
  AUTOPOPULATE?" class.
- **Orchestration helper (FUNCTION):** wraps AUTOPOPULATE + manual per-call
  population + external API call; replaces ~100-200 LOC at each caller
  (~30-200 LOC → 1 call + ~10-30 LOC of POD args setup). Closes "did
  caller wire everything?" class.

```cpp
// POD args struct with default member init (CLAUDE.md item 27 padding;
// CLAUDE.local.md cohort-audit: stack-allocated, no cache concern)
template <unsigned F>
struct StampArgs {
    int    format_version = MODEL_FORMAT_VERSION;
    double wf_metric      = 0.0;
    int    grid_member_count = 1;    // single-horizon default
    int    grid_member_idx   = 0;
    int    horizon_count     = 1;
    const char* run_name     = "";   // empty = no emit
    // ... more fields with sensible single-call defaults
};

// Orchestration helper — wraps AUTOPOPULATE + manual per-call + external call
template <unsigned F>
inline StampWriteResult Stamp_AssembleAndEmit(
    const char* path,
    const char* secret,
    const ControllerConfig<F>& cfg,
    const StampArgs<F>& args) {

    StampInferenceCfgInputs inf = {};

    // (1) Registry-driven cfg-bound fields (closes Class 18 mirror at
    //     production-caller level — any caller using this helper
    //     automatically gets ALL cfg-bound fields)
    STAMP_CFG_AUTOPOPULATE(inf, cfg);

    // (2) Per-call model-const fields (manually mapped from args struct;
    //     args provides defaults so caller only sets what differs)
    inf.format_version = args.format_version;
    inf.wf_metric      = args.wf_metric;
    if (args.run_name && args.run_name[0]) {
        STAMP_SET(inf, run_name);
        // ... copy run_name
    }
    // ... more args→inf mappings

    // (3) External API call (signature stable since v5.X)
    return stamp_write_for_model(path, secret, /*...*/ &inf);
}
```

## Caller patterns

### Pre-helper (Site A — Backtest_RunFullValidation, RFV-shape):

```cpp
StampInferenceCfgInputs inf = {};

// 200+ LOC of manual STAMP_SET(inf, X) + inf.X = src.X for ~30 fields
STAMP_CFG_AUTOPOPULATE(inf, cfg);       // ← Site A had this
inf.format_version = MODEL_FORMAT_VERSION;
inf.wf_metric = (label_kind == 2)
    ? out->walkforward.mean_val_correlation
    : out->walkforward.mean_val_accuracy;
// ... 25+ more lines

stamp_write_for_model(path, secret, /*...*/ &inf);
```

### Pre-helper (Site B — train_model_worker_fn, BUG):

```cpp
StampInferenceCfgInputs inf = {};

// 90+ LOC manual STAMP_SET + inf.X = src.X for ~10 fields
// ← Site B WAS MISSING STAMP_CFG_AUTOPOPULATE entirely (PARITY-020)
inf.format_version = MODEL_FORMAT_VERSION;
inf.wf_metric = state->train_accuracy / 100.0;
// ... missing 22 cfg-bound fields

stamp_write_for_model(path, secret, /*...*/ &inf);
```

### Post-helper (both sites unified):

```cpp
tt::StampArgs<BACKTEST_FP> args;
args.wf_metric = /* caller-specific computation */;
args.grid_member_count = /* caller-specific */;
// ... only the args that differ from defaults

StampWriteResult sr = tt::Stamp_AssembleAndEmit<BACKTEST_FP>(
    path, secret, cfg, args);
```

## When to use

The pattern fits when ALL of the following are true:

1. **2+ production callers** assemble the same complex struct + call the
   same external API in canonical order
2. **Class 18 mirror risk:** sites are drifting (or already drifted) such
   that one site has the population step that another forgot
3. **Companion macro already exists** for the registry-driven half (e.g.,
   STAMP_CFG_AUTOPOPULATE). Per-call population at each site is the
   remaining risk surface.
4. **External API is stable** (the helper wraps it but doesn't own its
   signature — adding the helper is a refactor, not an API change)

If only (1) is true and (3) is missing, you want the autopopulate-companion-
macro pattern first (autopopulate-pattern-for-production-caller-class.md).
The orchestration helper extends that pattern when there's *additional*
per-call population that the companion macro can't reach.

## Trade-offs

**Wins:**
- Single canonical assembly path. Class 18 mirror at production-caller
  level cannot recur — caller picks args.X and the helper handles the
  rest.
- Future callers (4th, 5th, ...) get all the registry-walk + manual-
  per-call work for free.
- Single mock point for future test fixtures + decoupling-roadmap-
  positioning (CLAUDE.local.md set 2026-05-12; helper is the natural
  fence between cfg/training-time state + the wire format).

**Costs:**
- Args struct: 1 entry per per-call field (~20-30 entries today). Default
  member init keeps callers concise but the struct itself is wordy.
- Slight indirection for debugging. Caller-side variables → POD args
  field → helper inf.X → wire output. Manual sequence is more linear
  if you only have one caller.
- Templated on `<F>` to match ControllerConfig<F>. Compile-time only;
  runtime cost identical to inline manual code.

## Anti-patterns

- **Don't use this pattern for 1 caller.** If only RFV calls
  stamp_write_for_model, just keep manual assembly inline + AUTOPOPULATE
  call. Don't pre-build infrastructure for callers that don't exist.
- **Don't make the args struct a class with methods.** POD only.
  Default member init does all the "smart defaults" work; logic lives
  in the helper, not the args.
- **Don't extend AUTOPOPULATE to reach per-call population.** That's
  the failure mode of v5.14.8.0's STAMP_MODEL_CONST_AUTOPOPULATE
  (PARITY-022 quarantine). Per-call population needs a CALLER SOURCE
  (POD args struct), which is fundamentally different from the
  registry-walk source.

## Branchless-discipline note

The helper itself is slow-path (called from training workers + RFV
single-horizon button + future batch CLI). Per CLAUDE.md item 18
(slow-path latency reduction), the helper:

- Avoids unnecessary branches in the hot subset of population (single
  `if (run_name[0])` per optional field; could be hoisted further via
  registry-driven dispatch if 5+ optional fields accumulate — not needed
  at 2-3 today)
- Pre-zeroes `inf = {}` for clean comparison + memcmp byte-identity
- POD args means no virtual dispatch, no hidden allocation
- Templated on `<F>` so compile-time inlining is straightforward

The runtime cost vs inline manual is identical (same instructions,
same memory access pattern; just packaged inside a function).

## Cross-references

- **CLAUDE.md item 13** — X-macro registry pattern; this helper is the
  next-level-up production-caller compositing
- **CLAUDE.md item 15** — Parity-tested-by-construction; helper is the
  single canonical assembly path
- **CLAUDE.md item 19** — Structural fix preferred; helper extraction
  closes Class 18 mirror structurally instead of patching each site
- **CLAUDE.md item 21** — AUTOPOPULATE companion macro pattern (sister)
- **CLAUDE.md item 27** — Struct padding determinism (POD args zero-init)
- `autopopulate-pattern-for-production-caller-class.md` — Companion-macro
  pattern (one level below; the helper internally calls AUTOPOPULATE)
- `structural-fix-preferred-decision-framework.md` — Pattern selection
  framework (Class 18 mirror → structural fix preferred → helper
  extraction)
- `audit-driven-pre-coding-gate.md` — Pattern discovered via v5.15.3
  pre-coding /parity-check + /merge-scan finding PARITY-020 + PARITY-021

## Promotion criteria to CLAUDE.md

Per CLAUDE.local.md "codify design principles in CLAUDE.md as patterns
mature" rule (set 2026-05-09; cross-ref doc): promote when:

- ≥ 2 applications in codebase (currently 1: `tt::Stamp_AssembleAndEmit<F>`)
- OR DESIGN_SPECS doc exists (✓ this doc)
- AND pattern applies broadly (production-caller compositing common)

Promote at next sprint where pattern surfaces (likely v5.16 if a new
production-caller class emerges OR batch CLI per TECH_DEBT-034 lands
the 2nd application).
