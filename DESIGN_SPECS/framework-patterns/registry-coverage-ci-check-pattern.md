---
type: framework-pattern
stage: 4-cohort
version: 1.1
established: 2026-05-16
last_amended: 2026-08-16
tags: [framework-discipline, structural-fix, pattern-codification]
surface: [registry, ci-tooling, test-infrastructure]
sister_specs: [meta-registry-pattern-for-codebase-registry-discipline.md, manual-fields-inventory-pattern.md, cross-walker-struct-field-uniqueness-discipline.md, bitmap-overflow-protection-discipline.md]
applies_at_skills: []
---

# Registry coverage CI check pattern

**Established:** 2026-05-16 (v5.15.5.F.4c.4 — retroactive extraction from 3 canonical applications)
**Status:** Stage 4 COHORT (2026-08-16). **The bump rests on the LANDED applications only** — Check 2 (App 1), Check 7 (App 2) and the NodeContext persist partition (App 4, tool shipped + wired at pre-commit Check Q). App 3's tool was never built (TD-274) and **App 5 is DESIGNED-NOT-LANDED**, so neither is part of the basis; the stage was already stale at 3 before this amendment (the lifecycle rule is ≥2 applications). Recorded explicitly because promoting a pattern on the strength of an unbuilt application is the exact over-read this spec's own Gotcha 1 warns about.
**Tags:** structural-fix, framework, ci-tooling, registry-discipline; closes Class 18/19/21/27/30; serves H15 (sister discipline)
**Cross-references:**
- `structural-fix-preferred-decision-framework.md` — parent family (this is a structural-fix mechanism via CI tooling)
- `pattern-codification-lifecycle.md` — canonical example of retroactive recognition + umbrella unification at 3rd canonical
- `meta-registry-pattern-for-codebase-registry-discipline.md` — orthogonal: H15 = registries enrolled in meta-registry; this = fields enrolled in registries
- `decision-time-data-binding-pattern.md` — sibling-array variant delegates CI discipline here (Check 8 closes Class 30 via this spec)
- `cfg-scope-discipline.md` — per-node cfg enrollment via Check 2 delegates here
- `manual-fields-inventory-pattern.md` — exemption mechanism (Section C precedent)
- `DOCS/RECURRING_BUG_PATTERNS.md` Class 18/19/21/27/30 — the bug classes this pattern's applications close
- CLAUDE.md item 19 (structural fix preferred when bug class can recur)
- CLAUDE.md item 31 (framework discipline meta-principle)
- CLAUDE.local.md going-forward rules: "Cohort-audit when new cfg field has 2+ siblings" + "Framework discipline over ad-hoc per-instance code when recurrence is foreseeable"

---

## Problem statement

A subsystem owns a canonical X-macro registry (`FOREACH_PER_CORE_CFG_FIELD`, `FOREACH_OMS_PER_SLOT_FIELD`, ...). The registry's value is that AUTOPOPULATE expansions walk it: parser, save/load, GUI render, init walk, drift check, snapshot emit, etc. **Adding a row to the registry gives free behavior expansion across all those surfaces.**

The recurring failure mode: a contributor adds a NEW field to the struct that the registry covers — but forgets to enroll the row. Code works locally because manual touch points (boot init, per-fill writes) handle the new field's needs directly. AUTOPOPULATE expansions silently skip it. Drift accumulates between struct reality and registry coverage. Behavioral failures appear later as latent bugs — fields missing from snapshots, GUI panels missing entries, drift checks failing to catch tampering, etc.

**Catalogued instances pre-codification:**

| Bug class | Site | Manifestation |
|---|---|---|
| Class 18 (mirror-incomplete) | Per-node cfg fields added without `PerCoreCfg<F>` enrollment | Per-node override silently NULL; falls back to global cfg |
| Class 19 (hardcoded enum names in gating) | Per-node capability not consulting `applies_to_*_cat` | Strategy capability checks drift from registry truth |
| Class 21 (cross-file cfg surface mismatch) | Cfg field in non-default cfg file without `lives_in_struct` tag | Parallel descriptor proliferation |
| Class 27 (scalar cfg-mirror cache) | Subsystem state caches cfg as scalar → per-instance flattening | Per-node fees collapse to core 0's value |
| Class 30 (sibling array without registry enrollment) | OmsState per-slot sibling array added but not in `FOREACH_OMS_PER_SLOT_FIELD` | AUTOPOPULATE silently skips the array; latent drift |

All five classes share the same root cause: **framework discipline broke at the human-vigilance layer at field-add time.** Manual review missed the registry enrollment step. The fix-class shape is identical: CI tooling that enforces struct↔registry consistency at build/CI time, with explicit-exempt mechanism for legitimately-special cases.

---

## The principle

**A canonical X-macro registry asserts a SHAPE about its target struct. A CI check ENFORCES that shape at build/CI time. The struct and the registry CANNOT silently drift apart — divergence fails the build, with an actionable error message pointing at the fix (enroll OR add to exemption list with rationale).**

The CI check is the structural fix that converts "human vigilance at field-add time" (failure-prone) into "build-time mechanical enforcement" (failure-impossible-without-explicit-bypass).

---

## Two variants

