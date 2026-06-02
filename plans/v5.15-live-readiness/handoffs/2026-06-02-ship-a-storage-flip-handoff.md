---
type: handoff
ship_tag: "#11 Ship-A storage flip (16B FixedPoint<2,64> wiring) — the atomic phase that makes FPN<64> actually BE 16B"
plan_type: refactor (16B binary-core compaction)
sprint: v5.15-live-readiness
sprint_end_goal: make the codebase more maintainable for future development (MVP → professional; .E is the foundational rework)
ship_end_goal: "Ship A — compact the binary numeric core FPN<64> 24B sign-mag → FixedPoint<2,64> 16B two's-complement, VALUE-equivalently; tag = the STOP-before-money boundary (D-130). The 16B op library is BUILT + PROVEN; the flip WIRES it."
coding_status: op-library-complete-and-committed + storage-flip-PENDING (the flip is the next, atomic, red-build-until-done phase)
predecessor_handoff: handoffs/2026-06-01-session8-ship-a-integration-handoff.md
decision_log: plans/v5.15-live-readiness/decision-logs/v5.15.5.F.4d.1.E-architecture-v2.md (D-97..D-146; SSoT; D-142..D-146 = Session-9)
engine_head: 6c0e570 (feat/v5.15-live-readiness; PUSHED. Ship-A op-library ends at 4efa8d3; the commits on top are a SEPARATE, PARALLEL guard-hardening pass [NOT Ship-A code]: 8438bbd/8182c43 = identifier-retirement H21 (Check H); dad6f19 = bounds static_asserts + OrderEventLog <cerrno>; d2ee570 = maker-fee desync guard; a095e27/6c0e570 = TOOLS.md enrollment + the 2 guard selftests. The flip interacts with these — see step 5 + §5.5.)
workspace_head: 497dc3e (+ this currency commit) (decision log D-142..146; + the parallel guard-hardening pass — dead-code/identifier + opportunistic-closure + guards-compound codifications, the tech-debt automation, TECH_DEBT-152/153/154/155, the guard-coverage audit synthesis)
deletion_scope: none
pickup: /accept-handoff <this doc>
---

# Ship-A storage flip handoff — the 16B wiring (Session 9 close, 2026-06-02)

