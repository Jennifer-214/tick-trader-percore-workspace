#!/bin/bash
# check_session_docs.sh — ONE mechanical sweep of all DOC/PLAN CI checks.
#
# WHY THIS EXISTS (codified v5.15.5.F.4d.1.E Session-4, 2026-05-30):
# Plan bodies + memories live in the WORKSPACE repo (committed via /sync-workspace),
# but the pre-commit hook (B-Plus etc.) is installed in the ENGINE repo + plans/ is
# gitignored there → the engine hook NEVER gates workspace doc commits. The
# bidirectional-memories check isn't in the hook at all. Net result: NOTHING
# mechanical caught a broken plan-body citation (CoreFrameworks/ prefix) or a one-way
# memory sister-link this session — they survived until hand-run. This aggregator is
# the SINGLE command that runs every doc/plan CI tool, so "are the docs clean?" is a
# deterministic one-shot, not N hand-checks. Fired by /close-session Stage 0.
#
# It CALLS existing tools (no logic duplication — SSoT for "full doc sweep"):
#   check_doc_metadata.py --bidirectional --memories   [HARD — exit 1 on asymmetry/broken-ref]
#   check_plan_body_symbol_existence.py (B-Plus)        [HARD — exit 1 on fabrication]
#   check_capture_audit.py --quiet                      [HARD — index/sentinels/skill-linkage]
#   check_tools_inventory.py                            [HARD — every tools/*.{sh,py} enrolled in DOCS/TOOLS.md]
#   check_always_loaded_budget.py                       [HARD — CLAUDE.md/local + MEMORY.md vs harness byte caps]
#   check_fpn_doc_size_currency.py                      [HARD — docs' single-FPN<> byte size vs the code's sizeof assert]
#   check_navinfra_cohort_reference.py                  [HARD — every audit/plan-check/pickup skill reaches the nav-infra consult]
#   check_forward_promise_audit.py                      [ADVISORY — MED/LOW expected]
#   check_meta_registry.py                              [ADVISORY — engine-structural; pre-existing orphans surfaced]
#
# Exit 0 = all HARD checks pass. Exit 1 = a HARD check failed (fix before declaring clean).
# Bypass a single check via the same SKIP_* env vars the pre-commit hook honors.
#
# Usage:
#   tools/check_session_docs.sh                 # B-Plus over session-modified workspace plan bodies
#   tools/check_session_docs.sh --all-plans     # B-Plus over ALL plan bodies (slower; full sweep)

set -uo pipefail
# Machine-portable roots (per feedback_machine_portable_resolver_for_committed_tool_paths):
# REPO_ROOT derives from this script's location (<engine>/tools/check_session_docs.sh);
# WORKSPACE_ROOT via env-override -> sibling-default. No $HOME hardcode in a committed,
# public-AGPL tool — runs on any clone / any PC / SSH-grid node.
REPO_ROOT="${FOXML_ENGINE:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
if [ -n "${FOXML_WORKSPACE:-}" ] && [ -d "${FOXML_WORKSPACE}" ]; then
    WORKSPACE_ROOT="${FOXML_WORKSPACE}"
elif [ -d "$(dirname "$REPO_ROOT")/tick-trader-percore-workspace" ]; then
    WORKSPACE_ROOT="$(dirname "$REPO_ROOT")/tick-trader-percore-workspace"
else
    WORKSPACE_ROOT="$REPO_ROOT"
fi
ALL_PLANS=0
[ "${1:-}" = "--all-plans" ] && ALL_PLANS=1

HARD_FAIL=0
declare -a RESULTS

run_hard() { # name, cmd...
    local name="$1"; shift
    if "$@" >/tmp/csd_$$.log 2>&1; then
        RESULTS+=("  ✅ HARD  $name")
    else
        RESULTS+=("  ❌ HARD  $name  (exit $?) — see detail below")
        echo "----- $name detail -----"; cat /tmp/csd_$$.log
        HARD_FAIL=1
    fi
    rm -f /tmp/csd_$$.log
}
run_advisory() { # name, cmd...
    local name="$1"; shift
    if "$@" >/tmp/csd_$$.log 2>&1; then
        RESULTS+=("  ✅ ADV   $name")
    else
        RESULTS+=("  ⚠️  ADV   $name  (exit $?; advisory — not blocking)")
    fi
    rm -f /tmp/csd_$$.log
}

