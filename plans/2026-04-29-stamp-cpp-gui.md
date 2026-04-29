# v5.3.0 — Held-out training + in-process HMAC + auto-stamp + ML QOL

**Amended 2026-04-29 PM** — original plan was just the C++ helper +
checkbox. Two findings during readiness rescoped it:

1. **Held-out training is stubbed.** `BacktestEngine.hpp:714` hardcodes
   `ran_held_out=0` and `held_out_metric=0.0f`. Comment ("Phase 7
   finalize — happens when there's a real model to evaluate") confirms
   it's a deliberate stub awaiting model signal. So today, the stamp
   bash script signs metrics typed in by hand, and there's nothing for
   an auto-stamp hook to fire on.

2. **Auto-stamp is the right design** but only meaningful once held-out
   actually computes. So Phase 7 finalize moves into this ship as the
   foundation; auto-stamp is the cap.

Replaces the v5.2.3 bash script with a C++ helper called directly from
foxml_suite. Also fixes two known v5.2.0 Phase 1 hacks (popen-based HMAC
verify and sha256sum shell-out) using the same primitive. **Plus**:
ships real held-out training, auto-stamp on completion, and a small
batch of ML iteration QOL improvements that share the same call sites.

## Why ship

The v5.2.3 bash script unblocks the held-out gate workflow but requires
operators to leave the suite, run a CLI, and re-import the stamped model
— and the suite doesn't even compute held-out metrics yet, so the
operator is signing numbers from external validation. The held-out gate
is theatre until Phase 7 finalize ships.

Two adjacent cleanups fall out for free:

1. `verify_model_stamp` shells out to `openssl dgst` via popen. Comment at
   line 760-762 calls it a "v5.2.0 Phase 1" hack with intent to use
   EVP_HMAC. Once we have an in-process primitive for the writer, the
   verifier should use it too — no reason to keep two paths.
2. `sha256_file_hex` shells out to `/usr/bin/sha256sum`. Same fix: use
   `EVP_sha256` in-process. The openssl headers are already included by
   `BinanceOrderAPI.hpp` so no new build dep.

The shell-out path also has shell-injection surface (canonical body
contains user-controlled fields like `trained_on`). In-process eliminates
that entirely.

## Why C++ helper, not "shell out from GUI to bash script"

Original "option 1" was foxml_suite shells out to `tools/stamp_model.sh`.
That has three downsides:
- Two shell-outs (Suite → bash → openssl) instead of one in-process call.
- Secret passed via env or argv — visible in `ps`.
- Error reporting back to GUI is awkward (parse stderr).

Option 2 (this plan) calls a function. The secret stays in process memory.
Errors come back as a struct. The bash script keeps existing as the CLI
entry-point for batch / CI workflows.

## Phase ordering

The ship is split into three phases with rollback tags between them:

```
Phase A — held-out training (Phase 7 finalize)        ~2-3h
  pre-v5.3.0a-heldout
Phase B — in-process HMAC + stamp_write_for_model      ~1.5-2h
  pre-v5.3.0b-stamp-cpp
Phase C — auto-stamp + ML QOL bundle                   ~2-3h
  pre-v5.3.0c-automation
v5.3.0 tag (ship together as one release)
```

If Phase C runs long, the QOL bundle splits into v5.3.1 and v5.3.0 ships
A+B only. Phases A and B are load-bearing; C is the polish.

## Where

| Phase | File | Change |
|---|---|---|
| A | `Backtest/BacktestEngine.hpp` `Backtest_RunFullValidation` (line 676) | Replace held-out stub (line 712-718) with real training pass: train one model on train+val portion, eval on held-out portion, populate `held_out_count` / `held_out_metric` / `held_out_mse` / `held_out_correlation` + flip `ran_held_out=1`. |
| A | `Backtest/HeldOutSplit.hpp` | Add `HeldOutSplit_TrainEval()` helper if not already factored — train + score in one call, takes split as input, returns metric struct. |
| A | `tests/controller_test.cpp` | New test group: held-out training produces a real metric (non-zero, finite, in plausible range), `ran_held_out=1`, gap = `|wf_mean - held_out|` matches `wf_to_held_out_gap`. |
| B | `MemHeaders/HmacSha256.hpp` (NEW) | Extract `binance_hmac_sha256` here; add `hmac_sha256_hex` and `sha256_file_hex_inproc` using `EVP_sha256`. |
| B | `DataStream/BinanceOrderAPI.hpp` | Replace inline `binance_hmac_sha256` with thin wrapper calling shared primitive. |
| B | `ML_Headers/ModelInference.hpp` | (a) `stamp_write_for_model()` next to `verify_model_stamp`. (b) `sha256_file_hex` swap to in-process. (c) `verify_model_stamp` popen → in-process. |
| B | `tests/controller_test.cpp` | RFC 4231 HMAC vectors + round-trip + bash-compat regression. |
| C | `Backtest/BacktestEngine.hpp` `Backtest_RunFullValidation` | At end, if `ran_held_out=1` AND `cfg.auto_stamp_on_held_out=1`, call `stamp_write_for_model` with computed metrics + `cfg.held_out_stamp_secret`. Append result to optional run-history log. |
| C | `CoreFrameworks/ControllerConfig.hpp` | Add `auto_stamp_on_held_out` int (default 1), `run_history_path[256]` str (default empty = disabled), `model_save_versioning` int (default 1). Parsers + tooltips. |
| C | `Backtest/BacktestPanels.hpp` line 990+2025 | Replace original "Save Run" button with optional "Run Full Pipeline" combo button: train → WF → held-out (auto-stamps if cfg). Plus minor: "View Stamps" panel button (lists `*.stamp` files in `models/` with their metrics). |
| C | `MemHeaders/RunHistory.hpp` (NEW) | Append-only JSONL writer: one line per validation completion with timestamp, model_path, wf_mean, held_out, gap, gap_acceptable, fingerprint, stamp_ok. ~80 lines, no deps. |
| C | `tests/controller_test.cpp` | Auto-stamp fires when cfg=1; doesn't fire when cfg=0. RunHistory_Append produces parseable JSONL. |
| all | `tools/stamp_model.sh` | UNCHANGED. Bash CLI stays as the batch/CI entry-point. |
| all | `Version.hpp` | 5.2.3 → 5.3.0 |

## Edits — `MemHeaders/HmacSha256.hpp` (new)

```cpp
#pragma once
#include <openssl/hmac.h>
#include <openssl/evp.h>
#include <stdio.h>
#include <string.h>

namespace tt {

// HMAC-SHA256(secret, data) → 64-byte lowercase hex.
// hex_out must be >= 65 bytes. Returns 1 on success, 0 on failure.
inline int hmac_sha256_hex(const char* secret, const char* data, char* hex_out) {
    unsigned char raw[32];
    unsigned int raw_len = 0;
    if (!HMAC(EVP_sha256(),
              secret, (int)strlen(secret),
              (const unsigned char*)data, strlen(data),
              raw, &raw_len)) {
        return 0;
    }
    if (raw_len != 32) return 0;
    static const char hex[] = "0123456789abcdef";
    for (int i = 0; i < 32; ++i) {
        hex_out[2*i  ] = hex[raw[i] >> 4];
        hex_out[2*i+1] = hex[raw[i] & 0xF];
    }
    hex_out[64] = '\0';
    return 1;
}

// SHA-256 of a file via EVP, in-process, no shell-out.
// Reads in 64K chunks so memory cost is bounded for any file size.
inline int sha256_file_hex_inproc(const char* path, char* hex_out, size_t hex_cap) {
    if (hex_cap < 65) return 0;
    FILE* f = fopen(path, "rb");
    if (!f) return 0;
    EVP_MD_CTX* ctx = EVP_MD_CTX_new();
    if (!ctx) { fclose(f); return 0; }
    if (EVP_DigestInit_ex(ctx, EVP_sha256(), nullptr) != 1) {
        EVP_MD_CTX_free(ctx); fclose(f); return 0;
    }
    unsigned char buf[65536];
    size_t n;
    while ((n = fread(buf, 1, sizeof(buf), f)) > 0) {
        if (EVP_DigestUpdate(ctx, buf, n) != 1) {
            EVP_MD_CTX_free(ctx); fclose(f); return 0;
        }
    }
    fclose(f);
    unsigned char raw[32];
    unsigned int raw_len = 0;
    if (EVP_DigestFinal_ex(ctx, raw, &raw_len) != 1 || raw_len != 32) {
        EVP_MD_CTX_free(ctx); return 0;
    }
    EVP_MD_CTX_free(ctx);
    static const char hex[] = "0123456789abcdef";
    for (int i = 0; i < 32; ++i) {
        hex_out[2*i  ] = hex[raw[i] >> 4];
        hex_out[2*i+1] = hex[raw[i] & 0xF];
    }
    hex_out[64] = '\0';
    return 1;
}

} // namespace tt
```

## Edits — `ML_Headers/ModelInference.hpp` — new `stamp_write_for_model`

```cpp
struct StampWriteResult {
    int  ok;             // 1 = wrote stamp; 0 = refused (gap or i/o)
    char error[256];     // human-readable failure reason
    char stamp_path[512]; // where it was written
};

// Build the same canonical body the verifier reads. Field order MUST
// match exactly; any reorder breaks the signature.
inline StampWriteResult stamp_write_for_model(const char* model_path,
                                                const char* secret,
                                                int format_version,
                                                const char* trained_on_iso, // YYYY-MM-DD
                                                double wf_mean_val,
                                                double held_out_metric,
                                                double gap_threshold,
                                                int force) {
    StampWriteResult r{};
    r.ok = 0;

    // 1. SHA-256 of the model file (in-process)
    char model_sha[80] = {0};
    if (!tt::sha256_file_hex_inproc(model_path, model_sha, sizeof(model_sha))) {
        snprintf(r.error, sizeof(r.error), "could not sha256 %s", model_path);
        return r;
    }

    // 2. Compute |wf - held_out|
    double gap = wf_mean_val - held_out_metric;
    if (gap < 0) gap = -gap;

    // 3. Refuse on gap > threshold (unless force)
    if (gap > gap_threshold && !force) {
        snprintf(r.error, sizeof(r.error),
            "REFUSE: gap %.4f > threshold %.4f (--force to override)",
            gap, gap_threshold);
        return r;
    }

    // 4. Canonical body — must match bash script + verifier byte-for-byte
    char canonical[2048];
    int n = snprintf(canonical, sizeof(canonical),
        "model_format_version=%d\n"
        "model_sha256=%s\n"
        "trained_on=%s\n"
        "wf_mean_val=%g\n"
        "held_out_metric=%g\n"
        "gap=%.6f\n"
        "gap_threshold=%g\n",
        format_version, model_sha, trained_on_iso,
        wf_mean_val, held_out_metric, gap, gap_threshold);
    if (n <= 0 || n >= (int)sizeof(canonical)) {
        snprintf(r.error, sizeof(r.error), "canonical body overflow");
        return r;
    }

    // 5. HMAC-SHA256(secret, canonical)
    char sig[80];
    const char* effective_secret = (secret && secret[0]) ? secret : "";
    if (effective_secret[0] == '\0') {
        // Dev mode — write placeholder signature; verify will warn.
        memcpy(sig, "devmode-no-secret-no-signature", 31);
        sig[31] = '\0';
    } else {
        if (!tt::hmac_sha256_hex(effective_secret, canonical, sig)) {
            snprintf(r.error, sizeof(r.error), "HMAC-SHA256 failed");
            return r;
        }
    }

    // 6. Write <model>.stamp
    snprintf(r.stamp_path, sizeof(r.stamp_path), "%s.stamp", model_path);
    FILE* f = fopen(r.stamp_path, "w");
    if (!f) {
        snprintf(r.error, sizeof(r.error), "fopen failed: %s", r.stamp_path);
        return r;
    }
    fputs(canonical, f);
    fprintf(f, "signature=%s\n", sig);
    fclose(f);
    r.ok = 1;
    return r;
}
```

## Edits — verify side swap (replace popen path)

In `verify_model_stamp` (line 760-789), replace:
```cpp
char cmd[8192];
snprintf(cmd, sizeof(cmd),
    "printf '%%s' \"%s\" | openssl dgst -sha256 -hmac '%s' 2>/dev/null ...",
    canonical, secret);
FILE* p = popen(cmd, "r");
... fgets ... pclose ...
```
with:
```cpp
char computed[80];
if (!tt::hmac_sha256_hex(secret, canonical, computed)) {
    r.valid = 0;
    snprintf(r.reason, sizeof(r.reason), "HMAC-SHA256 failed");
    return r;
}
if (strcmp(computed, stamp_sig) == 0) { ... }
```

Same inputs, same outputs, no shell. Same swap on `sha256_file_hex` →
`sha256_file_hex_inproc`.

## Edits — Phase A: held-out training (Phase 7 finalize)

Replace `BacktestEngine.hpp` line 712-718 stub:
```cpp
out->ran_held_out = 0;
out->held_out_count = 0;
out->held_out_metric = 0.0f;
// ... etc
```
with:
```cpp
// Train ONE model on the train+val portion (no CV — that's WF's job).
// Eval that model on the locked held-out portion.
HeldOutTrainEvalResult he = HeldOutSplit_TrainEval(&slice, split, label_type);
out->ran_held_out      = he.ok ? 1 : 0;
out->held_out_count    = he.eval_count;
out->held_out_metric   = he.metric;          // accuracy or correlation per label kind
out->held_out_mse      = he.mse;
out->held_out_correlation = he.correlation;
```

Where `HeldOutSplit_TrainEval` (NEW) is mechanically the same as one
walk-forward fold but with split.trainval_end_idx as the fold boundary
— train on 0..trainval_end_idx, eval on trainval_end_idx..sample_count.
Reuses existing training plumbing; no new ML code. `metric` is selected
by `LabelType_IsRegression` like the WF mean already is.

## Edits — Phase C: auto-stamp in `Backtest_RunFullValidation`

After Phase A's held-out block, append:
```cpp
// Auto-stamp on held-out completion. Operator opts out via cfg.
if (out->ran_held_out && cfg.auto_stamp_on_held_out) {
    StampWriteResult sr = stamp_write_for_model(
        cfg.last_model_save_path,        // populated when Save Model was last clicked
        cfg.held_out_stamp_secret,
        MODEL_FORMAT_VERSION,
        today_iso(),
        /*wf_mean_val=*/   (LabelType_IsRegression(label_type)
                              ? out->walkforward.mean_val_correlation
                              : out->walkforward.mean_val_accuracy),
        out->held_out_metric,
        cfg.gap_threshold,
        /*force=*/0);
    out->stamp_ok = sr.ok;
    if (!sr.ok) {
        fprintf(stderr, "[stamp] auto-stamp failed: %s\n", sr.error);
    }
}

// Append run history (cfg-gated). One JSONL line per validation completion.
if (cfg.run_history_path[0]) {
    RunHistory_Append(cfg.run_history_path, /* fields ... */);
}
```

No checkbox, no secret input field on the panel. The cfg owns the
secret + the policy; the panel just shows the result.

## Edits — Phase C: foxml_suite "Run Full Pipeline" button + Stamp panel

Replace existing Save Run button (line 990 + 2025 in BacktestPanels.hpp)
with a combo:
```cpp
if (ImGui::Button("Train + Validate + Stamp")) {
    // Triggers Backtest_RunFullValidation in worker thread (existing pattern).
    // After completion: model saved (auto-versioned), WF + held-out done,
    // stamp written if cfg permits.
    spawn_full_pipeline_worker();
}
ImGui::SameLine();
if (ImGui::Button("Train Only"))     { spawn_train_only_worker(); }
ImGui::SameLine();
if (ImGui::Button("Validate Only"))  { spawn_validate_only_worker(); }
```

Plus a new "Model Stamps" panel button on the main panel bar that opens
a window listing `*.stamp` files in `models/` with parsed metrics.
Clicking a row shows full stamp content + `verify_model_stamp` result.

## Edits — Phase C: model save versioning (small)

In the Save Model worker (existing path), if `cfg.model_save_versioning=1`:
```cpp
// Save as <name>.<YYYYMMDD-HHMM>.bin and update <name>.bin -> versioned symlink
char versioned_path[512];
snprintf(versioned_path, sizeof(versioned_path), "%s.%s.bin",
         basename_no_ext, today_compact());
Model_Save(versioned_path);
unlink(canonical_path);
symlink(versioned_path, canonical_path);   // <name>.bin → <versioned>.bin
```

Stamps live alongside the versioned `.bin` so each version has its own
provenance. When a user picks `<name>.bin` to load, the symlink resolves
to whichever version is "current" — and its stamp travels with it.

## Verification

### New tests (controller_test.cpp)

```
PHASE A — held-out training
  test: ran_held_out=1 after Backtest_RunFullValidation completes
  test: held_out_metric is finite + plausible (in [0, 1] for accuracy)
  test: held_out_count = sample_count - trainval_end_idx
  test: gap_acceptable=1 when gap < threshold AND ran_held_out=1
  test: gap_acceptable=0 when held-out skipped (split locked)

PHASE B — in-process HMAC primitive
  test: hmac_sha256_hex matches RFC 4231 vectors 1-4 (hex-compare)
  test: sha256_file_hex_inproc matches sha256sum CLI on a known file
  test: stamp_write_for_model → verify_model_stamp → valid=1
  test: refuses when gap > threshold (force=0)
  test: writes when gap > threshold (force=1) — verifier rejects on gap

PHASE B — bash-compat regression  ⚠ load-bearing
  test: existing tools/stamp_model.sh-generated stamp still verifies
        after the in-process HMAC swap. Generates a stamp via shelling
        to bash script, then loads it via verify_model_stamp using the
        new in-process path. Must return valid=1. If this test fails,
        the canonical body format diverged.

PHASE C — auto-stamp + run history + versioning
  test: cfg.auto_stamp_on_held_out=1 + ran_held_out=1 → stamp file written
  test: cfg.auto_stamp_on_held_out=0 + ran_held_out=1 → no stamp file
  test: cfg.auto_stamp_on_held_out=1 + ran_held_out=0 → no stamp file
  test: RunHistory_Append produces valid JSONL (parse round-trip)
  test: model save with versioning=1 creates <name>.<date>.bin + symlink
```

The bash-compat test (Phase B) is the most important one. Stamps already
exist on disk (we shipped v5.2.3); if v5.3.0 verifies them differently,
that's a silent regression breaking all prior stamps.

### Manual smoke test

1. Build foxml_suite (v5.3.0)
2. Set `held_out_stamp_secret=test-secret-123` and `auto_stamp_on_held_out=1`
   in `engine.cfg`
3. Click "Train + Validate + Stamp" in suite
4. Verify model saved as `<name>.YYYYMMDD-HHMM.bin`, symlink exists
5. Verify stamp file exists alongside, parses + verifies
6. Boot engine in `held_out_gate_strict=1` with same secret in env → loads OK
7. Tamper with model `.bin` (touch a byte) → engine refuses on boot
8. Open "Model Stamps" panel — see all stamped models with metrics

## Acceptance

- Build green: `./build.sh test gui suite`
- 776 existing tests pass
- ~16 new tests across Phases A/B/C
- foxml_suite "Train + Validate + Stamp" pipeline button works end-to-end
- "Model Stamps" panel lists all stamps with parsed metrics
- Auto-stamp fires when cfg permits, doesn't when it doesn't
- Existing v5.2.3 stamps still verify after the swap (bash-compat test)
- `tools/stamp_model.sh` unchanged, still works as CLI entry-point
- Phase A: a model trained via the suite produces a real held_out_metric
  in plausible range, not a zero stub

## Rollback

Three rollback tags, one per phase:
- `pre-v5.3.0a-heldout` — revert Phase A only (BacktestEngine + HeldOutSplit)
- `pre-v5.3.0b-stamp-cpp` — revert through Phase B (also HmacSha256, ModelInference, BinanceOrderAPI)
- `pre-v5.3.0c-automation` — revert through Phase C (also BacktestPanels, RunHistory, ControllerConfig auto-stamp fields)

Bash script (`tools/stamp_model.sh`) is untouched across all phases —
CLI workflow always survives.

## Order of attack

```
PHASE A (held-out training)
1.  Tag pre-v5.3.0a-heldout
2.  Backtest/HeldOutSplit.hpp — add HeldOutSplit_TrainEval helper
3.  Backtest/BacktestEngine.hpp — replace stub block with real call
4.  tests/controller_test.cpp — Phase A test group (5 tests)
5.  Build + test; verify a smoke run produces non-zero held_out_metric
    with plausible value

PHASE B (in-process HMAC + stamp helper)
6.  Tag pre-v5.3.0b-stamp-cpp
7.  Patch foxml_suite CMakeLists.txt: add `ssl crypto` to link libs ⚠
    (readiness blocker — must do before any stamp_write calls in suite)
8.  MemHeaders/HmacSha256.hpp — new primitive
9.  Test the primitive against RFC 4231 vectors (Phase B group)
10. ML_Headers/ModelInference.hpp — add stamp_write_for_model
11. Round-trip test stamp_write → verify_model_stamp
12. ML_Headers/ModelInference.hpp — swap verify's popen path
13. ML_Headers/ModelInference.hpp — swap sha256_file_hex's popen path
14. Bash-compat regression test ⚠ — must succeed
15. DataStream/BinanceOrderAPI.hpp — switch primitive caller
16. Smoke test: testnet HMAC signed REST call still works ⚠

PHASE C (auto-stamp + ML QOL)
17. Tag pre-v5.3.0c-automation
18. CoreFrameworks/ControllerConfig.hpp — new cfg fields + parsers
19. Backtest/BacktestEngine.hpp — auto-stamp call after held-out
20. MemHeaders/RunHistory.hpp — JSONL appender
21. Backtest/BacktestPanels.hpp — Train+Validate+Stamp button
22. Backtest/BacktestPanels.hpp — Model Stamps panel
23. Save Model worker — versioning + symlink
24. tests/controller_test.cpp — Phase C test group
25. Manual smoke: run pipeline, verify stamps + history + versioned files

FINISH
26. Bump Version.hpp 5.2.3 → 5.3.0
27. Build all targets, run all tests
28. Commit + tag v5.3.0 + push
```

Steps 7, 14, 16 are hard gates — if any fails, stop and diagnose.

## What's NOT in this plan (deferred to v5.3.x or later)

- **Pure-C HMAC reimpl** (no openssl dep). Free here since openssl is
  already linked via Binance.
- **Phase 2 C++ stamp_model binary** (CLI tool combining validation
  + stamping). Bash script + GUI cover both workflows.
- **Feature ablation runner** — drop one feature at a time, measure
  delta. This is task #50 territory (parallel sweep runner) — different
  shape of work, different ship.
- **Side-by-side run compare panel** — useful but bigger UI work
  (~2-3h alone). v5.4.x candidate.
- **Auto-promotion to `models/promoted/`** — based on stamp pass +
  metric thresholds, copy to a "ready for live" directory. Conceptually
  clean but adds another path to maintain. Defer until promotion
  workflow is real (i.e. there are multiple competing models worth
  promoting).
- **Train-test contamination check** — verify held-out timestamps
  don't overlap with train. Probably already enforced via index
  arithmetic in HeldOutSplit; sanity assertion can be added cheaply
  later.
- **Nightly auto-revalidation cron** — re-run held-out on yesterday's
  data, alert on drift. Operationally cool, but needs the basics first.

## Drift audit (train ↔ serve, write ↔ read)

Walked each phase asking: does this introduce a divergence between what
training/suite produces and what the engine consumes? One real bug
found in Phase C, plus a clean bill of health on the others.

| # | Drift type | Phase | Verdict |
|---|---|---|---|
| 1 | **Path drift** — stamp at versioned path, engine reads symlink path | C | **BUG — must fix** |
| 2 | Metric drift — gap computed by suite, gap re-checked by engine | C | clean — engine reads written `gap` field, doesn't recompute |
| 3 | Format drift — stamp body schema | all | clean — unchanged |
| 4 | Feature/label drift — held-out training feature set | A | clean — reuses WF training plumbing (same `ModelFeatures_Pack`) |
| 5 | Threshold drift — `gap_threshold` source | C | clean — both sides read `cfg.gap_threshold` |
| 6 | Tick-source drift — held-out training input data | A | clean — `BacktestResults` slice; same producer as live engine consumes via `BacktestSharded_Run` |
| 7 | Time-source drift — wall-clock for `trained_on` | B/C | clean — string field, not load-bearing math |

### Drift bug #1 — symlink stamp lookup

`verify_model_stamp` at `ML_Headers/ModelInference.hpp:645`:
```cpp
snprintf(stamp_path, sizeof(stamp_path), "%s.stamp", model_path);
```

If `model_path = "models/buy.bin"` and that's a symlink to
`models/buy.20260429-1645.bin`, the verifier looks for
`models/buy.bin.stamp` which doesn't exist (the actual stamp is
`models/buy.20260429-1645.bin.stamp`).

