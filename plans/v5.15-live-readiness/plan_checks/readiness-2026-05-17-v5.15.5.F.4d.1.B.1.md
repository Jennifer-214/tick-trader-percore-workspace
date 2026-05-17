# /readiness paranoia audit — v5.15.5.F.4d.1.B.1 framework-consolidation plan body v1.0

**Plan:** `subplans/2026-05-17-v5.15.5.F.4d.1.B.1-framework-consolidation.md` v1.0
**Sidecar:** `subplans/2026-05-17-v5.15.5.F.4d.1.B.1-framework-consolidation-examples.md` v1.0
**Audit date:** 2026-05-17
**Predecessor:** `v5.15.5.F.4d.1.A` (engine `39b9947`; pushed)
**Top-line verdict:** **YELLOW** — structurally sound; 4 mechanical gaps + 1 HIGH false-REUSE; coding ready after 30-45min patch

---

## Verdict matrix

| # | Check | Verdict | Notes |
|---|---|---|---|
| C.1 | Branch state | PASS | `feat/v5.15-live-readiness` matches HEAD; pre-tag `pre-v5.15.5.F.4d.1.B.1` named at Step 0 |
| C.2 | Phase order matches deps | PASS | `.B.1` → `.B.2` → `.B.3` defensive ordering documented; deferral table explicit |
| C.3 | First concrete move (Step 0) | PASS | "git tag -s -a pre-v5.15.5.F.4d.1.B.1" + write 2 DESIGN_SPECs to disk |
| C.4 | Function/constructor names cited | **GAP-1 (HIGH)** | Sidecar references `tt::cfg_populate_inf_field<F>`, `tt::cfg_emit_field<F>`, `tt::cfg_drift_compare<F>`, `cfg_gate_lookup_populate`, `cfg_gate_lookup_drift` — NONE exist in codebase (verified `rg`). False-REUSE per Check 19. Plan must either (a) Step 0 explicitly adds these tt:: helpers, OR (b) reuses existing `tt::cfg_*_field<T>` family in CfgFieldDispatch.hpp |
| C.5 | File:line refs for tests | PASS | `controller_test.cpp:24962-25047` verified; `StampHelper.hpp:183` verified (`INFERENCE_CFG_AUTOPOPULATE(inf, cfg);` at line 183) |
| C.6 | Stale-claim audit | PASS | `CfgDerivedInferenceCfgRegistry.hpp:101-123` cohort verified at HEAD (14 rows, 5 cohorts as documented); `MetaRegistry.hpp:99` row verified |
| C.7 | Effort vs LOC realism | PASS | 6-8h aligns: 2 NEW DESIGN_SPECs ~1.5h + CfgGateRegistry.hpp + 3 macros ~1.5h + 3 migrations ~1h + 10-15 tests ~1.5h + Steps 7-9 ~2h |
| C.8 | Source-audit references | PASS | 11 audit reports cited (Batch 1 + Batch 2); synthesis cross-ref; predecessor postmortem cited |
| C.9 | Predecessor / dependent named with paths | PASS | `.A` postmortem path cited; sub-master v1.3 path cited |
| C.10 | Tag names locked | PASS | Pre-tag + ship tag named; rollback anchor explicit |

---

## 28-check walkthrough (abbreviated; only non-PASS items elaborated)

