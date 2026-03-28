---
description: OrchAI CLI 실행 및 실전 테스트 가이드
---

# 🚀 OrchAI 실행 워크플로우

본 문서는 사령부(`Architect`)가 승인한 공식 실행 가이드입니다. 

## 1. 전제 조건
- Python 3.10 (설치 경로: `C:\Users\song\AppData\Local\Programs\Python\Python310\python.exe`)
- `typer`, `rich` 패키지 설치 완료 (이미 사령관이 설치함)

## 2. 기본 실행 명령어 (PowerShell)

// turbo
```powershell
$env:PYTHONPATH="."
& "C:\Users\song\AppData\Local\Programs\Python\Python310\python.exe" apps/cli/main.py "Hello OrchAI!"
```

## 3. 주요 옵션
- `--mode [cli|api]`: 드라이버 모드 선택 (기본값: `cli` - 비용 0원)
- `--model [model_name]`: 명시적 모델 지정 (기본값: 오토셀렉트)

## 4. 트러블슈팅
- **ModuleNotFoundError:** 반드시 `$env:PYTHONPATH="."`를 먼저 실행하십시오.
- **WinError 2:** 로컬에 `claude` CLI가 설치되어 있고 로그인이 되어 있는지 확인하십시오.
