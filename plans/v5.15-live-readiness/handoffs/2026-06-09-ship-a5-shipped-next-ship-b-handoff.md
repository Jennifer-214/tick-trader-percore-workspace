---
type: handoff
status: active
ship_tag: "Ship A.5 FPN->FPN_Binary rename — SHIPPED + GPG-tagged v5.15.5.F.4d.1.E.0.8 (2026-06-09, same-day plan->gate->code->tag); close-out NET-ZERO ledger. NEXT = plan Ship B (decimal money — the FIRST capital-bearing ship)"
plan_type: refactor (cosmetic type+trait rename; zero-semantic, zero-codegen — PROVEN via A/B oracle)
sprint: v5.15-live-readiness
phase: ".E.0 FOUNDATIONAL — Ship B is where money STARTS (heavier-default audit posture, D-77)"
sprint_end_goal: make the codebase more maintainable for future development; correctness-true foundation before the .E.1 rename + multi-exchange
decision_log: plans/v5.15-live-readiness/decision-logs/v5.15.5.F.4d.1.E-architecture-v2.md (D-97..D-167; Session-12 addendum = D-163..D-167, this session)
engine_head: 0e48150 (feat/v5.15-live-readiness; SIGNED tag v5.15.5.F.4d.1.E.0.8 at c74690b + post-tag close-out 0e48150; both PUSHED)
workspace_head: at or after a18ed9d (this close-out's ledger/handoff/decision-log commit follows; /accept-handoff accepts the self-referential delta)
predecessor_handoff: handoffs/2026-06-08-ship-a-acceptance-complete-at-tag-handoff.md (superseded; A.5 was picked up, planned, gated, shipped + closed from it in ONE session)
pickup: /accept-handoff <this doc>
required_reading: [this doc, the decision-log Session-12 addendum (D-163..D-167), subplans/2026-05-30-v5.15.5.F.4d.1.E-money-numeric-core-foundation.md (the standing Ship-B body — RE-AUDIT at pickup per D-144), DESIGN_SPECS/refactor-patterns/rename-ship-methodology.md (Stage 3)]
---

# Ship A.5 SHIPPED + closed NET-ZERO — next pickup = PLAN SHIP B (decimal money)

**A.5 went plan → MED gate → consult → code → acceptance → GPG tag → debt-close-out in ONE session (2026-06-09).** Tag `v5.15.5.F.4d.1.E.0.8` ("Good signature from Caramel") at `c74690b`; post-tag close-out commit `0e48150`; workspace `a18ed9d`+. The ledger ends the day NET-ZERO (160 + 161 opened at acceptance, both CLOSED same-day per the operator's close-out-now call).

## Where this sits (carry session-to-session)

```
.E.0.1  determinism net ............................ ✅ E.0.6
#11 Ship-A   16B binary compaction ................. ✅ E.0.7 (STOP-before-money boundary)
#11 Ship-A.5 FPN -> FPN_Binary rename .............. ✅ E.0.8  ◀── done (this session)
#11 Ship-B   decimal money (FixedPoint<10,8>) ...... NEXT — the FIRST capital-bearing ship
.E.1   Core->Node rename + per-node drainer + multi-exchange registry
.E.2+  headless -> WS-API -> sub-accounts -> Alpaca -> strategy hot-reload
```

**Ship B is where money starts.** Heavier-default audit posture applies (D-77); the D-100 oracle is the standing acceptance gate; golden regen + un-bypass pre-commit Check F land AT Ship B's close (D-157). Do NOT treat the green E.0.x run as "near live."

## State at pickup (verify — `/accept-handoff` does this)

- Engine `0e48150` on `feat/v5.15-live-readiness`; tag `v5.15.5.F.4d.1.E.0.8` SIGNED + PUSHED (tag at `c74690b`; `0e48150` = the post-tag TECH_DEBT close-out: 4 files, suite-verified). Tree clean (`build_*` untracked dirs gitignored now — the A.5 commit closed that hole).
- Gate at close: controller_test **3246/0** · gui ok · asan **3246/0** (via the NEW pinned runner) · ubsan **3246/0** · codegen A/B oracle pre==post IDENTICAL · `calls_graph_diff` CLEAN · doc CI ALL HARD GREEN.
- `Version.hpp` = `5.15.5.F.4d.1.E.0.8` (TAGGED). Check F still bypassed-with-rationale (D-157, unchanged).
- CLAUDE.local.md sprint rows current; always-loaded budgets TIGHT (CLAUDE.md 39.1k / CLAUDE.local 39.6k of 40k caps; MEMORY 23.3k of 24.4k) — **a compression pass is due soon**; treat any always-loaded addition as needing equal-size removal.

## What landed this session (the short list)

1. **The rename:** 77 engine/test files; `is_FPN_v` retired (39 sites; alias deleted); `FPN_*` fn family + FixedPoint64 absorb = EXPLICIT Ship-B non-goals (D-163/D-165). H21 verified zero wire-visible changes; NO operator migration.
2. **`rename-ship-methodology.md` Stage 3** — the `.E.1` Core→Node rename inherits it (totality-oracle discriminator: compiler-guarded vs TOOL-REGEX vs PROSE-AMBIGUOUS — `.E.1`'s tokens are the third kind and NEED the AST tooling TECH_DEBT-142 asks for; 142 annotated, closes at `.E.1`).
3. **Two real incidents, both structurally closed:** the `.D.1` doc classifier was UNANCHORED → double-renames + fn-name corruption across 28 doc files → boundary-anchored fix + idempotency PROVEN (2nd apply = 0) + repairs landed. And the `rg -rln` flag phantom (display-replacement faked a live rewriter) → "verify the VERIFIER's invocation."
4. **Guards hardened:** doc-size guard exit-1 on canon-missing + SCAN_GLOBS widened (caught `latency-path-discipline.md` still teaching 24B — fixed, with the dead `w[]` BlendOnMask sample swapped for the live `__int128` body); NEW `tools/run_sanitizer_suite.sh` (pinned `ulimit`/`detect_leaks`; `[FAIL]`-preserving).
5. **Close-out (D-167):** TECH_DEBT-160 CLOSED (2 sites FIXED provable — SetCoreStrategy bound, recorders `rend-1` sister-cohort; 1 verified-FP documented — SPSCRing masked write, both remedies proven ineffective, comment at site, any OTHER stringop = signal) + TECH_DEBT-161 CLOSED (runner + leak audit: 765/765 = init fixtures, zero runtime-path leaks; ubsan 3245/1 proven flake by quiet rerun).
6. **Codified:** `feedback_structure_judgment_loop_not_output` (D-166, operator-directed) + `feedback_close_out_now_over_defer_when_small` (the D-159 promise, paid at pickup) + GLOSSARY § Numeric core types + § 15 spelling bridge + the evidence-destroying-instrumentation meta-lesson (D-167; harvest row pending at `/close-session`).

## What's NEXT — plan Ship B (decimal money)

1. **The standing Ship-B body** = `subplans/2026-05-30-v5.15.5.F.4d.1.E-money-numeric-core-foundation.md` (v0.2, step-6 folded; acceptance §302-330 — the Ship-A-scoped rows are DONE, the rest is Ship B). **RE-AUDIT at pickup** (D-144: targets rot between plan-write and code-time; it pre-dates A.5's rename + Ship A's shipped reality). Pre-coding: HIGH-RISK tier gate + `/blindspot-scan` + the D-93 new-fn design audits; D-100 oracle (`plan_checks/2026-06-01-11-phase1-divmul-proof/`) is the standing acceptance gate.
2. **At Ship B's close:** golden refreeze + un-bypass Check F (D-157) + TECH_DEBT-159 re-pack `/dod-audit` (D-161) + the H4 SEMANTIC rewrite in CLAUDE.md (decimal-money/binary-features) + FPN_* op-family naming decision + FixedPoint64 absorb (D-99).
3. **Standing notes (NOT blockers):** MASTER.md last refreshed May 27 (pre-E.0.5) — the live state = CLAUDE.local table + CHANGELOG + postmortems; backfill = optional `.F`-sweep item. TECH_DEBT-157(b) alignof-locks stay advisory (tracked-by-tooling). The 8 SPSCRing stringop lines in gui builds are KNOWN-classified (comment at `SPSCRing.hpp` TryPush) — do not re-investigate; any OTHER stringop site is signal.

## Operator norms (carry forward)

Address Caramel as Caramel/she/her; no AskUserQuestion modals (inline); evaluate on robustness+latency+design not time; correctness + planning over speed; consult after gates before coding; branchless preferred; MED/LOW findings get dispositions; close-out-now over defer for small in-flight finds (D-159 — she invoked it HERSELF this session on the fresh debt rows); capture decisions/findings/state AS THEY HAPPEN, unconditionally; **money-bearing surfaces (everything from Ship B on) get the HEAVIER pass by default (D-77)**.

## First action

`/accept-handoff <this doc>` → verify gate green + tag live → then **re-audit the money-foundation body against post-A.5 HEAD and open the Ship-B planning cycle** (per-ship `/precoding-audit-gate` HIGH-RISK + `/blindspot-scan`; consult before coding). Money starts here — slow is correct.