| # | Check | Verdict | Note |
|---|---|---|---|
| 1 | Hot path purity | PASS | UNTOUCHED; verification gate explicitly cites |
| 2 | Train-serve parity | PASS | 0-row walk at `.B.1`; vacuous PASS for byte preservation |
| 3 | Surface area | PASS | ~5 files (1 NEW + 4 modified); under 8-file threshold |
| 4-10 | (standard items) | PASS | No new heap state / threading / version bumps that aren't planned |
| 11 | Architectural sprint | PASS | Framework consolidation; deferral table covers orphan risk |
| 13 | Strategy lifecycle | N/A | No strategy changes |
| 14 | X-macro dispatch | PASS | FOREACH_CFG_GATE shape cited; meta-registry enrollment planned |
| 18 | Reuse audit | **GAP-2 (MED)** | Plan doesn't enumerate which existing `tt::` family helpers are reused vs new; see GAP-1 root cause |
| 19 | Pre-existing-work audit | **GAP-3 (HIGH)** | 5 false-REUSE helpers in sidecar code samples (per C.4 GAP-1). Plan must explicitly state these are NEW + Step 0 lists their addition, OR reuse existing surfaces |
| 20-24 | (standard sprint guards) | PASS | Mirror-fn enumeration covered via sister registry inspection |
| 25 | TECH_DEBT surface scan | PASS-WEAK | Step 9 mentions auto-write; doesn't list which entries to open. TECH_DEBT-087/-088/-089/-090 already exist for related risk; could note "no new entries expected" or list candidates |
| 27 | DESIGN_SPECS pattern application (DOD) | PASS | Composition narrative: composed-mask + sidecar-override + autopopulate + metadata-bit-driven-derived-filter all cited; 2 NEW Stage 3 first refs documented |
| 28 | Test-strength | PASS | 10-15 new tests are pure-additive; no weakening |
| 29 | **Canonical sister considered (NEW)** | **GAP-4 (MED)** | Plan body has NO explicit "Canonical sister registries considered" section. Sidecar exists (`canonical-sister-extension-discipline.md` Stage 2 DRAFT) but plan doesn't cite per-sister fold/no-fold verdict for: FOREACH_CFG_DERIVED_INFERENCE_CFG (folded — replaced) / FOREACH_STAMP_BOUND_CFG (kept — `.B.3`) / FOREACH_CFG_DRIFT_CHECK (status?) / FOREACH_CFG_FIELD master (extended) / FOREACH_METADATA_BIT (consumed). The discipline being codified at this ship REQUIRES the plan demonstrate adherence |
| 31 | Wider-build verification | PASS | `.A` postmortem documents 5 binaries clean post-build |

---

## Categorical applicability + H15/H19 enrollment for FOREACH_CFG_GATE

| Check | Verdict | Note |
|---|---|---|
| `lives_in_struct` enum value | PASS-WEAK | New registry lives in `MemHeaders/`; not a cfg-file location but X-macro registry; sidecar override pattern doesn't need lives_in_struct tag |
| `applies_to_strategy_cat` etc. | N/A | Sidecar is per-row; not a cfg field |
| H15 (FOREACH_REGISTRY enrollment) | PASS | Step 4 explicitly enrolls `FOREACH_CFG_GATE` + 3 consumer macros |
| H19 (LEVEL > 0 → valid PARENT) | PASS | Level 1, PARENT = FOREACH_METADATA_BIT — correct per sidecar discipline |
| Meta-registry topology | PASS | 4 new rows fit existing Level 1 structure |

---

## Drift audit (train ↔ serve, write ↔ read)

| Category | Verdict | Note |
|---|---|---|
| Feature drift | PASS | No feature changes |
| Wire format / canonical body byte order | PASS | 0-row walk at `.B.1` produces empty body → vacuous PASS; CRIT-6 (byte order decision) explicitly deferred to `.B.2` per synthesis |
| Threshold drift | PASS | No threshold consts |
| Build-flag drift | PASS | All targets exercised at Step 9 |

---

## Hidden scope detected

1. **GAP-1 / GAP-3 (HIGH; SAME root cause):** sidecar references 5 helper functions that don't exist in codebase. Coder reading sidecar would assume they're available; Step 0 of coding trips. Resolution options:
   - **(a) Add Step 0.5:** introduce `tt::cfg_populate_inf_field<T>`, `tt::cfg_emit_field<T>`, `tt::cfg_drift_compare<T>` in `CoreFrameworks/CfgFieldDispatch.hpp` (sister to existing `tt::cfg_parse_field<T>`, `tt::cfg_save_field<T>` at `:70`+`:178`). +30-45 min effort.
   - **(b) Update sidecar examples** to use existing `tt::cfg_emit_field<T>` if it can be repurposed; or document via existing `tt::cfg_save_field<T>` for emit and add comparison logic inline at the consumer macro level.
   - **Auto-pick recommendation: (a)** per `feedback_auto_pick_future_oriented` — extends existing `tt::` family canonical; future cfg-derived consumers all reuse same helpers; aligns with framework discipline.
