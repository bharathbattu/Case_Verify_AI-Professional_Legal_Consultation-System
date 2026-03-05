"""
Tests for auth/simple_auth.py — Development-only authentication.

Covers: S-09 (UUID instead of hash, env-based credentials)
"""

import json
import os
import uuid
import pytest
from unittest.mock import patch, MagicMock

# conftest.py already registered a streamlit stub; import after conftest runs.
from auth.simple_auth import (
    _load_dev_users,
    _stable_uuid,
    _user_uuid_map,
    SimpleAuthenticator,
    get_user_info,
    register_user,
)


# ---------------------------------------------------------------------------
# Helper: a fresh session_state dict patched onto the simple_auth module's
# ``st`` reference for each test.
# ---------------------------------------------------------------------------
def _fresh_state():
    return {}


class TestLoadDevUsers:
    """Tests for _load_dev_users()."""

    def test_returns_empty_when_env_not_set(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("SIMPLE_AUTH_USERS", None)
            result = _load_dev_users()
            assert result == {}

    def test_returns_empty_for_blank_string(self):
        with patch.dict(os.environ, {"SIMPLE_AUTH_USERS": "   "}):
            result = _load_dev_users()
            assert result == {}

    def test_parses_valid_json(self):
        users = {"demo": "pass1", "admin": "pass2"}
        with patch.dict(os.environ, {"SIMPLE_AUTH_USERS": json.dumps(users)}):
            result = _load_dev_users()
            assert result == users

    def test_returns_empty_for_invalid_json(self):
        with patch.dict(os.environ, {"SIMPLE_AUTH_USERS": "not json{"}):
            result = _load_dev_users()
            assert result == {}

    def test_returns_empty_for_non_dict_json(self):
        with patch.dict(os.environ, {"SIMPLE_AUTH_USERS": '["a", "b"]'}):
            result = _load_dev_users()
            assert result == {}


class TestStableUUID:
    """Tests for _stable_uuid() — S-09: UUID instead of hash(username)."""

    def setup_method(self):
        _user_uuid_map.clear()

    def test_returns_valid_uuid_string(self):
        result = _stable_uuid("testuser")
        parsed = uuid.UUID(result)
        assert parsed.version == 4

    def test_same_user_gets_same_uuid(self):
        first = _stable_uuid("user1")
        second = _stable_uuid("user1")
        assert first == second

    def test_different_users_get_different_uuids(self):
        uuid1 = _stable_uuid("alice")
        uuid2 = _stable_uuid("bob")
        assert uuid1 != uuid2

    def test_not_predictable_from_username(self):
        # uuid4 is random — clearing the map gives a different value each time
        _user_uuid_map.clear()
        first_run = _stable_uuid("demo")
        _user_uuid_map.clear()
        second_run = _stable_uuid("demo")
        assert first_run != second_run


class TestSimpleAuthenticator:
    """Tests for SimpleAuthenticator class."""

    def setup_method(self):
        _user_uuid_map.clear()

    def test_login_success_with_valid_credentials(self):
        fake_state = _fresh_state()
        import auth.simple_auth as _sa
        users = {"demo": "secret123"}
        with patch.dict(os.environ, {"SIMPLE_AUTH_USERS": json.dumps(users)}):
            with patch.object(_sa.st, "session_state", fake_state):
                auth = SimpleAuthenticator()
                result = auth.login("demo", "secret123")
                assert result is True
                assert fake_state["authentication_status"] is True
                assert fake_state["username"] == "demo"

    def test_login_failure_with_wrong_password(self):
        fake_state = _fresh_state()
        import auth.simple_auth as _sa
        users = {"demo": "secret123"}
        with patch.dict(os.environ, {"SIMPLE_AUTH_USERS": json.dumps(users)}):
            with patch.object(_sa.st, "session_state", fake_state):
                auth = SimpleAuthenticator()
                result = auth.login("demo", "wrong")
                assert result is False

    def test_login_failure_with_unknown_user(self):
        fake_state = _fresh_state()
        import auth.simple_auth as _sa
        users = {"demo": "secret123"}
        with patch.dict(os.environ, {"SIMPLE_AUTH_USERS": json.dumps(users)}):
            with patch.object(_sa.st, "session_state", fake_state):
                auth = SimpleAuthenticator()
                result = auth.login("unknown", "secret123")
                assert result is False

    def test_login_sets_uuid_not_hash(self):
        fake_state = _fresh_state()
        import auth.simple_auth as _sa
        users = {"demo": "pass"}
        with patch.dict(os.environ, {"SIMPLE_AUTH_USERS": json.dumps(users)}):
            with patch.object(_sa.st, "session_state", fake_state):
                auth = SimpleAuthenticator()
                auth.login("demo", "pass")
                user_id = fake_state.get("user_id")
                parsed = uuid.UUID(user_id)
                assert parsed.version == 4

    def test_login_disabled_when_no_users(self):
        fake_state = _fresh_state()
        import auth.simple_auth as _sa
        with patch.dict(os.environ, {"SIMPLE_AUTH_USERS": ""}):
            with patch.object(_sa.st, "session_state", fake_state):
                auth = SimpleAuthenticator()
                result = auth.login("demo", "demo123")
                assert result is False

    def test_logout_clears_session_state(self):
        fake_state = {
            "authentication_status": True,
            "username": "demo",
            "name": "Demo",
            "user_id": "some-uuid",
        }
        import auth.simple_auth as _sa
        with patch.object(_sa.st, "session_state", fake_state):
            auth = SimpleAuthenticator()
            auth.logout()
            assert "authentication_status" not in fake_state
            assert "username" not in fake_state


class TestGetUserInfo:
    """Tests for get_user_info()."""

    def setup_method(self):
        _user_uuid_map.clear()

    def test_returns_dict_with_expected_keys(self):
        info = get_user_info("testuser")
        expected_keys = {"id", "username", "email", "full_name", "organization",
                        "role", "is_active", "created_at", "last_login"}
        assert set(info.keys()) == expected_keys

    def test_id_is_uuid(self):
        info = get_user_info("testuser")
        parsed = uuid.UUID(info["id"])
        assert parsed.version == 4

    def test_email_contains_username(self):
        info = get_user_info("alice")
        assert "alice" in info["email"]


class TestRegisterUser:
    """Tests for register_user() — always succeeds in dev mode."""

    def test_always_returns_true(self):
        assert register_user("user", "email@test.com", "pass") is True
