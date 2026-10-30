# 최석준의 GitHub 공동작업 따라 하기

## 현재 상태

- GitHub 계정: `hahahoho12360`
- 팀 저장소: https://github.com/bigpark61/AI_DevCoach
- 담당 브랜치: `feature/github-analysis`
- 첨부 v2 변경분과 자동 검사 결과를 이 브랜치로 제출할 준비가 끝났다.
- 현재 연동 앱의 브랜치 생성이 403으로 거부되어 원격 브랜치·커밋·PR은 아직 없다. 아래 웹 업로드 절차를 먼저 수행한다.
- 사용자의 요청에 따라 Codex가 작업을 보조했다. 본인 PC 실행 결과와 팀원의 리뷰는 별도로 남긴다.

## 용어를 학교 모둠 숙제로 생각하기

| 용어 | 쉬운 뜻 | 이번 프로젝트에서 하는 일 |
| --- | --- | --- |
| Repository | 모둠의 공용 숙제함 | 전체 프로그램과 변경 기록 보관 |
| Clone | 숙제함을 내 컴퓨터에 복사 | 기존 팀 작업 이력도 함께 받기 |
| Branch | 나의 작업용 갈래 | `main`을 직접 바꾸지 않고 작업 |
| Commit | 이름과 설명이 붙은 저장 지점 | 무엇을 바꿨는지 기록 |
| Push | 내 기록을 공용 숙제함으로 보내기 | 내 브랜치를 GitHub에 업로드 |
| Pull Request(PR) | 내 변경을 검토해 달라는 신청 | 팀원이 코드와 테스트 결과 검토 |
| Review | 친구의 확인과 의견 | 실제 검토 내용과 수정 요청 기록 |
| Merge | 검토한 변경을 공용 완성본에 합치기 | 승인된 내용을 `main`에 통합 |

브랜치 생성과 PR 작성만으로 팀원의 검토가 이루어진 것은 아니다. 실제 작업 내용과 테스트 결과를 설명하고 팀원에게 독립적인 검토를 받는 과정이 필요하다.

## 1. 웹에서 브랜치·업로드·PR 만들기

다운로드한 패키지의 `upload-to-github` 폴더에는 변경한 파일 8개만 들어 있다. 아래 절차로 올린다. 원본 카톡 ZIP 전체를 올리지 않는다.

1. GitHub에 `hahahoho12360`으로 로그인하고 https://github.com/bigpark61/AI_DevCoach 를 연다.
2. Code 화면의 브랜치 선택 버튼(`main`)을 누른다. `feature/github-analysis`를 입력하고 main에서 새 브랜치를 생성한다. 이미 같은 브랜치가 있다면 기존 작업부터 확인한다.
3. 화면에 `feature/github-analysis`가 선택되었는지 확인한다. `main`이 표시되어 있으면 아직 업로드하지 않는다.
4. Add file → Upload files를 누른다.
5. 파일 탐색기에서 `upload-to-github` 폴더를 열고, 그 안의 `backend`, `frontend`, `migrations`, `tests`, `docs` 폴더와 `README.md`를 선택하여 GitHub 업로드 화면으로 끌어 놓는다. 바깥 `upload-to-github` 폴더 자체를 끌어 놓지 않는다.
6. 업로드 목록이 `backend/main.py`, `frontend/app.js`처럼 저장소 최상위 기준의 경로인지 확인한다. 총 8개 파일이어야 한다. `.env`, DB 파일, ZIP 파일은 포함되지 않는다.
7. 커밋 제목은 `feat: import GitHub analysis v2 and validation notes`로 적는다. 본문에는 '팀에서 제공한 v2 소스를 반영하고 Codex 보조 자동 검사 결과를 기록함. Windows 수동 확인과 팀원 리뷰는 별도 진행'이라고 출처와 검사 범위를 설명한다.
8. 현재 `feature/github-analysis` 브랜치로 Commit changes를 누른다.
9. Pull requests → New pull request를 누른다. `base: main`, `compare: feature/github-analysis`를 선택한다.
10. Files changed에서 예상한 8개 파일인지 확인하고 Create pull request를 누른다. 제목은 `GitHub 분석 v2 반영 및 실행 검증 기록`으로 적는다. 패키지의 `PR_DESCRIPTION.txt`를 설명란에 복사한다.
11. 팀원에게 PR 링크를 공유하고 실제 검토를 받는다. 자동 검사 기록은 `docs/testing/2026-10-28-github-analysis.md`에서 확인한다. 직접 실행하지 않은 검사를 완료로 표시하지 않는다.

