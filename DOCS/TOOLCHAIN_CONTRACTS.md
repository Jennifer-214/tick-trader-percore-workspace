# TOOLCHAIN CONTRACTS — the language-neutral fact-family layer ((a) of E.1.2.B `0.2`; D-418)

**Why this exists (D-415):** the C++ conversion is deferred to v1, and what accrues meanwhile is
CONTRACTS — the fact shapes and guarantees every producer must honor, stated without reference
to the implementing language, so the v1 core converts against a locked seam instead of reading
Python. Machine-readable halves live in `tools/lib/toolio_schemas.json` (envelope: `grammar/1`,
`findings/1`) and the goldens under `tools/goldens/`; this doc is the prose half: per fact
family — CONSUMES / EMITS / GUARANTEES / FAILURE MODES. Seeded from `tools/CLAUDE.md`
§ "Tool invariants + gotchas" + the D-413/D-414 arc's landed semantics.

**The two cross-cutting laws** (every family inherits them):
- **Tri-state honesty (Class 57):** a producer distinguishes *verified-none* / *unverifiable* /
  *failed-to-run* — a failure is a REFUSAL, never empty-facts; a partial state is NAMED, never
  flattened to a clean default at any seam.
- **Write-vs-verify separation (D-374):** gates VERIFY and red; writers write only when a human
  explicitly invokes them; nothing auto-rewrites under the operator.

---

## 1 · STRUCT-LAYOUT facts (`[SIZE]` / `[ALIGN]` / `[CACHE_LINES]` / `[STRADDLE]`)

- **CONSUMES:** compiler record-layout dumps of the shipped ABI (Itanium; layout-portable flag
  subset — D-321) over the converted `[STRUCT]` corpus (per-header isolate probes cover
  under-instantiated structs, D-363).
- **EMITS:** per record `{size, align, straddlers:[{name, off, size}], partial?:[field…]}`.
- **GUARANTEES:** sizes/offsets are ABI-fixed (never optimization-dependent). A *straddler* is a
  sub-64-byte field crossing a 64-byte boundary (≥64-byte fields span inherently and are
  excluded BY INTENT). An unresolved field is delta-BOUNDED by its neighbor's offset: a bound
  inside one line = PROVEN clean; a crossing bound = listed in `partial` BY NAME. A record with
  a non-empty `partial` may NEVER be written as a definitive `none`. A record ABSENT from the
  dump is UNPOLICED (counted and named), never verified. A DUMPED record is complete-by-
  construction (the compiler only prints finished layouts); compiler rc≠0 is tolerated dialect
  noise — missing records are the only casualty and they surface as unpoliced.
- **FAILURE MODES:** run failure ⇒ refusal (no facts), with fallback producers allowed only when
  they honor this same contract. Written-fact refresh is stamp-on-change and idempotent
  (Class 56): a second run is a 0-diff.
