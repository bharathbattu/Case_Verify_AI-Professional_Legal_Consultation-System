"""
Tests for auth/authenticator.py — Extended coverage for logout, is_authenticated,
get_current_user, register_user, get_user_info, and the Authenticator.login() DB path.

Supplements test_authenticator.py which already covers rate-limiting internals.
"""

import pytest
from unittest.mock import patch, MagicMock, call
from types import SimpleNamespace

import sys
# Ensure the conftest streamlit stub is used (already in sys.modules from conftest.py)


class TestAuthenticatorLogout:
    """Tests for Authenticator.logout()."""

    def test_logout_clears_session_state(self):
        import streamlit as st
        st.session_state["authentication_status"] = True
        st.session_state["username"] = "testuser"
        st.session_state["user_id"] = 1

        from auth.authenticator import Authenticator
        auth = Authenticator()

        # Patch session_manager methods so they don't hit real DB
        auth.session_manager = MagicMock()

        auth.logout()

        auth.session_manager.end_session.assert_called_once()
        auth.session_manager.clear_session_state.assert_called_once()

    def test_logout_handles_session_manager_exception(self):
        import streamlit as st
        st.session_state["username"] = "testuser"

        from auth.authenticator import Authenticator
        auth = Authenticator()
        auth.session_manager = MagicMock()
        auth.session_manager.end_session.side_effect = Exception("DB error")

        # Should not raise
        auth.logout()
        # clear_session_state still called in finally
        auth.session_manager.clear_session_state.assert_called_once()


class TestAuthenticatorIsAuthenticated:
    """Tests for Authenticator.is_authenticated()."""

    def test_returns_false_when_no_auth_status(self):
        import streamlit as st
        st.session_state.clear()

        from auth.authenticator import Authenticator
        auth = Authenticator()
        auth.session_manager = MagicMock()

        assert auth.is_authenticated() is False

    def test_returns_false_when_no_session_token(self):
        import streamlit as st
        st.session_state.clear()
        st.session_state["authentication_status"] = True
        # No session_token

        from auth.authenticator import Authenticator
        auth = Authenticator()
        auth.session_manager = MagicMock()

        assert auth.is_authenticated() is False

    def test_returns_true_when_session_valid(self):
        import streamlit as st
        st.session_state.clear()
        st.session_state["authentication_status"] = True
        st.session_state["session_token"] = "valid-token"

        from auth.authenticator import Authenticator
        auth = Authenticator()
        auth.session_manager = MagicMock()
        auth.session_manager.validate_session.return_value = MagicMock()  # non-None user

        assert auth.is_authenticated() is True

    def test_returns_false_when_session_invalid(self):
        import streamlit as st
        st.session_state.clear()
        st.session_state["authentication_status"] = True
        st.session_state["session_token"] = "expired-token"

        from auth.authenticator import Authenticator
        auth = Authenticator()
        auth.session_manager = MagicMock()
        auth.session_manager.validate_session.return_value = None

        assert auth.is_authenticated() is False


class TestAuthenticatorGetCurrentUser:
    """Tests for Authenticator.get_current_user()."""

    def test_returns_none_when_no_token(self):
        import streamlit as st
        st.session_state.clear()

        from auth.authenticator import Authenticator
        auth = Authenticator()

        result = auth.get_current_user()
        assert result is None

    def test_returns_user_when_token_valid(self):
        import streamlit as st
        st.session_state.clear()
        st.session_state["session_token"] = "valid-token"

        fake_user = SimpleNamespace(id=1, username="alice")

        from auth.authenticator import Authenticator
        auth = Authenticator()
        auth.session_manager = MagicMock()
        auth.session_manager.validate_session.return_value = fake_user

        result = auth.get_current_user()
        assert result is fake_user


