# Disaster Recovery Testing

**Audience:** Operator running periodic DR drills.

**Cadence:** Quarterly. Document each drill outcome.

---

## DR scenarios to test

### 1. Engine crash mid-trade

**Setup:** Engine running; active trading on multiple nodes.

**Test:**
```bash
# Find engine PID
PID=$(systemctl show -p MainPID --value fox-engine.service)

# Force kill (simulates segfault)
sudo kill -9 $PID
```

**Expected outcome:**
- systemd restarts engine within 5s
- Engine reads mmap state from disk
- Parallel reconcile per sub-account completes
- Engine resumes per `on_crash_restart_action = resume` (or operator's chosen policy)
- No double-submitted orders
- No missing fills

**Verify:**
```bash
# Compare positions before crash vs after recovery
# Check audit log for reconcile events
jq -c '.event_type=="reconcile_complete"' /var/lib/fox/audit/state-changes.jsonl | tail -5
```

### 2. Exchange API outage

**Setup:** Engine running.

**Test:**
```bash
# Block exchange API at firewall (1 minute test)
sudo iptables -A OUTPUT -d api.binance.com -j DROP
sleep 60
sudo iptables -D OUTPUT -d api.binance.com -j DROP
```

**Expected outcome:**
- Engine detects WS disconnect within ~30s
- Reconnect attempts with exponential backoff
- After firewall removed: reconnect succeeds; TLS session resumed
- Trading resumes within ~30s of API availability

**Verify:**
```bash
# Check reconnect_count metric
jq -c '.event_type=="ws_reconnect"' /var/lib/fox/audit/state-changes.jsonl | tail -5
```

### 3. Sub-account suspension simulation

**Setup:** Test against testnet.

**Test:** Manually revoke API key on Binance testnet UI.

**Expected outcome:**
- Engine detects consecutive submit failures
- Node halt after cfg threshold (default 10 consecutive)
- Webhook alert fired
- Sibling nodes continue trading

**Verify:** fox-tui shows specific node halted; others operational.

### 4. State file corruption

**Setup:** Engine running.

**Test:**
```bash
# Stop engine
sudo systemctl stop fox-engine.service

# Corrupt state file (testing only!)
sudo dd if=/dev/urandom of=/var/lib/fox/state/state.mmap bs=1M count=1 conv=notrunc

# Start engine
sudo systemctl start fox-engine.service
```

**Expected outcome:**
- Engine detects state file corruption (header validation fails)
- Engine refuses to start with clear error
- Operator must:
  - Restore from backup (if available)
  - Or manually reconcile against exchange truth

**Verify error message + recovery workflow.**

### 5. Clock drift simulation

**Setup:** Engine running.

**Test:**
```bash
# Disable NTP temporarily
sudo systemctl stop chrony

# Skew clock by 30s
sudo date -s "$(date -d '30 seconds ago')"
```

**Expected outcome:**
- Engine detects drift > recvWindow (5s)
- Submit errors with code -1022 (Binance signature invalid)
- Webhook alert fired
- Engine halts trading until clock corrected

**Cleanup:**
```bash
sudo systemctl start chrony
# Wait for NTP sync
sudo systemctl restart fox-engine.service
```

### 6. Disk full

**Setup:** Engine running.

**Test:**
```bash
# Fill disk (simulate runaway audit log)
sudo fallocate -l $(df --output=avail / | tail -1)K /tmp/fillit
```

**Expected outcome:**
- Engine detects disk full on audit log write
- Audit log writer thread halts; alert
- Trading continues (in-memory operations OK)
- State file flush may fail; engine emits alert

**Cleanup:**
```bash
sudo rm /tmp/fillit
```

### 7. Webhook receiver down

**Setup:** Engine running with webhook URL configured.

**Test:** Block webhook URL at firewall.

**Expected outcome:**
- Webhook send fails silently (logged in errors.jsonl)
- Engine continues operation (webhooks are best-effort)
- Operator alerted via Prometheus / fox-tui that webhook delivery is failing

### 8. fox-tui crash mid-monitoring

**Setup:** Engine + fox-tui running.

**Test:** Kill fox-tui process.

**Expected outcome:**
- Engine continues operation unaffected (viewer is read-only)
- Operator can re-attach: `fox-tui`
- No state loss

---

## DR drill template

For each quarterly drill, document:

```
## DR Drill: <Scenario> — <Date>

### Setup
- Engine version: ...
- Test environment: testnet / paper / live-small-cap
- Affected nodes: ...

### Steps executed
1. ...
2. ...

### Outcomes observed
- Time to detection: ...
- Time to recovery: ...
- Data loss: ...
- Operator actions required: ...

### Issues found
- ...

### Follow-up actions
- ...
```

---

## Backup discipline

```bash
# Daily backup (cron)
fox-cli backup-state --output /backup/fox-state-$(date +%Y%m%d).bin

# Retention: 30 days
find /backup/ -name "fox-state-*.bin" -mtime +30 -delete

# Verify backup integrity
fox-cli verify-state-file /backup/fox-state-2026-05-28.bin
```

---

**End of DR_TESTING.md v1.0** (2026-05-28).
