# SCORECARD.md - Production Readiness Audit

**Project:** Case Verify AI - Professional Legal Consultation System  
**Audit Date:** 2026-03-05  
**Auditor:** Production Sentinel (claude-opus-4.6)  
**Overall Grade:** 1.5 / 5.0 - NOT PRODUCTION READY

---

## Executive Summary

This application is a **well-conceived legal consultation tool** with a solid domain model (60+ Indian case types, court hierarchy, limitation periods). However, it has **critical security vulnerabilities**, **broken authentication**, **minimal test coverage**, **no observability infrastructure**, and **significant code quality issues** that make it unsuitable for production deployment in its current state.

**The system requires significant hardening before any production use, especially given that it handles sensitive legal case data.**

---

## Scorecard (0-5 Scale)

| # | Pillar | Score | Grade | Summary |
|---|---|---|---|---|
| 1 | **Security** | 0.5/5 | F | Hardcoded API keys, plaintext passwords, broken auth, no CSRF/rate limiting |
| 2 | **Reliability** | 1.5/5 | D | Dead code, bare excepts, type errors, missing method implementations |
| 3 | **Observability** | 1.0/5 | D- | Basic logging exists but no structured logging, no metrics, no monitoring |
| 4 | **Performance** | 2.0/5 | C- | Caching exists but unbounded; no timeouts on API calls; no connection pooling strategy |
| 5 | **Testing** | 0.5/5 | F | 6 tests total, no coverage for 90%+ of codebase, no integration tests |
| 6 | **Operability** | 1.0/5 | D- | No health checks, no Docker, no CI/CD, fragile startup scripts |

**Weighted Average: 1.1 / 5.0**

---

## Pillar 1: Security (0.5/5) - CRITICAL

### S-01: Hardcoded Live API Key [P0-CRITICAL]
- **Evidence:** `start_case_verify.ps1:10` and `start_case_verify.bat:11` contain `AIzaSyDDFsLnVJvV5O6hJS1hnnWz3MwmAF8sdWM`
- **Impact:** Anyone with repo access has your Google Gemini API key. Can be used for unauthorized API calls billed to your account.
- **Verification:** `grep "AIza" start_case_verify.ps1 start_case_verify.bat` confirmed.
- **Fix:** Revoke key immediately. Use `.env` file loaded via `python-dotenv`. Add `*.ps1`/`*.bat` to `.gitignore` or remove keys.

### S-02: Plaintext Password Storage [P0-CRITICAL]
- **Evidence:** `auth/simple_auth.py:12-15` stores `{"demo": "demo123", "admin": "admin123"}` in plaintext.
- **Impact:** Any code path that falls through to `simple_auth.py` (which is ALL paths since `authenticator.py` is empty) has zero password security.
- **Verification:** `read auth/simple_auth.py` lines 12-15, `read auth/authenticator.py` = 0 lines.
- **Fix:** Implement `authenticator.py` with bcrypt hashing. Remove `simple_auth.py`.

### S-03: Hardcoded Admin Credentials in Database Init [P1-HIGH]
- **Evidence:** `init_database.py:34` creates admin with password `admin123`.
- **Verification:** `grep "admin123" init_database.py` confirmed.
- **Fix:** Require admin password via environment variable or interactive setup.

### S-04: Cookie Secret Committed to Repo [P1-HIGH]
- **Evidence:** `config/auth_config.yaml:3` contains `key: case_verify_secret_key_2024`
- **Impact:** Session forgery possible if attacker knows the cookie signing key.
- **Fix:** Move to environment variable. Rotate the key.

### S-05: Bcrypt Hash Committed to Repo [P2-MEDIUM]
- **Evidence:** `config/auth_config.yaml:10` contains `password: $2b$12$CrFb...`
- **Impact:** Offline brute-force attack vector.
- **Fix:** Move auth config to environment or exclude from version control.

