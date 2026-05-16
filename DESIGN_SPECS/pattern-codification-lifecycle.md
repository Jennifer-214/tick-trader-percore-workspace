# Pattern codification lifecycle (audit → DESIGN_SPEC → invariant → enforcement → cohort migration)

**Established:** 2026-05-11 (v5.14.11.B mega-bundle — meta-pattern emerged from end-to-end codification of `branchless-math-kernel-pattern.md` + `struct-padding-determinism-pattern.md`)
**Status:** ACTIVE
**Cross-references:**
- Sister patterns: `structural-fix-preferred-decision-framework.md` (the WHY), `audit-driven-pre-coding-gate.md` (the audit step), `cfg-flag-eligibility-criteria.md` "Cohort audit" section (cohort migration step)
- First reference application: v5.14.11.B mega-bundle (codified 2 patterns end-to-end)
- CLAUDE.md item 19 (structural fix preferred)
- CLAUDE.local.md going-forward rule "codify design principles in CLAUDE.md as patterns mature" (2026-05-09)
- CLAUDE.local.md going-forward rule "each DESIGN_SPECS doc has a CLAUDE.md cross-ref" (2026-05-09)

---

## Problem statement

When a new architectural pattern emerges (e.g., during a sprint a recurring bug class is structurally fixed, or a new discipline is identified), the natural temptation is to JUST APPLY the fix to the immediate site + move on. This leaves the pattern as TRIBAL KNOWLEDGE — a contributor's memory of "we did this once" — without any structural mechanism preventing the bug class from recurring elsewhere.

**Recurring failure mode (pre-v5.14.11.B):**

1. Sprint identifies a structural fix (e.g., "Cholesky branches are bad")
2. Fix is applied to ONE site
3. The PATTERN is documented in commit messages + maybe a postmortem
4. Future contributors don't see the pattern; they recreate the bug class
5. Eventually re-discovered via another sprint; repeat

**Codification breaks the cycle:** convert tribal knowledge into ENFORCED INFRASTRUCTURE. The pattern becomes:
- Discoverable (DESIGN_SPEC + CLAUDE.md cross-link)
- Verifiable (skill audit catches violations)
- Reusable (next contributor applies it to new surface without re-deriving)
- Cohort-migrate-able (audit finds existing latent instances; bundle the migration)

v5.14.11.B applied this lifecycle to 2 patterns simultaneously. The mega-bundle's 8 sub-tags map directly onto the lifecycle stages.

---

## The lifecycle (7 stages)

### Stage 0: Pattern identification

A new architectural pattern surfaces when one or more of:
- An audit finding (`/dod-audit`, `/parity-check`, `/merge-scan`, `/readiness`) reveals a recurring bug class
- Operator pushback on a code shape ("this should be branchless")
- A structural fix is applied + reviewer recognizes the pattern is reusable elsewhere
- A 2nd application of the pattern emerges (per CLAUDE.local.md "promote when 2+ applications" rule)

Output: rough description of the pattern + which existing surface(s) it applies to.

### Stage 1: Pre-codification audit (catalog the bug class)

Audit the entire codebase for instances of the bug class (or its bug-shape):
- Use `/dod-audit`, `/merge-scan`, or targeted grep
- Classify findings by severity (CRITICAL / HIGH / MEDIUM / LOW)
- Identify the canonical "first reference" instance where the structural fix will land

Output: audit findings report in `plans/plan_checks/<DATE>-<scope>-audit.md` documenting all known instances + which are in-scope for the codification ship vs deferred.

**v5.14.11.B.0 example:** ML_Headers/ math-kernel audit produced findings:
- F1 (CRITICAL): Cholesky branches → fix in .B.1
- F2 (MEDIUM): ThompsonBanditState padding → fix in .B.2
- F3-F7 (INFO/LOW): no action

### Stage 2: Write the DESIGN_SPEC

