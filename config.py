"""
Centralised application configuration with startup environment validation.

Op-02 / Hardening Plan: Validates all required (and optional) environment
variables at import time so the app fails fast with a clear message instead
of crashing mid-request.
"""
import os
import sys
import logging
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def _require(var: str, *, hint: str = "") -> str:
    """Return env var value or exit with a clear error."""
    value = os.getenv(var, "").strip()
    if not value:
        msg = f"FATAL: Required environment variable {var} is not set."
        if hint:
            msg += f"  Hint: {hint}"
        logger.critical(msg)
        print(msg, file=sys.stderr)
        raise SystemExit(1)
    return value


def _optional(var: str, default: str = "") -> str:
    return os.getenv(var, default).strip()


def _optional_int(var: str, default: int) -> int:
    raw = os.getenv(var, "")
    if raw.strip():
        try:
            return int(raw.strip())
        except ValueError:
            logger.warning("Invalid integer for %s=%r, using default %d", var, raw, default)
    return default


# ---------------------------------------------------------------------------
# Configuration dataclass
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AppConfig:
    """Immutable application configuration populated from environment."""

    # -- Required ---------------------------------------------------------
    gemini_api_key: str = field(repr=False)  # repr=False: never log secrets

    # -- Secrets (required in production, auto-generated in dev) ----------
    cookie_secret: str = field(repr=False)

    # -- Environment ------------------------------------------------------
    environment: str = "development"  # development | staging | production

    # -- Database ---------------------------------------------------------
    database_url: str = "sqlite:///./case_verify.db"

    # -- AI ---------------------------------------------------------------
    ai_model_name: str = "gemini-1.5-flash"
    ai_temperature: float = 0.2
    ai_max_tokens: int = 1024
    ai_timeout_seconds: int = 30

    # -- Session ----------------------------------------------------------
    session_timeout_hours: int = 24

    # -- Email (optional) -------------------------------------------------
    smtp_server: str = ""
    smtp_port: int = 587
    sender_email: str = ""
    sender_password: str = field(default="", repr=False)

    # -- Rate limiting ----------------------------------------------------
    max_login_attempts: int = 5
    login_lockout_minutes: int = 15

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        return self.environment.lower() == "development"

    @property
    def ai_enabled(self) -> bool:
        key = self.gemini_api_key
        return (
            bool(key)
            and key != "your_gemini_api_key_here"
            and key != "your_api_key_here"
            and len(key) > 20
            and not key.startswith("<ENTER_YOU")
        )


# ---------------------------------------------------------------------------
# Build config singleton
# ---------------------------------------------------------------------------

def _build_config() -> AppConfig:
    """Build and validate config from environment variables."""
    env = _optional("ENVIRONMENT", "development")

    # Gemini key is required (even if it's a placeholder in dev)
    gemini_key = _optional("GEMINI_API_KEY", "")
    if not gemini_key:
        logger.warning("GEMINI_API_KEY not set — AI features will be disabled.")
        gemini_key = ""

    # Cookie secret: required in production, auto-generated in dev
    cookie_secret = _optional("COOKIE_SECRET", "")
    if not cookie_secret:
        if env.lower() == "production":
            _require("COOKIE_SECRET", hint="Generate with: python -c \"import secrets; print(secrets.token_hex(32))\"")
        else:
            import secrets
            cookie_secret = secrets.token_hex(32)
            logger.info("Auto-generated COOKIE_SECRET for development.")

    config = AppConfig(
        gemini_api_key=gemini_key,
        cookie_secret=cookie_secret,
        environment=env,
        database_url=_optional("DATABASE_URL", "sqlite:///./case_verify.db"),
        ai_timeout_seconds=_optional_int("AI_TIMEOUT_SECONDS", 30),
        session_timeout_hours=_optional_int("SESSION_TIMEOUT_HOURS", 24),
        smtp_server=_optional("SMTP_SERVER"),
        smtp_port=_optional_int("SMTP_PORT", 587),
        sender_email=_optional("SENDER_EMAIL"),
        sender_password=_optional("SENDER_PASSWORD"),
        max_login_attempts=_optional_int("MAX_LOGIN_ATTEMPTS", 5),
        login_lockout_minutes=_optional_int("LOGIN_LOCKOUT_MINUTES", 15),
    )

    logger.info(
        "Configuration loaded: env=%s, ai_enabled=%s, db=%s",
        config.environment,
        config.ai_enabled,
        config.database_url.split("://")[0] + "://***"
    )
    return config


settings: AppConfig = _build_config()
