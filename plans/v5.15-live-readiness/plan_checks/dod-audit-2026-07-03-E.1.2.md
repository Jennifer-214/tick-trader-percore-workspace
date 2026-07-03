# /dod-audit report — E.1.2 NodeState/Position SoA layout freeze — 2026-07-03

**Agent:** i-class (INVESTIGATIVE) · **Skill:** /dod-audit (plan-mode) · **For:** Caramel
**Target:** `plans/v5.15-live-readiness/subplans/2026-06-15-v5.15.5.F.4d.1.E.1.2-nodestate-soa-layout.md` (reformalized v1.0, 2026-07-02)
**Engine HEAD:** `b10e778` (byte-identical to E.1.1 ship `0ee227a`) · all `file:line` re-grounded at HEAD via grep + cascade tools (NOT recalled)
**Invariants in play:** H4 H6 H10 H12 H14 H22 · **Anti-patterns watched:** Class 26/27, Class-45 (D-110), Class-51 (vacuously-green guard)

## Catalog ingested (patterns bearing on this surface)
portfolio-soa-vectorization-pattern (Stage 2-draft; D-55 first-canonical AVX @ .E.6/.E.7) · cache-line-discipline (Stage 2) · per-node-purity-scale-invariance (Stage 3; H22) · multi-bit-state-encoding-pattern (H14) · bitmap-overflow-protection-discipline · registry-tuple-as-single-source-of-truth · heterogeneous-registry-pattern · autopopulate-pattern-for-production-caller-class · struct-change-cascade-impact-tooling (D-202/D-229) · wire-format-byte-preservation-discipline (H12/H21) · per-node-position-ownership-model.

## Mechanical tools RUN (authority over grep)
- `gen_code_map.sh --composition "Position<64>"` → **0 direct + 0 transitive containers** (the 192B freeze is CONTAINED — confirms plan). NOTE: --composition catches EMBEDDING, NOT AoS access-pattern rewrite (see F2).
- `gen_code_map.sh --byte-context "Position<64>"` → 2 size-pins (`Portfolio.hpp:117`, `:143`) + `PortfolioController.hpp:2036-2040` (dead serializer, delete-target).
- `check_struct_alignment.py` → GREEN; all 4 byte-serialized types size-pinned. (b)-advisory: `ExecutionCore` + `PerNodeSnap` etc. lack `static_assert(alignof==64)` (pre-existing, out of scope).
- `check_struct_size_budget.py` → Position=128B, Portfolio=2112B, ExecutionCore=66.8KB — all within budget. Manifest is a derived-fact the freeze must update (F6).
- grep (verified): **NO AVX/`__m512`/`_mm512` kernel over Position/Portfolio/ExecutionCore exists.** PositionExitGate has **zero call sites** (only def @ `Portfolio.hpp:478` + comments). `check_determinism.sh:33` = gate 4 = the real H10 AVX-vs-scalar-#else check.

## Summary
| Pattern / invariant | Verdict |
|---|---|
| portfolio-soa-vectorization (D-55) / H10 | **MISSED/INCOHERENT** — claimed, not wired; scope-contradicted (F1) |
| struct-change cascade (AoS accessors) | **MISSED** — blast-radius omitted (F2, conditional on F1) |
| multi-bit-state-encoding / H14 | **MISSED** — riding-flag encoding unspecified (F3) |
| compose-sub-registries serializer | **SOUND** — Stage-2 call correct; route /registry-fit-audit (F4) |
| slow_account Money vs FPN (H4) | **CLEAN (plan catches)** — sketch is the landmine (F5) |
| size-pin enumeration completeness | **INCOMPLETE** — size_budget manifest omitted (F6) |
| owner_node_id cap consistency (H22) | **LOW gap** (F7) |
| H6 alignas(64) 3-cache-line / H12 padding | mostly sound; H12 named-pad rider (in F1/F3) |

## Findings (severity-ordered)

