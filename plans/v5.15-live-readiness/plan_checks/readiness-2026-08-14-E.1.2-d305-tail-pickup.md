# /readiness report — E.1.2 nodestate-soa-layout (D-305 tail pickup) — 2026-08-14

**Target:** `subplans/2026-06-15-v5.15.5.F.4d.1.E.1.2-nodestate-soa-layout.md` (⏩ EXECUTION-STATE banner = the executable spec; body = audit trail)
**Context:** fired inline from `/accept-handoff` Stage 6 at the engine-resume pickup. Engine HEAD `3c57534` = tag `pre-E.1.2-resume`, source-identical to the c-class verification HEAD `a71b893`.

## What we already have (Stage 0 preamble)
- Currency: the 2026-08-11 c-class re-ground verified 40 anchors (0 fabrications) at `a71b893`; amendment 9 (ws `2d4889c`) executed the full punch-list. This pass re-verified the LOAD-BEARING subset at HEAD rather than re-deriving all 40.
- Decisions: D-289/291/292/294/295/296/302/303/304/305 all `STATUS: DECIDED`; D-297 superseded by D-302; D-419 LANDED. **No open decisions block coding** — the genuinely-open items are the carried dive questions (TD-189 · MAX_NODES_PER_CLUSTER naming · AM-4 evidence re-locate · Reconcile re-read · :490-496 recompute list · swap_model_path_requested writer-group · seq@58112 isolate · AM-4 :488/:901 re-derive).
- Specs warm: wire-format-byte-preservation (H9, Layers 1-7) · dead-code-and-identifier-retirement (H21, stage-6) · cache-line-discipline (H6) · per-node-position-ownership · OMS 4-phase persist precedent (`OmsFieldRegistry.hpp:423-433` count-lock + `:475-598` SAVE/DECLARE/READ/COMMIT + `static_assert(false)` undesigned combos).
- Anti-patterns armed: Class 18 (mirror drift) · Class 44/45 (SSoT family) · Class 51 (vacuously-green guard — governs the poison-fixture/positive-control/golden design; the A-pass folded its modes into the gate recipe).

## Mechanical pre-pass (Stage 0.5)
- `check_session_docs.sh` — **SWEEP CLEAN** (all HARD pass; 1 pre-existing advisory: close-out completeness window).
- Check 32 symbol-existence — **0 fabrications** (58 anchors: 18 drift [known cite-era, `[NOW:]`-governed] + 21 annotated + 7 notfound in SUPERSEDED audit-trail sections).
- Check 45 tests-section — **PASS** (3 sub-categories present).
- Check 46 `check_identifier_retirement.py` — **GREEN** (46 identifiers match ledger).

## Load-bearing anchor verification at HEAD (all ✅)
| Claim (banner) | Verified |
|---|---|
| `FOREACH_NODE_PERSIST_FIELD` grep-zero (not started) | ✅ rg exit 1 |
| D-289 delete targets present: `Portfolio_Save/_Load` `:836/:890` · `PortfolioController_*Snapshot` `:2185+` · `CONTROLLER_SNAPSHOT_VERSION 14` `:2181` | ✅ exact |
| `PORTFOLIO_SNAPSHOT_VERSION 7` @ `Portfolio.hpp:800` (RETIRES, no bump — BLK-2) | ✅ |
| `SHARDED_SNAPSHOT_VERSION 10u` @ `ShardedSnapshotPersist.hpp:109` (→11) | ✅ |
| F-096 legs still `double` @ `Async.hpp:859/:872/:877-881/:926` | ✅ (`Money_ToDouble`→`*`→`money_from_double_payload`) |
| 4-version assert `tests/controller_test.cpp:27013-27014` + second SHARDED pin `:11588` | ✅ exact |
| Version-named golden `tests/sharded_snapshot_v10_golden.hpp` exists (regen/RENAME at bump) | ✅ |
| `cache_layout_baseline.txt` = exactly 4 engine keys (NodeContext regime_state + 3 TUISharedState) + 9 TrainingPanelState suite keys (NEVER retire the 9) | ✅ exact |
| Step-2c sub-registries H15-enrolled (`FOREACH_REGIME/FEEDER/CONFIDENCE_PERSIST_FIELD` @ `MetaRegistry.hpp:102-104`) | ✅ |
| Delegates live in serializer (`RegimeState_FieldwiseWrite:247` · `RegressionFeederX_FieldwiseWrite:252` · `ConfidenceScorer_FieldwiseWrite:272`); nested staging landed field-by-field; REC-A fold NOT yet done (`RecomputeRunningSums` separate @ `:595`) | ✅ matches remaining-scope |

