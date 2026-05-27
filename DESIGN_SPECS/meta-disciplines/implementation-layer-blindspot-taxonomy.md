---
type: meta-discipline
stage: 3-first-canonical
version: 1.2
established: 2026-05-18
last_amended: 2026-05-27
tags: [meta-discipline, audit-methodology, framework-discipline]
surface: [registry]
sister_specs: [audit-driven-pre-coding-gate.md, audit-scope-taxonomy.md, wire-format-byte-preservation-discipline.md, cfg-field-categorization-discipline.md]
applies_at_skills: [/blindspot-scan, /precoding-audit-gate]
pillars:
  - B14: multi-surface-deletion-ordering (Stage 3 first canonical at v5.15.5.F.4d.1.B.4 WIP-14b — 51-site engine_arch=centralized deletion)
  - B15: unconditionalization-latent-assumption-audit (Stage 2 DRAFT 1st instance at v5.15.5.F.4d.1.B.4)
---

# Implementation-layer blind-spot taxonomy

**Stage:** Stage 2 DRAFT v1.0 (drafted 2026-05-18 at v5.15.5.F.4d.1.B.3 mid-coding after operator surfaced 12 blind spots that 3 audit batches missed)
**Promotes to:** Stage 3 ACTIVE v1.0 at `.B.3` ship close (first canonical reference: `/blindspot-scan` first invocation against Step 1.6.3)
**Sister specs:** `audit-driven-pre-coding-gate.md` (parent pattern; this is the 9th-axis extension), `canonical-sister-extension-discipline.md` (M1 sister-registry parity discipline this complements), `wire-format-byte-preservation-discipline.md` (Layer 7 sister addressing cross-tool emit enumeration), `pattern-codification-lifecycle.md` (codification workflow)

---

## Problem statement

The existing `/precoding-audit-gate` fires 5-8 audits that catch DIFFERENT classes of SHAPE-level concerns:

| Audit | Catches |
|---|---|
| `/parity-check` | Train↔serve identity drift; wire-format byte risks; production-caller field-population gaps |
| `/trace-deps` | Dependency chain gaps (function signatures, file:line refs, missing struct fields, consumer enumeration) |
| `/readiness` | Plan-level completeness (28-check pass; cold-pickup completeness; behavior-change-via-default) |
| `/merge-scan` | Reuse opportunities + Class 18 mirror-incomplete + branch-density regressions |
| `/dod-audit` | DESIGN_SPECS pattern application (cache, branchless, bitmap, X-macro patterns) |
| `/accounting-audit` | OMS/fee/commission/P&L/Class 27/H4 violations |
| `/registry-fit-audit` | Registry misapplication (eligibility criteria, KIND vs storage routing) |
| `/hft-audit` | Universal HFT principles (cache layout, branchless, lock-free, FPN edge cases) |

These audits operate at the SHAPE / STRUCTURE / SCOPE layer. **They do NOT catch IMPLEMENTATION-DETAIL blind spots** — type-compatibility cascades, field-name collisions across unified registries, transitional state coexistence, context-dependent C++ constructs (e.g., `if constexpr` template-context requirements), include-cycle risk, row-order drift between sister registries.

**Canonical case (codified 2026-05-18 at `.B.3` Step 1.6.3 mid-coding):** 3 batches of audits (v1.2 / v1.9 / v1.11) all returned GREEN/YELLOW-with-amendments. Operator asked "what other issues are we not aware of?" — surfaced 12 blind spots that none of the 8 audit skills targeted. The 12 mapped to 12 RECOGNIZABLE CATEGORIES that this taxonomy now codifies.

**Pattern shape:** SHAPE audits answer "is the design right?" IMPLEMENTATION-DETAIL audits answer "will the code compile + run correctly without surprise rework?". Both layers are needed; neither substitutes for the other.

---

## When to apply

Fire the implementation-layer audit (via `/blindspot-scan` skill OR manual taxonomy walk-through) AFTER `/precoding-audit-gate` returns GREEN or YELLOW-with-amendments and BEFORE substantive coding starts.

**Trigger criteria — apply when ANY of:**

