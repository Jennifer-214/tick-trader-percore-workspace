# Observability Reference

**Audience:** Operator setting up monitoring infrastructure + querying engine state.

For deployment: `DOCS/DEPLOYMENT_GUIDE.md`. For tuning: `DOCS/PERFORMANCE_TUNING.md`. For incidents: `DOCS/INCIDENT_RUNBOOK.md`.

---

## Two publication formats

Per `framework-patterns/dual-format-metrics-publication-pattern.md`:

| Format | Consumer | Update cadence | Purpose |
|---|---|---|---|
| mmap shared memory | fox-tui (local TUI) | Real-time (~sub-ms) | Active operation; immediate state |
| Prometheus /metrics | Grafana scrape | Scrape interval (10-30s) | Historical TSDB; remote alerts |

Both consume same engine internal state; different serialization.

---

## Metric inventory (Prometheus exposition format)

### Per-node metrics

```
# HELP fox_node_latency_hot_p50_ns Hot path p50 latency (nanoseconds)
# TYPE fox_node_latency_hot_p50_ns gauge
fox_node_latency_hot_p50_ns{cluster="binance",node="0",strategy="momentum_v3"} 187

# HELP fox_node_latency_hot_p99_ns Hot path p99 latency
# TYPE fox_node_latency_hot_p99_ns gauge
fox_node_latency_hot_p99_ns{cluster="binance",node="0"} 412

# HELP fox_node_latency_hot_p9999_ns Hot path p99.99 latency
# TYPE fox_node_latency_hot_p9999_ns gauge
fox_node_latency_hot_p9999_ns{cluster="binance",node="0"} 1842

# HELP fox_node_latency_slow_p50_ns Slow path cycle p50
# TYPE fox_node_latency_slow_p50_ns gauge
fox_node_latency_slow_p50_ns{cluster="binance",node="0"} 8456

# HELP fox_node_latency_slow_p99_ns Slow path cycle p99
fox_node_latency_slow_p99_ns{cluster="binance",node="0"} 23104

# HELP fox_node_fills_count Cumulative fills count
# TYPE fox_node_fills_count counter
fox_node_fills_count{cluster="binance",node="0",mode="live"} 1247
fox_node_fills_count{cluster="binance",node="1",mode="paper"} 423

# HELP fox_node_wins_count Cumulative winning trades
# TYPE fox_node_wins_count counter
fox_node_wins_count{cluster="binance",node="0"} 645

# HELP fox_node_losses_count Cumulative losing trades
# TYPE fox_node_losses_count counter
fox_node_losses_count{cluster="binance",node="0"} 412

# HELP fox_node_realized_pnl Realized P&L (USD)
# TYPE fox_node_realized_pnl gauge
fox_node_realized_pnl{cluster="binance",node="0",mode="live"} 523.47

# HELP fox_node_open_notional Currently open position notional
# TYPE fox_node_open_notional gauge
fox_node_open_notional{cluster="binance",node="0"} 5200.00

# HELP fox_node_drawdown_current Current drawdown from peak
# TYPE fox_node_drawdown_current gauge
fox_node_drawdown_current{cluster="binance",node="0"} 0.012

# HELP fox_node_kill_flag Per-node kill flag (0 OFF; 1 ON)
# TYPE fox_node_kill_flag gauge
fox_node_kill_flag{cluster="binance",node="0"} 0
```

### Per-cluster metrics

```
# HELP fox_cluster_connection_uptime_seconds Uptime since last connection
# TYPE fox_cluster_connection_uptime_seconds counter
fox_cluster_connection_uptime_seconds{cluster="binance"} 345600  # 4 days

# HELP fox_cluster_reconnect_count Cumulative reconnects since boot
# TYPE fox_cluster_reconnect_count counter
fox_cluster_reconnect_count{cluster="binance"} 2

# HELP fox_cluster_rate_tokens_available Rate-limit tokens remaining
# TYPE fox_cluster_rate_tokens_available gauge
fox_cluster_rate_tokens_available{cluster="binance",subaccount="0"} 1185
fox_cluster_rate_tokens_available{cluster="binance",subaccount="1"} 1156

# HELP fox_cluster_realized_pnl Cumulative realized P&L for cluster
# TYPE fox_cluster_realized_pnl gauge
fox_cluster_realized_pnl{cluster="binance"} 523.40

# HELP fox_cluster_kill_flag Per-cluster kill flag
# TYPE fox_cluster_kill_flag gauge
fox_cluster_kill_flag{cluster="binance"} 0

# HELP fox_cluster_tls_resumption_rate TLS session resumption success rate
# TYPE fox_cluster_tls_resumption_rate gauge
fox_cluster_tls_resumption_rate{cluster="binance"} 0.97
```