class TestAuthenticatorLoginDbPath:
    """Tests for Authenticator.login() DB interaction."""

    def setup_method(self):
        from auth.authenticator import _login_attempts
        _login_attempts.clear()

    def test_login_returns_false_when_user_not_found(self):
        import streamlit as st
        st.session_state.clear()

        from auth.authenticator import Authenticator
        auth = Authenticator()
        auth.session_manager = MagicMock()

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch("auth.authenticator.SessionLocal", return_value=mock_db):
            result = auth.login("nonexistent", "password")

        assert result is False
        mock_db.close.assert_called_once()

    def test_login_returns_false_when_wrong_password(self):
        import streamlit as st
        st.session_state.clear()

        fake_user = MagicMock()
        fake_user.id = 42
        fake_user.username = "alice"
        fake_user.hashed_password = "$2b$12$fakehash"
        fake_user.is_active = True
        fake_user.full_name = "Alice"
        fake_user.role = "user"

        from auth.authenticator import Authenticator
        auth = Authenticator()
        auth.session_manager = MagicMock()

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = fake_user

        with patch("auth.authenticator.SessionLocal", return_value=mock_db):
            with patch("auth.authenticator.bcrypt.verify", return_value=False):
                result = auth.login("alice", "wrong_password")

        assert result is False

    def test_login_returns_false_when_session_creation_fails(self):
        import streamlit as st
        st.session_state.clear()

        fake_user = MagicMock()
        fake_user.id = 1
        fake_user.username = "bob"
        fake_user.hashed_password = "$2b$12$fakehash"
        fake_user.is_active = True
        fake_user.full_name = "Bob"
        fake_user.role = "user"

        from auth.authenticator import Authenticator
        auth = Authenticator()
        auth.session_manager = MagicMock()
        auth.session_manager.create_session.return_value = None  # session creation fails

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = fake_user

        with patch("auth.authenticator.SessionLocal", return_value=mock_db):
            with patch("auth.authenticator.bcrypt.verify", return_value=True):
                result = auth.login("bob", "correct_password")

        assert result is False

    def test_login_returns_true_on_success(self):
        import streamlit as st
        st.session_state.clear()

        fake_user = MagicMock()
        fake_user.id = 99
        fake_user.username = "carol"
        fake_user.hashed_password = "$2b$12$fakehash"
        fake_user.is_active = True
        fake_user.full_name = "Carol"
        fake_user.role = "admin"

        from auth.authenticator import Authenticator
        auth = Authenticator()
        auth.session_manager = MagicMock()
        auth.session_manager.create_session.return_value = "tok-abc-123"

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = fake_user

        with patch("auth.authenticator.SessionLocal", return_value=mock_db):
            with patch("auth.authenticator.bcrypt.verify", return_value=True):
                result = auth.login("carol", "correct_password")

        assert result is True
        assert st.session_state.get("authentication_status") is True
        assert st.session_state.get("username") == "carol"

    def test_login_handles_db_exception(self):
        import streamlit as st
        st.session_state.clear()

        from auth.authenticator import Authenticator
        auth = Authenticator()
        auth.session_manager = MagicMock()

        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("DB crash")

        with patch("auth.authenticator.SessionLocal", return_value=mock_db):
            result = auth.login("anyuser", "anypassword")

        assert result is False
        mock_db.rollback.assert_called_once()
        mock_db.close.assert_called_once()


class TestGetAuthenticatorFactory:
    """Tests for get_authenticator() factory function."""

    def test_returns_authenticator_instance(self):
        from auth.authenticator import get_authenticator, Authenticator
        auth = get_authenticator()
        assert isinstance(auth, Authenticator)


class TestRegisterUserExtended:
    """Extended tests for register_user() — UserManager integration."""

    def test_register_calls_user_manager(self):
        mock_um = MagicMock()
        mock_um.__enter__ = MagicMock(return_value=mock_um)
        mock_um.__exit__ = MagicMock(return_value=False)
        mock_um.create_user.return_value = True

        with patch("auth.authenticator.UserManager", return_value=mock_um):
            from auth.authenticator import register_user
            result = register_user("newuser", "new@test.com", "password123")

        assert result is True
        mock_um.create_user.assert_called_once()

    def test_register_returns_false_on_duplicate(self):
        mock_um = MagicMock()
        mock_um.__enter__ = MagicMock(return_value=mock_um)
        mock_um.__exit__ = MagicMock(return_value=False)
        mock_um.create_user.return_value = False

        with patch("auth.authenticator.UserManager", return_value=mock_um):
            from auth.authenticator import register_user
            result = register_user("dupuser", "dup@test.com", "password123")

        assert result is False


class TestGetUserInfo:
    """Tests for get_user_info()."""

    def test_returns_none_when_user_not_found(self):
        mock_um = MagicMock()
        mock_um.__enter__ = MagicMock(return_value=mock_um)
        mock_um.__exit__ = MagicMock(return_value=False)
        mock_um.get_user_by_username.return_value = None

        with patch("auth.authenticator.UserManager", return_value=mock_um):
            from auth.authenticator import get_user_info
            result = get_user_info("ghost")

        assert result is None

    def test_returns_dict_when_user_found(self):
        fake_user = SimpleNamespace(
            id=5,
            username="alice",
            email="alice@test.com",
            full_name="Alice Smith",
            organization="ACME",
            role="user",
            is_active=True,
            created_at=None,
            last_login=None,
        )

        mock_um = MagicMock()
        mock_um.__enter__ = MagicMock(return_value=mock_um)
        mock_um.__exit__ = MagicMock(return_value=False)
        mock_um.get_user_by_username.return_value = fake_user

        with patch("auth.authenticator.UserManager", return_value=mock_um):
            from auth.authenticator import get_user_info
            result = get_user_info("alice")

        assert result is not None
        assert result["username"] == "alice"
        assert result["email"] == "alice@test.com"
        assert result["role"] == "user"