브랜치 생성이나 Upload files가 웹에서도 안 보이면, 팀장에게 `hahahoho12360`의 Collaborator 초대 수락 여부와 Write 권한을 확인해 달라고 요청한다. 사용자의 웹 작업 권한과 ChatGPT 연동 앱 권한은 별개다.

검토 기준 main은 `947ddb0f1a61ac9ab8413b779e676656179e73d3`이다. 그 이후 팀원이 같은 파일을 바꿨다면 이 패키지로 덮어쓰기 전에 최신 변경을 비교해야 한다.

## 1-1. 생성된 PR 확인

GitHub에 `hahahoho12360`으로 로그인한다. 팀 저장소의 Pull requests에서 GitHub 분석 v2 제출 PR을 연다. Conversation은 설명과 대화, Commits는 저장 기록, Files changed는 바뀐 파일이다.

이미 작성된 PR이 있다면 같은 내용을 다시 올리거나 같은 PR을 새로 만들 필요가 없다. 실제 변경사항을 같은 브랜치에 추가로 push하면 기존 PR에 반영된다.

## 2. 내 Windows PC에서 실행하기

Git와 Python 3.12 이상을 설치한다. 새 작업 폴더를 만들고 파일 탐색기 주소창에 `powershell`을 입력한 후 Enter를 누른다. 새로 열린 창에서 한 줄씩 실행한다.

```powershell
git --version
py -3.12 --version
git clone --branch feature/github-analysis https://github.com/bigpark61/AI_DevCoach.git AI_DevCoach-seokjun
cd AI_DevCoach-seokjun
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
```

- `git clone`: 팀의 코드와 작업 이력을 다운로드한다. 같은 폴더에서 한 번만 실행한다.
- `cd`: 이후 명령을 실행할 폴더로 들어간다.
- `venv`: 이 프로젝트에 쓸 부품 상자를 따로 만든다.
- `pip install`: 필요한 프로그램 부품을 설치한다.
- `unittest`: 정해진 동작이 맞는지 자동으로 확인한다. 마지막에 `Ran 10 tests`와 `OK`가 나오면 현재 10건이 통과한 것이다.
- `uvicorn`: 웹앱을 켠다. 실행 중인 PowerShell 창은 열어 둔다. 종료는 Ctrl+C.

Python 3.12 대신 다른 3.12 이상 버전이 이미 있다면 `py -0p`로 확인하고 `py -3.12`를 해당 버전으로 바꾼다. 가상환경을 직접 실행하므로 `Activate.ps1`이나 실행 정책 변경은 필요 없다.

브라우저 주소창에 다음을 입력한다.

- 앱: http://127.0.0.1:8000
- 상태 확인: http://127.0.0.1:8000/api/health

상태 확인에 `{"status":"ok","database":"sqlite"}`가 나타나는지 본다. 새 테스트 계정으로 가입·로그인한 뒤 프로필, 진단, 학습계획 흐름을 진행한다. GitHub 분석 메뉴는 학습 메뉴에 있다. 실제 저장소 분석은 외부 인터넷 연결이 필요하다.

기본 실행에는 카톡 ZIP의 `.env`, `data/`, `.venv/`, `node_modules/`를 복사할 필요가 없다. `.env` 없이 시작하면 새 SQLite DB가 만들어진다. 예시 PostgreSQL 주소가 있는 `.env.example`도 그대로 `.env`로 복사하지 않는다. 서술형 답안의 실제 AI 채점은 별도로 OpenAI 설정이 필요하다. API 키가 없어 실패한 것을 모든 기능의 오류로 기록하지 않는다.

## 3. 직접 확인한 결과 기록하기

본인이 직접 실행한 후에만 PC 운영체제, Python 버전, 실행 명령, 성공 여부, 실패한 단계와 오류 문구를 기록한다. PR에 결과를 남길 때 자동 검사와 본인의 수동 확인을 구분한다. 키·비밀번호가 보이는 화면은 올리지 않는다.

