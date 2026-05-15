# v5.15.5.F.4c.3 WIP2d-1.B.0b → Phase 3 handoff (post-compaction pickup)

**Generated:** 2026-05-15 (session compaction boundary)
**Engine HEAD:** `80449a5` (`feat/v5.15-live-readiness`, 12 commits ahead of origin)
**Workspace HEAD:** `7580a2d` (`main`, 1 commit ahead of origin)
**Tests:** GREEN — controller_test 3148, depth_recorder_test 856
**Tag status:** NOT yet tagged (ship in progress; tag at WIP2d-1 Phase 3+4 close OR at full ship close)

---

## 0. TL;DR — what just happened, what's next

Session pushed **6 engine commits** + **1 workspace commit** that finished the WIP2d
structural-primitive arc of `.F.4c.3`. Net effect: **15/15 tech debt classes closed
structurally** at this ship. The per-core cfg discipline framework is now structurally
complete — every future per-core field is a 1-row registry addition with X-macro
struct generation + bidirectional CI + meta-registry + compile-time bounds + branchless
dispatch.

**The next live work** is **WIP2d-1 Phase 3 + Phase 4** — the mechanical work the bit-split
closure UNLOCKED but did not complete: ~5–15 global-consumer sites reading per-core fields
still need Pattern 1/2/3 migration (Class 26 application). 3 sites already have explicit
`// WIP2d-1 Phase 3` markers in source. Then the remaining 6 sub-commits to close Step 2
(WIP2d-2 → WIP2h), then Steps 3/5/6/7/8/9 of `.F.4c.3` proper.

---

## 1. Read-first (10-minute load; deterministic for the engine + decision discipline)

### Always-loaded baseline (will already be in fresh context)
- `/home/caramel/code/CLAUDE.md` (workspace + projects)
- `/home/caramel/code/FoxML_Trader_v2/CLAUDE.md` (engine; symlinked to workspace)
- `/home/caramel/code/FoxML_Trader_v2/CLAUDE.local.md` (private overlay; sprint state)
- `~/.claude/projects/-home-caramel-code-FoxML-Trader-v2/memory/MEMORY.md` (memory index)

