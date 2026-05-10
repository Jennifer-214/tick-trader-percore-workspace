# Wire-format byte-preservation discipline (HMAC chain protection)

**Established:** 2026-05-09 (v5.14.8 sprint)
**Status:** ACTIVE
**Cross-references:**
- Companion: `x-macro-registry-with-presence-dispatch.md` (registry as source of truth for canonical wire format)
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

### Layer 3: Registry tuple's `fmt` column

```cpp
X(name, group, presence, type, fmt, default_val, get_value, emit_when, doc)
//                              ^^^
//                   Per-entry printf format string locked here.
//                   Registry-driven emit ALWAYS uses this format.
```

Adding a new entry requires explicit `fmt` choice. Reviewer/audit can grep for `"%g"` vs `"%.6g"` vs `"%.17g"` discrepancies.

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
