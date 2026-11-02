# AI DevCoach

AI DevCoach MVP for account registration, learner profiling, skill assessment, and personalized learning plans.

## Live deployments

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

## Admin dashboard

Set `ADMIN_EMAILS` to a comma-separated list of existing account email addresses to enable the Admin dashboard and its user-progress API. For example, set `ADMIN_EMAILS=coach@example.com,owner@example.com` in the local environment or deployment secrets. Only those signed-in accounts can access `/api/admin/overview`; changing the list takes effect on the next request. The dashboard shows account and task-progress summaries without exposing learner notes.

## Deploy to Vercel

1. Push the repository to GitHub, then import it as a new Vercel project. Set the project root to the repository root and use the **FastAPI** framework preset. `vercel.json` also declares the `fastapi` framework.
2. In **Project Settings > Environment Variables**, set `DATABASE_URL` to the pooled PostgreSQL connection string, `DATABASE_URL_UNPOOLED` to the direct connection string, and `COOKIE_SECURE` to `true`. Add `OPENAI_API_KEY` to enable written-answer grading; `OPENAI_MODEL` is optional.
3. To enable production password-reset emails, also set `APP_BASE_URL` to the deployed site URL and configure `SMTP_HOST`, `SMTP_PORT`, and `SMTP_FROM`. Add `SMTP_USERNAME` and `SMTP_PASSWORD` if required by your mail provider; set `SMTP_USE_SSL=true` when the provider requires implicit TLS.
4. Before the first deployment, set `DATABASE_URL_UNPOOLED` in your local, ignored `.env` file and apply the database migrations using the commands in [Database migrations before deployment](#database-migrations-before-deployment).
5. Deploy from the Vercel dashboard or with the Vercel CLI. With GitHub connected, pushes to the configured branch trigger deployments automatically. The FastAPI entrypoint is configured as `backend.main:app` in `pyproject.toml`.
6. Open the deployment URL and verify `/api/health` returns `{"status":"ok", ...}`.

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
