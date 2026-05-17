# D4 audit — DESIGN_SPECS spec-vs-code drift scan

**Sprint:** v5.15-live-readiness
**Sub-ship:** v5.15.5.F.4d.1.A
**Engine HEAD at scan:** `545b0879948a0893f806dc6afe7992968acd57e3` (tag `v5.15.5.F.4d`)
**Scan date:** 2026-05-16
**Auditor:** Level 4 codebase pattern survey (D4 — partial down-payment on TECH_DEBT-089)
**Methodology:** Sample-based ~5-min skim per spec; verify cited mechanism (function names / struct names / registry names / X-macro names) against engine HEAD via `rg`/`find`. Prioritized Thread A specs (most recent codifications) + 2 NEW specs from `.F.4d.1.A` + Stage 2→3 promotions from `.F.4c.3`.

---

## TL;DR

| Metric | Count |
|---|---|
| Total DESIGN_SPECS in workspace | 76 |
| Audited in this D4 pass | 14 (~18% sample) |
| ALIGNED (spec matches HEAD) | 7 |
| DRIFT-MINOR (small mismatch; spec needs amendment) | 2 |
| DRIFT-MAJOR (named mechanism missing / wrong abstraction) | 3 |
| PROMOTION-PREMATURE (Stage 3 ACTIVE claim without first-canonical landing) | 2 (overlap with DRIFT-MAJOR) |
| Self-flagged-corrections-in-progress | 2 (metadata-bit-driven-derived-filter + framework-composition-overview — already mark v1.x Path γ correction in progress) |

**Overall verdict:** **YELLOW** — process discipline at planning-session-time has been catching most drift, BUT 2-3 specs slipped past with aspirational Stage 3 promotions OR canonicals-count inflation. The drift pattern matches the metadata-bit case: spec is drafted at planning time projecting where the ship WILL land; reconciliation back to spec at actual ship close is missed; spec then misleads downstream consumers.

**Recommendation:** TECH_DEBT-089 full sweep (remaining 60+ specs) **is warranted** but lower priority than (a) closing the drift on the 3 DRIFT-MAJOR specs identified here, AND (b) instituting a `/ship` skill auto-step that walks specs cited in plan body + verifies their Stage tracker against actual code landed.

---

## Per-spec verdicts

### Tier 1 — Thread A (`.F.4d` planning codifications)

#### 1. `metadata-bit-driven-derived-filter-framework.md`
**Verdict: SELF-FLAGGED (v1.2 Path γ correction in progress)** — known baseline case that triggered this audit.
- Stage 3 ACTIVE promotion at `.F.4d` was ASPIRATIONAL; STAMP_BOUND_CFG_DERIVED bit was reserved but NO derived filter framework was built.
- v1.0/v1.1 mechanism (Option B runtime walk + 3 macro variants) SUPERSEDED by Option E (existing `FOREACH_METADATA_BIT` + `cfg_compute_mask` + `CFG_FIELD_FOR_EACH_SET_BIT` at `CfgFieldRegistry.hpp:1020-1159`).
- Status banner is correct + remediation pointer to `2026-05-16-v5.15.5.F.4d.1-tech-debt-audit-findings.md` is in place.
- Pending: full doc cleanup at `.F.4d.1.A` ship close (Phase 1i task).

#### 2. `framework-composition-overview.md`
**Verdict: SELF-FLAGGED (v1.1 Path γ correction in progress)** — sister to #1.
- Topology diagram references `DerivedFilterRoster.hpp` / `FOREACH_DERIVED_FILTER` Level-1 meta-registry that doesn't exist.
- `CFG_FIELD` row in topology mentions "single source of truth" but code split that into `FOREACH_GLOBAL_CFG_FIELD` + `FOREACH_PER_CORE_CFG_FIELD` at `.F.4c.3` (current actual single-source-of-truth is the union of the two; topology diagram still shows the pre-split shape).
- Status banner correctly flags pending rewrite at `.F.4d.1.A` ship close.

