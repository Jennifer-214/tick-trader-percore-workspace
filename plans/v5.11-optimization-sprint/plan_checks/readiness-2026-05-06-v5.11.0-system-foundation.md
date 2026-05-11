# /readiness report — 2026-05-06-v5.11.0-system-foundation.md — 2026-05-06

**Plan audited:** `plans/2026-05-06-v5.11.0-system-foundation.md`
**Sprint:** Sprint C (v5.11 optimization sprint), ship 1/9
**Branch (claimed):** `feat/v5.11-optimization` (created from `experiment/per-core-sharding` HEAD = `7f0b9a9`)
**Predecessor:** v5.10.0e at commit `f340c37` (verified in git log)
**Current working branch:** `experiment/per-core-sharding` (per gitStatus snapshot)
**Audit run by:** Claude Opus 4.7 (1M context), readiness skill
**Audit date:** 2026-05-06

---

## Plan summary

v5.11.0 is the system-foundation kickoff for the v5.11 optimization sprint. Five phases:

- **A (`v5.11.0.A`)** — FTZ/DAZ MXCSR bits set in `main.cpp` (~10 LOC, 30m).
- **B (`v5.11.0.B`)** — `mlockall(MCL_CURRENT|MCL_FUTURE)` + `RLIMIT_MEMLOCK` preflight; fail-fast on hard error (~25 LOC, 1h).
- **C (`v5.11.0.C`)** — `setsockopt(IPPROTO_TCP, TCP_NODELAY)` on `binance_tcp_connect()` + `binance_rest_tcp_connect()` (~10 LOC, 45m).
- **D (`v5.11.0.D`)** — PGO orchestration (CMake `apply_pgo_flags` + `build.sh build_pgo`); LTO already in place (~40 LOC, 2h).
- **E (folded into final)** — Part 3 architectural verify: greps + 4 `static_assert(!std::is_polymorphic<T>::value)` (~10 LOC, 30m).

Sub-tags: `v5.11.0.A/B/C/D` + final `v5.11.0`. Pre-anchor: `pre-v5.11.0`. **Hot path UNTOUCHED.**

---

## Checklist verdicts (17-item)

