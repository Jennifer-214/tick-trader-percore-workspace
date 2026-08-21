# AR-8 Adversarial Review — E.1.2.C tail handoff (default-REFUTED)

> Saved verbatim at receipt per `feedback_save_agent_reports_verbatim` (orchestrator writes; agent was read-only).
> Reviewer: a-class subagent, default-REFUTED, Stage 6.5.4 of /close-session. Every finding was triaged + fixed at close (disposition footer).

**Target:** `/home/caramel/code/FoxML_Trader_v2/plans/v5.15-live-readiness/handoffs/2026-08-20-E.1.2.C-tail-3G-shipped-leg4-ready-handoff.md`
**Method:** every load-bearing claim re-derived against HEAD (engine `f4bbafe`, ws `ee00034`) by running the named tools, re-running the suite binary, resolving every cite, and diffing the handoff against the plan body, MASTER UPDATE 35, D-428/D-429, PARITY_ISSUES.md, and TD-288. Roots covered: engine source dirs + `tests/` + `tools/` + `plans/` + workspace `DOCS/` (named explicitly per Landmine 19).

## VERDICT: REFUTED-WITH-FINDINGS

The shipped-work claims are solid — every anchor I attacked survived (see "Survives" below). But the handoff's **first re-derive command fails at HEAD on a HARD gate that the handoff pair itself broke after the last clean sweep**, and the Capture-completeness ledger omits a close-out failure the maker's own tool had already reported before this review ran. A fresh session following the doc literally REDs at step one.

## Findings

**F1 — HIGH — "expect SWEEP CLEAN" is FALSE at HEAD; the handoff pair broke it and never re-checked.**
Handoff:30 (`./tools/check_session_docs.sh # expect SWEEP CLEAN`) and Check 12's "(sweep CLEAN)" (handoff:88). Measured: `SWEEP FAILED` — HARD `reciprocal-supersession ((g)-4/D-416)`: *"UNRECIPROCATED supersession: 2026-08-20-E.1.2.C-tail-3G-shipped-leg4-ready-handoff.md supersedes 2026-08-20-E.1.2.C-legs-0-2-3-shipped-handoff.md, but its superseded_by = '(absent)'"*. The predecessor (`handoffs/2026-08-20-E.1.2.C-legs-0-2-3-shipped-handoff.md:3`) carries `status: superseded  # by …` — the back-pointer lives only in a comment; the machine-readable `superseded_by:` key was never written. Timeline proves the mechanism the directive predicted: last clean sweep 20:05:27 (`sweep8.log`, "SWEEP CLEAN") → handoff written 20:12:00 → predecessor flipped 20:12:11 → only the narrow singleton check re-run 20:12:33 (`hs.log`) → full sweep never re-run. Check 5's "flipped `superseded` at this close" (handoff:83) describes a half-flip that violates the project's own gate. **Fix (one line + one run):** add `superseded_by:` to the predecessor frontmatter, re-run the full sweep as the LAST pre-commit act.

