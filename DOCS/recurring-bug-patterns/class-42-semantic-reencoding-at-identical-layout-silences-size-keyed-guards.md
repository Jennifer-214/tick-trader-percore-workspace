---
type: bug-class
class: 42
name: semantic-reencoding-at-identical-layout-silences-size-keyed-guards
codified: 2026-06-10 (Ship-B close; promised at D-172a, gate finding S-4/R3-B)
severity: CRITICAL (persistence/wire misread; guards stay green while meaning flips)
recurrence_count: 1
surface_tags: persistence, wire-format, versioning, money
sister: H21 (identifier retirement), Class 40, D-181 (the epoch-net structural answer)
mechanized_by: encoding-keyed static_asserts (MONEY_ENCODING_EPOCH guards — the D-181 pattern)
---

# Class 42 — semantic re-encoding at identical layout silences size-keyed guards

## The shape

Every layout-keyed guard — `sizeof` static_asserts, `offsetof` locks, `entry_size` header
gates, "bump the version when the struct changes" conventions — keys on BYTES. A semantic
re-encoding at unchanged bytes (Ship-B: `FPN_Binary<64>` 2⁻⁶⁴ → `Money` 10⁻⁸, both bare
16B `__int128`) passes EVERY one of them while every persisted/wire value silently changes
meaning. Old snapshots replay binary-scaled ints as decimals; old event logs misread every
money field; nothing red-builds, nothing refuses to load.

Canonical instance: Ship-B R3-B — the 16B→16B decimal flip was invisible to all of
PORTFOLIO/SHARDED/CONTROLLER snapshot size locks, the OMSEL `entry_size` gate, and the
stamp byte layout.

## Detection signature

- A migration described as "same size, different meaning/encoding/scale/unit".
- Version constants whose bump-trigger comments mention only LAYOUT ("fields changed",
  "bytes changed") on structs that carry VALUES with an encoding.
- Any wire/persistence surface whose loader checks magic + size but not an
  encoding/format version.

## The structural fix (the D-181 epoch-net pattern)

Key guards on the ENCODING, not (only) the layout: a compile-time encoding epoch
(`MONEY_ENCODING_EPOCH = is_fp_decimal_v<EngineMoneyT> ? 1 : 0`) + per-surface
static_asserts demanding the version floor rise WITH the epoch
(`static_assert(EPOCH == 0 || VERSION >= N + EPOCH)`). The re-encoding then red-builds
until every persistence/wire version rides the same commit — the build PRESCRIBES the
flip cohort. Proven at the Ship-B P2b flip: five surface guards fired and listed their
own remediation.

## False-positive surface (M3)

Layout-keyed guards are CORRECT and sufficient for layout-only changes (field add/remove/
reorder/resize) — this class does NOT deprecate sizeof/offsetof locks; it says they are
incomplete for encoding flips. A re-encoding that genuinely changes size is caught by the
existing size guards and is NOT this class. Display-only re-interpretations (a double
derived for the TUI) carry no persistence and need no epoch key.