**Fix (chosen): create a stamp symlink alongside the model symlink.**
In Phase C's versioned save flow:
```cpp
// model:  buy.bin -> buy.20260429-1645.bin
// stamp:  buy.bin.stamp -> buy.20260429-1645.bin.stamp
char stamp_link[520];
char stamp_target[520];
snprintf(stamp_link, sizeof(stamp_link), "%s.stamp", canonical_path);   // "buy.bin.stamp"
snprintf(stamp_target, sizeof(stamp_target), "%s.stamp", versioned_path); // "buy.20260429-1645.bin.stamp"
unlink(stamp_link);
symlink(stamp_target, stamp_link);
```

Engine's `verify_model_stamp` is unchanged — it reads `<model>.stamp`,
which now resolves through the symlink to the versioned stamp. No
engine-side drift; both .bin and .stamp follow symlinks consistently.

Alternative was `realpath()` on the engine side — rejected because it
shifts complexity to the load path and creates a divergence between
"path passed in" and "path actually checked." Symmetric symlinks keep
the contract simple: `<X>.stamp` is always next to `<X>.bin`, whether
both are symlinks, both are real files, or both don't exist.

**Test (Phase C):** create versioned model + symlink + versioned stamp
+ stamp symlink. Call `verify_model_stamp("models/buy.bin", ...)`.
Must return `valid=1`.

