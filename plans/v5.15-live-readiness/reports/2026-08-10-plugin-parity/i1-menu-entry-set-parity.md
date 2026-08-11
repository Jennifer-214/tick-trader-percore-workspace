---
type: agent-report
status: FROZEN — verbatim agent output, saved at receipt (operator directive 2026-08-10)
directive: plugin-parity fleet — unified menu/action surfaces (operator ask: one menu, all surfaces derive)
agent_class: i-class
task: I-1 — menu/action-surface entry-set parity census
delivered: 2026-08-10
disposition_register: ../../plan_checks/2026-08-10-plugin-parity-fleet-register.md
---

# INVESTIGATIVE CENSUS — menu/action-surface parity, fox-symdeps.nvim (`feat/hud-robustness`, HEAD `f3bf273`) — VERBATIM

All paths under `tools/plugins/fox-symdeps.nvim/`. Read-only pass; nothing edited. One behavior claim (D6) verified by headless repro on the installed nvim 0.12.4, not inferred.

## § Inventory — every surface that builds or describes an action list

**The intended SSoT pair:**

| # | Surface | Where | Items come from | Fields carried | Title | Icons/legend | Context-gating | Anchor |
|---|---|---|---|---|---|---|---|---|
| 1 | **Actions registry** (12 rows: HUD, board-add, follow, compare, derived-preview, docs / derived-write, asm-explorer, branchtag / straddle-diag, ambient, lock-layout) | `actions.lua:14-65`, filter `for_type` `:71-84` | — (IS the registry) | `label, run, all|types{function,struct}, when()?, writes?("comments"\|"code")` | n/a | n/a (data) | `types` + pcall'd `when()` | n/a |
| 2 | **Shared renderer** `menu.open` | `menu.lua:26-99`; icon fn `:10-14`; legend `:38-42`; docking `:19-24` | caller-supplied | reads `label`, `writes`, `run` only | `opts.title` (caller-formatted) | YES when items carry `writes` | none (assumes pre-filtered) | `opts.anchor_win` else cursor |

**menu.open callers (3):**

| # | Caller | Where | Items | Type source | Title | Icons | `when()` eval context | Anchor |
|---|---|---|---|---|---|---|---|---|
| 3 | `<leader>dm` / `:FoxSymdepsMenu` | `init.lua:235-248` (keymap `:300`) | registry rows **VERBATIM** → `writes` intact | **tag space**: `tagcontext.enclosing_block` → `blk.type:lower()` (`:241`); nil block → `""` = universal-only | `blk.type.." "..blk.name` or `"fox-symdeps"` (`:244`) | **YES** | source buffer (correct) | `panel.win() or followcard.win()` else cursor (`:242,246`) |
| 4 | HUD `m` key (dd float, dD board, df followcard, compare companion) | `hud.lua:852-872` (bind `:266`) | registry rows **RE-WRAPPED to `{label, run}`** — `writes` (and everything else) **DROPPED** (`:856-865`) | **treesitter space**: `ctx.kind:lower()` (`:855`); domain = symbol/type/field/struct/function per `context.lua:5-9,21-37` | `ctx.kind:upper().." "..ctx.symbol` (`:868`) | **NO** | **HUD scratch buffer** (wrong buffer — see D2) | `self.win` (`:870`) |
| 5 | docview multi-ref chooser | `docview.lua:195-207` | **hand-built** data rows (`id — path:line`) | n/a (data chooser) | `"[REFERENCE] → defining site"` (`:207`) | n/a (read-only rows) | n/a | none; **no `palette` passed** either |

**Parallel key-bound action surfaces (no popup — the same ops enumerated again by hand):**

| # | Surface | Where | Notes |
|---|---|---|---|
| 6 | HUD base keymap | `hud.lua:244-271` | `m/a/w/r/Q/y/?/…`; noops `i,o,x,dd,p` (`:269`) |
| 7 | Lens-contributed keys via `map_action` | `hud.lua:172-181`, dispatch `lens.lua:20-22` | `mutations m` (applies kind field/symbol) · `false_sharing s` (applies kind ~= function) · `access_density t` · `notes n` · `byte_layout_cascade b/c` — same-buffer `keymap.set` **overwrites** prior bindings |
| 8 | Board keys | `panel.lua:170-175` | `L/H/x/s` bound at open, before `inspect()` (`:177`) |
| 9 | Global `<leader>d*` maps | `init.lua:265-306` | third enumeration of the same ops the registry lists |
| 10 | HUD footer hint line | `hud.lua:707-713` | lens hints + hardcoded `"m menu · r refresh · Q qf · y yank · ? help"` |
| 11 | HUD `?` help float | `hud.lua:292-330` | fully hand-maintained prose |
| 12 | README key docs | `README.md:76-78` | fourth enumeration |

