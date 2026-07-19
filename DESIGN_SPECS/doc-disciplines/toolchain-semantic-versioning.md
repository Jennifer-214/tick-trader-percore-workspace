---
type: doc-discipline
stage: 2-draft
version: 1.0
established: 2026-07-19
tags: [doc-discipline, dev-plane, versioning, ssot]
surface: [ci-tooling, doc-pipeline]
sister_specs: []
applies_at_skills: []
---

# Toolchain semantic versioning (dev-plane product versioning — SSoT)

**Established:** 2026-07-19 (decision-log **D-373**, E.1.2.B planning). **Stage: 2-DRAFT** — first canonical reference lands at E.1.2.B `0.1` (`TOOLCHAIN_VERSION` stamped).

## Problem

The in-code documentation toolchain (`foxtag` C++ core + the `check_*` family + the `fox-symdeps.nvim` plugin) is a dev-plane **product with N consumers**, but it has no coherent version — only the LOCKED `[SCHEMA]_[v1.0]` *format* version, which is a different axis (the grammar contract, not the tooling). "Which version of the toolchain am I on" has no answer; a consumer can't declare compatibility.

## The scheme

**Standard 3-part semver `MAJOR.MINOR.PATCH`** for the toolchain-as-a-product:

- **MAJOR — tied to the `[SCHEMA]` contract.** A `[SCHEMA]_[vN]` grammar bump is the one change that ripples to *every* consumer (plugin + CI + CLI must re-coordinate) — the definition of a breaking major. So **schema `v1.0` ↔ toolchain `1.x`; schema `v2` ↔ `2.x`.** Additive vocab rows are backward-compatible (old blocks still parse — the "1-line extensible vocab" design) and do NOT bump the schema → they are MINORs.
- **MINOR** — a new surface / producer / capability, backward-compatible (a new `foxtag` command, a new plugin surface, a new `check_*`).
- **PATCH** — a bug fix.
- **Pre-release** — the semver `-suffix` channel (`1.0.0-rc1` = "feature-complete, soaking"). Optional; not a required 4th component.

**`0.x` until the first cohesive release → `1.0.0`.** The same 0-until-milestone the engine's `RELEASE_VERSION 0.3` uses (pre-1.0 until the milestone lands). V1's `1.0.0` = "every capability live on the surface that fits it, all consuming one core" (north-star §8.6).

**One version SSoT — `tools/TOOLCHAIN_VERSION`.** A dev-plane analog of the engine's `Version.hpp`: one file, every surface reads + reports it (`foxtag --version` · plugin `:checkhealth` · the CI banner). This is the *one-core-N-consumers* thesis applied to the version itself — a single number, not per-component drift.

## Why not (rejected alternatives)

- **The engine's deep `.F.4d.1.E…` cadence** — that granularity exists *only* because `ENGINE_VERSION` is wire-bound (embedded in stamps/fingerprints/HMAC per H9) and must track every determinism-affecting sprint phase. The toolchain is never wire-bound → plain 3-part semver is cleaner.
- **Independent per-component versions** (plugin vs foxtag vs checkers) — drifts; violates the one-core cohesion the whole system rests on.

## Boundary / caveats

- The `[SCHEMA]_[vN]` format version and the `TOOLCHAIN_VERSION` product version are **distinct axes** that happen to couple at MAJOR — the tooling iterates freely (MINOR/PATCH) while the schema stays `v1.0`.
- The plugin lives in a separate git repo; the SSoT is either a shared `TOOLCHAIN_VERSION` the plugin reads, or the plugin tags aligned versions. (Settle at `0.1`.)

## Cross-references

- Decision log: **D-373** (this scheme) · D-337 (one-producer-N-consumers) · D-372 (V1 redefinition) · D-346 (`[SCHEMA]_[v1.0]` LOCKED).
- Sister (prose): engine `Version.hpp` (the SSoT-version pattern this mirrors) · `in-code-doc-system-north-star.md` §8.6 (the V1 = whole-toolchain definition) · `doc-intelligence-toolchain-architecture.md` (the one-core thesis).
- Applied at: E.1.2.B `0.1` (first `TOOLCHAIN_VERSION` stamp).

**End — Stage 2 DRAFT.** Reciprocal `sister_specs` links + index enrollment land at first-canonical (E.1.2.B `0.1`).
