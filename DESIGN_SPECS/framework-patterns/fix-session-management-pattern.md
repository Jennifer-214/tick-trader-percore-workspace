---
type: framework-pattern
stage: 2-draft
version: 1.0
established: 2026-05-28
landing_ship: v5.15.5.F.4d.1.E.7 (DEFERRED; operator-triggered)
sister_specs:
  - framework-patterns/foreach-exchange-meta-registry-pattern.md
  - concurrency-patterns/persistent-ws-connection-management-pattern.md (sister; different protocol family)
tags: [framework-discipline, fix-protocol, session-management, sequence-numbers]
surface: [fix-adapter, ibkr-protocol]
---

# FIX session management pattern (Stage 2 DRAFT)

**Pattern intent:** Long-lived FIX 4.4+ session for institutional exchanges (IBKR; CME; etc.). Sequence number tracking. Reconnect with logon + resend. Heartbeat. Stage 2 DRAFT; lands when operator adds FIX-based exchange.

## Pattern

```cpp
struct FIXSessionState {
    char sender_comp_id[32];
    char target_comp_id[32];
    char endpoint[256];

    // CRITICAL: sequence numbers
    std::atomic<uint64_t> next_outgoing_seqnum;
    std::atomic<uint64_t> last_incoming_seqnum;

    int socket_fd;
    SSL* ssl_state;
    std::atomic<uint8_t> session_state;     // LOGGED_OUT/LOGGING_ON/LOGGED_ON/DISCONNECTING

    uint64_t heartbeat_interval_us;
    std::atomic<uint64_t> last_received_us;
    std::atomic<uint64_t> last_sent_us;

    PersistentMsgStore msg_store;             // mmap'd; survives crashes
};
```

## Logon + resend protocol

```cpp
void FIXSession_Logon(FIXSessionState* sess) {
    FIXMessage msg;
    msg.SetMsgType("A");
    msg.SetField(98, "0");                    // EncryptMethod=None (TLS handles)
    msg.SetField(108, sess->heartbeat_interval_us / 1000000);  // HeartBtInt
    SendMessage(sess, msg);
    sess->session_state.store(LOGGING_ON);
}

void FIXSession_HandleResendRequest(FIXSessionState* sess, FIXMessage& msg) {
    uint64_t begin = msg.GetIntField(7);
    uint64_t end = msg.GetIntField(16);
    for (uint64_t seq = begin; seq <= end; ++seq) {
        FIXMessage stored = sess->msg_store.Retrieve(seq);
        ResendMessage(sess, stored);
    }
}

void FIXSession_HandleSequenceGap(FIXSessionState* sess, uint64_t expected, uint64_t received) {
    if (received > expected) {
        // Gap; send ResendRequest
        SendResendRequest(sess, expected, received - 1);
    } else if (received < expected && !msg.GetBoolField(43)) {
        // Duplicate without PossDup; disconnect + re-logon
        FIXSession_Disconnect(sess);
        FIXSession_Logon(sess);
    }
}
```

## Stage progression

- **Stage 2 DRAFT**: codified at `.E.0` time; reference for future
- **Stage 3 first canonical**: when operator adds IBKR (or any FIX-based exchange) — operator-triggered

## Cross-references

- Sister: `concurrency-patterns/persistent-ws-connection-management-pattern.md` (WS analog)
- Operator: `plans/v5.15.5.F.4d.1.E.7-ibkr-exchange.md` (deferred reference)
