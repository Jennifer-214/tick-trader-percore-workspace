# /parity-check report — 2026-07-03 — E.1.2 NodeState SoA layout-freeze plan

## Plan summary
- **Target:** `plans/v5.15-live-readiness/subplans/2026-06-15-v5.15.5.F.4d.1.E.1.2-nodestate-soa-layout.md` (status: reformalized-coding-plan v1.0, pre-gate).
- **Engine HEAD:** `b10e778` (= E.1.1 ship `0ee227a` + benign `.clang-format`; engine code byte-identical to `0ee227a`).
- **Audit scope:** wire/persistence identity of the determinism-gated Position/NodeState layout freeze — the LAST foundation leaf. Snapshot BYTES change → this is the highest-stakes lens.
- **Invariants in play:** H9 (wire byte preservation) · H12 (explicit padding) · H21 (append-only wire identifiers / Knight-Capital) · H10 (SIMD fallback byte-identity) · H22 (per-node purity).
- **Cross-check baseline:** `DOCS/PARITY_ISSUES.md` (PARITY-039 restore↔live TP/SL, FIXED .E.0.10 — NOT re-opened by any finding here) + decision-log D-282..D-290 + `wire-format-byte-preservation-discipline.md`.
- **Verdict: RED** — 2 BLOCKING findings must resolve before coding. The plan is well-grounded and its currency-corrections are largely right, but as written it (a) bumps a wire-identifier whose sole emitter it deletes in the same ship (contradicts D-289), and (b) under-specifies the NodeContext serializer such that ~24 flat money-bearing node scalars have no drop-proof walker — the exact D-110 surface the ship exists to close.

**Report note:** these are PRE-CODING PLAN findings (the plan is wrong/incomplete), not discovered runtime code parity bugs → no new `PARITY-NNN` ledger rows allocated (PARITY_ISSUES.md tracks code drift; these resolve by amending the plan). PARITY-039 verified STILL-FIXED, not regressed.

---

## Findings by severity

### BLOCKING-1 (H21 / wire-identifier) — `PORTFOLIO_SNAPSHOT_VERSION` must be RETIRED, not bumped 7→8

**Summary:** The plan's acceptance criteria + Phase G say "bump `PORTFOLIO_SNAPSHOT_VERSION` 7→8". But Phase D (per D-289) DELETES `Portfolio_Save`/`Portfolio_Load` — the SOLE consumers of that macro. Bumping a wire-version whose only emitter you delete in the same commit is incoherent and diverges from the cited decision.

**Evidence (grounded at HEAD `b10e778`):**
- `#define PORTFOLIO_SNAPSHOT_VERSION 7` — `CoreFrameworks/Portfolio.hpp:534`.
- EVERY non-comment reference to the macro: the `#define` (:534), the epoch static_assert (`Portfolio.hpp:540-544`), and inside `Portfolio_Save` (`:558`,`:568`) / `Portfolio_Load` (`:602`). Full `rg` of the symbol confirms zero other functional users. The Position wire embedded in the LIVE snapshot is gated by `SHARDED_SNAPSHOT_VERSION`, NOT this macro (`ShardedSnapshotPersist.hpp` never references `PORTFOLIO_SNAPSHOT_VERSION`; it uses `PORTFOLIO_SNAPSHOT_MAGIC` at `:329` only to REFUSE legacy "TICK" files).
- **D-289 (the cited decision, decision-log `:1836`)** is explicit: "Delete both dead Position serializers (CONTROLLER=14 + `Portfolio_Save/Load`) ... delete `#define` + dead fns + ledger row (`identifier_ledger.txt:55/57`) + tool SOURCES row". So D-289 treats PORTFOLIO exactly like CONTROLLER — both `#define`s deleted, both ledger rows (`:55` PORTFOLIO, `:57` CONTROLLER) tombstoned.
- The plan's own acceptance line is internally asymmetric: "`PORTFOLIO_SNAPSHOT_VERSION` 7→8 bumped ... `CONTROLLER_SNAPSHOT_VERSION`=14 DELETED (dead-path retirement, not a bump)." Both formats' serializers are deleted in Phase D, so both version macros should be retired — the plan retires one and bumps the other.
- `wire-format-byte-preservation-discipline.md:327` — "Delete field (no replacement) | HARD"; a WHOLE-format retirement is a tombstone (keep the ledger row, mark RETIRED, delete the `#define`+fns), never an increment to a phantom `v8` that no emitter ever writes.

