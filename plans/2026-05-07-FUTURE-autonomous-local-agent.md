# FUTURE — Autonomous Local-Agent Operation (v5.12+ candidate)

**Status:** EXPLORATION — not committed, no kickoff date.
**Branch state:** N/A — when activated, would warrant its own feature branch
**Effort estimate:** Massive — 2-4 week sprint minimum, possibly multi-month
  if full autonomy is the goal. Phased shipping recommended.
**Date opened:** 2026-05-07
**Trigger:** operator got local LLM models installed; mused about
"headless mode where a local agent can operate this stuff"

---

## Goal

Enable a local LLM agent (running on operator's hardware, no
external API calls) to operate the trading workflow autonomously:
collect features, train models, validate, paper-test, iterate on
hyperparameters / horizons / TP-SL, surface promising candidates
for operator review. Live trading deployment ALWAYS requires
explicit operator HMAC-signed approval — agent never crosses that
boundary.

This frees the operator from being the bottleneck for the
rate-limiting workflow steps (waiting for collect, eyeballing WF
results, picking next experiment).

## Why this is non-trivial

The system is mostly GUI-driven on the suite side. Engine binaries
are CLI-callable, but the orchestration logic (Collect → Train →
Validate → Save Run) lives entirely in ImGui click handlers in
`Backtest/BacktestPanels.hpp`. An autonomous agent can't click ImGui
buttons.

Two paths forward (Path A is simpler, Path B is more general):

### Path A — CLI front-end mirroring the GUI workflow

Add `./bin/foxml_suite_cli` that exposes the same workers but via
command-line + JSON I/O.

  ./bin/foxml_suite_cli collect-features \
    --files data/BTCUSDT/2026-04-*.csv \
    --label peak_valley_stable \
    --output-json status.json

  ./bin/foxml_suite_cli train \
    --horizons 1000,7500,15000 \
    --tp 0.03,0.05,0.07 \
    --sl 0.03,0.05,0.07 \
    --run-name agent_run_001 \
    --output-json results.json

  ./bin/foxml_suite_cli validate-existing \
    --model models/classification/agent_run_001_horizon_1000/barrier.json \
    --output-json validation.json

Agent invokes via shell, parses JSON, decides next action.

**Pros:** Easy to bootstrap. Existing workers (`train_multi_horizon_worker_fn`
etc.) refactored to take a `WorkerArgs` struct + emit JSON instead of
mutating GUI state.

**Cons:** Spawning a subprocess per command is heavy. Status updates
mid-run are awkward (poll output file). Cancellation requires SIGTERM.

### Path B — Long-running daemon + RPC

`./bin/foxml_daemon` runs continuously, exposes a Unix socket or HTTP
endpoint with an RPC interface (gRPC, JSON-RPC, or simple HTTP+JSON).
Agent connects, issues commands, gets streaming status back.

  POST /v1/collect-features
  GET  /v1/status (returns current job state + progress)
  POST /v1/train
  POST /v1/cancel
  GET  /v1/runs (lists past runs with metrics)
  GET  /v1/stamp/<run-name> (returns stamp body for audit)

**Pros:** Clean streaming status. One process owns all state. Agent
can monitor in-progress runs. Same daemon could also serve a web
dashboard for operator monitoring.

**Cons:** Daemon lifecycle management. Bigger initial code surface.
RPC framework choice is bikeshed-prone.

**Recommendation:** Path A first as MVP (1-2 weeks). Path B if Path A
proves insufficient (probably 1-2 months for full daemon + RPC + web
dashboard).

## Already in place (no work needed)

- **Engine binaries are CLI-driven**: `./bin/engine_test`, `./bin/engine`
  — TUI is display-only, doesn't gate operations. Agent can start +
  stop the engine via shell.
- **Configs are text-readable/writable**: agent can edit `engine.cfg`,
  `backtest.cfg` between runs. No GUI lock.
- **Structured outputs**: health log is JSONL. Per-symbol metrics +
  order history are CSV. Stamp body is parseable HMAC-signed text.
  Summary.txt per run is human-and-machine-readable. Agent can ingest
  all of these without scraping.
- **Stamps are HMAC-signed**: agent can verify model integrity before
  acting on it (catches "trained model corrupted" failure mode).
- **CHANGELOG / CODE_MAP / KNOWN_ISSUES are markdown**: agent can
  read project state to inform decisions.

## What needs building

### Phase 1 — CLI front-end (Path A MVP)

1. **Refactor workers** (~3 days): extract `train_multi_horizon_worker_fn`,
   `collect_multi_horizon_worker_fn`, `fullvalidation_worker_fn` from
   GUI-state-coupled to operate on `WorkerArgs` struct + emit
   `WorkerResult` struct. ImGui click handlers become thin adapters
   that call the same workers + render results.

2. **CLI binary** (~2 days): new `cli/foxml_suite_cli.cpp` parses argv,
   builds WorkerArgs, calls workers, serializes WorkerResult to JSON
   on stdout. Mode: blocking (waits for completion) + status output to
   stderr.

3. **JSON serialization** (~1 day): existing FullValidationResults +
   WalkForwardResults + per-horizon stamp body need to_json() helpers.
   Keep simple — flat JSON, no nested cleverness.

4. **Build target** (~1 hour): `./build.sh cli` adds the new binary.

5. **Tests** (~1 day): smoke test for each subcommand. Validate JSON
   output schema. Ensure CLI produces bytewise-identical models to
   GUI for the same inputs (parity check).

**Total Phase 1: ~7-10 days.** Agent can now drive train+validate
loops via shell. No live-trading interaction yet.