**Other choosers (`vim.ui.select` family, deliberate):** `browse.lua:31,:58` (struct / workspace-symbol pickers — ":49 Rides vim.ui.select (so your fzf)") · `asmflags.lua:46,49` · `nodemodel.lua:251` (heal confirm).

**Test coverage:** zero in-tree tests reference `fox-symdeps.menu`, `for_type`, `_writes_icon`, or anchor placement. Commit `cd971ac` claims "Headless-proven: icons per tier · placement · when-gate · registry sanity" — those proofs were **not committed**.

## § Divergences

**D1 — HIGH (the reported instance (iii)).** Write-tier metadata stripped on the HUD path. `hud.lua:856-865` rebuilds each registry row as `{ label, run }` — `writes` never copied — so `menu._writes_icon` returns blank and `any_writes` stays false → **no ✎/⚠ column, no legend** on dd→m / board-m / followcard-m. `init.lua:243` passes rows verbatim → dm **does** render icons+legend. History: `cd971ac` added icons in `menu.lua`/`actions.lua` + only `anchor_win` to the HUD wrapper. **Note-correction:** ideas §9(iii) attributes icons to the HUD path and plain to dm — code + the cd971ac diff show the **reverse**; the substance (two invokers, one shape got the tier work) is correct, the attribution swapped.

**D2 — HIGH.** `when()` gates evaluate in the wrong buffer on the HUD path. `Hud:_menu` calls `actions.for_type` at `hud.lua:855` with focus in the HUD scratch buffer; the Docs row's gate reads current buf/cursor → scans the HUD's rendered text → effectively always false → **the Docs row silently vanishes from every HUD-invoked menu** (false-positive also possible if rendered text contains the literal). dm evaluates in the source buffer → correct.

**D3 — HIGH.** Two type spaces feed `for_type`: dm = tag space (UPPER FUNCTION/STRUCT/REGISTRY/… via `nodemodel.scope_openers()`), HUD = treesitter kinds (symbol/type/field/struct/function). Same cursor → different entry sets: an unconverted file gives dm universal-only + `"fox-symdeps"` title while dd→m gives full rows; a [REGISTRY] block gives dm universal-only while the HUD may resolve `struct`. Registry `types` covers only function/struct — REGISTRY/TYPE/ENUM/STRATEGY have no rows at all.

**D4 — HIGH (functional collision).** Mutations lens **rebinds `m`** on field/symbol HUDs (applies kind field/symbol; `map_action` same-buffer overwrite) → **the action menu is unreachable from field/symbol HUDs**; footer shows both `m mutations` and hardcoded `m menu` — contradictory hints for one key. Possibly intended per help text (`hud.lua:304,328` documents m="who writes") — but then the menu has no key at all there.

**D5 — HIGH (functional collision).** Board `s`=compare clobbered: `panel.lua:172` binds `s`=compare at open; `inspect()` at `:177`; false_sharing (applies kind ~= function) rebinds `s` → for any struct card, **in-board `s` runs the false-sharing scan, not compare** — while `actions.lua:18` + `panel.lua:6` still advertise "s in-board compares". Compare reliably reachable only via the menu row.

**D6 — MED (verified).** dd is float mode; float mode closes on BufLeave (`hud.lua:272-277`). Pressing `m` enters the menu buffer → BufLeave → `Hud:close()`. **Headless repro (nvim 0.12.4):** the HUD closes, the anchored menu survives at frozen coords → "docks to the HUD" holds only for panel-mode HUDs; for dd→m the HUD vanishes behind the menu, and **canceling the menu leaves nothing**.

**D7 — MED.** Title derivation ×3 — dm `blk.type + blk.name` (`STRUCT FixedPoint<2,64>`), HUD `ctx.kind:upper() + ctx.symbol`, docview chooser a fixed string.

**D8 — LOW.** docview chooser passes no `palette` → themed border branch skipped (`menu.lua:60-63`) — the one untinted `menu.open` popup; also never docks.

**D9 — MED (adjacent).** Stale-ctx lens closures after board card switch: `Hud:reset` clears `action_hints` (`hud.lua:192`) but never unbinds; closures capture bind-time ctx (`lens.lua:21`) → after `H`/`L`, `s/t/n/b/c` (and clobbered `m`) run against the **previous card's symbol** until re-bind.