**Why BLOCKING:** This is the H21 Knight-Capital surface the ship is meant to exemplify. A phantom `PORTFOLIO_SNAPSHOT_VERSION=8` with no emitter, sitting in the golden ledger, is precisely the "wire identifier that means nothing / could be reused wrong later" hazard H21 exists to prevent. And the coder literally cannot execute both instructions (bump a macro + delete its only functions) coherently.

**Under-cited deletion-cascade sites the retirement must also touch (the plan omits these):**
- The epoch static_assert `Portfolio.hpp:540-544` (`!is_fp_decimal_v<...> || PORTFOLIO_SNAPSHOT_VERSION >= 7`) references the macro → delete with it.
- Golden ledger `tools/identifier_ledger.txt:55` (`version|PORTFOLIO_SNAPSHOT_VERSION|7`) → tombstone.
- Tool SOURCES `tools/check_identifier_retirement.py:59` (the PORTFOLIO row; SHARDED is `:57`, CONTROLLER `:58`, PORTFOLIO `:59`) → delete.

**Recommended resolution:** Amend acceptance + Phase G to RETIRE `PORTFOLIO_SNAPSHOT_VERSION` (delete `#define`+epoch-assert+fns, tombstone ledger row `:55`, delete SOURCES row `:59`, `--update`) — mirroring the CONTROLLER treatment — OR, if there is a genuine reason to keep `Portfolio_Save/Load` alive (there is none at HEAD: zero live callers), re-open the D-289 delete decision explicitly. Do NOT bump to 8.

---

### BLOCKING-2 (D-110 / wire drop-proof) — NodeContext "compose-sub-registries" under-covers the ~24 flat node scalars (incl. 9 money fields)

**Summary:** Finding #2's core question — "does the sub-walker set cover EVERY currently-persisted NodeContext field?" — answers **NO as worded.** The plan (Phase C) says convert the hand-loop to "a thin driver delegating to `regime_state` + `pnl_feeder` + `confidence` sub-walkers ... NOT a flat `FOREACH_NODE_PERSIST_FIELD`." Those three named delegates cover ~13 fields. The persisted NodeContext set is DOMINATED by ~24 FLAT scalars that fit none of the three named groups — and 9 of them are money-bearing.

**Evidence — the persisted NodeContext set (enumerated from the live hand-loop `ShardedSnapshotPersist.hpp:176-260`):**
- FLAT scalars with NO named walker in the plan: `strategy_id`(:176), `resolved_strategy_id`(:177), `strategy_state_kind`(:182), `allocated_balance`(:187, **Money**), `entries_processed`(:190), `exits_processed`(:191), `node_realized`(:192, **Money**), `node_fees`(:193, **Money**), `node_open_notional`(:194, **Money**), `node_wins`(:195), `node_losses`(:196), `node_gross_wins`(:202, **Money**), `node_gross_losses`(:203, **Money**), `idle_cycles`(:204), `last_entry_price`(:207, **Money**), `last_entry_tick`(:208), `sl_cooldown_remaining`(:209), `node_peak_balance`(:212, **Money**), `node_dd_pct`(:213, **Money**), the KILL_TRIPPED byte(:219-221), `node_ks_trips_total`(:227), and the 3 prediction doubles `staged_prediction`/`active_prediction`/`last_confidence`(:244-246, confirmed NodeContext-level fields `ControllerEventLoop.hpp:347-349`, NOT part of the ConfidenceScorer delegate).
- Covered by named delegates: `regime_state.*` (7 fields, :230-236) → regime delegate; `pnl_feeder.*` (:239-241) → pnl_feeder delegate; the ConfidenceScorer ic/rmse arrays (:260) → confidence delegate.