### Drift watchpoints for future ML changes

Beyond this plan, the patterns most likely to introduce drift:

- Adding a feature to `ModelFeatures_Pack` without updating the
  fingerprint computation → stamps and models drift apart silently.
- Computing accuracy in the suite via `WalkForward_ComputeAccuracy`
  but in the live engine via a different formula → metric drift.
- Persisting a struct (snapshot, run history) without bumping its
  version → format drift after struct fields are added.

`/readiness` is being extended to check these systematically — see the
skill's drift section.

## Hardening — load-bearing details surfaced during readiness pass 2

These were missing from the first amendment; surfaced when the
readiness skill was tightened to check for atomicity, locale, telemetry,
and propagation. Each is a small change at the implementation level but
a real bug if skipped.

### Atomic stamp writes

`stamp_write_for_model` writes via `fopen("w") + fputs + fclose`. If the
engine boots mid-write (operator running validation when an autoboot
fires), it reads a half-written stamp. Pattern must be:

```cpp
char tmp_path[520];
snprintf(tmp_path, sizeof(tmp_path), "%s.tmp", r.stamp_path);
FILE* f = fopen(tmp_path, "w");
... write canonical + signature ...
fclose(f);
if (rename(tmp_path, r.stamp_path) != 0) {
    unlink(tmp_path);
    snprintf(r.error, sizeof(r.error), "rename failed: %s -> %s",
             tmp_path, r.stamp_path);
    return r;
}
```

