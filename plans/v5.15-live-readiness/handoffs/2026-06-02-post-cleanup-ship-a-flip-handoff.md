---
type: handoff
ship_tag: "#11 Ship-A storage flip — RESUME after the code-only-public spring-cleaning session"
plan_type: refactor (16B binary-core compaction)
sprint: v5.15-live-readiness
sprint_end_goal: make the codebase more maintainable for future development
ship_end_goal: "Ship A — compact FPN<64> 24B sign-mag → FixedPoint<2,64> 16B two's-complement, VALUE-equivalently; tag = the STOP-before-money boundary (D-130). Op-library BUILT + PROVEN; the storage flip WIRES it."
coding_status: op-library-complete + storage-flip-PENDING (unchanged) — but the repo was RESTRUCTURED this session (code-only-public); read the DELTA below
predecessor_handoff: handoffs/2026-06-02-ship-a-storage-flip-handoff.md   # ← the FULL flip detail is here; still valid
decision_log: plans/v5.15-live-readiness/decision-logs/v5.15.5.F.4d.1.E-architecture-v2.md (D-97..D-146; SSoT)
engine_head: 052670d (feat/v5.15-live-readiness; LOCAL — NOT pushed; the flip op-library ends at 4efa8d3)
required_reading: [this doc, predecessor_handoff, plan-body, CLAUDE.md §0 prime-directive]
pickup: /accept-handoff <this doc>
---

# Ship-A flip — RESUME after spring cleaning (2026-06-02)

**The flip is UNCHANGED + still the next work. What changed is the repo AROUND it.** This handoff
is a thin DELTA on top of `handoffs/2026-06-02-ship-a-storage-flip-handoff.md` (which has the full
8-step flip, D-142..146, the slice 423/0, the R1/R3 sets). Read that for the flip; read THIS for
what's different now.

## 1. State at pickup (verify — `/accept-handoff` does this)
- **Engine HEAD `052670d`** (`feat/v5.15-live-readiness`, **LOCAL — not pushed**). On top of the flip
  op-library (`4efa8d3`) sit: the guard-hardening pass (`8438bbd`..`6c0e570`) + **this session's two
  spring-cleaning commits**: `9a22fb0` (tools/+tests/ → private) + `052670d` (code-only-public surface).
- **Version.hpp** still `5.15.5.F.4d.1.E.0.6` (the flip hasn't tagged; STOP-before-money, D-130).
- `controller_test` **3241/0** (verified post-cleanup); slice net `tools/ship_a_fp2_64_slice.cpp` **423/0**.
- Working tree: only unrelated `.E.2` doc drafts + `build_probe/` untracked (leave them).

## 2. THE DELTA — what the spring cleaning changed (read before you touch the repo)
This session was a **code-only-public restructure** + a doc/process pass. None of it changed the flip,
but it changed the repo's shape:

1. **`tools/` + `tests/` are now PRIVATE** — moved to the workspace (`tick-trader-percore-workspace/{tools,tests}`),
   symlinked back into the engine, gitignored. **They're present locally** (the build + hooks work
   unchanged); they're just untracked. The public engine repo is now **code-only**: source + build +
   LICENSE/README/assets. See `DESIGN_SPECS/meta-disciplines/public-private-boundary-and-ecosystem-discipline.md`.
2. **Engine-reading tools were made portable** — `.absolute()` not `.resolve()` (the symlink trap;
   **LANDMINES Landmine 5**). The flip will run `tools/gen_code_map.sh --byte-context FPN` (for the R1 set)
   + `tools/ship_a_fp2_64_slice.cpp` + `tools/fp_determinism_golden.cpp` — **all still work** (verified:
   gen_code_map found 92 FPN sites; the slice net is intact). They resolve the engine via the symlink.
3. **`build.sh` + `CMakeLists.txt` are GUARDED** — the now-private `tools/`+`tests/` references are wrapped
   `[ -f ... ]` / `if(EXISTS ...)`. Locally everything builds (3241/0); a public clone skips the dev/test
   targets. **The flip's build commands are unaffected.**
4. **NEW always-loaded doc-budget guard** — `tools/check_always_loaded_budget.py` (wired HARD into
   `check_session_docs.sh`). CLAUDE.md / CLAUDE.local.md / MEMORY.md are all NEAR their byte caps (97/97/90%) —
   if you add to any always-loaded doc during the flip, it may flag; trim if so.