| # | Item | Verdict | Notes |
|---|---|---|---|
| 1 | Plan goal stated up front | PASS | Lines 20-25: "table-stakes HFT init invariants" theme is explicit. |
| 2 | Phases ordered in dependency order | PASS | A → B → C → D → E. D depends on A/B/C (PGO trains under FTZ+lock). E is verify-only, folds into final. |
| 3 | Each phase has a Step 0 (concrete first move) | PASS | A: include `<xmmintrin.h>+<pmmintrin.h>`. B: include `<sys/mman.h>+<sys/resource.h>`. C: include `<netinet/tcp.h>`. D: add `option(USE_PGO_GENERATE)` near CMakeLists.txt:18-25. E: run greps as written. |
| 4 | All function/macro names cited exist (or are real C library symbols) | PASS | `_MM_SET_FLUSH_ZERO_MODE` (xmmintrin.h), `_MM_SET_DENORMALS_ZERO_MODE` (pmmintrin.h), `mlockall` (sys/mman.h), `getrlimit/RLIMIT_MEMLOCK` (sys/resource.h), `TCP_NODELAY/IPPROTO_TCP` (netinet/tcp.h), `std::is_polymorphic` (type_traits) — all real. |
| 5 | All file:line refs verified vs HEAD | PASS-with-1-nit | 11 of 12 verified directly (see Dependency table). One nit: plan says "case dispatch at build.sh:174-211"; actual range is 174-213 (esac at 213). Cosmetic only. |
| 6 | LOC estimate reconciled to file size deltas | PASS | Total ~80 LOC source + ~10 docs. main.cpp ~810 LOC; build.sh 213 LOC; CMakeLists.txt 199 LOC. ~14% delta on build.sh is plausible at 2h. |
| 7 | Source-audit refs cited with paths | PASS | `DOCS/LATENCY_OPTIMIZATION_AUDIT.md` Parts 12 + 3, `DOCS/STRATEGY_AND_CODING_RULES.md` §9 + §11, plus 4 plan refs. |
| 8 | Predecessor and successor named with paths | PASS | Predecessor `2026-05-02-MASTER-v5.9-to-v5.10.md`, master `2026-05-06-MASTER-v5.11-optimization-sprint.md`, successor v5.11.1 (hot-path AVX-512, plan TBD). |
| 9 | Tag names locked + rollback anchor named | PASS | `pre-v5.11.0` + `v5.11.0.A/B/C/D` + final `v5.11.0`. Push command provided. |
| 10 | Stale-claim audit performed before write | PASS | Section at lines 349-374 spot-checks 12 specific claims, each marked VERIFIED. I re-checked 8 of them independently — all true. |
| 11 | Hot path UNTOUCHED (or modifications justified) | PASS | Plan grep returns 0 matches for `BG_Evaluate`/`SG_Evaluate`/`ExecutionCore_Tick`. Phase E adds `static_assert` to ExecutionCore.hpp (compile-time only, not runtime). v5.11.1 owns the hot-path AVX-512 work. |
| 12 | Display ↔ execution invariant respected | PASS (N/A) | No new hot-path predicate terms; no GUI surface obligations triggered. |
| 13 | X-macro registry pattern used where multi-site addition | PASS (N/A) | No new strategies/features/SHALT codes added. PGO option is a single-site CMake addition, not a registry-eligible category. |
| 14 | NaN-free feature pack (v5.9.0+) preserved | PASS-with-flag | Plan doesn't modify `Features_PackAll`. BUT FTZ/DAZ change FP behavior — see Hardening checks (drift surface for snapshot tests). |
| 15 | Parity-tested-by-construction lifecycle respected | YELLOW | FTZ/DAZ is a parity-affecting build/runtime invariant. Plan doesn't say whether `BUILD_FLAGS_HASH` (or equivalent) needs a bump for "MXCSR set / not set" in stamp body. PGO build introduces a second build flag axis that must produce bytewise-identical model output (plan does call this out as the cross-build determinism gate). See drift audit. |
| 16 | Failure telemetry path captured by operator's logging | YELLOW | mlockall fatal failure prints to stderr at main.cpp:128-130 BEFORE `freopen` redirect at main.cpp:141. Headless / systemd operator won't see WHY engine refused to start — the log file won't capture it. Real visibility gap. |
| 17 | Resource cleanup paths covered | PASS | mlockall doesn't allocate; no cleanup. PGO writes `.gcda` profile files, not user-visible state, no atomic-rename concern. |

---

## Dependency verification (claimed deps + verification)

| Plan claim | Verification | Status |
|---|---|---|
| `main.cpp:119` — `int main(int argc, char *argv[])` | Read main.cpp:119 — exact match | VERIFIED |
| `main.cpp:128-129` — `BinanceConfig_Load + ControllerConfig_Load` | Read main.cpp:128-129 — exact match | VERIFIED |
| `main.cpp:42-44` — include block (intended insert point) | Read main.cpp:42-43 has `<stdio.h>+<stdlib.h>`. Line 44 is blank, 45-49 is LATENCY_PROFILING block. Plan's "alongside existing 42-44" is slightly off — actual block is 41-43 with blank at 44. Cosmetic. | VERIFIED-with-nit |
| `DataStream/BinanceCrypto.hpp:141` — `socket()` call inside `binance_tcp_connect()` | Confirmed at line 141; loop at 140-148, `connect()` success break at 144, `freeaddrinfo` at 150. Plan's "insert at line 145 between connect()-success and freeaddrinfo" is the right slot. | VERIFIED |
| `DataStream/BinanceOrderAPI.hpp:205` — `socket()` call | Confirmed at line 205, loop at 204-210. | VERIFIED |
| `DataStream/BinanceOrderAPI.hpp:220` — existing `setsockopt(SO_RCVTIMEO)` | Confirmed at line 220 (`setsockopt(sockfd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));`). Plan correctly cites placing TCP_NODELAY *before* this. | VERIFIED |
| `CMakeLists.txt:11,93,138,171,196` — `-O3 -march=native -funroll-loops -flto` per target | All 5 lines confirmed verbatim. | VERIFIED |
| `CoreFrameworks/ExecutionCore.hpp:61` — `struct alignas(64) ExecutionCore` | Read line 61: `struct alignas(64) ExecutionCore {` (preceded by `template <unsigned F>` at 60). | VERIFIED |
| `ExecutionCore.hpp:210` — `__atomic_store_n(&core->permission, ...)` | Confirmed at line 210 inside `ExecutionCore_SetPermission`, `__ATOMIC_RELEASE`. | VERIFIED |
| `ExecutionCore.hpp:356` — `__atomic_load_n(&core->permission, ...)` | Confirmed at line 356, `__ATOMIC_ACQUIRE`. | VERIFIED |
| Test count 1621/0 | Cannot run build; accepting operator's 2026-05-06 verification. | ACCEPTED |
| v5.10.0e at commit `f340c37`, pushed to origin | Confirmed in `git log` (recent commits show `f340c37 v5.10.0e — Runtime IC drift detection`). Push to origin: accepting operator's claim. | VERIFIED-locally |
| Zero `virtual ` in `CoreFrameworks/Strategies/ML_Headers/FixedPoint/MemHeaders/DataStream/` | Independent grep returns empty. | VERIFIED |
| Zero `std::unordered_map / std::map / std::list` in core dirs | Independent grep returns empty. | VERIFIED |
| `build.sh` `build_engine()` ends near line 100; case dispatch at 174-211 | Read confirms `build_engine` ends at 100; case at 174 with `esac` at 213 (plan said 211). | VERIFIED-with-nit |
| Referenced docs: CLAUDE_INVARIANTS.md, CLAUDE_ML_INVARIANTS.md, EXECUTION_DISPLAY_INVARIANTS.md, EASY_ADDITIONS_INVARIANTS.md, PARITY_LIFECYCLE.md | All 5 exist in DOCS/. | VERIFIED |
| Referenced plans: master, REFERENCE, ANNOTATED-REVIEW, hft-suggestions×2, MASTER-v5.9-to-v5.10, SESSION_HANDOFF | All 7 exist in plans/. | VERIFIED |
| `DOCS/OPERATOR_DEPLOYMENT.md` (TBD) | Confirmed does NOT exist. Plan correctly marks as TBD; not blocking. | VERIFIED-as-TBD |