echo "=========================================================="
echo " check_session_docs.sh — mechanical doc/plan CI sweep"
echo "=========================================================="

# --- HARD 1: bidirectional + index sync over memories (the red-build catcher) ---
if [ "${SKIP_BIDIR_CHECK:-0}" != "1" ]; then
    run_hard "doc-metadata bidirectional+index (memories)" \
        python3 "$REPO_ROOT/tools/check_doc_metadata.py" --bidirectional --memories
else
    RESULTS+=("  ⏭  HARD  doc-metadata bidirectional (SKIP_BIDIR_CHECK=1)")
fi

# --- HARD 1b: DESIGN_SPECS index currency (README/TAG_INDEX/CLAUDE-skill-table regenerated after a spec add) ---
# Closes the gap where a spec is added but rebuild_doc_indexes.py isn't re-run → the index drifts
# (the .E.1.0-s2 close: 2 new specs unindexed; the operator caught it, not the sweep). --check writes nothing.
if [ "${SKIP_INDEX_CURRENCY:-0}" != "1" ]; then
    run_hard "DESIGN_SPECS index currency (README/TAG_INDEX vs rebuild --check)" \
        python3 "$REPO_ROOT/tools/rebuild_doc_indexes.py" --check
else
    RESULTS+=("  ⏭  HARD  DESIGN_SPECS index currency (SKIP_INDEX_CURRENCY=1)")
fi

# --- HARD 1c: in-code tag-block validator (E.1.2.A schema — self-test non-vacuity + full-tree scan) ---
if [ "${SKIP_CODE_TAG_CHECK:-0}" != "1" ]; then
    run_hard "code tag-blocks --selftest (non-vacuity)" \
        python3 "$REPO_ROOT/tools/check_code_tag_blocks.py" --selftest
    run_hard "code tag-blocks full-tree scan (in-file [SCHEMA] whitelist; mixed-state OK)" \
        python3 "$REPO_ROOT/tools/check_code_tag_blocks.py"
else
    RESULTS+=("  ⏭  HARD  code tag-blocks (SKIP_CODE_TAG_CHECK=1)")
fi

# --- HARD 1c-2: [SCHEMA] version cohesion (D-371 — every converted [SCHEMA]_[ver] == the LOCKED
# version, the value SSoT-derived from the spec's "Status: LOCKED — [SCHEMA]_[v1.0]" line; catches
# the v1-vs-v1.0 drift the validator's prefix gate can't see; WIP_EXEMPT now empty, whole corpus). Kept OUT
# of the parity-gated validator so foxtag<->Python validate byte-parity stays intact. ---
if [ "${SKIP_SCHEMA_VERSION_CHECK:-0}" != "1" ]; then
    run_hard "schema-version cohesion ([SCHEMA]_[ver] == locked; SSoT-derived, D-346)" \
        python3 "$REPO_ROOT/tools/check_schema_version.py"
else
    RESULTS+=("  ⏭  HARD  schema-version cohesion (SKIP_SCHEMA_VERSION_CHECK=1)")
fi

# --- HARD 1b-9: the four D-137 selftest wrappers that NOTHING invoked ---
# Each of these is the non-vacuity proof for a gate that IS wired HARD, and each was listed in
# DOCS/TOOLS.md as STANDING-CI "via the tool's --selftest" -- a claim that was simply false: no
# call-site existed in check_session_docs, the hook, or any umbrella runner. They passed when run
# by hand today, but that is luck, not coverage: a tooth nobody exercises rots silently, which is
# exactly how the H21 version-decrease tooth sat dead (see 1c-1 below).
# 355ms for all four. → DESIGN_SPECS/meta-disciplines/advertised-capability-never-exercised.md
run_hard "corpus-membership guard teeth (ADD/DELETE/RENAME/REORDER flagged; absent golden = HARD)" \
    bash "$REPO_ROOT/tools/check_corpus_membership_selftest.sh"
run_hard "import-from-core lint teeth (planted rollers in BOTH spellings flagged; own-dir passes)" \
    bash "$REPO_ROOT/tools/check_import_from_core_selftest.sh"
