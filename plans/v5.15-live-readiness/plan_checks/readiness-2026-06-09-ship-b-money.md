# /readiness report — 2026-05-30-v5.15.5.F.4d.1.E-money-numeric-core-foundation.md (v0.3) — 2026-06-09

**Audit scope:** Ship-B REMAINING work only (decimal money). Ship-A rows SHIPPED + dispositioned (E.0.7/E.0.8) — excluded per scope directive. Decisions D-97..D-167 all DECIDED — none re-flagged (Stage-0 D-105-fake-blocker discipline honored). Stage-2.5 mechanical floor attested GREEN by invoker (B-Plus 0 fabrications; tests-section PASS; fee-enumeration COMPLETE; check_session_docs HARD GREEN) — not re-derived; Checks 32/45 satisfied by that pre-pass.

**Focus:** cold-pickup completeness for the Ship-B CODING SEQUENCE (ordered steps / per-step files / sidecar linkage / rollback+tag / golden-regen D-100 / retrain checklist M4 / Check-F un-bypass D-157) + effort-vs-scope.

## Stage 0 — what we already have

- HIGH-RISK money ship; `audit_tier: HIGH-RISK` declared (Check 34 PASS); heavier-default posture (D-77) named in frontmatter + closing line.
- Sister specs cited both ways (SSoT, two-foundations D-82/D-100, golden-master-over-oracle, fp-determinism-canonical-path, H12, x-macro). Check 29 sister-registries section PRESENT (B5 fix-in-plan verified applied — § Canonical sister registries; venue-SSoT prose carries the `.E.1` scoping).
- Ledger state verified: TECH_DEBT-144/-146/-147/-149/-159 all present in workspace `DOCS/tech-debt/open.md` (159 = D-161 re-pack, gated Ship-B — forward-promise LANDED). PARITY-033 named in body.
- D-100 oracle artifacts ON DISK: `plan_checks/2026-06-01-11-phase1-divmul-proof/{PROOF.md, divmul_pow10_proof.py, decimal_oracle.py}`. `tools/check_storage_t_coverage.py` exists (B3 extension target).
- Check F verified at `.githooks/pre-commit:210-232` (bypass = `SKIP_DETERMINISM_CHECK=1`); golden-regen command documented at `tools/check_fp_determinism.sh:13-15`; D-157 body at decision-log :1010-1011 (bypassed-with-rationale until stabilization → refreeze + un-bypass).

## Anchor spot-verification (C.6) — 9/9 EXACT

`FixedPointN.hpp:82` generic / `:84` `<2,64>` / `:97-107` traits incl. `is_fp_decimal_v` :100-102 ✅ · `CfgFieldDispatch.hpp:348` `%.17g` under `is_fp_binary_v` ✅ · `EngineCommon.hpp:156-159` BNB `FromDouble(0.75)` muls ✅ · `ControllerConfig.hpp:1366` `Fee_Compute` ✅ · `OrderManager.hpp:1160/1178` fill handlers ✅ · `BinanceUserData.hpp:361/378` commission double-parse ✅. Same-day re-audit claim ("all 65 anchors re-derived") holds on sample. **C.6 PASS.**

## Checklist verdicts (10-item core)

| # | Item | Verdict | Notes |
|---|------|---------|-------|
| 1 | Hot path purity | PASS | compares-only steady path; 3 rare-entry muls; divmul fixed-cost PROVEN (D-140); `calls_graph_diff` acceptance row present |
| 2 | Train-serve parity | PASS | M5 precision-SSoT declared; ema_price dual-impl (B6) + both replay surfaces (B2) enumerated; drift walk below |
| 3 | Surface area | ACCEPTED | large by nature (42 accounting + ~30 cfg + ~30 stamp + persistence + ~12 casts) but fully enumerated + netted (D-130 split) |
| 4 | Pointer/heap | N/A | H1 codebase; no heap |
| 5 | Backward compat | **GAP** | Ship-B snapshot-version bump not explicit — see Gap 2 (format drift) |
| 6 | Multi-threading | PASS | no new threads/atomics; type flows through existing rings |
| 7 | Test coverage | PASS | Check 45 section present (a/b/c subcategories); mechanical tool PASS attested |
| 8 | Docs+invariants | PASS | codification slate § (H4 CLAUDE.md update at close, Classes 37+, skill updates) |
| 9 | Forward maintenance | PASS | #4 single rounding helper, #5 single parse, coverage-tool both-branch extension — structural closes throughout |
| 10 | Rollback story | PARTIAL | trigger 5 "Pre-tag rollback anchor" + A.5 tag = standing STOP boundary; tag name monotonic-at-ship = ACCEPTED policy (D-88/D-108); `pre-<tag>` name not spelled — fold into Gap 1 |

## Cold-pickup C.1–C.10

