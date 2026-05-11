# Public Release v2.0 — Strategy + Plan (2026-04-29)

## Current state

| Repo | Visibility | Architecture | Active version |
|---|---|---|---|
| `Jennyfirrr/tick-trader-percore` | Private | Sharded (v5.x) | v5.1.8 |
| `Jennyfirrr/FoxML_Trader` | Public | Legacy single-core | v1.0.x |

The public repo is on **legacy architecture** — not 1:1 with the sharded
work you've been shipping. Anyone reading FoxML_Trader is looking at
2025-era code, not the per-core sharded engine you actually built.

## The decision space

Three paths, with honest tradeoffs:

### Path A — Stay private, public gets stale

Keep shipping v5.x privately. Let FoxML_Trader v1.0.x sit. Eventually
deprecate it.

- ✅ Zero ongoing maintenance burden
- ✅ Alpha + ML model files stay private by definition
- ❌ Career portfolio piece is your *old* legacy code — undersells the
  engineering you actually do
- ❌ When recruiters / managing directors look at FoxML_Trader, they
  see 2025 code, not the prop-shop-pattern v5.x

### Path B — Open-source the architecture, keep alpha private

Promote the v5.x sharded code to a new public repo (`FoxML_Trader_v2`
or similar). Strip alpha-generating cfg + ML model files. Engine
architecture is public; specific tunings + trained models stay private.

- ✅ Portfolio piece reflects current skill (prop-shop-grade engine)
- ✅ Alpha edge preserved (no model files, no specific cfg tunings)
- ✅ Contributes to open-source community (rare to see HFT-pattern code)
- ⚠️ AGPL-3.0 license already on the codebase — anyone who modifies
  must share back. Right license for this kind of release.
- ⚠️ Maintenance: need to keep public in sync with private periodically
- ⚠️ Some small adjustments needed (default cfg should be deliberately
  neutral, not your tuned values)

This is the path most prop-shop-adjacent OSS takes (e.g. Alphalens,
Linnet, RustQuant). Engine architecture isn't the edge — alpha + data
+ execution latency are. Public engine ≠ giving away edge.

### Path C — Open-source everything as-is

Make `tick-trader-percore` itself public. AGPL-3.0 already on the headers.

- ✅ Maximum transparency, single source of truth
- ❌ Your specific cfg tunings (TP/SL %, regime thresholds) become
  public — anyone can copy them into their own engine
