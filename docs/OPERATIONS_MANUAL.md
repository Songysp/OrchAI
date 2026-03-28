# OrchAI 사령부 가동 매뉴얼 (Operations Manual)

## 1. 🧬 핵심 가치 및 정체성 (Core Identity)
- **CLI-First**: 모든 인터페이스의 최우선 순위는 터미널(CLI)이다.
- **Zero-Cost**: 유료 API 호출을 최소화하고, 사용자 로컬의 claude CLI 자산을 백그라운드에서 최대한 활용한다.
- **Hybrid Adapter**: CLI 드라이버와 API 드라이버를 상황에 맞게 스위칭하는 유연한 아키텍처를 유지한다.

## 2. 🏛️ 사령부 분업 프로토콜 (The Quartet Rules)
- **Lead Architect (Gemini)**: 고수준 설계 및 전체 컨텍스트 관리. 백그라운드 에이전트들의 결과물을 최종 통합.
- **Engine Specialist (Claude)**: 백그라운드 CLI 소환(.cmd 호출)을 통한 핵심 로직 및 드라이버 코딩 전담.
- **Auditor (Codex)**: Pydantic 모델 설계 및 엔진 코드의 개념적 무결성 감사.
- **Tester**: pytest 기반의 기능 유효성 검증.

## 3. 🌪️ 작업 방식 (Work Method: CLI Delegation)
- **동적 소환**: 사령관은 claude "task..." 또는 codex "audit..." 명령어를 백그라운드 터미널(cmd /k)에서 실행하여 병렬로 에이전트를 가동한다.
- **환경 상속**: 윈도우 환경 변수(os.environ.copy())를 완벽히 상속하여 로컬 claude CLI의 인증 및 MCP 연동을 유지한다.
- **비동기 핸드오프**: 각 에이전트가 생성한 파일은 사령관이 view_file로 실시간 스캔하여 다음 단계로 이행한다.

## 4. 🛡️ 검증 및 승인 루프 (Verification Cycle)
- **Plan**: 사령관이 task.md를 업데이트하고 작업을 할당한다.
- **Execute**: 백그라운드에서 에이전트들이 코드를 생산한다.
- **Audit**: 코덱스가 코드의 "Zero-Cost" 원칙 준수 여부를 감사한다.
- **Test**: 테스터가 로컬 환경에서 실제 구동 여부를 확인한다.
- **Approve**: 모든 단계를 통과하면 사령관이 DONE 처리한다.