**The hard part is DONE.** Sessions 8–9 built + PROVED the full 16B op library; this handoff is for the **atomic storage flip** — point `FPN<64>` at the 16B type and reconcile everything the build then enumerates, in one red→green pass. Best done with fresh, focused context (it's capital-core and red-build until complete).

## 1. State (verify at pickup — `/accept-handoff` does this)
- **Engine HEAD `d2ee570`** (`feat/v5.15-live-readiness`). The Ship-A op-library is 8 commits on anchor `575a31c` (ending `4efa8d3`):
  `6f50864` (16B type+traits+simple ops) · `b11949f` (native div+sqrt) · `2deb6d9` (release v0.3) · `fa760d3` (README) · `3f96a40` (conversions+double-rt transcendentals) · `e342828` (Exp/Sin/Cos+FromInt) · `c53e182` (branchless transcendentals + i128 primitives) · `4efa8d3` (post-op-library hygiene — removed dead `fp2_to_mag_fpn`, refreshed slice-count comments). **Pushed.** **+4 commits past `4efa8d3` = the PARALLEL guard-hardening pass** (NOT Ship-A code): `8438bbd`/`8182c43` identifier-retirement H21 (Check H) · `dad6f19` bounds static_asserts + OrderEventLog `<cerrno>` · `d2ee570` maker-fee desync guard. The flip interacts with these (step 5); the full pass + the 6 remaining guards are in **§5.5**.
- **Workspace HEAD `3ac6dd0`** (decision log D-142..146 + plan sync + the Session-9 readiness report).
- Working tree: pre-existing untracked `.E.2` doc drafts + `build_probe/` (leave them — unrelated).
- Baseline: `controller_test` **3241/0** throughout (the op-port is ADDITIVE — `FPN<64>` still 24B until the flip).

## 2. What's DONE — the 16B op library (additive, proven, committed)
`FixedPoint/FixedPointN.hpp` now has, alongside the untouched 24B `FPN<F>`:
- **`FixedPoint<2,64>`** — bare 16B `__int128` two's-complement (value = v/2^64), `static_assert(sizeof==16)`.
- **Disjoint traits** `is_fp_binary_v` / `is_fp_decimal_v` (B6; `is_FPN_v` → binary alias at the flip).
- **Full native op surface** (the `fp2_*` functions): Mul Abs Negate AddSat Sub Min Max Div Sqrt FromInt From/ToDouble Log InvSqrt Tan Pow Atan2 Exp Sin Cos — **value-equivalent to 24B `FPN<64>`, slice net 423/0** (`tools/ship_a_fp2_64_slice.cpp`, which tests the PRODUCTION header fns).
- **Branchless** (operator: stable latencies): hot arithmetic 0 jumps; saturation via `of_mask` / mask-derived `2^127-1` (`of_m>>1`); transcendentals via **`i128_abs` / `i128_cneg`** ((v^sgn)-sgn) — asm-verified, only fixed-trip loops + 2 cold `__builtin_expect`-rare seed_bit guards remain.
- **`udiv_q64`** — the certified `FPN_DivNoAssert` 128-iter long-division lifted to a magnitude-level `__int128` helper (no FPN<64> dependency). The extract-the-certified-core pattern (D-142).

**Key Session-9 decisions (decision log D-142..D-146, SSoT — read them):**
- D-142: op-port = native via EXTRACTED certified cores (not a parallel wide-delegate type — option B rejected as effort-lean).
- D-143: wiring = ALIAS not rename (rename = later A.5 ship); shed vestigial arbitrary-width (F=128 trait-test-only); FRAC param kept.
- D-144: **R3 snapshot versions → 13/9/6 (current+1)** — HEAD is already at 12/8/5, so the plan's literal "12/8/5" is a NO-OP bump (would silently load 24B snapshots into the 16B engine). Re-derive from HEAD + bump PAST current + add a layout-coupled-version test.
- D-145: branchless 16B ops + i128 primitives.
- D-146: release v0.3 (display-only; engine version stays wire-bound).

## 3. THE NEXT WORK — the atomic storage flip (task #1)
**Red-build until ALL of this lands together** (the compiler enumerates the breaks; the proven `fp2_*` are the bodies). Suggested order:

1. **Make `FPN<64>` the 16B type** — the cleanest mechanism (per D-143 alias-not-rename): redefine so `FPN<64>` resolves to `FixedPoint<2,64>` (16B storage), with `FPN_*<64>` op specializations = the `fp2_*` bodies (replace the current `USE_NATIVE_128` FP64-forwarding block). Keep `FixedPoint<RADIX,FRAC>` as the impl; `FPN_Binary`/`FPN_Decimal` the public aliases.
2. **Port the ~8-11 `.w[]` internal-access sites** (they assume sign-magnitude layout): **3 in `OrderGates.hpp`** (the hot price/volume magnitude compares `price.w[NW-1]/.w[0]` → native `a.v >= b.v`; latency-check the codegen stays branch-free per D-133) + the `controller_test.cpp` byte/value-equality checks. (Earlier grep over-counted — the `rw.w[i]` cluster in controller_test is array-of-FPN, NOT FPN internals.)
3. **Port the easy ops the storage flip surfaces** (the build will name them): comparisons (native `a.v</==/>= b.v`), Floor/Ceil/Round (frac-mask the low 64 bits), Sign/IsZero, BlendOnMask, Mod, Lerp/SmoothStep, FromFP64/ToFP64 — mostly trivial for two's-complement. Re-point any remaining FP64-forwarding specializations.
4. **Re-derive the R1 layout asserts to 16B** — **regenerate the authoritative set from `tools/gen_code_map.sh --byte-context FPN`** (do NOT trust a hand-list — R1 was ~3× under-counted once; paste the tool output, per `feedback_paste_tool_output_dont_summarize`). The set includes: `controller_test.cpp:24429` `sizeof(FPN<64>)==24`→`==16` (+ the rationale string), Position offset ladder (`Portfolio.hpp:115-141`, 192→112B), `Order.hpp:148/150`, `OrderEventLog.hpp` disk entry_size, `ExecutionCore.hpp:176/178`, `GateControlNetwork.hpp:31`, `FlowFeatures` clusters, `CfgFieldDispatch.hpp:471/475` (has_unique_object_representations holds at 16B), `Fingerprint.hpp` SHA-over-cfg, `tools/fp_determinism_golden.cpp:26,29`, the `ShardedSnapshotPersist`/`PortfolioController`/`Portfolio` fwrite/fread `sizeof(FPN<F>)` sites.
5. **Bump R3 snapshot versions to 13/9/6** (D-144): `CONTROLLER_SNAPSHOT_VERSION` 12→**13** (`PortfolioController.hpp:2065`), `SHARDED_SNAPSHOT_VERSION` 8→**9** (`ShardedSnapshotPersist.hpp:94`), `PORTFOLIO_SNAPSHOT_VERSION` 5→**6** (`Portfolio.hpp:530`) — re-read HEAD first; bump PAST current. Add a test asserting each strictly increased. **NEW (post-handoff codification):** these 3 versions are now enrolled in the H21 identifier-retirement ledger (`tools/identifier_ledger.txt`). A monotonic bump is FINE — `check_identifier_retirement.py` (pre-commit Check H) PASSES a bump (it only FAILS a decrease/reuse/drop) — but run `python3 tools/check_identifier_retirement.py --update` right after bumping to re-freeze the ledger at 13/9/6 (else later commits carry a stale "BUMP" advisory). The flip's dead-code removals (the `USE_NATIVE_128` FP64-forwarding block; `fp2_from_fpn` once the slice retires) are Class 40 / Rule 1 — remove, don't leave compiled-in.
6. **Rewrite the F=128 trait-test** in `tests/test_common.hpp` (shed arbitrary-width, D-143) — it uses `FPN<128>::F`; change to exercise `is_fp_binary_v`/`is_fp_decimal_v` over `FixedPoint<2,64>`/`<10,8>` instead.
7. **Re-freeze the determinism golden** — `tools/fp_determinism_golden.cpp` emits the 16B byte-array (24B→16B regenerates it; this IS the D-139 fresh re-cert). Run `tools/check_determinism.sh` / the selftest. Models RE-STAMP (value-preserving; D-125/D-131 no-live-models).
8. **Acceptance + tag Ship A**: slice 423/0 still green; `controller_test` green; `build.sh ubsan` clean (±INT_MIN abs/negate/mul probe — B1); max-magnitude saturate-not-wrap probe at 2^63 (R2); latency-impact estimate (D-133); `build.sh test`+`gui`+`asan`+`ubsan` all green (Check 31). Version.hpp bump + CHANGELOG + GPG tag (monotonic-at-ship, D-88) + postmortem + `/sync-workspace`.

**Then:** Ship A.5 (rename `FPN`→`FPN_Binary`, clang-rename, pure-cosmetic against the 16B anchor) → Ship B (decimal `FixedPoint<10,8>` money — the B1-B6 findings + the divmul `÷10^8` N=127 M=0x55e63b88c230e77e7ee106959b5d3e1f S=153 per D-140).

## 4. Critical pickup reads
- **Decision log D-142..D-146** (`decision-logs/v5.15.5.F.4d.1.E-architecture-v2.md`) — the Session-9 SSoT.
- **Plan body** `subplans/2026-05-30-v5.15.5.F.4d.1.E-money-numeric-core-foundation.md` — Session-9 banner + the R1 relocation set (§ Gate findings) + R3 (corrected to 13/9/6) + acceptance criteria.
- `FixedPoint/FixedPointN.hpp` — the `FixedPoint<2,64>` type + `fp2_*` (the flip's op bodies) + `i128_abs`/`i128_cneg` + the current `USE_NATIVE_128` FP64 block (the thing the flip replaces).
- `tools/ship_a_fp2_64_slice.cpp` — the value-equivalence net (423/0); keep it green through the flip.
- Before coding: `DOCS/STRATEGY_AND_CODING_RULES.md` (H1-H20) + `plans/_cross-cutting/2026-05-06-latency-path-discipline.md` (the OrderGates hot-path port).

## 5. TaskList state at handoff write (recreate via TaskCreate)
| ID | Status | Subject |
|---|---|---|
| #1 | in_progress | **#11 Ship-A storage flip** — point FPN<64> at 16B + .w[] sites + R1→16 + R3→13/9/6 + trait-test + golden re-freeze → tag |
| #2 | pending (blocked by #1) | Ship-B: decimal FixedPoint<10,8> money migration (B1-B6 findings; divmul) |
| #3 | in_progress | Tools-discipline tail + gen_code_map skill-wiring |
| #4 | pending | Codify .E.0.6 determinism-net tail (AR-4 + locale-sister) |
| #5 | pending (blocked by #1,#2) | SWAR parse (POST-#11) |
| #6 | pending | **Guard-hardening** — H1/H3 no-heap/no-locks forbidden-token CI guard (TECH_DEBT-155 / §5.5) |
| #7 | completed | Guard: bounds static_asserts — LANDED `dad6f19` |
| #8 | completed | Guard: maker/taker fee-desync (`OMS_GuardTakerBoundFeeBasis`) — LANDED `d2ee570`; real fix TECH_DEBT-154 |
| #9 | pending | **Guard-hardening** — wire meta-registry enforcement (H15/H19) + fix CLAUDE.md doc-drift |
| #10 | pending | **Guard-hardening** — H16 MetadataFlag→derived-filter coverage check |
| #11 | pending | **Guard-hardening** — OMS submit qty/notional cap (closest LIVE Knight-Capital sibling; needs cap-value decision) |
| #12 | pending | **Guard-hardening** — H7/H8 hot-path asm branch-count gate |
| #13 | pending | **Guard-hardening** — legacy BuyGate phantom + snapshot body CRC32 |

## 5.5 Parallel in-flight: capital-safety guard-hardening pass

A SEPARATE workstream from the flip (same branch), run this session because the operator's *"guards compound over a lifetime"* instinct surfaced enforcement-layer gaps worth closing now. **Full findings + per-guard file:lines + approaches:** `plans/v5.15-live-readiness/plan_checks/2026-06-02-guard-coverage-audit-synthesis.md`. Tracked: **TECH_DEBT-155** (+ -152/-153/-154 siblings).

- **Headline:** the production sharded capital path is WELL-DEFENDED (Knight-Capital risks already guarded). The gaps are enforcement-layer — convention-only invariants with no mechanical guard (the H21 shape).
- **LANDED (2/8):** #7 bounds static_asserts (`dad6f19`); #8 maker-fee desync guard `OMS_GuardTakerBoundFeeBasis` (`d2ee570`) + OrderEventLog `<cerrno>`. Codified this pass: memories `feedback_guards_compound_enforcement_is_leverage` / `feedback_opportunistic_tech_debt_closure` / `feedback_design_once_maintain_forever`; the **tech-debt automation** `tools/check_tech_debt.py` (pre-commit **Check J** — surfaces overlapping OPEN debt on every commit, classify subsume/adjacent/defer); the dead-code/identifier-retirement discipline (**H21** + Class 40 + DESIGN_SPEC).
- **PENDING (6):** #6 H1/H3 forbidden-token · #9 meta-registry enforcement + CLAUDE.md doc-fix (the doc names 3 CI checks that don't exist) · #10 H16 coverage · **#11 OMS qty/notional cap** (closest LIVE Knight-Capital sibling) · #12 H7/H8 asm branch-count gate · #13 legacy phantom + snapshot CRC32. Each spec'd in the synthesis.
- **Pickup:** continue from the synthesis + TECH_DEBT-155 — the file:lines + approaches are captured, so NO loaded context needed. #11 needs a cap-value decision (cfg-driven vs hard ceiling); the rest are ready.
- **Privacy:** the meta-tools relocation to the private workspace is DECIDED (meta-only boundary) + tracked TECH_DEBT-153 (its own dedicated pass; the build/test/CI-load-bearing tools stay public).

## 6. Operator norms
Address Caramel as Caramel/she/her; no AskUserQuestion modals (inline); evaluate on robustness+latency+design not time; **consult before coding** (the flip is capital-core); branchless preferred (stable latencies — her explicit value); MED/LOW findings get a disposition; paste tool output don't summarize; **make-it-good-as-it-exists** for this foundational determinism-gated code (not make-it-exist-then-good). No live models (epoch/stamp/wire breaks free provided post-change determinism re-cert, D-131).

## 7. First action
`/accept-handoff <this doc>` → verify git state + recreate TaskList → `tools/gen_code_map.sh --byte-context FPN` for the authoritative R1 set → start the atomic flip at step 1 (redefine FPN<64> as the 16B type). It's red-build until step 8; keep the slice (423/0) + `controller_test` as the gates. Consult Caramel before the tag.

**End of Ship-A storage-flip handoff. The 16B op library is proven (423/0); the flip is the atomic wiring — fully specified, capital-core, best with fresh focus.**