## Checklist verdicts (scoped to the banner)
| # | Item | Verdict | Notes |
|---|---|---|---|
| 1 | Hot path purity | PASS | persist/registry/test surface; acceptance requires `calls_graph_diff` GREEN + conformance no-regression at close |
| 2 | Train-serve parity | PASS | snapshot is engine-side warm-restart, not a train-serve artifact; `/parity-check` only if wire shifts a shared surface (handoff routing) |
| 3 | Surface area | PASS | bounded cohort: new registry header + serializer + 2 version sites + deletes + tests + 1 Python tool |
| 4 | Heap lifecycle | PASS | no new heap state |
| 5 | Backward compat | PASS-BY-DESIGN | version-reject IS the migration (D-131 epoch-free, no live models); FEATURE_LOOKUP operator-impact SECTION owed at close |
| 6 | Multi-threading | PASS | snapshot save/load = slow-path/boot single-thread sites; the TUISharedState/NodeContext straddler re-bless is close-gate, writer-group analysis carried |
| 7 | Test coverage | PASS | Tests-changed section enumerated (modified/broken-replaced/NEW incl. poison fixture + positive control + value round-trip) |
| 8 | Docs+invariants | PASS | AM-6 class + CI guard authored together at close; H21 tombstones enumerated |
| 9 | Forward maintenance | PASS | the whole ship IS the structural fix (registry + count-locks + paired-bump) |
| 10 | Rollback | PASS | dual anchors: `pre-E.1.2-resume`@3c57534 (fresh) + `pre-v5.15.5.F.4d.1.E.1.2`@b10e778 (do NOT move) |
| 46 | Identifier retirement | PASS | tool GREEN now; retire cascade = ledger+SOURCES lockstep one-commit-each at Steps 3-5 |
| 47 | M10 oracle totality | NOTE | main-session coding (no delegation planned). The frozen golden = TOTAL oracle once landed; the new Python layout-audit tool's selftest = PARTIAL → hand-review its first output against the 37-row wire map |

## Notes / worth-fixing-during-coding (no blockers)
1. **Confidence count-lock still missing** (no `_PERSIST_COUNT` static_assert in `ConfidenceScore.hpp`) — in-scope remaining work (build recipe: regime ==7 · feeder ==3 · confidence ==7). Regime/feeder COUNT constants exist (`RegimeDetector.hpp:681-683` · `LinearRegression3X.hpp:138-140`); verify at dive whether the ==7/==3 wire-pin static_asserts exist beside them or only the raw counts.
2. The 18 Check-32 line-anchor drifts are all in the b10e778-era body under the banner's cite-era rule — re-derive per `[NOW:]` markers at dive; do not code from the body.
3. Two-phase landing discipline (byte-identical-to-v10 FIRST, then the v11 delta) is the load-bearing sequencing — the frozen golden must predate the delta commit (Class-51: "a golden regenerated in the act it polices is not a golden").
4. A2 impl invariant to carry into Step 1: **READ dispatches on STORAGE_KIND only, never COMMIT_KIND** (NO_COMMIT rows still consume wire bytes) — the offset-desync trap.

## Verdict: **GREEN** — start the D-305 tail (item 1: ordered `FOREACH_NODE_PERSIST_FIELD`) after operator consult.
