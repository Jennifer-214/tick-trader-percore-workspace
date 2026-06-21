---
type: refactor-pattern
stage: 4-cohort
version: 1.1
established: 2026-06-09
tags: [refactor-pattern, doc-discipline, terminology-evolution, ci-tooling]
surface: [registry, boot-time]
sister_specs: [canonical-sister-extension-discipline.md, single-source-of-truth-discipline.md]
sister_docs: [DOCS/recurring-bug-patterns/class-36-overlapping-span-substitution-corruption.md, plans/v5.15-live-readiness/rename-candidates-running-list.md]
applications: ["v5.15.5.F.4d.1.E.0.8 Ship A.5 FPN→FPN_Binary (1st canonical)", "v5.15.5.F.4d.1.E.1.1 Core→Node (3645 sites; 2nd application, LANDED 2026-06-21 → promoted Stage 4; added the DOC-DATA-FILE bucket + the World-1/World-2 compiler-oracle lesson; TECH_DEBT-142 closure home)"]
---

# Rename-ship methodology

**Stage 4 COHORT (promoted 2026-06-21 at `.E.1.1`, the 2nd application).** Authored Stage 2 DRAFT 2026-06-09 at A.5 Step 0 (gate-enriched by `plan_checks/2026-06-09-a5-rename-gate-synthesis.md` S-3/S-6/S-7/S-8/S-9/S-12); 1st canonical Ship A.5; 2nd application `.E.1.1` Core→Node (3645 sites) — which added the DOC-DATA-FILE triage bucket + the World-1/World-2 compiler-oracle lesson (`feedback_rename_enumerator_is_world2_aid_compiler_is_world1`).

## Problem

Symbol/terminology renames recur as dedicated ships (A.5 `FPN`→`FPN_Binary`; `.E.1` Core→Node ~5,000 sites; queued: `Backtest_*` unification, `EngineSharded/` dir question — see `rename-candidates-running-list.md`). Ad-hoc renames fail in recurring ways: prose-token over-rename corrupting historical/transition docs (B19; TECH_DEBT-142), overlapping-span substitution corruption (Class 36), silently-dead tool regexes (guards string-matching the old spelling), missed cohort surfaces (docs trees, build files, skills that scaffold code), and acceptance gates citing tools that no longer exist. The methodology below is the execution recipe; each phase names the failure it prevents.

## Phase 1 — Token analysis (before any plan locks)