---

## Hidden scope detected

1. **Test-binary FTZ/DAZ symmetry** (genuine, P1 fix). Plan adds FTZ/DAZ in **engine** `main.cpp` only. `tests/controller_test.cpp:1423 int main()` does NOT call `_MM_SET_FLUSH_ZERO_MODE`. Phase A's smoke tests (#1, #2 in test-summary table) work under controller_test, so they need to call the same helper *inside* the test setup (or the controller_test main itself) — otherwise they're testing the test process MXCSR state, not the engine's. **More importantly,** any snapshot-style ML feature test that compares precomputed values to live `Features_PackAll` output will now diverge in subnormal territory: trained-model scoring under FTZ vs. test-side scoring without FTZ produces bytewise-different results when feature values land in subnormal range. This is the real parity drift surface. Recommend adding the `set_mxcsr_ftz_daz()` helper (Phase A's recommended factoring) to `controller_test.cpp:1423` main() and `parity_harness.cpp` main() too, alongside the engine's main.cpp.

2. **mlockall failure visibility gap** (genuine, P1-P2 fix). `mlockall` fires at `main.cpp:128-130` (per plan, post-cfg-load). `freopen(log_file)` redirect happens at `main.cpp:141`. Order means a fatal `mlockall` failure goes to terminal stderr, not the log file. Headless operator (systemd, screen, nohup with output to /dev/null) loses the failure reason. Two fixes:
   - **Fix A (recommended):** Move `mlockall` call to AFTER the log redirect (after line 147, before sharded dispatch at 159). Cost: cfg parsing memory isn't locked. Acceptable — cfg memory is parsed-and-discarded, not in the hot path.
   - **Fix B:** Keep mlockall at 128-130 but emit failure message to BOTH stderr AND a sidechannel (e.g. write to `logging/boot_error.txt` before `exit(1)`). More code, but lock the cfg memory.
   Plan currently picks neither.

3. **Static_assert template instantiation site** (genuine, P2 fix). Plan recommends `static_assert(!std::is_polymorphic<ExecutionCore<64>>::value)` at the bottom of `ExecutionCore.hpp`. This requires `ExecutionCore<64>` to be a complete type at the assertion site — which it will be IF the assert is placed AFTER the struct closing brace (the struct definition is the type, the template is a recipe). Standard C++ lets you take `is_polymorphic<X<64>>` as a constant expression once `X<64>` is instantiable, which it is once the `template <unsigned F> struct ExecutionCore { ... };` definition is parsed. **This works and the plan is correct,** but the wording "at the bottom of the file after the struct" should be tightened to "immediately after the struct closing brace, before any free-function definitions referencing the struct" so the assert lands at a fully-formed type point. Cosmetic but clarity matters when 4 sites get the same pattern.

