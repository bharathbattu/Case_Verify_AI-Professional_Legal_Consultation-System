"""
Graceful shutdown handlers for Case-Verify AI.

Op-04 / Hardening Plan: Registers ``atexit`` and signal handlers to ensure
clean resource teardown (database connections, temp files, active sessions)
when the process is stopped by Docker, systemd, or Ctrl-C.

Usage::

    from shutdown import register_shutdown_hooks
    register_shutdown_hooks()   # call once at app startup
"""

import atexit
import logging
import signal
import sys
from typing import Optional

logger = logging.getLogger(__name__)

_shutdown_registered = False


def _cleanup() -> None:
    """
    Central cleanup routine invoked on exit.

    Steps:
      1. Dispose SQLAlchemy engine (closes all pooled DB connections).
      2. Flush logging handlers.
    """
    logger.info("Shutdown: cleaning up resources…")

    # 1. Close database engine
    try:
        from database.connection import engine
        engine.dispose()
        logger.info("Shutdown: database engine disposed.")
    except Exception as exc:
        logger.warning("Shutdown: failed to dispose DB engine: %s", exc)

    # 2. Flush log handlers
    for handler in logging.root.handlers:
        try:
            handler.flush()
        except Exception:
            pass

    logger.info("Shutdown: cleanup complete.")


def _signal_handler(signum: int, frame: Optional[object]) -> None:
    """Handle SIGTERM / SIGINT for graceful container stop."""
    sig_name = signal.Signals(signum).name if hasattr(signal, "Signals") else str(signum)
    logger.info("Received signal %s — initiating graceful shutdown.", sig_name)
    _cleanup()
    sys.exit(0)


def register_shutdown_hooks() -> None:
    """
    Register atexit and signal handlers.  Safe to call multiple times
    (idempotent).
    """
    global _shutdown_registered
    if _shutdown_registered:
        return
    _shutdown_registered = True

    atexit.register(_cleanup)

    # SIGTERM is what Docker sends on `docker stop`
    try:
        signal.signal(signal.SIGTERM, _signal_handler)
    except (OSError, ValueError):
        # ValueError on non-main thread; OSError on unsupported platform
        pass

    # SIGINT (Ctrl-C) — default handler already calls atexit, but we
    # register anyway for explicit logging.
    try:
        signal.signal(signal.SIGINT, _signal_handler)
    except (OSError, ValueError):
        pass

    logger.info("Shutdown hooks registered (atexit + SIGTERM/SIGINT).")
