# /blindspot-scan report — .E.0.1 pre-`.E.1` foundational-fix net — 2026-05-30

**Lens:** Layer-2 of HARDENED `/precoding-audit-gate` (HIGH-RISK, money-bearing, heavier-default). IMPLEMENTATION-DETAIL 12-category taxonomy.
**Plan:** `subplans/2026-05-29-v5.15.5.F.4d.1.E.0.1-pre-E1-foundational-fix-net.md` v0.2.
**Engine HEAD:** `0b841b3` — all 7 implicated files byte-UNTOUCHED since plan authored (`git status --porcelain` clean). All plan file:line claims VERIFIED against current code.
**Verdict:** **YELLOW** — 4 SILENT-RISK items (2 LOUD-but-plan-silent + 2 genuinely silent). No RED. All fixes sound; pre-coding amendments below close the gaps.

---

## Per-category verdict table

| Cat | Name | Verdict | Finding |
|---|---|---|---|
| B1 | Type-change cascade | IRRELEVANT | No struct field types shift; no STORAGE_T migration. FP fixes are body-level. |
| B2 | Field-name collision | N-A | No registry unification; no struct-gen. |
| B3 | Transitional-state coexistence | **SILENT-RISK** | F-056+F-058+F-057 must land ATOMICALLY; tsan/asan ALREADY build native test today (build-dir asymmetry) → half-apply window breaks suite. See SR-3. |
| B4 | Surface-G applicability | N-A | No per-entry `has_<name>` generation. |
| B5 | Compile-time scaling | IRRELEVANT | No template-instantiation growth (deletes a spec; swaps fn calls). |
| B6 | STORAGE_T variant coverage | N-A | No new STORAGE_T variant. |
| B7 | Include topology | **SILENT-RISK** | `<cstring>` (F-058) + `<charconv>` (recorder-emit) ABSENT in target headers today; include site choice matters; ParseFast carries charconv but recorders don't include it. See SR-1. |
| B8 | Type-sensitive consumer | GUARDED-BY-BUILD | F-058 memcpy / F-056 NR are byte-preserving on x86; any consumer drift is LOUD. |
| B9 | Unverified audit claim | GUARDED-BY-BUILD | R1 was empirically refuted in v0.2 with an enumerated byte-compare table (claim→evidence satisfied). FP `to_chars` compile-verified this audit. |
| B10 | Struct layout drift (H12) | IRRELEVANT | FP64/FPN<64> not used in memcmp/SHA/HMAC/wire context. F-058 is layout-preserving. `_padding=0` already present (FixedPointN.hpp:47). |
| B11 | Context-dependent C++ (`if constexpr` / const-corr) | **SILENT-RISK** | `parse_double_fast_advance` takes `const char**`; call sites pass `char**` (`strtod(p,&p)`). NOT a 1:1 drop-in — needs `const char*` local or cast. Plan body's "near-1:1 substitution" is WRONG. See SR-2. |
| B12 | Wire/row-order byte-format | **SILENT-RISK** (low) | Recorder-emit `%.8f`→`std::to_chars` CHANGES recorded CSV bytes + the parser must round-trip them. Plan asserts "no existing recordings"; verify + column-order unchanged. See SR-4. |
| B13 | Cross-walker struct uniqueness | N-A | No struct-generating walkers touched. |
| B14 | Multi-surface deletion ordering | IRRELEVANT | No feature deletion spanning ≥3 files (F-056 deletes ONE spec in ONE file). |
| B15 | Unconditionalization latent-assumption | IRRELEVANT | No cfg-gate "always-true" unconditionalization. |
| B17 | Forward-decl namespace shadow | N-A | No header extraction / subfolder split. |
| B18 | Block-scope statics on hoist | N-A | No lambda/fn hoist. |
| B19 | Doc-sweep terminology drift | N-A | No doc/terminology sweep (code ship). |

**Tally:** SILENT-RISK 4 · GUARDED-BY-BUILD 2 · IRRELEVANT 6 · N-A 8. (B16 absent from taxonomy.)

---

## SILENT-RISK items (file:line + concrete amendment)

### SR-1 (B7) — include topology for the two new standard headers
**Sites:**
- F-058 `memcpy`: `FixedPoint/FixedPointN.hpp:1221-1226` (inside `#ifdef USE_NATIVE_128`, after `#include "FixedPoint64.hpp"` at :1218). NEITHER `FixedPointN.hpp` nor `FixedPoint64.hpp` includes `<cstring>`/`<string.h>` today (verified — both pull only `<stdint.h> <assert.h> <math.h>`).
- recorder-emit `std::to_chars`: `DataStream/TickRecorder.hpp:186` + `DataStream/DepthRecorder.hpp:249`. Neither includes `<charconv>` (they have `<stdio.h><stdlib.h><stdint.h><string.h><time.h>...`). ParseFast.hpp carries `<charconv>`+`<cstring>` but the recorders do NOT include ParseFast.hpp.