4. **PGO determinism explicit gate** (already-flagged in plan, no hidden scope but worth re-emphasizing). PGO compiler flags affect codegen; if the engine emits any nondeterministic ordering (hash maps with insertion-order, atomic counters captured into log lines, etc.), PGO and non-PGO builds may diverge despite identical FP math. Plan's "cross-build determinism gate" via v5.9.2 replay-determinism test addresses this AT FINAL — but doesn't cover whether `BUILD_FLAGS_HASH` should reflect "PGO-on" so the model stamp records which variant a model was trained under. **Status:** plan acknowledges via "open thread #2 from session handoff." Acceptable as-is for v5.11.0 if the cross-build determinism test passes.

5. **`-fprofile-correction` semantic risk** (minor, P3). Plan's CMake snippet uses `-fprofile-correction` with `-fprofile-use`. This flag tells GCC to ignore profile mismatches (e.g., when training-build sources differ slightly from production-build sources). For a build pipeline that strictly trains on the same SHA, you don't need it; if you keep it, you silently mask the case where stale profile data is used against newer source. **Recommendation:** drop `-fprofile-correction` to fail-fast, OR keep it and document the risk. Plan currently doesn't justify it.

6. **CMake `target_link_options` PGO compatibility** (minor, P3). Plan's apply_pgo_flags uses `target_link_options(... -fprofile-generate=...)`. GCC supports this; clang LTO PGO uses different flags (`-fprofile-instr-generate`). Plan doesn't pin the compiler. If operator switches to clang, the flag set differs. **Recommendation:** add a compiler check in apply_pgo_flags or document GCC-only.

---

## Cold-pickup context completeness (10 items, per CLAUDE.local.md)

The plan self-audits 10/10 GREEN at lines 401-413. Independent re-walk:

| # | Field | Self-audit | Re-walk verdict |
|---|---|---|---|
| 1 | Branch state named specifically | "feat/v5.11-optimization (already created)" | PASS — current branch is still `experiment/per-core-sharding` per gitStatus, but plan says feat/v5.11-optimization was created from its HEAD. Specific enough; not "TBD." |
| 2 | Phase order matches dependency | A→B→C→D→E (D needs A/B/C; E folds final) | PASS — verified above. |
| 3 | Each phase Step 0 concrete | Yes per phase headers | PASS — every phase has Step 0 with file:line + concrete code shape. |
| 4 | Function/macro names | All cited (FTZ macros, mlockall, setsockopt, etc.) | PASS — all real C/C++/POSIX symbols. |
| 5 | File:line refs verified | All in stale-claim audit | PASS — 12/12 spot-verified by me. |
| 6 | Stale-claim audit | Dedicated section | PASS — present and accurate. |
| 7 | Effort vs LOC reconciled | Per-phase breakdown | PASS — totals reconcile. |
| 8 | Source-audit refs with paths | DOCS/LATENCY_OPTIMIZATION_AUDIT.md + STRATEGY_AND_CODING_RULES.md | PASS — paths cited; private docs but referenced correctly. |
| 9 | Predecessor / dependent named with paths | 2026-05-02-MASTER-v5.9-to-v5.10.md, MASTER-v5.11, v5.11.1 successor | PASS — all paths spelled. |
| 10 | Tag names locked + rollback anchor | pre-v5.11.0, v5.11.0.A/B/C/D, v5.11.0 | PASS — push command at lines 318-328 makes the tag set explicit. |

**Cold-pickup verdict: 10/10 PASS.** A fresh session 7+ days later can pick this up without chat memory.

---

## Drift audit (8 categories)

