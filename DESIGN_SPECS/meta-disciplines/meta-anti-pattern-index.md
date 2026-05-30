---
type: meta-discipline
subtype: meta-anti-pattern-index
name: meta-anti-pattern-index
stage: 3-first-canonical
version: v1.0
established: 2026-05-29
sprint: v5.15-live-readiness
landing_ship: v5.15.5.F.4d.1.E.0.2
status: first-canonical (9 rows; Session-3 harvest +AR-3 +PL-3 +CP-1-bump; Session-4 2026-05-30 harvest = AR-1 recurrence-bump [conclusion-before-verification ×~6, the session's dominant shape; structural net landed: aggregator + pre-commit Check E + 6 skills wired]; populated ongoing via the /close-session harvest Stage)
purpose: Single greppable HOME + scan parity for NON-code recurring errors (audit-reasoning / planning / workspace-hygiene / cascade-propagation) — the META parallel of DOCS/RECURRING_BUG_PATTERNS.md.
decision_ref: D-75 (subsystem) + D-76 (.E.0.2 prioritization) + Decision A (INDEX, not a new class-series) + Decision B (lives in DESIGN_SPECS/meta-disciplines/ — private; references private plans/handoffs/decision-logs)
sister_specs:
  - meta-disciplines/structural-enforcement-when-memory-insufficient.md
  - meta-disciplines/canonical-sister-extension-discipline.md
  - meta-disciplines/audit-driven-sub-sprint-trajectory-verification.md
  - meta-disciplines/implementation-layer-blindspot-taxonomy.md
tags: [meta-discipline, anti-pattern-index, audit-methodology, workspace-hygiene, cascade-propagation, meta-error-tracking]
consumed_by:
  - "/close-session harvest Stage (WRITES new rows)"
  - "/capture-audit Check 12 (READS the CP cascade entries)"
  - "/precoding-audit-gate Piece-4 hardened (READS all rows as checks)"
---

# Meta anti-pattern index (the META parallel of RECURRING_BUG_PATTERNS)

**What this is.** A single greppable HOME for NON-code recurring errors — the mistakes made in *audit-reasoning, planning, and workspace-hygiene*, plus *cascade-propagation* misses — with the same scan parity that CODE anti-patterns have via `DOCS/RECURRING_BUG_PATTERNS.md` (Classes 1-36) + `/bug-check`. Landed at `.E.0.2` (D-75/D-76); it is the catalog half of the meta-error-tracking subsystem.

## It is an INDEX, not a new class-series (Decision A)

This catalog does **not** re-number or duplicate the meta-disciplines that already exist. It **aggregates + points to** them, and **adds** the org/planning/workspace shapes that lacked a home:

| Existing meta-shape family | Canonical home | Relationship here |
|---|---|---|
| **M1-M7** audit-methodology gaps | `DOCS/DESIGN_PHILOSOPHY.md` § 11.5 | POINTED-TO (no re-number) |
| **B14-B19** implementation-blindspot pillars | `meta-disciplines/implementation-layer-blindspot-taxonomy.md` | POINTED-TO |
| **Workspace-hygiene checks** | `/capture-audit` (11 checks) + `/metadata-audit` | POINTED-TO |
| **Cascade / sister-cohort** | `feedback_sister_cohort_amendment_completeness` + M7 | POINTED-TO (CP-1 makes it mechanical) |
| **NEW org / planning / workspace / audit-reasoning shapes** | *here* | INDEXED (entries below) |

Why an index, not a parallel registry: per `canonical-sister-extension-discipline` + `feedback_framework_layer_payoff_diminishing_returns` — re-numbering M/B would be a duplicate registry (Class-21-shaped at the meta layer). The index gives scan parity *without* the duplication.

Why private (Decision B): unlike `RECURRING_BUG_PATTERNS.md` (public; code patterns are safe to publish), this index references private `plans/` / `handoffs/` / `decision-logs/` and internal process → it lives in `DESIGN_SPECS/meta-disciplines/` (private via the workspace), alongside the M1-M7 narrative. The *parity* with the code catalog is in STRUCTURE + FUNCTION (a scannable catalog with a scan), not in location.

## Schema

Each NEW entry: **ID** (category-prefixed — `AR` audit-reasoning / `PL` planning / `WH` workspace-hygiene / `CP` cascade-propagation) · **Shape** · **Existing home** (memory / M-N / B-N / Class-N, or NEW) · **Detection** (mechanical grep | reflection prompt) · **Enforced by** (which mechanism) · **Source**. Each per-shape detail carries a **False-positive surface** (M3 — distinguish a legitimate sibling from the anti-pattern). Pointed-to M/B entries keep their own IDs; this index only references them.

## Indexed recurring meta-error shapes (seed cohort — `.E.0`/`.E.0.1` session, 2026-05-29)

| ID | Shape | Existing home | Detection | Enforced by | Source |
|---|---|---|---|---|---|
| **AR-1** | Categorical risk-dismissal over an UN-enumerated set ("the rest are exact/safe/identical/unaffected") — generalized to **conclusion-before-verification** ("done"/"clean" asserted before running the check that's right there) | `feedback_enumerate_set_before_categorical_claim` (M8-candidate) + `feedback_run_doc_ci_tools_first_never_hand_verify` (the conclusion-before-verify sibling, NEW Session-4) | reflection: "did I bound scope / dismiss a risk / declare done-or-clean via a property or status I didn't enumerate + verify member-by-member, when the verifying tool was available?" | gate verification pass + harvest + **the doc-CI aggregator (`check_session_docs.sh`) as the standing mechanical answer** | `.E.0.1` R1 — `FromDouble` assumed exact-integer; it wasn't · **`.E.0.2` close ×2** — concluded "guard dormant"/"done-line" before the cheap mechanical check · **Session-4 (2026-05-30) ×~6 — DOMINANT shape of the session**: `ML_Headers/Fingerprint.hpp` phantom (asserted a file/line from plausibility, was `Backtest/`); "clean stopping point" asserted 3× (each time a tool then found drift — red-build sister, broken `CoreFrameworks/` citation, TD-150); Task-#12 marked complete 3× while grep showed a skill still unwired; TD-150 mis-filed as real debt then deleted-from-both-files (caught by grep). EVERY instance caught by the tool or operator pushback, never by self-judgment → the fix is now STRUCTURAL: `feedback_run_doc_ci_tools_first_never_hand_verify` + the aggregator + pre-commit Check E + the 6 skills wired (D-112/D-115). Recurrence-despite-AR-1-note across a whole session = the M7 escalation that produced that structural net. |
| **AR-2** | Over-generalized spec/definition — a categorical claim baked into a spec/gate-def without enumerating the set it quantifies over | instance of AR-1 | reflection: "does this spec/gate-def quantify over a set ('all ops', 'every field') without listing it?" | gate verification pass + harvest | determinism gate defined "all-ops native==generic" → `FromDouble`/`ToDouble` break it |
| **AR-3** | Documentation-accepted-as-verification — a load-bearing invariant asserted in a comment/doc treated as evidence it HOLDS, with no establishing code AND no enforcing guard ("a comment is not a guard") | NEW (sister: guard-coverage-matrix; D-92) | reflection: "is a load-bearing invariant asserted only in a comment, with neither establishing code nor a guard?" | gate verification/completeness-critic pass + harvest | **Session-3 (2026-05-30)** — the locale phantom-invariant (`CoreModelZoo:2845` "engine boot pins LC_NUMERIC") backed by NEITHER code NOR guard (worked by ambient-C luck); the audit-reasoning shape that lets phantoms persist. CODE-side sibling → RECURRING_BUG_PATTERNS phantom-invariant Class |
| **CP-1** | Cascade-not-propagated — a decision/spec/definition amended in one place; sibling references left stale | `feedback_sister_cohort_amendment_completeness` + M7 escalation | **mechanical** — `/capture-audit` Check 12 (grep amended term across plans/handoffs/decision-logs/memories) | `/capture-audit` Check 12 | gate-def change had to cascade to handoff/A2/D-74 by hand · **`.E.0.2` cross-ref closure** — forward-refs propagated but reverse-refs NOT (3× this session); the *asymmetry* half of cascade-completeness → mechanize via `check_doc_metadata --bidirectional` + index-completeness (#14) · **RECURRED `.E.0.x` capture session (2026-05-29)** — 3 new memories' forward-refs written, reverse-refs omitted (caught only by operator prompt + the completeness sweep). **Recurrence-DESPITE-the-CP-1-note = M7 trigger**: the memory note is insufficient → the fix is **bringing memories into the structured `sister_specs:` frontmatter** (TECH_DEBT-115 Phase-2-3 memory slice) so the EXISTING `check_doc_metadata --bidirectional` covers them — NOT a bespoke inline-`[[link]]` parser (canonical-sister: use the system you already built). A one-way sister-link then becomes a **red build** (→ **TECH_DEBT-115** durable home). **CLOSED for the memory corpus at `.E.0.4` (2026-05-30; subsystem ships as `E.0.5`)** — the 85-memory migration made `sister_specs:` an undirected (auto-reciprocal) graph + `check_doc_metadata --bidirectional --memories` is now a RED build on any one-way sister; the CP-1 mechanical guard is LIVE. · **Session-3 (2026-05-30)** — **D-97** (decimal-vs-binary money decision) captured in the decision-log but NOT propagated to the `.E.0.1`/`.E.0.3` plan bodies (the `.E.0.3` STUB still *asserted* the superseded binary direction); caught only by operator "did we update the plan?". A NEW decision GATING existing plans (vs an amended cross-referenced term) → Check 12's amended-term-cascade may miss the decision→gated-plan direction; mechanization-gap candidate. |
| **WH-1** | Memory-link convention drift — `[[slug]]` cross-links using the `name:` form instead of the filename form | NEW (sister to `/capture-audit` Check 1) | **mechanical** — grep `[[...]]` links that don't resolve to a memory filename | `/capture-audit` (sister check) + `/metadata-audit` | `.E.0` memory cross-links used kebab `name:` not filename |
| **WH-2** | Stale index pointer — an always-loaded index (MEMORY.md / sprint-state / MASTER) points to a superseded state | NEW (sister to `/capture-audit` Check 1 + Check 5) | **mechanical-ish** — index entry vs current `Version.hpp` / HEAD / ship-state | `/capture-audit` | sprint-state pointer lagged ship-state · **RECURRED ×2 at the `.E.0.5` close (2026-05-30)** — CLAUDE.local.md sprint-state lagged at `.D.1` (stale since the `.E.0.4` close) + the catalog's OWN frontmatter self-count was stale (said "6 rows", was 7); both caught + fixed at the `.E.0.5` close. 2× at the ship-close surface (incl. the catalog self-policing itself) → **mechanization candidate (M7)**: a close-ritual check reconciling always-loaded index pointers (CLAUDE.local.md sprint-state version / catalog self-counts / MEMORY.md) against `Version.hpp`/ship-state — recurrence-despite-the-note is the escalation signal. |
| **PL-1** *(first harvest output, 2026-05-29 dogfood)* | Under-applied auto-pick-future-oriented — defaulted to the lighter/faster structural option when corpus principles (D-73 bedrock-first / guard-matrix completeness / heavier-default-for-capital) already implied the heavier one; operator surfaced it | `feedback_auto_pick_future_oriented` (violation direction) | reflection: "did operator steer me from a lighter option to a more-structural one the corpus already implied?" | gate verification pass + harvest | apparatus-build session ×2 (apparatus-first sequencing + gate-hardening) · **`.E.0.1` fix-audit session (2026-05-29) ×4** — light-drift ×3 (global-`setlocale` over per-thread `uselocale`; `uselocale`-wrap over the more-structural `to_chars`; "subset-in-E defer-rest-to-F" over close-the-class-now) then **over-heavy ×1** (proposed migrating a cfg-`atof` "net-gating subset" that was *empty*) = the **symmetric over-correction** (mis-calibrating structural-weight in *both* directions); centered by the independent fix-audit + operator pushback. Calibration note: the `check_plan_body_symbol_existence` checker false-positives on verbatim code-body snippets that quote real header-defined types (the F-058 blocks). |
| **PL-2** *(harvest 2026-05-29)* | Agent-self-skip of a thorough step — skipped a review/audit/check on the agent's OWN judgment ("redundant"/"already covered"/"trivial"), leaving the un-covered part unverified | `feedback_never_skip_thoroughness_unless_explicit` (sister: heavier-default) | reflection: "did I skip a thorough step on my own judgment, not an explicit operator skip? did prior coverage of OTHER work excuse skipping NEW work?" | skill default-fire gating (skip = operator-explicit-only) + harvest | `.E.0.2` close — skipped Stage 5.5 ("2 reviews ran") but the close-out wasn't reviewed; operator caught it |
| **PL-3** *(harvest 2026-05-30)* | Severity-as-skip-license — treated a finding's non-CRITICAL severity as license to DROP it (no disposition), rather than as urgency/sequencing | NEW (`feedback_address_med_low_findings_not_just_high_crit`; D-91) | reflection: "does EVERY finding (incl. MED/LOW) carry a disposition — fix/fold/ledger-with-ID/document — or did I drop one because it 'wasn't critical'?" | **structural** — `/precoding-audit-gate` Stage-4 disposition-completeness rule + harvest | **Session-3 (2026-05-30)** — the gate's OWN Stage-4 template said "MED=not blocking / LOW=future-work" + the synthesis repeated it; operator "MED/LOW ≠ ignore = techdebt". STRUCTURALLY FIXED at the same surface (gate Stage-4 reframed) |

## How the three mechanisms share this schema

- **Piece 3 — `/close-session` harvest (WRITES).** At session close, the structured-reflection Stage runs the AR/PL/WH/CP prompts; recurring shapes → new rows here (or a recurrence bump + a new Source line on an existing row). The session's own pushbacks/errors are the highest-signal seed corpus (`feedback_operator_pushback_as_audit_signal` § generative dimension — this seed cohort is 3/5 from one hour of `.E.0.1` pushback).
- **Piece 2 — `/capture-audit` Check 12 (READS the CP rows).** CP-1 is the mechanical one: on a sentinel-block amendment, grep its key terms across the corpus → flag un-propagated refs.
- **Piece 4 — hardened `/precoding-audit-gate` (READS all rows as checks).** Mechanical rows (CP-1/WH-1/WH-2) run as deterministic Stage-0 greps; reflection rows (AR-1/AR-2) run as the verification/completeness-critic pass prompts. As the harvest grows this table, the gate auto-gains coverage — the memory→catalog→gate→harvest loop.

## Per-shape detail (+ false-positive surface, M3)

### AR-1 — categorical risk-dismissal over an un-enumerated set
A risk is judged "low likelihood" or scope is bounded by asserting a property over a *set* whose members were never listed and checked. The real risk hides in the unverified member. **Fix:** enumerate the set, verify each, name any non-conformer. **False-positive surface:** a set that is *genuinely* enumerated + verified (then the categorical claim is sound) — AR-1 is only the *un*-enumerated case. Sister: Class-33 (consumer-enumeration) lifted to the risk-assessment layer.

### AR-2 — over-generalized spec/definition
A spec or gate definition encodes a universal ("all ops", "every field", "always identical") that was never checked against the actual set, so a member silently violates it. **Fix:** enumerate at definition time; scope the claim to the verified members. **False-positive surface:** a universal that IS exhaustively true by construction (e.g. a `static_assert` over a closed enum) — not over-generalized. An instance of AR-1 at the spec layer.

### CP-1 — cascade-not-propagated
An amended decision/spec/definition leaves stale references in sibling docs (handoffs, decision-logs, plans, memories) that still cite the old form. **Fix:** the `/capture-audit` Check 12 mechanical scan. **False-positive surface:** a term legitimately referenced in many places that does NOT need updating (a historical-record citation, a postmortem describing the old state) — Check 12 must distinguish "stale forward-looking ref" from "truthful historical record" (sister to `feedback_archived_changelog_preservation_discipline` + `feedback_terminology_evolution_bridge_not_history_rewrite`).

### WH-1 — memory-link convention drift
`[[slug]]` cross-links written with the front-matter `name:` form (kebab) when resolution is by *filename* (`feedback_*` / `user_*` / `project_*`). **Fix:** grep `[[...]]` tokens; flag any that don't match a memory filename. **False-positive surface:** an intentional forward-link to a not-yet-written memory (the memory system explicitly allows `[[name]]` that doesn't resolve yet) — flag as INFO, not error.

### WH-2 — stale index pointer
An always-loaded index (MEMORY.md, CLAUDE.local.md sprint-state, MASTER) names a state that the latest ship/decision superseded. **Fix:** diff the index's claimed state against `Version.hpp` / HEAD / latest ship. **False-positive surface:** an index intentionally describing a frozen baseline (a "last shipped" anchor) rather than the live tip.

### PL-1 — under-applied auto-pick-future-oriented *(first harvest entry)*
Defaulting to the lighter/faster structural option when the corpus's own principles already imply the heavier/more-structural one — leaving the operator to surface it. **Fix:** at a structural fork, explicitly check the corpus (D-73 / guard-matrix / heavier-default / `feedback_auto_pick_future_oriented`) BEFORE recommending the lighter default. **False-positive surface:** when the lighter option is genuinely correct because the heavier one is over-engineering past the inflection (`feedback_framework_layer_payoff_diminishing_returns`) — PL-1 is *only* mis-defaulting AGAINST a corpus principle, not every time the lighter option wins. Home: `feedback_auto_pick_future_oriented` (violation-direction sibling).

### PL-2 — agent-self-skip of a thorough step *(harvest)*
Skipping a review/audit/check because the AGENT judges it redundant/trivial/already-covered — the efficiency-instinct quietly erodes coverage and the un-covered part stays unverified (a hole). **Fix:** thorough steps fire by DEFAULT; skip ONLY on explicit operator instruction (a flag / stated "skip it"); a review fires on UN-reviewed work regardless of prior passes on OTHER work. **False-positive surface:** an operator-EXPLICIT skip (`--no-review`, "skip this") is legitimate — PL-2 is *agent*-discretion skip, not operator-discretion. Home: `feedback_never_skip_thoroughness_unless_explicit`; sister: `feedback_heavier_default_audit_posture_for_capital` (light is earned) + AR-1 (verify before you conclude).

### AR-3 — documentation-accepted-as-verification *(harvest 2026-05-30)*
A load-bearing invariant is asserted in a comment/doc and treated as evidence it holds — but no code establishes it AND no guard enforces it, so it "works" only by ambient luck. **Fix:** load-bearing invariants get a guard (CI / `static_assert` / runtime), never a comment; at audit, flag any comment-asserted invariant lacking establishing-code + a guard (= the guard-coverage-matrix "no convention-only on critical surfaces" discipline). **False-positive surface:** a comment *describing* an invariant that IS established + guarded elsewhere (documentation, not the sole mechanism) — AR-3 is only the *unbacked* assertion. CODE-side sibling: the phantom-invariant Class in RECURRING_BUG_PATTERNS. Source: the locale `"engine boot pins LC_NUMERIC"` comment with no boot pin + no guard (D-92).

### PL-3 — severity-as-skip-license *(harvest 2026-05-30)*
Treating a finding's non-CRITICAL severity as permission to DROP it (no disposition) rather than as urgency/sequencing — silently accruing tech-debt under a severity label. **Fix:** every finding at every severity carries exactly one disposition (fix-in-ship / fold-to-task / ledger-with-ID / document); severity gates urgency + sequencing, never whether-to-address. **False-positive surface:** an operator-EXPLICIT "drop it / won't-fix" is a legitimate (documented) disposition — PL-3 is the *silent* drop. Home: `feedback_address_med_low_findings_not_just_high_crit`; structurally enforced at `/precoding-audit-gate` Stage-4 (disposition-per-finding). Sister: PL-2 (self-skip of a STEP; PL-3 is self-skip of a FINDING's disposition).

## Population + maintenance (yield-as-signal)
- The `/close-session` harvest is the population mechanism — do NOT hand-curate ad hoc.
- Track row count + recurrence over time. Healthy: new shapes slow as the apparatus matures. A spike = a new class of meta-error slipped in → that's the M7 signal to add the guard.
- Prompt for RECURRING shapes worth cataloging, NOT one-off fixes (anti-ceremony, per `.E.0.2` R3).

---
**End — meta-anti-pattern-index v1.0 (first canonical; `.E.0.2` Step B). Decisions A + B resolved; schema is the shared contract for Pieces 2/3/4.**
