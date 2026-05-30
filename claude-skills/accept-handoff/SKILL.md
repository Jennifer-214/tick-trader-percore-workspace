---
name: accept-handoff
description: Receiver-side handoff verification skill. Fresh-session pickup runs ONE command to load handoff doc + all cited reference files + run drift-check + recreate TaskList + verify git state matches handoff claims + reconcile decision-log status (decided vs open). Closes the "fresh session forgets to load required reading" failure mode. Sister to /handoff (writer side); both close the multi-session pickup loop. Output: PICKUP-READY status + concrete "your next action is X" instruction.
type: skill
concern: workflow
audit_cadence: per-session-start
tags: [doc-discipline, framework-discipline, operator-collaboration, meta-discipline]
surface: [handoff-pipeline, session-pickup]
sister_skills: [/handoff, /capture-audit, /readiness, /sync-workspace]
loads_dynamically: [CLAUDE.md, CLAUDE.local.md, memory/MEMORY.md, DOCS/DESIGN_PHILOSOPHY.md, target-handoff.md, cited-reference-files, in-flight-plan-body.md, decision-log.md]
applies_meta_discipline: M7 (structural-enforcement-when-memory-insufficient)
established: 2026-05-26
first_canonical_application: post-.B.4 v1.7.4 handoff addendum cycle
---

# /accept-handoff — Receiver-side handoff verification

## Why this skill exists

The `/handoff` skill writes a comprehensive handoff doc. But nothing structurally enforces that the receiver (fresh session) actually loads everything cited or runs the audits the handoff says to run. Receiver-side discipline historically relies on:
- Operator manually pasting handoff content
- Fresh session manually loading each cited file
- Fresh session remembering to run /capture-audit + /readiness

This is the same memory-only-discipline-insufficient pattern that M7 addresses — a textbook Stage 6 escalation candidate at the handoff-receiver surface. `/accept-handoff` provides structural enforcement: ONE command loads everything + runs drift check + recreates TaskList + reports concrete next action.

## What this skill does (sequential)

### Stage 1: Locate handoff doc

- If `<path>` arg given: use it
- Else default: most recently modified file in `plans/<active-sprint>/handoffs/*.md`
- If no handoff found: ERROR — sprint must have at least one handoff

Active sprint = detected from `Version.hpp` per `/handoff` Stage 1.

### Stage 2: Parse handoff doc

Extract:
- Engine HEAD claimed (e.g., "Engine HEAD `726e7df`")
- Workspace HEAD claimed (e.g., "Workspace HEAD `4408a02`")
- Active branch (e.g., "feat/v5.15-live-readiness")
- In-flight plan body path (cited under "Critical pickup-time reads")
- Required reading files list (cited under "Critical pickup-time reads" + "Cross-references")
- TaskList table from Stage 1.5 capture (if present)
- PENDING items list ("What's PENDING" sections)
- WIP-checkpoint commits enumerated

### Stage 3: Load required reading dynamically

Read each cited file via Read tool.

**Stage 3.1 — Always-loaded baseline** (read regardless of citation):
- `/home/caramel/code/FoxML_Trader_v2/CLAUDE.md`
- `/home/caramel/code/FoxML_Trader_v2/CLAUDE.local.md`
- `~/.claude/projects/-home-caramel-code-FoxML-Trader-v2/memory/MEMORY.md`

**Stage 3.2 — Handoff-cited reads** (load each file from "Critical pickup-time reads" section):
Per-file action: Read → confirm file exists + content non-empty → log to internal "loaded files" list.
If any cited file MISSING at HEAD: WARN — handoff may reference stale path.

**Stage 3.3 — CLAUDE.local.md trigger-required reads** (auto-load based on plan surface; per `CLAUDE.local.md § Required reading before performance-sensitive code` table):

Detect plan body surface keywords; auto-load matching trigger docs even if not explicitly cited:

