---
type: framework-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-28
landing_ship: v5.15.5.F.4d.1.E.2
canonical_applications:
  - v5.15.5.F.4d.1.E.2 (mmap + Prometheus dual publication)
sister_specs:
  - framework-patterns/built-in-observability-pattern.md (metric inventory)
  - framework-patterns/native-tui-via-mmap-readonly-pattern.md (mmap consumer)
tags: [framework-discipline, metrics-publication, mmap, prometheus, dual-format]
surface: [observability, mmap, http-endpoint]
applies_at_skills: [/precoding-audit-gate]
---

# Dual-format metrics publication pattern

**Pattern intent:** Engine emits metrics in TWO formats: mmap (real-time; fox-tui zero-copy reads) + Prometheus exposition (HTTP /metrics; Grafana scrape). Each format serves different consumer.

## Format comparison

| Axis | mmap | Prometheus /metrics |
|---|---|---|
| Consumer | fox-tui (local TUI) | Grafana via SSH-tunneled scrape |
| Update cadence | Real-time (sub-ms after change) | Scrape interval (typ. 10-30s) |
| Latency | ~10μs (mmap read; seqlock) | ~10-100ms (HTTP roundtrip) |
| Historical data | No (current snapshot only) | Yes (Prometheus retains TSDB) |
| Cross-host | No (local-only) | Yes (Grafana scrapes via SSH tunnel) |
| Format | Native struct | HTTP text per Prometheus spec |

Both consume from same engine internal metrics; just different serialization.

## Pattern description

### Engine-side update

```cpp
// Engine maintains internal metrics state
struct alignas(64) MetricsState {
    // Per-node histograms
    HistogramBuckets hot_latency_buckets[MAX_NODES];
    HistogramBuckets slow_latency_buckets[MAX_NODES];

    // Counters
    std::atomic<uint64_t> total_fills;
    std::atomic<uint64_t> total_submit_errors;
    // ...
};

// On each tick / fill / event: update internal state (atomic)
void Metrics_RecordHotLatency(uint32_t node_id, uint64_t latency_ns) {
    HistogramBuckets& buckets = g_metrics.hot_latency_buckets[node_id];
    Bucket_Increment(buckets, latency_ns);
}
```

### mmap publication (real-time)

```cpp
// State publish cycle (per native-tui-via-mmap-readonly-pattern):
void StatePublish_Cycle(EngineState<F>& state) {
    // Copy internal metrics state into mmap region
    region->header.writer_seqlock.fetch_add(1, std::memory_order_acq_rel);  // odd
    region->per_node_metrics = g_metrics.snapshot();
    region->header.writer_seqlock.fetch_add(1, std::memory_order_release);  // even
}
```

### Prometheus publication (on /metrics request)

```cpp
// HTTP /metrics endpoint (localhost-only per D-19)
void HttpHandler_Metrics(int sock_fd) {
    char buf[256*1024];
    int len = 0;

    // Iterate FOREACH_METRIC_SPEC; emit each in Prometheus format
    #define EMIT_GAUGE(name, value, ...) \
        len += snprintf(buf + len, sizeof(buf) - len, \
                        "# HELP %s\n# TYPE %s gauge\n%s %f\n", \
                        name##_HELP, name, name, value);

    EMIT_GAUGE("fox_global_realized_pnl",
               FPN_ToDouble(state.aggregator.global.cached_total_realized_pnl));
    // ... etc per metric

    // Per-node loop
    for (uint32_t n = 0; n < state.node_count; ++n) {
        len += snprintf(buf + len, sizeof(buf) - len,
                        "fox_node_latency_hot_p99_ns{cluster=\"%s\",node=\"%u\"} %lu\n",
                        cluster_name, n, hot_p99[n]);
    }

    write(sock_fd, buf, len);
}
```

### Operator workflow

```bash
# Local: fox-tui reads mmap (real-time; sub-ms updates)
fox-tui

# Remote: Grafana scrapes via Prometheus
# 1. Operator has Prometheus running on monitoring host
# 2. SSH tunnel: ssh -L 9091:127.0.0.1:9091 server
# 3. Prometheus scrape config: scrape_target = localhost:9091
# 4. Grafana dashboard queries Prometheus
```

## Stage progression criteria

- **Stage 3 first canonical** (`.E.2`): dual publication implemented
- **Stage 4 cohort** (when 2nd format: e.g., StatsD for tracing): pattern proven
- **Stage 5 CLAUDE.md** (3rd application): promoted

## Anti-patterns avoided

- **Single-format publication** — either real-time OR historical; not both
- **Prometheus-only** — TUI requires real-time low-latency
- **Custom protocol** — vendor lock-in; Prometheus is industry standard

## Cross-references

- Sister: `framework-patterns/built-in-observability-pattern.md`
- Sister: `framework-patterns/native-tui-via-mmap-readonly-pattern.md`
- First application: `plans/v5.15-live-readiness/subplans/2026-05-28-v5.15.5.F.4d.1.E.2-headless-configs-docs.md`