**The divergence:** D-283 item (2) (decision-log `:1810`) explicitly mandated the flat `FOREACH_NODE_PERSIST_FIELD` "mirroring `FOREACH_OMS_FIELD`" for exactly these scalars. `FOREACH_NODE_PERSIST_FIELD` is grep-zero (never built). The reformalized plan drops it ("NOT a flat FOREACH_NODE_PERSIST_FIELD") WITHOUT a superseding decision — D-287 (`:1828`) only refuted the fabricated `SERIALIZER_GENERATED` meta-flag, not the flat-scalar registry itself. So the plan's architecture claim ("NodeContext needs nested/array/delegate") is half-right (regime/pnl_feeder/confidence do) but it silently discards the walker for the DOMINANT flat-scalar group.

**Why BLOCKING:** The acceptance criterion states "the NodeContext persist-serializer are registry-driven (no hand field-list can silently drop a field → closes the D-110 silent-zero-on-restore risk + TECH_DEBT-196)." As worded, the ~24 flat scalars must EITHER stay hand-`fwrite`'d in the "thin driver" (→ the acceptance criterion FAILS; the D-110 drop risk on the money counters — `node_realized`/`node_fees`/`node_gross_wins`/`allocated_balance` — is UNCLOSED, which is the whole point of the refactor) OR be unhomed. A dropped/mis-ordered money scalar under AoS→SoA is the literal D-110 nightmare (a repr/layout change silently recovering a slightly-wrong balance).

**Recommended resolution:** Restore a flat node-scalar registry (the D-283 `FOREACH_NODE_PERSIST_FIELD`, DIRECT/BIT like `FOREACH_OMS_FIELD`) for the ~24 scalars, composed WITH the three delegate sub-walkers (regime/pnl_feeder/confidence) — i.e. the driver is `FOREACH_NODE_PERSIST_FIELD` for scalars + `regime_state`/`pnl_feeder`/`confidence` delegates for the structured tail. State the composition explicitly + enumerate ALL persisted fields (a paste-the-enumeration table, per `feedback_paste_tool_output_dont_summarize`) so the pre-coding gate can verify none is dropped. If any scalar is intentionally dropped-and-recomputed (see node_dd_pct, MED-4), name it in the drop list.

---

### HIGH-1 (Position leg) — sole live Position serializer verified; registry-drive is structurally drop-proof, but wire field-ORDER + pad handling under AoS→SoA is unspecified

- **Confirmed:** the sole live Position serializer is the raw blob `fwrite(state->oms->portfolio.positions, sizeof(Position<F>), 16, f)` at `ShardedSnapshotPersist.hpp:169` (save) / `fread(positions, sizeof(Position<F>), 16, f)` at `:394` (load). The two dead ones (`Portfolio_Save/Load`, `PortfolioController_*Snapshot`) confirmed zero live callers.
- **Drop-proof for Position fields:** because `Position<F>` IS registry-generated from `FOREACH_POSITION_FIELD` (`MemHeaders/PositionFieldRegistry.hpp:49-59`), a macro-driven gather/scatter auto-flows EVERY PERSIST field. No field can be silently dropped as long as the gather + scatter are pure `FOREACH_POSITION_FIELD` walks (same macro → identical order both directions). GREEN.
- **Gap (verify-at-code):** the plan is silent on (a) wire field-ORDERING under AoS→SoA — SoA-major (`all 16 tp, all 16 sl, ...`) vs position-major (`pos[0].all, pos[1].all, ...`, matching the old blob). Either is fine under a version bump IFF save+scatter agree; a mismatch = D-110. (b) The old blob wrote 128B/pos INCLUDING `_pad_pos[7]`; a registry gather writes only PERSIST field bytes (no `_pad_pos`, no reserved pad, unless those are registry rows). The plan must state the persisted per-position byte count is now sum-of-PERSIST-fields (decoupled from `sizeof`), so the size-pin (`POSITION_PERSIST_BYTES`) and the wire don't silently diverge. Fold both into Phase C as explicit statements + assert save/load symmetry in the NEW round-trip test.