run_hard "schema-version guard teeth (drifted [SCHEMA]_[v1] flagged; locked passes; exempt opts out)" \
    bash "$REPO_ROOT/tools/check_schema_version_selftest.sh"
run_hard "tool-I/O envelope teeth (emit/read/validate incl. negative controls)" \
    bash "$REPO_ROOT/tools/toolio_selftest.sh"

# Wired 2026-07-20 (C5). Both are NEW teeth for guards that were already HARD-wired here with no
# non-vacuity proof of their own — the shape the block above exists to prevent, recurring.
# citable_ids' --selftest was worse than absent: the flag was ACCEPTED AND IGNORED (no argparse),
# so it and `--this-does-not-exist` both printed the index and exited 0.
run_hard "citable-ID resolver teeth (by-definition / zero-pad / grandfathered suffix / block bounds / registry-fatal)" \
    python3 "$REPO_ROOT/tools/citable_ids.py" --selftest
run_hard "capture-audit teeth (Checks 13+14: findings construction, index floor, absent-golden = HARD)" \
    python3 "$REPO_ROOT/tools/check_capture_audit.py" --selftest

# --- HARD: the ELEVEN further selftests that existed and fired NOWHERE (wired 2026-07-20) ---
# Measured at wiring: 23 *_selftest.sh existed, 8 were invoked by anything. The other 15 were
# advertised-capability-never-exercised at scale — and running them for the first time found FOUR
# RED, two on capital/determinism surfaces (TECH_DEBT-265). A tooth nobody exercises does not
# decay gracefully; it decays silently, and its guard keeps reporting green the whole time.
# The four RED are deliberately NOT wired here — wiring a known-red gate trains the operator to
# ignore the gate, which is the failure mode this whole block exists to prevent.
# Cost ~14s, dominated by latency-path (8.5s) + struct-size-budget (3.9s). Acceptable for a
# session-close gate; do NOT move these to pre-commit without re-timing.
run_hard "capital-adversarial-audit teeth"        bash "$REPO_ROOT/tools/check_capital_adversarial_audit_selftest.sh"
run_hard "cfg-key-prefix-drift teeth"             bash "$REPO_ROOT/tools/check_cfg_key_prefix_drift_selftest.sh"
run_hard "close-out-completeness teeth"           bash "$REPO_ROOT/tools/check_close_out_completeness_selftest.sh"
run_hard "code-tag-blocks teeth (wrapper)"        bash "$REPO_ROOT/tools/check_code_tag_blocks_selftest.sh"
run_hard "conversion-completeness teeth (wrapper)" bash "$REPO_ROOT/tools/check_conversion_completeness_selftest.sh"
run_hard "handoff-capture-completeness teeth"     bash "$REPO_ROOT/tools/check_handoff_capture_completeness_selftest.sh"
run_hard "latency-path-conformance teeth (H8)"    bash "$REPO_ROOT/tools/check_latency_path_conformance_selftest.sh"
run_hard "meta-registry teeth (H15)"              bash "$REPO_ROOT/tools/check_meta_registry_selftest.sh"
run_hard "struct-size-budget teeth"               bash "$REPO_ROOT/tools/check_struct_size_budget_selftest.sh"
run_hard "tech-debt writer teeth (--close TTY-gated + byte-identical)" \
    bash "$REPO_ROOT/tools/check_tech_debt_selftest.sh"
run_hard "sanitizer-suite teeth"                  bash "$REPO_ROOT/tools/run_sanitizer_suite_selftest.sh"

# Wired 2026-07-20 after CHECK 4 (invocation truth) proved DOCS/TOOLS.md CLAIMED these fired here
# and they did not. Two teeth that existed, were enrolled, were advertised as gated -- and had
# never run from any trigger. Fixing the WIRING rather than the row, because the teeth are real.
run_hard "add_vocab teeth (tag-vocabulary mutation guarded)" \
    bash "$REPO_ROOT/tools/add_vocab_selftest.sh"
run_hard "register-fit teeth (finding-register shape guarded)" \
    bash "$REPO_ROOT/tools/check_register_fit_selftest.sh"

