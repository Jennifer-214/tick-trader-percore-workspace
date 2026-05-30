---
name: prefer boundary-stable refactors over wide cascades
description: When refactoring a system whose behavior crosses a type/struct boundary, default to keeping the boundary types unchanged and pushing the change to one side; cascading through every consumer is the wrong shape unless explicitly required.
metadata:
  type: feedback
  originSessionId: 70e3e1bb-6139-4191-82b6-b095689ca6d6
  tags: [refactor-discipline, structural-fix]
  sister_specs: []
---
When refactoring a function or struct whose outputs feed many consumers
(RegimeSignals fields, GUI panels, snapshots, FeatureRegistry, etc.),
default to:

1. Keep the public boundary types unchanged
2. Do the new computation INSIDE the function with whatever types are
   correct (e.g. FPN<F> for determinism), then convert at the boundary
3. Achieve the goal (e.g. bytewise determinism) via deterministic
   conversions at the edges rather than rewriting every consumer

**Why:** This was the model architecture choice operator wanted for
v5.10.0b.2.5.C (FlowFeatures FPN_Exp/FPN_Sqrt conversion). I had
mapped out a 6-file cascade (FlowState → RegimeSignals → FeatureRegistry
→ GUI → snapshot → tests). Operator pointed out the smaller path:
keep `double` API, do FPN math internally. Achieves the determinism
goal; saves ~3 hours of editing + ~5 files of merge surface; defers
the wide cascade to v5.11 when there's a dedicated optimization sprint
for it.

This pattern relates to the audit's Part 3 architectural principle —
"Reducing Memory Touch Sites" — generalized from cache lines to source
files: don't sprawl a refactor across many sites if you can isolate
it behind a stable interface.

**How to apply:**
- Before scoping a refactor, identify the public type boundaries
  (struct fields visible outside the file, function return types,
  enum values exposed in headers)
- Ask: "can the new behavior live entirely inside the existing type
  boundary?" — if yes, keep the boundary, change the internals
- Only cascade if the boundary type itself is the source of the bug
  (e.g. converting RegimeSignals.flow_10s to FPN really IS what
  closes the gap — but that's a v5.11 ship with explicit budget)
- Mention this trade-off to operator when proposing scope, so the
  choice is explicit rather than absorbed into "let's just refactor
  everything"

**Heuristic for "stable boundary vs full cascade":**
- File-touch count: 1-3 → boundary scope; 4+ → propose stable boundary
  + ask operator before cascading
- Cross-file determinism gap: if the boundary IS double and converting
  through FPN→double→FPN is determined to be safe, stable-boundary wins
- Performance-sensitive boundary (hot path): cascade may be required
  to avoid double work; weigh against blast radius
