---
type: readiness-report
plan: plans/v5.15-live-readiness/subplans/2026-06-10-v5.15.5.F.4d.1.E.0.10-net1-correctness-net.md
date: 2026-06-11
verdict: GREEN
context: composed by /accept-handoff Stage 6 (pickup of the .E.0.10 active handoff)
---

# /readiness report — `.E.0.10` Net-1 correctness net — 2026-06-11

## Stage 0 — "what we already have" (institutional preamble)

- **Ship class:** TEST/TOOLING ONLY (no engine code → structurally cannot break the hot path). `audit_tier: HIGH-RISK` is COMPLETENESS-risk (gates `.E.1` + re-triages the capital backlog), not code-risk.
- **Sister specs (frontmatter, all loaded):** golden-master-over-reimplemented-oracle · phased-pre-rework-correctness-foundation · two-foundations (determinism vs correctness) · guard-matrix-bounds-hardening · tag-disposition-at-fix-time. The plan applies them correctly (characterization = freeze real output + diff; Net-1 freezes, deliberate fixes stay separate).
- **Decisions reckoned with:** D-73/74 (Net-1/2 split) · D-98 (backlog absorption) · D-110 (decimal recovery — DONE) · **D-190 (P&L gross SSoT — IMPLEMENTED, `Money_FillGross`@Portfolio.hpp:397)**. None reopened. No fake-blocker (D-105-shape) present.
- **Canonical sister registries section PRESENT** (`feedback_plans_cite_sister_registry_inspection` satisfied): the disposition register EXTENDS the TECH_DEBT 3-file split (status-by-location), does NOT reinvent it; feeds the E-guard-coverage-matrix; populates each `.E.x` plan's `findings_sidecar:`.
- **Ledgers in surface:** 93 open TECH_DEBT + 5 PARITY (the re-triage target). The register is the live disposition SSoT.

## Stage 0.5 — mechanical floor (deterministic, already run)

`tools/check_session_docs.sh` → **CLEAN, all HARD pass** (doc-metadata bidirectional+index · B-Plus [no session-modified plan bodies] · capture-audit mechanical · tools-inventory · always-loaded budget · handoff-active singleton · FPN-doc-size · forward-promise · meta-registry). Only advisory: `capital-test adversarial markers — 5 unmarked (KNOWN backlog)`. Check 32 (plan-body symbol-existence) + Check 45 (tests-section) satisfied by the sweep — NOT re-derived.

## Checklist verdicts (10-item + relevant numbered)

