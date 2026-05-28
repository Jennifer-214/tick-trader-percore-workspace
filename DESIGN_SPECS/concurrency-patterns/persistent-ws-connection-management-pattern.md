---
type: concurrency-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-28
landing_ship: v5.15.5.F.4d.1.E.3
canonical_applications:
  - v5.15.5.F.4d.1.E.3 (Binance /ws-api/v3 persistent connection)
sister_specs:
  - framework-patterns/tls-session-resumption-pattern.md (sister; reconnect optimization)
  - framework-patterns/per-exchange-submit-protocol-selection.md (FOREACH_EXCHANGE submit_protocol column)
  - concurrency-patterns/io-uring-kernel-bypass-pattern.md (sister at .E.4; replaces userspace I/O)
tags: [concurrency, websocket, persistent-connection, reconnect, keepalive]
surface: [exchange-connection, ws-api]
applies_at_skills: [/precoding-audit-gate, /latency-track]
---

# Persistent WS connection management pattern

**Pattern intent:** Long-lived WebSocket connection per cluster. Pre-warmed TLS at engine boot. Ping/pong keepalive. Reconnect with exponential backoff + TLS session resumption. Cluster-level halt on prolonged outage.

## Problem statement

Per-submit REST connection lifecycle: TCP connect + TLS handshake + HTTP request + response + TCP close. ~70-90ms per submit; handshake dominates.

Persistent WS connection lifecycle: open ONCE at engine boot; submits = WS frames over open connection. ~50ms per submit (network RTT only; no handshake).

**Net savings: ~15-25ms per submit.**

For Binance: `/ws-api/v3` endpoint specifically supports order operations over persistent WS.

## Pattern description

### Connection lifecycle

```
[Engine Boot]
    ↓
[CONNECTING]: TCP connect + TLS handshake + WS upgrade + auth
    ↓
[CONNECTED]: ready to send/receive WS frames
    ↓ Keepalive: ping every 30s; wait pong; reconnect on timeout
    ↓ On disconnect: → [RECONNECTING] → [CONNECTING]
    ↓ Operator halt: → [CLUSTER_HALTED]
    ↓ Engine shutdown: → [DISCONNECTING] → close
```

### Connection state machine (per `.E.3` plan body)

```cpp
enum WSConnectionState : uint8_t {
    WS_STATE_DISCONNECTED  = 0,
    WS_STATE_CONNECTING    = 1,
    WS_STATE_CONNECTED     = 2,
    WS_STATE_RECONNECTING  = 3,
    WS_STATE_DISCONNECTING = 4,
    WS_STATE_CLUSTER_HALTED = 5,
    WS_STATE_TERMINATED    = 6,
};

struct alignas(64) PersistentWSConnection {
    char endpoint[256];
    int socket_fd;
    SSL* ssl_state;
    SSL_SESSION* cached_session;             // for resumption

    alignas(64) struct {
        std::atomic<uint8_t> state;
        std::atomic<uint64_t> connected_us;
        std::atomic<uint64_t> last_ping_us;
        std::atomic<uint64_t> last_pong_us;
        std::atomic<uint32_t> reconnect_count;
    } health;

    alignas(64) struct {
        uint64_t next_request_id;
        SPSCRing<RequestPending, 256> in_flight;
    } protocol;

    pthread_t keepalive_thread;
};
```

### Reconnect with exponential backoff

```cpp
void WSKeepalive_Run(PersistentWSConnection* conn) {
    uint64_t backoff_us = 1*1000*1000;  // start at 1s
    const uint64_t MAX_BACKOFF_US = 60*1000*1000;  // cap at 60s

    while (!shutdown_flag) {
        if (conn->health.state.load() == WS_STATE_CONNECTED) {
            // Ping every 30s; reconnect if pong missed
            WSFrame_SendPing(conn);
            uint64_t deadline = NowUs() + 5*1000*1000;
            while (NowUs() < deadline) {
                if (conn->health.last_pong_us >= conn->health.last_ping_us) break;
                usleep(100*1000);
            }
            if (NowUs() >= deadline) {
                LOG_WARN("WS pong timeout; reconnecting");
                PersistentWSConnection_Reconnect(conn);
                backoff_us = 1*1000*1000;  // reset on successful reconnect
            }
            usleep(25*1000*1000);  // sleep 25s; next ping
        } else if (conn->health.state.load() == WS_STATE_DISCONNECTED) {
            usleep(backoff_us);
            PersistentWSConnection_Reconnect(conn);
            backoff_us = std::min(backoff_us * 2, MAX_BACKOFF_US);
        }
    }
}
```

### TLS session resumption (per sister spec)

Engine caches `SSL_SESSION*` after successful handshake. On reconnect, `SSL_set_session(new_ssl, cached_session)` skips handshake. Saves ~20-50ms on reconnect.

Per `framework-patterns/tls-session-resumption-pattern.md`.

### In-flight request correlation

Each submit assigns unique `request_id`. Engine pushes `{request_id, original_cmd, send_ts}` to in_flight ring. Response handler pops by request_id.

On disconnect mid-request:
- cfg flag `reconnect_retry_inflight = true|false`
- TRUE: retry via idempotent submit (client_order_id ensures no double-submit)
- FALSE: fail-loud; operator triage

### Cluster-level halt threshold

```
# configs/clusters/binance/cluster.cfg:
ws_outage_threshold_minutes = 10
```

If reconnect_count > threshold OR outage duration > threshold:
- Set cluster_kill_flag
- Aggregator detects + mirrors to per-node kill flags
- Operator webhook alert
- Engine continues running but halts trading on this cluster

## Stage progression criteria

- **Stage 3 first canonical** (`.E.3`): Binance /ws-api/v3 persistent connection
- **Stage 4 cohort** (when 2nd application: e.g., Coinbase Pro WS): pattern proven
- **Stage 5 CLAUDE.md** (3rd application): promoted

## Anti-patterns avoided

- **REST-per-submit** — handshake overhead per submit
- **No reconnect logic** — single disconnect = permanent failure
- **Aggressive reconnect storms** — IP-ban risk
- **No outage threshold** — cluster trades despite prolonged unavailability

## Cross-references

- Sister: `framework-patterns/tls-session-resumption-pattern.md`
- Sister: `framework-patterns/per-exchange-submit-protocol-selection.md`
- Sister: `concurrency-patterns/io-uring-kernel-bypass-pattern.md` (at `.E.4`; integrates)
- First application: `plans/v5.15-live-readiness/subplans/2026-05-28-v5.15.5.F.4d.1.E.3-ws-api-persistent-connections.md`
