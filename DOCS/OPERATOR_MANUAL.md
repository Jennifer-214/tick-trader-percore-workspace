# Operator Manual

**Audience:** Operator doing daily operations on running engine.

For first-time deployment: see `DOCS/DEPLOYMENT_GUIDE.md`. For terminology: see `DOCS/GLOSSARY.md`. For troubleshooting: see `DOCS/INCIDENT_RUNBOOK.md`.

---

## Daily operations

### Monitor state

```bash
# Local: attach TUI
fox-tui

# Remote via SSH tunnel
ssh -L /tmp/fox.sock:/var/run/fox/engine.sock server
fox-tui --socket /tmp/fox.sock

# Quick check: aggregate via fox-cli
fox-cli dump-state
fox-cli dump-state binance/node_0    # specific node
```

### Pause / resume node

```bash
# Halt one node (e.g., suspicious behavior)
fox-cli pause-node binance/node_2

# Resume after operator verification
fox-cli resume-node binance/node_2
```

### Halt cluster (entire exchange)

```bash
# Halt all binance nodes (e.g., Binance API issue)
fox-cli halt-cluster binance

# Resume after issue resolved
fox-cli resume-cluster binance
```

### Global emergency stop

```bash
# Halt EVERYTHING immediately
fox-cli halt-all

# Resume (operator must explicitly)
fox-cli resume-all
```

### Reload config (hot-reload runtime params)

```bash
# Edit cfg
$EDITOR /etc/fox/configs/clusters/binance/nodes/node_0/strategy.cfg

# Trigger reload
fox-cli reload-node-config binance/node_0

# OR reload entire cluster
fox-cli reload-cluster-config binance
```

Note: boot-time fields (exchange endpoint; credentials; subaccount_id) require restart. Engine refuses hot-reload with clear error.

### Capital management

```bash
# Move funds between sub-accounts
fox-cli transfer-funds --from binance:0 --to binance:2 --amount 1000 --asset USDT

# View per-sub-account balances
fox-cli dump-state binance | grep balance
```

### Kill switch thresholds

```bash
# Set per-node drawdown threshold
fox-cli set-kill-threshold node binance/node_0 0.15   # 15%

# Set per-cluster threshold
fox-cli set-kill-threshold cluster binance 0.10

# Set global threshold
fox-cli set-kill-threshold global 0.05
```

### Strategy rotation (per `STRATEGY_LIFECYCLE.md`)

```bash
# Promote paper-tested strategy to live
$EDITOR /etc/fox/configs/clusters/binance/nodes/node_5/core.cfg
# Change mode = paper → mode = live; capital_allocation = 500
fox-cli reload-node-config binance/node_5
fox-cli transfer-funds --from binance:0 --to binance:5 --amount 500

# Rollback strategy
fox-cli rollback-strategy binance/node_5
```

### Hot-reload strategy code (at `.E.X` ship)

```bash
# Rebuild strategy
cd /home/caramel/code/FoxML_Trader_v2
./build.sh strategies     # builds libstrategy_momentum.so etc.

# Hot-swap into running engine
fox-cli model-swap binance/node_0 --to /home/caramel/code/FoxML_Trader_v2/build/libstrategy_momentum.so

# Rollback if issues
fox-cli rollback-strategy binance/node_0
```

### Audit log review

```bash
# Recent fills
tail -100 /var/lib/fox/audit/trades.jsonl | jq

# Errors in last hour
SINCE=$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S)
jq -c "select(.ts > \"$SINCE\")" /var/lib/fox/audit/errors.jsonl

# Operator command history
jq '.event_type' /var/lib/fox/audit/commands.jsonl | sort | uniq -c | sort -rn

# Daily P&L from trades
jq -c '.event_type=="fill" | {ts: .ts[:10], net_pnl: .net_pnl}' /var/lib/fox/audit/trades.jsonl | ...
```

### State backup

```bash
# Operator-triggered snapshot
fox-cli backup-state --output /tmp/fox-state-$(date +%Y%m%d).bin

# Restore on new server (migration)
fox-engine --restore /tmp/fox-state-2026-05-28.bin --state-dir /var/lib/fox/state/
```

### Engine upgrade workflow

```bash
# 1. Stop old
sudo systemctl stop fox-engine.service

# 2. Build new (in dev tree)
cd /home/caramel/code/FoxML_Trader_v2
git pull
./build.sh test

# 3. Install new binaries
sudo cp build/fox-engine /usr/local/bin/

# 4. Verify configs still parse (engine refuses to start if not)
sudo -u fox /usr/local/bin/fox-engine --validate-cfg --config-dir /etc/fox/configs/

# 5. Start new
sudo systemctl start fox-engine.service

# 6. Verify
fox-tui    # check state restored; nodes operating
```

---

## fox-cli command reference (quick)

```
fox-cli pause-node <cluster>/<node>             # halt one node
fox-cli resume-node <cluster>/<node>            # resume
fox-cli halt-cluster <cluster>                  # halt entire cluster
fox-cli resume-cluster <cluster>
fox-cli halt-all                                # global emergency
fox-cli resume-all
fox-cli transfer-funds --from <c>:<sub> --to <c>:<sub> --amount <amt> --asset <a>
fox-cli reload-node-config <cluster>/<node>
fox-cli reload-cluster-config <cluster>
fox-cli set-kill-threshold {global|cluster <name>|node <c>/<n>} <fraction>
fox-cli dump-state [<scope>]                    # debug dump
fox-cli dump-metrics --since <duration>
fox-cli reconcile-node <cluster>/<node>         # force reconcile
fox-cli reconcile-cluster <cluster>
fox-cli add-node <cluster> --sub-account <id> --symbol <s> --strategy <name>
fox-cli remove-node <cluster>/<node>
fox-cli model-swap <cluster>/<node> --to <so-path>
fox-cli rollback-strategy <cluster>/<node>
fox-cli watch <cluster>/<node>                  # tail per-node events
fox-cli backup-state --output <path>
fox-cli verify-audit-chain --file <jsonl-path>  # tamper-evidence check
```

---

## Common workflows

### "I want to test a new strategy variant"

1. Develop strategy in `Strategies/`
2. Backtest via `foxml-train --config training/<variant>.training.cfg`
3. Create paper-mode node: `fox-cli add-node binance --sub-account <next> --symbol <s> --strategy <variant> --mode paper`
4. Watch for 1-4 weeks via fox-tui
5. Promote to live if validated: edit core.cfg → mode = live; transfer-funds; reload-node-config
6. Gradual capital ramp per `STRATEGY_LIFECYCLE.md`

### "Something looks wrong"

1. `fox-cli pause-node <cluster>/<node>` (halt suspicious node)
2. Review audit log: `tail -50 /var/lib/fox/audit/errors.jsonl`
3. Reconcile: `fox-cli reconcile-node <cluster>/<node>`
4. If serious: `fox-cli halt-cluster <cluster>` or `fox-cli halt-all`
5. Diagnose via fox-tui + audit logs
6. Resume after fix

### "I want to rebalance capital"

1. Check current allocation: `fox-cli dump-state binance | jq '.subaccounts'`
2. Transfer: `fox-cli transfer-funds --from binance:0 --to binance:2 --amount <amt> --asset USDT`
3. Verify: re-check; per-cluster aggregator updates

---

**End of OPERATOR_MANUAL.md v1.0** (2026-05-28).