# --- ADV: close-out completeness (M8 / TECH_DEBT-250) — auto-write ledger coverage ---
# ADVISORY, not HARD, and deliberately: it fires on a WINDOW, so mid-session runs would red
# constantly. Its job is to be LOUD at close, not to block work. The judgment half of the
# close-out ritual has no other detector — twice now the only trigger was operator pushback.
run_advisory "close-out completeness (auto-write ledgers touched across the session window)" \
    python3 "$REPO_ROOT/tools/check_close_out_completeness.py" --since HEAD~20 --min-commits 8

# --- HARD 1c-1: H21 identifier-retirement guard TEETH (D-137 negative self-test) ---
# The guard itself runs at pre-commit Check H, but its negative self-test ran NOWHERE — and its
# version-decrease tooth sat broken for an unknown period, hardcoding SHARDED_SNAPSHOT_VERSION|8
# against a ledger that had moved to |10, so the sed was a no-op and the case proved nothing.
# An unwired self-test is how a tooth rots unnoticed; wiring it is the structural close (M7).
# Safe to run in a standing sweep since 2026-07-20: it plants defects in a throwaway COPY via
# IDENTIFIER_LEDGER and asserts the tracked golden was never mutated.
run_hard "identifier-retirement guard teeth (renumber/version-decrease/silent-removal all RED; H21)" \
    bash "$REPO_ROOT/tools/check_identifier_retirement_selftest.sh"

# --- HARD 1c-2: corpus MEMBERSHIP pin (E.1.2.B 0.2 / D-386 + D-396) ---
# The contract states the RULES; this proves they still resolve to the same FILES. Different
# failure surfaces: a rule can stay valid while a file silently leaves the corpus and stops being
# checked. Pinned as a LIST, not a count — commit 1da1c1c moved SIX files' identities with the
# tracked count going 167 -> 167, delta ZERO, so a count pin is blind to renames and to any swap.
# Deliberately NOT folded into the parity-gated validator: a corpus-spanning property inside
# `validate` would make one implementation flag what the other does not and re-break byte-parity
# (the :39 corollary; same call made at D-371 for check_schema_version and `foxtag fields`).
run_hard "corpus membership pin (resolved file-list == blessed golden, order incl.; D-386/D-396)" \
    python3 "$REPO_ROOT/tools/check_corpus_membership.py"

# --- HARD 1d: in-code conversion COMPLETENESS gate (E.1.2.A — coverage: every unit warranting a block HAS one) ---
# Non-vacuity selftest (ExecutionCore clean + GateControlNetwork flagged + trivial return-structs exempt) +
# baseline mode: a NEW lumped/un-blocked unit FAILS; the grandfathered gaps live in
# tools/lib/completeness_baseline.txt (shrinks as the Phase-C cleanup lands, per the plan's § COMPLETENESS-GATE).
# Catches the GateControlNetwork class — a struct/registry buried in another unit's [CODE], invisible to the validator.
if [ "${SKIP_COMPLETENESS_CHECK:-0}" != "1" ]; then
    run_hard "conversion completeness --selftest (non-vacuity)" \
        python3 "$REPO_ROOT/tools/check_conversion_completeness.py" --selftest
    run_hard "conversion completeness (baseline — a NEW lumped/missing unit = fail)" \
        python3 "$REPO_ROOT/tools/check_conversion_completeness.py" --baseline "$REPO_ROOT/tools/lib/completeness_baseline.txt"
else
    RESULTS+=("  ⏭  HARD  conversion completeness (SKIP_COMPLETENESS_CHECK=1)")
fi

