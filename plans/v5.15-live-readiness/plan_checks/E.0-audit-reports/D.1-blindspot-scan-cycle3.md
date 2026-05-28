---
type: audit-report
audit: blindspot-scan
scope: .D.1 plan body v0.4 (doc-sweep adapted)
target_ship: v5.15.5.F.4d.1.D.1
cycle: 3
date: 2026-05-28
plan_body: plans/v5.15-live-readiness/subplans/2026-05-28-v5.15.5.F.4d.1.D.1-doc-system-end-goal-language-sweep.md
plan_version_audited: v0.4 (frontmatter + footer aligned)
skill: /blindspot-scan
sister_audits: [/readiness cycle 3 expected, /trace-deps cycle 3 expected]
predecessor: D.1-blindspot-scan-cycle2.md (v0.3 audit; 1 NOT-CLOSED L-3 + 5 NEW; 3 actionable)
---

# /blindspot-scan cycle 3 against .D.1 plan body v0.4

## Verdict

**YELLOW-with-2-MED** — v0.4 closes the 3 actionable cycle-2 blindspots cleanly (PASS on NEW-1 hook-source addition, NEW-3 currency-registry self-coverage, NEW-5 rollback asymmetry). Cycle 3 surfaces 4 NEW blindspots, with 2 MED-severity that materially affect execution correctness. Convergence trajectory is overall convergent (7 → 3 → 4 actionable; the +1 vs cycle-2 reflects fresh-eyes catching dogfood bugs introduced by the v0.4 amendments themselves, not divergent finding-discovery). Per `feedback_iteration_spiral_signals_audit_meta_gap`: NOT a meta-gap signal — these are first-order findings, not symptoms of audit-methodology blindness. **Cycle 4 NOT recommended** — close the two MED findings inline (small Edit-tool patches; no design change), proceed to coding. The MED findings would only land as silent execution-time bugs (wrong tool grep / wrong sidecar row); operator can absorb during Phase A or H execution.

## Cycle 2 closure verification

| Cycle 2 finding | Severity | v0.4 closure | Verification |
|---|---|---|---|
| **NEW-1** Phase A.7 missing `tools/hooks/pre-commit` + `tools/install-git-hooks.sh` | MED-LOW | **PASS** | Phase A.7 table at lines 308-309 of v0.4 plan body now lists both: `tools/hooks/pre-commit` (versioned source) AND `tools/install-git-hooks.sh` (installer). Discipline note explicit: "sister-cohort completeness; otherwise new contributors' `install-git-hooks.sh` reinstalls outdated hook". Closure complete. |
| **NEW-2** B19/B14 pillar boundary ambiguity | LOW-INFO | **ACCEPT-WITH-RATIONALE** (cycle 2 final) | Plan body acknowledges B19 is Stage 2 DRAFT; boundary refinement defers naturally to Stage 3 promotion via `pattern-codification-lifecycle.md` 2nd-canonical requirement. Acceptable. |
| **NEW-3** Currency registry self-coverage gap | LOW | **PASS** | Phase H.4.2 currency registry at lines 644-654 now includes two NEW rows: "Site classification matrix" (source Site classification section / propagates to tool detection rules at A.1) + "B19 pillar Stage 2 DRAFT body" (source H.10 / propagates to taxonomy.md). Closure complete. |
| **NEW-4** Other cfg fields cited as vestigial but actually-deleted | LOW | **ACCEPT-WITH-RATIONALE** (cycle 2 final) | Cycle 2 systematic verification passed all 3 fields (engine_mode + engine_arch + BacktestSharded_Run); no fresh check needed in v0.4. |
| **NEW-5** L-3 workspace-side rollback asymmetry NOT-CLOSED | LOW | **PASS** | Phase A.0 at line 244 of v0.4 now includes explicit "Rollback asymmetry note (per cycle 2 NEW-5)" paragraph: "The pre-tag reverts ENGINE REPO state ... It does NOT revert workspace-side state (memories at ~/.claude/projects/... + TaskList + audit-report files at plan_checks/E.0-audit-reports/). If rollback needed mid-ship, those landed-mid-cycle artifacts persist and may need manual reversion. Document at ship-close postmortem." Closure complete. |
| **NEW-6** Transition-documentation regex robustness | LOW | **ACCEPT-WITH-RATIONALE** (cycle 2 final) | Operator TSV review catches; appropriate accept. |

