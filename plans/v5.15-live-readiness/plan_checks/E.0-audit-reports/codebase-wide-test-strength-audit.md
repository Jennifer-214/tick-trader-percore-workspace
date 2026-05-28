---
type: audit-report
audit: test-strength-audit
scope: codebase-wide
target_ship: v5.15.5.F.4d.1.E.0
engine_head: 61ae3cc (v5.15.5.F.4d.1.D)
date: 2026-05-28
auditor: Claude (Layer-2 subagent for .E.0 Phase 1)
---

# /test-strength-audit codebase-wide baseline (`.E.0` Phase 1)

## Verdict

**GREEN-READY-TO-CODE** — test specification integrity baseline is STRONG. The codebase has zero codified test-weakening anti-patterns (no `_smoke_check` suffix abuse, no `#if 0` / `DISABLED_` blocks, no commented-out `check()` lines, zero `TODO/FIXME/HACK` markers, zero empty/tautological assertions). The 28 `weak-existence` assertions found are paired with adjacent strict identity checks forming multi-axis assertion bundles. Strict-by-default `==` count assertions outnumber `>=` count assertions 221:21 (10.5:1), and every `>=` instance is either a syscall return-code check (`fd >= 0`, 18/21), a tolerance bound paired with a ceiling (`stddev >= 0.49` + `<= 4.01`), or a documented registry monotonic-grow exception (`LABEL_COUNT >= 11` paired with `static_assert`). Test corpus is **strong enough** as a baseline to detect Core→Node rename-induced semantic drift in `.E.1`.

## Test corpus inventory

| File | Lines | `check()` count | Shape |
|---|---|---|---|
| `tests/controller_test.cpp` | 26,279 | 3,135 | Monolithic unit/integration; `state.cores[i].field` heavy |
| `tests/integration_test.cpp` | 323 | 31 | DataStream + MockGenerator + ROR regression |
| `tests/depth_recorder_test.cpp` | 517 | 26 | DepthRecorder CSV emit + rotation + gap markers |
| `tests/binance_test.cpp` | 143 | 0 | Manual live-data smoke runner (no assertions; prints to stderr) |
| `tests/parity_harness.cpp` | 295 | 0 | Train-serve parity comparator (binary; `fprintf` + exit code) |
| `tests/test_common.hpp` | 175 | 0 | Shared infrastructure (inline `check()` defn + counters) |
| `tests/wire_format_invariants.hpp` | 171 | 0 | Reusable I1-I5 invariants helper for derived-filter consumers |
| **Total assertions** | — | **3,192** | — |

**Notes:**
- The CLAUDE.md "3118 tests" claim now reads ~3,192 (post-`.B.5` extraction). Drift normal; per-test growth tracked across ships.
- `parity_harness.cpp` is a **comparator binary**, not assertion-based. Uses `1e-9` price tolerance, `1e-12` feature tolerance, `1e-4` BPS tolerance for total_fees cross-path equality. Strict by design; rename-resilient because it operates on `BacktestResults` aggregate struct, not raw `state.cores[]` array indexed access.
- `binance_test.cpp` is a manual smoke runner against the live Binance public WS endpoint (no assertions, only stderr trace). Not part of the assertion-strength surface.

## Findings by severity

| Severity | Count | Notes |
|---|---|---|
| HIGH (clearly weakened without justification) | **0** | Codebase is clean |
| MED (weak but defensible; could strengthen) | **4** | Smoke-style `> 0` checks lacking ceiling pair on the same path |
| LOW (legitimate weakening or pre-existing tech debt) | **22** | `fd >= 0` syscall checks (18) + `LABEL_COUNT >= 11` registry-monotonic (1) + `gap >= 1` depth-recorder (2) + `lines > 1` (1) |
| Pattern D (empty/tautological) | **0** | Zero instances |
| Pattern E (commented-out `check`) | **0** | Zero instances |
| Skip markers (`#if 0` / `DISABLED_` / `if (false)`) | **0** | Zero instances |
| TODO / FIXME / HACK markers | **0** | Zero (verified excluding `XXXXXX` mkstemp templates) |