- Struct-gen migration: unconditional or filtered struct-field auto-generation crosses ≥2 registries
- Type unification migration: STORAGE_T column being adopted; struct field types shift across rows
- Cross-registry consumer: a single struct or function accesses fields from ≥2 registries
- Macro hoisting: X-macro walker bodies extracted from call sites into framework primitive
- Include surface change: new cross-directory includes proposed (`MemHeaders/` ↔ `CoreFrameworks/` ↔ `ML_Headers/`)
- Wire-format ordering change: master registry order differs from legacy walker emit order
- Pre-coding audit gate ran 3+ batches with iterative findings (signals SHAPE-level audits exhausted; IMPLEMENTATION-DETAIL likely still open)

**Skip when:**

- Trivial single-file changes (1-row registry addition)
- Pure additive work (new tests, comments, docs)
- Plan body already enumerates type-change deltas + field uniqueness + include direction

---

## The 12 categories

Each category gets: **Definition** / **Detection mechanism** / **Loud vs silent** / **Worked example** / **Detection guard recommendation**.

### B1 — Type-change cascade when struct field types shift mid-migration

**Definition:** Existing struct declares field `T_old name;` (e.g., `double ridge_lambda;`); migration changes registry STORAGE_T column to T_new (e.g., `FPN<F>`); auto-gen of struct replaces with `T_new name;`. Downstream consumer sites that compare/assign by-T_old break compile.

**Detection mechanism:**
- Enumerate currently-flagged field-name set
- For each: extract OLD struct field type (from existing X-macro walker source registry) + NEW struct field type (from master registry STORAGE_T column)
- Diff → produce type-change punch-list
- Grep consumer sites for each name → classify each as TYPE-SENSITIVE (uses `==` against literal of T_old, or assigns to T_old field) vs TYPE-AGNOSTIC (passes through, copies value-by-value)
- Output: per-field type-change consumer scope estimate

**Loud vs silent:** LOUD (build failure with type-mismatch diagnostic). HIGH-RISK because consumer count can be 50-100+; rebuild cycles wasted if surfaced mid-coding.

**Worked example:** `.B.3` Step 1.6.3 unconditional struct-gen via Decision C Approach A. 27 currently-STAMP_BOUND_CFG_DERIVED-flagged fields (`ridge_lambda`, `thompson_mu_prior`, `bandit_blend_ratio`, etc.) shift from FOREACH_STAMP_BOUND_CFG declared types (often `double`) to master registry STORAGE_T (often `FPN<F>`). ~80 test fixture sites in `tests/controller_test.cpp` reference `sr.<field>` and compare against literal `double` values — must wrap in `FPN_ToDouble(...)` or add `operator==(FPN<F>, double)` for compile success.

**Detection guard:** Pre-coding type-change diff via `/blindspot-scan` Pillar B1.

---

### B2 — Field-name collision across heterogeneous registries unifying into shared struct

**Definition:** Unconditional struct-gen walks ≥2 registries with row-name (or row-legacy_field) extracted as struct field name. If any name appears in BOTH registries (per-core + global, or per-core + ml_cfg_flag, etc.), struct gets duplicate field declaration → compile error.

**Detection mechanism:**
- Extract field-name set from each registry
- Compute pairwise intersection across all registry pairs
- Emit: any non-empty intersection = collision risk
- Per-collision: flag whether intentional sister (different domains; rename one) or accidental (one is mistyped; fix the typo)

**Loud vs silent:** LOUD (compile failure). LOW-MED risk because most cfg fields have unique names by convention, but unification of 4+ registries makes collision more likely (>140 names to deconflict).

**Worked example:** `.B.3` Step 1.6.3 4-walker unification across FOREACH_PER_CORE_CFG_FIELD (79 rows) + FOREACH_GLOBAL_CFG_FIELD (47 rows) + FOREACH_ML_CFG_FLAG (12 rows; legacy_field column) + FOREACH_GATE_CFG_FLAG (6 rows; legacy_field column) = 144 names. E.g., is `bandit_enabled` (ml_cfg_flag) unique vs per-core `bandit_blend_ratio`? Names ARE distinct, but uniqueness must be verified mechanically.

**Detection guard:** `tools/check_field_name_uniqueness.py` CI tool (NEW at `.B.3` ship close). Runs in test target.

---

### B3 — Transitional state coexistence with bounded growth

**Definition:** Multi-step migration where SOURCE pattern (e.g., FOREACH_STAMP_BOUND_CFG walker) AND TARGET pattern (e.g., unconditional struct-gen via master registries) BOTH alive temporarily. Struct holds BOTH field sets until SOURCE deleted at the migration's Step LAST. Growth is bounded but unverified.