**Closure summary:** 3 PASS / 3 ACCEPT-WITH-RATIONALE. v0.4 amendments closed every actionable cycle-2 finding cleanly. No PARTIAL or NOT-CLOSED items carried forward.

## Cycle 3 fresh-eyes blindspots

### NEW-1 — Phase F.4 self-contradictory Check 44/45 numbering (MED)

**Risk:** Plan body Phase F.4 amendment text + code block are internally inconsistent. The text says (line 513): "my new check is Check 45, next-numbered after pre-existing Check 44". The code block at line 519 inserts row `| 44 | Tests changed section ...` (Check 44). The section-header code block at line 523 says `### Check 45 — Tests changed section`. The skill table row says one number; the section body says another.

**Verified state via direct read of `/home/caramel/code/tick-trader-percore-workspace/claude-skills/readiness/SKILL.md`:**

```
Line 611: | 34 | Audit tier declared ...
Line 612: | 36 | Sister-registry parity ...
...
Line 619: | 43 | Operator-facing doc cohort ...
```

Table SKIPS 35 + 44 + 45. Last visible row IS 43 (matches plan body). But **also skips 35**. The sister-cohort gap from .B.4 is actually larger than v0.4 frames it: 35 ALSO missing (likely also `check-35-*.md` sidecar exists somewhere). v0.4 framing acknowledges 44 gap but says nothing about 35.

The plan body Phase F.4 currently:
- Frames new check as "Check 45"
- But code-inserts as Check 44 row
- And calls H.4.2 registry row "SKILL.md Check 45 amendment"
- Verification gate line 763 says "Check 45 numbering per cycle 2 audit correction"

**Operator execution risk:** Phase F.4 implementation ambiguous — should I add a row at `| 44 |` or `| 45 |`? Without resolution, mid-execution operator decision OR silent drift. If pre-commit hook references `tools/check_plan_body_tests_section.py` invocation from "Check 45 — Tests changed" but readiness skill table has it as Check 44, future audits + readiness invocations cite different numbers.

**Recommendation (PRE-CODING amendment NEEDED):** Resolve v0.4 self-contradiction. Either:
- (A) New check = 44 (lowest unused) + add gap-fill note "Check 35 + 36-43 + 44-45 numbering preserved-as-is per categorical-trigger discipline" + delete sister-cohort gap framing (since 44 is now the new check)
- (B) New check = 45 + add separate "Check 44 = cfg-field-categorization SKILL.md table row gap-fill" addendum that adds BOTH rows (Check 44 cfg-field-categorization + Check 45 Tests changed) in Phase F.4
- (C) New check = 46 (next-after-pre-existing-44-and-45-sidecars) + add separate gap-fill addendum that adds Check 44 + 45 rows for pre-existing sidecars

**Severity: MED.** Self-contradiction is structural (not just numbering preference); silent drift would propagate to memory cross-refs + pre-commit hook invocation paths + future audit citations. Single Edit-tool patch closes; no design change needed.

### NEW-2 — Phase H.10 grep syntax is wrong (MED)

**Risk:** Phase H.10 instruction at line 713 reads: "verify pillar count at Phase H.10 execution time before writing (use `grep -E '^### Pillar B' DESIGN_SPECS/meta-disciplines/implementation-layer-blindspot-taxonomy.md`)".

**Verified via mechanical test:**

```bash
$ grep -cE '^### Pillar B' /home/caramel/code/tick-trader-percore-workspace/DESIGN_SPECS/meta-disciplines/implementation-layer-blindspot-taxonomy.md
0

$ grep -cE '^### B[0-9]' /home/caramel/code/tick-trader-percore-workspace/DESIGN_SPECS/meta-disciplines/implementation-layer-blindspot-taxonomy.md
17

$ grep -nE '^### B[0-9]' /home/caramel/code/tick-trader-percore-workspace/DESIGN_SPECS/meta-disciplines/implementation-layer-blindspot-taxonomy.md | head -3
75:### B1 — Type-change cascade when struct field types shift mid-migration
94:### B2 — Field-name collision across heterogeneous registries unifying into shared struct
112:### B3 — Transitional state coexistence with bounded growth
```

Actual heading shape is `### B1 — ...`, NOT `### Pillar B1 — ...`. The word "Pillar" appears in section BODIES (e.g., line 90: "Pre-coding type-change diff via `/blindspot-scan` Pillar B1.") but never in section HEADERS.

