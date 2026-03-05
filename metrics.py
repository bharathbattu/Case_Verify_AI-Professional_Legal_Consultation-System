"""
Prometheus metrics for Case-Verify AI.

O-02 / Hardening Plan: Provides request-rate, error-rate, cache-hit ratio,
and API-latency visibility without requiring a running Prometheus server —
metrics are collected in-process and can be scraped from an HTTP endpoint
or written to a push-gateway.

Design
------
* Wraps ``prometheus_client`` behind a thin shim so the rest of the
  codebase never crashes when the library is absent (e.g. in CI or
  environments without the optional dependency).
* All metric objects are module-level singletons; importing this module
  multiple times is safe.
* Starts an optional HTTP /metrics endpoint on ``METRICS_PORT`` (default 8000)
  when run as ``__main__`` or when ``start_metrics_server()`` is called
  explicitly.

Metrics exposed
---------------
``case_verify_analyses_total``          Counter   – labelled by relief type
``case_verify_analysis_errors_total``   Counter   – labelled by relief type
``case_verify_cache_hits_total``        Counter   – cache hits in agent.py
``case_verify_cache_misses_total``      Counter   – cache misses in agent.py
``case_verify_api_latency_seconds``     Histogram – Gemini API call duration
``case_verify_login_attempts_total``    Counter   – labelled by outcome (success|failure)
``case_verify_rate_limited_total``      Counter   – login attempts blocked by rate-limiter

Usage
-----
    from metrics import (
        inc_analyses, inc_analysis_error,
        inc_cache_hit, inc_cache_miss,
        observe_api_latency,
        inc_login, inc_rate_limited,
    )
"""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Generator

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Try to import prometheus_client; fall back to no-op stubs.
# ---------------------------------------------------------------------------
try:
    from prometheus_client import (
        Counter,
        Histogram,
        start_http_server,
        REGISTRY,
    )
    _PROMETHEUS_AVAILABLE = True
    logger.info("prometheus_client available — metrics collection active")
except ImportError:
    _PROMETHEUS_AVAILABLE = False
    logger.warning(
        "prometheus_client not installed — metrics collection disabled. "
        "Install it with: pip install prometheus-client"
    )


# ---------------------------------------------------------------------------
# No-op stubs used when prometheus_client is absent
# ---------------------------------------------------------------------------
class _NoOpCounter:
    """Silent no-op replacement for prometheus_client.Counter."""
    def labels(self, **_kwargs) -> "_NoOpCounter":
        return self
    def inc(self, _amount: float = 1) -> None:
        pass


class _NoOpHistogram:
    """Silent no-op replacement for prometheus_client.Histogram."""
    def labels(self, **_kwargs) -> "_NoOpHistogram":
        return self
    def observe(self, _value: float) -> None:
        pass
    def time(self):
        """Context manager / decorator compatible stub."""
        import contextlib
        return contextlib.nullcontext()


# ---------------------------------------------------------------------------
# Metric singletons
# ---------------------------------------------------------------------------
def _make_counter(name: str, doc: str, labelnames: list[str] | None = None):
    if not _PROMETHEUS_AVAILABLE:
        return _NoOpCounter()
    return Counter(name, doc, labelnames or [])


def _make_histogram(name: str, doc: str, labelnames: list[str] | None = None,
                    buckets=None):
    if not _PROMETHEUS_AVAILABLE:
        return _NoOpHistogram()
    kwargs = {"labelnames": labelnames or []}
    if buckets is not None:
        kwargs["buckets"] = buckets
    return Histogram(name, doc, **kwargs)


# Analysis counters
ANALYSES_TOTAL = _make_counter(
    "case_verify_analyses_total",
    "Total number of legal-case analyses requested, labelled by relief type.",
    ["relief_type"],
)

ANALYSIS_ERRORS_TOTAL = _make_counter(
    "case_verify_analysis_errors_total",
    "Total number of analysis requests that resulted in an error.",
    ["relief_type"],
)

# Cache counters
CACHE_HITS_TOTAL = _make_counter(
    "case_verify_cache_hits_total",
    "Total number of analysis requests served from the LRU cache.",
)

CACHE_MISSES_TOTAL = _make_counter(
    "case_verify_cache_misses_total",
    "Total number of analysis requests that bypassed the cache.",
)

# API latency histogram (buckets tuned for typical Gemini response times)
API_LATENCY = _make_histogram(
    "case_verify_api_latency_seconds",
    "Gemini API call duration in seconds.",
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 60.0],
)

# Auth counters
LOGIN_ATTEMPTS_TOTAL = _make_counter(
    "case_verify_login_attempts_total",
    "Total login attempts, labelled by outcome (success or failure).",
    ["outcome"],
)

RATE_LIMITED_TOTAL = _make_counter(
    "case_verify_rate_limited_total",
    "Total login attempts blocked by the rate-limiter.",
)


# ---------------------------------------------------------------------------
# Convenience helpers — called from agent.py and authenticator.py
# ---------------------------------------------------------------------------

def inc_analyses(relief_type: str = "unknown") -> None:
    """Increment the total-analyses counter for a given relief type."""
    try:
        ANALYSES_TOTAL.labels(relief_type=relief_type).inc()
    except Exception:
        pass


def inc_analysis_error(relief_type: str = "unknown") -> None:
    """Increment the analysis-errors counter."""
    try:
        ANALYSIS_ERRORS_TOTAL.labels(relief_type=relief_type).inc()
    except Exception:
        pass


def inc_cache_hit() -> None:
    """Increment the cache-hit counter."""
    try:
        CACHE_HITS_TOTAL.inc()
    except Exception:
        pass


def inc_cache_miss() -> None:
    """Increment the cache-miss counter."""
    try:
        CACHE_MISSES_TOTAL.inc()
    except Exception:
        pass


def observe_api_latency(seconds: float) -> None:
    """Record a Gemini API call duration."""
    try:
        API_LATENCY.observe(seconds)
    except Exception:
        pass


def inc_login(success: bool) -> None:
    """Increment the login-attempts counter."""
    try:
        outcome = "success" if success else "failure"
        LOGIN_ATTEMPTS_TOTAL.labels(outcome=outcome).inc()
    except Exception:
        pass


def inc_rate_limited() -> None:
    """Increment the rate-limited counter."""
    try:
        RATE_LIMITED_TOTAL.inc()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Optional HTTP /metrics endpoint
# ---------------------------------------------------------------------------

def start_metrics_server(port: int | None = None) -> None:
    """
    Start Prometheus HTTP /metrics scrape endpoint.

    Reads ``METRICS_PORT`` env var (default 8000).  Safe to call multiple
    times — subsequent calls are silently ignored when the server is already
    running.
    """
    if not _PROMETHEUS_AVAILABLE:
        logger.warning("Cannot start metrics server: prometheus_client not installed.")
        return
    resolved_port = port or int(os.getenv("METRICS_PORT", "8000"))
    try:
        start_http_server(resolved_port)
        logger.info("Prometheus /metrics endpoint started on port %d", resolved_port)
    except OSError as exc:
        # Port already in use — server was already started
        if "already in use" in str(exc).lower() or exc.errno == 98 or exc.errno == 10048:
            logger.debug("Metrics server already running on port %d", resolved_port)
        else:
            logger.error("Failed to start metrics server: %s", exc)


# ---------------------------------------------------------------------------
# CLI entry-point — dump current metric values to stdout
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    if not _PROMETHEUS_AVAILABLE:
        print("prometheus_client is not installed. Run: pip install prometheus-client")
        sys.exit(1)
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    print(generate_latest(REGISTRY).decode())
