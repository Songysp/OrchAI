# TODOS.md — Engineering Debt & Prerequisite Tracking

Items that are not yet tasks (not in TASKS.md) but must be addressed before or during upcoming work.
Managed by Claude. Items graduate to TASKS.md when they become the next concrete unit of work.

---

## Blocking — CLI Pivot Prerequisites

| # | Item | Why it matters | Depends on |
|---|------|---------------|------------|
| T1 | **Implement real `ClaudeAdapter`** — `packages/agents/claude_adapter.py` is a mock stub returning fake text | The entire orchai orchestration chain produces garbage until this is real. First blocking item for CLI pivot. | P4-4.3 architecture decision |
| T2 | **Create `apps/cli/` directory + `apps/cli/main.py`** — declared in `pyproject.toml` as `orchai` entrypoint but doesn't exist | `pip install -e .` succeeds but `orchai` crashes on launch | T1 (real adapter needed to wire up) |
| T3 | **Implement Ping-Pong orchestration loop** in `apps/orchestrator/services/orchestrator_service.py` — Builder ↔ Critic cycle with max retries (3) and human-in-loop escalation | This is the core orchestration correctness behavior described in `docs/CLI_ORCHESTRATOR_PIVOT.md` | T1, T2 |

---

## Clean-up — Post-Pivot

| # | Item | Why it matters |
|---|------|---------------|
| T4 | **Remove Slack/Discord adapters** — `apps/orchestrator/slack/`, `apps/orchestrator/discord/`, related lifecycle code in `apps/orchestrator/main.py` | Pivot removes these; leaving dead code creates confusion and inflates test surface |
| T5 | **Migrate storage from PostgreSQL/Redis plan to JSON files** — `TASKS.md` P5 tasks are now obsolete per `docs/CLI_ORCHESTRATOR_PIVOT.md` | P5 tasks (PostgreSQL, Redis, background workers) conflict with the zero-install JSON file approach. Mark P5 BLOCKED or superseded. |

---

## Known Debt (Non-blocking)

| # | Item | Notes |
|---|------|-------|
| T6 | `pyproject.toml` broken entrypoint resolved once `apps/cli/main.py` exists | Fixed TOML parse error (2026-03-28); entrypoint itself still unresolvable until T2 done |
| T7 | `packages/agents/claude_adapter.py` mock returns `"Mock response from claude"` — all integration tests pass against fake data | Any test that passes through the adapter today is testing the mock, not the real chain |

---

## Notes

- T1 is the critical path. Nothing in the CLI pivot works without a real Claude subprocess adapter.
- T4 and T5 are safe to defer until T1-T3 are done.
- Items here should not be worked on out of order — T1 → T2 → T3 is the dependency chain.