`rename()` is atomic on POSIX within the same filesystem. Same pattern
for the `.bin` save in versioning, since callers may verify the symlink
target before the file fully exists.

### Locale pinning for HMAC canonical body

`%g` and `%f` honor `LC_NUMERIC`. A stamp signed under `LC_NUMERIC=C`
won't verify under `LC_NUMERIC=de_DE.UTF-8` because the canonical body
contains `0,55` instead of `0.55`. The bash script's `awk -v ... 'printf
"%.6f"'` has the same issue.

Fix: add to the very top of `stamp_write_for_model` (and
`Reconcile_*` / any other place the canonical body is built):
```cpp
locale_t prev = uselocale(newlocale(LC_NUMERIC_MASK, "C", (locale_t)0));
... build canonical body ...
uselocale(prev);
```

This is thread-safe (`uselocale` is per-thread) and doesn't disturb the
rest of the process. Add a test: run round-trip with `LC_NUMERIC=de_DE`
set in the environment; sig must still match.

The bash script equivalent is one-line: `LC_NUMERIC=C` at the top of
`tools/stamp_model.sh`. Add it.

### Phase A test fixture

The test "Phase A: held_out_metric is plausible" needs:
- A small deterministic dataset (~10K samples, fixed RNG seed)
- A model architecture (XGBoost likely, since suite uses it)
- A held-out split with known boundary

