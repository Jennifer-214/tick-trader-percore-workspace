---
type: agent-report
status: FROZEN — verbatim agent output, saved at receipt (operator directive 2026-08-10)
directive: plugin-parity fleet — invoker surface (keybinds/commands) + vocab-derivation per the §9 law
agent_class: i-class
task: I-3 — keybinds + vocab derivation census (+ C++-vs-script placement verdict)
delivered: 2026-08-10
disposition_register: ../../plan_checks/2026-08-10-plugin-parity-fleet-register.md
---

# I-CLASS REPORT — fox-symdeps.nvim invoker surface + vocab-derivation census — VERBATIM

All claims grounded in current code on `feat/hud-robustness` (HEAD f3bf273) at `tools/plugins/fox-symdeps.nvim/`.

## § 1 · Entry-point inventory

### 1a. Global keymaps (registered `init.lua:265-306`; default trigger `init.lua:9`)

| Key | Action | Site |
|---|---|---|
| `<leader>dd` | float HUD on unit at cursor | init.lua:265 |
| `<leader>dD` | board — ADD card | init.lua:266 |
| `<leader>df` | follow card toggle | init.lua:269 |
| `<leader>dS` | browse structs | init.lua:272 |
| `<leader>dr` | roam workspace symbol | init.lua:275 |
| `<leader>dw` | dashboard | init.lua:278 |
| `<leader>dg` | straddle diagnostics toggle | init.lua:281 |
| `<leader>dl` | ambient size lens toggle | init.lua:284 |
| `<leader>da` | **insert static_assert** (the one sanctioned code-writer, ⚠) | init.lua:287 |
| `<leader>dc` | winbar size chip toggle | init.lua:290 |
| `<leader>de` | source↔asm explorer | init.lua:293 |
| `<leader>db` | branch tags toggle | init.lua:296 |
| `<leader>du` | use-lens toggle | init.lua:299 |
| `<leader>dm` | `:FoxSymdepsMenu` palette | init.lua:300 |
| `]u` / `[u` | use-lens hop (only non-d binds) | init.lua:301-302 |
| `<leader>d[` / `<leader>d]` | board card flip (global) | init.lua:305-306 |

which-key group label init.lua:307-310.

### 1b. Commands
`:FoxSymdepsReload` :194 · `:FoxSymdepsAsmFlags` :198 · `:FoxSymdepsCockpit` :201 · `:FoxSymdepsDerived` (bang = ✎ write+save) :204-233 · `:FoxSymdepsMenu` :235-248 · `:FoxSymdepsReloadAll` :249 · `:FoxUnit` tagcursor.lua:124-132.

### 1c. In-window keys, per surface
- **HUD** — hud.lua:244-268: `j/k/↓/↑` move · `<C-d>/<C-u>` page · `<CR>/l/→` activate · `h/←` fold · `q/<Esc>` close · `Q` quickfix · `y` yank · `r` refresh · `w` width-lits · `a` asm-diff · `m` menu · `/` filter · `?` help; `i o x dd p` no-op'd (:269-271). Lens keys via `map_action` (lens.lua:20-21): `s` false-sharing · `m` mutations · `n` notes · `t` access-density · `b`/`c` cascade (byte_layout_cascade.lua:201-202).
- **Board extras** — panel.lua:170-175: `L/H` flip · `x` drop · `s` compare.
- **Dashboard** — dashboard.lua:100-113: nav + `r` + `q/<Esc>`; no `y/Q///?`.
- **Menu** — menu.lua:86-98: `1-9` run · `<CR>/l` run · `q/<Esc>/h` cancel · autoclose BufLeave/WinLeave.
- **Docview float** — docview.lua:109-114: `q` close · `p` pin; chooser rides `menu.open` (:207) **without a palette**.
- **Asmview** — asmview.lua:113-115: `q` + `f` re-pick. No `<Esc>`.
- **Asmexplorer** — asmexplorer.lua:246: `q` only.
- **Quickfix shim** — hud.lua:45-50: `q` = cclose. **Help float** — hud.lua:346-349: `q/<Esc>/?`.
- **External pickers**: browse/roam `vim.ui.select`/`input`; asmflags chooser; foxtag heal prompt.

### 1d. Autocmd-triggered UI
Cockpit auto-dock (cockpit.lua:31) · tagcursor CursorMoved debounce → `User FoxUnitChanged` (tagcursor.lua:106-117) → follow-card swap (followcard.lua:63-71) · live-edit TextChanged refetch (hud.lua:962-976) · external-reload + sizeof-delta alert (hud.lua:981-1003, 96-102) · ambient CursorHold (ambient.lua:44) · status winbar (status.lua:65-66) · branchtag BufWritePost/BufEnter (branchtag.lua:160) · use-lens re-apply (highlight.lua:68) · ColorScheme re-hl (init.lua:261) · float BufLeave autoclose (hud.lua:273, dashboard.lua:114, menu.lua:98) · asmexplorer CursorMoved sync + BufWritePost recompile (asmexplorer.lua:250-258).

