# /readiness report — 2026-05-06-v5.11.1-hot-path-avx512.md — 2026-05-06

**Plan audited:** `plans/2026-05-06-v5.11.1-hot-path-avx512.md`
**Sprint:** Sprint C (v5.11 optimization sprint), ship 3/9
**Branch (claimed):** `feat/v5.11-optimization` at `d1fb214` (tag `v5.11.0.1`) — VERIFIED HEAD
**Predecessor:** v5.11.0.1 at `d1fb214` (no I/O on hot path) — VERIFIED via `git log`
**Master plan:** `plans/2026-05-06-MASTER-v5.11-optimization-sprint.md` § v5.11.1 — VERIFIED, mapping consistent
**Audit date:** 2026-05-06
**Audit run by:** Claude Opus 4.7 (1M context), readiness skill

---

## Verdict — **YELLOW**

The plan is structurally sound and reflects deep prior thinking; all 5 phases match the audit's Part 1 items, the order is dependency-correct, and the discipline doc's pre-merge checklist is integrated. **Three categories of issues warrant amendment before coding starts.**

---

## Executive summary

1. **All file:line refs in the stale-claim audit are off by ~+11 lines** (not the plan's claimed +9). v5.11.0.1 added 19 LOC across 2 sites; the struct-tail extension shifts every line at/below 142 by +10, and the `core->ring_push_failures = 0;` addition in `ExecutionCore_Init` shifts everything below by +1 → net +11 at line 247 onwards. Plan's stale-claim table marks them all "VERIFIED" while flagging "+9 shift" — this is internally contradictory and must be refreshed.
2. **Plan undercounts callers requiring template-bool migration.** Plan Phase 1.1 lists `EngineSharded.hpp`, `BacktestSharded.hpp` (no caller present), `ShardedBacktestDriver.hpp`, `LegacyReferenceDriver.hpp` (exists but no caller). The actual call sites are 2 production (`EngineSharded.hpp:2000`, `ShardedBacktestDriver.hpp:197`) + **6 test sites in `tests/controller_test.cpp:5818,5841,5880,5886,5914,5919`** that the plan does not enumerate. Adding a non-deducible second template parameter forces all 8 sites to be updated explicitly; tests will fail to compile if missed.
3. **Plan's per-phase ns-gain estimates do not always match the audit.** The audit gives explicit "1ns" for Phase 1.1 (the load + branch); plan claims "5-10ns". Plan's "30-80ns" for 1.5 mixes the audit's 30-50ns permission ping-pong with a self-attributed Finding A live_sl single-line load gain — fine if the dual attribution is made explicit. Plan's "5ns" for 1.4 is plan-internal (audit gives no number). None of these are blocking, but the gain numbers should not be presented as audit-derived when they are plan-derived.

After (1)-(3) are amended and the secondary items in §"Unstated gaps" are addressed, plan can move to GREEN.

---

## Stale-claim re-walk (vs HEAD `d1fb214`, post v5.11.0.1)

| # | Plan claim | Verification @ HEAD `d1fb214` | Status |
|---|---|---|---|
| 1 | `ExecutionCore_Tick` definition at `ExecutionCore.hpp:236` | Actual line **247** (+11) | STALE (line drifted) |
| 2 | `lat_enabled` checks at lines 240, 242, 505 | Actual **251, 253, 515** (+11 each) | STALE |
| 3 | ExecutionCore struct at lines 62-143 | Actual **62-153** (closing brace at 153, +10 from struct tail extension) | STALE (end shifted) |
| 4 | `live_sl` field at line 77 | Confirmed at line 77 — UNCHANGED (precedes the v5.11.0.1 extension) | VERIFIED |
| 5 | `permission` field at line 66 | Confirmed at line 66 — UNCHANGED | VERIFIED |
| 6 | `live_tp_b/sl_b` declarations near 95-96 | Confirmed at lines 95, 96 — UNCHANGED | VERIFIED |
| 7 | Permission writer at line 210 (in `ExecutionCore_SetPermission`) | Actual **line 230** (+20 — plan claimed +9) | STALE |
| 8 | Permission reader at line 365 (within `Tick`) | Actual **line 376** (+11) | STALE |
| 9 | Leg B branch gate at line 346 | Actual `if (__builtin_expect(active_b, 0))` at **line 357** (+11) | STALE |
| 10 | CMOV active/inactive blend at lines 276-277 | Actual **lines 287-288** (+11) | STALE |
| 11 | Rare-branch event push at line 395 | Actual `if (__builtin_expect(can_enter \| can_exit_a \| can_exit_b, 0))` at **line 406** (+11) | STALE |
| 12 | FPN<64> = 24 bytes at `FixedPoint/FixedPointN.hpp:31-41` | Read confirms `uint64_t w[N]` (N=2 for F=64) + `int32_t sign`; with 8-byte alignment requirement → 16 + 4 + 4 padding = 24 B. Math is correct. | VERIFIED |
| 13 | `LATENCY_PROFILING` cmake option at `CMakeLists.txt:18` | Read confirms `option(LATENCY_PROFILING …)` at line 18 | VERIFIED |
| 14 | Replay-determinism test at `tests/controller_test.cpp:10251` | Test BLOCK lives lines 10147-10260; `check(...)` line 10258. Line 10251 is mid-loop body in the bytewise-compare. Plan's pointer is approximately right but should refer to 10147 (block header) or 10258 (the assertion) | LOOSE |
| 15 | `tools/calls_graph_diff.sh` exists | Confirmed | VERIFIED |
| 16 | Master plan + predecessor + audit + discipline doc + reference plans all exist at the named paths | All confirmed via `ls plans/`. Note `plans/2026-05-08-v5.11-OPTIMIZATION-REFERENCE.md` AND `plans/2026-05-08-v5.11-optimization-reference.md` both exist at identical size 4516B — likely duplicate; not a plan defect | VERIFIED |
| 17 | i7-11850H is dev box with AVX-512 | Cannot verify (sandbox blocks `/proc/cpuinfo` read). Audit + plan + discipline doc all reference i7-11850H; existing code references **i5-1035G4** at multiple sites including ExecutionCore.hpp comments → there are TWO machines in the operator's environment. Plan should clarify whether `i7-11850H` is the deployment box (audit's target) or the bench/dev box | UNVERIFIED |

