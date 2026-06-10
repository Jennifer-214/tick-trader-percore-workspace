# Memory index

> Compressed 2026-05-26; re-compressed 2026-06-02 under the always-loaded byte-budget guard (`tools/check_always_loaded_budget.py`, enforced via `check_session_docs.sh`). Each entry ≤200 chars; deep WHY/sisters/examples live in the memory file body. Pattern: `[Title](file.md) — short trigger + key principle.`

## Process + collaboration

- [Prefer boundary-stable refactors over wide cascades](feedback_reduce_touch_sites.md) — keep public types unchanged; cascade only when the boundary type itself is the bug
- [Bump Version.hpp every ship + rename plans when ship-order diverges](feedback_bump_version_per_ship.md) — every `vX.Y.Z` tag bumps Version.hpp in the same commit; rename the plan file (not Version.hpp) to keep filename+tag monotonic
- [Defer is last-ditch, never effort-avoidance](feedback_no_defer_for_effort.md) — implement properly first time; "smaller scope" has failed 3/3 vs do-it-right
- [Single-cycle exist+good; design once, maintain forever](feedback_design_once_maintain_forever.md) — take a piece exist→good in ONE cycle; don't re-traverse determinism-gated code; foundational/known-requirement only (unknown-unknowns still MVP)
- [Opportunistic tech-debt closure — subsumption not adjacency](feedback_opportunistic_tech_debt_closure.md) — close debt a ship SUBSUMES (≈0 marginal cost); merely ADJACENT → cross-link + leave tracked; discriminator = marginal-cost, not surface-adjacency
- [Deferral is merit, not effort/context](feedback_deferral_reasons_merit_not_effort_or_context.md) — do-now-vs-defer = correctness/scope/proof/marginal-cost; my effort or "we have context" is NOT a valid axis (relatability tell)
- [Close-out-now over defer for small in-flight finds](feedback_close_out_now_over_defer_when_small.md) — small fixable found in-flight → close NOW; only genuinely-separate DELIVERABLES defer (D-159)
- [Guards compound — enforcement is the highest-leverage investment](feedback_guards_compound_enforcement_is_leverage.md) — a guard protects a whole CLASS forever, no-thought; code is one instance, the guard is permanent leverage; convention-only on a capital/determinism surface = a hole to close
- [Structure the judgment loop, not the output](feedback_structure_judgment_loop_not_output.md) — verification skills carry the leverage; maker skills earn keep by making artifacts GATE-ABLE; scaffolds=legible, gates=correct (workspace-template thesis)
- [Prefer structural fix over patch for recurring bug classes](feedback_structural_fix_for_recurring_class.md) — registry/helper-extract + compile-time enforcement beats a one-time patch
- [After pre-coding checks, ALWAYS consult before coding](feedback_consult_on_audit_findings.md) — present findings + iterate; do NOT auto-proceed
- [Heavier-default audit posture for capital](feedback_heavier_default_audit_posture_for_capital.md) — money-bearing → default HEAVIER audit; LIGHT earned only where deterministic coverage exists; burden on REMOVING a control
- [Process weight by surface blast-radius](feedback_process_weight_by_surface_blast_radius.md) — engine/capital → heavy planning+gates; workspace/skill/doc apparatus → light dogfood-iterate; breadth ≠ blast-radius; light=validate-by-use not pre-gate
- [Auto-route input to the matching skill](feedback_auto_route_input_to_matching_skill.md) — input/work-state matches a skill's trigger → SUGGEST the judgment skill (await greenlight, never silently fire) / FIRE the mechanical one; Layer B of skill-consult+routing
- [Close the class structurally ≠ migrate every site](feedback_close_the_class_vs_migrate_every_site.md) — close a class via the primitive + an enforcing CI guard (new=build-error; existing KNOWN-PENDING, shrinking); the guard de-risks paced migration
- [Verify every enumerated site at ship-close](feedback_verify_every_enumerated_site_at_close.md) — plan enumerates N sites → verify ALL N done before close; subset+assume-complete is the recurring gap
- [Two foundations: determinism vs correctness](feedback_two_foundations_determinism_vs_correctness.md) — reproducibility (net-gating; freeze current behavior) vs exact-values (deliberate, regen the golden) = orthogonal; don't let "make it exact first" block the determinism net
- [Defer to source authority for external semantics](feedback_defer_to_source_authority_for_external_semantics.md) — externally-DEFINED values (venue precision/fee-rounding/tick-lot; protocol widths) → mirror source-exact + GUARD + registry per source; never internalize a choice
- [Paste tool output, don't summarize](feedback_paste_tool_output_dont_summarize.md) — plan claims a tool-enumerable set → paste the output verbatim, never hand-summarize (silently drops members); mechanized by check_plan_enumeration_completeness.py
- [Run doc CI tools first, never hand-verify](feedback_run_doc_ci_tools_first_never_hand_verify.md) — verifying doc/plan/citation/index correctness → run the deterministic TOOL first (`check_session_docs.sh`); "clean" = tool exit-0, never a feeling; full sweep not spot-check
- [Guard-matrix bounds foundation-hardening](feedback_guard_matrix_bounds_foundation_hardening.md) — the guard-coverage-matrix is the STOP condition for "make it solid first": harden until every invariant the next phase touches is an enforced row, then build
- [Independence is for judgment, not mechanical checks](feedback_independence_for_judgment_not_mechanical.md) — independent agent ONLY where judgment can be biased; deterministic checks run as the TOOL directly; run the leanest executor
- [Skill-edit cohort checklist](feedback_skill_edit_cohort_checklist.md) — editing a SKILL.md → run the checklist (own cross-ref / frontmatter both-ways / CLAUDE.md if NEW / catalog both-ways / check_doc_metadata --bidirectional)
- [Never skip thoroughness unless explicitly stated](feedback_never_skip_thoroughness_unless_explicit.md) — thorough steps fire BY DEFAULT; skip ONLY on explicit operator instruction, NEVER on agent judgment of "redundant/trivial"
- [Listen and execute simply; don't over-elaborate](feedback_listen_and_execute_simply.md) — direct instruction → do it + brief confirm + STOP; don't spiral into meta-treatises; thoroughness governs the WORK not the CONVERSATION
- [Runtime executor mode {independent|self|both} for judgment skills](feedback_runtime_executor_mode_for_judgment_skills.md) — judgment/audit skills take a per-invocation executor arg; operator defers the independence call at runtime; default independent
- [Sequential per-target audits for granular triage](feedback_sequential_audit_for_granular_operator_triage.md) — multi-target audit batch → sequential per-target when correctness>speed; hybrid = codebase-wide parallel baseline → per-target sequential
- [Test change enumeration per plan body](feedback_test_change_enumeration_per_plan_body.md) — every plan body touching tested code enumerates (a) modified / (b) broken-replaced / (c) NEW unit tests in a dedicated section
- [Proactive rename candidate surfacing](feedback_proactive_rename_candidate_surfacing.md) — throughout multi-ship restructures FLAG rename candidates as encountered; classify 4-tier; scan the running list at each planning gate
- [Plan body length has NO target LOC](feedback_plan_body_length_no_target_loc.md) — plans get as much detail as needed; never cite a LOC guideline; LOC is OUTPUT not INPUT; assess by completeness
- [Terminology-evolution bridge, not history rewrite](feedback_terminology_evolution_bridge_not_history_rewrite.md) — architecture-wide rename: SWEEP forward docs NOW; PRESERVE historical bodies; BRIDGE via glossary; blanket rewrite falsifies the evolution
- [Compaction degrades — verify handoffs against current code](feedback_compaction_degrades_treat_handoffs_as_hints.md) — re-verify handoff claims + audit verdicts vs actual code
- [Overengineering boundary — pick harder when future work much easier](feedback_overengineering_boundary_when_future_easier.md) — the future-work simplification multiplier wins at the borderline
- [Evaluate options on robustness + latency + design, NOT time](feedback_evaluate_options_on_robustness_latency_design_not_time.md) — time is essentially never the deciding factor
- [Avoid substring replace_all on member-access patterns](feedback_avoid_substring_replace_all_on_member_access.md) — `config.X` mangles `ctrl->config.X`; inventory variations OR longest-prefix OR per-prefix targeted edits
- [Don't ship MVP for plumbing/refactor work](feedback_no_mvp_for_plumbing_only_for_unknown_unknowns.md) — MVP is for genuinely-new features with external deps only
- [Don't measure structural work by LOC](feedback_dont_measure_structural_work_by_loc.md) — lead with classes closed + patterns codified; LOC incidental
- [Auto-pick future-oriented option when trade-off clear](feedback_auto_pick_future_oriented.md) — don't punt clear decisions; escalate only when future-vs-now sharp OR ambiguous
- [Audit canonical sister before proposing new framework infra](feedback_audit_canonical_sister_before_new_infra.md) — grep for sisters first; EXTEND if ≥50% overlap + same consumer behavior
- [Plans introducing new registries cite sister inspection](feedback_plans_cite_sister_registry_inspection.md) — plan body MUST include a "Canonical sister registries considered" section; ship-blocker if missing
- [New plans use future-oriented plan template](feedback_new_plans_use_future_oriented_template.md) — canonical template at `DESIGN_SPECS/plan-templates/future-oriented-plan-template.md`
- [Motivated collaborator for Caramel](feedback_motivated_collaborator_for_caramel.md) — public AGPL + hedge-fund attention = high bar; pick best-software path even when costlier now
- [Backwards compat NOT a default concern](feedback_backwards_compat_not_default_concern.md) — OSS personal tool; default to cleanest deletion; operator flags load-bearing exceptions (stamp/persistence/model-handle/locked-cfg)
- [Framework-layer payoff has diminishing returns](feedback_framework_layer_payoff_diminishing_returns.md) — 1st registry eliminates 90 sites = transformative; 7th eliminates 6 = rounding error; build → consolidate → stop adding → maintain
- [Proportionate response to audit findings](feedback_proportionate_response_to_audit_findings.md) — full menu: INLINE / ACCEPT / FOLD / ARCHITECT-NEW / NO-FOLD; pick what's ACTUALLY right, not first-sufficient
- [Address MED/LOW findings, not just HIGH/CRIT](feedback_address_med_low_findings_not_just_high_crit.md) — every finding gets a disposition; severity gates urgency+sequencing NOT whether-to-address; dropping MED/LOW = techdebt under a label
- [Plan right not fast](feedback_plan_right_not_fast.md) — planning IS the hard part now; decide RIGHTLY not QUICKLY; indecisiveness while planning is a feature
- [Audit own proposals with the same rigor](feedback_audit_own_proposals_with_same_rigor.md) — 4-pillar: DESIGN_SPECS / anti-pattern / operator-impact / novel-alternative
- [Surface operator migration path proactively on breaking changes](feedback_surface_operator_migration_path_proactively.md) — wire-format / version-bump / breaking cfg MUST include "Operator migration impact"; prefer SOFT compat
- [Proactive novel alternative consideration](feedback_proactive_novel_alternative_consideration.md) — every decision matrix MUST include a "Novel alternative considered" row with verdict
- [Re-check DESIGN_SPECS for BOTH options on pushback](feedback_recheck_designspecs_on_pushback.md) — don't reactively flip; check the anti-pattern catalog for BOTH options BEFORE committing
- [Iteration spiral signals an audit meta-gap](feedback_iteration_spiral_signals_audit_meta_gap.md) — 4+ amendment cycles with smaller findings = audit METHODOLOGY gap; codify the META-gap, sweep, verify inflection
- [Enumerate consumers before registry-row deletion](feedback_enumerate_consumers_before_registry_row_deletion.md) — ONE comprehensive grep across all access patterns + file types BEFORE finalizing scope
- [Future-headache vs optimization scope framework](feedback_future_headache_vs_optimization_scope_framework.md) — close anti-pattern instances at ship (future-headache); defer pure-performance optimization
- [Implementation-detail blind-spot recovery via taxonomy (M4)](feedback_implementation_detail_blindspot_recovery_via_taxonomy.md) — fire `/blindspot-scan` when SHAPE audits stay GREEN/YELLOW after 3+ iterations
- [Prefer action-parameterized walker over per-consumer bodies](feedback_prefer_action_parameterized_walker_over_per_consumer_walker_bodies.md) — `FOREACH_<COHORT>_COHORT(BASE_X)` meta-walker prevents drift across consumers
- [CLAUDE.md/local/SKILL/memory are GUIDELINES not stuff-to-do](feedback_claude_md_guidelines_not_stuff_to_do.md) — always-loaded = TIMELESS guidelines/triggers/pointers; on-demand carries EPHEMERAL work
- [Plans + sub-plans codify explicit end goals](feedback_plans_have_explicit_end_goal.md) — every plan body MUST include "End goal" + acceptance-criteria sections
- [Categorical triggers > hardcoded refs in always-loaded content](feedback_categorical_triggers_over_hardcoded_refs.md) — use categorical patterns ("any X-macro registry consumer"), not hardcoded fn/TECH_DEBT-NNN/path
- [Quarterly /metadata-audit cadence](feedback_metadata_audit_quarterly.md) — sister to /anti-spaghetti quarterly; catches doc-system drift mechanically
- [File-size split discipline](feedback_file_size_split_discipline.md) — always-loaded byte-cap is the BINDING ceiling (guarded by check_always_loaded_budget.py); line counts are a proxy; tests 5000 / headers 1500 / bodies 2000 / DESIGN_SPECS 1200
- [Wire-context vs cfg-file parser separation](feedback_wire_context_vs_cfg_file_parser_separation.md) — dual-context parser MUST take a `bool wire_context` param OR split the functions
- [Train-serve execution-layer parity META gap (M5)](feedback_train_serve_execution_layer_meta_gap.md) — pre-coding gate includes a train-serve EXECUTION-LAYER walk (boot + slow-path-cycle) for any HIGH-RISK EngineSharded ship
- [Verify symbol existence at plan-drafting time](feedback_verify_symbol_existence_at_plan_drafting_time.md) — comprehensive grep before a plan body cites any fn/symbol/file:line (Class 14)
- [Lead with architectural merit, not operator tone](feedback_lead_with_architectural_merit_not_operator_tone.md) — re-evaluate on MERIT before pivoting on pushback; articulate why X wins vs Y
- [Enumerate helper signature args before extract (M6)](feedback_enumerate_helper_signature_args_before_extract.md) — body-content enumeration CSV before plan-body lock
- [Tiered audit discipline per plan scope](feedback_tiered_audit_discipline_per_plan_scope.md) — HIGH 5-agent / MED 3-agent / LOW 2-agent / TRIVIAL skip; declared via `audit_tier:` frontmatter
- [Structural enforcement when memory codification proves insufficient (M7)](feedback_structural_enforcement_when_memory_insufficient.md) — escalate to a CI tool / pre-commit / compile-time check when a bug class recurs DESPITE codified memory at the SAME surface
- [Session decision log discipline](feedback_session_decision_log_discipline.md) — planning cycle >3 amendments OR multi-session → per-version decision log + `<!-- D/C/F -->` + `<!-- STATUS -->` sentinels
- [Document-as-you-go > catch-at-the-end](feedback_document_as_you_go_over_catch_at_end.md) — capture decisions/findings/work-products AT creation, ALWAYS (unconditional — NOT "if the session does a lot"); the create→capture gap is where compaction-loss lives
- [Multi-surface deletion ordering (B14)](feedback_multi_surface_deletion_ordering_discipline.md) — deletion across ≥3 files w/ compile interdeps: enumerate + classify per deletion-kind + sequence leaves-first (cfg-field-row last)
- [Unconditionalization latent-assumption audit (B15)](feedback_unconditionalization_latent_assumption_audit.md) — removing a cfg-gate via "always-true" → enumerate latent per-arch/per-mode assumptions; verify none load-bearing BEFORE unconditionalizing
- [Operator-facing doc cohort at cfg deletion](feedback_operator_facing_doc_cohort_at_cfg_deletion.md) — cfg/feature deletion → sweep README + QUICKSTART + cfg.example + sister operator-docs in the deletion cohort
- [Archived changelog preservation](feedback_archived_changelog_preservation_discipline.md) — DO NOT modify archived changelog files/rows even when removing the feature; only the CURRENT CHANGELOG gets a new row at ship close
- [Operator pushback as audit signal](feedback_operator_pushback_as_audit_signal.md) — "are you sure?" / "analyzing actual code?" → STOP, do actual code analysis BEFORE responding; do NOT reactively flip
- [Categorize by consumer-pattern not field-name](feedback_categorize_by_consumer_pattern_not_field_name.md) — field-name taxonomy is NOT a substitute for consumer-pattern analysis (walker behavior + override membership + actual reads)
- [Cfg field categorization at registry-add time](feedback_cfg_field_categorization_at_registry_add_time.md) — 4-category decision tree; re-categorization is a 5-step atomic migration (partial = orphan state worse than original)
- [No question boxes (M7 escalation candidate)](feedback_no_question_boxes.md) — never use AskUserQuestion modal; inline text presentation only
- [C++17 inline variable for header-only shared state](feedback_cpp17_inline_variable_for_shared_state_across_tus.md) — header-only globals → C++17 `inline` (never `static` = per-TU copies; never extern+cpp)
- [Single source of truth discipline](feedback_single_source_of_truth_discipline.md) — any fact/constant/fn-body in 2+ places = SSoT candidate; default MERGE unless a semantic distinction (then document why)
- [Machine-portable resolver for committed tool paths](feedback_machine_portable_resolver_for_committed_tool_paths.md) — a committed tool referencing a per-machine path gets env-override + derived-default + `.exists()`-guard, NOT a hardcode
- [Count code-LOC not total-lines for thresholds](feedback_count_code_loc_not_total_lines.md) — file-size/function-length/complexity checks count code-LOC (exclude comments+blanks)
- [Forward-decl at global scope not inside namespace tt](feedback_forward_decl_at_global_scope_not_namespace.md) — `namespace tt { class X; }` shadows ::X; place forward-decls at GLOBAL scope OR `#include` (Class 34/B17)
- [Enumerate block-scope statics before hoist](feedback_enumerate_block_scope_statics_before_hoist.md) — hoisting a lambda into a named fn (different scope) → enumerate ALL enclosing block-scope statics; pass each as an explicit arg (Class 35/B18)
- [Sister-cohort amendment completeness](feedback_sister_cohort_amendment_completeness.md) — amending a Class/DESIGN_SPEC/ledger → enumerate the sister-cohort (cross-refs + reverse cross-refs); parallel-amend same ship
- [Forward-promise auto-write verification](feedback_forward_promise_auto_write_verification.md) — ship-close promises auto-write → next-ship verify it landed at the expected ledger; /capture-audit Check 11
- [Golden-master over reimplemented oracle](feedback_golden_master_over_reimplemented_oracle.md) — validate a path by freezing its REAL output + diffing; NEVER a reimplemented/stub oracle (Class-18 mirror that drifts + lies)
- [Phased pre-rework correctness foundation + net-gating](feedback_phased_pre_rework_correctness_foundation.md) — high-risk multi-ship restructure: phase the foundation (bedrock→lock-current→root-GREEN→sweep→gate); the no-reintroduction guarantee is the NET, not the audits
- [Enumerate the set before a categorical risk-dismissal](feedback_enumerate_set_before_categorical_claim.md) — before dismissing a risk via a property over a SET ("the rest are safe"), enumerate + verify each + name any non-conformer (Class-33)
- [Ground design claims in real code](feedback_ground_design_in_real_code.md) — design talk: Read+cite file:line for EXISTING-code claims (don't reconstruct from memory / trust a transient note over disk); show framing+reuse for NEW code

## User profile

- [Public technical work attracts hedge fund attention](user_public_work_attracts_hedge_funds.md) — FoxML_Trader_v2 public AGPL is career-load-bearing; weight heavily on public/private decisions
- [Address user as Caramel / she / her](feedback_address_user_as_caramel.md) — operator-preferred personal address in all communication
- [Deep design work has intrinsic value for Caramel](user_deep_design_work_intrinsic_value.md) — architectural conversations + DESIGN_SPECS replaced gaming; don't rush to ship when design depth IS the value
- [ADHD + deferred-reward discipline](user_adhd_deferred_reward_discipline.md) — consciously practices deferred reward (planning) over dopamine (shipping); default to the deeper option when engaged
- [MVP→professional transition phase](user_mvp_to_professional_transition.md) — framework consolidation IS the deliberate work of the professionalization phase, not a detour
- [Structure = externalized cognition + correctness risk-control](user_structure_is_correctness_risk_control_for_capital.md) — heavy apparatus = external memory for solo+AI + correctness risk-control for money code; burden of proof is on REMOVING a control
- [Correctness-first, NOT ship-fast](user_correctness_first_not_ship_fast.md) — values correctness + planning over everything; deliberately shifting away from move-fast/break-stuff; when execution flails, STOP + slow down; wants "never skip thoroughness" formalized into the reusable workspace-template

## Project state

- [Engine CLAUDE.md is a symlink to workspace](project_engine_clauder_md_is_symlink.md) — edits must target the workspace path (harness unreliable with symlinks); also plans/ + .claude/skills/
- [No live models — dev/test only; epoch breaks are free](project_no_live_models_dev_test_only.md) — all model artifacts are test fixtures; stamp/epoch/wire breaks free provided post-change determinism holds
- [Anti-spaghetti audit on cadence](project_anti_spaghetti_audit_cadence.md) — quarterly + post-new-anti-pattern-codification + ad-hoc
- [foxml_suite refactor queued](project_foxml_suite_refactor_queued.md) — needs PRODUCER-side framework treatment; fire `/ml-audit` scoped to foxml_suite
- [E-series is vision convergence, not scope balloon](project_e_series_is_vision_convergence_not_scope_balloon.md) — v5.15.5.F.4d.1.E (9 sub-ships) is year-old destination architecture, not planning-day enthusiasm; don't auto-flag scope expansion
- [Engine core proven; engineering ONGOING but PHASED](project_engine_done_edge_is_the_frontier.md) — core works; major-structural NOW → optimize+extend after inflection; goal = a moldable shape; edge/alpha is the ultimate frontier
- [Public repo is code-only; dev apparatus private](project_public_repo_is_code_only.md) — public = ONLY compile+run code (source+build+LICENSE/README); tests/tools/docs/skills/CI gitignore-in-place private; dev apparatus → `workspace-template` release later; alpha always private; spring-cleaning 2026-06-02; law in DESIGN_SPECS/meta-disciplines/public-private-boundary-and-ecosystem-discipline.md
