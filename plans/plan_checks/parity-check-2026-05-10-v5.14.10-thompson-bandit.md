# /parity-check report — 2026-05-10 — v5.14.10 Bayesian Thompson sampling bandit

## Plan summary

- **Plan:** `plans/v5.14-foxml-port-and-maker/subplans/2026-05-08-v5.14.10-bayesian-thompson-bandit.md`
- **HEAD branch:** `feat/v5.14-foxml-port-and-maker` (latest commit `490618b` per git status)
- **Audit scope:** Targeted (per handoff focus areas) + Section A-L sweep narrowed to surfaces the plan touches
- **Cross-check baseline:** post-v5.14.9.F.2 (ml_cfg_flags bitmap migration); FOREACH_STAMP_BOUND_CFG 7-col Y3 dispatch; FOREACH_ENSEMBLE_POST_LOAD registry; PARITY-001..012 ledger
- **Pre-existing thompson/bandit_algorithm code in tree:** NONE (greenfield); zero collisions
- **Pre-existing `std::mt19937*` / `std::random_device` / `std::normal_distribution` usage:** NONE (the codebase does not currently consume <random>)

---

## Verdict

**YELLOW** — proceed with 4 plan amendments before scope-lock.

The core design (parallel ThompsonBanditState struct, Exp3 default = bytewise-unchanged, separate `thompson_state.json` sidecar with forward-compat-by-absence) is sound and matches established v5.13.4.C / v5.14.1.E precedents. No CRITICAL findings.

What needs to land in the plan before coding starts:

- 1× **HIGH** — `cfg.bandit_algorithm` enum is inference-affecting and MUST be stamp-bound via FOREACH_STAMP_BOUND_CFG (parallels exit_blender_mode exactly). Plan currently silent.
- 1× **HIGH** — replay-determinism contract is partially specified. Plan says "uses mt19937_64 with cfg seed" but mixes `rng_state` (uint64) with `std::normal_distribution` (Box-Muller internally). The `std::normal_distribution` engine state is implementation-defined across libstdc++/libc++ versions and is NOT byte-stable across cross-binary deployments. Need to either (a) own the Box-Muller math directly + persist 64-bit mt19937_64 internal state, or (b) lock libstdc++ minimum version + add a snapshot test that catches drift.
- 1× **MED** — wire-format byte-preservation discipline: plan does specify `format_version` field but doesn't lock per-field `fmt` strings (`%.17g` for doubles per BANDIT_STATE_FORMAT_VERSION precedent at BanditLearning.hpp:404), doesn't pin LC_NUMERIC=C at write-time, and doesn't specify whether `rng_state` serializes as decimal `%llu` or hex `%016llx` (matters for round-trip reproducibility under odd-locale deployments).
- 1× **MED** — display↔execution invariant breach (CLAUDE.md item 12): plan adds a hot-path-affecting predicate (`bandit_algorithm` enum dispatch in ML_BuildParameters) but proposes ZERO PerCoreSnap fields + ZERO ML Status panel branches. v5.13.4 sell-side bandit has snapshot fields; symmetric coverage required for buy-side Thompson.

Fix all 4 in the plan before kickoff; estimated +60 min plan-amendment effort. Coding effort estimate (`~610 LOC`) stays approximately unchanged.

---

## Findings by severity

### CRITICAL

None.

---

### HIGH

#### HIGH-1 — `cfg.bandit_algorithm` not stamp-bound; train-serve algorithm drift undetected

**Severity rationale:** Bandit algorithm choice is INFERENCE-AFFECTING — Exp3 produces blended weights, Thompson produces one-hot weights at chosen arm, and a "Both" cfg=2 telemetry mode adds per-fill log overhead. If a model is trained / paper-tested under one algorithm and silently served under another, blended weights diverge → trade selection diverges → P&L drift undetected.

**Sites:**
- Plan Step 5 (`cfg.bandit_algorithm` declared without stamp binding): `plans/v5.14-foxml-port-and-maker/subplans/2026-05-08-v5.14.10-bayesian-thompson-bandit.md:161`
- Direct precedent (analogous enum): `cfg.exit_blender_mode` at `CoreFrameworks/ControllerConfig.hpp:1104` IS stamp-bound at `ML_Headers/StampBoundCfgRegistry.hpp:137-138`
- Sister Thompson hyperparams (`thompson_mu_prior`, `thompson_precision_prior`, `thompson_precision_obs`) also affect bandit selection trajectory under cfg=1/2; same drift class