**Summary:** 7/17 line-citation rows are STALE by +10 to +20 lines; the plan's "verified +9 shift" annotation is approximately right for the in-`Tick`-body lines (+11) but wrong for the writer at line 230 (+20, since `_SetPermission` is between the struct and `Tick` and is also affected by `_Init`'s +1 shift). All STALE rows are clerical drift; none change the structural correctness of the plan. **Refresh the table with the actual line numbers before coding starts.**

---

## Cold-pickup re-walk (CLAUDE.local.md 10-field rule)

Plan claims 10/10. Re-walked independently:

| # | Field | Plan claim | Re-walk verdict |
|---|---|---|---|
| 1 | Branch state named | `feat/v5.11-optimization` at `d1fb214` | ✓ VERIFIED |
| 2 | Phase order matches dependency | 1.1 → 1.5 → 1.2 → 1.3 → 1.4 (each phase's deps documented) | ✓ — **but note** dependency claim "1.2 operates on the new layout" is actually "1.2 *benefits from* the new layout, but doesn't strictly require it." Plan's choice of order is sound; the dependency framing is overstated. Not a defect. |
| 3 | First concrete move per phase | Each phase has Step 0 with file:line + code shape | ✓ — but Step 0 file:line refs are stale (see §Stale-claim audit) |
| 4 | Function/macro names | `_mm512_cmpge_epu64_mask`, `_mm512_mask_blend_epi64`, `__AVX512F__`, `if constexpr (LAT_ENABLED)` | ✓ all real intrinsics + standard C++17 |
| 5 | File:line refs for cited tests / baselines | 13 citations | ✓ provided, **but 7/13 are stale by +11 lines** — see §Stale-claim audit |
| 6 | Stale-claim audit section present | Yes | ✓ present; **but internally inconsistent** (lines marked VERIFIED while flagging +9 drift) — needs refresh against actual +11 |
| 7 | Effort vs LOC reconciled | ~220-300 LOC source + ~140 test for 10-14h | ✓ reasonable. Phase 1.1 estimate (~30 LOC) needs revision once test-site update count is correct (8 sites not 4). |
| 8 | Source-audit refs with paths | `LATENCY_OPTIMIZATION_AUDIT.md` Part 1 + `STRATEGY_AND_CODING_RULES.md` §4-7 + `latency-path-discipline.md` + 2 reference plans | ✓ |
| 9 | Predecessor/dependent plans named with paths | `plans/2026-05-06-v5.11.0-system-foundation.md` predecessor; v5.11.2 successor (pending) | ✓ |
| 10 | Tag names locked + rollback anchors | `pre-v5.11.1` rollback + `v5.11.1.1/.5/.2/.3/.4` (1.4 conditional) + `v5.11.1` final | ✓ |

**Cold-pickup score: 9/10 effective.** The stale line numbers (#5, #6) are the gap — fresh session would hit them on first edit, lose ~10min to re-grep. Refresh once and 10/10.

---

## Audit alignment check

Plan maps directly to LATENCY_OPTIMIZATION_AUDIT.md Part 1's 5 items:

| Plan phase | Audit item | Audit ns claim | Plan ns claim | Notes |
|---|---|---|---|---|
| 1.1 (template-bool) | Audit 1 (Compile-Time Elision) | "~1ns load + branch" | "5-10ns" | **Plan inflates by 5-10×.** Even with 2 lat_enabled checks (entry + exit), the savings cap is ~2ns. Reduce plan claim to "~1-3ns" or note the inflation. |
| 1.5 (cache layout + perm isolation + Finding A) | Audit 5 (Permission False Sharing) | "30-50ns stall on next tick" | "30-80ns" | Plan adds Finding A (`live_sl` single-line load) on top. Reasonable but make the dual attribution explicit: "30-50ns from audit Part 5 + ~10-30ns plan-derived from Finding A live_sl." |
| 1.2 (AVX-512 leg compares) | Audit 2 (Vectorized Leg B) | "branch entirely removed; both legs in 1 cycle" (no ns) — leg B currently costs ~40ns per audit | "40ns" | Reasonable — matches the audit's leg-B cost description. |
| 1.3 (SIMD blend) | Audit 3 (Vectorized CMOV) | (no ns claim) | "5-10ns" | Plan-internal estimate; not audit-derived. Should annotate as such. |
| 1.4 (branchless ring commit) | Audit 4 (Branchless Ring) | (no ns claim) | "5ns" | Plan-internal estimate; plan is honest ("worth 5ns at best"). Acceptable, but tag explicitly as plan-derived not audit. |

**Total expected p50 improvement: plan claims 85-145ns.** With the corrected 1.1 estimate (~2ns instead of 5-10ns), revised total is **77-137ns**. Still meaningful, but the upper bound is more like ~100ns realistic. Pre-coding section "Theme" should reduce the optimistic upper bound or annotate as best-case.

---

## Codebase grep audit (Phase 1.5 pre-conditions)

Plan calls for greps before reordering struct. Ran on operator's behalf:

| Grep | Plan expectation | Actual result |
|---|---|---|
| `grep -rn "offsetof(ExecutionCore" --include="*.hpp" --include="*.cpp"` | Find any code that pinned offsets | **EMPTY** — no hardcoded offsets. ✓ Plan's reorder is safe. |
| `grep -rn "memcpy.*ExecutionCore\|memcpy.*&core->\|memcpy.*core->"` | Find any direct-memory copies | **EMPTY** — no memcpy on ExecutionCore. ✓ |
| `grep -rn "__AVX512F__\|_mm512_"` | Existing AVX-512 in codebase | **EMPTY** — first AVX-512 code in the engine. Plan's `#ifdef __AVX512F__` + scalar fallback infrastructure is necessary; cannot piggyback on existing pattern. |
| `grep -rn "immintrin\|xmmintrin\|x86intrin"` | Existing intrinsic header includes | `main.cpp:51 (x86intrin)`, `CoreFrameworks/SystemInit.hpp:16 (xmmintrin)`, `CoreFrameworks/EngineSharded.hpp:76 (x86intrin)`. ✓ Header infrastructure exists. |
| `grep -rn "core\.entry_price\|core->entry_price"` (steady-state read check) | Plan claims entry_price is "WRITE-only on entry events" | Confirmed for production hot path: only writes at `ExecutionCore.hpp:178, 185 (Init)` and `442, 469 (rare entry branch)`. **However:** `experiments/per_core_sharding/bench_batch_floor.cpp:129` reads `g_core.entry_price` in steady state, and `CoreFrameworks/ShardedSnapshotPersist.hpp:619` writes it on snapshot recovery. Bench is offline; recovery is not hot-path. Plan's claim holds for production hot path. ✓ |

---

## Discipline doc compliance check

The plan claims "every phase requires" the 5-item pre-merge checklist from `plans/2026-05-06-latency-path-discipline.md`. Walked it:

| Item | Coverage in plan | Verdict |
|---|---|---|
| 1. `./build.sh test` 1642/0 baseline | Each phase's "Sub-ship gate" line | ✓ |
| 2. `-S` assembly inspection of `ExecutionCore_Tick` body — no stack spills, no malloc/free, no libc fnames | Phase 1.2 + 1.5 + final tag `-S` step listed | ✓ |
| 3. `tools/calls_graph_diff.sh` — no orphans | Final tag step 6 only — **not per-phase** | PARTIAL. For incremental phases, no orphan check. Worth adding. |
| 4. Replay-determinism test (`tests/controller_test.cpp:10251`) — bytewise-equal | Final tag step 7 + each phase's "verification" | ✓ |
| 5. Bench gate (operator-side): p99 ≤ pre-ship p99 across 10M-tick replay | Final tag step 8 + open-question item 3 | ✓ — operator-side, called out clearly |

Discipline rule self-check:
- **Rule 1 (cache layout)** — Phase 1.5 explicit; static_asserts proposed. ✓
- **Rule 2 (no I/O on hot path)** — already shipped in v5.11.0.1; plan doesn't reintroduce. ✓
- **Rule 3 (SPSC failure → counter)** — Phase 1.4 explicitly preserves the `ring_push_failures` counter. ✓
- **Rule 4 (branch predictor + register pressure)** — Phase 1.1 template elision is the canonical example; Phase 1.2 risk section calls out stack spills. ✓ — but the plan's mitigation ("inspect -S … use `register` hints or refactor scope if spills occur") is reactive. **Add a concrete spill-detection grep**: `grep -E '(\$0x[0-9a-f]+)?\(%rsp\)|-[0-9]+\(%rbp\)' exec_core.s` to detect stack-relative writes to function frame slots.
- **Rule 5 (FPN sizing)** — plan correctly uses 24-byte FPN<64> assumption. ✓
- **Rule 6 (no pointer chasing)** — plan doesn't introduce any. ✓
- **Rule 7 (cross-thread sync)** — plan correctly isolates `permission` to its own line. ✓

---

## Unstated gaps (P1 = blocker, P2 = should-fix, P3 = polish)

### P1 — Phase 1.1 caller enumeration is incomplete

**Plan §Phase 1.1 caller-site list:**
> - `EngineSharded.hpp` per-core hot-path loop
> - `BacktestSharded.hpp` per-core driver (likely the same)
> - `ShardedBacktestDriver.hpp`
> - `LegacyReferenceDriver.hpp` (if still alive)

**Actual (verified by grep):**
- `CoreFrameworks/EngineSharded.hpp:2000` — `ExecutionCore_Tick(&cores[i], t);` ✓ matches plan
- `CoreFrameworks/ShardedBacktestDriver.hpp:197` — `ExecutionCore_Tick(core, tick);` ✓ matches plan (although plan called it "BacktestSharded.hpp" — that file exists but doesn't call `ExecutionCore_Tick`)
- `CoreFrameworks/LegacyReferenceDriver.hpp` — file exists but **no `ExecutionCore_Tick` call** (greps clean). Plan's "(if still alive)" assumption is incorrect.
- `Backtest/BacktestSharded.hpp` — file exists but **no `ExecutionCore_Tick` call**.
- `tests/controller_test.cpp:5818, 5841, 5880, 5886, 5914, 5919` — **6 test call sites that plan does not enumerate.**

When `ExecutionCore_Tick` becomes `template <unsigned F, bool LAT_ENABLED>`, the second arg cannot be deduced from function arguments → all 8 callers must explicitly specify `<F, false>` (or `<F, true>` for the latency build). **Tests will fail to compile until updated.** Plan's Phase 1.1 effort estimate (~30 LOC source) covers the production callers but not the 6 test sites.

**Fix:** Re-list callers as: 2 production (EngineSharded, ShardedBacktestDriver) + 6 tests + 0 BacktestSharded/LegacyReferenceDriver. Bump Phase 1.1 effort to ~50 LOC source + ~20 LOC test.

### P1 — Stale line numbers in plan body + audit table

Body sections (Phase 1.1, 1.5 Step 0/1/2, Phase 1.2 Step 0, etc.) all use the pre-v5.11.0.1 line numbers. Stale-claim audit acknowledges this but uses "+9" — actual shift is +11 for in-`Tick` lines and +20 for the writer at line 230 (`SetPermission` is shifted by both struct extension +10 and `_Init` extension +1, plus `SetPermission` was already 9 lines past `_Init`). Refresh entire stale-claim table with current numbers, then re-walk plan body Step 0/Step 1/Step 2 references for consistency.

### P2 — Snapshot recovery write site to `entry_price`

`CoreFrameworks/ShardedSnapshotPersist.hpp:619` writes `core_ptr->entry_price = entry;` during snapshot recovery. The new layout puts `entry_price` on cache line 1 (intentional — it's not in the steady-state path). This still works (field name unchanged), but the layout is implicitly relying on snapshot recovery being a one-time event — a fact worth stating in the plan's Phase 1.5 verification section. Add a 1-line note: "Snapshot recovery (ShardedSnapshotPersist.hpp:619) writes entry_price on resume; not steady-state, but verify the new layout's by-name field access still compiles."

### P2 — RDTSC asymmetric pattern (Finding D) + standardization claim

Plan §Phase 1.1 states: "**Recommend `rdtscp; lfence` both sides**". Verified that current code uses `mfence; lfence; rdtsc` at entry (line 255) and `rdtscp; lfence` at exit (line 517). Standardizing on `rdtscp; lfence` is reasonable — but plan should also call out that this changes the entry's ordering semantics (rdtscp is serializing post-execution, while mfence+lfence+rdtsc is conservative pre-execution). For the latency-bracket use case the change is fine. **Add to test plan:** `test_rdtsc_bracket_consistent` — verify entry+exit measurements with the new pattern give the same delta semantics as the old (modulo the eliminated mfence stall).

### P2 — Phase 1.5 dependency framing on Phase 1.2

Plan says "1.2 operates on the newly-laid-out fields; doing 1.5 after 1.2 would require re-doing 1.2's intrinsics offsets." Verified: AVX-512 intrinsics use field-by-name access (e.g., `_mm512_set_epi64(core->live_tp.w[0], …)`), not raw offsets. **The dependency is `1.5 makes 1.2 cleaner` not `1.5 blocks 1.2`.** Plan's chosen order is still optimal (1.5 second), but the framing should be relaxed to acknowledge that 1.2 could technically operate on either layout. Cosmetic only.

### P2 — ns-gain estimates not audit-attributed

See §Audit alignment check. Phase 1.1 (5-10ns vs audit's 1ns), Phase 1.3 (5-10ns plan-internal), Phase 1.4 (5ns plan-internal) — annotate which numbers are audit-derived vs plan-derived. Total p50 improvement claim of "85-145ns" should be revised to ~75-135ns or annotated as upper-bound.

### P2 — Per-phase calls_graph_diff missing

Discipline doc pre-merge checklist item 3 is `tools/calls_graph_diff.sh`. Plan only runs it at final tag, not after each sub-tag. Add to each phase's "Sub-ship gate" line.

### P2 — Stack-spill detection mechanism

Plan says "inspect assembly … no stack spills." Concrete mechanism missing. **Add to each AVX-512 phase's verification step:**
```bash
grep -E '(\$0x[0-9a-f]+)?\(%rsp\)|-[0-9]+\(%rbp\)' exec_core.s
# Count stack-relative writes inside ExecutionCore_Tick body.
# Pre-v5.11.1 baseline count: <N> (capture before phase 1.2).
# Post-phase: count must be ≤ baseline + epsilon (function preamble).
```

### P3 — Hardware identity ambiguity (i7-11850H vs i5-1035G4)

Code comments reference `i5-1035G4` as bench hardware (lines 22, 57, 266, 292, 323 of `ExecutionCore.hpp`). Audit + plan reference `i7-11850H` as deployment hardware. Plan §Open question 1 says "Build host (i7-11850H) has AVX-512" — but i5-1035G4 (Ice Lake mobile) does NOT have AVX-512 (Intel disabled it in consumer 10th-gen mobile). If bench/dev runs on i5-1035G4, the AVX-512 code path will only execute on the i7-11850H — meaning bench validation cannot directly measure the AVX-512 gain on the dev box. Plan should clarify whether bench measurement happens on the i7-11850H or the i5-1035G4.

### P3 — Replay-determinism test pointer (tests/controller_test.cpp:10251)

Plan points to line 10251. Actual block is at lines 10147-10260 (header at 10147, key assertion at 10258). Line 10251 is mid-loop; it's a load-bearing line for the bytewise compare but not the assertion entry. Cosmetic — refer to 10147 (block header) or 10258 (assertion) for clarity.

### P3 — Test-count baseline number

Plan claims "1642/0 baseline." Grep of `check(` in `tests/controller_test.cpp` returns 1605 — does not match 1642. CLAUDE.md mentions 739+ (very stale). The 1642 number must come from running the test binary; cannot verify in sandbox. Trust the operator's count, but the discipline doc + master plan + this plan should agree (they do — all use 1642). No action; flag if plan's expected post-coding count of 1650 doesn't match after the new tests land.

### P3 — Duplicate reference plan files

`plans/2026-05-08-v5.11-OPTIMIZATION-REFERENCE.md` and `plans/2026-05-08-v5.11-optimization-reference.md` both exist with identical size 4516B. Plan references the uppercase one. Worth deduping (case-only difference can confuse case-insensitive filesystems, though Linux ext4 is case-sensitive).

---

## Risk-section sanity check

The plan's §Open Questions / Explicit Deferrals enumerates:
1. AVX-512 hardware availability — see P3 above. Plan handles via `#ifdef __AVX512F__` + scalar fallback. ✓
2. Phase 1.4 conditional ship — plan defers based on post-1.2/1.3 `-S` inspection. Reasonable.
3. Bench harness operator-side — clear.
4. Asymmetric RDTSC — see P2 above.
5. **Cross-build determinism** — "4 build variants × 1 replay = 4 hashes that must match." This is a real 4-axis validation requirement (PGO on/off × AVX-512 on/off). Plan says operator does this once at final v5.11.1. **The deferral is a P2 concern:** if a determinism mismatch surfaces between `-O3 -march=native -DAVX512` and `-O3 -mno-avx512f`, root-cause is ambiguous between (a) AVX-512 code path bug, (b) `-march=native` enabling other optimizations, (c) PGO speculation differences. Plan should either:
   - Reduce scope to 2 axes (AVX-512 on/off only) for this ship, defer PGO axis to v5.11.0.D follow-up, OR
   - Provide a structured triage flow (which axis to bisect first if hashes differ).

---

## Recommendations

1. **Refresh the stale-claim audit table** with actual line numbers (+11 for in-Tick lines, +20 for `_SetPermission` writer). Update plan body's Step 0 file:line refs in Phase 1.1, 1.5, 1.2, 1.3, 1.4.
2. **Re-enumerate Phase 1.1 callers** to include the 6 test sites in `tests/controller_test.cpp` and remove the BacktestSharded/LegacyReferenceDriver phantoms. Bump Phase 1.1 effort.
3. **Annotate ns gains** as audit-derived vs plan-derived; revise Phase 1.1 claim to ~1-3ns.
4. **Add per-phase calls_graph_diff invocations** to each Sub-ship gate.
5. **Define stack-spill detection grep** as a concrete mechanism in Phase 1.2's verification.
6. Address P2 items above.

---

## Cross-references

- Predecessor: `plans/2026-05-06-v5.11.0-system-foundation.md` (v5.11.0 final at `370a7ba`); `v5.11.0.1` at `d1fb214`
- Master plan: `plans/2026-05-06-MASTER-v5.11-optimization-sprint.md` § v5.11.1
- Discipline doc: `plans/2026-05-06-latency-path-discipline.md` (verified comprehensive; Rule 1 layout + Rule 2 I/O + Rule 4 branchless + Rule 5 FPN sizing all referenced)
- Audit: `DOCS/LATENCY_OPTIMIZATION_AUDIT.md` Part 1 (5 items map 1:1 to plan phases)
- Coding rules: `DOCS/STRATEGY_AND_CODING_RULES.md` §4 Branchless + §5 AVX-512 + §7 L1 Cache (all aligned with plan)
- Successor: v5.11.2 (slow path O(1) regression + RollingStats padding) — pending plan, opens after v5.11.1

---

## Summary table

| Item | Verdict |
|---|---|
| Branch state correct | ✓ |
| Phase order dependency-correct | ✓ (with cosmetic dependency-framing nit) |
| Each phase has Step 0 with file:line + code shape | ✓ but **lines stale** |
| Function/macro names valid | ✓ |
| File:line refs verified | ✗ 7/13 STALE |
| Stale-claim audit present and accurate | ✗ internally inconsistent (+9 claimed, +11 actual) |
| Effort estimate plausible | ⚠ Phase 1.1 LOC under-estimated by ~6 test sites |
| Source-audit refs with paths | ✓ |
| Predecessor / successor named | ✓ |
| Tag names locked + rollback anchors | ✓ |
| Cold-pickup score | 9/10 |
| Audit alignment | ✓ items map 1:1 |
| Audit ns claims vs plan ns claims | ⚠ 1.1 inflated 5-10×; 1.3/1.4 plan-internal |
| Codebase pre-condition greps clean | ✓ (no offsetof, no memcpy, no AVX-512 yet) |
| Discipline doc 5-item pre-merge checklist | ✓ (calls_graph_diff per-phase missing) |
| Unstated gaps | 2× P1, 5× P2, 4× P3 |

**Verdict — YELLOW.** Plan is structurally sound with deep prior thinking; all 5 phases are audit-aligned, the order is correct, the discipline doc is integrated. Two P1 issues (stale line numbers + undercounted callers) need amendment. Five P2 polish items strengthen verifiability. After these are addressed, the plan can move to GREEN and coding can begin on `pre-v5.11.1` rollback anchor.

**Top recommendation:** Run a single `sed`/find-replace pass to refresh all `ExecutionCore.hpp:NNN` references against the current `d1fb214` line numbers (mostly +11 inside `Tick`, +20 for `SetPermission`), then add the 6 test call sites in `tests/controller_test.cpp` to Phase 1.1's caller enumeration before kicking off coding.
