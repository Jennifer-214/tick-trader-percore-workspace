# A-CLASS VERDICT — D2 (PARITY-044 model-side guard): O2 `training_side` key vs S-C `expected_role`-alone

> Saved verbatim at receipt 2026-08-20 (orchestrator write per `feedback_save_agent_reports_verbatim`).
> Final anchor from the agent's closing note: `ModelInference.hpp:1620` — the stamp path derives as `<model_path>.stamp`, and the stamp binds model file CONTENTS by SHA-256 (`:2368` region), so a rename-both-files misuse keeps the stamp valid and reaches the role check — exactly the case the guard must catch.

**Agent:** a-class ADVERSARIAL tiebreaker · engine HEAD `417e524` (`feat/v5.15-live-readiness`) · 2026-08-20
**Target:** D2 fork in `plans/v5.15-live-readiness/subplans/2026-08-20-v5.15.5.F.4d.1.E.1.2.C-ml-verification-program.md` (§ Design space). Inputs attacked: `reports/2026-08-20-ml-verification-program/serve-side-exit-load-and-side-key-guard.md` (§Q4 + option matrix, recommends O2+O1) and `reports/2026-08-20-ml-verification-program/retirement-and-test-blast-radius.md` (§option matrix S-C, rejected there; risks 1/4/7).
**Roots covered by every membership probe** (Landmine 19): `CoreFrameworks/ Strategies/ ML_Headers/ MemHeaders/ DataStream/ FixedPoint/ Backtest/ GUI/ tests/ tools/` + `foxml_suite.cpp main.cpp`. All probes uncapped, rc captured directly (one pipeline-rc attempt was hook-blocked and redone per Class-57). Settled forks honored: convention (a) side=1 ⇒ role file `exit.json` co-located; leg-3 semantics (b); T2 retirement; fan fix B+C — none re-litigated.

## VERDICT LINE

