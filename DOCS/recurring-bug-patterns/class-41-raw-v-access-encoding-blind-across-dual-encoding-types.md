---
type: bug-class
class: 41
name: raw-.v-access-encoding-blind-across-dual-encoding-types
codified: 2026-06-10 (Ship-B P2b flip; v5.15.5.F.4d.1.E Ship B)
severity: CRITICAL (silent wrong-behavior on capital paths; compiles clean)
recurrence_count: 1
surface_tags: money, fixed-point, hot-path, gates
sister: class-23 (type-erased dispatch), class-28 (branch hand-waves), H13, H14
mechanized_by: (candidate) grep sweep `\.v\s*(>=|<=|>|<|==|!=)` at encoding-seam reviews
---

# Class 41 — raw `.v` access is encoding-blind across dual-encoding 16B types

## The shape

`Money` (`FixedPoint<10,8>`, value = v/10⁸) and `FPN_Binary<64>` (value = v/2⁶⁴) are both
bare `{ __int128 v; }` 16-byte structs. **Any code that reads `.v` directly compares RAW
INTEGERS with no encoding semantics** — the type system cannot help once `.v` is peeled.

At the Ship-B P2b flip, `BuyGate` (OrderGates.hpp) compared
`stream->price.v >= conditions->price.v` where `stream` had flipped to decimal Money but
`conditions` (the legacy strategy thresholds) stayed binary. A decimal `.v` for $100 is
10¹⁰; a binary `.v` for $100 is ≈1.8×10²¹ — the volume gate could **never pass**, so the
engine silently produced ZERO entries. It compiled clean. Every unit test passed. Only the
integration smoke ("some buys happened") caught it.

## Detection signature

- `.v` compares (`>=`, `<=`, `>`, `<`, `==`, `!=`) or arithmetic where the two operands'
  DECLARED types differ, or where one side's domain was recently migrated.
- Mask-blend lines (`(a.v & mask) | (b.v & ~mask)`) blending across domains.
- ANY `.v` access in a file touched by an encoding migration is suspect until proven
  single-domain (both operands provably the same encoding).

## The rule

Raw `.v` access is reserved for **proven single-domain** sites (blends, persistence
memcpy, sign masks within one type). Cross-type compares go through the typed API
(`Money_Lt/Le/Gt/Ge/Eq` vs `FPN_*` compare fns), which red-builds on a domain mismatch.
Encoding migrations MUST enumerate every `.v`-compare site as part of the work-order
(the P2b work-order enumerated registry/struct/op sites but NOT raw-`.v` sites — the gap).

## False-positive surface

- `.v` compares inside ONE type's own implementation (FixedPointN.hpp kernel bodies,
  Money one-liners) are the implementation itself — fine.
- Persistence/wire memcpy of `.v` is encoding-agnostic BY DESIGN (the version field
  carries the encoding; H21/S-4 covers re-encode).
- Blends where both sources are the same verified domain (e.g. PC's first-tick ema blend
  post-fix: both `price_b`/`ema_new` binary) — fine.

## Worked instance

Ship-B P2b (2026-06-10): `BuyGate` price + volume gates (2 sites) → fixed by the ONE-cast
legacy-gate ingress (`Money_ToBinary(stream->price)` at gate entry, thresholds stay
binary per the D-184 legacy-apparatus ruling). Found via the integration smoke after
3,268 unit tests passed — unit coverage does not substitute for cross-domain
integration smokes at an encoding epoch.