**Reproducer:**
1. Operator trains a model with `cfg.bandit_algorithm=0` (Exp3 default).
2. Operator sets `cfg.bandit_algorithm=1` in engine.cfg and restarts. No stamp warning fires (because cfg.bandit_algorithm isn't in FOREACH_STAMP_BOUND_CFG).
3. Live engine quietly switches to Thompson sampling. `weights_buf[]` is now one-hot (vs Exp3 blend). Strategy dispatcher consumes different weights → different arm chosen → different fills → P&L diverges silently.
4. No drift-count increment, no boot WARN, no observable signal that the training context and serving context disagree.

**Recommended fix (Surface G + AUTOPOPULATE):**

Add to `FOREACH_STAMP_BOUND_CFG` in `ML_Headers/StampBoundCfgRegistry.hpp` (matches `exit_blender_mode` shape):

```cpp
/* v5.14.10 — Bayesian Thompson sampling bandit selector (PARITY drift detection) */
X(bandit_algorithm,                int,    "%d",     0,   cfg.bandit_algorithm,                                                                  \
    (cfg.bandit_algorithm != 0), DIRECT_FIELD)                                                                                                    \
X(thompson_mu_prior,               double, "%.17g",  0.0, FPN_ToDouble(cfg.thompson_mu_prior),                                                    \
    (cfg.bandit_algorithm != 0), DIRECT_FIELD)                                                                                                    \
X(thompson_precision_prior,        double, "%.17g",  0.0, FPN_ToDouble(cfg.thompson_precision_prior),                                             \
    (cfg.bandit_algorithm != 0), DIRECT_FIELD)                                                                                                    \
X(thompson_precision_obs,          double, "%.17g",  0.0, FPN_ToDouble(cfg.thompson_precision_obs),                                               \
    (cfg.bandit_algorithm != 0), DIRECT_FIELD)
```

`thompson_rng_seed` is intentionally EXCLUDED from stamp binding — operator should be free to re-seed exploration without invalidating a trained stamp. Document this exclusion explicitly in plan Step 5.

**Effort:** 5 min plan amendment + ~20 min code (4 X-rows; auto-flow through STAMP_CFG_AUTOPOPULATE per CLAUDE.md item 21; legacy stamps load with `has_*=0` per Surface G). Total ship cost increment minimal.

**Cross-ref:** New finding → **PARITY-013** auto-written below.

---

#### HIGH-2 — Replay-determinism contract under-specified; std::normal_distribution is NOT cross-binary byte-stable

**Severity rationale:** Plan claims (line 199): "Identical seed + identical reward sequence → identical sample sequence. Bytewise-deterministic across runs." This claim is TRUE for same-binary same-stdlib deployments, but FALSE across libstdc++ minor-version bumps. `std::normal_distribution` is implementation-defined: libstdc++ uses Marsaglia polar method with internal `_M_saved` state; libc++ uses a different algorithm. Even within libstdc++, the saved-second-draw state can differ across versions. v5.9.2 replay-determinism contract is at risk if a backtest is replayed on a different machine / build.

Also, the plan struct mixes `uint64_t rng_state` (a single seed value) with `std::normal_distribution` usage in Step 1's pseudo-code:
```
Uses Box-Muller for std::normal_distribution alternative
(deterministic; seeded by rng_state).
```

This is ambiguous — either:
- (a) The struct stores ONLY a 64-bit seed and we own the Box-Muller math directly (deterministic, byte-stable, cross-binary safe), OR
- (b) The struct stores a `std::mt19937_64` instance (≈2.5KB internal state) plus a `std::normal_distribution` (libstdc++-specific saved-second state ~16B). Determinism only within same libstdc++ version.

The plan reads (a) but the implementation pseudo-code suggests (b).

**Sites:**
- Plan Step 1 struct definition: `plans/v5.14-foxml-port-and-maker/subplans/2026-05-08-v5.14.10-bayesian-thompson-bandit.md:94` (`uint64_t rng_state`)
- Plan Step 1 method body: line 99 ("Uses Box-Muller for std::normal_distribution alternative")
- Plan REUSE list: line 26-28 names `std::mt19937_64` + `std::normal_distribution` — codebase HAS NEVER USED <random> previously; introducing it crosses a discipline boundary

**Reproducer (today):**
- Operator runs replay backtest on dev box (libstdc++-13). Records 1000 ticks of Thompson samples to a CSV.
- Operator deploys binary to prod (libstdc++-12 or different vendor).
- Same cfg.thompson_rng_seed=42 + same reward sequence → libc++ runtime computes a different normal sample at step N → divergence point inflates → backtest CSV ≠ live decisions.

**Recommended fix:**

Pick option (a). Plan amendment Step 1 should commit to:

> ThompsonBanditState owns:
> - `uint64_t rng_state` (the live mt19937_64 internal state, advanced per draw)
> - NO std::normal_distribution member; we implement Box-Muller (or Ziggurat) directly using only the canonical mt19937_64 64-bit state evolution.
> - `Thompson_Sample` returns: for each arm, draw u1, u2 from mt19937_64 raw 64-bit output; convert to (0,1) via deterministic uniform conversion (NOT std::generate_canonical — that's also implementation-defined); apply Box-Muller cos transform to get standard normal; scale by 1/sqrt(precision_post[arm]) and add mu_post[arm]; argmax.
> - The Box-Muller math uses ONLY std::log, std::sqrt, std::cos, std::sin (IEEE-754 deterministic per CLAUDE.md FPN/double determinism discipline).

The mt19937_64 raw 64-bit output IS standardized by C++11 (§29.6.5.2): given a seed S, the i-th call to `result_type operator()` produces a fully-specified deterministic sequence. So `std::mt19937_64` itself is byte-stable across stdlib implementations as long as the consumer reads raw `operator()()` output. Only the secondary distributions (normal, uniform_real_distribution, generate_canonical) are implementation-defined.

Add a snapshot test (per CLAUDE.md item 15: parity-tested-by-construction) — fixed seed `42`, draw 1000 samples from `Thompson_Sample` against a 2-arm posterior, compute SHA-256 of the sample-trace, lock the hash. Future stdlib-version drift trips the test immediately.

Effort: ~30 min for direct Box-Muller implementation + 30 min snapshot test. Saves having to debug a real production parity issue later.

**Cross-ref:** New finding → **PARITY-014** auto-written below.

---

### MEDIUM

#### MED-1 — Wire-format byte-preservation incomplete in `thompson_state.json` spec

**Severity rationale:** Plan correctly identifies `format_version` header (per BANDIT_STATE_FORMAT_VERSION precedent) and "forward-compat-by-absence" (per exit_bandit_state.json shape at CoreModelZoo.hpp:1942-1990). But several wire-format discipline items per `DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md` are unspecified:

1. **Per-field `fmt` strings not locked.** BanditLearning.hpp:404-414 uses `%.17g` for doubles (lossless round-trip), `%d` for ints. Plan Step 4 doesn't specify; risk of `%g` slipping in (locale-dependent precision drift).
2. **LC_NUMERIC pinning at write time.** BanditLearning.hpp:355-358 documents that the engine boot pins LC_NUMERIC=C process-wide but does NOT do per-write `uselocale` (relies on operator pinning at boot). Plan should explicitly call out the same dependency. Cross-process portability concern: if a Python tool ever reads `thompson_state.json`, locale matters again.
3. **`rng_state` serialization format unspecified.** Decimal `%llu` works but loses ~1 char/byte vs hex `%016llx` (which is canonical for "this is opaque state, not a measurement"). Pick one + lock it; bash-readability favors hex for opaque seeds (matches stamp body's `feature_registry_hash` `"%016lx"` precedent at StampBoundCfgRegistry.hpp).
4. **Atomic write via `.tmp` + rename.** Bandit_SaveJSON pattern at BanditLearning.hpp:376 uses `tmp_path` + `rename`. Plan Step 4 says "parallel to exit_bandit_state.json pattern" but should call out atomicity explicitly so a future reviewer doesn't accept a non-atomic implementation.

**Recommended fix:** Plan Step 4 amendment to spec exact format:

```
File layout (locked at v5.14.10.0):
{
  "format_version": 1,
  "saved_at_ts_ns": <int64>,
  "model_bundle_sha256": "<64-char hex>",
  "n_regimes": <int>,
  "n_arms": <int>,
  "regimes": [
    {
      "regime_id": <int>,
      "regime_name": "<str>",  // optional; omitted if names not provided
      "n_arms": <int>,
      "total_pulls": [<uint64>, ...],   // %llu
      "mu_post": [<double>, ...],        // %.17g
      "precision_post": [<double>, ...], // %.17g
      "rng_state": "0x%016llx"           // hex string for opaque seed
    },
    ...
  ]
}

Write: locale_t pinned via uselocale(LC_NUMERIC=C) at function entry,
       restored before return. Atomic via .tmp + rename pattern.
       Returns 0 on any I/O failure (caller logs + falls back to uniform priors).
```

**Effort:** 10 min plan amendment + 0 incremental code (these are constraints on existing design, not new code).

**Cross-ref:** Closes-by-discipline; doesn't need a PARITY-NNN entry (no current bug — preventive spec tightening).

---

#### MED-2 — Display↔execution invariant breach: zero PerCoreSnap fields + zero ML Status panel branches

**Severity rationale:** CLAUDE.md item 12: "every term in BG_Evaluate / SG_Evaluate must have a corresponding GUI surface. Adding a new hot-path predicate term requires a `PerCoreSnap` field + a panel render in the same PR."

Plan adds:
- A new dispatcher branch in `ML_BuildParameters` at Strategies/StrategyParameters.hpp:887-1005 that affects `weights_buf[]` (consumed by Model_Predict_Ensemble_Weighted at line 1002-1009 — directly affects predictions per tick).
- A new bandit state object (`thompson_bandits[NUM_REGIMES]`) that operators need to inspect to debug "is Thompson actually picking diverse arms?" — same telemetry need that drove `ensemble_bandit_arm_probs` and `ensemble_n_updates_per_regime` in EngineSharded.hpp:646-694 for the Exp3 path.

Currently ZERO mention of:
- A `thompson_bandit_chosen_arm[NUM_REGIMES]` snapshot field
- A `thompson_bandit_total_pulls_per_regime[NUM_REGIMES][N_ARMS]` snapshot field
- A `thompson_bandit_mu_post[NUM_REGIMES][N_ARMS]` snapshot field for the ML Status panel
- A `bandit_algorithm` snapshot field (operator can't see which path is active without re-reading cfg)

Operator's visible failure mode: paper-tests Thompson, sees flat P&L, has NO panel surface to ask "is the Thompson posterior actually diverging from uniform priors? Is mu_post moving? Are pulls evenly distributed?" — must shell into the binary, dump bandit state via stderr.

Plan also lacks:
- ML Status panel branch differentiating "bandit_algorithm: Exp3 / Thompson / Both"
- Per-fill telemetry plumbing for cfg=2 dual mode (the "(uses calibration log v5.13.0.B with new columns)" comment at plan line 144 is the only mention; specifics not designed)

**Sites:**
- Snapshot publish site that needs amendment: `CoreFrameworks/EngineSharded.hpp:646-694` (where `ensemble_bandit_arm_probs` is currently populated)
- Snapshot struct: `CoreFrameworks/ShardedSnapshot.hpp` (search for `ensemble_bandit_arm_probs` to find the parallel additions)
- Panel: ML Status panel (find via `grep -n ensemble_bandit_arm_probs GUI/`)

**Recommended fix:** Plan amendment — add Step 7 "Snapshot + GUI propagation":

```
### Step 7 — Snapshot + ML Status panel surface

Per CLAUDE.md item 12 (display↔execution invariant). New snapshot fields:

- `thompson_bandit_active` (uint8) — 1 if cfg.bandit_algorithm in {1,2}; else 0
- `thompson_bandit_chosen_arm[NUM_REGIMES]` (int8) — last arm chosen by Thompson_Sample per regime (-1 if not yet sampled)
- `thompson_bandit_total_pulls_per_regime[NUM_REGIMES][N_ARMS]` (uint32) — pull counts (already tracked in struct)
- `thompson_bandit_mu_post_per_regime[NUM_REGIMES][N_ARMS]` (float) — posterior means for diagnostics

Populator: extend EngineSharded.hpp:646-694 ensemble snapshot section.

ML Status panel (GUI/DashboardPanels):
- New row: "Bandit Algorithm: Exp3 | Thompson | Both"
- New table when Thompson active: per-regime per-arm (mu_post, precision_post, total_pulls)

Cfg=2 dual mode telemetry: per-fill calibration log gains 2 columns:
  - exp3_chosen_arm_idx (argmax of Bandit_GetProbabilities weights)
  - thompson_chosen_arm_idx (Thompson_Sample return)
Same calibration log mechanism as v5.13.0.B; column extension only.
```

**Effort:** ~60 min code (snapshot field + populator + panel branch + cfg=2 telemetry log columns). Should land in v5.14.10.B (not deferred to .C) so operator has visibility from first usable build.

**Cross-ref:** New finding → **PARITY-015** auto-written below.

---

### LOW

#### LOW-1 — Plan title says "v5.14.11" but ship is v5.14.10

Already noted in the handoff; will be fixed separately. Confirms plan-state-vs-current-codebase staleness check is needed before scope-lock per `/readiness` Cold-pickup discipline (CLAUDE.local.md "Going-forward rule for new plans" item #7).

#### LOW-2 — Plan REUSE claim cites "BANDIT_MAX_ARMS" but Thompson struct uses literal "BANDIT_MAX_ARMS" without verifying that constant covers Thompson's needs

Existing `BANDIT_MAX_ARMS=8` at BanditLearning.hpp:60. Plan Step 1 reuses the constant directly. Confirmed safe — same arm count semantics. Document the reuse explicitly so future contributors know the constants are intentionally shared (vs accidentally copy-pasted).

#### LOW-3 — Plan latency analysis claim "~80ns (N=8 Gaussian draws via mt19937 + Box-Muller + argmax reduction)" is back-of-envelope

Single-draw Box-Muller: ~25-40ns (one log + one sqrt + one cos + 2 mt19937 advances). 8 draws + 8 normalizations + argmax: ~250-400ns is a more realistic estimate. Won't change ship decision (slow-path budget is 100µs), but document so the post-coding `/latency-track` audit doesn't flag a >3x discrepancy as drift.

---

### DOCUMENT-ONLY

None.

---

## Cross-cutting concerns

### XC-1 — PostLoadSetup registry extension

Per `FOREACH_ENSEMBLE_POST_LOAD` at `ML_Headers/CoreModelZoo.hpp:2088-2104` (PARITY-009 close pattern): boot, backtest, and hot-swap all call `EnsembleModelZoo_PostLoadSetup` which iterates the registry. Adding Thompson init + persistence load to the registry means all 3 paths inherit automatically (no Class 18 mirror gap).

Plan Step 2 says "full init via new `EnsembleModelZoo_InitThompsonBandits` after _LoadFromCfg" — this should be wired into `FOREACH_ENSEMBLE_POST_LOAD` per the established pattern, NOT called inline at boot only.

Plan Step 4 persistence save/load should also wire into the registry:
- `init_thompson_bandits` (parallel to `init_bandits` and `init_exit_bandits`)
- `load_thompson_state` (parallel to `load_bandit_state` and `load_exit_bandit`)

This is a single plan amendment line in Step 2 + Step 4 captioning; closes PARITY-009 sister-bug class for the new feature preemptively. Failure to use the registry extension WILL be caught by `/readiness` Check 24 (mirror-function audit) but cleaner to pre-empt.

**Effort:** 5 min plan amendment + 0 code overhead (registry extension was always going to happen, just calling it out).

**Recommended fix:** Add a sentence to plan Step 2 + Step 4: "Wire init + persistence into FOREACH_ENSEMBLE_POST_LOAD registry per v5.14.2.E.1 PostLoadSetup pattern; boot/backtest/hot-swap inherit automatically."

---

## Behavior matrix (verify train and serve agree for default cfg)

Default cfg.bandit_algorithm = 0 (Exp3) per plan Step 5. Engine behavior must be byte-identical to pre-v5.14.10:

| Scenario | Trainer view | Engine view | Identical? |
|---|---|---|---|
| Default cfg (Exp3 path) | Bandit_GetProbabilities → weights_buf | Bandit_GetProbabilities → weights_buf | YES (per plan; verify via existing Exp3 snapshot test) |
| cfg.bandit_algorithm=1 (Thompson) | N/A (no training-time Thompson; runtime-only) | Thompson_Sample → one-hot weights_buf | N/A — runtime-only state; no train-side equivalent |
| cfg.bandit_algorithm=2 (Both) | Same as Exp3 (training does Exp3 alone) | Exp3 weights consumed; Thompson logged | NO — but acceptable: training-time logging adds telemetry, not behavior change |
| Restart with `thompson_state.json` present | N/A | LoadThompsonState overlays posteriors; Exp3 path unchanged | YES (Exp3 default) / N/A (Thompson runtime-only) |
| Restart with `thompson_state.json` MISSING | N/A | Uniform priors stay (per plan); no boot REFUSE | YES (legacy stamp behavior preserved) |
| Cfg drift: trained Exp3, served Thompson | Stamp body has bandit_algorithm=0 | Live cfg.bandit_algorithm=1 | **NO** without HIGH-1 fix → silent drift |

The "Cfg drift" row is the HIGH-1 finding's load-bearing case.

---

## Suggested ship sequence

Plan's existing sub-tag plan is good. Recommended amendments per findings:

| Sub-tag | Step | Findings addressed | Notes |
|---|---|---|---|
| v5.14.10.A | 1+2: ThompsonBandit struct + math kernel | HIGH-2 (own Box-Muller; mt19937_64 raw output only) + LOW-2 | +30 min for direct Box-Muller |
| v5.14.10.B | 3+5: dispatch + cfg fields + **stamp binding** + **snapshot/panel** | HIGH-1 + MED-2 + XC-1 | +25 min for FOREACH_STAMP_BOUND_CFG entries; +60 min for snapshot/panel |
| v5.14.10.C | 4: persistence with locked wire format | MED-1 | +10 min for fmt-string + locale-pinning spec |
| v5.14.10.D | 6: tests + propagation + replay-determinism snapshot test | HIGH-2 verification + MED-2 GUI smoke | +30 min for SHA-locked sample-trace test |
| v5.14.10 | umbrella | — | Tag after .D green |

Total incremental effort vs original plan: ~165 min (~2.75 hrs). Worth it — preempts 3 potential parity issues that would surface later.

---

## NOT a bug (verified-safe items)

- **Forward-compat-by-absence pattern.** Plan correctly mirrors v5.13.4.C exit_bandit_state.json. Missing `thompson_state.json` → uniform priors stay. Same shape as bandit_state.json (which has been load-bearing since v5.10.0a.G.9). No issue.
- **REUSE of `BANDIT_MAX_ARMS` constant.** Confirmed at BanditLearning.hpp:60 = 8. Thompson struct's `mu_post[BANDIT_MAX_ARMS]` etc. correctly inherit the cap. (Captured as LOW-2 only because explicit reuse documentation is desirable.)
- **Plan claim "Hot path UNTOUCHED."** Confirmed — ML_BuildParameters runs on slow path (per CLAUDE.md slow-path target ≤100µs). All Thompson dispatch happens in slow-path rebuild context, never in BG_Evaluate / SG_Evaluate. Hot-path latency budget unaffected.
- **Plan claim "default 0 preserves Exp3 path."** Confirmed by examining StrategyParameters.hpp:887-1005 — the Exp3 weighted-blend branch is the existing path; adding a switch with `case 0:` preserving it is bytewise-equivalent. (Subject to the compiler emitting the switch as predicted-not-taken cmov for case 0; trivially predictable + cache-warm cfg load.)
- **Confidence_composite_enabled migration to ml_cfg_flags bitmap.** Plan doesn't touch this surface; no impact. Pre-existing context confirmed the migration completed at v5.14.9.F.2 and FOREACH_STAMP_BOUND_CFG entry uses BITMAP_BIT emit_source.

---

## PARITY_ISSUES.md entries created

Per `/parity-check` auto-write contract (CLAUDE.local.md):

- **PARITY-013** — `cfg.bandit_algorithm` not stamp-bound (HIGH-1) — OPEN, target v5.14.10.B
- **PARITY-014** — Thompson replay-determinism contract under-specified; std::normal_distribution non-portable (HIGH-2) — OPEN, target v5.14.10.A
- **PARITY-015** — Thompson display↔execution invariant breach: no snapshot/panel surface (MED-2) — OPEN, target v5.14.10.B

Entries written below; status-update log entry appended to PARITY_ISSUES.md tail.

---

## Map-update suggestions (post-audit)

- `DOCS/PARITY_ISSUES.md` — auto-updated with PARITY-013/014/015 (in progress as part of this audit)
- `DOCS/CLAUDE_ML_INVARIANTS.md` — consider a sentence about "non-deterministic <random> distributions are forbidden in train-serve paths; raw mt19937_64 output + own-the-math is the discipline" once HIGH-2 fix lands
- `DOCS/PARITY_LIFECYCLE.md` — bandit-state JSON files now a documented surface (bandit_state.json + exit_bandit_state.json + thompson_state.json triplet)
- Plan update: add Step 7 (snapshot/panel) + Step 8 (replay-determinism snapshot test); rename "v5.14.11" → "v5.14.10" in title (separately tracked per LOW-1)