5. **NEW correctness-first prime directive** (always-loaded) — CLAUDE.md top + DESIGN_PHILOSOPHY §0. The flip
   is capital-core: plan-before-code, consult before the tag, don't rush. (You already live this.)

**Engine is NOT pushed.** The spring-cleaning commits are local on `feat/v5.15-live-readiness`. Pushing
publishes the clean code-only surface — operator's call (outward-facing). Don't push without her go.

## 3. THE FLIP — the actual next work (full detail in the predecessor handoff)
**Unchanged.** Resume at the predecessor handoff's §3 step 1: redefine `FPN<64>` → `FixedPoint<2,64>` (16B,
alias-not-rename D-143), then the ~8-11 `.w[]` sites (incl. 3 hot OrderGates) + R1 layout-asserts → 16B
(regenerate via `tools/gen_code_map.sh --byte-context FPN`, paste verbatim) + R3 snapshot versions
**12/8/5 → 13/9/6** (D-144; HEAD confirmed still at 12/8/5) + golden re-freeze → acceptance → **tag Ship A
(STOP-before-money, consult Caramel)**. Gates: slice 423/0 + controller_test green throughout (red-build
until step 8). Then A.5 rename → Ship B (decimal money).

## 4. Critical pickup reads
- **Predecessor handoff** `handoffs/2026-06-02-ship-a-storage-flip-handoff.md` (the full flip).
- **Decision log D-97..D-146** + **plan body** `subplans/2026-05-30-v5.15.5.F.4d.1.E-money-numeric-core-foundation.md`.
- `FixedPoint/FixedPointN.hpp` (the `FixedPoint<2,64>` type + `fp2_*` + the `USE_NATIVE_128` block the flip replaces).
- Before coding the OrderGates hot-path port: `DOCS/STRATEGY_AND_CODING_RULES.md` (H1-H21) + `plans/_cross-cutting/2026-05-06-latency-path-discipline.md`.
- NEW this session: `DESIGN_SPECS/meta-disciplines/public-private-boundary-and-ecosystem-discipline.md` + LANDMINES 5/6 (only matters if you touch the tooling/build).

## 5. TaskList state at handoff write (recreate via TaskCreate)
| ID | Status | Subject |
|---|---|---|
| #1 | in_progress | **#11 Ship-A storage flip** — point FPN<64> at 16B + .w[] + R1→16 + R3→13/9/6 + golden → tag (THE work) |
| #2 | pending (blocked by #1) | Ship-B: decimal FixedPoint<10,8> money migration |
| #3 | in_progress | Tools-discipline tail + gen_code_map skill-wiring |
| #4 | pending | Codify .E.0.6 determinism-net tail (AR-4 + locale-sister) |
| #5 | pending (blocked by #1,#2) | SWAR parse (POST-#11) |
| #6,#9-#13 | pending | Guard-hardening pass (H1/H3 forbidden-token · meta-registry · H16 · OMS cap · H7/H8 asm · legacy phantom) |
| #7,#8 | completed | bounds static_asserts (dad6f19) · fee-desync guard (d2ee570) |
| #14 | pending | Doc-budget M7 codification tail (file-size-split ext + going-forward rule + meta-anti-pattern row) |
| #15 | completed | **Code-only-public spring cleaning** (this session — tools+tests+everything private; build 3241/0; codified) |
| #16 | pending | **Session wrap-up follow-ups** — sync (DONE: workspace 7b018fd + template d04e350 pushed) · doc-budget codify-tail · going-forward rule for the public/private law · template host-gitignore · CODE_OF_CONDUCT/BOUNTY privatization confirm · **push the engine branch** |

## 6. Operator norms
Address Caramel as Caramel/she/her; no AskUserQuestion modals (inline); evaluate on robustness+latency+design
not time; **correctness + planning over speed (the new prime directive — CLAUDE.md §0)**; consult before
coding + before the tag (capital-core); branchless preferred (stable latencies); MED/LOW findings get a
disposition; paste tool output don't summarize; when execution flails, STOP. No live models (D-131).

## 7. First action
`/accept-handoff <this doc>` → verify state + recreate TaskList → read §2 DELTA (the repo changed shape) →
then resume the flip at the predecessor handoff's step 1 (`tools/gen_code_map.sh --byte-context FPN` for the
authoritative R1 set, then redefine FPN<64> as the 16B type). Red-build until step 8; consult Caramel before
the tag. The flip is fully specified + de-risked; the only NEW thing is the repo is now code-only-public.

**End. The flip is unchanged + ready; this handoff just carries the spring-cleaning delta + the current (local, unpushed) git state.**
