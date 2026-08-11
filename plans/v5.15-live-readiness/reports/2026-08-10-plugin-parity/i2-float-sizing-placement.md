---
type: agent-report
status: FROZEN — verbatim agent output, saved at receipt (operator directive 2026-08-10)
directive: plugin-parity fleet — float/window sizing + placement conventions
agent_class: i-class
task: I-2 — float sizing/placement parity census
delivered: 2026-08-10
disposition_register: ../../plan_checks/2026-08-10-plugin-parity-fleet-register.md
---

# FLOAT/WINDOW sizing + placement census — fox-symdeps.nvim (`feat/hud-robustness`) — VERBATIM

Scout notes: no tool in `DOCS/TOOLS.md` covers a Lua float census (verified) → grep/read discovery is correct. No plugin `DOCS/DECISIONS.md` entry pins sizing/placement (verified) — nothing below re-litigates a settled fork. Three behavior claims verified by headless-nvim probe: **P1** an oversize float is width-clamped by nvim and `wrap` defaults ON in floats (150→98 on a 100-col editor); **P2** a bottom-edge float keeps its requested height — overflow rows clip invisibly; **P3** a `relative="win"` float survives its anchor window's close (position freezes).

## § Inventory

All paths under `tools/plugins/fox-symdeps.nvim/lua/fox-symdeps/`.

### Floats (7 `nvim_open_win` float sites)

| # | Surface | Site | Placement | Size derivation | Caps/clamps | Border/title | Close | Focus |
|---|---|---|---|---|---|---|---|---|
| F1 | **Chooser menu** (palette `<leader>dm` · HUD `m` · docview chooser) | `menu.lua:54`; placement `:19-24` | `relative="cursor"` row1/col0, OR docked `relative="win"` row1/col2 into `anchor_win` | Content-driven: width from `#title+6`/16 to max `strdisplaywidth+2` (`:31-42`, +1 legend row); height `=#lines` (`:50`) | **NONE** on either axis; wrap never disabled | minimal + rounded, title centered, optional palette border hl | `q`/`<Esc>`/`h` + `BufLeave`/`WinLeave` once; guicursor hidden | enters |
| F2 | **HUD float card** (`<leader>dd`) | `hud.lua:215-225` | `relative="cursor"` row1/col2 | **FIXED 72×28** (`:219-220`) — the only fully-fixed float | None; wrap+linebreak+breakindent shift:2 overflow strategy (`:233-236`) | minimal + rounded, centered `FoxSymdepsTitle`, family winhighlight | `q`/`<Esc>` + `BufLeave` once, float-mode only (`:272-278`) | enters; cursor hidden |
| F3 | **Help float** (`?`) | `hud.lua:337-343` | `relative="editor"`, centered, `max(0,…)` floors | Content-driven both axes | None (~36 rows — clips on short terminals per P2) | minimal + rounded, centered title | `q`/`<Esc>`/`?`; **no focus-loss autocmd** | enters |
| F4 | **Dashboard** (`<leader>dw`) | `dashboard.lua:77-87` | `relative="editor"`, centered | `W=min(96, 82% cols)`, `H=min(40, 82% lines)` | Caps 96×40 | minimal + rounded, centered; wrap+breakindent | `q`/`<Esc>` + `BufLeave` once; cursor hidden | enters |
| F5 | **Doc reading float** (docview) | `docview.lua:100-106` | `relative="editor"`, right-edge, ≈centered−1 | `w=min(110, max(60, 55% cols))`, `h=72% lines` | floor 60 + cap 110 width; height %-only | rounded, **title_pos="left"**, **no `style=minimal`**, **no FoxSymdeps winhighlight** — REAL buffer, deliberate | **`q` only**, `p` promotes to pin, `WinClosed` clears maps; **no `<Esc>`, no focus-loss close** | enters |

### Splits