### Coverage notes

- `_smoke_check` suffix convention has **zero adoption**. The skill's Pattern A/B/C filters that whitelist this suffix have no effect; all tests are STRICT-by-contract per skill body.
- TECH_DEBT cross-refs: 10 in-file comments reference closed `TECH_DEBT-NNN` items (mostly TECH_DEBT-004 confidence_freshness_tau deletion; TECH_DEBT-013 BIT_FLAG split; TECH_DEBT-028 state_flags bitmap). These document HISTORICAL closures, not active debt.

## HIGH findings

**None.** All weakened-style assertions reviewed have either:
- Strict identity-check siblings in same `{...}` block (multi-axis assertion bundle), OR
- Justified semantic basis (syscall return code, tolerance bound, monotonic registry, directional sanity)

## MED findings

### MED-1: `controller_test.cpp:386` — `check("buy volume from observed mean", mean_v > 0)`

**Context (`test_warmup`):** Warmup feeds 10 ticks with volumes ranging $500..$590; `mean_v` is the rolling mean of those volumes. The PRECEDING check at line 383 verifies `mean_p` (price mean) against an explicit expected value with tolerance: `fabs(mean_p - 100.25) < 0.5`. The volume check should be similarly strict — expected mean of `(500, 510, ..., 590)` = 545.0, so `fabs(mean_v - 545.0) < 5.0` would catch a rolling-stats regression that `> 0` would miss.

**Rename risk:** If Core→Node rename perturbs `RollingStats` initialization order (e.g., volume field accidentally swapped with another column), `> 0` would still pass while `mean_p` strict check might catch it — but not always.

**Suggested strengthening:** `check("buy volume from observed mean", fabs(mean_v - 545.0) < 5.0)`.

### MED-2: `controller_test.cpp:733` — `check("some buys happened", total_buys > 0)`

**Context (`test_full_pipeline`):** Runs 500 ticks through `PortfolioController_Tick`; sanity-checks that AT LEAST one buy happened. Paired with strict checks: `state == CONTROLLER_ACTIVE` (734) + `total_ticks == 500` (735) + `trade log lines > 1` (747).

**Rename risk:** Moderate. `total_buys` is computed by diffing `Portfolio_CountActive()` per tick. If Core→Node rename perturbs portfolio bitmap field offset or default-init, the count could come out zero AND `total_ticks == 500` would still pass. The `> 0` IS the catch here — it's the only assertion verifying trading actually happened.

**Suggested strengthening:** Codify expected buy count range from prior runs. If 500 ticks under default cfg typically produces 8-15 buys, replace with `total_buys >= 5 && total_buys <= 25`. Tightens lower bound (catches "almost no buys" regressions) + adds ceiling (catches "too many buys = sizing broken" regressions).

### MED-3: `controller_test.cpp:1448` — `check("v5.15.5.F.4b: KIND_DOUBLE_PCT save returns positive char count", n > 0)`

**Context:** Snprintf-style emit function returns char count written. `n > 0` confirms it didn't fail. Should be paired with an expected char count or content check.

**Rename risk:** Low — this is cfg field registry emit, not Core surface. But the assertion shape is weak.

**Suggested strengthening:** Verify the EMITTED CONTENT, not just that it was non-empty. `check("emitted '%.6f' format", strstr(buf, "0.001") != nullptr)`.

### MED-4: `controller_test.cpp:951` — `check("mt disabled: buys allowed despite falling slope", buy_p > 0)`

**Context (`test_multi_timeframe_disabled`):** Verifies that when `min_long_slope=0` (gate disabled), buys still happen during falling-price feed. Paired with predecessor test `test_multi_timeframe` at lines 904 + 914 which verifies the ENABLED case (`buy_p_rising > 0` paired with `buy_p_falling < 0.01`).

