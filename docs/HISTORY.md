# OrchAI Project History: The Journey to HiveMind

이 문서는 OrchAI 프로젝트의 탄생부터 현재의 CLI-First 하이브리드 오케스트레이터로 진화하기까지의 모든 기록을 담고 있습니다.

## 📅 2026-03-27: 탄생 (The Network Era)
OrchAI는 처음에 **"Slack과 Discord를 통해 AI 개발팀을 부리는 서버형 서비스"**로 기획되었습니다. 
- **당시 목표:** 사용자가 어디서나 가볍게 AI 팀에게 업무를 지시할 수 있는 환경 구축.
- **주요 기술:** FastAPI (API), PostgreSQL (DB), Redis (상태 관리), Slack/Discord Adapters.
- **성과:** 도메인 모델(Project, Task, Decision) 설계 및 기본적인 목업 연동 완료.

## 📅 2026-03-28: 성찰 (The Context Friction)
개발이 진행될수록 몇 가지 기술적/경험적 한계에 부딪혔습니다.
- **Context Switching:** 개발자는 코드를 터미널과 에디터에서 보는데, 결과는 Slack으로 확인해야 하는 불편함.
- **Infra Overload:** 로컬 개발 툴임에도 불구하고 Redis, Postgres 등 무거운 인프라 설치가 필수적인 구조.
- **Latency & Cost:** 네트워크 API 통신의 지연 시간과 비용 부담.

## 📅 2026-03-28 (18:00): 피벗 (The CLI Pivot)
운명적인 **Engineering Review** 세션이 열렸습니다. 사령관(Gemini), 엔지니어(Claude), 독설가(Codex)가 모여 난상토론을 벌인 결과, 우리는 다음과 같은 결론에 도달했습니다.

> *"개발자에게 가장 가까운 곳은 터미널이며, AI를 가장 강력하게 부리는 방법은 터미널에 이미 설치된 AI CLI를 직접 오케스트레이션하는 것이다."*

- **Pivot 결정:** 모든 네트워크 어댑터와 무거운 서버 인프라를 제거.
- **신규 컨셉:** **"HiveMind"** — 로컬 터미널에서 `claude --print`와 같은 명령어를 직접 호출하여 AI 드림팀을 구성하는 초경량, 초고속 오케스트레이터.

## 📅 현재: 구축기 (The Hybrid Era)
우리는 현재 **'하이브리드 드라이버(CLI/API 선택 가능)'**라는 독창적인 아키텍처를 바탕으로 `orchai` 명령어를 완성해 나가고 있습니다. 
- **철학:** CLI-First, Hybrid Driver, Zero-Infrastructure.

이 역사는 단순히 기록이 아니라, 우리 프로젝트가 왜 이 길을 걷고 있는지에 대한 증거입니다.