Author a `DESIGN_SPECS/<pattern>.md` file with:
- Problem statement (recurring bug shape)
- Design space explored (alternatives + why one chosen)
- The pattern (concrete shape, code template)
- Trade-offs + when to apply
- Reference implementations (will be backfilled in Stage 3)
- Lessons / gotchas
- **`## Audit detection` section** — symptoms that `/dod-audit` (or similar tooling) can grep for; enables auto-discovery + future enforcement
- Patterns NOT used here (rejected alternatives)
- Cross-references

Naming convention: `<pattern-kebab-case>.md` describing the pattern, not the specific ship.

**v5.14.11.B.0 example:** wrote `branchless-math-kernel-pattern.md` + `struct-padding-determinism-pattern.md`.

### Stage 3: First reference application (verify the pattern works)

Apply the pattern to its canonical first reference site:
- The site identified in Stage 1's audit
- Should be a CRITICAL or HIGH finding so the fix is load-bearing
- Verify the pattern works as documented (tests pass; byte-equivalence holds; latency invariant; etc.)
- Backfill Stage 2's "Reference implementations" section with the commit reference

Output: a passing build + tag of the first-reference sub-ship.

**v5.14.11.B.1 + .B.2 examples:** Cholesky branchless rewrite + FPN padding fix. Both verified bytewise-equivalent to prior behavior; all tests pass.

### Stage 4: Subsequent applications (verify pattern is reusable)

Apply the pattern to OTHER known violation sites if simple:
- Cohort-migrate per CLAUDE.local.md "cohort-audit when new field has siblings" if instances cluster
- Open TECH_DEBT entries with EXPLICIT triggers for complex cases

**v5.14.11.B.3 example:** UpdateOnline + BuildCorr AVX-512 application (subsequent reference for branchless-math-kernel-pattern + avx512-byte-determinism-pattern).

**v5.14.11.B.2 example:** ThompsonBanditState padding fix applied alongside FPN — cohort migration of "structs with implicit padding in byte-equivalence contexts" within a single ship.

### Stage 5: CLAUDE.md cross-link + invariant promotion

Add a CLAUDE.md item that:
- States the architectural invariant in 3-15 sentences
- Points at the DESIGN_SPEC for the deep dive
- Lists reference applications (first + subsequent)
- Cross-references related items (e.g., CLAUDE.md item 26 cross-refs item 18 + item 25)

Per CLAUDE.local.md "codify design principles" rule:
- 2+ applications, OR
- Documented DESIGN_SPEC + applies broadly

→ promote to CLAUDE.md item

Per CLAUDE.local.md "each DESIGN_SPECS doc has a CLAUDE.md cross-ref" rule:
- Add the cross-link at the end of the new CLAUDE.md item: `Pattern documented in DESIGN_SPECS/<name>.md`.

**v5.14.11.B.4 example:** Added CLAUDE.md item 26 (branchless math kernels) + item 27 (struct padding determinism). Both cross-link their DESIGN_SPECS.

### Stage 6: Tooling enforcement (catch future violations)

Wire the pattern's `## Audit detection` signatures into the appropriate skill(s):
- `/dod-audit` baseline check category (add 3x. entry pointing at the DESIGN_SPEC)
- `/readiness` Check 27 (already invokes /dod-audit; auto-picks up new categories)
- Optionally: dedicated skill if the pattern's detection needs more than grep-based heuristics

**v5.14.11.B.5 example:** Added /dod-audit baseline check categories 3i (math kernel branches) + 3j (struct padding); updated /readiness Check 27 cross-ref count.

### Stage 7: Wider audit + cohort migration

Audit OTHER scopes for the same bug class:
- Different directories (e.g., `CoreFrameworks/` + `Strategies/` if Stage 1 audited `ML_Headers/`)
- Different surfaces (e.g., struct padding in OTHER structs if Stage 1 fixed FPN)
- Apply the cohort-audit going-forward rule per finding

**v5.14.11.B.6 example:** Wider engine audit of CoreFrameworks/+Strategies/ for math-kernel branches. Verdict: GREEN; no findings.

### Umbrella: Bundle + final commit