Use the existing pattern from `tests/controller_test.cpp` synthetic
data tests: generate deterministic ticks via fixed-seed RNG, label them
with a known function, train + held-out eval, assert metric is in
[0.4, 0.99] (range, not specific value — training is approximate).

If `BacktestResults` requires real ML training infrastructure not
available in `controller_test` (zero-dep build), the assertion can be
relaxed to a structural test: stub `HeldOutSplit_TrainEval` to return
a fixed result, assert wiring through `Backtest_RunFullValidation`
populates the right fields. Real model assertions then live in `parity_harness`
(suite-build) or as a Backtest_RunFullValidation smoke run during manual
verification.

### Default for `auto_stamp_on_held_out`

Plan said default=1. That changes behavior for existing users who run
held-out validation without a configured secret — they'd start emitting
`devmode-no-secret-no-signature` stamps automatically. Two outcomes
neither of which is desirable:

- Engine in non-strict mode loads them with a stderr warning (noise)
- Engine in strict mode refuses to load (breaks workflow until they
  set the secret)

**Change default to 0.** Operator opts in by setting the cfg + the
secret. Document in the field's tooltip + CHANGELOG: "set to 1 after
configuring `held_out_stamp_secret` to enable auto-stamp on validation
completion."

### GUI failure telemetry