**D10 — LOW.** Hand-list drift: help `m`="who writes" (`hud.lua:304,328`); "Panel … p follow/pin" (`hud.lua:312`) — `p` is a noop (`:269`), pin-`p` lives in docview; `README.md:77` pre-role-swap; `<leader>dm` absent from README keys.

**D11 — LOW (structural root).** Four parallel enumerations of the op set — registry, leader maps, HUD keys+footer+help, README; D1/D4/D5/D10 are the accumulated drift.

**D12 — INFO.** Renderer split `menu.open` vs `vim.ui.select` — deliberate for browse (fzf); asmflags could go either way; nodemodel heal is a modal confirm.

## § Unification recommendation

**One registry, one runner, one renderer; every popup/key/footer/help DERIVES** (the codebase's H15/H18 registry discipline + the §9 METHOD).

**Registry deltas:** rows gain `id` (stable key) · `key` (single-letter hotkey; lens actions fold in as rows: `m` mutations, `s` false-sharing, `t` density, `n` notes, `b`/`c` cascade; load-time assert rejects same-key overlapping-`types`+`when` rows — the clobber class becomes a caught error) · `when(ctx)` **signature change** (explicit ctx: buf/row0/kind/symbol — HUD passes tracked source ctx, dm passes cursor ctx; kills D2 by construction) · `types` re-keyed to the **tag vocabulary** with ONE treesitter-kind→tag-type map at the resolver seam (kills D3); field/symbol stay an extra axis · `writes` unchanged · NO per-surface visibility flags (speculative; `when(ctx)`+`types` cover every current case).

**Runner + renderer:** new `actions.run(row, ctx)` does the restore-source-window dance centrally (the ONLY reason the HUD wraps — move it and the wrap/D1 is structurally impossible); `menu.open` keeps its contract but callers pass **rows, never re-shaped copies**; title formats centrally (kills D7); footer + help "Actions" sections **generate from rows** (kills D10/D11 action-portion); nav keys stay hand-listed. D6: suppress BufLeave-close while a child menu is open, or re-open on menu close — operator call.

**Converts to rows:** the 5 lens key-actions; board `s`=compare (bound from its row, collision-checked). **Cannot unify:** browse pickers (fzf-filterable dynamic data — deliberate) · asmflags picks + heal confirm (data-chooser/modal) · dashboard/docview/asm-view local nav keys · docview chooser ITEMS (data; but the call gains `palette` + optional anchor → closes D8).

**Migration order:** (1) `actions.run` + explicit-ctx `for_type(ctx)`/`when(ctx)` — closes D1+D2, ~15 lines net; (2) `key` column + collision assert + lens-row fold — closes D4/D5/D9; (3) tag-vocab type unification — closes D3; (4) footer/help/README derivation — closes D10/D11; (5) docview opts + D6 decision; (6) commit the missing headless tests (the cd971ac proofs, made permanent).

**Option matrix:** A minimal-patch (copy `writes` through) — rejected, class recurs · **B registry-derived everything — recommend** · C vim.ui.select renderer — rejected (loses number-run/tier column/docking) · D keymap-as-SSoT — partial-adopt only (desc set FROM rows, one-way).

**Blast radius of B:** `actions.lua`, `menu.lua`, `hud.lua` (_menu, map_action, footer, help), `init.lua`, `lens.lua` + 5 lenses, `panel.lua:170-175`, `docview.lua:207`, `README.md`; zero existing tests touch these seams (itself a finding).

## § Refute spots (for the paired a-class)

1. **D1 direction** — operator note vs code+diff; refute by headless build of both menus off a fixture; if the note is right, something moved post-screenshots.
2. **D6 realism** — minimal facsimile repro; the full stack (timers, on_close, guicursor munging) could differ.
3. **D4 bug-vs-design** — help documents m=mutations on fields; if intended, the fix is a key-space decision, weakening the collision-assert framing.
4. **Type-vocab extension timing** — REGISTRY/TYPE facets unbuilt (D-334); maybe function/struct+universal suffices until they land.
5. **`when(ctx)` signature** is the one breaking API — grep out-of-tree lens consumers (the `_TEMPLATE.lua.txt` contract) before calling it free.

## § Open questions

1. Should the derived-writer row also offer on REGISTRY units (`tagwriter.lua:33` suggests it works)?
2. D6 disposition: suppress-close-while-child-open, or re-open after?
3. Is m-on-field=mutations intended? If yes, which key gets the menu there?
4. dm anchor preference when board AND followcard are both open (`init.lua:242` hard-orders panel)?
5. The ideas-§9(iii) attribution swap — one-line correction when the fix lands.
