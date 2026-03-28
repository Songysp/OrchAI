---
description: OrchAI 개발 환경 설정 및 로컬 설치 가이드
---

# 🛠️ OrchAI Setup Workflow

이 워크플로우는 프로젝트 피벗 이후 새롭게 도입된 CLI 환경을 설정하는 단계를 정의합니다.

1. **의존성 확인**
   - Python 3.11 이상이 설치되어 있는지 확인합니다.
   - 로컬 터미널에 `claude` CLI가 설치되어 있고 `claude auth login`이 완료되었는지 확인합니다.

2. **패키지 설치 (Editable Mode)**
   // turbo
   ```bash
   pip install -e .
   ```
   이 명령을 통해 `pyproject.toml`에 정의된 `orchai` 명령어가 시스템에 등록됩니다.

3. **설정 파일 준비**
   - `config.json` 파일을 생성하여 사용할 드라이버(CLI 또는 API)를 설정합니다.

4. **설치 확인**
   // turbo
   ```bash
   orchai --help
   ```
   정상적으로 도움말이 출력되면 설치가 완료된 것입니다.