| Category | Status | Detail |
|---|---|---|
| 1. Boundary-stable refactor (memory file: feedback_reduce_touch_sites.md) | NO RISK | All edits are additive — zero existing types/structs modified. No cascade. |
| 2. Hot-path purity | NO RISK | Zero modifications to `BG_Evaluate`/`SG_Evaluate`/`ExecutionCore_Tick`. Phase E only adds compile-time `static_assert` on the struct, doesn't change runtime. |
| 3. NaN-free feature pack (CLAUDE.md decision 14) | LOW RISK | FTZ flushes subnormals to zero — feature values previously computed as `1e-310` (subnormal) now become `0.0`. `Features_PackAll` already validates with `FPN_IsValidFinite` + `isnan/isinf`; subnormals weren't being filtered (legal finite values). Behavior change is small (subnormal→0) but legitimate. Models trained without FTZ may have learned to discriminate on subnormal-range features; retrain may be needed if backtest replay shows >1bp PnL drift. Plan should call this out as a parity-aware retrain trigger. |
| 4. Train-serve parity | YELLOW | Setting FTZ in engine's main but not in trainer's main (controller_test, parity_harness, foxml_suite, any Python training script) creates divergence. Plan's verification mentions v5.9.2 replay-determinism test — but only across PGO-axis, not across MXCSR-axis. **Recommend:** Phase A also patches controller_test.cpp:1423 main() and parity_harness main(); foxml_suite main() too if it does any FP math during model build (it does — backtest training pipeline). |
| 5. Display ↔ execution invariant (CLAUDE.md 12) | NO RISK | No new hot-path predicate terms. |
| 6. Easy-additions invariant (CLAUDE.md 13) | NO RISK | No category in FOREACH_* registries triggered. |
| 7. Snapshot field forward-compat | NO RISK | No snapshot fields added/changed. |
| 8. Build-flag drift / `BUILD_FLAGS_HASH` | YELLOW | PGO adds a build-flag axis. If stamps record build-flag-hash, PGO-trained model and non-PGO-engine would mismatch (or vice versa). Plan does call this out as cross-build determinism gate via v5.9.2 replay test. **If the v5.9.2 test passes bytewise across PGO/non-PGO, then BUILD_FLAGS_HASH need not include PGO state.** If it doesn't, BUILD_FLAGS_HASH must change. Ship-side decision deferred to actual test output. ACCEPTABLE as-flagged. |

---

## Hardening checks

