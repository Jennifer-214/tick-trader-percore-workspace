---
type: audit-report
skill: D-93 design audit (LAYER 2 — no subagents, no edits)
date: 2026-06-09
cluster: S-17 flag-loud overflow mechanism + S-4/R3-B epoch-versioning design
target_plan: plans/v5.15-live-readiness/subplans/2026-05-30-v5.15.5.F.4d.1.E-money-numeric-core-foundation.md (v0.4)
head: 0e48150 (v5.15.5.F.4d.1.E.0.8) — verified
inputs_read: blindspot-scan-2026-06-09 (items 1-2) · verification-pass V4/V5/V6 · dod-audit F1 · synthesis S-4/S-17 · D-93/D-144/D-147/D-173 decision-log bodies
verdict: 2× DESIGN-OK-with-addition · 5× DESIGN-GAP · 1× DESIGN-WRONG (Q7 — "hard-refuse" rests on a strict-gated mechanism)
---

# D-93 design audit — money overflow flag-loud (S-17) + epoch guards (S-4/R3-B)

All code claims verified at HEAD 0e48150. New findings vs the prior gate evidence are marked **NEW**.

## Part 1 — S-17 flag-loud overflow

### Q1 — Where does the sticky flag LIVE? — **DESIGN-GAP** (home unspecified; the named sister is not a viable home)

The plan/S-17 pins shape only: "sticky flag word (`FailureModeRegistry` `__atomic_fetch_or` sister), boundary-checked per cycle." Verified constraints at HEAD:

