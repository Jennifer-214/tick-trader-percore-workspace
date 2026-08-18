---
type: plan-check
check_kind: readiness
plan: plans/v5.15-live-readiness/subplans/2026-06-15-v5.15.5.F.4d.1.E.1.2-nodestate-soa-layout.md
run_date: 2026-08-17
run_context: /accept-handoff Stage 6 (pickup-time re-verify, NOT pre-coding)
engine_head: cddd8f6
verdict: GREEN-for-decision / NOT-YET-GREEN-for-coding
---

# /readiness — E.1.2 — pickup re-verify at engine `cddd8f6`

## Scoping note (read first)

This plan body is **not** the live spec for the current work, by its own declaration.
Its EXECUTION-STATE banner (AMENDMENT 9) states the D-421+ work "is tracked in the
decision log's D-421 STATUS block and the active handoff, NOT here." So the checklist
below is scoped to **what is actually live** — the D-426 queue (#1–#4) — and the body's
Phase A–G prose is treated as the design-context layer it declares itself to be.

Auditing the superseded body against current code would be a **PARTIAL oracle**
(M10 / `feedback_delegate_on_total_oracle_handreview_on_partial`): a GREEN from it
would certify scope that is explicitly void. Flagged rather than silently produced.

## Stage 0.5 — mechanical pre-pass (deterministic; ran FIRST)

| Tool | Result |
|---|---|
| `tools/check_session_docs.sh` | **exit 0 — SWEEP CLEAN** (all HARD checks; covers Check 32 symbol-existence, Check 45 tests-section, forward-promise, capture-audit-mechanical, meta-registry H15, index-currency) |
| `./build.sh test` | **rc=0** |
| `./build/controller_test` | **3755 passed / 0 failed** — matches the handoff's stated count exactly (the "did NOT move" tripwire holds) |
| `check_identifier_retirement.py` | **GREEN — 94 identifiers**, 0 `ADD (ok` lines |
| `check_identifier_retirement_selftest.sh` | **PASS** — teeth incl. 3 new stamp-key cases; 46 wire keys resolved from the live registry |
| `check_amendment_cascade.py` (default window) | **rc=0 clean**; the sweep's `--since HEAD~20` leg yields 5 LOW advisories, all CP-1 false positives (tool/skill *names* in prose + "hand-set" as ordinary English) |

## Live-scope dependency verification (the D-426 queue)

Every claim below re-verified against HEAD `cddd8f6`, not taken from the handoff.

| Claim | Verified | Evidence |
|---|---|---|
| `STAMP_PUT` landed, additive, unused | ✅ | `StampBoundModelConstRegistry.hpp:164` `stamp_put_field`, `:705` macro, `:191` trait decl, `ModelInference.hpp:2155` specialization |
| Build is C++17 (the route-#1 blocker) | ✅ | `CMakeLists.txt:4` `set(CMAKE_CXX_STANDARD 17)` |
| 17 live `STAMP_SET(inf, …)` sites | ✅ exact | `ML_Headers/StampHelper.hpp` = 17 |
| The LIVE zero-emit is real | ✅ | `StampHelper.hpp` — `STAMP_SET(inf, inference_cfg_bandit_blend_ratio);` inside the `MASK_ML_CFG_BANDIT_ENABLED` gate with **no value assignment** |
| `_GROUPS` ↔ enum drift (TECH_DEBT-286) | ✅ **5 vs 6** | `_GROUPS` rows = inference_cfg, scaler, xgb_hyperparams, grid_member, label_params. Enum adds `STAMP_BIT_environment_meta`. Missing one = `environment_meta`, exactly as claimed |
| Item #2 absence (cfg-derived handle fields written by nothing) | ✅ **EMPTY** | `rg` over `ML_Headers/ CoreFrameworks/ Backtest/ GUI/ MemHeaders/` → rc=1, zero matches |
| The two `REFUSE_STRICT` rows | ✅ | `CfgDriftCheckRegistry.hpp:282` `thompson_precision_prior`, `:286` `thompson_precision_obs` |

## Route-#1 feasibility (the reviewer's member-bearing-registry route) — PREMISE HOLDS

The close-out review's correction is **verified sound**, and the arithmetic closes three ways:

- `FOREACH_STAMP_BOUND_MODEL_CONST` = `PRE_CFG` (**22**) + `POST_CFG` (**24**) = **46 rows**
- The selftest independently resolved **46 wire keys** from the live registry
- The `presence` column splits **37 INCLUDE + 9 SKIP_HANDLE = 46**

`inference_cfg_bandit_blend_ratio` IS a member-bearing row (`:356`, group `_`, `INCLUDE`,
`double`, default `0.0`) — so the trait's universe contains it, and `_GROUPS` is not
involved. **Route B is confirmed unnecessary for this purpose; route A (C++20) is not
required by the trait's needs.**

**One wrinkle the route survives cleanly (worth stating because it looks like a blocker
and is not):** 9 rows are `SKIP_HANDLE`, i.e. absent from `ModelHandle`. A per-name
`void_t` trait TEMPLATE instantiated on the *actual* struct type answers per-(type,name)
automatically, so the `presence` split needs no special handling — the trait asks the real
type, never the registry column. And default-ALLOW for a non-member is semantically right:
setting a presence bit for a field the handle does not mirror is legitimate.

## Checklist verdicts (live scope only)

| # | Item | Verdict | Notes |
|---|---|---|---|
| 1 | Hot path purity | PASS | emit/stamp surface is boot + train→serve, not per-tick |
| 2 | Train-serve parity | **DRIFT-BUG (known, tracked)** | PARITY-042 — the cfg-drift gate layer is vacuous in production. Pre-existing, homed, not introduced here |
| 5 | Backward compat / wire | **GAP-BY-DESIGN** | Item #3 deliberately changes signed-body bytes (SOFT bump, `fees` precedent). Blocked on the positional-vs-relative decision — correctly gated |
| 7 | Test coverage | PASS | selftest teeth verified non-vacuous (46 keys, CODE-side anchored) |
| 19 | Pre-existing-work | PASS | `STAMP_PUT` verified landed; conversion (#4) correctly sequenced *behind* the guard (#1) |
| 27 | DESIGN_SPECS application | PASS | `advertised-capability-never-exercised.md` third-unit amendment **verified landed** (line 18, ws `46a872b`) |
| 45 | Tests-changed section | PASS (mechanical) | sweep green |
| 46 | Identifier retirement / H21 | PASS | guard GREEN + teeth PASS; `stamp-key` enrolled and covering the signed body |
| 47 | **Acceptance-oracle totality (M10)** | ⚠️ **PARTIAL — the live risk** | See below |

### Check 47 detail — the one that matters

The **positional ledger semantics** make the acceptance oracle for item #3 **PARTIAL**:
deleting index 0 of a dense 46-value category emits **1 REMOVED + 45 RENUMBERED**
(arithmetic independently confirmed: 46 keys, `bandit_blend_ratio` at index 0). A reviewer
facing 45 false lines on an HMAC-signed wire surface is in exactly the condition under
which a real regression hides — the **M3 cry-wolf shape**, relocated from the refuted
scanner into the ledger.

This is correctly identified as **BLOCKING** in the handoff and must be settled before #3.

## Recommendations

### Must settle before coding
1. **The name-universe route (#1).** Premise verified — start with the reviewer's
   member-bearing-registry route. This is a genuine fork on a capital-adjacent wire
   surface and the session overturned itself once here → `/decision-check` earns its firing.
2. **Positional-vs-relative ledger semantics.** Gate on #3. The reviewer's candidate
   (name-set membership + relative order) is one comparison change in the tool, no ledger
   reshape — but it is *undecided*, not decided.

### Worth doing during
- Re-bless `tools/goldens/citable-ids.txt` (#4b) — confirmed stale: `D-426`,
  `TECH_DEBT-285`, `TECH_DEBT-286`, `PARITY-042` all return **0 hits**. Needs a real TTY.

### Acceptable risk (don't block)
- The 5 amendment-cascade LOW advisories — verified false positives.
- TECH_DEBT-286 — real, homed, separate; confirmed NOT a blocker for #1.

## Verdict

**GREEN for the DECISION · NOT-YET-GREEN for CODING** — correctly so.

The mechanical floor is fully clean and every checkable claim in the handoff survived
re-verification at HEAD. Nothing is blocked on discovery. Two decisions stand between here
and mechanical work, and both are genuinely open in the decision log (D-426 STATUS), not
stale prose.
