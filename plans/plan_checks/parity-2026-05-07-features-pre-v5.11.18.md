# /parity-check report — features surface — 2026-05-07

## Pre-v5.11.18 Audit

**Scope:** Feature pipeline parity in anticipation of v5.11.18 per-core
`feature_mask_<N>` cfg field (uint64_t hex bitmap; 1=enabled feature
index). v5.11.18 will:
1. Add `feature_mask_<N>` cfg per-core (uint64_t, hex bitmap; 1=enabled feature index)
2. Pass feature_mask through MLBuildContext to Features_PackAll, which masks zero-valued features per-core
3. Stamp body extension for `feature_mask` (Surface G has_* pattern; NO MODEL_FORMAT_VERSION bump)
4. Load-time check that stamp's feature_mask matches runtime cfg's mask

**HEAD:** feat/v5.11-optimization

**Baseline Protections:** v5.9.4a+ (FEATURE_REGISTRY_HASH v5.8.6,
scaler binding v5.9.3a, cfg fields stamp-bound v5.9.2b,
model_num_outputs v5.9.4a, snapshot tests v5.9.2a)

---

## Key Findings

### ✓ ALREADY-PROTECTED: Feature Registry Hash Blocks Structure Changes
**Status:** GAP DOES NOT EXIST; protection in place

The existing `FEATURE_REGISTRY_HASH()` at
`ML_Headers/FeatureRegistry.hpp:400-403` computes FNV-1a hash over
ENABLED features only (line 388: `if ((enabled))`). Disabling a
feature via the FOREACH_FEATURE X-macro (line 294-328) flips the hash
automatically.

**Current mechanism:**
- FOREACH_FEATURE macro defines FEATURE_ENABLED/DISABLED flags (lines 291-292)
- feature_registry_hash_compute() branches on enabled flag (line 388)
- FEATURE_REGISTRY_HASH() is cached static (line 401-403)
- Stamp body embeds this hash at training time (ModelInference.hpp:901, 1131-1134)
- CoreModelZoo_TryLoadRole refuses load on mismatch in strict mode (CoreModelZoo.hpp:288)

**v5.11.18 implication:** Per-core feature_mask at RUNTIME differs
from per-core ENABLED flags at COMPILE-TIME. The registry hash
protects structural changes (add/remove/reorder rows, version bumps)
but does NOT protect per-core selective masking. A model trained with
all 34 features enabled will have a stamp containing the full
registry hash. If v5.11.18 runtime cfg masks out features at runtime
per-core, the stamp's hash still represents the full 34-feature set.

---

### ⚠️ CRITICAL-GAP: Scaler Binding Does Not Cover Masked Features

**Severity:** CRITICAL — Silent prediction drift when masked features shift mean-stddev

**Problem:** The scaler sidecar binding at
`ML_Headers/FeatureStandardizer.hpp:23-32` ties the sidecar's
`feature_registry_hash` (line 136, 241) to the FULL registry hash at
training time. When v5.11.18 masks features at runtime per-core:
- Features_PackAll at `ML_Headers/FeatureRegistry.hpp:449-463` will skip masked features
- FeatureStandardizer_Apply at FeatureStandardizer.hpp:180-204 will still apply scaler[i] to feature[i] for unmasked indices
- BUT: if training scaler[i] was computed with feature_i active (in the full training set), and runtime masks feature_i, then indices shift. Feature indices now encode differently between train time (all 34) and runtime (subset).

**File citations:**
- FeatureStandardizer.hpp:136 — registry_hash embedded in struct
- FeatureStandardizer.hpp:241 — hash read from sidecar file during load
- FeatureStandardizer.hpp:180-204 — Apply path (loops 0..n, applies scaler[i] to features[i])
- FeatureRegistry.hpp:449-463 — Features_PackAll packs only enabled features; index=FEATURE_<ID> for each

**Current masking mechanism:** FOREACH_FEATURE X-macro branches on
(enabled) flag, skipping disabled features in both the hash
computation and the pack logic. But this is COMPILE-TIME. The
registry hash depends on which rows are ENABLED at compile. At
runtime, v5.11.18 will introduce RUNTIME-PER-CORE masking via a
uint64_t bitmap.

