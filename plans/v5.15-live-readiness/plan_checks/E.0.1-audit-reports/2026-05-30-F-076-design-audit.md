---
type: design-audit
ship: v5.15.5.F.4d.1.E.0.1
finding: F-076 (config fingerprint determinism — the H12 byte-equivalence class)
gate: new-function design-audit (/hft + /dod + H12 + determinism lenses) BEFORE coding
status: DRAFT — for operator consult (3 open decisions)
---

# F-076 design + design-audit — deterministic config fingerprint

## TL;DR
F-076 is **one** site, not two. `Backtest/Fingerprint.hpp:180` raw-hashes `ControllerConfig<F>`
(`SHA256_Update(&s, cfg_ptr, cfg_size)`), and the cfg is **never zero-init'd**
(`ControllerConfig_Default` = `ControllerConfig<F> cfg;`), so its **inter-field padding is garbage**
→ identical cfg *values* produce different fingerprints across runs (H9/H12 violation; model-lineage
non-determinism). **Recommended fix: zero-init ControllerConfig** (padding→0 → raw hash deterministic),
NOT the plan's field-wise canonicalize (over-engineered; enumeration-fragile on the mixed struct).
The plan's sibling "StampT memcmp" is **already safe** (probed). New **Class 37+** + a compile-time guard.

## Investigation (probed, not assumed)
- `sizeof(ControllerConfig<64>) = 68224`; `has_unique_object_representations = 0` → **inter-field padding present** → raw-hash non-deterministic. F-076 confirmed.
- `ControllerConfig_Default()` (`ControllerConfig.hpp:1469`): `ControllerConfig<F> cfg;` (default-init → garbage padding). `ControllerConfig_Load` copies from `_Default`. → the cfg's padding is never zeroed = the **root cause**.
- **Cascade enumeration** (whole-struct byte-equivalence): exactly **one** raw-struct hash — `Fingerprint:180`. Every other `memcmp` is `sizeof(double/float)` scalar or in tests (deliberate). No raw-struct HMAC (HMAC is over the canonical *string* body). **Not a sprawling cascade.**
- **StampT `cfg_drift_compare`** (`CfgFieldDispatch.hpp:454`): FPN branch `memcmp(&a,&b,sizeof(FPN<F>))` — probed `FPN<64>`: 24 bytes, `has_unique_object_representations = 1` → **no padding** → memcmp deterministic (same-value FPNs byte-identical even after a garbage memset, verified). `char[]` branch uses `strncmp` (strlen-aware). **StampT needs no fix.** (Finding: plan over-listed it.)

## Why NOT remove the padding
ControllerConfig is 68KB with `alignas(64)` cross-thread fields (H6 false-sharing prevention) — the padding is **load-bearing**. You cannot de-pad it. So the choice is zero-init the padding, or canonicalize (hash fields, skip padding). Cache-line padding and byte-equivalence are orthogonal; they only collide at the hash site.

## The fix — options for ControllerConfig

