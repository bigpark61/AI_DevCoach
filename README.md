# AI DevCoach

AI DevCoach MVP for account registration, learner profiling, skill assessment, and personalized learning plans.

**2026-11-18 code-quality update:** Ruff, Black and ESLint checks pass. After adding
chat-history response cache headers, all 30 application tests pass in the verification environment.
The previous 29/30 result is retained in the dated historical record. See the
[Korean lint setup and follow-up guide](docs/lint-guide-ko.md) and
[verification record](docs/testing/2026-11-18-cache-headers.md). Earlier dated verification below is historical.

## Live deployments

- Vercel: https://ai-dev-coach.vercel.app

## Run locally

Requires Python 3.12 or newer.

```powershell
uv run --with-requirements requirements.txt uvicorn backend.main:app --reload
```

Open http://127.0.0.1:8000. Without `DATABASE_URL`, local development uses SQLite at `data/devcoach.db`.

To use Neon/PostgreSQL, set `DATABASE_URL` to the pooled connection string. Set `COOKIE_SECURE=true` when serving over HTTPS. The existing SQLite database is not copied automatically.

### Windows PowerShell: reproducible setup (without `uv`)

The `uv` command above is the documented default. If `uv` is unavailable, use the following steps from the repository root (Python 3.12+ required):

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
```

Open `http://127.0.0.1:8000` and `http://127.0.0.1:8000/docs` to check the local app and API documentation. These examples do not require activating PowerShell scripts. If you choose to activate the environment instead, follow your organization's execution-policy rules; do not permanently weaken machine-wide policy.

### Local automated testing and formatting

