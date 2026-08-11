---
type: finding-disposition-register
ship: E.1.2.B 0.4 (plugin parity fleet — operator-directed, 2026-08-10 evening)
status: LIVE — dispositions flip at fix commits. Corpus = three i-class reports (I-1 entry-set parity · I-2 float sizing/placement · I-3 keybinds + vocab derivation), delivered in-session 2026-08-10; raw transcripts lived in /tmp (loss-prone) — THIS FILE is the durable extraction, written same-hour.
plugin_head_at_census: f3bf273 (feat/hud-robustness); e116ae2 (docview routing) landed mid-census — I-3 censused at f3bf273
operator_directives: unified menu across surfaces · recency-sort-as-rule · TAG ADD · float dismiss-on-leave + pin (ideas §11) · "2-4 agents investigate parity, continue meanwhile"
dogfoods: feedback_name_members_never_tallies_in_docs + feedback_document_as_you_go_over_catch_at_end
---

# Plugin parity fleet — finding-disposition register

All paths `tools/plugins/fox-symdeps.nvim/lua/fox-symdeps/` unless noted. Severities are the
agents' own (apparatus plane). Every finding OPEN until its fix commit flips it here.

## I-1 — entry-set parity (menu/action surfaces)

- **P1 (HIGH; = §9-instance-iii root):** `hud.lua:856-865` re-wraps registry rows to bare
  `{label, run}` — `writes` (and every future field) DROPPED → tier icons/legend ride ONE
  invoker only. `init.lua:243` passes rows verbatim. **Direction disputed:** operator
  screenshots showed icons on dd→m and plain on dm; code + the cd971ac diff say the reverse
  (I-1 refute-spot #1: possibly stale runtime / label swap). Fix is direction-agnostic:
  one item shape by construction.
- **P2 (HIGH):** `when()` gates evaluate in the HUD SCRATCH buffer (`hud.lua:855`) — the Docs
  row's gate (`actions.lua:33-47`) scans the HUD's own rendered text → **the docview row
  silently never appears on HUD-invoked menus** (a defect in tonight's ship). dm evaluates in
  the source buffer, correct.
- **P3 (HIGH):** two TYPE SPACES feed `for_type`: dm = tag space (`tagcontext`, upper
  FUNCTION/STRUCT/REGISTRY/…), HUD = treesitter kinds (`context.lua:5-9`) → same cursor,
  different entry sets; registry `types` vocabulary covers only function/struct — REGISTRY/
  TYPE/ENUM/STRATEGY/TEST have ZERO gated actions.
- **P4 (MED, headless-verified on nvim 0.12.4):** dd-FLOAT mode closes on BufLeave
  (`hud.lua:272-277`) — pressing `m` enters the menu → the HUD closes UNDER it; menu survives
  at frozen coords; canceling leaves NOTHING (a read-only action costs the HUD).
- **P5 (MED):** stale-ctx lens closures after board card flip — `Hud:reset` clears hints but
  never unbinds; `s/t/n/b/c/m` run against the PREVIOUS card's symbol until that lens rebinds.
- **P6 (MED/LOW):** title derivation ×3 formats · docview chooser passes no `palette`
  (untinted border; also never docks) · help/README stale (`hud.lua:304,312,788`;
  `README.md:77`; `_TEMPLATE.lua.txt:27`) · four parallel enumerations of the op set
  (registry / leader maps / HUD keys+footer+help / README) = the drift engine.
- **I-1 recommendation:** ONE registry (rows gain `id` + `key` + `when(ctx)` explicit-ctx +
  tag-vocab `types`) · `actions.run(row, ctx)` central runner (kills the re-wrap class) ·
  renderer takes ROWS verbatim · footer/help/README action-sections DERIVE · load-time key
  collision assert. Rejected: minimal patch (class recurs) · vim.ui.select renderer (loses
  tier column/number-run/docking) · keymap-as-SSoT (fold as one-way desc derivation only).

## I-2 — float/window sizing + placement

- **S1 (HIGH):** chooser cramping is STRUCTURAL — `menu.lua:31-42,50` computes size from
  content with no editor clamp and never sets `nowrap`; nvim clamps oversize floats + float
  wrap defaults ON (probe-verified) → long labels wrap, rows push out of view. The docview
  label-shortening patched the symptom only.
- **S2 (MED):** anchor-dock has no fit-to-anchor logic (`menu.lua:19-24`) — wide menus spill
  over the code window; tall menus clip in the 12-line bottom strip.
- **S3 (MED):** HUD float is the sole FIXED surface (72×28) — clamps+wraps under ~76 cols,
  clips bottom rows, under-fills 4K (north-star §6 "fill available space").
- **S4 (MED):** five ad-hoc width caps (strip 60 / dashboard 96×40 / docview 110 / card 72 /
  pin uncapped) — no shared policy owner; §6 reads as "surplus → MORE panes, not wider".
- **S5 (LOW-MED):** close conventions split 3 ways (q+Esc+focus-loss / q+Esc persistent /
  q-only); help float lacks focus-loss close (orphan on click-away — drift, not choice);
  docview q-only is half-deliberate (real-buffer Esc would leak).
- **S6 (LOW):** `title_pos` + winhighlight family breaks on docview; pin split lacks
  `winfixwidth` (`docview.lua:88`); aspect-2.2 threshold duplicated (`hud.lua:58`,
  `panel.lua:69`); portrait bottom strip uncapped (45 rows on 113 lines — test-pinned, so
  currently intended).
- **I-2 recommendation:** small `ui.lua` token helper — `small-chooser` (content-driven,
  clamped, `nowrap`, anchor-fit + cursor fallback) · `card` (HUD) · `reading-pane` (docview's
  formula, codified; real-buffer = q-only rule) · `board-card` (resolve_placement moves here +
  shared constants) · `full-compare`. Declarative surfaces-REGISTRY deliberately deferred
  (7 sites < framework threshold; the token table is its seed). Migration: menu → help/dash →
  docview → HUD card → placement constants → pin winfixwidth.

## I-3 — keybinds + vocab derivation

- **K1 (HIGH; = I-1 P-collisions, mechanism agreed):** lens `map_action` same-buffer
  `keymap.set` overwrites post-open → `m` menu unreachable on field/symbol HUDs
  (mutations lens) · board `s` compare shadowed on struct cards (false-sharing lens) while
  `actions.lua:18` still advertises it. Footer shows BOTH hints for one key.
- **K2 (MED):** ALL 16 leader binds are d-prefix — dropped leader = destructive vim operators
  ON ENGINE SOURCE (§6 keybind-safety, family-wide). Prefix choice = operator taste + needs a
  scan against her live nvim config (outside repo).
- **K3 (MED):** nodemodel decodes 1 of 5 grammar vocab tables (`nodemodel.lua:103`) —
  `categories/ref_subcats/concern/surface` sit unclaimed in the payload; docview's subcat
  routing is hand-set (validate against `ref_subcats` once decoded); hotpath lens
  REGEX-SCRAPES the Python tool's source for tier facts (T1 second-parser shape) → tool-owned
  emit.
- **K4 (LOW):** keymap docs ×4-5 hand copies, 3 drifted → ONE keymap registry rendering
  init-registration / footer / help / README / template taken-list.
- **K5 (verdict):** unified menu core stays SCRIPT-side (D-415: the core owns FACTS; menus are
  window lifecycle + closures; the fastest-churning surface). Core-emitted affordance matrix
  (unit_type × action × tier) = v1-conversion candidate, PARKED; the Lua registry is its
  locked-contract precursor.

## CONVERGENT SYNTHESIS (all three agree)

**One registry · one runner · one renderer · one placement layer · docs derive.** Phases
(each independently shippable; defect-first):

1. **Defect closes:** `actions.run(row, ctx)` + explicit-ctx `when(ctx)`/`for_type(ctx)`
   (kills P1+P2 structurally) · docview chooser gains `palette` (+anchor) · P4 disposition
   (suppress float BufLeave-close while child menu open, or reopen after) — OPERATOR Q.
2. **Key registry + collision assert:** rows gain `id`+`key`; lens actions fold in as rows;
   bind-from-registry with load-time same-key assert (kills K1/P5 via rebind-with-fresh-ctx).
3. **One type space:** treesitter-kind→tag-type adapter at the resolver seam; registry types
   re-keyed to tag vocab (kills P3); decode the remaining 4 grammar tables (K3) — unlocks
   ref_subcat validation + future tag-filterable trees.
4. **`ui.lua` placement tokens** (S1-S6) + float dismiss-on-leave + `p`-pin as persistence
   (operator's §11(v) call) + recency-sort as a renderer rule (§11(iii)).
5. **Docs derive:** footer/help/README action sections + keymap registry (K4/P6).
6. **Headless teeth:** icons-per-tier · when-ctx · collision assert · anchor-fit · the
   cd971ac proofs made permanent (zero menu-seam tests exist today — itself a finding).
7. **Later/parked:** d-prefix exit (K2, operator taste + config scan) · TAG ADD row (§11(ii))
   rides the registry once phase 2 lands · affordance-matrix-from-core at v1 (K5).

## REFUTE SPOTS (self-flagged; verify before/while fixing)

P1 direction (screenshots vs code — moot under the fix, note for honesty) · P4 realism in the
full stack (facsimile repro) · K1-m intended-UX question (help text documents m=mutations —
if intended, the fix is a key-space decision, not a bug) · type-vocab extension timing
(REGISTRY facets unbuilt — maybe function/struct+universal suffices until D-334 cards land) ·
`when(ctx)` signature is the one breaking API (grep out-of-tree lens consumers first) ·
S-nowrap truncation vs wrap+grow-height honesty.

## OPERATOR QUESTIONS — ANSWERED 2026-08-10 (same evening)

1. P4/D6 → **KEEP the HUD open under its child menu** (suppress-close-while-child-open).
   Generalized by the operator into the **LAYER-STACK RULE**: *"the highest layer — opened item
   > menu > HUD; when the top level item opens, it should close the other 2"* — each surface
   keeps its PARENT alive while open; an action that opens a new top surface COLLAPSES its
   ancestors. Implemented phase 1: menu buffers carry `b:fox_symdeps_menu`; the HUD float's
   BufLeave guard skips departures INTO its own child menu (cancel returns to a live HUD);
   `actions.run`'s `ctx.collapse` closes the ancestor chain when an item runs.
2. K1 → operator has NO attachment to m=mutations ("not sure what this is") → treat as a
   COLLISION BUG; structural fix stands (who-writes routes through the menu as a registry row,
   `m` = menu universally). Phase 2.
3. S4/§6 → operator neutral ("not sure what you mean") → DEFAULT to the north-star reading
   (both I-2 and the orchestrator): readability caps stay; ultrawide surplus → MORE PANES.
4. K2 → **PARKED by operator** ("we don't have to move this yet, i can just hit u if i
   delete") — d-prefix stays; revisit on her call.
5. dm anchor → subsumed by the layer-stack rule (#1): dock to the HIGHEST live layer.

## PHASE-1 DISPOSITIONS (plugin commit this same evening)

- **P1/K-item-shape → CLOSED-phase-1**: `actions.menu_rows` passes registry rows VERBATIM
  (`__index` — `writes`/all future fields ride every invoker); `actions.run(row, ctx)` owns the
  restore-source dance the HUD wrapper hand-rolled. Identical popups by construction.
- **P2 → CLOSED-phase-1**: `for_type(t, ctx)` + `when(ctx)` explicit ctx; the Docs row gates
  against the invoker-named SOURCE buffer (the HUD names its tracked buffer).
- **P4 → CLOSED-phase-1** per answer #1 (guard + collapse).
- **P6/S6 docview-palette half → CLOSED-phase-1** (chooser now family-styled).
- **§11(v) float dismiss-on-leave → CLOSED-phase-1** (WinLeave dismiss; p-pin owns
  persistence). **§11(iii) recency-sort → LANDED for the docview chooser**
  (`docview.sort_found`, prefix-grouped newest-first, toothed); generalizes to other lists at
  phase 4's renderer.
- REMAINING phases 2-6 per the synthesis (key registry + collision assert · one type space ·
  ui.lua tokens · docs-derive · headless teeth); K2 parked.
