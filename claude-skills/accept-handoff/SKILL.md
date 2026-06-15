---
name: accept-handoff
skill_kind: mechanical
trigger_heuristics: ["fresh-session pickup / accept a handoff -> fire /accept-handoff (read + verify)"]
description: Receiver-side handoff verification skill. Fresh-session pickup runs ONE command to load handoff doc + all cited reference files + run drift-check + recreate TaskList + verify git state matches handoff claims + reconcile decision-log status (decided vs open). Closes the "fresh session forgets to load required reading" failure mode. Sister to /handoff (writer side); both close the multi-session pickup loop. Output: PICKUP-READY status + concrete "your next action is X" instruction. Always-on full arming (M8 session-arm): every pickup loads code-maps + nav-infra + surface DESIGN_SPECS + the anti-pattern catalog + a next-action surface kit (skills/tools/specs/invariants) — the operator never has to request it.
type: skill
concern: workflow
audit_cadence: per-session-start
tags: [doc-discipline, framework-discipline, operator-collaboration, meta-discipline]
surface: [handoff-pipeline, session-pickup]
sister_skills: [/handoff, /capture-audit, /readiness, /sync-workspace]
loads_dynamically: [CLAUDE.md, CLAUDE.local.md, memory/MEMORY.md, memory/MEMORY_EXTENDED.md, DOCS/DESIGN_PHILOSOPHY.md, target-handoff.md, cited-reference-files, in-flight-plan-body.md, decision-log.md, DOCS/CODE_MAP.md, dependency-graph-DAG, CANONICAL-FINDINGS.md, DOCS/TOOLS.md, DOCS/RECURRING_BUG_PATTERNS.md]
applies_meta_discipline: M7 (structural-enforcement-when-memory-insufficient) + M8 (definition-of-done-and-armed-scout-verification — session-arming applied to pickup)
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

## Always-on full arming (the operator never needs to ask for it)

> Codified 2026-06-12 at Caramel's directive (*"make all this part of the process — I'm tired of saying it, and I wanna make sure it always gets loaded and set into context"*). The recurring manual ask — *"load all the code-maps, consult the workspace for the design-specs / anti-patterns / DAG / skills / tools, and use the correct ones where appropriate"* — is now the skill's STANDING CONTRACT, not something to request per-pickup. Stages 3.2–3.7 load it; the Stage-8 report SURFACES it so it is visibly always-on.

**The frame: arm the SESSION the way M8 arms a subagent.** A fresh session picking up a handoff is in the *identical* blind position as a freshly-spawned verification subagent — it boots with nothing but the prompt (`definition-of-done-and-armed-scout-verification.md`, M8). M8's fix is to ARM the subagent before it executes: load the surface's reference-docs + the mechanical toolchain to RUN + the nav-infra + the domain skill, then scout, then execute. `/accept-handoff` IS that arming step applied to the whole session. Parity on facts + tooling; the operator keeps the judgment.

**The always-on arming set (every pickup, no request needed):**
1. **Code-maps + nav-infra** — CODE_MAP (regen), the DAG, the live finding/disposition register, TOOLS.md (Stage 3.6).
2. **Surface-matched DESIGN_SPECS** — cited (3.2) + keyword-triggered (3.3) + the in-flight plan's extract surfaces (3.4).
3. **Anti-pattern catalog** — `RECURRING_BUG_PATTERNS.md`, consulted for the Class IDs the work touches (Stage 3.6) — the known bug shapes the next edit must not reintroduce.
4. **Next-action surface kit** — the surface-matched skills + tools + specs + anti-pattern classes + invariants routed to the immediate next action (Stage 3.7), surfaced in the Stage-8 report. This is the *"use the correct ones where appropriate"* ask, made deterministic.

**Load vs consult — the discipline that keeps "mandatory" from blowing the context budget (and accelerating the very compaction this is meant to survive):** *mandatory* means the session ALWAYS routes through the arming set — NOT that every byte is dumped into context. Three tiers:
- **Always LOADED (full content):** the small + always-relevant — the baseline (CLAUDE.md / CLAUDE.local.md / MEMORY.md) + a freshly-regen'd CODE_MAP.
- **Always CONSULTED (mandatory routing, read-on-demand):** the tool index (TOOLS.md), the skill suite (CLAUDE.md lists it), the anti-pattern catalog, and — when the sprint has them — the DAG + findings index. Knowing they exist + reaching for them at the decision points IS the arming; the full file is grepped/read on demand, not pre-dumped.
- **Conditionally full-loaded (by surface keyword):** the heavy reference docs (STRATEGY_AND_CODING_RULES, latency audit, the DESIGN_PHILOSOPHY families) — loaded when the ship's surface matches (Stage 3.3), not every pickup.

Full-loading everything every time would eat the window the actual work needs + push the session toward compaction sooner — the opposite of the goal. So: consult-over-load for the indexes; full-load only the small-always-relevant + the surface-matched heavy docs.