**Detection mechanism:**
- Enumerate field sets generated by SOURCE walker + TARGET walker
- Compute peak coexistence size (bytes per struct + total struct count)
- Verify peak is bounded (≤25KB suggested ceiling per struct; ≤100KB program-wide for transitional structs)
- Plan body MUST annotate "transitional state allowed; size budget = N KB; resolves at Step <N>"

**Loud vs silent:** SILENT (no compile/test error; growth could exceed cache lines for hot-path structs OR exceed .bss budget if grossly underestimated). LOW risk for boot-time structs (ModelStampResult, StampInferenceCfgInputs); MED risk if applied to hot-path structs.

**Worked example:** `.B.3` Step 1.6.3 (unconditional struct-gen lands) → Step 2 (legacy registry deletion). Between Step 1.6.3 and Step 2, ModelStampResult has BOTH the 144 master-registry auto-gen fields AND the 27 legacy FOREACH_STAMP_BOUND_CFG fields AND 10 POST_CFG fields. Estimated peak ~5-15KB per struct. Bounded; vanishes at Step 2.

**Detection guard:** Plan body annotation requirement (`/readiness` Check 37).

---

### B4 — Semantic-vs-mechanical pattern mirror (Surface G applicability per registry type)

**Definition:** Pattern (e.g., per-entry `has_<name>` Surface G flag) is mechanically applicable to ALL registry types but SEMANTICALLY meaningful only for SOME. Generating it for ALL produces dead-byte fields with no correctness impact but space waste.

**Detection mechanism:**
- For each registry, identify whether the Surface G semantic applies (consumer reads `has_<name>` to gate behavior) OR is dead (consumer reads `<name>` direct value)
- Distinguish applies-to-all from applies-to-some-only
- Recommend conditional generation OR document rationale for unconditional

**Loud vs silent:** SILENT (no correctness impact). LOW priority; cosmetic.

**Worked example:** `.B.3` Step 1.6.3 — for FOREACH_ML_CFG_FLAG / FOREACH_GATE_CFG_FLAG bitmap-bool entries, framework drift walker at `CfgGateRegistry.hpp:383+` reads `handle.legacy_field` DIRECT (not `handle.has_legacy_field`). Adding `uint8_t has_<legacy_field>` to struct-gen is dead. Decision: keep for sister-consistency with per-core/global rows (consumer code may evolve to use it; bounded byte cost).

**Detection guard:** DESIGN_SPEC body annotation; not a blocker.

---

### B5 — Compile-time scaling threshold

**Definition:** Template instantiation explosion when X-macro walked over many rows × multiple template fns. Each row × type-combination → distinct instantiation. Build time grows.

**Detection mechanism:**
- Estimate instantiation count: rows × template-fn-count × call-site-count
- Threshold: warn if estimated instantiations ≥1000 OR if past-ship compile-time growth ≥20% since baseline
- Mitigation: use type-erased descriptor lookup for non-hot-path consumers; explicit instantiation for hot-path

**Loud vs silent:** LOUD-ISH (slower builds; user-visible). LOW risk per ship; cumulative if not monitored.

**Worked example:** `.B.3` Step 1.6.3 — 144 fields × 4 walker invocations × 2 sites (struct-gen) + 1 site (parser) = ~600-1000 `tt::cfg_parse_field<T>` template instantiations. Estimated +5-10s compile time. Recoverable.

**Detection guard:** Build-time budget gate in CI (NEW at future ship; not at `.B.3`); manual estimation at coding time per `/blindspot-scan` Pillar B5.

---

### B6 — STORAGE_T variant coverage gap

**Definition:** Master registry adds a NEW STORAGE_T variant (e.g., `char[N]` for KIND_STRING). Consumer template `tt::cfg_*_field<T>` doesn't have a branch for the new variant → compile failure when X-macro walker hits the row.

**Detection mechanism:**
- Enumerate all STORAGE_T variants present in master registries (per-core + global)
- For each variant, verify `tt::cfg_parse_field<T>` + `tt::cfg_emit_field<T>` + `tt::cfg_drift_compare<T>` + `tt::cfg_set_field<T>` have a covering branch
- Emit: missing branch = coverage gap

**Loud vs silent:** LOUD (compile failure at the missing branch). Catches itself at build but may be diagnosed late (after substantial coding).

