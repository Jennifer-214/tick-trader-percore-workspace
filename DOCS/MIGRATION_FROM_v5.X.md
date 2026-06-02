# Migration from v5.X to v0.1.0+

**Audience:** Operator running existing v5.X engine; transitioning to v0.1.0+ post-`.E` sub-sprint.

**Companion to:** `DOCS/REPO_CLEANUP_GUIDE.md` (codebase-side changes). This doc is OPERATOR-WORKFLOW side.

---

## Why migrate

v0.1.0 is the result of `.E` sub-sprint (~25-35 days engineering). Brings:
- Per-node sub-account economic isolation
- Multi-exchange substrate
- Headless service architecture (24/7 operation; SSH-administered)
- io_uring + kTLS for kernel-bypass-lite I/O
- WS-API persistent connections (~15-25ms/submit saved)
- Event-sourced O(1) aggregator (sub-fill kill switch latency)
- Strategy hot-reload via dlopen
- Comprehensive operator-facing documentation

Per D-9 (backwards-compat-not-default-concern): clean break. v5.X cfg won't parse with v0.1.0+.

---

## Migration timeline (operator-recommended)

**Total: ~2-4 hours one-time operator work + 1-2 weeks staged deployment.**

| Phase | Time | Action |
|---|---|---|
| Pre-prep | 30 min | Backup current state; document current operation; plan downtime |
| Sub-account provisioning | ~2 hours | Create N Binance sub-accounts; API keys; IP restrictions; initial capital |
| Cfg migration | ~30 min | Run `fox-migrate-cfg`; verify |
| Server prep | ~1 hour | Install fox-engine + viewers + systemd; configure kernel params |
| Test deploy | Day 1 | Boot v0.1.0 against testnet first |
| Paper-mode | Week 1-2 | Run paper-mode alongside any remaining v5.X live nodes |
| Live cutover | Week 2 | Transfer real capital; v0.1.0 takes over |
| v5.X retirement | Week 2 | Shut down v5.X; archive |

---

## Phase 1: Pre-prep

```bash
# Backup current state
cd /home/caramel/code/FoxML_Trader_v2
git tag pre-v0.1.0-migration   # rollback anchor
cp engine.cfg engine.cfg.v5backup
cp -r models/ models.v5backup/
cp -r data/ data.v5backup/

# Document current state
fox-cli dump-state > /tmp/v5-state-snapshot.json   # if v5 has fox-cli; otherwise use engine_gui

# Plan downtime window
# v5.X must stop completely during cfg migration + sub-account provisioning
# Minimize downtime: prep sub-accounts BEFORE stopping v5.X
```

---

## Phase 2: Sub-account provisioning (Binance)

Per `DOCS/CONTRIBUTING/add-exchange.md` for first-time exchange setup:

### On Binance UI

1. Sub-Accounts → Create Sub-Account (×N; typical N=4 for dev; N=8-16 for production)
2. Verify each sub-account email
3. For each sub-account:
   - API Management → Create API
   - Enable Spot & Margin Trading (or appropriate for your trading style)
   - DISABLE Withdrawals (critical; engine refuses to start otherwise)
   - Add IP restriction (engine deployment IP)
4. Note each sub-account email + API key + API secret

### Transfer initial capital

For each sub-account, transfer initial allocation via Binance UI:
```
Master Account → Sub-Account 0: $2500 USDT
Master Account → Sub-Account 1: $2500 USDT
...
```

Total capital per sub-account: operator decision (typically equal allocation).

---

## Phase 3: Cfg migration

```bash
# Stop v5.X
sudo systemctl stop fox-engine-v5.service    # or kill engine process

# Use migration tool
cd /home/caramel/code/FoxML_Trader_v2
./build.sh test    # ensures v0.1.0 binary available
./build/fox-migrate-cfg --from engine.cfg.v5backup --to /etc/fox/configs/

# Verify output
ls /etc/fox/configs/
# Should see: engine.cfg + clusters/binance/{cluster.cfg, credentials/, nodes/}
```

### Manual cfg refinement

`fox-migrate-cfg` does best-effort; manually review:
- Sub-account credentials (env-var references)
- Per-node strategy assignments
- Kill switch thresholds
- Capital allocations

```bash
$EDITOR /etc/fox/configs/engine.cfg
$EDITOR /etc/fox/configs/clusters/binance/cluster.cfg
for f in /etc/fox/configs/clusters/binance/nodes/node_*/core.cfg; do
    $EDITOR "$f"
done
```

---

## Phase 4: Set environment variables

Create `/etc/fox/secrets.env`:
```
BINANCE_MASTER_API_KEY=<key from Binance UI>
BINANCE_MASTER_API_SECRET=<secret>
BINANCE_SUB0_API_KEY=<sub-account 0 key>
BINANCE_SUB0_API_SECRET=<sub-account 0 secret>
BINANCE_SUB1_API_KEY=<sub-account 1 key>
BINANCE_SUB1_API_SECRET=<sub-account 1 secret>
# ... etc
```

