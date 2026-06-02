---
type: meta-discipline
stage: 3-first-canonical
established: 2026-06-02
tags: [handoff, workflow, doc-discipline, machine-portable, instantiate, ecosystem]
surface: [handoff, accept-handoff, tools]
status: active
sister_specs: [symlinked-tool-host-root-resolution, structural-enforcement-when-memory-insufficient, meta-anti-pattern-index]
---

# Handoff active-state machine (`status: {active, superseded}`)

How no-arg `/accept-handoff` knows WHICH handoff is the live one. An explicit
frontmatter state field + a singleton guard, replacing fragile filesystem-mtime
resolution. Codified 2026-06-02 (`.E` #11 session wrap).

## The law

> Every handoff carries a frontmatter `status:` field. **At most ONE handoff is
> `status: active`** at any time (globally, across `plans/**/handoffs/`). No-arg
> `/accept-handoff` resolves the live handoff by that tag. The writer flips the
> prior active → `superseded` when it writes a new one.

States:

| `status:` | meaning |
|---|---|
| `active` | THE one live handoff — what no-arg `/accept-handoff` picks up |
| `superseded` | a prior handoff a newer one replaced (still readable; just not the entry point) |
| *(absent)* | legacy / untagged ≡ **inactive** — zero retrofit of pre-existing handoffs |

## Why (the failure it prevents)

`/accept-handoff` used to resolve no-arg pickup by **most-recently-modified file
mtime**. Fragile: a `git checkout` / `pull` can reset a whole batch of file mtimes
to a single timestamp (observed 2026-06-02 — ~60 handoffs all stamped
`2026-05-19_00:42:38` by a past git op). If such a reset ever lifts an OLD handoff
above the real one, no-arg pickup silently resolves the WRONG handoff — and a
handoff is exactly the artifact a fresh, context-poor session trusts blindly.

The explicit tag is **deterministic** and survives mtime churn. The guard makes
"exactly the live one" TRUE rather than hoped-for.

## The one design choice that matters: supersede-on-WRITE, not inactive-on-consume

The transition `active → superseded` fires when a NEWER handoff is **written**,
NOT when the old one is **read/parsed** by `/accept-handoff`.

Consume-flip (the tempting version) breaks re-pickup:

> Pick up handoff H → start the work → session dies mid-way (context runs out)
> **without writing a new handoff**. Next session must pick up H *again* — it's
> still the live work. If parse already flipped H to `inactive`, no-arg
> `/accept-handoff` now finds **zero active** → broken.

So a handoff stays `active` until a successor **supersedes** it. `/accept-handoff`
is **read-only** (no commit-on-pickup, idempotent re-pickup); the writer owns the
state transition, where the knowledge ("I am replacing the prior handoff") lives.

## The three wired surfaces

1. **Writer — `/handoff` Stage 6.0** (+ `/close-session`'s handoff step): before
   writing the new `active` handoff, flip any current `active` → `superseded`
   (`grep -rl '^status: active' <sprint>/handoffs/*.md`, Edit each). New handoff's
   Stage-5 frontmatter template carries `status: active`.
2. **Resolver — `/accept-handoff` Stage 1**: explicit `<path>` arg wins; else the
   `status: active` handoff (exactly 1 → use it; 0 tagged → fall back to mtime for
   the transition era; >1 → ERROR, surface all, don't guess).
3. **Guard — `tools/check_handoff_active_singleton.py`**: HARD in
   `check_session_docs.sh` (so `/close-session` + `/accept-handoff` + `/sync-workspace`
   all fire it). Counts frontmatter `status: active` across `plans/**/handoffs/`
   (skips `_TEMPLATE*` / `README.md`; body prose excluded). `>1` = red build; `0` =
   advisory (sprint between handoffs, or pre-adoption). `--selftest` teeth-proof.
   Machine-portable (`.absolute()` + env override, never `.resolve()`) so it runs
   when symlinked from the private workspace into the host — sister
   `symlinked-tool-host-root-resolution.md` (LANDMINE 5).

## Sister idiom — this is not new infrastructure

A `status:` field on a doc, read mechanically, is the SAME idiom as the
decision-log `<!-- STATUS: decided -->` sentinels that `/accept-handoff` Stage 4.6
already reads. The guard-as-permanent-leverage framing is
`feedback_guards_compound_enforcement_is_leverage` (the frontmatter discipline is
the one-time habit; the guard protects the whole class forever).

## Novel alternative considered — a pointer file

A single `handoffs/.active` file (or `LATEST` symlink) naming the live handoff
gives the ≤1 invariant *structurally* (can't point to two) with no guard needed.
**Rejected:** it doesn't travel WITH the doc (status-in-frontmatter is visible the
moment you open the handoff); a stale pointer to a renamed/deleted file is its own
failure mode; and a second sync-able artifact is more drift surface, not less.
Frontmatter + a singleton guard wins.

## Ecosystem / template

Generalizes verbatim into every `/instantiate`'d project: the template ships
`check_handoff_active_singleton.py` + the `status:` field in its handoff/
accept-handoff skill skeletons, so robust handoff resolution is a property of the
workflow, not of this one repo. Part of the "living syncable workspace" method.