2. **GAP-2 (MED):** Reuse audit not explicit. Plan should enumerate which existing tt:: helpers extend vs which are NEW. Resolved by GAP-1 patch.
3. **GAP-4 (MED):** Plan body lacks "Canonical sister registries considered" section. Adding this section IS what `canonical-sister-extension-discipline.md` requires. Recommend ~10 min addition listing 5-6 sister registries inspected (FOREACH_CFG_DERIVED_INFERENCE_CFG / FOREACH_STAMP_BOUND_CFG / FOREACH_CFG_DRIFT_CHECK / FOREACH_CFG_FIELD / FOREACH_METADATA_BIT / FOREACH_DRIFT_OVERRIDE planned at .C) with per-sister fold/no-fold verdict.

---

## Recommendations

### Must fix before coding
- **GAP-1+3 patch (HIGH):** decide how the 3 tt:: helpers + 2 cfg_gate_lookup_* fns land. Add Step 0.5 to plan body OR document existing-helper reuse. Without this, Step 1-2 implementation references undefined symbols. **Effort: 30 min plan edit + ~45 min coding-time helper landing.**

### Worth fixing during coding
- **GAP-4 (MED):** Add "Canonical sister registries considered" section to plan body Why-this-ship-exists area. Per-sister fold/no-fold verdict. Demonstrates the codified discipline at THIS ship (the discipline IS what shapes the ship per `canonical-sister-extension-discipline.md` v1.0). **Effort: 10 min.**
- **GAP-2 (MED):** Step 9 auto-write should list candidate TECH_DEBT entries if any (or explicit "no new entries expected" if Batches 1+2 audit residuals all covered by existing -087/-088/-089/-090). **Effort: 5 min.**

### Acceptable risk (don't block)
- Sidecar `cfg_gate_lookup` template signature in examples `(const ControllerConfig<auto>&)` syntax is invalid C++ — `auto` template parameter doesn't apply here. Coder will catch at compile; not a blocker for plan approval but flag.
- Sidecar `CfgGateEntry struct` shape is sketched, not fully specified. Acceptable for sidecar (intent docs); coder finalizes shape at coding time.

---

## Top-line verdict: YELLOW

**GREEN-condition:** apply GAP-1+3 patch (Step 0.5 adds 3 tt:: helpers + 2 cfg_gate_lookup_* fns, OR explicit existing-helper reuse). After patch: GREEN to start coding. ~30-45 min total plan amendment.

Plan body is structurally sound, well-cited, defensive ordering correct, scope ~6-8h realistic, verification gate complete, predecessor + audit cross-refs intact. The single material gap is mechanical (false-REUSE on 5 helper fns in code samples). The discipline-codification gap (Check 29 / canonical-sister-considered section) is procedural and addressed by adding 1 narrative section.

**Effort to GREEN: ~45 min plan amendment + ~45 min Step 0.5 helper landing at coding time (or zero if existing-helper reuse path chosen).**

---

## Cross-references
- Audit synthesis: `plan_checks/2026-05-17-v5.15.5.F.4d.1.B-audit-synthesis.md`
- `.A` postmortem: `postmortems/2026-05-17-v5.15.5.F.4d.1.A-postmortem.md`
- Sub-master v1.3: `subplans/2026-05-16-v5.15.5.F.4d.1-thread-a-framework-full.md`
- 2 NEW DESIGN_SPECs (Stage 2 DRAFT, Stage 3 first reference at this ship):
  - `canonical-sister-extension-discipline.md`
  - `cfg-derived-consumer-framework.md`
- Engine HEAD: `39b9947` (`.A` ship, pushed)