**Rename risk:** Low — gate-disabled state shouldn't depend on Core surface. But assertion is intentional-yes/no smoke; could verify `buy_p` is near the expected entry-offset price.

**Suggested strengthening:** OPTIONAL. Replace with `fabs(buy_p - expected) < tolerance` if there's a deterministic expected entry price for this cfg. If not, leave as-is and document `// intentional smoke: gate-disabled mode verifies binary "buys happen" only`.

## LOW findings (legitimate / pre-existing)

- 18 `fd >= 0` checks across tmpfile/mkstemp flows. Idiomatic POSIX check (mkstemp returns -1 on failure, ≥0 on success). Strengthening to `== specific_fd` would be nonsensical — fd value is arbitrary.
- 1 `LABEL_COUNT >= 11 (8 baseline + 3 CS)` at controller_test.cpp:19607 — explicit justification in test name; sister `static_assert(LABEL_COUNT >= 11, ...)` at 19605 ensures the registry can't shrink below 11 at compile time. Registry-monotonic-grow exception (Pattern A LOW per skill body).
- 1 `stddev >= 0.49` paired with `<= 4.01` ceiling — tolerance bound, both directions checked (controller_test.cpp:858-859).
- 2 `gaps >= 1` in depth_recorder_test.cpp:329 + 360 — gap-marker count where 1+ gap is acceptable (gap markers fire on backward `lastUpdateId` OR wallclock-gap >2s; could be N markers depending on what other events fire). Reasonable loosening.
- 1 `lines > 1` at controller_test.cpp:747 — "header + at least one trade" check. Could strengthen to `>= 2` but semantically equivalent.

## Tests at risk during Core→Node rename

The mechanical rename will touch ~5,000+ sites per the `.E.1` plan body. Within tests/, the renamed-surface footprint is substantial:

| Rename pattern | Sites | Risk level |
|---|---|---|
| `state.cores[i].field` member access | **238** (`controller_test.cpp`) | HIGH — most concentrated rename touch-site density |
| `check()` lines containing the substring "Core" or "core" | **242** | MED — name string changes; cosmetic but verify assertion bodies survive |
| `per_core_*` symbol prefix | **54** | MED — registry/cfg surface |
| `core_N_` cfg key string (e.g., `core_0_strategy=`) | **30** | LOW (cfg keys may stay `core_N_` for backwards compat) |

**Highest-risk tests:** Phase 2.1, 2.2, 4 (`controller_test.cpp:5295..5775` range). These access `state.cores[slot].core_open_notional`, `state.cores[slot].entries_processed`, `state.cores[slot].halt_reason`, `state.cores[slot].pending_params.*`, `r->state.cores[0].core_realized`, `r->state.cores[0].core_kill_tripped`, `r->state.cores[0].allocated_balance`. Member field names use `core_*` prefix as a SEMANTIC namespace (not just struct-locator); a rename that converts `state.cores → state.nodes` MUST also rename `cores[i].core_open_notional → nodes[i].node_open_notional` etc., otherwise asymmetric naming creates confusion + grep-discovery failures during future audits. 

**Saving grace:** All Phase 2.x tests use STRICT equality (`== 0.0`, `== 1`, `fabs(...) < 1e-6`). If the rename perturbs ANY semantic (e.g., default-init differs because the rename touched struct initializer ordering), these strict assertions will catch it. The four MED-severity weak checks above are the ONLY surface where rename-induced drift could potentially slip past.

**Train-serve parity:** `parity_harness.cpp` operates on `BacktestResults` aggregate (`legacy.feature_matrix[i*N+j]`, `legacy.sample_prices[i]`) NOT raw `state.cores[]`. Tolerances are 1e-9 (price) + 1e-12 (feature) + 1e-4 (BPS fees). Highly resilient to rename — operates one layer above the renamed surface.

