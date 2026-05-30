---
name: feedback-wire-context-vs-cfg-file-parser-separation
description: "When a parser function serves BOTH cfg-file context (operator types %) AND wire context (raw fraction), KIND_DOUBLE_PCT scaling MUST be context-aware OR functions MUST be split — silent 100× round-trip drift otherwise"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 23677810-15af-419a-bb0f-e89d723c198b
  sister_specs: []
  tags: [wire-format, structural-fix]
---

When a parse function serves BOTH cfg-FILE context (operator types `15.0` meaning "15%") AND wire-context (stamp body has raw `0.15` fraction), KIND_DOUBLE_PCT-style display scaling MUST be context-aware OR the two parsers MUST be separate functions. Reusing one function across both contexts causes silent 100× round-trip drift in the wire context.

**Why:** Caught at v5.15.5.F.4d.1.B.3 Phase F when `cfg_parse_field<FPN<F>>` applied `/100` scaling unconditionally for KIND_DOUBLE_PCT rows. Phase F's framework-driven stamp parser (`parse_stamp_cfg_to_derived`) reused `cfg_parse_field` → stamp body `fee_rate_taker=0.001` parsed back as `0.00001` (1e-5; 100× too small) → operator's fees in stamp would silently break the runtime engine's fee calculations. The cfg-file scaling was correct for its context (operator-facing `%` convention); reusing it for wire context was the bug.

**How to apply:** Whenever introducing a NEW parser function that's used by BOTH cfg-file AND wire/HMAC body contexts, ADD an explicit `bool wire_context` (or sister) param + apply KIND_DOUBLE_PCT scaling only when `!wire_context`. The `tt::cfg_emit_field<T>` for FPN<F> already uses raw `FPN_ToDouble()` (no KIND_DOUBLE_PCT scaling) per Layer 2 wire-format byte preservation — the parse counterpart MUST match. Closes the same Class 18 anti-pattern (mirror in conversion direction) at parser semantic layer. Apply to ANY new dual-context parser added to `tt::` namespace (`stamp_parse_*` / `cfg_parse_*` / future `*_parse_*` sisters). Sister: `wire-format-byte-preservation-discipline.md` Layer 2 (locale pinning + format string discipline at emit/parse).

Caught 2026-05-24 during Phase F test migration when 1 of 3230 tests caught the asymmetry (`v5.9.2b: parsed fee_rate_taker matches stamp`). Without the fee_rate round-trip test in the legacy v5.9.2b block, this would have shipped silently. Production cost: every stamp emitted with explicit `--fee_rate_maker/--fee_rate_taker` flags would have round-tripped with fees 100× smaller on engine load. Sister: `feedback_audit_canonical_sister_before_new_infra` (cfg-file parser was the canonical sister; should have audited for context-asymmetry when introducing wire-context reuse).
