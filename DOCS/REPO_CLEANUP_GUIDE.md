# Repo Cleanup Guide (v0.1.0 transition)

**Audience:** Operators familiar with v5.X codebase; transitioning to v0.1.0+ (per `.E` sub-sprint).

**Per D-9 + D-61:** No backwards compat. Clean break. Legacy paths archived to `legacy/` directory; new architecture replaces.

This guide documents what's deprecated, what's archived, what stays, and the operator migration path.

---

## What's archived to `legacy/`

The following code paths are archived at `legacy/` at `.E.1`/`.E.2`. They no longer build by default; they're preserved for reference.

### `legacy/engine_gui/` (at `.E.2`)

- Dear ImGui-based GUI code
- SDL2 + OpenGL integration
- engine_gui binary
- GUI-specific cfg fields

**Replaced by:** `fox-tui` (notcurses-based; reads mmap state) + `fox-cli` (UDS command channel).

**Rationale:** Per `meta-disciplines/gui-deprecation-decision-rationale.md`. GUI couples engine binary to graphics dependencies; can't run headless; single-viewer.

### `legacy/foxml_suite/` (at `.E.2`)

- foxml_suite binary
- Integrated ML training GUI

**Replaced by:** `foxml-train` CLI tool + Jupyter notebooks (for interactive exploration).

**Rationale:** Production ML training should be scriptable / cron-driven. Jupyter handles interactive exploration. CLI is canonical for production.

### `legacy/central_drainer/` (at `.E.1`)

- Run.hpp:1455 drainer lambda body
- DrainWithSubmit / DrainPostFill / OMS_DrainSubmit / OrderManager_Tick (drainer-only-caller forms)
- Drainer-specific data structures

**Replaced by:** Per-node slow-path absorption. Each per-node owns its own OMS submit + fill consume + post-fill bookkeeping.

**Rationale:** Class 26 surface (cross-core iteration in drainer) eliminated structurally. Per `framework-patterns/global-aggregator-readonly-pattern.md`.

### `legacy/single_core/` (at `.E.1`)

- Single-core LIVE mode (deprecated since v5.0; finally deleted)
- Legacy `engine_arch = centralized`

**Replaced by:** Per-node sharded architecture (current; per-node at `.E.1`).

**Rationale:** Long-deprecated; final cleanup at `.E.1`.

### Legacy `engine.cfg` monolithic parser path

- Old single-file engine.cfg parser
- Hardcoded cfg sections

**Replaced by:** Hierarchical config layout per `framework-patterns/cluster-node-hierarchy-filesystem-layout-pattern.md`.

**Migration:** One-shot tool `fox-migrate-cfg` converts old engine.cfg → new hierarchical layout. Operator runs once.

---

## What's renamed

| Old | New | Surface |
|---|---|---|
| `core` (trading unit) | `node` | All code + docs |
| `state.cores[i]` | `state.nodes[i]` | All consumers |
| `MAX_CORES` | `MAX_NODES` | Limits.hpp |
| `CoreContext` / `CoreState` | `NodeState` / `NodeContext` | Struct types |
| `FOREACH_PER_CORE_CFG_FIELD` | `FOREACH_PER_NODE_CFG_FIELD` | X-macro registry |
| `engine` binary | `fox-engine` (headless service) | Build target |
| `engine_gui` binary | (archived; replaced by `fox-tui`) | Build target |
| `foxml_suite` binary | (archived; replaced by `foxml-train`) | Build target |
| `core_N_strategy` cfg | `node_N_strategy` (via per-node folder) | cfg field |

**Internal note:** "core" as CPU architecture concept (e.g., "CPU core") is preserved. Disambiguation: "CPU core" when discussing hardware; "node" when discussing trading unit.

---

## What stays unchanged

- **FoxLIB primitives** — header-only library; unchanged
- **FPN_Binary<F> fixed-point math** — H4 + core accounting; unchanged
- **Branchless hot path discipline** — H7; unchanged
- **H1-H20 invariants** — all preserved (H15, H17, H18, H19, H20 added at v5.15.5)
- **Per-node sharded architecture** — extended to per-node + per-cluster (additive)
- **X-macro registry pattern** — extended with FOREACH_EXCHANGE + FOREACH_SUBACCOUNT
- **Strategy implementations** — per-strategy logic unchanged (just per-node container)
- **ML feature compute** — per-cluster feature registry (per-exchange variant)
- **Stamp body format** — extended with cluster_id + sub_account_id + variant_id + software_version (byte-preserved per H9)
- **Test framework** — controller_test extended; not replaced
- **Audit-driven discipline** — preserved + extended at sub-sprint scope (`.E.0`)