### HIGH — F1 · SoA/AoS scope contradiction ⇒ vacuous H10 guard-row (the central finding; ship-blocker-until-resolved)
- **Surface:** plan L42/L50/L79/L136/L142 vs the RE-GROUNDED Phase-B mechanic; `Portfolio.hpp:151-155` (AoS `Position<F> positions[16]` today); grep-verified no AVX kernel.
- **Pattern:** `portfolio-soa-vectorization-pattern.md` (Stage 2-draft; **D-55 stages the SoA-vectorization AVX kernel first-canonical at .E.6/.E.7, NOT E.1.2**); `cache-line-discipline.md` (SIMD parity); CLAUDE.md **H10**; RECURRING_BUG_PATTERNS **Class-51** (vacuously-green guard).
- **Symptom:** The authoritative RE-GROUNDED coding mechanic (Phase B L79: *append `peak`/`owner_node_id`/riding-flag rows to `FOREACH_POSITION_FIELD` → grow 128→192B*) produces an **AoS struct**. Yet the acceptance criterion (L50), guard-row §4a (L136), and INBOUND seam (L142) assert E.1.2 is *"the first real SoA AVX kernel with bytewise-identical scalar fallback."* (a) No AVX kernel over Position exists; (b) no phase wires one; (c) D-55's own staging defers the vectorization kernel to .E.6/.E.7; (d) the plan says H10 is *"VALIDATED against E.1.0's ±USE_NATIVE_128 gate"* — but that gate is the **128-bit-arithmetic-backend** snapshot round-trip, NOT `check_determinism.sh` **gate 4** (AVX-512 byte-identical to scalar `#else` — H10's actual subject). **⇒ the H10 guard-row is VACUOUS in E.1.2 (Class-51): a guard-coverage-matrix §4a row claimed filled when nothing bites.** Conversely, if the SoA *layout* pivot (`positions[]`→per-field arrays) IS intended per D-55's ".E.1 layout transition," the plan gives NO concrete per-field-array spec (only the SUPERSEDED scaffold's one-liner L150-151) and enumerates NONE of the AoS-accessor rewrite (F2).
- **Fix (recommended):** Resolve scope BEFORE Phase B. E.1.2 = **struct-grow AoS 192B only**; **STRIKE** the "first real SoA AVX kernel" + H10-guard-fill claims (L50/L136/L142) and **re-home H10-first-consumer to the .E.6/.E.7 vectorization leaf** per D-55's own staging; keep "SoA" out of E.1.2 acceptance (or scope it explicitly to *serializer field-grouping*, not a `positions[]` pivot). If the pivot IS wanted, add F2's blast-radius + a per-field-array layout spec. Either way, E.1.2's determinism gate is the **snapshot round-trip** (correct + kept), which is NOT H10 — do not conflate.
- **Effort:** plan edit (1-2 paragraphs) to disambiguate + strike/re-home; the code cost is unchanged.

