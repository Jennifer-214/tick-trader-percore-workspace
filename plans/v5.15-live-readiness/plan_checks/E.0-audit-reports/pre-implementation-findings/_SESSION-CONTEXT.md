---
type: audit-session-context
purpose: single self-contained doc for an agent to pick up the v5.15 pre-implementation audit without the original session
scope: FoxML_Trader_v2 codebase audit (bandit + ML + 9 code surfaces)
engine_head_scanned: ce2173b (v5.15.5.F.4d.1.D.1 WIP)
date: 2026-05-28
status: audit COMPLETE; codification + runtime-confirmation + fixes QUEUED
canonical_code_touched: NONE (read-only, snapshot-isolated)
---

# Pre-implementation audit — session context for pickup

**Read this first.** Self-contained context to continue the v5.15 pre-implementation audit
without the original chat session. Everything referenced here is durable; the raw sweep
outputs (in `/tmp`) are ephemeral — treat the sidecars in this directory as the record.

---

## 1. TL;DR

A multi-pass, READ-ONLY audit of the FoxML_Trader_v2 engine was run to de-risk the path to
paper-test / live. It produced **141 net-new findings** (2 CRITICAL, 38 HIGH, 63 MEDIUM,
38 LOW) on top of ~85 from earlier passes, all deduped + adversarially verified, **with zero
changes to canonical engine code**. Findings are triaged into per-ship sidecars in this
directory. Three things remain QUEUED: (a) **runtime-confirmation** of 49 provisional
findings, (b) **codification** of the learnings (deferred until `.D.1` ships), (c) the actual
**fixes** (land at each `.E` ship's coding time). See §7.

---

## 2. What was done (method)

Four escalating READ-ONLY passes, each deduped against all prior + the `TECH_DEBT`/`PARITY`
ledgers, each with an adversarial verify stage:

1. **round-0** — bandit subsystem + ML training + backtest harness (22 findings, doc:
   `../codebase-wide-ml-bandit-audit.md`, F1–F22).
2. **pass-1** — 7 code surfaces in isolation (46 findings).
3. **pass-2** — integration *seams* between subsystems + a completeness/coverage critic (~17;
   found the slow→hot flag-clobber zombie a per-surface scan can't see).
4. **deep sweep (5×9)** — 49 skill-lens agents: 9 sections × 5 audit-skill lenses + 3
   specialized depth lenses (concurrency-correctness, wire-format, live-trading-protocol) +
   1 cross-cutting determinism sweep (141 net-new).

**Isolation discipline (important — preserve it):** the engine was audited against a **frozen,
disposable git-archive snapshot** at HEAD `ce2173b`, *not* the live tree — because a separate
`.D.1` rename agent owns the live tree's uncommitted work, so stray writes there could not be
safely cleaned. This was vindicated: an agent did try to compile inside the sweep; the artifact
was contained in the disposable copy and deleted with it. **The canonical tree is byte-for-byte
untouched.** Any future run-required step (see §7.2) must use the same throwaway-clone discipline.

---

## 3. Yield / current state

- **Deep sweep:** 196 raw lens-findings → **141 NEW** after filtering **35 already-tracked**
  (matched existing `TECH_DEBT`/`PARITY`) + **20 cross-lens duplicates**.
- Severity (new): **2 CRITICAL, 38 HIGH, 63 MEDIUM, 38 LOW**.
- **4 sections RED:** concurrency, live-binance, regime-features, **fixedpoint-mem** (the
  coverage-gap section — found the most: 23, incl. 9 HIGH).
- **49 of 141 are PROVISIONAL** (`needs_runtime_confirmation`), **including both CRITICALs** —
  static analysis flagged them but could not confirm. Do **not** treat these as fact until run.
- Prevention payload: **~140 anti-pattern instances, 97 CI-tool candidates, 122 test specs**
  attached to findings (inputs for codification).

---

## 4. Deliverables (durable — in this directory)

```
pre-implementation-findings/
├── _SESSION-CONTEXT.md          ← this file (start here)
├── _README.md                   ← dir description
├── MASTER-BACKLOG.md            ← triage buckets + all CRIT/HIGH + codification rollup
├── PRE-PAPER-TEST-findings.md   ← 55  (URGENT gate — both CRITs + foundational HIGHs)
├── E.1-findings.md              ← 30  (Foundation: drainer→per-node, concurrency, persistence)
├── E.2-findings.md              ← 14  (headless / mmap / crash-recovery)
├── E.3-findings.md              ← 10  (WS-API + persistent connections)
├── E.5-findings.md              ← 6   (sub-accounts / capital)
├── E.6-findings.md              ← 2   (exchange adapter)
└── BACKLOG-STANDALONE-findings.md ← 24 (lower-priority cleanups)
```
Round-0 (bandit/ML/backtest): `../codebase-wide-ml-bandit-audit.md`.
Each finding carries: where · what · why · `fix_ship` · `dont_carry_forward` · `ci_tool_candidate`
· `test_gap` · `anti_pattern_candidate` · `confidence` · `needs_runtime_confirmation` · `known_tracked`.

---

## 5. Reference files (needed to ACT on the findings)

Two roots:
- **Engine code:** `/home/caramel/code/FoxML_Trader_v2` (scanned at `ce2173b`; code symbols
  rename core→node at `.E.1`, so finding line-numbers are approximate and will shift).
- **Workspace** (canonical design docs + plans + skills): `/home/caramel/code/tick-trader-percore-workspace`
  — paths below are relative to this. (The public engine repo symlinks/gitignores most of these.)

- **Invariants / judging:** `CLAUDE.md` (H1-H20), `DOCS/DESIGN_PHILOSOPHY.md`,
  `DOCS/STRATEGY_AND_CODING_RULES.md`, `DOCS/CLAUDE_INVARIANTS.md`, `DOCS/CLAUDE_ML_INVARIANTS.md`,
  `DOCS/CLAUDE_INTEGRATION.md`, `DOCS/LATENCY_OPTIMIZATION_AUDIT.md`,
  `FoxML_Trader_v2/DOCS/MANUAL_FIELDS_INVENTORY.md` (Class 26/27 exemptions),
  `plans/_cross-cutting/2026-05-06-latency-path-discipline.md`.
- **Codification format:** `DOCS/RECURRING_BUG_PATTERNS.md` (index) + `DOCS/recurring-bug-patterns/`
  (per-class bodies; Class 1–36 exist — **number NEW classes from 37**); `DESIGN_SPECS/` + `README.md`;
  `DESIGN_SPECS/meta-disciplines/{doc-frontmatter-convention,doc-tag-vocabulary,pattern-codification-lifecycle}.md`;
  scaffold new specs with `/doc-create`.
- **Ledgers (land rows + dedup):** `DOCS/TECH_DEBT.md` + `DOCS/tech-debt/{open,in-flight,closed}.md`,
  `DOCS/PARITY_ISSUES.md`.
- **.E ship context (fix_ship routing + don't-carry-forward):**
  `plans/v5.15-live-readiness/E-MASTER-REFERENCE.md`,
  `plans/v5.15-live-readiness/subplans/2026-05-28-v5.15.5.F.4d.1.E.{0,1,2,3,5,6,X}-*.md`,
  `plans/v5.15-live-readiness/subplans/2026-05-28-v5.15.5.F.4d.1.E-dependency-graph.md`,
  `plans/v5.15-live-readiness/decision-logs/v5.15.5.F.4d.1.E-architecture-v2.md`.

---

## 6. The 2 provisional CRITICALs (do not lose)

- **`conc-5`** — multi-producer race on the per-core `submit_queue` SPSC ring: the drainer
  thread AND the per-core slow thread both push → violates the single-producer invariant.
  Confirm via `./build.sh tsan` + a drainer/slow-thread stress. (section: concurrency)
- **`live-bc-1`** — user-data WS points at Binance **global** (`stream.binance.com`) while
  orders + listen-key use Binance **US** (`api.*`): an endpoint split that would break live
  fills. Confirm via config/code trace (likely no build needed). (section: live-binance)

Both → `PRE-PAPER-TEST-findings.md`.

---

## 7. What's QUEUED (ordered; none done yet)

### 7.1 Codification — **DEFERRED until `.D.1` ships**
Consolidate the ~140 anti-pattern instances into candidate **Classes starting at 37** (36 is
taken by `.D.1`) + ~97 CI-tool specs + ~122 test specs + new `DESIGN_SPECS` + `TECH_DEBT`/`PARITY`
rows + plan-body `findings_sidecar:` backlinks + `E-MASTER-REFERENCE.md` index rows.
**Why deferred:** all those files are being edited by the `.D.1` rename agent right now —
writing into them now would collide. *Drafting* into this isolated subdir before `.D.1` lands is
fine. Recommended new skills (decide net-new vs. extend-existing **by yield** at codification):
`/determinism-audit`, `/concurrency-audit`, `/wire-format-audit` (likely fold into `/parity-check`),
`/live-trading-audit`, `/seam-audit`. Run `/capture-audit` after to verify propagation.

### 7.2 Runtime confirmation — needs build + run (isolated throwaway clone only)
Confirm/refute the 49 provisionals, prioritizing the 2 CRITICALs (§6) + the fixedpoint cluster
(build *with* vs *without* `USE_NATIVE_128`, diff `FPN_Sqrt<64>` output; the production FP path
is currently untested — tests compile without the flag). Observation only — never the canonical tree.

### 7.3 PRE-PAPER-TEST correctness mini-ship
After runtime-confirm, the surviving subset of the 55 `PRE-PAPER-TEST` findings gates the
paper-test milestone (`../../../ROADMAP-2026-05-17-to-paper-test.md`) — schedule as a focused ship.

### 7.4 Fixes
Routed to their `.E` ships via the sidecars; land at each ship's coding time per the
`dont_carry_forward` notes. **No engine code has been changed.**

### 7.5 Ensuring findings actually get USED (enforcement — not just filed)

A doc is a **passive** record; findings in a file get forgotten. To *guarantee* they're applied
when `.E` is implemented, wire them into things the implementer/CI is FORCED to engage with —
strongest first:

1. **CI checks + regression tests (the real guarantee — machine-enforced, zero memory required).**
   Convert the 97 `ci_tool_candidate` findings into CI checks and the 122 `test_gap` specs into
   regression tests at codification. A reintroduced bug then breaks the build / test suite — it
   physically cannot be silently lost, even if every doc goes unread. This is the codebase's own
   gradient (compile-time/CI > runtime > convention) and the lowest-ceremony way to make findings stick.
2. **Plan-body required-reading link (forces a human to see them).** Add each sidecar to its `.E.X`
   plan body's mandatory "Required reading + reference docs cross-check" section (the D-52 section
   already in the plan template) + a `findings_sidecar:` frontmatter pointer. Then nobody can open
   the `.E.1` plan without being pointed at `E.1-findings.md` and its `dont_carry_forward` notes.
   (Deferred to post-`.D.1` — rename owns the plan bodies.) `/capture-audit` verifies the link holds.
3. **Per-ship pre-coding gate input (forces the process).** Make the relevant sidecar a required
   input to each `.E.X` ship's `/precoding-audit-gate` (already fired before every HIGH-RISK ship),
   so the gate checks the findings were addressed.

**Do NOT mistake "findings filed" for "findings handled."** This doc + the sidecars are the record;
the *guarantee* is CI/tests (#1) + the plan-body link (#2), wired at codification.

---

## 8. Hard constraints (do not violate)

1. **Do NOT change canonical engine code** during audit/codification/handoff work. Fixes land
   only at their assigned ship's coding time.
2. **Do NOT write codification into rename-owned files** (`RECURRING_BUG_PATTERNS`, `DESIGN_SPECS`,
   `TECH_DEBT`/`PARITY`, `claude-skills`, `.E` plan bodies, `E-MASTER-REFERENCE`) until `.D.1` ships.
3. **Any run-required step uses a disposable clone**, never the live tree (shared with the rename agent).
4. **Findings line-numbers are approximate** (pre-rename code; core→node shifts them at `.E.1`) —
   cite by symbol + structural description.
5. **Provisional findings (49) are suspicions, not facts** until runtime-confirmed.

---

## 9. How to pick this up (first actions)

1. Read `MASTER-BACKLOG.md`, then `PRE-PAPER-TEST-findings.md`.
2. Operator-triage the PRE-PAPER-TEST bucket (FIX-NOW / DEFER / ACCEPT).
3. Highest-value next step: runtime-confirm the 2 CRITICALs + fixedpoint cluster (§7.2) on a
   disposable clone.
4. When `.D.1` has shipped: do the codification (§7.1), Classes from 37, via `/doc-create` +
   ledger writes + `/capture-audit`.
5. Fixes flow into `.E.1`+ at coding time per each sidecar's `dont_carry_forward`.

---

**End of session context.** This doc + the sidecars in this directory are the complete,
durable record of the audit — no original-session memory required to continue.
