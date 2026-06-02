# Incident Runbook

**Audience:** Operator responding to incidents.

For daily operations: see `DOCS/OPERATOR_MANUAL.md`. For glossary: see `DOCS/GLOSSARY.md`.

---

## Common incidents + responses

### Engine crashed (systemd restart cycle)

**Symptoms:** `systemctl status fox-engine` shows recent restarts.

**Response:**
1. `sudo journalctl -u fox-engine.service -n 200` — review last 200 log lines
2. Identify crash cause (segfault; OOM; cfg validation failure; etc.)
3. If cfg validation: fix cfg + restart
4. If OOM: check memory budget cfg; review per-node ring sizes
5. If segfault: capture core dump; file bug report
6. Reconciliation runs automatically on restart per `crash-recovery-via-mmap-state-pattern`

**Default action:** systemd Restart=on-failure handles automatically. Engine state recovered from mmap. Operator reviews logs to identify root cause.

### Exchange API outage

**Symptoms:** fox-tui shows cluster connection DOWN; reconnect_count climbing; submits failing.

**Response:**
1. Check exchange status (Binance status page; Alpaca status; etc.)
2. If exchange-side outage: WAIT. Engine will keep reconnecting with exponential backoff.
3. If outage > cfg threshold (default 10min): cluster auto-halts; operator alert webhook fires
4. After exchange recovery: `fox-cli resume-cluster <name>` to re-enable trading

### Sub-account suspended by exchange

**Symptoms:** consecutive submit failures on one sub-account; error code from exchange.

**Response:**
1. fox-cli pause-node <cluster>/<node> (halt that node specifically)
2. Contact exchange support; understand suspension reason
3. Resolve with exchange (KYC; abnormal activity flag; etc.)
4. After resolution: fox-cli resume-node <cluster>/<node>

### Reconciliation drift detected

**Symptoms:** Audit log `reconcile_discrepancy` events; webhook alert fired.

**Response:**
1. Review audit log: `jq -c '.event_type=="reconcile_discrepancy"' /var/lib/fox/audit/state-changes.jsonl | tail -10`
2. Identify magnitude + which sub-account
3. If small drift (rounding; minor): trust exchange truth; continue
4. If large drift: HALT affected node; manual investigation; possible engine bug
5. Force reconcile: `fox-cli reconcile-node <cluster>/<node>`

### Clock drift (Binance recvWindow)

**Symptoms:** Submit errors with code -1022 ("Signature for this request is not valid"); time drift warnings in logs.

**Response:**
1. Check NTP sync: `chronyc tracking` or `timedatectl status`
2. If drift > 5s: NTP issue; restart chrony / systemd-timesyncd
3. Engine refuses to start if drift > recvWindow (5s default); operator must fix
4. After NTP sync: engine resumes

### Webhook alerts

Engine emits webhooks on these events; operator should configure receivers:
- `ALERT_DRAWDOWN_THRESHOLD` — kill switch tripped
- `ALERT_SUBACCOUNT_SUSPENDED` — exchange-side suspension detected
- `ALERT_EXCHANGE_DOWN` — prolonged WS outage
- `ALERT_RECONCILE_DRIFT` — engine state mismatch with exchange
- `ALERT_AGGREGATOR_INTEGRITY_DRIFT` — running aggregate doesn't match seqlock walk (engine bug class)
- `ALERT_PERMISSION_CHANGED` — sub-account permissions changed unexpectedly

### Engine refuses to start

**Common causes:**
- Cfg validation failure (clear error message in journalctl)
- API permission failure (sub-account has enableWithdrawals; engine refuses per D-31)
- Hardware feature missing (SHA-NI; AVX2; TSC required)
- Kernel version too old (io_uring requires 5.6+)
- isolcpus not configured in production mode

**Response:** Read error message; fix specific issue; retry.

### High latency tail (p99 spike)

**Symptoms:** fox-tui shows per-node hot_p99 elevated; Prometheus metric `fox_node_latency_hot_p99_ns` spiking.

**Response:**
1. Verify CPU isolation: `cat /sys/devices/system/cpu/isolated`
2. Verify nohz_full active: `cat /sys/devices/system/cpu/nohz_full`
3. Check for noisy neighbor processes: `top -H` filter to engine cores
4. Verify NUMA placement: `/proc/<pid>/numa_maps`
5. Check kernel scheduler stats: `perf stat` on engine cores

### Operator-triggered emergency halt

```bash
# Halt all trading immediately
fox-cli halt-all

# Investigate via fox-tui + audit logs
fox-tui
jq -c '.severity=="ERROR"' /var/lib/fox/audit/errors.jsonl | tail -20

# After resolution
fox-cli resume-all
```

---

## Debugging tooling

```bash
# Engine state dump
fox-cli dump-state                       # global
fox-cli dump-state binance               # per-cluster
fox-cli dump-state binance/node_0        # per-node

# Audit chain verification
fox-cli verify-audit-chain --file /var/lib/fox/audit/trades.jsonl

# Latency benchmark (one-shot)
fox-cli benchmark-latency --node binance/node_0 --duration 60s

# Force reconcile
fox-cli reconcile-cluster binance

# Recent events
fox-cli watch binance/node_0    # tail per-node events
```

---

**End of INCIDENT_RUNBOOK.md v1.0** (2026-05-28).
