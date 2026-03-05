"""
Authentication system for Case-Verify AI
Provides secure bcrypt-based authentication with session management.

Fixes: S-02, R-01 — Replaces empty authenticator with production-grade auth.
       S-06      — Rate limiting on login (attempt counter + lockout).
"""
import logging
import time
import streamlit as st
from typing import Optional, Dict, Any
from datetime import datetime

from passlib.hash import bcrypt
from database.models import User
from database.connection import SessionLocal
from .session_manager import SessionManager
from .user_manager import UserManager, hash_password

logger = logging.getLogger(__name__)

# Lazy import metrics to avoid circular imports at module load
def _record_login_metric(success: bool) -> None:
    try:
        from metrics import inc_login
        inc_login(success=success)
    except Exception:
        pass


def _record_rate_limited_metric() -> None:
    try:
        from metrics import inc_rate_limited
        inc_rate_limited()
    except Exception:
        pass

# Lazy import audit to avoid circular dependency at module load
def _audit(*, user_id=None, action="", resource_type=None, resource_id=None, details=None):
    """Fire-and-forget audit log entry."""
    try:
        from audit import log_action
        log_action(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
        )
    except Exception:
        pass  # audit must never crash auth

# ---------------------------------------------------------------------------
# S-06: In-memory rate limiter (per-username)
# ---------------------------------------------------------------------------
# Key = username, Value = (fail_count, first_fail_epoch)
_login_attempts: Dict[str, tuple] = {}

# Defaults — overrideable via config.py / env vars at call-site
_DEFAULT_MAX_ATTEMPTS = 5
_DEFAULT_LOCKOUT_SECONDS = 15 * 60  # 15 minutes


def _check_rate_limit(
    username: str,
    max_attempts: int = _DEFAULT_MAX_ATTEMPTS,
    lockout_seconds: int = _DEFAULT_LOCKOUT_SECONDS,
) -> Optional[int]:
    """
    Return seconds remaining in lockout if rate-limited, else None.
    """
    record = _login_attempts.get(username)
    if record is None:
        return None
    fail_count, first_fail_ts = record
    elapsed = time.time() - first_fail_ts
    if elapsed > lockout_seconds:
        # Window expired — reset
        _login_attempts.pop(username, None)
        return None
    if fail_count >= max_attempts:
        remaining = int(lockout_seconds - elapsed)
        return max(remaining, 1)
    return None


def _record_failed_attempt(username: str) -> None:
    record = _login_attempts.get(username)
    now = time.time()
    if record is None:
        _login_attempts[username] = (1, now)
    else:
        fail_count, first_fail_ts = record
        _login_attempts[username] = (fail_count + 1, first_fail_ts)


def _clear_attempts(username: str) -> None:
    _login_attempts.pop(username, None)


class Authenticator:
    """
    Production-grade authenticator using bcrypt password hashing
    and database-backed session management.
    """

    def __init__(self):
        self.session_manager = SessionManager()

    def login(self, username: str, password: str) -> bool:
        """
        Authenticate user with username and password using bcrypt verification.
        
        Returns True on success, False on failure.
        Enforces S-06 rate limiting (lockout after repeated failures).
        """
        if not username or not password:
            return False

        # S-06: check rate limit before hitting the database
        remaining = _check_rate_limit(username)
        if remaining is not None:
            logger.warning(
                "Login blocked for '%s': rate-limited for %d more seconds",
                username, remaining,
            )
            _record_rate_limited_metric()
            return False

        db = SessionLocal()
        try:
            user = db.query(User).filter(
                User.username == username,
                User.is_active == True
            ).first()

            if not user:
                # Constant-time comparison to avoid timing attacks
                bcrypt.hash("dummy_password_for_timing")
                _record_failed_attempt(username)
                _record_login_metric(success=False)
                logger.warning(f"Login failed: user '{username}' not found")
                return False

            if not bcrypt.verify(password, user.hashed_password):
                _record_failed_attempt(username)
                _record_login_metric(success=False)
                logger.warning(f"Login failed: invalid password for user '{username}'")
                return False

            # Successful authentication — clear rate limiter & create session
            _clear_attempts(username)
            session_token = self.session_manager.create_session(user.id)
            if session_token is None:
                logger.error(f"Login succeeded but session creation failed for user '{username}'")
                return False

            # Update Streamlit session state
            st.session_state['authentication_status'] = True
            st.session_state['username'] = user.username
            st.session_state['name'] = user.full_name or user.username.title()
            st.session_state['user_id'] = user.id
            st.session_state['user_role'] = user.role
            st.session_state['current_user'] = user

            # Update last login timestamp
            user.last_login = datetime.utcnow()
            db.commit()

            logger.info(f"User '{username}' logged in successfully")
            _record_login_metric(success=True)
            _audit(user_id=user.id, action="login", resource_type="session")
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"Login error for user '{username}': {str(e)}")
            _record_login_metric(success=False)
            _audit(action="login_error", details={"username": username, "error": str(e)})
            return False
        finally:
            db.close()

    def logout(self):
        """End current session and clear Streamlit state."""
        user_id = st.session_state.get('user_id')
        username = st.session_state.get('username', 'unknown')
        try:
            self.session_manager.end_session()
            logger.info(f"User '{username}' logged out")
            _audit(user_id=user_id, action="logout", resource_type="session")
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
        finally:
            self.session_manager.clear_session_state()

    def is_authenticated(self) -> bool:
        """Check if the current session is authenticated."""
        if not st.session_state.get('authentication_status', False):
            return False

        session_token = st.session_state.get('session_token')
        if not session_token:
            return False

        user = self.session_manager.validate_session(session_token)
        return user is not None

    def get_current_user(self) -> Optional[User]:
        """Return the currently authenticated User object, or None."""
        session_token = st.session_state.get('session_token')
        if not session_token:
            return None
        return self.session_manager.validate_session(session_token)


def get_authenticator() -> Authenticator:
    """Factory function — returns an Authenticator instance."""
    return Authenticator()


def register_user(
    username: str,
    email: str,
    password: str,
    full_name: str = "",
    organization: str = ""
) -> bool:
    """
    Register a new user with bcrypt-hashed password.
    
    Returns True on success, False on failure.
    """
    if not username or not email or not password:
        return False

    if len(password) < 6:
        logger.warning(f"Registration rejected: password too short for '{username}'")
        return False

    with UserManager() as um:
        success = um.create_user(
            username=username,
            email=email,
            password=password,
            full_name=full_name or None,
            organization=organization or None
        )
        if success:
            logger.info(f"User '{username}' registered successfully")
        else:
            logger.warning(f"Registration failed for '{username}' (duplicate or DB error)")
        return success


def get_user_info(username: str) -> Optional[Dict[str, Any]]:
    """Get user information by username."""
    with UserManager() as um:
        user = um.get_user_by_username(username)
        if not user:
            return None
        return {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'full_name': user.full_name or user.username.title(),
            'organization': user.organization or "",
            'role': user.role,
            'is_active': user.is_active,
            'created_at': str(user.created_at) if user.created_at else None,
            'last_login': str(user.last_login) if user.last_login else None,
        }
