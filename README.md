# Quiniela

A multi-tournament football prediction pool ("quiniela") web application built with Django. Users predict match outcomes for a tournament's matchdays, and the app automatically tracks scores and ranks participants.

**Live demo:** [quiniela.lukifix.mx](https://quiniela.lukifix.mx) — the whole site requires an account to view, so use these demo credentials:

- **Username:** `Demo`
- **Password:** `Demo`

Logging in takes you to the currently active tournament (a live, in-progress one). To see a completed tournament with final standings, go to [quiniela.lukifix.mx/mundial-2026/](https://quiniela.lukifix.mx/mundial-2026/) after logging in.

## Features

- **Multi-tournament support** — any number of tournaments can run at once, each with its own matchdays and matches (originally built for Liga MX, generalized to support any competition, e.g. World Cup).
- **Two payment models per tournament** — a single one-time entry fee, or a per-matchday fee.
- **Prediction submission** — users pick outcomes (home win / draw / away win) for each match in the current matchday.
- **Automatic scoring and ranking** — points are calculated from correct predictions, with tie handling for 1st/2nd/3rd place.
- **PDF export** — matchday results and standings can be exported to PDF for participants who don't check the site directly.
- **Read-only REST API** (Django REST Framework) — matches, a user's own predictions, and the ranking table are exposed as JSON endpoints for programmatic access.
- **Account management** — registration, login, logout, and password recovery by email (via [Resend](https://resend.com)).
- **Admin tooling** — payment confirmation, bulk email notifications, and data import from Excel via custom management commands.

## Tech stack

- **Backend:** Django 6.0, Django REST Framework 3.17
- **Database:** PostgreSQL (via `psycopg2` and `dj-database-url`)
- **PDF generation:** ReportLab
- **Email:** Resend
- **Static files:** WhiteNoise
- **Testing:** pytest / pytest-django
- **Deployment:** Railway (Gunicorn + Postgres)

See `requirements.txt` for exact pinned versions.

## API

Three read-only endpoints, all scoped to a tournament by its slug:

| Endpoint | Auth required | Description |
|---|---|---|
| `GET /<torneo_slug>/api/jornada/<numero>/partidos/` | No | Matches and results for a given matchday |
| `GET /<torneo_slug>/api/jornada/<numero>/pronosticos/` | Yes (session) | The logged-in user's own predictions for that matchday |
| `GET /<torneo_slug>/api/ranking/` | Yes (session) | The tournament's current standings |

Authentication reuses the site's normal session-based login — no separate API tokens.

## Getting started locally

### Requirements

- Python 3.13
- A PostgreSQL database, **or** SQLite for quick local development (see below)

### Setup

```bash
git clone https://github.com/Darkial11/quiniela.git
cd quiniela
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

### Environment variables

The app is configured entirely through environment variables (no `.env` file is loaded automatically):

| Variable | Required | Notes |
|---|---|---|
| `SECRET_KEY` | Recommended | Falls back to an insecure default if unset — always set this explicitly outside of quick local testing |
| `DATABASE_URL` | One of these two | A full database URL, e.g. `postgres://...` (used in production) or `sqlite:///db.sqlite3` for quick local development |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | | Used instead of `DATABASE_URL` to connect to a local/remote PostgreSQL instance directly |
| `DEBUG` | No | Set to `True` for local development. Enables `localhost`/`127.0.0.1` in `ALLOWED_HOSTS` and disables the HTTPS-only cookie/redirect settings so the dev server works over plain `http://` |
| `RESEND_API_KEY` | For email features | Needed for password recovery and admin notification emails |

For local development without a Postgres instance:

```bash
# PowerShell
$env:DATABASE_URL="sqlite:///db.sqlite3"
$env:SECRET_KEY="local-dev-key"
$env:DEBUG="True"

# bash
export DATABASE_URL="sqlite:///db.sqlite3"
export SECRET_KEY="local-dev-key"
export DEBUG="True"
```

Then:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

The admin panel is at `/luki-panel/` (not the Django default `/admin/`).

## Running tests

```bash
pytest -v
```

Tests use the same database configuration as the app (via `DATABASE_URL`), so point it at SQLite for a fast, isolated test run — Django creates a separate test database automatically and never touches real data.

## Deployment

Deployed on [Railway](https://railway.app). The `Procfile` defines the release step (applies migrations) and the web process (Gunicorn). Database migrations are generated locally and committed to the repository — they are **not** generated automatically during deployment.