### Phase 2 — Engine status + control endpoints

6. **Engine status JSON** (~2 days): `./bin/engine_test --status-json`
   returns position state, equity, recent trades, health summary.
   Agent can monitor live engine without parsing TUI.

7. **Engine control via cfg + HUP signal** (~1 day): agent writes new
   engine.cfg, sends SIGHUP, engine reloads non-hot fields. Already
   partly works for some fields; audit + complete coverage.

8. **Run-history API** (~2 days): `./bin/foxml_suite_cli list-runs`
   returns all past runs with WF + held-out + gap metrics. Agent can
   pick best-performer for a paper-test slot.

**Total Phase 2: ~5 days.** Agent can monitor + control deployed
engines (still no live-trading-without-approval boundary; that's
next).

### Phase 3 — Live-trading approval boundary

9. **Operator-signed approval tokens** (~3 days): agent decides "this
   model is good"; operator inspects + signs an approval token (HMAC
   over model_path + cfg snapshot). Engine refuses to enter live mode
   without a valid approval token in cfg. Agent can't generate the
   token (operator's signing key never reaches agent).

10. **Audit trail** (~2 days): every agent action logged to
    `agent_runs/agent_audit.jsonl` with timestamp + cmd + outcome +
    operator-approval-status. Operator can review what agent did
    after-the-fact.

**Total Phase 3: ~5 days.** Live-trading boundary enforced. Operator
keeps final authority.

### Phase 4 — Agent orchestration layer

11. **Agent prompts + scripts**: operator-side. Configure local LLM
    (e.g. via Ollama / llama.cpp) with a system prompt describing the
    workflow. Agent loop: list runs → identify gap-worst horizons →
    propose retrain with new TP/SL → call CLI → wait → parse results
    → repeat. Operator-side; no engine code change.

12. **Cost / quality gates**: agent loops can spin forever spending
    electricity. Add operator-side budget caps (max trainings/day,
    max GPU/CPU hours). Out of engine scope — operator's agent
    config concern.

**Total Phase 4: open-ended.** Operator-side configuration; engine
provides the building blocks.

## Risks + pitfalls

1. **Audit pollution** — agent generating thousands of trainings makes
   the past-runs list useless. Mitigation: agent must tag runs with
   experiment ID + auto-archive low-performers + run-quality scoring.

2. **Live-trading boundary leak** — agent figures out how to bypass
   approval (e.g. directly edits engine.cfg's `live_trading=1` field).
   Mitigation: live_trading flag MUST require HMAC-signed cfg, signed
   by operator's offline key. Agent never gets the key.

3. **Resource exhaustion** — agent loops + 1M-tick datasets + 8 horizons
   = disk/CPU/RAM exhaustion. Mitigation: budget caps per-day, auto-
   throttle, hard limit on concurrent jobs.

4. **Model overfit by tuning loop** — agent spamming hyperparam +
   horizon variations = looking-back fishing for the best validation
   accuracy. The held-out region becomes effectively training data
   over many iterations. Mitigation: rotating held-out region (use
   different held-out cuts each retrain) + walk-forward over time
   not just splits.

5. **Cost in inference** — local LLM running 24/7 is non-trivial
   electricity. Mitigation: agent runs on demand, not continuously.
   Trigger via operator command or cron schedule.

6. **Agent makes catastrophic cfg changes** — e.g. sets
   `kill_switch_enabled=0`. Mitigation: cfg validator that refuses
   safety-critical changes from agent (operator-only fields list).

7. **The agent isn't actually smart enough** — local LLMs (8B-70B)
   have variable reasoning quality. Agent might pick worse strategies
   than operator. Mitigation: agent-as-assistant first (suggests
   actions, operator approves), agent-as-driver later when proven.

## Re-trigger conditions

- Operator has a stable workflow they're tired of running manually
  (e.g. "I retrain weekly, run paper for 3 days, eyeball metrics" —
  exactly the kind of loop a local agent could automate)
- Local LLM hardware is sufficient (8-32GB VRAM for the agent's
  reasoning loop is probably enough; larger if doing strategy
  research)
- v5.11 sprint truly complete + paper-tested for weeks (no
  half-finished surfaces to confuse the agent)
- Operator wants to step back from day-to-day operation but keep
  authority over live-trading deployments

## NOT in scope (just so it's clear)

- Agent makes trading decisions LIVE (forbidden — engine decides via
  trained model + risk gates; agent only operates training loop)
- Agent picks symbols / markets to trade (operator decides; agent
  works within the symbol set operator provides)
- Engine architecture changes for the agent's benefit (engine stays
  pure; agent works around it via CLI/RPC layer)
- Cloud / external API integration (purely local agent; that's the
  point — no external dependencies for the operator's workflow)

## Predecessor / related work

- v5.11.41-44 multi-horizon pipeline (the workflow agent would drive)
- v5.11.45 `tools/validate_feature_mask.sh` (agent-friendly validation
  pattern; CLI tools that emit pass/fail)
- existing `tools/stamp_model.sh` (CLI-callable stamp manipulation;
  pattern for the new CLI front-end)
- `controller_test` (existing CLI test harness; pattern for headless
  test mode)

## NOT a current commitment

This file documents the DIRECTION, not a planned ship. Operator
opened it 2026-05-07 as exploration after installing local LLM
models. To activate: operator decides to start, kicks off Phase 1,
and this file becomes the v5.12.0 master plan.

Until then: Claude sessions can refer to this for "what does
autonomous operation look like?" but should NOT auto-implement
without operator kickoff.