The pattern manifests in two variants distinguished by the DIRECTION of the assertion. Both share the same MECHANISM (Python tool template, exemption list mechanism, CI integration point, three-barrier structural-fix shape).

### Shape A — Positive coverage (struct → registry)

**Assertion:** every struct field matching predicate MUST be enrolled in the canonical registry, OR explicit-exempt with rationale.

**Used when:** registry rows expand via AUTOPOPULATE (parser / save / GUI render / init walk / drift check / snapshot emit / etc.) and adding a row gives free behavior expansion. The risk is a struct field existing but not getting the expansion → silent drift.

**Maturity:** Stage 3 ACTIVE (3 canonical applications: Check 2 + Check 8 + the NodeContext partition guard — note Check 8's TOOL was specified but never built, see Application 3's correction; the partition guard is the second Shape-A application with a shipping tool).

### Shape B — Anti-pattern enforcement (struct → forbidden pattern)

**Assertion:** every struct field MUST NOT match an anti-pattern shape, OR explicit-exempt with rationale category + migration trigger.

**Used when:** a bug class has been structurally closed (Class 27, H13, H14, etc.) and future contributors might re-introduce the anti-pattern. The risk is a new field re-introducing the closed bug class → CI fails the build.

**Maturity:** Stage 2 DRAFT (1 canonical application: Check 7). Variant-level promotion to Stage 3 awaits 2nd canonical (projected: scalar cfg-mirror extension to ConfidenceScorer / PortfolioController, OR H14 C++ bitfield syntax enforcement, OR H13 type-erased reinterpret_cast enforcement).

### Shape comparison

| Dimension | Shape A (positive coverage) | Shape B (anti-pattern enforcement) |
|---|---|---|
| Direction of assertion | Field MUST be in registry (or exempt) | Field MUST NOT match anti-pattern (or exempt) |
| Trigger surface | New AUTOPOPULATE registry introduced | New bug class structurally closed |
| Output on success | All struct fields covered | No struct fields match anti-pattern |
| Output on failure | "Field X exists but not in registry" | "Field X matches anti-pattern Y" |
| Exemption rationale | Special handling (e.g., dedicated clear helper) | Legitimate use case for the anti-pattern shape (e.g., decision-time-bound, cold-path-only) |
| Maturity at extraction | Stage 3 ACTIVE | Stage 2 DRAFT |

Both shapes share the same Python tool template + exemption list mechanism + CI fire point. The "what to check" varies; the "how to enforce" doesn't.

---

## Mechanism choice: compile-time vs runtime

Both Shape A (positive coverage) and Shape B (anti-pattern enforcement) can be enforced via two mechanism variants. The choice is **data-availability-driven**: compile-time when the source data is X-macro-driven; runtime Python tool when the source data is runtime-only (struct field grep, build artifact analysis).

### Compile-time variant — X-macro static_assert

**When to use:**
- Source data is X-macro-driven (`FOREACH_*` registry rows enumerable at compile time)
- Predicate can be expressed as X-macro reduction (bitmap OR, count, etc.)
- Result fits a single `static_assert(expr, message)` evaluable at compile time

**Mechanism:**
```cpp
// X-macro reduction gathers covered items via FOREACH expansion:
#define X_GATHER(...) | <bit-or-count-expr>
inline constexpr <type> COVERED = (0 FOREACH_<NAME>(X_GATHER));
#undef X_GATHER

// Exemption set (explicit; documented per-bit/row):
inline constexpr <type> EXEMPT = <bit-or-row-expr> | <...>;

// All items in use:
inline constexpr <type> ALL_IN_USE = <bit-or-row-expr>;

// Coverage assertion — build fails on violation:
static_assert(
    (ALL_IN_USE & ~(COVERED | EXEMPT)) == 0,
    "<violation description + actionable fix instruction>"
);
```

**Strictly better than Python CI tool when applicable:**
- **Build-fails** on violation — can't be bypassed (Python CI can be skipped via `--no-verify` or environment toggle)
- **Single file** — no separate `tools/` script to maintain or invoke
- **Aligns with existing codebase discipline** — X-macro static_asserts are canonical here (`bitmap-overflow-protection-discipline.md` HARD invariant + `CfgFieldRegistry.hpp:212` MetadataFlag overflow guard + `:959-962` descriptor array size guard + ~10 instances of `FOREACH_X_COUNT_ONE` reduction)
- **Error message at static_assert site** — easier to debug than parsing Python output; the violation message can include the specific bit/row name + actionable fix
- **No Python interpreter dependency** at CI time

**Canonical first application:** H16 enforcement at `v5.15.5.F.4d.1.A` — `CfgFieldDescriptor::MetadataFlag` bit coverage via `FOREACH_DERIVED_FILTER` reduction co-located in `CoreFrameworks/CfgFieldRegistry.hpp` (was originally planned as `.D` Check 9 Python tool; revised to compile-time at `.F.4d.1` planning per "compile-time mechanism preferred when source data X-macro-driven" amendment).

### Runtime variant — Python CI tool

**When to use:**
- Source data is NOT X-macro-driven (struct field declarations grepped from headers; build artifacts; cross-file consistency)
- Predicate requires regex or AST parsing (not expressible as compile-time reduction)
- Result depends on data that isn't constexpr-available

**Mechanism:** Python script under `tools/` per `## Detection shape` template below.

