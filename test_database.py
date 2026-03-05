"""
Tests for database/connection.py — Session management and context manager.

Covers: P-04 (db_session context manager)
"""

import pytest
from unittest.mock import patch, MagicMock, PropertyMock


class TestDbSession:
    """Tests for the db_session() context manager."""

    @patch("database.connection.SessionLocal")
    def test_commits_on_clean_exit(self, mock_session_factory):
        mock_session = MagicMock()
        mock_session_factory.return_value = mock_session

        from database.connection import db_session
        with db_session() as session:
            assert session is mock_session

        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()
        mock_session.rollback.assert_not_called()

    @patch("database.connection.SessionLocal")
    def test_rollbacks_on_exception(self, mock_session_factory):
        mock_session = MagicMock()
        mock_session_factory.return_value = mock_session

        from database.connection import db_session
        with pytest.raises(ValueError):
            with db_session() as session:
                raise ValueError("test error")

        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()
        mock_session.commit.assert_not_called()

    @patch("database.connection.SessionLocal")
    def test_always_closes_session(self, mock_session_factory):
        mock_session = MagicMock()
        mock_session_factory.return_value = mock_session

        from database.connection import db_session
        try:
            with db_session() as session:
                raise RuntimeError("boom")
        except RuntimeError:
            pass

        mock_session.close.assert_called_once()


class TestGetDb:
    """Tests for the legacy get_db() generator."""

    @patch("database.connection.SessionLocal")
    def test_yields_and_closes(self, mock_session_factory):
        mock_session = MagicMock()
        mock_session_factory.return_value = mock_session

        from database.connection import get_db
        gen = get_db()
        session = next(gen)
        assert session is mock_session

        # Exhaust generator
        try:
            next(gen)
        except StopIteration:
            pass

        mock_session.close.assert_called_once()


class TestInitDatabase:
    """Tests for init_database()."""

    @patch("database.connection.engine")
    def test_creates_all_tables(self, mock_engine):
        from database.connection import init_database
        # init_database() does `from database.models import Base` locally,
        # so we must patch the name inside database.models (not connection).
        with patch("database.models.Base") as mock_base:
            init_database()
            mock_base.metadata.create_all.assert_called_once_with(bind=mock_engine)
