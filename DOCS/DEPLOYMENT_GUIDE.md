# Deployment Guide

**Audience:** Operator deploying engine on a server (production) or laptop (dev).

For terminology: see `DOCS/GLOSSARY.md`. For architecture: see `DOCS/ARCHITECTURE_OVERVIEW.md`. For daily operations: see `DOCS/OPERATOR_MANUAL.md`.

---

## ⚠️ DO NOT 24/7 ON A LAPTOP

**Standard laptops are NOT suitable for 24/7 live trading deployment of this engine.** Sustained max-CPU + busy-poll patterns + 24/7 audit log writes WILL damage consumer-grade laptops (thermal failure; fan wear-out; battery degradation; SSD wear). Use a server (workstation; desktop; cloud instance). See `DOCS/HARDWARE_REQUIREMENTS.md` § "Hardware Safety Warning" for full discussion.

**Laptops are fine for:** development; backtesting; paper-test (finite duration; pause overnight); documentation. NOT for 24/7 live.

---

## Hardware requirements

### Production (server)

- **CPU:** 24+ cores recommended (Threadripper / EPYC / Xeon). 16 cores minimum tight.
- **Memory:** 32GB+ RAM (engine + viewer + monitoring)
- **Network:** Low-latency to exchange (colocated ideal; commodity broadband OK)
- **Storage:** 500GB+ SSD for state + audit logs + models
- **Kernel:** Linux 5.6+ (recommend 6.0+); kTLS module loaded; isolcpus + nohz_full kernel params
- **Hardware features:** SHA-NI (HMAC); AVX2 (FPN_Binary math); TSC (high-precision timing)

### Dev (laptop)

- **CPU:** 8+ cores
- **Memory:** 16GB+ RAM
- **Network:** Any
- **Kernel:** Linux 5.6+ recommended
- **Topology:** dev mode (OS-scheduled; no strict isolcpus)

---

## Production install (systemd service)

### Step 1: Build engine + viewers

```bash
cd /home/caramel/code/FoxML_Trader_v2
./build.sh test               # builds engine + tests
./build.sh strategies         # builds per-strategy .so files (for hot-reload at .E.X+)

# Install binaries (one-time)
sudo cp build/fox-engine /usr/local/bin/
sudo cp build/fox-tui /usr/local/bin/
sudo cp build/fox-cli /usr/local/bin/
sudo cp build/foxml-train /usr/local/bin/
```

### Step 2: Create system user + directories

```bash
sudo useradd -r -s /usr/sbin/nologin fox
sudo mkdir -p /var/lib/fox/state /var/lib/fox/audit /var/lib/fox/models
sudo mkdir -p /etc/fox/configs/clusters
sudo chown -R fox:fox /var/lib/fox /etc/fox
sudo chmod 700 /etc/fox/configs/clusters    # credentials restricted
```

### Step 3: Configure kernel (one-time; via boot parameters)

Edit `/etc/default/grub`:
```
GRUB_CMDLINE_LINUX_DEFAULT="isolcpus=4-23 nohz_full=4-23 rcu_nocbs=4-23 transparent_hugepage=always"
```

Apply:
```bash
sudo update-grub
sudo reboot
```

### Step 4: Provision Binance sub-accounts (one-time)

Per `DOCS/CONTRIBUTING/add-exchange.md` + `DOCS/OPERATOR_MANUAL.md`:

1. Binance UI → Sub-Accounts → Create N sub-accounts (recommended: 4 for dev; 8-16 for production)
2. For each sub-account: create API key (trade-only; IP-restricted; NO withdrawal)
3. Fund each sub-account via internal transfer from master

### Step 5: Set environment variables (credentials)

Create `/etc/fox/secrets.env`:
```
BINANCE_MASTER_API_KEY=...
BINANCE_MASTER_API_SECRET=...
BINANCE_SUB0_API_KEY=...
BINANCE_SUB0_API_SECRET=...
BINANCE_SUB1_API_KEY=...
BINANCE_SUB1_API_SECRET=...
# ... etc
```

```bash
sudo chmod 600 /etc/fox/secrets.env
sudo chown fox:fox /etc/fox/secrets.env
```

### Step 6: Create engine.cfg + cluster cfg + per-node cfgs

Use migration tool (if migrating from v5.X):
```bash
fox-migrate-cfg --from /etc/fox/old-engine.cfg --to /etc/fox/configs/
```

OR create fresh per `DOCS/CONTRIBUTING/add-cfg-field.md`. Sample structure:

```
/etc/fox/configs/
├── engine.cfg
├── clusters/
│   └── binance/
│       ├── cluster.cfg
│       ├── credentials/
│       │   ├── master.cfg
│       │   ├── sub_0.cfg
│       │   ├── sub_1.cfg
│       │   └── ...
│       └── nodes/
│           ├── node_0/
│           │   ├── core.cfg
│           │   ├── strategy.cfg
│           │   ├── ml.cfg
│           │   └── observability.cfg
│           └── ...
```

### Step 7: Install systemd unit

```bash
# Copy template from engine source
sudo cp /home/caramel/code/FoxML_Trader_v2/installation/fox-engine.service /etc/systemd/system/

# Or create manually:
sudo tee /etc/systemd/system/fox-engine.service <<'EOF'
[Unit]
Description=Fox HFT Trading Engine
After=network.target

[Service]
Type=simple
User=fox
Group=fox
EnvironmentFile=/etc/fox/secrets.env
ExecStart=/usr/local/bin/fox-engine --config-dir /etc/fox/configs/ --state-dir /var/lib/fox/state/
Restart=on-failure
RestartSec=5
LimitMEMLOCK=infinity
CPUAffinity=4-23
Nice=-20

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
```

### Step 8: Boot engine + verify

```bash
sudo systemctl enable fox-engine.service
sudo systemctl start fox-engine.service
sudo systemctl status fox-engine.service

# Check logs
sudo journalctl -u fox-engine.service -f

# Attach TUI
sudo -u fox fox-tui
```

### Step 9: (Optional) Install Prometheus + Grafana for monitoring

Standard install per their docs. Configure Prometheus scrape:

```yaml
# /etc/prometheus/prometheus.yml
scrape_configs:
  - job_name: 'fox-engine'
    static_configs:
      - targets: ['localhost:9091']
```

---

## Dev install (laptop; direct launch)

### Step 1: Build

```bash
cd /home/caramel/code/FoxML_Trader_v2
./build.sh test
./build.sh strategies
```

### Step 2: Configure (dev mode)

```bash
mkdir -p configs/clusters/binance/credentials configs/clusters/binance/nodes/node_0
# Set topology.mode = dev in configs/engine.cfg
# Use testnet credentials in configs/clusters/binance/credentials/
```

Source secrets (or use direnv):
```bash
export BINANCE_TESTNET_API_KEY=...
export BINANCE_TESTNET_API_SECRET=...
```

### Step 3: Run directly

```bash
./build/fox-engine --config-dir ./configs/ --state-dir ./state/

# In another terminal
./build/fox-tui
```

---

## SSH-tunneled remote access

Engine running on server; operator on laptop:

```bash
# Tunnel UDS for fox-cli + fox-tui
ssh -L /tmp/fox.sock:/var/run/fox/engine.sock server

# Local fox-tui via tunnel
fox-tui --socket /tmp/fox.sock

# Tunnel Prometheus for Grafana
ssh -L 9091:127.0.0.1:9091 server
# Grafana scrapes localhost:9091
```

---

## Troubleshooting

See `DOCS/INCIDENT_RUNBOOK.md` for common issues + responses.

---

**End of DEPLOYMENT_GUIDE.md v1.0** (2026-05-28).
