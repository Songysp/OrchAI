# OrchAI: 단일 CLI 인터랙티브 오케스트레이터 아키텍처 피벗 기획서 (OpenCode Style)

**Goal Description**
기존에 분산형 서버/클라이언트 환경으로 기획되었던 Webhook/운영용 메신저(Slack, Discord) 연동을 전면 제거하고, 100% 로컬 환경에서 사용자 터미널만으로 동작하는 가볍고 강력한 **단일 CLI 앱(OpenCode, Claude Code 스타일)**으로 피벗합니다.
이 과정에서 내부 에이전트 다중 협업(Ping-Pong) 및 휴먼-인-더-루프(Human-in-the-loop) 상태 제어 시스템을 핵심으로 재설계합니다.

## 📌 주요 아키텍처 결정 사항

1. **상태망 저장소 (Zero-Install 인프라):**
   * 기존 기획했던 무거운 서버 인프라(Postgres, Redis 등)를 걷어냅니다.
   * `Claude Code`의 구조를 벤치마킹하여, 단기 대화 세션 상태와 에이전트 컨텍스트는 **프로젝트 디렉터리 내 JSON 파일 저장 방식(`data/projects/...`)**으로 완전히 대체합니다.
2. **AI 에이전트 상호작용 (Ping-Pong & Feedback Loop):**
   * [Builder] 에이전트와 [Critic] 에이전트 간의 자율 리뷰 및 재수정(Ping-Pong) 반복 사이클을 오케스트레이션 뼈대 로직에 내장합니다.
   * 무한 루프 토큰 낭비를 막기 위해 **Max Retries (예: 3회)** 제한을 설정하고, 결렬 시 **Human-in-the-loop (결정 권한 사용자 이양 REPL 대화창)** 통제 장치를 필수로 구현합니다.
3. **사용자 인터페이스 (Interactive REPL):**
   * 터미널에 `orchai` 명령어 입력 시 앱이 종료되지 않고 내장된 `rich.prompt`를 활용해 즉시 무한 대기 화면 창(REPL) 상태가 지속됩니다. 
   * 에이전트들의 실시간 구동 및 토론 현황을 콘솔 바탕에서 `rich.status`(스피너 등)로 생중계하여 시각적 직관성을 극대화합니다.
4. **하이브리드 어댑터 전략 (Hybrid Driver):**
   * 사용자 환경에 따라 **CLI 방식**(`claude --print`) 또는 **API 방식**(SDK 활용) 중 선택할 수 있는 구조를 도입합니다.
   * 이는 구독 정보가 있는 사용자의 비용을 절감하면서도, 안정적인 API 연결성을 동시에 확보하기 위함입니다.
5. **장기 기억 장치 (미래의 Phase 2):**
   * 토큰 절약을 위해, 당장 시도하지 않고 앱이 어느 정도 안정화된 추후에 플러그인 형태로 로컬 벡터 DB(e.g., `chromadb`)를 추가하여, 기존 프로젝트 운영 노하우와 코딩 컨벤션(RAG)을 오케스트레이터가 장기기억으로 학습하도록 확장할 예정입니다.

---

## 🛠️ Proposed Changes (향후 변경될 코드 영역)

### [Component 1] 환경 초기화 및 진입점
- **`pyproject.toml` 수정:**
  - `discord.py` 및 `slack-sdk` 통신 의존성 어댑터 코드 삭제.
  - 파이썬 CLI 생성용 `typer`, 콘솔 스타일링 UI 렌더링용 `rich` 명시적 라이브러리 설치.
  - `[project.scripts]` 구문을 추가해 시스템 전역에서 `orchai` 런타임 커맨드라인 엔트리포인트를 강제 지정.
- **신규 엔진 계층 `apps/cli/main.py` 추가:**
  - 애플리케이션 프론트 진입점 생성. `typer` 앱 초기화 후 사용자와 끝없이 무한 대화하며 중앙 `OrchestratorService`에 메시징 이벤트를 던지고 가져오는 핵심 챗 스트림 루프 (`interactive_loop()`) 구현.

### [Component 2] 메신저 어댑터 삭제 (Clean up)
- **제거 대상 폴더/파일:** `apps/orchestrator/slack/` 및 `apps/orchestrator/discord/` 전체 삭제.
- **`apps/orchestrator/main.py` (FastAPI 앱 쪽) 수정:**
  - Slack Socket 모드 시작 및 Discord Gateway 구동 라이프사이클(Lifespan) 코드들 완전 제거 및 CLI 전용으로 순수 재구성 대비.

### [Component 3] 오케스트레이션 코어 강화 (Ping-Pong 및 지휘 로직)
- **`apps/orchestrator/services/orchestrator_service.py` 수정:**
  - 기존 외부 플랫폼에 종속된 메시지 객체(Payload) 체계 대신, 내부 순수 CLI Prompt와 에이전트 Feedback을 매핑하는 구조체 기반으로 입력 계층 재구성.
  - `Agent StateMachine` 로직의 실체적 구현: `Plan -> Build -> Critic -> (Critic Reject 발견 시 Build로 재진입 Count 증가) -> Max Count 판정 시 사용자 즉시 개입 프롬프트` 과정을 통제하는 코루틴 도입.
