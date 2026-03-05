"""
Tests for metrics.py (O-02)

Validates that all public helper functions in the metrics module:
  - exist and are callable
  - never raise exceptions even when prometheus_client is absent
  - update counters when prometheus_client IS available

These tests do NOT start an HTTP server.
"""
import sys
import importlib
import unittest.mock as mock


# ---------------------------------------------------------------------------
# Import the live metrics module once (singleton — re-importing is fine).
# We must NOT use importlib.reload() because prometheus_client raises
# "Duplicated timeseries" when metric objects are registered twice in the
# same process-level CollectorRegistry.
# ---------------------------------------------------------------------------
import metrics as _metrics_live


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _import_metrics_no_prometheus():
    """
    Return a fresh metrics module with prometheus_client hidden.

    We use a private CollectorRegistry to avoid the global registry
    duplicate-registration error.
    """
    # Temporarily hide prometheus_client
    orig = sys.modules.get("prometheus_client")
    sys.modules["prometheus_client"] = None  # type: ignore[assignment]
    sys.modules.pop("metrics", None)
    try:
        import metrics as m
    finally:
        if orig is None:
            sys.modules.pop("prometheus_client", None)
        else:
            sys.modules["prometheus_client"] = orig
        # Re-cache the live module so subsequent imports get the real one
        sys.modules["metrics"] = _metrics_live
    return m


# ---------------------------------------------------------------------------
# Tests: graceful degradation (no prometheus_client)
# ---------------------------------------------------------------------------

class TestMetricsDegradedMode:
    """All helpers must be silent no-ops when prometheus_client is missing."""

    def setup_method(self):
        self.m = _import_metrics_no_prometheus()

    def test_prometheus_not_available_flag(self):
        assert self.m._PROMETHEUS_AVAILABLE is False

    def test_inc_analyses_does_not_raise(self):
        self.m.inc_analyses("money-recovery")

    def test_inc_analysis_error_does_not_raise(self):
        self.m.inc_analysis_error("cheque-bounce")

    def test_inc_cache_hit_does_not_raise(self):
        self.m.inc_cache_hit()

    def test_inc_cache_miss_does_not_raise(self):
        self.m.inc_cache_miss()

    def test_observe_api_latency_does_not_raise(self):
        self.m.observe_api_latency(1.23)

    def test_inc_login_success_does_not_raise(self):
        self.m.inc_login(success=True)

    def test_inc_login_failure_does_not_raise(self):
        self.m.inc_login(success=False)

    def test_inc_rate_limited_does_not_raise(self):
        self.m.inc_rate_limited()

    def test_start_metrics_server_does_not_raise(self):
        # Should log a warning but never raise
        self.m.start_metrics_server(port=19999)


# ---------------------------------------------------------------------------
# Tests: real prometheus_client present (uses the live singleton module)
# ---------------------------------------------------------------------------

class TestMetricsWithPrometheus:
    """When prometheus_client is present, counters and histograms are real objects."""

    def setup_method(self):
        try:
            import prometheus_client  # noqa: F401
        except ImportError:
            import pytest
            pytest.skip("prometheus_client not installed")
        self.m = _metrics_live

    def test_prometheus_available_flag(self):
        assert self.m._PROMETHEUS_AVAILABLE is True

    def test_inc_analyses_increments_counter(self):
        relief = "test-relief-unique-xyz"
        before = self.m.ANALYSES_TOTAL.labels(relief_type=relief)._value.get()
        self.m.inc_analyses(relief_type=relief)
        after = self.m.ANALYSES_TOTAL.labels(relief_type=relief)._value.get()
        assert after == before + 1

    def test_inc_cache_hit_increments(self):
        before = self.m.CACHE_HITS_TOTAL._value.get()
        self.m.inc_cache_hit()
        after = self.m.CACHE_HITS_TOTAL._value.get()
        assert after == before + 1

    def test_inc_cache_miss_increments(self):
        before = self.m.CACHE_MISSES_TOTAL._value.get()
        self.m.inc_cache_miss()
        after = self.m.CACHE_MISSES_TOTAL._value.get()
        assert after == before + 1

    def test_observe_api_latency(self):
        self.m.observe_api_latency(2.5)

    def test_inc_login_success(self):
        before = self.m.LOGIN_ATTEMPTS_TOTAL.labels(outcome="success")._value.get()
        self.m.inc_login(success=True)
        after = self.m.LOGIN_ATTEMPTS_TOTAL.labels(outcome="success")._value.get()
        assert after == before + 1

    def test_inc_login_failure(self):
        before = self.m.LOGIN_ATTEMPTS_TOTAL.labels(outcome="failure")._value.get()
        self.m.inc_login(success=False)
        after = self.m.LOGIN_ATTEMPTS_TOTAL.labels(outcome="failure")._value.get()
        assert after == before + 1

    def test_inc_rate_limited(self):
        before = self.m.RATE_LIMITED_TOTAL._value.get()
        self.m.inc_rate_limited()
        after = self.m.RATE_LIMITED_TOTAL._value.get()
        assert after == before + 1

    def test_inc_analysis_error(self):
        relief = "test-error-relief"
        before = self.m.ANALYSIS_ERRORS_TOTAL.labels(relief_type=relief)._value.get()
        self.m.inc_analysis_error(relief_type=relief)
        after = self.m.ANALYSIS_ERRORS_TOTAL.labels(relief_type=relief)._value.get()
        assert after == before + 1


# ---------------------------------------------------------------------------
# Tests: no-op stubs behave correctly (using degraded-mode module)
# ---------------------------------------------------------------------------

class TestNoOpStubs:
    """Direct unit tests for _NoOpCounter and _NoOpHistogram."""

    def setup_method(self):
        self.m = _import_metrics_no_prometheus()

    def test_noop_counter_inc(self):
        c = self.m._NoOpCounter()
        c.inc()
        c.labels(foo="bar").inc(5)

    def test_noop_histogram_observe(self):
        h = self.m._NoOpHistogram()
        h.observe(1.0)
        h.labels(foo="bar").observe(2.0)

    def test_noop_histogram_time_context(self):
        h = self.m._NoOpHistogram()
        with h.time():
            pass
