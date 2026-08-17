---
type: agent-report
agent_class: a-class
date: 2026-08-17
engine_head: a160123
directive: "REFUTE the orchestrator's per-key-bit recommendation for the stamp emit gate"
verdict: REFUTED
status: verbatim-at-receipt
---

> Saved VERBATIM at receipt. Orchestrator wrote the file; the agent was read-only.
> Orchestrator verification + the resolved disagreement with the sister a-class are in
> `README.md`, NOT inline — the report is unedited.

---

## VERDICT: **REFUTED**

Plus a **materially-wrong-shape flag**: the design handed to me is neither Tier 1 nor Tier 2 of the operator's already-framed fork, and it is the fourth member of a bit-scoped family that `MASTER.md` UPDATE 30 already refuted. Roots covered: `CoreFrameworks/ Strategies/ ML_Headers/ MemHeaders/ DataStream/ FixedPoint/ Backtest/ GUI/ tests/ tools/ *.cpp *.hpp` + `models/`.

---

### 1. H21-safety claim — TRUE on the letter, but the conclusion drawn from it is FALSE

I verified the tombstone claim independently rather than reading it. It holds:

- `has_flags` exists at exactly three sites: `/home/caramel/code/FoxML_Trader_v2/ML_Headers/ModelInference.hpp:392` (ModelHandle), `:1452` (ModelStampResult), `:2068` (StampInferenceCfgInputs).
- `./tools/gen_code_map.sh --composition ModelHandle` → **0 transitive containers**. The 4 direct containers (`MLStrategyState`, `NodeModelZoo`, `EnsembleModelZoo`, `PortfolioController`) carry no raw-byte persist; `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/ShardedSnapshotPersist.hpp:160-191` writes explicit scalars, never a struct blob.
- `rg has_flags GUI/ logging/ Backtest/ DataStream/ CoreFrameworks/ foxml_suite.cpp main.cpp` → **zero hits**. Never rendered, never logged.
- `MASK_<stampname>` consumers outside the registry → **tests only**.
- All 16 `*.stamp` artifacts under `/home/caramel/code/FoxML_Trader_v2/models/` are text `key=value`; no bit word.

So renumbering is not a Knight-Capital reuse. **Conceded.**

**But the safety inference is refuted by a fact the claim never checks.** The H21 guard is *vacuously green on this exact surface right now*:

```
$ grep -c "stamp-key" tools/identifier_ledger.txt      → 0
$ python3 tools/check_identifier_retirement.py | grep -c "ADD (ok"  → 46
[identifier-retirement] GREEN — 94 persisted/wire identifiers match the ledger; no renumber/reuse/drop.
```