**F2 — MED — Capture-completeness omits a known-red close-out advisory.**
The close-out tool ran at 20:14:31 (`co3.log` — AFTER the handoff was written) and FAILED: 4 auto-write surfaces with zero commits (`tools/CLAUDE.md` gotcha harvest · `DESIGN_SPECS/` pattern-application · `DOCS/recurring-bug-patterns/` known-instance row · `DOCS/CODE_MAP.md` mirror sync) + 2 MED handoff-quality findings (memory frontmatter non-canonical; memory.backup drift ×3 — drift predates the session, so handoff:99's "zero memory writes this session" itself is TRUE, mtimes all ≤ Aug 19). The ws working tree holds UNCOMMITTED mid-fix edits to exactly `DESIGN_SPECS/meta-disciplines/dead-code-and-identifier-retirement-discipline.md` + `DOCS/recurring-bug-patterns/class-51-vacuously-green-guard.md` — 2 of the 4 surfaces, unmentioned anywhere in the handoff. The Capture-completeness section presents only green checks; a fresh session would believe close bookkeeping is whole.

**F3 — MED — live stale comment contradicts the deletion the handoff headlines.**
`/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/EngineSharded/Run.hpp:1876-1877`: "(now legacy in EnsembleHotSwap.hpp; kept compiled but not called from this production path)" — the file was DELETED at `753fbed`; "kept compiled" is false. Double irony: D-429 (4) justified the burial partly on the includes' "FALSE comments", and the burial commit touched this file (:451-455 tombstone) yet left a third false comment 1400 lines below — while plan:104 records "#12 per-leg same-commit sweeps landed". The register-#12 totality check at `/post-ship-audit` is the designated catcher, but the comment misleads NOW (SUBAGENT_ARMING §2.5 class).

**F4 — MED — the plan the Arming says to read first still declares "consult before any code".**
`subplans/2026-08-20-v5.15.5.F.4d.1.E.1.2.C-ml-verification-program.md:5`: `status: draft — pre-coding gate IN FLIGHT (… a-class refute pass next; consult before any code)` — contradicted by its own AMENDED section (:114, "gate CLOSED") and by the handoff's "everything shipped". Check 2 is narrowly true (the named fields exist) but the dce4b9f doc-drift pass fixed drift everywhere except the plan's own status line. Sister nit: frontmatter `owning_findings` still says the fan-shift defect's "ledger id pending" while register line :102 decided "no ledger entry ever minted, this line is the record".

**F5 — LOW — D-429 under-lists the surfaced-disposition set.**
D-429 (8) says surfaced-as-designed = "#17b" only; the SSoT register block (plan:103) + `dce4b9f`'s title say TWO ("#17b" + "#7's Shape-B never-HMAC operator-visible note"). Both artifacts are "Read first" in the Arming; they disagree by one member.

**F6 — LOW — "DOCS/ is per-FILE symlinks" (handoff:66) has exactly one exception, and it's the load-bearing one.**
Census: 61/62 top-level DOCS entries are symlinks; `DOCS/CODE_MAP.md` is a REGULAR engine-side file (regenerated 20:13, content CURRENT — has the session's new symbols, zero EnsembleHotSwap) whose workspace-TRACKED mirror at `ee00034` is STALE (0 `ModelBundleScan` hits; last synced pre-window at `1a4ec47`). A fresh session applying "use workspace absolute paths" to CODE_MAP reads stale ground truth. Engine-side reads (what SUBAGENT_ARMING names) are fine.

**F7 — LOW — reports paths lack the sprint prefix.** Handoff:53 cites `reports/2026-08-20-ml-verification-program/…`; resolves only from `plans/v5.15-live-readiness/`, not the engine root the fresh session starts in. Files exist at the full path.

**F8 — NIT — "EVERY agent-side queue item is DONE" (handoff:13)** is true of the predecessor queue but the session-minted #16/A-12 flag is open agent-side work; correctly re-listed at NEXT ACTIONS 3, but coding_status read alone over-claims.

## Survives (attacked and held — not trusted from prose)

- **Windows exact:** engine `29a9a3a..f4bbafe` = the 7 listed commits, pushed (no ahead/behind); ws `d16bce9..ee00034` = the 11 listed commits, origin/main at `ee00034`.
- **Suite 3850/0 MEASURED:** I re-ran `build/controller_test` → "RESULTS: 3850 passed, 0 failed"; `s6.log` (19:54:10) postdates the last test edit (19:50); the 3856→3850 delta is 6 assertions across 5 deleted cells (cells ≠ assertions; trajectory 3824→3837→3856→3850 corroborated across saved logs). The binary predates only the comment-only `f4bbafe` tag refresh.
- **EnsembleHotSwap.hpp gone;** all residual refs are comments (one stale = F3).
- **One matcher, both consumers:** `Model_ParseHorizonSibling` defined `ML_Headers/NodeModelZoo.hpp:2401`, called by the loader inside `EnsembleModelZoo_AutoDetectFromDir` (:2610, boot-reached via `EngineCommon.hpp:365`) AND the picker (`GUI/ModelBundleScan.hpp:161`).
- **Ledgers:** PARITY-044 `status: closed` (4-leg mechanism block), PARITY-043 closed at `7168953`, PARITY-042 `status: open` with explicit still-open surface updates; TD-288 open/med, names exactly 9 members.
- **Boot oracle real and observable:** `CoreFrameworks/EngineCommon.hpp:377-384` prints "ensemble active (primary=%s, %d horizons; %d total models, %d exit predictors)"; the picker→`node_N_model_dir=`→`cfg.node_model_dir`→boot-read plumbing exists (`ControllerConfig.hpp:3281`, `EngineCommon.hpp:364`).
- **Tools:** identifier guard GREEN 93 (ran it); `calls_graph_diff.sh` CLEAN (ran it); determinism GREEN (`dt5.log` 19:39); `check_cache_layout.py --tu/--fix` flags exist (tool:615/:622).
- **Anchors:** `Version.hpp:15` = "5.15.5.F.4d.1.E.1.1"; MASTER UPDATE 35 (`MASTER.md:70`) consistent on every point; D-428 STATUS amended in place; D-429's re-verification cites resolve (`EngineCommon.hpp:673`, `StrategyParameters.hpp:1448`, `NodeModelZoo.hpp:2209-2218`); Landmine 21 real (`LANDMINES.md:574`) and its engine-path claim measured true; Check 6's hook claim LIVE-confirmed (the `block_rg_r_typo.sh` hook fired on my own `rg -rn`); volatile-count discipline holds (suite count only in the fence; "9 members named" matches); predecessor PENDING fully discharged except deliberate carries; `Training_ResolveRole` really lives at `Backtest/LabelFunctions.hpp:560`.

## The cascade / structural read

The failure shape is **half-flip + narrow re-check**: a two-sided doc mutation (supersede pair) executed one-sided, then "verified" with the narrow green check (singleton) instead of the broad one that contains the reciprocal gate — a Class-51-adjacent shape (a green narrow check standing in for the failed broad one), and the exact model-bounded-writer failure AR-8 exists to catch. **Simpler/safer option ignored:** make the flip atomic — the handoff-writing step should write BOTH `status: superseded` and `superseded_by:` on the predecessor in the same edit (the (g)-4 gate exists because this two-sided edit keeps getting half-done; this session is another instance), and the close sequence should pin "full sweep is the LAST act before the close commit". Immediate mechanical fixes: the `superseded_by:` line, the Run.hpp:1876 comment, the plan status field, the reports path prefix, and surfacing the co3.log advisory verbatim in Capture-completeness.

No re-cascade signal: the handoff's shape (leg-4-next, D6/D7 forks, #16 flag, deferred version bump) is the CORRECT frame per D-428/D-429/MASTER — the refutation is of its self-verification claims, not its plan of record.

---

**Orchestrator disposition (recorded at close):** all 8 findings FIXED before the sync commit — F1 `superseded_by:` key + full sweep re-run as the last act (SWEEP CLEAN, ws `44e7114`); F2 the Capture-completeness section now carries the enforcer's owed-surfaces paragraph; F3 fixed engine `2092b95`; F4 plan status→executing + owning_findings un-staled; F5 D-429 (8) amended; F6 recorded in Landmine 21 + mirror re-synced; F7 paths prefixed; F8 coding_status corrected. The tools/CLAUDE.md gotcha harvest (the 4th F2 surface) landed at the operator's are-you-sure pass (ws `fe11d7e`) with the two-key-pair + sweep-last-act rule codified.
