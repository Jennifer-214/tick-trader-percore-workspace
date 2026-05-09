# /trace-deps report — v5.14.3 3-layer registry fingerprinting — 2026-05-08

**Verdict:** **GREEN** — all 6 REUSE verified at exact file:line; pattern matches 7 existing Surface G precedents

## Summary
- 6 REUSE claims verified at exact file:line
- 5 NEW functions/structs proposed
- 7 Surface G `has_*` flag examples confirmed (v5.9.3a → v5.11.41)
- 0 GAPS / 0 DRIFT / 0 DRIFT-RISK

## REUSE verification (all PASS)

| Claim | Plan said | Actual | Status |
|---|---|---|---|
| `FEATURE_REGISTRY_HASH()` | FeatureRegistry.hpp:400 | :400 | PASS |
| `feature_registry_hash_compute()` | :385 | :385 | PASS |
| Surface G `has_*` pattern (6+ examples) | various | v5.9.3a `has_scaler_fields` :1217 / v5.9.4a `has_model_num_outputs` :1224 / v5.9.5h `has_build_flags_hash` :1239 / v5.10.0d `has_label_registry_hash` :1251 / v5.11.18a `has_feature_mask` :1265 / v5.11.41 `has_label_params` :1271 + `has_xgb_train_nthread` :1278 | PASS (7 confirmed) |
| `verify_model_stamp` parser | ModelInference.hpp:1312 | :1312 with field-by-field strtok_r loop :1417-1596 | PASS |
| `stamp_write_for_model` emit | ModelInference.hpp:1901 | :1901 with sequential snprintf gated by has_* flags :1972-2153 | PASS |
| `held_out_gate_strict` 3-tier contract | CoreModelZoo.hpp:102 | :102 (-1=skip / 0=warn / 1=refuse); same pattern as v5.9.3a scaler at :354-388 | PASS |

## NEW claim coherence

- **Python `tools/feature_overlay.py`** (NEW): hashlib SHA256 + JSON canonical encoding; standard Python deps
- **C++ `FeatureRegistryOverlay.hpp`** (NEW): `FeatureOverlay_Load` + `_VerifyAgainstStamp`; uses `tt::sha256_file_hex_inproc()` at ModelInference.hpp:1288 (existing helper)
- **Stamp body extension**: `has_overlay_hash` + `overlay_hash[65]` + `has_effective_hash` + `effective_hash[65]` (Surface G; goes at canonical position 24+ after v5.11.41 fields)
- **Loader integration**: hooks into `CoreModelZoo_TryLoadRole` at ~:354 (mirrors v5.9.3a scaler-sidecar pattern exactly)

## Cross-checks

- ✓ Pattern PERFECT MATCH with v5.9.3a scaler sidecar (sidecar SHA256 → stamp `has_*` field → loader 3-tier verify)
- ✓ Canonical position locking at 24+ follows master plan rule
- ✓ Back-compat: legacy stamps without flag → loader skips check (identical to all 7 existing has_* flags)

## Verdict: **GREEN** — Phase 2 sub-ship ready to code
