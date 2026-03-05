"""
test_session_manager_require_role.py — Covers the require_role static decorator
in auth/session_manager.py (lines 246-268) that was missed in the main
test_session_manager.py file.
"""

import pytest
from unittest.mock import MagicMock, patch
import streamlit as st


def _clear_st():
    st.session_state.clear()


# ---------------------------------------------------------------------------
# SessionManager.require_role static decorator (lines 246-268)
# ---------------------------------------------------------------------------

class TestRequireRole:
    """Tests for SessionManager.require_role static decorator."""

    def test_admin_can_access_any_role(self):
        """Admin role bypasses all role checks and calls the wrapped function."""
        _clear_st()
        st.session_state['user_role'] = 'admin'

        from auth.session_manager import SessionManager

        called = []

        @SessionManager.require_role("lawyer")
        def protected_fn():
            called.append(True)
            return "ok"

        result = protected_fn()
        assert result == "ok"
        assert called == [True]

    def test_matching_role_allows_access(self):
        """User with exact required role can access the function."""
        _clear_st()
        st.session_state['user_role'] = 'lawyer'

        from auth.session_manager import SessionManager

        called = []

        @SessionManager.require_role("lawyer")
        def protected_fn():
            called.append(True)
            return "lawyer_result"

        result = protected_fn()
        assert result == "lawyer_result"
        assert called == [True]

    def test_wrong_role_stops_and_shows_error(self):
        """User with wrong role triggers st.error and st.stop."""
        _clear_st()
        st.session_state['user_role'] = 'user'

        from auth.session_manager import SessionManager

        called = []

        # st.stop raises a special exception in Streamlit; in our stub it's
        # a MagicMock so we need to make it raise to stop execution
        st.stop = MagicMock(side_effect=RuntimeError("st.stop called"))

        @SessionManager.require_role("admin")
        def protected_fn():
            called.append(True)  # Should not be called

        with pytest.raises(RuntimeError, match="st.stop called"):
            protected_fn()

        st.error.assert_called()
        assert called == []

    def test_missing_role_stops_and_shows_error(self):
        """When user_role not in session state, st.error and st.stop are called."""
        _clear_st()  # No 'user_role' key

        from auth.session_manager import SessionManager

        called = []
        st.stop = MagicMock(side_effect=RuntimeError("st.stop called"))

        @SessionManager.require_role("admin")
        def protected_fn():
            called.append(True)

        with pytest.raises(RuntimeError, match="st.stop called"):
            protected_fn()

        st.error.assert_called()
        assert called == []

    def test_decorator_preserves_function_arguments(self):
        """Wrapped function receives its arguments correctly when role matches."""
        _clear_st()
        st.session_state['user_role'] = 'lawyer'

        from auth.session_manager import SessionManager

        @SessionManager.require_role("lawyer")
        def fn_with_args(a, b, keyword="default"):
            return (a, b, keyword)

        result = fn_with_args(1, 2, keyword="custom")
        assert result == (1, 2, "custom")

    def test_admin_passes_through_for_user_role(self):
        """Admin bypasses even 'user' role requirement."""
        _clear_st()
        st.session_state['user_role'] = 'admin'

        from auth.session_manager import SessionManager

        @SessionManager.require_role("user")
        def fn():
            return "user_fn"

        assert fn() == "user_fn"


# ---------------------------------------------------------------------------
# Module-level require_auth decorator (lines 11-19)
# ---------------------------------------------------------------------------

class TestModuleLevelRequireAuth:
    """Tests for the module-level require_auth decorator (not the static method)."""

    def test_unauthenticated_returns_none(self):
        """When not authenticated, wrapped function returns None."""
        _clear_st()  # No authentication_status set

        from auth.session_manager import require_auth

        called = []

        @require_auth
        def protected():
            called.append(True)
            return "result"

        result = protected()
        assert result is None
        assert called == []
        st.warning.assert_called()

    def test_authenticated_calls_function(self):
        """When authenticated, wrapped function is called normally."""
        _clear_st()
        st.session_state['authentication_status'] = True

        from auth.session_manager import require_auth

        called = []

        @require_auth
        def protected():
            called.append(True)
            return "result"

        result = protected()
        assert result == "result"
        assert called == [True]