### Global metrics

```
# HELP fox_global_realized_pnl Deployment-wide realized P&L
# TYPE fox_global_realized_pnl gauge
fox_global_realized_pnl 847.23

# HELP fox_global_open_notional Deployment-wide open position notional
fox_global_open_notional 24500.00

# HELP fox_global_drawdown_current Deployment-wide drawdown
fox_global_drawdown_current 0.012

# HELP fox_global_kill_flag Global kill flag
fox_global_kill_flag 0

# HELP fox_engine_uptime_seconds Engine uptime
# TYPE fox_engine_uptime_seconds counter
fox_engine_uptime_seconds 345617

# HELP fox_engine_software_version Engine software version
# TYPE fox_engine_software_version gauge
fox_engine_software_version{version="0.1.0"} 1

# HELP fox_aggregator_cycle_count Aggregator integrity cycle count
# TYPE fox_aggregator_cycle_count counter
fox_aggregator_cycle_count 3456178

# HELP fox_aggregator_integrity_drift_count Aggregator drift events
# TYPE fox_aggregator_integrity_drift_count counter
fox_aggregator_integrity_drift_count 0
```

### Submit + fill latency histograms

```
# HELP fox_submit_roundtrip_us Submit roundtrip latency (microseconds)
# TYPE fox_submit_roundtrip_us histogram
fox_submit_roundtrip_us_bucket{cluster="binance",le="1000"} 0
fox_submit_roundtrip_us_bucket{cluster="binance",le="5000"} 12
fox_submit_roundtrip_us_bucket{cluster="binance",le="10000"} 245
fox_submit_roundtrip_us_bucket{cluster="binance",le="25000"} 891
fox_submit_roundtrip_us_bucket{cluster="binance",le="50000"} 1234
fox_submit_roundtrip_us_bucket{cluster="binance",le="100000"} 1247
fox_submit_roundtrip_us_bucket{cluster="binance",le="+Inf"} 1247
fox_submit_roundtrip_us_count{cluster="binance"} 1247
fox_submit_roundtrip_us_sum{cluster="binance"} 36214000

# HELP fox_fill_latency_us Fill notification latency
# TYPE fox_fill_latency_us histogram
# Similar bucketing
```

### Error rates

```
# HELP fox_submit_errors_total Cumulative submit errors by code
# TYPE fox_submit_errors_total counter
fox_submit_errors_total{cluster="binance",error_code="-1003"} 3   # rate limit
fox_submit_errors_total{cluster="binance",error_code="-2010"} 1   # insufficient balance

# HELP fox_reconcile_discrepancies_total Cumulative reconcile drift events
# TYPE fox_reconcile_discrepancies_total counter
fox_reconcile_discrepancies_total{cluster="binance",subaccount="2"} 1

# HELP fox_kill_switch_trips_total Cumulative kill switch trips
# TYPE fox_kill_switch_trips_total counter
fox_kill_switch_trips_total{level="node"} 0
fox_kill_switch_trips_total{level="cluster"} 0
fox_kill_switch_trips_total{level="global"} 0

# HELP fox_tls_userspace_fallback_rate kTLS fallback rate (should be 0)
fox_tls_userspace_fallback_rate 0.0

# HELP fox_strategy_hot_reload_success Strategy hot-reload success counter
fox_strategy_hot_reload_success 0
```

---

## Prometheus scrape config

```yaml
# /etc/prometheus/prometheus.yml
scrape_configs:
  - job_name: 'fox-engine'
    scrape_interval: 15s
    static_configs:
      - targets:
          - 'localhost:9091'    # via SSH tunnel or local Prometheus
    relabel_configs:
      - source_labels: [__address__]
        target_label: deployment
        replacement: 'caramel-laptop-001'
```

For SSH tunneled scrape (engine on server; Prometheus on monitoring host):

```bash
# On monitoring host:
ssh -L 9091:127.0.0.1:9091 server@example.com
# Prometheus scrapes localhost:9091; tunneled to engine
```

---

## Grafana dashboard suggestions

### Global overview panel

