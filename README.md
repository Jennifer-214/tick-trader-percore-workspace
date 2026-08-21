# tick-trader-percore-workspace

The engineering substrate for **[FoxML_Trader_v2](https://github.com/Jennifer-214/FoxML_Trader_v2)** — a
per-node risk-sharded, tick-level crypto HFT engine in C++17 (40-400ns p99
hot path, decimal fixed-point money, X-macro registries, no heap).

The engine repo holds the code that runs. This repo holds nearly everything
that decides *what* gets written and *whether it is allowed to ship*: the
design-spec catalog, the plan + decision-log archive, the CI check tools, the
test sources, the anti-pattern catalog, and the Claude Code skill/agent
definitions that drive an audit-first workflow. Neither repo is complete
without the other — the engine's `plans/`, `tests/`, `tools/`, `DESIGN_SPECS/`
and most of its `DOCS/` are symlinks into this one.

The name is historical: the engine was called `tick-trader-percore` when the
split happened.

## What is actually in here

| Path | Contents | Scale |
|---|---|---|
| `plans/` | Ship plans, readiness reports, decision logs, handoffs, postmortems, audits — sprints v5.9 → v5.15 | 962 markdown files |
| `DESIGN_SPECS/` | Reusable architectural patterns, tagged by surface / concern / lifecycle stage | 194 specs, 12 categories |
| `DOCS/` | Architecture, invariants, operator manual, changelogs, glossary, the `TECH_DEBT` / `PARITY_ISSUES` ledgers, and 58 recurring bug classes | 205 files |
| `tools/` | CI checks and their selftests, golden-blessing tooling, `foxtag` tag scanner, latency budgets | 74 Python (43 `check_*`), 30 selftests |
| `tests/` | Engine test sources, golden vectors, `INVARIANTS_MAP.md` | 20 files |
| `claude-skills/` | 40 Claude Code skills — audit gates, anti-pattern scans, ship + handoff workflow | 40 skills |
| `claude-agents/` | Agent class definitions (a / c / d / i / v) | 5 |
| `.githooks/pre-commit` | One hook, checks A–T: identifier retirement, determinism net, struct layout safety, latency-path conformance, doc floor, P&L single-source, … | 38 KB |
| `CLAUDE.md` + subsystem `CLAUDE.md` | Always-loaded orientation: hard invariants H1–H22, priority gradients, discovery index | root + 5 nested |
| `memory.backup/` | Operator-collaboration memories, mirrored from `~/.claude/` | 161 |
| `configs/` | Annotated engine / backtest / controller cfg defaults (no secrets) | 4 |
| `FEATURE_LOOKUP.md` | Operator-visible feature catalog — cfg flags, fallback behavior, where to verify each feature at runtime | 120 KB |
| `PAPER_TESTING/` | Per-version paper-run observation / watch / punch lists | 6 |
| `GEMINI_FINDINGS/`, `GEMINI_SUGGESTIONS/` | Cross-model audit sweeps — findings graded by severity, kept as a second-opinion record | 21 |
| `backups/`, `DOCS/archive/`, `deferred_5.15`, `OPTIMIZATION_POINTS.md`, `note` | Overlay snapshots, retired skill definitions, deferral rationales, loose working notes | — |

`DESIGN_SPECS/` breakdown: framework-patterns 74 · meta-disciplines 36 ·
refactor-patterns 25 · data-disciplines 16 · concurrency-patterns 12 ·
audit-methodologies 8 · doc-disciplines 7 · wire-format-patterns 6 ·
plan-templates 5 · feature-patterns 3 · ledger-templates 1 ·
subsystem-designs 1.

## The workflow it encodes

Capital-bearing code held to a correctness-first bar: plan → pre-coding audit
gate → implement → ship → postmortem, with structural fixes preferred over
patches whenever a bug class can recur.

- **Patterns are catalogued, not remembered.** A pattern earns a spec in
  `DESIGN_SPECS/`, advances through lifecycle stages (`2-draft` →
  `6-cadence-locked`), and gets promoted to a `CLAUDE.md` invariant once it has
  a cohort of applications behind it.
- **Bug classes are catalogued too.** 58 classes in
  `DOCS/recurring-bug-patterns/`, each with detection signatures and a
  false-positive surface, swept before coding.
- **Audits run before code, not after.** The skills in `claude-skills/` are
  the gates — `/precoding-audit-gate`, `/blindspot-scan`, `/dod-audit`,
  `/hft-audit`, `/bug-check`, `/readiness`.
- **Mechanical rules get a CI check.** If a discipline can be enforced by a
  script it becomes a `tools/check_*.py` with its own selftest, wired into the
  pre-commit hook and the ship gate.
- **Decisions are written down.** `plans/*/decision-logs/` records what was
  decided and why; handoffs carry state across context boundaries.

## Start here

- `CLAUDE.md` — hard invariants (H1–H22) + priority gradients; the orientation doc
- `DOCS/DESIGN_PHILOSOPHY.md` — the why behind every principle, with worked examples
- `DESIGN_SPECS/README.md` — the pattern catalog and its tag vocabulary
- `DOCS/RECURRING_BUG_PATTERNS.md` — the anti-pattern catalog
- `plans/INDEX.md` — the plan archive; `plans/v5.15-live-readiness/MASTER.md` is the active sprint

## How it is wired

```
~/code/tick-trader-percore-workspace/     <- real directories (this repo)
    plans/  DESIGN_SPECS/  DOCS/  tools/  tests/
    claude-skills/  claude-agents/  .githooks/  CLAUDE.md

~/code/FoxML_Trader_v2/                   <- symlinks into the workspace
    plans          -> ../tick-trader-percore-workspace/plans
    DESIGN_SPECS   -> ../tick-trader-percore-workspace/DESIGN_SPECS
    tools          -> ../tick-trader-percore-workspace/tools
    tests          -> ../tick-trader-percore-workspace/tests
    .githooks      -> ../tick-trader-percore-workspace/.githooks
    CLAUDE.md      -> ../tick-trader-percore-workspace/CLAUDE.md
    .claude/skills -> ../../tick-trader-percore-workspace/claude-skills
    .claude/agents -> ../../tick-trader-percore-workspace/claude-agents
    DOCS/<name>.md -> ../../tick-trader-percore-workspace/DOCS/<name>.md   (61 per-file links)
    <Subsystem>/CLAUDE.md -> ../../tick-trader-percore-workspace/<Subsystem>/CLAUDE.md
```

77 symlinks in total. All relative, so the layout works on any machine where
both repos sit under the same parent directory. The engine `.gitignore`s these
paths, so edits land in this repo's history rather than the engine's.

## Syncing

Most content propagates through the symlinks — editing a plan or a spec from
inside the engine repo writes straight into this working tree. A few things
have no symlink and are copied explicitly by the `/sync-workspace` skill:
`engine.cfg` / `backtest.cfg` / `controller.cfg` → `configs/`, the private
`CLAUDE.local.md` overlay → `CLAUDE.local.md.backup`, and
`~/.claude/projects/<project>/memory/*.md` → `memory.backup/`.

Backup is on-demand rather than continuous — a file edited a dozen times in a
session should be one checkpoint commit, not twelve.

## Not in here

- Engine source, build artifacts, model binaries, recorded tick data
- `secrets.cfg`, API keys, `.claude/settings.local.json`,
  `.claude/scheduled_tasks.lock` — runtime state and machine-specific config
- The private `CLAUDE.local.md` overlay itself — only its `.backup` snapshots

## Caveats

These are working notes, not a product. Plans record what was believed at the
time they were written, and superseded ones stay in the tree on purpose — the
reasoning trail is the point. Cross-references assume the engine repo sits
alongside; some resolve only through the symlink layout above. The engine is
AGPL-3.0; this repo carries no license file of its own.