**Worked example:** `.B.3` Step 0.5c LANDED — `tt::cfg_parse_field<T>` extended with char[N] branch (no-op verified at HEAD since no current char[N] fields). At `.F.4e` future ship adding KIND_STRING, the branch is in place; static_assert at registry boot-time verifies all STORAGE_T variants are covered.

**Detection guard:** `tools/check_storage_t_coverage.py` CI tool (NEW at `.B.3` ship close).

---

### B7 — Include topology cycle risk

**Definition:** Proposed new include relationship between files. If A → B existed pre-migration and migration adds B → A, compile fails on cyclic include.

**Detection mechanism:**
- Map current include graph for affected files
- Inspect new include edges proposed by migration
- Compute: any cycle in resulting graph
- Mitigation if cycle detected: forward declarations OR template parameterization OR header split

**Loud vs silent:** LOUD (compile failure with clear "incomplete type" or "redeclaration" diagnostic).

**Worked example:** `.B.3` Step 1.6.3 option (e) — `MemHeaders/CfgGateRegistry.hpp` needs to include `CoreFrameworks/CfgFieldRegistry.hpp` (for FOREACH_PER_CORE_CFG_FIELD). Need to verify CfgFieldRegistry.hpp doesn't reverse-depend on CfgGateRegistry.hpp.

**Detection guard:** `/blindspot-scan` Pillar B7 — pre-coding grep of existing includes + propose-then-verify shape.

---

### B8 — Consumer enumeration incompleteness at type-sensitivity layer

**Definition:** `/trace-deps` enumerates ALL CONSUMER SITES (Class 14 prevention). But type-sensitivity of each site is NOT enumerated. Type-change cascade (B1) requires per-site type-sensitivity classification.

**Detection mechanism:**
- After `/trace-deps` enumerates consumer sites, classify each as:
  - **TYPE-SENSITIVE-READ:** site compares field against literal of OLD type → needs wrap or operator
  - **TYPE-SENSITIVE-WRITE:** site assigns field from variable of OLD type → needs conversion
  - **TYPE-AGNOSTIC:** site passes through; copies value-by-value; doesn't compare or write by-type
- Emit per-site classification; total count of TYPE-SENSITIVE sites = effort estimate

**Loud vs silent:** Surfaces during /trace-deps re-run with classification extension; otherwise compile failures at coding time (LOUD but late).

**Worked example:** `.B.3` Step 1.6.3 — /trace-deps enumerated 149 sites total. Classification revealed ~80 TYPE-SENSITIVE-READ sites in test fixtures (compare `sr.ridge_lambda == 0.005`), ~10 TYPE-SENSITIVE-WRITE sites (assign `handle->ridge_lambda = sr.ridge_lambda`), rest TYPE-AGNOSTIC.

**Detection guard:** `/trace-deps` skill amendment — TYPE-SENSITIVE classification per call site (NEW at `.B.3` ship close).

---

### B9 — Unverified audit claims (claim → no evidence chain)

**Definition:** Audit report makes a claim ("`tt::cfg_drift_compare<T>` auto-handles FPN/double cross-type comparison via implicit conversion") without citing source-of-truth evidence (file:line of the template definition + reading the relevant branch). Claim accepted at face value; subsequent decisions built on possibly-incorrect ground truth.

**Detection mechanism:**
- For every claim about runtime behavior or type compatibility in audit reports, verify cited file:line
- If claim has no citation, demote to "unverified" status; demand follow-up read

**Loud vs silent:** SILENT (claim looks fine in report; ground truth could be wrong; manifests as runtime bug or compile error during coding).

**Worked example:** `.B.3` `/parity-check` MEDIUM-1 claimed "cfg_drift_compare<T> auto-handles via implicit conversion" without reading the template definition. Operator question forced verification → trust-but-verify discipline.

**Detection guard:** `/parity-check` skill amendment — claim → evidence chain requirement (each claim must cite file:line) at `.B.3` ship close.

---

### B10 — Struct layout drift across mixed-width fields

**Definition:** Struct holds fields of varying widths (uint8_t / uint32_t / int64_t / FPN<F>). Compiler inserts padding holes between fields for alignment. If struct is used in byte-equivalence context (memcmp, SHA-256, HMAC input, wire format), padding contents are undefined → byte-equivalence breaks.

**Detection mechanism:**
- Identify whether struct is used in any byte-equivalence context
- If YES: enforce H12 invariant (explicit `int<N>_t _padding<N> = 0;` per padding hole)
- If NO: padding holes are cosmetic; no action

