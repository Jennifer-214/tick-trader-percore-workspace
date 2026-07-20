---
name: close-session
skill_kind: mechanical
trigger_heuristics: ["ready to wrap up / end the session -> suggest /close-session"]
description: End-of-session ritual orchestrator (SENDER side; sister to /accept-handoff). Composes the mechanical doc/plan sweep + /capture-audit --deep + /readiness (conditional) + /handoff + /sync-workspace into one end-of-session close, so codification that drifts under context-budget pressure is captured deterministically.
type: skill
concern: workflow
sister_skills: [/accept-handoff, /handoff, /capture-audit, /readiness, /sync-workspace]
established: 2026-05-26
---

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

**Why this exists (the gap it closes):** plan bodies + memories live in the WORKSPACE repo (committed via `/sync-workspace`), but the engine pre-commit hook (B-Plus etc.) only fires in the ENGINE repo where `plans/` is gitignored → the engine hook NEVER gates workspace doc commits, and the bidirectional-memories check was in no hook at all. So a broken plan-body citation (`CoreFrameworks/` prefix dropped) and a one-way memory sister-link survived an entire session of hand-assertion at `.E` Session-4. This aggregator + its wiring here is the structural close (M7): the agent no longer relies on remembering to hand-run the tools. Per `feedback_run_doc_ci_tools_first_never_hand_verify`. Sister: the engine `.githooks/pre-commit` (the tracked, git-run pre-commit hook via `core.hooksPath=.githooks` — same tools, engine-repo surface; consolidated .E.0.1).

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

- (1) memory index sync — every memory file indexed in `MEMORY.md` OR `MEMORY_EXTENDED.md` (TECH_DEBT-163 split; guard spans both)
- (2) Plan body frontmatter completeness (`audit_tier:` + `decision_log:` + `sister_specs:`)
- (3) Decision log artifact existence at expected path
- (4) Sentinel matching (`<!-- D/C/F: <id> --> + <!-- STATUS: <state> -->` in plan body)
- (5) Handoff doc currency (PENDING items vs git log; stale claims)
- (6) Stage 6 promotion candidates per M7 escalation criteria
- (7) DESIGN_SPECS Stage 2→3 promotion eligibility
- (8) Skill-in-CLAUDE.md-suite linkage (every NEW skill cross-referenced)
- (9) Memory→DESIGN_SPECS sister cross-ref completeness (every NEW memory pairs with a spec OR explicitly is operator-collaboration-only)
- (10) going-forward rules currency — `CLAUDE.local.md` (Tier-0 collaboration) + `DOCS/GOING_FORWARD_RULES.md` (the full Tier-2 index)

### Stage 3 — Operator triage + fix iteration

For each `/capture-audit` finding:

- **HIGH severity**: BLOCK — surface to operator + apply fix inline
- **MED severity**: WARN — surface + operator decides (fix now / defer with rationale / dismiss)
- **LOW + INFO**: document in close-out report; usually defer

Common findings + their fixes:
- "D-N captured in decision log but no memory file" → write NEW memory file + index it BY TIER (collaboration/judgment/user/project → `MEMORY.md`; deep-technical/process → `MEMORY_EXTENDED.md`) + the going-forward rule BY TIER (every-turn collaboration → `CLAUDE.local.md`; Code&design/Process/Docs → `DOCS/GOING_FORWARD_RULES.md`) — TECH_DEBT-163 tiering; do NOT re-bloat the always-loaded docs
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

### Stage 4.6 — Session-issue fix-sweep: FIX the fixable-now before close (don't just log) [NEW v5.15.5.F.4d.1.E.0.10]

The close's bias is **FIX, not LOG.** Enumerate EVERY issue the session surfaced — not only the Stage-3 `/capture-audit` mechanical findings and the Stage-4.5 meta-shapes, but ALSO the tooling false-positives / gaps the session hit, doc / SSoT-index drift (e.g. a stale MASTER banner), guard gaps, and half-applied conventions. For each, apply the close-out-now test:

- **Fixable-now** (small + in-context + does NOT change the handoff / plans / capital-path) → **FIX IT NOW.** Do NOT log it as a TECH_DEBT-to-defer. A CI guard, a doc/index fix, a tooling false-positive carve-out is fixable-now by default — and a built guard COMPOUNDS where a logged TECH_DEBT just waits (`feedback_guards_compound_enforcement_is_leverage`).
- **Genuinely-separate DELIVERABLE** (its own ship / scope) OR **capital-code needing a focused fresh-context cycle** → defer with a HOME (TECH_DEBT / a plan / the handoff). Defer is the EXCEPTION, decided on merit (`feedback_deferral_reasons_merit_not_effort_or_context`), never the default.

