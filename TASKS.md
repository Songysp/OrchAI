# TASKS.md ??Work Queue

Single source of truth for all pending and completed work.
Managed by Claude. Updated after every task completion.

**Status values:** `OPEN` | `IN PROGRESS` | `DONE` | `BLOCKED`

## Execution Rules

- Always select the highest-priority `OPEN` task within the lowest-numbered priority group (`P1 > P2 > P3 > ...`).
- Within the same priority group, follow the order listed in the table (top to bottom).
- Do not skip tasks unless status is `BLOCKED`.
- After completing a task, immediately proceed to the next eligible task.

---

## Active Tasks

### P1 ??Slack/Discord Real Transport

| # | Task | Status | Assignee | Notes |
|---|------|--------|----------|-------|
| 1.1 | Slack Socket Mode ? real event connection | DONE | Codex | Implemented Socket Mode runtime startup/shutdown + channel-routed ingress; requires SLACK_APP_TOKEN |
| 1.2 | Slack signature verification (X-Slack-Signature) | DONE | Codex | Enforced v0 HMAC + timestamp validation on Slack HTTP ingress before payload handling (`SLACK_SIGNING_SECRET`) |
| 1.3 | Discord gateway/webhook real event connection | DONE | Codex | Added Discord gateway runtime startup/shutdown + channel-routed ingress; requires DISCORD_BOT_TOKEN |
| 1.4 | Bot message loop prevention (ignore bot_id messages) | DONE | Codex | Added translator-level bot_id filtering for Slack and Discord inbound message events |
| 1.5 | Duplicate event prevention (deduplication by event_id) | DONE | Codex | Added ingress-level bounded dedup cache keyed by platform/project/event_id with duplicate ignore action |

---

### P2 ??Approval / Task Operation UX

| # | Task | Status | Assignee | Notes |
|---|------|--------|----------|-------|
| 2.1 | Add `/tasks` command ??list recent tasks | DONE | Codex | Added user-control command handler with recent-first task listing (top 5) including status/title. |
| 2.2 | Add `/latest` command ??show most recent task summary | DONE | Codex | Added latest-task command returning most recent task id/status/title with summary fallback. |
| 2.3 | Add `/decisions` command ??list recent decisions | DONE | Codex | Added recent-first decision listing command (top 5) with task linkage and summary snippet. |
| 2.4 | Improve approval wait summary message | DONE | Codex | Approval wait message now includes task/approval IDs, reasons, and /approve /reject /status command hints |
| 2.5 | Resume from checkpoint (not restart) after approval | OPEN | Claude + Codex | Architecture decision needed first |

---

### P3 ??Web Dashboard API Prep

| # | Task | Status | Assignee | Notes |
|---|------|--------|----------|-------|
| 3.1 | `GET /api/tasks` ??paginated task list endpoint | OPEN | Codex | |
| 3.2 | `GET /api/decisions` ??decision list endpoint | OPEN | Codex | |
| 3.3 | `GET /api/approvals` ??approval queue endpoint | OPEN | Codex | Already exists, review response schema |
| 3.4 | Conversation history model + endpoint | OPEN | Claude + Codex | Model design needed first |
| 3.5 | Enrich `GET /api/projects/{project_id}` with runtime status | OPEN | Codex | |

---

### P4 ??Execution Workflow

| # | Task | Status | Assignee | Notes |
|---|------|--------|----------|-------|
| 4.1 | GitHub execution adapter (run workflows via GitHub API) | OPEN | Codex | |
| 4.2 | CLI execution adapter (run local shell commands) | OPEN | Codex | |
| 4.3 | Build/test/fix workflow integration | OPEN | Claude + Codex | Architecture decision needed first |
| 4.4 | Execution result log + artifact storage | OPEN | Codex | |

---

### P5 — Storage / Infrastructure

**결정 완료 (2026-03-28):** 상태관리 → Redis, DB → PostgreSQL

| # | Task | Status | Assignee | Notes |
|---|------|--------|----------|-------|
| 5.1 | PostgreSQL storage backend adapter | OPEN | Codex | StorageBase interface 구현. DB: PostgreSQL (확정) |
| 5.2 | Redis 실시간 상태 관리 adapter | OPEN | Codex | 실시간 task 상태. Cache: Redis (확정) |
| 5.3 | Background worker / task queue separation | OPEN | Claude + Codex | Architecture decision needed first |
| 5.4 | Secrets / environment strategy per deployment target | OPEN | Claude | |

---

## Completed Tasks

| # | Task | Completed | Notes |
|---|------|-----------|-------|
| ??| Platform structure (`apps/`, `packages/` separation) | 2026-03-27 | See HANDOFF.md 짠2 |
| ??| Domain models (Project, Task, Decision, Approval) | 2026-03-27 | See HANDOFF.md 짠2 |
| ??| File-based storage MVP | 2026-03-27 | See HANDOFF.md 짠2 |
| ??| Multi-project config (`configs/projects/`) | 2026-03-27 | See HANDOFF.md 짠2 |
| ??| AgentFactory + mock adapters | 2026-03-27 | See HANDOFF.md 짠2 |
| ??| RepresentativeWorkflow MVP orchestration | 2026-03-27 | See HANDOFF.md 짠2 |
| ??| Rules engine + approval flow | 2026-03-27 | See HANDOFF.md 짠2 |
| ??| Slack/Discord chat ingress skeleton | 2026-03-27 | See HANDOFF.md 짠2 |
| ??| FastAPI endpoints (tasks, projects, approvals, ingress) | 2026-03-27 | See HANDOFF.md 짠2 |
| ??| GitHub Actions CI (19 tests passing) | 2026-03-27 | See HANDOFF.md 짠2 |

---

## Notes

- Tasks marked `Claude + Codex` require Claude to produce a design/decision first before Codex implements.
- Do not start a task unless it is the highest-priority `OPEN` item.
- Update this file after every completed task.
