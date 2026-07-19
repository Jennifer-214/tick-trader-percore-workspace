---
type: framework-pattern
stage: 2-draft
version: 1.0
established: 2026-07-19
tags: [framework-pattern, dev-plane, ssot, doc-pipeline, ai-plane]
surface: [ci-tooling, doc-pipeline]
sister_specs: []
applies_at_skills: []
---

# Standardized tool-I/O — the envelope + the uniform payload (the machine serialization of the tag system)

**Established:** 2026-07-19 (decision-log **D-376** envelope+payload, **D-377** `.toolbus/`; E.1.2.B `0.1.5`). **Stage: 2-DRAFT** — the envelope shape is locked as the direction; the exact payload typing is validated at the `0.1.5` dive against all enumerated payloads. First canonical: `foxtag grammar --json`.

## Problem

The toolchain's producers (foxtag `units`/`layout`/`codegen`/`fields`; `check_register_fit`; …) and gates (`check_*` validators) each emit a bespoke shape — so a consumer needs N readers, tools can't be chained, and the plugin/AI can't consume outputs uniformly. The "felt like none of it matters" gap (D-372) is partly *this*: the facts exist but nothing composes them. The fix is ONE format every tool speaks, so a single read/write mechanism serves all — and multi-step composition + native CLI/plugin/AI use fall out for free.

## Two layers

### 1. The ENVELOPE (outer, uniform)

```json
{
  "envelope_version": "1.0",
  "kind": "grammar",
  "schema_version": "v1.0",
  "producer": { "tool": "foxtag", "version": "0.1.0", "command": "grammar", "args": ["--json"] },
  "status":   { "ok": true, "code": 0, "findings": [] },
  "target":   { "paths": [], "git_head": "4c076ed" },
  "payload":  { }
}
```

- **`status.findings` UNIFIES producers + gates.** A gate is just `kind:"verdict"` with its findings (`{file,line,severity,message,kind}`) in `status` and an empty payload. So the plugin's gate-verdicts-as-`vim.diagnostic` and the AI acting on structured findings read the SAME shape as any producer output. One shape, every tool — this is what makes multi-step composition real.
- **`schema_version`** = the D-373 `[SCHEMA]` compat gate (a chained tool refuses an incompatible payload). **`target.git_head`** = staleness detection (is this fact current for HEAD?). **`producer`** = provenance for chaining / caching / debug. **`envelope_version`** = the format's own version (additive — add fields without breaking v1 readers).

### 2. The PAYLOAD (inner, uniform — the deeper standardization)

The payload is **one or more NAMED RECORD-SETS.** Each record-set declares a field *schema* (name + type, drawn from the tag vocab where it applies) + *rows*; a field value may nest another record-set.

- `grammar` → tables `{categories, unit_types, derived_axes, ladder, …}`
- `units` → a `units` table (rows = unit records) · `layout` → a `fields` table · `verdict` → a `findings` table

**One writer emits `{schema, rows}`; one reader walks `{schema, rows}` — for ANY tool.** That is "the same read/write mechanism, general enough for all tools."

**This IS the tag system's machine serialization.** The vocab doc (`doc-tag-vocabulary.md`) is the field dictionary; the in-code `//[CATEGORY]_[value]` tags and these JSON record-sets are two serializations of the ONE vocabulary. Adopting the I/O format EXTENDS the tag system to tool-I/O — they are one system ("the code side of the vocab doc, alongside the tag system"). A record-set can *be* a vocab set (the `categories` table's rows ARE the vocab categories).

## `.toolbus/` — the rendezvous (D-377)

A gitignored, latest-wins directory where a tool drops its latest envelope (`grammar.json`, `layout--ExecutionCore.json`). **Cache, not IPC:** latest-wins · gitignored · regenerable (no history, no GC); staleness is free (`target.git_head`). Read by the plugin (vocab without a subprocess per keystroke), the AI (one canonical location), and multi-step chains. The dev-plane twin of the decoupling endgame's published-state dir. Run-scoping/history deferred until a concrete consumer needs it.

## Adoption (behind parity, ALONGSIDE the tag system)

1. `foxtag grammar --json` — the **1st canonical envelope** (unblocks the plugin: derive `UNIT` set + axes from the payload, killing the hardcoded Lua mirror).
2. Stand up `.toolbus/`; the plugin + AI read from it.
3. Other foxtag commands (`units`/`layout`/`fields`/`codegen`) + the `check_*` producers adopt the envelope **behind `parity_check`** (D-349 — PASS ≠ cutover; per-consumer, gated).
4. `foxtag_client.py` grows function-call helpers (`grammar()`, `units()`, …) returning parsed payloads; pybind11 slots behind the same API later.

## Payload kinds + integrity (D-378)

