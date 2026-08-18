---
name: foxml-suite-refactor-queued
description: "foxml_suite needs same framework consolidation treatment as engine — queued as dedicated sub-sprint after v5.15-live-readiness `.F.4d.1.D` close"
metadata: 
  node_type: memory
  type: project
  originSessionId: 23677810-15af-419a-bb0f-e89d723c198b
  sister_specs: [project_viewer_is_imgui_decoupled_not_tui.md]
  tags: [project-state, refactor-discipline]
---

foxml_suite (the backtest + training GUI binary; built from build_suite/ with XGBoost) needs the same framework consolidation treatment that engine has been receiving through `.F.4d.1.B.*`. Current sprint scope (`.F.4d.1.*` + `.F.4e` + `.F.4f`) is engine-side primarily — Caramel surfaced 2026-05-23 that foxml_suite has only gotten CONSUMER-side migration (149-site sweep at `.B.3` Step 1.6.4 touched BacktestPanels.hpp reads of `inf.inference_cfg_<name>`), NOT producer-side framework discipline for its own cfg/state surfaces.

**Why:** ensure easier maintainability across the entire codebase, not just engine. Sister to `feedback_motivated_collaborator_for_caramel` — public AGPL + hedge fund visibility = same exacting standard everywhere. foxml_suite refactor likely predates v5.16+ decoupling (per `plans/_future/2026-05-12-decoupling-endgoal-roadmap.md` which includes "cmdline-invocable training") — hardening BEFORE decoupling = cleaner eventual restructure.

**How to apply:** at end of `.F.4d.1.D` (estimated ~2-3 weeks from 2026-05-23 ship close), fire `/ml-audit` scoped specifically to foxml_suite surface area (Backtest/ + ML training entry points + training cfg fields + RunHistory wire format + BacktestPanels + GUI panels). Draft a dedicated sub-sprint plan body (mirror `.F.4d.1` shape: cohort identification → migration → framework codification → ship close). Expected scope: ~2-3 weeks focused.

**Specific surfaces likely needing framework treatment:**
- `backtest.cfg` parser — currently manual; should be sister registry to FOREACH_GLOBAL_CFG_FIELD (FOREACH_BACKTEST_CFG_FIELD?)
- Training cfg surface — fields scattered; registry-driven; auto-flow to GUI
- BacktestPanels ImGui render — hand-coded per panel; could auto-gen from cfg metadata (sister to `.F.4e` engine GUI work)
- RunHistory wire format — HMAC-signed body; SAME Layer 6b SOFT-bump procedure codified at `.B.3` Phase F applies
- Hyperparam sweep cfg — KIND_RANGE_INT/DOUBLE RESERVED at `CoreFrameworks/CfgFieldRegistry.hpp:108-109` for v5.15.6.C; implement here
- Training pipeline → engine boot integration — cross-process model+stamp file handoff; Layer 7 cross-tool discipline + potentially `framework-driven-cli-binary-pattern.md` 2nd canonical
- `Backtest/BacktestPanels.hpp` file split — ~5500 lines; sister to TECH_DEBT-114 controller_test.cpp split discipline

**Cross-refs:**
- Parent sprint goal `v5.15-live-readiness` (the "live readiness" half is feature integration; foxml_suite consolidation is REFACTOR half extension)
- `feedback_no_defer_for_effort` — this is NEW SCOPE discovery, not effort-deferral (foxml_suite IS distinct surface area)
- `feedback_motivated_collaborator_for_caramel` — same quality bar applies
- `feedback_categorical_triggers_over_hardcoded_refs` — trigger for this sub-sprint kick-off = `.F.4d.1.D` close confirmed + `/ml-audit` scoped to foxml_suite returns concrete findings
- `plans/_future/2026-05-12-decoupling-endgoal-roadmap.md` — long-horizon decoupling; foxml_suite consolidation feeds INTO this cleanly

**Status:** CONFIRMED (Option A; pre-v5.16 sub-sprint) — not in any current plan body yet; awaiting `.F.4d.1.D` close + `/ml-audit` foxml_suite scoping run. NOT effort-deferral per `feedback_no_defer_for_effort` — sequenced AFTER `.F.4d.1` framework consolidation so foxml_suite refactor inherits the locked engine-side framework as its template.
