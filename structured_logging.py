"""
Structured JSON logging configuration for Case-Verify AI.

O-01 / Hardening Plan: Replaces ad-hoc ``logging.basicConfig`` calls with
a single, structured JSON formatter that writes machine-parseable log lines.
Import ``configure_logging()`` once at application startup (e.g. top of app.py).

Features
--------
* JSON-formatted log lines (``timestamp``, ``level``, ``logger``, ``message``,
  ``module``, ``funcName``, ``lineno``, plus any ``extra`` fields).
* Writes to **stderr** (container-friendly; captured by Docker / CloudWatch /
  Datadog without file mounts).
* Optional file handler (``LOG_FILE`` env var).
* Respects ``LOG_LEVEL`` env var (default: ``INFO``).
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Optional


class _JSONFormatter(logging.Formatter):
    """Emit each log record as a single JSON line."""

    _BUILTIN_ATTRS = frozenset(
        logging.LogRecord("", 0, "", 0, "", (), None).__dict__.keys()
    )

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
            "lineno": record.lineno,
        }

        # Append any *extra* fields the caller attached
        for key, value in record.__dict__.items():
            if key not in self._BUILTIN_ATTRS and key != "message":
                try:
                    json.dumps(value)  # ensure serialisable
                    log_entry[key] = value
                except (TypeError, ValueError):
                    log_entry[key] = repr(value)

        if record.exc_info and record.exc_info[1] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, ensure_ascii=False)


def configure_logging(
    level: Optional[str] = None,
    log_file: Optional[str] = None,
) -> None:
    """
    Configure the root logger with structured JSON output.

    Parameters
    ----------
    level : str | None
        Logging level name (``DEBUG``, ``INFO``, …).  Falls back to
        ``LOG_LEVEL`` env var, then ``INFO``.
    log_file : str | None
        Optional path for a file handler.  Falls back to ``LOG_FILE``
        env var.
    """
    resolved_level = (level or os.getenv("LOG_LEVEL", "INFO")).upper()

    formatter = _JSONFormatter()

    # Stderr handler (always present)
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setFormatter(formatter)

    handlers: list = [stderr_handler]

    # Optional file handler
    resolved_file = log_file or os.getenv("LOG_FILE", "")
    if resolved_file.strip():
        file_handler = logging.FileHandler(resolved_file.strip(), encoding="utf-8")
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    logging.basicConfig(
        level=getattr(logging, resolved_level, logging.INFO),
        handlers=handlers,
        force=True,  # Python 3.8+: override any prior basicConfig
    )

    # Quiet noisy third-party loggers
    for noisy in ("urllib3", "google", "httpcore", "httpx"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    root = logging.getLogger()
    root.info(
        "Structured logging initialised",
        extra={"log_level": resolved_level, "log_file": resolved_file or None},
    )
