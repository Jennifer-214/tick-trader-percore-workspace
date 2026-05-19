# /readiness report — `v5.15.5.F.4d.1.B.3` plan body Phase L amendment — 2026-05-18

**Plan audited:** `/home/caramel/code/FoxML_Trader_v2/plans/v5.15-live-readiness/subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md` (engine symlink → workspace path)

**Audit focus:** Phase L (Decision G + Step 1.6.8') readiness — v1.14 amendment landing framework-driven C++ CLI binary (`tools/stamp_model_cli.cpp`) to replace `tools/stamp_model.sh` (6+ cross-tool sync recurrence count).

**Audit scope:** narrow — Phase L amendment readiness only. Wider plan body considered GREEN per prior `/readiness` cycles (v1.10 / v1.11 / v1.12 RE-SWEEPS, all PASS).

---

## Stage 0 DESIGN_SPECS preload (matched surfaces)

- `framework-driven-cli-binary-pattern.md` — NEW Stage 2 DRAFT at workspace; verified on disk (28546 bytes, 2026-05-18)
- `wire-format-byte-preservation-discipline.md` Layer 7 (cross-tool emit-site enumeration; M2) — verified amended at workspace (Layer 7 cross-refs framework-driven-cli pattern)
- `canonical-sister-extension-discipline.md` — § Temporal evolution amendment landed v1.10
- `structural-fix-preferred-decision-framework.md` § Step 2 (4+ recurrence = MANDATORY)
- `pattern-codification-lifecycle.md` (Stage 2 DRAFT → Stage 3 first canonical at this ship)
- `implementation-layer-blindspot-taxonomy.md` (Meta-gap M4; not invoked for Phase L since Phase L is structural-fix-recurrence pattern, not new struct-gen / type-unification surface)

---

## Checklist verdicts — 28-check audit (focus on Phase L amendment)

| # | Item | Verdict | Notes |
|---|------|---------|-------|
| 1 | Hot path purity | PASS | Phase L is slow-path CLI tooling; engine hot path untouched |
| 2 | Train-serve parity | PASS | CLI uses framework `stamp_write_for_model` directly; can't diverge |
| 3 | Surface area | PASS | ~150-200 LOC CLI + ~30 LOC build system + ~50-100 LOC tests + ~5 LOC shim; bounded |
| 4 | Pointer init / heap lifecycle | PASS | No heap state; CLI binary stateless main()+exit |
| 5 | Backward compat | PASS | Deprecation shim preserves `tools/stamp_model.sh --model X`; TECH_DEBT-110 tracks shim deletion |
| 6 | Multi-threading | PASS | Single-threaded CLI binary; no new shared state |
| 7 | Test coverage | PASS | L4 specifies round-trip + byte-identity + legacy-verify + workflow-replication tests |
| 8 | Docs + invariants | PASS | DESIGN_SPEC Stage 2 DRAFT landed; CLAUDE.local.md rule landed; cross-refs at L6 |
| 9 | Forward maintenance | PASS | Phase L IS the forward-maintenance fix (drift impossible by construction) |
| 10 | Rollback story | PASS | Pre-tag `pre-v5.15.5.F.4d.1.B.3` exists; same-commit coupling with 1.6.7.3 documented |
| 11 | Branch state | PASS | `feat/v5.15-live-readiness` |
| 12 | Phase execution order | PASS | Phase L couplings (L1→L2→L3→L4→L5→L6) + same-commit with Step 1.6.7.3 explicit at line 836 |
| 13 | First concrete move (Step 0) | PASS | L1 (DESIGN_SPEC already landed) → L2 (CLI binary) |
| 14 | Function/constructor names cited | PASS | `stamp_write_for_model` at ML_Headers/ModelInference.hpp:1688 VERIFIED at HEAD |
| 15 | File:line refs for tests/baselines | PASS | tools/stamp_model.sh line 12 (Phase 2 note) + line 221 (version literal) + line 244 (orphan) all VERIFIED accurate at HEAD |
| 16 | Stale-claim audit | **GAP** | Status header line 8 says "DRAFT v1.12"; should be v1.14. Line 1034 verification gate still says "tools/stamp_model.sh cross-tool migration complete per Step 1.6.8 (Layer 7): 6 wire-key renames + line 221 version literal" — STALE (now Phase L `tools/stamp_model_cli.cpp`). Line 1083 FEATURE_LOOKUP entry still says "Cross-tool sync (v1.10 per Layer 7): tools/stamp_model.sh:221 version literal synced" — STALE. Line 1087 pre-coding triggers heading says "DRAFT v1.10 → ACTIVE coding" — STALE. Line 1136 footer claims v1.10 effort estimate "~22-32h focused" without Phase L +3-5h delta. |
| 17 | Effort claims reconcile with file size deltas | PASS | Phase L scope ~4-6h focused; matches +3-5h delta over v1.10 bash-patch ~45min |
| 18 | Source-audit references | PASS | Caramel pushback "are you sure the upcoming coding cycle is optimal" + memory `feedback_no_defer_for_effort` + `feedback_motivated_collaborator_for_caramel` cited as catalysts |
| 19 | Predecessor / dependent plans | PASS | Predecessor `.B.2` cited; successor `.C` cited |
| 20 | Tag names locked | PASS | Pre-tag rollback anchor named; same-commit coupling with 1.6.7.3 named |
| 21 | (reserved) | N/A | |
| 22 | (reserved) | N/A | |
| 23 | (reserved) | N/A | |
| 24 | X-macro symmetry tests | N/A | Phase L doesn't introduce new X-macro registries |
| 25 | TECH_DEBT entries | PASS | TECH_DEBT-110 NEW (deprecation shim deletion; trigger / scope / why-deferred all specified at line 1076). TECH_DEBT-106 STATUS-AMENDED v1.14 (partial obviation by Phase L; scope NARROWS) at line 1074. Both proper per discipline. |
| 26 | (reserved) | N/A | |
| 27 | `/dod-audit` composition | PASS | framework-driven-cli-binary-pattern.md applied (NEW Stage 2 DRAFT; first canonical = this ship); canonical-sister-extension-discipline (5 sister candidates inspected); structural-fix-preferred-decision-framework (6+ recurrence evidence cited per § Step 2); pattern-codification-lifecycle (Stage 2 DRAFT pre-coding; Stage 3 first canonical at ship close) |
| 28 | (reserved) | N/A | |
| **29** | **Canonical sister registries considered** | **PASS** | 5 NEW candidates at line 190 for Phase L: Layer 7 (NO-FOLD as structural fix), CI tooling pattern (NO-FOLD), cfg-derived-consumer-framework (EXTEND consumer), tools/compare_scalers.cpp (EXTEND sister tool), framework-driven-cli-binary-pattern.md (NEW Stage 2 DRAFT). Total 17 candidates aggregated. |
| **30** | **Future-oriented plan template sections** | **PASS** | Required sections present for Phase L: (1) Design space + future-oriented choice (Decision G at line 131); (2) Canonical sister registries considered (5 new candidates at line 190); (3) Bug classes closed (Class 18/19/21/22 cross-tool surface at lines 209-212); (4) DESIGN_SPECs landed/amended (framework-driven-cli-binary-pattern.md Stage 2 DRAFT at line 228); (5) Verification gate (L4 sub-step round-trip + byte-identity + legacy-verify + workflow-replication at line 807); (6) TECH_DEBT auto-write (TECH_DEBT-110 NEW + TECH_DEBT-106 amend at lines 1074-1076); (7) Pre-coding triggers (this audit gate fire IS the trigger — Phase L itself per `feedback_audit_canonical_sister_before_new_infra` at L1); (8) Operator migration impact (CLI flag continuity + retention period at line 838); (9) Novel alternative consideration (α-ζ design space at L1 spec). |
| **31** | **4-pillar self-audit pillar 1 — DESIGN_SPECS cross-check** | **PASS** | framework-driven-cli-binary-pattern.md Stage 2 DRAFT EXISTS on disk (verified 28546 bytes); cross-refs sister specs (Layer 7 + cfg-derived-consumer-framework + autopopulate + meta-registry); recurrence threshold cited per `structural-fix-preferred-decision-framework.md` § Step 2 |
| **32** | **Pillar 2 — Anti-pattern catalog check** | **PASS** | Class 18 / 19 / 21 / 22 explicitly cited at lines 209-212 as classes closed at cross-tool surface via Phase L |
| **33** | **Pillar 3 — Operator impact** | **PASS** | Per-line 838-842: NO operator action during retention; mechanical migration post-shim-deletion. Deprecation shim preserves invocation surface (`tools/stamp_model.sh --model X` continues to work via exec redirect). |
| 34 | Pillar 4 — Novel alternative | PASS | α-ζ design space in DESIGN_SPEC body (covered in L1 spec body); confirmed at Decision G "Pattern body covers... design space α-ζ" at line 196 |
| **34** | **Consumer enumeration / cross-tool / sister-registry parity** | **PASS** | Cross-tool surface enumerated; bash↔C++ mirror identified; framework single-source-of-truth (`stamp_write_for_model`) verified |
| **35** | **Cross-file-type discipline** | **PASS** | C++ binary calls existing C++ framework header; build system integration via CMake (sister to existing tools/compare_scalers.cpp); deprecation shim is 1-line bash |
| **36** | **Sister-registry parity verification (M1a)** | N/A | Phase L doesn't introduce sister registries |
| **37** | **Transitional state budget (B3)** | N/A | Phase L is structural-fix-recurrence; not struct-gen migration |

---

## Phase L specifics — Stage 0 DESIGN_SPECS dependency verification

| Claimed dependency | Verified | Notes |
|---|---|---|
| `tools/stamp_model.sh` exists at HEAD | YES | 16735 bytes; verified 2026-05-08 last mod |
| `tools/stamp_model.sh:12` Phase 2 documentation note | YES | Line 12 = "# tools/stamp_model.cpp that runs validation directly from CLI." VERIFIED |
| `tools/stamp_model.sh:221` version literal `stamp_format_version=1` | YES | Line 221 = `if [[ "$FORMAT_VERSION" -ge 5 ]]; then`; line 222 = `CANONICAL="${CANONICAL}stamp_format_version=1` — accurate ref |
| `tools/stamp_model.sh:244` `inference_cfg_freshness_tau` orphan | YES | Line 243 = `inference_cfg_held_out_fraction=${HOF_FMT}`; line 244 = `inference_cfg_freshness_tau=${FTAU_FMT}` — accurate ref |
| `tools/compare_scalers.cpp` exists (sister C++ tool precedent) | YES | 6199 bytes; verified 2026-05-08 last mod |
| `stamp_write_for_model` at `ML_Headers/ModelInference.hpp:1688` | YES | `inline StampWriteResult stamp_write_for_model(const char* model_path, ...)` confirmed at line 1688 |
| `framework-driven-cli-binary-pattern.md` Stage 2 DRAFT at workspace `DESIGN_SPECS/` | YES | 28546 bytes; "**Status:** Stage 2 DRAFT v1.0" header VERIFIED; problem statement + design space α-ζ + pattern shape sections present |
| `wire-format-byte-preservation-discipline.md` Layer 7 amendment | YES | Layer 7 § Cross-tool emit-site enumeration EXISTS (line 304); cross-refs framework-driven-cli-binary-pattern.md at line 352 ("Layer 7 discipline OBVIATED at framework-driven cross-tool surfaces") |
| 6+ recurrence count documented | YES | Plan body line 138 enumerates v5.2.3 / v5.8.8 / v5.9.3b / v5.9.4a / v5.9.5c / v5.11.18a + .B.3 batch; matches script header lines 12-30 |
| CLAUDE.local.md going-forward rule landed | YES | Line 107 of CLAUDE.local.md: "Framework-driven CLI binary for cross-tool wire-format surfaces (≥3 recurrence)" with trigger + cross-refs |
| `plans/_future/2026-05-12-decoupling-endgoal-roadmap.md` breadcrumb | YES | Line 515: "v5.15.5.F.4d.1.B.3 Phase L — `tools/stamp_model_cli.cpp` replaces `tools/stamp_model.sh` (POSITIONING: STRONGLY POSITIVE; first framework-driven CLI binary)" |
| `decoupling-endgoal-roadmap.md` "Training entry points" axis advance | YES | Line 544-545: "Phase L is a precedent for the FOREACH_CLI_MODE registry's eventual instantiation" |

---

## Top 5 findings (Phase L amendment readiness)

### Finding 1 — Status header NOT updated to v1.14 (DOCUMENTATION DRIFT; non-blocking)

**Sites:**
- Plan body line 8: `**Status:** **DRAFT v1.12 (2026-05-18) — FULL plan body**` — should be v1.14 with Decision G + Phase L summary in supersedes chain
- Plan body line 1136 footer: `**End of .B.3 plan body v1.10 DRAFT.**` + effort estimate `**~22-32h focused**` (excludes Phase L +3-5h)

**Verdict:** GAP (cosmetic). Plan body internal references to v1.14 amendment correct; only the status banner + footer summary are stale. Cold-pickup risk: fresh session reading line 8 status might miss that Phase L is the live scope.

**Fix:** ~5 min mechanical — update line 8 status header to v1.14 with Decision G summary; update line 1136 footer to include Phase L effort + Class 19/22 newly-closed at cross-tool surface + framework-driven-cli-binary-pattern.md NEW Stage 2 DRAFT.

### Finding 2 — Verification gate line 1034 STALE bash-patches reference

**Site:** Plan body line 1034: `tools/stamp_model.sh cross-tool migration complete per Step 1.6.8 (Layer 7 first canonical reference): 6 wire-key renames + line 221 version literal =1→=2 + line 244 orphan deleted + cross-ref comments added + 7 lower-hit files PRESERVE WITH COMMENT verification`

**Verdict:** GAP (semantic regression). This verification-gate item describes the SUPERSEDED v1.10 bash-patch scope. Phase L SUPERSEDES this — verification should describe `tools/stamp_model_cli.cpp` exists + builds + L4 verification tests PASS + deprecation shim landed. If a fresh session implements per this line literally, they'd apply bash patches and miss Phase L entirely.

**Fix:** ~10 min — replace line 1034 with Phase L verification criteria: (a) `tools/stamp_model_cli.cpp` exists + builds + ldd shows no extra deps; (b) L4 round-trip + byte-identity + legacy-verify + workflow-replication tests PASS; (c) deprecation shim at `tools/stamp_model.sh` is 1-line exec redirect; (d) DESIGN_SPEC `framework-driven-cli-binary-pattern.md` promoted Stage 2 DRAFT → Stage 3 ACTIVE; (e) TECH_DEBT-110 entry committed.

### Finding 3 — FEATURE_LOOKUP entry line 1083 STALE bash-patch reference

**Site:** Plan body line 1083: `**Cross-tool sync (v1.10 per Layer 7):** tools/stamp_model.sh:221 version literal synced to engine STAMP_FORMAT_VERSION_CURRENT=2; both sites have cross-reference comments enforcing per Layer 7 § Cross-tool version literal sync discipline.`

**Verdict:** GAP (operator-facing FEATURE_LOOKUP draft will land stale). Should describe Phase L: version literal lives ONCE at engine; CLI inherits via framework call; bash↔C++ mirror structurally eliminated.

**Fix:** ~5 min mechanical — replace "Cross-tool sync (v1.10 per Layer 7)" paragraph with "Cross-tool structural elimination (v1.14 per Phase L)" paragraph describing CLI binary + framework inheritance + deprecation shim retention period.

### Finding 4 — Pre-coding triggers heading line 1087 STALE version reference

**Site:** Plan body line 1087: `## Pre-coding triggers (REQUIRED before promoting DRAFT v1.10 → ACTIVE coding)`

**Verdict:** DOCUMENT-ONLY drift. Heading still says "v1.10 → ACTIVE coding". Body items (1-14) all PASS. Plan is structurally ready; only the heading version string is stale.

**Fix:** ~30 sec — change `v1.10` → `v1.14` in heading.

### Finding 5 — Decision G ordering before Decision F in document (acceptable)

**Sites:**
- Decision G at line 131
- Decision F at line 155

**Verdict:** ACCEPTED. Decision G is the v1.14 add appended after Decision E (chronological insertion). Decision F is the older Decision F (v1.3 originating) coming after. Order anomaly is cosmetic — not a logic gap. Both decisions cross-reference each other correctly (F operator-migration + G structural-fix are complementary). A future cleanup pass could reorder alphabetically but not blocking.

---

## Cold-pickup completeness verdict (Phase L specifically)

**Cold-pickup score: 9/10 (GREEN with documentation polish needed)**

| # | Field | Phase L verdict |
|---|---|---|
| C.1 | Branch state | PASS — `feat/v5.15-live-readiness` matches operator practice |
| C.2 | Phase execution order matches dependency order | PASS — Phase L coupling block at lines 830-836 documents L1→L2→L3→L4→L5→L6 + same-commit with 1.6.7.3 |
| C.3 | First concrete move | PASS — L1 DESIGN_SPEC ALREADY LANDED (file exists at workspace); L2 is "write tools/stamp_model_cli.cpp" |
| C.4 | Function/constructor names cited | PASS — `stamp_write_for_model` + `ControllerConfig<64>` + `StampInferenceCfgInputs` + `getopt_long` all named |
| C.5 | File:line refs for cited tests/baselines | PASS — verified `tools/stamp_model.sh:12/221/244` accurate; `ModelInference.hpp:1688` accurate |
| C.6 | Stale-claim audit | **FAIL** — 4 documentation sites STALE (Status header / verification gate line 1034 / FEATURE_LOOKUP line 1083 / pre-coding triggers heading line 1087); Findings 1-4 above |
| C.7 | Effort claims reconcile with file size deltas | PASS — ~150-200 LOC C++ + ~30 LOC build + ~50-100 LOC tests + ~5 LOC shim; reasonable estimate within ~4-6h focused (bash script at 716 lines → 1-line shim is well-defined scope) |
| C.8 | Source-audit references | PASS — Caramel pushback + memory `feedback_no_defer_for_effort` (3-instance pattern) + `feedback_motivated_collaborator_for_caramel` (best-software discipline) all cited as catalysts; `tools/stamp_model.sh:12` Phase 2 prior-art note cited |
| C.9 | Predecessor / dependent plans named with paths | PASS — predecessor `.B.2` cited; successor `.C` cited; sub-master path explicit |
| C.10 | Tag names locked | PASS — pre-tag `pre-v5.15.5.F.4d.1.B.3` named; same-commit coupling with Step 1.6.7.3 explicit at line 836 + line 1003 |

**Cold-pickup verdict for Phase L specifically:** GREEN with documentation polish. Fresh session opening the plan body would NOT lose >30 min re-deriving Phase L context because Decision G section (line 131) + Step 1.6.8' section (line 795-842) + canonical sister table (line 188-198) all describe Phase L clearly. The 4 STALE documentation sites (Status header / verification gate / FEATURE_LOOKUP / pre-coding triggers heading) are cosmetic — they describe the SUPERSEDED v1.10 scope but are clearly NOT the live scope per line 795 banner ("SUPERSEDES Step 1.6.8 bash-patches per v1.14 amendment 2026-05-18"). A fresh session would read line 795 and orient correctly within ~2 min.

---

## Blocking gaps that must resolve before Phase L coding starts

**None blocking.** All 4 STALE doc sites are downstream of Phase L coding (verification gate fires AT ship close; FEATURE_LOOKUP entry composed AT ship close; pre-coding triggers heading is documentation). They can be cleaned up at ship-close auto-write OR pre-coding as a 20-minute polish pass.

**Recommended pre-coding polish (~20 min total):**
1. Update Status header line 8 to v1.14 with Decision G + Phase L summary in supersedes chain (~5 min)
2. Update verification gate line 1034 to Phase L scope (~10 min)
3. Update FEATURE_LOOKUP entry line 1083 to Phase L scope (~5 min)
4. Update pre-coding triggers heading line 1087 version string (~30 sec)
5. Update footer line 1136 with Phase L effort delta + new classes closed (~3 min)

---

## Recommendations

### Must fix before coding
NONE — Phase L scope is fully specified at Decision G (line 131) + L1-L6 sub-steps (line 795-842) + canonical sister table (line 188-198) + bug classes closed (line 209-212) + DESIGN_SPECs landed (line 228) + TECH_DEBT entries (line 1074-1076).

### Worth fixing during coding
- 4 STALE doc sites per Findings 1-4 (20 min polish pass; can land WITH Phase L coding commit OR in separate cleanup commit)

### Acceptable risk (don't block)
- Decision G ordering before Decision F (Finding 5) — cosmetic; can defer to next plan body cleanup

---

## Verdict: GREEN — start coding

**Phase L amendment is READY for coding.** All structural requirements per future-oriented-plan-template.md PRESENT. All cited file/function refs VERIFIED at HEAD. Canonical sister table comprehensive (17 candidates total). Bug classes precisely scoped (Class 18/19/21/22 at cross-tool surface). DESIGN_SPECS pre-amendments LANDED (framework-driven-cli-binary-pattern.md Stage 2 DRAFT on disk; Layer 7 cross-refs in place; CLAUDE.local.md rule landed; roadmap breadcrumb landed).

The 4 stale doc sites (Findings 1-4) are cosmetic and don't block the structural work. Recommended 20-minute polish pass before coding OR landing-as-part-of-Phase-L-commit.

**Cold-pickup completeness:** 9/10 GREEN. A fresh session reading Decision G + L1-L6 + canonical sister table would orient correctly within 5 minutes. Required reading: lines 131-153 (Decision G) + lines 188-198 (canonical sister) + lines 795-842 (L1-L6 sub-steps + couplings + operator migration).

---

## Map-update suggestions (post-coding)

- **CODE_MAP.md regen** after Phase L lands — NEW `tools/stamp_model_cli.cpp` main() + helper fns
- **DESIGN_SPECS/README.md catalog entry** for `framework-driven-cli-binary-pattern.md` (at ship close)
- **CLAUDE.local.md going-forward rule** — already LANDED at line 107 (pre-coding)
- **`plans/_future/2026-05-12-decoupling-endgoal-roadmap.md` "Training entry points" axis** — already LANDED at line 515 (pre-coding); update at ship close to mark Phase L AS-SHIPPED rather than AS-PLANNED

---

**End of /readiness report.** Phase L (Decision G + Step 1.6.8') amendment is GREEN for coding. 4 stale documentation sites identified for 20-min polish pass (Findings 1-4); none block coding. Cold-pickup completeness 9/10. All claimed dependencies verified at HEAD.
