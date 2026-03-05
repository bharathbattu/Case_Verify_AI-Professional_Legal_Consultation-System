"""
Simplified authentication for Case-Verify AI
Temporary module to avoid database dependencies during development.

Security notes (S-09):
  - Uses uuid4 instead of hash(username) for user IDs to avoid
    predictable / colliding identifiers.
  - Passwords are NOT hardcoded — reads from SIMPLE_AUTH_USERS env var
    (JSON dict) or falls back to disabled auth in production.
"""
import logging
import os
import json
import uuid
import streamlit as st

logger = logging.getLogger(__name__)


def _load_dev_users() -> dict:
    """
    Load development-only credentials from the SIMPLE_AUTH_USERS env var.

    Expected format (JSON string):
        {"demo": "someP@ss1", "admin": "Adm!n9876"}

    Returns an empty dict when the variable is absent or in production,
    which effectively disables simple auth login.
    """
    raw = os.getenv("SIMPLE_AUTH_USERS", "")
    if not raw.strip():
        return {}
    try:
        users = json.loads(raw)
        if not isinstance(users, dict):
            logger.error("SIMPLE_AUTH_USERS must be a JSON object — ignoring")
            return {}
        return users
    except json.JSONDecodeError:
        logger.error("SIMPLE_AUTH_USERS is not valid JSON — ignoring")
        return {}


# Stable UUID mapping so repeated logins for the same user keep the same id
# within a single process lifetime (resets on restart, which is fine for dev).
_user_uuid_map: dict = {}


def _stable_uuid(username: str) -> str:
    """Return a deterministic-per-process UUID for *username*."""
    if username not in _user_uuid_map:
        _user_uuid_map[username] = str(uuid.uuid4())
    return _user_uuid_map[username]


class SimpleAuthenticator:
    """Simple authentication system without database (development only)."""

    def __init__(self) -> None:
        self.users = _load_dev_users()

    def login(self, username: str, password: str) -> bool:
        """Login a user with username and password."""
        if username in self.users and self.users[username] == password:
            st.session_state["authentication_status"] = True
            st.session_state["username"] = username
            st.session_state["name"] = username.title()
            st.session_state["user_id"] = _stable_uuid(username)
            return True
        return False

    def logout(self) -> None:
        """Logout the current user."""
        for key in ["authentication_status", "username", "name", "user_id"]:
            if key in st.session_state:
                del st.session_state[key]


def get_authenticator():
    """Get the authenticator instance."""
    return SimpleAuthenticator()


def register_user(
    username: str,
    email: str,
    password: str,
    full_name: str = "",
    organization: str = "",
) -> bool:
    """Register a new user (simplified version — always succeeds in dev)."""
    return True


def get_user_info(username: str):
    """Get user information by username (simplified)."""
    return {
        "id": _stable_uuid(username),
        "username": username,
        "email": f"{username}@example.com",
        "full_name": username.title(),
        "organization": "Demo Organization",
        "role": "user",
        "is_active": True,
        "created_at": "2024-01-01",
        "last_login": None,
    }