Aggregate sub-tags into umbrella tag (e.g., `v5.14.11.B`). At umbrella time:
- Verify all sub-tags shipped clean
- Capture any FURTHER patterns that emerged during the codification (recursive — this DESIGN_SPEC was written at v5.14.11.B umbrella from the mega-bundle's own meta-pattern)
- Push engine + sync workspace
- Update master plan with closure note

---

## The pattern (concrete shape — mega-bundle sub-tag structure)

The lifecycle maps naturally onto a mega-bundle sub-tag structure:

| Sub-tag | Stage | Purpose |
|---|---|---|
| `.0` | Stage 1 + 2 | Pre-codification audit + write DESIGN_SPEC(s) |
| `.1`, `.2`, `.3`, ... | Stage 3 + 4 | First reference applications + subsequent applications |
| `.<n-3>` | Stage 5 | CLAUDE.md items + DESIGN_SPECS catalog update |
| `.<n-2>` | Stage 6 | Tooling enforcement (skill updates) |
| `.<n-1>` | Stage 7 | Wider audit + cohort migration if needed |
| `.<n>` | (optional) | Cache alignment / final cleanup |
| `umbrella` | Closure | Bundle + final commit |

Each sub-tag has its own commit + git tag + Version.hpp bump for rollback granularity. Per-sub-tag tags allow surgical rollback if any single stage introduces issues.

### Numbering convention

`v<version>.<sub-tag>.<sub-sub-tag>` (e.g., `v5.14.11.B.3`). Sub-sub-tag granularity is operator preference; mega-bundles benefit from finer rollback anchoring.

Pre-tag anchors: `pre-v<version>.<sub-tag>.<next-sub-sub-tag>` (e.g., `pre-v5.14.11.B.4` = checkpoint after `v5.14.11.B.3` ships).

---

## Trade-offs + when to apply

### Apply when:

- Pattern emerges in a sprint with clear bug-class evidence (recurrence count ≥ 1 + structural fix obvious)
- 2+ surfaces would benefit from the pattern (cohort migration valuable)
- The pattern is REUSABLE (not a one-off fix)
- Operator wants enforcement going forward (vs accepting future occurrences)
- Sprint has time budget for codification work (~6-9 hours for a 2-pattern mega-bundle)

### Skip when:

- Pattern is ONE-OFF — apply structural fix without codification overhead
- Pattern is TOO ABSTRACT — wait for 2nd application before formalizing
- Time pressure forces "ship the fix; codify later" — but EXPLICITLY queue codification as TECH_DEBT with trigger; don't let it rot

### Cost:

- Stage 1 audit: 1-2h depending on codebase scope
- Stage 2 DESIGN_SPEC: 1-2h per pattern (300-500 lines)
- Stage 3 first reference: 30 min - 2h depending on complexity
- Stage 4 subsequent: 30 min - 2h per additional site
- Stage 5 CLAUDE.md: 30 min
- Stage 6 tooling: 30 min - 1h
- Stage 7 wider audit: 1-3h
- Umbrella: 30 min

Total for 1-pattern codification: ~4-6h. For 2-pattern mega-bundle (v5.14.11.B): ~8-10h.

### Win:

- **Bug class structurally extinct** — future contributors who hit the same pattern get fixed-by-design
- **Pattern reusable** — DESIGN_SPEC + CLAUDE.md item make it discoverable
- **Enforcement automatic** — `/dod-audit` catches violations at audit time without operator manual review
- **Cohort migration efficient** — wider audit + bundled fix amortizes per-site overhead
- **Compounds** — each new codified pattern enriches the library; future ships have more invariants to lean on

### Misapply when:

- **Codifying too early** — single instance + no recurrence + no clear shape → wait. Premature codification accumulates dead DESIGN_SPECS docs.
- **Codifying too broadly** — bundling unrelated patterns into one DESIGN_SPEC. Each pattern should have its own clear scope.
- **Skipping Stage 6 enforcement** — DESIGN_SPEC + CLAUDE.md without tooling check = passive documentation; future contributors still violate.
- **Skipping Stage 7 wider audit** — leaves latent violations in the codebase that surface later as bug recurrence.

---

## Reference implementations

### v5.14.11.B mega-bundle — canonical first reference

Codified 2 new patterns end-to-end:
- `branchless-math-kernel-pattern.md` (sub-tags .B.0/.B.1/.B.3/.B.4/.B.5)
- `struct-padding-determinism-pattern.md` (sub-tags .B.0/.B.2/.B.4/.B.5)

Sub-tag structure:
- **.B.0** (Stage 1+2): ML_Headers/ audit + write 2 DESIGN_SPECS
- **.B.1** (Stage 3): Cholesky_Solve constant-8 first reference
- **.B.2** (Stage 3+4): FPN padding + ThompsonBanditState cohort migration
- **.B.3** (Stage 4): UpdateOnline + BuildCorr AVX-512 second/third applications
- **.B.4** (Stage 5): CLAUDE.md items 26+27 + catalog update
- **.B.5** (Stage 6): /dod-audit + /readiness skill enforcement
- **.B.6** (Stage 7): wider engine audit (CoreFrameworks/+Strategies/) — GREEN; 0 findings
- **.B.7**: RidgeWeights cache alignment (orthogonal cleanup folded in)
- **umbrella**: bundle + this meta-DESIGN_SPEC written + final commit

Outcome:
- 2 bug classes structurally extinct (math-kernel branches; struct padding UB)
- 2 reusable patterns codified + cross-linked
- 2 CLAUDE.md invariants added
- /dod-audit + /readiness enforce both patterns automatically
- 0 wider-engine violations found; discipline is across-the-board clean

Test count: 2896 → 2904 (+8 new tests; 0 failures).

### Sister patterns (codified pre-v5.14.11.B; precedents)

- v5.14.8 codified items 19-23 (5 patterns) via similar lifecycle
- v5.14.9.F codified DOMAIN SPLIT cfg-flag refactor via similar lifecycle
- v5.14.10 codified Thompson bandit + per-snapshot-cluster-layout + calib log column registry via similar lifecycle

This DESIGN_SPEC retroactively names the lifecycle that v5.14.8/.9/.10 each applied implicitly. v5.14.11.B is the first ship to FOLLOW the lifecycle explicitly.

---

## Lessons / gotchas

### Symlink-aware engine/workspace commit split

DESIGN_SPECS docs + claude-skills/ live in workspace; CLAUDE.md is per-file-symlinked from engine to workspace. Each sub-tag's Stage 2/5/6 writes touch BOTH repos:
- Engine repo: Version.hpp bump (always)
- Workspace repo: DESIGN_SPEC + CLAUDE.md edits + skill spec edits

Two separate commits + pushes per sub-tag. Tags live in engine repo only.

If `git add path/to/symlinked/file` returns "beyond a symbolic link", commit the file via workspace path instead. Engine repo can't add files that live behind symlinks.

### Stage 6 enforcement is load-bearing

Skipping skill enforcement (Stage 6) means the pattern is documented but not ENFORCED. Future contributors can violate the pattern + `/dod-audit` won't catch it. The codification is incomplete.

Always wire the `## Audit detection` section into the appropriate skill before declaring the codification done.

### Cohort migration in Stage 4 amortizes setup cost

When the bug class has MULTIPLE existing instances (per Stage 1 audit), bundle the migrations as a cohort in the same ship. The DESIGN_SPEC + CLAUDE.md + tooling setup happens ONCE; per-site fix is a few lines.

v5.14.11.B.2 cohort-migrated FPN + ThompsonBanditState in a single sub-tag (both are "structs with implicit padding in byte-equivalence contexts"). Setup cost amortized.

### Stage 7 wider audit is optional but high-value

A wider audit (different directories / surfaces) catches LATENT violations that would otherwise lurk until rediscovered. Even when verdict is GREEN (no findings), the audit confirms the discipline is across-the-board clean — provides confidence + future-audit baseline.

### Meta-codification (this doc)

The pattern of "how to codify a pattern" is itself a pattern. v5.14.11.B exercised the lifecycle explicitly + this DESIGN_SPEC retroactively documents it. Future codification efforts can reference this lifecycle directly.

---

## Audit detection

`/dod-audit` should NOT flag violations of this lifecycle directly (it's a process pattern, not a code pattern). Instead, audit at sprint-end + PR-review:

- **Symptom 1:** new DESIGN_SPEC added without corresponding CLAUDE.md cross-link → Stage 5 missed
- **Symptom 2:** new pattern applied at code site but no DESIGN_SPEC exists → Stage 2 missed
- **Symptom 3:** new pattern doc lacks `## Audit detection` section → Stage 6 enforcement won't auto-flow
- **Symptom 4:** sprint closed without wider audit of related surfaces → Stage 7 missed

Sprint-end checklist (add to /handoff skill or /ship skill):
- Did we audit the codebase for the bug class? (Stage 1)
- Did we write the DESIGN_SPEC? (Stage 2)
- Did we apply the first reference? (Stage 3)
- Did we cohort-migrate other instances? (Stage 4)
- Did we add CLAUDE.md item? (Stage 5)
- Did we wire enforcement? (Stage 6)
- Did we audit wider surfaces? (Stage 7)

---

## Patterns NOT used here (and why)

### "Just apply the fix; document in commit message"

Tribal knowledge. Future contributors don't see commit messages from sprints they weren't part of. Pattern recurs.

### "Write DESIGN_SPEC after fix; skip CLAUDE.md item"

Pattern is discoverable to those who explicitly look at DESIGN_SPECS dir. CLAUDE.md is always-loaded; cross-link enables FRESH session to see the pattern without explicit query.

### "Skip wider audit; trust new contributors to follow pattern"

Latent violations may already exist (audit-time discovery). Wider audit + cohort migration extinguishes the bug class in one sweep; trusting future discipline accumulates risk.

### "Codify in single commit at end of sprint"

Loses sub-tag rollback granularity. If Stage 4 application breaks something, hard to bisect to the specific fix. Sub-tag structure preserves surgical rollback.

### "Skip per-sub-tag Version.hpp bumps"

Violates the "every vX.Y.Z tag includes Version.hpp bump" rule (CLAUDE.local.md feedback_bump_version_per_ship). Each sub-tag is a tag; each tag bumps.

---

## Cross-references

- `structural-fix-preferred-decision-framework.md` (decides WHEN to codify; recurrence count threshold)
- `audit-driven-pre-coding-gate.md` (the Stage 1 audit mechanism)
- `cfg-flag-eligibility-criteria.md` "Cohort audit when new field has siblings" section (Stage 4 cohort migration discipline)
- `branchless-math-kernel-pattern.md` (canonical first reference of this lifecycle)
- `struct-padding-determinism-pattern.md` (canonical second reference of this lifecycle)
- `registry-coverage-ci-check-pattern.md` (**canonical example of RETROACTIVE EXTRACTION at Stage 2** — spec written after 3 canonical applications already shipped in code; demonstrates the "skip Stage 1 audit" + "extract umbrella unification at 3rd canonical" variant of this lifecycle; written at `.F.4c.4` from Check 2 + Check 7 at `.F.4c.3` + Check 8 NEW. Per-variant Stage tracking inside one spec body — Shape A Stage 3 ACTIVE; Shape B Stage 2 DRAFT — is also a canonical example of this lifecycle's "multi-shape spec body" pattern)
- FoxML_Trader_v2 `CLAUDE.md` item 19 (structural fix preferred — the WHY underlying this lifecycle)
- FoxML_Trader_v2 `CLAUDE.local.md` going-forward rule "codify design principles in CLAUDE.md as patterns mature" (Stage 5 promotion criterion)
- FoxML_Trader_v2 `CLAUDE.local.md` going-forward rule "each DESIGN_SPECS doc has a CLAUDE.md cross-ref" (Stage 5 cross-link requirement)
- FoxML_Trader_v2 `CLAUDE.local.md` going-forward rule "cohort-audit when new cfg field has siblings" (Stage 4 cohort migration)
- v5.14.11.B subplan: `plans/v5.14-foxml-port-and-maker/subplans/2026-05-11-v5.14.11.B-branchless-math-mega-bundle.md` (canonical first explicit lifecycle application)