**Loud vs silent:** SILENT for cosmetic case; LOUD for byte-equivalence case (memcmp returns nonzero on otherwise-identical structs).

**Worked example:** `.B.3` ModelStampResult holds 144 mixed-width fields after Approach A. NOT used in byte-equivalence context (wire body is generated SEPARATELY via emit walker; struct itself isn't memcmp'd or hashed). H12 not applicable. Padding holes are cosmetic.

**Detection guard:** H12 invariant clarification — applies only when struct IS byte-equivalence input.

---

### B11 — Context-dependent C++ construct (if-constexpr template-context requirement)

**Definition:** Filter via `if constexpr (((meta) & FLAG) != 0)` body-gated. Requires X-macro walker body to be expanded inside a template context (template fn, template class member, or template-instantiated lambda). If walker is expanded in a NON-template function, `if constexpr` doesn't compile.

**Detection mechanism:**
- Inspect site where X-macro walker is expanded
- Verify enclosing function is template-instantiated (has `template <typename...>` declaration)
- If NOT template, must template-ify (add `template <unsigned F>` parameter) OR use runtime `if (...)` (less performant)

**Loud vs silent:** LOUD (compile failure with "if constexpr only valid in template" diagnostic).

**Worked example:** `.B.3` Step 1.6.3 Site 2 parser dispatch — currently `verify_model_stamp(...)` is a non-template inline function. Adding `if constexpr (meta & STAMP_BOUND_CFG_DERIVED)` walker bodies would fail to compile. Mitigation: option (e) framework consolidation places the walker inside `cfg_derived::parse_stamp_cfg_to_derived<F>(...)` template fn → naturally template-context.

**Detection guard:** Pre-coding inspection of host function context (`/blindspot-scan` Pillar B11).

---

### B13 — Cross-walker struct-field uniqueness (different walkers contribute to same struct)

**Definition:** Multiple X-macro walkers contribute fields to the SAME struct (e.g., ModelStampResult receives fields from both FOREACH_STAMP_BOUND_MODEL_CONST AND from master cfg via STAMP_RESULT_DERIVED_FIELDS_AUTO_GEN walker). Name collision across walkers produces duplicate member declarations → compile error.

**Distinct from B2:** Pillar B2 catches name collision across the 4 master cfg registries (within the same walker scope). B13 catches collision across SEPARATE struct-generating walkers (multiple walkers, same target struct).

**Detection mechanism:**
- Enumerate ALL X-macro registries that generate struct fields anywhere in the codebase
- Pairwise intersect field-name sets across walker pairs targeting the same struct
- Verify any collision is registered in an H18 SIDECAR EXCLUSION sparse sidecar (e.g., `FOREACH_STAMP_RESULT_FIELD_EXCLUSION`)
- Failure to register = CI fail

**Loud vs silent:** LOUD (build failure with duplicate member declaration diagnostic). Caught at build time; rebuild cycle wasted if surfaced mid-coding.

**Worked example:** `.B.3` Step 1.6.3 unconditional struct-gen via Approach A. Master FOREACH_GLOBAL_CFG_FIELD has `xgb_min_child_weight`, `xgb_seed`, `xgb_train_nthread` (runtime cfg values). FOREACH_STAMP_BOUND_MODEL_CONST_POST_CFG ALSO has those names (training-time architectural constants). Same conceptual field, two registries, legitimately dual-source (training-time-recorded vs runtime-tunable). ModelStampResult Approach A unconditional struct-gen collides with MODEL_CONST walker → 3 duplicate member errors. Resolved via `FOREACH_STAMP_RESULT_FIELD_EXCLUSION(X)` sparse sidecar listing the 3 colliding names + `#define name _stamp_result_excluded_##name` redirect bracket at struct sites (master walker emits dead-prefixed fields; real fields come from MODEL_CONST walker).

**Detection guard:** `tools/check_struct_field_uniqueness.py` CI tool (NEW at `.B.3` ship close); `/readiness` Check 40 (NEW at ship close); H18 SIDECAR EXCLUSION pattern in CfgGateRegistry.hpp.

**Sister pattern:** B2 (4-registry collision within walker scope). B13 extends to cross-walker scope when struct receives fields from multiple X-macro walkers.

**Anti-pattern to avoid:** Bulk-remove duplicate-named fields from one registry to "consolidate" — registries may encode legitimate dual semantics (e.g., training-time-recorded vs runtime-live). Per H18 SIDECAR pattern, sparse exclusion preserves both semantics while preventing struct collision. Consolidation only when registries genuinely encode the same semantic.