**Canonical applications:**
- **Check 7** (`tools/check_per_core_registry_integrity.py` Shape B): scalar cfg-mirror anti-pattern enforcement on subsystem struct fields — fields are flat declarations, NOT X-macro-driven; regex scan required.
- **Check 8** (`tools/check_per_core_registry_integrity.py` Shape A extension): OmsState per-slot sibling array coverage — array fields are flat declarations (not yet X-macro-driven); regex scan against `FOREACH_OMS_PER_SLOT_FIELD` body.
- **Check 10** (`tools/check_cohort_eligibility.py` Shape A; lands at `v5.15.5.F.4d.1.D`): cohort harmonization audit per `cfg-flag-eligibility-criteria.md` — heuristic grouping by section + cohort drift detection; not expressible as pure compile-time reduction.

### Mechanism choice decision matrix

| Question | Answer | Mechanism |
|---|---|---|
| Is the source data enumerable via `FOREACH_*` registry? | YES | **Compile-time static_assert** (preferred) |
| Is the source data struct-field-declared (not in X-macro)? | YES | Runtime Python tool |
| Is the predicate expressible as bitmask OR / count / equality? | YES + source X-macro-driven | **Compile-time static_assert** |
| Does the predicate require regex / AST / heuristic grouping? | YES | Runtime Python tool |
| Is performance / build-time cost a concern? | Build-time check has zero runtime cost | Either; compile-time slightly heavier at build, zero at run |
| Does the check need to fire in pre-commit hooks WITHOUT a build? | Pre-commit needs runtime mechanism | Runtime Python tool |

**Preference order:** compile-time first if data permits; runtime Python tool when compile-time not feasible.

---

## Trigger criteria

Apply this pattern when ALL conditions hold:

1. **Subsystem has a canonical X-macro registry** (e.g., `FOREACH_PER_CORE_CFG_FIELD`, `FOREACH_OMS_PER_SLOT_FIELD`, `FOREACH_OMS_FIELD`).
2. **Registry rows expand via AUTOPOPULATE** OR **the registry asserts a discipline shape** (e.g., "no scalar cfg-mirror caches").
3. **Struct field shape is identifiable via regex** (e.g., `\w+\[MAX_PORTFOLIO_POSITIONS\]` per-slot array, `[Ff]ee_rate\w*` for scalar cfg-mirror anti-pattern, `core_<F>` per-node field).
4. **Bug class exists** with ≥1 historical instance OR projected forward-risk (cohort audit finds latent instances OR pattern is being structurally closed).

If criteria 1-3 hold but 4 doesn't, **defer** — premature CI checks accumulate maintenance overhead without proportional value.

---

## Detection shape (the CI check itself)

A Python script under `tools/` that:

1. **Discovers source files** — glob list (e.g., `CoreFrameworks/OrderManager.hpp`, `Strategies/*.hpp`).
2. **Extracts target field shape from struct** — regex scan for field matches (e.g., `\bdouble\s+\w+\[MAX_PORTFOLIO_POSITIONS\]\b`).
3. **Extracts registry contents** — regex scan the X-macro definition for enrolled field names (e.g., parse the `FOREACH_OMS_PER_SLOT_FIELD(X)` body for `X(name[_i], type, init, reset)` tuples).
4. **Compares the two sets** — symmetric diff (Shape A) OR pattern-match diff (Shape B).
5. **Consults explicit-exempt list** — fields with rationale category + migration trigger (per `manual-fields-inventory-pattern.md`).
6. **Fails (exit nonzero) on unexpected diff** — actionable error message pointing at the fix.

### Output format template (failure case)

```
RED: <subsystem> registry-coverage check FAILED
  Registry: FOREACH_<X>
  Target struct: <struct_path>:<line>
  Field shape: <regex>

  [Shape A failure mode:]
  Found in struct but not in registry:
    - field_a (struct line 335)
    - field_b (struct line 411)
  Found in registry but not in struct:
    - field_c (registry line 322)

  [Shape B failure mode:]
  Anti-pattern match (FORBIDDEN shape detected):
    - field_x (struct line 502)
    - field_y (struct line 510)

  Exemption list (Section <X> in <inventory_path>):
    - field_d (rationale: SPECIAL_CLEAR_HELPER; migration trigger: registry gains 5th column for RESET_HELPER)

  Action: enroll [field_a, field_b] in FOREACH_<X> with appropriate INIT/RESET values
          OR add to Section <X> exemption list with rationale category + migration trigger
```

### Infrastructure shared across applications

- **Python tool template** — copy nearest sister check (e.g., `check_per_core_registry_integrity.py`); adjust field-shape regex + registry-content regex + exemption list path
- **Exemption list mechanism** — single canonical doc (`MANUAL_FIELDS_INVENTORY.md` or sister) with Section A/B/C/... per subsystem; rationale category + migration trigger required per exemption
- **CI integration point** — fire in pre-commit hook + Step 0.A build verification (sister to existing Check 2 + Check 7)

---

## Anti-patterns

### Anti-pattern 1 — Runtime check instead of CI-time

Checking at engine boot doesn't prevent the bug class from shipping. By the time the check fires, the violation is already merged. CI-time fail catches it pre-merge — the only point at which prevention is structural rather than detective.

