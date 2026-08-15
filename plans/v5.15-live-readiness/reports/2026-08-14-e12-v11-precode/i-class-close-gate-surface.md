---
type: agent-report
status: FROZEN — verbatim agent output, saved at receipt
directive: map the v11 close-gate BUILD surface (golden regen/rename, version asserts, AM-4 fixtures, cache-layout re-bless, TTY bless choreography, AM-6 target)
agent_class: i-class
delivered: 2026-08-14
consumed_by: the v11 bump-commit runbook + Step-5 close-gate implementation
sister_reports: orchestrator-am4-evidence.md · i-class-money-surfaces.md · i-class-d289-blast-radius.md (this directory)
---

# I-CLASS SURFACE MAP — v11 CLOSE-GATE BUILD SURFACE (E.1.2 Steps 3–5, SHARDED 10→11)

**Agent:** I-class investigative · **Engine HEAD:** `5ac8a7b` (verified) · **Date:** 2026-08-14
**Directive scope:** map the BUILD surface for the locked gate design (frozen hex-TEXT golden + registry-driven per-FIELD-distinct poison + per-field value round-trip + positive control + wire-length pin + AM-4 mid-pair fixtures). Gate design NOT re-litigated.
**Mechanical tools RUN at HEAD (ground truth, not recall):** `check_identifier_retirement.py` → GREEN, 48 identifiers, 2 standing wire-const ADDs · `node_persist_layout.py` → GREEN, 46 rows match golden · `check_cache_layout.py --strict-new` → 0 NEW, **4 grandfathered engine findings still LIVE**.

---

## 1. The EXISTING v10 gate as landed at D-305/1 — exists/new classification

### 1a. The golden header (`/home/caramel/code/FoxML_Trader_v2/tests/sharded_snapshot_v10_golden.hpp`, 647 lines)

- **How generated:** NOT hand-written, NOT a standalone tool — a **regen mode compiled into the test itself**. The header's own instructions (`:11-13`): `g++ -std=c++17 -O2 -I.. -DREGEN_SNAPSHOT_GOLDEN -o /tmp/ctgen controller_test.cpp && /tmp/ctgen`, then paste the emitted array body. The `#ifdef REGEN_SNAPSHOT_GOLDEN` printf block lives at `tests/controller_test.cpp:6369-6377` (prints the full `0x%02x,` hex body + the `_LEN` line, 16 bytes/row).
- **Regen policy comment** (`:11`, `:14-15`): "REGENERATE ONLY behind a reviewed SHARDED_SNAPSHOT_VERSION bump (H21 / D-302 paired-bump)… never regen inside a layout-changing commit" — i.e., the v11 bump commit IS the sanctioned regen event.
- **Contents:** provenance comment `:4-15` (poison fixture name, D-305, mask note), capture note `:18-19` ("len 9968 bytes, timestamp-masked, captured from the v10 hand-loop at engine HEAD 84d73e0"), `SHARDED_SNAPSHOT_V10_GOLDEN[]` `:20`, `SHARDED_SNAPSHOT_V10_GOLDEN_LEN = 9968UL` `:646`. Those two symbols are the ONLY identifiers.

### 1b. The byte-golden test (Test 2G, `tests/controller_test.cpp:6352-6396`)

Full harness: `build_state(4, 10000.0)` (`:6357`) → `poison_persisted(r, 4)` (`:6358`) → `ShardedSnapshot_Save<64>` to `/tmp/ftv2_snapshot_golden.dat` (`:6359-6361`) → whole-file fread into 64KB buf (`:6363-6366`) → **mask exactly `[12,20)`** `for (int i = 12; i < 20 && i < (int)gn; ++i) gbuf[i] = 0;` (`:6367`) → REGEN printf OR the two checks (`:6379-6383`) → positive control (`:6385-6394`: mutate `nodes[1].node_realized`, re-save, re-mask, assert bytes differ). Mask width == sizeof(`timestamp_us`) at header offset 12 (save header writes magic 4 + version 4 + num_nodes 4 + timestamp 8, `CoreFrameworks/ShardedSnapshotPersist.hpp:157-160`).

### 1c. Locked-gate layer classification — EXISTS vs NEW at Step 5

