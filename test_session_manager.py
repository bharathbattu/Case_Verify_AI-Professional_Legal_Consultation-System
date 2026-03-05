"""
Tests for auth/session_manager.py — SessionManager class.

All DB calls mocked; exercises create_session, validate_session, end_session,
cleanup_expired_sessions, extend_session, get_active_sessions, etc.
"""

import pytest
from types import SimpleNamespace
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock, call
import streamlit as st


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_sm():
    """Return a fresh SessionManager with a mocked DB."""
    from auth.session_manager import SessionManager
    sm = SessionManager()
    return sm


def _clear_st():
    st.session_state.clear()


def _col_mock():
    """Return a MagicMock column stub that supports all comparison operators.

    Python 3.13 raises TypeError for ``MagicMock() > datetime`` because
    MagicMock no longer provides default rich-comparison dunder methods.
    This helper produces a child mock where __gt__, __lt__, __eq__, etc. are
    explicitly configured to return a truthy MagicMock (mimicking a SQLAlchemy
    BinaryExpression) so that filter() argument construction never raises.
    """
    m = MagicMock()
    m.__gt__ = MagicMock(return_value=MagicMock())
    m.__lt__ = MagicMock(return_value=MagicMock())
    m.__ge__ = MagicMock(return_value=MagicMock())
    m.__le__ = MagicMock(return_value=MagicMock())
    m.__eq__ = MagicMock(return_value=MagicMock())
    m.__ne__ = MagicMock(return_value=MagicMock())
    return m


def _model_mock(**cols):
    """Return a MagicMock with named column attributes built via _col_mock()."""
    m = MagicMock()
    for name in cols:
        setattr(m, name, _col_mock())
    return m


# ---------------------------------------------------------------------------
# SessionManager.is_authenticated
# ---------------------------------------------------------------------------

class TestIsAuthenticated:

    def test_false_when_not_set(self):
        _clear_st()
        sm = _make_sm()
        assert sm.is_authenticated() is False

    def test_true_when_set(self):
        _clear_st()
        st.session_state['authentication_status'] = True
        sm = _make_sm()
        assert sm.is_authenticated() is True

    def test_false_when_not_true(self):
        _clear_st()
        st.session_state['authentication_status'] = None
        sm = _make_sm()
        assert sm.is_authenticated() is False


# ---------------------------------------------------------------------------
# SessionManager.create_session
# ---------------------------------------------------------------------------

class TestCreateSession:

    def test_creates_session_and_returns_token(self):
        _clear_st()
        mock_db = MagicMock()
        with patch("auth.session_manager.SessionLocal", return_value=mock_db):
            with patch("auth.session_manager.UserSession"):
                sm = _make_sm()
                token = sm.create_session(user_id=1)
        assert token is not None
        assert len(token) > 0
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_creates_session_sets_streamlit_state(self):
        _clear_st()
        mock_db = MagicMock()
        with patch("auth.session_manager.SessionLocal", return_value=mock_db):
            with patch("auth.session_manager.UserSession"):
                sm = _make_sm()
                sm.create_session(user_id=42)
        assert st.session_state.get("authentication_status") is True
        assert st.session_state.get("user_id") == 42

    def test_returns_none_on_db_exception(self):
        _clear_st()
        mock_db = MagicMock()
        mock_db.add.side_effect = Exception("DB error")
        with patch("auth.session_manager.SessionLocal", return_value=mock_db):
            sm = _make_sm()
            token = sm.create_session(user_id=1)
        assert token is None
        mock_db.rollback.assert_called_once()
        mock_db.close.assert_called_once()


# ---------------------------------------------------------------------------
# SessionManager.create_session_by_username
# ---------------------------------------------------------------------------

class TestCreateSessionByUsername:

    def test_returns_true_when_user_found(self):
        _clear_st()
        fake_user = SimpleNamespace(id=5)
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = fake_user

        with patch("auth.session_manager.SessionLocal", return_value=mock_db):
            with patch("auth.session_manager.UserSession"):
                sm = _make_sm()
                # Patch create_session to avoid full DB calls
                sm.create_session = MagicMock(return_value="tok-123")
                result = sm.create_session_by_username("alice")
        assert result is True

    def test_returns_false_when_user_not_found(self):
        _clear_st()
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch("auth.session_manager.SessionLocal", return_value=mock_db):
            sm = _make_sm()
            result = sm.create_session_by_username("ghost")
        assert result is False


# ---------------------------------------------------------------------------
# SessionManager.validate_session
# ---------------------------------------------------------------------------

