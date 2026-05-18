# Wire-format byte-preservation discipline (HMAC chain protection)

**Established:** 2026-05-09 (v5.14.8 sprint)
**Status:** ACTIVE
**Cross-references:**
- Companion: `x-macro-registry-with-presence-dispatch.md` (registry as source of truth for canonical wire format)
- Sister: `implementation-layer-blindspot-taxonomy.md` (meta-discipline M4; this discipline's Layer 7 cross-tool emit-site enumeration IS the M2 codification — the implementation-detail blind-spot taxonomy is the meta-discipline registry where M2 lives)
- First systematic application: FOREACH_STAMP_BOUND_MODEL_CONST migration in v5.14.8.A.merged
- Pattern precedent: `feature_registry_hash` (v5.8.6); `model_format_version` (v5.9.0)
- Closes: GATE-NEW-2 in v5.14.8 audit gates

---

## Problem statement

When a struct is serialized to a stable wire format (file on disk, network protocol, signed body for HMAC verification), the BYTE-FOR-BYTE shape is part of the contract. Any change that affects:

- Field order in serialization
- Format strings (`%g` vs `%.6g` vs `%.17g`)
- String quoting / escaping
- Locale-dependent number formatting
- Whitespace / line endings
- Optional field presence semantics

...breaks the contract. For HMAC-signed bodies, the signature won't verify against legacy stamps. For replay-determinism tests, output bytes diverge.

When migrating manual emit/parse code to registry-driven X-macro generation, every refactor risks introducing one of these silent wire-format changes. The registry MUST produce byte-identical output to the manual code being replaced; otherwise legacy artifacts (signed stamps, persisted snapshots, recorded JSONL) become unreadable.

This pattern provides discipline for refactors that maintain wire-format byte-preservation across rewrites.

---

## Threat model

### Surfaces susceptible to wire-format drift

1. **HMAC-signed bodies** — stamp body, snapshot manifest, RunHistory entries. Signature won't verify if any byte changes.
2. **Versioned formats** — `MODEL_FORMAT_VERSION`, `SHARDED_SNAPSHOT_VERSION`. Old + new readers diverge silently if format shape changes without version bump.
3. **Replay-determinism tests** — same input bytes → same output bytes. Deterministic CSVs, deterministic JSONL.
4. **Cross-process boundaries** — file written by tool A, read by tool B (e.g., bash CLI emits, C++ verifier reads).

### Common drift causes (each is a real bug class we've hit)

1. **Field order changed** — registry rows reordered; emit produces fields in new order; HMAC differs.
2. **Format string drift** — manual emit used `%g`; registry uses `%.17g`; numbers serialize with different precision.
3. **Locale dependency** — `%g` honors `LC_NUMERIC`. A stamp signed under `LC_NUMERIC=C` won't verify under `de_DE` (where 0.55 → "0,55").
4. **Optional field semantics** — group-or-nothing emit (5 fields together) vs per-line gating (only 3 fields if 2 has_* are 0). Same data, different bytes.
5. **Whitespace** — extra/missing newline at file end; tabs vs spaces; trailing spaces.
6. **Buffer size change** — fixed-size buffer that overflows or pads differently.

---

## Design space explored

### Option A: Trust manual review

Each refactor is reviewed for byte-preservation. Reviewer checks emit code line-by-line.

**Rejected.** Discipline-based; misses drift in non-obvious places (locale, precision, optional semantics). Reviewer drift; new contributors miss the discipline.

### Option B: Diff-based regression testing

Generate canonical body from synthetic-populated struct via OLD code; save as test fixture. Refactor; regenerate via NEW code; diff. Drift breaks the test.

**Acceptable.** Catches MOST drift but requires fixture maintenance + the drift is detected POST-coding, not pre-coding.

### Option C (chosen): Multi-layered defense

1. **Pre-coding gate** — `/parity-check` Section E verifies registry order matches emit order.
2. **Coding-time invariants** — registry tuple's `fmt` column locks per-entry format string; locale pinning at canonical body construction.
3. **Post-coding tests** — round-trip HMAC test (parse pre-migration stamp; re-emit; verify HMAC unchanged). Snapshot test on canonical body output.
4. **Operational checkpoints** — version bump on intentional format changes; legacy parser tolerates absent fields (Surface G discipline).

Defense in depth catches drift at multiple stages.

---

## The pattern (concrete shape)

### Layer 1: Pre-coding gate via /parity-check Section E

The audit walks:
- Registry entry order (FOREACH_<REGISTRY>) vs current emit code order (line-by-line)
- Per-entry format strings vs registry's `fmt` column
- Optional-field semantics (group has_* gating vs per-entry has_* gating)
- Locale pinning at emit construction (`uselocale(newlocale(LC_NUMERIC_MASK, "C", 0))`)

If any DIVERGES, the gate fails the ship. Re-converge BEFORE coding starts.

### Layer 2: Locale pinning at emit construction

```cpp
// FROM ModelInference.hpp stamp_write_for_model:
locale_t pinned = newlocale(LC_NUMERIC_MASK, "C", (locale_t)0);
locale_t prev = (locale_t)0;
if (pinned) prev = uselocale(pinned);
// ... build canonical body via snprintf ("%g", "%.6g", "%.17g", ...) ...
if (pinned) {
    uselocale(prev);
    freelocale(pinned);
}
```

`uselocale` is per-thread (thread-safe; doesn't affect rest of process). Pin to LC_NUMERIC=C for canonical body construction. Restore before return.

### Layer 3: Registry tuple's `fmt` column — single source of truth for emit AND parse

```cpp
X(name, group, presence, type, fmt, default_val, get_value, emit_when, doc)
//                              ^^^
//                   Per-entry printf format string locked here.
//                   Registry-driven emit ALWAYS uses this format.
```

Adding a new entry requires explicit `fmt` choice. Reviewer/audit can grep for `"%g"` vs `"%.6g"` vs `"%.17g"` discrepancies.

**DRY extension — fmt also drives parser base detection (v5.15.0.B):** for unsigned integer fields, the parser auto-detects strtoull base from the `fmt` column rather than maintaining a parallel `parser_base` column or per-site manual branches. Hex-encoded fields (build_flags_hash, label_registry_hash, feature_mask emit via `"%016lx"`) → strchr finds 'x'/'X' → base 16. Decimal fields ("%u", "%lu", "%d") → base 10. Result: a new hex field added to the registry auto-flows through both emit AND parse with no manual parser branch.

```cpp
// In tt::stamp_parse_field<T> (StampBoundModelConstRegistry.hpp):
} else if constexpr (std::is_unsigned_v<T>) {
    const int base = (fmt[0] != '\0' &&
                      (strchr(fmt, 'x') != nullptr ||
                       strchr(fmt, 'X') != nullptr)) ? 16 : 10;
    dst = static_cast<T>(strtoull(val, nullptr, base));
}

// Caller (parser X-macro) passes fmt from the registry tuple:
#define X(name, group, presence, type, fmt, default_val, get_value, emit_when, doc) \
    else if (strcmp(key, #name) == 0) { \
        tt::stamp_parse_field(r.name, val, fmt); \
        STAMP_PARSER_SET_HAS_##group(name); \
    }
FOREACH_STAMP_BOUND_MODEL_CONST_PRE_CFG(X)
```

**Meta-principle (applies broadly):** before adding a new tuple column to encode a new dimension, check if an existing column already encodes it. The originally-proposed `parser_base` column (v5.15.0.B initial draft) was discarded in favor of fmt-detection because `fmt` already specifies the format unambiguously. Net result: 0 tuple-shape change + 0 caller updates + future hex fields auto-flow.

Cost of runtime fmt-detection: 1 strchr scan per field load (~2-3ns; boot/hot-swap-time path only; not slow path or hot path). Trade-off favors DRY + auto-flow over the constant-time win of a compile-time base column.

### Layer 4: Post-coding round-trip HMAC test

```cpp
// Test pseudocode:
{
    // 1. Take a known v(N-1) stamp body bytes (committed test fixture).
    const char* legacy_canonical = R"(...)";  // exact bytes from v5.14.7 stamp
    const char* legacy_secret = "test-secret";
    char legacy_hmac[65];
    hmac_sha256_hex(legacy_canonical, legacy_secret, legacy_hmac);

    // 2. Parse it via NEW (registry-driven) verify_model_stamp.
    ModelStampResult r = verify_model_stamp("legacy.stamp", legacy_secret);

    // 3. Reconstruct StampInferenceCfgInputs from parsed result via AUTOPOPULATE.
    StampInferenceCfgInputs inf{};
    populate_from_result(&inf, &r);  // copy parsed fields into emit-side struct

    // 4. Re-emit canonical body via NEW (registry-driven) stamp_write_for_model
    //    with same secret + HMAC computation.
    char canonical_buf[4096];
    int n = build_canonical_body(canonical_buf, sizeof(canonical_buf), &inf);

    // 5. Compare BYTES.
    check("v5.14.8.A.7: canonical body bytes byte-for-byte match v5.14.7",
          n == strlen(legacy_canonical) &&
          memcmp(canonical_buf, legacy_canonical, n) == 0);

    // 6. Compute HMAC of re-emitted body; compare to legacy HMAC.
    char new_hmac[65];
    hmac_sha256_hex(canonical_buf, legacy_secret, new_hmac);
    check("v5.14.8.A.7: HMAC byte-identical post-migration",
          strcmp(new_hmac, legacy_hmac) == 0);
}
```

If either check fails, refactor introduced wire-format drift. Bisect to find the offending registry row / format string / locale issue.

### Layer 5: Canonical body snapshot test (locked hash)

Prevents future row reorders from silently breaking the chain:

```cpp
// At A.merged commit:
StampInferenceCfgInputs inf{};
populate_synthetic_all_fields(&inf);  // populate every registry field with known values
const char* body = build_canonical_body(...);
uint64_t snapshot_hash = fnv1a_64(body);
check("v5.14.8.A.7: registry canonical body output hash unchanged",
      snapshot_hash == 0xDEADBEEFCAFEBABE);  // locked at A.merged time
```

Future PR that reorders registry rows → body bytes change → hash changes → test fails. Forces deliberate hash reset.

### Layer 5b: Structural invariant tests for derived-filter wire-format protection

**Established 2026-05-14 (v5.15.5.F.4 planning); REVISED 2026-05-16 (v5.15.5.F.4d.1 first-application discipline correction per Option F):** original draft proposed a LOCKED-hash-constant snapshot mechanism; Caramel's "principle beats registry for ELIMINATING" rule (set 2026-05-15 at `.F.4c.3` WIP2d-1.B.0c) caught a Class 18 mirror at the hash-constant layer. Option F replaces snapshot-as-lock with structural invariant tests at the consumer site, aligning § 5b with existing Layer 4 + `calls_graph_diff` + Check 7 discipline.

When a registry is a DERIVED FILTER of a larger source registry (per `x-macro-registry-with-presence-dispatch.md` derived-filter section), the wire-format byte-preservation discipline extends with **structural invariant tests** that encode the canonical body's intent directly.

**Problem:** `FOREACH_STAMP_BOUND_CFG_DERIVED` becomes a derived walk over `FOREACH_CFG_FIELD` filtered by `STAMP_BOUND_CFG_DERIVED` metadata bit. Adding a new flagged row to the SOURCE registry extends the DERIVED walk. **Risk:** if a NEW field is inserted in the middle of `FOREACH_CFG_FIELD` (rather than at the end of the flagged subsequence), the derived walk produces fields in a DIFFERENT order. HMAC chain breaks for all legacy stamps. **Plus:** format-string drift, locale leak, walker code bug — each is a separate drift vector requiring detection.

**Mechanism — structural invariant tests (Option F canonical):**

The framework macro `DERIVED_FILTER_DECLARE_WIRE_FORMAT(NAME, SOURCE_FOREACH, METADATA_BIT)` (revised signature; no LOCKED params) generates a canonical body emit fn + a `NAME##_run_generic_invariants()` runner that asserts the canonical body's intent:

| # | Invariant | Drift caught |
|---|---|---|
| I1 | Line count == flagged-row count (per scalar source) | Walker skip-condition bug; missing emit |
| I2 | Each line matches `<name>=<value>\n` pattern | Format-string drift; emit body bug |
| I3 | Body contains no `,` decimal separator | Locale-pin Layer 2 leak (e.g., LC_NUMERIC=de_DE bug) |
| I4 | Per-row name appears EXACTLY when bit set | Filter logic inverted; row silently skipped |
| I5 | Per-core descriptors emit before global descriptors | Walker invocation order regression |

Two-source variants (`WIRE_FORMAT_TWO_SOURCE`) extend invariants to bitmap-source rows. Domain-specific invariants (e.g., bitmap-bool ternary normalization for HMAC byte-equivalence) live in the consumer header (e.g., `StampBoundDerivedFilter.hpp`).

**Concrete code snippet:**

```cpp
// CoreFrameworks/StampBoundDerivedFilter.hpp — invokes framework macro
DERIVED_FILTER_DECLARE_WIRE_FORMAT_TWO_SOURCE(
    STAMP_BOUND_CFG,
    FOREACH_CFG_FIELD,                          // scalar source
    STAMP_BOUND_CFG_DERIVED,                    // metadata bit
    FOREACH_ML_CFG_FLAG,                        // bitmap source
    ml_cfg_flags                                // bitmap field on cfg struct
);
// Auto-generates: STAMP_BOUND_CFG_emit_canonical_body(buf, cap) +
//                 STAMP_BOUND_CFG_run_generic_invariants() — I1-I5 stubs

// Test section (in controller_test.cpp):
{
    SECTION("STAMP_BOUND_CFG generic invariants PASS");
    STAMP_BOUND_CFG_run_generic_invariants();
    // Each invariant logs via check() inside the runner; named output per invariant
}
```

**On intentional change** (new STAMP_BOUND_CFG_DERIVED field added):
1. Add metadata bit to source row in `FOREACH_CFG_FIELD` (1-row mechanical change)
2. Invariants auto-handle the new row: I1's flagged-row count grows by 1; line count grows correspondingly; I4 verifies new row appears in body; all other invariants stay true
3. **No manual LOCKED const update.** **No fixture file regeneration.** **No CHANGELOG drudgery** for the byte-preservation discipline (the new field's CHANGELOG entry covers it).

**On accidental change** (reorder of existing rows, format-string drift, locale leak, walker bug):
- I1-I5 fire with **semantic failure messages** ("STAMP_BOUND_CFG I3: locale-pin Layer 2 (no comma decimals) FAILED")
- Investigation is direct: invariant name points at the drift vector
- Compare to LOCKED-const approach: "hash mismatch: got 0x...; expected 0x..." — opaque; investigator has to bisect

**Why structural invariants beat snapshot mechanisms:**

| Property | LOCKED const (rejected v1.0) | Fixture file (rejected) | **Structural invariants (chosen v1.1)** |
|---|---|---|---|
| Magic number in source | Yes (hex hash constant) | No | **None** |
| Class 18 mirror | Constant ↔ runtime walker | Fixture ↔ runtime walker | **None** — tests encode intent directly |
| Per-cohort manual update | 6+ across `.B` cohort migration | 1 per ship (tool invocation) | **Zero** — invariants auto-handle |
| Failure message | Opaque hex diff | Byte diff (inspectable) | **Named invariant + semantic message** |
| Generated files in git | No (in-source) | Yes (fixture) | **No** |
| New CI infrastructure | LOCKED const CI test | Tool + git-diff verify | **None** — tests in `controller_test.cpp` |
| Aligned with existing discipline | Novel mechanism | Yes (sister to Layer 4) | **Yes** (sister to Layer 4 + `calls_graph_diff` + Check 7) |
| Closes Class 18 at mirror layer | No (introduces it) | Partially | **Fully** |

**Alignment with codified rule:** Per CLAUDE.local.md "Registries optimize for ADDING; principle + sweep optimizes for ELIMINATING" (set 2026-05-15) — the snapshot-as-lock mechanism is a registry-of-bytes that shouldn't accumulate. Structural invariant tests apply the principle (canonical body must satisfy these invariants) without the registry intermediate.

**Why this aligns with Layer 4 + sister CI patterns:**
- Layer 4 (existing): committed `v5_14_stamp_canonical.bin` fixture serves a DIFFERENT purpose — back-compat verification (legacy stamps still load). Layer 5b's concern (anti-regression on canonical body shape) is structurally different + handled by invariants, NOT another snapshot.
- `tools/calls_graph_diff.sh verify`: compares current call graph to BASELINE; baseline file IS the snapshot. Same shape as a fixture; appropriate for call-graph regression but Layer 5b can do better with invariants (semantic checks > byte-diff).
- CI Check 7 (`check_per_core_registry_integrity.py`): predicate-based, not snapshot-based. Closest in spirit to Option F.

**First application:** `STAMP_BOUND_CFG_DERIVED` at v5.15.5.F.4d.1.A (universal cfg field registry; bit 13 reserved at v5.15.5.F.4d; first canonical implementation at v5.15.5.F.4d.1.A). Subsequent applications: any wire-format derived-filter sister registry uses the same `_run_generic_invariants()` mechanism mechanically (1-row addition to `FOREACH_DERIVED_FILTER` + framework auto-generates the invariant runner; consumer adds domain-specific invariants if needed).

**Alternatives considered + rejected (documented for future contributors):**
- **Path A — LOCKED-constant hash:** magic number in source code; Class 18 mirror at constant ↔ runtime walker; per-cohort manual sync. Original v1.0 draft of this section; rejected at first-application time per Caramel's "magic number" pushback.
- **Path C — fixture file as lock:** eliminates magic number but still a registry-of-bytes accumulating per filter; per-cohort fixture regeneration (or tool-driven) still required. Rejected per "principle beats registry for ELIMINATING" rule.
- **Path D — CMake-generated header with hash:** generated-files-in-git smell; CMake-specific; still a snapshot artifact. Rejected.
- **Path E — comments-as-fixture inline:** source file growth; manual sync at comment level (Class 18 mirror at comment-vs-runtime); awkward for binary content. Rejected.

### Layer 6: Surface G discipline (back-compat for legacy stamps)

```cpp
// In verify_model_stamp init block:
ModelStampResult r{};
// All has_* fields default to 0 (zero-init via brace-init).

// Parser body:
while (read_line(...)) {
    if (strcmp(key, "field_X") == 0) {
        r.field_X = parse(val);
        STAMP_SET(r, field_X);  // set has_* bit
    }
    // ... else strcmp branches
    // UNKNOWN keys: silently ignored (forward-compat).
}

// Caller: check has_* before reading:
if (STAMP_HAS(r, field_X)) {
    use(r.field_X);
} else {
    // Legacy stamp; field absent. Skip check or use default.
}
```

Surface G means: legacy stamps (without new fields) load with `has_*=0` defaults; new code skips checks for absent fields. Forward-compat without version bump.

### Layer 7: Cross-tool emit-site enumeration discipline

**Established 2026-05-17** (v5.15.5.F.4d.1.B.3 v1.9 RE-SWEEP — Meta-gap M2 codified after `/parity-check` caught 2 missing cross-tool emit sites that the wire-key-only enumeration at v1.9 had scoped past).

Layers 1-6 enforce byte-preservation at the engine emit/parse boundary. But the wire format is also produced by **non-engine** emit sites — `tools/*.sh` CLI helpers, training scripts, recording tools, any cross-process tool that writes the same on-disk format. Engine-side wire-format changes alone are insufficient: cross-tool emit sites must be enumerated + migrated atomically with the engine change.

**Threat shape (#4 in Threat model expanded):**

Cross-process boundaries — tool A (e.g., `tools/stamp_model.sh`) emits wire format; tool B (engine) parses. Engine refactor changes the wire format; tool A still emits old shape; tool A's output fails verification against engine parser. Symptom: operator runs CLI helper post-engine-upgrade; produced stamp doesn't load.

**Caught at v5.15.5.F.4d.1.B.3 v1.9 RE-SWEEP:**

Plan body Step 1.6.8 enumerated wire-key migrations in `tools/stamp_model.sh` (lines 240-262, 6 cohort fields). But missed:
- **Line 221:** `stamp_format_version=1` hardcoded literal (engine bumped to v2 at `.B.3` → CLI would emit v1-versioned + v2-keyed stamps; engine parser sees version mismatch + drift check inconsistent)
- **Line 244:** `inference_cfg_freshness_tau=` orphan emit (engine deleted at v5.14.9.D; tool still emits → engine parser sees unknown key; cosmetic + tool-state-stale)

The cross-tool enumeration at v1.9 was PARTIAL because it scoped to "the keys in the deletion cohort" without scanning for ALL wire-format literals in cross-process emit sites.

**Discipline (when wire-format changes — applies to engine version bumps + key renames + format-string changes + field deletions):**

1. **Comprehensive grep** over `tools/` (and other cross-tool emit dirs) for ALL literals matching the changing format:
   - Version literals (e.g., `rg "stamp_format_version=" tools/`)
   - Format key prefixes (e.g., `rg "inference_cfg_" tools/`)
   - Format-specific tokens (HMAC-emit shape, fee_rate format, any other engine-mirrored literal)
2. **Per-site disposition decision:**
   - **MIGRATE** — site emits a key in the deletion/change scope → update to new shape
   - **DELETE** — site emits an orphan key (engine no longer parses) → remove
   - **PRESERVE WITH CROSS-REF COMMENT** — site emits a legitimate key (e.g., training-time field that stays in scope) → add comment cross-referencing the engine-side canonical definition
3. **Mandatory comprehensive enumeration in plan body** when wire-format change is in scope (not piecemeal during coding):
   - Per-file site count
   - Per-pattern site count (version literal / key prefix / format token)
   - Disposition decision per site

**Cross-tool version literal sync discipline:**

The version literal (e.g., `stamp_format_version=N`) is duplicated in C++ header (`STAMP_FORMAT_VERSION_CURRENT` constant at `ML_Headers/ModelInference.hpp`) AND bash script (`tools/stamp_model.sh:221`). The 2-source sync is acceptable for low-recurrence cross-tool, enforced by:

- **Cross-reference comments** at each site pointing to the other (e.g., bash comment "MUST match engine `STAMP_FORMAT_VERSION_CURRENT` at `ML_Headers/ModelInference.hpp`")
- **Wire-format ship-close checklist:** when bumping `STAMP_FORMAT_VERSION_CURRENT`, search-replace the bash literal in same commit
- **Future CI:** `tools/check_cross_tool_emit_parity.py` compares wire keys emitted by engine vs CLI (TECH_DEBT defer — discipline alone is sufficient at current scale; CI tool warranted when 3+ cross-tool emit sites exist)

**Enforcement:**

- `/parity-check` Section E amendment — scan `tools/*.sh` + cross-process emit sites when wire-format change proposed; report per-file site counts + per-pattern site counts + disposition per site
- `future-oriented-plan-template.md` amendment — wire-format-changing plans MUST include "Cross-tool emit-site enumeration" section with per-file + per-pattern + per-site disposition

### Pattern lifecycle for Layer 7

- **Stage 1 (problem identification):** v1.9 RE-SWEEP caught CRIT-RESWEEP-1 (version literal) + HIGH-RESWEEP-1 (orphan key) — Meta-gap M2 surfaced
- **Stage 2 (DESIGN_SPEC):** THIS Layer codified at `.B.3` v1.10 plan body
- **Stage 3 (first canonical reference):** `.B.3` ship — Step 1.6.8 expansion is the canonical first application (comprehensive enumeration + per-site disposition + cross-reference comments)
- **Stage 4 (subsequent applications):** future ships with wire-format changes apply Layer 7 mechanically per `future-oriented-plan-template.md` amendment

---

## Trade-offs + when to apply

### Apply when:
- Wire format is locked (HMAC-signed; persistent file format; cross-process)
- Refactor migrates manual emit/parse to registry-driven (or any structural rewrite)
- Legacy artifacts (stamps, snapshots) must still verify post-refactor
- Multiple producers (bash CLI + C++ tool) must produce identical bytes

### Skip when:
- Wire format is internal-only (no persistent legacy artifacts)
- Format change is intentional (version bump path; legacy artifacts deprecated)
- Output is unsigned + unverified

### Cost:
- ~30-60 min for canonical body fixture generation (one-time per migration)
- ~20-30 min for round-trip HMAC test code
- ~5-10 min per audit gate (`/parity-check` Section E walkthrough)
- Locale pinning: 2-3 LOC at emit-construction site (negligible)

### Win:
- Wire-format drift caught at audit/test time (not at "operator's signed stamp doesn't verify in production" time)
- Refactors can ship with confidence (test as gate; build green = bytes preserved)
- Format changes become DELIBERATE (test failure forces decision)

---

## Reference implementations

### v5.14.8.A.merged (FoxML_Trader_v2)

- Layer 1 (pre-coding gate): `/parity-check` Section E ran post-A.0.b shipped; verified registry entry order matches emit code order
- Layer 2 (locale pinning): `ModelInference.hpp` stamp_write_for_model uses `uselocale(newlocale(LC_NUMERIC_MASK, "C", 0))`
- Layer 3 (registry fmt column): each row's `fmt` explicit; ranges include `"%d"`, `"%g"`, `"%.6g"`, `"%.17g"`, `"%016lx"`, `"%s"`, `"%u"`
- Layer 4 (round-trip HMAC test): v5.14.8.A.7 sub-tag landing this as integration verification
- Layer 5 (snapshot test): folded into A.7 alongside HMAC round-trip
- Layer 6 (Surface G): `has_*` flags default to 0 for legacy stamps; parser tolerates unknown keys

---

## Lessons / gotchas

### Locale pinning is THREAD-LOCAL via `uselocale`

`setlocale` is process-wide and thread-unsafe; can corrupt other threads. `uselocale(newlocale(...))` is per-thread; safe in lock-free hot-path code. Pattern: pin at start of canonical body construction; restore before return.

### Format string discipline: % NUM .NUM g matters

- `%g` — minimum digits for precision; varies; locale-dependent
- `%.6g` — 6 significant digits; precision-locked
- `%.17g` — full lossless double round-trip; precision-locked

Mixing in the same wire format is fine IF each entry is consistent across emit/parse cycles. Document in registry's `fmt` column.

### Boolean representation: `%d` with 0 or 1

```cpp
inf->feature_scaler_present ? 1 : 0  // normalize to 0/1 for emit
```

If the C++ field is `int` with value 5 (truthy but not 1), emit produces `"feature_scaler_present=5"`. Cross-version parser may interpret as different value. Normalize at emit time.

### String quoting / escaping

Wire format that includes user strings (e.g., `expected_role="buy_signal"`) needs to handle:
- Strings with quotes inside (escape via `\"`)
- Strings with newlines (forbidden at this level; reject at write time)
- Strings with locale chars (UTF-8 bytes are fine; locale doesn't affect)

Document the escape rules per format.

### Buffer size + truncation

Canonical body buffer must be sized for worst-case all-fields-populated. Underestimate → snprintf truncates → wire format incomplete → HMAC won't match. Audit budget: ~100 bytes per typed field × N fields + ~50 bytes per group's fixed headers + slack.

For v5.14.8.A.merged: 32 fields × 100 bytes ≈ 3200 bytes; current 4096 buffer has slack but verify with extended fields in v5.14.8.D.

### Round-trip test ON A REAL LEGACY STAMP

Synthetic test fixtures are good but a REAL v(N-1) stamp from disk is the gold-standard verification. Commit the fixture file with the test (gitignored model file → save just the canonical body bytes as test data).

### Snapshot test hash regenerates on intentional change

When intentionally changing wire format (e.g., adding a new field that emits a new line), the snapshot hash changes. Update the locked value in the test + document in CHANGELOG that the format changed.

---

## Patterns NOT used here (and why)

### Schema versioning every change

Tried in early ships. Rejected because forward-compat via Surface G `has_*` flags is cheaper for additive changes. Reserve version bumps for BREAKING changes (field removals, type changes, semantic shifts).

### Differential serialization (delta from base)

Considered for snapshot evolution. Rejected because canonical body is small (<4KB); full serialization is fast + simpler.

### Compressed serialization

Rejected because HMAC chain depends on uncompressed bytes; compression introduces format dependency.

---

## Cross-references

- `x-macro-registry-with-presence-dispatch.md` — registry's `fmt` column locks per-entry format
- `audit-driven-pre-coding-gate.md` — `/parity-check` Section E catches drift at audit time
- FoxML_Trader_v2 `DOCS/PARITY_LIFECYCLE.md` — wire-format surfaces inventory
- FoxML_Trader_v2 `DOCS/PARITY_VERIFICATION_CHECKLIST.md` — per-surface check pattern
- FoxML_Trader_v2 `CLAUDE.md` item 15 — parity-tested-by-construction discipline
- FoxML_Trader_v2 `tools/stamp_model.sh` — bash CLI emit (must produce identical bytes to C++ emit)
