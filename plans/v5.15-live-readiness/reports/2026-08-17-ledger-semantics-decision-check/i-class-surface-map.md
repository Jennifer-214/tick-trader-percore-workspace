---
type: agent-report
agent: i-class (investigative)
directive: /decision-check — stamp-key positional vs relative ledger semantics
run_date: 2026-08-17
engine_head: cddd8f6
status: VERBATIM — saved by the orchestrator at receipt; agent was read-only
---

> Saved verbatim per `feedback_save_agent_reports_verbatim`. Orchestrator verification of each
> load-bearing claim lives in this directory's README, NOT inline here.

---

# I-CLASS SURFACE MAP — `stamp-key` positional-vs-relative ordinal semantics in `check_identifier_retirement.py`

**Scope:** ONLY the value-semantics of the `stamp-key` category. Engine root `/home/caramel/code/FoxML_Trader_v2`, HEAD `cddd8f6` (branch `feat/v5.15-live-readiness`).
**Roots covered by grep:** `CoreFrameworks/ Strategies/ ML_Headers/ MemHeaders/ DataStream/ FixedPoint/ Backtest/ GUI/ tests/ tools/` (Landmine 19 honored — `.` never used).
**Mutations:** NONE. `tools/identifier_ledger.txt` was never written; `--update` was never invoked. All experiments ran against a symlink-farm scratch tree at `~/.cache/ir_exp/root` with `FOXML_REPO_ROOT` + `IDENTIFIER_LEDGER` overrides. Final `git status --porcelain` shows only the four pre-existing untracked operator files.

## 0. Tools RUN (not asserted)

| Command | Result |
|---|---|
| `python3 tools/check_identifier_retirement.py` | **rc=0** — `GREEN — 94 persisted/wire identifiers` |
| `bash tools/check_identifier_retirement_selftest.sh` | **rc=0** — all 6 teeth PASS, incl. `stamp-key non-vacuity -> 46 wire keys resolved` |
| Scratch-tree baseline (unmodified copy) | **rc=0 GREEN** — harness proven non-vacuous before any plant |
| 8 planted-mutation scenarios + 2 burned-name resurrections + 1 positive control | measured below |

