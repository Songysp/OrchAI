# task.md — OrchAI CLI Master Tasks (OrchAI Quartet Assigned)

Engineering Review (2026-03-28)를 거쳐 확정된 4인 체제(Architect, Engine, Tester, Auditor) 분업 계획입니다.

## P1: Foundation & Engine (하이브리드 어댑터)

| # | Task | Status | Assignee | Note |
|---|------|--------|----------|------|
| T1 | **하이브리드 `ClaudeAdapter` 구현** | IN PROGRESS | **Engine** | `drivers/` 패턴 적용. CLI/API 드라이버 구현 |
| T2 | **프로젝트 설정(`config.json`) 연동** | OPEN | **Auditor** | 드라이버 선택 및 모델 설정 검증 로직 |

## P2: Interface (명령어 도구)

| # | Task | Status | Assignee | Note |
|---|------|--------|----------|------|
| T3 | **`apps/cli/main.py` 신규 생성** | OPEN | **Engine** | `Typer` 기반의 REPL 및 입력 루프 구축 |
| T4 | **Rich UI 통합** | OPEN | **Tester** | 실시간 구동 현황(스피너) 및 UI 렌더링 테스트 |

## P3: Orchestration (하이마인드 로직)

| # | Task | Status | Assignee | Note |
|---|------|--------|----------|------|
| T5 | **핑퐁 오케스트레이션 루프 구현** | OPEN | **Engine** | Planner -> Worker -> Reviewer 순환 루프 구축 |
| T6 | **에스컬레이션 처리** | OPEN | **Auditor** | 루프 결렬 시 사용자 개입 로직 (Concept Audit) |

## P4: Verification (검증 및 사후 처리)

| # | Task | Status | Assignee | Note |
|---|------|--------|----------|------|
| T7 | **전체 통합 테스트** | OPEN | **Tester** | `tests/test_hive_logic.py` 30여 개 케이스 테스트 |
| T8 | **기존 레거시 코드 정리** | OPEN | **Architect** | Slack/Discord 어댑터 제거 및 최종 배포 확인 |

---

## 작업 규정 (Protocol)
- **Engine (Claude)**은 코딩 후 반드시 **Auditor (Codex)**에게 리뷰를 요청합니다.
- **Tester**는 모든 기능에 대해 `pytest`를 작성하며, 실패 시 `Engine`에게 수정을 요구합니다.
- **Architect (Gemini)**는 모든 단계가 완료된 후 `APPROVED` 태그를 남겨야 태스크가 `DONE` 처리됩니다.
- 모든 에이전트는 작업 요약 시 `[CONCEPT CHECK] CLI-First, Hybrid Driver, No-Infra` 문구를 포함해야 합니다.
