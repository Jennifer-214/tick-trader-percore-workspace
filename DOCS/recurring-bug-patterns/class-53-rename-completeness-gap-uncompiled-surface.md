# Class 53 — Rename-completeness gap on the compiler-invisible surface (the un-compiled referencing side goes stale)

> Codified 2026-06-24 at v5.15.5.F.4d.1.E.1.1 (the ② Core→Node rename, commit `1da1c1c` — the World-2 surface the compiler-oracle cannot see). Per-class file per file-size-split-discipline. Sibling instance of the `rename-ship-methodology.md` World-1/World-2 lesson. **H-promotion deferred to Stage 5** per pattern-codification-lifecycle.

## Shape

An architecture-wide rename updates the **COMPILED side** — code tokens + the parser — and the **compiler red-build is its completeness oracle** (a half-renamed tree won't compile; per `rename-ship-methodology.md` Phase 4, the compiler is "World-1"). But the rename **leaves the UN-compiled REFERENCING side stale:**

- **cfg DATA files** (`engine_sharded.cfg` and friends) — the parser flips to the new key prefix, but the active data file still carries the OLD keys;
- **operator-facing STRING literals** — REFUSE fix-hints, log/JSONL keys, GUI labels, deploy hints, README prose;
- **copyable DOC examples** — commented-out cfg snippets an operator pastes.

This **silently breaks the parser↔data CONTRACT** with **NO oracle for the non-code surface** ("World-2"): the rename's code-token cascade had a perfect oracle for TOKENS (the compiler) and NONE for DATA/STRINGS. The symptom is a **silent RUNTIME break with zero CI signal** — the build is green, the suite is green, and the engine runs the WRONG behavior because the data keys no longer match what the parser accepts.

It is the **World-2 half** of any rename ship: the methodology's compiler-oracle (Phase 4) closes World-1 completeness for free, which is exactly why the World-2 surface is easy to forget — there is no red build to remind you.

## Detection heuristic

After any architecture-wide rename, flag the surfaces the compiler **cannot** see:
- (a) **active cfg DATA files** still carrying the OLD key prefix while the parser now accepts only the NEW one (the parser↔data drift — a runtime break, not a build break);
- (b) **operator-facing string literals** (printf/fprintf/log/REFUSE/fix-hint/GUI-label) naming the old term — especially REFUSE fix-hints that instruct the operator to set a key the parser no longer accepts (an **unresolvable live-boot loop**);
- (c) **persisted/emitted keys** (a HealthLog JSONL field) named the old term;
- (d) **copyable doc examples** (commented `core_N_*` cfg lines) an operator would paste verbatim.

Discriminator: *does a green build PROVE this reference was updated?* If the reference lives in DATA, a STRING, or a DOC, the answer is no — and it needs a non-compiler guard.

## Structural fix — a non-code-surface oracle (because the compiler has none)

The rename's code-token cascade has a perfect oracle; the non-code surface has none — so **build one:**

- **A cfg-key ∩ parser-recognized-prefix DRIFT GUARD** — the NEW `tools/check_cfg_key_prefix_drift.py`: scans cfg files + operator-facing source string literals against the parser's accepted prefix + a retired-key/prefix ledger + the DESIGN_PHILOSOPHY § 15 PRESERVE allowlist. **Selftest-proven non-vacuous** (per Class 51 — a drift guard that never exercises its target is worse than none); it found 1 site the agent eyeball missed.
- **Extend the canonical-sister `check_doc_rename_classification.py` to source STRING LITERALS** — the doc-rename executor already sweeps `.md`; teach it the operator-facing string surface so the same token-map executor covers it.
- **AMEND `rename-ship-methodology.md` with the non-code-surface-oracle requirement** — every rename ENUMERATES + GUARDS its data / string / example surfaces, which have NO compiler oracle. (This is the World-2 lesson the methodology already records at Phase 2 — `feedback_rename_enumerator_is_world2_aid_compiler_is_world1` — plus the DOC-DATA-FILE bucket at Phase 3; Class 53 is the anti-pattern instance that earns those a teeth'd guard rather than a prose reminder.)

The fix spirit: **the rename's completeness claim is only as strong as its WEAKEST oracle** — and on the data/string/doc surface the compiler abstains, so a mechanical guard tying the two sides of the cfg contract is mandatory.

## Canonical instance (the ② Core→Node rename, `1da1c1c`)

The mechanical Core→Node rename (names-only, frozen logic) flipped the cfg parser to `node_`-only (`ControllerConfig.hpp:2919`, `strncmp(key,"node_",5)`) but left, at the `1da1c1c` snapshot:

- **active cfg keys** — `engine_sharded.cfg`'s `core_0/1/2/3_strategy` keys remained while the parser accepted only `node_*` → nodes silently ran the **SIMPLE_DIP default** (`ControllerConfig.hpp:1925`, `node_strategies[i]=2`) instead of `momentum` / `ema_cross` — a **LIVE regression** (the parser saw an unrecognized `core_*` key, fell through to the default strategy);
- **dozens of operator-facing `core` / `Core` / `PER-CORE` strings** (~60–85, point-in-time) — LiveReadiness REFUSE fix-hints (→ an **unresolvable live-boot loop**: the hint told the operator to set a `core_*` key the parser had retired) + GUI labels + deploy hints + README + diagnostic log strings (`ModelValidation.hpp:161`, `EngineCommon.hpp:288`, `NodeModelZoo.hpp:839`);
- **~140–180 commented copyable examples** (point-in-time) — commented `core_N_*` cfg snippets (`engine.cfg.example`) an operator would paste — none caught by ANY CI.

The build was green throughout (names-only, logic frozen) — which is precisely why none of the above surfaced at compile time. The cfg-data + parser-contract breach is now REPAIRED: the ③ config-compiler makes the parser **HARD-REFUSE** the retired `core_` prefix (`ControllerConfig.hpp:3143` — `FATAL: '...' uses the RETIRED 'core_' key prefix ... Boot REFUSED`) so a stale key now refuses instead of silently defaulting (the Class 52 refuse-don't-coerce link), and `engine_sharded.cfg` was migrated to `node_*` (`:287-290`). The residual string/example cleanup is what the drift guard now nets.

## False-positive surface (per M3)

NOT this anti-pattern when:

- **PRESERVE-AS-HISTORY.** Changelogs / decision-logs / postmortems / `Version.hpp` use the old term ACCURATELY for their time (glossary § 15 terminology-evolution-bridge, `DOCS/DESIGN_PHILOSOPHY.md:1004-1019`). Rewriting them FALSIFIES the evolution record — the rename ship's own narrative ("we renamed Core→Node") needs the historical record to show the OLD term. Leaving old terminology there is CORRECTNESS, not a gap.
- **H21-PRESERVED wire/persistence keys — never renamed.** The HealthLog JSONL `"core"` key (`MemHeaders/HealthLog.hpp:267` — the variable is `node_id` but the emitted JSON key stays `"core"`) is a wire-format identifier under H21 (append-only + immutable; a renamed persisted key = the Knight-Capital failure mode). It reads "stale" but is INTENTIONALLY preserved — the drift guard must allowlist H21 surfaces (this is exactly the methodology Phase 6 "renames NEVER touch persistence/wire-visible identifiers — if it WOULD, it's an epoch change, not a rename").
- **LEGIT-CPU-CORE — never a rename target.** `ExecutionCore` (RATIFIED PRESERVE at the `.E.1.1` design, `ExecutionCore.hpp:62`; renaming it would also break the conformance gate's `ExecutionCore_Tick` kernel manifest) / `cpu_id` (`Run.hpp:184`, a NODE owns 2 CPUs; `node_id ≠ cpu_id`) / `CoreFrameworks/` / "physical core" / `MULTICORE` / ImGui `##`-id suffixes are genuine CPU-core usages (the PROSE-AMBIGUOUS class per the methodology's Phase 1 — "core" = CPU-core vs trading-node). Flagging these is the false-RED; the drift guard must allowlist them.
- **A true LEAF rename with no data/string/doc consumers** needs no non-code guard — the methodology's "when NOT to apply" (zero doc/tool footprint → just do it inside the owning ship).

The discriminator: the flag fires only where a rename leaves a STALE reference on the compiler-blind surface that BREAKS a runtime contract — never on a faithfully-preserved historical record, and never on a legitimate same-spelled-but-different-concept usage.

## recurrence_count

**1** — the ② Core→Node instance. Sibling to Class 36's rename-tool-span/link corruption at the APPLY layer (Class 36 = the tool corrupts what it rewrites; Class 53 = the rewrite never reaches the un-compiled surface).

## Distinct from / sibling of

- **Class 36 (overlapping-span substitution corruption)** — the COMPILED-side-tool sibling: Class 36 is the bulk-rewrite TOOL corrupting spans/links it DOES touch; Class 53 is the surface the rewrite NEVER touches because the compiler doesn't force it. Two halves of "the rename's mechanics are incomplete."
- **H22 (the cfg-integrity-guard / per-node-purity family)** — sibling-but-distinct-invariant: `check_cfg_key_prefix_drift.py` is a mechanical guard tying two sides of a per-node cfg CONTRACT, the same family as the H22 `check_per_core_registry_integrity.py` guards — but the invariant is rename-completeness of the cfg-key surface, not per-node read-purity.
- **Class 52 (swallow-and-coerce capital/config parse)** — the swallow-and-coerce sibling: both are silent-mishandling-of-bad-config (Class 52 at parse, Class 53 at the parser↔data contract). **Refuse-don't-coerce is the shared fix spirit** — a stale `core_*` key SHOULD refuse (unrecognized → fault), not silently fall through to the default.
- **The terminology-evolution-bridge discipline** (glossary § 15 / `feedback_terminology_evolution_bridge_not_history_rewrite`) — the doc-population treatment side: FORWARD docs sweep, HISTORICAL docs preserve+bridge. Class 53 is the CODE-DATA-STRING counterpart that the bridge discipline doesn't cover (it governs narrative docs; Class 53 governs the runtime contract).

## Closure mechanism

- **`tools/check_cfg_key_prefix_drift.py`** (NEW) — the cfg-key ∩ parser-prefix drift guard; selftest-proven non-vacuous (Class 51); the standing net for "a future rename left the data/string surface stale."
- **`check_doc_rename_classification.py` extended to source string literals** — the canonical-sister executor covering the operator-facing string surface.
- **`rename-ship-methodology.md` AMENDED** — the non-code-surface-oracle requirement (enumerate + guard data/string/example surfaces; the compiler is World-1 only); composes with the existing World-1/World-2 + DOC-DATA-FILE buckets.
