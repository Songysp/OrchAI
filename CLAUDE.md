# CLAUDE.md — AI Dev Team Platform Collaboration Rules

All agents (Claude, Codex, or any future AI) **must read and follow this document** before performing any work in this repository.

---

## 0. Project Concept (Read This First)

이 프로젝트의 핵심 개념: **"AI 팀을 구성하고 협업시키는 시스템"**

```
[사용자]
   ↓ (Channel 3: user-control)
[Orchestrator]
   ├─ Channel 1 (ai-council): 전략 회의 — Orchestrator, Planner, Reviewer
   └─ Channel 2 (ai-ops):    작업 수행 — Worker AI들 (Backend/Frontend/Data/Research)
```

**AI 역할:**
- `Orchestrator` (= representative): 두뇌. 사용자 ↔ 시스템 중심. 최고 성능 모델.
- `Planner`: 작업 분해 및 실행 계획
- `Worker AI` (= builder): 실제 작업 수행. 종류별로 분리 가능
- `Reviewer` (= critic + tester): 결과 검증, 품질 검토

**핵심 원칙:**
- 모든 AI는 Orchestrator를 통해서만 통신 (직접 통신 금지)
- 요청 1건 = 1 Thread
- 사용자에게는 Orchestrator만 노출 (내부 협업 내용 비노출)

**OpenClaw:**
- 공식 Slack/Discord API가 1차 경로
- OpenClaw는 브라우저/UI 자동화 보조용 선택적 옵션
- Slack: Socket Mode + `openclaw plugins enable slack`
- Discord: ACP 프로토콜 + `/acp spawn claude --thread auto`

구현 중 이 컨셉에서 벗어나는 변경은 하지 말 것.

---

## 1. Role Assignment

### Default: Sequential Pipeline

```
Claude → Codex → Claude
(plan)   (impl)  (review)
```

| Agent  | Responsibilities |
|--------|-----------------|
| Claude | Planning, architecture decisions, structural design, TASKS.md management, code review, refactoring guidance |
| Codex  | Implementation, debugging, writing tests |

- **Task-based delegation (C)** is allowed only for small, well-scoped tasks where scope is unambiguous.
- **Parallel independent work (A) is NOT allowed.**

---

## 2. Conflict Resolution

- **Final authority: the user.**
- If the user is not involved:
  - Architecture / structure decisions → **Claude has priority**
  - Implementation details → **Codex has priority**
- Additional rules:
  - Prefer smaller, safer changes over large changes.
  - **Codex must NOT change architecture** (directory structure, domain models, service boundaries, API contracts).
  - Major structural changes must follow a Claude decision first.

---

## 3. Execution Unit

**Single source of truth: `TASKS.md` and `docs/HANDOFF.md`**

### Rules
- Always work on **ONE** highest-priority task at a time.
- Do not work on multiple tasks simultaneously.
- Update task status in `TASKS.md` after completion.
- Do not go outside the current task's scope.

### Constraints
- No large refactors in a single step.
- Minimize multi-file changes per task.
- Prefer incremental progress over large jumps.

---

## 4. Execution Loop

Every agent must follow this loop for each task:

```
1. Read TASKS.md → identify the highest-priority OPEN task
2. Select that ONE task
3. Implement the minimal change required
4. Verify (run tests / lint / manual check as appropriate)
5. Update TASKS.md → mark task DONE or IN PROGRESS with a note
6. Summarize the result (what was done, what was not done, blockers)
```

Do not skip steps. Do not jump ahead to the next task before completing the current one.

---

## 5. Task Ownership

- **Claude is responsible for selecting and assigning tasks.**
- Codex must NOT start a new task unless explicitly assigned by Claude or the task clearly lists `Codex` as the sole assignee.
- If a task is assigned to `Claude + Codex`, Claude must first produce a design or plan before Codex begins implementation.

---

## 6. Task Selection Rules

- Always select the highest-priority `OPEN` task within the lowest-numbered priority group (`P1 > P2 > P3 > ...`).
- Within the same priority group, follow the order listed in the table (top to bottom).
- Do not skip tasks unless status is `BLOCKED`.

---

## 7. gstack Skills Usage

gstack is installed for both Claude and Codex (`~/.claude/skills/gstack`).
Claude invokes these automatically at appropriate points in the workflow:

| When | Skill | Trigger |
|------|-------|---------|
| After Codex implements a task | `/review` | Always — before marking DONE |
| After a P1/P2 group completes | `/qa` | Quality gate |
| When a bug or unexpected behavior appears | `/investigate` | On demand |
| Before marking a major milestone done | `/qa` | Manual call |

Codex may also use gstack skills during implementation when appropriate.

---

## 8. Continuation Rule

- After completing a task, immediately proceed to the next eligible task following TASKS.md priority rules.
- Do not wait for user input unless:
  - the task is `BLOCKED`
  - the task explicitly requires a user decision
  - architecture-level ambiguity exists that Claude cannot resolve alone

---

## 8b. Commit & Push Rule

- After every completed task (marked DONE in TASKS.md), commit and push to remote.
- Commit message format: `[P{priority}-{task_num}] {short description}`
- Stage only files relevant to the completed task.
- Push to `origin main` after every commit.

---

## 9. Implementation Guard (Codex)

Codex must NOT:
- refactor unrelated modules
- introduce new patterns across the codebase
- modify files outside the current task scope

Codex must limit changes strictly to the current task.

---

## 10. Planning Guard (Claude)

- Provide only the minimal design required for the current task.
- Do not design for future tasks unless they are an explicit prerequisite.
- Do not propose architectural changes beyond the task scope.

---

## 11. Scope Guards

- Do not rename, move, or delete existing modules unless the task explicitly requires it.
- Do not add new dependencies without noting it in the task summary.
- Do not modify `CLAUDE.md` or `TASKS.md` format without user approval.
- Do not modify CI configuration unless the task is specifically about CI.

---

## 12. References

- Current work queue: [`TASKS.md`](TASKS.md)
- Project handoff context: [`docs/HANDOFF.md`](docs/HANDOFF.md)
- Architecture: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