#### 3. `sidecar-override-pattern-for-registry-auto-flows.md`
**Verdict: DRIFT-MAJOR / PROMOTION-PREMATURE** — newly identified.
- Status line: "**Stage 3 ACTIVE v1.0** (first canonical reference application landed at v5.15.5.F.4d ship close 2026-05-16; FOREACH_DRIFT_OVERRIDE sparse sidecar indexed by parent FIELD_IDX scheme — 5 XGBoost training-only fields canonical at `CfgDriftCheckRegistry.hpp:202-221`)"
- **Actual code:** `rg "FOREACH_DRIFT_OVERRIDE|struct DriftOverride|g_global_drift_overrides|g_per_core_drift_overrides"` returns ZERO matches in any `.hpp` file.
- `Version.hpp:79-80`: *"canonicals 6/7/8 (DriftOverride / RegistryRosterEntry / ManualFieldInventoryEntry) defer to TECH_DEBT-085 along with FOREACH_DRIFT_OVERRIDE sidecar."*
- **Nature of drift:** spec claims Stage 3 ACTIVE with file:line refs to existing wide-variant rows, but no migration occurred at `.F.4d` ship. Spec is sister to `metadata-bit-driven-derived-filter-framework.md` — both had aspirational Stage 3 promotions at `.F.4d` planning that didn't ship.
- **Fix:** banner correction + status downgrade to "Stage 2 DRAFT; awaiting first canonical at `.F.4d.1` (TECH_DEBT-085 scope)".

#### 4. `meta-registry-pattern-for-codebase-registry-discipline.md`
**Verdict: DRIFT-MAJOR** — partial truth, but tuple shape + filename mismatch.
- Status: "Stage 3 ACTIVE v1.0 — first canonical at `.F.4c.3` WIP2d-0.B (`FOREACH_PER_CORE_DOMAIN_BITMAP`); second canonical at `.F.4d`."
- **Verified:** `FOREACH_REGISTRY` DOES exist at `CoreFrameworks/MetaRegistry.hpp` (lines 35-65; ~25-30 rows enrolled).
- **Drift A (filename):** spec cites `CoreFrameworks/RegistryRoster.hpp` — actual file is `CoreFrameworks/MetaRegistry.hpp`. Same content; just renamed.
- **Drift B (tuple shape):** spec shows 8-column tuple `(NAME, source_file, LEVEL, PARENT, design_spec, BUG_CLASS, WIRE_FORMAT_KIND, doc)` — actual is 4-column tuple `(NAME, LEVEL, PARENT, doc)`. The 4 missing columns (source_file / design_spec / BUG_CLASS / WIRE_FORMAT_KIND) were dropped at implementation time but spec was not updated. Significant: future contributors reading the spec would attempt to add 8 columns; build would fail with cryptic macro errors.
- **Drift C (sister-meta absence):** spec references `FOREACH_DERIVED_FILTER` Level-1 meta-registry as "managed by THIS spec's Level-2 FOREACH_REGISTRY"; that Level-1 meta-registry doesn't exist (it's the sibling of #3 drift above).
- **Fix:** rewrite `## Per-row data struct` + `## FOREACH_REGISTRY tuple` sections to match actual 4-column shape + update filename references.

#### 5. `composed-filter-mask-pattern.md` (NEW at `.F.4d.1.A`)
**Verdict: ALIGNED**
- Spec claims 3 canonicals at `CfgFieldRegistry.hpp:1162-1257`: `render_mask` / `save_mask` / `cli_explain_mask`.
- **Verified at HEAD:** `cfg_compose_global_render_mask` / `g_global_cfg_render_mask` / sibling `_save_mask` / `_cli_explain_mask` + per-core analogues exist at expected file:line range.
- Sample live consumer at `SettingsPanel.hpp:1100,1136` — spec citation matches.

#### 6. `wire-format-canonical-body-invariants-helper.md` (NEW at `.F.4d.1.A`)
**Verdict: ALIGNED (Stage 2 DRAFT pre-canonical, as declared)**
- Status: Stage 2 DRAFT v1.0 → Stage 3 first reference at `.F.4d.1.A` ship (STAMP_BOUND_CFG_DERIVED first canonical).
- `run_wire_format_canonical_body_invariants` + `tests/wire_format_invariants.hpp` do NOT yet exist — spec correctly self-flags this is pre-canonical.