**Operator execution risk:** If operator runs the proposed grep at H.10 execution time:
- Output = 0 pillars (because regex matches zero headings)
- Operator either:
  - (a) Misreads as "no pillars; just write B19 freely" (silent miscount)
  - (b) Realizes regex wrong + spends 10-30 sec debugging + manually corrects (annoyance)
  - (c) Trusts plan body claim of "17 codified pillars (B1-B15 + B17-B18; B16 gap pre-exists)" and skips the verification entirely (defeats the purpose of "verify pillar count at execution time")

Same issue: engine-side `/home/caramel/code/FoxML_Trader_v2/DESIGN_SPECS/` doesn't exist (no symlink); workspace path is canonical. Plan body grep doesn't show path qualification.

**Recommendation (PRE-CODING amendment NEEDED):** Correct grep syntax to `grep -cE '^### B[0-9]' /home/caramel/code/tick-trader-percore-workspace/DESIGN_SPECS/meta-disciplines/implementation-layer-blindspot-taxonomy.md` + state expected output ("17 codified pillars: B1-B15 (skipping B16) + B17-B18"). Single Edit-tool patch closes.

**Severity: MED.** Silent miscount risk OR operator-friction. Plan body already states the count claim ("17 codified pillars") — the grep is just a verify-at-execution step. But the verify mechanism is broken, defeating the discipline of mechanical verification.

### NEW-3 — Phase A.7 hook-source path verification gap (LOW)

**Risk:** Phase A.7 v0.4 amendment adds `tools/hooks/pre-commit` and `tools/install-git-hooks.sh` to the cohort table. But the actual workspace `tools/` directory does NOT have these paths:

```
$ ls /home/caramel/code/tick-trader-percore-workspace/tools/hooks/
ls: cannot access '...': No such file or directory

$ ls /home/caramel/code/tick-trader-percore-workspace/tools/install-git-hooks.sh
ls: cannot access '...': No such file or directory
```

Only the engine-side paths exist:
```
$ ls /home/caramel/code/FoxML_Trader_v2/tools/hooks/
pre-commit

$ ls /home/caramel/code/FoxML_Trader_v2/tools/install-git-hooks.sh
/home/caramel/code/FoxML_Trader_v2/tools/install-git-hooks.sh
```

Plan body Phase A.7 frames these as "VERSIONED hook source" implying engine-tracked; but plan body also references workspace paths in other contexts (e.g., `tick-trader-percore-workspace/claude-skills/readiness/SKILL.md`). The hook source IS engine-tracked (not workspace-tracked), which IS correct for tooling that needs to ship with the public repo. Just worth being explicit so operator doesn't confuse workspace/engine boundary.

**Operator execution risk:** Minimal. Operator at Phase A.3 + A.6 will run `git status` and discover the actual paths; no silent drift, but verification step would be smoother with engine-vs-workspace path explicit.

**Recommendation:** ACCEPT-WITH-RATIONALE OR optional improvement — add "(engine-tracked at `/home/caramel/code/FoxML_Trader_v2/tools/hooks/pre-commit`; ships with public repo)" qualifier to A.7 row to clarify boundary. Not blocking.

**Severity: LOW.** Path verification at execution time would surface this; no silent failure mode.

### NEW-4 — Decision-log entries pre-drafted but D-65/D-66 file absence at rollback time (LOW)

**Risk:** Plan body Phase A.0 rollback-asymmetry note (added per cycle 2 NEW-5) addresses memories + TaskList + audit-report files. But it doesn't explicitly call out: **D-65 + D-66 decision-log entries are pre-drafted in plan body body (lines 470-477) but NOT YET in the actual decision-log file** (`v5.15.5.F.4d.1.E-architecture-v2.md`) at rollback time.

If rollback happens mid-ship after Phase F.2 lands D-65/D-66 to decision-log file (per H.4.2 currency registry entry for D-65/D-66 propagation): pre-tag reverts engine state, but decision-log file IS engine-tracked (`plans/` is symlinked into engine repo). So rollback WOULD revert decision-log changes. Verified via `ls plans/v5.15-live-readiness/decision-logs/`: file exists at engine-side path; tracked by git per pre-tag.

So actually NOT a rollback asymmetry concern (decision log IS in pre-tag scope). The cycle-2 NEW-5 rollback-asymmetry note (memories at `~/.claude/projects/...` + TaskList) does NOT need extending to D-65/D-66.

