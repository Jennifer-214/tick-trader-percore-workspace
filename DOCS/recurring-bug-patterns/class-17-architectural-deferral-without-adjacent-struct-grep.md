---
type: ledger-template
class_id: 17
title: Architectural deferral made without grepping adjacent struct fields
parent_index: DOCS/RECURRING_BUG_PATTERNS.md
established: 2026-05-18
---

## Class 17 — Architectural deferral made without grepping adjacent struct fields

**Surface:** plan-time. (Detail: any plan that defers a feature with rationale "we
don't have data X". Can be wrong if X (or a usable analog) IS
already in an adjacent struct that the plan author didn't grep.
Expensive class because it punts months of work for zero reason.

**Symptom:** a feature gets deferred to vN+1 sprint with effort
estimate "needs new infra (M LOC, 2 weeks)". Operator (or future-
Claude) reads the plan months later, asks "wait, isn't X
accessible via Y?" — yes, X is in `someStruct->ring_buf[]` which
the plan author didn't check. The deferral was invalid; vN could
have shipped in 2 hours instead of vN+1's 2 weeks.

**Detection:** [delegates to /trace-deps Step 5 — 2-hop adjacent-struct walk before accepting deferrals.]

**Root cause:** pre-coding audit (typically /trace-deps) checks
"does the surface I'm calling EXIST" but doesn't always check
"is the data I need somewhere accessible, even if not in the
obvious place". The audit's "data not in this struct" finding
is correct as far as it goes, but the author + auditor stop
before walking adjacent structs that the obvious one points to.

**Detection:**

```bash
# When considering deferring "feature X needs data Y":
# 1. List every struct accessible from the function's input ctx:
grep -A20 "^struct CtxStructName" CoreFrameworks/<file>.hpp
# (note every pointer field — those are doors to other structs)

# 2. For each pointer field's type, walk INTO that struct and
#    grep for fields that could provide Y:
grep -A50 "^struct PointedToStruct" <file>.hpp

# 3. Specifically look for:
#    - `*_buf[]` ring buffers (raw history)
#    - `*_history[]` arrays
#    - `running_*` accumulators (deltas can give raw values)
#    - `head` / `count` write-position markers (signal a ring exists)

# Pre-coding skill /trace-deps Step 5 (NEW v5.14): for any deferral,
# run a 2-hop walk through adjacent structs before accepting the
# defer rationale.
```

**Known instances:**

- **v5.14.5 frac diff (caught + reverted same day)**: plan
  initially deferred `ML_Compute_FracDiff_*` to v5.16+ with
  rationale "FeatureComputeCtx<F> only has `signals` +
  `short_rolling` (aggregates); no raw price history accessible".
  Operator caught it: "we have raw tick data for backtesting".
  Investigation: `ctx->short_rolling->price_buf[W]` is the raw
  ring (pre-existing for eviction logic; W=128 = 128 lags
  available). Plus `head` (write position) + `count` (warmup
  state). Frac diff truncates at K≈50 lag terms (|C(0.5,50)|<1e-6),
  well within W=128. The feature needs ZERO new infrastructure —
  3 inline functions reading the existing ring with `(head-1-k)
  & (W-1)` indexing. Re-shipped as v5.14.5.C, not deferred.

**Prevention:**

- **`/trace-deps` Step 5** (NEW): for any deferral with rationale
  "missing data X", explicitly walk adjacent structs (1-2 hops
  from the input ctx) and grep for ring buffers / history arrays
  / accumulators that could provide X. ONLY accept the deferral
  if the 2-hop walk turns up nothing.
- **Plan-template discipline** (going forward): "Deferred to vN+M"
  blocks must list "Adjacent structs walked: <list>" + "Why none
  provide the data: <reason>". Forces the deferring author to
  show their work.
- **CLAUDE.local.md memory** (already exists, generalizes here):
  "boundary-stable refactor" rule — prefer NOT cascading struct
  changes. Frac diff was deferred specifically because we thought
  cascading FeatureComputeCtx was needed. This class memory
  reminds us to look for boundary-preserving access first.
