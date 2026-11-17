# AI DevCoach Lint 실행 및 후속 작업 안내

2026년 11월 16일 멘토링 일지의 최석준 담당 작업인 Lint 설정, 기존 코드 적용,
검사 방법 정리, AI 개발 지침 작성을 위한 안내다. 실제 수정·검증 기록은
[2026년 11월 18일 후속 검증 기록](testing/2026-11-18-cache-headers.md)을 확인한다.

## 기존 패치를 적용한 사용자에게 필요한 다음 작업

기존 AI_DevCoach_lint.patch를 적용했고 Lint·포맷·컴파일이 PASS인 상태라면
다시 clone하거나 기존 패치를 반복 적용하지 않는다. 아래는 Windows CMD 기준이다.
새 파일 AI_DevCoach_lint_followup.patch를 다운로드 폴더에 저장하고 진행한다.

```cmd
cd /d "C:\Users\bluestone\Desktop\AI_DevCoach_git"
git status
git branch --show-current
git apply --check "%USERPROFILE%\Downloads\AI_DevCoach_lint_followup.patch"
```

확인 명령이 성공했을 때만 다음을 실행한다. 기존 작업 브랜치를 유지한다.

```cmd
git apply "%USERPROFILE%\Downloads\AI_DevCoach_lint_followup.patch"
.venv\Scripts\python.exe scripts/check_quality.py --test
echo %ERRORLEVEL%
```

보조 검증 환경에서는 30개 테스트와 다섯 검사가 모두 통과했다. 사용자 PC에서도
같은 결과와 종료 코드 0을 확인하고 5~7단계로 진행한다.
SKILL.md와 docs/seokjun-lint-contribution.md를 읽고 직접 확인한 항목만 체크한다.
후속 패치를 적용한 뒤 아래의 최초 설치 절차 1~2를 반복할 필요는 없다.
패치 확인이 실패하면 강제 적용하지 말고 실제 파일 차이를 확인한다.

## 무엇을 검사하는가

| 구분 | 도구와 규칙 | 검사 범위 |
| --- | --- | --- |
| Python 정적 검사 | Ruff 0.17.5, E4·E7·E9·F·I | backend, migrations, tests, scripts 등 저장소 Python 파일 |
| Python 형식 검사 | Black 26.10.1, 88자 기준, Python 3.12 대상 | 같은 Python 파일 |
| JavaScript 검사 | ESLint 10.15.0, 권장 규칙 | frontend/app.js 및 JavaScript 설정 파일 |
| TypeScript 검사 | typescript-eslint 8.73.0, 권장 규칙 | neon.ts 등 TypeScript 파일, 타입 정보 없는 검사 |
| 기능 검사 | 기존 unittest 테스트 | 임시 SQLite DB와 모의 AI/GitHub 응답을 이용한 테스트 |

Lint는 코드를 실행하기 전에 정해진 규칙 위반을 찾는 검사다. Formatter는 줄바꿈,
공백 등 표현 형식을 통일한다. Test는 입력을 주었을 때 예상 결과가 나오는지 확인한다.
셋은 서로 대체하지 않는다. HTML/CSS lint, TypeScript 타입 검사, 운영 PostgreSQL,
실제 AI 응답 품질과 운영 사이트 검증은 이 공통 명령에 포함하지 않는다.

개발 도구 버전은 requirements-dev.txt와 package-lock.json으로 고정한다.
Python 실행 의존성은 기존 requirements.txt의 범위를 유지했으므로 모든 Python
간접 의존성이 고정된 것은 아니다. 기존 uv.lock은 변경하지 않았다.

## 1 최초 설치 시 저장소와 브랜치 확인

이번 작업은 코드 수정과 로컬 검증까지 완료했다. GitHub 연결의 브랜치 생성 요청은
403 권한 오류로 거부되었고 별도 Git 인증도 없어 원격 브랜치·커밋·PR은 만들지 못했다.
제공된 AI_DevCoach_lint.patch를 사용자 컴퓨터의 Downloads 폴더에 저장한다.

