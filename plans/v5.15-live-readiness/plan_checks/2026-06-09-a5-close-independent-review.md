# Independent deliverable review — Ship A.5 session close (2026-06-09)

**Reviewer:** independent agent (D-79 anti-self-attestation; `/close-session` Stage 5.5). Verified against DISK + GIT only; builder narrative treated as claims.
**Verdict: CLOSE-WITH-FIXES** — every deliverable landed and is push-verified; 4 small mechanical fixes + the expected pending close commit. Nothing broken, nothing fabricated, privacy boundary held (one PRE-EXISTING flag).

---

## Git ground truth

| Claim | Verified |
|---|---|
| Engine HEAD `0e48150` on `feat/v5.15-live-readiness`, pushed | ✅ `HEAD == origin/feat/v5.15-live-readiness == 0e48150` |
| Tag `v5.15.5.F.4d.1.E.0.8` SIGNED at `c74690b`, pushed | ✅ `git tag -v`: "Good signature from Caramel" (EDDSA 7197A1F2…); object `c74690b8…`; `ls-remote` shows the tag on origin |
| Rollback anchor `pre-v5.15.5.F.4d.1.E.0.8` = `f52d874`, signed | ✅ verified (Good signature, object f52d874…) |
| Workspace `a18ed9d` + `984ba08` pushed | ✅ `HEAD == origin/main == 984ba08`; `a18ed9d` is its parent |
| Engine tree clean | ✅ `git status --porcelain` EMPTY (the conversation-start snapshot showing `?? build_probe/ build_ubsan/` is stale — `.gitignore:158-159` covers both since `c74690b`) |

**Expected uncommitted close-ritual delta (workspace tree NOW — must ride the pending close commit):**
- `M DESIGN_SPECS/meta-disciplines/meta-anti-pattern-index.md` — **the AR-5 row + detail section live ONLY here** (grep of `984ba08:` version = 0 hits for AR-5)
- `M plans/v5.15-live-readiness/handoffs/2026-06-09-ship-a5-shipped-next-ship-b-handoff.md` — delta = the TaskList-at-close table (lines 56-63), nothing else (diff verified)
- `M memory.backup/MEMORY.md` + `M memory.backup/{feedback_guards_compound…, feedback_independence_for_judgment…, feedback_run_doc_ci_tools_first…, user_structure_is_correctness…}.md` — sister-cross-ref mirror updates
- `?? memory.backup/feedback_structure_judgment_loop_not_output.md` — new-memory mirror (close_out_now mirror already committed)

---

## Per-manifest verification

**A. Ship — PASS.** `Version.hpp:8` = `"5.15.5.F.4d.1.E.0.8"`; E.0.8 block at lines 20-53. CHANGELOG E.0.8 row at workspace `DOCS/CHANGELOG.md:28`. Rename totality (re-run by reviewer, committed tree `c74690b`/`0e48150` via `git grep -P '\bFPN\b'`): ONLY `Version.hpp` (14 lines / 15 occurrences) + `FixedPoint/FixedPointN.hpp` (1 line) — all history/provenance comments, zero live code. `is_FPN_v` in C++: only comments at `FixedPointN.hpp:66,93,106` + `Version.hpp:22,62`; alias deleted. tests/ (workspace): `rg '\bFPN\b'` = 0. tools/: matches only in the 6 allowlisted guard/fixture files; **per-file counts re-verified EXACT vs the frozen allowlist (2/8/4/45/10/2)**. No `FPN_Binary_Binary` corruption anywhere in engine (0 hits); workspace hits (4 files) are incident-discussion only (tool comments / CHANGELOG / methodology spec / postmortem). Count drift noted in finding F2.

**B. Plan + gate — PASS (one fix).** Plan exists, frontmatter `status: v0.2 (2026-06-09) — GATE-AMENDED`. Gate synthesis + exactly 4 per-audit reports (`readiness- / trace-deps- / dod-audit- / completeness-critic-2026-06-09-a5-rename.md`) + enumeration txt with `=== FINAL ALLOWLIST ===` section (line 34). **Finding F2:** the FINAL allowlist's first two section headers — "Engine code+tests (bare FPN):" (line 35) and "is_FPN_v (provenance/history mentions only):" (line 36) — are EMPTY; only the tools/ cohort got pasted counts. The frozen engine-side numbers (Version.hpp 14+2, FixedPointN.hpp 1+3) were never recorded; the EXPECTED-RESIDUAL above it still projects "11 + 1" (pre-rename; the E.0.8 history block itself added FPN mentions). A future reader re-running totality greps gets 14 and has no frozen number to compare — looks like a violation. This is the paste-tool-output rule un-applied inside its own freeze artifact.

