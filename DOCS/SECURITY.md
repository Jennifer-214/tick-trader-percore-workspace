# Security

**Audience:** Operator + contributor. Security disciplines for engine deployment + operation.

For terminology: `DOCS/GLOSSARY.md`. For deployment: `DOCS/DEPLOYMENT_GUIDE.md`. For incident response: `DOCS/INCIDENT_RUNBOOK.md`.

---

## Threat model

The engine handles real funds via exchange APIs. Threats:

1. **API key compromise** — engine binary compromised; attacker exfiltrates keys
2. **Sub-account misuse** — keys with excess permissions (e.g., withdrawals enabled)
3. **Network MITM** — TLS misconfiguration; intercepted traffic
4. **Engine bug** — over-leveraging; runaway trading
5. **Operator mistake** — wrong command at wrong time
6. **Insider threat** — operator workstation compromised
7. **Supply chain** — dependency injection (liburing; openssl; etc.)

Each mitigated by layered defenses.

---

## API key permission discipline (CRITICAL)

Every sub-account API key MUST be configured with:

- ✅ `enableTrading = true`
- ✅ `enableSpotAndMarginTrading = true` (or futures-specific)
- ❌ `enableWithdrawals = false` (CRITICAL — engine refuses to start otherwise)
- ✅ IP-restricted to engine's deployment IP

Engine boot-time check queries exchange for actual permissions (not trusting cfg). If `canWithdraw=true`, engine REFUSES to start with explicit error:

```
FATAL: Sub-account 0 has canWithdraw=true on Binance; refusing to start.
       Fix at Binance API key management → uncheck "Enable Withdrawals".
```

Per `framework-patterns/per-node-economic-isolation-pattern.md`.

---

## Credentials storage

### env-var references in cfg (PREFERRED)

```
# configs/clusters/binance/credentials/sub_0.cfg:
api_key = ${BINANCE_SUB0_API_KEY}
api_secret = ${BINANCE_SUB0_API_SECRET}
```

Actual keys in:
- **systemd EnvironmentFile** (production): `/etc/fox/secrets.env`; `chmod 600 fox:fox`
- **direnv .envrc** (dev): `~/.envrc`; gitignored
- **HashiCorp Vault** (enterprise): vault agent renders secrets to file; engine reads

### What NOT to do

❌ Plain-text API keys in `cluster.cfg` (would be world-readable)
❌ API keys in git history (rotate immediately if leaked)
❌ Shared API key across sub-accounts (defeats isolation)
❌ Production keys on laptop / dev environment

### Permission discipline on credential files

```bash
sudo chmod 700 /etc/fox/configs/clusters/binance/credentials/
sudo chmod 600 /etc/fox/configs/clusters/binance/credentials/*.cfg
sudo chmod 600 /etc/fox/secrets.env
sudo chown -R fox:fox /etc/fox/
```

Only `fox` user (engine runtime) can read.

---

## Sub-account isolation (structural defense)

Per `framework-patterns/per-node-economic-isolation-pattern.md`:

- Each per-node binds to ONE sub-account
- Sub-accounts are INDEPENDENT trading entities on Binance
- Compromise of one sub-account's API key = bounded loss (that sub-account only)
- Losses isolated; rate budget independent; siblings unaffected

Per-sub-account capital partition: operator decides per-sub-account allocation. Smaller per-sub-account capital = bounded blast radius.

---

## IP restriction

Each sub-account API key restricted to engine's deployment IP. Configured at Binance API key management.

If engine IP changes (server migration; cloud instance):
1. Update IP restriction at Binance UI (one-time)
2. Engine re-validates IP at boot

Engine queries cluster's IP restriction at boot; refuses to start if not matching deployment IP.

---

## TLS configuration

- TLS 1.3 required (per `framework-patterns/tls-session-resumption-pattern.md`)
- Cipher suites: AES-GCM (preferred) or ChaCha20-Poly1305
- Server cert pinning optional (cfg-driven): `clusters/binance/cluster.cfg: pin_server_cert_sha256 = ...`
- Session tickets cached for resumption (sister: `tls-session-resumption-pattern.md`)

Engine refuses TLS < 1.3 connections; refuses unsupported ciphers; refuses unpinned cert if pinning enabled.

---

## Audit log integrity

Per `concurrency-patterns/structured-audit-log-pattern.md`:

Optional SHA-256 hash chain for tamper-evidence:
```
# configs/engine.cfg:
audit_log_hash_chain = true       # default false; opt-in
```

Each audit entry includes `prev_hash` + `hash`. Operator verifies chain integrity:
```bash
fox-cli verify-audit-chain --file /var/lib/fox/audit/trades.jsonl
# Output: CLEAN or POSITION <N> CORRUPTED
```

Tamper-evident: if attacker modifies audit log, hash chain breaks.

---

## Operator workstation security

Operator's laptop / dev machine:
- SSH keys with passphrase (not bare keys)
- ssh-agent for key forwarding (avoid copying keys to server)
- 2FA where possible (GitHub; Binance UI; etc.)
- Encrypted disk
- No production credentials on laptop (use env vars sourced from secure source)

---

## Supply chain

Engine dependencies:
- **OpenSSL** — system-installed; verify version + integrity at boot
- **liburing** — system-installed; AGPL-compatible (LGPL)
- **simdjson** — vendored or system; verify integrity
- **notcurses** (TUI) — system-installed

Each dependency:
- Tracked in build.sh
- Version pinned where possible
- License-audited (must be AGPL-compatible)
- Reviewed during /security-review skill execution

---

## Engine binary integrity

Production deployments:
- Reproducible builds (deterministic compilation)
- Binary checksums verified at install
- systemd unit verifies binary signature (if configured)

Operator can detect tampering via build reproduction:
```bash
./build.sh test --reproducible
sha256sum build/fox-engine
# Compare to expected checksum
```

---

## Webhook + Prometheus exposure

- Prometheus endpoint: 127.0.0.1:9091 (localhost only; per D-19)
- Webhook URL: cfg-driven; operator controls
- Audit log: only operator readable (chmod 600)

External attack surface: NONE by default. SSH tunneling provides remote access without opening external ports.

---

## Periodic security drills

Per `DOCS/DR_TESTING.md` + this doc:

- Quarterly: rotate sub-account API keys
- Quarterly: re-validate IP restrictions
- Quarterly: review audit log for anomalies
- Quarterly: dependency audit (check for CVEs)
- Quarterly: backup state file integrity check

Document each drill outcome.

---

## Incident response

Per `DOCS/INCIDENT_RUNBOOK.md` § "API key permissions audit at boot" + § "Sub-account suspension":

If credentials compromised:
1. IMMEDIATELY revoke API keys at Binance UI
2. Halt engine: `sudo systemctl stop fox-engine.service`
3. Rotate keys (new API keys with proper permissions)
4. Update cfg + secrets file
5. Restart engine; verify operation
6. Audit log review for any pre-revocation suspicious activity
7. Operator post-mortem

---

**End of SECURITY.md v1.0** (2026-05-28).