Auto-stamp errors today only `fprintf(stderr)`. Operator running the
suite sees no signal in the GUI. Add to `BacktestPanels.hpp` results
panel:

```cpp
if (state->wf_results.last_validation_completed) {
    if (state->wf_results.stamp_attempted && !state->wf_results.stamp_ok) {
        ImGui::TextColored(red, "⚠ Stamp failed: %s",
                           state->wf_results.stamp_error);
    } else if (state->wf_results.stamp_ok) {
        ImGui::TextColored(green, "✓ Stamp written: %s",
                           state->wf_results.stamp_path);
    }
}
```

`FullValidationResults` gains `stamp_attempted`, `stamp_ok`,
`stamp_error[256]`, `stamp_path[256]`. Already runtime-only (not
persisted), so no snapshot version bump.

### Stamps panel: cache + refresh, no per-frame I/O

ImGui renders ~60Hz. Calling `opendir` / `stat` / `fopen` on every
frame jams the render thread. Pattern:

```cpp
static std::vector<StampInfo> g_cache;
static double g_cache_age = 0;
if (ImGui::Button("Refresh")) g_cache_age = 0;
if (g_cache_age == 0 || ImGui::IsWindowAppearing()) {
    g_cache = scan_stamps_directory();   // disk I/O once
    g_cache_age = ImGui::GetTime();
}
for (auto& s : g_cache) { ... render rows ... }
```