**C. Decision log — PASS.** D-163..D-167 all present in Session-12 addendum (`v5.15.5.F.4d.1.E-architecture-v2.md:1038-1062`); each entry has BOTH `<!-- D/C/F: D-16x -->` and a paired `<!-- STATUS: … -->` (verified all 5 pairs at relative lines 5/7, 9/11, 13/15, 17/19, 21/23 of the addendum).

**D. Postmortem — PASS.** Exists; "## Addendum — post-tag close-out" at line 69. Addendum content cross-checked against commit `0e48150` diffs + ledger rows: consistent (3-site 160 disposition, 765/765 leak classification, ubsan-flake rerun, AR-5 meta-lesson).

**E. Ledger NET-ZERO — PASS.** `closed.md:1211` (161) + `:1218` (160), both `closed: 2026-06-09`. `grep -n 'TECH_DEBT-160\|161' open.md` = NO MATCHES. -142 in `open.md:2900` with the A.5 cross-link blockquote ("STAYS OPEN — closes at `.E.1`"). -159 at `open.md:3129`, `status: open (deferred-for-merit; gated on Ship-B)`.

**F. Tools — PASS (one fix).** Both runner scripts `-rwxr-xr-x`. `run_sanitizer_suite.sh`: `FOXML_SUITE_ROOT` override (line 20), `[FAIL]`-preserving (`rg -n "\[FAIL" | head -20` at line 38 before verdict). **Selftest RUN by reviewer: PASS, exit 0** ("RED-on-fail + [FAIL] surfaced + GREEN-on-pass + RED-on-missing"). Both enrolled in `DOCS/TOOLS.md:25-26`, selftest as TEST-HARNESS. `check_doc_rename_classification.py`: lookaround anchoring `(?<![A-Za-z0-9_])…(?![A-Za-z0-9_])` present at BOTH token finditer sites (lines 420-421, 504-505). `check_fpn_doc_size_currency.py`: canon-missing → RED + `return 1` (lines 264-270); SCAN_GLOBS widened (line 105: + `plans/_cross-cutting/**`, `claude-skills/**`, `FEATURE_LOOKUP.md`); guard RUN by reviewer: GREEN, parses canonical 16B from the renamed `FPN_Binary<64>` assert. **Finding F3:** the guard's own docstring is STALE vs its S-4 hardening — line 18 still says "prints WARN + exits 0 (it never false-fails on a parse miss)" and line 73's comment says "WARN+exit-0 if the header isn't there", both contradicting the exit-1 code (line 46's exit legend also omits the canon-missing exit-1). The doc-currency guard's own doc is non-current.

**G. Handoff pair — PASS.** Old 2026-06-08 handoff `status: superseded` (line 3, names the successor). New handoff `status: active` and it is the SINGLETON across all `plans/**/handoffs` (full find+grep sweep; independently confirmed by the sweep's HARD handoff-singleton check). TaskList table present (uncommitted delta) and matches the live harness TaskList 1:1 (tasks 1-2 completed, 3 pending-gated). Frontmatter claims verified against git: `engine_head: 0e48150` ✅, tag at `c74690b` signed+pushed ✅, `workspace_head: at or after a18ed9d` ✅ (984ba08 is the promised follow-on; self-referential wording is honest). required_reading paths ALL exist (decision-log Session-12; `2026-05-30-…-money-numeric-core-foundation.md` 67KB; `rename-ship-methodology.md`). Spot-verified body claims: byte budgets EXACT to the byte (39,109 / 39,637 / 23,298 vs claimed 39.1k/39.6k/23.3k); D-100 oracle dir exists (`plan_checks/2026-06-01-11-phase1-divmul-proof/` with PROOF.md); Ship-B body acceptance section sits at ~§302-330 as cited; MASTER.md staleness honestly disclosed (line 54).

**H. Spec — PASS.** `rename-ship-methodology.md` `stage: 3-first-canonical` (line 3); Phase-5 executor-verification addendum present (verify-EXECUTOR-vs-substring-matrix + idempotency-proof paragraph). `meta-anti-pattern-index.md`: AR-5 row (line 57) + detail section (line 119) — **uncommitted; see delta note above.**

**I. Memory — PASS.** Both memory files exist in the harness dir; MEMORY.md-indexed (lines 13, 15); both mirrored in `memory.backup/` (close_out_now committed; structure_judgment untracked-pending). `check_doc_metadata.py --bidirectional --memories` RUN: "Checked 105 files … All frontmatter valid.", exit 0.

**J. Close-out commit — PASS.** `0e48150` = EXACTLY 4 files (ControllerEventLoop.hpp +6/-1, SPSCRing.hpp +12, DepthRecorder.hpp +16/-6, TickRecorder.hpp +11/-4). Diffs match the narrative (provable `slot >= MAX_EXECUTION_CORES` clause; `to_chars(…, rend-1, …)` separator reservation). SPSCRing comment documents BOTH failed remedies verbatim (`SPSCRing.hpp:156-158`: "(1) #pragma GCC diagnostic ignored — IGNORED by the late IPA passes…; (2) __builtin_unreachable() range hint … no effect"). Full `rev-list` scan of every pushed branch commit: ZERO `build_probe/`/`build_ubsan/` paths — the c74690b repair HELD; `.gitignore:158-159` covers both.

**K. CLAUDE.local.md — PASS (one fix).** Disk rows current: row 43 = E.0.8 SHIPPED 2026-06-09; row 44 = Ship-B-next + the NEW handoff filename. **Finding F4:** row 44 says "D-97..**D-166**" while the log (and the handoff) end at **D-167** — one-off stale range.

**L. Sweep — PASS.** `check_session_docs.sh` RUN by reviewer: **✅ SWEEP CLEAN**, all 7 HARD + 2 ADV green, exit 0.

**M. Privacy — PASS (one pre-existing flag).** `c74690b` = 80 files: 77 rename files in the 8 public source dirs + `Version.hpp` + `README.md` + `.gitignore` — all engine-legitimate ("77 files" claim reconciles as 80 minus those 3). `0e48150` = the 4 source headers only. NO `plans/`, `DOCS/`-private, `tools/`, or `tests/INVARIANTS_MAP.md` paths in either commit (tests/+tools/ are gitignored workspace symlinks). **PRE-EXISTING FLAG (not introduced by this close): `Strategies/private/EmaCross.hpp` carries the header "PRIVATE — do not publish to public repositories" yet is TRACKED in the PUBLIC repo** (`gh repo view`: visibility PUBLIC; `git check-ignore` = not ignored; tracked since ≥ v5.4.0 `3469763`; `c74690b` modified it as part of the rename). Either the header is stale or the file needs operator triage — flagging because every push re-publishes it.

---

## Fix list (CLOSE-WITH-FIXES)

| # | Fix | Where | Size |
|---|---|---|---|
| F1 | rename-candidates row 12 still `QUEUE-FOR-NEXT-RENAME-SHIP (IN-FLIGHT at A.5)` in the **Active candidates** table while the Closed table (line 56) + CHANGELOG say CLOSED — flip/remove the Active row (planning gates scan this list; a Ship-B/.E.1 session would misread #12 as in-flight) | `plans/v5.15-live-readiness/rename-candidates-running-list.md:46` | 1 line |
| F2 | FINAL ALLOWLIST engine-side sections EMPTY — paste the frozen counts (Version.hpp: 14 bare-FPN lines / 2 is_FPN_v; FixedPointN.hpp: 1 / 3) under the two headers; optionally annotate why EXPECTED-RESIDUAL's "11+1" grew (the E.0.8 history block's own mentions) | `plan_checks/2026-06-09-a5-rename-enumeration.txt:35-36` | 4 lines |
| F3 | Stale guard docstring: "WARN + exits 0" / "WARN+exit-0" contradict the S-4 exit-1 hardening | `tools/check_fpn_doc_size_currency.py:18,73` (+ exit legend line 46) | 3 lines |
| F4 | "D-97..D-166" → "D-97..D-167" | engine `CLAUDE.local.md` row 44 (workspace-side source) | 1 token |
| F5 | Commit the expected close-ritual delta (AR-5 row + handoff TaskList table + memory mirrors) — AR-5 currently exists ONLY in the working tree | workspace pending close commit | the close commit itself |

## Trivia (no action required)

- Handoff line 43 "77 engine/test files" conflates: 77 = engine-commit rename files; the 4 test files + 9 tool files were workspace-side (`a18ed9d`).
- `check_doc_rename_classification.py:269` has a third, UNANCHORED finditer (KEEP-term context matcher) — failure direction is rename-suppression (safe), outside the incident class.
- Three legacy handoffs carry free-text non-"active" statuses (WIP-boundary era) — they don't break the singleton invariant but dilute the status vocabulary.

**Builder honesty spot-checks that PASSED:** byte budgets exact; tag signature real; selftest/guards/sweep re-run green by reviewer; ledger NET-ZERO real; postmortem addendum matches the commit it describes; no residual double-rename corruption.