| Gate layer | Status | Where |
|---|---|---|
| Frozen hex-TEXT golden (masked [12,20)) | **EXISTS** | golden hpp + test `:6352-6383` |
| Wire-length pin | **EXISTS** | `:6379-6380` + `_LEN` `:646` |
| Byte-identity memcmp | **EXISTS** | `:6381-6383` |
| Positive control (Class-51 teeth) | **EXISTS** | `:6385-6394` |
| Per-FIELD-distinct poison fixture (nonzero, ALL-64 confidence, node-varying) | **EXISTS — but HAND-ENUMERATED, not registry-driven** | `poison_persisted` lambda `:6270-6340` |
| Per-field value round-trip | **EXISTS** | Test 2 `:6398-6638` (OMS 10 fields `:6504-6529` + bit-cleared case `:6531-6543` + per-node loop `:6545-6622` + Position 7 money fields `:6623-6637`) |
| AM-4 mid-pair round-trip fixture | **NEW** | nothing exists — `partner` has zero hits in ShardedSnapshotPersist.hpp |
| AM-4 orphan-leg fixture | **NEW** | ditto |
| Registry count-lock ==29 | **EXISTS** | `MemHeaders/NodeCtxPersistRegistry.hpp:114-124` |
| Layout golden + paired-bump | **EXISTS** | `tools/goldens/node_persist_layout.txt` (46 rows; row `019|node_dd_pct|Money|SCALAR:COMMIT|` at file line 27) + `check_identifier_retirement.py::paired_bump_check` `:268-320` |

