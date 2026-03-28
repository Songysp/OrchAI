# OrchAI Architecture: The HiveMind CLI

## Overview
OrchAI는 로컬 개발 환경 최적화된 **CLI 기반 에이전트 오케스트레이터**입니다. 이 시스템은 복잡한 인프라 없이 파이썬 런타임과 LLM CLI(Claude)만으로 작동하는 'Zero-Infrastructure'를 지향합니다.

---

## 핵심 계층 (Core Layers)

### 1. 전면 인터페이스 (CLI Interface)
- **`apps/cli/main.py`**: Typer를 사용하여 구현된 인터랙티브 REPL. 
- 사용자의 입력을 받고, `Rich` 라이브러리를 통해 에이전트들의 토론 과정을 시각화합니다.

### 2. 오케스트레이션 코어 (HiveMind Engine)
- **`OrchestratorService`**: 작업을 분석하고 에이전트들에게 배분합니다.
- **Loop Strategy**: Planner -> Worker -> Reviewer 루프를 돌며, Reviewer의 피드백에 따라 최대 3회까지 재작업을 수행하는 '핑퐁(Ping-Pong)' 시스템을 가집니다.

### 3. 하이브리드 어댑터 계층 (Hybrid Drivers)
- **`BaseAgentAdapter`**: 모든 AI 에이전트의 공통 인터페이스.
- **`CLIDriver`**: `subprocess`를 통해 로컬에 설치된 `claude` CLI 등을 실행 (비용 효율적).
- **`APIDriver`**: 표준 REST API/SDK를 통해 통신 (고가용성).

### 4. 경량 저장소 (File-based Storage)
- **State Management**: Redis 대신 프로젝트 내 JSON 파일로 상태를 관리합니다.
- **Trace Logging**: 모든 에이전트 호출 이력은 SQLite 데이터베이스에 기록되어 나중에 복기가 가능합니다.

---

## 데이터 흐름 (Data Flow)

1. **User input** -> `orchai` CLI
2. **Planner Agent** -> 작업 분해 (subtasks)
3. **Worker Agent** -> 실제 구현 (Implementation)
4. **Reviewer Agent** -> 검증 (Verification)
5. **If Reject** -> Worker에게 피드백과 함께 재전달 (Loop)
6. **Final Result** -> 사용자 터미널 출력 및 파일 저장