| # | Item | Verdict | Notes |
|---|------|---------|-------|
| 1 | Hot path purity | ✅ PASS | No hot-path code added. F-059 READS `ExecutionCore.hpp:543` (`live_tp=Money_Add(price,Money_Mul(price,tp_pct))`) to characterize; adds nothing. |
| 2 | Train-serve parity | ✅ PASS | Characterization FREEZES current behavior; no feature/label/model/stamp change. The one drift found (D-190 P&L rounding) was a real DRIFT-BUG — already FIXED + triple-guarded. |
| 3 | Surface area | ✅ PASS | Additions to `tests/controller_test.cpp` + CI checks + the register. No `if(live)`/`if(arch)` proliferation. |
| 4 | Pointer init / heap lifecycle | ✅ PASS | Test fixtures use `R* r = new R(); … delete r;` (test-local heap, freed). |
| 5 | Backward compat | ✅ PASS | No SHARDED_SNAPSHOT_VERSION / MODEL_FORMAT_VERSION change; no cfg removals. |
| 6 | Multi-threading | ✅ PASS | conc-5 verified on a DISPOSABLE clone via tsan (no threading mod). Torn-read class remediation explicitly DEFERRED to `.E.1` aggregator. No new threads/atomics. |
| 7 | Test coverage | ✅ PASS | The plan IS coverage. 6 characterization tests landed; suite **3359/0**. |
| 8 | Docs + invariants | ✅ PASS | H1–H20 CI invariant checks + disposition-tracker CI guard + torn-read RECURRING_BUG_PATTERNS class (TECH_DEBT-165) are first-class deliverables. |
| 9 | Forward maintenance | ✅ PASS | Register dogfoods WH-7; adversarial-default is the structural M7 close (BINDING). |
| 10 | Rollback story | ✅ PASS | Test/tooling, additive; Phase-0 pre-tag anchor. |
| 19 | Pre-existing-work audit (SHIP-BLOCKING) | ✅ PASS | Phase-1 re-triage IS the pre-existing-work audit ("nothing closed until grepped" — paid twice this session). |
| 25 | TECH_DEBT surface scan | ✅ PASS | Re-triages 93 TECH_DEBT + 5 PARITY into the register — the deliverable. |
| 32/45 | Plan-body symbol / tests-section | ✅ PASS | Mechanical sweep GREEN. (The `.E.1` plan's 10 illustrative B-Plus fragments are a DIFFERENT plan — task #13, currently latent.) |
| 34 | Audit tier declared | ✅ PASS | `audit_tier: HIGH-RISK (code-risk LOW…)` in frontmatter, scope-matched. |

## Dependency verification (F-059 next-action surface)

| Claimed dependency | Verified | Notes |
|---|---|---|
| `ExecutionCore.hpp:543` live_tp per-fill compute | ✅ confirmed | `live_tp = Money_Add(tick.price, Money_Mul(tick.price, tp_pct))` — the real exit path the stub-oracle never covered |
| `Money_FillGross` (D-190 SSoT) | ✅ CODE_MAP:250 → Portfolio.hpp:397 | guard `check_money_gross_single_source.py` (Check G/L) |
| `SG_Evaluate` (exit trigger) | ✅ CODE_MAP:114 → :189 | the trigger F-059 freezes |
| `EventLoop_DrainPostFill` / `…OneCore` | ✅ CODE_MAP:55/54 → :1798/:1370 | post-fill consumer |
| `oms-ts-1` template + `// ADV-REFUTE:` marker | ✅ controller_test.cpp:8311 | the pattern to mirror (hand-derived `Money_Eq` exact asserts) |
| `check_capital_adversarial_audit.py` + self-test | ✅ TOOLS.md:35/36 | STANDING-CI; enforces the marker |

## Cold-pickup completeness (C.1–C.10)

9/10 present. C.1 branch ✓ · C.2 phase order ✓ (0→1→2→3) · C.3 first move ✓ (F-059, surfaced precisely) · C.4 fn names ✓ (all verified) · C.5 file:line ✓ · **C.6 ⚠️ stale-claim** (see below) · C.7 effort ✓ (no LOC target per discipline) · C.8 source-audit ✓ (CANONICAL-FINDINGS corpus) · C.9 predecessor/successor ✓ (`.E.0.9`/`.E.1` named) · C.10 tag ✓.

## The one finding — C.6 STALE-PLAN-PROSE (⚠️ YELLOW, non-blocking)

The plan **frontmatter is stale relative to its own execution state** (the live SSoT is the register + handoff, which ARE current — so this misleads only a reader who trusts the frontmatter over the register):
- `status: DRAFT v0.1 (pre-audit-gate)` — but the ship is **mid-Phase-2** (6 characterization tests landed, D-190 fixed, register live). Recommend → `status: IN-FLIGHT (Phase-2; oms-ts-1 landed; F-059/conc-5/MED-tier remain)`.
- Acceptance line *"suite still 3285/0"* — the real baseline is now **3359/0** (3285 was the pre-Net-1-tests floor; the criterion meant "don't regress 3285", now superseded).
- `naming_note` "operator-confirm" for the `.E.0.10` semantic=tag realignment — **de-facto adopted** (all work tags `.E.0.10`). Mark confirmed.

**Fix:** one frontmatter/acceptance refresh during the next edit of this plan; doesn't impede coding.

## Recommendations
- **Must fix before coding:** none.
- **Worth fixing during coding:** C.6 frontmatter refresh (status DRAFT→IN-FLIGHT; baseline 3285→3359; naming_note confirmed).
- **Acceptable risk:** the 5-block capital-marker advisory (D-110/oms-ts-2/core_fees) — shrinking per close-the-class as each gets an independent refute.

## Verdict: **GREEN** — start coding now

The plan is sound and mid-execution; every cited surface verified to exist; suite 3359/0; mechanical floor clean; the next action (F-059) is fully grounded with a concrete template (`oms-ts-1`) and target (`ExecutionCore.hpp:543`). The sole finding is a non-blocking stale-frontmatter refresh.

## Map-update reminders
- Run `./tools/gen_code_map.sh` after F-059 + MED-tier tests land (new test fns) — already regenerated at pickup (818 fns).
- `tests/INVARIANTS_MAP.md` — add rows when the H1–H20 CI invariant checks land.