Install the pinned development tools, then run the shared checks (Python 3.12+, Node.js 24+ recommended):

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
npm ci
.\.venv\Scripts\python.exe scripts/check_quality.py
.\.venv\Scripts\python.exe scripts/check_quality.py --test
```

The script **checks without modifying source files**. It runs Ruff, Black and ESLint;
`--test` also runs unittest and Python compilation. Missing tools and failed checks produce
a nonzero exit code. Lint success does not establish functional correctness.

**Observed local verification, 2026-11-15:** In the supplied Windows PowerShell session, `21 passed, 1 warning` was recorded after a change to the activity-log query's tie-break ordering in `backend/main.py`. The warning concerned a deprecated Starlette `TestClient` import. This is a recorded snapshot, not a guarantee that a fresh checkout or deployed service passes all tests today.

## Password reset

Password reset links are single-use and expire after 30 minutes. Configure `APP_BASE_URL`, `SMTP_HOST`, `SMTP_PORT`, and `SMTP_FROM`, plus `SMTP_USERNAME` and `SMTP_PASSWORD` when required by the provider. Set `SMTP_USE_SSL=true` for implicit TLS; otherwise SMTP STARTTLS is used. Keep SMTP credentials in the ignored `.env` file or deployment secret settings.

For local development only, set `PASSWORD_RESET_DEV_MODE=true` while `COOKIE_SECURE` is not `true`. The reset request screen then shows a local test link instead of sending email. Do not enable this mode in deployed environments; production reset links are sent only by email. After changing a password, all active sessions for that account are revoked.

## Admin dashboard

Set `ADMIN_EMAILS` to a comma-separated list of existing account email addresses to enable the Admin dashboard and its user-progress API. For example, set `ADMIN_EMAILS=coach@example.com,owner@example.com` in the local environment or deployment secrets. Only those signed-in accounts can access `/api/admin/overview`; changing the list takes effect on the next request. The dashboard shows account and task-progress summaries without exposing learner notes.

## Deploy to Vercel

1. Push the repository to GitHub, then import it as a new Vercel project. Set the project root to the repository root; choose the **Other** framework preset if Vercel does not detect the project automatically.
2. In **Project Settings > Environment Variables**, set `DATABASE_URL` to the pooled PostgreSQL connection string, `DATABASE_URL_UNPOOLED` to the direct connection string, and `COOKIE_SECURE` to `true`. Add `OPENAI_API_KEY` to enable written-answer grading; `OPENAI_MODEL` is optional.
3. Before the first deployment, set `DATABASE_URL_UNPOOLED` in your local, ignored `.env` file and apply the database migrations using the commands in [Database migrations before deployment](#database-migrations-before-deployment).
4. Deploy from the Vercel dashboard or with the Vercel CLI. With GitHub connected, pushes to the configured branch trigger deployments automatically. The FastAPI entrypoint is configured as `backend.main:app` in `pyproject.toml`.
5. Open the deployment URL and verify `/api/health` returns `{"status":"ok", ...}`.

Use a separate database or Neon branch for Vercel Preview deployments; do not point previews at production data.

## Database migrations before deployment

Set `DATABASE_URL_UNPOOLED` in the local `.env` file to the direct (non-pooled) PostgreSQL connection string, then run:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Run migrations before the first deployment and before deploying any later schema change. The app does not modify the PostgreSQL schema at startup. Keep `.env` out of Git.

## Neon and PostgreSQL

`DATABASE_URL` is used by the app for pooled runtime queries. Alembic prefers `DATABASE_URL_UNPOOLED` for migrations. Both values are loaded from `.env` locally; the environment file is ignored by Git.

Run `npm run build` to invoke the project's Python backend compile-check script (`python -m compileall -q backend`); this is **not** a frontend bundle build or a substitute for automated tests. `/api/health` is intended to verify database connectivity; check the actual live response during deployment verification.

## AI provider, RAG, and learning agent

Objective questions are still scored by answer-key comparison. Written answers use a structured rubric (root-cause understanding: 4 points, solution: 4 points, clarity: 2 points). AI requests run only on the backend; credentials are never sent to the browser.

For OpenAI, set `OPENAI_API_KEY` before starting the server. `OPENAI_MODEL` defaults to `gpt-4o-mini`; `AI_MODEL` overrides it when a provider requires a different catalog model ID. `OPENAI_BASE_URL` is optional for OpenAI-compatible providers.

```powershell
$env:OPENAI_API_KEY = "your-openai-api-key"
$env:OPENAI_MODEL = "gpt-4o-mini"
uv run --with-requirements requirements.txt uvicorn backend.main:app --reload
```

The OpenAI-compatible Neon AI Gateway can be used instead by setting `NEON_AI_GATEWAY_TOKEN` and `NEON_AI_GATEWAY_BASE_URL`. The gateway is optional and requires `aiGateway: true` on a supported paid Neon project; this repository does not enable or provision it automatically. Set `AI_MODEL` to an enabled model from that branch's catalog.

The AI Coach and plan generator use BM25 retrieval over the curated Markdown library in `backend/knowledge/`. The chat shows source IDs in answers. Its tools are read-only: search the library, inspect the signed-in user's current progress, and list that user's tasks. It cannot change plans or progress. AI-generated plan content is merged into the existing validated schedule; if the provider is unavailable, sources are missing, or generated output fails validation, the deterministic rules-based plan is retained. The current RAG corpus is local and lexical; it does not yet use embeddings or external documents. Without an AI provider, written-answer grading and Agent chat return a configuration error; the existing record-based progress coach remains available.

## Included flows

- Email/password signup and login, single-use email password reset, required consent capture, server-side PBKDF2 password hashing, and HttpOnly session cookies.
- Learner profile creation and updates.
- A resumable 22-question assessment (20 objective and 2 written answers), objective scoring, OpenAI rubric-based written-answer scoring, and competency feedback.
- Personalized weekly plan drafts using the learner profile and latest assessment, time/structure validation, editable drafts, and explicit approval.
- Source-cited AI Coach with local RAG search and bounded, user-scoped read-only tools.

Plan generation uses retrieved sources when an AI provider is configured, with a deterministic rules-based fallback. Email verification is not configured in this MVP. SMTP must be configured to deliver password-reset links outside local development mode.


## Implementation boundaries and current verification

This README describes an **MVP**, not a fully autonomous learning agent. The current RAG implementation performs lexical BM25 retrieval on the bundled Markdown library; it does **not** support embedding-based search or arbitrary external-document ingestion. Agent chat and its tools are currently read-only, and learner progress / plan modifications require their existing dedicated application workflows. An AI provider must be configured for written-answer grading and AI chat.

| Item | Evidence / status |
| --- | --- |
| Local Python unit/integration test run | **Observed:** 21 passed, 1 deprecation warning, 2026-11-15 |
| Activity-log ordering bug fix | **Observed:** `ORDER BY created_at DESC, rowid DESC` tested locally and merged into `main` via GitHub PR, 2026-11-15 |
| Black style check | **Observed:** Black installed; `backend/main.py` **would be reformatted**; formatting was not applied |
| GitHub branch / PR | **Observed:** `chore/apply-black` was merged into `main`; despite the branch name, the PR contained an activity-log sorting fix rather than a Black reformat |
| Vercel deployment | Deployment URL documented above; a GitHub PR preview displayed **Ready**. **Not independently verified:** health, end-to-end signup, database access, AI grading, and post-merge production rollout |
| PostgreSQL/Neon migrations | Instructions are documented; production migration execution and schema state were **not** verified as part of this review |
| Authentication, admin, password reset | Described in the project; email delivery, security properties, and production permissions require dedicated staging/production checks |

**SQLite ordering note.** The activity-log table declares a `TEXT PRIMARY KEY`, and the reported local fix sorts by `created_at DESC, rowid DESC`. That tie-break approach is SQLite-specific. If the same query is used against PostgreSQL, verify portability and choose an explicit, database-independent order column/sequence or an equivalent deterministic strategy before production rollout. Test timestamp ties intentionally.

## Post-deployment verification checklist

- [ ] Run `python -m pytest -q` in a freshly installed environment and save the actual output.
- [ ] Verify `/api/health` on the deployed URL; record the HTTP status and body (without secrets).
- [ ] Confirm database migrations ran on the intended PostgreSQL branch before deployment.
- [ ] Verify signup/login/logout, consent, authorization boundaries, and password reset in a non-production test account.
- [ ] Verify assessment resume, objective scoring, written-answer grading with a configured AI provider, and the no-provider fallback.
- [ ] Verify plan draft, review, approval, task submission/completion, time logs, and activity-log newest-first order—including equal timestamps.
- [ ] Confirm AI Coach citations refer to real library documents; verify the read-only tool permissions.
- [ ] Keep preview and production databases separate; check that no secrets or `.env` files are committed.
- [ ] Check Vercel production deployment after the `main` merge; a preview's Ready status alone does not establish this.

## Proposed next development milestones (not yet implemented)

1. **Ordering portability and regression tests:** Replace any SQLite-only sorting reliance with an explicit total order that behaves consistently across SQLite and PostgreSQL; add a test with identical timestamps and different insertion order.
2. **Continuous integration:** Run a clean dependency install, `pytest`, Python compilation, and selected formatting checks on each pull request, without blindly formatting the codebase.
3. **Agent decision and action loop:** For each learner query, read the profile, prior mistakes, assessment and activity history; determine the next learning action; produce relevant practice; evaluate the response; store errors; and propose a new plan. Any durable plan or progress change should have scoped authorization, validation, logging, and clear user confirmation where appropriate.
4. **Personalization evaluation:** Define measurable success criteria such as relevance to learner weaknesses, correctness of retrieved citations, successful re-planning, error-revisit rate, and avoidance of duplicate exercises.
5. **Operations and privacy:** Add health-check evidence, failure alerts, logging/retention policy, backup/restore drills, token/secret handling, and staging/production separation.

## Contribution workflow and shared-computer precautions

```powershell
git switch main
git pull origin main
git switch -c fix/your-change
# After editing and testing:
git diff
git add backend/main.py
git commit -m "fix: describe the specific change"
git push -u origin fix/your-change
```

Open a pull request, review the file changes and checks, then merge. On a shared computer, use repository-scoped Git identity rather than relying on unknown auto-populated author metadata, and sign out of connected services when finished. Do not commit `.env`, credentials, local databases, or `.venv`.





# AI DevCoach

AI DevCoach는 계정 등록, 학습자 프로필, 역량 평가, 개인화 학습계획을 제공하는 최소 기능 제품(MVP)입니다.

## 운영 중인 배포 주소

- Vercel: https://ai-dev-coach.vercel.app

## 로컬 환경에서 실행하기

Python 3.12 이상이 필요합니다.

```powershell
uv run --with-requirements requirements.txt uvicorn backend.main:app --reload
```

웹브라우저에서 http://127.0.0.1:8000 을 여세요. `DATABASE_URL`을 설정하지 않으면 로컬 개발 환경에서는 `data/devcoach.db`에 있는 SQLite 데이터베이스를 사용합니다.

Neon/PostgreSQL을 사용하려면 `DATABASE_URL`을 연결 풀링(pooled connection) 문자열로 설정합니다. HTTPS로 서비스를 제공할 때는 `COOKIE_SECURE=true`를 설정합니다. 기존 SQLite 데이터베이스는 자동으로 복사되지 않습니다.

### Windows PowerShell: `uv` 없이 개발환경 재현하기

위 `uv` 명령어는 문서에 기재된 기본 실행 방법입니다. `uv`를 사용할 수 없다면 저장소의 최상위 폴더에서 다음과 같이 실행할 수 있습니다(Python 3.12 이상 필요).

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
```