# --- HARD 2: B-Plus plan-body symbol existence (the citation-error catcher) ---
if [ "${SKIP_PLAN_BODY_CHECK:-0}" != "1" ]; then
    B_PLUS="$REPO_ROOT/tools/check_plan_body_symbol_existence.py"
    if [ "$ALL_PLANS" = "1" ]; then
        run_hard "B-Plus (ALL plan bodies)" python3 "$B_PLUS" --all
    else
        # session-modified workspace plan/doc .md (precise scope; the close surface)
        MODIFIED=$(git -C "$WORKSPACE_ROOT" diff --name-only HEAD -- 'plans/**/*.md' 2>/dev/null; \
                   git -C "$WORKSPACE_ROOT" ls-files --others --exclude-standard -- 'plans/**/*.md' 2>/dev/null)
        MODIFIED=$(echo "$MODIFIED" | grep -E 'subplans/.*\.md$|MASTER\.md$' | sort -u || true)
        if [ -z "$MODIFIED" ]; then
            RESULTS+=("  ✅ HARD  B-Plus (no session-modified plan bodies)")
        else
            FAB=0
            for rel in $MODIFIED; do
                f="$WORKSPACE_ROOT/$rel"
                [ -f "$f" ] || continue
                # TECH_DEBT-193: a forward-design DRAFT plan (bplus_scope: design-draft) carries to-build
                # `(NEW)` sketches + deliberately-stale citations (re-derived at its pre-coding gate per the
                # plan's own discipline). DEFER its B-Plus to that gate — /readiness runs B-Plus HARD on the
                # plan when it goes to code (the compensating control; the doc-sweep is the wrong time). Opt-in
                # marker → normal plans stay HARD (no hole in the Class-14 fabrication catch).
                if grep -qiE '^bplus_scope:[[:space:]]*design-draft' "$f"; then
                    echo "  [B-Plus] deferred (bplus_scope: design-draft → pre-coding gate): $rel"
                    continue
                fi
                python3 "$B_PLUS" "$f" >/tmp/csd_bp_$$.log 2>&1 || FAB=1
            done
            if [ "$FAB" = "1" ]; then
                RESULTS+=("  ❌ HARD  B-Plus (session plan bodies) — fabrication/missing citation")
                echo "----- B-Plus detail (last) -----"; cat /tmp/csd_bp_$$.log
                HARD_FAIL=1
            else
                RESULTS+=("  ✅ HARD  B-Plus (session plan bodies)")
            fi
            rm -f /tmp/csd_bp_$$.log
        fi
    fi
else
    RESULTS+=("  ⏭  HARD  B-Plus (SKIP_PLAN_BODY_CHECK=1)")
fi

# --- HARD 3: capture-audit mechanical checks (index-sync / sentinels / skill-linkage) ---
if [ "${SKIP_CAPTURE_AUDIT_CHECK:-0}" != "1" ]; then
    run_hard "capture-audit mechanical (index/sentinels/skill-linkage)" \
        python3 "$REPO_ROOT/tools/check_capture_audit.py" --quiet
else
    RESULTS+=("  ⏭  HARD  capture-audit mechanical (SKIP_CAPTURE_AUDIT_CHECK=1)")
fi

# --- HARD 4: tools-inventory enrollment (every tools/*.{sh,py} has a row in DOCS/TOOLS.md) ---
if [ "${SKIP_TOOLS_INVENTORY_CHECK:-0}" != "1" ]; then
    run_hard "tools-inventory enrollment (DOCS/TOOLS.md)" \
        python3 "$REPO_ROOT/tools/check_tools_inventory.py"
else
    RESULTS+=("  ⏭  HARD  tools-inventory enrollment (SKIP_TOOLS_INVENTORY_CHECK=1)")
fi

# --- HARD 4b: import-from-core lint (E.1.2.B 0.1 / D-375 — no NEW roll-your-own repo-root; 7 grandfathered) ---
if [ "${SKIP_IMPORT_FROM_CORE_CHECK:-0}" != "1" ]; then
    run_hard "import-from-core lint (no NEW roll-your-own repo-root)" \
        python3 "$REPO_ROOT/tools/check_import_from_core.py"
else
    RESULTS+=("  ⏭  HARD  import-from-core lint (SKIP_IMPORT_FROM_CORE_CHECK=1)")
fi

# --- HARD 5: always-loaded doc context budget (the silent-truncation guard) ---
if [ "${SKIP_DOC_BUDGET_CHECK:-0}" != "1" ]; then
    run_hard "always-loaded doc budget (CLAUDE.md/local + MEMORY.md vs harness caps)" \
        python3 "$REPO_ROOT/tools/check_always_loaded_budget.py"
else
    RESULTS+=("  ⏭  HARD  always-loaded doc budget (SKIP_DOC_BUDGET_CHECK=1)")
fi