| Option | Mechanism | Pro | Con | Verdict |
|---|---|---|---|---|
| **A. Zero-init (recommended)** | default ctor `ControllerConfig(){ memset(this,0,sizeof(*this)); }` (robust, all paths) — or minimally `cfg{}` value-init in `_Default` | 1 change; padding=0 by construction; preserves fingerprint scope; `is_trivially_copyable` preserved (verified pattern) | adds a default ctor (mild deviation from "C-style, no classes"; makes struct non-aggregate — but no aggregate-init sites exist) | **CHOSEN** |
| B. Canonicalize (plan's original) | field-wise hash into a zeroed buffer | decoupled; explicit | needs to enumerate the **mixed X-macro + manual** struct; a missed field = silent **Class-18 lineage drift**; more code | rejected (over-engineered + drift-prone) |
| C. per-field `_padding=0` (H12 canonical) | explicit padding members | matches ThompsonBandit | impractical for ~222 fields | rejected |

## Prevention — close the class
- **Compile-time guard (small structs):** a `hash_pod<T>()` / `memcmp_pod<T>()` wrapper carrying `static_assert(std::has_unique_object_representations_v<T>)`. Placed at the **hash/compare site**, never on the struct definition — so it can NEVER fire on a cache-line-padded struct that isn't raw-hashed. FPN<F> already passes; future small stamp structs are guarded.
- **ControllerConfig (can't pass the static_assert — deliberately padded):** zero-init ctor + a **characterization test** (freeze the fingerprint of a fixed cfg; assert identical cross-run + after a garbage-memset-then-populate) — the runtime guard the compile-time one can't give a padded struct.
- **CI grep / determinism-net add:** flag `SHA256_Update(…, sizeof(<struct>))` / `memcmp(…, sizeof(<struct>))` whose target isn't `has_unique_object_representations` → review.

## New anti-pattern (Class 37+)
*"Raw-struct byte-equivalence (`SHA-256` / `memcmp` / wire-emit over `&struct, sizeof`) on a struct with inter-field padding (or `char[]` post-NUL) is non-deterministic for equal field values. Fix: zero-init (padding→0) for big/padded structs; padding-free layout + `static_assert(has_unique_object_representations)` for small ones; or canonicalize. Prevention = the site-level static_assert guard + a CI grep — which makes H12 mechanically enforced instead of remembered."* Sister to H9/H12; meta-sister to the verify-by-real-trigger lesson.

## Design-audit verdicts (/hft + /dod + H12 + determinism)
- **HFT / H1 (alloc-free):** zero-init ctor = `memset`, no malloc. ✅ Boot/stamp-time, not the 500ns hot path. ✅
- **H4:** no float math. ✅
- **H9 / H12 (the target):** zero-init makes the byte-equivalence deterministic — directly closes the violation; the static_assert mechanizes H12 for small structs. ✅
- **DOD:** struct-level fix (no per-field walker) — simpler than the registry-walk canonicalize and avoids its mixed-struct enumeration drift; the static_assert is compile-time enforcement (DOD-preferred). ✅
- **Determinism / golden-epoch (D-100):** the fingerprint changes once (lineage break — same disposition as `.E.0.1` R4; old gitignored models retrain; documented). Within the new epoch, deterministic. ✅
- **Class-18 drift:** zero-init AVOIDS it (no enumeration to drift); canonicalize would INCUR it → another reason A wins. ✅

## Tests changed
- **NEW:** characterization test — `_Default` + populate → fingerprint twice + after a garbage-memset-then-populate → identical; cross-process determinism assertion (fold into the determinism net).
- **NEW:** `static_assert(has_unique_object_representations_v<FPN<64>>)` on the POD hash/compare guard.
- **MODIFIED:** existing fingerprint tests — regenerate the golden fingerprint (epoch boundary; deliberate, not weakening per `/test-strength-audit`).

## Acceptance criteria
- ControllerConfig zero-init'd at all fingerprinted creation paths; `Fingerprint_Compute` deterministic for equal field values (characterization test GREEN cross-run).
- StampT confirmed already-safe (documented; optional belt-and-suspenders static_assert).
- `has_unique_object_representations` site-guard added; CI grep (or determinism-net fold) for raw-struct byte-equivalence.
- Class 37+ codified; H9/H12 cross-ref noted. Fingerprint golden regenerated (epoch); R4 retrain note.
- Hot path untouched; `controller_test` GREEN.

## OPEN — operator consult (before coding)
1. **Zero-init mechanism:** default-constructor (robust across ALL creation paths) vs `cfg{}`-in-`_Default` only (minimal, but a fresh `ControllerConfig<F> cfg;` elsewhere could re-introduce garbage — discipline-reliant). → **I lean default-constructor** (determinism shouldn't depend on every site remembering `{}`).
2. **The CI guard:** standalone check vs folded into the determinism net (Check F). → **I lean folded** (one determinism gate).
3. **StampT (already safe):** document-only, or add the `static_assert` for belt-and-suspenders? → **I lean add it** (cheap; guards a future small-struct raw-hash).