## § 2 · Collisions + convention divergences

**HIGH — same-key, two live semantics, last-write-wins by context:**
1. **`m` = menu vs mutations.** hud.lua:266 maps `m`→`_menu`; the mutations lens binds `m` via `map_action` when `ctx.kind ∈ {field, symbol}`, and lenses bind *after* window-open (same-buffer `keymap.set` replaces) → **the menu is unreachable by key on field/symbol contexts**. The `?` help says `m` = who-writes (hud.lua:304); the footer shows *both* `m mutations` and the unconditional `m menu` (hud.lua:175-179 vs :713). Known 🟡 north-star §7.5:210 — this census refines the mechanism.
2. **`s` = board-compare vs false-sharing.** panel.lua:173 binds `s`→compare at open; false_sharing then binds `s` for every non-function card → **compare-by-`s` shadowed on exactly the struct cards it was built for**, while actions.lua:18 still advertises it. Re-binding recurs on every re-inspect.

**MED — §6 keybind-SAFETY violated family-wide:** all 16 leader binds are d-prefix; a dropped/timed-out leader turns them into destructive vim operators (`dd` delete-line, `dw`, `da`/`df` operator-pending, `d[`/`d]` motions). The in-HUD no-ops defend only the HUD buffer — the source buffer, where engine code lives, is undefended.

**MED — §9(iii) two-popups root located:** hud.lua:857-865 (`_menu`) rebuilds items as `{label, run}`, **dropping `writes`** (and any future field), while `:FoxSymdepsMenu` passes rows intact (init.lua:241-247) — tier icons ride one invoker. (The §9(iii) note records the asymmetry with sides inverted vs current code; the structural root — two independent item-shape builders over one `menu.open` — is the same either way.) Third invoker docview.lua:207 adds a third shape (no palette).

**MED — same-semantic different-key across surfaces:** close = `q/<Esc>` (HUD/dashboard/menu/help) vs `q`-only (asmview/asmexplorer/docview) · `h/l` = fold/expand in trees but cancel/run in the menu · `p` = pin in docview but a no-op in the HUD while help claims "Panel … p follow/pin" (hud.lua:312 — stale; follow moved to `<leader>df`) · `Q/y///?` HUD-only though dashboard rows are equally jumpable.

**LOW — stale key documentation (3 drift instances):** help `m` claim :304 · help panel-`p` :312 · lens template taken-list (_TEMPLATE.lua.txt:27) omits `m r s t c n` + the no-op set · `_to_quickfix` docstring says `<C-q>` (:788) vs actual `Q` (:257).

## § 3 · Vocab-derivation table (surface → axis → current vs derived)

Ground truth: `foxtag grammar --json` **already emits five vocab tables** — `categories`(79) · `ref_subcats`(11) · `concern`(59) · `surface`(33) · `unit_types`(10, with `closable`) — but nodemodel.lua:103 decodes **only `unit_types`**.