### Tier 2 — Recent `.F.4c.3` + `.F.4d` codifications

#### 7. `multi-state-dispatch-with-per-state-update-metadata.md`
**Verdict: ALIGNED with minor cosmetic mismatch**
- Status: Stage 2 DRAFT → Stage 3 ACTIVE at `.F.4d` ship close.
- **Verified:** `FOREACH_BANDIT_ALGORITHM` exists with 5 states (EXP3 / THOMPSON / EXP3_OP_THOMPSON_GHOST / THOMPSON_OP_EXP3_GHOST / BLENDED); `g_buy_reward_dispatch` + `g_exit_reward_dispatch` auto-derived dispatch tables at `ML_Headers/bandit_dispatch_table.hpp`.
- **Cosmetic drift:** spec uses generic function names `BanditAlgo_Exp3_Apply` / `BanditAlgo_Thompson_Apply` / `BanditAlgo_Blended_Apply`. Actual code uses dispatch-table function-pointer fields; the per-algorithm reward functions are named differently (e.g., `Exp3IXBandit_Update`, `ThompsonBandit_Update`). Pattern structure is correct; names are illustrative.

#### 8. `multi-bit-state-encoding-pattern.md`
**Verdict: DRIFT-MINOR / inflated canonicals count**
- Status: INVARIANT (post-`.F.4d` ship; **5 canonical applications**: EVENT_LOG_MODE + DriftOverride + RegistryRosterEntry + ManualFieldInventoryEntry + Order::flags_packed bandit context bits 17-25).
- **Verified at HEAD:** EVENT_LOG_MODE (`OmsStateFlagRegistry.hpp:167`) + Order::flags_packed bandit bits (`Order.hpp:108`) — 2 actual canonicals.
- **Missing:** DriftOverride / RegistryRosterEntry / ManualFieldInventoryEntry structs DO NOT exist (deferred to TECH_DEBT-085 = `.F.4d.1`).
- **Nature of drift:** spec promoted to INVARIANT status counting 5 canonicals but only 2 shipped. Spec is correct in describing the pattern; the count inflation distorts the "INVARIANT" status decision (the pattern threshold for invariant promotion per `pattern-codification-lifecycle.md` is ≥3 canonicals).
- **Fix:** downgrade count to 2 canonicals + update INVARIANT status to "Stage 5 candidate; full INVARIANT promotion deferred to `.F.4d.1` close when 3 more canonicals land".

#### 9. `decision-time-data-binding-pattern.md`
**Verdict: ALIGNED**
- Status: Stage 2 DRAFT → Stage 3 ACTIVE at `.F.4c.3` ship close.
- **Verified:** `Order::pre_resolved` sub-struct + `MASK_ORDER_PRE_RESOLVED` bit 16 + `o->pre_resolved.fee_rate` direct read at HandleFill — all artifacts present at `Order.hpp` + `ControllerEventLoop.hpp:971,1259,1530`.

#### 10. `branchless-dispatch-discipline.md`
**Verdict: ALIGNED**
- Status: Stage 2 DRAFT → Stage 3 ACTIVE at `.F.4c.3` ship close.
- **Verified:** `g_buy_reward_dispatch` / `g_exit_reward_dispatch` fn-pointer tables (Pattern 1), `MASK_ORDER_BANDIT_3BIT` for branchless 3-bit slot dispatch — all present at `ML_Headers/bandit_dispatch_table.hpp`.