`http://127.0.0.1:8000`과 `http://127.0.0.1:8000/docs`에 접속하여 로컬 애플리케이션과 API 문서를 확인합니다. 이 명령어는 PowerShell의 가상환경 활성화 스크립트를 실행하지 않아도 됩니다. 직접 가상환경을 활성화하려는 경우 소속 기관의 스크립트 실행 정책을 따르고, 컴퓨터 전체의 보안 정책을 영구적으로 완화하지 마세요.

### 로컬 자동 테스트 및 코드 형식 검사

Python 3.12 이상, Node.js 24 이상을 권장합니다. 개발 도구를 설치하고 팀 공통 명령으로 검사합니다.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
npm ci
.\.venv\Scripts\python.exe scripts/check_quality.py
.\.venv\Scripts\python.exe scripts/check_quality.py --test
```

스크립트는 **소스 파일을 수정하지 않고** Ruff·Black·ESLint 검사를 실행합니다.
`--test`를 붙이면 unittest와 Python 컴파일 검사도 실행합니다. 2026년 11월 18일
캐시 헤더 수정 후 검증 환경에서 Lint·포맷·컴파일과 기능 테스트 30개가 모두 통과했습니다.
자세한 설치와 후속 작업은 [Lint 실행 안내](docs/lint-guide-ko.md), 실제 결과와
미검증 범위는 [검증 기록](docs/testing/2026-11-18-cache-headers.md)을 확인하세요.

**2026년 11월 15일 로컬 검증 기록:** 제공된 Windows PowerShell 실행 화면에서 `backend/main.py`의 활동 기록 조회 순서를 수정한 뒤 `21 passed, 1 warning`이 확인되었습니다. 경고는 Starlette `TestClient`의 사용 중단 예정(deprecated) 가져오기 방식과 관련이 있습니다. 이는 당시 확인된 실행 기록이며, 새로 내려받은 저장소나 현재 배포된 서비스의 모든 테스트가 통과한다는 보장은 아닙니다.

## 비밀번호 재설정

비밀번호 재설정 링크는 한 번만 사용할 수 있으며 30분 후 만료됩니다. `APP_BASE_URL`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_FROM`을 설정하고, 이메일 제공업체에서 요구한다면 `SMTP_USERNAME`, `SMTP_PASSWORD`도 설정합니다. 암시적 TLS(implicit TLS)를 사용할 때는 `SMTP_USE_SSL=true`를 설정하며, 그렇지 않으면 SMTP STARTTLS를 사용합니다. SMTP 인증정보는 Git에서 제외되는 `.env` 파일 또는 배포 서비스의 비밀 환경변수 설정에 보관합니다.

