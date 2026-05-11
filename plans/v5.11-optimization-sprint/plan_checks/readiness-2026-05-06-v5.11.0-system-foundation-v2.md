# /readiness report (v2 / re-readiness) — 2026-05-06-v5.11.0-system-foundation.md — 2026-05-06

**Plan audited:** `plans/2026-05-06-v5.11.0-system-foundation.md`
**Sprint:** Sprint C (v5.11 optimization sprint), ship 1/9
**Re-readiness:** v1 ran earlier this session at `f340c37` (v5.10.0e). v5.10.1 → v5.10.4 have shipped since (current HEAD `7d1ff8d`, tag `v5.10.4`).
**Branch (claimed):** `feat/v5.11-optimization` (currently at `7f0b9a9`, Sprint B close)
**Current parent:** `experiment/per-core-sharding` at `7d1ff8d` (v5.10.4, +6 commits ahead of feat branch)
**Predecessor (per plan):** v5.10.0e at `f340c37` — STALE, real predecessor is now v5.10.4 at `7d1ff8d`
**Audit run by:** Claude Opus 4.7 (1M context), readiness skill
**Audit date:** 2026-05-06

---

## Executive summary

Plan was already amended GREEN once; the v1 P1 fixes (helper extraction, mlockall ordering, etc.) are correctly applied. v5.10.1-v5.10.4 did NOT touch any of the surfaces v5.11.0 targets (main.cpp, DataStream/Binance{Crypto,OrderAPI}.hpp, CMakeLists.txt, build.sh, ExecutionCore.hpp, foxml_suite.cpp, parity_harness.cpp, controller_test.cpp main()). All 17 file:line citations re-verify against `7d1ff8d`. Two minor amendments needed:

1. **Test count baseline** 1621/0 → 1636/0 (5 occurrences in plan)
2. **Test-binary include path style** — plan says `#include "CoreFrameworks/SystemInit.hpp"` for all 4 mains, but tests use `../CoreFrameworks/X` ascending style (will fail to compile if applied verbatim)
3. **Branch base** — `feat/v5.11-optimization` is at `7f0b9a9` (Sprint B close), v5.10.1-4 are not in it. Operator must decide: rebase the feature branch onto `7d1ff8d` first, OR start v5.11.0 on the older base. Rebase is the clean choice since v5.10.1-4 didn't touch v5.11.0 surfaces.
4. **Predecessor reference stale** — plan says "Predecessor: v5.10.0e final (commit `f340c37`)". Real predecessor is now `7d1ff8d` (v5.10.4).

After these cosmetic amendments, plan is GREEN.

---

## Stale-claim re-walk (vs HEAD `7d1ff8d`, post v5.10.1-4)

