---
name: feedback-surface-operator-migration-path-proactively
description: "On wire-format / version-bump / breaking cfg proposals, surface operator migration impact FIRST in the recommendation. Default toward non-breaking alternatives unless breaking is structurally necessary. Audit findings often miss operator-workflow dimension."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ba5429a9-2f65-4f8d-950c-3ae250973f24
---

When proposing any change with operator-visible impact — wire-format bump / stamp version change / cfg schema change / parser bounds tightening / file format evolution — surface the OPERATOR MIGRATION DIMENSION as a first-class evaluation axis, not an afterthought.

**Default toward non-breaking alternatives** unless breaking is structurally necessary. Consider these patterns first:
- **Parser dual-recognition + emit transition** (sister to `wire-format-byte-preservation-discipline.md` Layer 6 Surface G — parser tolerates BOTH old and new wire keys; emit transitions to new; SOFT version bump signals new EMIT format; existing artifacts continue loading)
- **Closed-set back-compat layer** (`canonical-sister-extension-discipline.md` § INLINE MERGE — bounded time-tracked deprecation via TECH_DEBT entry)
- **Surface G forward-compat** (parser tolerates ABSENT fields — additive changes without version bump)

If a non-breaking alternative exists + costs <2x more than breaking option, choose non-breaking. Operator workflow protection ranks high in the trade-off matrix.

**Why:** Codified 2026-05-17 at `.B.3` audit cycle. Both `/parity-check` CRIT-1 + `/accounting-audit` HIGH-1 framed stamp_format_version bump as binary STRICT vs LENIENT. Neither surfaced the SOFT compat option (parser dual-recognition). Caramel pushback #4 ("ideally we would never have to use [restamp_model.sh]") exposed the gap. The audits MISSED operator-impact entirely; took her senior-engineering judgment to surface it. Encode so future-me checks operator-impact proactively, not reactively.

**How to apply:** Every recommendation involving wire-format / version / file format / cfg schema change MUST include explicit "Operator migration impact" section in the proposal. Section must enumerate: (a) what action operator needs to take if this lands; (b) whether non-breaking alternatives exist; (c) if breaking IS chosen, the rationale + mitigation tools.

**Recognition markers:**
- Wire-format / version / cfg schema change without "Operator migration impact" section → not ready to surface
- "STRICT mode" recommendation without considering SOFT compat alternative → not ready
- "Operator re-trains models" or "operator regenerates stamps" tool proposal — RED FLAG; check for parser back-compat alternative FIRST

**Future-oriented-plan-template.md decisions table column:** "Operator migration impact" added alongside Robustness/Latency/Design/Future-easier.

**Sister:** [[feedback-audit-own-proposals-with-same-rigor]] (this is the 3rd of 4 pillars) + [[feedback-recheck-designspecs-on-pushback]] + [[feedback-evaluate-options-on-robustness-latency-design-not-time]] (this memory adds OPERATOR-IMPACT as 5th axis alongside the existing 4).