로컬 개발용으로만 `COOKIE_SECURE`가 `true`가 아닌 상태에서 `PASSWORD_RESET_DEV_MODE=true`를 설정할 수 있습니다. 이 경우 비밀번호 재설정 요청 화면에 이메일 전송 대신 로컬 테스트 링크가 표시됩니다. 배포 환경에서는 이 모드를 활성화하지 마세요. 운영 환경의 비밀번호 재설정 링크는 이메일로만 발송됩니다. 비밀번호가 변경되면 해당 계정의 모든 활성 세션이 무효화됩니다.

## 관리자 대시보드

`ADMIN_EMAILS`에 기존 계정의 이메일 주소를 쉼표로 구분해 입력하면 관리자 대시보드와 사용자 학습진도 API를 사용할 수 있습니다. 예를 들어 로컬 환경변수 또는 배포 비밀 설정에서 `ADMIN_EMAILS=coach@example.com,owner@example.com`과 같이 지정합니다. 지정된 이메일 계정으로 로그인한 사용자만 `/api/admin/overview`에 접근할 수 있으며, 목록 변경은 다음 요청부터 적용됩니다. 대시보드는 학습자의 개인 메모를 공개하지 않으면서 계정과 과제 진행 상황의 요약을 제공합니다.

## Vercel에 배포하기