### Anti-pattern 2 — Coverage check without exemption mechanism

Some fields legitimately need special handling (e.g., `OmsState::last_exit_predicted_meta` uses dedicated `OMS_META_CLEAR` helper because its per-slot clear semantics differ from the standard `FOREACH_OMS_PER_SLOT_FIELD` reset). Without an exemption mechanism, the CI check becomes too rigid → gets disabled → discipline silently rots. Exemption list is load-bearing.

### Anti-pattern 3 — Exemption without rationale categories

Silent exemptions accumulate over time. Future maintainers can't tell which exemptions are legitimately permanent vs which were defer-decisions awaiting migration. Mandate: every exemption entry has a **rationale category** (named taxonomy) + **migration trigger** (concrete event that would close the exemption).

Example exemption entry format (from Check 7 Section C precedent):
```
- field_name: <name>
  rationale: <category>  (e.g., DECISION_TIME_BOUND / COLD_PATH_OK / SPECIAL_CLEAR_HELPER / TRANSITIONAL_DELETION_SCHEDULED)
  migration_trigger: <event>  (e.g., "registry gains 5th column for RESET_HELPER" / "PerCoreOverrides<F> deletion at WIP2f")
  added: <ship>
  notes: <free-form context>
```

### Anti-pattern 4 — Auto-generating the registry from struct

Defeats the entire point. The registry needs to be authored EXPLICITLY because the discipline is encoded at the registry definition (which AUTOPOPULATE expansions consume + which the CI check enforces). Auto-generating from struct means the struct is canonical — same drift class re-emerges in a different shape (struct fields and the auto-gen tool's predicate logic can drift).

### Anti-pattern 5 — Single tool for all subsystems

Reuse-by-copy-paste over a tool template is fine; ONE monolithic tool that handles every subsystem's checks accumulates complexity + slows the per-subsystem check turnaround. Each subsystem gets its own `tools/check_<subsystem>_registry_integrity.py` (or Section in a per-domain script — e.g., `check_per_core_registry_integrity.py` houses both Check 2 + Check 7 because both share PerCoreCfg domain).

---

## Canonical applications (3 at extraction time)

### Application 1 — Check 2: Per-node cfg field enrollment (Shape A)

**Shipped:** v5.15.5.F.4c.3 (2026-05-15)
**Target struct:** `PerCoreCfg<F>` (in `CoreFrameworks/PerCoreCfg.hpp`)
**Registry:** `FOREACH_PER_CORE_CFG_FIELD`
**Field shape:** explicit per-cfg field on PerCoreCfg<F>
**Tool:** `tools/check_per_core_registry_integrity.py` (Section A logic)
**Closes:** Class 18 (mirror-incomplete) + Class 19 (hardcoded enum names) + Class 21 (cross-file cfg surface mismatch)
**Exemption mechanism:** none — full coverage required (all per-node cfg fields must be enrolled; no exemptions)
**Failure mode prevented:** per-node override silently NULL when caller code reads `core_cfg->X` for a field that's in `cfg.X` but not in PerCoreCfg<F>

### Application 2 — Check 7: Scalar cfg-mirror anti-pattern enforcement (Shape B)

**Shipped:** v5.15.5.F.4c.3 WIP2d-1.B.0c (2026-05-15)
**Target struct:** `OmsState` (scalar cfg-mirror fields specifically)
**Registry:** N/A — anti-pattern enforcement (no positive registry to match against)
**Field shape:** scalar fields on subsystem state matching `<subsystem>->fee_rate_<X>` / `<subsystem>->slippage_<Y>` / similar (cfg-mirror anti-pattern shape)
**Tool:** `tools/check_per_core_registry_integrity.py` (Section C logic) + `tools/scan_class_27_full.py` (codebase-wide complement)
**Closes:** Class 27 (scalar cfg-mirror cache)
**Exemption mechanism:** `MANUAL_FIELDS_INVENTORY.md` Section C — rationale categories (DECISION_TIME_BOUND, COLD_PATH_OK, TRANSITIONAL_DELETION_SCHEDULED) + migration triggers
**Failure mode prevented:** per-instance cfg values flattening to core 0's values when subsystem caches them as scalars

### Application 3 — Check 8: OmsState per-slot sibling array enrollment (Shape A) — NEW at .F.4c.4

**Shipping:** v5.15.5.F.4c.4
**Target struct:** `OmsState` (per-slot sibling arrays specifically)
**Registry:** `FOREACH_OMS_PER_SLOT_FIELD` (at `MemHeaders/OmsFieldRegistry.hpp:321`)
**Field shape:** `\w+\[MAX_PORTFOLIO_POSITIONS\]` arrays in OmsState
**Tool:** `tools/check_oms_per_slot_registry_integrity.py **[NEVER BUILT — TD-274]**` (NEW at .F.4c.4)
**Closes:** Class 30 (sibling array without registry enrollment)
**Exemption mechanism:** explicit-exempt list within the tool — rationale categories (currently: SPECIAL_CLEAR_HELPER for `last_exit_predicted_meta[16]` which uses dedicated `OMS_META_CLEAR` helper)
**Failure mode prevented:** AUTOPOPULATE expansions (init walk, post-fill reset, snapshot skip) silently skipping fields that physically exist as per-slot arrays
**Canonical first-fix instance:** `OmsState::last_exit_fee[MAX_PORTFOLIO_POSITIONS]` (added at v5.15.5.F.4c.3 WIP2d-1.B.1 but never enrolled in `FOREACH_OMS_PER_SLOT_FIELD` — latent drift surfaced at .F.4c.4 verification pass; enrolled simultaneously with new `bandit_reward_bps[_i]` row)


⚠ **CORRECTION 2026-08-15 (D-421):** `tools/check_oms_per_slot_registry_integrity.py **[NEVER BUILT — TD-274]**` **does not
exist** — it was never written. Nine sites across four documents (including this spec's Tool row,
its copy-me-template list, its Stage-6 "three canonical CI tools exist" claim, and Class 30's
frontmatter `closure_mechanism`) assert that it does. **Class 30 is therefore documented as
structurally closed by nothing.** The class is not currently violated — `OmsState` has 6 per-slot
arrays, 5 enrolled and 1 carrying the `OMS_META_CLEAR` exemption (verified, not assumed) — but by
nobody-having-added-one, not by enforcement. Tracked `TECH_DEBT-274`; the real close is D-421's
DOMAIN column, which generalises this check to all enrolled registries rather than adding a 9th
bespoke guard. Application 3 is retained here as a DESIGN that was specified and not built.

---

### Application 4 — the NodeContext persist partition (Shape A) — NEW at E.1.2 / D-421

**Shipping:** v5.15.5.F.4d.1.E.1.2
**Target struct:** `NodeContext<F>` (`CoreFrameworks/ControllerEventLoop.hpp`) — 49 members, hand-declared
**Registry:** `FOREACH_NODE_PERSIST_FIELD` (`MemHeaders/NodeCtxPersistRegistry.hpp`) — 29 wire rows
**Field shape:** every struct member (clang `-fdump-record-layouts`, not a regex — see below)
**Tool:** `tools/check_node_ctx_partition.py` (NEW; 17 teeth) — **the first application that actually ships a tool since Check 2/Check 7**
**Closes:** the silent-field-drop class (`TECH_DEBT-196`; founding instance `node_gross_wins` added v4.7.25, never persisted, Stats read $0.00 after every restart until v5.4.3)
**Exemption mechanism:** `FOREACH_NODE_CTX_PERSIST_EXEMPT(NAME, CATEGORY, "rationale")` — a **closed category set** with a mandatory prose rationale, plus an always-RED category (`UNESTABLISHED_UNTIL_FIRST_PASS`) that records a known-bad state without excusing it
**Measured at landing:** 49 members, 27 covered, 22 exempt-pending

**Three things this application adds to the pattern, each earned by a real failure:**

1. **The field shape is COMPILER-DERIVED, not regex-derived.** Applications 1–3 identify members by
   a name pattern (`\w+\[MAX_PORTFOLIO_POSITIONS\]`). That works only where the cohort is
   textually distinctive. A *whole struct's* membership is not — so this one reads the real layout
   from clang and subtracts the registry. Regex would have missed exactly the fields that matter
   (a `void*`, a sub-struct, a plain `uint16_t`).
2. **Three RED directions, not one.** Anti-pattern 2 says "coverage check without exemption
   mechanism"; this adds that an exemption list is itself an input that can rot. **STALE-EXEMPT** (an
   exemption naming a non-member) is the sharp one: it makes the partition read as fully accounted
   while covering a ghost, and it is what catches the "silence the red by bulk-exempting" move —
   one typo in the bulk list still REDs. **CONTRADICTION** (both persisted and exempt) refuses to
   guess which declaration is the lie.
