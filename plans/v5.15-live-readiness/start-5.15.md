# start-5.15 — v5.15.0 coding pickup handoff

**Created:** 2026-05-12 (after plan drafting + pre-coding audits + Step 0 inventory)
**Target sub-ship:** v5.15.0.A — ModelHandle X-macro migration (then .B parser refactor, .C tests)
**Branch:** `feat/v5.15-live-readiness`
**HEAD:** `1752fde` (`v5.14.post1` — `train_model_worker_fn` stamp body migration gap fix)
**Pre-tag rollback anchor:** `pre-v5.15.0` = `1752fde` (same as HEAD; no v5.15.0 code shipped yet)
**Sprint baseline:** `v5.14` (the sealed predecessor sprint)
**Sprint MASTER:** `plans/v5.15-live-readiness/MASTER.md`
**This ship's plan:** `plans/v5.15-live-readiness/subplans/2026-05-12-v5.15.0-modelhandle-migration.md`
**Sprint kickoff handoff:** `plans/v5.15-live-readiness/handoffs/2026-05-12-v5.15-kickoff-handoff.md` (predecessor; plan-only)

---

## Paste this prompt into a fresh Claude Code session to start v5.15.0 coding

```
I'm picking up v5.15.0 — ModelHandle X-macro migration + verify_model_stamp
parser refactor — for the v5.15 live-readiness hardening sprint on
FoxML_Trader_v2. This is a fresh context window; do NOT trust any
prior-session memory. Verify everything against current code.

Caramel is the operator (she/her). Address her as Caramel. No
AskUserQuestion modals — present options inline. After pre-coding
checks, ALWAYS consult before coding (don't auto-proceed).

## Pre-flight state (verified 2026-05-12 at handoff write time)

- Branch `feat/v5.15-live-readiness` exists + checked out
- HEAD = `1752fde` (v5.14.post1)
- Tag `pre-v5.15.0` exists (rollback anchor; same commit as HEAD)
- Tag `v5.14.post1` resolves to `1752fde` (verified)
- Working tree clean (only `context_cont.md` untracked — stale v5.14-era
  doc, ignore)
- Version.hpp says "5.14.post1"
- Tests baseline: 2904 passing at v5.14.post1
- `tests/controller_test.cpp` is 23,691 lines (over the 5k-line discipline
  threshold from CLAUDE.md test-split rule, but split is queued as v5.11.35
  sub-ship — NOT v5.15 scope)

## Sprint state recap

v5.15 is live-readiness hardening + ModelHandle structural unification.
5 sub-ships planned; v5.15.0 is FIRST (HIGH-RISK; foundational —
v5.15.1 + v5.15.2 + v5.15.3 consume the unified ModelHandle.has_flags).

| Sub-ship | LOC | Time | Risk | Status |
|---|---|---|---|---|
| **v5.15.0** | ~580 | 5-6h | HIGH | THIS SHIP. Plan drafted; pre-coding audits done; .A Step 0 inventory done; ready for .A Step 1 |
| v5.15.1 | ~220 | 3-4h | LOW | not started |
| v5.15.2 | ~330 | 4-5h | MEDIUM | not started |
| v5.15.3 | ~200 | 3.5-4h | MEDIUM | not started |
| v5.15.4 | ~330 | 5-6h | MEDIUM+ | not started |

**v5.15.0 absorbs:**
- TECH_DEBT-014 (ModelHandle X-macro migration; the actual ship)
- TECH_DEBT-003 (verify_model_stamp parser refactor; .B half)

## Step 0 — orient + verify state (BEFORE planning anything)

Run in parallel:

```bash
cd /home/caramel/code/FoxML_Trader_v2 && cat Version.hpp | grep ENGINE_VERSION_STRING
cd /home/caramel/code/FoxML_Trader_v2 && git log --oneline -5
cd /home/caramel/code/FoxML_Trader_v2 && git tag --sort=-creatordate | head -8
cd /home/caramel/code/FoxML_Trader_v2 && git status -s
cd /home/caramel/code/FoxML_Trader_v2 && git branch --show-current
```

Expected:
- ENGINE_VERSION_STRING = "5.14.post1"
- latest commit = "1752fde v5.14.post1 — train_model_worker_fn stamp body migration gap fix"
- tags include `pre-v5.15.0`, `v5.14.post1`, `v5.14`, `v5.14.11`, ...
- branch = "feat/v5.15-live-readiness"
- status clean (only `?? context_cont.md` is OK; that's a stale doc)

If ANY of these don't match — STOP. Surface the discrepancy to Caramel
before proceeding.

## Step 1 — load required reading (in parallel)

These three are ALWAYS-LOAD:
- `CLAUDE.md` (public project instructions; items 1-27)
- `CLAUDE.local.md` (private overlay; going-forward rules)
- `~/.claude/projects/-home-caramel-code-FoxML-Trader-v2/memory/MEMORY.md`
  (auto-memory index — load each linked file as relevant)

This ship's plan + parent context:
- `plans/v5.15-live-readiness/MASTER.md` (sprint master)
- `plans/v5.15-live-readiness/subplans/2026-05-12-v5.15.0-modelhandle-migration.md` (THE plan for this ship)
- `plans/v5.15-live-readiness/working/2026-05-12-v5.15.0-has-field-inventory.md` (the Step 0 inventory from prior session — 14 has_* fields × 84 caller sites)
- `plans/plan_checks/plan-check-2026-05-12-v5.15.md` (sprint plan-check synthesis; YELLOW → GREEN after amendments)

Pre-coding audit reports (review these before coding to know what was caught):
- `plans/plan_checks/parity-check-2026-05-12-v5.15.md`
- `plans/plan_checks/dod-audit-2026-05-12-v5.15.md`
- `plans/plan_checks/readiness-2026-05-12-v5.15.md`
- `plans/plan_checks/trace-deps-2026-05-12-v5.15.md`
- `plans/plan_checks/merge-scan-2026-05-12-v5.15.md`

CLAUDE.local.md required reading (for performance-sensitive code):
- `DOCS/STRATEGY_AND_CODING_RULES.md` (11 strict invariants)
- `plans/_cross-cutting/2026-05-06-latency-path-discipline.md` (7 latency-path rules)
- `DOCS/LATENCY_OPTIMIZATION_AUDIT.md` (relevant parts for stamp/ML surface — Parts 4, 8, 11)

DESIGN_SPECS that v5.15.0 explicitly cites (read before .A Step 1):
- `tick-trader-percore-workspace/DESIGN_SPECS/README.md` (catalog + "I need to..." discovery)
- `DESIGN_SPECS/framework-patterns/heterogeneous-registry-pattern.md` (X-macro with presence-dispatch — the cited "x-macro-registry-with-presence-dispatch.md" maps to this file)
- `DESIGN_SPECS/framework-patterns/bitmap-flag-api.md` (BITMAP_* macros; bit-packed has_flags discipline)
- `DESIGN_SPECS/framework-patterns/autopopulate-pattern-for-production-caller-class.md` (STAMP_*_AUTOPOPULATE companion)
- `DESIGN_SPECS/wire-format-patterns/pre-post-cfg-registry-split-for-emit-order-preservation.md` (the FOREACH_STAMP_BOUND_MODEL_CONST_PRE_CFG / _POST_CFG split this ship preserves)
- `DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md` (HMAC chain byte-equivalence)
- `DESIGN_SPECS/wire-format-patterns/struct-padding-determinism-pattern.md` (alignas + explicit `_padding = 0`)
- `DESIGN_SPECS/data-disciplines/per-snapshot-cluster-layout-pattern.md` (alignas(64) + hot/warm/cold clusters)
- `DESIGN_SPECS/meta-disciplines/structural-fix-preferred-decision-framework.md` (Class 18 mirror — both sides of source/sink boundary)
- `DESIGN_SPECS/audit-methodologies/audit-driven-pre-coding-gate.md` (already-applied to this ship)

CLAUDE.md items relevant: **12** (display↔execution invariant), **13**
(X-macro registry), **15** (parity-tested-by-construction), **18**
(slow-path latency discipline), **19** (structural fix preferred), **20**
(bit-packed flag storage), **21** (AUTOPOPULATE companion), **22**
(PRE/POST split for canonical-emit-order), **23** (type-trait dispatch
via templated helpers, NOT non-template `if constexpr`), **27** (struct
padding determinism).

## Step 2 — re-verify plan against current HEAD

The plan was drafted **today** (2026-05-12) and codebase has NOT moved
since. The Step 0 inventory at
`plans/v5.15-live-readiness/working/2026-05-12-v5.15.0-has-field-inventory.md`
was generated at HEAD = 1752fde (verified).

**Stale-claim audit re-check (cheap; 5 min):**

```bash
# Confirm ModelHandle still has 14 uint8_t has_* fields (NOT 16 — earlier handoff was off)
rg -n "^\s*uint8_t\s+has_" /home/caramel/code/FoxML_Trader_v2/ML_Headers/ModelInference.hpp
# Expected: 14 entries