### HIGH-2 (confidence shared-wire) — SURVIVES the PortfolioController deletion — VERIFIED SAFE

- The confidence sub-walk helpers (`ConfidenceScorer_FieldwiseWrite`/`_FieldwiseRead`/`_CommitPersistedFields`/`_RecomputeRunningSums`, driven by `FOREACH_CONFIDENCE_PERSIST_FIELD`) are HOMED in `ML_Headers/ConfidenceScore.hpp:993-1058`. `PortfolioController_SaveSnapshot`/`_LoadSnapshot` are merely CALLERS (`:2094`/`:2228`/`:2234`); the LIVE ShardedSnapshot path calls the same helpers at `:260`/`:487`/`:585`. Deleting the PortfolioController serializers does NOT delete the helpers → the live confidence sub-walker survives. **GREEN.** Finding #2's confidence-leg concern is resolved-safe.
- **LOW rider:** `ConfidenceScorer_ShadowLoadLegacyV1` (`ConfidenceScore.hpp:1122`) has exactly ONE caller — `PortfolioController_LoadSnapshot:2219` (the v11-legacy migration; the sharded path never migrates, it refuses). Deleting PortfolioController orphans `ShadowLoadLegacyV1`. Fold its deletion into Phase D (dead-code removal) or track it — the plan doesn't mention it.

### HIGH-3 (H21 deletion cascade) — CONTROLLER deletion under-enumerates the version-macro test sites

The plan cites only "the `controller_test.cpp` 4-version snapshot assert (≈`:26819`)". There are (at least) THREE more sites that reference the version macros E.1.2 changes; deleting `CONTROLLER_SNAPSHOT_VERSION` and bumping `SHARDED` will COMPILE-BREAK the un-updated ones:
- `tests/controller_test.cpp:11394-11395` — `check(... SHARDED_SNAPSHOT_VERSION == 10u)` (exact; must → 11).
- `tests/controller_test.cpp:26749-26757` — `static_assert(CONTROLLER_SNAPSHOT_VERSION >= 13 + MONEY_ENCODING_EPOCH && SHARDED >= 9 && PORTFOLIO >= 6 ...)` + its `check()` twin — references the TO-BE-DELETED `CONTROLLER_SNAPSHOT_VERSION` AND `PORTFOLIO_SNAPSHOT_VERSION`; both must be removed/retired here.
- `tests/controller_test.cpp:26819-26820` — `SHARDED == 10u && CONTROLLER == 14 && PORTFOLIO == 7 && STAMP == 3` — three of four terms change; the CONTROLLER + PORTFOLIO terms must be removed (deleted macros), SHARDED→11.

Compile-caught (not silent), so severity is bounded — but for an "open the struct ONCE, avionics-grade" freeze, enumerate ALL sites up front (per `feedback_verify_every_enumerated_site_at_close`). Fold into the test-change-enumeration section.

---

### MEDIUM-1 (currency / Phase F) — the ③ ControllerConfig fingerprint-safety fold is ~mostly already DONE at HEAD; the `Fingerprint.hpp:180` cite is wrong