3. **The category vocabulary must be FALSIFIABLE, and was corrected BY verification.** Anti-pattern 3
   says "exemption without rationale categories". Not sufficient — the `ic.actuals` bug had a stated
   reason, documented in the header, that was true of the push path and false across the persist
   boundary. Verifying all 22 fields **refuted two of the four categories originally drafted**
   (`WALL_CLOCK` — the field it obviously fits is safe for the *opposite* reason, and accepting it
   would enshrine a false premise; `DISPLAY_ONLY` — the field it obviously fits fires a real
   MARKET_SELL). Categories now phrase the evidence that would refute them, e.g. `DERIVED_EACH_PASS`
   must answer *"what reads it before the FIRST derive?"* — the single question separating a safe
   field from the one genuinely-broken one on that shard.

**What the application produced beyond coverage:** three engine defects, found by *verifying* the
exemption reasons rather than accepting them — a capital control that silently disarmed, an
indeterminate cross-thread read, and an observability channel that had never worked. That is the
argument for the pattern at large: the check is cheap, and the act of justifying each exemption is
where the findings actually come from.

### Application 5 — stamp emit-producer coverage (Shape A, **compile-time variant**) — DESIGNED at E.1.2 / D-421 step 6

> ⚠ **STATUS: DESIGNED, NOT LANDED (2026-08-16).** Gated on an in-flight adversarial pass and on a
> fix/delete pass that must precede it. **This block is written in the DESIGN tense on purpose** —
> Application 4 above cites a sister tool marked `[NEVER BUILT — TD-274]`, and this spec has already
> paid once for describing a mechanism as though it existed. Nothing here may be cited as shipped
> until the `static_assert`s are in the tree. Gotcha 1 ("don't extract too early") applies to the
> *claim*, not the design: the design is recorded now because the next session needs the reasoning,
> not because the work is done.

