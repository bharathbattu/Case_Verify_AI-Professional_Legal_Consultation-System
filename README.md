# Case Verify AI

Case Verify AI is a Streamlit-based legal consultation assistant for Indian law workflows. It analyzes case facts, maps them to limitation periods and forums, and generates a structured professional report with legal reasoning, jurisdiction guidance, strategic recommendations, and risk factors.

The application supports both:
- AI mode (Google Gemini) when `GEMINI_API_KEY` is configured
- Offline fallback mode when no valid API key is present

## Features

- Professional legal consultation output in a 7-section format
- 60+ legal scenario mappings from `rules/limitation.json`
- Court hierarchy and forum guidance from local JSON rules
- Authentication system with session management and role support
- User dashboard, case history, and export workflows (PDF/Excel)
- Document upload and text extraction (PDF, DOCX, TXT, image OCR)
- Structured JSON logging, health checks, audit logging, and metrics hooks
- Docker support with healthcheck and hardened runtime settings

## Tech Stack

- Python 3.11+
- Streamlit
- SQLAlchemy + SQLite (`case_verify.db`)
- Google Gemini (`google-generativeai`) for AI analysis
- ReportLab / OpenPyXL / Pandas for export
- PyMuPDF / PyPDF2 / python-docx / pytesseract for document processing

## Quick Start (Local)

### 1. Create and activate virtual environment

PowerShell:

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Configure environment

Create `.env` (or copy from `.env.example`) and set values as needed.

Minimum useful values:

```env
ENVIRONMENT=development
GEMINI_API_KEY=
DATABASE_URL=sqlite:///./case_verify.db
```

Notes:
- If `GEMINI_API_KEY` is empty/placeholder, the app runs in offline mode.
- `COOKIE_SECRET` is auto-generated in development if not set.

### 4. Initialize database

```powershell
python init_database.py
```

This creates tables and an admin user.

### 5. Run the app

```powershell
streamlit run app.py --server.port 8520
```

Open `http://localhost:8520`.

## App Navigation

When full Phase 3.3 modules are available, UI exposes four tabs:

1. `Case Analysis`
2. `User Management`
3. `Case History`
4. `Export Reports`

If optional auth/component imports fail, the app falls back to basic case analysis mode.

## Core Analysis Flow

1. User provides facts, case type, relief sought, and PIN.
2. `agent.py` maps user relief text to a canonical key (`map_relief_to_key`).
3. Input is validated (`validate_inputs`).
4. AI call is attempted (if enabled) with legal prompt and JSON response format.
5. On AI unavailability/error, offline fallback analysis is generated.
6. Limitation period and deadline are computed using `rules/limitation.json`.
7. Forum and court metadata are resolved from `rules/forum.json` and `rules/court_hierarchy.json`.
8. Enhanced analytics are merged from `enhanced_analytics.py`.
9. Final report is formatted and rendered in Streamlit.

## Project Structure

```text
.
|- app.py
|- agent.py
|- config.py
|- init_database.py
|- health.py
|- metrics.py
|- structured_logging.py
|- shutdown.py
|- sanitize.py
|- audit.py
|- document_processor.py
|- enhanced_analytics.py
|- database/
|  |- connection.py
|  |- models.py
|- auth/
|  |- __init__.py
|  |- authenticator.py
|  |- session_manager.py
|  |- user_manager.py
|  |- simple_auth.py
|- components/
|  |- user_dashboard.py
|  |- case_history.py
|  |- export_interface.py
|- exports/
|  |- pdf_generator.py
|  |- excel_exporter.py
|  |- email_sender.py
|- rules/
|  |- limitation.json
|  |- forum.json
|  |- court_hierarchy.json
|  |- detailed_provisions.json
|  |- language_support.json
|- tests: test_*.py files at repo root
```

## Configuration

Main environment variables used by current code:

- `ENVIRONMENT` (`development`, `staging`, `production`)
- `GEMINI_API_KEY`
- `COOKIE_SECRET` (required in production)
- `DATABASE_URL` (default: `sqlite:///./case_verify.db`)
- `AI_TIMEOUT_SECONDS`
- `SESSION_TIMEOUT_HOURS`
- `SMTP_SERVER`, `SMTP_PORT`, `SENDER_EMAIL`, `SENDER_PASSWORD`
- `MAX_LOGIN_ATTEMPTS`, `LOGIN_LOCKOUT_MINUTES`
- `ADMIN_PASSWORD`, `ADMIN_EMAIL` (used by `init_database.py`)

## Authentication and Sessions

- Production auth uses bcrypt verification and DB-backed session tokens.
- Login rate limiting is applied per username (in-memory lockout logic).
- Session data is mirrored into Streamlit session state.
- Fallback auth modules exist for development resilience.

## Observability and Operations

- Structured logs via `structured_logging.py` (JSON format)
- Health check via `python health.py`
- Audit trail writes to `audit_logs` table via `audit.py`
- Prometheus metric hooks in `metrics.py` (no-op when client lib absent)
- Graceful shutdown handlers in `shutdown.py`

## Testing

Run all tests:

```powershell
pytest
```

Run a specific test file:

```powershell
pytest test_agent.py -v
```

Notes:
- `conftest.py` provides stubs for several heavy/optional dependencies to keep tests portable.
- `pytest.ini` configures discovery with `test_*.py`.

## Docker

The repository includes:

- `Dockerfile` (multi-stage build)
- `docker-compose.yml` (runtime config + healthcheck)

Basic compose run:

```powershell
docker compose up --build
```

App inside container listens on `8501` by default.

## Security Notes

- Never commit real API keys or production secrets.
- Keep `.env` private.
- Input and HTML rendering paths use sanitization helpers in `sanitize.py`.
- Use strong `ADMIN_PASSWORD` and rotate credentials after first boot.

## Legal Disclaimer

This software is an educational/legal workflow aid and does not replace qualified legal counsel. Always verify outputs and consult a licensed advocate for case-specific advice.