`/home/caramel/code/FoxML_Trader_v2/tools/check_identifier_retirement.py:157-158` added the `stamp-key` SOURCES row today (D-425 #10), but the blessed `--update` was never run. With zero recorded rows, a **dropped or reordered wire key cannot classify as REMOVED/RENUMBERED** — it just fails to ADD. `MASTER.md` UPDATE 30 names this enrollment "task #10 FIRST … a PREREQUISITE, not a follow-up," precisely so a large deletion on this signed body doesn't run under a meaningless green. The code half landed; the data half did not. This is the same Class-51 shape the a-class already refuted once on this surface, surviving for a different reason.

Second point the claim inverts: `check_identifier_retirement.py:152-156` deliberately does **not** enroll bit positions. "H21-safe" and "completely unguarded" are the same sentence here.

### 2. Bit budget — holds numerically; 64 is not the binding constraint

Measured by compile-probe (not recalled):

| | measured |
|---|---|
| `tt::STAMP_BIT_COUNT` | **23** |
| `FOREACH_STAMP_BOUND_MODEL_CONST_COUNT` | **46** |
| `FOREACH_STAMP_BOUND_MODEL_CONST_GROUP_COUNT` | **5** (enum has **6**) |

The registry's own comment at `/home/caramel/code/FoxML_Trader_v2/ML_Headers/StampBoundModelConstRegistry.hpp:532-534` — *"groups first (6 bits), then standalones (7 bits) = 13 total. uint64_t has 51 bits headroom"* — is wrong on all three numbers. Its claim on `:534-535` that a "build-time test asserts STAMP_BIT_COUNT matches GROUP_COUNT + standalone count" is also false: the actual test is `STAMP_BIT_COUNT >= 13` at `/home/caramel/code/FoxML_Trader_v2/tests/controller_test.cpp:24012-24013`, satisfiable by 13, 23, 46, or 64.

46 ≤ 64. But:

- The real ceiling is a **consumer layout lock**: `ModelInference.hpp:502-511` pins `sizeof(ModelHandle<64>) % 64 == 0` *and* `offsetof(ModelHandle<64>, has_flags) < 64`. Widening past `uint64_t` lands in the HOT cache line.
- Going 23 → 46 spends 23 of 41 free bits and buys **nothing on the wire**, leaving 18 — while the registry's advertised contract is "new field = 1 row."
- `enum StampHasFlagBit` is **hand-written**, and `tests/controller_test.cpp:23920-23924` already documents it as the SSoT over the registry: *"no row in the GROUPS list, so the real group-bit count is 6. The registry is not the SSoT — `enum StampHasFlagBit` is."* Its two declaration mirrors are already drifted (`_GROUPS` missing `environment_meta`; `_STANDALONE` carrying 7 of 17 standalones). The recommendation **doubles that hand-written mirror from 23 to 46** entries. That grows a Class-18 mirror on a registry that has already demonstrated it cannot keep one in sync.

### 3. "Producers set bit and value adjacently" — FALSE. The counterexample is a live instance of the defect being fixed, on a standalone row that already has its own bit

`/home/caramel/code/FoxML_Trader_v2/ML_Headers/StampHelper.hpp:249-251`:

```c++
if (BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_BANDIT_ENABLED)) {
    STAMP_SET(inf, inference_cfg_bandit_blend_ratio);
}
```

No value assignment. `rg "inference_cfg_bandit_blend_ratio\s*="` across all named roots: the **only** writers are `tests/controller_test.cpp:15596` and `:24105` (fixtures), plus the parse→handle copy at `ML_Headers/NodeModelZoo.hpp:471`. The emit-side value's only producers are test fixtures — Class 58's highest-yield signature, the one `DOCS/SUBAGENT_ARMING.md` §3.1 exists to make findable.

Cause is byte-for-byte the `fees` cause: `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/CfgFieldRegistry.hpp:669` carries `bandit_blend_ratio` with `STAMP_BOUND_CFG_DERIVED` and states *"was standalone inference_cfg_bandit_blend_ratio at StampBoundModelConstRegistry.hpp:296; framework walker emits unprefixed."* The `.B.3` migration took the producer; the bit-set stayed.

Effect: `StampInferenceCfgInputs inf = {}` (`StampHelper.hpp:185`) zero-inits → PRE_CFG row 1 (`StampBoundModelConstRegistry.hpp:301-302`) gates on `STAMP_EMIT_CHECK_HAS__` = its own bit = set → emits `inference_cfg_bandit_blend_ratio=0` into the HMAC body (`ModelInference.hpp:2258-2264`) **alongside** the true `bandit_blend_ratio=<real>` from `populate_stamp_cfg_from_derived` (`:2280-2284`) → propagates to the handle at `NodeModelZoo.hpp:469-472` → displayed at `/home/caramel/code/FoxML_Trader_v2/Backtest/BacktestPanels.hpp:2309-2311`. Latent only because all 16 artifacts predate it and none enabled bandit — the identical "fires when the operator turns the feature on" property that hid `fees`.

Two more, in the other direction:
- `StampBoundModelConstRegistry.hpp:379-381` — `feature_mask`'s `get_value` names `inf->feature_mask_train`, a member with **no declaration anywhere** (confirmed by grep; `StampHelper.hpp:296` says so in-line).
- **16 of 46 rows have no emit producer at all**: `environment_meta` (5), `scaler_fit_data_hash`, `removal_reasons_csv`, and the 9 `inference_cfg` rows. Inert only because nothing sets their bit. The first ship that sets one bit for one row emits the rest as zeros.

### 4. Unrepresentable? No — a mitigation, already empirically defeated

Reintroduction sequence, requiring zero new bits, compiling clean **under per-row bits**:

1. A migration moves wire key `K` from model-const to the cfg-derived cohort (exactly `.B.3`, done twice: `fee_rate_*`, `bandit_blend_ratio`).
2. It deletes `inf.K = <value>;` because the value now comes from cfg at emit time, and leaves the *separate* statement `STAMP_SET(inf, K);` — typically inside a feature-flag `if`, i.e. a different line at different indentation. `StampHelper.hpp:249-251` **is literally that shape**.
3. Compiles: bit exists, field exists, `= {}` zero-inits.
4. `K=0` lands in the signed body next to the true `K=<real>`.

Nothing in per-row bits makes step 2 fail. Unrepresentability requires bit-set and value-write to be **one expression**; two statements are two statements. And this is already settled: `MASTER.md` UPDATE 30 — *"All three failed the same way: the `fees` bit HAD a producer, so any bit-scoped check graded it green … a coverage check over an emitted format must key on the WIRE KEY, not the group bit."* The recommendation is a bit-scoped **construction** with the same blind spot as the three refuted bit-scoped **checks**; `inference_cfg_bandit_blend_ratio` is the empirical proof rather than the argument.

### 5. Simpler / safer, in the order I'd take them

**(a) Do the already-decided Tier 2.** Handoff line 61: *"Tier 2 = gate each row directly against `args`/`cfg` at emit time, no `inf`, no group."* The sibling at `/home/caramel/code/FoxML_Trader_v2/MemHeaders/CfgGateRegistry.hpp:425-440` already works this way and has **no has-bit at all** — `populate_stamp_cfg_from_derived` reads `cfg.name` and gates via `cfg_gate::lookup_populate(_idx, …)`. A row cannot emit a value it does not read. This removes a strict superset of what the recommendation removes (bitmap on emit + `group` + the 7-macro dispatcher family + `emit_when` + `get_value`) and is the only option that closes the class rather than narrowing it.

**(b) If Tier 2 must be staged, do this one line of leverage first — it is smaller than the 46-bit change and strictly stronger at the stated goal.** Replace `STAMP_SET(s, name)` (`StampBoundModelConstRegistry.hpp:638`) with a value-carrying `STAMP_PUT(s, name, value)` that sets the bit and assigns in **one expression**, and delete `STAMP_SET`. ~17 sites in `StampHelper.hpp` + 13 in `NodeModelZoo.hpp`. No bit renumbering, no wire reasoning, no ledger dependency. It delivers exactly the property the recommendation claims but does not have: deleting the value *forces* deleting the bit-set. It would have caught `fees`, and it red-lights `inference_cfg_bandit_blend_ratio` at compile time today.

**(c) Run `python3 tools/check_identifier_retirement.py --update` at the operator TTY before either.** Right now the guard is green over an empty row-set.

**(d) Not available cheaply:** a compile-time "every row has a producer" assertion. The producer is a free-form statement in a caller body, not a registry column; the registry-column form is the bit-keyed producer sidecar already refuted on H18.

**(e) Do NOT reopen** the generic gate-reachability check, the `STAMP_EMIT_PRODUCER_<G>` marker, or the bit-keyed sidecar — settled, `MASTER.md` UPDATE 30.

### 6. Cascade the recommendation misses

1. **`group` is a cross-registry semantic predicate, not just an emit gate.** `MemHeaders/CfgGateRegistry.hpp:811-820` hardcodes `STAMP_HAS((handle), inference_cfg)` into `DRIFT_CHECK_FROM_DERIVED`, feeding `cfg_gate::lookup_drift` (`:186-208`) where **every** branch returns `stamp_has_inference_cfg && (expr)`. Dissolve `MASK_inference_cfg` and the entire cfg-derived drift cohort loses its gate symbol. Unmentioned.
2. **12 drift rows in a second registry gate on group bits.** `/home/caramel/code/FoxML_Trader_v2/ML_Headers/CfgDriftCheckRegistry.hpp:224/:228/:232/:236/:240` (5 xgb rows on `xgb_hyperparams`) and `:257/:261/:266/:332` (4 rows on `inference_cfg`, **two of them `REFUSE_STRICT`**). Per-row bits force a per-row semantic decision on a REFUSE-capable path. Note `:273`: several rows already migrated **off** the stamp group bit onto `COHORT_GATE_*` cfg predicates — the settled direction of travel is toward the cfg source, i.e. toward Tier 2, not toward more bits.
3. **Consumers:** 13 handle-propagation sites at `NodeModelZoo.hpp:376-478`, plus `:509`, `:2182`, `:2276`, `:2423`; 3 GUI sites `BacktestPanels.hpp:2270/:2294/:2321`; 1 at `ML_Headers/FeatureRegistryOverlay.hpp:172`.
4. **The "~44 declarations in controller_test.cpp" figure is RIGHT but MISAPPLIED.** `rg -c "StampInferenceCfgInputs\s+\w+" tests/controller_test.cpp` = **44** — that is the **Tier-2** number, because Tier 2 removes `inf` from the emit path. Under *this* recommendation `inf` survives, so 44 understates it: the real edit surface is **75 `STAMP_SET` + 83 `STAMP_HAS` + 13 `MASK_*`** in that one file, of which **55** reference a group name. Live tuple-arity declarations are **8** (`ModelInference.hpp:425/1456/1731/1757/2072/2258/2291` + `controller_test.cpp:23966`) — dropping two columns changes arity at all 8.
5. **H15.** `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/MetaRegistry.hpp:94-95` enroll `_GROUPS` and `_STANDALONE`; deletion needs the tombstone shape already modelled at `:82`, gated by `tools/check_meta_registry.py`.
6. **Parse-side behaviour delta the "byte-identical" claim doesn't cover.** Emit stays byte-identical (verified: every group whose bit is set today has *all* values written — scaler 2/2 `:392,:395`; xgb 8/8 `:335-346`; grid_member 2/2 `:386-387`; label_params 3/3 `:376-378`; `environment_meta` and `inference_cfg` bits are never set). But on parse, **any one** group key currently lights the whole group bit; per-row bits change which drift rows arm on a partial legacy stamp.
7. **CONCEDED: `emit_when` and `get_value` really are dead.** The only body consuming them is `STAMP_MODEL_CONST_AUTOPOPULATE_ONE` (`:766-775`), whose caller macro is a `static_assert(false)` quarantine (`:691-696`) with zero call sites. Proof they never compile: `feature_mask`'s `get_value` names a nonexistent member. Removing them is correct — Tier 2 removes them too.

---

### THE STRONGEST CASE AGAINST

The recommendation's load-bearing claim — that per-row bits make bit-without-value unrepresentable "the same construction that already protects the 17 standalone rows" — is refuted by a live instance sitting in the standalone set it cites as proof: `StampHelper.hpp:249-251` sets `inference_cfg_bandit_blend_ratio`'s **own** bit and never writes its value, so the next stamp emitted with bandit enabled will print `inference_cfg_bandit_blend_ratio=0` into an HMAC-signed identity document beside the true rate, exactly as `fees` did, with per-row bits already in force. Because bit-set and value-write are separate statements in C++, no bit-scoped construction can couple them — which is the same conclusion `MASTER.md` UPDATE 30 already reached for the three refuted bit-scoped *checks*, and the reason the operator's own Tier 2 gates against `args`/`cfg` with no bit at all. Meanwhile the change would spend 23 free bits, double a hand-written 23-entry enum that the tests already document as drifted from its registry, force a semantic rewrite of two `REFUSE_STRICT` drift gates and the cross-registry `stamp_has_inference_cfg` predicate, and land on a signed wire surface whose H21 guard currently reports GREEN over an empty ledger.

### WHAT I WOULD RECOMMEND INSTEAD

1. **Bless the ledger now** — `python3 tools/check_identifier_retirement.py --update` at the operator TTY (46 stamp-key rows). Nothing else on this surface should move first; `MASTER.md` says so and the measurement confirms the prerequisite is only half done.
2. **Fix `inference_cfg_bandit_blend_ratio` as a Tier-0 sibling of the `fees` deletion** — it is the same defect, still live, and it invalidates the "class closed" claim the same way `a160123` had to. Its retired name goes into `RETIRED_NAMES` beside the two `fee_rate` keys.
3. **Then Tier 2** (dissolve the emit-side bitmap; gate on the value source, mirroring `CfgGateRegistry.hpp:425-440`), which subsumes everything the audited recommendation wanted. If it must be staged, land `STAMP_PUT` first — smaller than the 46-bit change, no wire risk, and it is the construction that actually makes the defect unrepresentable.
4. **Do not** adopt "46 per-row bits" as a standalone ship. It is a mitigation presented as a structural close, on a surface where that exact overclaim has now shipped twice.
