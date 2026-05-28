---
type: framework-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-28
landing_ship: v5.15.5.F.4d.1.E.2
canonical_applications:
  - v5.15.5.F.4d.1.E.2 (Prometheus /metrics endpoint + mmap state-publication)
sister_specs:
  - framework-patterns/dual-format-metrics-publication-pattern.md (sister)
  - concurrency-patterns/structured-audit-log-pattern.md (sister)
  - framework-patterns/native-tui-via-mmap-readonly-pattern.md (mmap consumer)
tags: [framework-discipline, observability, prometheus, metrics, latency-histograms]
surface: [observability, monitoring]
applies_at_skills: [/precoding-audit-gate]
---

# Built-in observability pattern

**Pattern intent:** Engine emits comprehensive metrics natively. Per-node latency histograms + per-cluster connection health + per-cluster rate-limit usage + per-sub-account state. No external instrumentation framework required.

## Metrics emitted

### Per-node

- `fox_node_latency_hot_p50_ns{cluster, node, strategy}` (gauge)
- `fox_node_latency_hot_p99_ns{cluster, node}` (gauge)
- `fox_node_latency_hot_p9999_ns{cluster, node}` (gauge)
- `fox_node_latency_slow_p50_ns{cluster, node}` (gauge)
- `fox_node_latency_slow_p99_ns{cluster, node}` (gauge)
- `fox_node_fills_count{cluster, node, mode}` (counter)
- `fox_node_wins_count{cluster, node}` (counter)
- `fox_node_losses_count{cluster, node}` (counter)
- `fox_node_realized_pnl{cluster, node, mode}` (gauge)
- `fox_node_open_notional{cluster, node}` (gauge)
- `fox_node_drawdown_current{cluster, node}` (gauge)
- `fox_node_kill_flag{cluster, node}` (gauge; 0 or 1)

### Per-cluster

- `fox_cluster_connection_uptime_seconds{cluster}` (counter)
- `fox_cluster_reconnect_count{cluster}` (counter)
- `fox_cluster_rate_tokens_available{cluster, subaccount}` (gauge)
- `fox_cluster_rate_tokens_used_per_minute{cluster}` (rate)
- `fox_cluster_realized_pnl{cluster}` (gauge)
- `fox_cluster_kill_flag{cluster}` (gauge)

### Global

- `fox_global_realized_pnl` (gauge)
- `fox_global_open_notional` (gauge)
- `fox_global_drawdown_current` (gauge)
- `fox_global_kill_flag` (gauge)
- `fox_engine_uptime_seconds` (counter)
- `fox_aggregator_cycle_count` (counter)
- `fox_aggregator_integrity_drift_count` (counter)

### Submit + fill latency

- `fox_submit_roundtrip_us{cluster}` (histogram; bucketed; p50/p99/p99.99)
- `fox_fill_latency_us{cluster}` (histogram)

### Error rates

- `fox_submit_errors_total{cluster, error_code}` (counter)
- `fox_reconcile_discrepancies_total{cluster, subaccount}` (counter)
- `fox_kill_switch_trips_total{level}` (counter; level=global/cluster/node)

## Publication mechanism

Dual-format per `dual-format-metrics-publication-pattern.md`:

1. **mmap** (real-time; fox-tui reads zero-copy)
2. **Prometheus /metrics endpoint** (HTTP; Grafana scrape)

```cpp
// /metrics endpoint (localhost-only per D-19)
void HttpServer_HandleMetrics(int sock_fd) {
    // Emit Prometheus exposition format
    char buf[64*1024];
    int len = 0;

    len += snprintf(buf + len, sizeof(buf) - len,
                    "# HELP fox_global_realized_pnl Global realized P&L in USD\n"
                    "# TYPE fox_global_realized_pnl gauge\n"
                    "fox_global_realized_pnl %f\n",
                    FPN_ToDouble(g_state.aggregator.global.cached_total_realized_pnl));
    // ... emit other metrics ...

    write(sock_fd, buf, len);
}
```

## Histogram bucketing strategy

Per-node hot-path latency:
- Bucket boundaries: 50ns / 100ns / 200ns / 500ns / 1μs / 2μs / 5μs / 10μs / 50μs / Inf
- Counts per bucket; expose as Prometheus histogram

Submit roundtrip:
- Bucket boundaries: 1ms / 5ms / 10ms / 25ms / 50ms / 100ms / 250ms / 1s / Inf

## Stage progression criteria

- **Stage 3 first canonical** (`.E.2`): comprehensive metrics emitted
- **Stage 4 cohort** (when 2nd surface: e.g., per-strategy histograms): pattern proven
- **Stage 5 CLAUDE.md** (3rd application): promoted

## Anti-patterns avoided

- **External instrumentation framework dependency** — bloat
- **No latency histograms** — operator can't see tail latency
- **Periodic scrape overhead on hot path** — emit from slow-path only

## Cross-references

- Sister: `framework-patterns/dual-format-metrics-publication-pattern.md`
- Sister: `concurrency-patterns/structured-audit-log-pattern.md`
- First application: `plans/v5.15.5.F.4d.1.E.2-headless-configs-docs.md`