# --- HARD 6: handoff-active singleton (≤1 `status: active` handoff — explicit-state resolution) ---
if [ "${SKIP_HANDOFF_ACTIVE_CHECK:-0}" != "1" ]; then
    run_hard "handoff-active singleton (≤1 status:active across plans/**/handoffs)" \
        python3 "$REPO_ROOT/tools/check_handoff_active_singleton.py"
    run_hard "handoff capture-completeness (active handoff carries a substantive section)" \
        python3 "$REPO_ROOT/tools/check_handoff_capture_completeness.py"
else
    RESULTS+=("  ⏭  HARD  handoff-active singleton (SKIP_HANDOFF_ACTIVE_CHECK=1)")
fi

# --- HARD 7: FPN-doc-size currency (docs' single-FPN<> byte size vs the code's sizeof assert) ---
# No FOXML_ENGINE pin: the tool's own dual-root resolver finds the engine (canonical parse) AND the
# workspace (incl. workspace-only docs) — pinning FOXML_ENGINE would confine the scan to one tree.
if [ "${SKIP_FPN_DOC_SIZE_CHECK:-0}" != "1" ]; then
    run_hard "FPN-doc-size currency (single-FPN<> byte size vs FixedPointN.hpp sizeof assert)" \
        python3 "$REPO_ROOT/tools/check_fpn_doc_size_currency.py"
else
    RESULTS+=("  ⏭  HARD  FPN-doc-size currency (SKIP_FPN_DOC_SIZE_CHECK=1)")
fi

# --- HARD 8: nav-infra cohort reference (every audit/plan-check/pickup skill reaches the nav-infra consult) ---
# M7 close of the "operator hand-nudges the DAG/CODE_MAP in every session" surface (2026-06-11, the .E.0.10
# pickup): the adversarial-audit spec's applies_at_skills MUST each reach the nav-infra consult — via the
# shared Stage-0 doc citation OR a direct ref. A cohort skill that drops it = red build, no nudge required.
if [ "${SKIP_NAVINFRA_COHORT_CHECK:-0}" != "1" ]; then
    run_hard "nav-infra cohort reference (audit/plan-check/pickup skills reach the nav-infra consult)" \
        python3 "$REPO_ROOT/tools/check_navinfra_cohort_reference.py"
else
    RESULTS+=("  ⏭  HARD  nav-infra cohort reference (SKIP_NAVINFRA_COHORT_CHECK=1)")
fi

# --- HARD 9: index-currency (the sprint MASTER CURRENT-STATE banner ↔ the singleton active handoff) ---
# M7 close of WH-2 (stale SSoT-index banner): the MASTER "Pickup → handoffs/..." pointer kept naming a
# SUPERSEDED handoff while a newer one was the live status:active singleton — recurred across sessions,
# caught only by operator prompt, never by this floor. Cross-checks the two SSoTs; composes with HARD 6
# (singleton enforces ≤1 active; this enforces MASTER-names-it). TECH_DEBT-194.
if [ "${SKIP_INDEX_CURRENCY_CHECK:-0}" != "1" ]; then
    run_hard "index-currency (MASTER banner ↔ active handoff)" \
        python3 "$REPO_ROOT/tools/check_index_currency.py"
else
    RESULTS+=("  ⏭  HARD  index-currency (SKIP_INDEX_CURRENCY_CHECK=1)")
fi

# --- HARD 10: Class-44 cfg-flag-orphan regression guard (the #9 structural close) ---
# Promotes scan_class_44_cfg_orphan.py to STANDING-CI (was SKILL-WIRED to /bug-check only). --strict
# EXCLUDES the 5 KNOWN-PENDING cohort flags (A13/A14/A35/A36/A37 — shrinking as #9 closes) + runs the
# oracle self-check, so it fires ONLY on a genuinely-NEW operator-settable MASK_*_CFG_* flag with no live
# sharded reader → closes the Class-44 cfg-flag-orphan class structurally; the guard de-risks the paced
# tombstone migration (feedback_close_the_class_vs_migrate_every_site). Scans engine source via the tool's
# own resolver. HARD-appropriate (unlike the pre-existing-surfacing check_meta_registry): --strict's
# KNOWN_COHORT baseline means it never fires on the known backlog, only on a regression.
if [ "${SKIP_CFG_ORPHAN_CHECK:-0}" != "1" ]; then
    run_hard "Class-44 cfg-flag-orphan (--strict: NEW orphan beyond the #9 cohort = fail)" \
        python3 "$REPO_ROOT/tools/scan_class_44_cfg_orphan.py" --strict