#### 11. `registry-coverage-ci-check-pattern.md`
**Verdict: DRIFT-MINOR**
- Status: Stage 3 ACTIVE (3 canonical applications at extraction time: **Check 2 + Check 7 + Check 8**).
- **Verified Check 2/7:** `tools/check_per_core_registry_integrity.py` exists and contains Section A (positive coverage) + Section C (anti-pattern enforcement). Both Check 2 + Check 7 live in same Python tool.
- **Check 8 drift:** spec describes Check 8 as "sister tool `tools/check_oms_per_slot_registry_integrity.py`" (per `cfg-scope-discipline.md` cross-reference). Sister tool does NOT exist; only `check_per_core_registry_integrity.py` + `check_meta_registry.py` exist in `tools/`.
- `FOREACH_OMS_PER_SLOT_FIELD` registry DOES exist at `MemHeaders/OmsFieldRegistry.hpp` (5 rows; `static_assert >= 5`). But the CI tool that would enforce coverage of that registry against `OmsState` struct is unbuilt.
- **Nature of drift:** spec claims 3 canonical Check applications (extraction warrant for Stage 3 status) but only 2 actually shipped. Check 8 was planned at `.F.4c.4` but the Python tool didn't land — only the registry's `static_assert` shape did.
- **Fix:** downgrade canonicals count to 2 + acknowledge Check 8 as planned-not-shipped + add to TECH_DEBT to actually build the sister tool.

### Tier 3 — Stage 2→3 promotions claimed at `.F.4c.3` ship close

#### 12. `cfg-scope-discipline.md`
**Verdict: ALIGNED**
- Status: Stage 2 DRAFT v1.0 → Stage 3 ACTIVE at `.F.4c.3` ship close + Stage 3 ACTIVE amendments at v5.15.5.F.4c.3 r-8.
- **Verified:** `FOREACH_GLOBAL_CFG_FIELD` + `FOREACH_PER_CORE_CFG_FIELD` registries split exists at `CfgFieldRegistry.hpp:251+`. Scope categorization rules described in spec match actual registry contents.

#### 13. `cfg-section-parser-state-machine.md`
**Verdict: PROMOTION-PREMATURE**
- Status: "Promotes to Stage 3 ACTIVE v1.0 at `.F.4c.3` ship close" — but the implementation didn't land.
- **Verified actual code:** `rg "ParseScope|ParseState|\[core N\]"` returns only TODO-style comments at `ControllerConfig.hpp:287,1333,1452,1951,2099,3163` saying "Step 3 will replace this with [core N] section parser writing cores[c] directly."
- The promised `enum class ParseScope { GLOBAL, PER_CORE, ... }` + state machine described in spec body lines 31-46 does NOT exist.
- **Nature of drift:** spec promoted to Stage 3 at `.F.4c.3` ship close, but `.F.4c.3` chose to defer the `[core N]` parser. This is TECH_DEBT-080 (queued for `.F.4f` cleanup ship). The Stage 3 ACTIVE banner is incorrect.
- **Fix:** revert to Stage 2 DRAFT v1.0; correct "Promotes to Stage 3 ACTIVE at `.F.4f` ship close" (depends on TECH_DEBT-080 landing).

#### 14. `type-trait-dispatch-via-tt-namespace.md`
**Verdict: ALIGNED**
- Status: ACTIVE (Class 23 first canonical at `.F.4b`).
- **Verified:** `tt::cfg_parse_field<T>` / `tt::cfg_save_field<T>` / `tt::cfg_render_field<T>` exist at `CoreFrameworks/CfgFieldDispatch.hpp:49,170,219+`. Mirror of `tt::stamp_parse_field<T>` at `ML_Headers/StampBoundModelConstRegistry.hpp:86-99`. Pattern is canonical + production-tested.

---

## Aspirational Stage 3 promotions lacking first-canonical proof

Sister cases to the metadata-bit baseline:

| Spec | Claimed Stage | Actual | Sister to baseline? |
|---|---|---|---|
| `sidecar-override-pattern-for-registry-auto-flows.md` | Stage 3 ACTIVE at `.F.4d` | 0 canonicals shipped (FOREACH_DRIFT_OVERRIDE deferred to TECH_DEBT-085) | YES — same `.F.4d` planning aspirational |
| `multi-bit-state-encoding-pattern.md` | Stage 5 INVARIANT (5 canonicals) | 2 canonicals at HEAD; 3 deferred to `.F.4d.1` | YES — count inflation matches the aspirational-projection pattern |
| `cfg-section-parser-state-machine.md` | Stage 3 ACTIVE at `.F.4c.3` | 0 canonicals (deferred TECH_DEBT-080) | NO — different sprint; this is a `.F.4c.3` deferral, not a `.F.4d` aspiration |
| `registry-coverage-ci-check-pattern.md` | Stage 3 ACTIVE (3 canonicals) | 2 canonicals (Check 8 sister tool didn't land) | YES — count inflation by 1 |
| `meta-registry-pattern-for-codebase-registry-discipline.md` | Stage 3 ACTIVE (2 canonicals: PER_CORE_DOMAIN_BITMAP + FOREACH_REGISTRY) | FOREACH_REGISTRY exists; tuple shape + filename + sister DERIVED_FILTER drift | PARTIAL — pattern is real but described shape doesn't match |

**Pattern recognition:** **the aspirational-Stage-3-at-`.F.4d`-planning-without-reconciliation-at-`.F.4d`-ship-close shape applies to AT LEAST 3 specs** (metadata-bit + sidecar + meta-registry tuple). This is consistent with the lack of a structural ship-close reconciliation step.

---

## Recommendation

### Three-tier response

**Tier 1 — Fix drift in the 3 DRIFT-MAJOR specs at `.F.4d.1.A` ship close (before they mislead more downstream work):**
1. `sidecar-override-pattern-for-registry-auto-flows.md` — downgrade Stage 3→2 banner; rewrite first-canonical claim with TECH_DEBT-085 deferred reference.
2. `meta-registry-pattern-for-codebase-registry-discipline.md` — update tuple shape (8→4 cols) + filename (`RegistryRoster.hpp`→`MetaRegistry.hpp`) + drop sister DERIVED_FILTER claim.
3. `multi-bit-state-encoding-pattern.md` — downgrade canonical count (5→2) + Stage 5 INVARIANT → Stage 4 candidate.

Per-spec edits are ~5-15 LOC each (status banner + 1-2 paragraph rewrites). Total ~30-60 min of focused work. Add as Phase 1i closure scope in `.F.4d.1.A` plan body.

**Tier 2 — Process discipline addition** (catches future drift before it lands):
- Add `/ship` skill step: walk all DESIGN_SPECS cited in plan body; for each cited spec, verify that the spec's Stage 3 ACTIVE claim (if claimed) is consistent with actual code landed in this ship.
- Specifically: if spec status says "first canonical at this ship," verify the named mechanism exists at HEAD post-ship.
- If mismatch: block ship OR auto-revert spec banner to Stage 2 DRAFT + add follow-up TECH_DEBT.
- Codify as new ship checklist item.

**Tier 3 — TECH_DEBT-089 full sweep**:
- Remaining ~60 specs at lower priority — the Tier 1 fixes + Tier 2 process protection together should prevent NEW drift; the legacy specs (older than v5.15.5.F.4c.3) are mostly Stage 4-5 (proven; multiple canonicals; less aspirational-promotion risk).
- Schedule as 1 dedicated audit sprint after `v5.15` umbrella close: ~2-3h walking the 60 remaining specs at 2-5 min each.
- Down-payment from D4: the 14 audited here are the highest-risk subset (recent codifications); full sweep is mostly verification not remediation.

---

## Audit summary

**Audited:** 14 specs / 76 total (~18%)
**Verdict distribution:** 7 ALIGNED / 2 DRIFT-MINOR / 3 DRIFT-MAJOR / 2 PROMOTION-PREMATURE (overlap with DRIFT-MAJOR)
**Self-flagged-corrections in progress:** 2 (Path γ correction already documented in spec bodies)
**Newly identified drift:** 3 specs needing banner amendments at `.F.4d.1.A` ship close
**Process gap identified:** no structural reconciliation step between planning-time Stage 3 claims + ship-time actual implementation
**Recommendation summary:** fix 3 DRIFT-MAJOR specs at `.F.4d.1.A` (Tier 1) + add `/ship` spec-reconciliation step (Tier 2) + schedule full TECH_DEBT-089 sweep post-v5.15-umbrella (Tier 3).
