# Architecture

This repository is structured as a reusable platform, not a one-off app.

The system is designed to evolve into:

- a multi-project AI dev team platform,
- interchangeable Slack and Discord interfaces,
- a future web dashboard,
- later database-backed persistence.

## Repository structure

```text
apps/
  orchestrator/
    api/
    discord/
    slack/
    workflows/
    services/

packages/
  agents/
  chat/
  config/
  domain/
    models/
    services/
  execution/
  github/
  prompts/
    roles/
    system/
  rules/
  storage/
    base.py
    file_store/

configs/
data/
docs/
infra/
workspaces/
```

## Layer responsibilities

### `apps/orchestrator`

Application assembly layer for the running service.

- `api/`
  - FastAPI-facing HTTP entrypoints
  - should remain thin and delegate to reusable services
- `discord/`
  - Discord-specific application integration entrypoints
- `slack/`
  - Slack-specific application integration entrypoints
- `workflows/`
  - app-level workflow composition for representative and council flows
- `services/`
  - app-layer runtime assembly and dependency wiring

This layer may know about FastAPI and runtime composition, but it should not own domain rules.

### `packages/domain`

Reusable platform domain.

- `models/`
  - project, task, approval, decision, and conversation models
- `services/`
  - orchestration and lifecycle services

This layer must remain independent from Slack, Discord, and web concerns.

### `packages/storage`

Persistence abstraction layer.

- `base.py`
  - storage interfaces
- `file_store/`
  - file-backed MVP implementation

Future Postgres or Redis backends should be added here without breaking callers.

### `packages/chat`

Transport adapter layer.

- `base.py`
  - generic chat adapter contracts
- `slack_adapter.py`
  - Slack transport adapter
- `discord_adapter.py`
  - Discord transport adapter

Core orchestration should depend on these abstractions, not on Slack or Discord SDK details directly.

### `packages/agents`

Model-provider adapter layer.

- `base.py`
- `claude_adapter.py`
- `codex_adapter.py`
- `gemini_adapter.py`

This keeps provider choice swappable per role.

### `packages/prompts`

Prompt asset organization.

- `roles/`
  - role-specific prompts such as representative, planner, builder, critic, tester
- `system/`
  - system-level platform prompts

Prompt assets should remain reusable and free from project-specific hardcoding.

## Design rules

- keep project-specific behavior config-driven
- keep chat-platform behavior adapter-driven
- keep domain logic independent from route handlers
- keep orchestration logic reusable across chat and future web interfaces
- keep platform code separate from project workspaces

## Multi-project model

Each project is expected to define its own configuration for:

- repository metadata,
- workspace path,
- selected chat platform,
- logical channel bindings,
- agent-role mapping,
- commands,
- rules.

This allows one platform instance to coordinate multiple projects without hardcoded assumptions.