Nav-infra consulted: `DOCS/TOOLS.md:94` (the tool's inventory row), `:71` (`node_persist_layout.py`, the shared parse library), `:64` (`bless.py`), `DOCS/CODE_MAP.md:942`. Methodology lens: `.claude/skills/parity-check/SKILL.md:308-317` (Section E — stamp body schema parity).

## 1. The surface map — read/write sites + call sequence

### 1.1 The producing registry — `ML_Headers/StampBoundModelConstRegistry.hpp`

| Site | What |
|---|---|
| `:344-447` | `FOREACH_STAMP_BOUND_MODEL_CONST_PRE_CFG` — **22 rows measured** |
| `:462-556` | `FOREACH_STAMP_BOUND_MODEL_CONST_POST_CFG` — **24 rows measured** |
| `:561-563` | `FOREACH_STAMP_BOUND_MODEL_CONST` = `PRE_CFG(X) POST_CFG(X)` — **this union is what the SOURCES row enrolls** |
| `:356-357` | the row under discussion — `X(inference_cfg_bandit_blend_ratio, _, INCLUDE, double, "%g", 0.0, …)` — the **first** row of PRE_CFG, hence ledger ordinal 0 |
| `:449-456` | the emit-order contract: *"the emitter walks PRE_CFG -> FOREACH_STAMP_BOUND_CFG -> POST_CFG to preserve canonical wire format byte-for-byte"* |
| `:604-640` | `enum StampHasFlagBit` — `STAMP_BIT_*` are **enum members**, never `#define`s (load-bearing, see F1) |

### 1.2 The call sequence, emit side — `ML_Headers/ModelInference.hpp`

```
:2291-2298   #define X(...) snprintf(canonical+n, …, #name "=" fmt "\n", inf->name)
             FOREACH_STAMP_BOUND_MODEL_CONST_PRE_CFG(X)      <- ledger ordinals 0..21
:2313-2317   cfg_derived::populate_stamp_cfg_from_derived<F>(canonical+n, …)   <- NOT enrolled; dozens of keys
:2324-2331   FOREACH_STAMP_BOUND_MODEL_CONST_POST_CFG(X)     <- ledger ordinals 22..45
:2352        tt::hmac_sha256_hex(effective_secret, canonical, sig)
```

**Consequence, measured:** `STAMP_BOUND_CFG_DERIVED` appears 41x in `CfgFieldRegistry.hpp` and 31x in `CfgGateRegistry.hpp`, and those rows emit **between** ordinal 21 and ordinal 22. So a POST_CFG key's ledger ordinal is **not** its position in the signed body. The ledger ordinal is a rank within the model-const union only — an order *proxy*, never a wire position.

### 1.3 The call sequence, verify side — **the decisive fact**

`ML_Headers/ModelInference.hpp:1663-1668`:

```c
// Add this line to canonical (in original "key=val\n" form)
int wrote = snprintf(canonical + canonical_len,
                      sizeof(canonical) - canonical_len,
                      "%s=%s\n", key, val);
```

The verifier rebuilds the HMAC body **from the file's own line order**, not from the registry. Parser dispatch is `strcmp(key, #name)` chained (`:1731-1737`), i.e. key-driven and order-independent.

**Therefore: a registry reorder cannot break verification of an existing signed stamp.** What the registry order actually governs is the *re-emission* byte order — i.e. Section-E's *"the in-process stamp emitter produces identical canonical body for identical inputs"* (`parity-check/SKILL.md:315-317`). That is an **H9 byte-reproducibility** property, not an H21 identifier-reuse property. This reframes the whole decision and I flag it as the single most load-bearing finding of this map.

### 1.4 The guard — `tools/check_identifier_retirement.py`

| Site | Role |
|---|---|
| `:157-158` | the `stamp-key` SOURCES row — `{"prefix": "", "value": "positional"}` |
| `:144-156` | the enrolment comment (quoted verbatim in section 4) |
| `:226-238` | `_parse_foreach` — `val = idx` then `idx += 1` per accepted row -> **dense absolute ordinal in parse order** |
| `:161-162` | `MONOTONIC = {"version"}` — **the existing, established per-category semantics switch** |
| `:305-343` | `compare()` — the whole comparison |
| `:318-320` | REMOVED branch |
| `:329-332` | **RENUMBERED branch — the ONE branch whose meaning changes** |
| `:335-338` | VALUE-REUSE branch (reachable only when a name held its value) |
| `:278-297` | `ledger_lines()` — emits `cat|name|value`, sorted by `(value, name)` |
| `:352-386` | `retired_name_check()` — the H21 name-burn sweep; regex at `:365-366` is `^\s*#\s*define\s+NAME\b` **only** |
| `:453-479` | `--update` -> `bless.py` (TTY required, typed confirmation, non-interactive rc=2) |

Parse-order fidelity verified in the shared library: `tools/node_persist_layout.py:187-205` (`_rows` walks `finditer` order) and `:165-184` (`_expand_nested` splices a nested body **in place**). **The parse does preserve emit order.**

Invocation: `.githooks/pre-commit:425-443` (Check H, trigger-scoped to `ML_Headers/` among others) · `/readiness` Check 46 · `/post-ship-audit`.

### 1.5 Cohort siblings + blast radius

- **Ledger consumers:** the tool itself + `.githooks/pre-commit:427` (which stages-triggers on `tools/identifier_ledger.txt`). No other reader.
- **Selftest:** `tools/check_identifier_retirement_selftest.sh` — cases (4) `:90-106`, (5) `:108-119`, (6) `:121-137` are the `stamp-key` teeth.
- **Blast radius of the change itself: ONE python file + ONE shell file.** No C++ touched, no ledger reshape (measured, section 2).

## 2. Q1 — the tool's real mechanics, and the "one comparison change" claim adjudicated

**How `positional` is computed:** `_parse_foreach` (`:226-238`) walks comment-stripped, nested-expanded macro-body rows in textual order; for each accepted row it stores `out[prefix+name] = idx` and increments. `idx` counts *accepted* rows only. So the value is a **dense 0-based ordinal over the union macro's textual order**.

**How it is compared:** `compare()` (`:305-343`) iterates the FROZEN map. Per name: absent -> `REMOVED`; present with a different int -> `RENUMBERED`; present with the same int -> the `VALUE-REUSE` scan. A shift-by-one therefore produces one `RENUMBERED` line per shifted name.

**Does the ledger FILE FORMAT have to change? NO — measured.** My prototype read `tools/identifier_ledger.txt` **unmodified** and produced correct relative-order verdicts on all six scenarios. The `category|identifier|value` format already encodes a total order; relative semantics just reads the int as a rank.

**Is "one comparison change, no ledger reshape" TRUE?** *Substantially yes, understated by three concrete items.*

| Claim component | Verdict | Evidence |
|---|---|---|
| ledger file format unchanged | **TRUE** | prototype parsed the live ledger as-is |
| only one `compare()` branch changes meaning | **TRUE** | `:329-332` is the sole RENUMBERED site |
| "one change" | **UNDERSTATED — 3 additions** | (i) a category-scope constant mirroring `MONOTONIC` at `:161-162`; (ii) **selftest case (4) at `:98` BREAKS** — measured: its `grep -q 'RENUMBERED stamp-key :: feature_mask'` returns NO MATCH because the tooth now emits `REORDERED stamp-key :: feature_mask` (it still FIRES — only the label changed; the message at `:101-103` needs rewording too). Case (5) at `:114` and case (6) are unaffected — measured MATCH; (iii) mid-insert protection needs a *second, independent* rule |
| implicit: the ledger's number keeps meaning what it meant | **FALSE** | `ledger_lines():293-296` re-densifies on bless, so post-delete the column silently shifts from "the value" to "a rank". A doc obligation, not a code one — but it must be discharged, or the ledger becomes a mixed-semantics file with nothing saying so. |

## 3. Q2 — every `positional` category, and whether the change leaks

| Category | value mode | rows | Is the ordinal itself persisted? |
|---|---|---|---|
| `enum:StrategyId` | positional | 5 | **YES** — `Strategies/StrategyInterface.hpp:173-181` generates `STRATEGY_##id,` with no explicit value => ordinal **IS** the enum value written to snapshots + trade logs |
| `enum:RegimeId` | positional | 5 | **YES** — same generation shape |
| `enum:ShaltCode` | positional | 20 | **YES** — same; `StrategyInterface.hpp:242-243` states trade logs reference the numeric values |
| `enum:NodeStateFlag` | positional | 6 | **YES** — `MemHeaders/NodeStateFlagRegistry.hpp:116-124`: ordinal = bit position, `MASK_NODE_STATE_##name = BITMAP_BIT_U8(NODE_STATE_FLAG_##name)` |
| `stamp-key` | positional | 46 | **NO** — the wire token is the *string name* (`key=value`). Verified against all 16 in-tree artifacts: every one is name-keyed text; **no artifact anywhere encodes an ordinal** |
| `enum:BanditAlgorithm` | *explicit* | 5 | n/a — reads the literal value column |
| `version`, `wire-const` | define/constexpr | 7 | n/a |

**`stamp-key` is the sole category in the set whose ordinal is a synthetic order-proxy rather than a persisted value.** That is a genuine semantic distinction, not a convenience carve-out.

**Would it leak?** Structurally no, *if implemented opt-in*. The tool already has the exact idiom — `MONOTONIC = {"version"}` at `:161-162` — so a second frozen set `RELATIVE_ORDER = {"stamp-key"}` is the same shape, and an unlisted category keeps today's behavior by construction.

**What breaks if it leaks (the reason this must be opt-IN, never opt-OUT):** deleting `STRATEGY_MEAN_REVERSION` genuinely renumbers `STRATEGY_MOMENTUM` 1->0 in every persisted snapshot and trade log. Under relative semantics that reports **1 REMOVED and calls the other four fine** — a false green on the literal Knight-Capital shape. An opt-out default would silently convert four correct guards into the failure they exist to prevent.

## 4. Q3 — the contested reading (precise, factual)

**Verbatim, `tools/check_identifier_retirement.py:144-156`:**

```
    # E.1.2 D-425 #10 (2026-08-17) — the STAMP WIRE KEYS. H21 names "cfg-field name keys" as a
    # tracked identifier class, and these are exactly that: the `key=value` tokens of an
    # HMAC-signed model stamp. Their emit ORDER is the canonical body order (the registry's own
    # PRE_CFG/POST_CFG split exists to preserve it around the sister cfg registry), so `positional`
    # is the correct value semantics and strictly stronger than name-set membership: a REORDER
    # perturbs the signed bytes and lands as RENUMBERED, a dropped key as REMOVED. Verified against
    # a real artifact (models/**/barrier.json.stamp) — parsed order matches the emitted key order.
    #
    # NOT enrolled, deliberately: the `STAMP_BIT_*` / `MASK_*` group+standalone bit POSITIONS. They
    # are a hand-written enum, not registry-derived, and `has_flags` is never persisted, hashed or
    # memcmp'd — no artifact encodes a bit position (the :553 tombstone states this and independent
    # review confirmed it by byte-context read, not by trusting the comment). Renumbering them is
    # H21-safe; only the retired NAMES need protecting, and those live in RETIRED_NAMES above.
```

**My reading — the comment weighs `positional` against *name-set membership ALONE*. It does not consider relative order, and does not exclude it.**

The argument is a two-clause comparative: `positional` is *"strictly stronger than name-set membership"* because **(a)** a REORDER lands as RENUMBERED and **(b)** a dropped key lands as REMOVED. The named competitor is the bare phrase *"name-set membership"* — a set-only property, which by construction cannot see (a). Both cited advantages are *also* delivered by name-set + relative order. The comment contains no token — not "relative", "rank", "subsequence", "inversion", "sparse", "stable" — that engages a third option. **The relative-order alternative was never weighed; the comparison is genuinely against the weaker of the two candidates.**

Two ancillary factual points about that same comment, both measured:

- *"Verified against a real artifact … parsed order matches the emitted key order."* The claim as written is about **order**, and order is what an artifact can show. It is **not** evidence for the *indices*, and cannot be: I read `models/classification/multi_2year_01_horizon_15000/barrier.json.stamp` and the emitted keys are a **strict subsequence with holes** (`training_poll_interval` -> `model_num_outputs` -> …, skipping `feature_scaler_present`/`scaler_sha256`/`grid_member_*`/`feature_mask` and every POST_CFG key). The artifact demonstrates **relative order and nothing else** — the emit walk is per-row `has_*`-gated, so absolute ordinals are *never* observable on the wire. The artifact is, if anything, evidence *for* the relative reading.
- All 16 in-tree stamps carry `stamp_format_version=1` (measured: `grep -rn "stamp_format_version=" models/` -> 16 hits, all `1`), and `STAMP_FORMAT_VERSION_EPOCH_FLOOR=3` hard-refuses them. **None contains `inference_cfg_bandit_blend_ratio`.** So the artifact corpus is pre-epoch, pre-`.B.3`-migration, and has zero exposure to the key under discussion.

## 5. Q4/Q5 — the option matrix, with MEASURED numbers

Baseline non-vacuity proven first: unmodified scratch tree -> GREEN.

| Scenario planted in the registry | (b) POSITIONAL — violation lines | (a) RELATIVE, plain | **(f) RELATIVE + tail-append** |
|---|---:|---:|---:|
| 0 — no change (control) | 0 OK | 0 OK | 0 OK |
| **1 — DELETE row 0 `inference_cfg_bandit_blend_ratio`** | **46** (1 REMOVED + 45 RENUMBERED) | **1** | **1** |
| 2 — MID-BODY INSERT of a new key at idx 5 | 41 RENUMBERED + 1 ADD | **0 — MISSES IT** | **1** (`INSERTED-MID-BODY`) |
| 3 — APPEND AT END (the sanctioned add) | 0 + 1 ADD | 0 + 1 ADD | 0 + 1 ADD |
| 4 — adjacent SWAP (`xgb_seed` <-> `xgb_min_child_weight`) | 2 | 1 | 1 |
| 5 — long-range MOVE (`run_name` -> end of POST_CFG) | 17 | 1 | 1 |
| **6 — DELETE row 0 *plus* a smuggled SWAP** | **45** — and **the swap is half-ERASED** | **2** | **2** |
| 7 — DELETE the LAST key (idx 45) | 1 | 1 | 1 |

**Scenario 6 is the finding that decides this.** Under positional, delete+swap emits **fewer** lines (45) than the clean delete (46), and `xgb_min_child_weight` — one of the two swapped keys — produces **zero lines** (measured: `grep -c 'xgb_min_child_weight' -> 0`). It lands back on the value it already held, so `compare()` takes the `else` branch at `:333-338`, finds no other holder, and reports nothing. Its partner's line is textually identical in shape to the 43 innocent shift lines. **A real reorder co-occurring with a delete is not merely buried in the noise under positional — it is partially erased by it.**

### The options

| # | Option | Cost | Protects | Stops protecting |
|---|---|---|---|---|
| **(a)** | **Relative order, plain** | `RELATIVE_ORDER` set + ~20 lines in `compare()`; selftest `:98` grep + `:101-103` message; a doc line that the number is now a rank | drop (1 line) · any reorder (1 line/moved key) · the scenario-6 hidden swap | **mid-body INSERT — measured GREEN.** Silently retires the only mechanical enforcement of the append-at-end wire discipline (`StampBoundModelConstRegistry.hpp:519-521`, `:539-540`) |
| **(b)** | **Keep positional, accept 45 renumber lines** | zero code; a 46-line red on every legitimate tail-ward delete forever | everything today | nothing new — but it *behaves* as if it protects less: scenario 6 proves a real reorder is concealed by the noise it generates |
| **(c)** | **TTY-gated `--update` epoch re-bless after the delete** | zero code. **MEASURED operator burden: an 89-line bless diff**, in which the smuggled swap is exactly ONE line (`+stamp-key|xgb_seed|9` vs the honest `10`) among 43 visually identical shift lines | preserves the M10/D-385 property (an agent structurally cannot re-bless) | the *review* is the guard, and the measurement shows the review cannot see the one line that matters |
| **(d)** | **Sparse/stable ordinals** — ledger becomes a slot ALLOCATOR | largest: `ledger_lines()`/`write_ledger()` must read the prior ledger; **breaks the golden-master property** the tool's own docstring rests on (`:26-29`) | everything (a) does, plus mid-insert, plus numbers become literally H21-conformant ("keep the number") | the guard's own auditability — a ledger that is a function of its own history is harder to verify than one that is a function of the code |
| **(e)** | **Separate order-digest row** | small | drop + any order change incl. mid-insert, in 1 line | **diagnosis** — the line names no key, so it fires identically for a sanctioned append and a smuggled swap |
| **(f)** | **NOVEL — relative order + TAIL-APPEND rule** | (a)'s cost + ~8 more lines: a NEW name not in the tail of the current order is an `INSERTED-MID-BODY` violation. **No ledger format change, no allocator, no history dependence** | **strictly dominates (a) and (b) on every measured cell** | nothing measured |
| (g) | *Don't delete the row — fix its producer* | dissolves this decision entirely | — | **SETTLED, not re-litigated**: D-426 DECIDED the delete on the `fees` precedent (`decision-logs/…-E-architecture-v2.md:2902`). Listed for completeness only |

## 6. Why the ORDER signal must survive, whichever option wins

I checked whether positional's order signal is redundant with a sister guard. **It is not — it is the only one.**

- `wire-format-byte-preservation-discipline.md:192-206` specifies **Layer 5, a locked canonical-body hash** whose stated purpose is *"Prevents future row reorders from silently breaking the chain"*. Measured: **it does not exist.** Zero hits for a body hash / `fnv1a` over the stamp body in `tests/`.
- `:208-228` specifies **Layer 5b structural invariants I1-I5**, incl. I5 (emit order). Measured: **`run_generic_invariants` and `DERIVED_FILTER_DECLARE_WIRE_FORMAT` have ZERO hits** across `CoreFrameworks/ ML_Headers/ tests/`. The machinery is documented, not built. Its stated scope is the *cfg-derived* half anyway, not the model-const registry.
- The tests that do exist are count-shaped (`controller_test.cpp:23912-23913` `>= 25 entries`, `:23978-23979` walk-count) — order-blind by construction.
- `controller_test.cpp:28499-28513` is an emit->verify round-trip in the **same binary**, so both halves share whatever order the registry has. Order-insensitive by construction.

**Conclusion: `check_identifier_retirement.py`'s `stamp-key` ordinal is the sole mechanical order guard on this HMAC-signed body at HEAD.**

## 7. Severity-classified findings surfaced en route

**F1 — HIGH — Class 51 (vacuously-green guard, mode A). `retired_name_check()` cannot protect 3 of its 4 burned names.** Its regex (`:365-366`) matches `^\s*#\s*define\s+NAME\b` only.

- **MEASURED:** re-introducing `inference_cfg_fee_rate_maker` as an `X()` registry row -> **rc=0, GREEN**, reported as `ADD (ok; run --update to record)`.
- **MEASURED:** re-introducing `STAMP_BIT_fees` as an enum member -> **rc=0, GREEN**. (`STAMP_BIT_*` are enum members — `:604-640`; measured zero `#define STAMP_BIT_` tree-wide.)
- **POSITIVE CONTROL:** re-introducing `#define CONTROLLER_SNAPSHOT_VERSION 1` -> **rc=1**, `RETIRED-NAME-REUSE` fires correctly. The mechanism works; it just cannot reach a registry-row or enum-member name.
- This **directly contradicts** the comment at `:88-105`, which claims *"Burning the names here is what makes that deletion ENFORCED rather than narrated — without these entries a re-introduced `STAMP_BIT_fees` classifies as a fresh 'ADD (ok)'"*. Measured: **it classifies as a fresh "ADD (ok)" *with* the entry.**
- **This is a hard prerequisite for the decision, not an adjacent nicety.** Under *every* option, deleting `inference_cfg_bandit_blend_ratio` moves its protection from the ledger row to `RETIRED_NAMES`. Measured, that destination is empty for this shape.

**F2 — MED — stale checkable comment.** `StampBoundModelConstRegistry.hpp:341-343` says *"PRE_CFG section: … 26 entries today."* Measured: **22**. Suggested wording: drop the count entirely — `FOREACH_STAMP_BOUND_MODEL_CONST_PRE_CFG_COUNT` is the re-derivable anchor.

**F3 — MED — precision defect in the enrolment comment.** `:148-150` reads *"Their emit ORDER is the canonical body order … so `positional` is the correct value semantics."* The premise is true; the inference to *absolute ordinals* does not follow, and is contradicted by the same file: the enrolled union macro (`:561-563`) concatenates PRE_CFG+POST_CFG while the emitter interleaves the cfg-derived half between them (`ModelInference.hpp:2313-2317`).

**F4 — LOW — the discipline SSoT already rules for the name.** `dead-code-and-identifier-retirement-discipline.md:125-129`: *"the NAME is the identifier, a non-persisted BIT is not"*, and `:129` states the stamps are *"name-keyed"* and *"wire-emitted, by name, not the raw byte"*. `:103` lists **cfg-field name keys** as the tracked class — by name. The spec never asserts a stamp key's *ordinal* is an identifier.

## 8. RECOMMENDATION

**Adopt option (f) — relative order + tail-append rule, opt-IN scoped to `stamp-key` — with F1 fixed in the same commit.**

1. `RELATIVE_ORDER = {"stamp-key"}` next to `MONOTONIC` at `:161-162` — **opt-in so an unlisted category keeps today's behavior by construction**.
2. In `compare()`, for categories in that set, replace the `:329-332` RENUMBERED branch with: REMOVED unchanged -> then compare the frozen name-order **restricted to survivors** against the current order restricted to frozen names; report each key outside the longest non-moving subsequence as `REORDERED`.
3. Add the tail-append rule: a name present in current-but-not-frozen that does **not** sit in the tail of the current order is `INSERTED-MID-BODY`.
4. `check_identifier_retirement_selftest.sh:98` grep `RENUMBERED` -> `REORDERED` (+ reword `:101-103`). Add two new teeth: a planted mid-insert must RED, and a planted delete-plus-swap must produce exactly 2 lines naming both facts.
5. Fix F1: extend `retired_name_check()` beyond `#define` to sweep enrolled-registry row names.
6. Rewrite the `:144-156` comment to state what is actually true: the wire identifier is the **name**; the ledger int is a **rank**, not a position. Correct F3 while there.

**If the a-class refutes (f), (d) is the fallback I would advance, not (b).**

## 9. Where the paired A-CLASS should push hardest

1. **HIGHEST — "the tail-append rule is a second registry-shape assumption dressed as a comparison tweak."** My (f) asserts *new keys always append at the very end of the union macro*. True for POST_CFG. **Is it true for a new PRE_CFG key?** A key legitimately added at the end of *PRE_CFG* lands at ordinal 22, i.e. mid-order in the union — my rule would flag a **sanctioned** add as `INSERTED-MID-BODY`. I did **not** measure that case.
2. **The category-scoping argument rests on "no artifact encodes a stamp-key ordinal."** Every one of the 16 is `stamp_format_version=1`, pre-epoch, refused at the floor. **The corpus is entirely historical.** If any *other* consumer (foxml_suite trainer, a Python trainer sidecar, a GUI panel, a fixture generator outside `tests/`) positionally indexes stamp keys, my whole category distinction falls. **Class 58-C, my biggest un-swept surface.**
3. **Is `compare()`'s VALUE-REUSE branch (`:335-338`) load-bearing for `stamp-key` at all?** Measured 0 hits in every scenario. I did not prove unreachability, only observed it 8/8.
4. **F1's fix scope.** An adversary should ask whether extending `retired_name_check()` to registry rows reintroduces the coupling its docstring calls "SOURCES-independent BY NECESSITY" (`:353-361`).
5. **Does anything read `ledger_lines()`' value column semantically?** I traced only `.githooks/pre-commit:427` and the tool itself.
6. **The claim that verification is order-independent** (1.3). It is the pivot of my whole reframe. The reconstruction is `"%s=%s\n"` from *parsed* key/val, so it normalizes whitespace; I did not chase what else it normalizes.
7. **My scenario-6 "erasure" claim** rests on an *adjacent* swap under a shift-by-one. A non-adjacent swap would not erase. The honest statement is *"a delete can erase an adjacent reorder"*.