else
    RESULTS+=("  ⏭  HARD  Class-44 cfg-flag-orphan (SKIP_CFG_ORPHAN_CHECK=1)")
fi

# --- ADVISORY: forward-promise (MED/LOW backlog expected) ---
run_advisory "forward-promise audit (--since HEAD~5)" \
    python3 "$REPO_ROOT/tools/check_forward_promise_audit.py" --since HEAD~5

# --- ADVISORY: meta-registry orphans (engine-structural; pre-existing surfaced) ---
run_advisory "meta-registry coverage" \
    python3 "$REPO_ROOT/tools/check_meta_registry.py"

# --- ADVISORY: capital-test adversarial-refute markers (TECH_DEBT-164 part B — the AR-8 failsafe) ---
# The binding adversarial-default can't be self-attested: every capital TEST block must carry an
# // ADV-REFUTE (independent refute ran) or // ADV-SELF (opt-out + reason) disposition. tests/ is
# gitignored so this is a standing marker scan, not a diff gate. Advisory: existing unmarked = KNOWN
# shrinking backlog; a NEW unmarked capital test bumps the count conspicuously at the gate.
if [ "${SKIP_CAPITAL_ADV_CHECK:-0}" != "1" ]; then
    CAP_OUT=$(python3 "$REPO_ROOT/tools/check_capital_adversarial_audit.py" 2>&1)
    if echo "$CAP_OUT" | grep -q 'WARN'; then
        CAP_N=$(echo "$CAP_OUT" | sed -n 's/.*WARN — \([0-9]*\) capital.*/\1/p')
        RESULTS+=("  ⚠️  ADV   capital-test adversarial markers — ${CAP_N:-?} unmarked block(s) (KNOWN backlog; NEW capital tests need // ADV-REFUTE or // ADV-SELF)")
    else
        RESULTS+=("  ✅ ADV   capital-test adversarial markers (every capital test carries a refute disposition)")
    fi
fi

# --- ADVISORY: decision-log completeness (a new Hard-Invariant with no D-entry = likely un-logged decision) ---
# The create->capture gap (feedback_document_as_you_go): a decision lands in its home (a new Hnn row in
# CLAUDE.md) but never gets a D-N. H22 sat un-logged until operator pushback at the .E.0.10 close -> M7
# escalation. Check 13 of check_capture_audit.py; advisory + explicit-only (heuristic, never hard-fails).
if [ "${SKIP_DECISION_COMPLETENESS_CHECK:-0}" != "1" ]; then
    run_advisory "decision-log completeness (new invariant ⇒ a D-entry; the create→capture gap)" \
        python3 "$REPO_ROOT/tools/check_capture_audit.py" --check 13 --since "${DLOG_SINCE:-HEAD~8}"
fi

# --- ADVISORY: cache-layout gate (D-320 — cross-thread straddle = H6 false-sharing / [SIZE] drift) ---
# INERT until structs are converted (mixed-state: no [STRUCT] block → early return, no clang). Layout
# via clang -fdump-record-layouts reusing the fox-symdeps parser (nvim/clang-dependent) → ADVISORY: a
# missing dep or a gate finding surfaces, never hard-blocks the doc sweep. Promote to HARD once
# conversion lands + the run cadence is set (perf: one clang run when structs exist). Never auto-aligns.
if [ "${SKIP_CACHE_LAYOUT_CHECK:-0}" != "1" ]; then
    run_advisory "cache-layout gate (converted [STRUCT] blocks: cross-thread straddle = H6 false-sharing / [SIZE] drift)" \
        python3 "$REPO_ROOT/tools/check_cache_layout.py"
fi

echo ""
echo "=== SWEEP RESULTS ==="
for r in "${RESULTS[@]}"; do echo "$r"; done
echo ""
if [ "$HARD_FAIL" = "1" ]; then
    echo "❌ SWEEP FAILED — a HARD doc/plan check failed. Fix before declaring clean."
    exit 1
fi
echo "✅ SWEEP CLEAN — all HARD doc/plan checks pass (advisories may be non-zero; see above)."
exit 0
