---
type: readiness-report
audited_plan: subplans/2026-05-30-v5.15.5.F.4d.1.E-money-numeric-core-foundation.md
ship: "#11 numeric-foundation unification (decimal money + unified FixedPoint<RADIX,FRAC>)"
date: 2026-05-31
auditor: /readiness Layer-2 (invoked by /accept-handoff Stage 6; deep pass)
gate_position: pre-coding step 5 (new-fn DESIGN pass) — NOT a code-readiness gate
engine_head: 3f415a0 (feat/v5.15-live-readiness)
verdict: YELLOW
verdict_meaning: "step-6 plan amendment pending before coding — NOT pickup-blocked; the step-5 design pass does NOT require a GREEN plan body"
supersedes: the inline Stage-6 light pass (preserved findings corroborated below)
---

# /readiness report — money-numeric-core foundation (#11) — 2026-05-31 (Layer-2 deep pass)

> **READ THIS FIRST — verdict interpretation.** This is a PRE-CODING pickup at gate **step 5
> (new-function DESIGN pass)**, not a code-readiness gate. The intervening steps 6 (amend the
> plan body for the 5 CRITICALs + 4 forks + MED/LOW dispositions) and 7 (`/blindspot-scan` +
> re-fire `/precoding-audit-gate` on the AMENDED plan) sit before any code (step 8). A **YELLOW
> verdict here means "the step-6 amendment is pending before coding" — it does NOT mean pickup is
> blocked.** The design pass (step 5) does not require a GREEN plan body; it requires the
> architectural decisions settled (they are — D-97..D-124) and the surfaces enumerated (they are).
> This is the EXPECTED, CORRECT outcome for a step-5 pickup, and it explicitly avoids the
> canonical `.E` Session-4 D-105 false-positive (re-flagging settled decisions as open blockers).
>
> **Relationship to the inline light pass:** a lighter `/readiness` ran inline at /accept-handoff
> Stage 6 and independently reached YELLOW + flagged the same stale-prose finding. This deep pass
> SUPERSEDES it (subsumes its verdict, extends its dependency table to grep-confirmed file:line, and
> adds the propagation/drift/cold-pickup-triad layers + 2 NEW findings + 1 extension). The
> corroboration of the prior pass's verdict + stale-prose finding is itself a signal the verdict is right.

## Plan summary

- **One ship** (`#11` numeric-foundation unification), internally phased P1-P5 (D-108: cannot split
  — phase-gate instead). Plan_type `refactor` (structural core unification + bug-class closure)
  with a `feature` edge (decimal money correctness + tick/lot quantization).
- **Branch:** `feat/v5.15-live-readiness`. **Tag:** assigned monotonic-at-ship (D-88/D-108; the
  `.E.0.6` placeholder was consumed by the determinism-net ship).
- **Predecessor:** `.E.0.1` (= tag E.0.6, SHIPPED 2026-05-31, commit `3f415a0`) — THE NET this ship
  runs under. **Successor:** `.E.1` (Core→Node rename + multi-exchange) — lands on #11's final shape.
- **Decision state:** D-97..D-124 ALL settled/landed (verified via sentinel map). The 4 implementation
  forks (C1/C3/C4/H2) RESOLVED (D-122/123/124). The genuinely-OPEN decision list is **EMPTY**.
- **The triad under audit** is {plan body + decision log D-97..D-124 + handoff} — the handoff supplies
  the step-5 design agenda (6 new-fn clusters), the 4 forks, the 6 edge-bites, and the P1-P5 phasing.

## Checklist verdicts (10-item from CLAUDE_REVIEW.md + numbered checks)

