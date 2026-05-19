---
type: ledger-template
class_id: 32
title: Mega-file accumulation past size threshold without split discipline (drift-prone + navigation-degrading)
parent_index: DOCS/RECURRING_BUG_PATTERNS.md
established: 2026-05-19
surface_tags: [ci-tooling, registry, test-infrastructure]
severity: medium
recurrence_count: 4
first_instance: 2026-05-18 (3 mega-files surfaced at v5.15.5.F.4d.1.B.3 — TECH_DEBT.md 2013 lines / RECURRING_BUG_PATTERNS.md 2198 lines / /readiness SKILL.md 1681 lines; pre-existing test file controller_test.cpp ~25k lines codified at v5.11.35)
closure_mechanism: file-size-split-discipline + per-type hard thresholds + INDEX dispatch pattern + /metadata-audit threshold violations report + tools/check_doc_metadata.py (sister CI tool checks frontmatter; file-size check can be added)
sister_classes: [11, 18, 31]
---

# Class 32 — Mega-file accumulation past size threshold without split discipline

**Detected:** 2026-05-18 (during institutional-memory refresh at v5.15.5.F.4d.1.B.3; 3 mega-files surfaced exceeding hard thresholds: TECH_DEBT.md 2013 lines / RECURRING_BUG_PATTERNS.md 2198 lines / /readiness SKILL.md 1681 lines).
**Severity:** MEDIUM — file is functional but accumulates invisible cost: slow to navigate, slow to load (token-budget impact when context-included), drift-prone (changes scattered across one large file), and merge-conflict surface area grows.

## Recurring symptom

A file grows past its type-specific hard threshold without periodic split review. Common shapes:

```
DOCS/TECH_DEBT.md             (2013 lines, ~115 entries — single monolithic ledger)
DOCS/RECURRING_BUG_PATTERNS.md (2198 lines, 32 classes — single monolithic catalog)
SKILL.md files                 (>1500 lines — per-section bodies that should be sidecars)
tests/controller_test.cpp     (~25k lines, 3118 tests — single monolithic test file)
```

Per-type hard thresholds (per `DESIGN_SPECS/doc-disciplines/file-size-split-discipline.md`):

| File type | Hard threshold |
|---|---|
| Always-loaded docs (CLAUDE.md / CLAUDE.local.md / MEMORY.md) | 600 lines |
| Tests | 5000 lines OR 100 sections |
| Source headers (.hpp) | 1500 lines |
| Source bodies (.cpp) | 2000 lines |
| Ledger files (TECH_DEBT / RBP / PARITY / FEATURE / HOT_PATH / LANDMINES) | 2000 lines |
| SKILL.md | 1500 lines |
| DESIGN_SPECS | 1200 lines |
| Plan body docs | 1200 lines |
| Memory rules | 500 lines |

## Why this is a class (not a one-off bug)

Files grow incrementally past threshold without being noticed. Each individual entry/test/section addition feels small. Accumulation past threshold has invisible cumulative cost:
- **Navigation:** finding a specific entry in a 2000-line file takes longer
- **Token budget:** including the file in context burns budget; truncation risk
- **Drift surface:** large files have more places where stale content can hide
- **Merge conflict surface:** parallel work touching different sections of one large file collides
- **Cognitive load:** reviewer can't hold the full file in mental working memory

The first canonical worked example (test file size discipline) was codified at v5.11.35 in CLAUDE.md as a TYPE-SPECIFIC rule. Generalized to ALL file types at v5.15.5.F.4d.1.B.3 (3 simultaneous applications: TECH_DEBT split / RBP split / /readiness split).

## False-positive surface (per M3 discipline)

Not all large files are Class 32:
- **Auto-generated artifacts** (CHANGELOG.md / catalog files) — size grows with project history; split breaks chronological retrieval
- **Single-purpose canonical references** (Limits.hpp / Version.hpp) — small file with one responsibility; size limit doesn't apply
- **Generated indexes** (DESIGN_SPECS/README.md / TAG_INDEX.md) — auto-regenerated; size reflects content count
- **Bounded-size by design** — e.g., monolithic ENUM definition that's already at its complete state

## Closure mechanism

**Structural fix** per `DESIGN_SPECS/doc-disciplines/file-size-split-discipline.md`:

1. **Split + INDEX pattern:** when file exceeds hard threshold:
   - Identify split criteria (by-status / by-cohort / by-domain / by-concern / by-date)
   - Create sub-files; each retains canonical content
   - Convert original to INDEX file with `splits_into:` frontmatter + table of contents
   - Sub-files get `parent_index:` frontmatter pointing back
   - Cross-refs preserved via ID-based grep (TECH_DEBT-NNN / Class N / Check N grep-retrievable regardless of sub-file location)

2. **Periodic audit:** `/metadata-audit` quarterly cadence reports threshold violations
3. **Operator-flagged review:** "this file is hard to navigate" surfaces threshold candidate
4. **CI verification:** `tools/check_doc_metadata.py` can be amended to flag size violations at commit time (queued; sister to existing frontmatter validation)
5. **Sister discipline at ship-close:** `/ship` skill amends suggest split if any modified file crosses threshold this ship

## Worked instances

- **v5.11.35 (codified):** Test file size discipline in CLAUDE.md (`tests/controller_test.cpp` > 5000 lines OR > 100 sections must split BEFORE adding more tests). TECH_DEBT-114 tracks the actual split (queued).
- **v5.15.5.F.4d.1.B.3 (2026-05-18; 3 simultaneous applications):**
  - TECH_DEBT.md 2013 → 214-line INDEX + open.md (79 entries) / in-flight.md (2 entries) / closed.md (24 entries) — TECH_DEBT-116 closure
  - RECURRING_BUG_PATTERNS.md 2198 → 80-line INDEX + 29 per-class sub-files — TECH_DEBT-117 closure
  - /readiness SKILL.md 1681 → 625 lines (orchestration + index) + 26 per-check sidecar files — TECH_DEBT-118 closure
  - Generalized discipline codified as `DESIGN_SPECS/doc-disciplines/file-size-split-discipline.md`

## Sister classes

- **Class 11** (Extensibility friction / silent drift) — parent meta-class; Class 32 is one shape of silent drift (file size accumulates silently)
- **Class 31** (Hardcoded refs in always-loaded docs) — sister at doc-layer drift family; both are mechanical-accumulation drift patterns
- **Class 18** (Mirror-incomplete) — parent at structural-drift family

## Cross-references

- `DESIGN_SPECS/doc-disciplines/file-size-split-discipline.md` (closure mechanism; threshold table; split + INDEX pattern)
- `DESIGN_SPECS/doc-disciplines/categorical-triggers-in-always-loaded-docs.md` (sister doc-discipline; same drift family)
- `tools/check_doc_metadata.py` (CI enforcement; size check sister to frontmatter validation)
- `/metadata-audit` skill (quarterly threshold violations report)
- CLAUDE.md § Test file size discipline (canonical predecessor; v5.11.35)
- CLAUDE.md § File-size split discipline (generalized; 2026-05-18)
- `feedback_file_size_split_discipline.md` (going-forward rule)
- TECH_DEBT-114 (test file split queued; first canonical worked instance)
- TECH_DEBT-116/-117/-118 (mega-file splits applied at v5.15.5.F.4d.1.B.3; canonical worked applications)
- TECH_DEBT-115 (institutional-memory rollout that codified the generalized discipline)
