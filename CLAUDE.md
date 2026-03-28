# CLAUDE.md — OrchAI CLI Orchestrator Rules (The OrchAI Quartet)

All agents **must follow this document** before performing any work in this repository.

---

## 0. Project Concept: The HiveMind
OrchAI is a local, CLI-first orchestration platform that enables collaborative workflows between specialized AI agents.

### Core Architecture
- **Entrypoint:** `orchai` (mapped to `apps/cli/main.py`)
- **Engine:** Hybrid Adapter pattern (CLI Driver vs API Driver)
- **Workflow:** Planner → Worker(s) → Reviewer loop with iterative refined (Ping-Pong).

---

## 1. The OrchAI Quartet (AI Team Roles)
To ensure the "CLI-First" concept is strictly followed, we operate as a 4-agent team:

1. **Lead Architect (Gemini - Project Lead):** 
   - **Responsibility:** Overall orchestration, goal alignment, and **Final Approval Gate**.
   - **Authority:** Approves/Rejects every sub-task. No task is DONE without Gemini's `APPROVED` tag.

2. **Engine Specialist (Claude - Team Leader):** 
   - **Responsibility:** Core logic implementation (T1, T3, T5).
   - **Authority:** Directs the terminal `gstack` skills and `teams` parallelism.

3. **Testing Specialist (Tester - Sub-Agent):** 
   - **Responsibility:** Test code generation and verification (T7).
   - **Authority:** Can block a task if `pytest` fails or coverage is insufficient.

4. **Critic/Auditor (Codex - Sub-Agent):** 
   - **Responsibility:** Conceptual audit and code review.
   - **Authority:** Flags deviations from the "CLI-First" or "Zero-Infrastructure" design.

---

## 2. Cross-Monitoring & Approval Gate
- **No Self-Approval:** No agent can mark their own task as `DONE` without Gemini's review.
- **Auditor First:** Every implementation must be reviewed by the `Auditor` (Codex) before being submitted to the `Architect` (Gemini).
- **Concept Guard:** Every summary must start with: *"[CONCEPT CHECK] CLI-First, Hybrid Driver, No-Infra."*

---

## 3. Technology Stack & Directory Structure
- **Core:** Python 3.11+, Typer (CLI), Rich (UI), SQLite (Trace)
- **Directory Rules:**
  - `apps/cli/`: Main CLI entrypoint and REPL.
  - `packages/agents/`: AI adapters and connection drivers.
  - `packages/domain/`: Shared data models (Project, Task, etc.).
  - `packages/storage/`: File-based and SQLite storage.
  - `docs/`: Design and pivot documentation.

---

## 4. Execution Rules
- **Single Task Focus:** Work on one task from `task.md` at a time.
- **No Over-Engineering:** Prefer simple stdlib-first solutions (Approach A) before moving to complex infrastructure.
- **Documentation First:** Update relevant docs in `docs/` before implementing major architectural changes.

---

## 5. References
- **Master Pivot Doc:** [`docs/CLI_ORCHESTRATOR_PIVOT.md`](docs/CLI_ORCHESTRATOR_PIVOT.md)
- **Active Tasks:** [`task.md`](task.md) (Check for priority T1-T7) / [`TASKS.md`](TASKS.md) (Legacy)
- **Engineering Review:** [`~/.gstack/projects/Songysp-OrchAI/main-reviews.jsonl`](#)
