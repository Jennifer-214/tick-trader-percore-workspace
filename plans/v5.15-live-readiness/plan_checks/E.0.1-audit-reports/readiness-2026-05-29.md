# /readiness report — `.E.0.1` pre-`.E.1` foundational-fix net (Net-2) — 2026-05-29

**Target plan:** `plans/v5.15-live-readiness/subplans/2026-05-29-v5.15.5.F.4d.1.E.0.1-pre-E1-foundational-fix-net.md` (v0.1 DRAFT)
**Engine:** FoxML_Trader_v2 @ HEAD `2492e43`, branch `feat/v5.15-live-readiness`
**Auditor:** Layer-2 subagent (deep re-verify + completeness pass; supersedes the light session-pickup pass).
**Audit tier:** HIGH-RISK (declared in frontmatter; touches engine FP + backtest parser + CMake). Stage-0 DESIGN_SPECS loaded: single-source-of-truth, structural-fix, wire-format-byte-preservation (F-076 H9/H12 surface), backtest-paper-live-convergence.

---

## Verdict: GREEN (start coding) — with 2 doc-hygiene amendments worth folding at Phase A; NO blocking gap.

Every load-bearing symbol, file:line, and forward-ref artifact verified to exist. The acceptance criteria are testable and the corrected determinism-gate definition (sqrt-scoped, NOT blanket all-ops) matches the actual preserved harness. R1 (FromDouble/ToDouble) is the strongest part of the plan — named, line-anchored, and pre-dispositioned. The two amendments are citation-quality, not correctness: (1) a fabricated helper name in an *out-of-ship* fix-design, (2) F-076's hazard surface is real but the plan leaves it un-cited (Phase A "locate" rather than file:line).

---

## Dependency verification (all cited symbols re-grepped against HEAD 2492e43)