1. 저장소를 GitHub에 올린 뒤 Vercel의 새 프로젝트로 가져옵니다. 프로젝트 루트는 저장소 최상위 폴더로 설정하고, Vercel이 프로젝트 유형을 자동으로 인식하지 못한다면 프레임워크 프리셋으로 **Other**를 선택합니다.
2. **Project Settings > Environment Variables**에서 `DATABASE_URL`은 풀링된 PostgreSQL 연결 문자열, `DATABASE_URL_UNPOOLED`는 직접 연결 문자열, `COOKIE_SECURE`는 `true`로 설정합니다. 서술형 답안 채점을 활성화하려면 `OPENAI_API_KEY`를 추가합니다. `OPENAI_MODEL`은 선택 사항입니다.
3. 첫 배포 전 로컬의 Git 제외 대상 `.env` 파일에 `DATABASE_URL_UNPOOLED`를 지정하고, 아래 [배포 전 데이터베이스 마이그레이션](#배포-전-데이터베이스-마이그레이션)의 명령어로 마이그레이션을 적용합니다.
4. Vercel 대시보드 또는 Vercel CLI를 이용해 배포합니다. GitHub를 연결한 경우 설정된 브랜치에 푸시하면 자동 배포가 시작됩니다. FastAPI 진입점은 `pyproject.toml`에서 `backend.main:app`으로 설정되어 있습니다.
5. 배포 주소를 열어 `/api/health`에서 `{"status":"ok", ...}` 형태의 응답이 반환되는지 확인합니다.

Vercel 미리보기(Preview) 배포에는 별도 데이터베이스 또는 Neon 브랜치를 사용하세요. 미리보기 배포가 운영 데이터를 직접 사용하도록 연결하지 마세요.

## 배포 전 데이터베이스 마이그레이션

로컬 `.env` 파일에서 `DATABASE_URL_UNPOOLED`를 풀링되지 않은 PostgreSQL 직접 연결 문자열로 설정한 다음 실행합니다.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m alembic upgrade head
```

첫 배포 전과 이후 데이터베이스 스키마가 변경되는 배포 전에 마이그레이션을 실행해야 합니다. 애플리케이션은 실행을 시작할 때 PostgreSQL 스키마를 자동으로 수정하지 않습니다. `.env` 파일을 Git에 올리지 마세요.

## Neon 및 PostgreSQL

애플리케이션은 실행 중 풀링된 데이터베이스 조회에 `DATABASE_URL`을 사용합니다. Alembic은 마이그레이션에 `DATABASE_URL_UNPOOLED`를 우선 사용합니다. 로컬에서는 두 값 모두 `.env`에서 불러오며, 이 환경변수 파일은 Git 추적에서 제외됩니다.

`npm run build`를 실행하면 프로젝트의 Python 백엔드 컴파일 검사 스크립트(`python -m compileall -q backend`)가 실행됩니다. 이는 **프론트엔드 번들 빌드가 아니며 자동 테스트를 대체하지도 않습니다.** `/api/health`는 데이터베이스 연결 상태를 검증하도록 설계되어 있으므로 배포 확인 단계에서 실제 응답을 점검해야 합니다.

## AI 제공업체, RAG 및 학습 에이전트

객관식 문항은 정답표와 답안을 비교하여 채점합니다. 서술형 답안은 구조화된 평가 기준을 사용합니다(원인 이해: 4점, 해결책: 4점, 명확성: 2점). AI 요청은 백엔드에서만 실행되며 인증정보는 브라우저에 전달하지 않습니다.

OpenAI를 사용한다면 서버를 실행하기 전에 `OPENAI_API_KEY`를 설정합니다. `OPENAI_MODEL`의 기본값은 `gpt-4o-mini`이며, 제공업체에 따라 다른 모델 ID가 필요하면 `AI_MODEL`이 이 값을 덮어씁니다. OpenAI 호환 제공업체에서는 `OPENAI_BASE_URL`을 선택적으로 지정할 수 있습니다.

```powershell
$env:OPENAI_API_KEY = "your-openai-api-key"
$env:OPENAI_MODEL = "gpt-4o-mini"
uv run --with-requirements requirements.txt uvicorn backend.main:app --reload
```

OpenAI 호환 Neon AI Gateway를 사용하려면 `NEON_AI_GATEWAY_TOKEN`과 `NEON_AI_GATEWAY_BASE_URL`을 설정할 수 있습니다. Gateway는 선택 사항이며, 지원되는 유료 Neon 프로젝트에서 `aiGateway: true`가 필요합니다. 이 저장소는 Gateway를 자동으로 활성화하거나 생성하지 않습니다. 해당 브랜치의 모델 목록에서 사용 가능한 모델을 골라 `AI_MODEL`에 설정합니다.

AI Coach와 학습계획 생성기는 `backend/knowledge/`의 선별된 Markdown 자료를 대상으로 BM25 검색을 사용합니다. 채팅 답변에는 자료 출처 ID가 표시됩니다. 사용 가능한 도구는 읽기 전용으로, 자료 검색, 로그인한 사용자의 현재 학습진도 확인, 해당 사용자의 과제 목록 조회만 수행합니다. **이 도구들은 학습계획이나 진도를 변경할 수 없습니다.** AI가 생성한 계획 내용은 검증된 기존 일정 구조에 합쳐집니다. AI 제공업체를 사용할 수 없거나, 출처가 없거나, 생성 결과가 검증을 통과하지 못하면 규칙 기반으로 생성한 계획을 유지합니다. 현재 RAG 자료집은 로컬 텍스트 검색 방식이며 임베딩이나 외부 문서는 아직 사용하지 않습니다. AI 제공업체가 설정되지 않으면 서술형 답안의 AI 채점과 에이전트 채팅은 설정 오류를 반환하지만, 기존 기록 기반 학습진도 코치는 사용할 수 있습니다.

## 포함된 주요 기능 흐름

- 이메일과 비밀번호를 이용한 회원가입 및 로그인, 1회용 비밀번호 재설정 링크, 필수 동의 기록, 서버 측 PBKDF2 비밀번호 해싱, HttpOnly 세션 쿠키
- 학습자 프로필 생성 및 수정
- 중단 후 다시 이어갈 수 있는 22문항 평가(객관식 20문항, 서술형 2문항), 객관식 채점, OpenAI 평가 기준에 따른 서술형 채점, 역량 피드백
- 학습자 프로필과 최근 평가에 기반한 주간 개인화 학습계획 초안, 시간과 구조 검증, 초안 수정, 명시적 승인 절차
- 로컬 RAG 검색과 사용자별 접근 범위가 제한된 읽기 전용 도구를 활용하는 출처 표시형 AI Coach

AI 제공업체가 설정되어 있으면 검색 자료를 활용하여 계획을 생성하고, 실패 시에는 결정적 규칙 기반 방식으로 대체합니다. 이 MVP에는 이메일 주소 인증이 설정되어 있지 않습니다. 로컬 개발 모드가 아닌 환경에서 비밀번호 재설정 링크를 발송하려면 SMTP 설정이 필요합니다.

## 구현 범위와 현재 검증 상태

이 README가 설명하는 것은 **MVP이며 완전 자율형 학습 에이전트가 아닙니다.** 현재 RAG는 포함된 Markdown 자료를 BM25 방식으로 검색하며, **임베딩 기반 검색이나 임의의 외부 문서 수집 기능은 지원하지 않습니다.** 에이전트 채팅과 도구는 현재 읽기 전용이므로, 학습진도와 계획을 수정하려면 기존 애플리케이션의 별도 기능을 사용해야 합니다. 서술형 채점과 AI 채팅에는 AI 제공업체 설정이 필요합니다.

| 항목 | 근거 및 상태 |
| --- | --- |
| 로컬 Python 단위·통합 테스트 | **실행 화면 확인:** 2026-11-15에 21개 통과, 사용 중단 예정 기능 경고 1개 |
| 활동 기록 정렬 오류 수정 | **실행 화면 확인:** `ORDER BY created_at DESC, rowid DESC`를 로컬에서 테스트하고 2026-11-15 GitHub PR을 통해 `main`에 병합 |
| Black 코드 스타일 검사 | **실행 화면 확인:** Black 설치 완료. `backend/main.py`는 **형식 변경이 필요하다는 결과**였으며, 실제 포맷팅은 적용하지 않음 |
| GitHub 브랜치 및 PR | **실행 화면 확인:** `chore/apply-black`을 `main`에 병합. 브랜치 이름과 달리 PR 내용은 Black 포맷팅이 아니라 활동 기록 정렬 수정임 |
| Vercel 배포 | 위에 배포 주소가 기재되어 있으며 GitHub PR 미리보기에는 **Ready**가 표시됨. **독립적으로 검증하지 못한 사항:** 헬스 체크, 회원가입 전체 흐름, 데이터베이스 접근, AI 채점, 병합 이후 운영 배포 |
| PostgreSQL/Neon 마이그레이션 | 실행 방법은 문서화했지만, 검토 과정에서 운영 데이터베이스의 마이그레이션 실행 및 스키마 상태는 확인하지 못함 |
| 인증, 관리자, 비밀번호 재설정 | 프로젝트에 기능이 설명되어 있으나 이메일 전송, 보안 속성, 운영 환경 권한은 스테이징 또는 운영 환경에서 별도 검증해야 함 |

**SQLite 정렬 관련 주의사항:** 활동 기록 테이블은 `TEXT PRIMARY KEY`를 사용하고, 보고된 로컬 수정은 `created_at DESC, rowid DESC`로 정렬합니다. 이 보조 정렬 방식은 SQLite에 한정됩니다. 동일한 조회문을 PostgreSQL에서도 사용한다면 호환성을 검증하고, 운영 반영 전에 데이터베이스와 무관하게 순서가 결정되는 별도의 정렬 열·일련번호 또는 이에 준하는 전략을 선택해야 합니다. 시간값이 동일한 상황도 의도적으로 테스트하세요.

## 배포 이후 검증 체크리스트

- [ ] 새로 설치한 환경에서 `python -m pytest -q`를 실행하고 실제 결과를 저장합니다.
- [ ] 배포 주소의 `/api/health`에 접속하여 HTTP 상태 코드와 응답 본문을 기록합니다(비밀정보 제외).
- [ ] 배포 전 올바른 PostgreSQL 브랜치에 데이터베이스 마이그레이션이 적용되었는지 확인합니다.
- [ ] 운영 데이터와 분리된 테스트 계정으로 회원가입·로그인·로그아웃, 동의, 권한 경계, 비밀번호 재설정을 확인합니다.
- [ ] 평가 이어하기, 객관식 채점, AI 제공업체가 설정된 상태의 서술형 채점, 제공업체가 없을 때의 대체 동작을 확인합니다.
- [ ] 계획 초안·검토·승인, 과제 제출·완료, 학습시간 기록, 활동 기록 최신순 표시를 확인합니다. 생성 시간이 동일한 경우도 검사합니다.
- [ ] AI Coach가 실제 자료를 출처로 인용하는지 확인하고 읽기 전용 도구 권한을 검증합니다.
- [ ] 미리보기와 운영 데이터베이스를 분리하고 비밀정보나 `.env` 파일이 Git에 올라가지 않았는지 확인합니다.
- [ ] `main` 병합 이후 Vercel 운영 배포를 점검합니다. 미리보기의 Ready 상태만으로 운영 배포 성공을 확정할 수 없습니다.

## 향후 개발 단계 제안(아직 구현되지 않은 기능)

1. **정렬 방식 호환성 및 회귀 테스트:** SQLite 전용 정렬 방식에 의존하는 부분을 SQLite와 PostgreSQL에서 동일하게 동작하는 명시적인 전체 정렬 기준으로 바꿉니다. 생성 시간이 같고 삽입 순서가 다른 기록을 사용하는 테스트도 추가합니다.
2. **지속적 통합(CI):** 모든 Pull Request에서 의존성 패키지를 새로 설치하고 `pytest`, Python 컴파일, 필요한 코드 형식 검사를 실행합니다. 코드 전체를 무작정 자동 포맷팅하지는 않습니다.
3. **에이전트 판단 및 실행 순환 구조:** 학습자 질문을 받을 때마다 프로필, 과거 오답, 평가 및 활동 기록을 조회하고 다음 학습 행동을 결정합니다. 관련 연습문제를 제시하고 답을 평가하며 오답을 저장한 뒤 새 계획을 제안하도록 확장합니다. 영구적인 계획·진도 변경에는 사용자별 권한, 유효성 검증, 기록, 필요한 경우 명확한 사용자 확인을 적용해야 합니다.
4. **개인화 성능 평가:** 학습자 약점과의 관련성, 검색 출처의 정확성, 재계획 성공률, 오답 재학습률, 중복 연습문제 방지 등 측정 가능한 기준을 정합니다.
5. **운영 및 개인정보 보호:** 헬스 체크 결과, 장애 알림, 로그·보관 기간 정책, 백업 및 복원 훈련, 토큰·비밀정보 관리, 스테이징과 운영 환경 분리 등을 추가합니다.

## 기여 작업 흐름 및 공용 컴퓨터 사용 시 주의사항

```powershell
git switch main
git pull origin main
git switch -c fix/your-change
# 코드를 수정하고 테스트한 뒤:
git diff
git add backend/main.py
git commit -m "fix: describe the specific change"
git push -u origin fix/your-change
```

Pull Request를 생성하고 변경된 파일과 검사 결과를 검토한 다음 병합합니다. 공용 컴퓨터에서는 자동으로 채워진 알 수 없는 작성자 정보에 의존하지 말고 저장소 단위로 Git 사용자 정보를 설정하세요. 작업이 끝나면 연결된 서비스에서 로그아웃하세요. `.env`, 인증정보, 로컬 데이터베이스, `.venv`는 Git에 커밋하지 마세요.

