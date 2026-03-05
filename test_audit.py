"""
Tests for audit.py — Audit trail writer.

Covers: O-04 (Audit trail)
"""

import pytest
from types import SimpleNamespace
from unittest.mock import patch, MagicMock, call


def _make_audit_log_factory():
    """
    Return a callable that behaves like AuditLog(**kwargs) by building a
    SimpleNamespace, so attribute-access assertions work correctly.
    """
    def factory(**kwargs):
        return SimpleNamespace(**kwargs)
    return factory


class TestLogAction:
    """Tests for log_action()."""

    @patch("audit.AuditLog", side_effect=_make_audit_log_factory())
    @patch("audit.SessionLocal")
    def test_writes_audit_entry(self, mock_session_factory, mock_audit_log):
        mock_session = MagicMock()
        mock_session_factory.return_value = mock_session

        from audit import log_action
        log_action(user_id=1, action="login", resource_type="session")

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

    @patch("audit.AuditLog", side_effect=_make_audit_log_factory())
    @patch("audit.SessionLocal")
    def test_passes_all_fields(self, mock_session_factory, mock_audit_log):
        mock_session = MagicMock()
        mock_session_factory.return_value = mock_session

        from audit import log_action
        log_action(
            user_id=42,
            action="analyse_case",
            resource_type="case",
            resource_id="CVA-123",
            details={"type": "Civil"},
            ip_address="127.0.0.1",
        )

        call_args = mock_session.add.call_args
        entry = call_args[0][0]
        assert entry.user_id == 42
        assert entry.action == "analyse_case"
        assert entry.resource_type == "case"
        assert entry.resource_id == "CVA-123"
        assert entry.ip_address == "127.0.0.1"

    @patch("audit.AuditLog", side_effect=_make_audit_log_factory())
    @patch("audit.SessionLocal")
    def test_rollbacks_on_db_error(self, mock_session_factory, mock_audit_log):
        mock_session = MagicMock()
        mock_session.commit.side_effect = Exception("DB error")
        mock_session_factory.return_value = mock_session

        from audit import log_action
        # Should not raise — fire-and-forget
        log_action(user_id=1, action="test")

        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    @patch("audit.AuditLog", side_effect=_make_audit_log_factory())
    @patch("audit.SessionLocal")
    def test_always_closes_session(self, mock_session_factory, mock_audit_log):
        mock_session = MagicMock()
        mock_session_factory.return_value = mock_session

        from audit import log_action
        log_action(action="test")

        mock_session.close.assert_called_once()

    @patch("audit.AuditLog", side_effect=_make_audit_log_factory())
    @patch("audit.SessionLocal")
    def test_none_user_id_accepted(self, mock_session_factory, mock_audit_log):
        mock_session = MagicMock()
        mock_session_factory.return_value = mock_session

        from audit import log_action
        # Should not raise
        log_action(action="anonymous_action")
        mock_session.add.assert_called_once()

    @patch("audit.AuditLog", side_effect=_make_audit_log_factory())
    @patch("audit.SessionLocal")
    def test_resource_id_converted_to_string(self, mock_session_factory, mock_audit_log):
        mock_session = MagicMock()
        mock_session_factory.return_value = mock_session

        from audit import log_action
        log_action(action="test", resource_id=12345)

        entry = mock_session.add.call_args[0][0]
        assert entry.resource_id == "12345"

    @patch("audit.AuditLog", side_effect=_make_audit_log_factory())
    @patch("audit.SessionLocal")
    def test_none_resource_id_stays_none(self, mock_session_factory, mock_audit_log):
        mock_session = MagicMock()
        mock_session_factory.return_value = mock_session

        from audit import log_action
        log_action(action="test", resource_id=None)

        entry = mock_session.add.call_args[0][0]
        assert entry.resource_id is None