If a pickup ever can't fully arm (a cited doc is missing, a tool errors), that's a SURFACED finding in the report — never a silent skip.

## What this skill does (sequential)

### Stage 1: Locate handoff doc

Resolution order — **explicit state first; mtime is only the transition-era fallback**:

1. **`<path>` arg given** → use it (explicit always wins — and this is how you resume a `deferred` / parked handoff directly, regardless of its status).
2. **Else: the handoff whose frontmatter is `status: active`** (the live-pickup pointer; the writer keeps exactly one — supersede-on-write, per `/handoff` Stage 6.0). Scan `plans/<active-sprint>/handoffs/*.md` (defensively, all `plans/**/handoffs/`) for a frontmatter `status: active`:
   - **exactly 1** → use it. **Auto-prioritize it — do NOT ask the operator to choose.** It's the deliberate live pointer.
   - **0 tagged** (legacy / none adopted the tag yet) → FALL BACK to most-recently-modified `*.md` (the old behavior; fine during the transition before handoffs carry the tag).
   - **>1** → ERROR: the `status: active` singleton invariant is violated (`tools/check_handoff_active_singleton.py` should have caught it at the last sweep). Surface ALL actives; do NOT guess.
3. **Surface (do NOT auto-pick) any `status: deferred` handoffs.** After resolving the active one, scan for `deferred` and print a one-line note: *"⏸ N parked (deferred): &lt;files&gt; — PAUSED because a different priority jumped the queue; resume one explicitly via `/accept-handoff &lt;path&gt;`, or it auto-resumes (deferred → active) when the current active work closes."* A deferred handoff is **never** auto-picked by no-arg, but the operator must SEE it so a park isn't forgotten. (If the guard reported "deferred + 0 active", that's the forgot-to-resume case — pick the deferred one explicitly, or promote it to `active`.)
4. **No handoff found at all** → ERROR — sprint must have at least one handoff.