### S-06: No CSRF Protection [P2-MEDIUM]
- **Evidence:** `grep "(csrf|CORS|cors|xss|sanitiz|rate_limit)" *.py` returned 0 results.
- **Impact:** Streamlit has some built-in CSRF mitigation, but no explicit protection exists.
- **Fix:** Add Streamlit CSRF header validation; implement rate limiting on login.

### S-07: `unsafe_allow_html=True` XSS Risk [P2-MEDIUM]
- **Evidence:** 17 occurrences across `app.py`, `document_processor.py`, `case_history.py`.
- **Impact:** If user-controlled input flows into HTML templates (especially `error_details` in app.py:783), XSS is possible.
- **Fix:** Sanitize all user inputs before HTML rendering. Use `html.escape()` for dynamic content.

### S-08: No Dependency Vulnerability Scanning [P2-MEDIUM]
- **Evidence:** No `safety`, `pip-audit`, or `snyk` configuration found. No `npm audit` equivalent run.
- **Fix:** Add `pip-audit` to CI pipeline. Run `safety check` regularly.

### S-09: `user_id = hash(username)` Predictable IDs [P2-MEDIUM]
- **Evidence:** `auth/simple_auth.py:24` uses Python's `hash()` for user IDs.
- **Impact:** `hash()` output is not stable across Python versions and not cryptographically secure.
- **Fix:** Use UUIDs for user identifiers.

---

## Pillar 2: Reliability (1.5/5)

### R-01: Empty `authenticator.py` - Core Feature Missing [P0-CRITICAL]
- **Evidence:** `auth/authenticator.py` = 0 bytes, 0 lines.
- **Impact:** The entire auth chain falls through to `simple_auth.py` (plaintext), making the session_manager, user_manager, and database auth models effectively unused in practice.
- **Verification:** `read auth/authenticator.py` = empty; `read auth/__init__.py` shows triple-fallback that always lands on simple_auth.
- **Fix:** Implement `authenticator.py` using `user_manager.py` + `session_manager.py`.

### R-02: ~135 Lines of Dead/Unreachable Code [P1-HIGH]
- **Evidence:** `app.py:480-616` contains a second `format_analysis_result` implementation after `return` on line 479.
- **Impact:** Wasted maintenance surface. Developer confusion.
- **Verification:** `read app.py` lines 470-500 shows `return formatted_result` then immediately unreachable code.
- **Fix:** Delete lines 480-616.

### R-03: Bare `except:` Clauses (Swallowed Errors) [P1-HIGH]
- **Evidence:** 4 bare `except:` clauses found:
  - `excel_exporter.py:131,211,306` — silently swallow all exceptions including `KeyboardInterrupt`
  - `agent.py:174` — date parsing silently fails
- **Verification:** `grep "except\s*:" *.py` confirmed.
- **Fix:** Use specific exception types. At minimum `except Exception:`.

### R-04: LSP Type Errors (14+ Issues) [P1-HIGH]
- **Evidence from LSP diagnostics:**
  - `app.py:112` — `.render()` method doesn't exist on `UserDashboard`
  - `app.py:218` — `.render()` method doesn't exist on `CaseHistory`
  - `app.py:227` — `.render()` method doesn't exist on `ExportInterface`
  - `agent.py:253,107` — `None` passed where `str` required
  - `agent.py:477` — `generate_content` called on potentially `None` model
  - `session_manager.py:15` — `is_authenticated` attribute doesn't exist
  - `session_manager.py:57` — returns `None` where `str` required
- **Impact:** Runtime `AttributeError` crashes when these code paths execute.
- **Fix:** Implement missing `.render()` methods or rename to actual method names. Add None guards.

### R-05: Missing Error Recovery on JSON Rule Loading [P2-MEDIUM]
- **Evidence:** `agent.py:41-54` loads JSON at module import time with no error handling.
- **Impact:** If any rule file is missing or malformed, the entire application fails to start.
- **Fix:** Add try/except with graceful degradation for each JSON file.

---

## Pillar 3: Observability (1.0/5)