- **Gate semantics:** cross-thread arming comes ONLY from the block-level orient-tier `[THREAD]`
  declaration — ANY ≥2-role orient line arms, ORDER-INSENSITIVE (OR-fold; a single-role line can
  neither arm nor disarm, and tag-line order is never load-bearing — AR-8 hole 7).
  `[STRADDLE_EXEMPT]_[field]_[reason]` is orient-tier-only (same tier discipline) and silences the
  VERDICT per field — the FACT still gets written; an exemption matching no current
  straddler/unverified field is reported DORMANT (typo'd-with-baselined-real-finding is the silent
  rot this catches). Enforcement is strict-new over a SHRINK-ONLY grandfather baseline
  (`tools/lib/cache_layout_baseline.txt`) — shrink-only is ENFORCED: re-bless refuses growth
  (rc 2, keys named), and orphan keys (fixed-but-still-grandfathered) are reported per run,
  TU-scope-honestly (a struct unpoliced in this run's TU is UNKNOWN here, never "fixed").
- **v1 contract item (field-existence validation):** the emitter does not yet carry the record's
  FULL field list, so an exemption naming a never-existed field is only caught via the dormant
  report. The v1 layout producer EMITS the full field-name set per record; the gate then
  validates every `[STRADDLE_EXEMPT]` name against it (typo → RED, not advisory).

## 2 · CITED-PATH resolution (the D-417 resolver)

- **CONSUMES:** a cited relpath + project/workspace roots; the VCS's own rename records
  (chain-resolved old→…→current, kept only where the target exists at HEAD) + a
  unique-basename move probe.
- **EMITS:** exactly one of `("RESOLVED", path)` · `("RENAMED", current_relpath)` — the
  auto-repair payload · `("MISSING", none)`.
- **GUARANTEES:** never guesses — ambiguity stays MISSING (the H21-adjacent caution). No
  hand-maintained rename table (both derivation layers are DERIVED from ground truth).
- **FAILURE MODES:** a non-VCS root contributes no map (silently degrades to direct+basename
  resolution — resolution weakens, never fabricates).
- **Consumer semantics:** frozen records (`frozen_record_paths` SSoT) are truthful artifacts —
  their stale cites are never repaired; append-only docs (decision logs) are ANNOTATED
  (`[NOW:]`), never rewritten; `[CITE-AS-EVIDENCE]` cites are quoted staleness — untouchable.

## 3 · CALL-GRAPH facts (written `[UPSTREAM]` / `[CONSUMERS]`)

- **CONSUMES (write side):** the editor's semantic index at write time, or verified curation —
  every written symbol must be real at write time.
- **EMITS:** orient/DERIVED-tier symbol lists; `[ORIGIN]` must state the TRUE provenance
  (machine vs curated — stamping AUTO over hand-written lines is a provenance lie).
- **GUARANTEES (verify side, the A2 gate — DECLARED PARTIAL, M10):** every written symbol
  EXISTS as a code token; every consumer co-occurs with its unit in ≥1 file's code. The gate
  prints its own non-coverage every run: MISSING consumers are invisible until the v1
  generator lands. Template placeholders MUST be non-symbol-shaped (`<angle-form>`) — a
  symbol-shaped placeholder leaked into real source once and survived 5 weeks.
- **FAILURE MODES:** phantom (never-existed symbol) and stale-reference both RED the gate.

## 4 · CITABLE-ID corpus (`D-…` / `Class …` / `TECH_DEBT-…` / …)

- **CONSUMES:** the defining-form registry (`tools/lib/citable_id_namespaces.json`) over the
  doc corpus.
- **EMITS:** the by-DEFINING-FORM id index; the blessed golden (`tools/goldens/citable-ids.txt`).
- **GUARANTEES:** membership by definition, never by mention (a by-mention set cannot go red —
  Class 51); ids are append-only identities (H21): retire by tombstone, never reuse; removals
  from the golden require an explicit TTY bless showing the diff (D-394/D-410).
- **FAILURE MODES:** cited-but-undefined / defined-twice-divergent / gap-without-tombstone
  all RED.

## 5 · THE UPDATE ORCHESTRATOR (`update_toolchain.py`; D-374/D-418)

- **CONSUMES:** ground truth only (the compiler, the VCS, the SSoT registries).
- **EMITS:** regenerated WRITTEN derived state, in dependency order: layout `--fix` →
  (call-graph: declared-skip until v1) → cite auto-repair (family 2's consumer semantics) →
  indexes → the VERIFY sweep.
- **GUARANTEES:** WRITTEN-only (never the volatile LIVE-PREVIEW facts — instr/SIMD/branches,
  D-327); idempotent end-to-end (second run = 0-diff); verify-after is part of the run;
  explicitly-invoked ONLY — wiring it into any hook is a contract violation (flag-not-auto).
- **FAILURE MODES:** a failed stage reports and the verify sweep gates; the operator reviews
  the git diff before committing — the diff IS the review surface.

## 6 · ENVELOPE (the machine-readable half)

`tools/toolio.py` + `tools/lib/toolio_schemas.json`: every structured producer emits the
standardized envelope (payload + `git_head`/`producer.version`/`status` frame); goldens
normalize the volatile frame out before comparison. Schema names are versioned (`grammar/1`);
a shape change is a NEW version, never a mutation (H21-adjacent).

---

*Contract changes land HERE first, then in implementations — this doc is the v1 conversion's
acceptance seam (each family's teeth are its oracle). Owner thread: E.1.2.B `0.2` (a)/(d);
established 2026-08-10 (D-418).*
