# A-class adversarial verify — E.1.2 pre-coding gate (2026-07-03)

**Role:** a-class (ADVERSARIAL / default-refuted). Refute the 3 most-consequential, least-cross-confirmed i-class findings by CODE-READ. Engine HEAD `b10e778` (byte-identical to E.1.1 ship `0ee227a`). All `file:line` grepped/Read at HEAD, not recalled.

---

## T1 — Serializer scalar-drop (AR-11: parity-check vs dod-audit) → **CONFIRMED** (parity-check right; plan Phase-C materially wrong)

**Code-read of the ACTUAL NodeContext save loop `ShardedSnapshotPersist.hpp:172-261` (load `:436-499`).** Per-node the loop `fwrite`s, in order:

- FLAT scalars (direct `fwrite(&ctx.FIELD,…)`, NO named walker): `strategy_id`/`resolved_strategy_id`/`strategy_state_kind` (`:176-182`); **`allocated_balance`** `:187`; `entries_processed`/`exits_processed` `:190-191`; **`node_realized`/`node_fees`/`node_open_notional`** `:192-194`; `node_wins`/`node_losses` `:195-196`; **`node_gross_wins`/`node_gross_losses`** `:202-203`; `idle_cycles` `:204`; **`last_entry_price`** `:207`; `last_entry_tick`/`sl_cooldown_remaining` `:208-209`; **`node_peak_balance`/`node_dd_pct`** `:212-213`; `kill_byte` (from `node_state_flags`) `:218-221`; `node_ks_trips_total` `:227`; + the 3 prediction doubles **`staged_prediction`/`active_prediction`/`last_confidence`** `:244-246`.
- NESTED sub-walkable (inline today): `regime_state.*` 7 fields `:230-236`; `pnl_feeder.price_samples[8]`+head+count `:239-241`; `ConfidenceScorer_FieldwiseWrite(&ctx.confidence)` `:260` (the ONE existing named registry walker).

**Count:** ≈24 flat scalars incl. **9 `Money`** (allocated_balance, node_realized, node_fees, node_open_notional, node_gross_wins, node_gross_losses, last_entry_price, node_peak_balance, node_dd_pct) + **3 doubles**. Parity-check's enumeration is ACCURATE.

**Decision-log resolve:** D-283 item(2) (`decision-log:1810`) explicitly mandates *"registry-drive the NodeContext persist-serializer (the hand fwrite-loop … → **`FOREACH_NODE_PERSIST_FIELD`, mirroring FOREACH_OMS_FIELD**)"* — a FLAT registry. D-287 (`:1828`) refuted only *"the fabricated `SERIALIZER_GENERATED` flag"* (the meta-registry enforcement bit) — it did **NOT** authorize dropping the flat registry. `rg FOREACH_NODE_PERSIST_FIELD` = **0 hits** → it is a to-BUILD registry D-283 ordered and the plan drops.

**Plan Phase-C wording (`plan:83`):** *"a thin loop delegating to regime_state + pnl_feeder + confidence sub-walkers. **NOT a flat FOREACH_NODE_PERSIST_FIELD**."* Those 3 delegates cover ONLY the nested/array block (~17 nested fields); the ≈24 flat scalars (9 Money + 3 doubles) get **no registry home** → as worded, DROPPED (D-110 silent-zero-on-restore) OR left as the very hand-list the plan's own acceptance criterion (`plan:52`: "no hand field-list can silently drop a field") forbids. Direct self-contradiction.

**dod-audit ("compose-sub-registries is correct because a flat registry can't express the nested structure") = REFUTED as a FALSE DICHOTOMY.** A flat registry can't express the NESTED parts — true — but that does not mean NO flat registry; the scalar block still needs one. **Correct design = the HYBRID:** `compose(flat FOREACH_NODE_PERSIST_FIELD [the 24 scalars] + regime_state + pnl_feeder + confidence delegates)`. That is exactly D-283 item(2) (FOREACH_NODE_PERSIST_FIELD) PLUS delegation, and D-287 leaves it standing. Plan Phase-C must be rewritten to the hybrid BEFORE coding (re-cascade signal, arming §4).

---

## T2 — SoA pivot or AoS struct-grow? (dod F1: H10 guard vacuous) → **CONFIRMED** (struct-grow; H10 row vacuous)

**(a) No AVX kernel over Position/Portfolio exists or is wired.** Whole-tree AVX sites = `ML_Headers/RidgeBlender.hpp` + `ML_Headers/BanditLearning.hpp` + the `Version.hpp` build-flag manifest string ONLY. Zero SIMD intrinsic co-located with position/portfolio. The sole positions[] reader is `PositionExitGate` (`Portfolio.hpp:478`) — a **scalar** `__builtin_ctz` while-loop, and it is the LEGACY single_core exit gate (sharded exits read `ExecutionCore.live_tp` replica; per-field table §1). `Portfolio.positions[]` stays `Position<F> positions[16]` = **AoS** (`Portfolio.hpp:155`); Phase-B grows `Position` 128→192B by appending FOREACH_POSITION_FIELD rows — a struct-GROW, not a struct-of-arrays pivot. Plan's own acceptance line (`plan:50`) admits: *"the SoA relayout is hot-path-INERT — the gate reads ExecutionCore<F>, never Portfolio.positions[]."*