| # | Surface | Site | Size derivation | Conventions |
|---|---|---|---|---|
| S1 | **Panel strip** (board · follow card · compare companion) | `hud.lua:206-213` via `resolve_placement` `:56-62` | aspect ≥2.2 → `split right, width=min(60, 40% cols)` + `winfixwidth`; else `split below, height=max(12, 40% lines)` + `winfixheight` | winbar title; `q`/`<Esc>`; persistent; **unit-tested** `tests/test_hud_placement.lua` |
| S2 | **Asm flag-diff pane** | `asmview.lua:107` | `split below, height=min(#lines+1, 26)` | winbar; `q` + `f` re-pick; no Esc |
| S3 | **1:1 asm explorer** (`<leader>de`) | `asmexplorer.lua:239-241` | `rightbelow vsplit` — no size control (50/50) | winbar; focus returned to source; `q` + source BufWipeout/BufDelete + toggle-close |
| S4 | **Doc pin split** | `docview.lua:80-89` | `botright vsplit`, `width=max(60, 42% cols)` — floor, no cap, **no winfixwidth** | Native `:q` lifecycle — deliberate |
| S5 | **Quickfix** (`Q`) | `hud.lua:45-50` | `botright copen` default | `q` → cclose |

### Native choosers (`vim.ui.select` — deliberate: "so your fzf" `browse.lua:49`)
`asmflags.lua:46,49` · `browse.lua:31,58` · `nodemodel.lua:251`.

### Placement-policy constants (scattered)
Aspect **2.2**: `hud.lua:58` AND `panel.lua:69` (duplicated) · compare gate **cols≥140 / lines≥36**: `panel.lua:67-71` · cockpit **MIN_WIDTH=120**: `cockpit.lua:8` · bytemap width gate **≥69**: `hud.lua:571-573` · footer manual wrap: `hud.lua:707-727`.

`compose.lua`: window-free (confirmed). Menu-chooser cohort: `init.lua:243-247` (palette, anchor board/follow), `hud.lua:867-871` (HUD `m`, anchor HUD), `docview.lua:207` (**no anchor, no palette**).

## § Divergences

1. **[HIGH] Chooser cramping is structural; only the symptom was patched.** `menu.lua:31-42,50` computes width purely from content, no editor clamp, never `nowrap`; per P1 nvim clamps and float wrap defaults ON → long labels wrap while height stays `#lines` → rows pushed out of view. The docview label-shortening fixed labels only — any future long-label chooser regresses. Height equally unclamped (P2 silent clip).
2. **[MED] Anchor-dock has no fit-to-anchor logic** (`menu.lua:21`): right strip ≤60 wide at the editor's right edge → wide menus spill left over the code window; tall menus docked into the 12-line bottom strip clip below.
3. **[MED] HUD float is the sole fully-fixed surface (72×28)** — clamps+wraps under ~76 cols, bottom rows clip (P2), under-fills 4K (north-star §6 "fill available space").
4. **[MED] Absolute caps ad hoc, no shared policy:** strip 60 / dashboard 96×40 / docview 110 / card 72 / pin uncapped — five answers to one question; §6 implies *more panes, not wider panes*.
5. **[LOW-MED] Close-key + focus-loss conventions split three ways:** `q`+`<Esc>`+focus-loss (menu/HUD/dashboard) · `q`+`<Esc>` persistent (panels) · `q`-only no-focus-loss (docview/asmview/asmexplorer). Help float has no focus-loss close → click-away orphans it (drift, not choice). Docview's `q`-only half-deliberate (buffer-local `<Esc>` on a REAL buffer would leak).
6. **[LOW] Visual family breaks:** `title_pos="left"` docview-only; docview float border outside the family hl; docview chooser missing `palette` → untinted (`init.lua:245`, `hud.lua:869` both pass one).
7. **[LOW] Pin split sets width without `winfixwidth`** (`docview.lua:88`) — first `wincmd =` destroys the 42% sizing; the sibling strip sets its fix (`hud.lua:213`).
8. **[LOW] Guard-shape asymmetry:** right = `min(60, 40%)` (cap, no floor) vs below = `max(12, 40%)` (floor, no cap) — 113-line portrait yields a 45-row strip (test-pinned, currently *intended*).
9. **[LOW] Threshold SSoT:** aspect 2.2 duplicated; roominess constants scattered (120 / 140+36 / 69).
10. **[INFO] Two chooser families by design** (menu.lua rejects `vim.ui.select` for action menus; pickers ride fzf). Borderline: asmflags' fixed A/B pick is menu-shaped.
11. **[INFO] Currency: §9(iii) appears CLOSED at HEAD** — both invokers build via `actions.for_type` and rows carry `writes`; the ideas note is unticked. *(Orchestrator note: I-1/I-3 adjudicate — the divergence IS live via the hud re-wrap dropping fields; I-2 read the call sites but not the item-shape rebuild.)*
12. **[INFO] Float-HUD `m` menu docks to a window its own BufLeave is closing** — P3: float survives, frozen; cosmetic.

