# Headless operation — aspirational option (CONSIDERED + DEFERRED 2026-05-14)

**Created:** 2026-05-14 (during v5.15.5.F.4c session; operator-direction conversation)
**Status:** **CONSIDERED + DEFERRED.** Caramel preference noted (`tail -f` + CLI workflow appealing) but the strategic pivot was walked back — GUI remains primary for now. This doc captures the consideration in case future revisit makes sense.
**NOT a committed plan.** No ship targets; no enforced discipline; no plan amendments downstream of this doc.

---

## What was considered

Promoting the `engine` binary (existing ANSI TUI; no SDL/OpenGL/ImGui dependency) to primary operator entry point, with `engine_gui` + `foxml_suite` becoming supplementary. New operator-facing features would ship as CLI subcommands + structured log output (`tail -f | jq` consumable) rather than new GUI panels.

The pivot would be a strategic shift, NOT a codebase restart — the codebase already has the headless skeleton (`./build.sh test` produces a GUI-free binary). The split between `engine` and `engine_gui` is at the binary level, not the source level.

## What was decided

**Deferred.** Reasons:

- The `tail -f` workflow is appealing in theory but hasn't been validated against actual operator use.
- GUI is currently working + maintained; pivot risks unwinding correct work for an unvalidated direction.
- `.F.4c` work in progress is forward-compatible with either direction (metadata bits + framework foundations work for GUI-primary OR headless-primary).
- "Continue what we're doing + add hooks via inline comments" is the lighter-touch approach.

## What was kept (forward-compatible groundwork)

The following landed at `.F.4c` and remain useful regardless of GUI vs headless priority:

- **4 metadata bits** on `CfgFieldDescriptor` — `BOOT_ONLY`, `HAS_SIDE_EFFECT`, `DEPRECATED`, `WARN_ON_CLAMP`. Solve structural problems independent of operator UX direction. GUI walker can consume `BOOT_ONLY` to hide rng seeds from panel; CLI walker (if ever built) can consume same bit.
- **TECH_DEBT-063** (`field_defs[]` elimination) — happens automatically as registry migration progresses, regardless of headless priority.
- **TECH_DEBT-065** (JSON structured log) — useful for operator log monitoring regardless of GUI/headless. May or may not ship.
- **TECH_DEBT-066** (CLI subcommands `--explain-cfg` / `--list-cfg` / `--validate-cfg`) — useful for headless workflow AND for paper-test ops debugging. May or may not ship.
- **TECH_DEBT-067** (per-core observability) — useful for production debugging regardless. May or may not ship.
- **Inline comments approach** — as new cfg fields land with `BOOT_ONLY` etc. bits, add comments like `// BOOT_ONLY: future headless CLI walker filters by this bit if/when --list-cfg ships`. Captures the future consideration without committing the codebase to a direction.

## What was walked back

- **CLAUDE.local.md "Operator UX orientation" section** — removed. No directional commitment.
- **`.F.4e` plan reframe** — reverted to original scope (KIND_STRING + KIND_FILE_PATH + 5 GUI metadata bits + cfg.example auto-gen + reverse-drift CI). Re-evaluate when `.F.4e` is in scope.
- **`.F.4d` Step 1.D.5 (headless CLI consumer note)** — removed. `.F.4d` derived filter framework stays consumer-agnostic without explicit commitment to CLI consumers.
- **TECH_DEBT-064** — softened from "GUI feature freeze process discipline" to "headless operation option (considered + deferred)".

## When to revisit

This doc is worth re-reading if:

- The `.F.4` umbrella closes and operator (Caramel) wants to test-drive the `tail -f` workflow on real engine output (`engine` binary running in production-like config; operator scripts log parsing; verify ergonomics)
- GUI maintenance burden becomes blocking (e.g., `SettingsPanel.hpp` field_defs[] grows beyond manageable; ImGui dep version bump breaks something; new panel asks pile up)
- A specific operator workflow surfaces that's genuinely better in headless than GUI (e.g., remote ops via ssh; programmatic monitoring via JSON snapshots; multi-engine fleet management)
- Production deployment targets that don't have display servers (cloud VMs, containers without X11) — then headless becomes operationally required, not just preferred

## What this doc is NOT

- ❌ A committed direction. (Deferred, not adopted.)
- ❌ A discipline rule. (No "must" or "MUST NOT" enforcement.)
- ❌ A timeline. (No ship target; no due date.)
- ❌ A plan amendment trigger. (Downstream plans were reverted to original scope.)

It's a captured conversation + a flag for future revisit. The metadata bits + TECH_DEBT entries that landed are the only actionable artifacts.

---

## Cross-references

- `DOCS/TECH_DEBT.md` entries 063, 064 (deferred-option), 065, 066, 067
- `plans/v5.15-live-readiness/subplans/2026-05-13-v5.15.5.F.4c-int-int_enum-bool-migration.md` Step 2 "New metadata bits — headless-first orientation" section (KEPT — bits are useful regardless)
- `DataStream/EngineTUI.hpp` (existing ANSI TUI substrate; available for future enhancement)

---

**End of doc.** This is a deferral record, not a roadmap. Revise to "active roadmap" if pivot is later approved.
