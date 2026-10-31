# AI DevCoach

AI DevCoach MVP for account registration, learner profiling, skill assessment, and personalized learning plans.

## Live deployments

- Render: https://ai-devcoach.onrender.com
- Vercel: https://ai-devcoach.vercel.app

## Run locally

Requires Python 3.12 or newer.

```powershell
uv run --with-requirements requirements.txt uvicorn backend.main:app --reload
```

Open http://127.0.0.1:8000. Without `DATABASE_URL`, local development uses SQLite at `data/devcoach.db`.

To use Neon/PostgreSQL, set `DATABASE_URL` to the pooled connection string. Set `COOKIE_SECURE=true` when serving over HTTPS. The existing SQLite database is not copied automatically.

## Password reset

Password reset links are single-use and expire after 30 minutes. Configure `APP_BASE_URL`, `SMTP_HOST`, `SMTP_PORT`, and `SMTP_FROM`, plus `SMTP_USERNAME` and `SMTP_PASSWORD` when required by the provider. Set `SMTP_USE_SSL=true` for implicit TLS; otherwise SMTP STARTTLS is used. Keep SMTP credentials in the ignored `.env` file or deployment secret settings.

For local development only, set `PASSWORD_RESET_DEV_MODE=true` while `COOKIE_SECURE` is not `true`. The reset request screen then shows a local test link instead of sending email. Do not enable this mode in deployed environments; production reset links are sent only by email. After changing a password, all active sessions for that account are revoked.

## Deploy to Render

1. Create or choose a PostgreSQL database. Use its pooled connection string for `DATABASE_URL` and its direct connection string for `DATABASE_URL_UNPOOLED`.
2. Before the first deploy, set `DATABASE_URL_UNPOOLED` in your local, ignored `.env` file and apply the schema as described below.
3. Push the repository to GitHub, then in Render choose **New > Blueprint** and connect the repository. Render reads `render.yaml`, installs dependencies, and starts the web service.
4. Enter the two database URLs when prompted. The Blueprint sets `COOKIE_SECURE=true` and checks `/api/health`.
5. To grade written answers, add `OPENAI_API_KEY` under the service's **Environment** settings. `OPENAI_MODEL` is optional.
6. Open the Render service URL and verify that `/api/health` returns `{"status":"ok", ...}`.

The Blueprint uses Render's free web-service plan. Its local filesystem is not persistent, so production must use PostgreSQL rather than the SQLite fallback.

## Deploy to Vercel

1. Push the repository to GitHub and import it as a new Vercel project. Keep the project root at the repository root and use the **Other** framework preset if Vercel does not detect it automatically.
2. Add `DATABASE_URL` (pooled) and `DATABASE_URL_UNPOOLED` (direct) in **Project Settings > Environment Variables**. Also set `COOKIE_SECURE=true`. Add `OPENAI_API_KEY` to enable written-answer grading; `OPENAI_MODEL` is optional.
3. Apply the database migrations before deploying, then deploy from the Vercel dashboard or with the Vercel CLI. The FastAPI entrypoint is already configured as `backend.main:app` in `pyproject.toml`.
4. Open the deployment URL and verify `/api/health` returns `{"status":"ok", ...}`.

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

Run `npm run build` to compile-check the backend before deployment. `/api/health` verifies database connectivity.

## OpenAI written-answer grading

Objective questions are still scored by answer-key comparison. The two written answers are sent from the backend to OpenAI and graded against a structured rubric (root-cause understanding: 4 points, solution: 4 points, clarity: 2 points). The API key is never sent to the browser.

Set the API key in the same PowerShell terminal before starting the server:

```powershell
$env:OPENAI_API_KEY = "your-openai-api-key"
$env:OPENAI_MODEL = "gpt-4o-mini"
uv run --with-requirements requirements.txt uvicorn backend.main:app --reload
```

`OPENAI_MODEL` is optional and defaults to `gpt-4o-mini`. Without `OPENAI_API_KEY`, submitting any non-empty written response returns an explicit configuration error; there is no keyword-scoring fallback. OpenAI request or structured-response failures preserve submitted answers and allow the learner to retry.

## Included flows

- Email/password signup and login, single-use email password reset, required consent capture, server-side PBKDF2 password hashing, and HttpOnly session cookies.
- Learner profile creation and updates.
- A resumable 22-question assessment (20 objective and 2 written answers), objective scoring, OpenAI rubric-based written-answer scoring, and competency feedback.
- Personalized weekly plan drafts using the learner profile and latest assessment, time/structure validation, editable drafts, and explicit approval.

The assessment's written-answer scorer uses OpenAI; plan generation remains a deterministic rules-based MVP implementation. Email verification is not configured in this MVP. SMTP must be configured to deliver password-reset links outside local development mode.
