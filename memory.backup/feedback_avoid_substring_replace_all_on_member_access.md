---
name: Avoid substring replace_all on member-access patterns
description: replace_all on member access patterns like cfg.X can mangle ctrl->cfg.X by replacing the substring; use full-prefix patterns or accept the failed-edit signal
metadata:
  type: feedback
  originSessionId: 532f69da-4245-44f3-92c9-acbb549b9570
  tags: [refactor-discipline]
  sister_specs: [feedback_enumerate_consumers_before_registry_row_deletion.md, feedback_proactive_rename_candidate_surfacing.md]
---
When migrating member-access patterns with Edit's `replace_all`, watch out: the substring may appear in nested access contexts (e.g., `ctrl->config.X` contains `config.X`).

A `replace_all` on `config.X` → `BITMAP_IS_SET(config.flags, ...)` will produce:
- `config.X` → `BITMAP_IS_SET(config.flags, ...)` ✓ correct
- `ctrl->config.X` → `ctrl->BITMAP_IS_SET(config.flags, ...)` ✗ MANGLED (ctrl-> orphaned; `config` becomes a free variable reference)

This is silent at the Edit-time level (the Edit reports success); the build catches it later as a compile error.

**How to apply:**

1. **Inventory ALL prefix patterns first.** Run a grep that captures the full member-access chain (e.g., `rg '(cfg|config|ctrl->config|state->config|data->config_used)\.\bfield_name\b'`). Don't trust partial-grep summaries — they hide nested-prefix variations.

2. **Use the LONGEST-prefix replace_all first.** If you do separate replace_alls per prefix, do `ctrl->config.X` BEFORE `config.X` so the longer pattern wins. Otherwise the shorter substring replace mangles the longer one.

3. **Or: use full-prefix unique patterns.** For each distinct prefix (cfg, cfg->, config, config->, ctrl->config, state->config, data->config_used, etc.), do a separate replace_all targeting that exact prefix. Avoids substring overlap entirely.

4. **Verify with grep post-replace.** After replace_alls, grep for mangled artifacts: `rg '->BITMAP_|->[A-Z]+_IS_SET'` etc. catches the `ctrl->BITMAP_IS_SET(...)` orphan pattern.

5. **Trust the build.** Compile errors after replace_all cascade are usually the mangling artifacts surfacing. Don't paper over them; trace back to the substring replace that caused them.

**Concrete examples — TWO distinct mangling shapes observed:**

**Shape A (v5.14.9.F.1) — chained-prefix mangling:**
Migrating `config.barrier_gate_enabled` → `BITMAP_IS_SET(config.gate_cfg_flags, ...)` via replace_all caught both `config.barrier_gate_enabled` (line 347) and `ctrl->config.barrier_gate_enabled` (line 1853). Line 1853 became `ctrl->BITMAP_IS_SET(config.gate_cfg_flags, ...)` — orphaned `ctrl->` + free `config`. Caught at compile time.

**Shape B (v5.14.9.F.2) — variable-name-containing-substring mangling:**
Migrating `cfg.confidence_composite_enabled` → `BITMAP_IS_SET(cfg.ml_cfg_flags, ...)` via replace_all also caught `fake_cfg.confidence_composite_enabled` (test-local FakeCfg struct) and `parsed_cfg.use_exit_model` (test variable name). These became `fake_BITMAP_IS_SET(cfg.ml_cfg_flags, ...)` and `parsed_BITMAP_IS_SET(cfg.ml_cfg_flags, ...)` — variable-name PREFIX got orphaned + `cfg` became a free var. Critical: the `cfg` part was NOT a member-access prefix — it was a SUFFIX of an identifier (`fake_cfg`, `parsed_cfg`). The prefix-aware rule misses this entirely.

**Strengthened inventory regex (catches BOTH shapes):**

```bash
# Step 1: inventory ALL variations (including variable-name suffixes)
rg '\b[a-zA-Z_][a-zA-Z0-9_]*cfg\.\bfield_name\b'   # variable names ENDING in 'cfg'
rg '(cfg|config|ctrl->config|state->config|data->config_used|h->|inf\.)\.\bfield_name\b'   # member-access prefixes
# Both must be inventoried + handled
```

**Better policy:** when scope is >5 sites + multiple prefix variations:
1. Inventory BOTH chained-prefix patterns AND variable-name-containing-substring patterns
2. Distinguish: which sites are the REAL field (migrate) vs which use a LOCAL struct with same field name (DON'T migrate — like FakeCfg test fixture)
3. Prefer Edit-level targeting with full surrounding context over replace_all on bare member name
4. Or: use replace_all with longer string anchors (`cfg.field = 0;` not `cfg.field`)

**Post-replace verification (BOTH shapes):**
```bash
rg '->[A-Z_]+\(\b' --type cpp -g '!build*'        # catches X->FUNC( mangling (Shape A)
rg '\b[a-z_]+_BITMAP_IS_SET\b' --type cpp -g '!build*'   # catches var_FUNC( mangling (Shape B)
rg '\b[a-z_]+_[A-Z_]+\(' --type cpp -g '!build*'  # general var-name-orphan check
```

**The pattern is: BOTH chained-prefix AND identifier-suffix variations can mangle replace_all. Inventory must catch both.**
