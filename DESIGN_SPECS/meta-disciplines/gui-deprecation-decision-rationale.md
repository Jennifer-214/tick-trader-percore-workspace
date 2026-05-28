---
type: meta-discipline
stage: 3-first-canonical
version: 1.0
established: 2026-05-28
landing_ship: v5.15.5.F.4d.1.E.2
canonical_applications:
  - v5.15.5.F.4d.1.E.2 (engine_gui hard-deprecation; foxml_suite deprecation)
sister_specs:
  - meta-disciplines/headless-engine-viewer-split-pattern.md (parent; what replaces GUI)
  - meta-disciplines/backwards-compat-not-default-concern.md (rationale; clean break)
tags: [meta-discipline, gui-deprecation, power-user-design, clean-break]
surface: [build-system, engine-binary, viewer-layer]
applies_at_skills: [/precoding-audit-gate]
---

# GUI deprecation decision rationale

**Pattern intent:** Codifies the framework for "deprecate convenience surface in favor of power-user infrastructure" decisions. Worked example: engine_gui + foxml_suite GUI hard-deprecated at `.E.2` in favor of fox-tui + fox-cli + foxml-train.

## Problem statement

Existing engine had Dear ImGui-based GUI integrated. Operator-facing surface; convenient for novice operators; but:

- Couples engine binary to GUI dep (SDL2; OpenGL; ImGui)
- Single-process; GUI thread crash takes down trading
- Requires X11/Wayland (not headless ssh)
- Single-viewer; can't observe from multiple operators
- Maintenance overhead

For HFT-class engine + headless service architecture (per D-4): GUI is wrong abstraction.

## Decision framework: when to hard-deprecate convenience surface

Apply this rubric:

1. **Does the convenience surface couple to load-bearing infrastructure?**
   - YES: deprecation candidate
   - NO: keep as one of many viewers

2. **Is there a power-user replacement that's clean separation?**
   - YES: deprecate convenience; use power-user replacement
   - NO: defer deprecation

3. **Does deprecation enable other architectural improvements?**
   - YES: deprecate aggressively
   - NO: deprecate at convenience (don't rush)

4. **What's the operator migration cost?**
   - LOW (workflow analog exists): hard-deprecate
   - HIGH (no workflow analog): soft-deprecate + transition period

5. **Is convenience surface still needed by any current operator?**
   - YES: keep maintained
   - NO: archive

Apply to engine_gui:
1. Couples engine to SDL2/OpenGL → YES
2. fox-tui (notcurses) + fox-cli are clean replacements → YES
3. Headless boundary unlocks decoupling endgame → YES
4. Operator workflow (Caramel) prefers CLI/TUI per power-user discipline → LOW migration cost
5. No other operators currently → NO need to keep

**Decision: HARD-DEPRECATE.** Archive engine_gui binary; remove from build; replace with fox-tui + fox-cli.

Apply to foxml_suite:
1. Couples ML training to GUI binary → YES
2. foxml-train CLI + Jupyter for exploration → YES
3. Headless training enables CI/cron-driven training → YES
4. Operator workflow can shift (Jupyter for exploration; CLI for production) → LOW
5. Same operator → NO need to keep

**Decision: HARD-DEPRECATE.** Archive foxml_suite binary; replace with foxml-train CLI.

## Operator migration impact

For engine_gui → fox-tui:

| Surface | Pre | Post |
|---|---|---|
| Launch | `./engine_gui` | `fox-tui` (notcurses; SSH-able) |
| Operator commands | GUI menus | fox-cli verbs |
| Live state view | GUI panels | fox-tui panels (similar layout; vi keybindings) |
| Remote access | X-forward over SSH (slow) | Native TUI over SSH (fast) |

For foxml_suite → foxml-train + Jupyter:

| Surface | Pre | Post |
|---|---|---|
| Interactive ML exploration | foxml_suite | Jupyter notebooks |
| Production model training | foxml_suite GUI | foxml-train CLI |
| Backtest with charts | foxml_suite | Jupyter + matplotlib |

## Archival strategy

```
legacy/
├── engine_gui/                  # archived Dear ImGui code; preserved for reference
│   ├── README.md                # "DEPRECATED at .E.2; preserved for reference"
│   ├── GUI/                     # original GUI panels
│   └── (other GUI-specific files)
├── foxml_suite/                 # archived foxml_suite source
│   └── README.md
└── README.md                    # documents what's here and why
```

`build.sh` no longer builds these; they exist as reference. Operator who wants old GUI behavior can re-enable manually (but documented as DEPRECATED).

## Anti-patterns avoided

- **Maintaining old surface during transition** — maintenance overhead; ambiguity
- **Silent removal** — operator surprise
- **Forcing one viewer pattern** — multiple viewers (TUI; CLI; Grafana) is better than one

## When to NOT hard-deprecate

- Convenience surface is decoupled (e.g., separate binary)
- Multiple operators use it
- No power-user replacement
- Operator migration cost is HIGH

In those cases: keep convenience surface + add power-user options alongside.

## Stage progression criteria

- **Stage 3 first canonical** (`.E.2`): engine_gui + foxml_suite hard-deprecated
- **Stage 4 cohort** (when 2nd surface hard-deprecated): pattern proven
- **Stage 5 CLAUDE.md** (3rd application): promoted

## Cross-references

- Parent: `meta-disciplines/headless-engine-viewer-split-pattern.md` (what replaces)
- Sister: `meta-disciplines/backwards-compat-not-default-concern.md` (rationale)
- First application: `plans/v5.15-live-readiness/subplans/2026-05-28-v5.15.5.F.4d.1.E.2-headless-configs-docs.md`
