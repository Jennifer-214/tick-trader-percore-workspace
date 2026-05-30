---
type: audit-report
audit: adversarial-fix-audit
finding: F-076
date: 2026-05-29
engine_head: 2492e43
auditor: independent-fix-auditor
verdict: PROPOSED-FIX-CORRECT-DIRECTION-BUT-UNDERSCOPED
---

# F-076 fix-audit — Fingerprint_Compute canonical hash

**Finding (confirmed):** `Backtest/Fingerprint.hpp:180` SHA-256s RAW `ControllerConfig<F>` bytes; its own comment (`:171`) claims sorted-field canonical serialization. Struct is default-init, has dirty inter-field padding + un-zeroed char-array tails → non-deterministic fingerprint.

**Proposed fix (audited):** "Field-wise canonical hash — serialize each field explicitly (matching the comment), padding-immune. Possibly reuse FOREACH_CFG_FIELD. H12-struct as alternative."

---

## Q1 — Does changing the hash break any FATAL fingerprint consumer? PARTLY FATAL.

Consumers of `training_fingerprint` (grep, full tree):

- **ML_Headers/ModelInference.hpp:511** — `strncpy` store only. NOT compared. The fatal gate above it (`:500` MODEL_FORMAT_VERSION → `return 0`) is a *different* attr (`foxml_version`). Fingerprint read is non-fatal. ✓ GT3 correct on this site.
- **ML_Headers/CoreModelZoo.hpp:2239** `EnsembleModelZoo_ComputeBundleId` — concatenates first-8-hex of each loaded handle's `training_fingerprint` → 64-char `bundle_id`.
- **That `bundle_id` IS fatally compared:** CoreModelZoo.hpp:2599 (`thompson_state.json` → "bundle_id mismatch; rejecting" → `return 0`), :2734 (exit variant), and BanditLearning.hpp:691-692 (`Bandit_LoadJSON` memcmp → reject). Mismatch → bandit/Thompson state **rejected → reverts to uniform priors** (EnsembleModelZoo_InitBandits).

**Severity verdict:** GT3's "just stores it" is INCOMPLETE — it missed the bundle_id chain. BUT the lineage-break is still **LOW-HARM**, for a subtler reason than GT3 gave:

1. `ComputeBundleId` reads the fingerprint **string already embedded in the model file** (set once at train, `BacktestPanels.hpp:3159`). It does NOT recompute via `Fingerprint_Compute` at load. So save-side bundle_id and load-side bundle_id both read the SAME stored string → **they match regardless of whether that string was computed deterministically.** The bug does not, by itself, cause spurious bundle_id rejections.
2. Bundle_id check is gated `if (saved_id[0] != '\0' && ...)` and `if (expected ...[0])` — empty fingerprint → check skipped (forward-compat-by-absence).
3. Per ground-truth, existing fingerprints are garbage anyway; nothing downstream does cross-build fingerprint *equality* expecting determinism today.

**Net:** changing the algorithm re-bases every fingerprint (all old model files get a new value next train). No FATAL consumer compares a fingerprint across the algorithm change — bundle_id self-consistency is preserved because both sides read the embedded string. Lineage-break = **acceptable** (the lineage was a lie before). **Caveat the proposing agent did NOT flag:** ControllerConfig.hpp:369-370 documents a LOAD-BEARING invariant — *"Backtest fingerprint hashes `fee_rate` (NOT maker/taker) — preserves bundle compatibility."* A field-wise rewrite that naively serializes all three fee fields **changes the hash semantics that comment pins**. Must preserve (hash `fee_rate`, skip `fee_rate_maker`/`fee_rate_taker`) or consciously re-base. This is exactly the kind of detail a pragmatic-patch glosses.

## Q2 — Is field-wise-via-FOREACH_CFG_FIELD FEASIBLE? NO, not as stated. The registry covers a MINORITY of the hashed struct.