# Confirm FOREACH_STAMP_BOUND_MODEL_CONST_PRE_CFG / _POST_CFG locations
rg -n "FOREACH_STAMP_BOUND_MODEL_CONST_PRE_CFG\|FOREACH_STAMP_BOUND_MODEL_CONST_POST_CFG\|STAMP_MODEL_CONST_AUTOPOPULATE_ONE" /home/caramel/code/FoxML_Trader_v2/ML_Headers/StampBoundModelConstRegistry.hpp | head -10
# Expected: PRE_CFG at :267, POST_CFG at :377, AUTOPOPULATE at :601, AUTOPOPULATE_ONE at :680

# Confirm verify_model_stamp + stamp_write_for_model still exist + sizes
wc -l /home/caramel/code/FoxML_Trader_v2/ML_Headers/ModelInference.hpp
# Expected: ~1994 lines (NOT ~2500+ as MASTER cold-pickup §7 said; corrected to ~2000 per /plan-check LOW-1)

# Confirm BacktestEngine RFV emit chain
sed -n '1039,1045p' /home/caramel/code/FoxML_Trader_v2/Backtest/BacktestEngine.hpp
# Expected: Backtest_RunFullValidation header at :1039 (NOT :1147 — that was a stale claim; /readiness H.2)

# Confirm BacktestPanels train_model_worker_fn
grep -n "train_model_worker_fn" /home/caramel/code/FoxML_Trader_v2/Backtest/BacktestPanels.hpp | head -3
# Expected: around :2847 (NOT :3206 — stale; /readiness H.1)
```

If any of these don't match, surface the drift to Caramel before .A
Step 1.

**Already-resolved drift items (per `plan-check-2026-05-12-v5.15.md`):**
- HIGH-1: ControllerConfigParser.hpp ✗ doesn't exist → use ControllerConfig.hpp (v5.15.2 concern)
- HIGH-2/3: core_strategy_explicit + ControllerConfigKeyExplicit tracking infra needs addition (v5.15.2/.4 concern)
- HIGH-4: EngineSharded_HotSwapSingleZoo doesn't exist as named fn (v5.15.4 concern)
- HIGH-5: v5.15.3 decoupling-roadmap breadcrumb out of scope (already amended)

None of HIGH-1 through HIGH-5 affect v5.15.0. Sprint composes GREEN
post-amendments for the surface this ship touches.

## Step 3 — pre-coding audit gate STATUS

Already done at plan-drafting time. 5 audits dispatched in parallel via
Agent + Explore subagents; reports + synthesis at `plans/plan_checks/`.
Convergent findings:

| Audit | Verdict | Key finding affecting v5.15.0 |
|---|---|---|
| /parity-check | GREEN for v5.15.0; PARITY-020/021/022/023 surface OUTSIDE .0 | v5.15.0 preserves HMAC byte-equivalence by appending nothing + restructuring storage only |
| /trace-deps | HIGH-1 caught 2 missed grep targets — ModelValidation.hpp (7 sites) + FeatureRegistryOverlay.hpp:158. Inventory file includes both. | Step 0 inventory comprehensive |
| /readiness | H.1/H.2 file:line corrections (BacktestPanels train_model_worker_fn :3206 → :2847; BacktestEngine RFV :1147 → :1039) | Plan amended |
| /dod-audit | HIGH-2: Use **Option C** — REUSE `MASK_STAMP_HAS_*` constants from ModelStampResult for ModelHandle.has_flags. Don't duplicate. | Decision LOCKED — see .A Step 1 below |
| /merge-scan | Drift-detection reuse opportunity for v5.15.1 (consolidate with existing CoreModelZoo.hpp:206-225 CFG drift loop) | Affects v5.15.1, not .0 |

**Verdict: GREEN. v5.15.0 ready to code.**

## Step 4 — design philosophy reminders (CLAUDE.local.md + memory)

- **Defer is last-ditch, never effort-avoidance** (memory:
  feedback_no_defer_for_effort). v5.15.0 is HIGH-RISK because of caller-
  site count (84). Don't downgrade to "migrate the easy 20 sites + defer
  the rest" — execute the full per-site cross-off discipline like
  v5.14.8.A.6.
- **Structural fix > direct patch** (CLAUDE.md item 19). v5.15.0
  extinguishes the Class 18 mirror at the source/sink boundary —
  ModelHandle structure (sink) + verify_model_stamp parser (source) both
  become registry-driven together. Do NOT split into two ships.
- **No MVP for plumbing/refactor work** (memory:
  feedback_no_mvp_for_plumbing). Ship full design: complete migration +
  full parser data-driven dispatch + full HMAC byte-equivalence tests +
  legacy-stamp load test.
- **Boundary-stable refactor preferred** (CLAUDE.local.md 2026-05-06).
  But this ship is exactly the case where the boundary type IS the gap —
  ModelHandle's 14-has_* layout is what we're migrating. So cascade is
  correct + intentional. Call it out in the postmortem.
- **Hot path UNTOUCHED.** ModelHandle reads happen on slow-path
  inference dispatch (existing consumer). Migration reshapes reads from
  `if (h.has_X)` to `BITMAP_IS_SET(h.has_flags, MASK_X)` — same cycle
  count. Verify with `tools/calls_graph_diff.sh` + diff of `BG_Evaluate
  / SG_Evaluate / ExecutionCore_Tick` (must be zero changes).
- **HMAC chain byte-equivalence.** This is the load-bearing risk.
  Synthesize representative pre/post-migration ModelHandle; emit stamp
  body via `stamp_write_for_model`; SHA-256 must be byte-IDENTICAL to
  v5.14.post1 baseline (the migration is storage-only, not wire-format).
  See `wire-format-byte-preservation-discipline.md`.
- **Surface G forward-compat preserved.** No MODEL_FORMAT_VERSION bump.
  v5.14-era stamps MUST load cleanly on v5.15 engine (legacy stamps lack
  some `has_*` flags → default 0 → effective legacy behavior).
- **Per-site cross-off discipline.** Inventory file has 84 sites; each
  site gets crossed off as migrated. Final list MUST be empty before .A
  closes. This prevents v5.14.post1-class missed-site recurrence.
- **Bump Version.hpp.** 5.14.post1 → 5.15.0 in the same commit as the
  ship tag.
- **Don't use AskUserQuestion** (memory: feedback_no_question_boxes).
  Plain inline text.
- **Evaluate options on robustness + latency + design philosophy, NOT
  time** (memory: feedback_evaluate_options_on_robustness_latency_design_not_time).
- **After audit findings, ALWAYS consult** (memory:
  feedback_consult_on_audit_findings). Don't auto-proceed.
- **Don't substring-replace_all on member access** (memory:
  feedback_avoid_substring_replace_all_on_member_access). Migration is
  84 sites with `(.|->)has_X` patterns; inventory both dot+arrow shapes
  and migrate per-Edit-targeted blocks, NOT global replace_all.

## Step 5 — next concrete move

### v5.15.0.A — ModelHandle struct rewrite (3-4 hr; ~400 LOC)

**Step 0 DONE.** Inventory at
`plans/v5.15-live-readiness/working/2026-05-12-v5.15.0-has-field-inventory.md`
— 14 has_* fields × 84 caller sites, comprehensive coverage including
ModelValidation.hpp (7 arrow-access) + FeatureRegistryOverlay.hpp:158
(legacy silent-skip) that earlier narrower grep missed.

**Step 1 (NEXT) — design has_* bit positions + MASK_* constants.**

DECISION LOCKED via /dod-audit HIGH-2: **Option C — REUSE
MASK_STAMP_HAS_* bit positions from ModelStampResult.** Do NOT create a
separate MASK_HANDLE_HAS_* namespace. The parser refactor (.B) writes
BOTH `ModelStampResult.has_flags` AND `ModelHandle.has_flags` from the
SAME dispatch table row — aligned bit positions mean one mask column.

Concrete macro shape:

```cpp
// In ML_Headers/ModelInference.hpp near ModelHandle declaration:
// v5.15.0 — ModelHandle.has_flags uses SAME bit positions as
// ModelStampResult.has_flags (Option C from /dod-audit; closes the
// dispatch-table-double-write asymmetry that /dod-audit HIGH-2 flagged).
#define HANDLE_HAS(h, name)  BITMAP_IS_SET((h).has_flags, MASK_STAMP_HAS_##name)
#define HANDLE_SET(h, name)  BITMAP_SET((h).has_flags, MASK_STAMP_HAS_##name)
#define HANDLE_CLR(h, name)  BITMAP_CLR((h).has_flags, MASK_STAMP_HAS_##name)
```

**Step 2 — struct rewrite via FOREACH expansion.**

```cpp
struct alignas(64) ModelHandle {
    // HOT CLUSTER (cache line 1):
    void *handle;                          // 8 B
    int   backend;                         // 4 B
    int   num_features;                    // 4 B
    int   num_outputs;                     // 4 B
    int   buy_class_idx;                   // 4 B
    int   normalizer;                      // 4 B
    double normalizer_param;               // 8 B
    uint64_t has_flags;                    // 8 B  (REPLACES 14 uint8_t has_*)
    int   scaler_load_failed;              // 4 B
    int32_t _hot_pad0 = 0;                 // 4 B  (explicit padding per item 27)
    // Used: 56 B; reserved: 8 B (next slot in line 1)

