# Architecture

This repository is structured as a reusable orchestration platform, not a one-off chat bot.

## Core principle

The user experiences one AI development team, while the platform internally coordinates:

- a representative AI for user interaction,
- planner and scout roles for analysis,
- a builder role for implementation,
- a critic role for challenge and review,
- a tester role for validation.

That behavior belongs to the platform domain, not to Slack, Discord, or a future web UI.

## Layered design

### 1. Domain layer

`packages/domain`

- Owns project, task, approval, decision, and conversation models
- Owns orchestration services and task lifecycle logic
- Does not know whether requests came from Slack, Discord, or HTTP

### 2. Transport layer

`packages/chat`

- Defines the `ChatAdapter` abstraction
- Implements `SlackAdapter` and `DiscordAdapter`
- Maps logical domains to physical channels:
  - `ai-council`
  - `ai-ops`
  - `user-control`

This makes chat platform choice a per-project configuration concern, not a business-logic concern.

### 3. Agent provider layer

`packages/agents`

- Defines `AgentAdapter`
- Keeps provider-specific behavior behind adapters
- Allows preferred mappings like Claude for representative and critic, Gemini for planner and tester, and Codex for builder without coupling orchestration to any single vendor

### 4. Persistence layer

`packages/storage`

- Defines store interfaces:
  - `ProjectStore`
  - `TaskStore`
  - `ConversationStore`
  - `DecisionStore`
  - `ApprovalStore`
- Current MVP uses file-backed JSON stores
- Future Postgres or Redis implementations can replace these behind the same interfaces

### 5. Policy layer

`packages/rules`

- Evaluates approval and execution policy
- Keeps project-specific controls configurable
- Intended for approval-gated changes like auth, schema, or large deletions

### 6. Execution and repository integration

`packages/execution` and `packages/github`

- Separate orchestration from how work is executed
- Supports a future split between local CLI execution and GitHub Actions execution
- Prevents the core platform from depending on one runtime model

### 7. Application layer

`apps/orchestrator`

- FastAPI app exposing reusable APIs
- Intended to serve both transport adapters and a future dashboard
- Keeps request handling thin and pushes behavior into the domain layer

## Multi-project model

Each project is configured independently through YAML and includes:

- `project_id`
- repository metadata
- workspace path
- selected chat platform
- logical channel bindings
- agent-role mapping
- commands
- rules

This allows one platform instance to manage multiple repositories and multiple chat workspaces cleanly.

## Slack vs Discord strategy

Slack and Discord are intentionally treated as separate transports with different operational concerns.

### Slack

The scaffold is designed to align with a Slack App approach using:

- Socket Mode
- bot token
- app token
- project-scoped allowlist or policy controls

These are represented as project metadata and adapter concerns rather than assumptions in orchestration logic.

### Discord

Discord is handled as a distinct adapter with its own channel and threading behavior.

The platform does not assume Slack and Discord have identical event, thread, or permission semantics.

## Future dashboard support

The FastAPI API is intentionally UI-agnostic so a future web dashboard can consume:

- project list
- task list
- decision history
- approval queue
- conversation history
- agent execution status

without moving business logic out of chat handlers later.

## MVP scope in this scaffold

Phase 1 now provides:

- typed domain models,
- configuration loading,
- storage interfaces,
- file-based storage implementation,
- rules and execution extension points,
- Slack and Discord adapter skeletons,
- agent adapter skeletons,
- FastAPI API skeleton,
- sample project configs,
- Docker-first local startup files.

Phase 2 can now add real representative workflow, internal council debate, approvals, and execution orchestration on top of stable interfaces.