**Target domain:** `enum StampHasFlagBit` (`ML_Headers/StampBoundModelConstRegistry.hpp:537-573`) — 24 bits
**Registry:** `FOREACH_STAMP_BOUND_MODEL_CONST` rows (48) → bits via the `group` column + standalone names
**Producer root:** `tt::Stamp_AssembleAndEmit` (`ML_Headers/StampHelper.hpp:179`) — the single production emit funnel
**Mechanism:** compile-time `static_assert` (this spec's own § "Mechanism choice decision matrix" resolves it: *enumerable via `FOREACH_*` → compile-time preferred*)
**Closes:** the group/standalone bit with no emit-side producer — measured **8 of 24** unreachable at HEAD, incl. `feature_mask`, whose parity-critical `r.valid = 0` REFUSE (`ML_Headers/ModelInference.hpp:1880-1893`) has never fired (0 of 16 on-disk stamps carry the key; control `label_registry_hash` is 16/16)

**Three things this application adds to the pattern, each earned by a real failure:**

1. **The marker must BE the code, not point at it.** The obvious design — require a
   `STAMP_EMIT_PRODUCER_<G>` marker per group — is a **Class-18 mirror**: a marker row and the
   population code are two places, so a row can claim a producer that does not exist and stay green
   forever. The working shape puts the *population statements themselves* in the sidecar row
   (`X(BIT, GATE_EXPR, ...statements...)`, variadic so commas in `memcpy(a,b,n)` survive) and expands
   it AS the assembler body. **Deleting the row deletes the code**, so a row cannot lie. Generalizes
   beyond stamps: *a coverage registry over BEHAVIOUR must own the behaviour, not assert about it.*
2. **Verify the guard does not ALREADY exist — the first sketch was a no-op.** The proposed
   "adding a group without a producer must not compile" is **already true at HEAD**: the emit walk
   token-pastes `STAMP_EMIT_CHECK_HAS_##group` (`ML_Headers/ModelInference.hpp:2259`), so an
   undefined dispatcher is an undeclared identifier. Verified by construction — group values used in
   rows are *exactly* the set of `STAMP_EMIT_CHECK_HAS_*` defines, and the build is green. The real
   gap is one level down and is **not preprocessor-visible**: whether the hand-written assembler
   body ever calls `STAMP_SET`. **Before adding a coverage guard, establish what the existing
   dispatch already enforces** — otherwise the new guard is ceremony over a closed hole.
3. **Derive the domain from the ENUM / use-site, never from a coverage list that is itself
   uncovered.** Both `FOREACH_..._GROUPS` (`:241-247`, 6 rows for 7 group bits) and
   `FOREACH_..._STANDALONE` (`:260-267`, 6 real of 17, plus a phantom `bandit` row with no
   `MASK_bandit` anywhere) are **decorative** — their only consumers are two vacuous `>=` test
   bounds. A guard deriving its universe from them scans **13 of 23** bits and reports clean. That is
   Class 58 sub-shape A sitting *inside* the fix for sub-shape B. Delete them rather than repair
   them; a repaired-but-decorative list reintroduces the mirror.

**A fourth lesson, about the ORACLE rather than the registry — structural beats corpus.** An
empirical count over emitted artifacts said 10 bits were unproduced; the structural count says **8**.
The 2 extra (`fees`, `inference_cfg_bandit_blend_ratio`) have *legitimate conditional* producers
(`StampHelper.hpp:249-254`, gated on `MASK_ML_CFG_BANDIT_ENABLED` / `MASK_GATE_CFG_COST_GATE_ENABLED`)
and are absent from the corpus only because those cfg flags were off when the corpus was written.
**A corpus-derived guard REDs on correct code; the compile-time guard greens it.** Generalizes:
*when a guard can be built on either the code or its output, the code is the sounder oracle — output
is a sample of one configuration.* (Sister caution: the corpus here is also 3 months stale, so it
could not testify about HEAD in either direction.)

**Why this is a compile-time application and not a Python tool.** Every text-based approach to this
surface was tried and failed: producers take ≥5 syntactic forms, 12 mask families are token-paste
fragments, and the decisive `STAMP_SET((inf), bit)` form defeats a `[^)]*` argument match. The
preprocessor resolves all of it for free. This is the decision matrix's *"enumerable via `FOREACH_*`"*
row arriving with evidence.
---

## How to add a new application

1. **Verify trigger criteria** — all 4 conditions hold (registry exists, AUTOPOPULATE-bearing, regex-identifiable field shape, bug class with ≥1 instance OR forward-risk).
2. **Determine variant** — Shape A (positive coverage) OR Shape B (anti-pattern enforcement).
3. **Author the canonical registry** if Shape A and not already present; OR identify the anti-pattern shape if Shape B.
4. **Write the CI check Python script** — copy nearest sister tool as template (`check_per_core_registry_integrity.py` for Shape A + Shape B; `check_oms_per_slot_registry_integrity.py **[NEVER BUILT — TD-274]**` for per-slot Shape A); adjust:
   - File glob (which sources to scan)
   - Field-shape regex (the predicate)
   - Registry-content regex (Shape A only)
   - Anti-pattern regex (Shape B only)
   - Exemption list path + rationale categories
   - Output error message template
5. **Add to CI pipeline** — fire in pre-commit hook OR Step 0.A build verification (sister to existing Check 2 + Check 7 + Check 8). Document where in the ship's plan.
6. **Document exemption list location** in CI check output AND canonical inventory doc (`MANUAL_FIELDS_INVENTORY.md` or sister with Section per subsystem).
7. **Codify closed bug class** in `DOCS/RECURRING_BUG_PATTERNS.md` (if not already documented) with cross-ref to this spec.
8. **Add row to § "Canonical applications"** in this spec at ship close.
9. **Variant-level Stage promotion** if 2nd canonical of Shape B lands — promote Shape B variant from Stage 2 DRAFT to Stage 3 ACTIVE within this spec.

---

## Pattern lifecycle position

- **Stage 0 (identification)** — recurring "field added without registry enrollment" failures observed across Class 18 / 19 / 21 / 27 / 30
- **Stage 1 (pre-codification audit)** — codebase scan found ≥1 instance per class
- **Stage 2 (DRAFT spec)** — skipped via retroactive extraction (3 canonical apps existed in code before spec was written)
- **Stage 3 (ACTIVE)** — extracted at v5.15.5.F.4c.4 from 3 canonical apps (Check 2 + Check 7 + Check 8); ACTIVE for Shape A; DRAFT for Shape B (per-variant Stage tracking inside spec body)
- **Stage 4 (subsequent applications)** — projected: Shape A extensions (STAMP_BOUND drift-row coverage, AUTOPOPULATE parser↔GUI parity, ML FeatureRegistry stamp emission, Strategy enum/dispatcher coverage); Shape B extensions (scalar cfg-mirror to ConfidenceScorer/PortfolioController, H14 bitfield enforcement, H13 reinterpret_cast forbidden, H4 FPN_Binary-on-accounting enforcement, PerCoreOverrides<F> FORBIDDEN check)
- **Stage 5 (CLAUDE.md cross-link + invariant promotion)** — candidate H21 invariant: "Every framework-eligible field is enrolled in its canonical registry, OR explicit-exempt with rationale category + migration trigger." Promotion criteria: 2+ subsystems with Shape A CI check OR Shape B's 2nd canonical lands. Deferred for now.
- **Stage 6 (tooling enforcement)** — three canonical CI tools exist at extraction time (`check_per_core_registry_integrity.py`, `scan_class_27_full.py`, `check_oms_per_slot_registry_integrity.py **[NEVER BUILT — TD-274]**`); future apps add per-subsystem scripts
- **Stage 7 (wider audit + cohort migration)** — `/dod-audit` baseline scan picks up "FOREACH_*" registries codebase-wide and surfaces enrollment gaps as cohort-audit candidates

---

## Audit detection

`/dod-audit` and `/registry-fit-audit` can detect candidate applications by:

- Grepping for `FOREACH_*(X)` X-macro registry definitions
- For each registry, identifying the target struct (usually the struct whose fields appear in registry rows)
- Comparing struct field shape (regex over `[MAX_PORTFOLIO_POSITIONS]` arrays / per-node fields / etc.) against registry contents
- Flagging cases where struct fields exist that match the shape but aren't in the registry → candidate Shape A application
- Cross-referencing closed bug classes (Class 27 etc.) for shape patterns → candidate Shape B application

Skill output template for surfacing candidates:
```
FINDING: <subsystem> may benefit from registry-coverage CI check (Shape A)
  Registry: FOREACH_<X> (file:line)
  Target struct: <struct> (file:line)
  Coverage gap detected: <N> field(s) match shape but not enrolled
  Suggested: add tools/check_<subsystem>_registry_integrity.py per registry-coverage-ci-check-pattern.md
```

---

## Patterns NOT used here (rejected alternatives)

### Rejected — Single unified registry-of-registries CI check

Considered: one mega-tool that scans every X-macro registry in `FOREACH_REGISTRY` and verifies coverage. Rejected because:
- Each registry has different field-shape predicates (regex differs per registry)
- Failure modes need subsystem-specific actionable messages
- Per-subsystem tools are simpler + faster + maintainable independently
- The `FOREACH_REGISTRY` meta-registry (H15) handles the ORTHOGONAL discipline (every registry enrolled in meta-registry); this spec handles the PERPENDICULAR discipline (every field enrolled in its registry)

### Rejected — Build-time static_assert instead of CI Python tool

Considered: pure-C++ static_assert that counts struct fields matching predicate vs registry COUNT. Rejected because:
- C++ doesn't have introspection-by-regex on struct fields (no AST access in template metaprogramming)
- Field counts alone aren't sufficient — need name-level diff for actionable error messages
- Static_assert at struct definition site can't pull from registry definition site cleanly
- Python tool is simpler + more flexible + faster to iterate

(Sister discipline: `bitmap-overflow-protection-discipline.md` DOES use static_assert because it checks count overflow, not field-level enrollment.)

### Rejected — Manual code review checklist

The whole point is that human vigilance failed. A checklist depends on the same vigilance.

---

## Trade-offs + when to apply

### Apply when:

- New X-macro registry introduced with AUTOPOPULATE-bearing expansions
- New bug class structurally closed where future contributors could re-introduce it
- Bug class has ≥1 historical instance OR projected forward-risk
- Subsystem has clearly identifiable field shape that grep/regex can match

### Don't apply when:

- Registry is closed / locked / will never grow (no future enforcement need)
- Field shape isn't regex-identifiable (too much ambiguity to write a useful check)
- Subsystem is single-instance with all fields hand-authored (no AUTOPOPULATE → no drift risk)
- Bug class hasn't occurred + isn't projected (don't accumulate maintenance overhead preemptively)

### Costs

- ~30 min to write a new per-subsystem CI check from template
- ~5 min per ship to maintain exemption list (review entries, update migration triggers)
- ~1 min per CI run to execute the check
- Per-subsystem script proliferation (one file per check) — acceptable; each is small

### Benefits

- Structural fix: bug class cannot recur without explicit bypass
- Documentation: exemption list captures legitimate edge cases with rationale
- Discoverability: contributor adding a field sees CI failure immediately, knows to enroll OR document exemption
- Cohort migration: when an exemption's migration trigger fires, all exemptions in that category get re-evaluated together

---

## Lessons + gotchas

### Lesson 1 — Retroactive recognition is valid spec extraction

This spec was extracted retroactively from 3 canonical apps already in code (Check 2 + Check 7 at .F.4c.3; Check 8 at .F.4c.4 in-flight). Per `pattern-codification-lifecycle.md`, retroactive extraction is legitimate when the meta-pattern has matured to 2+ apps; the spec captures what's already canonical practice. Compare: `decision-time-data-binding-pattern.md` extracted retroactively at .F.4c.3 after Class 27 closure recognized the cross-cutting pattern.

### Lesson 2 — Per-variant Stage tracking inside one spec is the cleanest organization

Shape A (Stage 3 ACTIVE) and Shape B (Stage 2 DRAFT) live in the same spec because they share infrastructure. Documenting maturity per-variant inside the spec is more honest than:
- Forcing Shape B into a parallel sister spec (premature extraction; spec proliferation)
- Asserting unified Stage 3 ACTIVE for the whole spec (overstates Shape B's maturity)

### Lesson 3 — The exemption list is load-bearing

Without exemption mechanism, the CI check becomes rigid → gets disabled when first legitimate edge case appears → discipline silently rots. The exemption list with rationale category + migration trigger is what makes the check sustainable.

### Lesson 4 — The CI check fix-shape composes the three-barrier structural-fix pattern

Each canonical application follows the three-barrier shape (per Class 23 prevention precedent):
- **Barrier 1: direct fix** at the canonical instance site (e.g., enroll `last_exit_fee` in `FOREACH_OMS_PER_SLOT_FIELD`)
- **Barrier 2: structural fix** via CI check (e.g., new `tools/check_oms_per_slot_registry_integrity.py **[NEVER BUILT — TD-274]**`)
- **Barrier 3: pattern codification** via bug class entry + spec amendment (e.g., Class 30 in RBP + this spec)

The three-barrier shape ensures the class cannot recur without explicit suppression at multiple points.

### Gotcha 1 — Don't extract too early

Pattern lifecycle says 2+ canonical apps before spec extraction. THIS spec qualifies (3 apps). A single CI check is NOT spec-worthy — capture the pattern locally in the application's commit message + bug class entry, then extract when 2nd application lands.

### Gotcha 2 — Tool template drift between sister apps

When copying a sister tool as template (e.g., `check_per_core_registry_integrity.py` → `check_oms_per_slot_registry_integrity.py **[NEVER BUILT — TD-274]**`), the templates can drift over time as one gets updated and the other doesn't. Mitigation: keep the template-shared logic in a shared module (`tools/_ci_check_shared.py`) if drift becomes an issue. Currently acceptable at 2 tools; reconsider at 4+.

### Gotcha 3 — Auto-write contract: keep canonical applications table updated

Every new application MUST add a row to § "Canonical applications" at ship close. Without this auto-write contract, the spec drifts from reality.

---

## CLAUDE.md cross-link target

Pattern documented in `DESIGN_SPECS/framework-patterns/registry-coverage-ci-check-pattern.md`.

Promotion to CLAUDE.md item criteria:
- 2+ Shape A subsystems with CI checks (currently met: Check 2 + Check 8)
- Shape B's 2nd canonical (currently 1 canonical: Check 7)
- Both criteria met → CLAUDE.md item promotion via candidate H21 invariant

Defer CLAUDE.md item creation until Shape B's 2nd canonical lands (per pattern-codification-lifecycle "2+ applications" rule applied per-shape).

---

## Auto-write contract at ship close

When a sub-ship adds a new application of this pattern:

- [ ] New row in § "Canonical applications" (variant + struct + registry + tool + classes closed + exemption mechanism)
- [ ] New bug class entry in `DOCS/RECURRING_BUG_PATTERNS.md` (if not already documented)
- [ ] Cross-reference from the new bug class entry to this spec
- [ ] If Shape B 2nd canonical: promote Shape B variant from Stage 2 DRAFT to Stage 3 ACTIVE in this spec
- [ ] If 4+ subsystems or template drift observed: extract `tools/_ci_check_shared.py` shared-logic module
