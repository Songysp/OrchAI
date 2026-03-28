---
description: OrchAI CLI 실행 및 실전 테스트 가이드
---

# 🚀 OrchAI Run & Test Workflow

설치가 완료된 후 `orchai` 명령어를 통해 오케스트레이션을 실행하고 테스트하는 방법을 정의합니다.

1. **대화형 실행 (REPL)**
   // turbo
   ```bash
   orchai
   ```
   실행 후 프롬프트에 작업을 입력합니다. (예: "로그인용 파이썬 스크립트 짜줘")

2. **단일 명령 실행**
   // turbo
   ```bash
   orchai "임시 폴더 생성하고 그 안에 hello.txt 만들어줘"
   ```

3. **로직 테스트 (Mock 모드)**
   // turbo
   ```bash
   pytest tests/test_hive_logic.py
   ```
   실제 AI 호출 없이 내부 오케스트레이션 루프(핑퐁)가 잘 작동하는지 확인합니다.

4. **실행 결과 확인**
   - 결과물은 설정된 프로젝트 경로의 `data/runs/` 폴더 내에 JSON 또는 Markdown 형태로 저장됩니다.