| Claimed dependency | Plan cite | Actual | Verdict |
|---|---|---|---|
| Generic NR `FPN_Sqrt` primary template | `FixedPointN.hpp:873` | `:873` (`template <unsigned F> inline FPN<F> FPN_Sqrt`) | ✅ EXACT |
| Native block | `FixedPointN.hpp:1217-1256` | `#ifdef USE_NATIVE_128` opens 1217; block runs to ~1256 | ✅ EXACT |
| `_to_fp64`/`_from_fp64` pointer-pun | `:1221-1226` | `_to_fp64` 1221, `_from_fp64` 1224; both `*((__uint128_t*)…)` | ✅ EXACT (UB confirmed real) |
| `FPN_Sqrt<64>` native specialization (delete target) | "~1254" | `:1254` (`{ return _from_fp64(FP64_Sqrt(_to_fp64(v))); }`) | ✅ EXACT |
| `FPN_FromDouble<64>`/`FPN_ToDouble<64>` native specializations (R1) | `:1250-1251` | `:1250` + `:1251` | ✅ EXACT |
| `FP64_Sqrt` (= `sqrt(double)` round-trip) | `FixedPoint64.hpp:313-316` | `:313` decl; body 314-316 (`FP64_FromDouble(sqrt(FP64_ToDouble(value)))`) | ✅ EXACT |
| `FP64_FromDouble` (R1 rounding source) | `FixedPoint64.hpp:38-41` | **`:33` decl**; body 34-44 (floor + frac×2⁶⁴ truncate) | ⚠️ DRIFT (off by ~5 lines; flagged by parent) |
| FromDouble "generic multi-word construction" cross-ref | "`:162+`" | `:162` is inside the **Mul overflow-mask / Division** block, NOT FromDouble's generic path | ⚠️ DRIFT (wrong anchor; semantics intact — see note) |
| Backtest tick parser `strtod` sites | `BacktestEngine.hpp:88-96` | `:87` (fmt-1 price), `:94-95` (aggTrades) — 3 `strtod` calls confirmed | ✅ (±1 line) |
| Depth replay `strtod` sites | `DepthReplayState.hpp:224-227` | `:224-227` (bid_p/bid_q/ask_p/ask_q) | ✅ EXACT |
| `tt::parse_double_fast_advance` (drop-in) | `ParseFast.hpp:78` | `:78`; strtod-style "parse + advance via *end_out", from_chars core, p-equality no-progress sentinel | ✅ EXACT — genuine 1:1 drop-in |
| `USE_NATIVE_128` cmake option (default ON) | `CMakeLists.txt:21` | `:21` `option(... ON)` | ✅ EXACT |
| engine target gets the define | `CMakeLists.txt:66-68` | `:66-68` (`if(USE_NATIVE_128) target_compile_definitions(engine …)`) | ✅ EXACT |
| test targets (F-057 surface) | `CMakeLists.txt:213-242` | `controller_test` 213+, `parity_harness` ~238, `depth_recorder_test` ~228; **only `MULTICORE_TUI`, NO `USE_NATIVE_128`** (220, 241) | ✅ F-057 CONFIRMED real |
| R1 cfg→FPN ingest path | `CfgFieldDispatch.hpp:80/242/283` | `:80` `dst=FPN_FromDouble<T::F>(v)`; `:242`; `:283` | ✅ EXACT (R1 blast-radius real) |
| sqrt determinism load-bearing | `RidgeBlender.hpp:39` | `:39-43` comment ties FPN_Sqrt determinism to replay-determinism test | ✅ EXACT |
| **F-076** `Fingerprint_Compute` | "locate" (uncited) | **`Backtest/Fingerprint.hpp:174`**; raw-byte hash at **`:180`** `SHA256_Update(&s, cfg_ptr, cfg_size)`; caller `BacktestPanels.hpp:3157` | ✅ EXISTS (plan under-cites) |
| **F-107** `tt::format_double_canonical` | F-107 fix-design | **DOES NOT EXIST anywhere** (code or docs). Canonical emit is inline `uselocale(newlocale(LC_NUMERIC_MASK,"C",…))` (RunHistory.hpp:88, BanditLearning.hpp:462) | ⚠️ FABRICATED SYMBOL (out-of-ship; see Q5) |

**Forward-ref artifacts (Q5) — all exist:** `A2-runtime-confirm-results.md` ✅, `determinism-gate-seed-fp_sqrt_diff.cpp` ✅, `CANONICAL-FINDINGS.md` ✅, decision-log `v5.15.5.F.4d.1.E-architecture-v2.md` ✅, `.E.0` gate plan ✅, sprint `MASTER.md` ✅. All 5 `sister_specs` exist ✅. Proposed NEW `fp-determinism-canonical-path-discipline.md` correctly does NOT yet exist ✅.

---

## Audit-question answers

### Q1 — Acceptance criteria testable + concrete? **PASS.**
- **Determinism-gate acceptance is unambiguous + grounded.** The "sqrt-scoped diagnostic RED→GREEN, NOT blanket all-ops" definition matches the actual harness byte-for-byte: `determinism-gate-seed-fp_sqrt_diff.cpp` dumps ONLY `FPN_Sqrt<64>` raw bytes under WITH/WITHOUT `USE_NATIVE_128` (no AddSat/Mul/Div comparison). The three-part decomposition (tests-build-native / cross-run+cross-binary byte-det / sqrt diagnostic) is each independently checkable. The explicit carve-out of FromDouble/ToDouble (R1) removes the one ambiguity a naive implementer would hit.
  - **One nuance the implementer must hold:** the sqrt harness itself routes its input through `FPN_FromDouble<64>` (line 11) before sqrt — so even the "sqrt-scoped" diagnostic's input construction differs native-vs-generic on non-exact doubles. The harness inputs are mostly exact (2.0, 0.25, 100.0) but include `12345.678`, `2.0000001`, `9999999.0`. The RED→GREEN claim holds because the *sqrt specialization* is the dominant divergence, but a perfectly-clean post-fix GREEN requires the FromDouble difference to be sub-ULP-invisible on those inputs OR the harness to compare against a native-built generic-sqrt. This is consistent with R1's disposition; no plan change required, but Phase B.1 should expect residual low-bit noise on the 3 non-exact inputs and not mistake it for an incomplete sqrt fix.
