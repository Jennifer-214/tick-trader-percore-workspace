# D-426 — the STAMP_SET member-existence guard, option E (BUILT + MEASURED → **LANDED**)

> **STATUS UPDATE 2026-08-17, later the same session — this document's original framing is SUPERSEDED.**
> It was written while the guard was proven-but-unlandable (one emit site had no value to pair). That
> blocker was removed by deleting the offending row, the emit sites were converted, and **the guard is
> now ARMED and committed** (engine `76e4b8e`). `guard-option-E.patch` here is therefore a HISTORICAL
> record of the measurement, not a patch awaiting application — do not re-apply it.
>
> The completeness claim the sequencing was designed for held: armed against the fully-converted tree,
> the guard produced **ZERO** refusals, which is the total-oracle proof that every site was converted.
> Read the sections below as the EVIDENCE TRAIL for why option E was chosen, not as pending work.

**Date:** 2026-08-17 · **Engine HEAD at measurement:** `cddd8f6` · **Decision:** D-426 (second AMENDED block)

## What this directory holds

| File | What it is |
|---|---|
| `guard-option-E.patch` | The verified guard, re-appliable with `git apply`. Against `ML_Headers/StampBoundModelConstRegistry.hpp` at `cddd8f6`. |
| `armed-build-evidence.log` | The real-tree build with the guard armed — the 62 refusals + the sites. |
| `guard_design.hpp` / `guard_allow.cpp` / `guard_refuse.cpp` | The standalone two-leg probe (allow-leg must compile; refuse-leg must NOT). |

## The result, in one line

Option E — `tt::is_valid`, the pre-C++20 spelling of `requires { s.name; }`, ~10 in-tree lines,
**no generated traits and no name-universe** — gives exactly the intended discrimination under C++17.

## The two verifications

**1. Standalone probe (two legs, positive control included).**
`guard_allow.cpp` compiles (group bit · parse side · handle side all legal);
`guard_refuse.cpp` **fails to compile** on the live-defect shape with the intended message.
A one-leg probe would have proven nothing — the refuse-leg IS the positive control.

**2. Armed against the real tree — the discrimination test that matters.**
62 `static_assert` failures across `ML_Headers/StampHelper.hpp` + `tests/controller_test.cpp`, and
**ZERO group bits refused.** Every production group bit passes (`xgb_hyperparams` `:334` ·
`label_params` `:375` · `grid_member` `:385` · `scaler` `:391`); every refused name is a real field;
parse (`r`) and handle (`*handle`) sides untouched via the `is_stamp_emit_inputs_v` opt-in.
**That is precisely the failure the reverted version had, and it does not recur.**

## Why E and not D (generate traits from the registry)

`StampInferenceCfgInputs` draws members from **TWO independent generators** —
`FOREACH_STAMP_BOUND_MODEL_CONST` (`ModelInference.hpp:2071`) and
`STAMP_RESULT_DERIVED_FIELDS_AUTO_GEN` (`:2084`, a different meta-registry). A trait list built from
either is **blind to the other's fields** and would silently ALLOW the exact defect the guard exists
to catch — **Class 58-A rebuilt inside the guard**, blind over the ~30 cfg-derived fields that are
queue item 1. The compiler sees the assembled struct; a registry list cannot.

## Why it was not committed AT THE TIME (resolved later the same session — see the status update above)

Arming the guard makes the emit-site conversion **mandatory** (the intended design). One of the 62
sites — `StampHelper.hpp:250`, the live `inference_cfg_bandit_blend_ratio` bit-without-value — **has
no value to pair.** So the conversion cannot complete and the tree cannot compile until that
zero-emit is resolved, which is a deliberate signed-wire byte change gated on the unsettled
positional-vs-relative ledger question.

**The three open decisions are ORDERED, not parallel:**
positional-vs-relative → zero-emit resolution → conversion + guard land in ONE commit.

Reverted to green (suite 3755/0, tree clean) per micro-commits-compile-gated.

## Carry into the conversion

Three production sites set the bit **before** writing the value — `StampHelper.hpp:350-351`
(`xgb_train_nthread`), `:354-355` (`build_flags_hash`), `:356` (`label_registry_hash`). That is the
fragile ordering `STAMP_PUT`'s value-first/bit-second contract removes, so those conversions are a
strict improvement, not a rename.

⚠️ **The conversion's acceptance oracle is PARTIAL** — compiles + suite-green does NOT prove the
emitted bytes. A mis-transcribed value on an HMAC-signed body passes both. Byte-level verification
(determinism gate + golden) is the real oracle.