**Example of silent drift:**
```
Training time (cfg: feature_mask_0 = 0xFFFFFFFFFFFFFFFF, all 34 enabled):
  Scaler trained on 34 features, sidecar.registry_hash = FULL_HASH = 0xfc9119b8ed47bcf9
  Model trained on scaled inputs
  Stamp embeds feature_registry_hash = 0xfc9119b8ed47bcf9

Runtime v5.11.18 (cfg: feature_mask_0 = 0x00000000000003FF, only 10 bits set):
  Engine loads scaler, verifies sidecar.registry_hash == 0xfc9119b8ed47bcf9 ✓ (PASSES)
  Features_PackAll packs only 10 features into out[] (indices 0,1,2,3,4,5,6,7,8,9)
  FeatureStandardizer_Apply still tries to apply scaler[0..33] to features[0..33]
  But features[10..33] are uninitialized / zero (not packed)
  Scaler applies mean/stddev for indices 10..33 to GARBAGE / ZERO input
  Output produces scaled garbage for masked-out features
  Model ingests corrupted input, prediction drifts
```

**Recommended fix:**
- **Option A (Fold into v5.11.18):** Extend scaler sidecar to embed a
  `feature_mask_train` bitmap, recording which features were active
  at training time. At load, verify runtime `feature_mask_<N>`
  matches training mask. Requires sidecar binary format extension
  (2-3 hours, similar to v5.9.3a scope).

- **Option B (Stamp binding ahead of time):** Stamp body adds
  optional `has_feature_mask` flag + `feature_mask_hex` field
  (v5.11.17.x). Operator workflow: train with all features, train
  emits stamp `feature_mask=0xFFFF..F`. Load-time checker verifies
  runtime cfg mask is identical or subset. Avoids sidecar change,
  only touches stamp (1-2 hours, same pattern as v5.9.2b cfg fields).

**Test plan:** Snapshot test needed: train model with 34 features +
scaler, then run backtest with `feature_mask_0 = 0x3FF` (10 bits),
verify predictions do NOT match full-feature baseline.

---

### ⚠️ HIGH-GAP: Features_PackAll Index Contract Brittle on Masking

**Severity:** HIGH — Subtle bugs when masked features are assumed to be indices 0..N-1

**Problem:** Features_PackAll at line 449-463 in FeatureRegistry.hpp
packs features into out[FEATURE_<ID>]. The ID is an enum constant
assigned at compile time (line 332-336):

When v5.11.18 masks features at runtime, code that loops
`for (i = 0; i < n; ++i)` and expects out[i] to hold a valid feature
will break. For example:

- StrategyParameters.hpp:707 — `int n = Features_PackAll(&ctx, features);` then passes `features` to model. If n < NUM_REGISTERED_FEATURES (masked), the model expects NUM_REGISTERED_FEATURES inputs but gets n < 34.
- MLStrategy.hpp:135 — same pattern.
- FeatureStandardizer_Apply at line 180-204: loops `for (int i = 0; i < n; ++i)` and applies scaler to features[i]. When features are masked, n != NUM_REGISTERED_FEATURES, but scaler was trained on 34 features.

**File citations:**
- FeatureRegistry.hpp:331-336 — enum FeatureId constexpr indices
- FeatureRegistry.hpp:449-463 — Features_PackAll packs to out[FEATURE_<ID>]
- StrategyParameters.hpp:707 — calls Features_PackAll, passes result to model (n features)
- MLStrategy.hpp:135 — same; v5.9.0 NaN check branches on `if (n < 0)`
- FeatureStandardizer.hpp:180-204 — Apply loops 0..n, applies scaler to features

**Recommended fix (fold into v5.11.18):** MLBuildContext gains a new
optional field `feature_mask_ptr` (uint64_t*) pointing to the
per-core mask bitmap. Features_PackAll signature becomes:
```cpp
int Features_PackAll(const FeatureComputeCtx<F>* ctx, float* out,
                      const uint64_t* mask = nullptr);
```
Logic: pack only features i where (mask & (1ULL << i)) != 0. Return
value = count of packed features. Callers must know to pass
NUM_REGISTERED_FEATURES (or count of set bits in mask) to the model.
Requires snapshot test.

---

### ✓ MEDIUM-SAFE: Stamp Body Extension Pattern Ready

**Status:** SAFE; Surface G pattern in place

Stamp body schema extension is ready for feature_mask. See
ModelInference.hpp:895-974 (ModelStampResult struct). Existing
pattern from v5.9.3a (scaler fields) + v5.9.4a (model_num_outputs) +
v5.9.5h (XGBoost hyperparams) shows the framework:

```cpp
uint8_t  has_scaler_fields;           // v5.9.3a
uint8_t  feature_scaler_present;
// v5.11.18 will add:
uint8_t  has_feature_mask;            // new
uint64_t feature_mask_train;          // or hex string if per-core
```

Parser at ModelInference.hpp:1104-1248 already has the structure.
Adding `feature_mask=<hex>` parsing is trivial (5 lines, mirroring
line 1131-1134).

