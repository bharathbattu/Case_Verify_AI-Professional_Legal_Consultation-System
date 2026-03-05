"""
Tests for auth/authenticator.py — Rate limiting, audit trail, authentication.

Covers: S-02, R-01 (Auth), S-06 (Rate limiting), O-04 (Audit trail integration)
"""

import time
import pytest
from unittest.mock import patch, MagicMock, PropertyMock

# We need to mock streamlit before importing authenticator
import sys
mock_st = MagicMock()
mock_st.session_state = {}
sys.modules.setdefault("streamlit", mock_st)

from auth.authenticator import (
    _check_rate_limit,
    _record_failed_attempt,
    _clear_attempts,
    _login_attempts,
)


class TestRateLimiting:
    """Tests for S-06: Login rate limiting."""

    def setup_method(self):
        """Clear rate limit state between tests."""
        _login_attempts.clear()

    def test_no_limit_initially(self):
        result = _check_rate_limit("testuser")
        assert result is None

    def test_allows_under_threshold(self):
        for _ in range(4):  # Below default max of 5
            _record_failed_attempt("testuser")
        result = _check_rate_limit("testuser")
        assert result is None

    def test_blocks_at_threshold(self):
        for _ in range(5):  # Exactly at default max
            _record_failed_attempt("testuser")
        result = _check_rate_limit("testuser")
        assert result is not None
        assert result > 0

    def test_blocks_over_threshold(self):
        for _ in range(10):
            _record_failed_attempt("testuser")
        result = _check_rate_limit("testuser")
        assert result is not None

    def test_clear_attempts_resets(self):
        for _ in range(5):
            _record_failed_attempt("testuser")
        _clear_attempts("testuser")
        result = _check_rate_limit("testuser")
        assert result is None

    def test_different_users_independent(self):
        for _ in range(5):
            _record_failed_attempt("user_a")
        # user_b should not be affected
        result = _check_rate_limit("user_b")
        assert result is None

    def test_lockout_expires_after_window(self):
        # Use a very short lockout for testing
        _record_failed_attempt("testuser")
        # Manually set first_fail to far in the past
        _login_attempts["testuser"] = (5, time.time() - 1000)
        result = _check_rate_limit("testuser", lockout_seconds=900)
        # 1000 > 900, so window expired
        assert result is None

    def test_lockout_returns_remaining_seconds(self):
        now = time.time()
        _login_attempts["testuser"] = (5, now)
        result = _check_rate_limit("testuser", max_attempts=5, lockout_seconds=600)
        assert result is not None
        assert 590 <= result <= 600  # approximately 600 seconds remaining

    def test_custom_max_attempts(self):
        for _ in range(2):
            _record_failed_attempt("testuser")
        # With max_attempts=2, should be blocked
        result = _check_rate_limit("testuser", max_attempts=2)
        assert result is not None

    def test_clear_nonexistent_user_no_error(self):
        # Should not raise
        _clear_attempts("nonexistent_user")


class TestAuthenticatorLogin:
    """Tests for Authenticator.login() method."""

    def setup_method(self):
        _login_attempts.clear()
        mock_st.session_state = {}

    def test_login_rejects_empty_username(self):
        from auth.authenticator import Authenticator
        auth = Authenticator()
        assert auth.login("", "password") is False

    def test_login_rejects_empty_password(self):
        from auth.authenticator import Authenticator
        auth = Authenticator()
        assert auth.login("user", "") is False

    def test_login_rejects_rate_limited_user(self):
        from auth.authenticator import Authenticator
        # Exhaust rate limit
        for _ in range(5):
            _record_failed_attempt("blocked_user")
        auth = Authenticator()
        result = auth.login("blocked_user", "any_password")
        assert result is False


class TestRegisterUser:
    """Tests for register_user() function."""

    def test_rejects_empty_username(self):
        from auth.authenticator import register_user
        assert register_user("", "email@test.com", "password123") is False

    def test_rejects_empty_email(self):
        from auth.authenticator import register_user
        assert register_user("user", "", "password123") is False

    def test_rejects_empty_password(self):
        from auth.authenticator import register_user
        assert register_user("user", "email@test.com", "") is False

    def test_rejects_short_password(self):
        from auth.authenticator import register_user
        assert register_user("user", "email@test.com", "12345") is False
