# AI DevCoach

AI DevCoach MVP for account registration, learner profiling, skill assessment, and personalized learning plans.

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

`pytest` and Black are developer tools and may not be included in `requirements.txt`. With the virtual environment created above:

```powershell
.\.venv\Scripts\python.exe -m pip install pytest black
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m black --check --diff backend/main.py
```

Black `--check --diff` **inspects but does not modify** files. A result stating `would be reformatted` reports a style difference, not a failing application test. Avoid formatting the entire file as part of an unrelated one-line fix; use a dedicated formatting change after reviewing its diff.

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