| # | Plan claim | Verification @ HEAD `7d1ff8d` | Status |
|---|---|---|---|
| 1 | `main.cpp:119` — `int main(int argc, char *argv[])` | Read main.cpp:119 — EXACT MATCH | VERIFIED |
| 2 | `main.cpp:120` (first executable line — fprintf banner) | Read main.cpp:120 — fprintf banner matches | VERIFIED |
| 3 | `main.cpp:128-129` — `BinanceConfig_Load + ControllerConfig_Load` | Read main.cpp:128-129 — EXACT MATCH | VERIFIED |
| 4 | `main.cpp:148` — insertion point AFTER freopen | Read main.cpp:147 closes the if-block; line 148 is the insertion slot before sharded dispatch at 159 | VERIFIED |
| 5 | `main.cpp:159` — sharded dispatch `if (ccfg.engine_mode == ENGINE_MODE_SHARDED)` | Read main.cpp:159 — EXACT MATCH | VERIFIED |
| 6 | `tests/controller_test.cpp:1424` — first line inside main at 1423 | Read confirms `int main()` at 1423; line 1424 is inside main | VERIFIED |
| 7 | `tests/parity_harness.cpp:120` — first line inside main at 119 | Read confirms `int main(int argc, char** argv)` at 119 | VERIFIED |
| 8 | `foxml_suite.cpp:86` — first line inside main at 85 | Read confirms `int main(int argc, char *argv[])` at 85 | VERIFIED |
| 9 | `DataStream/BinanceCrypto.hpp:141` — `socket()` call | Read confirms `socket(rp->ai_family, ...)` at line 141, loop 140-148, `connect()` success at 144, `freeaddrinfo` at 150. Insertion slot at 145 is correct. | VERIFIED |
| 10 | `DataStream/BinanceOrderAPI.hpp:205` — `socket()` call | Read confirms socket() at line 205, loop 204-210 | VERIFIED |
| 11 | `DataStream/BinanceOrderAPI.hpp:220` — existing `setsockopt(SO_RCVTIMEO)` | Read confirms `setsockopt(sockfd, SOL_SOCKET, SO_RCVTIMEO, ...)` at line 220 | VERIFIED |
| 12 | `CMakeLists.txt:11,93,138,171,196` — `-O3 -march=native -funroll-loops -flto` per target | All 5 lines confirmed (engine, engine_gui, foxml_suite, controller_test, parity_harness) | VERIFIED |
| 13 | `CMakeLists.txt:18-25` — option block insertion area | Read confirms options at lines 18-24 | VERIFIED |
| 14 | `build.sh:174-213` — case dispatch (`case "$TARGET" in` at 174, `esac` at 213) | Confirmed — `case` at 174, `esac` at 213 | VERIFIED |
| 15 | `build.sh:100` — `build_engine()` ends at line 100 | Confirmed — closes at 100 | VERIFIED |
| 16 | `CoreFrameworks/ExecutionCore.hpp:61` — `struct alignas(64) ExecutionCore` | Read confirms at line 61 | VERIFIED |
| 17 | `ExecutionCore.hpp:210` — permission writer (`__atomic_store_n` RELEASE) | Confirmed | VERIFIED |
| 18 | `ExecutionCore.hpp:356` — permission reader (`__atomic_load_n` ACQUIRE) | Confirmed | VERIFIED |
| 19 | Zero `virtual ` in core dirs | grep returns empty over CoreFrameworks/Strategies/ML_Headers/FixedPoint/MemHeaders/DataStream | VERIFIED |
| 20 | Zero `std::unordered_map / std::map / std::list` in core dirs | grep returns empty | VERIFIED |
| 21 | `tt::engine_set_mxcsr_ftz_daz()` does NOT yet exist | grep across all .hpp/.cpp returns empty | VERIFIED — does not exist |
| 22 | `CoreFrameworks/SystemInit.hpp` does NOT yet exist | `ls` returns "No such file or directory" | VERIFIED — does not exist |
| 23 | v5.10.0e tag at `f340c37` | `git tag --list 'v5.10.0e'` returns the tag | VERIFIED |
| 24 | Test count baseline 1621/0 | **STALE** — user reports 1636/0 post v5.10.1-4 (cannot run build to confirm; accept) | STALE — needs amend |

**24/24 file:line citations re-verify against current HEAD.** Only #24 (test count) is genuinely stale.

---

## What changed since v1 readiness

| Surface | v5.10.1-4 churn | v5.11.0 impact |
|---|---|---|
| `main.cpp` | UNCHANGED | None — all 5 line refs (119, 120, 128-129, 148, 159) hold |
| `DataStream/Binance{Crypto,OrderAPI}.hpp` | UNCHANGED | None — socket lines 141, 205, 220 hold |
| `CMakeLists.txt` | UNCHANGED | None — all 5 target compile_options lines (11, 93, 138, 171, 196) hold |
| `build.sh` | UNCHANGED | None — case/esac at 174-213 holds |
| `CoreFrameworks/ExecutionCore.hpp` | UNCHANGED | None — Phase E static_assert sites hold |
| `tests/controller_test.cpp` | +234 LOC, all appended at line 13393+ | main() at 1423 untouched; first line inside main at 1424 holds; replay-determinism test at 10251 unaffected |
| `tests/parity_harness.cpp` | UNCHANGED | None — main at 119 holds |
| `foxml_suite.cpp` | UNCHANGED | None — main at 85 holds |
| `Backtest/*`, `EngineSharded.hpp`, `ShardedSnapshot.hpp`, `EngineTUI.hpp`, `MLStatusPanel.hpp`, `CoreModelZoo.hpp` | TOUCHED (parity hardening, observability) | Tangential to v5.11.0 surface; no impact on Phase A/B/C/D/E targets |
| Test count | 1621/0 → 1636/0 (+15) | Plan baseline cited in 5 places — needs amend |