**D2: O1-ONLY(S-C-with-fixes)** — enforce the existing `expected_role` key at the `NodeModelZoo_TryLoadRole` chokepoint; do NOT mint `training_side`. Three named fixes are mandatory parts of the verdict (without them S-C is genuinely insufficient, and the retirement report's rejection of bare S-C stands):

1. **F1 — FV re-stamp derivation** (~10 LOC): in `fullvalidation_worker_fn`, after the `auto_stamp_path` copy at `Backtest/BacktestPanels.hpp:3534`, derive `fv_results.req_role` from the basename stem of `model_path_snap` when it exactly matches one of the four role names (`barrier`/`regime`/`exit`/`buy_signal`); otherwise leave empty (legacy behavior). This closes the ONLY production emit path that omits the key.
2. **F2 — the enforcement** (O1): compare `sr.expected_role` vs the `role_name` param already in scope (`ML_Headers/NodeModelZoo.hpp:189-190`), placed with the `model_num_outputs` sibling (`:479-500` is the exact shape: `STAMP_HAS` gate → strict REFUSE with `Model_Free`+`Model_Init` / non-strict WARN), per the decision table below. WARN arm sets a NEW `FOREACH_FAILURE_MODE` bit — **name it `ml_role_mismatch`, not `ml_side_mismatch`** (the comparison is role-vs-slot; a side-named bit would misdescribe the check) — on `handle->drift_flags_at_load`, riding the fixed dual-walk aggregation (`CoreFrameworks/ShardedSnapshot.hpp:703-747`) per the serve report's Q5 template, avoiding its single-zoo-only defect (`:667-676`).
3. **F3 — trainer-side side×label gate** (the O4 concern, moved to the producer): at the training click handlers, side=1 with a label outside the allowed exit set refuses/warns BEFORE training. No wire key. Proposed initial set: allow {WILL_PEAK, PEAK_VALLEY_STABLE}; WARN (not refuse) on {WILL_VALLEY, VOL_BARRIER} pending operator triage; refuse {WIN_LOSS, FORWARD_PNL, REGIME, CS_*} (`Backtest/LabelFunctions.hpp:83-96` is the full 11-row universe).

## Required output 1 — post-change production emit-path enumeration for `expected_role`

The emit is CONDITIONAL, verified: `ML_Headers/StampHelper.hpp:411-413` `if (args.req_role && args.req_role[0]) STAMP_PUT(...)`, default `""` at `:132` ("no expected_role emit"); absent means has-bit unset in the wire body (legacy pin `tests/controller_test.cpp:23516-23517`). The production funnel is closed: non-test `Stamp_AssembleAndEmit` callers are exactly `Backtest/BacktestEngine.hpp:1440` (RFV) and `Backtest/BacktestPanels.hpp:4059` (dead worker); `stamp_write_for_model`'s only non-test caller is `StampHelper.hpp:447` inside the funnel (uncapped sweeps, rc=0). RFV callers: `BacktestPanels.hpp:3557` (FV worker) and `:4457` (mh) — nothing else outside tests.

| # | Path | `req_role` post-change | Key present? |
|---|---|---|---|
| 1 | mh serial — Train Model N=1 (`:5875` → `:4913-4922` → `mh_run_one_horizon_fv`) | set UNCONDITIONALLY at `:4360` from `role` (`:4291-4293` + the leg-3 side arm); never empty | **YES, always** |
| 2 | mh parallel — Train Multi-Horizon (`:6080` → `:4638-4651` → same fn) | same `:4360` | **YES, always** |
| 3 | **FV worker re-stamp** (`fullvalidation_worker_fn:3475`) | `memset(&state->fv_results,0,...)` at `:3526`; only `auto_stamp_path/secret/format_version/req_label_*` populated (`:3528-3555`); `req_role` NEVER assigned → `""` | **NO — the hole. F1 closes it** |
| 4 | dead worker (`train_model_worker_fn`, StampArgs `:4029-4063`) | no `args.req_role` assignment (verified read) | NO — but ZERO callers (trainer report headline 1); slated for deletion (plan fold #2/D6); cannot produce production stamps |
| 5 | tests | various | out of scope |

**Structural bonus on path 1/2:** `auto_stamp_path` (`:4336-4337`, `"%s/%s.json", horizon_dir, role`) and `req_role` (`:4360`) are generated from the SAME local `role` — filename⟺key coherence is by construction at the producer; they cannot diverge without editing two lines of our own trainer, which the leg-3 pure-helper test pins.

## Attack on O2 (the new `training_side` key) — REFUTED, four grounds

**(a) The redundancy is measured, not hypothetical — and the serve report admits it.** Under settled convention (a), side=1 ⇒ role="exit" and every other role is side=0: a strict bijection at the only live producer. `training_side` is deterministically derivable from `expected_role` on every stamp the system can produce. The serve report's own O2 weakness row concedes "redundant with O1 for every currently-plannable case" and its own O3 warning names "two keys asserting overlapping facts = future drift surface" — then recommends both anyway. That is the single-source-of-truth violation (`feedback_single_source_of_truth_discipline`), recommended into a wire format.

**(b) O2 does not even fix the hole that motivates it.** The conditional-emit weakness the serve/retirement reports charge S-C with is SYMMETRIC: on the one production path that omits `expected_role` (path 3 above), `training_side` would be omitted identically — `FullValidationWorkerArgs` carries no side field, `fv_results` is memset at `:3526`, and nothing would set a hypothetical `req_training_side`. The hole is closed only by fixing the FV worker — and the natural FV fix derives the value from the basename, i.e., **on that path `training_side` could only ever be computed FROM the role name**, which is the redundancy proven at the second site.

**(c) O2 costs a mirror; S-C costs nothing.** O2's load-time check needs a role_name→side map ("exit→1, others→0" per the serve report's own O2 row) — a consumer-side mirror of the trainer's convention that must move in lockstep with any future role addition (Class-18 flavor: parallel encoding of one fact in two places). S-C's `sr.expected_role` vs `role_name` is a map-free identity comparison. Fewer moving parts wins (`feedback_structural_fix_over_belt_and_suspenders`).

**(d) H21 makes the speculative key expensive and the deferred key cheap.** A stamp wire key is append-only-forever (H21; ledger row; `tools/identifier_ledger.txt`). The only future in which `training_side` carries information `expected_role` doesn't is one where role≠side — a convention change that is itself speculative, and the sanctioned future (FUTURE_ML.md MoE rungs, plan § entry-aware-exits DEFERRED) may supersede binary "side" entirely. Both i-class reports establish that a POST_CFG tail-append is a cheap `ADD (ok)` at any later date — so deferring loses nothing (`feedback_dont_generalize_substrate_before_input_space_known`). Minting it now buys a permanent second assertion of a fact we already assert, purely against a producer bug in our own single-site, test-pinned trainer.

## Attack on S-C — the retirement report's rejection is partly a CURRENCY error; the real gaps get named fixes

The retirement report (§option matrix S-C; risk 1) rejects S-C on three claims. Verdict per claim:

1. *"Role ≠ side today; no exit branch exists; an exit-side PVS model gets role 'barrier'."* — **TRUE at HEAD, FALSE for the world the guard ships into.** Leg 3 (settled, same ship, commit C in the retirement report's own ordered checklist) adds the side arm: side=1 forces role="exit" regardless of label kind, including exit-side PVS. The rejection evaluated S-C against pre-leg-3 code; D2 ships WITH leg 3. Rejection ground does not survive.
2. *"Conditional emit → the check would be vacuous exactly where it matters."* — **Real but overweighted:** exactly ONE production path (FV re-stamp) omits the key, and F1 closes it in ~10 LOC. And per attack (b), O2 has the identical vacuity on the identical path — this ground cannot discriminate between the options.
3. *"Making expected_role load-bearing requires making its emit unconditional + redefining role semantics = a bigger wire change than one new key."* — **FALSE against code.** No wire change is needed at all: emitting the existing optional key on one more path is Surface-G additive (registry header discipline, `StampBoundModelConstRegistry.hpp:~30-35`; 45 keys accreted under format version 3 per the retirement report's own Q3), zero ledger events, zero bless. And role semantics are being extended by leg 3 REGARDLESS of D2's outcome — that cost is not attributable to S-C.

**S-C's REAL insufficiencies (conceded, hence "with-fixes" not bare S-C):** (i) without F1, the exit-slot strict absent-key REFUSE would false-fire on legitimately FV-re-stamped exit models, or the cell degrades to WARN; (ii) without F2's pinned table (below) the "conflates file-slot with side" charge stands as an undefined-behavior surface; (iii) `expected_role` genuinely cannot see label semantics — a WIN_LOSS model trained side=1 stamps role="exit" honestly and PASSES — but so does O2 (`training_side=1` is equally honest), so this discriminates NEITHER option and is answered by F3 at the producer, where label truth is actually known.

## Required output 2 — per-case catch matrix

All cases assume S-C-with-fixes (F1+F2+F3); O2+O1 column shown for comparison. "Rename-both" = model + `.stamp` renamed together — the stamp stays VALID because it binds file contents by SHA-256 and its own path derives from the model path (`ModelInference.hpp:1620`, `:2368`); rename-model-only → no stamp found → existing `:310-320` gate handles it before any role logic.

| # | Misuse case | S-C-with-fixes | O2+O1 |
|---|---|---|---|
| 1 | Buy model (barrier/regime/buy_signal stamp) renamed-both to `exit.json` | **CAUGHT** — `sr.expected_role` ∈ buy roles vs `role_name="exit"` → REFUSE/WARN | caught (both keys) |
| 2 | Exit model renamed-both to `buy_signal.json` / `barrier.json` / `regime.json` | **CAUGHT** — "exit" vs buy slot; chokepoint covers all 8 production call sites / 4 role names (`NodeModelZoo.hpp:687/:694/:701/:708`, `:2127/:2138/:2148/:2158`) — R4's full-role concern satisfied by construction | caught |
| 3 | REGIME 4-class in exit slot (serve R4 garbage-loads-clean case) | **CAUGHT** — "regime" vs "exit" | caught |
| 4 | `barrier.json` trained side=1 (the O4-considerations cell) | **MOOT-UNREACHABLE at the producer:** path and key come from the same `role` local (`:4336-4337` + `:4360`); convention (a) forces role="exit" at side=1; divergence requires editing our own trainer against its leg-3 pin. A hand-crafted barrier-stamp on a file named `exit.json` is case 1 (caught). | O2 catches the trainer-edited variant (side=1+role=barrier) that S-C would pass — the ONLY discriminating cell, and it is a guard against our own pinned single-site code |
| 5 | WIN_LOSS / FORWARD_PNL / CS_* model trained side=1 (semantic misuse) | key-PASSES; **caught by F3 at the trainer** | key-PASSES identically — NOT a discriminator; serve report concedes ("no side/role key catches") |
| 6 | Legacy keyless stamp in a BUY slot | **PASSES (skip)** — required legacy tolerance, `label_params` precedent (`:511`) | same |
| 7 | Legacy/keyless stamp in EXIT slot (incl. a pre-key buy model renamed-both) | **CAUGHT in strict** (absent-key REFUSE — exit slots have zero legacy population: `exit.json` producer sweep = 2 comments only, rc=0); WARN+flag non-strict. F1 prevents the false-REFUSE on FV-re-stamped exit models | same policy available; no advantage |
| 8 | Unstamped `exit.json` | strict: already refused at `:310-315` before the role check; non-strict: WARN + absent-key flag | same |
| 9 | Same-role wrong-run/wrong-horizon copy | NOT caught by any role/side key — horizon check (`:511-521`, always-refuse) + grid-member consistency (`:2389-2456`, `:2565-2568`) are the guards. Named as the guard's boundary, both options | same |

## Required output 3 — the shipped decision table (risk 7, pinned)

Comparison: `strcmp(sr.expected_role, role_name)` at the TryLoadRole chokepoint, after `have_sr`, beside the `:479-500` sibling. `role_name` ∈ {barrier, regime, buy_signal, exit}; slot type: EXIT ⟺ `role_name=="exit"`, else BUY. `held_out_gate_strict` ∈ {-1, 0, 1} (`:256-258`, `:267`).

| Slot | Key state | strict=1 | strict=0 | strict=-1 |
|---|---|---|---|---|
| BUY (barrier/regime/buy_signal) | present, == role_name | PASS | PASS | (no sr parsed — check skipped, PASS; existing explicit-skip posture) |
| BUY | present, != role_name | **REFUSE** (`Model_Free`+`Model_Init`+return 0, `:492-494` shape) | **WARN + `ml_role_mismatch` flag + load** | skipped |
| BUY | absent (has-bit 0) | **PASS, skip silently** — legacy tolerance, `label_params` precedent `:511`; NOT a silent fallback (no behavior substituted), so `CLAUDE_ML_INVARIANTS` § refusal-surface is not triggered | PASS, skip | skipped |
| EXIT | present, == "exit" | PASS | PASS | skipped |
| EXIT | present, != "exit" | **REFUSE** | **WARN + flag + load** | skipped |
| EXIT | absent | **REFUSE** — legal because exit-slot legacy population is verifiably zero AND F1 keeps re-stamped exit models keyed; without F1 this cell is a false-fire trap and must degrade to WARN | **WARN + flag + load** | skipped |

Both-arm tests owed per slot type (REFUSE-strict, WARN-nonstrict, legacy-skip-buy, absent-refuse-exit), via production `Stamp_AssembleAndEmit` — never the `:15582` fixture (its own MUST-TOUCH banner).

## Required output 4 — O4 (label-kind wire key + per-slot allowed table): DEFER the key, land F3 now

- The semantic gap is real (case 5) but the wire key is the wrong first tool: label truth exists authoritatively at the trainer, where F3 checks it for free — one site, no wire surface, no H21 commitment.
- The allowed-set itself is genuinely undecided: WILL_PEAK/PVS legal both sides (settled (b)); WILL_VALLEY ("price valleys within N ticks", `LabelFunctions.hpp:89`) and VOL_BARRIER are contested members; CS_* are regression labels. Burning a wire key + load-time table before the operator pins that vocabulary locks in a guess.
- O4's emit would inherit the FV path's identity-loss in a WORSE form than absence: the FV worker passes live panel `state->label_type` (`:3561` → RFV `args.label_kind` `:1400`), so a re-stamp would record a potentially WRONG label claim, not a missing one — and label kind is not basename-derivable, so no F1-style fix exists. Structural argument for deferral.
- Revisit trigger: if hand-managed / third-party model artifact flows ever appear (models not produced by our trainer), the load-time label key becomes worth its H21 cost; tail-append then.

## Residual risks + plan-body corrections owed under this verdict

1. **Plan bookkeeping section is O2-shaped and must be corrected:** "One TTY bless at close (stamp-key 45→46)" and "Commit order A(retire)→B(key)→C(role)→D(walker)" — under O1-ONLY there is **NO new stamp key, NO ledger event, NO bless for D2**; commit B becomes F1+F2 (emit-hole fix + enforcement), and the bless line drops (the retirement report's risk-2 45-vs-46 correction becomes moot). The PARITY-042 queue-order coordination note simplifies for the same reason.
2. **FV re-stamp is identity-lossy beyond role** (pre-existing, now adjacent): it also records CURRENT panel `req_label_*` (`:3553-3555`) and `label_type` (`:3561`) — an FV re-stamp of a co-located `_horizon_H` model with mismatched panel forward_ticks produces a stamp the always-refuse horizon check (`:511-521`) will kill at load. Name it in the plan so an FV-re-stamp refusal isn't misattributed to the new guard; candidate ledger entry.
3. **strict=-1 bypasses the guard entirely** (`have_sr=0`, `:266-267`) — inherited explicit-skip posture, same as every stamp check; state it in the guard's doc comment.
4. **R1 reachability** (serve report, HIGHEST-VALUE) remains the leg-3 gating unknown — unresolved by D2 either way; must be probed before leg-3 codes, per the plan's own gate column.
5. **Failure-bit naming:** `ml_role_mismatch` (per F2 above) — a side-named bit under a role-keyed check would be a born-stale name.
6. **Stale-comment sweep rides along:** `NodeModelZoo.hpp:2349` (`core_N_`→`node_N_`) and `:2243-2246` (VALLEY→STABLE) — already in the serve report's change list; same-commit with the TryLoadRole edit.

## Where I would concede (re-cascade signals)

- If the operator REJECTS F1 (refuses to touch `fullvalidation_worker_fn`), the exit-slot absent-key cell degrades to WARN and S-C's strict story weakens materially — O2 still would not help (attack b), but the overall guard is softer; the table above must ship with the WARN cell instead.
- If convention (a) is ever UNSETTLED (a future where side=1 legitimately emits a non-exit role file), attack (a)'s bijection collapses and `training_side` becomes a real second fact — tail-append it THEN; the mechanics both i-class reports mapped (registry 3-site + `ADD (ok)` + one bless) remain valid verbatim.
- The supplied fork shape itself (guard at the TryLoadRole chokepoint, 3-tier, failure-mode WARN surface) is SOUND — no re-cascade; the only material wrongness found in the inputs is the serve report's recommendation carrying one redundant wire key and the retirement report's S-C rejection resting partly on pre-leg-3 currency plus one false "bigger wire change" claim.