VS Code에서 AI_DevCoach 폴더를 열고 메뉴의 터미널 → 새 터미널을 선택한다.
origin이 팀 저장소인지, 수정 중인 파일이 없는지 먼저 확인한다.

```cmd
git remote -v
git status
git fetch origin
git switch -c chore/seokjun-lint origin/main
git apply --check "%USERPROFILE%\Downloads\AI_DevCoach_lint.patch"
git apply "%USERPROFILE%\Downloads\AI_DevCoach_lint.patch"
```

`--check`는 적용 가능한지만 확인하고 파일을 변경하지 않는다. 출력 없이 완료되고
`echo %ERRORLEVEL%` 실행 결과가 0이면 바로 다음 적용 명령을 실행한다. 이미 패치를 적용했으면
반복하지 않는다. 같은 이름의 브랜치가 있으면 새 작업명으로 생성한다.
기존 수정이 있거나 패치 확인이 실패하면 적용을 중단하고 오류를 확인한다.
팀원이 main을 추가로 수정하여 충돌하면 강제 덮어쓰지 말고 새 코드를 기준으로 조정한다.
파일을 다른 폴더에 저장했으면 Downloads 경로를 실제 다운로드 경로로 바꾼다.

## 2 최초 설치 시 검사 도구 설치

Python 3.12 이상과 Node.js 24 이상을 권장한다. ESLint 10의 실제 지원 범위는
Node.js ^20.19.0, ^22.13.0 또는 >=24.0.0이다.

```cmd
python --version
node --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
npm ci
```

이미 .venv가 있으면 생성 명령은 생략한다. PowerShell에서 npm 실행 정책 오류가
나면 `npm.cmd ci`를 사용한다. 가상환경 활성화나 컴퓨터 전체의 실행 정책 변경은
필요하지 않다. npm ci는 package-lock.json에 기록된 버전으로 node_modules를
재구성하므로 팀원이 같은 JavaScript 도구를 설치할 수 있다.

## 3 Lint와 포맷 검사

```cmd
.\.venv\Scripts\python.exe scripts/check_quality.py
echo %ERRORLEVEL%
```

요약에 Ruff, Black, ESLint가 모두 PASS이고 종료 코드가 0이면 이 검사는 통과다.
파일 내용을 자동으로 바꾸지 않는다. 한 검사가 실패해도 나머지 검사를 실행하고
결과를 모아서 보여 준다. Node.js나 ESLint가 없으면 실패로 보고하며 자동 설치하지 않는다.

각 도구를 따로 실행할 수도 있다.

```cmd
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m black --check .
npm run lint
```

Linux/macOS에서는 `.venv/bin/python scripts/check_quality.py`를 사용한다.

## 4 기능 테스트까지 확인

```cmd
.\.venv\Scripts\python.exe scripts/check_quality.py --test
echo %ERRORLEVEL%
```

이 명령은 앞의 세 검사에 unittest와 Python 컴파일 검사를 추가한다.
2026년 11월 17일에는 30개 중 1개가 실패했지만, 11월 18일 캐시 헤더를 수정한 뒤
보조 검증 환경에서 **30개 모두 성공**했다. 테스트 기대값은 유지했으며
`--test` 명령의 전체 종료 코드는 0이다. 사용자 PC의 결과는 직접 실행해 확인한다.

이 검증 환경에서는 SOCKS 프록시 환경변수 때문에 최초 테스트 1개가 추가 오류를 냈다.
외부 요청을 모의 응답으로 처리하는 테스트 실행 프로세스에서만 프록시 환경변수를
제외하자 해당 오류는 사라졌다. 이 처리는 운영 코드·의존성·팀 공통 스크립트에 반영하지 않았다.
프록시 오류가 없는 일반 환경에서는 별도 조치가 필요 없다.

## 5 변경 내용 검토 및 팀 검토 요청

```cmd
git diff --stat
git diff -- frontend/app.js pyproject.toml
git status --short
```