## § Helper recommendation + migration order

**Option matrix:** A per-site fixes — rejected (5 formulas + 3 conventions stay divergent) · **B new `ui.lua` token helper — RECOMMENDED** (`ui.dims(role, content_wh, opts)` + `ui.open(buf, role, opts)`; policy constants homed; right-sized for ~9 sites; grows into C) · C declarative SURFACES registry with conventions-test — not now (7 floats < framework threshold; B's token table is its seed) · D extend menu.lua — rejected (menu is a WIDGET; placement is the layer beneath).

**Tokens:** `small-chooser` (content-driven both axes then clamp `w ≤ min(content, editor−4)`, `h ≤ editor−4`; **nowrap**; docked variant clamps to `anchor_width−4`, falls back to cursor placement when anchor < ~40 cols) · `card` (72×28 preferred, editor-clamped, or responsive — OQ3) · `reading-pane` (docview's formula retained — the best in the file; centered variant serves help; real-buffer rule codified `q`-only) · `board-card` (`resolve_placement` moves verbatim + shim/test-repoint; shared constants `ASPECT_WIDE=2.2`, `COCKPIT_MIN=120`, `COMPARE_MIN={140,36}`) · `full-compare` (dashboard + §6 dual-panel tomorrow).

**Migration order (blast-radius ascending):** ① menu → `small-chooser` (closes D1+D2, the live complaint) → ② help float + dashboard (D5-orphan, D6) → ③ docview float → `reading-pane` → ④ HUD float → `card` (OQ3) → ⑤ placement relocation + shared constants (D8/D9) → ⑥ pin `winfixwidth` (D7).

**Should NOT migrate:** asmexplorer vsplit (deliberate 50/50 1:1 pane) · quickfix · `vim.ui.select` sites · asmview's cap-26 pane.

**Docview specifically:** chooser = `small-chooser` (keep shortened labels; the answer to "should this be bigger" is **clamp + nowrap so a content-driven box always fits**, not a bigger fixed box); doc float = `reading-pane` with current formula.

## § Open questions (operator calls)

1. **Fill-vs-readability (§6):** lift caps on ultrawide, or spend surplus on more panes (I-2 reads north-star as the latter)?
2. **Docview float focus-loss:** survive-on-leave, or dismiss + `p`-pin as the persistence path? *(Orchestrator: operator answered same evening — dismiss-on-leave; pin owns persistence — ideas §11(v).)*
3. **HUD card:** fixed-clamped or responsive?
4. **Bottom-strip ceiling:** cap portrait strip (~20-24 rows) or keep test-pinned 45-on-113?
5. **Codify "real-buffer floats are `q`-only"** as a token rule?

## § Refute spots (for the paired a-class)

1. D1's mechanism probe-verified but the observed cramp may have needed cursor-near-right-edge — refute by reproducing with pre-shortening labels at mid-screen.
2. `nowrap` truncates (no native ellipsis) — wrap+grow-height is computable and arguably more honest.
3. `resolve_placement` relocation vs its unit-test contract — shim vs repoint, SSoT smell.
4. B-over-C: the 0.5 roadmap surface count may cross the framework threshold sooner than judged.
5. D4's framing: each cap may be a deliberate undocumented readability choice — the right fix may be NAMING the caps in one home, not changing values.