- **`FOREACH_CFG_FIELD` does not exist.** Retired at .F.4c.3 → split into `FOREACH_GLOBAL_CFG_FIELD` (55 rows) + `FOREACH_PER_CORE_CFG_FIELD` (88 rows) (CfgFieldRegistry.hpp:263, :467; GT5 stale on the name).
- The hashed object is `ControllerConfig<BACKTEST_FP>` (`results->config_used`, BacktestEngine.hpp:269; `BACKTEST_FP` IS handled — it's just the F param, BacktestSharded.hpp:122 copy-assigns). Its layout:
  - ~55 auto-gen flat global fields (FOREACH_GLOBAL_CFG_FIELD, EMIT at ControllerConfig.hpp:1316),
  - **~148 MANUAL scalar fields** in the struct body (lines 359–1316; FPN/int/char[]/uint*) NOT in either registry,
  - **`PerCoreCfg<F> cores[MAX_EXECUTION_CORES]`** (line 1276) — the 88 per-core fields live HERE, indexed per-core; the registry iterates *descriptors*, not `cores[c]` instances,
  - legacy mirror arrays (`core_strategies[16]`, `core_symbol[16]`, `core_model_path[16][256]`, …).
- So `FOREACH_GLOBAL_CFG_FIELD` reaches ~55 of ~200+ flat fields and **zero** of the per-core `cores[]` payload that actually drives per-core trading. A registry-only field-wise hash would **silently hash a fraction of the config** — strictly WORSE than today (looks canonical, ignores per-core strategy/risk/ML). This is a real correctness trap, not a style nit.
- Per-type serialization the registry'd need: FPN<F> → already padding-clean (`FixedPointN.hpp:45-47`: `uint64_t w[N]; int32_t sign; int32_t _padding=0;`, and `FromDouble:189` normalizes -0 → sign collapses), so hashing `w[]`+`sign` is canonical. ints/bools trivial. char[] → must hash `strlen` only (the tail is the dirty source). Registry exposes STORAGE_T + name but **no generic "serialize this field" accessor** and no `cores[c]` walker — would need new infra.

## Q3 — Ranking the candidate fixes (Caramel's gradient: structural > patch; compile-time > runtime > convention; SSoT; canonical-sister)

| Approach | Verdict |
|---|---|
| **(B) H12-compliant struct (explicit `_padding=0` on ControllerConfig)** | **Strongest on gradient, but BLOCKED as a standalone.** Defeats the char-array-tail dirt? NO — `_padding` fixes inter-field gaps, not un-zeroed string tails (the empirically-confirmed 9-byte residue). Also: global fields are H17 auto-gen (can't hand-insert padding into the X-macro emit without a registry change); per-core `cores[]` is H17-locked with `static_assert(sizeof % 64)`. So pure-H12 is neither sufficient (tails) nor freely editable (H17). |
| **(C') Zero-init the hashed buffer at the populate site** — `ControllerConfig<F> tmp; memset(&tmp,0,sizeof tmp); tmp = *cfg;` then hash `tmp` | Insufficient ALONE (finding already proved: copy-assign re-dirties 9 bytes because the SOURCE char tails are dirty and copy faithfully). Would need memset of `config_used` *before every populate* everywhere it's filled — fragile, convention-level, not structural. REJECT as primary. |
| **(A) Field-wise canonical serialize, hand-listed OR registry+manual hybrid** | **Best ACTUALLY-CORRECT fix.** Hashing each field by VALUE (char[] by strlen, FPN by w[]+sign, scalars raw) is padding-AND-tail immune by construction — matches the comment claim (SSoT: the comment already promises this). MUST cover manual fields + `cores[0..N-1]` + legacy mirrors, not just the registry. Registry reuse is a PARTIAL SSoT win for the ~55 global rows; the rest is hand-listed or needs a `cores[]` walker. |
| **(D) Normalize-then-hash: a `Fingerprint_CanonicalizeConfig(dst, src)` that copies field-by-field into a zero'd struct, then raw-hash the canonical copy** | **Recommended primary.** Single canonicalization function = one SSoT site; raw SHA over the canonicalized buffer keeps SHA code untouched. char[] copied via `strncpy`+explicit tail-zero; FPN/scalars copied (already clean). Covers the WHOLE struct incl. cores[]. Compile-time-ish guard available: a `static_assert(sizeof(ControllerConfig<64>) == EXPECTED)` "canonicalizer coverage" sentinel that fires when the struct grows, forcing the canonicalizer to be revisited (the registry-drift guard analogue). |

**Ranked recommendation:** **(D) ≈ (A) over (B) over (C')**. (D)/(A) are the same family (explicit per-field value capture); (D) localizes it to one canonicalize fn + leaves SHA raw + naturally spans `cores[]`. Reuse `FOREACH_GLOBAL_CFG_FIELD` inside the canonicalizer for the global slice (SSoT for those rows) + hand-walk manual fields + `for c in cores[]`. Pure (B) and pure (C') are REJECTED as standalone (neither addresses char tails; both run afoul of H17 / convention-fragility).

## Q4 — New-bug risk introduced by the fix

1. **Coverage drift (HIGH):** if field-wise, any field added later but not added to the serializer → silently un-hashed. MITIGATE with the sizeof-sentinel `static_assert` above (compile-time, per Caramel's gradient) + ideally drive the global slice off the registry so those can't drift.
2. **fee_rate semantics (MED):** see Q1 — must preserve "hash fee_rate not maker/taker" or knowingly re-base. Don't auto-include all three.
3. **Char-array order/length stability (LOW):** hashing `len` then bytes is fine; hashing raw `sizeof` of a char[] re-introduces the tail bug — the serializer MUST use strlen, not sizeof, for strings.
4. **FPN cross-run byte form (NONE):** already `_padding=0` + `-0` normalized; `w[]`+`sign` is canonical cross-run/cross-binary. Safe to hash directly. Do NOT route FPN through `FromDouble`/`ToDouble` for hashing (R1: those are lossy/by-design-divergent) — hash the stored limbs.
5. **cores[] beyond num_execution_cores (LOW):** unused `cores[c]` slots are default-init but their char tails are dirty — the canonicalizer must zero tails for ALL MAX_EXECUTION_CORES slots (or hash only `[0,num_execution_cores)` — but that makes the hash depend on core count, which is arguably correct). Decide explicitly.

## Q5 — Net-gating verdict for `.E.0.1` (Net-2). NOT net-gating. Routes to Net-1 / PRE-PAPER-TEST.

`.E.0.1`'s net = FP+replay **determinism** CI gate (F-056/57/58, F-054/55) — the no-reintroduction net that makes the `.E.1` rename trustworthy. F-076 is a **model-lineage** determinism bug, orthogonal to the sqrt/locale/replay determinism net. Per the handoff (`net-scoped-handoff.md:37`) F-076 is already filed **"MED — `.E.0.1` (fold-if-net-gating) / PRE-PAPER-TEST."**

Is it net-gating for Net-1 (PERSIST/fingerprint characterization)? **Only weakly.** Net-1 is golden-master/characterization of REAL output (per F-059 discipline). A characterization test freezes *whatever the fingerprint emits today*. But F-076 means today's output is **non-deterministic** — you cannot freeze a golden value for a function whose output varies with buffer dirt. So **IF Net-1 characterizes Fingerprint_Compute, F-076 MUST be fixed first** (you can't golden-master a non-deterministic function — same logic as F-059's "don't characterize atop a non-deterministic floor", handoff:45). If Net-1 characterizes only PERSIST (snapshot) and NOT the fingerprint, F-076 is independent → PRE-PAPER-TEST.

**Honest verdict:** F-076 is **net-gating ONLY for a fingerprint golden-master** (can't freeze non-determinism); it is **NOT** gating the FP/replay determinism net that defines `.E.0.1`. Recommend: fix lives at **`.E.0.1` IF Net-1 scope includes fingerprint characterization, ELSE PRE-PAPER-TEST correctness mini-ship.** Either way the FIX itself is (D)/(A), with the sizeof-sentinel + fee_rate-preservation + strlen-not-sizeof + hash-FPN-limbs-not-ToDouble guards. Do NOT accept a memset-only or registry-only patch — both are confirmed insufficient.