**(b) No downstream spine forces a SoA pivot.** E.1.3 OUTBOUND (`E.1.3:68`) reads `owner_node_id` on Position + the `alignas(64)` NodeState/ClusterState clusters — cache-line clustering (H6), NOT struct-of-arrays over positions[]. No E.1.3/4/5 subplan reads per-field position arrays.

**(c) Neither gate-4 nor ±USE_NATIVE_128 exercises a Position AVX kernel.** `tools/h10_kernel_harness.cpp` builds ONLY `RidgeBlender_BuildCorr<64>` (`:32`). `USE_NATIVE_128` is **absorbed/inert** — no live `#ifdef USE_NATIVE_128` math-path in `FixedPoint/` or `CoreFrameworks/`; `FixedPointN.hpp:1246-1249` "include block REMOVED" + `CMakeLists.txt:221/233` "USE_NATIVE_128 absorbed; one FP path only." So ±USE_NATIVE_128 flips only a manifest STRING, not the FP codepath — a near-vacuous determinism AXIS too (secondary).

**Verdict:** E.1.2 is **struct-grow-only**. Strike the *"first real SoA AVX kernel with bytewise-identical scalar fallback"* acceptance criterion + the §4a H10 guard-row as VACUOUS (Class-51); re-home D-55 SoA + its H10 consumer to .E.6/.E.7. The determinism gate SHOULD reduce to a plain `Save→Load` byte-compare (still meaningful) and drop the ±USE_NATIVE_128 dimension or replace it with a real perturbation.

---

## T3 — Position_Reset stale-reserved-bytes capital bug (blindspot 1) → **REFINED** (mechanism real + forward-valid; "current capital bug" over-claimed)

**Code-true parts:** `Position_Reset` (`Portfolio.hpp:221-231`) is a **9-field HAND-LIST** (the exact current PERSIST set). `Portfolio_OpenSlot` (`:358-383`) + `Portfolio_AddPositionWithExits` (`:268-284`) write fields individually with **NO Reset call**. `Portfolio_RemovePosition` (`:299`) only clears the bit ("data stays in slot"). So on live slot REUSE, a field NOT written by OpenSlot retains the previous occupant's bytes. The live serializer `:169` blob-dumps `sizeof(Position<F>)` → a stale field IS persisted; and a byte-identical Save→Load round-trip **cannot** catch a stale-but-consistent value → the golden-master is genuinely BLIND to it. All confirmed.

**Over-claim:** `peak`/`owner_node_id` **do not exist at HEAD** — TODAY OpenSlot writes all 9 current PERSIST fields, so there is NO live capital bug and NO current non-determinism. This is a **forward risk** that Phase-B introduces. Phase-C's field-by-field serializer does NOT fix it either (it persists the stale VALUE regardless — the fix belongs at the WRITE site). The replay path is safe (`Portfolio_FromEventLog:715` calls `Portfolio_Init`→Reset on a fresh FoldResult, then OpenSlot per fill — fresh struct, registry-init defaults; no bypass).

**Plan is not blind but under-hardened:** Phase-B (`plan:79`) already says *"zero-init every new field at every OpenSlot/Add/bypass site"* — but that is itself the A28/TD-182 **subset-zeroing hand-list** the Reset SSoT comment (`:216-220`) says it closed. **The blindspot's structural fix is SOUND and strictly better:** generate `Position_Reset` from a `FOREACH_POSITION_FIELD` walk (the registry already has the `init` column) + route `OpenSlot`/`AddPositionWithExits` through it (Reset-then-overwrite). Auto-flows to every future row; closes the class permanently; trivial latency (per-fill, ~192B). ADD to Phase-B. Also ADD a golden-master fixture that exercises open→close→**reopen-same-slot**→persist (the round-trip blindness gap).

---

## Net for the plan
- **T1 (CONFIRMED):** rewrite Phase-C to the HYBRID `compose(flat FOREACH_NODE_PERSIST_FIELD + 3 delegates)` — honors D-283 item(2), un-drops the 9 Money + 3 doubles, satisfies the plan's own acceptance criterion. Ship-blocking as worded.
- **T2 (CONFIRMED):** strike the SoA/H10 acceptance criterion + §4a H10 guard-row (vacuous); re-home SoA→.E.6/.E.7; fix the ±USE_NATIVE_128 determinism axis.
- **T3 (REFINED):** not a live bug; adopt the registry-driven-Reset structural fix in Phase-B + a reopen-same-slot golden fixture. Downgrade severity from "capital bug" to "forward hardening."

No auto-proceed — consult Caramel.