- **The `kind` set is a registered VOCABULARY** (SSoT'd like the tag categories) — adding a payload kind is 1 row, every consumer tracks it; never hardcoded per tool.
- **Graph-shaped facts are kinds too.** A call-graph / dependency-DAG / trace / reference-graph / blast-radius is a payload whose record-set is EDGES (`{from, to, edge_kind}`) — no special graph infrastructure (a graph is rows of edges under the uniform model). These already EXIST scattered — the plugin's clangd call-hierarchy · `CODE_MAP` · `gen_code_map` · foxtag's `RefIndex` — but are not yet unified foxtag payload kinds; the `0.1.5` enumeration catalogs them. Starter kind set: `grammar · units · layout · fields · codegen · verdict · callgraph · depgraph · refgraph · blast_radius · instantiation`.
- **One write path, one read path.** A shared envelope-EMIT helper in `foxtag` + `foxtag_client` (the write-side SSoT, sibling to `foxroots`) + the uniform record-set READER. "Same read/write mechanism" is literally ONE code path each, not N hand-rolled emitters.
- **Integrity = caching, NOT crypto.** An OPTIONAL `content_hash` (SHA-256) in the envelope for cache / dedup / staleness (a consumer or multi-step chain checks "did this change?" without diffing). **NOT HMAC:** HMAC authenticates capital-bearing WIRE data against tampering — the ENGINE's H9 (stamps/snapshots; a real adversary + cross-binary determinism). The `.toolbus/` is local, gitignored, regenerable, no wire, no capital → nothing to authenticate; HMAC there solves a problem the dev-plane doesn't have. Content-hash yes; HMAC + a bespoke binary parser no — the payload is JSON, the record-set reader IS the parser.

- **Per-item versioning (D-379).** Each first-class artifact carries its OWN version, evolving independently — THREE envelope axes: `envelope_version` (the envelope format) · `schema_version` (the tag grammar the vocab speaks) · a per-`kind` payload-schema version (each record-set kind, carried in its self-describing schema). Plus `TOOLCHAIN_VERSION` (the product) + each DESIGN_SPEC's `version:`. A consumer checks only the axis it depends on; a kind evolves without perturbing others. The toolchain artifacts are first-class alongside engine code → engine-grade per-item tracking (removes solo-engineer decision-fatigue; externalized cognition).

## Typing lock (D-380) — the shapes, decided at the `0.1.5` informing pass

After the enumerate-first grounding, the substrate shape is LOCKED (decision **D-380**):

1. **Serialization = single-doc plain JSON.** NOT NDJSON (a streaming style; `.toolbus/` is a small latest-wins file read whole → one wrapped doc holds the envelope metadata NDJSON has nowhere to put). NOT YAML (a C++/Lua dependency the JSON path avoids; non-deterministic to emit byte-identically → breaks content-hash/staleness; a machine-ONLY bus has no use for YAML's human-authoring win — the human surfaces [frontmatter · the `[TAG]` grammar] keep their own formats).
2. **Payload = uniform record-set TABLE.** `{schema, rows}` — the schema IS the fixed field-layout (a record-set = an X-macro registry / `FOREACH_CFG_FIELD` serialized; the `SHIFT_*`/`MASK_*` "each slot a defined purpose" discipline, for records). Name is a COLUMN, not a map-key; rows sorted for determinism. `layout`/`fields`' map→rows reshape lands at each producer's GATED cutover (D-349), leaving their parity-proven shapes untouched until then.
3. **Schema-as-DATA registry (the mechanism for D-379's per-kind versioning).** ONE emit helper READS each kind's schema+version from a **language-neutral registry** — a data file BOTH the C++ core AND the Python tools read, NEVER a per-language hardcode (a C++-hardcoded schema + a Python copy would BE the Class-18 mirror the system exists to kill). The toolchain's "grammar-DERIVED, never hardcoded" law, raised one level to the payload + CI-gate schemas. Add/evolve a kind = a registry row; every producer + consumer tracks it. Start minimal (`grammar/1` + `verdict/1` so the gates have a target), grow per kind — generalizes beyond tool-I/O to the CI gates + tag/vocab rules (same definition-as-data discipline).
4. **Comments-only-never-code.** Tooling writes comments / `[DERIVED]` fact-blocks / index-docs ONLY — NEVER engine logic. `codegen` is read-only + LIVE-only (never persisted — flips with `-O`/`-march`). Auto-generated engine code is a Knight-adjacent trust hole on a capital path → structurally excluded.

## Discipline / open

- **Payload typing LOCKED (D-380)** — single-doc JSON · uniform record-set table · schema-as-DATA registry · comments-only-never-code (§ "Typing lock (D-380)" above), locked at the `0.1.5` informing pass AFTER enumerating all payloads first, never guessed (`feedback_dont_generalize_substrate_before_input_space_known`). The concrete `foxtag grammar --json` envelope + the registry land at the `0.1.5` build (sidecar `subplans/2026-07-19-E.1.2.B-sidecar-0.1.5-tool-io-substrate.md`); an armed I→A cascade gates it.
- **Generalize on cohort** — this spec promotes to first-canonical when `grammar --json` lands; to a cohort stage when the 2nd tool speaks the envelope. Don't build a universal protocol ahead of the consumers.

## Cross-references

- Decision log: **D-376** (envelope + payload) · **D-377** (`.toolbus/`) · D-337/D-349 (one-core / migration) · D-373 (`schema_version`) · D-372/D-375 (V1 / AI-plane).
- Sister (prose): `in-code-documentation-schema.md` (the in-code tag serialization — the sibling of this machine serialization) · `doc-intelligence-toolchain-architecture.md` (the one-core thesis) · `toolchain-semantic-versioning.md` (`schema_version` / `producer.version`) · `TECH_DEBT-176` (tool-composition / unified runner, the consumer of this substrate) · the decoupling endgame's `headless-engine-viewer-split-pattern` (the engine sibling of `.toolbus/`).
- Applied at: E.1.2.B `0.1.5`.

**End — Stage 2 DRAFT.** Reciprocal `sister_specs` links + index enrollment land at first-canonical (`0.1.5`).