### Required reading for THIS pickup (in priority order)
1. **This handoff** (you're here)
2. **`plans/v5.15-live-readiness/subplans/2026-05-15-v5.15.5.F.4c.3-global-vs-per-core-registry-split.md`**
   — full plan; scroll to "Remaining sub-commits" table for execution order
3. **`tick-trader-percore-workspace/DESIGN_SPECS/cfg-scope-discipline.md`** — Class 25 +
   Class 26 (NEW); Pattern 1/2/3 decision criteria for Phase 3 sites
4. **`tick-trader-percore-workspace/DESIGN_SPECS/per-instance-registry-pattern.md`** — the
   broader framework this ship instantiates (per-core axis = first canonical application)
5. **`tick-trader-percore-workspace/DESIGN_SPECS/meta-registry-pattern-for-codebase-registry-discipline.md`**
   — Stage 3 ACTIVE; FOREACH_REGISTRY now codebase-wide (CoreFrameworks/MetaRegistry.hpp)
6. **`tick-trader-percore-workspace/DESIGN_SPECS/manual-fields-inventory-pattern.md`**
   — NEW this session; Section A/B documented exemptions
7. **`DOCS/MANUAL_FIELDS_INVENTORY.md`** (in engine repo) — current state: 12 Section A
   entries + 5 Section B entries (now auto-generated)
8. **`DOCS/RECURRING_BUG_PATTERNS.md`** — Class 25 + Class 26 (Class 26 codification TBD;
   first canonical examples are the Phase 3 work)
9. **`tick-trader-percore-workspace/DOCS/DESIGN_PHILOSOPHY.md`** — H17 STRONG codified;
   H15 pulled forward to .F.4c.3 (was pending .F.4d)

### Skim-only / on-demand
- `DESIGN_SPECS/type-trait-dispatch-via-tt-namespace.md` — 2nd canonical app landed at
  WIP2d-1 Phase 1 (if-constexpr filter on walkers)
- `DESIGN_SPECS/bitmap-overflow-protection-discipline.md` § Auto-generation via
  meta-registry — references FOREACH_PER_CORE_DOMAIN_BITMAP
- `DESIGN_SPECS/x-macro-registry-with-presence-dispatch.md`
- `DESIGN_SPECS/autopopulate-pattern-for-production-caller-class.md`

---

## 2. What landed this session (6 engine commits + 1 workspace commit)

| Commit | Sub-commit | Net effect |
|---|---|---|
| `94da090` | **WIP2d-0** | Structural fix primitive: X-macro struct gen (`PerCoreCfg<F>` body emitted from registry) + `FOREACH_MANUAL_PER_CORE_FIELD` exemption table + bidirectional CI (`tools/check_per_core_registry_integrity.py`) + `DOCS/MANUAL_FIELDS_INVENTORY.md` NEW. Closes Findings 1+2+3. |
| `4154009` | **WIP2d-0.B** | Consolidation polish: TYPE column folded into `FOREACH_PER_CORE_CFG_FIELD` (auxiliary table retired). `ControllerConfig.hpp` parallel arrays X-macro-generated. `FOREACH_PER_CORE_DOMAIN_BITMAP` meta-registry NEW (5 rows: align/domain/field/storage/child). CI regex updated for new layout. |
| `4c6b150` | **WIP2d-1.A** | Symbol axis MANUAL exemption — `core_symbol` row in `FOREACH_MANUAL_PER_CORE_FIELD` + `main.cpp` pre-EngineSharded_Run symbol uniformity check + `BinanceConfig.symbol` override. Partial advance of `.F.4c.3.A` plan; KIND_STRING migration + multi-symbol DataStream still deferred to post-.F.4e. |
| `ea08210` | **WIP2d-1 Phase 1+2** | Phase 1: `if constexpr (!HAS_SIDE_EFFECT)` filter uniformly applied to parser + copy walker + render fn (2nd canonical type-trait-dispatch app). `strategy` row added to `FOREACH_PER_CORE_CFG_FIELD` with HAS_SIDE_EFFECT. Phase 2: **18 mechanical migrations** (13 in EngineSharded, 5 in ControllerEventLoop per-core fns, 2 in BacktestSharded). 3 wrapper sites in ControllerEventLoop reverted with `// WIP2d-1 Phase 3` markers (no core_id in scope). |
| `357cfa3` | **WIP2d-1.B.0** | Tech debt full closure (4 of 5 shortsighted items + Phase 1 latent regression). Bit split: `HAS_SIDE_EFFECT` → `MANUAL_PARSER` + `NO_FLAT_FIELD` (semantic separation; copy walker now filters NO_FLAT_FIELD only — restored copy for 5 pre-existing HAS_SIDE_EFFECT rows that DO have flat fields). `FOREACH_PER_CORE_NO_FLAT_FIELD_SYNC` AUTOPOPULATE pattern (replaces ad-hoc manual sync). Self-contained includes for 5 domain registries. Compile-time size-bound static_assert (`calc_per_core_cfg_expected_payload_bytes<F>()` constexpr). |
| `80449a5` | **WIP2d-1.B.0b** | Shortsighted #2 close: `CoreFrameworks/MetaRegistry.hpp` NEW with `FOREACH_REGISTRY` (62 entries; 19 initial + 43 bulk). `tools/check_meta_registry.py` NEW (3 CI checks). Pulls H15 forward to .F.4c.3 (was pending .F.4d). **15/15 tech debt classes closed structurally.** |
| `7580a2d` (workspace) | DOC consolidation | 7 DESIGN_SPECS + DESIGN_PHILOSOPHY + 2 plan body files. |

---

## 3. Current task state (DO NOT LOSE THIS; rebuild verbatim in fresh session)

These are the TaskList rows. Status preserved exactly as of compaction boundary:

| # | Status | Subject |
|---|---|---|
| 1 | completed | Step 0.A — Tag rollback anchor + verify build baseline |
| 2 | completed | Step 0.C — Cfg field scope classification table |
| 3 | completed | Step 1 — Two-registry framework infrastructure |
| **4** | **in_progress** | **Step 2 — Cohort migration + ControllerConfig restructure** (PARTIAL) |
| 5 | pending | Step 3 — Parser state machine for [core N] sections |
| 6 | pending | Step 5 — Per-core stamp body emit + drift check |
| 7 | pending | Step 6 — Settings panel Global tab + per-core tabs + Reset/Modified UI |
| 8 | pending | Step 7 — Backtest path + ~414 test fixture migrations |
| 9 | pending | Step 8 — DESIGN_SPECs Stage 2→3 + documentation |
| 10 | pending | Step 9 — Verification gate + ship close |
| 11 | completed | WIP2d-0 — Structural fix primitive (X-macro struct gen + dual-X-macro + CI + inventory + Findings 1+2+3) |
| 12 | completed | WIP2d-0.B — Consolidation polish (single registry + meta-registry + ControllerConfig X-macro expansion + CI regex) |
| **13** | **in_progress** | **WIP2d-1 — Multi-core orchestration mechanical + Finding 1 (strategy registry row)** — Phase 1+2 LANDED (`ea08210`); **Phase 3+4 NOT COMMITTED** |
| 14 | completed | WIP2d-1.A — Symbol axis manual exemption (partial advance of .F.4c.3.A) |
| 15 | completed | WIP2d-1.B.0 — Tech debt full closure (bit split + AUTOPOPULATE + FOREACH_REGISTRY + compile-time bounds + gcc -E CI) |

**Step 2 (task #4)** is in_progress because it's a parent task covering WIP2d-* through
WIP2h. WIP2d-0/0.B/1.A/1.B.0/1.B.0b are done; WIP2d-1 Phase 3+4 + WIP2d-2/3/4 + WIP2e +
WIP2f/g/h all remain. See § 5 for the execution order.

**WIP2d-1 (task #13)** is in_progress because only Phase 1+2 landed. Phase 3+4 work
queued — see § 4 immediately below.

---

## 4. The mid-progress unit: WIP2d-1 Phase 3+4

This is what you'd pick up first in a fresh session.

### Phase 3 — Class 26 application (~3–4 hr, MED-HIGH risk per-site)

**Class 26 (NEW; codification pending)** = "global consumer reads per-core field". Surfaced
by Phase 1 bit-split: HAS_SIDE_EFFECT was overloaded — meant both "skip parser case" and
"skip flat-to-cores copy", which broke 5 fields silently. The bit split fixed the
walker semantics; what remains is migrating production READ sites that still hit
`cfg.X` (global) when they should be reading `cfg.cores[c].X`.

**Known Phase 3 sites:**

1. **`CoreFrameworks/ControllerEventLoop.hpp:3381`** — `// WIP2d-1 Phase 3` marker
2. **`CoreFrameworks/ControllerEventLoop.hpp:3661`** — `// WIP2d-1 Phase 3` marker
3. **`CoreFrameworks/ControllerEventLoop.hpp:3662`** — `// WIP2d-1 Phase 3` marker

   All 3 are WRAPPER fns (no `core_id` in scope). Resolution per `cfg-scope-discipline.md`
   Phase 3 § needs Pattern 1 (lift wrapper into per-core loop), Pattern 2 (push c into
   wrapper signature), or Pattern 3 (redundant early exit removal). Decide per site.

4. **OMS surface (fee_rate_maker / fee_rate_taker)** — global consumer reads `cfg.fee_rate_maker`
   directly. Pattern 1 candidate: add `per_core_fee_rate_maker[16]` + `per_core_fee_rate_taker[16]`
   to OMS state, populate from `cfg.cores[c].fee_rate_*` on reload, drainer indexes by
   order's originating core. Risk: cross-thread reload staleness (TECH_DEBT entry needed).

5. **EngineSharded boot defaults** — `bandit_algorithm`, `barrier_blend_mode`,
   `risk_degradation_curve` reads at boot. These are MANUAL_PARSER (no auto override path),
   so reads are global-by-design. Verify each site is correctly using flat field, not
   accidentally treating it as per-core.

**Decision criteria (from `cfg-scope-discipline.md` § Phase 3 design discussion):**
- **Pattern 1** (per-core storage on global consumer): use when consumer has stable
  thread/loop identity (drainer threads, async workers); cost = N×sizeof + reload staleness
  window
- **Pattern 2** (push c into signature): use when wrapper is easily lifted into per-core
  loop OR when call-graph is shallow
- **Pattern 3** (redundant early exit removal): use when global consumer's logic is
  load-bearing-AT-startup-only (e.g., boot validation that becomes per-core after init)

### Phase 4 — docs + CI (~30 min)

1. **`DOCS/RECURRING_BUG_PATTERNS.md`** — codify Class 26 (Global consumer reading per-core
   field). First canonical examples = the 3 ControllerEventLoop wrapper sites + OMS surface.
   Cross-reference: Class 25 (scope erosion in per-core consumer; reverse direction).
2. **`DOCS/TECH_DEBT.md`** — entry for per-core OMS reload staleness window (cross-thread
   reload pulls stale fee_rate after operator change; LOW severity; mitigation = make-stale-window-explicit).
3. **`tools/check_per_core_registry_integrity.py`** Check 7 — `HAS_SIDE_EFFECT` consistency
   audit (every NO_FLAT_FIELD row has `_no_flat_field` reason in MANUAL_FIELDS_INVENTORY.md).
4. **`tick-trader-percore-workspace/DESIGN_SPECS/cfg-scope-discipline.md`** — new §
   "Global consumer reading per-core field" + § "HAS_SIDE_EFFECT uniform skip" (semantic
   note: bit split rendered the term obsolete; redirect to MANUAL_PARSER / NO_FLAT_FIELD).

### Tests
Must stay GREEN at 3148 (controller_test) + 856 (depth_recorder_test). Phase 3 changes are
production-only; the test fixture migration is WIP2h, separate.

### Commit message convention
```
v5.15.5.F.4c.3 WIP2d-1.B.1: <Pattern N> migration in <site>
```

---

## 5. Remaining sub-commits to close Step 2 (execution order)

After WIP2d-1 Phase 3+4 commits as WIP2d-1.B.1 through WIP2d-1.B.4:

| Sub-commit | Scope | Effort | Risk |
|---|---|---|---|
| **WIP2d-2** | X-macro registries F7 amendment (~72 sites) — apply Class 25 closure to remaining per-core consumers across `Strategies/`, `ML_Headers/`, `Backtest/` | 4–6 hr | MED |
| **WIP2d-3** | Per-core consumers + `PortfolioController` legacy cores[0] migration (~88 sites). Verify `PortfolioController` is centralized legacy; flag for deprecation. | 3–5 hr | MED |
| **WIP2d-4** | GUI mirror migration (~51 sites — Settings panel reads `cfg.cores[c]` exclusively in per-core tabs) + boot exemption documentation | 2–3 hr | LOW |
| **WIP2e** | A2 bitmap-bool migration — **28 KIND_BOOL rows** + 3 standalone booleans uniform handling. New cohort migration to per-core registry. Sister to .F.4c (63-row KIND_INT/_BOOL bitmap dispatcher landing). | 2–3 hr | LOW-MED |
| **WIP2g + WIP2h** | Flag-day flat-field deletion (89 fields off `ControllerConfig<F>`) + **~414 test fixture migrations**. Use `replace_all` per-prefix (avoid substring bug per memory `feedback_avoid_substring_replace_all_on_member_access.md`). | 5–8 hr | HIGH |
| **WIP2f** | Legacy deletion: `PerCoreOverrides<F>` struct + `core_overrides[16]` array + `ControllerConfig_ResolveForCore` fn — replaced by direct `cfg.cores[c].X` reads. | 1 hr | LOW |
| **Step 3** | `[core N]` section parser state machine for per-core override syntax in engine.cfg | 2–3 hr | MED |
| **Step 5** | Per-core stamp body emit + drift check (HMAC chain extension over cores[16]) | 3–4 hr | MED-HIGH |
| **Step 6** | Settings panel Global tab + per-core tabs + Reset/Modified UI (16 tabs × ~92 fields) | 4–6 hr | MED |
| **Step 7** | Backtest path equivalent — `BacktestSharded` walks `cfg.cores[c]` cleanly | 1–2 hr | LOW |
| **Step 8** | DESIGN_SPECS Stage 2→3 promotions + docs + CHANGELOG | 1–2 hr | LOW |
| **Step 9** | Verification gate + ship close (`/parity-check + /trace-deps + /dod-audit + /test-strength-audit + /ml-audit` parallel) + Version.hpp bump `5.15.5.F.4c.1` → `5.15.5.F.4c.3` + tag | 2 hr | LOW |

**Total remaining effort:** ~35–55 hr depending on Phase 3 decisions + WIP2h test sweep.

---

## 6. Verification commands (run first thing in fresh session)

```bash
cd /home/caramel/code/FoxML_Trader_v2

# Verify engine HEAD
git log --oneline -7
# Expected top line: 80449a5 v5.15.5.F.4c.3 WIP2d-1.B.0b: FOREACH_REGISTRY codebase-wide meta-registry...

# Verify tests still GREEN
./build.sh test 2>&1 | tail -5
./build/controller_test 2>&1 | tail -5
./build/depth_recorder_test 2>&1 | tail -5
# Expected: 3148 + 856 passing

# Verify CI scripts pass
python3 tools/check_per_core_registry_integrity.py
python3 tools/check_meta_registry.py
# Expected: all checks PASS

# Find Phase 3 markers (3 sites)
grep -n "WIP2d-1 Phase 3" CoreFrameworks/ControllerEventLoop.hpp
# Expected: 3 lines with markers
```

---

## 7. Sprint state snapshot (verbatim from CLAUDE.local.md "Current sprint state" table)

| Field | Value |
|---|---|
| Sprint | `v5.15-live-readiness` |
| Most recent ship | `v5.15.5.F.4c.1` — ImGui widget-ID structural fix + 18-row STAMP_BOUND cohort + Class 24 codification (2026-05-15; engine `88043ea` + tag) |
| In-progress ship | `v5.15.5.F.4c.3` — Architectural cfg split. Engine HEAD `80449a5`. **15/15 tech debt classes closed structurally.** Tests GREEN 3148+856. Not yet tagged. |
| Next ship after `.F.4c.3` finish | `v5.15.5.F.4c.2` — bandit 5-state ghost-training + per-core override generalization |
| Ship after `.F.4c.2` | `v5.15.5.F.4d` — wire-format framework + structural closure ship |
| Ship after `.F.4d` | `v5.15.5.F.4e` — KIND_STRING + KIND_FILE_PATH + 5 GUI metadata derived filters |

---

## 8. Tech debt closure summary (15/15 structurally closed at .F.4c.3)

These bug classes are now structurally closed (compile-time / CI-enforced):

| # | Class | Closure mechanism |
|---|---|---|
| 1 | Auxiliary table drift (FOREACH_PER_CORE_FIELD_TYPE) | Single registry; TYPE column on FOREACH_PER_CORE_CFG_FIELD; auxiliary retired |
| 2 | Manual struct field maintenance | X-macro struct gen via EMIT_PER_CORE_CFG_STRUCT_FIELD |
| 3 | Scattered parallel arrays in ControllerConfig | X-macro expansion via EMIT_PER_CORE_FLAT_FIELD |
| 4 | Hardcoded bitmap whitelist | FOREACH_PER_CORE_DOMAIN_BITMAP meta-registry (5 rows) |
| 5 | HAS_SIDE_EFFECT semantic overload | Bit split → MANUAL_PARSER (1u<<10) + NO_FLAT_FIELD (1u<<12) |
| 6 | Phase 1 latent regression (5 fields not copied) | Bit split semantic correction; copy walker filters NO_FLAT_FIELD only |
| 7 | Ad-hoc manual sync code | FOREACH_PER_CORE_NO_FLAT_FIELD_SYNC AUTOPOPULATE |
| 8 | Include-order brittleness | Self-contained CfgFieldRegistry.hpp includes |
| 9 | Bitmap overflow risk | Compile-time `static_assert(FOREACH_X_COUNT_VALUE <= sizeof(T) * 8)` (H20 candidate) |
| 10 | CI regex heuristic fragility | Compile-time `calc_per_core_cfg_expected_payload_bytes<F>()` constexpr static_assert |
| 11 | Documentation-only meta-registry | FOREACH_REGISTRY codebase-wide; tools/check_meta_registry.py CI |
| 12 | Anti-pattern 1 (boot validation walks flat fields) | EngineSharded boot now walks `cfg.cores[c].risk_degradation_curve` exclusively |
| 13 | Class 23 (type-erased reinterpret_cast dispatch) | Closed at .F.4b via `tt::` namespace; 2nd canonical app at WIP2d-1 Phase 1 if-constexpr filter |
| 14 | Class 25 (scope erosion in per-core consumer) | Closed at WIP2c.2 via single-param `const PerCoreCfg<F>* core_cfg` discipline |
| 15 | Manual fields bypass (Section A 12 entries) | FOREACH_MANUAL_PER_CORE_FIELD documented exemption + MANUAL_FIELDS_INVENTORY.md Section A/B inventory |

**Phase 3 work activates Class 26** (NEW; codification pending) — global consumer reading
per-core field. Currently UNCLOSED but UNBLOCKED — the framework is in place; per-site
Pattern 1/2/3 decisions are mechanical from here.

---

## 9. Things in flight / context the user reminded me about

Per Caramel's last message ("dont forget the task list and stuff in progress, we didnt
manage to make a full commit, so it was like half of one or mid progress"):

- **WIP2d-1 is half-committed.** Phase 1+2 in `ea08210`; Phase 3+4 NOT committed.
  Phase 3 has 3 explicit `// WIP2d-1 Phase 3` markers in source code as anchors.
- **Step 2 (task #4) is the umbrella in_progress task.** Many sub-commits remaining
  before it can flip to completed.
- **Tests at 3148 are passing despite Phase 3 incomplete** — that's because no consumer
  currently reads `cfg.cores[c].fee_rate_maker` (they all read `cfg.fee_rate_maker`).
  Phase 3 wires up that path; test fixtures stay on flat fields until WIP2h.
- **9 transient test fixtures** added at WIP2c.3 use the `ControllerConfig_PopulateCoresFromFlat`
  band-aid. These will be replaced at WIP2h with direct `cfg.cores[0].X` writes (mechanical).
- **No tag yet on `.F.4c.3`.** Don't tag until WIP2d-1 Phase 3+4 OR full ship close, per
  operator preference. Version.hpp still reads `5.15.5.F.4c.1` (NOT bumped).

---

## 10. Skills + tools to know in fresh session

| Tool | Purpose |
|---|---|
| `tools/check_per_core_registry_integrity.py` | 6 checks (incl. anti-pattern 1 scan). Run after every WIP2d-* commit. |
| `tools/check_meta_registry.py` | 3 CI checks; FOREACH_REGISTRY codebase ↔ definitions ↔ LEVEL/PARENT discipline. |
| `./build.sh test` | Engine + controller_test build (ANSI + zero deps). |
| `./build/controller_test` | 3148 tests. |
| `./build/depth_recorder_test` | 856 tests. |
| `/parity-check + /trace-deps + /dod-audit + /test-strength-audit + /ml-audit` | Pre-ship audit gate; run in parallel via Agent tool before Step 9. |
| `/handoff` | Generate handoff prompt (skill auto-loads MEMORY.md + plan + DESIGN_PHILOSOPHY narrative sections). |

---

## 11. Operator preferences (verbatim from memory; honor these in fresh session)

- Address user as **Caramel / she / her**, not "the operator" (`feedback_address_user_as_caramel`)
- **No `AskUserQuestion` modal widgets** — present options inline (`feedback_no_question_boxes`)
- **Defer is last-ditch**, never effort-avoidance (`feedback_no_defer_for_effort`)
- **After pre-coding audits, ALWAYS consult before coding** (`feedback_consult_on_audit_findings`)
- **Don't measure structural work by LOC** — count classes closed + patterns codified +
  future-mechanicalization (`feedback_dont_measure_structural_work_by_loc`)
- **Boundary-stable refactors** preferred (`feedback_reduce_touch_sites`)
- **Structural fix preferred for recurring bug classes** (`feedback_structural_fix_for_recurring_class`)
- **Don't ship MVP for plumbing/refactor work** — full documented design
  (`feedback_no_mvp_for_plumbing_only_for_unknown_unknowns`)
- **Bump Version.hpp on every ship** (`feedback_bump_version_per_ship`) — currently
  pending the bump from `5.15.5.F.4c.1` → `5.15.5.F.4c.3` at ship close
- **Engine CLAUDE.md is a symlink** to workspace; `CLAUDE.local.md` is NOT
  (`project_engine_clauder_md_is_symlink`)
- **Prefer ripgrep** over grep (`feedback_prefer_ripgrep`)
- **Avoid substring `replace_all` on `cfg.X`** — mangles `ctrl->config.X`; use
  per-prefix targeted edits OR longest-prefix-first (`feedback_avoid_substring_replace_all_on_member_access`)
- **Compaction degrades** — verify handoffs against current code; don't trust counts/sigs
  blindly (`feedback_compaction_degrades_treat_handoffs_as_hints`)
- **Never push to remote unless explicitly asked.**

---

## 12. First action in fresh session

```
1. Run § 6 verification commands. Confirm engine HEAD = 80449a5, tests GREEN at 3148+856.
2. Read § 1 priority list (cfg-scope-discipline.md, plan body, MANUAL_FIELDS_INVENTORY.md).
3. Rebuild TaskList per § 3 table.
4. Greenlight Phase 3 site-by-site decision (don't auto-implement) — open
   ControllerEventLoop.hpp at the 3 marker lines, propose Pattern 1/2/3 per site,
   then surface to Caramel for greenlight before coding.
```

End of handoff.
