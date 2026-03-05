"""
test_misc_coverage.py — Targeted micro-tests to push coverage over 70%.

Covers:
  database/connection.py  lines 89-92  — reset_database()
  metrics.py              lines 163-164, 171-172, 179-180, 187-188,
                          195-196, 204-205, 212-213 — except branches in helpers
                          lines 231-240 — start_metrics_server port-in-use path
  auth/__init__.py        lines 23-72  — simplified fallback classes/functions
"""

import sys
import os
import pytest
from unittest.mock import patch, MagicMock
import streamlit as st


# ===========================================================================
# database/connection.py — reset_database() (lines 89-92)
# ===========================================================================

class TestResetDatabase:

    def test_reset_database_calls_drop_and_create(self):
        """reset_database() must call drop_all then create_all."""
        from database import connection as conn

        mock_base = MagicMock()
        with patch("database.connection.engine") as mock_engine, \
             patch("database.models.Base", mock_base):
            # Patch the local re-import inside reset_database
            with patch("database.connection.Base", mock_base):
                conn.reset_database()

        mock_base.metadata.drop_all.assert_called_once()
        mock_base.metadata.create_all.assert_called_once()

    def test_reset_database_does_not_raise(self):
        """reset_database() should complete without raising."""
        from database import connection as conn

        mock_base = MagicMock()
        with patch("database.connection.Base", mock_base):
            conn.reset_database()  # Should not raise


# ===========================================================================
# metrics.py — except Exception: pass branches in helper functions
# (lines 163-164, 171-172, 179-180, 187-188, 195-196, 204-205, 212-213)
# ===========================================================================

class TestMetricsExceptBranches:
    """
    Force each helper's inner try/except by making the relevant metric object
    raise on call.  Uses the live metrics singleton so no reload is needed.
    """

    def setup_method(self):
        import metrics as m
        self.m = m

    def test_inc_analyses_except_branch(self):
        """ANALYSES_TOTAL.labels(...).inc() raises → silent except."""
        broken = MagicMock()
        broken.labels.return_value.inc.side_effect = Exception("boom")
        with patch.object(self.m, "ANALYSES_TOTAL", broken):
            self.m.inc_analyses("test-type")  # Must NOT raise

    def test_inc_analysis_error_except_branch(self):
        broken = MagicMock()
        broken.labels.return_value.inc.side_effect = Exception("boom")
        with patch.object(self.m, "ANALYSIS_ERRORS_TOTAL", broken):
            self.m.inc_analysis_error("test-type")

    def test_inc_cache_hit_except_branch(self):
        broken = MagicMock()
        broken.inc.side_effect = Exception("boom")
        with patch.object(self.m, "CACHE_HITS_TOTAL", broken):
            self.m.inc_cache_hit()

    def test_inc_cache_miss_except_branch(self):
        broken = MagicMock()
        broken.inc.side_effect = Exception("boom")
        with patch.object(self.m, "CACHE_MISSES_TOTAL", broken):
            self.m.inc_cache_miss()

    def test_observe_api_latency_except_branch(self):
        broken = MagicMock()
        broken.observe.side_effect = Exception("boom")
        with patch.object(self.m, "API_LATENCY", broken):
            self.m.observe_api_latency(1.0)

    def test_inc_login_except_branch(self):
        broken = MagicMock()
        broken.labels.return_value.inc.side_effect = Exception("boom")
        with patch.object(self.m, "LOGIN_ATTEMPTS_TOTAL", broken):
            self.m.inc_login(success=True)

    def test_inc_rate_limited_except_branch(self):
        broken = MagicMock()
        broken.inc.side_effect = Exception("boom")
        with patch.object(self.m, "RATE_LIMITED_TOTAL", broken):
            self.m.inc_rate_limited()


# ===========================================================================
# metrics.py — start_metrics_server (lines 231-240)
# ===========================================================================