**No v5.11.0 surface was perturbed by v5.10.1-4. Plan's structure remains intact.**

---

## Newly-detected gap (NOT caught by v1)

**Include-path style mismatch between engine main and test mains.**

The plan currently says (Phase A, line 86):
> All four files: `#include "CoreFrameworks/SystemInit.hpp"` near existing includes

But verification shows:
- `main.cpp:25-30` uses `"CoreFrameworks/Notify.hpp"` etc. — **descending style, no `../`**
- `foxml_suite.cpp:23-30` uses `"GUI/X.hpp"`, `"DataStream/X.hpp"` — **descending style**
- `tests/controller_test.cpp:18-30` uses `"../DataStream/MockGenerator.hpp"`, `"../CoreFrameworks/PortfolioController.hpp"` etc. — **ASCENDING style with `../`**
- `tests/parity_harness.cpp:36-38` uses `"../Backtest/BacktestEngine.hpp"`, `"../ML_Headers/ModelInference.hpp"` — **ASCENDING style with `../`**

**If Phase A applies the include verbatim across all 4 binaries, controller_test and parity_harness will fail to compile** (no `CoreFrameworks/SystemInit.hpp` reachable from `tests/`).

**Fix:** in Phase A code shape, specify two include lines:
- main.cpp + foxml_suite.cpp: `#include "CoreFrameworks/SystemInit.hpp"`
- tests/controller_test.cpp + tests/parity_harness.cpp: `#include "../CoreFrameworks/SystemInit.hpp"`

This is mechanical but the plan should call it out explicitly so the coder doesn't trip on it.

