---
type: framework-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-28
landing_ship: v5.15.5.F.4d.1.E.3
canonical_applications:
  - v5.15.5.F.4d.1.E.3 (cached SSL_SESSION on reconnect)
sister_specs:
  - concurrency-patterns/persistent-ws-connection-management-pattern.md (parent; reconnect logic)
tags: [framework-discipline, tls-resumption, reconnect-optimization]
surface: [tls-connection, reconnect-path]
---

# TLS session resumption pattern

**Pattern intent:** Cache `SSL_SESSION*` post-handshake. On reconnect, `SSL_set_session()` enables 0-RTT or 1-RTT resumption. Saves ~20-50ms handshake overhead.

## Pattern

```cpp
struct PersistentWSConnection {
    SSL_SESSION* cached_session;
    // ... other fields ...
};

void PersistentWSConnection_Connect(PersistentWSConnection* conn) {
    conn->socket_fd = TcpConnect(conn->endpoint);
    conn->ssl_state = SSL_new(g_ssl_ctx);
    SSL_set_fd(conn->ssl_state, conn->socket_fd);

    // Attempt resumption if we have cached session
    if (conn->cached_session) {
        SSL_set_session(conn->ssl_state, conn->cached_session);
    }

    SSL_connect(conn->ssl_state);

    // Post-handshake: check if resumption succeeded
    if (SSL_session_reused(conn->ssl_state)) {
        LOG_INFO("TLS session resumed; ~20-50ms saved");
        MetricsCounter_Increment("tls.session_resumption_success");
    } else {
        LOG_INFO("TLS full handshake; caching session ticket");
        if (conn->cached_session) SSL_SESSION_free(conn->cached_session);
        conn->cached_session = SSL_get1_session(conn->ssl_state);
        MetricsCounter_Increment("tls.session_resumption_miss");
    }
}

void PersistentWSConnection_Cleanup(PersistentWSConnection* conn) {
    if (conn->cached_session) {
        SSL_SESSION_free(conn->cached_session);
        conn->cached_session = nullptr;
    }
}
```

## Operational monitoring

Prometheus metric `fox_tls_session_resumption_rate{cluster}` should be > 90% in production. Alert if drops below threshold (indicates server-side ticket lifetime shorter than expected).

## Limitations

- Session tickets have lifetime (Binance: typically 24-48h)
- TLS 1.3 PSK resumption preferred over TLS 1.2 session ID
- Fallback: if resumption rejected, full handshake (no error; just slower)

## Cross-references

- Parent: `concurrency-patterns/persistent-ws-connection-management-pattern.md`
- First application: `plans/v5.15.5.F.4d.1.E.3-ws-api-persistent-connections.md`