The plan (Known-folds `:168`) says this leaf MUST "(b) ADD the `static_assert(sizeof(ControllerConfig)==N)` it currently LACKS (F-I — Check-K gap)". **STALE at HEAD `b10e778`:**
- The size-pin ALREADY EXISTS: `static_assert(sizeof(ControllerConfig<64>) == 53056, ...)` at `ControllerConfig.hpp:1323` (comment `:1315-1326` names it the "byte-equivalence size-pin for the fingerprinted cfg struct (D-254)"). E.1.1 ③ landed it.
- Item (a) "include the 4B gate-summary": `uint32_t cfg_load_fault_flags` ALREADY in the struct at `ControllerConfig.hpp:582`, already inside the `53056` pin.
- The plan's cite "`ControllerConfig.hpp:347 → Fingerprint.hpp:180`" is WRONG (orchestrator's flag CONFIRMED): `Fingerprint_Compute` is DEFINED at `Backtest/Fingerprint.hpp:174` (hashes `cfg_ptr` raw at `:180` inside the body); the SOLE call site is `Backtest/BacktestPanels.hpp:3157` (`Fingerprint_Compute<BACKTEST_FP>(fp_hex, &results->config_used, sizeof(results->config_used), ...)`). The `:180` cite traces to a stale in-code comment at `ControllerConfig.hpp:1316`. Re-ground Phase F to `BacktestPanels.hpp:3157`.
- **Only genuinely-open sub-item:** item (c), an EXPLICIT `assert(config_used.cfg_load_fault_flags==0)` AT the hash site `BacktestPanels.hpp:3157`, is not present. But the guarantee ALREADY holds two ways: control-flow (`cfg_capital_gate_ok` ALWAYS-ABORT on non-zero, `ControllerConfig.hpp:1344-1350`) + a defensive zeroing `results->config_used.cfg_load_fault_flags = 0` at `BacktestSharded.hpp:131`. So (c) is belt-and-suspenders, not load-bearing. NOTE E.1.2 does NOT change `ControllerConfig`'s size (NodeState/ClusterState are SEPARATE structs) → the `53056` pin stays; do NOT re-add it or bump N.

