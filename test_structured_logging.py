"""
Tests for structured_logging.py — JSON log formatter and configure_logging.

Covers: O-01 (Structured JSON logging)
"""

import json
import logging
import os
import pytest
from io import StringIO
from unittest.mock import patch

from structured_logging import _JSONFormatter, configure_logging


class TestJSONFormatter:
    """Tests for the _JSONFormatter class."""

    def setup_method(self):
        self.formatter = _JSONFormatter()

    def test_format_returns_valid_json(self):
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py",
            lineno=10, msg="hello", args=(), exc_info=None,
        )
        output = self.formatter.format(record)
        parsed = json.loads(output)
        assert parsed["level"] == "INFO"
        assert parsed["message"] == "hello"

    def test_format_includes_timestamp(self):
        record = logging.LogRecord(
            name="test", level=logging.WARNING, pathname="test.py",
            lineno=5, msg="warn", args=(), exc_info=None,
        )
        parsed = json.loads(self.formatter.format(record))
        assert "timestamp" in parsed
        assert "T" in parsed["timestamp"]  # ISO-8601 format

    def test_format_includes_module_info(self):
        record = logging.LogRecord(
            name="mylogger", level=logging.ERROR, pathname="my_module.py",
            lineno=42, msg="boom", args=(), exc_info=None,
        )
        parsed = json.loads(self.formatter.format(record))
        assert parsed["lineno"] == 42
        assert parsed["logger"] == "mylogger"

    def test_format_extra_fields(self):
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py",
            lineno=1, msg="with extra", args=(), exc_info=None,
        )
        record.user_id = 42
        record.action = "login"
        parsed = json.loads(self.formatter.format(record))
        assert parsed["user_id"] == 42
        assert parsed["action"] == "login"

    def test_format_non_serializable_extra(self):
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py",
            lineno=1, msg="bad extra", args=(), exc_info=None,
        )
        record.weird_obj = object()  # not JSON serializable
        parsed = json.loads(self.formatter.format(record))
        assert "weird_obj" in parsed  # should fall back to repr()

    def test_format_exception_info(self):
        try:
            raise ValueError("test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test", level=logging.ERROR, pathname="test.py",
            lineno=1, msg="error", args=(), exc_info=exc_info,
        )
        parsed = json.loads(self.formatter.format(record))
        assert "exception" in parsed
        assert "ValueError" in parsed["exception"]


class TestConfigureLogging:
    """Tests for configure_logging()."""

    def test_configures_root_logger(self):
        configure_logging(level="DEBUG")
        root = logging.getLogger()
        assert root.level == logging.DEBUG

    def test_respects_log_level_env_var(self):
        with patch.dict(os.environ, {"LOG_LEVEL": "WARNING"}):
            configure_logging()
            root = logging.getLogger()
            assert root.level == logging.WARNING

    def test_explicit_level_overrides_env(self):
        with patch.dict(os.environ, {"LOG_LEVEL": "WARNING"}):
            configure_logging(level="ERROR")
            root = logging.getLogger()
            assert root.level == logging.ERROR

    def test_quiets_noisy_loggers(self):
        configure_logging()
        for name in ("urllib3", "google", "httpcore", "httpx"):
            assert logging.getLogger(name).level >= logging.WARNING

    def test_handler_uses_json_formatter(self):
        configure_logging(level="INFO")
        root = logging.getLogger()
        json_handlers = [
            h for h in root.handlers if isinstance(h.formatter, _JSONFormatter)
        ]
        assert len(json_handlers) >= 1

    def test_file_handler_created_when_log_file_set(self, tmp_path):
        log_file = str(tmp_path / "test.log")
        configure_logging(log_file=log_file)
        root = logging.getLogger()
        file_handlers = [
            h for h in root.handlers if isinstance(h, logging.FileHandler)
        ]
        assert len(file_handlers) >= 1
        # Cleanup
        for h in file_handlers:
            h.close()
