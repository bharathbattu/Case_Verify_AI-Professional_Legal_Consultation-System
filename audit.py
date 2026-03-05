"""
Audit trail helper for Case-Verify AI.

O-04 / Hardening Plan: Writes structured records to the ``audit_logs`` table
(see ``database.models.AuditLog``) for key user actions: login, logout,
case analysis, export, and admin operations.

Usage::

    from audit import log_action
    log_action(user_id=42, action="login", resource_type="session")
    log_action(user_id=42, action="analyse_case", resource_type="case",
               resource_id="CVA-20260305-123456", details={"case_type": "Civil"})
"""

import logging
from typing import Any, Dict, Optional

from database.connection import SessionLocal
from database.models import AuditLog

logger = logging.getLogger(__name__)


def log_action(
    *,
    user_id: Optional[int] = None,
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
) -> None:
    """
    Persist an audit log entry to the database.

    All arguments are keyword-only to avoid positional mistakes.
    Failures are logged but never propagate — audit logging must not
    crash the main application flow.
    """
    db = SessionLocal()
    try:
        entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id is not None else None,
            details=details,
            ip_address=ip_address,
        )
        db.add(entry)
        db.commit()
        logger.debug(
            "Audit: user=%s action=%s resource=%s/%s",
            user_id, action, resource_type, resource_id,
        )
    except Exception as exc:
        db.rollback()
        logger.warning("Failed to write audit log: %s", exc)
    finally:
        db.close()