    // WARM CLUSTER:
    tt::FeatureStandardizer scaler;        // ~600 B

    // STAMP-DERIVED VALUE FIELDS (auto-generated via FOREACH):
    FOREACH_STAMP_BOUND_MODEL_CONST(EXPAND_HANDLE_FIELD)

    // COLD CLUSTER:
    char model_path[256];
    char training_fingerprint[65];
    char run_name[64];
};
static_assert(sizeof(ModelHandle) % 64 == 0, "ModelHandle cache-line sized");
```

**Step 3 — accessor macros.** HANDLE_HAS / HANDLE_SET / HANDLE_CLR
already shown above. Place in `ML_Headers/ModelInference.hpp` near struct.

**Step 4 — migrate the 84 caller sites.** Use the inventory file as the
checklist. Cross each off as migrated. Cohort by file for batched Edits:
- `CoreFrameworks/EngineSharded.hpp` (boot WARN comparisons; ~5 sites)
- `CoreFrameworks/ModelValidation.hpp` (post-load validate; ~7 sites)
- `ML_Headers/CoreModelZoo.hpp` (TryLoadRole post-verify copies + 2 misc; ~14 sites)
- `ML_Headers/ModelInference.hpp` (verify_model_stamp populator; ~14 sites — heavily refactored further in .B)
- `ML_Headers/StampBoundModelConstRegistry.hpp` (emit walks; ~9 sites — auto-generated via FOREACH already, but mask usage updates)
- `ML_Headers/FeatureRegistryOverlay.hpp:158` (1 legacy-stamp silent-skip)
- `tests/controller_test.cpp` (test fixtures; ~30 sites — bulk of mechanical work)

Migration pattern per site:
- `h.has_X` → `HANDLE_HAS(h, X)` (read context — wraps in `!= 0` predicate)
- `h.has_X = 1` → `HANDLE_SET(h, X)`
- `h.has_X = 0` → `HANDLE_CLR(h, X)`
- `.has_X = 1` in struct-init → keep as `.has_flags = MASK_STAMP_HAS_X | ...` aggregate OR set after construction

**Substring-replace_all warning** (memory:
feedback_avoid_substring_replace_all_on_member_access): `has_X` substring
appears in `.has_X` AND `->has_X` AND `&p.has_X` etc. Use Edit with full
surrounding context per site, NOT global replace_all. Inventory captures
all variations.

**Step 5 — DOD audit pass.** Run `/dod-audit` after migration completes
to verify:
- `alignas(64)` preserved on ModelHandle
- `sizeof(ModelHandle) % 64 == 0` static_assert passes
- Hot cluster (first 64 B) contains most-read fields
- Explicit padding fields where gaps exist
- No residual `uint8_t has_*` fields

### v5.15.0.B — verify_model_stamp parser refactor (1-1.5 hr; ~150 LOC)

After .A closes: refactor ~700 LOC if-else chain at verify_model_stamp
into data-driven dispatch table walking
`FOREACH_STAMP_BOUND_MODEL_CONST` + `FOREACH_STAMP_BOUND_CFG`. Uses the
EXISTING `tt::stamp_parse_field<T>` templated helper at
`ML_Headers/StampBoundModelConstRegistry.hpp:680+` (per CLAUDE.md item 23).

See sub-plan .B section for full design + EXPAND_PARSER_ROW macro shape.

### v5.15.0.C — HMAC tests + byte-equivalence (30-60 min; ~80 LOC tests)

Three tests:
1. **HMAC round-trip on migrated ModelHandle** — synth all 14 flags set
   + values; emit stamp body; SHA-256 must match v5.14.post1 baseline
2. **Legacy-stamp forward-compat** — load v5.14-era stamp on v5.15
   engine; verify clean load with 14 has_* flags preserved
3. **Parser dispatch table verification** — assert parser table walks
   EVERY FOREACH registry entry (no missed keys)

### Pre-.A consult with Caramel

Before writing code, present:
1. Confirmation that Step 0 inventory matches current HEAD (re-run from
   Step 2 above)
2. Option C bit-position reuse plan (LOCKED but flag for Caramel anyway)
3. .A → .B → .C sub-tag plan
4. Estimated 5-6 hr total

Wait for greenlight. Don't auto-proceed (memory:
feedback_consult_on_audit_findings).

## Step 6 — TECH_DEBT / PARITY in surface area

| Entry | Status | v5.15.0 disposition |
|---|---|---|
| **TECH_DEBT-003** (verify_model_stamp parser refactor) | OPEN | **CLOSE in .B** |
| **TECH_DEBT-014** (ModelHandle migration) | OPEN | **CLOSE in .A** |
| TECH_DEBT-029 (source file length reduction) | OPEN | Trigger: ModelInference.hpp is 1994 lines today; .B parser refactor may push past 5k. Watch the line count; if .B grows the file > 5k, defer reduction to a follow-up ship (file-split / extract verify_model_stamp). NOT v5.15.0 scope. |
| TECH_DEBT-036 (architectural-field AUTOPOPULATE redesign) | NEW; created during v5.15.3 audit (PARITY-022) | NOT v5.15.0 scope. Quarantine of broken `STAMP_MODEL_CONST_AUTOPOPULATE` happens at v5.15.3.A Step 0.5. Don't touch the macro in v5.15.0. |
| PARITY-020 / -021 / -022 / -023 | OPEN | OUTSIDE v5.15.0 surface. Closure happens in v5.15.3 + v5.15.4. |

**Auto-write contract** (CLAUDE.local.md 2026-05-09): when .A/.B close,
update TECH_DEBT-003 + TECH_DEBT-014 in
`tick-trader-percore-workspace/DOCS/TECH_DEBT.md` to ✅ CLOSED with ship
+ closure form. Don't defer the ledger update.

**DOCS/ symlinks editing** (v5.14.10 postmortem surprise): many
`DOCS/*.md` are symlinks to workspace. `Edit` REFUSES to write through
symlinks. ALWAYS check `readlink -f path` before editing; if it resolves
to workspace, edit the workspace path directly. Symlinked: TECH_DEBT,
PARITY_ISSUES, HOT_PATH_CHANGELOG, most CLAUDE_*.md, RECURRING_BUG_PATTERNS,
EASY_ADDITIONS_INVARIANTS.

## Step 7 — verification gate (sub-ship close)

Per v5.15.0 sub-plan §Verification gate:

- [ ] All tests pass (~2904 + ~20 new for migration coverage)
- [ ] `./build.sh test gui suite tsan asan all` GREEN (NEW post-
      v5.14.post1 discipline — wider build catches BacktestPanels +
      GUI panel consumers that test target skips)
- [ ] **HMAC byte-equivalence test (.C Test 1)** — SHA-256 of synth
      stamp body matches v5.14.post1 baseline OR documented difference
      with explicit registry rationale
- [ ] **Legacy-stamp load test (.C Test 2)** — v5.14-era stamp loads
      cleanly with all has_* flags preserved
- [ ] **Parser dispatch table verification (.C Test 3)** — table walks
      every FOREACH registry entry
- [ ] `/parity-check` GREEN — ModelHandle migration preserves train-
      serve identity
- [ ] `/dod-audit` GREEN — alignas(64), has_flags bit-pack, cluster
      layout, padding determinism
- [ ] `/merge-scan` GREEN — no missed reuse (parser dispatch + ModelStampResult parser may share)
- [ ] `/trace-deps` GREEN — every consumer of ModelHandle.has_* migrated
- [ ] **Hot path UNTOUCHED** — BG_Evaluate / SG_Evaluate /
      ExecutionCore_Tick diff = 0 (verify via `tools/calls_graph_diff.sh`)
- [ ] Decoupling-endgoal roadmap entry written at
      `plans/_future/2026-05-12-decoupling-endgoal-roadmap.md`
      (POSITIONING: ⬆️ positive — X-macro stamp body + bit-packed has_flags
      mmap-friendly; data-driven parser supports cross-version compat)
- [ ] TECH_DEBT-014 + TECH_DEBT-003 marked CLOSED in workspace
      TECH_DEBT.md
- [ ] Version.hpp bumped 5.14.post1 → 5.15.0 IN THE SAME COMMIT as tag
- [ ] CHANGELOG.md row for v5.15.0
- [ ] HOT_PATH_CHANGELOG: NO entry needed (no hot-path additions)
- [ ] Postmortem at
      `plans/v5.15-live-readiness/postmortems/2026-05-12-v5.15.0-postmortem.md`
- [ ] commit + tag `v5.15.0`; create `pre-v5.15.1` anchor; push branch + tag

## Step 8 — rollback discipline

**If migration breaks at any point:**

1. `git reset --hard pre-v5.15.0` (returns to engine HEAD pre-migration)
2. Re-run `./build.sh test gui suite tsan asan all` to confirm clean baseline
3. Surface failure to Caramel with: (a) sub-tag failed, (b) test/build failed, (c) last successful sub-tag

**Anti-shortcut rule** (CLAUDE.md — Executing actions with care): DO NOT
`git push --force` even on a private branch. Roll back local + re-attempt
sub-tag.

## Step 9 — filesystem conventions

- Engine repo: `/home/caramel/code/FoxML_Trader_v2`
- Workspace: `/home/caramel/code/tick-trader-percore-workspace`
- Plans live in workspace; symlinked from engine `plans/` → workspace
- Sprint dir: `plans/v5.15-live-readiness/{MASTER.md, subplans/, plan_checks/, postmortems/, handoffs/, working/}`
- DESIGN_SPECS: `workspace/DESIGN_SPECS/` (27 patterns)
- Skill outputs go to `plans/plan_checks/<skill>-<YYYY-MM-DD>-<scope>.md`
- Sprint umbrella tag created AFTER all sub-ships ship: `v5.15`
- Sub-ship tags: `v5.15.0`, `v5.15.1`, `v5.15.2`, `v5.15.3`, `v5.15.4`
- Post-ship patches: `v5.15.postN` (per scheme established v5.14.post1)

**Sprint umbrella close (after v5.15.4):** see MASTER §Verification gate
(sprint close) for the full checklist; runs after all 5 sub-ships ship.

## Closing reminder

v5.15.0 is the structural foundation for the v5.15 sprint. v5.15.1
consumes ModelHandle.has_flags for drift surfacing. v5.15.3 inherits the
canonical X-macro pattern for multi-horizon worker stamping. Get
ModelHandle right + the rest of the sprint inherits sound primitives.

If you find yourself writing complex bit-position logic, stop — re-read
`DESIGN_SPECS/framework-patterns/bitmap-flag-api.md` Section "Critical design decision:
predicate macros return bool explicitly". The top-bit truncation
landmine is real.

If you find yourself replicating registry-walk logic, stop — re-read
`DESIGN_SPECS/framework-patterns/heterogeneous-registry-pattern.md` Y3 dispatch canon. The
FOREACH expansion + token-paste dispatch is the right shape.

Good luck. Caramel will iterate with you on findings before coding.
```

---

## Notes for future-Claude reading this handoff doc (NOT in pasted prompt)

- Prompt above is self-contained — paste as FIRST message in a fresh
  `claude code` session.
- The kickoff handoff at
  `plans/v5.15-live-readiness/handoffs/2026-05-12-v5.15-kickoff-handoff.md`
  is the predecessor (covered plan-drafting + sprint sizing). THIS doc
  is the coding-pickup successor for v5.15.0 specifically.
- File at this memorable name (`start-5.15.md`) per Caramel's request —
  duplicates of canonical location aren't created to avoid drift.
- 9 steps + design philosophy + filesystem conventions follow the
  /handoff skill template; customized for v5.15.0 specifics.

---

## Quick links

- Sprint MASTER: `plans/v5.15-live-readiness/MASTER.md`
- This ship's plan: `plans/v5.15-live-readiness/subplans/2026-05-12-v5.15.0-modelhandle-migration.md`
- Step 0 inventory: `plans/v5.15-live-readiness/working/2026-05-12-v5.15.0-has-field-inventory.md`
- Sprint kickoff handoff (predecessor — plan-only):
  `plans/v5.15-live-readiness/handoffs/2026-05-12-v5.15-kickoff-handoff.md`
- Plan-check synthesis: `plans/plan_checks/plan-check-2026-05-12-v5.15.md`
- DESIGN_SPECS catalog: `tick-trader-percore-workspace/DESIGN_SPECS/README.md`
- TECH_DEBT ledger: `tick-trader-percore-workspace/DOCS/TECH_DEBT.md`
- PARITY_ISSUES: `tick-trader-percore-workspace/DOCS/PARITY_ISSUES.md`
- Coding invariants: `DOCS/STRATEGY_AND_CODING_RULES.md` (private)
- Latency rules: `plans/_cross-cutting/2026-05-06-latency-path-discipline.md`
- CLAUDE.md (always loaded): engine repo root
- CLAUDE.local.md (always loaded): engine repo root