**Severity:** P2 (not a structural risk; first compile would catch it; but cold-pickup field #4 says "name function/include exactly", so it's worth fixing pre-coding for cleanliness).

---

## Branch state staleness

Plan says (line 4):
> **Branch:** `feat/v5.11-optimization` (created 2026-05-06 from `experiment/per-core-sharding` HEAD = `7f0b9a9` Sprint B merge)

**Current state:**
- `feat/v5.11-optimization` branch tip: `7f0b9a9` (Sprint B close)
- `experiment/per-core-sharding` branch tip: `7d1ff8d` (v5.10.4, +6 commits ahead)

**Operator decision needed before coding:**
- **Option A (recommended):** Rebase or merge `experiment/per-core-sharding` (`7d1ff8d`) into `feat/v5.11-optimization` to absorb the v5.10.1-4 hardening. Since v5.10.1-4 didn't touch v5.11.0 surfaces, this is a clean merge.
- **Option B:** Start v5.11.0 on the older `7f0b9a9` base, plan to integrate v5.10.1-4 later. Higher merge risk if v5.11.x drives further changes into now-divergent files.

Plan does not currently say which path to take. **Amend plan**: pick A or B explicitly. Likely A.

If A: amend "Branch" line to "feat/v5.11-optimization (rebased onto experiment/per-core-sharding HEAD = `7d1ff8d` v5.10.4)". Predecessor amends to `7d1ff8d` v5.10.4 instead of `f340c37` v5.10.0e.

---

## Cold-pickup completeness check (10 fields)

Re-walk against the post-amendment plan + the new staleness identified above:

| # | Field | Plan state | Re-walk verdict |
|---|---|---|---|
| 1 | Branch state named specifically | `feat/v5.11-optimization` from `7f0b9a9` | **STALE** — base is now `7d1ff8d`. Amend. |
| 2 | Phase order matches dependency | A→B→C→D→E | PASS — unchanged |
| 3 | Each phase Step 0 concrete | Each phase has Step 0 with file:line | PASS — all line refs hold |
| 4 | Function/macro names | All cited | PASS — verified `tt::engine_set_mxcsr_ftz_daz` does NOT exist; `BUILD_FLAGS_HASH` exists at `ML_Headers/BuildFlags.hpp:69` |
| 5 | File:line refs verified | 24/24 verified above | PASS — all hold against `7d1ff8d` |
| 6 | Stale-claim audit | Self-audit @ `7f0b9a9` | **NEEDS RE-RUN** at `7d1ff8d`. Amend stale-claim section's header to "verified 2026-05-06 against `7d1ff8d` (v5.10.4)" instead of `7f0b9a9`. |
| 7 | Effort vs LOC reconciled | Per-phase breakdown | PASS — totals (90 LOC, 4-6h) reconcile with current file sizes (`main.cpp` 1202 LOC, `build.sh` 215, `CMakeLists.txt` 203) |
| 8 | Source-audit refs with paths | DOCS/LATENCY_OPTIMIZATION_AUDIT.md + STRATEGY_AND_CODING_RULES.md | PASS — paths cited |
| 9 | Predecessor / dependent named with paths | Predecessor `f340c37` v5.10.0e | **STALE** — real predecessor is `7d1ff8d` v5.10.4. Amend. |
| 10 | Tag names locked + rollback anchor | pre-v5.11.0 + v5.11.0.A/B/C/D + v5.11.0 | PASS |

**Cold-pickup verdict (post-shipping of v5.10.1-4): 7/10 PASS, 3/10 NEEDS AMEND** (branch state, stale-claim header date+SHA, predecessor SHA).

These are all cosmetic (SHA/branch references), not structural. The plan's actual Phase A-E content is structurally GREEN.

---

## Drift audit (re-walk)

| Category | v1 status | v2 status |
|---|---|---|
| 1. Boundary-stable refactor | NO RISK | NO RISK — all v5.11.0 edits are additive |
| 2. Hot-path purity | NO RISK | NO RISK — confirmed v5.10.1-4 did not perturb hot path; v5.11.0 doesn't touch it |
| 3. NaN-free feature pack | LOW RISK (subnormal flush) | LOW RISK — unchanged. Risk callout already added in plan amendment |
| 4. Train-serve parity | YELLOW (helper across mains) | GREEN — plan's helper-extraction pattern handles this; amendment adds the include-path fix |
| 5. Display↔execution invariant | NO RISK | NO RISK |
| 6. Easy-additions invariant | NO RISK | NO RISK |
| 7. Snapshot field forward-compat | NO RISK | NO RISK |
| 8. Build-flag drift / `BUILD_FLAGS_HASH` | YELLOW | UNCHANGED YELLOW — plan correctly defers PGO+`BUILD_FLAGS_HASH` decision to v5.9.2 replay test outcome. PGO doesn't add a `#define` so `BUILD_FLAGS_CANONICAL` is unaffected; cross-build determinism is the operative gate. |

**No new drift surfaces detected post v5.10.1-4.**

---

## v5.10.1-4 spillover audit

Did the parity-check Findings closures in v5.10.1-4 add any new "must verify" surfaces for v5.11.0?

- **v5.10.1.A** (LABEL_REGISTRY_HASH plumb-through): added `expected_label_registry_hash` arg to `verify_model_stamp`. v5.11.0 doesn't load models, so no impact.
- **v5.10.1.B** (grid_member_count validator): added `EnsembleZoo_VerifyGridMemberConsistency`. v5.11.0 doesn't use ensemble; no impact.
- **v5.10.1.C** (AutoDetect cfg-args plumb): wires cfg into `EnsembleModelZoo_AutoDetectFromDir`. v5.11.0 doesn't use that path; no impact.
- **v5.10.2** (hot-swap parity hardening): updates to `EngineSharded.hpp` slow-path. v5.11.0 hot path UNTOUCHED; slow-path additions don't conflict with PGO instrumentation.
- **v5.10.3** (display + observability): updates to `EngineSharded.hpp`, `EngineTUI.hpp`, `MLStatusPanel.hpp`. None overlap with v5.11.0 surfaces.
- **v5.10.4** (Finding #13 hotfix): `CoreModelZoo_LoadFromDir` arg plumb. v5.11.0 doesn't touch that function; no impact.

**Conclusion: v5.10.1-4 hardening is fully compatible with v5.11.0 plan as written.**

---

## Recommendations (post v1 amendment + v5.10.1-4 ship)

### Cosmetic amendments before coding (P2, all five trivial)

1. **Update test count baseline 1621 → 1636** in 5 places:
   - Line 96 (Phase A sub-ship gate)
   - Line 160 (Phase B sub-ship gate)
   - Line 302 (Phase D sub-ship gate)
   - Line 345 (Final tag composite verification)
   - Line 412 (stale-claim audit table)

2. **Add include-path callout** in Phase A (line 86):
   - `main.cpp` + `foxml_suite.cpp`: `#include "CoreFrameworks/SystemInit.hpp"` (descending, no `../`)
   - `tests/controller_test.cpp` + `tests/parity_harness.cpp`: `#include "../CoreFrameworks/SystemInit.hpp"` (ascending with `../`)

3. **Update Branch line** (line 4): change "from `experiment/per-core-sharding` HEAD = `7f0b9a9` Sprint B merge" to "from `experiment/per-core-sharding` HEAD = `7d1ff8d` (v5.10.4); operator should rebase `feat/v5.11-optimization` onto this before coding starts".

4. **Update Predecessor** (line 5): from `f340c37` v5.10.0e to `7d1ff8d` v5.10.4. Note that v5.10.0e is still the Sprint B closer; v5.10.1-4 are Sprint B+ hardening.

5. **Update stale-claim audit header** (line 392): from "verified 2026-05-06 against current HEAD `7f0b9a9`" to "verified 2026-05-06 against current HEAD `7d1ff8d`".

### Already addressed in v1 amendment (no new action)

- Phase A helper extraction across all 4 mains: **applied in v1 amendment** (lines 81-90)
- Phase B mlockall after freopen: **applied in v1 amendment** (lines 108, 114)
- Phase D `-fprofile-correction` dropped: **applied in v1 amendment** (line 248)
- Phase D GCC pin guard: **applied in v1 amendment** (lines 240-242)
- Phase E static_assert placement clarified: **applied in v1 amendment** (line 319)
- Subnormal-flush PnL drift callout: **applied in v1 amendment** (line 92)

### Acceptable risk (don't block)

- PGO training data deferral (`data/pgo_train.csv`): plan correctly handles via warn-and-skip
- No `--allow-unlocked-memory` flag: plan correctly defers
- Cross-thread MXCSR inheritance: plan correctly notes Linux-only as out-of-scope

---

## Verdict: GREEN with 5 cosmetic amendments

**One-line summary:** Plan is structurally ready. v5.10.1-4 ship did not perturb any v5.11.0 surface (24/24 file:line refs hold). Five cosmetic amendments needed: test count baseline (1621→1636), include-path style note for tests, branch base SHA refresh, predecessor SHA refresh, stale-claim audit SHA refresh.

**5-bullet executive summary:**
- All 24 file:line citations re-verify against current HEAD `7d1ff8d` (v5.10.4). Surfaces v5.11.0 targets (main.cpp, DataStream sockets, CMakeLists, build.sh, ExecutionCore, test mains) were UNTOUCHED by v5.10.1-4.
- v1 readiness P1 fixes (helper extraction, mlockall ordering, fprofile-correction drop, compiler pin, static_assert placement, subnormal-flush callout) are correctly applied in the plan amendment.
- New gap not caught by v1: include-path style mismatch — `tests/*.cpp` use `../CoreFrameworks/X` ascending style while `main.cpp`/`foxml_suite.cpp` use `CoreFrameworks/X` descending. Plan should specify both forms in Phase A so coder doesn't trip on first compile.
- Branch state stale: `feat/v5.11-optimization` is at `7f0b9a9` (Sprint B close), missing v5.10.1-4 hardening (+6 commits). Operator should rebase onto `7d1ff8d` before starting Phase A.
- Test count baseline 1621/0 → 1636/0 (per user prompt; +15 from v5.10.1-4 EXTENSIBILITY blocks). Cited in 5 places in plan.

**Top recommendation (single sentence):** GREEN — apply 5 cosmetic amendments (test count 1621→1636, dual include-path note for tests, branch base SHA, predecessor SHA, stale-audit SHA), rebase `feat/v5.11-optimization` onto `7d1ff8d`, then start Phase A coding.