---

### B12 — Cross-registry row ordering for wire-format emit

**Definition:** Master registry declaration order MAY differ from legacy walker emit order. Migration of emit walker changes wire-format key ORDERING. Layer 5b structural invariants catch via I1-I5 but post-facto (after Step 1.7); plan-time verification missed.

**Detection mechanism:**
- For each currently-flagged STAMP_BOUND_CFG_DERIVED field, extract: legacy walker emit order vs master registry declaration order
- Diff → produce reorder punch-list
- Verify Layer 5b structural invariants tolerate the diff OR plan body explicitly documents intentional reorder

**Loud vs silent:** SILENT if both walkers happen to produce identical order; LOUD (invariants fire) if order differs and Step 1.7 invariants invocation lands. Late-detection cost = revert + reorder.

**Worked example:** `.B.3` Step 1.6.4 — legacy FOREACH_STAMP_BOUND_CFG walker emits 27 keys in body order; master per-core registry emits same 27 keys in master declaration order. If orders differ, v2 wire format keys are reordered vs v1 → I1-I5 invariants fire OR HMAC verification fails for v2 stamps emitted with new walker compared to expected v1-derived stamps.

**Detection guard:** `/parity-check` skill amendment — row-order parity check before Step 1.7 invariants invocation (NEW at `.B.3` ship close).

---

### B14 — Multi-surface deletion ordering (NEW v5.15.5.F.4d.1.B.4 v1.7.5 WIP-12; Stage 2 DRAFT → Stage 3 first-canonical at Phase D)

**Definition:** When deleting a feature/cfg/symbol spanning ≥3 files with compile-time interdependencies, sites must be sequenced per **leaves-first ordering** (operator-facing docs first → stale comments → log strings → version-history-comments → GUI gating → tests → cohort wrappers → centralized branches → unconditionalize boot-spawn gate → cfg field surface last). Without leaves-first ordering, wrong order → mid-WIP compile-fail (LOUD failure mode but high rework cost: rebuild 6 dirs × N retries until ordering converges).

**Detection mechanism:**
- For each deletion target in plan body, run B-Plus v0.4 `--gen-deletion-cohort PATTERN` (operator-facing planning helper at COMMIT layer; sister to v0.3 line-anchor)
- Classify each match per **deletion-kind heuristic**: operator-facing-doc / stale-comment / log-string / version-history-comment / GUI-gating / test-surface / cohort-wrapper / DELETE-with-body / UNCONDITIONALIZE-body / enum-constant / cfg-field-row / archived-changelog (LEAVE) / current-changelog (historical-row LEAVE)
- Emit per-WIP ordering punch-list per leaves-first sequencing (sites with no compile dependency first; sites consumed by others last)
- Per H17 framework discipline: cfg-field-row deletion LAST (auto-removes cfg field declaration + parser entry via FOREACH_CFG_FIELD walker)

**Loud vs silent:** LOUD (compile failure mid-WIP if wrong order). HIGH rework cost; cohort size determines impact (51-site cohort = 30-60 min × N retries).

**Worked example:** `.B.4` v1.7.5 WIP-14 — `engine_arch` cfg field deletion (17 files / 81 occurrences cohort) via 12-step leaves-first ordering: (1) pre-deletion verification gates; (2-4) operator-doc + stale-comment + log-string deletion; (5) GUI gating per-site classification + delete; (6) TUISnapshot field + TUI_PopulateTopology fn signature + caller updates atomically; (7) test surface deletion; (8) sister wrapper cohort delete per Class 18 prevention; (9) negated centralized-arch branches delete; (10) unconditionalize boot-spawn gate (B15 verification first); (11) cfg field surface deletion (enum constants + cfg field + parser; LAST per H17); (12) post-deletion verification.

**Detection guard:** `/blindspot-scan B14` audit at pre-coding gate when plan body proposes feature deletion spanning ≥3 files. Sister to B-Plus v0.4 generator mode (mechanical classification) + `/readiness` Check 35 sidecar (audit-time enforcement). Sister memory `feedback_multi_surface_deletion_ordering_discipline.md` (Stage 3 codification at WIP-12).

---

### B15 — Unconditionalization latent assumption shift (NEW v5.15.5.F.4d.1.B.4 v1.7.5 WIP-12; Stage 2 DRAFT — 1st instance only; Stage 3 promotion conditional on 2nd canonical surfacing per `feedback_proactive_novel_alternative_consideration`)

