Base directory for this skill: /home/caramel/code/tick-trader-percore-workspace/claude-skills/close-session

# /close-session — End-of-session ritual orchestrator (SENDER side; sister to /accept-handoff)

## Why this skill exists

End-of-session cleanup is multi-step + memory-driven discipline that has proven to drift at boundaries: even with `/handoff` SKILL.md spec calling out Stage 1.8 (`/capture-audit --deep` pre-write gate) + Stage 2.5 (`/readiness` verify-on-write) as load-bearing, sessions skip them under context-budget pressure, leaving codification gaps that operator pushback catches later.

Codified `2026-05-26` after 3-observation pattern at `v5.15.5.F.4d.1.B.4` v1.7.5 transition cycle:

1. **TECH_DEBT-vs-inline-fix scope drift** — B-Plus line-anchor extension initially proposed as TECH_DEBT entry; operator caught via "let's go ahead and fix this" (per `feedback_no_defer_for_effort`).
2. **D18 backwards-compat scope simplification** — engine_arch deletion initially scoped with preserve-and-deprecate surfaces; operator caught via "im not too concerned about backwards compat tbh" (which became NEW memory `feedback_backwards_compat_not_default_concern`).
3. **D18 memory-file codification gap** — D18 decision captured in decision log + handoff doc but NOT formalized as standalone memory + going-forward rule; operator caught via "are you sure we arnt forgetting anything".

Each pushback was a step the session-close ritual SHOULD have caught earlier. Per M7 (`structural-enforcement-when-memory-insufficient.md`): when memory codification + skill-spec discipline proves insufficient at observation, escalate to structural enforcement. `/close-session` is that structural enforcement at the session-close surface.

## What this skill does (sequential stages)

### Stage 1 — Pre-flight context load

1. Detect active sprint via `Version.hpp` (sister to `/handoff` Stage 1)
2. Detect in-flight plan body via glob: `plans/<active-sprint>/subplans/*<ship-tag>*.md`
3. Read sprint MASTER + plan body frontmatter for state context
4. Detect engine + workspace HEAD SHAs + working tree status
5. Read most recent handoff doc (if any) — establishes baseline for drift detection

### Stage 2 — mechanical doc/plan CI sweep + forward-promise gate (deterministic; per .D Phase F.4 + .E Session-4)

**Stage 2.0 — the one-command doc/plan sweep (HARD gate; NEW v5.15.5.F.4d.1.E Session-4, 2026-05-30).** Run the aggregator FIRST — it is the SINGLE mechanical answer to "are the session's docs/plans clean?" (the recurring tiredness this stage removes). It runs every doc/plan CI tool in one shot: bidirectional+index memories check (the red-build catcher) + B-Plus plan-body symbol existence over session-modified workspace plan bodies (the broken-citation catcher) + forward-promise + meta-registry advisories.

```bash
# ONE command — replaces N hand-run checks (the structural fix for "I keep hand-verifying"):
/home/caramel/code/FoxML_Trader_v2/tools/check_session_docs.sh
# Exit 0 = all HARD checks pass. Exit 1 = a HARD check failed (citation error / one-way sister) → FIX before close.
# --all-plans for a full sweep (slower). Bypass a single check via SKIP_BIDIR_CHECK / SKIP_PLAN_BODY_CHECK.
```

**Why this exists (the gap it closes):** plan bodies + memories live in the WORKSPACE repo (committed via `/sync-workspace`), but the engine pre-commit hook (B-Plus etc.) only fires in the ENGINE repo where `plans/` is gitignored → the engine hook NEVER gates workspace doc commits, and the bidirectional-memories check was in no hook at all. So a broken plan-body citation (`CoreFrameworks/` prefix dropped) and a one-way memory sister-link survived an entire session of hand-assertion at `.E` Session-4. This aggregator + its wiring here is the structural close (M7): the agent no longer relies on remembering to hand-run the tools. Per `feedback_run_doc_ci_tools_first_never_hand_verify`. Sister: the engine `tools/hooks/pre-commit` (same tools, engine-repo surface).

**Stage 2.1 — Check 11 forward-promise** (deterministic hard gate; also inside the aggregator above, re-stated here for the LLM narrative + Stage 3 triage). If HIGH findings: surface for triage at Stage 3.

```bash
# Deterministic invocation — replaces LLM-orchestrated Skill invocation:
python3 /home/caramel/code/FoxML_Trader_v2/tools/check_forward_promise_audit.py \
    --since "${LAST_TAG:-HEAD~5}"

# Exit code != 0 → drift detected; proceed to Stage 3 triage
# Sister to /handoff Stage 1.8 gate (same tool; same drift class)
```

