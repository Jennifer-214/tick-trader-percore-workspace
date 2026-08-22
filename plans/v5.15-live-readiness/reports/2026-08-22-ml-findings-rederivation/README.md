# ML-findings re-derivation (2026-08-22)

Two i-class agents re-derived the LOST 2026-08-21 scan-1/scan-2 reports at HEAD `273cd4c`, fired at
the operator's direction (*"we had a list of findings about issues with the ML side i forgot that
never got saved so use I classes as needed"*). Reports persisted VERBATIM at receipt this time
(`feedback_save_agent_reports_verbatim`), with orchestrator notes marked inline where their open
uncertainties were resolved same-day.

| Report | Replaces | Key outcomes |
|---|---|---|
| `i-class-1-snapshot-vs-live.md` | lost scan-1 | S1-F1/F2/F3/F6 verified FIXED at HEAD (with axes); S1-F11 candidate recovered (**NEW-1** n_estimators hardcode); 7 NEW findings; full SNAPPED-vs-LIVE table; AR-20 chain re-verified + 2 plan-claim corrections (⚠ leaf-4 "four collapse to one", ⚠ leaf-14 whitelist set-equality) |
| `i-class-2-artifact-layout.md` | lost scan-2 | **S2-F9 RECOVERED** (3 divergent acceptance rules, measured matrix — D-a evidence re-grounded); S2-F10/F12 candidates (NEW-10/NEW-12); S2-F3 FIXED; S2-F1 partially re-opened (**NEW-2** family base dirs); 8 NEW findings incl. **NEW-1** zero-tree cancel save (live husk on disk) |

## Same-day dispositions (engine SHAs)

| Finding | Sev | Disposition |
|---|---|---|
| scan-2 NEW-1 (cancelled train saves zero-tree husk over real model) | HIGH | **FIXED** `87a8d61` (save gated on `it_completed > 0`); load-side back-stop WARN landed same-day (`XGBoosterBoostedRounds == 0` → loud husk warning; REFUSE-under-strict = operator call) |
| scan-2 NEW-2 (run_1/prod_0 have no family base dir — bandit state unwritable) | HIGH | **STOPGAP DONE** — `mkdir models/classification/{run_1,prod_0}` 2026-08-22 (same inert-dir class as twins); structural close = D-a |
| scan-1 NEW-1 / S1-F11 (WF+HeldOut hardcode n_rounds=200, ignore snapped n_estimators) | HIGH | **FIXED** same-day (both `n_rounds = hp.n_estimators`; `XGBHyperparams.hpp` coupling comment updated) — restores leaf 4's decided contract |
| scan-1 NEW-5 (train-during-collect UAF direction unguarded) | MED-HIGH | **FIXED** same-day (`&& !run_control->running` on can_train/can_wf/can_hp/can_fv; mh inherits) — completes leaf 6's decided mechanism |
| scan-1 NEW-6 (regression metric discriminant `== 2` unreachable; summaries record accuracy 0.00) | MED | **FIXED** same-day (both sites → `LabelType_IsRegression(label_type)`) |
| scan-1 NEW-4 (HP sweep snaps label_type from combo) | LOW-MED | **FIXED** same-day (→ `run_control->run_config.label_type`, leaf 7's rule at the third sibling) |
| S3-F11 candidate (mid-walk abort leaves stale labels; trainer trains on them) | — | **SUBSUMED by leaf 5** `f317c2d` — the wrapper routes through the batch body (NaN-prefill + rc) |
| scan-1 NEW-2 (neutral-filter divergence: shipped model keeps 0.5s WF/HO drop; also no class weights in mh trainer) | MED-HIGH (↑HIGH if compound reading holds) | **OPERATOR-OWED** — changes shipped-model training composition for BARRIER/VOL_BARRIER kinds (PVS/WIN_LOSS unaffected → current families safe); a-class refute-spot #2 before deciding |
| scan-1 NEW-3 / scan-2 NEW-4 (dead `train_model_worker_fn` ~470 lines; holds the ONLY `.scaler` producer; keeps `model_trained`/S1-F8 semantics alive) | MED-LOW | **couples to D-d** — delete-or-revive as one motion |
| scan-1 NEW-7 (sweep silently no-ops on typo'd key) | LOW-MED | **FIXED** same-day — upfront key probes REFUSE in both sweeps |
| scan-2 NEW-3 (duplicate `node_model_dir` across nodes silently clobbers state — H22-adjacent) | MED | **WARN landed** same-day in `EngineCommon_BootGlobal`; structural close = D-a |
| scan-2 NEW-5/6/7/8, NEW-10/NEW-12, S1-F4 residual, S1-F7, S1-F8, S1-F9, S1-F10 | LOW–MED | homed in the E.1.2.D plan punch list / D-a & D-d inputs |

Consumer-side AR-20 clause (scan-1 § 4): *for a threaded parameter, also grep the callee body for
every field actually being consumed* — close-ritual candidate, noted for the next `/close-session`.