**No MODEL_FORMAT_VERSION bump needed.** Forward-compat parser
accepts legacy stamps with has_feature_mask=0.

---

### ✓ LOW-GAP: SHARDED_SNAPSHOT_VERSION Does NOT Need Bump

**Status:** SAFE; no snapshot bump required

SHARDED_SNAPSHOT_VERSION at
`CoreFrameworks/ShardedSnapshotPersist.hpp:75` (currently 6) versions
the PerCoreSnap struct — the live engine's published state persisted
to disk. Adding a per-core cfg field (`feature_mask_<N>`) does NOT
affect the snapshot version because:

1. Cfg fields are loaded from `engine.cfg` at boot, not stored in snapshots
2. PerCoreSnap contains runtime state (positions, P&L, indicators), not cfg
3. v5.9.2b stamped inference cfg fields do NOT trigger snapshot version bumps; they're cfg state, not runtime state

---

### MEDIUM-NOTICE: Feature Masking Index Offset Problem

**Severity:** MEDIUM — Index aliasing when masking non-contiguous features

**Problem:** If v5.11.18 masks out features non-contiguously
(e.g., mask=0b101010, keep 0,2,4... skip 1,3,5...), the output
array from Features_PackAll will have holes. Code that assumes
out[0], out[1], out[2] are the first 3 features will break.

Current model assumes features are at indices FEATURE_SHORT_SLOPE
(0), FEATURE_SHORT_R2 (1), etc. If the packer skips feature 1, does
out[1] become FEATURE_SHORT_VARIANCE (index 2)? Or does out[0],
out[1] contain SHORT_SLOPE, SHORT_VARIANCE, with a hole at index 1?

**Recommended clarification:** In v5.11.18 MLBuildContext
documentation, specify: "feature_mask acts as a column selector,
not a row compressor. Features_PackAll still writes to
out[FEATURE_<ID>], and n = count of enabled features. Caller must be
aware n may be < NUM_REGISTERED_FEATURES. Model_Predict must receive
exactly NUM_REGISTERED_FEATURES inputs (pad masked features with
0.0 or identity scaler default)."

---

## Summary Table

| Surface | Status | Action | Timing |
|---------|--------|--------|--------|
| **Scaler binding** | CRITICAL GAP | Add feature_mask to sidecar OR stamp-bind mask | Fold into v5.11.18 |
| **Features_PackAll masking** | HIGH GAP | Update signature + caller contract | Fold into v5.11.18 |
| **Stamp body extension** | SAFE | Add has_feature_mask + feature_mask fields | Fold into v5.11.18 |
| **Snapshot version** | SAFE | No bump needed | No action |
| **Registry hash** | SAFE | No change; compile-time enabled flags unchanged | No action |
| **Index aliasing clarity** | MEDIUM NOTICE | Document sparse-array behavior | Pre-v5.11.18 docs |

---

## Suggested Ship Sequence

### v5.11.17.x (Pre-req, optional — improves operator safety)
- Add `feature_mask_<N>` cfg parsing (all-bits-on default, 0xFFFF..F)
- Add stamp body `has_feature_mask` + `feature_mask_train` optional fields
- Parser reads stamp's feature_mask at load; warn if runtime cfg differs
- No ML-side changes; masking is a no-op (all features enabled)

### v5.11.18 (Main)
- MLBuildContext gains `feature_mask_ptr` or `feature_mask_<N>` array
- Features_PackAll signature updated: accepts mask parameter
- Scaler sidecar extended with feature_mask field (OR stamp binding for mask)
- Snapshot tests cover masking behavior
- Load-time check: stamp's training mask must match or be subset of runtime cfg

### v5.11.19+ (Post-ship hardening)
- Paper-test masking on live trading (≥48h)
- Document operator recipe for "enable-subset-of-features" workflow

---

## Risk Assessment

**CRITICAL risks if shipped without fixes:**
1. Masked features receive scaled-zero inputs, model prediction drifts silently
2. Operator has no way to know if runtime mask matches training-time feature set
3. Snapshot tests won't catch the masking-scaler interaction

**Mitigation:** Fold both scaler binding AND Features_PackAll masking
logic into v5.11.18 as coordinated deliverables. Stamp binding for
mask is the lower-friction path (doesn't require sidecar binary
format change).

---

**Report generated:** 2026-05-07 | Auditor: Explore agent
**Scope:** Features surface parity pre-v5.11.18 per-core feature_mask cfg field
**Audit depth:** Section B (Feature pipeline parity) + Section D (Scaler binding) + Section E (Stamp body)