- **Replay-locale gate acceptance is concrete:** "parse a fixed tick/depth CSV under C and a non-C locale → byte-identical." Mechanically runnable. The "no process LC_NUMERIC=C pin currently" premise is VERIFIED — engine has locale pinning only at *emit* sites (RunHistory, BanditLearning), none at the backtest/depth *parse* sites, and `test_common.hpp:48` already includes `<locale.h>` for a locale-immunity test pattern to reuse.

### Q2 — Coding phases executable as written? **PASS** (one undefined sub-step, non-blocking).
- **Phase A** (confirm F-076 + F-107): executable. F-076's symbol is now located for the implementer (Fingerprint.hpp:174/180) — see recommendation to fold the cite.
- **Phase B** (FP atomic, with B.0 observe-the-red probe): the B.0 → B.1 revert-detect-reapply sequence is concrete and correct (flip F-057 with F-056 un-applied → expect RED → confirms coverage → then fix). Both branches (RED=proceed / GREEN=file coverage-gap finding) are specified. **Executable.**
- **Phase C** (replay): drop-in substitution `strtod(p,&p)` → `tt::parse_double_fast_advance(p,&p)`. The `if(*p==',') p++` comma-advance logic is preserved because `_advance` updates `*end_out` exactly like `strtod` updates its second arg. **Executable, genuine near-1:1.**
- **Phase D** (F-076 fold + Class codification handoff): executable.
- **Phase E** (ship close): standard ritual, concrete.
- **Undefined sub-step (minor):** F-057 says "Mirror in `build.sh` tsan/asan paths." But `build.sh:226` and `:238` **already** pass `-DUSE_NATIVE_128=ON` via `CMAKE_CXX_FLAGS`. So the build.sh "mirror" is largely **MOOT/already-done** for tsan/asan; the *actual* missing surface is the per-target `target_compile_definitions(controller_test/parity_harness PRIVATE USE_NATIVE_128)` in CMakeLists for the **default `build/` test target** (which inherits no native define). Plan should reword F-057 to: "CMakeLists per-target defs are the fix; tsan/asan already carry it via CXX_FLAGS — verify, don't duplicate." Non-blocking.

### Q3 — "Tests changed (Check 45)" complete? **PASS.**
All three categories present and accurate: NEW CI gates (H10 determinism harness + replay-locale identity, in `tools/`+`tests/`); modified (`CMakeLists.txt` + `build.sh` for F-057); broken-replaced ("none anticipated", with the correct caveat that a surfaced non-sqrt divergence is a NEW finding to fix, not a test to weaken — cites `/test-strength-audit`). The F-059 golden-master is correctly marked "spec'd here, written in Net-1" (NEW characterization, not built this ship). Honest about the 3239→ assertion count holding post-F-057 (native==generic after F-056). **Note:** current `grep -cE '^\s*check\('` returns 3132 raw check() lines — the 3239 figure (from `.D.1` close) includes macro-expanded/loop-driven assertions, so the raw grep undercount is expected, not drift.

