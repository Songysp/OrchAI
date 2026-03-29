# OrchAI — CLI-First AI Orchestrator

> Zero-Cost. Zero-Infrastructure. CLI-Native.

OrchAI is a local CLI orchestration platform that enables collaborative workflows between specialized AI agents. No servers, no cloud subscriptions, no message queues — just a terminal and a config file.

---

## Overview

| Principle | What it means |
|---|---|
| **CLI-First** | Entrypoint is `orchai` or `python -m apps.cli.main`. No web server required to run. |
| **Zero-Cost** | Uses the Claude CLI binary already on your machine. No API keys burned unless you choose API mode. |
| **Hybrid Driver** | Transparently switches between `claude` CLI subprocess and the Anthropic API. |
| **No Infrastructure** | SQLite for tracing, flat files for storage. Runs entirely on localhost. |

---

## Quick Start

```bash
# Install dependencies
pip install -e .

# Interactive shell (stays open and keeps conversation context)
orchai

# Single-turn chat with the AI worker
orchai chat "Explain the repository structure"

# Full Planner → Worker → Refiner orchestration loop
orchai orchestrate "Build a Python function to parse JSON logs"

# With options
orchai orchestrate "Refactor the config loader" \
    --mode api \
    --model claude-opus-4-6 \
    --max-turns 5
```

If you are running from the repository root on Windows, `orchai.cmd` lets you launch the shell without installing the package first.

When no `--provider` is supplied, OrchAI shows a startup menu:
1. `Claude CLI`
2. `Claude API`
3. `Gemini` (current repo implementation is a stub)
4. `Codex` (current repo implementation is a stub)

---

## Architecture

### Planner → Worker → Refiner Loop

```
User Prompt
    │
    ▼
┌─────────┐     task plan      ┌─────────┐
│ Planner │ ────────────────► │ Worker  │
│ (Claude)│                    │ (Claude)│
└─────────┘                    └────┬────┘
     ▲                              │ implementation
     │  architect feedback          ▼
     │                        ┌─────────┐
     └────────────────────── │ Refiner │
          DONE / escalate     │ (Claude)│
                              └─────────┘
```

- **Planner** — decomposes the user goal into a clear task plan.
- **Worker** — implements the plan, turn by turn.
- **Refiner** — reviews the output, either marks `DONE` or sends feedback back to Worker.
- **Architect** — escalation path when the loop cannot converge within `--max-turns`.

### Directory Structure

```
apps/
  cli/                  # Typer entrypoint + Rich UI
  orchestrator/         # FastAPI app (optional, for future dashboard)
    api/routes/         # REST endpoints (projects, tasks, approvals…)
    services/           # Orchestration and ingress services
    workflows/          # Representative + Council workflows

packages/
  agents/               # AI adapter layer
    claude_adapter.py   # Hybrid CLI/API driver
    drivers/
      claude_cli.py     # subprocess driver
      claude_api.py     # Anthropic SDK driver
  config/               # Config loader + service + models
  domain/               # Shared data models (Project, Task, Turn…)
  orchestrator/         # HiveOrchestrator engine
  storage/              # File-based stores (Project, Task, Decision…)
  chat/                 # Platform-neutral message abstractions (base only)

tests/                  # pytest suite
docs/                   # Design documents and pivot history
```

---

## The OrchAI Quartet (4-Agent Team)

Each major work session operates as a four-agent collaborative team:

| Role | Agent | Responsibility |
|---|---|---|
| **Lead Architect** | Gemini | Overall goal alignment. **Final Approval Gate** — no task is DONE without `APPROVED`. |
| **Engine Specialist** | Claude (this session) | Core logic implementation. Directs CLI tools and agent parallelism. |
| **Critic / Auditor** | Codex | Conceptual audit. Flags deviations from CLI-First and Zero-Infrastructure principles. |
| **Testing Specialist** | pytest | Verifies correctness. Blocks tasks if `pytest` fails or coverage is insufficient. |

Rules:
- No agent marks their own task `DONE` without Gemini review.
- Every implementation is audited by Codex before submission.
- Every summary begins with: *[CONCEPT CHECK] CLI-First, Hybrid Driver, No-Infra.*

---

## Configuration

```bash
# config.json (project root) — minimal example
{
  "platform": {
    "default_driver": "cli",
    "default_model": "claude-sonnet-4-6"
  }
}
```

Full config schema: [`packages/config/models.py`](packages/config/models.py)

---

## Task Board

| Task | Description | Status |
|---|---|---|
| T1 | Hybrid ClaudeAdapter (CLI + API drivers) | DONE |
| T2 | Config loader + service | DONE |
| T3 | HiveOrchestrator engine | DONE |
| T4 | CLI entrypoint (`apps/cli/main.py`) | DONE |
| T5 | Domain models (Project, Task, Turn) | DONE |
| T6 | File-based storage layer | DONE |
| T7 | Integration tests (`test_hive_logic.py`) | DONE — 2/2 passing |
| T8 | Legacy Slack/Discord adapter cleanup | DONE — stubbed out |

---

## Tech Stack

| Layer | Technology |
|---|---|
| CLI | [Typer](https://typer.tiangolo.com/) + [Rich](https://rich.readthedocs.io/) |
| AI Driver | Claude CLI subprocess / Anthropic Python SDK |
| Storage | Flat files (JSON) + SQLite trace |
| Config | JSON + Pydantic v2 models |
| Tests | pytest + pytest-asyncio |
| Optional API | FastAPI (for future dashboard — not required to run) |

---

## References

- **Pivot Rationale:** [`docs/CLI_ORCHESTRATOR_PIVOT.md`](docs/CLI_ORCHESTRATOR_PIVOT.md)
- **Active Tasks:** [`task.md`](task.md)
- **Operations Manual:** [`docs/OPERATIONS_MANUAL.md`](docs/OPERATIONS_MANUAL.md)
