---
name: feedback-enumerate-consumers-before-registry-row-deletion
description: "When proposing X-macro registry row deletion / rename / column-1-vs-source-name change, comprehensively enumerate consumer sites BEFORE finalizing scope. Auto-gen'd struct fields create hidden consumer coupling that piecemeal cross-greps miss. Run ONE comprehensive grep across ALL access patterns (dot/arrow/macro/token-paste) codebase-wide."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ba5429a9-2f65-4f8d-950c-3ae250973f24
---

When proposing X-macro registry row deletion (or rename, or column-1-vs-source-name asymmetry close), auto-generated struct fields create hidden consumer coupling. **Enumerate consumer sites VIA ONE COMPREHENSIVE GREP before finalizing scope** — piecemeal cross-greps miss sites + cause iteration spiral.

**The grep shape (comprehensive consumer access enumeration):**

```bash
# Per field-being-deleted: grep ALL access patterns codebase-wide
rg -n "(<field_name>|STAMP_HAS\([^,]*,\s*<field_name>\)|<MACRO>_<field_name>)" \
   <codebase_root> -g '*.hpp' -g '*.cpp' -g '*.py' -g '*.md'

# For sets of fields, use alternation:
rg -n "inference_cfg_(field1|field2|field3|...)\b" <codebase_root> -g '*.hpp' -g '*.cpp'
```

Capture site counts PER FILE:
```bash
rg -lc "<pattern>" <codebase_root>
```

**Why:** Codified 2026-05-17 at `.B.3` after 7 iterations of plan body amendments (v1.2 → v1.8) where consumer scope kept expanding via piecemeal cross-greps:
- v1.4: 9-entry POST_CFG deletion (consumer migration implicit)
- v1.5: 10 entries (1 standalone added); 12 test sites surface
- v1.6: 15 entries (5 model-state Class 32 added); 5 more BacktestPanels sites surface
- v1.7: 15 CfgDriftCheckRegistry STAMP-side renames + 5 more BacktestPanels missed at v1.6
- v1.8: ONE comprehensive grep reveals 149 total sites across 8 files; ~100 sites were missed by piecemeal approach

Each iteration found more because the original audit + my cross-greps were FIELD-LIST-AT-A-TIME or PATTERN-AT-A-TIME, not COMPREHENSIVE-ACROSS-ALL-FIELDS-AND-PATTERNS.

Caramel's exact framing: "i wanna ensure we completely update the codebase to be as maintainable as possible" — partial enumeration leaves consumer surfaces inconsistent + creates coding-time discovery cost.

**How to apply:** Before finalizing the scope of a plan body that proposes registry-row deletion / rename:

1. **List ALL fields in deletion scope** explicitly
2. **Construct comprehensive grep** with all field names in alternation
3. **Cover ALL access patterns:**
   - Direct field access: `.<name>`, `-><name>`, `::<name>`
   - Token-paste macros: `STAMP_HAS(_, <name>)`, `BITMAP_IS_SET(_, MASK_<NAME>)`, `STAMP_SET(_, <name>)`
   - String mentions in comments/docs/test fixtures
4. **Count sites per file** via `rg -lc` to size scope honestly
5. **Categorize sites:** production (must migrate at this ship) vs test (must migrate at this ship) vs comments (cosmetic; defer or batch)
6. **Plan body captures the PROCEDURE + total site count**, not necessarily every site explicitly (use `rg` at coding time as authoritative enumeration)

**Recognition markers:**
- "consumer migration is mechanical" framing in plan body → STOP; enumerate sites comprehensively first
- "9 entries to delete" without per-field consumer site count → not ready to surface
- Each cross-grep iteration finds more sites → SIGNAL the audit was incomplete; run one comprehensive sweep
- "Test fixture updates" listed as "~10 sites" or similar vague count → not ready to surface; grep + count

**Sister memory:** [[feedback-audit-canonical-sister-before-new-infra]] — that's for PRODUCER side (don't create parallel infra). This is the CONSUMER side (don't delete without enumerating). Both apply at framework consolidation surface; both are pre-coding planning discipline.

**Replace_all safety:** for field-name renames like `inference_cfg_bandit_blend_ratio` → `bandit_blend_ratio`, full-token replace_all is safe per `feedback_avoid_substring_replace_all_on_member_access` (full-token matches; no substring conflict). Coding-time procedure:
```bash
# Per field, one mechanical replace_all sweep:
rg -l "inference_cfg_bandit_blend_ratio" | xargs sed -i 's/inference_cfg_bandit_blend_ratio/bandit_blend_ratio/g'
# Build verify after each field rename to catch any unsafe consumer
```

15 fields × ~1 min replace_all + build verify each = ~15-30 min mechanical work for 100+ sites.

**Sister memory:** [[feedback-avoid-substring-replace-all-on-member-access]] — substring danger only; full-token names like `inference_cfg_<name>` are safe.

**Trade-off vs trying to enumerate every site in plan body:**

Apply this procedure-based discipline ONLY when consumer sites exceed ~30. Below ~30 sites, explicit enumeration in plan body is more readable + serves as coding checklist. Above ~30, procedure-based + post-coding grep-verify is more honest about scope.