| # | Surface | Vocab axis | Current | Derived form |
|---|---|---|---|---|
| 1 | Action gating `types` (actions.lua:50-64) | `unit_types` | Hand-typed lowercase, unvalidated; ENUM/REGISTRY/STRATEGY/TYPE/TEST have **zero** gated actions (REGISTRY = north-star's biggest named gap §7.5:210,217) | Registration-time validation: every `types` key ∈ `unit_types` (§9's "cite your axis" made mechanical); coverage holes become a visible list |
| 2 | HUD-menu type input (hud.lua:855) | same | Feeds **treesitter-kind** vocab into a tag-`[TYPE]`-keyed filter — `kind="type"` structs miss struct rows; registry/file rows unreachable from the HUD | ONE kind→unit-type adapter; `for_type` accepts unit-type only; both invokers one axis |
| 3 | Write-tier icons ✎/⚠ (menu.lua:9-14; actions.lua:51,63) | **T6** writer-tier (tools/CLAUDE.md:32, D-380) | Correctly declared per row, stripped by the hud wrap (:857-865) | Pass rows through; the tier column rides the one registry — identical popups by construction |
| 4 | Docview subcat routing (docview.lua:46-59) | `ref_subcats` (in payload; **not decoded**) | Two hand sets; unknown subcats silently default to `--where` | Decode `ref_subcats` for validation now; the routing *column* = a language-neutral contract extension to the core emit (accrues per D-415) |
| 5 | Scope openers (tagcontext.lua:33) | `unit_types.closable` | **Already derived** — the worked exemplar (retired hand-mirror kept as evidence :9-16) | — |
| 6 | Hotpath tier (hotpath.lua:23-31) | latency-tier manifest | **Regex-scrapes the Python tool's source** for `"tier": "hot"` — T1 second-parser shape | Tool-owned JSON emit (or foxtag-absorbed at v1) |
| 7 | Section glyphs/labels ×2 (hud.lua :521-696 vs :315-328) | plugin presentation vocab | Two hand copies; already drifted (`m` row) | One section registry `{id, glyph, label, gloss, kinds}` |
| 8 | Keymap docs ×4-5 (init.lua:265-306 · help :295-312 · README.md:74-80 · _TEMPLATE:27 · footer :709-727) | plugin key registry (doesn't exist) | Four hand copies, three drifted | One keymap registry (X-macro-shaped) rendering all five sites |
| 9 | Roam icons (browse.lua:50) | LSP-kind→glyph | Magic-number hand map | Fold into #7 glyph vocabulary |
| 10 | Compare when-gate (actions.lua:22-27) | runtime state (§6) | **Already the pattern done right** — exemplar | — |

## § 4 · C++-vs-script placement verdict

**The unified menu/keymap core stays SCRIPT-side (Lua). No C++ menu core; no Python hooks in this loop.**
1. **D-415** (log :2809): capabilities land script-side during churn; the v1 core owns **FACTS**. The menu is vim window lifecycle + buffer-local maps + run-closures — a subprocess/recompile boundary reintroduces the twin-maintenance tax on the plugin's *fastest-churning* surface (the action set changed 4× in a month: cd971ac, docview rows, compare row, follow-card row).
2. **The C++-eligible piece already exists and is underused**: the gating *vocabulary* is core-owned data behind the T10 envelope (5 tables); the plugin should consume more of it (decodes 1 of 5), not host new core code. New axes land as **contract rows** on the existing emit ("the contract, not the language, is what accrues").
3. **Novel alternative considered:** emit the **affordance matrix itself** from foxtag — `unit_type × action-id × T6-tier` as payload, Lua binding closures by id. Right T10 shape *eventually*; **rejected now** — locks a weekly-churning UX table into the rebuild loop mid-churn. Park as a v1 conversion-program candidate; the Lua actions registry is its locked-contract precursor.

## § 5 · Recommendation + migration order

| Opt | Shape | Assessment |
|---|---|---|
| A | Spot-fix stale docs + re-letter colliding keys | Cheapest; leaves the drift class open (3 instances already) |
| B | Pass-through item shape only | Closes the observed defect; gating vocab split + 4-site keymap drift remain |
| **C (recommended)** | Derivation seams in order below | Structural per recurrence evidence; each phase independently shippable |
| D (novel) | Core-emitted affordance matrix | Rejected for now per §4.3; revisit at v1 |

**Order:** 1. **Collision + staleness close-out**: free `m` universally by routing who-writes *through* the menu as a registry row (removes the special case — `feedback_structural_fix_over_belt_and_suspenders`), keep `s`=compare on boards (false-sharing likewise a row or re-letter), fix hud.lua:304/:312/:788, _TEMPLATE:27, pass the palette at docview.lua:207. 2. **One item shape**: `Hud:_menu` forwards rows, wrapping only `run` (shallow-copy preserves `writes` + future fields). 3. **One gating axis**: kind→unit-type adapter; registration-time `types` validation vs `nodemodel.model()`; decode the remaining 4 payload tables. 4. **Keymap registry** (X-macro-shaped) rendering registration/footer/help/README/template. 5. **d-prefix exit** (§6 safety): with #4 the prefix is one constant — 1-line flip + muscle-memory migration; choice is operator taste (needs a collision scan of her live nvim config, outside this repo). 6. **Cross-surface semantic normalization**: `q+<Esc>` everywhere; `y/Q/?` on dashboard; document `f` (asmview) as a distinct flags-pick semantic.

**Tests blast-radius:** near-zero — 44 tests pin pure functions, none pin keymaps.

## § Spots most worth an adversarial refute

1. **Phase-4 registry = the over-engineering candidate** (`feedback_framework_layer_payoff_diminishing_returns`); evidence for structural = 3 shipped drift instances; refute by showing hand-fix + convention suffices for a solo plugin.
2. **`s`-shadowing** rests on bind ordering + re-inspect re-binding — verify empirically in a live board on a struct card.
3. **Menu-as-router for `m`/`s`** trades one extra keypress on frequent ops — operator-UX call; press the latency-of-use side.
4. **Phase order**: correctness-first could put the d-prefix exit (destructive-edit hazard on engine source) before the registry; my order optimizes total work — the counter is legitimate under `user_correctness_first_not_ship_fast`.
5. **§9(iii) inversion**: if the operator's screenshots postdate HEAD, an unpushed/other-checkout divergence is worth a c-class currency check before coding against this map.
