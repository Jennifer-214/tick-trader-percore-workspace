# PAPER_TESTING — per-sprint paper-test reference

**Workspace-private.** Operator-side notes for what to watch + try
when running paper-test cycles after each sprint umbrella ships.

## Structure

```
PAPER_TESTING/
├── README.md          — this file (sprint index)
└── POST_<sprint>/
    ├── WATCH_LIST.md  — passive things to observe in logs/GUI during
    │                    normal paper-trading (what's NEW or CHANGED
    │                    in this sprint)
    ├── TRY_LIST.md    — active scenarios to deliberately exercise
    │                    (test hot-swap, test drift detection, test
    │                    new cfg fields, etc.)
    └── OBSERVATIONS.md — scratchpad: findings, anomalies, weird logs,
                          things to bring back to Claude
```

Each sprint's directory captures what's new in that sprint — NOT a
full operator manual. The `DOCS/` files in the engine repo
(OPERATOR_DEPLOYMENT, QUICKSTART, ML_USAGE, etc.) stay the canonical
operator reference; this dir is the supplement for "what should I
watch for THIS sprint's changes."

## Sprint index

| Sprint | Status | Directory | Notes |
|---|---|---|---|
| **v5.15** | Open (just shipped 2026-05-12) | `POST_v5.15/` | Live-readiness sprint; 6 TECH_DEBT + 4 PARITY closures; shadow-load hot-swap; trading_mode field; Model Health drift surface; LiveReadiness boot gate; Stamp_AssembleAndEmit helper |
| (future) v5.16 | Not started | — | — |

## Workflow per sprint

1. Sprint ships → Claude generates `POST_<sprint>/{WATCH,TRY,OBSERVATIONS}.md`
2. Operator runs paper-test for ≥1 week
3. Operator scribbles findings in OBSERVATIONS.md as they happen
4. End of paper-test phase: review OBSERVATIONS together; decide
   ship-readiness-for-live OR queue findings as v5.X+1 sprint scope
5. Mark sprint status in this README

## Why this lives in the workspace (not engine repo)

- Operator-specific deployment context (real symbols, real cfgs, real
  cores, real machine details)
- Findings may surface bugs not yet ledger-entered; ledger entries
  cross-link here when they originate from paper-test observations
- Sprint-specific "watch for X" lists rot fast — once v5.15 ships +
  paper-test closes, the WATCH_LIST is historical; engine docs stay
  evergreen

## Cross-references

- Sprint umbrella postmortem: `plans/<sprint>/postmortems/*umbrella-postmortem.md`
- Per-sub-ship postmortems: `plans/<sprint>/postmortems/*-postmortem.md`
- TECH_DEBT + PARITY ledger entries: `DOCS/TECH_DEBT.md` + `DOCS/PARITY_ISSUES.md`
- Decoupling roadmap (per-ship breadcrumbs): `plans/_future/2026-05-12-decoupling-endgoal-roadmap.md`
