# REPO_MAP.md - Case Verify AI Repository Map

**Audit Date:** 2026-03-05  
**Auditor:** Production Sentinel (claude-opus-4.6)

---

## 1. Tech Stack

| Layer | Technology | Version Constraint |
|---|---|---|
| Frontend/UI | Streamlit | >=1.28.0 |
| AI Backend | Google Gemini 1.5 Flash | google-generativeai >=0.7.0 |
| Database | SQLite + SQLAlchemy ORM | SQLAlchemy >=2.0.0 |
| Auth | Custom (bcrypt/passlib) + plaintext fallback | bcrypt >=4.0.0 |
| Document Processing | PyPDF2, PyMuPDF, python-docx, mammoth, pytesseract | Various |
| PDF Export | ReportLab | >=4.0.0 |
| Excel Export | openpyxl | >=3.1.0 |
| Email | SMTP via smtplib | stdlib |
| Testing | pytest | >=7.4.0 |
| Language | Python 3.x | Not pinned |

---

## 2. Data Flow Diagram

```
USER (Browser)
    |
    v
[Streamlit UI - app.py]
    |
    +-- Authentication Flow:
    |       app.py --> auth/__init__.py --> Attempts:
    |         1. Full auth (authenticator.py) [EMPTY FILE - always fails]
    |         2. Simplified auth (simple_auth.py) [PLAINTEXT passwords]
    |         3. Minimal fallback (inline in __init__.py)
    |
    +-- Analysis Flow:
    |       app.py --> agent.analyse()
    |         |
    |         +-- Input validation (validate_inputs, validate_pin_code)
    |         +-- Cache check (MD5 hash key -> in-memory dict)
    |         +-- AI Path: Google Gemini API --> JSON parse --> result
    |         +-- Fallback Path: Rule-based analysis from rules/*.json
    |         +-- Date extraction from facts text (regex)
    |         +-- Limitation period calculation
    |         +-- Court hierarchy lookup (rules/court_hierarchy.json)
    |         +-- Enhanced analytics (enhanced_analytics.py)
    |         +-- Result cached, returned as dict
    |
    +-- Database Path:
    |       app.py --> database/connection.py (SQLite via SQLAlchemy)
    |         |
    |         +-- Models: User, Case, Analysis, UserSession, AuditLog, SystemConfig
    |         +-- Session management: auth/session_manager.py
    |         +-- User CRUD: auth/user_manager.py
    |         +-- Case persistence: components/case_history.py
    |
    +-- Document Processing:
    |       app.py --> document_processor.py
    |         |
    |         +-- PDF: PyMuPDF -> PyPDF2 fallback
    |         +-- Word: mammoth -> python-docx fallback
    |         +-- Text: direct read with encoding fallback
    |         +-- Image: pytesseract OCR
    |         +-- Legal document generation (notices, petitions, affidavits)
    |
    +-- Export Path:
    |       components/export_interface.py
    |         |
    |         +-- exports/pdf_generator.py (ReportLab)
    |         +-- exports/excel_exporter.py (openpyxl)
    |         +-- exports/email_sender.py (SMTP)
    |
    +-- Dashboard/Analytics:
            components/user_dashboard.py
            components/case_history.py
            enhanced_analytics.py
```

---

## 3. File Inventory

### Core Application
| File | Lines | Purpose |
|---|---|---|
| `app.py` | 805 | Main Streamlit entry point; contains ~135 lines of dead code (481-616) |
| `agent.py` | 615 | AI analysis engine; rule-based fallback; caching |
| `document_processor.py` | 615 | File upload, OCR, legal document generation |
| `enhanced_analytics.py` | 459 | Cost estimation, timeline, alternative remedies |
| `init_database.py` | 77 | DB init with hardcoded admin credentials |

### Authentication (`auth/`)
| File | Lines | Purpose |
|---|---|---|
| `__init__.py` | 110 | Triple-fallback auth loader |
| `authenticator.py` | 0 | **EMPTY** - Full auth system never implemented |
| `simple_auth.py` | 55 | Plaintext password auth (demo fallback) |
| `session_manager.py` | 284 | Session CRUD, token-based sessions |
| `user_manager.py` | 262 | User CRUD with bcrypt hashing |

### Database (`database/`)
| File | Lines | Purpose |
|---|---|---|
| `__init__.py` | 8 | Package exports |
| `connection.py` | 52 | SQLAlchemy engine + SessionLocal factory |
| `models.py` | 160 | ORM models (6 tables) |

### Components (`components/`)
| File | Lines | Purpose |
|---|---|---|
| `case_history.py` | 416 | Case management UI |
| `user_dashboard.py` | 435 | Dashboard with analytics |
| `export_interface.py` | 536 | Export UI (PDF/Excel/Email/Bulk) |

### Exports (`exports/`)
| File | Lines | Purpose |
|---|---|---|
| `pdf_generator.py` | 469 | ReportLab PDF generation |
| `excel_exporter.py` | 483 | openpyxl Excel export |
| `email_sender.py` | 169 | SMTP email with attachments |

### Rules/Data (`rules/`)
| File | Purpose |
|---|---|
| `limitation.json` | 60+ case type limitation periods |
| `forum.json` | Court forum mappings per case type |
| `court_hierarchy.json` | Indian court hierarchy |
| `detailed_provisions.json` | Legal provisions database |
| `language_support.json` | Hindi/English translations |

### Tests
| File | Lines | Test Count | Coverage |
|---|---|---|---|
| `test_agent.py` | 110 | 5 tests | agent.py only (partial) |
| `test_performance.py` | 58 | 1 test | Performance benchmark |

### Configuration
| File | Purpose | Risk |
|---|---|---|
| `config/auth_config.yaml` | Auth settings | Contains bcrypt hash + cookie secret |
| `.env.example` | Environment template | Safe (placeholder values) |
| `requirements.txt` | Dependencies | No upper bounds |
| `pytest.ini` | Test config | Minimal |

### Startup Scripts (DANGEROUS)
| File | Risk |
|---|---|
| `start_case_verify.ps1` | **Hardcoded LIVE API key** |
| `start_case_verify.bat` | **Hardcoded LIVE API key** |

---

## 4. Database Schema (6 Tables)

```
User (id, username, email, hashed_password, full_name, organization, role, is_active, created_at, last_login)
Case (id, user_id FK->User, case_number, case_type, facts, relief_sought, pin_code, status, created_at, updated_at)
Analysis (id, case_id FK->Case, verdict, days_left, limitation_period, deadline, forum, court_info, applicable_sections, ai_response, tokens_used, analyzed_at)
UserSession (id, user_id FK->User, session_token, ip_address, user_agent, created_at, expires_at, is_active)
AuditLog (id, user_id FK->User, action, details, ip_address, timestamp)
SystemConfig (id, key, value, updated_at)
```

---

## 5. External Dependencies

- **Google Gemini API** - Core AI analysis (requires API key)
- **Tesseract OCR** - Image text extraction (requires system install)
- **SMTP Server** - Email export (requires credentials)
- **No CDN/external JS** - Self-contained Streamlit app