The above replaces the prior LLM-orchestrated `/capture-audit --deep` invocation; LLM still synthesizes findings narrative + drives Stage 3 triage with operator, but the detection layer is now mechanical (per `feedback_structural_enforcement_when_memory_insufficient` M7 escalation).

The deep gate's 12-check drift verification surfaces (Checks 1-10 enumerated below; Check 11 = forward-promise auto-write + Check 12 = amendment-cascade are detailed in the `/capture-audit` spec):

- (1) `MEMORY.md` index sync — every memory file has an index entry
- (2) Plan body frontmatter completeness (`audit_tier:` + `decision_log:` + `sister_specs:`)
- (3) Decision log artifact existence at expected path
- (4) Sentinel matching (`<!-- D/C/F: <id> --> + <!-- STATUS: <state> -->` in plan body)
- (5) Handoff doc currency (PENDING items vs git log; stale claims)
- (6) Stage 6 promotion candidates per M7 escalation criteria
- (7) DESIGN_SPECS Stage 2→3 promotion eligibility
- (8) Skill-in-CLAUDE.md-suite linkage (every NEW skill cross-referenced)
- (9) Memory→DESIGN_SPECS sister cross-ref completeness (every NEW memory pairs with a spec OR explicitly is operator-collaboration-only)
- (10) `CLAUDE.local.md` going-forward rules currency (recent operator preferences captured)

### Stage 3 — Operator triage + fix iteration

For each `/capture-audit` finding:

- **HIGH severity**: BLOCK — surface to operator + apply fix inline
- **MED severity**: WARN — surface + operator decides (fix now / defer with rationale / dismiss)
- **LOW + INFO**: document in close-out report; usually defer

Common findings + their fixes:
- "D-N captured in decision log but no memory file" → write NEW memory file + MEMORY.md index entry + CLAUDE.local.md going-forward rule
- "Plan body frontmatter missing audit_tier" → amend frontmatter
- "Skill mentioned in commit but not in CLAUDE.md suite table" → amend CLAUDE.md
- "Memory amended but description in MEMORY.md index is stale" → update index
- "Handoff doc cites paths that don't exist" → fix paths or remove stale citations

### Stage 4 — Re-fire `/capture-audit --deep` (verify clean; deterministic invocation per .D Phase F.4)

After applying fixes, re-run the mechanical detection to verify CLEAN:

```bash
python3 /home/caramel/code/FoxML_Trader_v2/tools/check_forward_promise_audit.py --strict
```

Exit code 0 → CLEAN; proceed to Stage 5. Exit code != 0 → loop back to Stage 3.

Exit condition: `/capture-audit --deep` returns CLEAN OR operator explicitly accepts remaining findings (e.g., known-deferred-to-Phase-D items).

### Stage 4.5 — Meta-error harvest (structured reflection → meta-anti-pattern-index) [NEW v5.15.5.F.4d.1.E.0.2]

