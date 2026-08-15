---
type: agent-report
status: FROZEN — verbatim agent output
directive: S-4 — complement-blindness sweep, shard 4/5: NODE-CTX + STATE / BITFLAG registries
agent_class: i-class
delivered: 2026-08-15
ground: engine HEAD 7240f3d, branch feat/v5.15-live-readiness
headline: S4-1 — NodeContext::gate_state is absent from all three partitions AND from every NODE_CTX_INIT_AUTOPOPULATE layer; no default member initializer, default-initialized container, and a cross-thread reader exists. It is the only NodeContext member with zero lifecycle touch anywhere — and it is NOT the item the seed report predicted. Two seed hypotheses (per-arm width guard, session-phase consumer mirror) were REFUTED by code and reported as such. Entire bitmap bit layer verified clean across all seven storage words
operator_decision_owed: Rec-1 (close S4-1 in-flight — one Layer-2 line zeroing gate_state, zero wire impact) · Rec-2 (the D-2 containment assert — every SUMMARY row resolves to a NODE_CTX_FIELD row) · Rec-3 (second FOREACH_FAILURE_MODE pairing for drift_flags_at_load) · Rec-5 (fold the 5-member doc-drift cohort into the D-327 ROW_COUNT generator's ship, carrying HAZ-S4-6 as a hard requirement or that generator ships vacuously green)
sister_reports: S1-capital-wire-persist.md · S2-cfg-surface.md · S3-stamp-hmac-ml.md · S5-emit-display-and-set-closure.md
saved_at: step-1 close-out, NOT at receipt — recovered VERBATIM from the session transcript
  (subagents/agent-<id>.jsonl final assistant message). Sisters S1/S3/S5 were saved at receipt;
  these two were missed, which is itself the save-agent-reports-verbatim discipline failing on the
  two shards that finished while the orchestrator was mid-implementation. Recovery method verified
  against S1 first (extract diffs from the saved copy by exactly the frontmatter block + one
  trailing-space normalization), so the body below is the agent's output, not a reconstruction.
---

# S-4 — COMPLEMENT-BLINDNESS sweep, shard 4/5: NODE-CTX + STATE / BITFLAG registries

**Ground:** engine `/home/caramel/code/FoxML_Trader_v2`, HEAD `7240f3d` (verified `git rev-parse`), branch `feat/v5.15-live-readiness`. Read-only pass — `git status --short` identical at start and end (4 pre-existing untracked operator files, nothing touched). Registries in scope: the 13 named at `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/MetaRegistry.hpp:59,82,83,84,85,86,87,88,89,90,95,96,113`.

**Headline:** the shard is *mostly* clean on true coverage, and the one genuinely-unaccounted item is **not** the one the seed report predicted. `NodeContext::gate_state` is absent from **all three** partitions **and** from every `NODE_CTX_INIT_AUTOPOPULATE` layer — it is the only `NodeContext` member with **zero lifecycle touch anywhere**, it has **no default member initializer**, its container is **default-initialized** (not value-initialized), and a **cross-thread reader exists**. `drift_history` at least gets a `DriftHistory_Init`. Two of my initial hypotheses were **refuted** by code (per-arm width guard, session-phase consumer mirror) and are reported as such.

---

## 0. Method + what was mechanically run

| Tool / probe | Result |
|---|---|
| `tools/check_meta_registry.py` | **RC=0** — 68 macros / 68 rows; Checks 1-3 PASS |
| `tools/check_identifier_retirement.py` | **RC=0** — "GREEN — 47 persisted/wire identifiers match the ledger" |
| `tools/check_code_tag_blocks.py` | **RC=0** — 202 files, 791 tag-blocks, "All tag-blocks valid" |
| **g++ count probe** (compiled against the real headers, `-DLICENSE_BYPASS`) | every registry count below is **compiler-derived**, not counted by eye |
| **g++ bit-arithmetic probe** | the OMS hybrid-word overlap assert verified to have real teeth (§ 2, table note) |

Compiler-derived counts (the anchor for every claim in this report):

```
NODE_STATE_FLAG_COUNT      = 6      PER_NODE_STATE_FLAG_COUNT  = 11
OMS_STATE_FLAG_COUNT       = 3      OMS EVENT_LOG_MODE shift=3 bits=2 mask=0x18
FAILURE_BIT_COUNT          = 11     FOREACH_FAILURE_MODE_COUNT = 15
GATE_DIAG_PAIR_COUNT       = 6      DISPLAY_META_FIELD_COUNT   = 10
SP_SECTION_COUNT           = 5      SESSION_PHASE_COUNT        = 4
EZOO_INIT_FLAG_COUNT       = 5      PER_ARM_FLAG_COUNT         = 3
NODE_CTX_INIT_FIELD_COUNT  = 40     NODE_CTX_RESET_FIELD_COUNT = 15
SUMMARY_FIELD_COUNT        = 20
--
NodeContext<64> trivially_default_constructible   = 0
EventLoopState<64> trivially_default_constructible = 0
SlowPathGateState trivially_default_constructible = 1, sizeof=2
```

**On the `static_assert` question the directive raised** — I read `/home/caramel/code/FoxML_Trader_v2/DESIGN_SPECS/refactor-patterns/bitmap-overflow-protection-discipline.md`. Its mandated form is
`static_assert(FOREACH_X_COUNT_VALUE <= sizeof(TYPE) * 8, ...)` (spec `:90-94`, `:115`, `:385`).
That is **width sufficiency (rows ≤ bits)**, categorically **not** coverage (rows == accounted bits). The spec never asks for a coverage form. Every bitmap assert on this shard follows the spec form and is therefore **structurally incapable of detecting an undeclared bit** — it is a *growth* guard, not a *completeness* guard. Exactly **one** assert on the shard is a genuine bit-region check (§ 2).

---

## 1. Per-registry verdict table

| # | Registry | Kind / generation direction | Authoritative domain | Complement check exists? | Complement (computed) | Verdict |
|---|---|---|---|---|---|---|
| 1 | `FOREACH_NODE_CTX_FIELD` `MemHeaders/NodeCtxInitRegistry.hpp:98-145` (40 rows) | **COVERAGE**. Struct is **hand-written** (`CoreFrameworks/ControllerEventLoop.hpp:315-614`); registry drives the init *walk*, not the declaration → gap is possible | 49 `NodeContext<F>` top-level members | **NO.** `NODE_CTX_INIT_FIELD_COUNT >= 30` (`:248`) — a **floor 10 below reality**; `NODE_CTX_RESET_FIELD_COUNT == 15` (`:262`) is an equality but only over the RST *sub*set. Neither can see the struct | 49 − 40 = **9**; 8 resolve to AUTOPOPULATE Layers 2-4 (`:308-322`); **1 genuinely unaccounted: `gate_state`** | ⚠ **FINDING S4-1** |
| 2 | `FOREACH_NODE_CTX_SUMMARY_FIELD` `MemHeaders/NodeCtxSummaryFieldRegistry.hpp:171-198` (20 rows) | **SELECTION** (curated operator subset of `NodeContext`) — no level-1 complement duty | n/a by design | `>= 18` floor (`:209`) | n/a at level 1. **Level 2 gap:** `Summary_EmitPerStrategy` (`:279-332`) hand-codes a 9-field aggregation mirroring a subset of the rows, unguarded | ⚠ **FINDING S4-5** (level-2) |
| 3 | `FOREACH_DISPLAY_META_FIELD` `MemHeaders/DisplayMetaRegistry.hpp:116-133` (10 rows) | ⚠ **FALSE-POSITIVE GUARD** — struct **generated from** the registry (`ControllerEventLoop.hpp:777-779`). Coverage is structural | struct is the registry's image | `== 10` equality (`:155`) | 2 non-registry members, **both excluded with a stated reason** (`DisplayMetaRegistry.hpp:41-44` + `ControllerEventLoop.hpp:856-859`) | ✅ **CLEAN** (doc nit S4-8) |
| 4 | `FOREACH_GATE_DIAG_PAIR` `MemHeaders/DisplayMetaRegistry.hpp:72-78` (6 rows) | ⚠ **FALSE-POSITIVE GUARD** — struct generated (`ControllerEventLoop.hpp:766-769`) | same | `== 6` equality (`:146`) | ∅ | ✅ **CLEAN** |
| 5 | `FOREACH_NODE_STATE_FLAG` `MemHeaders/NodeStateFlagRegistry.hpp:74-111` (**6** rows) | **SOURCE-OF-TRUTH** for bit positions (enum generated from rows, `:116-120`) | bits of `uint8_t node_state_flags` (`ControllerEventLoop.hpp:365`) | `COUNT <= 8` width-only (`:129`) | bits 0-5 declared; **6-7 undeclared headroom**, no writer outside the accessors (verified) | ✅ bits CLEAN · ⚠ **FINDING S4-2** (doc) |
| 6 | `FOREACH_PER_NODE_STATE_FLAG` `MemHeaders/PerNodeStateFlagsRegistry.hpp:75-107` (11 rows) | **SOURCE-OF-TRUTH** (`:113-117`) | bits of `uint16_t PerNodeSnap.state_flags` | `COUNT <= 16` width-only (`:126`) | bits 0-10 declared; 11-15 headroom, no writer | ✅ **CLEAN** (forward hazard § 5) |
| 7 | `FOREACH_OMS_STATE_FLAG` `MemHeaders/OmsStateFlagRegistry.hpp:108-121` (3 rows) | **SOURCE-OF-TRUTH** (`:126-130`) | bits 0-2 of the hybrid `uint8_t oms_state_flags` | `COUNT <= 8` width-only (`:139`) **+ the region-overlap assert** (`:212`) | fully accounted (§ 2) | ✅ **CLEAN — best on shard** |
| 8 | `FOREACH_OMS_STATE_MULTI_BIT` `MemHeaders/OmsStateFlagRegistry.hpp:178-188` (1 slot) | **SOURCE-OF-TRUTH** (explicit `bits`/`shift` columns) | bits 3-4 of the same word | **YES — the only genuine bit-region coverage assert on the shard** (`:212`), plus capacity asserts `:216`, `:230` | bits 5-7 **explicitly RESERVED** with a stated reason (`:31`) | ✅ **CLEAN** |
| 9 | `FOREACH_PER_ARM_FLAG` `ML_Headers/PerArmFlagRegistry.hpp:81-84` (3 rows) | **HYBRID** — generates one `uint8_t` **field per row** (`:113-120` → `ML_Headers/NodeModelZoo.hpp:1179`); bits within each word are indexed by **ARM**, not by row | bits = arm indices, bounded by `ENSEMBLE_HORIZON_MAX` (`NodeModelZoo.hpp:1018`) | Width guard **EXISTS** — `NodeModelZoo.hpp:1025` `static_assert(ENSEMBLE_HORIZON_MAX <= 8)` (**my "missing guard" hypothesis REFUTED**). But **no row↔init coverage check** | bits `primary_count..7` unused by construction (every loop bounds on `primary_count`) | ⚠ **FINDING S4-3** (init mirror + false enforcement claim) |
| 10 | `FOREACH_EZOO_INIT_FLAG` `ML_Headers/EzooInitFlagRegistry.hpp:76-83` (**5** rows) | **SOURCE-OF-TRUTH** (`:92-97`) | bits of `uint8_t ezoo->init_flags` (`NodeModelZoo.hpp:1176`) | `COUNT <= 8` width-only (`:132`) | bits 0-4 declared; 5-7 headroom | ✅ bits CLEAN · ⚠ **FINDING S4-4** (5 stale doc sites — worst on shard) |
| 11 | `FOREACH_FAILURE_MODE` `MemHeaders/FailureModeRegistry.hpp:133-258` (15 rows / **11** BIT_FLAG) | **SOURCE-OF-TRUTH** for bit positions (`:291-307`), storage-class-dispatched | bits of `uint16_t` — **TWO** paired words | `FAILURE_BIT_COUNT <= 16` (`:309`) — names **only one** of the two words | bits 0-10 declared; 11-15 headroom | ⚠ **FINDING S4-6** (undeclared second pairing) |
| 12 | `FOREACH_SESSION_PHASE` `CoreFrameworks/SessionPhaseRegistry.hpp:40-44` (4 rows) | **SOURCE-OF-TRUTH** + **cfg-field-name generator** (`session_<name_l>_mult`) | the 24-hour UTC domain | **YES — a genuine DOMAIN coverage assert**: `SESSION_BY_HOUR[0..23] < SESSION_PHASE_COUNT`, 24 asserts (`:104-127`) + per-row range asserts (`:73-81`) | ∅ — all 3 consumer lookup tables are **registry-generated** (`ShardedSnapshot.hpp:197-201`, `ControllerEventLoop.hpp:2702-2706`, `PortfolioController.hpp:1603-1607`). **My "3-way mirror" hypothesis REFUTED** | ✅ **CLEAN — model registry** |
| 13 | `FOREACH_SP_SECTION` `CoreFrameworks/SpSectionRegistry.hpp:32-37` (5 rows) | **SOURCE-OF-TRUTH** (`:42-47`); sizes `slow_path_breakdown[SP_SECTION_COUNT]` (`ControllerEventLoop.hpp:793`) | the set of rdtsc-bracketed slow-path sections | `SP_SECTION_COUNT >= 5` floor (`:69`) | **∅ in both directions** — exactly 5 instrumented sites, one per row: `CoreFrameworks/EngineCommon.hpp:611, 636, 657, 763, 797` | ✅ **CLEAN** · ⚠ **FINDING S4-7** (phantom H21 constraint) |

---

## 2. Bitmap bit-accounting — every storage word, every bit

| Storage word | Decl | Width | Declared bits | Undeclared bits | What accounts for them | Persisted / wire-visible? | H21 status |
|---|---|---|---|---|---|---|---|
| `NodeContext.node_state_flags` | `CoreFrameworks/ControllerEventLoop.hpp:365` | uint8 = 8 | **6** (0-5) | 6-7 | Headroom. `[OVERVIEW]` states "2 bits headroom" (`NodeStateFlagRegistry.hpp:67`). **No writer outside the `NODE_STATE_FLAG_*` accessors** (verified: zero direct `=`/`\|=`/`&=` writes outside the registry header) | **Only the VALUE of bit 1** (`KILL_TRIPPED`) reaches the wire — and it lands in a *separate* `uint8_t node_kill_tripped` field on `NodeSnap` (`CoreFrameworks/ShardedSnapshotPersist.hpp:381`). **The WORD LAYOUT is not on the wire.** | **LEDGER-ENROLLED** — `tools/identifier_ledger.txt:13-18`, SOURCES row `tools/check_identifier_retirement.py:115`. Positions frozen **conservatively** (stricter than the wire actually requires). The only shard bitmap so enrolled |
| `PerNodeSnap.state_flags` | `DataStream/EngineTUI.hpp` (`uint16_t`) | uint16 = 16 | **11** (0-10) | 11-15 | Headroom (`PerNodeStateFlagsRegistry.hpp:68`). Only writer outside accessors is the zeroing `snap->per_node[i].state_flags = 0;` at `CoreFrameworks/ShardedSnapshot.hpp:412` | **NO.** `TUISnapshot` is an in-process struct (`DataStream/EngineTUI.hpp:880`) published via `TUISnapshot_PublishHandle` (`:1588`) — no shm/file transport today | Runtime-only → bits **freely reclaimable** per `dead-code-and-identifier-retirement-discipline.md` Rule 2. **Forward hazard § 5** |
| `OrderManagerState.oms_state_flags` | `MemHeaders/OmsStateFlagRegistry.hpp` header § `:29-31` | uint8 = 8 | **3 flags (0-2) + 1 slot (3-4)** | 5-7 | **Explicitly RESERVED** with a stated reason (`:31`) | `KILL_SWITCH_TRIPPED` **VALUE** only, via the `FOREACH_OMS_FIELD` BIT projection (`CoreFrameworks/ShardedSnapshotPersist.hpp:412`); `EVENT_LOG_MODE` is SKIP_PERSIST (`OmsStateFlagRegistry.hpp:62`) | Runtime-only layout |
| `EnsembleModelZoo.init_flags` | `ML_Headers/NodeModelZoo.hpp:1176` | uint8 = 8 | **5** (0-4) | 5-7 | Headroom. Only non-accessor write is the zeroing at `NodeModelZoo.hpp:1435` | **NO** — self-declared runtime-only (`EzooInitFlagRegistry.hpp:154-156`: "would invalidate any stamp body that recorded the bitmap value (**none today**)") | Runtime-only. **This is precisely why the `THOMPSON_READY → BUY_THOMPSON_READY` rename at `.F.4d` was legal** (Rule 2) |
| `disabled_horizon_mask` / `arms_with_barriers_mask` / `corrupt_arms_mask` | generated by `PER_ARM_FLAG_DECLARE_FIELDS()` at `ML_Headers/NodeModelZoo.hpp:1179` | uint8 = 8 **each** | bits = **ARM index**, 0..`primary_count`-1 | `primary_count`..7 | Never set — every loop bounds on `primary_count` (`NodeModelZoo.hpp:1687`, `:1764`, `:2034`). Hard ceiling pinned by `static_assert(ENSEMBLE_HORIZON_MAX <= 8)` at `:1025` | **NO** — only copied into the display snapshot (`CoreFrameworks/ShardedSnapshot.hpp:776`); not in the bandit JSON persist | Runtime-only |
| `PerNodeSnap.failure_flags` | `DataStream/EngineTUI.hpp:1251` (`uint16_t`) | uint16 = 16 | **11** (0-10) | 11-15 | Headroom | **NO** (in-process) | Runtime-only |
| `ModelHandle.drift_flags_at_load` | `ML_Headers/ModelInference.hpp:399` (`uint16_t`) | uint16 = 16 | **the same 11** — set with `FAILURE_MASK_*` constants (`CoreFrameworks/ModelValidation.hpp:213`; column doc `ML_Headers/CfgDriftCheckRegistry.hpp:121`) | 11-15 | Headroom | **NO** | Runtime-only. **UNDECLARED pairing → S4-6** |

**Bit-accounting bottom line: every bit of every storage word on this shard is accounted for.** Zero undeclared live bits. The bitmap layer is genuinely clean — the exposure is in the *paired-word declaration* (S4-6) and in the *doc facts about* the bitmaps (S4-2, S4-4), not in the bits.

**The one real coverage assert, verified to have teeth.** `MemHeaders/OmsStateFlagRegistry.hpp:212`:

```cpp
static_assert((MASK_OMS_STATE_EVENT_LOG_MODE & _OMS_STATE_SINGLE_BIT_REGION) == 0,
              "EVENT_LOG_MODE multi-bit slot overlaps single-bit flag region; ...");
```

I simulated adding a 4th single-bit flag. `region = (1<<COUNT)-1`, `elm_mask = 0x18`:

```
COUNT=3  region=0x07  overlap=0x00 -> PASSES     (today)
COUNT=4  region=0x0F  overlap=0x08 -> FIRES      (a 4th flag IS caught)
COUNT=5  region=0x1F  overlap=0x18 -> FIRES
```

The header's growth warning at `:156-160` is **accurate**. This is the shape the other seven bitflag registries lack: it asserts a *relationship between declared bit regions*, not merely `count ≤ width`.

---

## 3. Unaccounted items, ranked by blast radius

### ⚠ S4-1 — `NodeContext::gate_state`: in **no** partition, in **no** init layer, **no** NSDMI, container default-initialized, and a cross-thread reader exists. — **HIGH (structural) / MED (live effect)**

This is the shard's payload, and it is a **strictly worse shape than `drift_history`** (the seed report's U-2), which at least receives `DriftHistory_Init` at `MemHeaders/NodeCtxInitRegistry.hpp:312`.