| Plan body contains keyword | Auto-load |
|---|---|
| `slow-path` / `slow_path` / `BG_Evaluate` / `SG_Evaluate` / `hot path` / `OMS_Drain` / `parsing` / `ML inference` / `strategy` | `DOCS/STRATEGY_AND_CODING_RULES.md` (11 strict invariants H1-H20) |
| `latency` / `optimization` / `regression` / `perf` / `cycle` | `DOCS/LATENCY_OPTIMIZATION_AUDIT.md` (13 parts) |
| `hot path` / `slow path` / `latency-impacting` / `per-tick` / `BG_Evaluate` / `producer` / `drainer` | `plans/_cross-cutting/2026-05-06-latency-path-discipline.md` (7 architectural rules) |
| `audit_tier: HIGH-RISK` OR cold-pickup OR designing-non-trivial | `DOCS/DESIGN_PHILOSOPHY.md` (master settings portal; 14 sections + § 11.5 M1-M7 registry) |

**Stage 3.4 — In-flight plan body extract surface auto-load** (read engine source files cited in plan body's Phase B/C/D Steps):

Scan plan body for `<source-file>.hpp:<line>-<line>` extract references. Auto-load each referenced engine source file (full file or relevant line range). Common surfaces:
- `EngineSharded.hpp` (per_core_slow lambda body extraction)
- `ControllerEventLoop.hpp` (sister consumer patterns)
- `SlowPathGateRegistry.hpp` (FOREACH_SLOW_PATH_GATE + AUTOPOPULATE macros)
- `BinanceDepth.hpp` (`BookSnapshot<F>` sister-canonical reuse)
- `ExecutionCore.hpp` (hot path)
- `OrderManager.hpp` (drainer)

**Stage 3.5 — Memory file cross-ref auto-load**:

Memory files referenced in plan body / handoff doc / decision log via `[[name]]` or `feedback_*` / `user_*` / `project_*` / `reference_*` patterns auto-load (these are typically already loaded via MEMORY.md auto-load; this is verification).

### Stage 4: Verify git state matches handoff claims

```bash
# Engine
cd /home/caramel/code/FoxML_Trader_v2
git rev-parse HEAD  # compare against engine HEAD claimed in handoff
git status --short  # confirm working tree state (clean vs dirty per handoff)
git branch --show-current  # confirm on expected branch

# Workspace
cd /home/caramel/code/tick-trader-percore-workspace
git rev-parse HEAD  # compare against workspace HEAD claimed in handoff
```

Discrepancies:
- HEAD drift (handoff claimed SHA X but HEAD is now SHA Y): walk intervening commits via `git log <X>..<Y> --oneline`
  - If ALL intervening commits are handoff doc / reading-list / ADDENDUM updates (self-referential refresh): ACCEPTABLE — silently note "N self-referential handoff refresh commits since handoff anchor SHA"; do NOT warn
  - If ANY intervening commit modifies substantive code / plan body / skill SKILL.md / DESIGN_SPECS / TECH_DEBT / PARITY_ISSUES: WARN — handoff may be stale beyond self-refresh; verify intent before pickup
  - Handoff doc itself uses "at or after `<SHA>`" framing for workspace HEAD anchor (chicken-and-egg of self-referential handoff doc refreshes)
- Branch mismatch: BLOCK — wrong branch; pickup unsafe
- Working tree dirty when handoff said clean (or vice versa): WARN — verify intent
- Engine forward-drift (engine HEAD ahead of handoff claim): typically means a ship landed since handoff write; investigate via `git log <claimed-sha>..HEAD --stat`

### Stage 4.5: Verify predecessor ship artifact claims (added 2026-05-27)

Sister to /handoff Stage 2.8 (sender enumeration) + /handoff template Step 1.4 (manual receiver verification). Where Stage 4 confirms current git state matches handoff anchor, Stage 4.5 confirms PREDECESSOR ship's claimed artifacts actually landed cleanly.

**Why this exists:** Predecessor ship close ritual can leave artifacts incomplete (memory file written but MEMORY.md not indexed; DESIGN_SPECS Stage promotion frontmatter not bumped; TECH_DEBT entry not moved from `open.md` to `closed.md` despite narrative claiming closure; PARITY entry status flag still `open` despite cited closure). A receiver picking up the next ship is the natural overlapping-check surface — overlapping checks at different phases catch drift single-check phases miss.

Parse the handoff body's `## What landed at <predecessor-tag> ship close (PREDECESSOR CONTEXT)` section. For each cited artifact claim, run the corresponding verify command:

| Artifact claim type | Verify command | Pass criterion |
|---|---|---|
| Predecessor tag exists | `git tag --list <predecessor-tag>` | Exact match returned |
| Predecessor tag GPG-signed | `git tag --verify <predecessor-tag>` | Signature valid (skip if signing not configured) |
| CHANGELOG.md row landed | `rg "^### <predecessor-tag>" DOCS/CHANGELOG.md` | Returns ≥1 match |
| Postmortem file exists | `ls <postmortem-path>` | File exists |
| TECH_DEBT closures moved | For each `TECH_DEBT-N` claimed closed: `rg "id: TECH_DEBT-N" tick-trader-percore-workspace/DOCS/tech-debt/closed.md` AND `rg "id: TECH_DEBT-N" tick-trader-percore-workspace/DOCS/tech-debt/open.md` | First matches; second NO match |
| PARITY closures marked | For each `PARITY-NNN` claimed closed: `rg -A3 "^id: PARITY-NNN" tick-trader-percore-workspace/DOCS/PARITY_ISSUES.md` | Shows `status: closed` |
| DESIGN_SPECS Stage promotions | For each cited Stage X→Y: `grep "^stage:" tick-trader-percore-workspace/DESIGN_SPECS/<path>.md` | Shows promoted stage |
| NEW memory files exist + indexed | For each cited: file exists at `memory/<name>.md` AND `grep <name>.md MEMORY.md` returns match | Both succeed |
| NEW going-forward rules in CLAUDE.local.md | For each rule: `grep -A2 "<rule-title>" CLAUDE.local.md` | Returns match in "Going-forward rules (index)" section |
| Version.hpp matches predecessor | `cat Version.hpp` (engine repo) | String matches predecessor-tag's claimed value at its ship close |

**Output classification:**
- ALL claims verified → CLEAN; proceed to Stage 5
- 1-2 LOW-severity failures (e.g., GPG-verify warning) → WARN; surface to operator; proceed to Stage 5
- ≥3 failures OR any HIGH-severity (TECH_DEBT-claimed-CLOSED still in `open.md`; cited memory file missing) → BLOCK; require operator triage before proceeding

**This step is OVERLAPPING with `/capture-audit` Check 1 (MEMORY.md sync) + Check 7 (DESIGN_SPECS promotion) + Check 8 (skill linkage) by design.** Stage 4.5 catches predecessor incompleteness BEFORE Stage 5 fires `/capture-audit --deep`; Stage 5 then catches drift since handoff write. Defense-in-depth at the handoff seam.

**If handoff body lacks a "What landed at <predecessor-tag>" section** (older handoffs predating /handoff Stage 2.8 codification): skip Stage 4.5 entirely; surface advisory note ("predecessor-context section missing; cannot verify predecessor claims mechanically") so receiver knows to verify manually.

### Stage 4.6: Decision-log status reconciliation (added 2026-05-30 — decided-vs-open ground truth)

Stages 4-4.5 verify git + artifacts but never surface the DECISION STATUS of the work being picked up. Without it, the receiver (or the composed `/readiness` auditor at Stage 6) can mistake an ALREADY-DECIDED item for an open blocker — especially when an in-flight plan's prose/frontmatter is STALE relative to the decision log. **Canonical failure (`.E` Session-4 pickup, 2026-05-30):** D-105 (rounding mode) was `<!-- STATUS: decided -->` in the log, but a stale foundation-doc frontmatter ("DRAFT pending 3 open decisions") + a `/readiness` subagent surfaced it as an "open blocker," and the receiver propagated it into the next-step framing. The decision sentinels are the SSoT (`feedback_session_decision_log_discipline`); this stage READS them so the receiver enters with an accurate decided/open map.

**Locate the log:** handoff frontmatter `decision_log:` field (fallback: the in-flight plan's `decision_log:`). Neither present (older handoffs) → skip with advisory ("no decision log cited; decision status unverifiable mechanically").

**Mechanical extraction (deterministic — run the grep; do NOT eyeball the log, per `feedback_run_doc_ci_tools_first_never_hand_verify`):**
```bash
rg -n "<!-- (D/C/F|STATUS):" "<decision_log_path>"
```
Pair each `<!-- D/C/F: D-NNN -->` with the following `<!-- STATUS: ... -->`; digest the decisions THIS handoff references (its `decision_log:` range / § core-decisions), STATUS text VERBATIM — the text carries nuance a bare decided/open flag loses (e.g. `decided (uniform-rounding incl. replay); rounding-MODE = research item` — later closed by a successor decision, so "decided-with-a-now-closed-subpart", not "open").

**Judgment cross-check — the contradiction surface** (mechanical→grep; judgment→here, per `feedback_independence_for_judgment_not_mechanical`): scan the in-flight plan body + handoff narrative for any decision the prose treats as OPEN (`open decision` / `TBD` / `pending` / `unresolved` / `to resolve` / `pending the N open decisions`) that the log marks `decided` → flag **STALE-PLAN-PROSE drift** (the plan lying about its own decision state — the exact thing that misleads pickup; recommend a frontmatter/body fix). Flag the converse too (log `open` but plan treats as settled).

**Output (feeds Stage 6 + Stage 8):**
- A compact **Decision status** digest: DECIDED count + the genuinely-OPEN/PENDING ones listed EXPLICITLY — these are the ONLY items the receiver must still DECIDE (frequently empty = "decisions done; the next move is execution, not a choice").
- STALE-PLAN-PROSE drift → WARN.
- **Pass the genuinely-open list into the Stage-6 `/readiness` invocation** as context, so the composed auditor does NOT re-flag a `decided` item as an open blocker (closes the propagation path of the canonical failure).

(Mechanical extraction may later fold into `tools/check_capture_audit.py` as a `--emit-decision-status` mode — sister to its Check 4 sentinel-MATCHING; the inline `rg` is the fast-path until then.)

### Stage 5: Mechanical doc/plan CI sweep (deterministic; per .D Phase F.6 + D-112/.E Session-4)

Run the **one-shot aggregator** as the receiver-side mechanical gate — it runs every doc/plan CI tool in one invocation (bidirectional+index memories / B-Plus session plan bodies / capture-audit mechanical [index-sync + sentinels + skill-linkage] / forward-promise / meta-registry). This is the SAME mechanical floor `/close-session` Stage 2.0 fires (writer + receiver symmetric). Per `feedback_run_doc_ci_tools_first_never_hand_verify` — run the tool, never hand-verify.

```bash
# ONE command (the receiver-side mechanical sweep — D-112 wiring):
/home/caramel/code/FoxML_Trader_v2/tools/check_session_docs.sh
# Exit 0 = all HARD checks pass. Exit 1 = HARD failure (citation error / one-way sister / orphan) → classify per severity below.
# Includes Check 11 forward-promise; for the handoff-anchored window specifically:
python3 /home/caramel/code/FoxML_Trader_v2/tools/check_forward_promise_audit.py \
    --since "${HANDOFF_WRITE_COMMIT:-HEAD~5}"

# Exit code != 0 → drift detected; classify per severity below
```

Severity classification:
- HIGH severity findings: BLOCK; require fix before continuing
- MED/LOW: WARN; surface for operator awareness
- INFO: tracking only; informational

Sister to /handoff Stage 1.8 + /close-session Stage 2/4 (same tool; mechanical at every handoff-related surface). LLM no longer orchestrates the detection — Python tool runs deterministically; LLM synthesizes findings narrative for operator review.

### Stage 6: Invoke /readiness against in-flight plan body

Run `/readiness <in-flight-plan-body-path>` to verify plan is still GREEN for coding.
- GREEN: proceed to Stage 7
- YELLOW: surface findings; operator decides
- RED: BLOCK; substantive fixes needed before coding

### Stage 7: Recreate TaskList from handoff Stage 1.5 capture

For each task entry in handoff TaskList table:
- Call `TaskCreate` with subject + description
- Set status per table (completed / in_progress / pending)
- Match task IDs to handoff IDs where possible

If TaskList table absent: WARN — operator may need to manually create tasks.

### Stage 8: Output PICKUP-READY status

Structured report:

```
=== /accept-handoff REPORT for <ship-tag> ===

Handoff source: plans/<sprint>/handoffs/<filename>.md
Handoff written: <date>
Files loaded: <N> cited; <M> always-loaded baseline

Git state verification:
  ✅ Engine HEAD: <sha> (matches handoff)
  ✅ Workspace HEAD: <sha> (matches handoff)
  ✅ Branch: <branch>
  ✅/⚠️/❌ Working tree: <clean|dirty>

Capture-audit:
  ✅/⚠️/❌ <N findings>; full report at plans/<sprint>/capture-audit-reports/<date>-accept-handoff.md

Decision status (Stage 4.6, vs decision log):
  ✅ <D> decided · ⚠️ <O> still OPEN: <explicit list, or "none — decisions done; next move is execution, not a choice">
  ⚠️ STALE-PLAN-PROSE drift: <plan treats X as open but log marks it decided> (omit line if none)

Readiness:
  ✅/⚠️/❌ <verdict>; <N findings>

TaskList recreated:
  ✅ <N> tasks recreated from handoff Stage 1.5
  In-progress: #<id> <subject>
  Next pending: #<id> <subject>

=== PICKUP-READY ===

Your immediate next action: <derived from in-progress task / pending tasks / handoff "PENDING" section>

Specifically: <concrete step with file paths + line refs>

If anything above is BLOCK status, address before proceeding.
```

## Invocation

- `/accept-handoff` — auto-resolve to most recent handoff in active sprint
- `/accept-handoff <path>` — explicit handoff path
- `/accept-handoff --skip-audits` — load files + recreate TaskList but skip /capture-audit + /readiness (faster; risky)
- `/accept-handoff --dry-run` — report what would be loaded without actually loading

## Execution model (Layer 1 orchestrator)

ONE-WAY HIERARCHY. Skill composes /capture-audit + /readiness BY REFERENCE (runs them inline; doesn't spawn).

```
LAYER 1: ORCHESTRATION
  - Main session invokes /accept-handoff
  - Skill executes Stages 1-8 inline (Read + Bash + skill composition)

LAYER 2: COMPOSED SKILLS (run inline)
  - /capture-audit --deep (Stage 5)
  - /readiness (Stage 6)
```

If reading this spec inside an Explore subagent: return error. `/accept-handoff` is only invoked from main session because it mutates TaskList + reports to operator directly.

## Sister disciplines

- `/handoff` — writer side; this skill is the receiver side
- `/capture-audit` — drift check; invoked at Stage 5
- `/readiness` — plan body verification; invoked at Stage 6
- `feedback_session_decision_log_discipline` — the `<!-- D/C/F -->` + `<!-- STATUS -->` sentinel SSoT that Stage 4.6 reads; `/capture-audit` Check 4 verifies the sentinels are PAIRED, Stage 4.6 USES them to inform the receiver (decided-vs-open)
- `feedback_compaction_degrades_treat_handoffs_as_hints` — sister discipline (handoffs ARE hints; this skill structurally verifies them against current state)
- `feedback_structural_enforcement_when_memory_insufficient` (M7) — parent meta-discipline
- `structural-enforcement-when-memory-insufficient.md` — pattern body for Stage 6 escalation

## Anti-patterns this prevents

- Fresh session forgets to load CLAUDE.md / CLAUDE.local.md (auto-loaded baseline; skill still verifies)
- Fresh session forgets to read in-flight plan body (Stage 3 loads automatically)
- Fresh session relies on stale handoff claims (Stage 4 verifies git state)
- Fresh session jumps to coding without running /readiness (Stage 6 enforces)
- TaskList lost between sessions (Stage 7 recreates from handoff capture)
- Decision-capture drift accumulated mid-session (Stage 5 catches)
- Receiver treats an ALREADY-DECIDED item as an open blocker — or trusts stale plan prose/frontmatter over the decision log (Stage 4.6 surfaces decision-log STATUS; canonical `.E` Session-4 D-105 failure)

## Future enhancements

- Cache handoff parse state across multiple invocations within session
- Auto-detect when /accept-handoff should fire (e.g., conversation transcript shows session-pickup language)
- Composite mode that also runs `/post-ship-audit` if handoff indicates ship-close context