The POPULATION mechanism for the meta-anti-pattern catalog (`DESIGN_SPECS/meta-disciplines/meta-anti-pattern-index.md`). Unlike Stage 2/4 (mechanical drift greps), this stage is JUDGMENT-LADEN — a structured reflection, not a scan (meta-error detection can't be pure-grepped). Rationale: `feedback_operator_pushback_as_audit_signal` § generative dimension — the session's own pushbacks/errors are the highest-signal seed corpus (the `.E.0.1` seed cohort was 3/5 from one hour of pushback).

**Reflection prompts (walk each; name the SHAPE, not the one-off fix):**
1. **Audit-reasoning (AR):** Did I dismiss a risk / bound scope via a property over a set I didn't enumerate (AR-1)? Did a spec/gate-definition bake in a categorical claim ("all", "every", "always") without listing the set (AR-2)?
2. **Cascade (CP):** Did a decision/spec/definition amendment this session need manual propagation to sibling docs (CP-1)? (If yes → it's also a Check 12 gap; note it.)
3. **Workspace-hygiene (WH):** Did a memory link / index pointer / cross-ref drift (WH-1/WH-2)?
4. **Planning (PL):** Did operator pushback surface a recurring planning shape (scope-flip, premature-defer, abstract-over-concrete) — not just a one-off correction?

**For each RECURRING shape surfaced:**
- Matches an existing catalog row → bump it + append a Source line (the new instance).
- NEW + recurring → add a row per the index schema (ID category-prefix + Shape + home + Detection + Enforced-by + Source + false-positive surface).
- One-off (not recurring, no pattern) → do NOT catalog (anti-ceremony per `.E.0.2` R3).

**Write target:** `DESIGN_SPECS/meta-disciplines/meta-anti-pattern-index.md` (the harvest is its WRITE path; Check 12 + the hardened gate are its READ paths). New/bumped rows land BEFORE Stage 6 `/handoff` (so the handoff reflects them) + Stage 7 `/sync-workspace` (so they're pushed).

**Anti-ceremony guard:** if a close produces only trivial one-offs, write nothing — yield-as-signal (a quiet harvest = mature apparatus; a spike = a new meta-error class slipped in → M7 escalation).

### Stage 5 — `/readiness` against in-flight plan body (planning-state ships only)

If close is at a planning-state boundary (vs post-coding mid-ship checkpoint), fire `/readiness <plan-path>` to verify plan body still GREEN. Skip for code-state close (where plan body amendment is done; just need to capture state).

Detection heuristic: if plan body version has bumped since last close OR substantive decisions landed since last close, fire `/readiness`.

### Stage 5.5 — Independent deliverable-completeness review [NEW v5.15.5.F.4d.1.E.0.2 / D-79]

Verify the SESSION'S substantive deliverables ACTUALLY landed complete + coherent on disk — by INDEPENDENT eyes, not self-attestation. Distinct from Stage 2/4 (mechanical capture-audit drift) + Stage 4.5 (meta-error harvest): this is a CONTENT-completeness + cross-artifact-COHERENCE pass. It is the close-session analog of `/precoding-audit-gate` Stage 3.5 (the verification pass) — same anti-self-attestation principle: **the agent that BUILT the work is prone to confirming "I did X" from memory rather than verifying X landed; an agent with no stake reports only what's on disk.** Sister: `feedback_golden_master_over_reimplemented_oracle` (verify the real artifact) + the AR-1 verify-don't-assume discipline (meta-anti-pattern-index).

**When to fire (heavier-default per D-77; NEVER agent-self-skipped — `feedback_never_skip_thoroughness_unless_explicit` / catalog PL-2):**
- FIRE BY DEFAULT for any substantial multi-artifact session — a subsystem/ship build, ≥~4 substantive artifacts, or any HIGH-RISK build. The orchestrating agent does NOT self-skip it on a judgment that it's "redundant" or "already covered."
- It fires on UN-reviewed work: a prior independent review of OTHER work this session does NOT excuse skipping the review of NEW work — close-out artifacts that land AFTER a build review still need their own pass (`.E.0.2` close caught this exact hole: skipped "because 2 reviews ran," but the harvest/memories/handoff were unreviewed).
- SKIP ONLY on EXPLICIT operator instruction — the `--no-review` flag, or the operator stating "skip it." Trivial closes (single-file / doc-tiny / pure checkpoint) are the OPERATOR's call to skip, not the agent's.

**Executor mode (operator-selectable per `feedback_runtime_executor_mode_for_judgment_skills`; default `independent`):** `independent` = spawn the reviewer agent (default — the anti-self-attestation point); `self` = the orchestrator self-reviews inline (cheaper, NO independence — operator-EXPLICIT only); `both` = run self + independent and compare verdicts (max rigor / calibration). Surface as an inline `{independent | self | both}` choice when the operator is at the decision point; otherwise default `independent`.

**Dimensions the reviewer checks** (each = a distinct failure mode a completeness-only pass misses):
1. **Landed + substantive** — each claimed deliverable is present + real content, not a stub.
2. **Coherent + fully propagated** — artifacts agree with each other AND each operator decision reached ALL its homes (decision-log + memory + MEMORY.md index + the skill/spec it governs + CLAUDE.local.md if a going-forward rule). A decision in the log but not wired into the skill it governs = half-landed. Complements `/capture-audit` Check 12 (mechanical stale-ref scan) with the judgment "did it fully land."
3. **No fabrication** — no tool / symbol / file cited as runnable-or-real that doesn't exist on disk.
4. **Edits were surgical** — the touched files' PRE-EXISTING + adjacent content is intact (an additive-looking edit can silently clobber a neighbor); *completeness checks new content arrived, this checks old content survived*. Includes the **WH-2 stale-index check**: no always-loaded index (MEMORY.md / sprint-state / MASTER) left pointing at superseded state.
5. **Meets the bar** — deliverables satisfy the plan's OWN acceptance criteria, not merely exist (N/A if no acceptance-criteria'd plan).
6. **Right side of the privacy boundary** — new/moved artifacts on the correct public-AGPL vs private-workspace side (a doc referencing private plans/handoffs must NOT land in the public tree).

(Considered + deferred: *operator-decision fidelity* — do artifacts match what the operator ACTUALLY decided vs agent drift; partly covered by #2/#5; add when intent-drift recurs + the checklist can encode the operator directives.)

**Procedure:**
1. **Build the deliverable checklist from the session's ACTUAL changes** — `git diff` (engine + workspace) for touched files + the decision-log entries (D-N) added + NEW memories + plan amendments. Each becomes a checklist item with its expected content markers.
2. **Spawn ONE independent reviewer** (general-purpose subagent) with: the checklist + file paths + skeptical criteria (content present + SUBSTANTIVE + complete + internally coherent; cite file:line; flag fabrications / stubs / cross-artifact incoherence). The reviewer has NO stake — it reports only what the files contain — and **does NOT fix anything**.
3. **Reviewer returns** VERIFIED / PARTIAL / MISSING per item + a cross-coherence check + an overall verdict.
4. **Triage** (like Stage 3): PARTIAL/MISSING → fix inline → re-verify the fixed items; VERIFIED → proceed. The result feeds the Stage 8 report.

### Stage 6 — `/handoff` (compose + write handoff doc)

Invoke `/handoff <ship-tag>` via Skill tool. `/handoff` internally runs its own Stages 1.5-4.5 + writes the doc to workspace path:
`plans/<sprint>/handoffs/<YYYY-MM-DD>-<ship-tag>-<descriptor>-handoff.md`

If `/handoff` errors (e.g., plan body has substantial gaps): HALT and surface to operator.

### Stage 7 — `/sync-workspace` (push everything)

Invoke `/sync-workspace` via Skill tool. Pushes:
- Plans (decision log + plan body + handoff doc + plan_checks audit synthesis docs)
- Memory backups
- CLAUDE.local.md backup
- Any other gitignored workspace-mirrored content

If push fails (auth / merge conflict / etc.): surface to operator. Don't retry blindly.

### Stage 8 — Final close-out report

Print structured report:

```
=== /close-session REPORT for <ship-tag> ===

Pre-flight state:
  Engine HEAD: <sha> (N commits ahead of origin per per-ship-close-push workflow)
  Workspace HEAD: <sha> (pushed)
  Tests: <count>/0

Stages executed:
  ✅ /capture-audit --deep (first pass)  — N findings
  ✅ Triage + fix iteration             — N findings addressed
  ✅ /capture-audit --deep (verify)     — CLEAN
  ✅ /readiness (if planning close)    — <verdict>
  ✅ Independent review (Stage 5.5; if substantial) — <N> deliverables VERIFIED / <N> PARTIAL fixed
  ✅ /handoff                           — written to <path>
  ✅ /sync-workspace                    — pushed to <remote>

Handoff doc:
  Path: plans/<sprint>/handoffs/<filename>.md
  Pickup command: /accept-handoff <path>

What landed this close:
  NEW memories: <list>
  Amended docs: <list>
  Decision log entries: <D-IDs / C-IDs / F-IDs>
  Codifications: <list>

Authoritative next-session entry:
  /accept-handoff <full-path-to-handoff-doc>
```

## Invocation

- `/close-session` — auto-resolve active sprint + in-flight ship via `Version.hpp`
- `/close-session <ship-tag>` — explicit ship tag if ambiguous
- `/close-session <ship-tag> --no-handoff` — skip Stage 6 if no handoff needed (e.g., quick checkpoint sync without session pickup)
- `/close-session <ship-tag> --planning-state` — fire Stage 5 `/readiness` (default skip if at code-state checkpoint)
- `/close-session --dry-run` — Stages 1-4 only (audit + triage); skip handoff + push

## Execution model (Layer 1 orchestrator)

ONE-WAY HIERARCHY. Compose sub-SKILLS by REFERENCE (invoke via Skill tool). The ONE exception that spawns a sub-AGENT is Stage 5.5 (independent deliverable-completeness review): its independence from the building agent IS the load-bearing property (anti-self-attestation), so it MUST be a separate agent, not self-review. No other stage spawns.

```
LAYER 1: ORCHESTRATION
  - Main session invokes /close-session
  - /close-session invokes sub-skills via Skill tool

LAYER 2: COMPOSED SKILLS
  - /capture-audit (Stage 2 + 4)
  - /readiness    (Stage 5; conditional)
  - /handoff      (Stage 6)
  - /sync-workspace (Stage 7)

LAYER 2 (spawned sub-agent — the one exception):
  - independent reviewer (Stage 5.5; general-purpose; spawned for INDEPENDENCE, conditional per gating)
```

If reading this spec inside an Explore subagent: return error. `/close-session` is only invoked from main session because it orchestrates handoff writing + workspace push (mutating effects).

## Sister disciplines

- `/accept-handoff` — RECEIVER side of handoff cycle; this skill is SENDER side
- `/handoff` — composes the handoff doc (invoked at Stage 6)
- `/capture-audit` — drift check (invoked at Stage 2 + Stage 4)
- `/sync-workspace` — push to remote (invoked at Stage 7)
- `/readiness` — plan body verification (invoked at Stage 5 conditionally)

Together: `/close-session` + `/accept-handoff` close the multi-session pickup loop. Both layers structurally enforce discipline that memory codification + manual ritual proved insufficient.

## Anti-patterns this prevents

- **"I composed the handoff doc but skipped formal /capture-audit"** — Stage 2 enforces; can't skip without explicit `--no-capture-audit` flag
- **Decision log entry captured but memory file missing** — Stage 2 Check 9 catches; Stage 3 triages
- **Skill mentioned in commits but not in CLAUDE.md suite table** — Stage 2 Check 8 catches
- **Plan body amendments not captured in handoff doc** — Stage 6 `/handoff` reads current plan body state, includes amendments
- **Workspace push forgotten after handoff write** — Stage 7 enforces
- **Operator-pushback-catches-gap recurrence pattern** — structural enforcement prevents recurrence

## When NOT to use

- Mid-coding (use `/sync-workspace` for quick checkpoint push instead; full close ritual is overkill)
- After single-file bug fix (no codification work; no handoff needed; just `/sync-workspace`)
- After `/accept-handoff` just ran (already in fresh state; nothing to close)
- For doc-only edits without decision-log entries (use `/sync-workspace` directly)

## When TO use

- End of substantial work session that landed N WIP-checkpoints
- After substantive amendment cycle that codified NEW memories / decisions / commitments
- Before handing off mid-ship work to fresh session (compaction event / day boundary)
- After ship close + before opening next ship in pipeline
- When operator asks "are you sure we aren't forgetting anything" — `/close-session` is the structural answer to that question

## Future enhancements

- Auto-detect "planning state" vs "code state" boundary for Stage 5 default
- Composite mode that also runs `/post-ship-audit` if closing post-ship (ship just tagged)
- Configurable check list (`--check-list <list>` to skip specific Stage 2 checks)
- Integration with `/plan-context-sweep` for cross-plan codification verification

## Pattern provenance

Codified `2026-05-26` at `v5.15.5.F.4d.1.B.4` v1.7.5 transition cycle close. 3-observation pattern of operator pushback catching codification gaps that memory + skill-spec discipline didn't prevent.

Per `feedback_structural_enforcement_when_memory_insufficient` (M7) + `feedback_motivated_collaborator_for_caramel`: when the system relies on operator-pushback to catch gaps, the system has a structural-enforcement gap. `/close-session` closes that gap at the session-close surface.

Sister codification: `/accept-handoff` (codified same cycle for the RECEIVER side of the loop; M7 first-canonical Stage 6 application).

## Cross-references

- `DOCS/DESIGN_PHILOSOPHY.md` § 11.5 (meta-discipline registry; M7 parent)
- `DESIGN_SPECS/meta-disciplines/meta-anti-pattern-index.md` (the META catalog Stage 4.5 harvest WRITES to)
- `~/.claude/projects/-home-caramel-code-FoxML-Trader-v2/memory/feedback_operator_pushback_as_audit_signal.md` (Stage 4.5 harvest rationale — § generative dimension) + `feedback_golden_master_over_reimplemented_oracle.md` (Stage 5.5 verify-the-real-artifact sister)
- `DESIGN_SPECS/meta-disciplines/structural-enforcement-when-memory-insufficient.md` (M7 first canonical)
- `claude-skills/accept-handoff/SKILL.md` (sister; receiver side)
- `claude-skills/handoff/SKILL.md` (composed at Stage 6)
- `claude-skills/capture-audit/SKILL.md` (composed at Stage 2 + 4)
- `claude-skills/sync-workspace/SKILL.md` (composed at Stage 7)
- `~/.claude/projects/-home-caramel-code-FoxML-Trader-v2/memory/feedback_session_decision_log_discipline.md` (sister memory)
- `~/.claude/projects/-home-caramel-code-FoxML-Trader-v2/memory/feedback_structural_enforcement_when_memory_insufficient.md` (M7 trigger memory)