### Q4 — Cold-pickup: codeable in <30 min without re-derivation? **PASS (≈8.5/10).**
A fresh session has: exact branch (`feat/v5.15-live-readiness`), every fix's file + line + before/after code snippet (F-056 delete-target, F-058 memcpy diff, F-057 cmake lines, F-054/55 substitution), phase order with first-concrete-moves, required-reading list pointing at the evidence base (`A2-runtime-confirm-results.md` + the harness). Acceptance is locked. The **two cold-pickup deductions** (each ~10-15 min, fold at Phase A):
- **C.4/C.5 — F-076 has no file:line.** Phase A says "locate `Fingerprint_Compute`." It's at `Backtest/Fingerprint.hpp:174`, raw-byte hash at `:180`, production caller `BacktestPanels.hpp:3157`. The aspirational comment at `Fingerprint.hpp:172` ("config fields serialized in **sorted order** for canonical hashing") **contradicts** the actual raw-`cfg_ptr` hash at :180 — i.e. F-076 is confirmed real and the comment is misleading. Fold these anchors in.
- **C.6 — F-107 cites a non-existent helper** (`format_double_canonical`); a picker-up grepping for it loses time. See Q5.

### Q5 — Forward-promises + cross-refs point to real artifacts? **PASS, with 1 fabricated symbol (out-of-ship).**
All 6 plan-level forward-ref artifacts + all 5 sister_specs exist (table above). The ONE miss is `tt::format_double_canonical` in the **F-107 fix-design** — the symbol exists nowhere in code or docs (CLAUDE.md's latency-budget row references it as the *intended* canonical helper, and RunHistory/BanditLearning implement the *pattern* inline, but no such function is built). Severity is **LOW/non-blocking** because F-107 is explicitly **routed OUT of this ship** to PRE-PAPER-TEST (task #4) — the fabricated cite is in a disposition note, not in code this ship writes. **Recommendation:** reword F-107 to cite the actual pattern ("the `uselocale(newlocale(LC_NUMERIC_MASK,"C",…))` emit-pin pattern used at RunHistory.hpp:88 / BanditLearning.hpp:462") rather than a helper that doesn't exist; OR note `format_double_canonical` as a *to-be-built* helper. This is a Class-14 (fabricated-symbol) surface; caught here precisely because F-107 isn't in-ship.

### Q6 — Honest risks R1-R5 adequately dispositioned? **PASS — R1 is exemplary.**
- **R1 (FromDouble/ToDouble) — the standout.** Self-corrects the original "non-sqrt ops are exact integer = identical" error (the operator-pushback gap that became `feedback_enumerate_set_before_categorical_claim`). Names the exact divergence (native `floor`+`frac×2⁶⁴`-truncate vs generic multi-word), the line anchors (1250-1251 — **EXACT**), the blast radius (CfgFieldDispatch ingest, every cfg double — **VERIFIED at :80/242/283**), AND the pre-decided disposition (EXPECTED + resolved-by-F-057, not a separate fix, because FromDouble inherently touches double in both paths + native is IEEE-deterministic). This is fully dispositioned — Phase B won't be surprised. **One residual the plan handles but the implementer must internalize:** R1's "resolved by F-057" means tested==shipped, NOT native==generic. The determinism *guarantee* for FromDouble is cross-run/cross-binary determinism (verified at B.1), not equality with the generic path. The plan states exactly this; just ensure the CI gate codifies "FromDouble native is self-consistent across runs" not "native==generic."
  - **Minor cite drift inside R1:** "generic multi-word construction (`:162+`)" — `FixedPoint64.hpp:162` is the Mul overflow-mask / Division block, not the generic FromDouble path. The generic `FPN_FromDouble` lives in the `FixedPointN.hpp` primary-template region, not FP64 :162. Semantics of the claim (native FromDouble differs from generic) are correct; the anchor is wrong. Fix or drop the `:162+` ref.
- **R2 (parse_double_fast result shift):** dispositioned — from_chars correctly-rounded + matches live; regenerate goldens via `/test-strength-audit`. Severity LOW. Adequate.
- **R3 (memcpy non-x86 bytes):** NIL on x86 (`-march=native`). Adequate.
- **R4 (F-076 fingerprint break):** LOW, only if folded; "existing fingerprints non-deterministic anyway" is correct given the raw-byte hash. Adequate.
- **R5 (scope creep):** NIL by design; bounded to net-gating findings. Adequate.

---

## 10-item CLAUDE_REVIEW checklist (condensed)

| # | Item | Verdict | Note |
|---|---|---|---|
| 1 | Hot-path purity | PASS | FPN_Sqrt slow-path/feature-only; FP _to/_from accounting not the 500ns loop; parser replay-only. `calls_graph_diff verify` in acceptance. |
| 2 | Train-serve parity | PASS | sqrt determinism IS train-serve (RidgeBlender:39, M5); both replay paths (tick+depth) covered. |
| 3 | Surface area | PASS | 4 files (FixedPointN, CMakeLists, BacktestEngine, DepthReplayState) + build.sh + CI; no `if(engine_arch)` proliferation. |
| 4 | Pointer/heap lifecycle | PASS | no new heap; memcpy is stack. |
| 5 | Backward compat | PASS | "no cfg/wire-format/API changes"; F-076 lineage break documented as intentional. |
| 6 | Multi-threading | PASS | no new thread/atomic/shared state. |
| 7 | Test coverage | PASS | 2 NEW CI gates + 3239 existing now exercise shipped path; B.0 observe-the-red proves coverage. |
| 8 | Docs + invariants | PASS | extends H5 + H10; CHANGELOG row in Phase E; candidate Classes 37+ to task #1; NEW DESIGN_SPEC as H10 sister-extension (canonical-sister checked). |
| 9 | Forward maintenance | PASS | single-source-of-truth (one parser, one sqrt path) — REDUCES sites. |
| 10 | Rollback | PASS | single branch, GPG-signed tag, Version.hpp bump. Could name `pre-` anchor (DOCUMENT-only). |

**Behavior-change-via-default:** N/A (no cfg). **Atomic file writes / GUI-thread I/O / failure telemetry:** N/A (no new file writes/panels). **Locale-pin hardening:** this ship IS the locale-pin hardening for the parse path — correctly scoped.

---

## Recommendations

### Must-fix before coding
- **NONE.** No blocking gap. GREEN to start.

### Worth fixing during coding (fold at Phase A — ~20 min total)
1. **F-076: add the file:line** — `Backtest/Fingerprint.hpp:174` (fn) + `:180` (raw `SHA256_Update(&s,cfg_ptr,cfg_size)`) + caller `BacktestPanels.hpp:3157`. Note the misleading `:172` comment ("sorted order") that the code does NOT honor — that contradiction IS the F-076 hazard.
2. **F-107: replace the fabricated `tt::format_double_canonical`** with the real inline emit-pin pattern (RunHistory.hpp:88 / BanditLearning.hpp:462) OR mark it explicitly as a to-be-built helper. (Out-of-ship; quality only.)
3. **F-057: reword the build.sh "mirror"** — tsan/asan already pass `-DUSE_NATIVE_128=ON` (build.sh:226/238); the real gap is per-target `target_compile_definitions` for the default `build/` test target in CMakeLists. Verify, don't duplicate.
4. **R1 cite-drift:** `FixedPoint64.hpp:38-41` → `:33` for `FP64_FromDouble`; drop/fix the `:162+` "generic construction" anchor (that's the Mul/Div block).

### Acceptable risk (don't block)
- Sqrt-harness input passes through FromDouble (R1 surface) — expect residual low-bit noise on the 3 non-exact inputs at GREEN; consistent with R1, not an incomplete sqrt fix.
- Raw `check()` count 3132 vs cited 3239 — expected (macro/loop-expanded assertions); not drift.

---

## Map-update reminders (post-coding)
- Re-run `./tools/gen_code_map.sh` if the F-076 fold adds/renames a `Pattern_FunctionName` (CODE_MAP.md last regen 2026-05-28, one commit behind HEAD — refresh anyway).
- `tests/INVARIANTS_MAP.md`: the 2 NEW CI gates (H10 determinism, replay-locale) promote H10/H5 enforcement — add rows.
