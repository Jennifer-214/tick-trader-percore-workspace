# Memory index

> Compressed 2026-05-26 per feedback_file_size_split_discipline. Each entry ≤200 chars; deep WHY/sisters/examples live in memory file body. Pattern: `[Title](file.md) — short trigger + key principle.`

## Process + collaboration

- [Prefer boundary-stable refactors over wide cascades](feedback_reduce_touch_sites.md) — keep public types unchanged; cascade only when boundary type itself is the bug
- [Bump Version.hpp on every ship + rename plans when ship order diverges from phase numbering](feedback_bump_version_per_ship.md) — every `vX.Y.Z` tag must include Version.hpp bump in same commit; rename plan file (not Version.hpp) when ship order diverges from phase numbering so plan filename + tag stay monotonic
- [Defer is last-ditch, never effort-avoidance](feedback_no_defer_for_effort.md) — implement properly first time; "smaller scope" recommendations have failed 3/3 vs do-it-right instinct
- [Prefer structural fix over patch for recurring bug classes](feedback_structural_fix_for_recurring_class.md) — X-macro registry / helper extract with compile-time enforcement beats one-time patch
- [After pre-coding checks, ALWAYS consult before coding](feedback_consult_on_audit_findings.md) — present findings + iterate; do NOT auto-proceed
- [Compaction degrades — verify handoffs against current code](feedback_compaction_degrades_treat_handoffs_as_hints.md) — re-verify handoff claims + audit verdicts vs actual code
- [Overengineering boundary — pick harder when future work much easier](feedback_overengineering_boundary_when_future_easier.md) — future-work simplification multiplier wins at borderline
- [Evaluate options on robustness + latency + design philosophy, NOT time](feedback_evaluate_options_on_robustness_latency_design_not_time.md) — time is essentially never the deciding factor
- [Avoid substring replace_all on member-access patterns](feedback_avoid_substring_replace_all_on_member_access.md) — `config.X` mangles `ctrl->config.X`; inventory variations OR longest-prefix OR per-prefix targeted edits
- [Don't ship MVP for plumbing/refactor work](feedback_no_mvp_for_plumbing_only_for_unknown_unknowns.md) — MVP is for genuinely-new features with external deps only
- [Don't measure structural work by LOC](feedback_dont_measure_structural_work_by_loc.md) — lead with classes closed + patterns codified; LOC incidental
- [Auto-pick future-oriented option when trade-off clear](feedback_auto_pick_future_oriented.md) — don't punt clear decisions; escalate only when future-vs-now sharp OR ambiguous
- [Audit canonical sister before proposing new framework infrastructure](feedback_audit_canonical_sister_before_new_infra.md) — grep codebase for sisters first; extend if ≥50% overlap + same consumer behavior
- [Plans introducing new registries cite existing sister inspection](feedback_plans_cite_sister_registry_inspection.md) — plan body MUST include "Canonical sister registries considered" section; ship-blocker if missing
- [New plans use future-oriented plan template](feedback_new_plans_use_future_oriented_template.md) — canonical template at `DESIGN_SPECS/plan-templates/future-oriented-plan-template.md`
- [Motivated collaborator for Caramel](feedback_motivated_collaborator_for_caramel.md) — public AGPL + hedge fund attention = high quality bar; pick best-software path even when costs more time now
- [Backwards compat NOT a default concern](feedback_backwards_compat_not_default_concern.md) — OSS personal tool; default to cleanest deletion (no preserve-and-deprecate surfaces); operator flags explicitly when load-bearing exceptions apply (stamp body / persistence / model handle / locked cfg)
- [Framework-layer payoff has diminishing returns](feedback_framework_layer_payoff_diminishing_returns.md) — first registry eliminates 90 sites = transformative; 7th layer eliminates 6 sites = rounding error. Phases: build → consolidation → post-inflection (stop adding) → maintenance
- [Proportionate response to audit findings](feedback_proportionate_response_to_audit_findings.md) — full menu: (A) INLINE MERGE / (B) ACCEPT WITH RATIONALE / (C) FOLD / (D) ARCHITECT NEW / NO-FOLD; pick what's ACTUALLY right not first-sufficient
- [Plan right not fast](feedback_plan_right_not_fast.md) — planning IS the hard part of SWE now; disciplines support decide-RIGHTLY not decide-QUICKLY; indecisiveness while planning is a feature
- [Audit own proposals with same rigor as operator-proposed plans](feedback_audit_own_proposals_with_same_rigor.md) — 4-pillar: DESIGN_SPECS check / anti-pattern check / operator-impact / novel-alternative
- [Surface operator migration path proactively on breaking changes](feedback_surface_operator_migration_path_proactively.md) — wire-format / version-bump / breaking cfg MUST include "Operator migration impact"; prefer SOFT compat
- [Proactive novel alternative consideration when applying existing patterns](feedback_proactive_novel_alternative_consideration.md) — every decision matrix MUST include "Novel alternative considered" row with verdict
- [Re-check DESIGN_SPECS for BOTH options on pushback](feedback_recheck_designspecs_on_pushback.md) — don't reactively flip; check anti-pattern catalog for BOTH options BEFORE committing
- [Iteration spiral signals audit meta-gap](feedback_iteration_spiral_signals_audit_meta_gap.md) — 4+ amendment cycles with smaller findings = audit METHODOLOGY gap; codify META-gap, apply sweep, verify inflection
- [Enumerate consumers comprehensively before registry-row deletion](feedback_enumerate_consumers_before_registry_row_deletion.md) — ONE comprehensive grep covering all access patterns across file types BEFORE finalizing scope
- [Future-headache vs optimization scope framework](feedback_future_headache_vs_optimization_scope_framework.md) — close anti-pattern instances at ship (future-headache); defer pure-performance optimization
- [Implementation-detail blind-spot recovery via taxonomy (M4)](feedback_implementation_detail_blindspot_recovery_via_taxonomy.md) — fire `/blindspot-scan` when SHAPE audits GREEN/YELLOW after 3+ iterations
- [Prefer action-parameterized walker over per-consumer walker bodies](feedback_prefer_action_parameterized_walker_over_per_consumer_walker_bodies.md) — `FOREACH_<COHORT>_COHORT(BASE_X)` meta-walker prevents drift across consumers
- [CLAUDE.md / CLAUDE.local.md / SKILL.md / memory are GUIDELINES not stuff-to-do](feedback_claude_md_guidelines_not_stuff_to_do.md) — always-loaded TIMELESS; on-demand carries EPHEMERAL work
- [Plans + sub-plans codify explicit end goals](feedback_plans_have_explicit_end_goal.md) — every plan body MUST include "End goal" + acceptance criteria sections
- [Categorical triggers > hardcoded refs in always-loaded content](feedback_categorical_triggers_over_hardcoded_refs.md) — use categorical patterns ("any X-macro registry consumer") not hardcoded refs (specific function names / TECH_DEBT-NNN)
- [Quarterly /metadata-audit cadence for doc-system drift detection](feedback_metadata_audit_quarterly.md) — sister to `/anti-spaghetti` quarterly; catches drift mechanically
- [File-size split discipline (generalized)](feedback_file_size_split_discipline.md) — always-loaded 600 lines / tests 5000 / source headers 1500 / bodies 2000 / ledgers 2000 / SKILL.md 1500 / DESIGN_SPECS 1200 / plans 1200 / memory 500
- [Wire-context vs cfg-file parser separation](feedback_wire_context_vs_cfg_file_parser_separation.md) — dual-context parser MUST take `bool wire_context` param OR split functions
- [Train-serve execution-layer parity META gap (M5)](feedback_train_serve_execution_layer_meta_gap.md) — pre-coding audit gate must include train-serve EXECUTION-LAYER walk (boot + slow-path-cycle body) for any HIGH-RISK ship touching EngineSharded
- [Verify symbol existence at plan-drafting time](feedback_verify_symbol_existence_at_plan_drafting_time.md) — comprehensive grep before plan body cites any function/symbol/file:line (Class 14 closure)
- [Lead with architectural merit, not operator tone](feedback_lead_with_architectural_merit_not_operator_tone.md) — re-evaluate on MERIT before pivoting on operator pushback; articulate why X wins vs Y
- [Enumerate helper signature args before extract (M6)](feedback_enumerate_helper_signature_args_before_extract.md) — body-content enumeration CSV at `plan_checks/<date>-<ship>-<helper>-body-content-enumeration.csv` BEFORE plan body lock
- [Tiered audit discipline per plan scope](feedback_tiered_audit_discipline_per_plan_scope.md) — HIGH-RISK 5-agent / MED-RISK 3-agent / LOW-RISK 2-agent / TRIVIAL skip; declared via `audit_tier:` frontmatter (Check 34)
- [Structural enforcement when memory codification proves insufficient (M7)](feedback_structural_enforcement_when_memory_insufficient.md) — escalate to Stage 6 (CI tool / pre-commit hook / compile-time check) when bug class recurs DESPITE codified memory at SAME surface
- [Session decision log discipline](feedback_session_decision_log_discipline.md) — when planning cycle > 3 amendments OR multi-session: maintain per-version decision log; sentinel discipline `<!-- D/C/F: <id> --> + <!-- STATUS: <state> -->`; `/capture-audit` Checks 3+4 enforce

## User profile

- [Public technical work attracts hedge fund attention](user_public_work_attracts_hedge_funds.md) — FoxML_Trader_v2 public AGPL (10k clones) load-bearing for career angle; weight heavily on public/private decisions
- [Deep design work has intrinsic value for Caramel](user_deep_design_work_intrinsic_value.md) — architectural conversations + DESIGN_SPECS replaced gaming; don't rush to ship when design depth IS the value
- [ADHD + deferred-reward discipline](user_adhd_deferred_reward_discipline.md) — consciously practices deferred reward (planning) over dopamine (shipping); default to deeper option when engaged
- [MVP→professional transition phase](user_mvp_to_professional_transition.md) — framework consolidation IS the deliberate work of professionalization phase, not a detour from features

## Project state

- [Engine CLAUDE.md is a symlink to workspace](project_engine_clauder_md_is_symlink.md) — edits must target workspace path (harness can be unreliable with symlinks); also plans/ + .claude/skills/
- [Anti-spaghetti audit on cadence](project_anti_spaghetti_audit_cadence.md) — quarterly + post-new-anti-pattern-codification sweep + ad-hoc; first canonical run 2026-05-17
- [foxml_suite refactor queued for post-`.F.4d.1.D`](project_foxml_suite_refactor_queued.md) — needs PRODUCER-side framework treatment; fire `/ml-audit` scoped to foxml_suite
