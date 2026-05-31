# Class 37: Raw-struct byte-equivalence (memcmp/hash/wire-emit) over a padding-bearing or char[]-post-NUL struct

## 1. Description
Comparing, hashing, or emitting a struct by its raw bytes (`sizeof(T)`) when the struct contains compiler-inserted padding bytes (from alignment) or fixed-size `char[]` arrays. These bytes contain uninitialized "garbage" from the stack or heap, making logically identical objects byte-asymmetric.

## 2. Worked Instance (F-076, 2026-05-30)
The `Fingerprint_Compute` function used `SHA256_Update` over `sizeof(ControllerConfig)`. Because the struct was default-initialized (not zero-initialized) and contained padding for `FPN<64>` alignment, the fingerprint hash diverged across runs for the same logical configuration, breaking train-serve lineage.

## 3. Structural Fix
- **Compile-time:** Use `static_assert(std::has_unique_object_representations_v<T>)` for any type subjected to raw-byte operations.
- **Construction:** Enforce zero-initialization (`memset(this, 0, sizeof(*this))` or `{}`) in the constructor.
- **Layout:** Use explicit `_padding` fields (H12) to make padding bytes deterministic and visible.
- **Operation:** Perform field-wise hashing/comparison instead of raw-byte operations for complex structs.