VS Code의 소스 제어 화면에서 설정, 중복 body 삭제, 포맷 변경을 확인한다.
Black 적용으로 줄 수가 많이 바뀌었지만 기능 변경과 포맷 변경을 구분해서 검토한다.
캐시 헤더 후속 수정까지 적용하여 테스트를 실행하고, 검토 완료 뒤 팀의 병합 절차를 따른다.
운영 환경 검증이 끝나기 전에는 운영 정상 동작까지 확인했다고 기록하지 않는다.

이번 변경은 비용을 유발하는 GitHub Actions를 새로 활성화하지 않는다. 아래 예시 커밋의
`[skip ci]`는 push/pull_request 워크플로 실행을 생략하기 위한 것으로, 코드의 Lint
규칙을 끄는 설정이 아니다. 로컬 검사 결과를 PR에 기록한다. 필수 CI가 설정된 팀에서는
검사가 Pending으로 남을 수 있으므로 유지관리자와 실행·비용 방침을 결정한다.

## 6 본인 계정으로 커밋 푸시 및 PR 만들기

패치를 적용하고 검사 결과와 변경 내용을 확인한 뒤 다음 명령을 사용한다.
새 파일과 변경 파일을 정확하게 선택하여 스테이징한다.

```cmd
.\.venv\Scripts\python.exe scripts/check_quality.py --test
git diff --check
git diff
git add .gitignore README.md pyproject.toml requirements-dev.txt package.json package-lock.json eslint.config.mjs AGENTS.md .agents/skills/lint/SKILL.md scripts/check_quality.py
git add backend/agent.py backend/ai_client.py backend/knowledge.py backend/main.py backend/planning.py frontend/app.js
git add migrations/env.py migrations/versions/0001_initial_schema.py migrations/versions/0002_github_analysis.py migrations/versions/0003_password_reset_tokens.py migrations/versions/0004_agent_chat_history.py
git add tests/browser_chat_smoke.py tests/test_app.py tests/test_chat_persistence.py docs/lint-guide-ko.md docs/testing/2026-11-17-lint.md docs/testing/2026-11-18-cache-headers.md docs/seokjun-lint-contribution.md
git diff --cached --stat
git commit -m "chore: apply lint standards, development skill and cache regression fix [skip ci]"
git push -u origin chore/seokjun-lint
```

GitHub 기여 기록을 본인 계정에 연결하려면 `git config user.name`과
`git config user.email`을 확인한다. 본인 GitHub에 등록된 이메일 또는 GitHub가
제공하는 noreply 주소를 저장소 범위에 설정한다. 타인의 작성자 정보를 사용하지 않는다.
AI의 도움을 받은 경우에도 실제 검토·실행·확인한 내용을 작업 기록에 남긴다.

푸시 후 GitHub 저장소의 Compare & pull request를 누르고 base: main,
compare: chore/seokjun-lint를 확인한다. 제목은 "Lint 기준 도입 및 AI 개발 지침 정리"로,
본문에는 실제 Lint·포맷·컴파일 결과와 테스트 결과를 적고 Create draft pull request를
선택한다. 로컬에서 30개 모두 성공했다면 그 사실을 기록한다. 팀 검토가 끝난 뒤 병합한다. 푸시 권한 오류가 발생하면
본인 계정으로 로그인되어 있는지와 팀 저장소의 쓰기 권한을 확인한다.

## 7 다음 AI 구현 요청에 적용

지침 원본은 `.agents/skills/lint/SKILL.md`이며 루트 AGENTS.md에서 참조한다.
ChatGPT 개인 스킬을 설치한 것은 아니다. 이 경로를 인식하지 않는 도구에는 파일을
직접 읽도록 요청한다. `${CLAUDE_PLUGIN_ROOT}`는 Claude 플러그인 실행 환경에
의존하므로 이 프로젝트의 공통 명령으로 사용하지 않는다.

