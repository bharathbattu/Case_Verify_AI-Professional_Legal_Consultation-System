"""
Health check and readiness probes for Case-Verify AI.

O-02 / O-03: Provides /healthz-style JSON endpoint consumed by Docker
HEALTHCHECK, Kubernetes probes, and monitoring dashboards.

Usage (standalone):
    python health.py            # prints JSON health status to stdout

Usage (imported):
    from health import check_health
    status = check_health()     # returns dict
"""
import json
import time
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Dict, Any

logger = logging.getLogger(__name__)

_start_time = time.monotonic()


def _check_database() -> Dict[str, Any]:
    """Verify database is reachable and tables exist."""
    try:
        from database.connection import SessionLocal
        db = SessionLocal()
        try:
            db.execute("SELECT 1")  # type: ignore[arg-type]
            return {"status": "ok"}
        finally:
            db.close()
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


def _check_rules_files() -> Dict[str, Any]:
    """Verify all required JSON rule files are present and parseable."""
    import json as _json
    rules_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rules")
    required = [
        "limitation.json",
        "forum.json",
        "court_hierarchy.json",
        "detailed_provisions.json",
        "language_support.json",
    ]
    missing = []
    corrupt = []
    for fname in required:
        fpath = os.path.join(rules_dir, fname)
        if not os.path.isfile(fpath):
            missing.append(fname)
            continue
        try:
            with open(fpath, encoding="utf-8") as f:
                _json.load(f)
        except (json.JSONDecodeError, OSError):
            corrupt.append(fname)

    if missing or corrupt:
        return {
            "status": "error",
            "missing": missing,
            "corrupt": corrupt,
        }
    return {"status": "ok"}


def _check_ai() -> Dict[str, Any]:
    """Report whether AI / Gemini is configured (does not make a live call)."""
    api_key = os.getenv("GEMINI_API_KEY", "")
    enabled = (
        bool(api_key)
        and api_key != "your_gemini_api_key_here"
        and api_key != "your_api_key_here"
        and len(api_key.strip()) > 20
        and not api_key.startswith("<ENTER_YOU")
    )
    return {"status": "ok" if enabled else "degraded", "ai_enabled": enabled}


def check_health() -> Dict[str, Any]:
    """
    Run all health probes and return an aggregate status dict.

    Returns dict with:
      - status: "healthy" | "degraded" | "unhealthy"
      - uptime_seconds: float
      - timestamp: ISO-8601
      - checks: {name: {status, ...}}
    """
    checks: Dict[str, Any] = {}
    checks["database"] = _check_database()
    checks["rules_files"] = _check_rules_files()
    checks["ai"] = _check_ai()

    # Aggregate
    statuses = [c.get("status", "unknown") for c in checks.values()]
    if any(s == "error" for s in statuses):
        overall = "unhealthy"
    elif any(s == "degraded" for s in statuses):
        overall = "degraded"
    else:
        overall = "healthy"

    return {
        "status": overall,
        "uptime_seconds": round(time.monotonic() - _start_time, 2),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
    }


# ---------------------------------------------------------------------------
# CLI entry-point (for Docker HEALTHCHECK)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    result = check_health()
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["status"] != "unhealthy" else 1)