**Action:** Re-ground Phase F ③ — cite `BacktestPanels.hpp:3157`; state (a)/(b) are ALREADY satisfied at HEAD (don't re-add the pin — risk of a duplicate/confused edit on a determinism surface); keep only the optional (c) assert-at-hash-site if wanted.

### MEDIUM-2 (H4 / parity) — Phase E under-scopes the F-096 double seam: the EXIT-qty read also round-trips money through `double`

- Confirmed the entry leg-split at `Async.hpp:842` (`double full_qty = Money_ToDouble(intended_qty)`) → `:847`/`:849` split in `double` → `:896` (`Money{ money_from_double_payload(order_qty_d) }`). The plan's `Money_Mul`/`Money_Sub` conservation fix is correct.
- BUT the EXIT branch at `Async.hpp:829-830` (`order_qty_d = Money_ToDouble(portfolio.positions[portfolio_slot].quantity)`) → `:896` is the SAME money→double→money round-trip class, and it feeds the persisted `Position.quantity` at fill. Under `±USE_NATIVE_128`, double-rounding differences here could perturb the persisted qty → a determinism/parity risk on the exact byte-compare gate. Phase E names only the entry split. Bring the exit-qty read into Phase E scope (pass the `Money` quantity directly, no double) OR explicitly defer with rationale.

### MEDIUM-3 (determinism gate completeness) — the NEW round-trip byte-compare must exercise a POPULATED multi-node snapshot, not just Position

- Confirmed there is NO existing `ShardedSnapshot_Save/Load` round-trip byte-compare test and NO `USE_NATIVE_128` test in `tests/` → the gate is genuinely NEW infrastructure (plan marks it NEW correctly). The plan's framing is right (byte-compare, "a byte-reorder keeps sizeof==192 but must FAIL").
- **Completeness requirement:** given BLOCKING-2 (flat-scalar coverage), a byte-compare that only populates + diffs the Position block would NOT catch a dropped node money scalar. The gate must Save→Load→memcmp a snapshot with ALL node blocks populated with distinct non-zero Money values across ≥2 nodes, under both `±USE_NATIVE_128`. State this in the acceptance test.
- **H12:** the plan says the reserved ~48B are "all named + `=0`-init + PERSIST". Clarify: if reserved bytes are manual pad (not `FOREACH_POSITION_FIELD` rows) they are `=0`-init in-struct but do NOT ride a registry-driven wire; if PERSIST rows, they ride. Pin which — it affects both the byte-compare and the H12 reserved-byte guarantee.

### MEDIUM-4 (derived field / Fight #2) — `node_dd_pct` drop-and-recompute must single-source the formula

- Plan Phase C: "Mark derived fields (`node_dd_pct`@`:213` ...) recompute-on-load, NOT raw-persist rows." `node_dd_pct` is currently PERSISTED (`:213`, Money) and is a pure fn of (`node_peak_balance`, current value). Dropping it from the wire is fine under the version bump, BUT the load-time recompute must use the SAME formula as the runtime writer (per `feedback_single_source_the_computation_not_just_the_mode`) or the displayed drawdown shifts on restore. Name the recompute site + confirm it calls the same helper the slow path uses. (Same category: the `ShardedSnapshot` display doubles `:490-496` — display-only, not persist wire, so out of parity scope, but the plan conflates them; keep the persist-wire vs display-snapshot distinction sharp.)

### MEDIUM-5 (stale-comment sweep scope — SUBAGENT_ARMING §2.5) — the version-history comment drift is larger than the plan's list

On a determinism surface a stale version comment actively misleads a future coder about the wire. The plan says "sweep ALL at the bump" but its enumerated list misses some:
- `PORTFOLIO_SNAPSHOT_VERSION` comments say **"5"** (`PositionFieldRegistry.hpp:14/21/27/42`) AND **"6"** (`Portfolio.hpp:45/68/80/82/134/142`) while the `#define` is **7** — and under BLOCKING-1 the macro RETIRES, so these comments must be swept/retired, not "bumped to 8".
- `SHARDED_SNAPSHOT_VERSION` version-history block `ShardedSnapshotPersist.hpp:51-93` documents only up to **v8** while the `#define` is **10** (v9/v10 undocumented in the block). Sweep to 11 + document v9/v10/v11.
- `Portfolio.hpp:102-114` is the SUPERSEDED 24B/192B layout block (plan flags it) — but note the NEW 192B target REUSES "192B", so replace the block cleanly, do not leave the old offsets (0-23/24-47…) that describe a DIFFERENT 24B-Money geometry.

---

### LOW
- **SoA wire-ordering** (folded into HIGH-1): specify SoA-major vs position-major; assert save/load symmetry.
- **`ConfidenceScorer_ShadowLoadLegacyV1` orphan** (folded into HIGH-2): dead after PortfolioController deletion.
- **Ledger/SOURCES line precision:** plan's "`identifier_ledger.txt:55/57`" — at HEAD PORTFOLIO=`:55`, SHARDED=`:56`, CONTROLLER=`:57`; tool SOURCES SHARDED=`:57`, CONTROLLER=`:58`, PORTFOLIO=`:59`. The "re-verify" flags in Phase D are correct to carry; the precise rows are as above.

### DOCUMENT-ONLY
- **TD-180 (size-pin trips while version bump forgotten):** the Position `sizeof` pin `Portfolio.hpp:117` WILL trip on 128→192 (forces the pin update), but NO guard links a Position LAYOUT change to a `SHARDED_SNAPSHOT_VERSION` bump — that remains manual discipline (Phase G). Acceptable as-is; reinforce as an explicit Phase-G checklist item. (The Ship-B epoch static_asserts at `Portfolio.hpp:540` / `ShardedSnapshotPersist.hpp:99` only fire on `MONEY_ENCODING_EPOCH` change, not on a layout grow.)

---

## Cross-cutting concerns (single fixes that close multiple findings)
- **Restoring `FOREACH_NODE_PERSIST_FIELD` + composing the 3 delegates** closes BLOCKING-2, makes the D-110 "no field silently dropped" test (plan test (c)-NEW) non-vacuous, and re-aligns with D-283 item (2). This is the single highest-leverage amendment.
- **Treating PORTFOLIO identically to CONTROLLER (retire, not bump)** closes BLOCKING-1 + MED-5's PORTFOLIO-comment half + the epoch-assert/ledger/SOURCES under-cites in one coherent retirement.

## Behavior matrix (Save-view vs Load-view agree, default cfg)
| Surface | Save writes | Load reads | Round-trips identically? |
|---|---|---|---|
| Position PERSIST fields (registry) | `FOREACH_POSITION_FIELD` gather | `FOREACH_POSITION_FIELD` scatter | YES if same macro + symmetric order (HIGH-1) |
| Position `_pad_pos` + reserved ~48B | (registry? or blob-pad?) | (must match) | UNSPECIFIED — pin it (MED-3/H12) |
| NodeContext ~24 flat scalars (9 Money) | plan: unspecified walker | plan: unspecified | **AT RISK** — no named walker (BLOCKING-2) |
| regime_state / pnl_feeder / confidence | delegate sub-walkers | delegate sub-walkers | YES (confidence helpers survive, HIGH-2) |
| `node_dd_pct` | plan: DROP + recompute | recompute from peak+current | only if formula single-sourced (MED-4) |
| Fill qty (F-096) → Position.quantity | entry+exit via `double` today | — | perturbable under ±NATIVE_128 (MED-2) |

## Suggested resolution sequence (pre-coding, before the /precoding-audit-gate)
1. Amend Phase C: restore `FOREACH_NODE_PERSIST_FIELD` (scalars) + delegates (regime/pnl_feeder/confidence); paste the full persisted-field enumeration table (BLOCKING-2).
2. Amend acceptance + Phase G: PORTFOLIO_SNAPSHOT_VERSION RETIRE (not bump); list the epoch-assert + ledger + SOURCES + comment sweep sites (BLOCKING-1, MED-5).
3. Re-ground Phase F ③: cite `BacktestPanels.hpp:3157`; mark (a)/(b) already-satisfied at HEAD; keep only optional (c) (MED-1).
4. Expand Phase E to the exit-qty seam (MED-2); expand the NEW gate to a populated multi-node ±NATIVE_128 byte-compare (MED-3).
5. Enumerate ALL version-macro test sites (:11394 / :26749-26757 / :26819) in the test-change section (HIGH-3).

## Spots most worth an ADVERSARIAL refute (for the paired a-class)
1. **BLOCKING-1 — refute the retire-not-bump.** Is there ANY live consumer of `PORTFOLIO_SNAPSHOT_VERSION` after `Portfolio_Save/Load` deletion (I found none), or any reason a phantom `v8` is legitimate? If `Portfolio_Save/Load` is secretly load-bearing (e.g. a test fixture generator), the delete itself is wrong — code-read the caller set, don't resolve by fiat (AR-11).
2. **BLOCKING-2 — refute the coverage gap.** Steelman "the flat scalars belong under the delegates / a flat registry isn't needed": is there a 4th walker the plan implies but doesn't name? Or is `FOREACH_NODE_PERSIST_FIELD` genuinely unbuildable for these scalars (it is buildable — they're all DIRECT like `FOREACH_OMS_FIELD`)? Push on whether D-287 silently authorized dropping it.
3. **HIGH-1 — refute drop-proofness.** Does AoS→SoA introduce a field the macro can't see (e.g. a manually-added struct member outside `FOREACH_POSITION_FIELD`)? Verify `Position<F>` has ZERO non-registry data members besides `_pad_pos`.
4. **MED-1 — refute "already done."** Confirm `sizeof(ControllerConfig<64>)==53056` at HEAD and that E.1.2 truly does not touch ControllerConfig's layout (if it folds ANY cluster field INTO ControllerConfig, the pin must bump + golden regen — then Phase F is NOT a no-op).

## NOT a bug (verified-safe)
- Confidence shared-wire survives PortfolioController deletion (HIGH-2) — helpers homed in `ConfidenceScore.hpp`.
- `ShardedSnapshotPersist.hpp:169` (blob) + `Async.hpp:842` (double seam) — orchestrator-flagged ACCURATE, re-confirmed.
- PARITY-039 (restore↔live TP/SL) — STILL FIXED (`.E.0.10`); the live-tp recompute at `ShardedSnapshotPersist.hpp:648-668` uses `ResolvePerFillTpPct/SlPct` (the A1 SSoT), not global `take_profit_pct`; not regressed by this plan.

*End of report.*