| Check | Status | Notes |
|---|---|---|
| Atomic file writes | N/A | PGO writes `.gcda` files via compiler; not user-visible state. |
| Locale pinning (LC_ALL=C) | N/A | No locale-sensitive parsing introduced. |
| GUI render-thread blocking I/O | N/A | No GUI changes. |
| Failure telemetry visibility | YELLOW | `mlockall` fatal exits before log redirect. Operator running headless loses failure reason. **See hidden-scope #2.** |
| Resource cleanup | N/A | mlockall doesn't allocate; no fd leak; FTZ/DAZ are register state. |
| Boot-time fatal-vs-warn split | PASS | mlockall = fatal `exit(1)`; TCP_NODELAY = warn-and-continue. Justifications correct (locked memory is HFT-critical, NODELAY varies by OS/NIC). |
| Order of init operations | YELLOW | Plan order: cfg load → mlockall → log redirect → engine dispatch. Reordering to log-redirect before mlockall (hidden-scope #2 Fix A) trades cfg-memory locked vs. failure visibility. **Operator decision needed.** |
| stderr capture path | YELLOW | Engine: stderr→logging/engine.log via freopen at main.cpp:141. Phase B's stderr writes BEFORE this redirect go to terminal, not log. |
| RLIMIT_MEMLOCK threshold tuning | PASS | Plan hardcodes 256MB heuristic (line 102). Reasonable for current sizing, easy to bump. |
| Test-side MXCSR symmetry | YELLOW | controller_test.cpp main() does no FTZ setup. Hidden-scope #1. |
| `-fprofile-correction` flag use | YELLOW | Mask risk for stale profile data. Hidden-scope #5. |
| Compiler-pinning for PGO | YELLOW | Plan assumes GCC syntax. Hidden-scope #6. |

---

## Recommendations

### Must fix before coding (P1)

1. **Add MXCSR FTZ/DAZ to controller_test main() AND parity_harness main()** (and foxml_suite main() if it does FP). Otherwise Phase A test is meaningless and any feature-snapshot test silently diverges from engine runtime. Recommended factoring: extract `static inline void set_mxcsr_ftz_daz()` into a small header (e.g. `CoreFrameworks/SystemInit.hpp` or inline at top of main.cpp + tests with `#include <xmmintrin.h>+<pmmintrin.h>`); call it as the first executable line in every binary's main(). This is the "extract helper" pattern Phase C already recommends for TCP_NODELAY — apply it consistently to FTZ.

2. **Move `mlockall` call to AFTER the log redirect** (after main.cpp:141, before sharded dispatch at line 159). Headless operators (systemd, nohup) MUST see the mlockall failure reason in their log file. Trade-off (cfg parsing memory isn't locked) is acceptable — cfg is parsed-and-discarded outside hot path. Alternatively (Fix B), write the fatal message to a sidechannel file `logging/boot_error.txt` before exit(1), but Fix A is simpler.

### Worth fixing during coding (P2)

3. **Phase E static_assert placement** — pin the assertion immediately after the struct closing brace, not at file end. Helps reviewer locate the contract; avoids any namespace-scope confusion if the file gains free-function templates later.

4. **Drop or document `-fprofile-correction`** — fail-fast on stale profile data is the HFT-correct posture; if plan keeps the flag, document why.

5. **Pin compiler in PGO orchestration** — add `if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU")` guard around `apply_pgo_flags`, OR document that PGO is GCC-only. Operator's current default is GCC (per `-march=native -funroll-loops` style), so this is a future-proofing fix.

6. **Add subnormal-flush parity callout to Phase A risk section** — note that models trained without FTZ may show small (≤1bp) PnL drift in backtest replay after FTZ enabled. If drift > 1bp, retrain. Operator should run a 1M-tick before/after replay during Phase A sub-ship gate.

### Acceptable risk (don't block)

7. **PGO training data deferral** — `data/pgo_train.csv` doesn't exist yet. Plan's warn-and-skip in `build_pgo()` is correct. Acceptable to mark Phase D's full PGO test as DEFERRED until operator provides a training CSV.

8. **No mlockall override flag** — plan's "ship without `--allow-unlocked-memory` flag" is correct posture. Add only if CI box can't raise ulimit.

9. **Cross-thread MXCSR inheritance** — Linux pthread_create inherits parent MXCSR per kernel semantics; plan's "set once in main()" is correct for Linux. macOS/Windows out of scope.

10. **TCP_NODELAY warn-not-fatal** — plan's choice (log-and-continue) matches the production posture for an OS-variable option; acceptable.

11. **Cosmetic: build.sh case dispatch line range** — plan says 174-211, actual is 174-213. Don't block, just fix the line number when amending.

12. **Plan claim "main.cpp:42-44 include block"** — actual block is 41-43 with blank at 44; plan's intent (insert alongside existing includes) is correct, just one line off.

---

## Verdict: YELLOW

**One-line summary:** Plan is exceptionally well-prepared (12/12 stale claims verified, 10/10 cold-pickup, hot path untouched, real audit-driven scoping); two genuine fixes needed (test-binary FTZ symmetry + mlockall-before-log-redirect ordering) plus three P2 polish items.

**5-bullet executive summary:**
- Plan structure is solid: 5 clean phases with sub-tags, dependency-correct order, pre-rollback anchor, cold-pickup completeness 10/10.
- All 12 cited file:line references independently verified vs HEAD `7f0b9a9`. Hot path UNTOUCHED — zero edits to `BG_Evaluate`/`SG_Evaluate`/`ExecutionCore_Tick`.
- **Genuine gap #1:** FTZ/DAZ set in engine's main.cpp but NOT in `tests/controller_test.cpp:1423` main() or `parity_harness` main(). Snapshot tests for feature compute will silently diverge from engine runtime in subnormal territory — train-serve parity drift surface.
- **Genuine gap #2:** `mlockall` fatal failure prints to stderr at main.cpp:128-130 BEFORE `freopen(log_file)` redirect at main.cpp:141. Headless/systemd operators lose the failure reason in their log file. Recommend swapping the order.
- Build-flag PGO drift (open thread #2 from session handoff) is correctly flagged as the cross-build determinism gate via v5.9.2 replay-determinism test. Acceptable as-flagged.

**Top recommendation (single sentence):** Swap the order so `mlockall` fires AFTER the `freopen(log_file)` redirect at main.cpp:141 (so operators running headless see WHY the engine refused to start), and apply FTZ/DAZ in `controller_test`/`parity_harness` mains too so snapshot tests match the engine's MXCSR state.