**Poison-fixture nuance (refute spot #3):** the landed fixture satisfies the A4 SPIRIT (every field distinct + nonzero + node-varying; ALL 64 confidence entries via bases 1000001/2000001/3000001 + c*1000 + j, `:6313-6319`) but NOT the mechanical `seed = FIELD_BASE≥1 + field_index; value = seed + node*STRIDE` formula, and it is NOT registry-driven — a future field add can silently miss its poison line (the exact zero-desert class A4 closed). At v11 someone must hand-swap `:6281` (`node_dd_pct = MQ(3.03 + 0.03*c)`) for a `partner_pending_pnl` poison line.

---

## 2. RENAME plan — v10_golden.hpp → v11 (rides the bump commit)

**File rename:** `tests/sharded_snapshot_v10_golden.hpp` → `tests/sharded_snapshot_v11_golden.hpp`.

**Every reference (complete; greps of engine + tests + workspace tools + hooks):**

| Site | What renames |
|---|---|
| `tests/controller_test.cpp:21` | `#include "sharded_snapshot_v10_golden.hpp"` + trailing comment |
| `tests/controller_test.cpp:6353` | comment "freeze the v10 hand-loop output" |
| `:6370` | REGEN printf `"REGEN sharded_snapshot_v10_golden.hpp"` |
| `:6371`, `:6376` | REGEN printf'd identifier names (`SHARDED_SNAPSHOT_V10_GOLDEN[]` / `_LEN`) |
| `:6379-6383` | check strings "matches frozen v10" ×2 + the 3 identifier uses |
| golden hpp `:4`, `:13`, `:18-19` | comments (v10 wording, identifier name, capture-HEAD note — re-stamp with v11 + new HEAD) |
| golden hpp `:20`, `:646` | the 2 identifiers → `SHARDED_SNAPSHOT_V11_GOLDEN` / `_LEN` |
| `MemHeaders/NodeCtxPersistRegistry.hpp:23`, `:110`, `:123` | filename in comments + inside the count-lock static_assert MESSAGE; also "Snapshot v10" wording `:108`, `:119-120`, `[OVERVIEW]` "at snapshot v10" `:46`, "(v10 byte layout)" `:60` |
| `CoreFrameworks/ShardedSnapshotPersist.hpp:194` | comment "frozen golden: tests/sharded_snapshot_v10_golden.hpp" |

Not renamed (frozen records, cite-era by design): `plans/.../readiness-2026-08-14-...md:27`, the plan_checks, `reports/`. No hits in CMakeLists.txt / build.sh / .githooks / tools (the byte-golden is test-TU-internal).

**Adjacent stale-comment sweep owed at the bump** (subplan `:98` "Sweep ALL at the bump"): the "legacy v11" refuse comments in `ShardedSnapshotPersist.hpp:32`, `:66`, `:282-284` mean the LEGACY PortfolioController v11 — an active name-collision once SHARDED itself is 11 (reword to "legacy PortfolioController-format snapshot"); same for Test 3's "refuse legacy v11 magic" `tests/controller_test.cpp:6640-6643` (that test refuses on MAGIC `0x4B434954`, not version — stays correct, comment misleads). Also the epoch-tripwire message `ShardedSnapshotPersist.hpp:119-120` still says "bump … to 10u … in THIS commit".

---

## 3. Version-assert surfaces (complete grep of tests/ — no other files reference these macros)

**Macro ground truth:** `SHARDED_SNAPSHOT_VERSION 10u` @ `CoreFrameworks/ShardedSnapshotPersist.hpp:112` (banner's `:109` is 3 lines stale post-63364a7) · `CONTROLLER_SNAPSHOT_VERSION 14` @ `CoreFrameworks/PortfolioController.hpp:2181` (D-289: DELETED) · `PORTFOLIO_SNAPSHOT_VERSION 7` @ `CoreFrameworks/Portfolio.hpp:800` (BLK-2: RETIRES, no bump) · **`MONEY_ENCODING_EPOCH = 1u`** (`FixedPoint/FixedPointN.hpp:300`, `is_fp_decimal_v<EngineMoneyT> ? 1u : 0u`; test `:26952-26953` pins ==1 POST-flip).

| Site | Current | v11 fate |
|---|---|---|
| `tests/controller_test.cpp:11587-11588` | `check("…SHARDED_SNAPSHOT_VERSION is 10 (…=8, Ship-A 16B=9, Ship-B DECIMAL epoch=10…)", SHARDED_SNAPSHOT_VERSION == 10u)` | `== 11u` + append history clause ("E.1.2 v11: node_dd_pct→partner_pending_pnl row swap") |
| `:26943-26945` static_assert | `CONTROLLER >= 13+EPOCH && SHARDED >= 9u+EPOCH && PORTFOLIO >= 6+EPOCH` | **The SHARDED clause survives numerically (11 ≥ 10) — but the line COMPILE-BREAKS when CONTROLLER deletes / PORTFOLIO retires.** Reshape to SHARDED-only: `static_assert(SHARDED_SNAPSHOT_VERSION >= 9u + MONEY_ENCODING_EPOCH, …)` |
| `:26948-26951` runtime check | mirrors the static_assert | same reshape to SHARDED-only |
| `:27013-27014` 4-version pin | `SHARDED == 10u && CONTROLLER == 14 && PORTFOLIO == 7 && STAMP_FORMAT_VERSION_CURRENT == 3` | **exact new 2-version shape:** `SHARDED_SNAPSHOT_VERSION == 11u && STAMP_FORMAT_VERSION_CURRENT == 3` + reword the check string `:27012` ("all four persisted versions" → "both") + the comment `:27010-27011` ("any v9/v13/v6/v2 artifact") |
| `:27015-27016` | `MAX_SUPPORTED_STAMP_FORMAT_VERSION == 3` | unchanged |
| serializer `:118-120` epoch tripwire | `MONEY_ENCODING_EPOCH == 0u || SHARDED >= 9u + EPOCH` | survives (11 ≥ 10); message text stale-sweeps |

**Hazard (H-2, below):** the directive names only `:27013` as "the 4-version assert", but `:26943-26951` is a SECOND surface hard-referencing the deleted/retired macros — every D-289 delete commit must reshape its clause to keep that commit compiling (micro-commits compile-gated).

---

## 4. AM-4 fixtures — where they land + reusable scaffolding

**The AM-4 contract** (subplan `:216`, D-291/AM-4 2026-07-03): persist `partner_pending_pnl` (NodeContext `Money`, `CoreFrameworks/ControllerEventLoop.hpp:488`); **RE-DERIVE `partner_pending_bitmap`** (EventLoopState `uint16_t`, `:901`) on load via slot parity `bit N = active(2N) XOR active(2N+1)`; do NOT persist the bitmap. Pairing consumer logic: `:1814-1831` (bit set + pnl parked on first-leg exit `:1830-1831`; bit cleared + pnl zeroed on pair completion `:1827-1828`).

**Engine-side NEW code the fixtures test:**
- Registry row swap in `FOREACH_NODE_PERSIST_FIELD` (`MemHeaders/NodeCtxPersistRegistry.hpp:91` drops; `X(partner_pending_pnl, Money, SCALAR, 0, COMMIT)` adds — net 0 rows/bytes, count-lock stays ==29, block stays 1944B).
- `NodeSnap` staging swap (`ShardedSnapshotPersist.hpp:371` — the struct is the HAND-KEPT DECLARE view per `NodeCtxPersistRegistry.hpp:141-143`; names must match row NAMEs).
- Bitmap re-derive: **cannot be a registry row** (`partner_pending_bitmap` lives on EventLoopState, not NodeContext) → a post-commit derive step; natural home = beside the re-activation finalizer's active_bitmap walk (`ShardedSnapshotPersist.hpp:493-498`, which already has `partial_exit_enabled` + `Sharded_SlotNode` in scope).
- `node_dd_pct` recompute needs NO load-side code: it's a display field "recomputed each rebuild" (`ControllerEventLoop.hpp:532` comment; compute site `:3278-3281`, kill-check consumer `:3292`) from persisted `node_peak_balance` — first slow-path rebuild restores it.

**The F-018 W/L pairing harness scaffolding** (`tests/controller_test.cpp:9896-10033`):
- local `struct R { OrderManagerState oms; EventLoopState state; SPSCRing tick_ring; ExecutionCore core; }` `:9899-9904`
- `build` lambda `:9908-9916` — **1 core owning slots 0+1, partials ON** (`MASK_OMS_STATE_PARTIAL_EXIT_ENABLED` `:9911`), mode-1
- `fill_leg` lambda `:9918-9934` — real-consumer per-leg `OrderManager_Submit` + `OrderManager_HandleFill` (leg B on slot 1 per FIX-3 `:9881-9884`)
- CASE L `:9938-9983` / CASE W `:9987-10032` build FULL pairs; a MID-PAIR state = the same sequence stopped after ONE exit+drain (2 opens → drain → 1 `fill_leg` SELL → drain ⇒ bit SET + `partner_pending_pnl` parked + partner slot still active).

**Where the two NEW fixtures land — options:**

| Option | Shape | Trade-off |
|---|---|---|
| **(a) Extend the F-018 block** (recommended) | new sub-case after CASE W reusing `build`/`fill_leg`: real mid-pair machine state → `ShardedSnapshot_Save<64>(…, /*partials*/1)` → fresh `R` → `Load(…, 1)` → assert bit re-derived ==1 + `Money_Eq` on the parked pnl (use CASE L's leg-A net `+267.29766082` as the parked value, already ULP-verified `:9941-9943`) | strongest: tests the REAL consumer-produced state; the pairing lambdas are only in scope here |
| (b) Phase-4 hand-built state | in the Phase-4 scope reusing `build_state`/`poison_persisted`; hand-set `positions[1]` active + `partner_pending_pnl` + save partials=1 | simpler, but hand-approximates the machine state; `build_state` (`:6243-6263`) registers cores WITHOUT partials geometry — needs a partials-aware variant anyway |
| (c) both | (a) as the semantic fixture + a poison line in `poison_persisted` so the GOLDEN covers the new row's bytes | the golden ALREADY needs the poison line regardless — so (c)'s second half is mandatory, not optional |

**Orphan-leg fixture (ii):** one leg active, pnl == 0 → Load → bit re-derived ==1, graceful (the next exit's `Money_Add(pnl, exit_net)` at `:1818` adds zero → classifies on the single leg — benign by construction; assert bit ==1 + `Money_IsZero(partner_pending_pnl)` + no crash/halt). Note the EXISTING Test-2/2G fixtures (one active slot, `:6339`/`:6492`) are accidental orphan-leg shapes — see H-4.

**Reusable helpers inventory:** there is NO shared snapshot round-trip helper fn — all 30+ Save/Load call sites (`:6345-7031`) are inline in the Phase-4 block; the partials-geometry save/load precedent is Test `:7010-7031` (partials-mismatch refusal: saved 0 / load-asking 1 refused) and the 4-arg cfg-Load overload appears at `:6801`/`:6834`.

---

## 5. `tools/lib/cache_layout_baseline.txt` (workspace: `/home/caramel/code/tick-trader-percore-workspace/tools/lib/cache_layout_baseline.txt`)

**Exact current keys (13 rows, verified):** header = "GRANDFATHERED findings (kind|struct|field), SHRINK-ONLY. Every row is dispositioned in the D-414 register (homed E.1.2 / suite-plane)."

- **The 4 engine keys to REMOVE at re-bless:** `false-sharing|NodeContext|regime_state` · `false-sharing|TUISharedState|kill_reset_per_node` · `false-sharing|TUISharedState|manual_close_requested` · `false-sharing|TUISharedState|swap_strategy_requested` — matches the directive exactly.
- **The 9 TrainingPanelState keys that MUST STAY** (foxml_suite refactor's, TD-269): `mh_horizon_complete`, `run_name`, `tm_phase_msg`, `ui_horizon_list`, `ui_label_kind_csv`, `ui_label_kind_per_horizon`, `ui_sl_pct_csv`, `ui_sl_per_horizon`, `ui_tp_pct_csv`.

**The check tool:** `tools/check_cache_layout.py` — `--strict-new` HARD mode (un-baselined finding = rc 1) `:597-600`; `--emit-baseline` re-bless `:601-602` with the **SHRINK-ONLY guard** (`_baseline_growth` `:188-193`; REFUSAL if the new set would GROW the committed baseline `:683-694` — "a NEW finding blessed around strict-new"); orphan pawl `_baseline_orphans` `:195-198` reports fixed-but-still-grandfathered keys every `--strict-new` run. NOT TTY-gated (unlike bless.py) — shrink-guard is its control. Invoked by `check_session_docs.sh:425-429` (run_hard, main TU + foxml_suite TU) and its selftest wrapper at pre-commit via the tools gate (`.githooks/pre-commit:323`).

---

## 6. TTY-gated bless choreography — the ordered runbook

**The TTY substrate:** `tools/bless.py` (D-394) — TTY REQUIRED, per-file diff shown, typed confirmation, non-interactive HARD-REFUSES rc=2, NO `--yes`/`--force`, no-op ⇒ no write (D-369). `node_persist_layout.py --bless` routes through it (`node_persist_layout.py:450-452`); `check_identifier_retirement.py --update` inherits the same contract (`:341-355` — "--update has NO automated caller; `.githooks/pre-commit:360` only PRINTS it"). `bless.py` also carries the **interactive roster console** (number-pick per-record bless, TTY-gated up front, `:352-356`) + a coverage tooth (every `tools/goldens/*.txt` must have a roster row, `:264-270`) + `--selftest` (`:408-409`). `check_cache_layout.py --emit-baseline` is the one non-TTY bless (shrink-guard instead).

**Check H trigger** (`.githooks/pre-commit:405-417`): fires on staged `CoreFrameworks/|ML_Headers/|Strategies/|MemHeaders/|FixedPoint/|tools/(identifier_ledger.txt|check_identifier_retirement.py|node_persist_layout.py|goldens/node_persist_layout.txt)` — i.e., **every Steps-3-5 commit fires Check H**, and Check H runs BOTH the ledger compare AND `paired_bump_check` (which imports `node_persist_layout` and diffs the live registry against the layout golden, `check_identifier_retirement.py:268-320`).

**Current ledger state (tool-run at HEAD):** GREEN, 48 identifiers; ledger rows `version|PORTFOLIO_SNAPSHOT_VERSION|7`, `version|SHARDED_SNAPSHOT_VERSION|10`, `version|CONTROLLER_SNAPSHOT_VERSION|14` (`tools/identifier_ledger.txt:55-57`); **the 2 standing wire-const ADDs pending recording: `ROLLING_IC_MAX_WINDOW = 64`** (`ML_Headers/ConfidenceScore.hpp:84`) **+ `MAX_WINDOW = 8`** (`ML_Headers/LinearRegression3X.hpp:34`) — SOURCES rows landed at D-305/1 (`check_identifier_retirement.py:113-114`), reported "ADD (ok)" until `--update`.

**Deterministic commit-order runbook** (each commit must be compile-green + Check-H-green — `feedback_micro_commits_compile_gated`):

**Commit 1 — the v11 bump commit (everything paired-bump forces into ONE commit):**
1. Registry row swap (`NodeCtxPersistRegistry.hpp:91` → `partner_pending_pnl`) + comment/static_assert-message v10→v11 sweep (`:46/:60/:108-110/:119-124`).
2. `NodeSnap` staging swap (`ShardedSnapshotPersist.hpp:371`) + the post-commit `partner_pending_bitmap` re-derive (gated on `partial_exit_enabled` — see H-3) + `SHARDED_SNAPSHOT_VERSION 10u→11u` (`:112`, with H21 tombstone comment extension) + the legacy-v11-comment sweep.
3. Test edits: poison fixture swap (`:6281`), Test-2 fixture+asserts (`:6411`, `:6566-6567` → negative "NOT restored" assert + new partner assert), second pin `:11587-11588` → 11u, AM-4 fixtures (if riding this commit), REGEN-block strings `:6370-6376` → V11.
4. **Regen the golden:** `cd tests && g++ -std=c++17 -O2 -I.. -DREGEN_SNAPSHOT_GOLDEN -o /tmp/ctgen controller_test.cpp && /tmp/ctgen` → paste into the RENAMED `sharded_snapshot_v11_golden.hpp` (+ `#include` at `:21`); expect len 9968 (net-0 — a different len means something else moved).
5. **TTY:** `python3 tools/node_persist_layout.py --bless` (layout golden re-bless — the DROPPED+ADDED pair shown in diff, typed confirm).
6. **TTY:** `python3 tools/check_identifier_retirement.py --update` (records SHARDED 11 BUMP + the 2 wire-const ADDs).
7. `./build.sh test` → controller_test green (the golden memcmp runs IN it) → commit. Check H at commit: layout-diff + version-bump ⇒ "bumps" info, ledger matches ⇒ GREEN.

**Commits 2 + 3 — D-289 retire/delete cascade, ledger+SOURCES lockstep one-commit-each** (readiness Check 46 note; order vs Commit 1 is D-305's "v11 delta then retire/delete" per the banner `:43`):
- Commit 2: delete `PortfolioController_SaveSnapshot/_LoadSnapshot` (`PortfolioController.hpp:2185/:2260`) + `CONTROLLER_SNAPSHOT_VERSION` (`:2181`, tombstone comment per H21) + remove its SOURCES row (`check_identifier_retirement.py:82`-region) + TTY `--update` + reshape the `:26943-26951` CONTROLLER clauses + `:27013` pin.
- Commit 3: delete `Portfolio_Save/_Load` (`Portfolio.hpp:836/:890`) + retire `PORTFOLIO_SNAPSHOT_VERSION` (`:800`, tombstone, NO bump — BLK-2) + SOURCES row + TTY `--update` + reshape the PORTFOLIO clauses. (Preserve the `"TICK"` refuse-magic `ShardedSnapshot_Load:329-333`-region — acceptance criterion, subplan `:80`.)
- Note: the ledger physically DROPS the row at `--update` (`write_ledger` regenerates from current, `:222-227`); H21 tombstoning lives in the code comment + git history of the ledger — the compare()'s REMOVED-violation (`:240-243`) is what forces the lockstep.

**Commit 4 — close-gate:**
- Fix the 4 cache-layout findings (see H-1 — prerequisite!), then `python3 tools/check_cache_layout.py --emit-baseline` (shrinks to the 9 suite keys; shrink-guard allows).
- AM-6 codification (bug class + CI guard authored together — § 7).
- F-096 Money legs (`CoreFrameworks/EngineSharded/Async.hpp:859/:872/:877-881/:926`) ride wherever D-305's order puts them (banner lists them inside item 3).

**`./build.sh test` chain answer:** `build.sh:269-270` runs `./build/controller_test` — so every test run **CHECKS** the golden (memcmp + length pin + positive control compiled in); it never REGENERATES (regen is the separate manual `-DREGEN_SNAPSHOT_GOLDEN` compile). `build.sh:271-276` then chains `check_latency_path_conformance.py || true` as a **non-gating REPORT** (the 3c57534 feature); the gating copy is pre-commit Check N (`.githooks/pre-commit:273-294`), whose trigger list includes `ML_Headers/ConfidenceScore.hpp` — so any Confidence comment-sweep commit fires Check N.

---

## 7. AM-6 codification target

**Locked scope** (subplan `:222`, amendment 6): RECURRING_BUG_PATTERNS class = "hand-declared byte-serialized struct + parallel hand-serializer → silent field-drop drift; instance `node_gross_wins`→$0.00, `ShardedSnapshotPersist.hpp:197-203` at `b10e778` [CITE-AS-EVIDENCE]; TD-196" + CI guard ("flag a byte-serialized struct field absent from its persist registry") + the count-lock — **authored WITH the guard at ship-close** (non-vacuity).

- **Next free Class number: 58.** Highest existing = Class 57 (`class-57-emit-boundary-honesty-flattening.md`; index table rows run to `| 57 |` in `/home/caramel/code/FoxML_Trader_v2/DOCS/RECURRING_BUG_PATTERNS.md`).
- **Format (Class-57 as template,** `/home/caramel/code/tick-trader-percore-workspace/DOCS/recurring-bug-patterns/class-57-emit-boundary-honesty-flattening.md`): `# Class NN — Title` → codification `>` blockquote (date, arc, founding instance, severity, sisters) → bold one-paragraph definition → `## Sub-shapes` → `## Detection signatures` → `## Structural fix` → **`## False-positive surface (M3)` — after Structural fix, before `## Instances`** → `## Instances`.
- **Index row:** `| 58 | <title> | persistence + wire-format | HIGH | DOCS/recurring-bug-patterns/class-58-<slug>.md |` (columns `| Class | Title | Surface | Severity | File |`, index `:43-44`); per-class file lands at the WORKSPACE path.
- **M3 content ready-made:** the false-positive surface = NodeContext fields DELIBERATELY off the wire (`node_dd_pct` post-v11 recompute · the 2 regime score ints "re-derived at warmup" `:6446` · `confidence.window` cfg-owned `ShardedSnapshotPersist.hpp:198-199` · `halt_reason`/`pending_params` ephemeral) — the guard needs an explicit UNPERSISTED-by-design allowlist.
- **Sibling-distinction owed (M3):** the registry header ALREADY files the founding instance under **Class 4** ("v5.4.3 … Class 4: added v4.7.25, silently never persisted", `NodeCtxPersistRegistry.hpp:63-66`) and Class 4 = "Snapshot save/load asymmetry". Class 58 must articulate the delta (Class 4 = one SIDE missing; Class 58 = field absent from the whole hand-walk / struct↔serializer parallel-mirror drift) or the a-class will call it a duplicate.
- **Guard identity question** (OPEN-3 below): whether the landed stack {==29 count-lock + 46-row layout golden + paired-bump + byte-golden} SATISFIES the "CI guard" clause, or whether the literal "struct-field absent from its persist registry" coverage checker (a NEW tool axis — struct-vs-registry, which none of the landed guards check) is still owed.

---

## HAZARDS

- **H-1 (structural, blocks the close-gate):** the 4 engine cache-layout findings are **LIVE at HEAD** (tool-run: "0 NEW; 4 grandfathered"). The banner's item-3 work list contains NO explicit fix for `NodeContext|regime_state` false-sharing or the 3 `TUISharedState` fields — only a carried OPEN "writer-group analysis" (banner `:47`). The close-gate re-bless "MINUS EXACTLY the 4 engine keys" is IMPOSSIBLE until those findings are actually fixed (removing baseline keys while the finding persists REDs the next `--strict-new`). Un-scoped work is hiding inside a "re-bless" bullet.
- **H-2 (compile-break):** `:26943-26945` static_assert + `:26948-26951` runtime check hard-reference `CONTROLLER_SNAPSHOT_VERSION` + `PORTFOLIO_SNAPSHOT_VERSION` — each D-289 delete commit MUST reshape its clause in the same commit or that commit doesn't compile. The directive's "4-version assert" framing under-counts the surfaces by one.
- **H-3 (capital-correctness, the sharpest AM-4 trap):** the re-derive `bit N = active(2N) XOR active(2N+1)` is only meaningful under partials geometry. Under `partial_exit_enabled=0`, slot N ↔ node N and EVERY lone active slot would spuriously set a partner bit. The re-derive MUST be gated on `partial_exit_enabled` (in scope at the finalizer, `ShardedSnapshotPersist.hpp:498-499`); else-branch clears the bitmap. The partials-mismatch refusal (`:7010-7031` tests) guarantees geometry consistency file↔cfg, so the gate is sufficient.
- **H-4 (fixture side-effect):** post-v11, the EXISTING Test-2/2G fixtures (one active slot, partials=0 saves) become accidental orphan-leg shapes — with the H-3 gate they derive bitmap=0 (correct); WITHOUT the gate they'd derive spurious bits with no current assert catching it (silent wrong state). An explicit "partials=0 load ⇒ partner_pending_bitmap == 0" assert in Test 2 pins the gate.
- **H-5 (semantic ordering):** `node_dd_pct` is only recomputed at the first slow-path rebuild (`ControllerEventLoop.hpp:3278`); between load and first rebuild the GUI/TUI export (`ShardedSnapshot.hpp:512`, `GUI/DashboardPanels.hpp:1142/:2186/:2202`) shows 0.00% dd. Benign (kill-check `:3292` runs in the same rebuild that recomputes) but worth one comment at the drop site.
- **H-6 (golden regen discipline):** the regen and the layout-golden `--bless` must ride the SAME commit as the version bump or Check H flips to VIOLATION on the NEXT commit ("layout golden is STALE", `paired_bump_check:307-313`). The choreography in § 6 is order-forced by the tooling, not convention.

## OPTION MATRIX (the genuinely-open build choices; gate design untouched)

| Choice | Options | Recommendation |
|---|---|---|
| AM-4 fixture home | (a) F-018 extension (real consumer) / (b) Phase-4 hand-built / (c) a + mandatory poison line | **(c)** — (a) for semantics, and the poison line is required for golden coverage regardless |
| partner row wire position | in-place at old `node_dd_pct` slot (minimal layout-golden diff) vs semantic re-group near the W/L counters | **in-place** — v11 rejects v10 files anyway, but in-place keeps the golden/layout diff to a clean DROPPED+ADDED pair at one index and every other offset stable for review — **[ORCHESTRATOR NOTE at receipt: SUPERSEDED by D-420 — the operator decided cohort-semantic placement before this report landed; D-420 wins]** |
| Delete-cascade order | bump-first (banner order) vs deletes-first | **bump-first per D-305's stated order** (banner `:43`); each delete commit carries its own assert-reshape (H-2) |
| Poison fixture form | keep hand-enumerated vs registry-driven | see novel-alternative row |
| **Novel alternative considered** | **(i) `NPF_PROJECT_POISON` — a 4th projection in `NodeCtxPersistRegistry.hpp`** (rows self-poison via `FIELD_IDX`-seeded values per the A4 formula; delegates get sub-poison walkers) — makes "registry-driven poison" literal: a future row add CANNOT miss its poison, closing the recurrence the hand lambda leaves open. Cost: BIT/PAD/DELEGATE poison semantics need design; the fixture also poisons OMS + Position fields OUTSIDE this registry, so the projection only covers the per-node block. **(ii) version-AGNOSTIC golden filename** (`sharded_snapshot_golden.hpp` + an asserted `GOLDEN_FOR_VERSION == SHARDED_SNAPSHOT_VERSION` constant) — kills the recurring rename cost at every future bump. **REJECT (ii):** the version-NAMED file is itself a deliberate forcing function (the rename IS the reviewed touch; readiness table `:27` treats it as a feature). **(i) = genuine candidate** — present at the dive as the honest reading of the locked "registry-driven poison" phrase; if declined, the hand-lambda gap gets a one-line comment tying it to the count-lock (a row add without a poison line still REDs the golden length/bytes, which bounds the exposure to value-collision, not drop). | offer (i), reject (ii) |

## SPOTS MOST WORTH AN ADVERSARIAL REFUTE (for the paired a-class)

1. **H-1** — demand the concrete fix mechanism for each of the 4 cache-layout findings inside Steps 3-5, or a scope amendment homing them; "re-bless minus 4" is currently a promise without a work item.
2. **H-3** — the partials-gated re-derive: refute by constructing the partials=0 load that sets a spurious partner bit; also probe the carried "can a leg open without its partner" question (the atomic-legs evidence re-locate, banner `:47`) — if legs can single-open transiently, the XOR formula mis-derives mid-pair-OPEN (not just mid-pair-EXIT) states.
3. **Poison-fixture fidelity** — the landed fixture is hand-enumerated, not registry-driven, and not the literal A4 seed formula; does the locked gate ACCEPT it (it generated the held golden) or does Step 5 owe the projection? Also verify the new partner poison value collides with no existing per-field base.
4. **§ 3 assert reshapes** — refute the 2-version shape by checking whether ANY other compiled reference to the deleted macros exists outside tests (my grep says no: definitions + their dying serializers + tests + the ledger tool SOURCES only — verify independently).
5. **Wire-length invariance** — confirm net-0 truly holds (16B Money out / 16B in, header + OMS + Position blob untouched) ⇒ v11 golden len == 9968; a regen printing anything else is a smoking gun.
6. **AM-6 vs Class 4** — the sibling-distinction (M3) and whether the "CI guard" clause is satisfied by landed tooling or owes the struct↔registry coverage checker.
7. **Mask width** — re-verify [12,20) == sizeof(timestamp_us) survives v11 (no header change rides the bump; `:157-160` untouched by the delta).

## OPEN QUESTIONS (for Caramel at the dive)

- **OPEN-1:** Do the 4 cache-layout fixes belong to Steps 3-5 proper or a named close-gate leaf? (H-1 — the TUISharedState writer-group analysis + `swap_model_path_requested[16]` INBOUND are still listed as open dive questions, not work items.)
- **OPEN-2:** AM-4 fixture home (c) confirmed? And should the mid-pair fixture use the F-018 ULP-verified leg-A net as the parked-pnl golden value?
- **OPEN-3:** AM-6 guard identity — landed stack vs the literal struct-field-coverage checker (with the M3 allowlist)?
- **OPEN-4:** `NPF_PROJECT_POISON` (novel alternative i) — adopt at Step 5 or defer with the bounding comment?
- **OPEN-5:** Where do the F-096 Money legs ride — inside Commit 1 or their own commit? (Banner groups them in item 3; they're wire-inert, so any commit works — own commit is cleaner for Check L blast-radius.)

**Key files:** `/home/caramel/code/FoxML_Trader_v2/tests/sharded_snapshot_v10_golden.hpp` · `/home/caramel/code/FoxML_Trader_v2/tests/controller_test.cpp` · `/home/caramel/code/FoxML_Trader_v2/MemHeaders/NodeCtxPersistRegistry.hpp` · `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/ShardedSnapshotPersist.hpp` · `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/ControllerEventLoop.hpp` · `/home/caramel/code/tick-trader-percore-workspace/tools/{node_persist_layout.py, check_identifier_retirement.py, bless.py, check_cache_layout.py, identifier_ledger.txt, goldens/node_persist_layout.txt, lib/cache_layout_baseline.txt}` · `/home/caramel/code/FoxML_Trader_v2/.githooks/pre-commit` · `/home/caramel/code/FoxML_Trader_v2/build.sh` · `/home/caramel/code/FoxML_Trader_v2/plans/v5.15-live-readiness/subplans/2026-06-15-v5.15.5.F.4d.1.E.1.2-nodestate-soa-layout.md`
