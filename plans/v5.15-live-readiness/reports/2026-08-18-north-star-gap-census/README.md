# 2026-08-18 north-star gap census — session register

Three i/c-class reports in this dir (a-plugin-surface / b-toolchain / c-paper-trail), saved
verbatim at receipt. Same evening the operator re-scoped to a ~1h micro-session: *"polish
mainly and making sure that the features actually work"* + *"the data dependent branch tags
dont work"* + *"search bar → fzf pop up."*

## Landed tonight (plugin `feat/hud-robustness`, pushed `77ab06e..c5bfc69`, suite 47/47 each)

- **`d3a0c18` branchtag rebased onto the SHIPPED-asm sidecars.** Root cause of "the tags
  don't work": the buffer-compile basis emits ZERO blocks for header/template functions
  (`ExecutionCore_Tick_Impl` — the operator's screenshot showed `✓ branchless` on the hot
  tick fn), and neither compile failure nor empty parse was guarded → RC-E false-green.
  This CLOSES census-C list-1 **item 18** (the last RC-E residue) and A's row-17 branchtag
  half. Proven on real sidecar data: 9048 attributed instrs → 16 data-dep lines incl. the
  `can_enter|can_exit` gates at ExecutionCore.hpp:636-638; empty range → `nocode`, never
  green. Deliberate test flip: the old "no instructions in range → branchless" assertion
  pinned the bug; replaced by the `nocode` pin (test-deletion-justification in the commit).
- **`c30ad77` ui.fuzzy_pick** (matchfuzzypos, zero deps) + every picker rewired: browse
  structs / by-[TAG] both stages / TAG ADD vocab (static), roam (LIVE clangd re-query —
  was type-blind input→list). Layer-stack marker honored; sizing = ui token `fzf_dims`.
- **`c5bfc69` Refresh-[DERIVED]-layout menu row** (`check_cache_layout.py --fix` via
  bless_term; `:checktime` at TermClose). Closes census-A rank-3 — the D-372
  "refresh DERIVED in place" layout leg.

## Queued (the finish-list, from the three reports — re-derive there, not here)

- **Plugin lane (A §2):** HUD graph-walk drill-in (rank 1) · per-entry compare/open-beside
  key (rank 2) · compare connective tissue (rank 4) · [DEFERRED] work-queue picker ·
  orphan tile · tag-query composer · diagnostics one-step + ambient `<T>` chip + flicker ·
  REGISTRY card facet (**blocked upstream** on [ROW]/[COLUMN] render — B rank 5).
  Menu-as-fzf (filter-as-you-type on the root menu) — operator floated it via screenshot;
  interaction with number-run/key-suffixes is a design call, ASK before building.
- **Toolchain lane (B §2):** v1 call-graph generator (rank 1) · pre-push gate 0.7 (rank 2)
  · 0.8 planes/self-hosting · RC-B per-header db · scaffold generator · [SWAR] detector.
- **Owed doc re-grounds (C §2/§3, none done tonight):** north-star §4/§5/§8/§10 re-ground
  (+ §6/§7.5 marks BOTH directions) · plan-body Status header (toolchain-v1-plugin-first,
  frozen at v1.5/2026-08-07 — C calls it the primary repair target) · D-372/D-413/D-414
  STATUS sentinels · TD-247 flip-to-closed · TD-254 id-line drift · TD-256 "unblocked"
  annotation · TD-231 verify-then-flip · TOOLCHAIN_VERSION bump-or-record · fleet-register
  register row for `77ab06e` (convention check).
