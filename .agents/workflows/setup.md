---
description: OrchAI 개발 환경 설정 및 로컬 설치 가이드
---

# 🛠️ OrchAI 셋업 워크플로우

본 문서는 팀원들이 로컬 환경을 동기화하기 위한 가이드입니다.

## 1. 의존성 설치 (Architect Path)

// turbo
```powershell
& "C:\Users\song\AppData\Local\Programs\Python\Python310\python.exe" -m pip install typer[all] rich pydantic-settings
```

## 2. 드라이버 확인
- `where.exe claude`를 실행하여 경로가 잡히는지 확인합니다.
- 인증이 필요한 경우 `claude.cmd`를 통해 미리 로그인하십시오.

## 3. 프로젝트 초기 파일 생성
- `config.json`의 스키마는 `ConfigService` 가이드에 따릅니다.