**Definition:** When removing cfg-gate via "always-true" simplification (e.g., `if (cfg.X == VALUE)` → unconditional because VALUE is the only surviving value post-feature-deletion), latent per-arch/per-mode assumptions inside the formerly-gated block become unconditional silently. Any assumption that was load-bearing for the OTHER cohort (the no-longer-existent one) silently fails — execution proceeds with assumption violated.

**Detection mechanism:**
- Identify UNCONDITIONALIZE-body kind sites via B-Plus v0.4 `--gen-deletion-cohort` classification (`UNCONDITIONALIZE-body (positive gate per B15 pillar; verify latent assumptions)`)
- For each site, enumerate latent assumptions inside the formerly-gated block (what does the body assume about the cfg value; what other code paths exist for the alternate cfg value; per-cohort initialization/cleanup/state-management dependencies)
- Verify latent assumptions are NOT load-bearing for the no-longer-existent cohort
- If cfg value being deleted entirely: alternate cohort no longer exists → assumptions unconditional safely
- If cfg value being merged into default: alternate cohort still exists → assumptions may need preservation via different transformation

**Loud vs silent:** SILENT — latent assumption broken silently post-deletion; not caught by compile. HIGH detection cost (debugging time hours-to-days depending on production observability).

**Worked example:** `.B.4` v1.7.5 WIP-14 — `engine_arch=per_core_slow` boot-spawn gate at `EngineSharded.hpp:2484`. PRE-DELETION: `if (cfg.engine_arch == ENGINE_ARCH_PER_CORE_SLOW) { ...spawn-per-core-threads... }`. POST-DELETION unconditionalized. B15 verification enumerates latent assumptions: `slow_threads[]` allocated (yes; sized for MAX_EXECUTION_CORES) / `args[]` initialized (yes; per-core context in caller) / `slow_path_thread_fn` exists + handles per-core dispatch (yes) / `pthread_create` succeeds (load-bearing per H1; caller-side error handling). VERDICT: UNCONDITIONALIZATION SAFE — all assumptions hold unconditionally post-deletion since `engine_arch=centralized` cohort being deleted entirely.

**Detection guard:** `/blindspot-scan B15` audit at pre-coding gate when plan body proposes UNCONDITIONALIZE-body kind sites. Sister to B-Plus v0.4 generator mode (mechanical classification flags UNCONDITIONALIZE-body kind) + `/readiness` Check 36 sidecar (audit-time enforcement). Sister memory `feedback_unconditionalization_latent_assumption_audit.md` (Stage 3 codification at WIP-12; Stage 3 first-canonical promotion DEFERRED to 2nd canonical per 2-instance threshold).

---

## Composition with sister skills

- **`/precoding-audit-gate`** — orchestrator; can include `/blindspot-scan` in audit_set (extended)
- **`/blindspot-scan`** — NEW skill; instantiates this taxonomy as parallel audit
- **`/readiness` Checks 36-39** — plan-body verification of B2 / B3 / B7 / B8 / B12 disciplines
- **`/trace-deps` TYPE-SENSITIVE classification** — extends consumer enumeration with B8 detection
- **`/parity-check` claim→evidence + row-order** — addresses B9 + B12 detection
- **CI tools** `check_field_name_uniqueness.py` (B2) + `check_storage_t_coverage.py` (B6) — automated detection at every build

---

## First canonical application

`.B.3` Step 1.6.3 pre-coding (2026-05-18) — taxonomy applied retroactively to the 12 blind spots operator surfaced. Produced punch-list:

