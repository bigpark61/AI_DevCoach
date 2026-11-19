---
name: lint
description: AI DevCoach의 lint 오류 수정 및 Python·JavaScript·TypeScript 기능 구현 시 기존 규칙을 확인하고 코드 검사, Python 포맷 검사, 관련 테스트와 변경 내역 검토를 수행한다. 코드 품질 개선 요청과 구현 전후 검증에 사용한다.
---

# AI DevCoach Lint 및 개발 지침

## 구현 전

- 저장소 루트의 AGENTS.md와 하위 지침, git status, pyproject.toml, eslint.config.mjs, requirements-dev.txt, package.json을 확인한다.
- Python 3.12 이상, 3.14 미만과 Node.js 24 이상을 사용한다. Python 개발 도구는 requirements-dev.txt, JavaScript 도구는 package-lock.json의 버전을 따른다.
- `.venv`의 Python으로 `scripts/check_quality.py --test`를 실행하여 수정 전 결과와 종료 코드를 기록한다. 도구가 없으면 미실행으로 보고하고 설치 방법을 안내한다. 검사를 건너뛴 결과를 통과로 보고하지 않는다.
- 검사 대상은 저장소의 Python 코드, JavaScript 및 TypeScript 코드다. HTML/CSS lint, TypeScript 타입 검사, 운영 환경 검증은 별도 작업이다.

## 구현 중

- Ruff의 E4·E7·E9·F·I 규칙과 Black, ESLint 권장 규칙을 따른다. 검사 통과를 위해 규칙을 끄거나 완화하거나 파일을 추가로 제외하지 않는다.
- 요청 범위에서 수정한다. 자동 수정이 필요하면 변경 내역을 검토하고 Ruff `--fix`와 Black을 사용한다. `--unsafe-fixes`는 사용하지 않는다.
- 중복 키, 사용하지 않는 import, import 순서와 포맷 변경을 구분하고 동작 변경 여부를 검토한다.
- `.env`, 키, 로컬 DB, 가상환경, node_modules를 커밋하지 않는다. 실제 AI 호출이나 운영 DB 변경 없이 가능한 검증을 우선한다.

## 구현 후

저장소 루트에서 Windows CMD 또는 PowerShell로 실행한다. 사용자 화면의 셸을 먼저 확인하고, CMD에서는 `%USERPROFILE%`·`echo %ERRORLEVEL%`, PowerShell에서는 `$env:USERPROFILE`·`$LASTEXITCODE`를 사용한다.

```text
.\.venv\Scripts\python.exe scripts/check_quality.py
.\.venv\Scripts\python.exe scripts/check_quality.py --test
git diff --check
git diff --stat
git diff
```

Linux/macOS에서는 `.venv/bin/python`으로 같은 스크립트를 실행한다. 스크립트는 다른 작업 디렉터리에서도 저장소 루트를 찾아 검사한다. 파일 수정, 도구 설치, 커밋·푸시는 수행하지 않는다.

- 각 실패에 파일·행, 규칙 ID, 원인, 수정 제안과 종료 코드를 기록한다. 도구의 error/warning 수준과 실제 서비스 위험도를 혼동하지 않는다.
- 실행을 막는 오류, 경고, 형식 문제를 구분하되 프로젝트에서 요구하는 Black 형식 검사를 선택 사항으로 낮추지 않는다.
- 수정 전부터 실패한 테스트, 새 실패, 미실행 검사를 구분한다. Lint 통과와 기능 테스트 통과를 별도로 보고한다.
- 커밋·푸시가 요청된 경우 변경 내용과 검사 결과를 확인하고 담당자의 작업 브랜치에서 진행한다. 알려진 실패가 남으면 그 사실을 공개하고 검토용 초안으로 남긴다.
- main 병합, 운영 배포, GitHub Actions 활성화는 해당 요청과 현재 팀의 운영 방침을 확인한다.

팀원의 설치·실행 절차와 검증 범위는 [검사 안내](../../../docs/lint-guide-ko.md)를 확인한다.