```promql
# Total realized P&L
fox_global_realized_pnl

# 24h P&L change
fox_global_realized_pnl - fox_global_realized_pnl offset 1d

# Drawdown
fox_global_drawdown_current * 100

# Kill switch state
fox_global_kill_flag + on() fox_cluster_kill_flag + on() fox_node_kill_flag
```

### Per-cluster panel

```promql
# Connection health
fox_cluster_connection_uptime_seconds / 86400   # days uptime
fox_cluster_reconnect_count

# Rate budget usage
1 - (fox_cluster_rate_tokens_available / 1200)   # % consumed

# TLS resumption rate
fox_cluster_tls_resumption_rate
```

### Per-node panel

```promql
# Latency histogram (heatmap)
histogram_quantile(0.99, rate(fox_submit_roundtrip_us_bucket[5m]))

# Win rate
fox_node_wins_count / (fox_node_wins_count + fox_node_losses_count)

# Cumulative P&L curve
fox_node_realized_pnl{mode="live"}
```

### Alert rules

```yaml
groups:
  - name: fox_engine_alerts
    rules:
      - alert: HighDrawdown
        expr: fox_global_drawdown_current > 0.05
        for: 1m
        annotations:
          summary: "Global drawdown >5%"

      - alert: KillSwitchTripped
        expr: fox_global_kill_flag == 1
        annotations:
          summary: "Global kill switch ON"

      - alert: ExchangeReconnectStorm
        expr: rate(fox_cluster_reconnect_count[5m]) > 0.5
        for: 5m
        annotations:
          summary: "Cluster reconnecting frequently"

      - alert: LatencyP99HotPathDegraded
        expr: fox_node_latency_hot_p99_ns > 2000
        for: 10m
        annotations:
          summary: "Hot path p99 > 2μs (H8 budget violated)"

      - alert: SubmitErrorRate
        expr: rate(fox_submit_errors_total[5m]) > 0.1
        annotations:
          summary: "Submit error rate elevated"

      - alert: ReconcileDrift
        expr: increase(fox_reconcile_discrepancies_total[1h]) > 0
        annotations:
          summary: "Reconcile drift detected; investigate"
```

---

## fox-tui display (real-time; via mmap)

fox-tui reads same metric data from mmap (lock-free seqlock-consistent). Displays:
- Global dashboard (P&L; notional; drawdown; kill switches)
- Per-cluster panels (connection health; rate budget; per-cluster P&L)
- Per-node panels (mode; symbol; strategy; position; latency)
- Recent audit events ring

Per `framework-patterns/native-tui-via-mmap-readonly-pattern.md`. ~sub-ms update; no scrape overhead.

---

## Audit log query (JSONL)

Per `concurrency-patterns/structured-audit-log-pattern.md`:

```bash
# Recent fills for specific node
jq -c '.cluster=="binance" and .node_id==0 and .event_type=="fill"' /var/lib/fox/audit/trades.jsonl | tail -20

# Errors in last hour
SINCE=$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S)
jq -c "select(.ts > \"$SINCE\")" /var/lib/fox/audit/errors.jsonl

# Daily P&L from fills
jq -c '.event_type=="fill" | {date: .ts[:10], net_pnl: .net_pnl}' /var/lib/fox/audit/trades.jsonl | ...

# Audit chain integrity (if hash-chain enabled)
fox-cli verify-audit-chain --file /var/lib/fox/audit/trades.jsonl
```

---

## Webhook alerts

Engine emits webhook POST on:
- `ALERT_DRAWDOWN_THRESHOLD`
- `ALERT_SUBACCOUNT_SUSPENDED`
- `ALERT_EXCHANGE_DOWN`
- `ALERT_RECONCILE_DRIFT`
- `ALERT_AGGREGATOR_INTEGRITY_DRIFT`
- `ALERT_PERMISSION_CHANGED`
- `ALERT_LATENCY_REGRESSION`
- `ALERT_KILL_SWITCH_TRIPPED`

Operator configures URL per cfg:

```
# configs/engine.cfg:
[alerts]
webhook_url = https://hooks.slack.com/services/...
event_types_subscribed = ["DRAWDOWN_THRESHOLD", "KILL_SWITCH_TRIPPED", "RECONCILE_DRIFT", "SUBACCOUNT_SUSPENDED"]
```

Engine doesn't ship integration with specific services (Slack; Discord; PagerDuty); operator wires webhook URL.

---

**End of OBSERVABILITY_REFERENCE.md v1.0** (2026-05-28).