| # | Verdict | Notes |
|---|---------|-------|
| C.1 branch | PASS | `feat/v5.15-live-readiness` named |
| C.2 phase order | **GAP** | § Sequencing is SHIP-level (net→this→rename); intra-Ship-B order exists only as the sidecar #1→#6 compounding chain + the unordered line-35 REMAINING list; B1-B6/casts/dispatcher-branch/FP64-absorb/close-steps never bound into one order |
| C.3 first concrete move | PARTIAL | next ACTS stated (gate re-fire + D-93 audits on #4/#5/#6) — but first CODE move unnamed; `FPN_*` naming decision (D-163 deferral) is sequencing-critical Step 0 (gates every new fn name) yet appears only in the line-35 list |
| C.4 fn names | PARTIAL | `divmul_pow10`/`FPN_Quantize`/`to_binary()`/`to_decimal()`/`FromString` named; **#4 rounding helper UNNAMED** anywhere (plan + sidecar say "the rounding helper") |
| C.5 test/baseline refs | PASS | golden tool paths, controller_test anchors, oracle paths all file:line |
| C.6 stale-claim | PASS | 9/9 anchors exact; historical blocks marked EXECUTED |
| C.7 effort | **GAP** | zero effort claims for Ship B; multi-session scope (see Effort below) → estimate unreliable per skill mapping |
| C.8 source-audit refs | PASS | every claim carries synthesis/proof/sweep path |
| C.9 predecessor paths | PASS | .E.0.1 / .E.0.3 / dependency-graph path-cited |
| C.10 tags | ACCEPTED | monotonic-at-ship-time (D-88/D-108) — documented divergence |

## Drift audit (8-category)

1 Feature PASS (features stay binary — the split IS the ship) · 2 Label PASS · 3 Metric PASS (#4 single helper by construction; C2 replay==production differential in D-100 gate) · 4 Path PASS · **5 Format DRIFT-RISK — see Gap 2** · 6 Threshold PASS (B4 price-domain pick declared as in-plan code-time decision) · 7 Tick-source PASS · 8 Build-flag PASS (UBSan lane landed; FP64/USE_NATIVE_128 absorb named).

**Gap 2 detail (format drift / Check 46-adjacent):** Ship B retypes persisted money fields `FixedPoint<2,64>` → `FixedPoint<10,8>` — **both 16B `__int128`**. Identical sizeof/offsets ⇒ the R1 static_assert net that self-protected Ship A does NOT fire; old snapshots would load byte-clean and be misread at 10⁸ scale. Version bump is the ONLY guard. But the R3 mechanics row was CONSUMED by Ship A (13/9/6 landed, verified `PortfolioController.hpp:2026`/`ShardedSnapshotPersist.hpp:94`/`Portfolio.hpp:518`), acceptance row 332 still reasons via "decimal `sizeof(FPN)`/layout change" (now FALSE post-A), and the layout-coupled-version test is specified as firing "in the same ship `sizeof(FPN)` changed" — which Ship B does NOT. **Fix:** add an explicit Ship-B R3 row — bump all 3 snapshot versions current+1 at code time (13/9/6 → 14/10/7 by today's HEAD; re-derive at code time per D-144 discipline) + extend the version-test trigger wording to "stored-integer SEMANTICS change (scale/radix), not only sizeof" + H21 tombstones.

## FOCUS items — MISSING vs PRESENT-but-scattered

| Item | Status | Detail |
|---|---|---|
| Ordered Ship-B step sequence | **MISSING (integrated)** | parts exist (sidecar #1→#6 order; line-35 list; B1-B6; pre-coding triggers) but no section binds them into ordered phases with a first code move |
| Per-step file targets | PRESENT-but-scattered | blast-radius + B1-B6 + relocation set carry file:line for essentially every site (verified) — organized by FINDING not by STEP; binding = part of the sequence section |
| New-fn sidecar linkage (D-93) | PRESENT / **sidecar STALE** | linked (line 124 + cross-refs; closing line names D-93 audits on #4/#5/#6) — but sidecar frontmatter still says "DRAFT — step 5; remaining = prove divmul + step-6 fold + step-7 audits" (all three DONE), cites D-122..D-129 as authoritative (log runs to D-167), and never marks #1/#2 LANDED at E.0.7/E.0.8 nor bridges FPN→FPN_Binary |
| Rollback anchor + tag plan | PRESENT-thin | trigger 5 + A.5 tag boundary + monotonic-at-ship policy (ACCEPTED); name the `pre-<tag>` anchor inside the sequence section |
| Golden-regen procedure (D-100) | PRESENT-but-scattered | gate CONTENT complete (§ golden-EPOCH 3 components + oracle on disk + regen command at `check_fp_determinism.sh:13-15` + acceptance rows) — no single ordered procedure: D-100 gate GREEN → regen which goldens → refreeze `fp_determinism_golden.txt` → Check F re-run un-bypassed |
| Model-retrain checklist (M4) | **MISSING (artifact)** | referenced 3× (M-row "training_fingerprint re-embed in the retrain checklist"; B-δ "epoch-invalidation pre-retrain checklist"; acceptance "Stamp/model retrain done") — the checklist is never ENUMERATED anywhere; no doc exists |
| Check-F un-bypass (D-157) | PRESENT-thin | named once (line-35 REMAINING); procedure is 2 lines (regen golden per documented command; commit WITHOUT `SKIP_DETERMINISM_CHECK=1`) but appears nowhere; **no acceptance row** — row 334 covers only ".E.0.1 gates GREEN on the binary side", which a bypassed Check F would not contradict. Also pin the timing sentence: refreeze+un-bypass AT Ship-B close; D-161/TECH_DEBT-159 re-pack rides that-or-after |

## Effort-vs-scope reconciliation (C.7)

No effort claims exist → nothing to reconcile → YELLOW contributor per skill mapping. Reconstructed scope = ~9 work clusters: (1) `<10,8>` instantiation+SCALE (small — traits already exist :100-102); (2) #3 wire-in (small — proven); (3) #4 helper + replay==production differential (med); (4) #5 FromString + 5-6 parse sites incl. C4/B6 fill+`Reconcile.hpp:544-546` (med); (5) #6 quantize+MIN_NOTIONAL+wire-string (med); (6) B1 commission-carry + B2 fee-site routing 10+ sites (med-high); (7) ~12 D-103 casts + B4 price-domain decision (med); (8) B3 dispatcher decimal branches + coverage-tool + stamp emit + ~30 cfg rows (med); (9) FP64 absorb + persistence round-trip test + D-100 gate + golden regen + retrain + un-bypass (med-high). Ship-A-scale, multi-session. Plan should carry coarse per-phase sizing so the operator can slot sessions.

## Recommendations

### Must fix before coding (~1 plan-editing session; no decision re-opens)
1. **[HIGH·cold-pickup C.2/C.3]** Add a "Ship-B execution sequence" section: Step 0 = `FPN_*` op-family naming decision (D-163 deferral — gates all new fn names) → ordered phases binding #3→#6 compounding order + B1-B6 + D-103 casts + B3 dispatcher branches + FP64 absorb + persistence/versioning + close ritual (D-100 gate → money-golden regen → refreeze → Check-F un-bypassed commit → retrain → tag). Bind existing file:line enumerations to steps; name the first code move and the `pre-<tag>` anchor.
2. **[HIGH·format-drift Check 46]** Explicit Ship-B snapshot-version row: 3 constants current+1 at code time (today 13/9/6→14/10/7); rewrite acceptance-row-332 rationale (semantic scale flip at SAME sizeof — static_asserts will NOT fire; version is the only guard); version-test trigger extended beyond sizeof.
3. **[MED·procedure+acceptance D-157/D-100]** Add the 4-step golden-regen/un-bypass procedure + a NEW acceptance row: "Ship-B close commit runs Check F UN-bypassed (no `SKIP_DETERMINISM_CHECK`); `fp_determinism_golden.txt` refrozen; D-161/TECH_DEBT-159 re-pack gates on this moment."
4. **[MED·cold-pickup M4]** Enumerate the retrain checklist (≈6 steps): flatten positions (B-ζ) → retrain per `core_N_model_dir` → `training_fingerprint` re-embed → re-stamp + HMAC verify → strict-mode load test (Check 17) → record epoch in CHANGELOG.

### Worth fixing during coding
5. **[MED·staleness]** Re-stamp the #4/#5/#6 sidecar (status → post-A.5; D-log range → D-167; mark #1/#2 SHIPPED, #3 PROVEN-awaiting-wire; FPN→FPN_Binary bridge note).
6. **[LOW·C.4]** Name the #4 rounding helper at Step 0 alongside the naming decision.
7. **[LOW·C.7]** Coarse per-phase effort tags on the new sequence section.

### Acceptable risk (don't block)
- Tag name TBD (monotonic-at-ship policy, D-88/D-108). B5 absence from B-series in body (fix-in-plan, verified applied). Pre-coding triggers 1-2 stale-but-done (checked-off state obvious from banners).

## Map updates (post-coding reminders)
- `./tools/gen_code_map.sh` regen after Ship B (new fns: divmul wire-in, rounding helper, FromString, Quantize, casts).
- INVARIANTS_MAP: new rows for D-100 gate + storage≥venue_precision static_assert + saturate-not-wrap money posture (flag-loud per D-147 deferred half).

## Verdict: **YELLOW**

Decision/findings/acceptance layers are exemplary — re-audited to HEAD same day, 9/9 anchors exact, every finding dispositioned, oracle + proof artifacts on disk. The gaps are all in the EXECUTION-SEQUENCE layer (exactly the FOCUS question): a fresh coding session has everything it needs to know WHY and WHAT, but must reconstruct the ORDER, the close-ritual procedures (regen/un-bypass/retrain), and one sharp edge (same-sizeof version bump) from scattered fragments. Items 1-4 ≈ one plan-editing session; then GREEN.
