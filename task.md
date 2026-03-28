# task.md — OrchAI CLI Master Tasks (OrchAI Quartet Assigned)

Engineering Review (2026-03-28)를 거쳐 확정된 4인 체제(Architect, Engine, Tester, Auditor) 분업 계획입니다.

## P1: Foundation & Engine (하이브리드 어댑터)

| # | Task | Status | Assignee | Note |
|---|------|--------|----------|------|
| T1 | **하이브리드 `ClaudeAdapter` 구현** | DONE ✓ | **Engine** | Architect Approved. CLI Driver confirmed working (cmd /c, env sync). |
| T2 | **프로젝트 설정(`config.json`) 연동** | DONE ✓ | **Auditor** | ConfigService 및 스키마 설계 완료 (Loader/Service 구현 완료). |

## P2: Interface (명령어 도구)

| # | Task | Status | Assignee | Note |
|---|------|--------|----------|------|
| T3 | **CLI 진입점 및 Rich UI 구축** | DONE ✓ | **Engine** | Typer/Rich 기반 main.py 기동 성공 (Zero-Cost boot). |
| T4 | **Rich UI 통합** | DONE ✓ | **Tester** | Rich spinner + P-W-R 루프 시각화 CLI 기동 확인. |

## P3: Orchestration (하이마인드 로직)

| # | Task | Status | Assignee | Note |
|---|------|--------|----------|------|
| T5 | **핑퐁 오케스트레이션 루프 구현** | DONE ✓ | **Engine** | Phase(Planner, Worker, Refiner) 및 LoopState, TurnResult 영속성 모델 구현 완료. Architect APPROVED. |
| T6 | **에스컬레이션 처리** | DONE ✓ | **Auditor** | 루프 결렬 시 typer.prompt를 통한 사용자 개입 로직 구현 완료. |

## P4: Verification (검증 및 사후 처리)

| # | Task | Status | Assignee | Note |
|---|------|--------|----------|------|
| T7 | **전체 통합 테스트** | DONE ✓ | **Tester** | `tests/test_hive_logic.py` 2/2 PASS. `test_config_service.py` 7/7 PASS. CLI-First 핵심 9개 ALL PASS. Architect APPROVED. |
| T8 | **기존 레거시 코드 정리** | DONE ✓ | **Architect** | `test_slack_socket_mode.py`, `test_discord_gateway_runtime.py` 삭제 완료. CLI-First 테스트만 잔존. Architect APPROVED. |

---

## 작업 규정 (Protocol)
- **Engine (Claude)**은 코딩 후 반드시 **Auditor (Codex)**에게 리뷰를 요청합니다.
- **Tester**는 모든 기능에 대해 `pytest`를 작성하며, 실패 시 `Engine`에게 수정을 요구합니다.
- **Architect (Gemini)**는 모든 단계가 완료된 후 `APPROVED` 태그를 남겨야 태스크가 `DONE` 처리됩니다.
- 모든 에이전트는 작업 요약 시 `[CONCEPT CHECK] CLI-First, Hybrid Driver, No-Infra` 문구를 포함해야 합니다.