PROACTIVE + DEFAULT: the agent runs this fix-sweep ITSELF — it must NOT wait for operator pushback ("fix them, don't log them"; "scan EVERYTHING, not top-N"). Codified `.E.0.10` 2026-06-13 as the M7 escalation of `feedback_close_out_now_over_defer_when_small`: despite that memory, the session LOGGED TECH_DEBT-193/194 (a B-Plus design-plan false-positive + the MASTER-staleness guard) and left MASTER stale, and the operator had to prompt both the fix-sweep AND the exhaustive (not-top-N) capture-scan. Memory proved insufficient → this structural close-ritual step is the enforcement. Sister: Stage 4.5 (catalogs the SHAPE; THIS fixes the INSTANCE) + `feedback_close_out_now_over_defer_when_small` + `feedback_no_defer_for_effort`.

After the fix-sweep, re-run Stage 2.0's `check_session_docs.sh` → confirm SWEEP CLEAN (the fixes landed; no new drift).

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
2. **Coherent + fully propagated** — artifacts agree with each other AND each operator decision reached ALL its homes (decision-log + memory + the memory index (MEMORY.md or MEMORY_EXTENDED.md by tier) + the skill/spec it governs + the going-forward index (CLAUDE.local.md Tier-0, or GOING_FORWARD_RULES.md, by tier)). A decision in the log but not wired into the skill it governs = half-landed; a decision made in-conversation but NEVER reaching the log at all (lived only in the register / handoff / TECH_DEBT) = **un-logged** — so ARM the reviewer with the session's operator-decision list + have it verify EACH decided item has a decision-log `D-N` entry (the conversation→log direction), not merely check downstream propagation of the ones already logged (the `.E.0.10` D-220 recurrence: the A6 SHALT-vs-degrade decision landed in register/TD-171/handoff but skipped the decision-log — caught by operator "are u sure", not the review; AR-8). Complements `/capture-audit` Check 12 (mechanical stale-ref scan) with the judgment "did it fully land."
3. **No fabrication** — no tool / symbol / file cited as runnable-or-real that doesn't exist on disk.
4. **Edits were surgical** — the touched files' PRE-EXISTING + adjacent content is intact (an additive-looking edit can silently clobber a neighbor); *completeness checks new content arrived, this checks old content survived*. Includes the **WH-2 stale-index check**: no always-loaded index (MEMORY.md / sprint-state / MASTER) left pointing at superseded state.
5. **Meets the bar** — deliverables satisfy the plan's OWN acceptance criteria, not merely exist (N/A if no acceptance-criteria'd plan).
6. **Right side of the privacy boundary** — new/moved artifacts on the correct public-AGPL vs private-workspace side (a doc referencing private plans/handoffs must NOT land in the public tree).
7. **Generated-index currency** (ARM the reviewer with this — `.E.1.1` recurrence 2026-06-21: BOTH the close report AND the first independent reviewer missed `CODE_MAP.md` left stale @ the PRE-change commit, because neither was armed to check it). Any GENERATED/derived index, ledger, or baseline the change INVALIDATES must be REGENERATED to the post-change state, not just "modified once early": `DOCS/CODE_MAP.md` (regen `gen_code_map.sh` — note its "Last regenerated: commit X" header must == HEAD), `DESIGN_SPECS/README.md` + `TAG_INDEX.md`, `tools/*baseline*.txt`, `identifier_ledger.txt`, `MANUAL_FIELDS_INVENTORY.md`. Grep each for residual PRE-change tokens. Distinct from #4's WH-2 (always-loaded indexes); this is the GENERATED-artifact class. The accept-handoff Stage 3.6 regen reflects the PICKUP commit — if work landed AFTER it, the index is stale-by-construction.
8. **Deferred-work executor-coverage** (ARM the reviewer — `.E.1.1` recurrence: the ship-close doc-sweep named `check_doc_rename_classification.py`, whose tokens STRUCTURALLY EXCLUDE the code-symbol cohort it was assigned → the named executor literally couldn't do the deferred job). For EACH deferred / ship-close item, verify the NAMED tool/path can ACTUALLY do the work (the deferral is HOMED-AND-ARMED, not homed-to-an-incapable-executor). A finding correctly sequenced-to-later but pointed at a tool that can't see it WILL silently slip.

(Considered + deferred: *operator-decision fidelity* — do artifacts match what the operator ACTUALLY decided vs agent drift; partly covered by #2/#5; add when intent-drift recurs + the checklist can encode the operator directives.)

**Procedure:**
1. **Build the deliverable checklist from the session's ACTUAL changes** — `git diff` (engine + workspace) for touched files + the decision-log entries (D-N) added + NEW memories + plan amendments. Each becomes a checklist item with its expected content markers.
2. **Spawn ONE independent reviewer** (general-purpose subagent) with: the checklist + file paths + skeptical criteria (content present + SUBSTANTIVE + complete + internally coherent; cite file:line; flag fabrications / stubs / cross-artifact incoherence). The reviewer has NO stake — it reports only what the files contain — and **does NOT fix anything**.
3. **Reviewer returns** VERIFIED / PARTIAL / MISSING per item + a cross-coherence check + an overall verdict.
4. **Triage** (like Stage 3): PARTIAL/MISSING → fix inline → re-verify the fixed items; VERIFIED → proceed. The result feeds the Stage 8 report.

### Stage 6 — `/handoff` (compose + write handoff doc)

**Stage 6.0 — RESUME a deferred handoff if THIS work was a detour.** Before composing a fresh handoff, check whether the session's current `status: active` handoff carries a `defers: <parked>` field. If it does, this work was a *detour* that PARKED another work-line — so closing it means **resuming the parked one**, not writing a brand-new handoff:
- flip `<parked>` from `status: deferred` → `status: active` (it becomes the next pickup),
- flip the current (detour) handoff → `status: superseded` (it's done),
- refresh the resumed handoff's `engine_head` / state lines if they drifted while the detour ran,
- verify `tools/check_handoff_active_singleton.py` now reports exactly 1 active (the resumed one).

Then SKIP the fresh-handoff write below — the resumed handoff IS the next-session entry. Otherwise (no `defers:`), proceed normally:

Invoke `/handoff <ship-tag>` via Skill tool. `/handoff` internally runs its own Stages 1.5-4.5 + writes the doc to workspace path:
`plans/<sprint>/handoffs/<YYYY-MM-DD>-<ship-tag>-<descriptor>-handoff.md`

If `/handoff` errors (e.g., plan body has substantial gaps): HALT and surface to operator.

### Stage 6.5 — THE JUDGMENT HALF (MANDATORY; full text in the ⚠️ section below)

The handoff now EXISTS (Stage 6), so it can be judged. Run, in order:

```bash
python3 tools/check_close_out_completeness.py     # both halves; ADVISORY exit, HIGH findings are not
```

1. **Every auto-write surface** touched or explained (mechanical; the tool decides).
2. **Answer all 8 judgment checks explicitly**, in greppable `Check N` form, in the handoff.
3. **No volatile counts in prose** — anchors only. Discharge history with `VOLATILE-OK`, never by
   deleting the check.
4. **Independent adversarial review of the handoff** (AR-8). NOT the author. Record the verdict.

**Do not proceed to Stage 7 with HIGH findings open.** A push freezes the handoff as the thing the
next session reads. → full rationale in the ⚠️ Stage 6.5 section below.

### Stage 7 — `/sync-workspace` (push everything) — **INVOKE THE SKILL; DO NOT HAND-ROLL**

> **⚠️ Observed 2026-07-20.** This stage was hand-rolled — `cp` the memory files, `git commit`,
> `git push` — because that *looks* equivalent. It is not. `/sync-workspace` runs
> `tools/migrate_memory_frontmatter.py --apply` (canonicalizes the block/inline frontmatter the
> harness mangles on agent-written memories, and re-derives sister links from body `[[links]]`) and
> then gates on `tools/check_doc_metadata.py --bidirectional --memories`. Hand-rolling skipped both.
> When finally run, the canonicalizer healed **7 files — 4 of which the manual pass never opened.**
>
> The skip was invisible because hand-fixing WORKED every time it was tried. That is the signature of
> this whole gap class: the tool is not FASTER than the hand version, it is CORRECT where the hand
> version is merely plausible. Reach for the skill because it EXISTS, not because you feel the need
> (`feedback_resource_use_gated_on_existence_not_felt_need`).

Invoke `/sync-workspace` via the Skill tool. Pushes:
- Plans (decision log + plan body + handoff doc + plan_checks audit synthesis docs)
- Memory backups
- CLAUDE.local.md backup
- Any other gitignored workspace-mirrored content

If push fails (auth / merge conflict / etc.): surface to operator. Don't retry blindly.

### Stage 7.5 — FINAL doc-floor gate (AFTER the handoff write — "re-run the floor as the LAST step") [NEW 2026-07-04, D-301]

The 6-consecutive AR-8 miss: the Stage-2.0 + Stage-4.6 `check_session_docs` runs happen BEFORE Stage 6 writes the handoff — so a handoff that omits the Capture-completeness/TaskList section, or a MASTER left stale vs the NEW active handoff, is invisible to those earlier runs (the `.E.1.2` RED-floor-commit `64efd33`). Close the loop:

1. **Re-run `check_session_docs.sh` HERE — after the handoff write + the sync — and READ IT FULL** (never grep-excerpt; a partial read of a green/red tool IS a self-attestation, per the meta-index S18/S20 lessons). Do NOT declare the close complete until it prints `SWEEP CLEAN`.
2. **Structural backstop (D-299/D-300):** the workspace pre-commit hook now runs the full aggregator (**Check P**) when a handoff/MASTER is staged — so the Stage-7 sync COMMIT is itself gated (a broken handoff FAILS the commit, un-bypassable barring `SKIP_DOC_AGGREGATOR_CHECK`). If the sync commit succeeded WITH a `[pre-commit] Check P PASS` line, the floor was GREEN by construction. If the commit FAILED, fix the handoff/MASTER and re-commit — never `SKIP_` past it.
3. **Fresh clone / gate unwired:** if Stage 7's commit showed NO `[pre-commit]` output, the hooks are UNWIRED (`core.hooksPath` unset) — run `tools/setup_hooks.sh` (idempotent) to wire both repos, then re-commit. See D-301.

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


## ⚠️ Stage 6.5 — THE JUDGMENT HALF (added 2026-07-20 after a 4x recurrence)

**Why this stage exists, stated so it cannot be skipped by feeling done.** The close-out has a
MECHANICAL half and a JUDGMENT half. The mechanical half is gated by `check_session_docs.sh`. The
judgment half was gated by NOTHING, and it was skipped in **two consecutive sessions** — both times
the only detector was the operator asking. In the second, a 22-commit session shipped with ZERO
commits to four owed auto-write ledgers while the sweep stayed green throughout, *because none of
those files is mechanically gated*. A green from a partially-mechanised ritual is evidence about
the mechanised half only.

### 5.1 — RUN the mechanical enforcer, do not assume it

```
python3 tools/check_close_out_completeness.py --since <session-start-sha>
```

Covers: auto-write ledger coverage · volatile counts in the handoff · a RE-DERIVE block ·
a judgment-check ledger · an independent-review record. HIGH findings BLOCK the close.

### 5.2 — ANSWER all eight judgment checks EXPLICITLY, in the handoff

`/capture-audit` checks **2 · 3 · 5 · 6 · 7 · 9 · 10 · 12** are tool-backed by nothing. Record a
verdict per check in the handoff **in `Check N` form** so a skip is VISIBLE rather than invisible.
"Nothing found" is a valid verdict; *silence is not*. The enforcer greps for this ledger.

### 5.3 — NO VOLATILE COUNTS in the handoff

A raw count is stale **on the commit that records it**. Observed: `26 commits` → corrected to `24`
→ already `25` by the next commit; and a stale `98 enrolled` survived TWO self-sweeps. This is not
a value to patch better — it is unfixable by writing a better number.

Anchor to a **SHA range** (`window 2167d9d..HEAD`) or a **state** ("baseline EMPTY", "pin EXACT"),
and give the reader the commands to RE-DERIVE anything actionable. Name things by ID, not by count:
"8 dangling ids" rots; `TECH_DEBT-101, -102, …` does not.

### 5.4 — INDEPENDENT ADVERSARIAL REVIEW of the handoff (AR-8), MANDATORY

**The maker does not grade their own artifact.** Self-checking a handoff failed FOUR CONSECUTIVE
TIMES in one close — and the third failure was the *sweep for stale values* missing a stale value
the first two introduced. A long handoff is typically patched many times and never re-read whole,
so internal contradiction accumulates exactly where the reader cannot see it.

Spawn an `a-class` agent, default-REFUTED, and tell it explicitly that a "looks fine" verdict is
almost certainly a miss. Point it at: internal contradictions between sections · claims false at
HEAD · contradictions with the plan body / MASTER / ledgers / decision log · stale volatile values ·
anything a fresh session would get wrong by following the document literally.

Record the verdict in the handoff. The enforcer greps for it.

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