---

## Operator migration workflow

For operators with existing v5.X engine.cfg + workflow:

### Step 1: Backup current state

```bash
cd /home/caramel/code/FoxML_Trader_v2
git tag pre-v0.1.0-migration   # rollback anchor
cp engine.cfg engine.cfg.backup
cp -r models/ models.backup/
```

### Step 2: Run config migration tool (at `.E.2`)

```bash
fox-migrate-cfg --from engine.cfg --to configs/
# Output: configs/clusters/binance/{cluster.cfg, credentials/, nodes/node_*/}
```

Validates result against original; reports any fields that couldn't be migrated automatically.

### Step 3: Provision sub-accounts on Binance (at `.E.5`)

Per `framework-patterns/foreach-subaccount-meta-registry-pattern.md` + `DOCS/OPERATOR_MANUAL.md`:

1. Binance UI → Sub-Accounts → Create N sub-accounts
2. Create API keys per sub-account (trade-only; IP-restricted; NO withdrawal)
3. Set env vars: `BINANCE_SUB0_API_KEY`, `BINANCE_SUB0_API_SECRET`, etc.
4. Populate `configs/clusters/binance/credentials/sub_*.cfg`

### Step 4: Install systemd unit (production)

```bash
sudo cp installation/fox-engine.service /etc/systemd/system/
sudo systemctl enable fox-engine.service
sudo systemctl start fox-engine.service
```

### Step 5: Install fox-tui + fox-cli

```bash
# Optional: AUR package (future)
yay -S fox-trader-suite

# OR manual install
sudo cp bin/fox-tui bin/fox-cli bin/foxml-train /usr/local/bin/
```

### Step 6: Verify operation

```bash
# Local
fox-tui
# Should display global dashboard + per-cluster panels

# Remote (laptop)
ssh -L /tmp/fox.sock:/var/run/fox/engine.sock server
fox-tui --socket /tmp/fox.sock

# Test command
fox-cli pause-node binance/node_0
fox-cli resume-node binance/node_0
```

---

## What if operator wants to roll back to v5.X?

Rollback procedure:

```bash
cd /home/caramel/code/FoxML_Trader_v2
git checkout pre-v0.1.0-migration
cp engine.cfg.backup engine.cfg
cp -r models.backup/* models/
./build.sh test
./engine                    # v5.X binary still works
```

Note: rollback loses any state accumulated post-migration. AGPL allows this freedom.

---

## Public vs private separation (post-migration)

| Layer | Public (AGPL on GitHub) | Private (gitignored) |
|---|---|---|
| Engine code | YES | - |
| FoxLIB | YES | - |
| Strategy implementations | YES | - |
| ML feature compute | YES | - |
| `configs/engine.cfg` template | YES (skeleton) | - |
| `configs/clusters/binance/cluster.cfg` template | YES (skeleton) | - |
| `configs/clusters/binance/credentials/` | - | YES (gitignored) |
| Actual API keys / secrets | - | YES (env vars) |
| Trained models | - | YES (gitignored) |
| Runtime audit logs | - | YES (host-local) |
| Operator personal cfg (TUI keybindings) | - | YES (gitignored) |

---

## Naming considerations (deferred decision per D-62)

Operator may rename repo from `FoxML_Trader_v2` to `FoxML_PortfolioManager` (or similar) at v0.1.0 ship close. Per D-62, this decision is deferred to clean version boundary.

If renamed:
- GitHub URL changes
- Documentation references update
- AGPL attribution check
- Migration plan for clones / forks / stars

Until then: repo name stays as-is for `.E` sub-sprint duration.

---

## Future considerations

- Public usage guide (per operator clarification 2026-05-28): substantial public-facing doc explaining how to configure stuff + config templates. **DEFERRED to post-`.E` separate session.**
- AUR packaging (`fox-trader-suite` package): optional; lands when operator prioritizes.
- Multi-region deployment: documented as architecture-supported; no code at v0.1.0.

---

**End of REPO_CLEANUP_GUIDE.md v1.0** (2026-05-28).
Updated as cleanup phases land.