1. **Collision check:** target spelling must be absent from code (`rg '\b<NEW>\b'` = 0 code hits; historical comment mentions → allowlist).
2. **Word-boundary exactness:** determine precisely what `\b<OLD>\b` matches. `_` is a word character — `\bFPN\b` matches neither `FPN_ToDouble` nor `is_FPN_v` nor `FPN_Binary`. Attempt a DISPROOF (construct strings that would over-match) rather than asserting.
3. **Pairwise substring-relation matrix (MANDATORY — Class 36):** for every token in the rename set × every related identifier, record ⊂/⊅ relations (e.g. `FPN` ⊂ `is_FPN_v`, `FPN` ⊂ `FPN_Binary`). The safety property is **word-boundary DISJOINTNESS + sequenced single-token passes** — never "the tokens don't overlap" (usually false as substrings). Multi-token renames (`.E.1`: `core_id`, `per_core`, `MAX_CORES`, …) order passes so no earlier pass's OUTPUT is a later pass's INPUT.
4. **Totality-oracle classification, per token** (the load-bearing discriminator):
   - **COMPILER-GUARDED** — C++ type/trait/fn tokens: a missed site = red build. Grep+mechanical-replace+red-build is sufficient AND complete; AST tooling optional.
   - **TOOL-REGEX** — Python/CI/script sites that string-match the token (`check_storage_t_coverage.py:86-87` `variant.startswith("FPN<")` / `"is_FPN_v<T>" in dispatch_text`; doc-guards' `CANON_RE`). **The compiler CANNOT see these; they go silently dead.** Enumerate as an explicit cohort, updated in the SAME COMMIT as the code flip, each guard teeth-proofed RED→GREEN.
   - **PROSE-AMBIGUOUS** — tokens with natural-language collisions across contexts (`.E.1`'s "core": CPU-core vs trading-node). Grep cannot decide; REQUIRES AST/symbol-aware tooling for code + per-site classification for docs (TECH_DEBT-142's ask). This class is WHY `.E.1` cannot reuse A.5's grep-primary mechanism unmodified.

## Phase 2 — Enumeration freeze

- Run the enumeration greps; **paste output VERBATIM into `plan_checks/`** (`feedback_paste_tool_output_dont_summarize`); wire `check_plan_enumeration_completeness.py` as the drop-guard.
- **Mechanization (CODE-side):** `tools/cascade.py rename` is the enumerator — engine source **plus the compiler-blind apparatus** (`tools/`/`build.sh`/`.githooks/`, the surface a grep-only freeze forgets, where a stale regex commits GREEN) + the `#include`-cascade for file-basename renames + the expected-residual allowlist, classified by the Phase-3 buckets below. Sister to the `.md`-side executor `check_doc_rename_classification.py` (Phase 5). ENUMERATES only — the code rename stays the human's ONE mechanical commit (Phase 4; compiler = oracle). See `rename-cascade-enumeration-tooling.md` (TD-175a); the standing "a future rename left an apparatus regex dead" net rides `check_tools_inventory.py`'s `build.sh`-scan.
- **World-1 vs World-2 — the enumerator is a planning aid, the compiler is the completeness oracle.** The freeze/enumerator de-risks the **compiler-BLIND** World-2 surface (apparatus + the DOC-DATA-FILE bucket); the **COMPILER is World-1** code-consumer-completeness — a half-renamed tree won't compile. So **budget a red→green compile loop**: the enumerator WILL have narrow spots (E.1.1: `.cores[` matched only dot-access → missed the `cores[N]` decl / `->cores[` arrow / bare `cores`; `core_[a-z]` missed regex-metachar `core_\w+`/`"core_"`/`core_<digit>`; the scan omitted `tests/`). The compiler caught every code one (7 rounds); the build + doc-CI gates caught the World-2 ones. Don't over-invest in making the enumerator code-complete — it can't be; the compiler is. Memory `feedback_rename_enumerator_is_world2_aid_compiler_is_world1`.
- Produce the **expected-residual ALLOWLIST** (file:count) for surfaces that legitimately keep the old spelling (ship-history comment blocks, archived dirs, `experiments/` exemptions). Post-rename totality = "grep matches the allowlist EXACTLY", never "= 0 hits" (which fails on the first historical mention).
- Plan-body counts are at-draft snapshots; the Step-1 freeze output is authoritative (counts rot between draft and code-time — D-144 generalization).

## Phase 3 — Triage buckets

| Bucket | Rule |
|---|---|
| CODE-TOKEN | mechanical replace; compiler = totality oracle |
| TOOL-REGEX | same-commit cohort; teeth-proof each guard RED→GREEN |
| COMMENT/STRING | current-identity → rename; explicit was/history phrasing → preserve |
| STALE-REWRITE | text that was ALREADY wrong before the rename (stale banners/sizes) — rewrite, don't token-swap a falsehood into a new falsehood |
| FORWARD-DOC | sweep via the doc-rename executor (Phase 5); includes non-obvious trees: engine-real doc subdirs inside symlinked trees, `plans/_cross-cutting/` living disciplines, `claude-skills/*/SKILL.md` (skills that SCAFFOLD code), build files' option-strings, root-level lookup docs |
| DOC-DATA-FILE | build/doc-CI-BOUND docs a check validates code against: `MANUAL_FIELDS_INVENTORY.md` Section A, `DOCS/TOOLS.md` tool-rows, skill `SKILL.md` tool-name refs, plan-body `file:line` citations → **co-migrate WITH the code commit** (NOT the Phase-5 narrative sweep — these are DATA, not narrative). The content-sub's no-docs scan systematically MISSES this bucket → the build + `check_session_docs.sh` gates are the backstop (E.1.1 caught: the integrity Section-A + 6 skill tool-refs + a plan citation) |
| HISTORICAL-PRESERVE | changelogs, postmortems, decision logs, handoffs, plan_checks, archives, memory corpus (flag-only) — terminology-evolution: bridge, don't rewrite |
| OTHER-SHIPS' PLAN BODIES | NOT swept — they re-audit at their own pre-coding gates; their sketches may target a DIFFERENT future spelling (`.E.1` money fields → `FPN_Decimal`, not `FPN_Binary`) |

## Phase 4 — Execution

- **ONE mechanical commit for the whole code-token pass** (+ TOOL-REGEX cohort). Per-dir commits are non-compiling checkpoints (the core flip leaves the build red until the last consumer converts) = bisect hazards. Red-build iterates LOCALLY; commit when whole-pass green + suite green.
- Strings/comments triage, then docs, as separate reviewable commits.
- Never introduce a temporary alias/bridge to make intermediate states compile — it blinds the totality oracle (deduction subtleties: an alias template is a NON-DEDUCED context; see D-151).

## Phase 5 — Doc sweep + bridge

- Execute via **`tools/check_doc_rename_classification.py`** (the `.D.1` Class-36-hardened token-map executor: overlap resolution, path-like-token KEEP, regression-tested) — do NOT hand-sweep or sed.
- **Verify the EXECUTOR's matching semantics against the Phase-1 substring matrix BEFORE `--write`** (A.5 incident, 2026-06-09): if any RENAME_MAP value CONTAINS its key (`FPN` ⊂ `FPN_Binary`), the executor MUST be boundary-anchored or `--apply` is non-idempotent — re-encountering already-renamed text compounds it (`FPN_Binary_Binary`). The `.D.1`-era matcher was unanchored (safe for `per-core`→`per-node`, where value ⊅ key); fixed with lookaround anchoring at the A.5 incident. **Idempotency proof = run `--apply` (preview) a second time over swept files and require 0 new applies.** Checking the grep against the matrix is NOT checking the tool against it — they are different matchers.
- **Exclude self-referential docs from the token sweep** (this spec, the rename plan body, the candidates list): docs that *discuss* the tokens cannot be token-swept (B19's transition-doc clause applied to the rename's own apparatus).
- Glossary bridge entry (old → new, dated) at the canonical glossary home — check the glossary's OWN scope rule for which home (DESIGN_PHILOSOPHY § 15 = deployment terms; runtime primitives → operator `DOCS/GLOSSARY.md`).
- Generated outputs (`DOCS/CODE_MAP.md`) are EXCLUDED — regenerate, never sweep.

## Phase 6 — Verification

- Totality greps vs the frozen allowlist (exact match).
- Value-identity: full suite, assertions byte-unchanged.
- **Codegen A/B oracle:** determinism-net output (e.g. `check_fp_determinism.sh`) captured pre/post → diff EMPTY. Uses the NET only; any frozen golden untouched (two-foundations).
- H21: renames NEVER touch persistence/wire-visible identifiers (cfg keys, persisted codes, stamp fields, snapshot versions). Verify by grep pre AND post. **If a rename WOULD touch one, it is not a rename ship — it is an epoch change; STOP and re-scope.**
- Guard teeth-proofs RED→GREEN; doc CI sweep green.

## Sister-scan lesson (recorded from A.5's gate)

Canonical-sister scans before proposing rename infrastructure MUST include the **`DOCS/TOOLS.md` inventory**, not just `DESIGN_SPECS/` — A.5's draft missed the existing `.D.1` doc-rename executor until the gate's /dod-audit found it (synthesis S-7).

## When NOT to apply

Single-file local renames (IDE-refactor scale); renames of identifiers with zero doc/tool footprint (just do them inside the owning ship); anything touching H21 surfaces (not a rename — an epoch).

## Lifecycle

Stage 1: recurring rename failures (B19/TECH_DEBT-142, Class 36, `.D.1` doc sweep) · Stage 2: THIS DOC (A.5 Step 0) · Stage 3: A.5 close (first canonical complete) · Stage 4: `.E.1` second application (prose-ambiguous class exercises the discriminator; TECH_DEBT-142 closes there) · Stage 5+: if rename ships keep recurring post-`.E.1`.