Refresh button + on-window-open scan = predictable I/O without per-frame
cost.

### CHANGELOG + engine.cfg.example propagation

Each cfg field added in Phase C must land in:
1. `engine.cfg.example` — with a one-line comment explaining the field
2. `DOCS/CHANGELOG.md` — versioned entry under v5.3.0
3. GUI tooltip (already implied by ControllerConfig.hpp `_T()` tooltips)

Plan now lists this explicitly:
```
- engine.cfg.example: append 3 lines (auto_stamp_on_held_out,
  run_history_path, model_save_versioning) with comments
- DOCS/CHANGELOG.md: add v5.3.0 entry with the three phases
- DOCS/CHANGELOG.md: add a one-line note about default change to
  auto-stamp (default=0 in this plan; was implicitly proposed as 1)
```

### Cancellation semantics for pipeline worker

"Train + Validate + Stamp" runs in one worker thread (existing pattern
from WalkForwardWorker). Operator hits Cancel mid-train:
- Train phase: existing `cancel_flag` already wired
- Held-out phase: must read same cancel_flag; if set, return early
  with `ran_held_out=0`
- Auto-stamp: gated on `ran_held_out=1`, so cancellation skips it
  cleanly

No new cancellation code needed — but the held-out implementation must
plumb the cancel_flag through. Phase A test: cancel during held-out
training, assert `ran_held_out=0` and no stamp written.