Active sprint = detected from `Version.hpp` per `/handoff` Stage 1. Active-tag resolution is robust to filesystem **mtime resets** — a `git checkout`/`pull` can reset a whole batch of handoff mtimes to one timestamp (the exact fragility this replaces). Discipline: `DESIGN_SPECS/meta-disciplines/handoff-active-state-machine.md`.

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
- **Post-write ADDENDUM / correction block** — any `## ⏩ Addendum` / "AFTER this handoff was written" / "post-write" / "CORRECTED" section. This is content authored AFTER the main body that **SUPERSEDES** parts of it (a corrected root cause, later captures, a status flip). **The body below such a block may be STALE relative to it; the addendum WINS on any conflict.** Extract it + ALWAYS surface it at Stage 8 — a post-write correction that sits loaded-but-unsurfaced is the exact "actionable info lost to the void" failure (the `.E.0.10` A6 handoff carried a corrected TECH_DEBT-202 root cause in an addendum while the original body's wrong mechanism remained below it). If the addendum names a specific superseded claim, cross-check the body for that claim + flag it stale in the report.

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

**Stage 3.6 — Navigation-infra load (regen + consult the index maps so pickup + the Stage-6 completeness checks measure against the REAL surface set, not a hand-recalled one):**

The artifact existing ≠ the artifact being used — this stage routes pickup through the nav-infra (the M7 close of "the map sits there unread"). Per `DESIGN_SPECS/audit-methodologies/adversarial-multi-agent-audit-methodology.md` step 3:

- **ALWAYS — regen + consult CODE_MAP:** `./tools/gen_code_map.sh` (idempotent, <5s) → `DOCS/CODE_MAP.md`. Real `Pattern_FunctionName` file:line — the anti-fabrication ground truth (grep THIS to verify a handoff's cited symbols, never recall a line). Sister to `/readiness` Stage 2 + `/precoding-audit-gate` Stage 2.5 (both already regen it).
- **CONDITIONAL — load the INDEX, never the per-ship sidecars** (consult-indexes-before-full-reads): if the active sprint has a **dependency-graph DAG** (`plans/<sprint>/subplans/*-dependency-graph.md`) and/or a **findings corpus** (`plans/<sprint>/plan_checks/**/CANONICAL-FINDINGS.md` + the live disposition register), load the DAG + the deduped INDEX. The ~500KB per-ship sidecars stay grep-on-demand. These are the surface-set + already-found/dispositioned set that the Stage-6 `/readiness` completeness pass measures against — a completeness check fed only the plan headline re-derives a false floor (the `.E.0.10` net-completeness instance).
- **Tool index (ALWAYS consult — the always-CONSULT tier):** `DOCS/TOOLS.md` (every `tools/*` + disposition + invoker) — consult on EVERY pickup, do NOT wait to "need" a tool: knowing the inventory is what stops a session hand-rolling what a tool already does (and seeds the Stage-3.7 kit's mechanical-toolchain row). The full file is read-on-demand; the consult itself is mandatory.
- **Anti-pattern catalog (ALWAYS):** `DOCS/RECURRING_BUG_PATTERNS.md` — consult (grep, don't recite — registry-driven) for the Class IDs the in-flight/next work touches (the handoff + register usually name them, e.g. Class 25/26/27 for cfg-scope work; Class 44/45 for the exit-chain / reconstruct-path family). These are the known bug shapes the next edit must not reintroduce; they seed the Stage-3.7 surface kit + any `/bug-check` the next action routes to.

**Stage 3.7 — Next-action surface kit (route the immediate next action — the M8 session-arm):**

The operator's recurring *"use the correct skills / tools / specs where appropriate and needed"* is THIS stage, made deterministic. For the immediate next action (the in-progress task / the handoff's "NEXT ACTION" section), assemble + SURFACE its **surface kit** — everything the action needs to start ARMED instead of blind:

| Kit element | How to derive |
|---|---|
| **Domain skill(s)** | Map the action's MATERIAL to its skill (per M8 / `/decision-check` Stage 2.5): money → `/accounting-audit`; hot-path → `/hft-audit`; cfg/registry → `/trace-deps` + `/dod-audit`; ML → `/ml-audit`; train↔serve → `/parity-check`; a design DECISION → `/decision-check`; an unknown-size hunt → the relevant fan-out audit. Prefer the handoff's explicit routing when present; else derive from surface keywords. |
| **Mechanical toolchain** | The specific `tools/*.py` the action RUNS (from `DOCS/TOOLS.md` + the handoff) — name the command, e.g. `check_per_core_registry_integrity.py` for per-core cfg work. "Run the tool", not "read the code". |
| **DESIGN_SPECS** | The pattern/discipline docs governing the surface (cited + keyword-derived). |
| **Anti-pattern classes** | The `RECURRING_BUG_PATTERNS` Class IDs the action must not reintroduce. |
| **Invariants** | The H-numbers in play (e.g. H22 per-node purity; H4 money-math; H7/H8 hot-path). |

Output the kit in the Stage-8 report. If the next action is a design DECISION, the kit IS the `/decision-check` arming payload — hand the spawned agents the docs + toolchain + nav-infra + domain skill (M8 arming); withhold only the orchestrator's verdict from the adversarial half. Honors consult-before-coding: SURFACE the kit + SUGGEST the judgment skill (await the operator's go); mechanical tools may auto-run.

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
| NEW memory files exist + indexed | For each cited: file exists at `memory/<name>.md` AND `grep <name>.md MEMORY.md MEMORY_EXTENDED.md` returns match | Both succeed (indexed in either) |
| NEW going-forward rules | For each rule: `grep -A2 "<rule-title>" CLAUDE.local.md DOCS/GOING_FORWARD_RULES.md` | Returns match (Tier-0 collaboration in CLAUDE.local.md; Code&design/Process/Docs in GOING_FORWARD_RULES.md — TECH_DEBT-163) |
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

⏩ POST-WRITE CORRECTIONS (addendum block — surface FIRST; omit line if none):
  <one line per superseding fact — e.g. "TD-202 root cause CORRECTED: the join is not missing, it's defeated by a test double-init; body's earlier 'never joined' phrasing is STALE">
  ⚠️ The handoff body PREDATES these — the addendum WINS on any conflict. Read the corrections before trusting the body.

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

Loaded-context manifest (always-on arming — Stage 3):
  ✅ Nav-infra: CODE_MAP (<N> fns, regen) · DAG · finding/disposition register · TOOLS.md
  ✅ Surface DESIGN_SPECS: <list>
  ✅ Anti-pattern classes consulted: <Class IDs> · Invariants in play: <H-numbers>

Next-action surface kit (the routed "correct ones" — Stage 3.7):
  Skills: <surface-matched skills, handoff-routed if present>
  Tools:  <mechanical toolchain to run>
  Specs:  <governing DESIGN_SPECS>
  Anti-patterns: <Class IDs not to reintroduce> · Invariants: <H-numbers>

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
- `definition-of-done-and-armed-scout-verification.md` (M8) — the **armed scout-first** discipline this skill applies to the SESSION (Stages 3.6/3.7 = arm-then-scout); pickup arms the session exactly as M8 arms a subagent
- `adversarial-multi-agent-audit-methodology.md` — the canonical agent-arming + cross-check step a judgment next-action (e.g. `/decision-check`) is routed into by Stage 3.7
- `feedback_auto_route_input_to_matching_skill` — Stage 3.7's routing is the pickup-surface application (SUGGEST judgment skills + await go; auto-run mechanical ones)

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
- **Mechanical surface-kit emitter** — derive the Stage-3.7 next-action kit (skills/tools/specs/invariants) deterministically from the handoff's routing block + a keyword→skill/tool/spec map table, instead of LLM-synthesis. Sister to the Stage-4.6 `--emit-decision-status` candidate; both could extend `check_capture_audit.py` or land as a new dedicated pickup-kit emitter tool (enroll it in `DOCS/TOOLS.md` when built).