### O-01: No Structured Logging [P2-MEDIUM]
- **Evidence:** 41 `logging.*` calls found, but all use basic `logging.basicConfig()` with format strings.
- **Impact:** Cannot parse logs programmatically. No correlation IDs for request tracing.
- **Fix:** Use `python-json-logger` or `structlog` for JSON-formatted logs.

### O-02: No Metrics/Monitoring [P1-HIGH]
- **Evidence:** `grep "(metrics|prometheus|statsd|datadog|newrelic)" *.py` = 0 results.
- **Impact:** No visibility into: request rates, error rates, latency, API quota usage, cache hit rates.
- **Fix:** Add Prometheus client or equivalent. Track Gemini API usage, response times, cache hit/miss ratio.

### O-03: No Health Check Endpoint [P1-HIGH]
- **Evidence:** `grep "(healthcheck|health_check|/health|/ready)" *.py` = 0 results.
- **Impact:** No way for orchestrators (K8s, Docker, load balancers) to verify application health.
- **Fix:** Add `/health` endpoint checking DB connectivity and Gemini API reachability.

### O-04: No Audit Trail for Analysis Results [P2-MEDIUM]
- **Evidence:** `AuditLog` model exists in `database/models.py` but no code writes to it.
- **Impact:** No forensic trail of who analyzed what and when.
- **Fix:** Write audit logs on login, analysis, export, and admin actions.

---

## Pillar 4: Performance (2.0/5)

### P-01: Unbounded In-Memory Cache [P1-HIGH]
- **Evidence:** `agent.py` uses `_response_cache = {}` (global dict) with no TTL, no max size, no eviction.
- **Impact:** Memory leak — cache grows indefinitely per unique query. In a long-running Streamlit server, this will eventually OOM.
- **Fix:** Use `functools.lru_cache`, `cachetools.TTLCache`, or Redis.

### P-02: MD5 for Cache Keys [P3-LOW]
- **Evidence:** `agent.py:110` uses `hashlib.md5()`.
- **Impact:** Hash collisions are theoretically possible (low practical risk for caching).
- **Fix:** Use `hashlib.sha256()` instead.

### P-03: No Timeout on Gemini API Calls [P1-HIGH]
- **Evidence:** `agent.py` calls `model.generate_content()` with no timeout parameter. `grep "timeout" *.py` found only session timeout, not API call timeout.
- **Impact:** If Gemini API hangs, the entire Streamlit thread blocks indefinitely.
- **Fix:** Add `timeout=30` parameter or use `asyncio.wait_for`.

### P-04: Database Session Per Method (No Connection Pooling Strategy) [P2-MEDIUM]
- **Evidence:** `session_manager.py` creates a new `SessionLocal()` in every method (lines 63, 75, etc.), closes in finally.
- **Impact:** High connection churn. SQLite with `StaticPool` mitigates this, but pattern doesn't scale to PostgreSQL.
- **Fix:** Use dependency injection or context manager pattern consistently.

### P-05: No Pagination on Case History Queries [P2-MEDIUM]
- **Evidence:** `case_history.py` loads all cases for a user without LIMIT/OFFSET.
- **Impact:** Performance degrades linearly with case count.
- **Fix:** Implement pagination with configurable page size.

---

## Pillar 5: Testing (0.5/5)

### T-01: Only 6 Tests for ~5,000+ Lines of Code [P0-CRITICAL]
- **Evidence:** `test_agent.py` has 5 tests, `test_performance.py` has 1 test. Total = 6 tests.
- **Approximate Coverage:** <5% — only `agent.analyse()`, `validate_pin_code()`, and `validate_inputs()` are tested.
- **NOT TESTED:**
  - Authentication flow (0 tests)
  - Session management (0 tests)
  - User management (0 tests)
  - Database operations (0 tests)
  - Document processing (0 tests)
  - PDF/Excel/Email export (0 tests)
  - Enhanced analytics (0 tests)
  - UI components (0 tests)
  - Error handling paths (0 tests)
  - Edge cases (date parsing, empty inputs, large files)
