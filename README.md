# AI DevCoach

AI DevCoach MVP for account registration, learner profiling, skill assessment, and personalized learning plans.

## Run locally

Requires Python 3.12 or newer.

```powershell
uv run --with-requirements requirements.txt uvicorn backend.main:app --reload
```

Open http://127.0.0.1:8000. Without `DATABASE_URL`, local development uses SQLite at `data/devcoach.db`.

To use Neon/PostgreSQL, set `DATABASE_URL` to the pooled connection string. Set `COOKIE_SECURE=true` when serving over HTTPS. The existing SQLite database is not copied automatically.

## Validate changes

Install Python 3.12 or newer and [uv](https://docs.astral.sh/uv/). From the project directory, run the tests and compile-check the backend with:

```powershell
uv run --python 3.12 --with-requirements requirements.txt python -m unittest discover -s tests
uv run --python 3.12 --with-requirements requirements.txt python -m compileall -q backend
```

These commands do not require an activated `.venv` or Node.js/npm. `uv` can install Python 3.12 if it is not already available. GitHub Actions runs the same checks on pushes and pull requests.

## Neon and PostgreSQL

Install dependencies and apply schema migrations with the direct (unpooled) URL:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m alembic upgrade head
```

`DATABASE_URL` is used by the app for pooled runtime queries. Alembic prefers `DATABASE_URL_UNPOOLED` for migrations. Both values are loaded from `.env` locally; the environment file is ignored by Git.

The Vercel entrypoint is `backend.main:app`, configured in `pyproject.toml`. Add these variables to the Vercel project's Production and Preview environments before deployment:

- `DATABASE_URL`
- `DATABASE_URL_UNPOOLED`
- `OPENAI_API_KEY` (required for non-empty written-answer grading)
- `OPENAI_MODEL` (optional; defaults to `gpt-4o-mini`)
- `COOKIE_SECURE=true`

Run the compile-check from [Validate changes](#validate-changes) before deployment. Apply Alembic migrations explicitly before serving traffic; the app does not modify the production schema at startup. `/api/health` verifies database connectivity.

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

- Email/password signup and login, required consent capture, server-side PBKDF2 password hashing, and HttpOnly session cookies.
- Learner profile creation and updates.
- A resumable 22-question assessment (20 objective and 2 written answers), objective scoring, OpenAI rubric-based written-answer scoring, and competency feedback.
- Personalized weekly plan drafts using the learner profile and latest assessment, time/structure validation, editable drafts, and explicit approval.

The assessment's written-answer scorer uses OpenAI; plan generation remains a deterministic rules-based MVP implementation. Email verification and SMTP delivery are not configured in this MVP.

## Upload to GitHub

If the GitHub repository is empty, initialize this folder and push the `main` branch:

```powershell
git init
git branch -M main
git remote add origin https://github.com/bigpark61/AI_DevCoach.git
git add .
git status --short
git commit -m "Initial upload"
git push -u origin main
```

Before committing, confirm that `.env`, `.venv`, and `data/devcoach.db` are not listed by `git status`. They are excluded by `.gitignore`. If the GitHub repository already contains commits, do not force-push; first fetch and integrate its existing history.