수동 검사 기록을 파일로 남기려면 `docs/testing/seokjun-windows-check.md`를 만들어 실제 확인 내용을 적는다. 내용이 없는 파일이나 의미 없는 변경으로 커밋 수를 늘리지 않는다.

## 4. 추가 작업을 커밋하고 올리기

먼저 GitHub Settings → Emails에서 본인의 커밋용 이메일을 확인한다. 개인 이메일 공개를 원하지 않으면 GitHub가 표시한 noreply 주소를 복사한다. 아래 `GITHUB에서_확인한_커밋용_이메일`은 그 실제 값으로 바꾼다.

```powershell
git config user.name "최석준"
git config user.email "GITHUB에서_확인한_커밋용_이메일"
git branch --show-current
git status
git add docs/testing/seokjun-windows-check.md
git diff --cached
git commit -m "test: record Windows execution check"
git push
```

`git add`는 다음 저장에 넣을 파일을 고른다. `git diff --cached`는 올라갈 내용을 미리 보여 준다. `git commit`은 내 컴퓨터에 기록을 만들고 `git push`는 GitHub에 보낸다. `git status`가 변경 없음이라고 하면 새로 저장할 작업이 없다는 뜻이며, 억지 커밋은 필요 없다. 첫 push에서 브라우저 로그인이 뜨면 본인 GitHub 계정으로 인증한다. GitHub 비밀번호를 명령줄 인증 암호로 사용하는 방식은 지원하지 않는다.

## 5. 팀원 리뷰와 통합

PR의 Files changed와 테스트 기록을 팀원이 검토하게 한다. 팀원은 발견한 문제나 확인한 내용을 작성하고 필요에 따라 Comment, Approve, Request changes를 선택한다. 작성자 본인의 확인은 다른 팀원의 승인과 구분된다.

수정 요청이 오면 수정·검사·커밋·push를 반복한다. 변경은 같은 PR에 누적된다. 검토와 테스트가 끝난 뒤 팀장 또는 합의된 담당자가 Merge한다. 공동작업 평가 자료로 PR 링크, 커밋 링크, 실제 리뷰 내용, 테스트 결과를 함께 보관한다. PR이 열려 있다는 것만으로 `main` 통합이 완료된 것은 아니다.

병합 후 다음 작업은 최신 main에서 새 브랜치로 시작한다.

```powershell
git switch main
git pull --ff-only origin main
git switch -c feature/next-task
```

## 처음 전달된 네 줄 명령이 부족한 이유

```text
git init
git remote add origin ...
git switch -c feature/github-analysis
git push -u origin feature/github-analysis
```

새 폴더라면 `git add`와 `git commit`이 없어서 보낼 커밋이 없다. 또한 팀 저장소에는 이미 이력이 있으므로 `git init`으로 별개의 이력을 만들기보다 `git clone`으로 기존 이력을 받는 것이 맞다. 이번 브랜치는 기존 main의 커밋을 이어받는다.

## 공식 참고자료

- GitHub 협업 흐름: https://docs.github.com/en/get-started/using-github/github-flow
- PR 빠른 시작: https://docs.github.com/en/pull-requests/get-started/pull-request-quickstart
- 커밋 이메일: https://docs.github.com/en/account-and-profile/how-tos/email-preferences/setting-your-commit-email-address
- Git add: https://git-scm.com/docs/git-add

## 이해 확인과 다음 요청 예시

각 명령을 실행하기 전에 '내 PC와 GitHub 중 어디가 바뀌는가?'를 예상하고, 실행 후 `git status`나 PR 화면으로 확인한다. 예상과 관찰이 다를 때 그 이유를 찾으면 명령어를 외우는 데서 한 걸음 더 나아갈 수 있다.

다음 요청 예시: '현재 PR과 변경 파일을 확인하고, 내가 직접 실행한 기록과 AI가 검사한 기록을 구분해 줘. 남은 작업을 목적·실행 방법·성공 화면·오류 대처 순서로 설명하고, 실제로 수행하지 않은 검증은 완료로 쓰지 마.'