- ❌ Your ML model files (if you don't `git rm` them first) leak training
  signal
- ❌ `engine.cfg` is gitignored but `engine.cfg.example` ships with
  defaults — those defaults reflect your design choices

Doable but riskier than B. Only worth it if "transparency over edge" is
your value statement (some research labs choose this).

## My recommendation: Path B

Reasoning:
1. You're early in alpha-hunt territory — edge is the scarce resource,
   protect it.
2. The engine architecture itself is genuinely impressive (per-core
   sharded, parity-verified, single-writer rules) and recruitment-grade.
3. The split between "engine" and "alpha" maps cleanly onto your existing
   directory structure: code is public, `.cfg` + `models/*.bin` + `data/`
   stay private (already gitignored).
4. AGPL-3.0 means competitors who use your code must share their
   modifications back — rare to see HFT firms touch AGPL for that
   reason. Free defensive moat.

## Implementation plan (Path B)

### Step 1 — Audit what's safe to publish (~1h)

Walk through the repo and classify:

| Category | Status | Action |
|---|---|---|
| `CoreFrameworks/` | All headers | PUBLIC — engine architecture |
| `Strategies/` | All headers + private/ | PUBLIC — strategy *interfaces* are public, but check if `private/EmaCross.hpp` has tunings we want hidden |
| `DataStream/` | Binance integration | PUBLIC — adapters are well-known patterns |
| `FixedPoint/`, `MemHeaders/` | FPN, allocators | PUBLIC — generic infrastructure |
| `ML_Headers/` | RollingStats, Inference | PUBLIC — but check ConfidenceScore for any embedded thresholds that leak signal |
| `GUI/` | Dear ImGui panels | PUBLIC |
| `Backtest/` | Engine + suite | PUBLIC |
| `tests/` | controller_test | PUBLIC |
| `DOCS/` | Changelogs + CLAUDE_*.md | PUBLIC — but redact any references to specific GSR / firm conversations |
| `engine.cfg.example` | Default cfg | PUBLIC — but reset to NEUTRAL defaults (1% TP, 0.5% SL, etc.) not your tuned values |
| `engine.cfg` (gitignored) | User's tuned cfg | PRIVATE — gitignore stays |
| `models/` (gitignored) | ML weights | PRIVATE — gitignore stays |
| `data/BTCUSDT/*.csv` (gitignored) | Tick history | PRIVATE — gitignore stays |
| `plans/` (gitignored) | Working plans | PRIVATE — gitignore stays |

**Action items found**:
- `engine.cfg.example` defaults — verify they're truly neutral, not your tuned values
- Check `Strategies/private/EmaCross.hpp` — is the contents alpha-flavored?
  If so, simplify to a textbook EMA cross before publishing
- DOCS/CLAUDE_INVARIANTS.md — references "v4.7.19 Stats panel showed
  exits: 2 (7 fills)" etc. — these are fine, they're bug post-mortems
- DOCS/changelogs/ — review for any firm-name mentions

### Step 2 — Create public repo (~30 min)

```bash
# On a clean clone
git clone tick-trader-percore tick-trader-public
cd tick-trader-public
git checkout main  # or your default branch

# Strip private stuff (defensive — most already gitignored)
rm -rf engine.cfg controller.cfg models/ data/ plans/ logging/ runs/
git add -A && git commit -m "redact private cfg + plans"

# Verify with a fresh clone-like state
git clean -fdx -e .git
ls  # should be only public-class files

# Init new remote
gh repo create Jennyfirrr/tick-trader-public --public --source=. --remote=public-origin
git push public-origin main
```

### Step 3 — Initial release (~30 min)

```bash
# Tag + release
git tag v2.0.0
git push public-origin v2.0.0
gh release create v2.0.0 \
  --title "v2.0.0 — per-core sharded architecture <3" \
  --notes "First release of the per-core sharded architecture (engine v5.x). See DOCS/CHANGELOG.md for the full evolution from v1.x legacy single-core to v5.x sharded prop-shop-pattern."
```

### Step 4 — README + intro material (~1h)

Write a public-facing README that:
- Explains what the engine IS (single-symbol HFT-pattern paper trader,
  not a black-box money printer)
- Hot-path latency claim with how to measure it
- Architecture overview (link to CLAUDE.md + CLAUDE_INVARIANTS.md)
- Build instructions
- "How to use this responsibly" — disclaimer that defaults are neutral,
  past performance doesn't predict future, AGPL-3.0 implications
- "How this relates to FoxML_Trader v1.x" — explain that v1.x is legacy,
  v2.x is the current architecture

### Step 5 — Sync workflow (ongoing)

Decide cadence: do you push to public on every minor version bump, or
batched?

Recommended: **push on every X.Y.0 minor bump** (so v5.2.0 → public,
but not v5.2.1 patches). Patches catch up at next minor.

Workflow:
```bash
# In private repo, after a minor version ships clean
git remote add public public-origin-url
git push public main:main
```

Or maintain a `public-mirror` local branch that's a redacted copy of
main, and only push that. Slightly safer (catches accidental leaks
before they go remote).

## Risks + mitigations

| Risk | Mitigation |
|---|---|
| Accidentally push private cfg / models / data | Keep `engine.cfg` etc. gitignored; verify with `git ls-files --error-unmatch engine.cfg` (should fail) before push |
| Specific tuning values leak via DOCS / changelog references | One-pass redact-review before initial v2.0 push; sed `/0\.[0-9]*%/p` to spot percentage-mentions |
| AGPL-3.0 misunderstood as MIT — competitors take + don't share back | License header on every file (already there); README explicitly states AGPL implications |
| Maintenance burden grows (issues, PRs, security advisories) | Use GitHub repo settings: "Issues only enabled for security advisories" if you don't want feature issues |
| Future you wants to re-private | Hard once published. Plan accordingly. |

## Versioning across repos

Public repo follows v2.x.y where:
- v2.x maps to whatever private v5.x was at the snapshot
- v2.0.0 = private v5.1.8 snapshot
- v2.1.0 = next minor private bump (v5.2.0?)
- Public patches happen for security only (not every private patch)

OR: just use the same version numbers (public v5.1.8 = private v5.1.8).
Cleaner mental model. Recommend this.

## Out of scope

- Multi-symbol support
- Real-money live deploy guidance (separate plan)
- Documentation tutorials
- Maintenance contracts / support
- A "lite" build for folks who want to embed it without ImGui

## Decision needed before starting

1. **Path A, B, or C?** (recommend B)
2. **New repo name?** Suggest `tick-trader-public` or `foxml-trader-v2`
3. **Versioning: same numbers as private, or fresh v2.x.y?** (recommend same)
4. **What to do with FoxML_Trader v1.x?** Archive? Deprecate with link to
   new repo? (recommend archive with README pointer)