class TestStartMetricsServer:
    """Tests for start_metrics_server() when prometheus_client IS available."""

    def _live_metrics(self):
        import metrics as m
        return m

    def test_starts_server_on_given_port(self):
        """start_metrics_server() calls start_http_server with resolved port."""
        m = self._live_metrics()
        if not m._PROMETHEUS_AVAILABLE:
            pytest.skip("prometheus_client not installed")

        with patch("metrics.start_http_server") as mock_start:
            m.start_metrics_server(port=19876)
            mock_start.assert_called_once_with(19876)

    def test_port_already_in_use_does_not_raise(self):
        """OSError 'already in use' → silently logged, no re-raise."""
        m = self._live_metrics()
        if not m._PROMETHEUS_AVAILABLE:
            pytest.skip("prometheus_client not installed")

        err = OSError("address already in use")
        err.errno = 98  # EADDRINUSE on Linux (10048 on Windows)
        with patch("metrics.start_http_server", side_effect=err):
            m.start_metrics_server(port=19877)  # Must NOT raise

    def test_port_already_in_use_windows_errno(self):
        """OSError errno 10048 (Windows EADDRINUSE) → silently logged."""
        m = self._live_metrics()
        if not m._PROMETHEUS_AVAILABLE:
            pytest.skip("prometheus_client not installed")

        err = OSError("address already in use")
        err.errno = 10048
        with patch("metrics.start_http_server", side_effect=err):
            m.start_metrics_server(port=19878)  # Must NOT raise

    def test_other_oserror_logs_error(self):
        """OSError that is NOT 'already in use' → logged as error, no raise."""
        m = self._live_metrics()
        if not m._PROMETHEUS_AVAILABLE:
            pytest.skip("prometheus_client not installed")

        err = OSError("permission denied")
        err.errno = 13
        with patch("metrics.start_http_server", side_effect=err):
            m.start_metrics_server(port=19879)  # Must NOT raise

    def test_reads_metrics_port_env_var(self):
        """When port arg is None, uses METRICS_PORT env var."""
        m = self._live_metrics()
        if not m._PROMETHEUS_AVAILABLE:
            pytest.skip("prometheus_client not installed")

        with patch("metrics.start_http_server") as mock_start, \
             patch.dict(os.environ, {"METRICS_PORT": "19880"}):
            m.start_metrics_server(port=None)
            mock_start.assert_called_once_with(19880)


# ===========================================================================
# auth/__init__.py — simplified fallback classes (lines 23-72)
# ===========================================================================

class TestAuthInitFallbackClasses:
    """
    Exercise the fallback class definitions in auth/__init__.py (lines 28-72)
    by importing the simplified auth fallback module directly and instantiating
    the classes/calling the functions defined there.

    We reload auth/__init__.py with the production imports forcibly broken so
    the except block runs.
    """

    def _load_fallback_auth(self):
        """
        Force auth/__init__.py to take the simplified fallback path by
        temporarily hiding the production modules from sys.modules.
        """
        # Save originals
        saved = {}
        for key in list(sys.modules):
            if key.startswith("auth."):
                saved[key] = sys.modules.pop(key)
        saved_auth = sys.modules.pop("auth", None)

        # Hide production submodules so `from .authenticator import ...` fails
        sys.modules["auth.authenticator"] = None   # type: ignore[assignment]
        sys.modules["auth.user_manager"] = None    # type: ignore[assignment]
        sys.modules["auth.session_manager"] = None # type: ignore[assignment]

        try:
            import importlib
            import auth as auth_fallback
            importlib.reload(auth_fallback)
            return auth_fallback
        finally:
            # Restore
            for key, val in saved.items():
                sys.modules[key] = val
            if saved_auth is not None:
                sys.modules["auth"] = saved_auth
            else:
                sys.modules.pop("auth", None)
            # Clean up the None stubs
            for key in ["auth.authenticator", "auth.user_manager", "auth.session_manager"]:
                if sys.modules.get(key) is None:
                    sys.modules.pop(key, None)

    def test_simplified_session_manager_is_authenticated(self):
        """Simplified SessionManager.is_authenticated reads st.session_state."""
        auth = self._load_fallback_auth()
        sm = auth.SessionManager()

        st.session_state.clear()
        assert not sm.is_authenticated()

        st.session_state['authentication_status'] = True
        assert sm.is_authenticated()

    def test_simplified_session_manager_create_session_by_username(self):
        """Simplified SessionManager.create_session_by_username sets state."""
        auth = self._load_fallback_auth()
        sm = auth.SessionManager()

        st.session_state.clear()
        sm.create_session_by_username("bob")
        assert st.session_state.get('username') == "bob"
        assert st.session_state.get('authentication_status') is True

    def test_simplified_session_manager_destroy_session(self):
        """Simplified SessionManager.destroy_session clears auth state."""
        auth = self._load_fallback_auth()
        sm = auth.SessionManager()

        st.session_state['authentication_status'] = True
        st.session_state['username'] = "bob"
        sm.destroy_session()
        assert 'authentication_status' not in st.session_state
        assert 'username' not in st.session_state

    def test_simplified_user_manager_instantiates(self):
        """Simplified UserManager can be instantiated."""
        auth = self._load_fallback_auth()
        um = auth.UserManager()
        assert um is not None

    def test_simplified_require_auth_blocks_unauthenticated(self):
        """Simplified require_auth decorator blocks if not authenticated."""
        auth = self._load_fallback_auth()
        st.session_state.clear()

        called = []

        @auth.require_auth()
        def fn():
            called.append(True)
            return "result"

        result = fn()
        assert result is None
        assert called == []

    def test_simplified_require_auth_allows_authenticated(self):
        """Simplified require_auth decorator passes through if authenticated."""
        auth = self._load_fallback_auth()
        st.session_state['authentication_status'] = True

        called = []

        @auth.require_auth()
        def fn():
            called.append(True)
            return "result"

        result = fn()
        assert result == "result"
        assert called == [True]