| Category | Verdict for Step 1.6.3 | Action |
|---|---|---|
| B1 type-change | 27 fields shift from FOREACH_STAMP_BOUND_CFG declared types to master STORAGE_T | Pre-coding diff via `/blindspot-scan` |
| B2 collision | 144 names across 4 registries; verify uniqueness | `tools/check_field_name_uniqueness.py` run |
| B3 transitional | ~5-15KB struct peak between Step 1.6.3 and Step 2 | Plan body annotates budget |
| B4 dead-byte | `has_<legacy_field>` for ml/gate cfg_flag possibly dead | Decision: keep for sister-consistency |
| B5 compile-time | ~600-1000 template instantiations; +5-10s estimated | Acceptable; no gate breach |
| B6 STORAGE_T coverage | char[N] branch landed at Step 0.5c (no-op verify) | `tools/check_storage_t_coverage.py` run |
| B7 include cycle | `CfgGateRegistry.hpp` → `CfgFieldRegistry.hpp` new edge | Verify reverse direction absent |
| B8 type-sensitive consumers | 149 sites; classify TYPE-SENSITIVE-READ / WRITE / AGNOSTIC | `/trace-deps` amendment re-run |
| B9 claim→evidence | `/parity-check` MEDIUM-1 `cfg_drift_compare<T>` claim | Read CfgFieldDispatch.hpp:382-388 |
| B10 struct layout | ModelStampResult NOT byte-equivalence input | H12 inapplicable; cosmetic only |
| B11 if-constexpr context | Site 2 parser dispatch in non-template fn | Option (e) consolidation naturally fixes |
| B12 row-order parity | Master order vs legacy FOREACH_STAMP_BOUND_CFG order | `/parity-check` amendment re-run |

---

## Anti-patterns to avoid

- **Treating SHAPE audit verdicts as implementation-detail verdicts.** SHAPE audits answer "is the design right?" — NOT "will the code compile/run without surprise?". Both layers are needed.
- **Build-driven implementation-detail discovery.** Letting compile failures surface B1/B2/B6/B7/B11 wastes ~1-2 build cycles per issue. Pre-coding `/blindspot-scan` is ~30-45 min; surfaces ALL 12 categories at once.
- **Categorizing every blind spot as either "audit gap" or "operator missed".** The taxonomy is the third path — STRUCTURAL category recognition that future audits encode.
- **Adding new categories without DESIGN_SPEC entry.** This taxonomy is the registry; new blind-spot categories surfaced at future ships MUST add a category here (B13+) with definition + detection + worked example.

---

## Codification lifecycle

Per `pattern-codification-lifecycle.md`:

- **Stage 1 (signal):** 2026-05-18 — operator surfaced 12 blind spots at `.B.3` Step 1.6.3 mid-coding. SHAPE audits had returned 3 batches of GREEN/YELLOW. Recognition: NEW categorical pattern of implementation-detail blind-spots distinct from SHAPE concerns.
- **Stage 2 (DRAFT):** 2026-05-18 — this doc. First-pass enumeration of 12 categories with detection mechanisms.
- **Stage 3 (ACTIVE; ship close):** `.B.3` — applied retroactively to Step 1.6.3; `/blindspot-scan` skill lands; CI tools land; sister skill amendments land.
- **Stage 4 (REUSED):** Future ships invoke `/blindspot-scan` after `/precoding-audit-gate`; new categories added as B13+ rows in this taxonomy.

---

## Reference implementations

(Populates at Stage 3 ACTIVE — first canonical application at `.B.3` ship close.)

- (pending) `claude-skills/blindspot-scan/SKILL.md` — first canonical skill
- (pending) `tools/check_field_name_uniqueness.py` — B2 detection
- (pending) `tools/check_storage_t_coverage.py` — B6 detection
- (pending) `plans/v5.15-live-readiness/plan_checks/blindspot-scan-2026-05-18-step-1.6.3.md` — first canonical audit fire

---

## Cross-references

- `audit-driven-pre-coding-gate.md` — parent pattern; this is the implementation-detail extension
- `canonical-sister-extension-discipline.md` — sister discipline for cohort migration (M1 from v1.10 codification)
- `wire-format-byte-preservation-discipline.md` Layer 7 — sister discipline for cross-tool emit enumeration (M2 from v1.10 codification)
- `pattern-codification-lifecycle.md` — codification workflow this followed
- `feedback_implementation_detail_blindspot_recovery_via_taxonomy.md` (engine memory) — operator-collaboration rule that fires the discipline
- FoxML_Trader_v2 `DOCS/RECURRING_BUG_PATTERNS.md` — bug class catalog (specific anti-patterns; this taxonomy is BROADER — anti-pattern prevention)
- `tools/check_field_name_uniqueness.py` + `tools/check_storage_t_coverage.py` — CI tools instantiating B2 + B6 detection

---

**Stage 2 DRAFT v1.0 — committed 2026-05-18 ahead of `.B.3` ship close.** Promotes to Stage 3 ACTIVE v1.0 at `.B.3` ship-close commit once `/blindspot-scan` skill + 2 CI tools + 3 sister skill amendments land + first canonical application documented.