### HIGH — F2 · AoS-accessor blast-radius omitted; PositionExitGate under-enumerated (CONDITIONAL on F1 = "SoA pivot in scope")
- **Surface (grep-verified dead/AoS):** `Portfolio.hpp:478` PositionExitGate (**0 call sites** — dead per I3), `:233` Position_Reset, `:262-277` Portfolio_Add, `:251` Portfolio_Find, `EngineSharded/Async.hpp:830` (`state.oms->portfolio.positions[portfolio_slot].quantity`), `ShardedSnapshotPersist.hpp:169`. Plan grep for these = **EMPTY**.
- **Pattern:** `struct-change-cascade-impact-tooling.md` (D-202 — `--composition` measures EMBEDDING, not `.positions[i].field`→`.field[i]` access rewrite); Class-45/**D-110** (silent-zero-on-restore).
- **Symptom:** If SoA pivots `positions[]`, PositionExitGate is a **THIRD** SoA-forced-broken function (AoS reads @ `:486-487`) that the synthesis MISSES — it flags only `PortfolioController_SaveSnapshot` as "SoA-forced-deletion (struct is live → stops compiling)." **Re-wiring (vs deleting) PositionExitGate re-introduces a SECOND writer to `active_bitmap`** (`:509` `active_bitmap &= ~(1<<idx)`) — the single-writer invariant its deadness currently preserves (the task's I3 concern). Portfolio_Add/Position_Reset/Async.hpp:830 all break too.
- **Fix:** If SoA in scope → enumerate every AoS-accessor site; **DELETE (never re-wire) PositionExitGate**; assert `active_bitmap` stays drainer-single-writer. If struct-grow only (F1 recommended) → **MOOT**: PositionExitGate keeps compiling, stays dead-but-inert (note it as such).

### MED — F3 · riding-flag(s) H14 encoding unspecified on a FROZEN struct
- **Surface:** plan L64/L79 ("riding-flag(s)… exact sub-layout = a Phase-B call; all named + `=0`-init"); grep-confirmed NO MBS_/BITMAP_ mention. Precedent EXISTS: `MemHeaders/BitmapMacros.hpp:82` (`BITMAP_SET`), `:205-214` (`MBS_SET_U8`/`MBS_GET_U8`/`MBS_EQ_U8` over `uint8_t`).
- **Pattern:** `multi-bit-state-encoding-pattern.md`; `bitmap-overflow-protection-discipline.md`; CLAUDE.md **H14** (C++ bitfield syntax FORBIDDEN — layout/signedness/packing-order implementation-defined ⇒ conflicts with the PERSIST wire + H12).
- **Symptom:** The plan leaves the D-206 give-back riding-flag(s) + 16-bit fill-record-owner as "a Phase-B call" without mandating H14-compliant `MASK_*`/`SHIFT_*` + `MBS_*`/`BITMAP_*` over `uintN` storage. For "open the struct ONCE," the flag encoding IS a locked layout decision; silence risks a bare-bool or (worse) a C++ bitfield → a re-touch of a FINAL struct.
- **Fix:** Phase B specifies the flag(s) as a `uint8_t`/`uint16_t` bitmap FOREACH_POSITION_FIELD PERSIST row + named `MASK_*`/`SHIFT_*` + BitmapMacros accessors + a `static_assert` bit-count guard (bitmap-overflow-protection).

### MED — F4 · compose-sub-registries serializer: SOUND shape + Stage-2 call is CORRECT (route /registry-fit-audit)
- **Surface:** `ShardedSnapshotPersist.hpp:161` (`FOREACH_OMS_FIELD` flat DIRECT/BIT), `:260` (`ConfidenceScorer_FieldwiseWrite` — already a `FOREACH_CONFIDENCE_PERSIST_FIELD` sub-walker, enrolled `MetaRegistry.hpp:102`), `:172-261` save / `:436-499` load hand-loop; plan Phase C.
- **Pattern:** `registry-tuple-as-single-source-of-truth.md`, `heterogeneous-registry-pattern.md` (SCOPE COLUMN vs DOMAIN SPLIT), `autopopulate-pattern-for-production-caller-class.md`.
- **Verdict — SOUND.** A flat `FOREACH_NODE_PERSIST_FIELD` (OMS-style DIRECT/BIT) CANNOT express NodeContext's nested `regime_state` struct + `pnl_feeder` array+ints + the confidence sub-registry — compose-sub-registries (thin outer loop delegating to sub-walkers) is the right shape; the `:260` confidence delegation already proves the mechanic. Keeping it **Stage-2 (NO `SERIALIZER_GENERATED` meta-flag)** is CORRECT: avoids the TD-057 schema cascade; respects pattern-codification-lifecycle (don't codify pre-2nd-application); grep-zero on `SERIALIZER_GENERATED` = no cascade to hook.
- **a-class flag:** moving Position off the raw-blob (`:169`, writes the 7B `_pad_pos` + reserved pad) to field-by-field gather DROPS padding from the wire — fine under the VERSION bump, but the load side (`:436-499`) must match field-exact; a dropped SoA field = **D-110** (the exact TECH_DEBT-196 close the plan claims).

### MED — F5 · slow_account Money-vs-FPN trap: plan CATCHES it; the referenced SKETCH is the landmine (VERIFIED-CLEAN as intent)
- **Surface:** `.E.1-foundation.md:432-436` — the v0.1 NodeState sketch declares `FPN<F> realized_pnl/open_notional/capital_allocated/drawdown_max/drawdown_current`. Plan L90 (Phase F) + L152 explicitly require **Money** + *"RE-GROUND it; its `FPN<F>` money fields must be `Money`."*
- **Pattern:** `per-node-purity-scale-invariance.md` (owner ⊥ tier ⊥ thread ⊥ wire); **H4**.
- **Verdict:** Plan correctly flags the silent-encoding-epoch trap (synthesis frozen-item 1). Correctly prunes `drawdown_max` (0 consumers) + `drawdown_current` (derivable). **CLEAN** — but the Phase-F implementer must NOT copy the FPN/`MAX_CORES`-phantom sketch verbatim. Carry the sketch's H12 discipline (`uint8_t mode; uint8_t _padding0[3]`) forward.

### LOW — F6 · size-pin enumeration incomplete: `check_struct_size_budget.py` manifest omitted
- **Surface:** the tool tracks Position=128B + Portfolio=2112B (hardcoded manifest); plan Phase B/G enumerate only `check_struct_alignment.py` Check-K + `Portfolio.hpp:117/143`.
- **Pattern:** `struct-change-cascade-impact-tooling.md` (**D-229** derived-fact drift — the guard this NEW `.E.1.0` tool IS).
- **Symptom:** Position 128→192B ⇒ Portfolio 2112→3136B. Leaving the size_budget manifest stale = the exact drift the tool exists to prevent.
- **Fix:** Phase B/G update the tool's manifest for BOTH Position + Portfolio + re-run `--selftest`; L1d budget stays green (3136B ≪ 48KB).

### LOW — F7 · owner_node_id=(cluster<<8)|node vs MAX_EXECUTION_NODES consistency (H22)
- **Surface:** `Limits.hpp:5/19` (MAX_PORTFOLIO_POSITIONS=16, MAX_EXECUTION_NODES=16); plan L90 (new caps ≤256 each; `owner_node_id=(cluster<<8)|node`).
- **Pattern:** `per-node-purity-scale-invariance.md` (§ Scale to N clusters); `per-node-position-ownership-model.md`.
- **Symptom:** the uint16 encoding admits node∈[0,255]×cluster∈[0,255] while the deployment caps at MAX_EXECUTION_NODES=16 / MAX_PORTFOLIO_POSITIONS=16. Keeping MAX_NODES_PER_CLUSTER distinct is correct; add a `static_assert` reconciling MAX_NODES_PER_CLUSTER×MAX_CLUSTERS vs the deployment cap so an owner_node_id can't encode a node beyond the slot cap. Reservation-level; fold at Phase F.

## Recommendations
**Resolve before Phase B (blocking):** F1 (disambiguate SoA scope + strike/re-home the H10 guard-fill) — this gates F2. **Fold into the plan now:** F3 (riding-flag H14 encoding), F6 (size_budget manifest), F7 (cap static_assert). **Confirm + proceed:** F4 (sound; /registry-fit-audit sign-off), F5 (plan-intent clean; guard the sketch copy). **No CRITICAL code findings** — this is a plan audit; the sharp edge is a plan-coherence gap on a FROZEN "open-once" struct.

## Verdict: YELLOW (leaning RED-if-unresolved)
No CRITICAL. One HIGH plan-coherence blocker (F1) + one conditional HIGH (F2) that MUST be resolved before Phase B — on a foundation-freeze leaf, an unresolved SoA/H10 scope contradiction risks either a Class-51 vacuous guard-claim OR a mid-ship AoS-accessor compile-cascade (the expensive re-traversal the ship exists to avoid). Struct-grow AoS 192B is otherwise sound + well-guarded.

## Spots most worth an adversarial (a-class) refute
1. **F1 resolution** — is the SoA LAYOUT pivot actually REQUIRED at E.1.2 by a downstream spine? Code-read what E.1.3+ reads from `Portfolio.positions` — if a spine needs SoA-laid-out positions, deferring forces a SECOND struct-open (violates "open ONCE") and my "struct-grow only" call inverts.
2. **F2 deadness** — is PositionExitGate REALLY dead, or live on the legacy `engine_arch=centralized` path (`main.cpp:9` names it in the pipeline comment)? If centralized still wires it at HEAD, SoA breaks a LIVE path, not dead code.
3. **F1 H10 vacuity** — refute the "gate 4 ≠ ±USE_NATIVE_128" distinction: does E.1.0's ±USE_NATIVE_128 round-trip transitively exercise ANY existing SIMD kernel (RollingStats AVX-512) such that H10 is non-vacuously covered even without a Position kernel?
4. **F4 Stage-2** — refute "keep informal": confidence-sub-walker is the 1st application, compose-sub-registries the 2nd — does pattern-codification-lifecycle / H18 make codification DUE now, not deferrable?
