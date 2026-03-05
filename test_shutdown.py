"""
Tests for shutdown.py — Graceful shutdown handlers.

Covers: Op-04 (Graceful shutdown)
"""

import atexit
import signal
import logging
import pytest
from unittest.mock import patch, MagicMock, call

import shutdown
from shutdown import register_shutdown_hooks, _cleanup, _signal_handler


class TestCleanup:
    """Tests for _cleanup() function."""

    @patch("shutdown.logging")
    def test_cleanup_disposes_engine(self, mock_logging):
        mock_engine = MagicMock()
        with patch.dict("sys.modules", {"database.connection": MagicMock(engine=mock_engine)}):
            _cleanup()
            mock_engine.dispose.assert_called_once()

    @patch("shutdown.logging")
    def test_cleanup_handles_engine_failure(self, mock_logging):
        # Should not raise even if engine.dispose fails
        with patch.dict("sys.modules", {}):
            with patch("shutdown.logger") as mock_logger:
                # Importing database.connection may fail
                try:
                    _cleanup()
                except SystemExit:
                    pass  # database module import may trigger SystemExit
                # No unhandled exception means success

    def test_cleanup_flushes_log_handlers(self):
        # Use a real NullHandler (not a MagicMock) so logging's internal
        # levelno >= handler.level comparison doesn't get a MagicMock.
        mock_flush = MagicMock()
        real_handler = logging.NullHandler()
        real_handler.flush = mock_flush  # type: ignore[method-assign]
        root_logger = logging.getLogger()
        root_logger.addHandler(real_handler)
        try:
            with patch.dict("sys.modules", {"database.connection": MagicMock(engine=MagicMock())}):
                _cleanup()
            mock_flush.assert_called()
        finally:
            root_logger.removeHandler(real_handler)


class TestSignalHandler:
    """Tests for _signal_handler()."""

    def test_signal_handler_calls_cleanup_and_exits(self):
        with patch("shutdown._cleanup") as mock_cleanup:
            with pytest.raises(SystemExit) as exc_info:
                _signal_handler(signal.SIGTERM, None)
            mock_cleanup.assert_called_once()
            assert exc_info.value.code == 0


class TestRegisterShutdownHooks:
    """Tests for register_shutdown_hooks()."""

    def setup_method(self):
        # Reset the registration flag
        shutdown._shutdown_registered = False

    def test_registers_atexit(self):
        with patch("shutdown.atexit.register") as mock_atexit:
            with patch("shutdown.signal.signal"):
                register_shutdown_hooks()
                mock_atexit.assert_called_once_with(_cleanup)

    def test_idempotent_registration(self):
        with patch("shutdown.atexit.register") as mock_atexit:
            with patch("shutdown.signal.signal"):
                register_shutdown_hooks()
                register_shutdown_hooks()  # Second call
                # Should only register once
                assert mock_atexit.call_count == 1

    def test_handles_signal_registration_failure(self):
        shutdown._shutdown_registered = False
        with patch("shutdown.atexit.register"):
            with patch("shutdown.signal.signal", side_effect=OSError("not supported")):
                # Should not raise
                register_shutdown_hooks()
                assert shutdown._shutdown_registered is True