**However**, the related concern: Phase F.2 lands D-65/D-66 to decision-log file. Phase H.7 verification mentions "Decision log v2 amended (D-65 + D-66 entries)" but doesn't check that D-65/D-66 sentinels in plan body match the actually-landed decision-log entries (could drift if plan body amended between Phase F.2 and H.7).

**Recommendation:** ACCEPT-WITH-RATIONALE. Phase F.2 lands them; Phase H.5 `/capture-audit --deep` Check 4 (sentinel matching) catches any post-landing drift. Defense-in-depth structure adequate.

**Severity: LOW.** No mechanical bug; just observation that question-asker raised a non-issue because decision-log IS engine-tracked.

## Convergence

- **Cycle 1:** 12 findings → 7 actionable implementation-detail blindspots
- **Cycle 2:** 7 cycle-1 verified (6 PASS / 1 NOT-CLOSED L-3) + 6 NEW (3 actionable: NEW-1 MED-LOW + NEW-3 LOW + NEW-5 LOW = carried-NOT-CLOSED → now closed in v0.4)
- **Cycle 3:** 6 cycle-2 verified (3 PASS / 3 ACCEPT-WITH-RATIONALE) + 4 NEW (2 actionable: NEW-1 MED Phase F.4 contradiction + NEW-2 MED H.10 grep syntax; 2 ACCEPT-WITH-RATIONALE: NEW-3 LOW path verification + NEW-4 LOW pre-drafted-decision-log)

**Trajectory verdict:** Convergent. Per `feedback_iteration_spiral_signals_audit_meta_gap`:
- Cycle 1 → 2: 7 → 3 actionable (57% reduction; convergent)
- Cycle 2 → 3: 3 → 2 actionable (33% reduction; convergent; smaller absolute reduction expected at lower base)
- Cycle 3 findings: BOTH MEDs are dogfood bugs (F.4 self-contradiction + H.10 wrong grep syntax) introduced by v0.4 amendments addressing cycle-2 findings. This is the expected pattern of "fixes-introduce-smaller-fixes" — NOT a sign of META-gap. The findings are also mechanical correctness (one Edit-tool patch each), NOT architectural.

**Meta-gap signal: NOT PRESENT.** Both MED findings are first-order amendment errors caught by fresh-eyes audit (which is what cycle-3 is for); they don't represent a class of blindspot that audit methodology missed. Cycle 4 NOT recommended.

## Recommended next move

- (X) **PREFERRED — Audit-first close (~10 min):** Apply 2 inline Edit-tool patches:
  1. Phase F.4: pick A/B/C above (operator-decided; recommend B — keeps Check 45 framing + adds gap-fill addendum for Check 35 + 44 numbering preservation)
  2. Phase H.10: fix grep syntax + state expected output count
  3. Then proceed to coding without cycle 4
- (Y) Coding-with-annotations: code with mental note to fix at Phase F.4 + H.10 execution time (low cost; ~5 min mid-ship correction)
- (Z) Cycle 4: NOT recommended — fresh-eyes would surface only more amendment-introduced micro-bugs without architectural value

## Inflection check

Per `feedback_iteration_spiral_signals_audit_meta_gap`:
- Iteration count since last meta-gap codification: 3 (cycle 1 + 2 + 3)
- Findings size trajectory: HIGH → MED → MED (NOT diverging; same severity ceiling but smaller absolute count)
- NEW pillars surfaced this fire: 0 (none of cycle-3 findings constitute a NEW blindspot category; all map to existing B14/B19 sweep/classification + B19 sub-cat 6 "plan-body-self-test bootstrap" + existing pre-drafted content discipline)
- Meta-gap signal: NOT PRESENT
- Audit methodology adequate; convergence verified

## Punch-list (ordered by severity)

1. **MED — Phase F.4 self-contradiction:** Resolve Check 44 vs 45 numbering (PRE-CODING; ~3 min Edit)
2. **MED — Phase H.10 grep syntax:** Correct to `^### B[0-9]` + state expected count "17 codified pillars" (PRE-CODING; ~2 min Edit)
3. **LOW — A.7 path qualification (optional):** Add engine-vs-workspace boundary note for `tools/hooks/pre-commit` (PRE-CODING optional; ~1 min Edit)
4. **LOW — Phase H.5 sentinel match check (acknowledged):** Existing `/capture-audit --deep` Check 4 covers; no amendment needed

**Total pre-coding amendment effort: ~5-10 min focused.**

---

**End of /blindspot-scan cycle 3 report.**
