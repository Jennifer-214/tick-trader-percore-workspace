---
type: plan-check
check_kind: readiness
plan: plans/v5.15-live-readiness/subplans/2026-06-15-v5.15.5.F.4d.1.E.1.2-nodestate-soa-layout.md
ship_tag: v5.15.5.F.4d.1.E.1.2
run_date: 2026-08-15
run_by: main-session (Layer 2 inline, composed by /accept-handoff Stage 6)
engine_head: 09824e8
workspace_head: 9be86d6
scope: REMAINING D/E/F only (A/B/C LANDED at engine 7778c66 / 1d3c797 / 4277e14)
verdict: GREEN
---

# /readiness report — E.1.2 nodestate-soa-layout — 2026-08-15

**Scope note:** this run audits ONLY the remaining work per the active handoff's ⏩ ADDENDUM
(which SUPERSEDES the plan body's § The work). Items **A/B/C are LANDED and verified** — the
capital wire is frozen at v11. Remaining: **D** (D-289/2 PORTFOLIO retire) · **E** (F-096 Money
legs) · **F** (close-gate).

## What we already have (Stage-0 preamble)

- **Pre-coding audits are PAID for this exact scope.** The 2026-07-03 `/precoding-audit-gate` +
  the 2026-07-04 I/A cascades + the FOUR frozen 2026-08-14 precode reports
  (`reports/2026-08-14-e12-v11-precode/`) are the gate. `audit_tier: HIGH` is declared and matched.
- **Decisions are CLOSED for D/E/F.** D-420 (AM-4) `STATUS: DECIDED`. BLK-2 (PORTFOLIO retires,
  no 7→8) settled. D-289 DELETE-not-tombstone settled (decision log `:1836`). The i-class OQ
  dispositions (OQ-1 T1 · OQ-3 keep `POSITION_PERSIST_BYTES` · OQ-4 strip floor terms · OQ-5
  RETIRED_NAMES adopted) are all resolved in the handoff addendum. **Zero open decisions block coding.**
- **Specs loaded:** `dead-code-and-identifier-retirement-discipline.md` (stage 6, governs D) ·
  `wire-format-byte-preservation-discipline.md` v1.2 Layer 5c (governs the frozen v11) ·
  `DOCS/STRATEGY_AND_CODING_RULES.md` (governs E — drainer/money path).
- **Anti-patterns in play:** Class 4 (snapshot save/load asymmetry — the sibling Class 58 must
  distinguish) · Class 40 (Knight-Capital dead code / identifier reuse — D's governing class) ·
  Class 51 (vacuously-green guard — binding on F's new guard) · Class 57 (pipe-swallow — bit twice
  during this pickup; the hook caught both).
- **Invariants in play:** H21 (tombstone) · H4 (Money on money paths) · H9/H12 (wire bytes) ·
  H18 (sidecar override — F's partition guard shape) · H15 (meta-registry enrollment for the new
  sidecar registry) · H7/H8 (hot path must stay untouched — `calls_graph_diff.sh` is the check).

## Mechanical pre-pass (Stage 0.5 — deterministic, run first)

| Tool | Result |
|---|---|
| `tools/check_session_docs.sh` (the one-shot aggregator) | **exit 0 — SWEEP CLEAN**, all HARD checks pass (1 advisory: close-out-completeness auto-write ledgers) |
| `check_plan_body_symbol_existence.py` (Check 32) | rc 0 — **0 FABRICATIONS**, 54 line-anchors (20 drift · 5 notfound · 21 annotated) |
| `check_plan_body_tests_section.py` (Check 45) | rc 0 — section present + 3 sub-categories |
| `check_identifier_retirement.py` (Check 46) | rc 0 — GREEN, 47 ids match ledger |
| `node_persist_layout.py` | rc 0 — GREEN, 46 flattened wire rows match golden |
| `check_struct_alignment.py` | rc 0 — GREEN, 3 byte-serialized types size-pinned (was 4 pre-C) |
| `check_money_gross_single_source.py` | rc 0 — PASS (D-190 SSoT clean) |
| `./build.sh test` (baseline) | rc 0 — **3719 passed, 0 failed**; conformance clean |

Baseline exactly matches the handoff's claimed 3719/0. The green floor is real, not asserted.

## Checklist verdicts (the 10-item CLAUDE_REVIEW walk)

| # | Item | Verdict | Notes |
|---|---|---|---|
| 1 | Hot path purity | **PASS** | D = dead-serializer deletion in `Portfolio.hpp` · E = drainer (`Async.hpp`), not `ExecutionCore_Tick`/`BG_Evaluate` · F = tooling/codification. `calls_graph_diff.sh` is the post-change DoD check (named in the handoff arming). |
| 2 | Train-serve parity | **PASS** | No `RegimeSignals` / `ModelFeatures_Pack` / label surface touched. Money-surfaces §H-8: F-018 bypasses the split structurally — if F-018 goldens move, the change leaked outside the mapped surface. |
| 3 | Surface area | **PASS** | D = 2 engine headers + tests · E = 1 file · F = workspace tools + DOCS + 1 registry. Each is a micro-commit; no `if (mode)` proliferation. |
| 4 | Pointer init / heap lifecycle | **PASS** | No new heap. H1 intact (deletions only in D). |
| 5 | Backward compat | **PASS** | SHARDED already 10→11 at B (verified `ShardedSnapshotPersist.hpp:114`). PORTFOLIO retires via **T1** (live `#define` stays at `Portfolio.hpp:800`, reworded as tombstone) ⇒ **ZERO ledger lockstep, no TTY** for commit D. H21 honored literally ("keep the number"). |
| 6 | Multi-threading | **PASS (named acceptance)** | E touches the drainer. No new threads/atomics. Pre-existing torn-read of `intended_qty` (money-surfaces LOW-3) and the torn producer-thread capture (MED-2) are explicitly **`.E.1` aggregator scope — do NOT fix here** (H-3 hazard). Conservation assert must be phrased for the same-read pair (OQ-3 form, already decided in the addendum). |
| 7 | Test coverage | **PASS (with re-derived cites — see GAP-1)** | Tests-changed section present. D owes the PORTFOLIO-term strip; E owes the conservation assert; F owes the Class-58 guard fixture + `NPF_PROJECT_POISON` coverage. |
| 8 | Docs + invariants | **PASS** | Class 58 codification IS item F. FEATURE_LOOKUP operator-migration SECTION + postmortem + `/ship` enumerated in the handoff close-out. |
| 9 | Forward maintenance | **PASS — this is the strong point** | F's partition guard (`FOREACH_NODE_UNPERSISTED_FIELD` H18 sidecar + the partition tooth in `node_persist_layout.py`) is the STRUCTURAL close of the recurrence class, not a patch. Guards-compound aligned. |
| 10 | Rollback story | **PASS** | Both anchors exist as real tags: `pre-E.1.2-resume` (@`3c57534`) + `pre-v5.15.5.F.4d.1.E.1.2` (@`b10e778`, do NOT move). |

## Numbered-check verdicts (the ones that bite this scope)

| Check | Verdict | Notes |
|---|---|---|
| 19 pre-existing-work (SHIP-BLOCKING) | **PASS** | Verified genuinely-NEW by grep-zero: `FOREACH_NODE_UNPERSISTED_FIELD` (0 hits) · `NPF_PROJECT_POISON` (0 hits; 3 projections SAVE/READ/COMMIT exist at `NodeCtxPersistRegistry.hpp:160/184/200`) · Class 58 slot free (max codified = 57). No false-NEW claim. |
| 25 TECH_DEBT surface scan | **PASS (operator-directed routing)** | Per `feedback_spotcheck_findings_route_to_plan_homes_not_techdebt`, MED-1 (live-session orphan off-by-one, 4-source enumeration) → `.E.1` plan home; MED-3 (event-log replay per-LEG W/L, no pairing) → the replay path's owning plan. Both named in the addendum's item F. **Neither is unhomed.** |
| 29 citation drift | **⚠️ GAP-1** | See below. |
| 32 plan-body symbol existence | **PASS** | 0 fabrications. The 5 NOTFOUNDs are tool false-negatives, verified by hand: `Backtest/Fingerprint.hpp:232` is an **exact** hit for `Fingerprint_Compute`; `ControllerEventLoop.hpp:488` → `partner_pending_pnl` at `:492` (off-by-4); `OmsFieldRegistry.hpp:423-433` → count-lock at `:444` (off-by-11). |
| 34 audit tier + scope match | **PASS** | `audit_tier: HIGH` declared; the wire genuinely changed (at B). The gate + I/A cascades + 4 frozen precode reports match the scope. Re-fire `/blindspot-scan` B12 only if the delta shape drifts — it did not. |
| 45 tests-changed enumeration | **PASS** | Tool-verified. |
| 46 identifier retirement + dead code | **PASS** | Guard GREEN. D is a prove-then-remove deletion; the compiler is the zero-caller oracle (i-class §1: all four fns have ZERO call sites, tree-wide with `--no-ignore`). `RETIRED_NAMES` blocklist (Option D) already landed at C. |
| 47 acceptance-oracle totality (M10) | **⚠️ ACTION — see below** | Classified per item. |

### Check 47 — acceptance-oracle classification (M10; drives delegate-vs-hand-review)

| Item | Oracle | Class | Consequence |
|---|---|---|---|
| **D** deletion of `Portfolio_Save/_Load` | the compiler (a surviving caller = compile error) + `./build.sh test` + `check_identifier_retirement.py` | **TOTAL** | Accept on green. |
| **D** stale-comment re-aim sweep (§5: 9 sites in `Portfolio.hpp`, 8 in `PositionFieldRegistry.hpp`) | none — no mechanical check that a re-aimed comment is *correct* | **PARTIAL** | **Context-carrying hand-review of the diff before commit.** Green build ≠ done. |
| **E** F-096 Money legs | conservation assert + Save→Load byte-compare. Per money-surfaces **H-7: NOT** old-vs-new trace parity (ULP shifts expected + quantified) | **PARTIAL** | Hand-review; do NOT gate on paper-trace equality. |
| **F** Class-58 guard + partition tooth | the guard's own non-vacuity (positive control + real-body-else-fail-LOUD) | **PARTIAL** | Class 51 is binding: the guard must assert its own non-vacuity, and the builder is model-bounded (AR-8) → this earns an independent adversarial review before commit, as the D-305/1b guard did. |

## Drift audit (train ↔ serve, write ↔ read)

| Category | Verdict |
|---|---|
| 1 Feature drift | **PASS** — no ML feature surface touched |
| 2 Label drift | **PASS** |
| 3 Metric drift | **PASS** — `check_money_gross_single_source.py` GREEN (D-190 SSoT) |
| 4 Path drift | **PASS** |
| 5 Format drift | **DRIFT-SAFE** — SHARDED bumped 10→11 at B with golden regen/RENAME riding the same commit (paired-bump enforced); PORTFOLIO retires per BLK-2 (T1 tombstone, no bump — correct: no live serializer remains to version) |
| 6 Threshold drift | **PASS** — `partial_exit_pct` single-sourced from cfg (`CfgFieldRegistry.hpp:760`) |
| 7 Tick/time-source drift | **PASS** |
| 8 Build-flag drift | **PASS** — E is `±USE_NATIVE_128`-inert (decimal `Money` ops, not the 128 path selection) |

## Hidden scope / GAPs

### ⚠️ GAP-1 (must fix during coding — cite re-derivation, NOT a rescope)

The plan body + close-gate report cite the version-assert surface as
`tests/controller_test.cpp:27013-27014`. **The C commit reshaped that region.** Re-derived at
engine `09824e8`:

| Cite in plan/report | Actual at HEAD |
|---|---|
| `tests/controller_test.cpp:27013-27014` (4-version equality) | **`:27094-27095`** — `SHARDED_SNAPSHOT_VERSION == 11u && PORTFOLIO_SNAPSHOT_VERSION == 7 && STAMP_FORMAT_VERSION_CURRENT == 3` |
| `:26943/:26949` + `:26945/:26951` (D-144 monotonic floors) | **`:27025-27026`** (static_assert) + **`:27030-27031`** (runtime check) — CONTROLLER terms already gone (C landed); the PORTFOLIO terms are what item D strips |
| second SHARDED pin `:11588` | **`:11666-11667`** — already `== 11u` (B landed) |

**Item D's test edit therefore targets exactly three PORTFOLIO terms:** `:27026`, `:27031`, `:27095`.
Check-32 independently confirms this (`plan:line~127` drift resolves to `PORTFOLIO_SNAPSHOT_VERSION`
at **27026**). Not a blocker — the cite is stale, the work is unchanged.

### DRIFT (pre-existing, non-blocking)

19 further line-anchor drifts in the plan body all fall inside sections the plan itself marks
**SUPERSEDED / VOID / ✅ LANDED** (the `572c978`-era Design-shape, the void Phase-B 192B text, the
amendment-8 audit trail, the ③ ControllerConfig delivered-fold). The EXECUTION-STATE banner + the
frozen reports are the operative spec, exactly as the banner instructs. No action.

### INFO

MASTER `UPDATE 28` still narrates "REMAINING = Steps 3–5 (the v11 DELTA…)" — one layer behind the
handoff ADDENDUM (A/B/C landed). The pointer linkage is HARD-green
(`index-currency (MASTER banner ↔ active handoff)` passed), so only the narrative lags. Fold the
A/B/C stamp into MASTER at the ship close.

## Recommendations

### Must fix before coding
*(none)*

### Worth fixing during coding
1. **GAP-1** — use the re-derived test cites above (`:27026`, `:27031`, `:27095`), not the plan's `:27013-27014`.
2. **Check 47** — budget the context-carrying hand-review for D's comment sweep, E's ULP-shifting Money legs, and F's new guard (the last also earns an independent adversarial pass per AR-8/Class 51 precedent).

### Acceptable risk (don't block)
3. The 19 superseded-section drifts (audit-trail only).
4. MASTER UPDATE-28 narrative lag (fold at close).
5. `check_struct_alignment.py` 13 advisory `alignof` lock suggestions — pre-existing, unrelated to this scope.

## Map-update suggestions (post-verify)

- `./tools/gen_code_map.sh` after D lands (deleting `Portfolio_Save`/`_Load` drops CODE_MAP 826 → 824).
- `tools/rebuild_doc_indexes.py` after D (CODE_TAG_INDEX rows for the deleted tag units).
- `tests/INVARIANTS_MAP.md` — Class 58's new guard promotes a DISCIPLINE row to ENFORCED at F.
- H15: the new `FOREACH_NODE_UNPERSISTED_FIELD` sidecar registry **MUST** get a `FOREACH_REGISTRY`
  row in `CoreFrameworks/MetaRegistry.hpp` at F, or `check_meta_registry.py` reds.

## Verdict: **GREEN** — start coding

Zero must-fix items. Decisions closed, audits paid, guards green, baseline 3719/0 proven, rollback
anchors real. The one cite drift (GAP-1) is re-derived above and costs nothing.

**First concrete move:** commit **D-289/2** per the i-class §6 ordered commit plan —
`Portfolio.hpp` delete units `:814-877` + `:879-946`, tombstone-reword `:799-800`, rewrite the
`:792-798` section banner, `[CONTAINS]` `:26-27` + `[OVERVIEW]` `:12`, the §5 re-aims across
`Portfolio.hpp` + `PositionFieldRegistry.hpp`; tests strip the 3 PORTFOLIO terms; **zero** workspace
ledger/SOURCES edits (T1). Then regen the two indexes.