**Risk:** LOUD if missed (compile error) — but the `memcpy` is gated behind `USE_NATIVE_128`, so if `<cstring>` is added in the wrong place (e.g. inside the `#ifdef` only) a generic-FPN<64> TU is unaffected while a native TU links — no silent corruption, but a confusing first-build failure. No include CYCLE risk (both are leaf standard headers; FixedPoint64.hpp is `#include`d by FixedPointN.hpp one-way; no reverse edge).

**Amendment:**
1. Add `#include <cstring>` to **FixedPointN.hpp top include block (~line 24-27), UNCONDITIONALLY** (not inside the `#ifdef`) — `memcpy` is std-blessed everywhere; keeps the header self-contained for any include order.
2. Add `#include <charconv>` to the top of BOTH `TickRecorder.hpp` and `DepthRecorder.hpp`. Do NOT rely on transitive inclusion via ParseFast (recorders are emit-only; they have no reason to pull ParseFast).

### SR-2 (B11) — `parse_double_fast_advance` is NOT a const-clean drop-in for `strtod`
**Sites:** `Backtest/BacktestEngine.hpp:88,89,95,96` + `DataStream/DepthReplayState.hpp:224-227` — all use `char *p; ... = strtod(p, &p);` where `&p` is `char**`.
**Primitive:** `tt::parse_double_fast_advance(const char *p, const char **end_out)` (`ParseFast.hpp:78`). The `end_out` param is `const char**`.
**Risk:** `char**` → `const char**` is NOT an implicit conversion in C++ (it is ill-formed — would allow const-violation). `tt::parse_double_fast_advance(p, &p)` as the plan literally writes it will **fail to compile**. LOUD, but the plan body (§ F-054/F-055, "near-1:1 substitution… my first draft over-engineered it") explicitly asserts a clean swap and would burn a build cycle + force an unplanned in-the-moment restructure.
**Amendment (pick one, document in plan body before coding):**
- **(A) preferred** — declare the cursor as `const char *p = line;` (and `const char *p = buf;`) at each parse block, since after the swap nothing writes through `p` except the parser's own `*end_out`. Verify the surrounding integer parses on the same `p` (`strtoll`/`strtoull`/`strtol` at BacktestEngine.hpp:87,90,94,97-99 + DepthReplayState.hpp:222-223) ALSO accept `const char*` — they take `char**`, so they have the SAME issue. → the WHOLE cursor can't be a single `const char*` if integer `strto*` stays. Resolution: keep a `char *p` and pass `(const char**)&p` via an explicit cast at each `parse_double_fast_advance` call, OR migrate the integer parses too (they're locale-immune, KNOWN-PENDING — a cast is the minimal net-scoped change).
- **(B)** add a `char**` overload `tt::parse_double_fast_advance(char *p, char **end_out)` to ParseFast.hpp that forwards. Cleaner at call sites; SSoT-respecting if it forwards to the const core. Flag as a (small) ParseFast.hpp surface addition not in the current plan body.

### SR-3 (B3) — atomic-land window + tsan/asan native asymmetry
**State today:** `build/` (default `test`) configures `cmake -B build -DCMAKE_BUILD_TYPE=Release` → `USE_NATIVE_128` option defaults ON → **`engine` builds native, but `controller_test`/`parity_harness` build GENERIC** (CMakeLists 213-242 have NO `target_compile_definitions(... USE_NATIVE_128)` — the option only wires `engine`/`engine_gui`/`foxml_suite`). This IS F-057. Meanwhile `build_tsan`/`build_asan` pass `-DUSE_NATIVE_128=ON` via raw `CMAKE_CXX_FLAGS` (build.sh:226,238) → global `-D` → **`controller_test` under tsan/asan ALREADY builds native today.**
**Risk (SILENT/build-state):** (a) F-057's `if(USE_NATIVE_128) target_compile_definitions(controller_test PRIVATE USE_NATIVE_128)` would DOUBLE-define under tsan/asan (already in CXX_FLAGS) — harmless `-D` repeat, but messy; (b) if F-057 lands before F-056 in `build/`, the suite genuinely exercises native sqrt → this is the v0.2 "observe-the-red" intent; confirmed the suite stays GREEN regardless (sqrt assertions are `rel_eps`), so the RED only shows in the standalone harness — the atomic-land risk is LOW for correctness but the build-dir asymmetry means **the determinism CI gate must pin WHICH build dir/flag set it runs under** or it can pass on a generic-test build and miss the point.
**Amendment:**
1. Land F-056 + F-058 + F-057 in ONE commit (already the plan's "Phase B atomic" intent — make the atomicity a hard pre-coding note, not just phase prose).
2. F-057: gate the `target_compile_definitions` on `if(USE_NATIVE_128)` so it tracks the option; this is consistent with the tsan/asan global `-D` (no conflict — PRIVATE add is idempotent with the CXX_FLAGS `-D`).
3. The determinism CI gate must run against a build that ACTUALLY defines `USE_NATIVE_128` for the test target — assert it (e.g. a `#ifndef USE_NATIVE_128 #error` in the determinism harness TU, or a `static_assert`). Otherwise "tested==shipped" silently regresses if a future edit drops the define.

### SR-4 (B12) — recorder-emit byte-format change + write∧read loop
**Sites:** `TickRecorder.hpp:186-187` (`%lld,%.8f,%.8f,%d`) + `DepthRecorder.hpp:249-255` (`%llu,%llu,%.8f,%.8f,%.8f,%.8f`). `std::to_chars` shortest-round-trip emits a DIFFERENT byte string than `%.8f` (e.g. `0.1` vs `0.10000000`, and full precision vs 8-fixed).
**Risk:** the plan correctly pairs this with the parse-side fix (F-054/55) to complete the loop, and asserts "no existing recordings → goldens generate fresh → no byte-compat constraint." That is the right call IF true. SILENT failure mode: any retained CSV (committed test fixture, operator's recorded day on disk, a golden checked in by Net-1) parsed after the emit change would round-trip differently. Also: `std::to_chars(buf, buf+N, d)` writes NO NUL — the `fprintf` is replaced by a manual buffer assembly; column COUNT/ORDER + the `\n` + the integer columns (`%lld`/`%llu`/`%d`) must be preserved exactly.
**Amendment:**
1. Before coding, `grep`/`ls` for any committed `*.csv` recording fixture + confirm Net-1 has NOT yet frozen a recorder-emit golden (the plan says recordings regen fresh — verify no fixture under `tests/`/`data/` is a recorder output).
2. Keep integer columns + delimiter + trailing `\n` byte-identical; only the `%.8f` float fields change. Assemble into a stack buffer with explicit NUL/length handling (to_chars returns `ptr`; use it). Add a unit assertion that a known FPN value emits the expected shortest string AND parses back byte-exact (write∧read identity) — this is the standing gate the plan wants.

---

## Punch-list (ordered by severity)

1. **SR-2 / B11** — resolve `const char**` vs `char**` mismatch in plan body BEFORE coding (cast at call site OR `char**` overload in ParseFast.hpp). Closes the only "plan says drop-in, compiler says no" item. (~10 min plan amend.)
2. **SR-1 / B7** — specify `#include <cstring>` (FixedPointN.hpp top, unconditional) + `#include <charconv>` (TickRecorder.hpp + DepthRecorder.hpp top). (~5 min.)
3. **SR-3 / B3** — make F-056+F-058+F-057 atomic-commit a hard note; gate F-057 define on `if(USE_NATIVE_128)`; add `#ifndef USE_NATIVE_128 #error` to the determinism harness so tested==shipped can't silently regress; reconcile with tsan/asan global `-D`. (~10 min.)
4. **SR-4 / B12** — verify no retained recorder CSV fixture/golden; preserve integer columns + delimiters byte-exact; add write∧read round-trip unit assertion. (~10 min verify + folds into the planned recorder-emit test.)

## Recommended next move
- (X) Audit-first: amend plan body for SR-1/SR-2/SR-3/SR-4 (~35 min total) BEFORE coding — all four are cheap text amendments; SR-2 in particular prevents a guaranteed mid-coding compile-fail + improvised restructure on a money-bearing path.

## Inflection check
Per `feedback_iteration_spiral_signals_audit_meta_gap`: this is the FIRST blindspot fire on `.E.0.1` (no prior iteration spiral). NEW pillars surfaced: **0** (all findings map to existing B3/B7/B11/B12). No taxonomy amendment needed. SR-2 is a clean instance of B11's "context-dependent C++ construct" generalized from `if constexpr` to const-correctness of a primitive's signature — worth a one-line worked-example note in B11 at ship close, but not a new pillar.

---

**Returned to operator for triage per `feedback_consult_on_audit_findings`. Does NOT recommend proceeding to code — Caramel triages.**