### Resource cleanup audit (sha256_file_hex_inproc)

Every early return must close FILE + free EVP_MD_CTX. Plan code listing
already does this. Add to the verification list: code review pass
specifically scanning for matched open/close pairs in new functions.
Mechanical check.

## Risks + mitigations

| Risk | Mitigation |
|---|---|
| Phase A: held-out training produces a metric that's wildly off from training-fold mean (gap > threshold by default) | This is exactly the failure mode the gate was designed to catch. If real models can't pass the gate, the gate is doing its job — first action would be to investigate the model, not relax the threshold. Test asserts metric is *finite + plausible*, not above any specific value. |
| Phase A: held-out training is deterministic-but-different from WF folds (different boundary), might score noticeably below WF mean even on clean models | Acceptable. The whole point of held-out is "data the model has never seen, including via CV" — some divergence from WF mean is expected. `gap_threshold=0.05` (default) leaves headroom. |
| Phase B: in-process HMAC produces different sig than openssl CLI | RFC 4231 test vectors + bash-compat regression test. Both must pass. |
| Phase B: BinanceOrderAPI signed-request flow breaks after primitive extraction | Keep wrapper signature identical; smoke-test signed REST call against testnet. |
| Phase B: `EVP_DigestInit_ex` differs between openssl 1.1 and 3.x | API stable since 1.1; codebase already requires it for Binance. |
| Phase B: trailing-newline discrepancy in canonical body | All three writers (bash, C++, verifier reconstruction) end every key=val with `\n`. Bash-compat test catches divergence. |
| Phase B: shell-injection via `trained_on_iso` (old popen path was vulnerable) | In-process path is immune — no shell. Mitigated by construction. |
| Phase C: auto-stamp fires when operator didn't intend (e.g. quick experiments) | `cfg.auto_stamp_on_held_out` opt-out. Default 1 since most users running held-out *do* want a stamp; sandbox machines flip to 0. |
| Phase C: model versioning breaks existing scripts that hardcode `<name>.bin` | Symlink keeps `<name>.bin` working. Scripts that follow the symlink continue working. Scripts that assume `<name>.bin` is a regular file (e.g. `stat -c %s`) — those are rare; opt-out via `model_save_versioning=0`. |
| Phase C: RunHistory file grows unbounded | JSONL append-only; ~200 bytes/line × ~10 runs/day = ~70KB/year per project. Not a concern. Caller can rotate manually if it ever matters. |
| Phase C: Stamps panel pulls metrics from disk on every render → flicker on slow disk | Cache on first read, refresh on F5 button. Same pattern as Trade History panel. |

## Versioning

| Version | Item | Effort |
|---|---|---|
| v5.3.0 | Phase A + B + C combined ship | ~6-8h |

If Phase C runs long, split into v5.3.0 (A + B core) and v5.3.1 (C
polish). Phases A and B together are the load-bearing minimum that
unblocks the workflow.

## QOL features evaluated and chosen / rejected

I considered ~10 ML automation ideas. The ones that made it into Phase C
share three properties: (a) cheap to add, (b) high frequency of use, (c)
no scope creep into other areas of the engine.

**Included in Phase C:**

1. **Auto-stamp on held-out completion** — eliminates a manual step that
   exists only because of legacy workflow.
2. **Run history JSONL log** — enables "what did I try yesterday?"
   queries without parsing GUI screenshots. Tiny code, big lookup value.
3. **Auto-versioned model saves with symlink** — eliminates accidental
   overwrites; operator can always roll back to an older version.
4. **"Train + Validate + Stamp" pipeline button** — collapses three
   button clicks into one. The most-frequent operator action becomes
   one click.
5. **Model Stamps inspection panel** — answers "which models are deploy-
   ready right now?" without `ls models/**.stamp` + cat.

**Deliberately rejected for v5.3.x:**

- **Feature ablation runner** — task #50 territory; deferred per user's
  prior signal.
- **Side-by-side run compare** — UX-heavy, useful but not load-bearing.
- **Auto-promotion to `models/promoted/`** — premature; only one model
  in flight today.
- **Hyperparam grid search GUI** — same shape as feature ablation, same
  defer.
- **Drift detection / alerting** — needs an "online metrics" channel
  that doesn't exist yet. Pre-live work.
- **Train-test contamination assertions** — likely already enforced via
  HeldOutSplit's index arithmetic. Cheap to add later if it ever
  matters.