## Recommended pre-`.E.1` test strengthening

Triage proposals (operator decides):

1. **MED-1 strengthen at controller_test.cpp:386** — replace `mean_v > 0` with `fabs(mean_v - 545.0) < 5.0`. Cheap; ~1 line change. Catches rolling-stats column-swap regression. Open as **TECH_DEBT (NEW)** — strengthening the warmup volume mean assertion.

2. **MED-2 strengthen at controller_test.cpp:733** — replace `total_buys > 0` with `total_buys >= K_LOW && total_buys <= K_HIGH` after operator confirms current expected range for the cfg (need 1 baseline run). Catches "trade count broke" regressions. Open as **TECH_DEBT (NEW)** — strengthen full-pipeline trade-count bound.

3. **MED-3 strengthen at controller_test.cpp:1448** — verify emitted content (`strstr(buf, "0.001000")` for KIND_DOUBLE_PCT) not just char count > 0. Low cost; closes assertion content gap. Open as **TECH_DEBT (NEW)** — KIND_DOUBLE_PCT emit content verification.

4. **MED-4 ACCEPT WITH RATIONALE** — `test_multi_timeframe_disabled` is intentional-binary smoke. Add documentation comment instead of strengthening.

5. **Process recommendation for `.E.1`:** Adopt `_smoke_check` suffix convention at first rename point. Renaming `test_warmup` → `test_warmup_smoke_check` (if the assertion bundle is intentionally weak) signals intent and would suppress future audit firing on those weak checks. OR — strengthen the weak checks instead. Caramel's call. Default-recommend strengthening per the high-quality-bar discipline (`feedback_motivated_collaborator_for_caramel`).

6. **Process recommendation for `.E.1` cycle-2 audit (`/test-strength-audit working` post-rename):** Skill is currently `diff`-driven (`git diff` working tree). When the rename ship lands, fire `/test-strength-audit v5.15.5.F.4d.1.D..HEAD` to scan the actual rename diff for accidental assertion weakening. If the diff is large enough to chunk, split per file: `git diff v5.15.5.F.4d.1.D..HEAD -- tests/controller_test.cpp` etc.

7. **Sister cohort:** The `_smoke_check` suffix discipline NOT being adopted is a Stage 2 DRAFT-eligible discipline. Worth a memory codification + skill amendment IF Caramel wants future rename ships to benefit from suffix-based audit suppression. Otherwise the skill keeps falsely flagging legitimate smoke checks.

## Auto-write contracts triggered

- **3 NEW TECH_DEBT entries** suggested for MED-1, MED-2, MED-3 strengthenings (operator decides whether to open at `.E.0` close or defer to `.E.1` discussion).
- **0 PARITY entries** — no parity findings (parity_harness itself is tight; cross-path BPS check is in place).
- **0 NEW Class** in RECURRING_BUG_PATTERNS — no new anti-pattern surfaced.

## Cross-references

- Audit skill body: `/home/caramel/code/FoxML_Trader_v2/.claude/skills/test-strength-audit/SKILL.md`
- Sister readme: `_README.md` (this dir)
- `.E.0` plan body: `subplans/2026-05-28-v5.15.5.F.4d.1.E.0-precoding-plan-audit-verification.md`
- `.E.1` rename ship plan: `subplans/2026-05-28-v5.15.5.F.4d.1.E.1-foundation-rename-per-node-drainer.md`
- INVARIANTS_MAP: `tests/INVARIANTS_MAP.md` (27 invariants → test sites mapping)
- Shared test infra: `tests/test_common.hpp` (inline `check()` defn + counters)
- Wire-format invariants helper: `tests/wire_format_invariants.hpp` (I1-I5 reusable)
- DESIGN_PHILOSOPHY § 11 (process discipline; test SPECIFICATION integrity over time)

---

**End of `.E.0` Phase 1 codebase-wide test-strength-audit baseline.**