- **Fix:** Target 70%+ coverage. Add unit tests for each module. Add integration tests for auth and analysis flows.

### T-02: No Integration Tests [P1-HIGH]
- **Evidence:** No test files test multi-module flows (e.g., login -> analyze -> save -> export).
- **Fix:** Add end-to-end tests using Streamlit testing framework or Selenium.

### T-03: No CI/CD Pipeline [P1-HIGH]
- **Evidence:** No `.github/workflows/`, `Jenkinsfile`, `gitlab-ci.yml`, or equivalent found.
- **Fix:** Add GitHub Actions workflow for lint, test, security scan on every PR.

### T-04: Test Sets Environment Variable Globally [P3-LOW]
- **Evidence:** `test_agent.py:11` sets `os.environ["GEMINI_API_KEY"] = "test_api_key"` at module level.
- **Impact:** Contaminates environment for other tests.
- **Fix:** Use `monkeypatch` fixture or `unittest.mock.patch.dict`.

---

## Pillar 6: Operability (1.0/5)

### Op-01: No Docker/Container Support [P1-HIGH]
- **Evidence:** No `Dockerfile`, `docker-compose.yml`, or container configuration found.
- **Impact:** No reproducible deployment. Environment drift between dev and production.
- **Fix:** Create multi-stage Dockerfile with health check.

### Op-02: No Environment Variable Validation [P1-HIGH]
- **Evidence:** `agent.py:12-16` checks for `GEMINI_API_KEY` but logs a warning and continues. No other env vars are validated at startup.
- **Impact:** Silent misconfiguration. App may start but partially function.
- **Fix:** Add startup validation that checks all required env vars and fails fast with clear messages.

### Op-03: Startup Scripts Hardcode Configuration [P1-HIGH]
- **Evidence:** `start_case_verify.ps1` and `start_case_verify.bat` hardcode the API key, set `STREAMLIT_BROWSER_GATHER_USAGE_STATS=false`.
- **Impact:** Configuration is baked into scripts rather than externalized.
- **Fix:** Use `.env` files loaded by `python-dotenv`. Remove hardcoded values from scripts.

### Op-04: No Graceful Shutdown Handling [P2-MEDIUM]
- **Evidence:** No signal handlers (`SIGTERM`, `SIGINT`) found. No cleanup of database connections on shutdown.
- **Impact:** Abrupt shutdowns may leave database locks or incomplete transactions.
- **Fix:** Register atexit handlers for DB cleanup.

### Op-05: No Backup Strategy for SQLite [P2-MEDIUM]
- **Evidence:** SQLite file (`case_verify.db`) has no backup configuration.
- **Impact:** Data loss on disk failure.
- **Fix:** Implement periodic SQLite backup or migrate to PostgreSQL for production.

### Op-06: Dependencies Not Pinned [P2-MEDIUM]
- **Evidence:** `requirements.txt` uses `>=` for all 17+ packages with no upper bounds.
- **Impact:** `pip install` may pull incompatible future versions, breaking the app.
- **Fix:** Generate `requirements.lock` or use exact pins (`==`) with `pip freeze`.

---

## Critical Path to Production

### Must Fix Before Any Deployment (P0):
1. Revoke and rotate the hardcoded API key
2. Implement proper authentication (replace empty `authenticator.py`)
3. Remove plaintext password storage
4. Add comprehensive test suite (target 70%+ coverage)
5. Delete dead code (app.py lines 480-616)

### Must Fix Before Production (P1):
6. Add Docker containerization
7. Implement health checks
8. Add API call timeouts
9. Bound the in-memory cache
10. Add CI/CD pipeline
11. Externalize all configuration
12. Add monitoring/metrics

### Should Fix (P2):
13. Structured logging
14. Audit trail implementation
15. CSRF protection
16. XSS input sanitization
17. Dependency pinning
18. Database connection management
19. Pagination

---

*End of Scorecard - Generated by Production Sentinel Audit*