> AGENTS.md와 .agents/skills/lint/SKILL.md를 먼저 읽고 이번 기능을 구현해 줘.
> 수정 전후 scripts/check_quality.py --test를 실행하고 새 오류, 기존 실패,
> 실행하지 못한 검사를 구분해 보고해 줘. 검사 통과를 위해 규칙이나 테스트 기대값을
> 완화하지 말고, 자동 수정 후 diff를 검토해 줘.

Lint 도입과 캐시 방지 테스트 수정 후에는 멘토링 일지의 실제 사용자 시나리오
검증을 이어 간다. 로그인 → 진단 → 계획 검토·승인 → 과제 제출·완료 → 통계 및
채팅 이력 확인 순서로 입력, 기대 결과, 실제 결과를 기록한다. 운영 DB와 실제 AI는
로컬 테스트와 별도의 검증 대상으로 다룬다.

## 메타 프롬프트와 자기 점검

> 이 변경이 완료되었다는 주장을 검사 종류별 증거로 검증해 줘. 정적 검사 통과,
> 기능 테스트 통과, 운영 환경 확인을 나누고 각 주장에 실행 명령·결과·미검증 범위를 붙여 줘.

스스로에게 “Lint가 0건이므로 서비스가 정상이라고 판단한 것은 아닌가?”를 묻는다.
이 질문에 답하는 근거가 실제 실행 기록인지까지 다시 확인하는 것이 판단 기준에 대한
자기 점검이다. 행동 연습으로 `--test` 없이 실행한 결과와 `--test`를 붙인 결과를
비교하고, 최초에는 왜 앞쪽만 성공했으며 후속 수정 뒤에는 무엇이 달라졌는지 설명해 본다.

## 근거

- 첨부된 AI 네이티브 파이널 프로젝트 멘토링 일지 2026년 11월 16일, 1.2·1.3·2.1 및 AI 개발 지침
- [Ruff 설정](https://docs.astral.sh/ruff/configuration/) 및 [검사와 자동 수정](https://docs.astral.sh/ruff/linter/)
- [Black 실행과 설정](https://black.readthedocs.io/en/stable/usage_and_configuration/the_basics.html)
- [ESLint 설정 파일](https://eslint.org/docs/latest/use/configure/configuration-files)
- [typescript-eslint 시작하기](https://typescript-eslint.io/getting-started/)
- [GitHub Actions 실행 생략](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/skip-workflow-runs)


## 선택 실습 Lint의 실제 작동 확인

소스 파일을 바꾸지 않고 표준입력으로 잘못된 코드와 정상 코드를 검사한다.

```cmd
echo print(missing_name) | .venv\Scripts\python.exe -m ruff check --stdin-filename practice.py -
echo print(123) | .venv\Scripts\python.exe -m ruff check --stdin-filename practice.py -
```

첫 번째는 정의되지 않은 이름 F821을 보고하고 두 번째는 통과해야 한다.
이것은 검사 도구가 실제 오류를 잡는지 확인하는 짧은 연습이다. 저장소 규칙을 변경하지 않는다.

## 증빙 및 제출

최종 실행 후 터미널의 Ran 30 tests / OK / 다섯 PASS 부분을 캡처한다.
실행 로그를 보관하려면 다음을 사용할 수 있다. 임시 로그를 저장소 밖에 저장하므로
실수로 소스와 함께 커밋될 가능성을 줄인다.

```cmd
.venv\Scripts\python.exe scripts/check_quality.py --test > "%TEMP%\AI_DevCoach_lint_final.txt" 2>&1
echo %ERRORLEVEL%
type "%TEMP%\AI_DevCoach_lint_final.txt"
```

실제 확인한 결과로 docs/seokjun-lint-contribution.md의 체크리스트와 실행 일시를
채운다. 커밋 후 아래 명령으로 해시를 확인하고 GitHub의 해당 커밋 URL과 PR URL을
제출 보고서에 기록한다. 캡처를 공개할 때 계정 정보나 키가 보이지 않는지 확인한다.

```cmd
git log -1 --oneline
git status
```