- **`PerCoreSnap.failure_flags` is NOT a state home.** It is the display-snapshot mirror: `uint16_t` on PerCoreSnap, **reset every publish** (`ShardedSnapshot.hpp:612`) and repopulated from engine-side SSoT (e.g. `zoo->*.drift_flags_at_load` OR'd in at :677-680). A sticky money flag stored only there is wiped per cycle. FailureModeRegistry is the correct **display mirror** (1 BIT_FLAG row; 10/16 bits used, `static_assert` cap at `FailureModeRegistry.hpp:286`), never the primary store.
- **Money ops are pure template fns** (no engine/ctx pointer) called from drainer (`OrderManager.hpp:1160-1210`), per-core slow threads (`ControllerEventLoop.hpp:1923/:1967`), boot replay (`Portfolio_FromEventLog`), hot rare-entry branch (`ExecutionCore.hpp:543/549/570`), backtest, tests.
- **Process-global atomic** (the naive read of "__atomic_fetch_or sister"): H3-clean and branchless, but (i) **cross-instance contamination** — controller_test runs many engines in one process; an in-process backtest/GUI run would poison a live engine's word; sticky+global+never-cleared = one forced-overflow test or backtest poisons every later boundary check; (ii) per-op lock-RMW on the line. REJECT as primary store.
- **Per-core failure_flags as primary**: unreachable from pure ops; drainer ops span cores. REJECT (mirror only).

**Picked shape (a/b/c all satisfied):**

1. **Op site:** `inline constinit thread_local uint64_t tt::g_money_of_acc` — decimal ops do an **unconditional plain `|=`** of the already-computed `of_m` bit (the predicate exists branchlessly in every body: `fp2_mul` `of_m` at `FixedPointN.hpp:1300-1303`, `fp2_addsat` :1316, `fp2_sub` :1324 — decimal twins inherit it). One `%fs`-relative OR: no branch, no RMW, no cross-thread traffic, no TLS-guard branch (constinit zero-init). `thread_local` precedent exists (`BanditLearning.hpp:661`, `CoreModelZoo.hpp:2565`).
2. **Drain:** each money-bearing thread drains (read+clear) its TLS word at its own cycle tail — drainer tail, per-core slow-cycle tail, boot-replay tail, backtest step tail — `fetch_or(relaxed)` into ONE engine-owned word: `alignas(64) std::atomic<uint64_t> money_overflow_flags` on **OMSState** (the money-authoritative struct; sister cluster `flatten_pending`/`recovery_until_us` `OrderManager.hpp:569/:576`). TLS cleared at engine init (cross-run hygiene) + a test-harness reset helper.
3. **Hot thread (required sub-decision):** the 3 rare-entry hot muls become decimal money muls at Ship B (D-170) but the hot thread has NO drain hook — adding one touches the per-tick path. **Recommend: carry the of-bit on the `TradeEvent`** (the event is already pushed in that same rare branch — zero steady-state cost; drainer ORs it at consume; ring-POD layout change rides the epoch). Fallback: prove `price×pct` operand bounds (≪2⁶³) and document a saturate-only exemption — but enumerate-the-set (D-77) favors the bit-carry.
4. **Replay determinism:** flag-set is a pure function of replayed values → replay MUST run the identical flag path (same TLS OR; boot-replay tail drains into the same word). Replay==production then holds INCLUDING flag state; replay flags are not corruption, they are the determinism property. **Required invariant in the plan body:** the sticky word NEVER feeds back into math — consumed only by the boundary action — else goldens become flag-coupled. Add a forced-overflow row to the C2 replay==production differential.

### Q2 — Which ops carry the guard; is the radix gate designed? — **DESIGN-OK + one required addition**

The gate shape is right and partially landed: disjoint `is_fp_decimal_v` exists (`FixedPointN.hpp:100-102`); D-147 pins binary `<2,64>` = silent saturate (R2 rests on it); the radix fork is `if constexpr (RADIX==10)` inside shared bodies. Since the generic `FixedPoint` is **declaration-only** at HEAD (:82) every decimal body is NEW — the OR is design-in, not retrofit.

**Required addition:** the S-16 per-op radix-disposition table gains a **flag-disposition column**:

| Op | Overflow predicate | Flags? |
|---|---|---|
| Mul (#2 reduce) | #3 guard `\|op\|<2⁶³` + product `of_m` | YES |
| Div (#7) | zero-divisor + quotient-range | YES |
| Add/Sub | decimal twins of `fp2_addsat`/`fp2_sub` `of_m` | YES |
| Negate/Abs | `INT128_MIN` (D-147 saturate) | YES (decimal only) |
| Casts: money→binary ingress | money max ~1.7e30 > binary 2⁶³ cap | YES |
| Casts: binary→money egress (D-170 gate-build) | widening — no overflow | no |
| Quantize (#6) | inherits mul/floor | no new predicate |
| FromString (#5) | malformed/range | **NO — stays `(value, ok)` surfaced at parse** (distinct mechanism; do not merge into the sticky word) |
| #4 rounding `(q,r)` | none (`0≤r<SCALE`) | no |

### Q3 — Boundary check: where + what action? — **DESIGN-GAP → one designed answer**

dod-F1 left three options. One is wrong: **kill-switch-eval is the producer thread** (`Async.hpp:443`) with a documented torn-read race + "TODO: move to drainer" (:432-443) — do not co-locate a money-integrity check there.

**Designed answer:** consumer = **drainer cycle tail** (end of `OrderManager_Tick` — the money-authoritative thread; all other threads only drain INTO the word; single consumer). On nonzero, `__builtin_expect`-rare branch (H20 decision-matrix-sanctioned):

- set sticky **`MASK_OMS_STATE_MONEY_OVERFLOW_TRIPPED`** — 1-row add to `OmsStateFlagRegistry.hpp` (canonical sister: `MASK_OMS_STATE_KILL_SWITCH_TRIPPED`; uint8_t bitmap near capacity — the registry's own overflow static_assert governs widening);
- **`EventLoop_ClearAllPermissions`** (`ControllerEventLoop.hpp:3196`) — this IS D-173's degrade, verbatim "halt NEW entries while exits keep managing": `permission` only gates entries (`can_enter = !active & permission & bg_fires`, `ExecutionCore.hpp:25`); SG/TimeExit/TrailingSL/fill-processing unaffected. Same mechanism as D-173's BNB degrade → ONE shared trip helper, two callers;
- mirror via a NEW FailureModeRegistry BIT_FLAG row (SEV_RED) at snapshot publish — display only.

NOT the kill-switch tier: no flatten, no `ks_trips_total` mutation — distinct sticky bit = distinct operator-visible WHY. Re-grant is operator-explicit only (Unpause-sister); never auto. **Boot tier:** boot-replay drain lands BEFORE first permission grant → flag at boot ⇒ permission never granted + RED row (replay-deterministic live-equivalence).

### Q4 — Forced-overflow probe — **DESIGN-GAP** (only "acceptance row" words exist)

- **Unit:** two `FromString` values ≥ ~9.3e10 (so `v=value·10⁸ ≥ 2⁶³`) → decimal Mul → assert saturate==MONEY_MAX **and** TLS word nonzero; drain → OMS word bit set. Negative control: in-range op leaves word zero. ubsan-lane clean.
- **Integration (sharded harness):** inject the forced overflow on the drainer path → assert (i) sticky OMS bit, (ii) every core `permission==0`, (iii) an OPEN position still exits (TimeExit/SG fires, fill drains, balance folds), (iv) NO new submit after trip, (v) PerCoreSnap mirror set, (vi) replay twin reproduces the identical flag state (the new C2 row), (vii) hot-side: a crafted entry event carrying the of-bit is OR'd by the drainer (if the TradeEvent-bit option is taken).

## Part 2 — S-4/R3-B epoch guards

### Q5 — "Same commit as the first money flip": mechanical enforcement — **DESIGN-GAP** (as written it is a review item, not a guard)

"Bump in the SAME COMMIT" + a hand-bumped `MONEY_ENCODING_EPOCH` constant both just relocate the forgettable step. The S-4 lesson (V4b verified: the D-144 trigger keys on `sizeof(FPN)`, which does NOT change; floor test `>=13/9/6` passes un-bumped, `controller_test.cpp:24448-24453` confirmed) demands the **type flip itself** be the trigger:

1. **Per-surface trait-keyed static_asserts, co-located with each persisted struct** — fire exactly when THAT surface's money field flips, sizeof-independent:
   - `static_assert(!tt::is_fp_decimal_v<decltype(OrderEvent<64>::price)> || OEL_FORMAT_VERSION >= 2, "money encoding flipped — bump event-log epoch (S-4)");`
   - same shape keyed on a persisted ctx money field ⇒ `SHARDED_SNAPSHOT_VERSION ≥ 10`, `CONTROLLER_SNAPSHOT_VERSION ≥ 14`, `PORTFOLIO_SNAPSHOT_VERSION ≥ 7`;
   - keyed on a StampT money field ⇒ `STAMP_FORMAT_VERSION_CURRENT ≥ 3`.
2. **Floor auto-raise:** derive `constexpr int MONEY_ENCODING_EPOCH = tt::is_fp_decimal_v<decltype(<canonical persisted money field>)> ? 1 : 0;` — the controller_test floor becomes `>= 13 + MONEY_ENCODING_EPOCH` (etc.). The floor rises mechanically the moment the canonical field flips; nothing to remember.
3. H21: tombstone comments on 13/9/6 + `tools/check_identifier_retirement.py --update` ledger rows (tool verified present; pre-commit Check H).

Forgetting any bump = RED BUILD at the flip commit. The discipline-text re-key (sizeof → value-encoding) stays, as documentation of the why.

### Q6 — OMSEL01→OMSEL02 loader reject — **DESIGN-GAP** (magic bump alone leaves two live defects)

Verified loader: magic memcmp at `OrderEventLog.hpp:498-501` → `WARN bad magic` + return -1.

- **(a) NEW — reject-then-append seam.** The only caller swallows -1 (`if (_loaded > 0)`, `OmsFieldRegistry.hpp:735-736`) and proceeds to `OrderEventLog_InitWithFile`, which opens `"ab"` and writes a header **only if the file is new** (:413-431) → post-epoch decimal events get APPENDED to the rejected OMSEL01-headed file. Mixed-epoch file under the OLD magic ⇒ next boot rejects the WHOLE file = silent loss of post-epoch events. **Required:** on epoch-reject, ROTATE (`rename → <path>.pre-epoch.<ts>`, evidence preserved) then create a fresh OMSEL02 file; never append to a rejected file; header-write condition becomes "new OR rotated".
- **(b) Reject tier + message.** Current `fprintf WARN + continue` is too quiet for a money epoch. Message must name the epoch + instruction ("pre-decimal event log (OMSEL01); positions should have been flattened pre-deploy (B-ζ); archived to <path>; replay skipped"). **Required decision:** LIVE mode + non-empty pre-epoch log ⇒ refuse boot (operator archives explicitly); paper/backtest ⇒ rotate+warn+continue.
- **(c) Mechanism choice (the S-4 "or claim a reserved word" fork): magic bump WINS** — it rejects in BOTH directions (an old binary memcmp-rejects a new file too). A reserved-word version is invisible to old loaders → an un-updated binary loads a new-epoch file misscaled (the Knight direction H21 exists for). Do both: bump magic to `"OMSEL02"` AND populate a `reserved[]` version word for future SOFT bumps. H21 tombstone: comment at the magic constant + `identifier_ledger.txt` row; `"OMSEL01"` never reused.

### Q7 — STAMP_FORMAT_VERSION 2→3 floor — **DESIGN-WRONG as specified** (the "hard-refuse" rests on a strict-gated mechanism)

Verified: `CURRENT=2 / MAX=2` (`ModelInference.hpp:141-142`); only `> MAX` rejected (:1544-1551) by setting `r.valid=0`. But the consumer honors `valid<=0` **only under `held_out_gate_strict==1`**; under strict=0 it logs "loading anyway" and LOADS (`CoreModelZoo.hpp:244-254`). A v2 (binary-money) stamp under strict=0 would load into the decimal engine — drift detection can't save it (V5's dual-type fall-through is on the same path). The plan's "loader hard-refuses pre-epoch stamps" is therefore not delivered by the existing reject class.

**Required:** the floor must be **UNCONDITIONAL** — a hard-invalid class that bypasses the strict branch (e.g. `sr.hard_invalid` honored regardless of `held_out_gate_strict`, or the floor check at the load site before the strict fork). Add `MIN_SUPPORTED_STAMP_FORMAT_VERSION = 3` beside CURRENT/MAX; bump CURRENT=3, MAX=3 (emit at :1881 follows CURRENT automatically); reason string carries the retrain instruction (M4 P5 checklist regenerates stamps at the epoch anyway, so the floor costs operators nothing). **Sub-decision (H21):** at floor=3 the `[1,2]` `FOREACH_LEGACY_PREFIXED_KEY` back-compat dispatch becomes dead code — delete the dead dispatch, tombstone the legacy key rows (dead-code-and-identifier-retirement).

### Q8 — Warm-restart epoch test (all three artifacts) — **DESIGN-GAP** (row exists; no shape)

**Recommended shape: synthesize OLD HEADERS at test time** — not checked-in binary goldens, not a version-bump-then-load-old-goldens dance:

- (a) snapshot file: valid magic + `version=13` → load → assert rejected + reason names the epoch;
- (b) event-log file: header magic `"OMSEL01"` → `LoadFromDisk` → assert -1 AND the file is ROTATED, not appended-to (regression for Q6a);
- (c) stamp text: `stamp_format_version=2` → verify → assert refused under **strict=1 AND strict=0** (the strict=0 leg is the load-bearing Q7 regression);
- POSITIVE control in the same test: current-version artifacts (14/10/7 + OMSEL02 + v3) load GREEN — so the test cannot pass by rejecting everything;
- one composed warm-restart boot: all three pre-epoch artifacts present → boot lands FLAT + loud, per the Q6b LIVE/paper tier.

Rationale: every reject fires at header parse, so pre-epoch BODY fidelity is irrelevant; synthesized headers don't rot and avoid keeping an old-format EMITTER alive (a frozen old-format generator is the reimplemented-oracle drift risk golden-master discipline warns about).

## Punch list — minimal design additions before code

1. **S-17 mechanism ¶** (plan body): TLS accumulate → per-thread cycle-tail drain → `OMSState::money_overflow_flags` (alignas-64 atomic) → drainer-tail single consumer → sticky OmsStateFlag bit + `ClearAllPermissions` (shared trip helper with D-173 degrade) + FailureModeRegistry mirror row; hot-side of-bit rides TradeEvent (or documented bounded-operand exemption); replay runs the identical flag path; invariant "flag never feeds math"; operator-explicit re-arm.
2. **S-16 table** gains the flag-disposition column (Q2 table above); FromString stays `(value, ok)`.
3. **Per-surface trait-keyed version static_asserts + derived `MONEY_ENCODING_EPOCH` floor auto-raise** — replaces "same commit" discipline with a red build (Q5).
4. **OrderEventLog epoch:** rotate-not-append on reject + loud epoch message + LIVE refuse-boot tier decision + magic bump AND version word + H21 ledger rows (Q6).
5. **Stamp floor:** unconditional hard-invalid class (strict-independent) + MIN=3/CURRENT=3/MAX=3 + legacy-key dead-code retirement (Q7).
6. **Epoch test:** synthesized-header fixtures ×3 + strict=0 stamp leg + rotation assertion + positive control + composed boot test (Q8).

Items 3-5 are silent-corruption-class on capital/persistence surfaces (D-77 heavier-default); all are plan-text + design decisions, no architecture re-open.