The five facts, each independently verified:

1. **No registry row.** `gate_state` is absent from `FOREACH_NODE_CTX_FIELD` (`NodeCtxInitRegistry.hpp:98-145`), from `FOREACH_NODE_CTX_SUMMARY_FIELD`, and (per shard 1's surface) from `FOREACH_NODE_PERSIST_FIELD`.
2. **No AUTOPOPULATE layer.** I walked all five layers of `NODE_CTX_INIT_AUTOPOPULATE` (`:300-325`). Layer 2 helper-Inits cover `pending_params` / `confidence` / `drift_history` / `turnover` / `regime_state` / `pnl_feeder`; Layer 3 covers `sp_telemetry`; Layer 4 covers `slow_state`. **`gate_state` appears in none of them.**
3. **No default member initializer.** `CoreFrameworks/ControllerEventLoop.hpp:330` is a bare `SlowPathGateState gate_state;`, and `struct SlowPathGateState { uint16_t flags; };` (`CoreFrameworks/SlowPathGateRegistry.hpp:183-185`) has no NSDMI. The probe confirms `SlowPathGateState` is trivially default constructible.
4. **The container is default-initialized, not value-initialized.** `CoreFrameworks/EngineSharded/Run.hpp:821` is a function-local `EventLoopState<F> state;` — no `{}`, no `static`. `EventLoopState_Init` (`ControllerEventLoop.hpp:1117-1165`) assigns named fields and calls the AUTOPOPULATE loop; **it does not memset**. So `gate_state.flags` holds an **indeterminate value** from construction until the node's first slow-path cycle.
5. **A cross-thread reader is reachable in that window.** `CoreFrameworks/ShardedSnapshot.hpp:597`:
   ```cpp
   if (BITMAP_IS_SET(state->nodes[i].gate_state.flags, tt::MASK_LADDER_ACTIVE)
       && state->nodes[i].last_confidence_factor == 0.0) {
       STATE_FLAG_SET(snap->per_node[i], LADDER_BOTTOM_HIT);
   }
   ```
   The publisher loop bounds on `state->registered_count` (`ShardedSnapshot.hpp:397`), so the window is *node registered → that node's first `SLOW_PATH_GATE_AUTOPOPULATE_PER_NODE`* (`ControllerEventLoop.hpp:2685-2686`, the sole per-node writer).

**The AND-partner is guaranteed true at boot.** `last_confidence_factor` is registry-init'd to `0.0` (`NodeCtxInitRegistry.hpp:119`). So the guard reduces, in the boot window, to *"is the indeterminate `MASK_LADDER_ACTIVE` bit set?"*.

**Blast radius: observability, not capital.** The only consumer in the window sets a display flag (`LADDER_BOTTOM_HIT` → ML Status panel + entry log). The in-engine consumers that read `gate_state->flags` for *decisions* (`Strategies/StrategyParameters.hpp:1201`, `:1435`, `:1604`, `:1706`) reach it via `ml_ctx.gate_state`, wired at `ControllerEventLoop.hpp:3003` — **downstream of the `:2685` populate in the same slow-path body**, so they are ordering-safe. It is nonetheless an indeterminate-value read (MSan-detectable) on a struct that sits at **offset 0 of the HOT cluster** by deliberate design (`ControllerEventLoop.hpp:318-329`, `:666`).

**Why the seed report's lens could not see this.** I-4 bucketed `gate_state` "DU — cfg-derived cache, repopulated every slow-path entry". That rationale is correct **for the persist partition** and silent **for the init partition** — repopulation-per-cycle says nothing about the first cycle. This is the concrete demonstration that a per-partition exemption reason does not transfer across partitions.

**Fix menu (I recommend (a); no edit made):**
- **(a) 1 row** — `X(gate_state, SlowPathGateState, SlowPathGateState{}, NORST)` won't typecheck against the `(TYPE)(INIT_VALUE)` cast at `NodeCtxInitRegistry.hpp:203`; the clean form is a **Layer-2 helper-Init line** `SlowPathGateState_Init(&_autop_ctx.gate_state);` (or `_autop_ctx.gate_state.flags = 0;`) alongside the six existing ones at `:308-315`. Zero wire impact, matches the established Layer-2 idiom, closes the class.
- **(b)** Give `SlowPathGateState` an NSDMI (`uint16_t flags = 0;`) at `SlowPathGateRegistry.hpp:184`. Cheapest, but silently changes `NodeContext`'s triviality and does **not** put the field in any partition — the complement gap survives.
- **(c)** Leave it and add the missing "deliberately uninitialized because…" citation. **Not recommended** — the reason would have to be "the reader is display-only", which is a property of *today's* consumer set, not of the field.

> **Novel alternative considered** (`feedback_proactive_novel_alternative_consideration`): rather than adding `gate_state` to the init registry, **delete the `NodeContext` copy entirely** and have the publisher read the gate bits it needs from the node's *resolved cfg* on demand. `gate_state` is a pure cfg-derived cache (`SlowPathGateRegistry.hpp:180-182`) fully rebuilt every slow-path entry — a cache with exactly one cross-thread reader that reads a *stale-or-indeterminate* value is arguably not earning its cache-line. **I do not recommend it**: the field is deliberately placed at HOT-cluster offset 0 for the decision-first bail-out (`ControllerEventLoop.hpp:318-329`), the in-band readers at `StrategyParameters.hpp:1201+` are on the latency-budgeted path, and re-deriving per read would reintroduce the branchy cfg dispatch the `.B.5` work removed. Recording it so the option is on the table and explicitly priced, not silently skipped.

### ⚠ S4-6 — `FOREACH_FAILURE_MODE` has **two** paired storage words; the overflow assert names **one**. — **MED (latent, spec-named)**

Bit positions from `FOREACH_FAILURE_MODE` are used by **two independent `uint16_t` words**:
- `PerNodeSnap.failure_flags` — `DataStream/EngineTUI.hpp:1251`
- `ModelHandle.drift_flags_at_load` — `ML_Headers/ModelInference.hpp:399`, set with `FAILURE_MASK_*` at `CoreFrameworks/ModelValidation.hpp:213` (column doc: `ML_Headers/CfgDriftCheckRegistry.hpp:121`)

and they are OR'd together at `CoreFrameworks/ShardedSnapshot.hpp:704-707` (+ the ensemble walk `:722-737`). The numbering is **consistent today** — *my initial "foreign bitmap OR'd in" hypothesis is REFUTED*; this is a correct design.

The gap is declarative. `MemHeaders/FailureModeRegistry.hpp:309-310` asserts only `FAILURE_BIT_COUNT <= 16` with the message *"exceeds uint16_t **failure_flags** capacity"* — `drift_flags_at_load` is nowhere declared as a paired storage word. This is **verbatim anti-pattern 4** of `bitmap-overflow-protection-discipline.md:331-345` ("Silently widening bitmap type without ensuring all consumers updated"): a future widening of `failure_flags` to `uint32_t` that updates the assert but not `drift_flags_at_load` makes the OR at `:704` truncate silently. The spec's own remedy is a `using FailureFlagsType = uint16_t;` alias plus a second assert; spec step 4 (`:107-116`) also requires the pairing be *documented*.

**Blast radius:** ML risk-control observability. Bits 11-15 are the drift/corruption family (`feature_hash_drift`, `scaler_drift`, `ml_model_corrupt` …) — the surface that gates `MODEL_CORRUPT` SHALT. Not capital-mutating, but it is the operator's only view of a corrupt-model refusal.

### ⚠ S4-3 — `FOREACH_PER_ARM_FLAG` generates the **fields** but not the **init**, and claims compile-time enforcement it does not have. — **MED**

`PER_ARM_FLAG_DECLARE_FIELDS()` (`ML_Headers/PerArmFlagRegistry.hpp:113-120`) generates one `uint8_t` per row into `EnsembleModelZoo` at `ML_Headers/NodeModelZoo.hpp:1179`. The **init is a hand-written three-line mirror** at `ML_Headers/NodeModelZoo.hpp:1471-1474` (verified: `EnsembleModelZoo_Init` is field-by-field, no wholesale memset of this cluster). The registry header states:

> *"Adding a new FOREACH_PER_ARM_FLAG entry requires adding ONE line here to keep them in sync (**compile-time enforcement**: missed init line = field stays uninitialized; first read triggers non-deterministic behavior **that's caught by parity tests**)."* — `ML_Headers/PerArmFlagRegistry.hpp:127-131`

**Both halves of that claim are false at HEAD.** (a) A missing init line is not a compile error — the field is generated regardless, so the build stays green. (b) The named catcher no longer exists: `parity_harness` was **RETIRED at `.E.1.1`** (root `CLAUDE.md`, `tests/` row). This is a Class-38 phantom-invariant / Class-51-adjacent shape: the registry↔init-site mirror has **zero** coverage check, and the comment tells the next author it is covered.

**Corroborating near-miss already in the file:** `NodeModelZoo.hpp:2023` (`EnsembleModelZoo_SetDisabledHorizons`) resets **one** of the three masks — legitimately, but it is exactly the partial-touch shape the missing coverage check would police. And `:2036` writes `ezoo->disabled_horizon_mask |= (1u << a);` raw rather than via `BITMAP_SET(..., BITMAP_BIT_U8(a))`, bypassing the `BITMAP_*` API the registry header prescribes at `:45-50`.

**Structural fix available at ~zero cost:** the file already has the machinery — replace the three hand-written lines with `FOREACH_PER_ARM_FLAG(PER_ARM_FLAG_INIT_FIELD_ONE)`. The header's own "future improvement candidate" note (`:132-136`) proposes a heavier nested-struct memset; the X-macro walk is strictly simpler and needs no consumer-site change.

### ⚠ S4-5 — `Summary_EmitPerStrategy` is an unguarded hand-coded mirror of a summary-registry subset. — **LOW-MED**

`MemHeaders/NodeCtxSummaryFieldRegistry.hpp:279-332` hand-aggregates 9 fields (`entries`, `exits`, `realized`, `fees`, `wins`, `losses`, `gross_wins`, `gross_losses`, `open_notional`) that are all also `FOREACH_NODE_CTX_SUMMARY_FIELD` rows. Adding a summable row to the registry silently omits it from `per_strategy` in `summary.json`. The file self-declares this at `:343-349` with a stated rationale (aggregation arithmetic differs per type) and names the eventual fix (`FOREACH_NODE_CTX_SUMMABLE_FIELD` sub-registry, `:347-349`). **Excluded-with-stated-reason → not the predictive smell**, but it is a genuine level-2 complement gap and the operator-facing artifact is the paper-reset archive.

### ⚠ S4-7 — `FOREACH_SP_SECTION` carries a **phantom H21 constraint**. — **LOW (inverse drift)**

`CoreFrameworks/SpSectionRegistry.hpp:24` tags `[REFERENCE]_[INVARIANT]_[H21]`, and `:77-81` says:

> *"For backward compat with **prior snapshot files that may persist per-section breakdown counts**, append new sections at the END of the registry."*

**Nothing persists `slow_path_breakdown`.** A full sweep of the identifier returns only: the struct decl (`ControllerEventLoop.hpp:793`), the init (`:817`), the enable (`EngineSharded/Run.hpp:1740`), the 5 sample sites (`EngineCommon.hpp:611-797`), and one TUI read (`DataStream/EngineTUI.hpp:2025`). Zero hits in `ShardedSnapshotPersist.hpp` / `ShardedSnapshot.hpp`.

This is the **inverse** of the usual drift: an over-claimed constraint rather than an under-claimed one. Per `dead-code-and-identifier-retirement-discipline.md` Rule 2 a runtime-only enum is **freely reorderable**; the prose imposes an append-only discipline the wire does not require, and the H21 tag makes `SP_SECTION` look ledger-eligible when it is not. Costless today, but it misleads exactly the person deciding whether an insertion is safe — and an *unfounded* H21 claim erodes the credibility of the founded ones.

---

## 4. Doc-drift cohort — the count-in-prose class, and the guard that would own it

Five confirmed instances, all in `[OVERVIEW]`/struct/test **prose**, all with every mechanical guard **GREEN**:

| # | Site | Says | Compiler says | Sev |
|---|---|---|---|---|
| **S4-2** | `CoreFrameworks/ControllerEventLoop.hpp:359` — `// v5.15.5.B.3 — 5 boolean flags bit-packed into uint8_t node_state_flags.` + a 5-item "Replaces:" list at `:360-361` | 5 | **6** (`MODEL_CORRUPT`, D-221). Registry's own `[OVERVIEW]` correctly says 6 (`NodeStateFlagRegistry.hpp:67`) | LOW |
| **S4-4** | `ML_Headers/EzooInitFlagRegistry.hpp:10, 21, 69, 88, 106` **+** `ML_Headers/NodeModelZoo.hpp:1174` — **six** sites saying "4 bits used" / "4/8 bits used" / "4 bits free", **four** of which name the **retired identifier `THOMPSON_READY`** (renamed `BUY_THOMPSON_READY` at `.F.4d`, per the row comment at `EzooInitFlagRegistry.hpp:80`) | 4 | **5** | **MED** — worst on shard; a retired name surviving in six places is tombstone-hygiene-adjacent even though the rename was legal (runtime-only, § 2) |
| **S4-8** | `CoreFrameworks/ControllerEventLoop.hpp:851` — `FOREACH_DISPLAY_META_FIELD(X) — 12 heterogeneous counters + flags` | 12 | **10** (`DISPLAY_META_FIELD_COUNT == 10` assert two files away at `DisplayMetaRegistry.hpp:155`) | LOW |
| **S4-9** | `ML_Headers/NodeModelZoo.hpp:1178` — `disabled_horizon_mask + arms_with_barriers_mask (uint8_t each, 8 arms = 8 bits)` | 2 masks | **3** (`corrupt_arms_mask`, D-221) | LOW |
| **S4-10** | `tests/controller_test.cpp:24013` `// Registry has 5 entries today (2 BIT_FLAG + 1 PERCENT_U8 + 2 COUNTER_U32)` and `:24018` `// BIT_FLAG count: 2 today` | 5 rows / 2 bits | **15 rows / 11 bits**. The live assertions are `>= 5` (`:24016`), `>= 6` (`:24102`), `>= 2` (`:24023`), `>= 7` (`:24600`) — **floors 4-10 rows below reality** | LOW-MED (test) |

**Which guard would have caught any of them: none.** Enumerated exhaustively:

- The bitmap `static_assert`s are `COUNT <= WIDTH` — pass at 4, 5, or 6.
- `check_code_tag_blocks.py` — **GREEN**; it validates tag *grammar* (categories, vocab, `[REFERENCE]` resolution), not the derived facts inside `[OVERVIEW]` prose.
- `check_identifier_retirement.py` — **GREEN**; it checks the name→value map in code, not comments. It would not flag `THOMPSON_READY` surviving in prose.
- `check_meta_registry.py` — **GREEN**; enrollment + LEVEL/PARENT topology only.
- Tests — **10 of my 13 registries have no test reference at all** (only `FOREACH_NODE_CTX_SUMMARY_FIELD`, `FOREACH_PER_NODE_STATE_FLAG`, `FOREACH_FAILURE_MODE` appear in `tests/`), and the three that do assert `>=` floors.

**The mechanism that would own this already exists as a declared-pending capability.** The `[DERIVED]` tool-owned block is the codebase's anti-drift device for exactly this fact class (`DOCS/SUBAGENT_ARMING.md` § 2.6: derived facts are tool-generated + CI-checked, never hand-edited). A `ROW_COUNT` generator is explicitly staged:

> `// [DERIVED]   (tool-refreshed — ROW_COUNT/CONSUMERS generators land with the drift-gate generalization; empty skeleton is correct, D-327)` — `CoreFrameworks/SpSectionRegistry.hpp:102`, `CoreFrameworks/SessionPhaseRegistry.hpp:180`, `CoreFrameworks/MetaRegistry.hpp:139`

**Only 2 of my 11 registry files carry the `[DERIVED]` skeleton at all** — `SessionPhaseRegistry.hpp` and `SpSectionRegistry.hpp`. The nine that lack it (`NodeCtxInitRegistry`, `NodeCtxSummaryFieldRegistry`, `DisplayMetaRegistry`, `NodeStateFlagRegistry`, `PerNodeStateFlagsRegistry`, `OmsStateFlagRegistry`, `PerArmFlagRegistry`, `EzooInitFlagRegistry`, `FailureModeRegistry`) contain **every one of the five drift instances**. I flag this as a **correlation, not a cause** — the landed skeletons are empty placeholders and prevented nothing (and `SpSectionRegistry` still carries S4-7). But it does mean the D-327 generator, when it lands, needs a **coverage sweep of its own** to enroll the other nine, or it will ship a guard that is green because it never looked.

---

## 5. Three-partition disagreement analysis — `NodeContext` (INIT / SUMMARY / PERSIST)

I own INIT and SUMMARY; `FOREACH_NODE_PERSIST_FIELD` is shard 1's. Membership below is compiler-verified on my two; the persist column is taken from the seed report's verified table.

**Denominators over ONE struct — five of them, none able to see the struct:**

```
49  NodeContext<F> top-level members   (ControllerEventLoop.hpp:315-614; seed report, clang+text+registry, 3-way agreement)
40  FOREACH_NODE_CTX_FIELD rows        (NodeCtxInitRegistry.hpp:98-145)     guard: >= 30   (floor)
15  RST-flagged subset                 (same registry, RESET column)        guard: == 15   (equality, subset-scoped)
20  FOREACH_NODE_CTX_SUMMARY_FIELD     (NodeCtxSummaryFieldRegistry.hpp:171-198) guard: >= 18 (floor)
29  FOREACH_NODE_PERSIST_FIELD parent rows / 46 flattened wire rows          [shard 1]
```

| # | Disagreement | Sev | Evidence |
|---|---|---|---|
| **D-1** | **`gate_state` is in NONE of the three partitions AND in no AUTOPOPULATE layer.** `drift_history` (the seed report's U-2) is in no *registry* but **does** get `DriftHistory_Init` (`NodeCtxInitRegistry.hpp:312`). `gate_state` gets nothing. It is the strictly-worse member and the partition-complement lens is what surfaces it | **HIGH** | § 3 / S4-1 |
| **D-2** | **SUMMARY ⊆ INIT holds exactly — 20 of 20 — and nothing asserts it.** A summary row naming a field with no init row would emit an **uninitialized value into operator-facing `summary.json`** via `Summary_EmitPerCoreEntry` (`NodeCtxSummaryFieldRegistry.hpp:239-249`). The property is free today and one row-addition away from breaking, silently. **This is the cheapest guard on the shard**: a single X-macro cross-walk asserting every SUMMARY name resolves to an INIT row | **MED** | verified name-by-name against `NodeCtxInitRegistry.hpp:98-145` |
| **D-3** | **The seed report's E-1, sharpened.** The Init registry's NORST rationale names five sub-structs as load-bearing across reset — *"confidence / pnl_feeder / regime_state / turnover / drift_history"* (`NodeCtxInitRegistry.hpp:182-186`). **But that same comment concedes at `:185-186` that those sub-structs "aren't in this scalar registry anyway".** So the Init registry does **not declare** `turnover`/`drift_history` NORST — it merely *mentions* them. Their reset behavior is determined by **absence** from `_node_ctx_reset_value_fields` (`:209-218`), i.e. by omission, not by declaration. The paper-RESET-preserves / warm-RESTART-destroys asymmetry the seed report flagged is therefore anchored in **exactly one prose sentence, with no mechanical binding at either end** | **MED** | as cited |
| **D-4** | `node_dd_pct` sits in **INIT + SUMMARY but not PERSIST** (dropped at v11, D-420). Any partition tool keyed on "member of *any* registry" mis-buckets it — as does one keyed on "member of *all*" | **LOW** | `NodeCtxInitRegistry.hpp:144` + `NodeCtxSummaryFieldRegistry.hpp:195` vs the v11 drop (seed report E-3) |
| **D-5** | `node_state_flags` is an INIT row (`NodeCtxInitRegistry.hpp:107`) but its persist coverage is a **single bit under a different name** (`node_kill_tripped`). The INIT partition treats it as one scalar; the PERSIST partition treats it as one bit. **Neither partition can express "partially covered"** — a three-partition guard must decide (seed report OQ-2) whether the domain is *fields* (49) or *fields + bits* | **LOW-MED** | `NodeCtxInitRegistry.hpp:107` vs `MemHeaders/NodeCtxPersistRegistry.hpp:97` |
| **D-6** | The RESET partition is the **only** one with an equality lock (`== 15`, `NodeCtxInitRegistry.hpp:262`) — and it is scoped to a *subset*, so it cannot see a field that is missing from the parent list entirely. The INIT (`>= 30`) and SUMMARY (`>= 18`) floors sit 10 and 2 rows below reality respectively | **LOW** | as cited |

**Net:** the three partitions **reconcile** on every field except `gate_state`, and the reconciliation is **entirely un-asserted**. The `49 = covered + exempt` identity the seed report identified as "genuinely new information no landed guard asserts" holds for INIT and SUMMARY too — with the additional finding that INIT's complement is **not** empty.

---

## 6. HAZARDS

- **HAZ-S4-1 — `gate_state` is invisible to a name-diff guard *and* to an "any registry" guard.** It is in none, so a naive complement check catches it — but a check written to the *persist* partition's exemption vocabulary (`POINTER / EPHEMERAL / RECOMPUTED / …`, seed report OQ-3) would bucket it "RECOMPUTED" from the persist rationale and **wrongly clear it for INIT**. Per-partition exemption reasons must be **per-partition**; this is the worked proof.
- **HAZ-S4-2 — display-plane bit positions become wire-visible under the decoupling roadmap.** `PerNodeSnap.state_flags` (11 bits) and `PerNodeSnap.failure_flags` (11 bits) are in-process today (`DataStream/EngineTUI.hpp:880`), so their positions are freely reclaimable. `plans/_future/2026-05-12-decoupling-endgoal-roadmap.md` has the engine running headless with **multiple viewers attaching concurrently** — at that moment `TUISnapshot` becomes a cross-process wire and **22 bit positions retroactively become H21 append-only**, with no tombstone history for anything reclaimed in the interim. `check_identifier_retirement.py`'s own docstring (`:33`) already stages this: *"bit-assignments + cfg-field name keys enroll next."* The forward-compatible move (`feedback_fix_toward_future_trajectory_not_static_state`) is to enroll them **before** the transport changes, not after.
- **HAZ-S4-3 — `FOREACH_SESSION_PHASE` rows generate operator-visible cfg key names.** `session_<name_lower>_mult` (`CoreFrameworks/SessionPhaseRegistry.hpp:32`, consumed at `ShardedSnapshot.hpp:199` / `ControllerEventLoop.hpp:2703` / `PortfolioController.hpp:1605`). Renaming a row renames a live `engine.cfg` key — an H21 cfg-field-name-key surface, and it is **not** in the retirement ledger (same staged gap as HAZ-S4-2). The registry is otherwise the cleanest on the shard.
- **HAZ-S4-4 — the `>= N` floor assert is the shard's dominant guard form and is structurally near-vacuous.** `NODE_CTX_INIT_FIELD_COUNT >= 30` (actual 40), `SUMMARY >= 18` (actual 20), `SP_SECTION_COUNT >= 5` (actual 5), `FOREACH_FAILURE_MODE_COUNT >= 5` (actual 15), `FAILURE_BIT_COUNT >= 2` (actual 11), `PER_NODE_STATE_FLAG >= 7` (actual 11), `PER_ARM_FLAG_COUNT >= 2` (actual 3). A floor 10 rows below reality asserts almost nothing. `/readiness` Check 21 apparently *prescribes* the `>=` style — worth re-examining, because the two registries that use **equality** (`GATE_DIAG_PAIR == 6`, `DISPLAY_META_FIELD == 10`) are the two whose counts are correct in every prose site on the shard.
- **HAZ-S4-5 — `MemHeaders/DisplayMetaRegistry.hpp:133-136` is a macro-continuation trap.** Row 10 at `:133` has **no trailing backslash**; the macro body ends there. Lines `:134-136` are trailing `/* … */` comments *outside* the macro that carry `\` continuations and therefore **look** like they are inside it. Benign today (arithmetic confirms 10 rows, and the `== 10` assert compiles), and the placement is deliberate per `:180`. But the header instructs "append one row" (`:173`) and the visually-obvious append point is **after** the trap. Worth a one-line marker.
- **HAZ-S4-6 — a `[DERIVED]`-block ROW_COUNT generator (D-327) must sweep for enrollment or it ships vacuously green.** Only `SessionPhaseRegistry.hpp` and `SpSectionRegistry.hpp` carry the skeleton; the nine files holding all five drift instances do not. A generator that refreshes only enrolled blocks is a Class-51 sub-shape B guard (empty input).

---

## 7. Spots most worth an adversarial refute (for the paired a-class)

1. **S4-1's exposure window — attack it hard, both directions.** I proved `gate_state` is written *only* at `ControllerEventLoop.hpp:2685-2686` and read cross-thread at `ShardedSnapshot.hpp:597`. I did **not** establish the actual thread interleaving at boot. *Refute the finding:* show the publisher cannot run for slot `i` before that slot's first slow-path cycle — e.g. `registered_count` is incremented only after the first cycle, or the publish path is gated on a warmup flag. *Refute my hedge:* find a **second** reader of `state->nodes[i].gate_state` outside the `:2685`→`:3003` ordered body, or a path where the slow thread stalls (backpressure / `poll_interval` starvation / a node registered but never ticked) that widens the window from milliseconds to indefinite. The former downgrades S4-1 to hygiene; the latter upgrades it.
2. **My "blast radius is display-only" claim on S4-1.** I traced the in-band `gate_state->flags` readers to `ml_ctx.gate_state`, wired at `ControllerEventLoop.hpp:3003`, downstream of `:2685`. **Try to break it:** is `ml_ctx` ever constructed on a path that does *not* run `SLOW_PATH_GATE_AUTOPOPULATE_PER_NODE` first — the backtest driver (`CoreFrameworks/ShardedBacktestDriver.hpp`), the deprecated `PortfolioController` path, hot-swap, or warm-restart? `MASK_LADDER_ACTIVE` / `MASK_CONFIDENCE_ENABLED` / `MASK_RIDGE_*` gate **entry sizing**. If any construction path skips the populate, this escalates from observability to a capital path.
3. **The `EventLoopState<F> state;` default-init claim (S4-1 fact 4).** I read `CoreFrameworks/EngineSharded/Run.hpp:821` and confirmed no `{}` / no `static`, and confirmed `EventLoopState_Init` does not memset. **Verify independently** — check the **backtest** construction site and the ~15 `tests/controller_test.cpp` sites (`:5697`, `:7070`, `:7500`, …); if any construct with `{}` or `static`, the *test* environment zero-inits while *production* does not, which is the worst case (green tests, live divergence) and **raises** severity rather than lowering it.
4. **S4-3's "false enforcement claim".** I assert a missed `FOREACH_PER_ARM_FLAG` init line produces no compile error and that the named catcher (`parity_harness`) is retired. **Refute by** finding a surviving parity/determinism gate that would catch an uninitialized `uint8_t` on `EnsembleModelZoo` — `tools/check_determinism.sh` gate 4, an ASan/MSan build, or a `controller_test` fixture that memsets the ezoo. If one exists the claim softens to "enforcement exists but is not compile-time".
5. **S4-6's "consistent numbering today".** I refuted my own foreign-bitmap hypothesis via `ModelValidation.hpp:213` + `CfgDriftCheckRegistry.hpp:121`. **Push on it:** enumerate *every* writer of `drift_flags_at_load` (I found the `FOREACH_CFG_DRIFT_CHECK` walker and `ArchFieldDrift`) and confirm each uses a `FAILURE_MASK_*` constant rather than a literal or a different registry's mask. One raw-literal writer turns S4-6 from latent to live. Per `feedback_enumerate_set_before_categorical_claim` I enumerated the OR sites but **not** exhaustively the SET sites.
6. **The bit-accounting "zero undeclared live bits" claim (§ 2).** I derived it from `rg` for `<word>\s*(=|\|=|&=|\^=)` outside the registry headers. That misses: writes through a pointer/reference alias, `memcpy` into the containing struct, and `__atomic_fetch_or` (which `FailureModeRegistry.hpp:340-343` explicitly provides as `FAILURE_ATOMIC_SET`). **Re-derive with those forms included** — my grep would not have seen `BITMAP_ATOMIC_SET` call sites at all.
7. **S4-7's "nothing persists `slow_path_breakdown`".** Single-identifier sweep. **Attack the generality:** is `NodeContextDisplayMeta` ever written wholesale (fwrite/memcpy of the struct, a `[DERIVED] [SIZE]_[9856B]` byte-context site)? `tools/gen_code_map.sh --byte-context NodeContextDisplayMeta` is the authoritative check and I did **not** run it. If the struct is byte-serialized anywhere, the H21 tag at `SpSectionRegistry.hpp:24` is founded and S4-7 inverts.
8. **D-2's "SUMMARY ⊆ INIT, 20 of 20".** Verified by name against the 40 INIT rows. **Re-verify mechanically** — a name that differs only by case or a trailing token would slip past a human check, and the consequence (uninitialized value in operator-facing `summary.json`) is the kind of thing that reads as plausible data.

---

## 8. Recommendation

**Ranked, no edits made, consult-before-coding per the standing contract.**

1. **Close S4-1 now, in-flight** (`feedback_close_out_now_over_defer_when_small`): one Layer-2 line in `NODE_CTX_INIT_AUTOPOPULATE` (`MemHeaders/NodeCtxInitRegistry.hpp:308-315`) zeroing `gate_state`. Zero wire impact, matches the six existing Layer-2 helper-Init calls, and it is the only *live* correctness item on the shard.
2. **Land the D-2 containment assert** — the cheapest structural guard available on this shard: an X-macro cross-walk asserting every `FOREACH_NODE_CTX_SUMMARY_FIELD` name resolves to a `FOREACH_NODE_CTX_FIELD` row. It converts a free property into an enforced one and directly protects an operator-facing artifact.
3. **Declare the second `FOREACH_FAILURE_MODE` pairing (S4-6)** via the spec's own remedy (`bitmap-overflow-protection-discipline.md:341-345`): a `using FailureFlagsType = uint16_t;` alias + a second `static_assert` naming `drift_flags_at_load` + the step-4 pairing comment. ~4 lines, closes a spec-named anti-pattern.
4. **Registry-drive the per-arm init (S4-3)** and correct the false enforcement claim at `ML_Headers/PerArmFlagRegistry.hpp:127-131`. The X-macro walk is simpler than the nested-struct alternative the header proposes.
5. **Fold the doc-drift cohort (S4-2 / S4-4 / S4-8 / S4-9 / S4-10) into the D-327 `[DERIVED]` ROW_COUNT generator's ship** rather than hand-fixing six prose sites — this is the SSoT answer, and hand-fixing would re-create the same drift on the next row addition. **Carry HAZ-S4-6 as a hard requirement of that ship:** the generator must sweep for `[DERIVED]`-block enrollment across all registry files, or it ships vacuously green over the nine files where the drift actually lives. The one exception worth an immediate manual fix is the **retired `THOMPSON_READY` name surviving in four EZOO sites** — that is tombstone hygiene, not a count, and the generator will not touch it.
6. **Track HAZ-S4-2 / HAZ-S4-3 as homed items** (`feedback_no_unhomed_debt_code_smell`) against the decoupling roadmap and the staged ledger enrollment at `tools/check_identifier_retirement.py:33` — not as new TECH_DEBT rows, since both already have declared homes.

**What I am explicitly reporting as CLEAN, because a clean registry is a result:** `FOREACH_GATE_DIAG_PAIR` and `FOREACH_DISPLAY_META_FIELD` (struct-generated, exclusions stated — the false-positive-guard case, correctly identified and correctly clean); `FOREACH_OMS_STATE_FLAG` + `FOREACH_OMS_STATE_MULTI_BIT` (the only genuine bit-region coverage assert on the shard, verified to have teeth); `FOREACH_SESSION_PHASE` (a genuine 24-hour domain-coverage assert, all three consumers registry-generated); `FOREACH_SP_SECTION` (complement ∅ in both directions); and the **entire bitmap bit layer** — every bit of all seven storage words is declared, reserved-with-reason, or provably unwritten.

---

**Key files** (all absolute):
`/home/caramel/code/FoxML_Trader_v2/MemHeaders/NodeCtxInitRegistry.hpp` · `/home/caramel/code/FoxML_Trader_v2/MemHeaders/NodeCtxSummaryFieldRegistry.hpp` · `/home/caramel/code/FoxML_Trader_v2/MemHeaders/DisplayMetaRegistry.hpp` · `/home/caramel/code/FoxML_Trader_v2/MemHeaders/NodeStateFlagRegistry.hpp` · `/home/caramel/code/FoxML_Trader_v2/MemHeaders/PerNodeStateFlagsRegistry.hpp` · `/home/caramel/code/FoxML_Trader_v2/MemHeaders/OmsStateFlagRegistry.hpp` · `/home/caramel/code/FoxML_Trader_v2/MemHeaders/FailureModeRegistry.hpp` · `/home/caramel/code/FoxML_Trader_v2/ML_Headers/PerArmFlagRegistry.hpp` · `/home/caramel/code/FoxML_Trader_v2/ML_Headers/EzooInitFlagRegistry.hpp` · `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/SessionPhaseRegistry.hpp` · `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/SpSectionRegistry.hpp` · `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/ControllerEventLoop.hpp` · `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/SlowPathGateRegistry.hpp` · `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/ShardedSnapshot.hpp` · `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/ShardedSnapshotPersist.hpp` · `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/EngineSharded/Run.hpp` · `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/EngineCommon.hpp` · `/home/caramel/code/FoxML_Trader_v2/ML_Headers/NodeModelZoo.hpp` · `/home/caramel/code/FoxML_Trader_v2/ML_Headers/ModelInference.hpp` · `/home/caramel/code/FoxML_Trader_v2/ML_Headers/CfgDriftCheckRegistry.hpp` · `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/ModelValidation.hpp` · `/home/caramel/code/FoxML_Trader_v2/DataStream/EngineTUI.hpp` · `/home/caramel/code/FoxML_Trader_v2/DataStream/CalibLogColRegistry.hpp` · `/home/caramel/code/FoxML_Trader_v2/DESIGN_SPECS/refactor-patterns/bitmap-overflow-protection-discipline.md` · `/home/caramel/code/tick-trader-percore-workspace/tools/identifier_ledger.txt` · `/home/caramel/code/tick-trader-percore-workspace/tools/check_identifier_retirement.py` · `/home/caramel/code/FoxML_Trader_v2/plans/v5.15-live-readiness/reports/2026-08-15-ui-consolidation/i-class-nodecontext-partition.md`