```bash
sudo chmod 600 /etc/fox/secrets.env
sudo chown fox:fox /etc/fox/secrets.env
```

---

## Phase 5: Install systemd unit

Per `DOCS/DEPLOYMENT_GUIDE.md`:

```bash
sudo cp /home/caramel/code/FoxML_Trader_v2/installation/fox-engine.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable fox-engine.service
```

---

## Phase 6: Configure kernel (if production mode)

Per `DOCS/PERFORMANCE_TUNING.md`:

```bash
# Edit /etc/default/grub
sudo vim /etc/default/grub

# Set:
# GRUB_CMDLINE_LINUX_DEFAULT="isolcpus=4-23 nohz_full=4-23 rcu_nocbs=4-23 transparent_hugepage=always"

sudo update-grub
sudo reboot
```

After reboot:
```bash
cat /sys/devices/system/cpu/isolated     # verify isolcpus active
```

---

## Phase 7: Test deploy (TESTNET FIRST)

Use Binance testnet sub-accounts for initial verification:

```bash
# Configure for testnet
$EDITOR /etc/fox/configs/clusters/binance/cluster.cfg
# Set: endpoints.rest = https://testnet.binance.vision/api
# Use testnet API keys

# Start engine
sudo systemctl start fox-engine.service

# Verify
sudo journalctl -u fox-engine.service -f
sudo -u fox fox-tui
```

Run on testnet for ~1 day. Verify:
- All sub-accounts boot cleanly (preflight check passes)
- Submit orders successfully on testnet
- Fills flow back through user-data WS
- fox-tui shows all expected state
- Reconciliation correct
- fox-cli commands work

---

## Phase 8: Paper-mode deployment

Once testnet validated:

```bash
# Switch back to mainnet endpoints
$EDITOR /etc/fox/configs/clusters/binance/cluster.cfg
# endpoints.rest = https://api.binance.com (production)

# Set all nodes to paper mode initially
for n in /etc/fox/configs/clusters/binance/nodes/node_*/core.cfg; do
    # Edit each: mode = paper
    sed -i 's/^mode = .*/mode = paper/' $n
done

# Restart
sudo systemctl restart fox-engine.service
```

Run paper-mode on production Binance for 1-2 weeks. Compare paper P&L to v5.X's historical P&L over same period. Verify strategy logic matches expectations.

---

## Phase 9: Live cutover

When paper-mode validated:

```bash
# Per-node: paper → live (one at a time; safety)
$EDITOR /etc/fox/configs/clusters/binance/nodes/node_0/core.cfg
# mode = paper → mode = live

# Reload
fox-cli reload-node-config binance/node_0

# Verify node_0 trades live; watch for 1 day
# Then promote node_1; node_2; etc.
```

Per `DOCS/STRATEGY_LIFECYCLE.md`: gradual capital ramp at performance milestones.

---

## Phase 10: v5.X retirement

After v0.1.0 stable in production for 1+ week:

```bash
# Stop v5.X (if still running)
sudo systemctl stop fox-engine-v5.service
sudo systemctl disable fox-engine-v5.service

# Archive v5.X (optional; rollback safety)
mv /opt/fox-engine-v5/ /opt/fox-engine-v5-archived-$(date +%Y%m%d)/

# Remove old systemd unit
sudo rm /etc/systemd/system/fox-engine-v5.service
sudo systemctl daemon-reload
```

---

## Rollback plan

If v0.1.0 has critical issues:

```bash
sudo systemctl stop fox-engine.service

# Restore v5.X
cd /home/caramel/code/FoxML_Trader_v2
git checkout pre-v0.1.0-migration
./build.sh test
cp engine.cfg.v5backup engine.cfg
cp -r models.v5backup/* models/

# Run v5.X
./engine    # or restart v5 systemd unit
```

Capital still in sub-accounts; can be transferred back to master via Binance UI if needed (or keep in sub-accounts; not engine-dependent).

---

## Common migration issues

### "Engine refuses to start: canWithdraw=true on sub-account X"

Forgot to disable withdrawal on that sub-account's API key. Fix at Binance UI → API Management.

### "Engine refuses to start: kernel version too old"

io_uring requires Linux 5.6+. Upgrade kernel OR set `topology.mode = dev` in engine.cfg (slower but works on older kernels).

### "fox-migrate-cfg failed on field X"

Manual cfg edit required for that field. Migration tool reports unmigrated fields explicitly.

### "Paper P&L diverges substantially from v5.X live P&L"

Investigate strategy parity. Most likely: feature compute drift between v5.X and v0.1.0. Run `/parity-check` skill against feature registry.

---

**End of MIGRATION_FROM_v5.X.md v1.0** (2026-05-28).