class TestValidateSession:

    def test_returns_user_for_valid_session(self):
        _clear_st()
        fake_user = MagicMock()
        fake_user.is_active = True
        fake_session = MagicMock()
        fake_session.user_id = 1

        mock_db = MagicMock()
        # validate_session makes two db.query() calls: one for UserSession, one for User.
        # We use side_effect on db.query itself to return separate query-builder mocks.
        session_qb = MagicMock()
        session_qb.filter.return_value.first.return_value = fake_session
        user_qb = MagicMock()
        user_qb.filter.return_value.first.return_value = fake_user
        mock_db.query.side_effect = [session_qb, user_qb]

        # Patch UserSession / User column attrs so comparisons don't raise TypeError
        # (MagicMock() > datetime raises TypeError in Python 3.13+)
        mock_us = _model_mock(session_token=1, is_active=1, expires_at=1)
        mock_u = _model_mock(id=1)
        with patch("auth.session_manager.SessionLocal", return_value=mock_db), \
             patch("auth.session_manager.UserSession", mock_us), \
             patch("auth.session_manager.User", mock_u):
            sm = _make_sm()
            result = sm.validate_session("valid-token")
        assert result is fake_user

    def test_returns_none_when_session_not_found(self):
        _clear_st()
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch("auth.session_manager.SessionLocal", return_value=mock_db):
            sm = _make_sm()
            result = sm.validate_session("bad-token")
        assert result is None

    def test_returns_none_on_db_error(self):
        _clear_st()
        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("DB crash")

        with patch("auth.session_manager.SessionLocal", return_value=mock_db):
            sm = _make_sm()
            result = sm.validate_session("any-token")
        assert result is None


# ---------------------------------------------------------------------------
# SessionManager.end_session
# ---------------------------------------------------------------------------

class TestEndSession:

    def test_marks_session_inactive(self):
        _clear_st()
        fake_session = MagicMock()
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = fake_session

        with patch("auth.session_manager.SessionLocal", return_value=mock_db):
            sm = _make_sm()
            sm.end_session("tok-abc")
        assert fake_session.is_active is False
        mock_db.commit.assert_called_once()

    def test_uses_session_state_token_when_no_arg(self):
        _clear_st()
        st.session_state['session_token'] = "state-token"
        fake_session = MagicMock()
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = fake_session

        with patch("auth.session_manager.SessionLocal", return_value=mock_db):
            sm = _make_sm()
            sm.end_session()
        mock_db.commit.assert_called_once()

    def test_no_op_when_no_token_anywhere(self):
        _clear_st()
        mock_db = MagicMock()

        with patch("auth.session_manager.SessionLocal", return_value=mock_db):
            sm = _make_sm()
            sm.end_session()  # Should not raise
        mock_db.query.assert_not_called()

    def test_rollbacks_on_db_error(self):
        _clear_st()
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.side_effect = Exception("crash")

        with patch("auth.session_manager.SessionLocal", return_value=mock_db):
            sm = _make_sm()
            sm.end_session("tok-xyz")  # Should not raise
        mock_db.rollback.assert_called_once()


# ---------------------------------------------------------------------------
# SessionManager.clear_session_state
# ---------------------------------------------------------------------------

class TestClearSessionState:

    def test_removes_expected_keys(self):
        _clear_st()
        st.session_state['session_token'] = "tok"
        st.session_state['username'] = "alice"
        st.session_state['user_id'] = 1
        st.session_state['authentication_status'] = True

        sm = _make_sm()
        sm.clear_session_state()

        assert 'session_token' not in st.session_state
        assert 'username' not in st.session_state
        assert 'user_id' not in st.session_state
        assert 'authentication_status' not in st.session_state

    def test_tolerates_missing_keys(self):
        _clear_st()
        sm = _make_sm()
        sm.clear_session_state()  # Should not raise


# ---------------------------------------------------------------------------
# SessionManager.extend_session
# ---------------------------------------------------------------------------

class TestExtendSession:

    def test_extends_expiry(self):
        _clear_st()
        fake_session = MagicMock()
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = fake_session

        with patch("auth.session_manager.SessionLocal", return_value=mock_db):
            sm = _make_sm()
            result = sm.extend_session("tok-abc")
        assert result is True
        mock_db.commit.assert_called_once()

    def test_returns_false_when_session_not_found(self):
        _clear_st()
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch("auth.session_manager.SessionLocal", return_value=mock_db):
            sm = _make_sm()
            result = sm.extend_session("nonexistent")
        assert result is False


# ---------------------------------------------------------------------------
# SessionManager.cleanup_expired_sessions
# ---------------------------------------------------------------------------

