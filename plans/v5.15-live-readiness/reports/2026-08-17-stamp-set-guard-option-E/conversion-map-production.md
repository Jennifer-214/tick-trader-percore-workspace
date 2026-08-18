# Emit-site conversion map — `ML_Headers/StampHelper.hpp` (production, 17 sites)

Prepared 2026-08-17 at engine `cddd8f6`. Line numbers are HEAD-relative; **re-derive by symbol
before editing** (this file shifts). The conversion's oracle is PARTIAL — compiles + suite-green
does NOT prove emitted bytes. Byte verification = the determinism gate + the stamp golden.

## STAYS `STAMP_SET` — group bits (no same-named member; guard correctly ALLOWS)

| Site | Bit | Gates the values written beside it |
|---|---|---|
| `:334` | `xgb_hyperparams` | `xgb_max_depth`, `xgb_learning_rate`, `xgb_n_estimators`, `xgb_subsample`, `xgb_colsample_bytree`, `xgb_min_child_weight`, `xgb_seed` |
| `:375` | `label_params` | `label_lookahead_ticks`, `label_tp_pct`, `label_sl_pct` |
| `:385` | `grid_member` | `grid_member_count`, `grid_member_idx` |
| `:391` | `scaler` | `feature_scaler_present` (+ scaler_sha256) |

Measured: all four pass the armed guard. This is the discrimination the reverted assert got wrong.

## CONVERTS to `STAMP_PUT` — scalar fields (value is adjacent; mechanical)

| Bit | Paired value | Note |
|---|---|---|
| `training_poll_interval` | `cfg.poll_interval` | |
| `feature_mask` | `0xFFFFFFFFFFFFFFFFULL` | ⚠ registry row's `get_value` names `inf->feature_mask_train`, a member that does NOT exist — dead column, compiles only because AUTOPOPULATE is quarantined (**PARITY-022**, pre-existing) |
| `training_timestamp_us` | `(uint64_t)ts_train.tv_sec*1000000ULL + (uint64_t)ts_train.tv_nsec/1000ULL` | already value-then-bit |
| `model_num_outputs` | `(K >= 2) ? K : 1` | |
| `xgb_train_nthread` | `args.snap_train_nthread > 0 ? args.snap_train_nthread : 1` | ⚠ **bit set BEFORE value** |
| `build_flags_hash` | `tt::BUILD_FLAGS_HASH()` | ⚠ **bit set BEFORE value** |
| `label_registry_hash` | `LABEL_REGISTRY_HASH()` | ⚠ **bit set BEFORE value** |
| `expected_num_classes` | `args.req_num_outputs` | |
| `expected_num_features` | `(int)MODEL_NUM_FEATURES` | |

The three ⚠ sites set the presence bit BEFORE writing the value — the exact fragile ordering
`STAMP_PUT`'s value-first/bit-second contract removes. Those conversions are a strict improvement.

## CONVERTS to `STAMP_PUT` — char-array fields (VERIFIED byte-identical)

| Bit | Paired value | Hand-written producer |
|---|---|---|
| `run_name` | `args.run_name` | `:402-404` strnlen → memcpy → explicit NUL |
| `expected_role` | `args.req_role` | `:414-416` strnlen → memcpy → explicit NUL |

`tt::stamp_put_field`'s array arm is `strnlen(s, std::extent_v<T>-1)` → `memcpy` → `dst[n]='\0'`.
For a char array `std::extent_v<T>-1 == sizeof(field)-1`, so the replacement is **byte-identical to
the producers it replaces** — verified against the actual producer bodies, not against the helper's
own comment. Null src is treated as empty rather than deref'd; both call sites already guard
`if (p && p[0])` outside the macro, so that arm is unreachable here and the behaviour is unchanged.

## THE BLOCKED SITE

`:250` `inference_cfg_bandit_blend_ratio` — **no value to pair.** The producer moved to the
cfg-derived half at the `.B.3` migration and the bit-set was left behind, so the signed body carries
`inference_cfg_bandit_blend_ratio=0` beside the truthful cfg-derived line. Cannot be converted;
must be RESOLVED (row deletion on the `fees` precedent, or the tombstone/other option under review).
This is why guard + conversion + resolution land in ONE commit.

## Not in this file

`tests/controller_test.cpp` carries the remaining refused sites (`inf`, `inf2`, `inf_wrong`,
`inf_right`).

**Checked the one that looked like a blocker and it is not.** `inf_wrong` / `inf_right`
(`:18845-18847`, `:18870-18872`) read like fixtures for the bit-WITHOUT-value case — which the guard
makes unspellable by design, and would have needed restructuring. They are not: they test a WRONG vs
RIGHT `label_registry_hash` **value**, and each pairs its value on the very next line
(`wrong_hash` / `LABEL_REGISTRY_HASH()`). Both convert mechanically, and both are also
bit-before-value ordering.

No test found so far that requires constructing bit-without-value. Still read each remaining site
before converting rather than sweeping — that is the PARTIAL-oracle discipline, not a suspicion.