| # | Item | Verdict | Notes |
|---|------|---------|-------|
| 1 | Hot path purity | PASS | Audit-confirmed: 500ns steady path does money COMPARES not mul/div; the 3 hot money-muls (`ExecutionCore.hpp:543/549/570`) are rare-entry-branch (`__builtin_expect`-cold). Gate H1 correctly notes the decimal *reduce* is a `__udivti3` libcall, but it's bounded by rare-entry; folded to D-93 design pass (`divmul_pow10`). To be re-proven by `calls_graph_diff` at ship. |
| 2 | Train-serve parity | GAP (step-6) | The cfg-struct layout change flows into `Fingerprint_Compute` (raw SHA over `cfg_ptr`, `Fingerprint.hpp:180`) + forces MODEL retrain (`MODEL_FORMAT_VERSION` currently 6). Plan names retrain (P4 epoch) + stamp reshape + golden regen (D-100). **M4 gap CONFIRMED + EXTENDED below** (`training_fingerprint` re-embed). Both `BacktestSharded_Run` and `EngineSharded_Run` see the same `FixedPoint<10,8>` money type — symmetric by construction. |
| 3 | Surface area | PASS | Blast radius is a bounded, enumerated table (~8 surfaces, audit-ratified by 3 Session-4 sweeps + the 7-agent gate). NO `if (engine_arch==)` / `if (live_trading)` proliferation — the domain split is TYPE-driven, not branch-driven. O-1 strong-typing makes the boundary compile-enforced. |
| 4 | Pointer init / heap lifecycle | PASS | No new heap state; `FixedPoint<R,F>` is POD-by-value (H1). |
| 5 | Backward compat | GAP (step-6, mechanical) | `SHARDED_SNAPSHOT_VERSION` (currently **8u**, verified `ShardedSnapshotPersist.hpp:94`) bump to 9 is implied ("old snapshots version-rejected") but the explicit 8→9 value is ABSENT from acceptance (= gate L1). `MODEL_FORMAT_VERSION` bump implied via retrain but not named with a value (→7). Both deliberate-epoch (D-100), correctly framed as not-back-compat. |
| 6 | Multi-threading | PASS | No new thread / shared state / atomic. The type flows through existing threads; cross-thread field count unchanged. |
| 7 | Test coverage | PASS (high-level) | "Tests changed" section present (Check 45): NEW (decimal-exactness differential / fees-PnL hand-ref / round-trip / static_assert / quantize / boundary-cast), Modified (mechanical type swap, binary assertions PRESERVED), Broken-replaced (money goldens REGENERATED at epoch — deliberate, `/test-strength-audit` distinguishes). Detail at code-time per the section's own note. |
| 8 | Docs + invariants | PASS (deferred-correctly) | CLAUDE.md H4 always-loaded update (FPN-for-accounting → decimal-money/binary-features) tracked in the codification slate to land WHEN code matches reality (correct per pattern-codification-lifecycle). CHANGELOG at ship close. |
| 9 | Forward maintenance | PASS | The unification IS the forward-maintenance win (one core; venue = 1 row). Gate H4 correctly de-scopes FOREACH_EXCHANGE to `.E.1` (compile-time scale CONSTANT + guard + `FPN_Quantize` off already-loaded `SymbolFilters` at #11). |
| 10 | Rollback story | PASS | Pre-tag rollback anchor in pre-coding triggers (item 5). B-ζ operational note: FLATTEN positions before deploy (no warm-restart across epoch) — LANDMINES entry promised. |
| 15 | ML feature-change parity regression | GAP (step-6) | Cfg-struct reshape → `Fingerprint_Compute` raw-SHA flips → ALL stamped models mismatch (intentional, the epoch). Plan names retrain. **EXT-M4 (below): name the `training_fingerprint` re-embed (`ModelInference.hpp:511`) in the retrain checklist explicitly + assert it.** |
| 16 | New stamp-bearing cfg → recipe doc | PASS | No NEW cfg field; the ~30 money cfg fields change TYPE (decimal). Recipe-doc impact = the H4 always-loaded update (slate). |
| 17 | Model-load path → strict-mode test | PASS | Model-load path unchanged structurally; HMAC verify present (`ModelInference.hpp`); the 3-tier strict-mode is not touched, only the stamp BODY reshapes. Post-retrain HMAC-verify is an acceptance criterion. |
| 29 | Mechanical citation drift | DRIFT (mechanical; step-6) | Gate L1 enumerated ~11 drifts (incl. `Fingerprint.hpp` 180-not-181 — the plan body SELF-NOTES this at line 154). Independently confirmed `Fingerprint.hpp:180` is the raw-SHA site. Non-blocking; refresh at step-6. See sub-section below. |
| 32 | Plan-body symbol-existence | PASS | Satisfied by the `check_session_docs.sh` pre-pass at /accept-handoff Stage 5 (SWEEP CLEAN). Not re-derived. |
| 34 | Audit tier declared | PASS | `audit_tier: HIGH-RISK` in frontmatter; matches the heavier-default capital posture (D-77). 7-agent gate fired. |
| 45 | Tests-changed section | PASS | Section present (see #7); mechanical floor satisfied by pre-pass. |

## Dependency verification (blast-radius citation spot-check — grep-confirmed at HEAD)

| Claimed dependency (plan/synthesis) | Verified at HEAD | Verdict |
|---|---|---|
| `BinanceCrypto.hpp:744-745` `FPN_FromString` parse | `:744` `out->price = FPN_FromString<F>(price_str)`; `:745` volume | ✅ PASS (parse pair present; price at 744) |
| `OrderManager.hpp:1186-1194` `handle_sell_fill` | `:1186` `Portfolio_CloseSlot` gross + `:1187` `FPN_Mul` exit_notional + fee muls + `FPN_Sub` net | ✅ PASS (exact body) |
| `OrderManager.hpp:1142-1144` LIVE fee COMPUTE (C3/F-A) | `:1142` `handle_buy_fill` → `:1144` `FPN_Mul(notional, entry_rate)` | ✅ PASS — **C3 CONFIRMED: LIVE computes the fee, does not book reported** |
| `CfgFieldDispatch.hpp:471` `StampT` static_assert | `:475` `static_assert(std::has_unique_object_representations_v<StampT>, "F-076/H12: ...")` | ✅ PASS — **C5 CONFIRMED: decimal padding would FAIL this exact build gate** |
| `Backtest/Fingerprint.hpp:181` raw SHA over cfg | `:180` `SHA256_Update(&s, cfg_ptr, cfg_size)` | ⚠️ DRIFT — actual **180** not 181 (plan self-notes; gate L1) |
| `ShardedSnapshotPersist.hpp` raw-fwrite money fields | `:182/185-187/195-196` `fwrite(&ctx.<f>, sizeof(FPN<F>), 1, f)` for allocated_balance/core_realized/core_fees/core_open_notional/gross_wins/losses | ✅ PASS — D-110 recovery surface confirmed (magic+version-gated, NOT HMAC) |
| `FixedPointN.hpp:47` `_padding` mirror (C5 fix model) | `:47` `int32_t _padding = 0; // explicit zero-init padding` | ✅ PASS (the canonical H12 pattern to mirror on the decimal struct) |
| D-102 producer carry: `Async.hpp:179-180` `FPN_FromDouble` | `:179` `t.price = FPN_FromDouble<F>(price_d)`; `:180` volume | ✅ PASS — the lossy double re-derive seam |
| C4 fill path: `OrderResult` double + adapter | `BinanceUserData.hpp:339` `binance_json_extract_double(json,"l")` → `:370-371` `result.avg_fill_price/fill_qty` (double) | ✅ PASS — **C4 CONFIRMED: lossy at string→double (`:339`), BEFORE any cast → O-1 won't catch it** |
| M6 `last_realized_return[]` double | `OrderManager.hpp:336` `double last_realized_return[MAX_PORTFOLIO_POSITIONS]` | ✅ PASS (signal-domain; H4-exempt disposition correct) |
| H2/D-124 `ema_price` muls | `Async.hpp:263-264` `FPN_Mul(ema_price, ema_alpha)` + `FPN_Mul(t.price, one_minus_alpha)` | ✅ PASS — D-124 resolves ema_price=binary feature → no producer-path decimal libcall |
| M2 balance overwrite + boot reconcile | `OrderManager.hpp:1410` `FPN_FromDouble(exchange_balance)`; `Run.hpp:653` `FPN_FromDouble(usdt_recovered)` | ✅ PASS (double→FPN money boundaries; D-100 gate disposition correct) |

**Triad-citation existence (cold-pickup):** predecessor `.E.0.1` plan body ✅, `.E.0.3` STUB ✅,
dependency-graph ✅, MASTER ✅, the `.E.0.1-new-function-designs` sidecar the handoff cites ✅,
TECH_DEBT-144/145/146/147/149 + F-107 all present in the workspace ledger (`DOCS/tech-debt/open.md`) ✅.

**No phantom/stale symbol citations.** Every load-bearing blast-radius anchor resolves to roughly
what the plan claims. The ONE numeric drift (`Fingerprint.hpp` 180 vs 181) is self-noted in the plan
body and is NOT load-bearing for the design pass.

## Hidden scope detected (NEW — beyond the gate's 14 findings + 6 bites)

The 7-agent gate (parity/trace/merge/dod/accounting/registry-fit/hft) was comprehensive on the
money DATA paths and the gate's completeness-critic added the operational edges. My value-add layer
(10-item + cold-pickup + propagation + drift sub-categories the gate under-covered) surfaced
**two genuinely-NEW items** and **one extension** of a gate finding. Everything else I checked
re-converged on the gate's existing 14+6 — the useful negative result: the gate was thorough.

- **N-1 [LOW·mechanical·step-6] — `MODEL_FORMAT_VERSION` bump value not named in acceptance.** The
  gate's L1 named the `SHARDED_SNAPSHOT_VERSION` 8→9 omission; the symmetric `MODEL_FORMAT_VERSION`
  bump (currently **6**, `ModelInference.hpp:134`) is implied by "stamp/model retrain" but no target
  value (→7) appears in the acceptance criteria. Propagation-check (SKILL.md "New version constant
  bump" row): the bump must land in CHANGELOG + a test for old-version rejection. The model side
  ALREADY HAS old-version rejection (`ModelInference.hpp:500` `if (model_ver != MODEL_FORMAT_VERSION)`),
  so this is purely "name the bump value in the acceptance list." **Does NOT change the step-5 design;
  step-6 line-item.**

- **N-2 [LOW·structural·step-6] — `Fingerprint_Compute` flips for TWO reasons; plan attributes one.**
  `Fingerprint_Compute` hashes BOTH the raw cfg struct (`:180`, reshaped by the decimal type) AND
  `MODEL_FORMAT_VERSION` (`:183`). So the fingerprint flips for TWO independent reasons under #11
  (layout change + version bump). Both intentional, but the plan's drift story describes only the
  layout-change reason. A one-line note completes the "why every stamp mismatches" rationale. **Does
  NOT change the step-5 design.**

- **EXT-M4 [MED·structural·step-6] — extends the gate's M4.** Gate M4 noted `training_fingerprint`
  re-embed missing from the retrain checklist. I CONFIRM + EXTEND with the file:line + assertion:
  `ModelInference.hpp:511` (`strncpy(m->training_fingerprint, fp, 64)`) embeds the SHA-of-config-at-training
  into the model struct's 65-byte `training_fingerprint` field (`:395`). After the cfg layout changes, a
  model retrained under #11 carries a NEW `training_fingerprint`; a model NOT retrained carries a stale
  one that no longer matches `Fingerprint_Compute` over the new cfg (M5 train-serve parity). **The P4
  retrain checklist must NAME the `training_fingerprint` re-embed as a step, AND the D-100 gate should
  ASSERT the re-embedded fingerprint == a fresh `Fingerprint_Compute` over the new decimal cfg layout.**
  **Step-6 amendment (P4 checklist line + D-100 gate row).**

**No NEW design-changing (step-5) gaps found.** All three NEW/extended items are step-6
plan-amendment line-items, consistent with the gate's YELLOW.

## Cold-pickup completeness (C.1–C.10) — assessed over the {plan + decision-log + handoff} TRIAD

| # | Field | Verdict | Notes |
|---|-------|---------|-------|
| C.1 | Branch state | PASS | `feat/v5.15-live-readiness` named in plan + handoff; matches current operator practice (no "create new branch"). |
| C.2 | Phase order matches dependency order | PASS | P1-P5 explicitly dependency-ordered (handoff §4: P1 byte-identity STOP-gate before money; P2 decimal type; P3 migrate+rounding; P4 epoch retrain; P5 persistence). Steps 4-before-3 in the pre-coding sequence is explicitly rationalized (handoff §1). |
| C.3 | First concrete move | PASS | Handoff §10 "First action": begin step-5, "start with the unified template + the int128 shared-mul + `divmul_pow10`, since C1=A is the spine." Mechanical + explicit. (For a pre-gate DRAFT, the "first move" is the design pass, not a code Step 0 — correct.) |
| C.4 | Function/constructor names cited | PASS | The 6 new-fn clusters named (handoff §3): `FixedPoint<RADIX,FRAC>`, canonical rounding helper, `divmul_pow10`, decimal `FromString`, `to_binary()`/`to_decimal()`, `FPN_Quantize`. Existing bodies to reuse cited with file:line. |
| C.5 | File:line for cited tests/baselines | PASS | The `.E.0.1` locked golden is the diff baseline (the NET); blast-radius sites carry file:line; D-100 external oracle (Python `decimal`) flagged as confirm-or-build at step 5. |
| C.6 | Stale-claim audit | YELLOW (mechanical) | One INTERNAL contradiction confirmed (line 29) + 3 satellite stale refs (107, 255, 262). All pre-amendment artifacts the gate flagged; non-blocking for the design pass but MUST clear at step-6 so a future cold pickup isn't misled into thinking decisions are open. See § "Stale-prose scope." |
| C.7 | Effort claims reconcile | PASS | No "~N LOC" claims to falsify (the plan deliberately carries NO target LOC per `feedback_plan_body_length_no_target_loc`). Blast-radius counts (42 accounting sites, ~30 stamp fields, ~9 persist fields) are audit-ratified. |
| C.8 | Source-audit references | PASS | Cites the 3 Session-4 agent sweeps + the gate synthesis + decision log D-97..D-124 (all on disk + verified). |
| C.9 | Predecessor/dependent plans named with paths | PASS | `.E.0.1`, `.E.0.3` STUB, dependency-graph all cited with paths + verified present. |
| C.10 | Tag names locked | PASS (deliberate) | Tag = monotonic-at-ship (D-88/D-108) — deliberately NOT pre-assigned. Rollback anchor (pre-tag) in pre-coding triggers. |

**Cold-pickup verdict: the TRIAD is fresh-session-complete.** A cold session loading
{plan + decision-log + handoff} via `/accept-handoff` has: the settled architecture, the 4 forks with
rationale, the 6 new-fn design agenda items, the P1-P5 phasing, the blast-radius file:line inventory,
the operational landmine, and the explicit "begin step 5, start with X" first action. The ONLY
cold-pickup blemish is C.6 (stale prose) — mechanical, step-6, non-blocking. **8.5/10 cold-pickup
items clean → GREEN on the cold-pickup axis per SKILL.md "encourage rather than gate" (the missing
1.5 = stale-prose, flagged for step-6).**

## Stale-prose scope (mandate item 4 — CONFIRMED; line 29 is NOT the only one)

Line 29 is the PRIMARY contradiction, but there are 3 satellite stale refs — all the same root cause
(the doc was written as decisions were settling, and the "pending" framing in a few satellite spots
wasn't swept when O-1/O-2/O-3 + R-1 resolved same-session). The inline light pass flagged the
frontmatter `status:` + § "Why this ship exists" angle; this deep pass enumerates the full set:

| Line | Stale text | Reality | Severity |
|---|---|---|---|
| **29** | "the ship sections are DRAFT pending **3 open decisions (§ Open decisions)** + 1 research line" | § Open decisions is titled "**RESOLVED 2026-05-30**"; O-1/O-2/O-3 + R-1 all settled (D-107/108/109/110); frontmatter line 6 says RESOLVED | PRIMARY — directly contradicts the same doc's § Open decisions + frontmatter |
| 107 | "**this is open decision O-3**" (FRAC semantics) | O-3 SETTLED (low-stakes, resolve at code-time per § Open decisions); the value is decided (`SCALE = RADIX^FRAC`) | satellite — same root |
| 255 | "Subsumes/reshapes: `.E.0.3` STUB — **pending O-2**" | O-2 SETTLED (D-108): `.E.0.3` folded into #11, STUB RETIRED | satellite — same root |
| 262 | footer "Ship plan = DRAFT **pending O-1/O-2/O-3 + R-1**" | all four RESOLVED | satellite — same root (footer mirrors line 29) |

Lines 4 (`ship_tag: TBD-monotonic-at-ship`) and 6 (`DRAFT v0.1 ... pending ONLY its own
/precoding-audit-gate + /blindspot-scan + new-fn design-audit`) are **NOT stale** — accurate (tag is
genuinely assigned at ship; the gate fired; the design-audit IS step 5, the resume point). **All 4
stale lines are step-6 cleanups; none blocks the step-5 design pass.** They matter only because a
FUTURE cold pickup reading line 29 in isolation could mistakenly re-open settled decisions (the
D-105 trap) — so clearing them at step-6 is worth-it hygiene. (Note: line 6 frontmatter `status:`
already reads "decisions SETTLED 2026-05-30 ... O-1/O-2/O-3 + R-1 all RESOLVED" — so the frontmatter
is CORRECT; it's the BODY prose at 29/107/255/262 that lags. The inline pass's "fix the frontmatter
status" recommendation is therefore slightly mis-aimed — the frontmatter is already right; the body
prose is what needs the sweep.)

## Drift audit (8 sub-categories — emphasis per mandate item 3: money TYPE + stamp wire + retrain)

| # | Category | Verdict | Notes + fix coherence |
|---|----------|---------|------------------------|
| 1 | **Feature drift** | DRIFT-SAFE | The decimal money type does NOT add/remove/reorder ML feature fields — features STAY binary `<2,64>`, byte-identical to the `.E.0.1` golden BY CONSTRUCTION (C1=A hoist, D-122). The cfg-struct layout change flips `Fingerprint_Compute` (intentional epoch), but the FEATURE shape is unchanged. Both backtest + live build the same shape. **Story coherent.** |
| 2 | **Label drift** | PASS | Labels untouched (`LabelFunctions.hpp` not in blast radius). |
| 3 | **Metric drift** | DRIFT-SAFE (with EXT-M4) | The realized-PnL/balance metric chain changes representation symmetrically (production `OrderManager.hpp:1186-1194` + replay `ControllerEventLoop.hpp:862-890` both route through the ONE canonical rounding helper — D-105/C2). Gate C2 correctly reframes "(all round)" as INTRODUCE + adds the replay-equals-production differential. **The `training_fingerprint` metric (EXT-M4) needs the explicit re-embed step + assertion.** |
| 4 | **Path drift** | PASS | No symlink/rename/versioning indirection introduced for companion files. |
| 5 | **Format drift** | DRIFT-BUG → fix-in-ship (deliberate epoch) | THREE formats reshape: (a) stamp wire body (~30 money fields, emit exact-decimal not `ToDouble→%.17g`); (b) `SHARDED_SNAPSHOT_VERSION` (8u→9, **value not yet named — N-1/L1**); (c) `MODEL_FORMAT_VERSION` (6→7, **value not yet named — N-1**). All deliberate-epoch (D-100), old readers version-reject cleanly. **Story coherent EXCEPT the two version-bump values must be named in acceptance.** |
| 6 | **Threshold drift** | DRIFT-SAFE | The EGRESS binary→decimal threshold casts (`StrategyParameters.hpp:347/428/511/634`) become explicit O-1 `to_decimal()` casts (compile-enforced). `qty_decimals` dual-home (gate M5) folded into H4 (declare precision-SSoT). |
| 7 | **Tick-source / time-source drift** | DRIFT-SAFE → HARDENED | D-102 producer carry-through (`Async.hpp:179-180`) — the plan KILLS the `string→FPN→double→FPN` detour, carrying the parsed decimal straight into the `Tick` ring. Drift-HARDENING (the current double detour is lossy for binary TODAY). Backtest parse (`BacktestSharded.hpp:84-85`) + depth (`BinanceDepth.hpp:163`) route through the same decimal `FromString`. |
| 8 | **Build-flag drift** | DRIFT-SAFE (firm-in-P1 required) | `USE_NATIVE_128` default-ON (verified `CMakeLists.txt:21`); the golden `<2,64>` runs the FP64 `__uint128_t` specializations. Gate B-ε (folded into C1/D-122): native-128 is COMPUTE-only; stored/wire/snapshot = canonical 2-word 24B layout. **Must be FIRM in P1 or binary byte-identity breaks — the plan's P1 STOP-gate enforces this. Story coherent.** |

**Drift-management story verdict: COHERENT.** Version bumps NAMED (snapshot + model + stamp body),
retrain NAMED (P4 epoch), golden regen NAMED (D-100 with the one-time correctness gate distinguishing
determinism≠correctness). The binary side stays byte-identical (reuse-certified-bodies, structurally
guaranteed by C1=A). The two GAPS are mechanical: (a) name the two version-bump VALUES (N-1 + L1);
(b) name the `training_fingerprint` re-embed step + assertion (EXT-M4). Both step-6.

### Mechanical citation drift findings (Check 29 — non-blocking, step-6 refresh)

| Plan claim | Actual at HEAD | Verdict |
|---|---|---|
| `Backtest/Fingerprint.hpp:181` raw SHA | `:180` `SHA256_Update(&s, cfg_ptr, cfg_size)` | DRIFT — 180 not 181 (plan SELF-NOTES at line 154; gate L1) |
| `SHARDED_SNAPSHOT_VERSION` bump absent from acceptance | current `8u` (`:94`); needs explicit →9 | DRIFT (omission) — gate L1 |
| `MODEL_FORMAT_VERSION` bump value absent | current `6` (`:134`); needs explicit →7 | DRIFT (omission) — N-1 (NEW) |
| (gate L1's other ~8 drifts) | — | enumerated by the gate; refresh wholesale at step-6 |

None is LOAD-BEARING in a way that misleads the step-5 design pass (the design pass works off the
decision log + handoff agenda, not the stale line refs).

## Recommendations

### Must fix before coding (= the step-6 amendment, NOT a pickup blocker)
*(All already on the gate's plate; this section CONFIRMS the gate was comprehensive + adds the NEW
items. None blocks the step-5 design pass — they block the step-7 re-fire / step-8 code.)*
1. Amend the plan body for the gate's C1-C5 + H1-H5 + MED/LOW dispositions (the gate's recommended path).
2. **NEW — EXT-M4:** add `training_fingerprint` re-embed (`ModelInference.hpp:511`) as a named P4
   retrain step + a D-100 gate assertion (re-embedded fp == fresh `Fingerprint_Compute` over new cfg).
3. **NEW — N-1:** name BOTH version-bump VALUES in acceptance: `SHARDED_SNAPSHOT_VERSION` 8→9 (gate L1
   had the snapshot side) + `MODEL_FORMAT_VERSION` 6→7.
4. Clear the 4 stale-prose BODY lines (29, 107, 255, 262) so a future cold pickup can't re-open settled
   decisions (the D-105 trap). NB the frontmatter `status:` is already correct — sweep the body prose.

### Worth fixing during coding
- **N-2:** one-line note that `Fingerprint_Compute` flips for TWO reasons (layout + version) so the
  "why all stamps mismatch" rationale is complete.
- Author the dangling `fp-determinism-canonical-path-discipline.md` sister-spec at step 3 (gate L2 +
  carried-item routing) — confirmed NOT on disk; the "binary stays byte-identical" reuse contract
  currently has no written spec to cite.

### Acceptable risk (don't block)
- Tag-name TBD (D-88/D-108 monotonic-at-ship — deliberate).
- CLAUDE.md H4 always-loaded update deferred to ship-close (correct per pattern-codification-lifecycle).
- The H1 `divmul_pow10` libcall question is a step-5 DESIGN deliverable (correctly folded), not a
  readiness blocker — bounded by rare-entry, and the design pass is exactly where it gets lowered.

## Map-update suggestions (post-coding)
- `gen_code_map.sh` regen — #11 adds many new `Pattern_FunctionName` (the unified template ops,
  `divmul_pow10`, `FPN_Quantize`, the boundary casts).
- `INVARIANTS_MAP.md` — H4 decimal-money invariant is a candidate new row when the H4 update lands.

## Verdict: **YELLOW**

**YELLOW = the step-6 plan amendment is pending before coding. Pickup is NOT blocked.** The
architecture is settled (D-97..D-124; the open-decision list is EMPTY), the surfaces are enumerated
and grep-verified, the cold-pickup TRIAD is fresh-session-complete, and the drift-management story is
coherent. The design pass (step 5 — the resume point) can proceed immediately; it does not require a
GREEN plan body. The amendments (the gate's 14+6, plus my 2 NEW + 1 extension) are step-6 work between
the design pass and any code.

I found **no NEW design-changing (step-5) gaps** — every surface I checked beyond the gate's coverage
either re-converged on an existing gate finding or surfaced a mechanical step-6 line-item. That is the
useful negative result the mandate asked for: **the 7-agent gate was comprehensive on the
design/correctness layer.** My value-add was the propagation/version-bump axis (N-1), the
fingerprint-coupling structural note (N-2), the concrete `training_fingerprint` extension of M4
(EXT-M4), the full stale-prose scope (4 body lines; frontmatter already correct), and the
cold-pickup-triad freshness verification.