class TestCleanupExpiredSessions:

    def test_marks_expired_sessions_inactive(self):
        _clear_st()
        expired = [MagicMock(), MagicMock()]
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = expired

        # Patch UserSession so column comparisons don't raise TypeError in Python 3.13+
        mock_us = _model_mock(expires_at=1)
        with patch("auth.session_manager.SessionLocal", return_value=mock_db), \
             patch("auth.session_manager.UserSession", mock_us):
            sm = _make_sm()
            count = sm.cleanup_expired_sessions()
        assert count == 2
        for s in expired:
            assert s.is_active is False

    def test_returns_zero_when_none_expired(self):
        _clear_st()
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        with patch("auth.session_manager.SessionLocal", return_value=mock_db):
            sm = _make_sm()
            count = sm.cleanup_expired_sessions()
        assert count == 0

    def test_returns_zero_on_db_error(self):
        _clear_st()
        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("crash")

        with patch("auth.session_manager.SessionLocal", return_value=mock_db):
            sm = _make_sm()
            count = sm.cleanup_expired_sessions()
        assert count == 0
        mock_db.rollback.assert_called_once()


# ---------------------------------------------------------------------------
# SessionManager.get_session_info
# ---------------------------------------------------------------------------

class TestGetSessionInfo:

    def test_returns_dict_for_valid_session(self):
        _clear_st()
        fake_session = MagicMock()
        fake_session.user_id = 7
        fake_session.created_at = datetime.now(timezone.utc)
        fake_session.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        fake_session.is_active = True
        fake_session.ip_address = "127.0.0.1"
        fake_session.user_agent = "test-agent"
        fake_session.device_info = {}

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = fake_session

        with patch("auth.session_manager.SessionLocal", return_value=mock_db):
            sm = _make_sm()
            result = sm.get_session_info("tok-abc")
        assert result is not None
        assert result['user_id'] == 7
        assert result['ip_address'] == "127.0.0.1"

    def test_returns_none_when_session_not_found(self):
        _clear_st()
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch("auth.session_manager.SessionLocal", return_value=mock_db):
            sm = _make_sm()
            result = sm.get_session_info("missing-token")
        assert result is None


# ---------------------------------------------------------------------------
# SessionManager.get_active_sessions
# ---------------------------------------------------------------------------

class TestGetActiveSessions:

    def test_returns_list_of_active_sessions(self):
        _clear_st()
        fake_sessions = [MagicMock(), MagicMock()]
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = fake_sessions

        # Patch UserSession so column comparisons don't raise TypeError in Python 3.13+
        mock_us = _model_mock(user_id=1, is_active=1, expires_at=1)
        with patch("auth.session_manager.SessionLocal", return_value=mock_db), \
             patch("auth.session_manager.UserSession", mock_us):
            sm = _make_sm()
            result = sm.get_active_sessions(user_id=1)
        assert result == fake_sessions

    def test_returns_empty_list_on_db_error(self):
        _clear_st()
        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("crash")

        with patch("auth.session_manager.SessionLocal", return_value=mock_db):
            sm = _make_sm()
            result = sm.get_active_sessions(user_id=1)
        assert result == []


# ---------------------------------------------------------------------------
# SessionManager.destroy_session (convenience method)
# ---------------------------------------------------------------------------

class TestDestroySession:

    def test_calls_end_session_with_state_token(self):
        _clear_st()
        st.session_state['session_token'] = "state-tok"
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = MagicMock()

        with patch("auth.session_manager.SessionLocal", return_value=mock_db):
            sm = _make_sm()
            sm.end_session = MagicMock()
            sm.destroy_session()
            sm.end_session.assert_called_once_with("state-tok")

    def test_calls_clear_session_state_when_no_token(self):
        _clear_st()
        sm = _make_sm()
        sm.clear_session_state = MagicMock()
        sm.destroy_session()
        sm.clear_session_state.assert_called_once()


# ---------------------------------------------------------------------------
# Module-level helpers: init_session_state, is_authenticated, get_current_user
# ---------------------------------------------------------------------------

class TestModuleLevelHelpers:

    def test_init_session_state_sets_defaults(self):
        _clear_st()
        from auth.session_manager import init_session_state
        init_session_state()
        assert 'authentication_status' in st.session_state
        assert st.session_state['authentication_status'] is None

    def test_init_session_state_does_not_overwrite_existing(self):
        _clear_st()
        st.session_state['username'] = "alice"
        from auth.session_manager import init_session_state
        init_session_state()
        assert st.session_state['username'] == "alice"

    def test_is_authenticated_false(self):
        _clear_st()
        from auth.session_manager import is_authenticated
        assert is_authenticated() is False

    def test_is_authenticated_true(self):
        _clear_st()
        st.session_state['authentication_status'] = True
        from auth.session_manager import is_authenticated
        assert is_authenticated() is True

    def test_get_current_user_none(self):
        _clear_st()
        from auth.session_manager import get_current_user
        assert get_current_user() is None

    def test_get_current_user_id_none(self):
        _clear_st()
        from auth.session_manager import get_current_user_id
        assert get_current_user_id() is None

    def test_get_current_user_id_returns_id(self):
        _clear_st()
        st.session_state['user_id'] = 42
        from auth.session_manager import get_current_user_id
        assert get_current_user_id() == 42
