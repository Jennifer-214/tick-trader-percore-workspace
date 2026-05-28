---
type: concurrency-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-28
landing_ship: v5.15.5.F.4d.1.E.2
canonical_applications:
  - v5.15.5.F.4d.1.E.2 (categorized JSONL audit logs + optional SHA-256 chain)
sister_specs:
  - framework-patterns/built-in-observability-pattern.md (sister; observability surface)
  - meta-disciplines/structural-enforcement-when-memory-insufficient.md (M7; audit log is forensic record)
tags: [concurrency, audit-log, jsonl, structured-logging, sha256-chain]
surface: [audit-log, observability, compliance]
applies_at_skills: [/precoding-audit-gate]
---

# Structured audit log pattern

**Pattern intent:** Engine emits audit events as JSONL (one JSON per line). Multiple categorized files: trades / state-changes / commands / errors / metrics-checkpoint. Optional SHA-256 hash chain for tamper-evident logging (cfg-driven; default off).

## Problem statement

Engine produces substantial event flow:
- Every fill (trade event)
- Every state change (cfg reload; node start/stop; kill switch transition)
- Every command received (operator action audit trail)
- Every error condition
- Periodic metric checkpoints (latency histograms; etc.)

Without structured logging: hard to grep; hard to feed into log-analysis tools; tamper-evident not possible.

With JSONL + categorized files + optional chain: queryable; tool-friendly; forensic-grade.

## Pattern description

### File structure

```
/var/lib/fox/audit/   (production)
~/.local/share/fox/audit/  (dev)

├── trades.jsonl                 # every fill, order, cancel
├── state-changes.jsonl          # every cfg reload, node start/stop, kill switch transitions
├── commands.jsonl               # every fox-cli command received (operator action audit trail)
├── errors.jsonl                 # every error condition
└── metrics-checkpoint.jsonl     # periodic metric snapshots (latency; rate; etc.)
```

### Event format (JSONL; one JSON per line)

```json
{"ts":"2026-05-28T14:23:17.123456Z","ts_ns":1735653797123456000,"category":"trades","engine_version":"5.15.5.F.4d.1.E.2","software_version":"0.1.0","deployment_id":"caramel-laptop-001","event_type":"fill","cluster":"binance","node_id":0,"subaccount_id":0,"symbol":"BTCUSDT","side":"buy","qty":"0.05","price":"43250.50","client_order_id":"C0_S0_N0_123","strategy":"momentum_v3.1"}
```

```json
{"ts":"2026-05-28T14:24:01.456789Z","category":"state-changes","event_type":"node_pause","cluster":"binance","node_id":3,"reason":"operator","operator_principal":"caramel"}
```

```json
{"ts":"2026-05-28T14:25:00.000000Z","category":"commands","event_type":"transfer_funds","cluster":"binance","from_subaccount":0,"to_subaccount":2,"amount":"1000","asset":"USDT","status":"success","tran_id":1234567890}
```

```json
{"ts":"2026-05-28T14:26:15.234567Z","category":"errors","event_type":"submit_failed","cluster":"binance","node_id":1,"client_order_id":"C0_S1_N1_124","error_code":-2010,"error_msg":"Insufficient balance"}
```

### Categorized writer threads (per-category)

```cpp
struct AuditLogWriter {
    int fd;                                   // file descriptor
    SPSCRing<AuditEventCompact, 4096> queue;  // engine writes; writer thread reads
    pthread_t writer_thread;
    // Optional SHA-256 chain
    bool chain_enabled;
    uint8_t prev_hash[32];                    // previous entry's hash
};

void AuditLog_Append(AuditLogWriter& writer, const AuditEvent& event) {
    AuditEventCompact compact = CompactAuditEvent(event);
    SPSCRing_Push(&writer.queue, compact);
}

void AuditLog_WriterThread(AuditLogWriter& writer) {
    while (!shutdown_flag) {
        AuditEventCompact event;
        if (SPSCRing_TryPop(&writer.queue, &event)) {
            char json_buf[2048];
            int len = SerializeToJSON(event, json_buf, sizeof(json_buf));

            // Optional SHA-256 chain
            if (writer.chain_enabled) {
                uint8_t hash[32];
                SHA256_Hash(json_buf, len, &writer.prev_hash, 32, hash);
                char chain_buf[100];
                int chain_len = snprintf(chain_buf, sizeof(chain_buf),
                                          ",\"prev_hash\":\"%s\",\"hash\":\"%s\"",
                                          HexEncode(writer.prev_hash),
                                          HexEncode(hash));
                // Splice chain fields into JSON before closing }
                InsertBeforeClose(json_buf, &len, chain_buf, chain_len);
                memcpy(writer.prev_hash, hash, 32);
            }

            json_buf[len++] = '\n';
            write(writer.fd, json_buf, len);
        } else {
            usleep(1000);  // 1ms sleep on empty queue
        }
    }
}
```

### Optional SHA-256 hash chain (tamper-evidence)

Each entry includes:
- `prev_hash`: SHA-256 of previous entry
- `hash`: SHA-256 of this entry (excluding `hash` field itself)

If any entry tampered, hash chain breaks; operator can verify integrity:

```bash
# Verify chain integrity
fox-cli verify-audit-chain --file /var/lib/fox/audit/trades.jsonl
# Output: CLEAN or POSITION <N> CORRUPTED
```

cfg-driven; default OFF (chain overhead small but adds ~100 bytes per entry; some operators don't need tamper-evidence).

### Log rotation

Standard logrotate config:

```
/var/lib/fox/audit/*.jsonl {
    daily
    rotate 90
    compress
    delaycompress
    notifempty
    create 600 fox fox
    postrotate
        # Engine has open fd; need signal to reopen
        /usr/bin/fox-cli rotate-audit-log || true
    endscript
}
```

90-day retention default (cfg-driven; per D-49 `audit_retention_days`).

### Query patterns

```bash
# Recent fills for specific node
jq -c '.cluster=="binance" and .node_id==0 and .event_type=="fill"' /var/lib/fox/audit/trades.jsonl | tail -20

# Errors in last hour
SINCE=$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S)
jq -c "select(.ts > \"$SINCE\")" /var/lib/fox/audit/errors.jsonl

# Operator command history
jq '.event_type' /var/lib/fox/audit/commands.jsonl | sort | uniq -c | sort -rn

# Daily P&L from trades
jq -c '.event_type=="fill" | {ts: .ts[:10], pnl: .net_pnl}' /var/lib/fox/audit/trades.jsonl | \
  awk -F'"ts":"' '{print $2}' | awk -F'"' '{print $1}' | sort | uniq -c
```

## Stage progression criteria

- **Stage 3 first canonical** (`.E.2`): 5 categorized files + JSONL + optional SHA-256 chain
- **Stage 4 cohort** (when 2nd application: e.g., per-cluster log split): pattern proven
- **Stage 5 CLAUDE.md** (3rd application): promoted

## Anti-patterns avoided

- **Unstructured logs** — hard to query
- **Single log file** — mixing event types makes filtering complex
- **Synchronous logging on hot path** — H7 violation; SPSC queue + writer thread
- **No tamper-evidence option** — limits forensic / compliance use cases

## Cross-references

- Sister: `framework-patterns/built-in-observability-pattern.md`
- Sister: `meta-disciplines/structural-enforcement-when-memory-insufficient.md`
- First application: `plans/v5.15-live-readiness/subplans/2026-05-28-v5.15.5.F.4d.1.E.2-headless-configs-docs.md`
