# 프로젝트 인수인계

## 1. 프로젝트 목적

이 프로젝트는 단일 봇이 아니라, 여러 프로젝트를 관리할 수 있는 재사용형 "AI Dev Team Platform"을 만드는 것이 목적이다.

핵심 제품 방향은 다음과 같다.

- 사용자는 대표 AI 하나와만 대화한다.
- 내부적으로는 representative, planner, builder, critic, tester 역할이 협업한다.
- Slack과 Discord를 프로젝트별로 선택할 수 있어야 한다.
- 향후 웹 대시보드를 추가해도 도메인/오케스트레이션 구조를 크게 바꾸지 않아야 한다.
- 프로젝트별 차이는 하드코딩이 아니라 설정 기반으로 관리한다.
- 저장소는 현재 파일 기반 MVP이지만, 이후 DB 기반으로 자연스럽게 확장 가능해야 한다.

현재 구현은 "플랫폼 골격 + MVP orchestration + chat ingress 흐름"까지를 목표로 진행되었다.

## 2. 현재 구현 범위

### 아키텍처/구조

- `apps/`, `packages/`, `configs/`, `data/`, `docs/`, `infra/`, `workspaces/` 구조 정리 완료
- `apps/orchestrator` 아래에 API, Slack, Discord, workflows, services 계층 분리 완료
- `packages/domain`, `packages/storage`, `packages/chat`, `packages/agents`, `packages/rules` 분리 완료
- FastAPI route layer는 얇게 유지하고, orchestration 로직은 서비스/워크플로우 계층으로 분리함

### 도메인/저장소

- 도메인 모델 구현 완료
  - `Project`
  - `Task`
  - `Decision`
  - `Approval`
- storage abstraction 구현 완료
  - `ProjectStore`
  - `TaskStore`
  - `DecisionStore`
  - `ApprovalStore`
- file-based store MVP 구현 완료
  - `data/projects/{project_id}/...` 구조 사용
  - task / decision / approval 개별 JSON 저장
  - atomic write 적용

### 프로젝트 설정/멀티 프로젝트

- `configs/projects/` 기반 프로젝트 로딩 구현 완료
- 샘플 Slack / Discord 프로젝트 설정 파일 존재
- 프로젝트별로 다음 항목을 설정 기반으로 관리 가능
  - chat platform
  - logical channel bindings
  - agent mapping
  - commands
  - rules

### 에이전트/역할 선택

- 역할별 provider/model 선택을 `project.agent_mapping`에서 읽도록 구현 완료
- `AgentFactory` 구현 완료
- orchestration이 provider명을 직접 하드코딩하지 않도록 정리 완료
- 현재는 mock adapter 기반이며, 실제 모델 API 연동은 아직 미구현

### 오케스트레이션 MVP

- 대표 AI 중심 기본 흐름 구현 완료
  1. 사용자 요청 수신
  2. task 생성
  3. representative 요약
  4. planner 분석
  5. builder 제안
  6. critic 리뷰
  7. tester 검증 관점 제안
  8. representative 집계
  9. decision 저장 및 task 상태 저장

- 주요 메서드 구현 완료
  - `create_task(project_id, user_input)`
  - `run_task(task_id)`
  - `get_task_status(task_id)`

- task stage 체계 구현 완료
  - `created`
  - `planning`
  - `building`
  - `reviewing`
  - `testing`
  - `waiting_human`
  - `completed`
  - `failed`

### 정책/승인 흐름

- simple rules engine 구현 완료
- 프로젝트 설정의 `rules`를 읽어 approval 필요 여부 판단 가능
- 현재 지원하는 MVP 규칙 유형
  - auth 관련 변경 승인 필요
  - db schema 관련 변경 승인 필요
  - mass deletion 관련 승인 필요
  - debate/retry limit 구조적 확장 포인트

- approval persistence 구현 완료
- approval 필요 시 task를 `waiting_human` / `blocked`로 전이
- 승인/거절 API 및 resume flow 구현 완료

### Chat adapter / ingress

- `ChatAdapter` 추상화 구현 완료
- `SlackAdapter`, `DiscordAdapter` skeleton 구현 완료
- logical channels 개념 정리 완료
  - `ai-council`
  - `ai-ops`
  - `user-control`
- orchestration이 logical channel 기준으로 메시지를 발행하도록 연결 완료

- chat ingress 구현 완료
  - Slack-style inbound payload 수신
  - Discord-style inbound payload 수신
  - inbound event를 platform-neutral event로 정규화
  - `user-control` 메시지면 task 생성 및 orchestration 실행

- chat command MVP 구현 완료
  - `/help`
  - `/approvals`
  - `/status <task_id>`
  - `/approve <approval_id> [comment]`
  - `/reject <approval_id> [comment]`

### FastAPI API

- 현재 사용 가능한 주요 엔드포인트
  - `POST /api/tasks`
  - `GET /api/tasks/{task_id}`
  - `GET /api/projects`
  - `GET /api/projects/{project_id}`
  - `GET /api/approvals`
  - `POST /api/approvals/{approval_id}/approve`
  - `POST /api/approvals/{approval_id}/reject`
  - `POST /api/integrations/slack/{project_id}/events`
  - `POST /api/integrations/discord/{project_id}/events`
  - `GET /health`

### 품질/운영

- GitHub Actions CI 구성 완료
- Node 20 deprecation 대응 반영 완료
- 현재 린트 범위는 `apps packages tests`
- 로컬 테스트 기준 현재 통과 상태
  - `19 passed`

## 3. 다음 우선순위

### 1순위: 실제 Slack/Discord transport 심화

현재는 Slack/Discord payload translator + placeholder adapter 수준이다.
다음 단계에서는 아래 항목이 필요하다.

- Slack App / Socket Mode 실제 이벤트 흐름 연결
- Slack 서명 검증 및 allowlist/policy 처리
- Discord gateway/webhook 실제 이벤트 흐름 연결
- thread/reply 동작을 플랫폼별 실제 동작으로 구체화
- 봇 메시지 루프 방지, 중복 이벤트 방지, retry 대응

### 2순위: approval / task 운영 UX 강화

- `/tasks`, `/latest`, `/decisions` 같은 조회 명령 추가
- approval 대기 task를 더 잘 요약해서 반환
- approval 후 "처음부터 재실행"이 아니라 "중단 지점부터 재개"하는 resume 개선
- decision / approval / task history를 대시보드용으로 더 구조화

### 3순위: 웹 대시보드 대비 API 확장

- task list / decision list / approval queue / run history API 확장
- conversation history 조회 모델 추가
- project detail 응답에 운영 상태를 더 포함
- future frontend가 바로 붙을 수 있는 response schema 정리

### 4순위: 실행/개발 워크플로우 고도화

- GitHub execution adapter / CLI execution adapter 심화
- 실제 build/test/fix workflow 연결
- 작업 실행 결과 로그와 artifact 구조화

### 5순위: 저장소/운영 인프라 확장

- Postgres/Redis 기반 storage backend 도입 준비
- background worker / queue 분리 검토
- production 배포 환경별 secrets / environment 전략 구체화

## 4. 현재 상태 한 줄 요약

현재 프로젝트는 "멀티 프로젝트 AI Dev Team Platform"의 구조적 기반, 대표 AI 중심 MVP orchestration, 규칙/승인 흐름, 그리고 Slack/Discord chat ingress MVP까지 구현된 상태다.
