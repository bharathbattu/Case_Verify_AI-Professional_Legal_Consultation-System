"""
Tests for init_database.py — DB init script with secure password management.

Covers: pure functions generate_secure_password(), validate_password_strength(),
        and the init_database() flow with mocked DB.
"""

import pytest
import string
from unittest.mock import patch, MagicMock, call


# ---------------------------------------------------------------------------
# Helpers — import the pure functions directly
# ---------------------------------------------------------------------------

from init_database import generate_secure_password, validate_password_strength


class TestGenerateSecurePassword:
    """Tests for generate_secure_password()."""

    def test_default_length(self):
        pw = generate_secure_password()
        assert len(pw) == 16

    def test_custom_length(self):
        pw = generate_secure_password(length=32)
        assert len(pw) == 32

    def test_minimum_length(self):
        pw = generate_secure_password(length=1)
        assert len(pw) == 1

    def test_characters_from_valid_set(self):
        valid = set(string.ascii_letters + string.digits + string.punctuation)
        pw = generate_secure_password(length=64)
        for ch in pw:
            assert ch in valid

    def test_different_calls_produce_different_passwords(self):
        # Cryptographically random — extremely unlikely to collide
        pw1 = generate_secure_password(length=32)
        pw2 = generate_secure_password(length=32)
        assert pw1 != pw2


class TestValidatePasswordStrength:
    """Tests for validate_password_strength()."""

    def test_accepts_strong_password(self):
        assert validate_password_strength("StrongPass1") is True

    def test_rejects_too_short(self):
        assert validate_password_strength("Ab1") is False

    def test_rejects_no_uppercase(self):
        assert validate_password_strength("lowercase1") is False

    def test_rejects_no_lowercase(self):
        assert validate_password_strength("UPPERCASE1") is False

    def test_rejects_no_digit(self):
        assert validate_password_strength("NoDigitHere") is False

    def test_accepts_exactly_8_chars(self):
        assert validate_password_strength("Abcde12!") is True

    def test_rejects_7_chars(self):
        assert validate_password_strength("Abcde1!") is False

    def test_all_conditions_met(self):
        # Mixed case, digit, long
        assert validate_password_strength("SecurePassword123!") is True


class TestInitDatabaseFunction:
    """Tests for init_database() using mocked DB/bcrypt."""

    def _make_mocks(self):
        """Return (mock_db, mock_session_local_ctx, mock_base_ctx, mock_bcrypt_ctx)."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None  # No existing admin
        return mock_db

    @patch("init_database.bcrypt")
    @patch("init_database.User")
    @patch("init_database.Base")
    @patch("init_database.SessionLocal")
    @patch("init_database.engine")
    def test_creates_tables_on_fresh_db(self, mock_engine, mock_sl, mock_base, mock_user, mock_bcrypt):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_sl.return_value = mock_db
        mock_bcrypt.gensalt.return_value = b"$2b$12$fakesalt"
        mock_bcrypt.hashpw.return_value = b"$2b$12$fakehash"

        from init_database import init_database
        result = init_database()

        assert result is True
        mock_base.metadata.create_all.assert_called_once_with(bind=mock_engine)

    @patch("init_database.bcrypt")
    @patch("init_database.User")
    @patch("init_database.Base")
    @patch("init_database.SessionLocal")
    @patch("init_database.engine")
    def test_creates_admin_user_when_missing(self, mock_engine, mock_sl, mock_base, mock_user, mock_bcrypt):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_sl.return_value = mock_db
        mock_bcrypt.gensalt.return_value = b"$2b$12$fakesalt"
        mock_bcrypt.hashpw.return_value = b"$2b$12$fakehash"

        from init_database import init_database
        result = init_database()

        assert result is True
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()

    @patch("init_database.bcrypt")
    @patch("init_database.Base")
    @patch("init_database.SessionLocal")
    @patch("init_database.engine")
    def test_skips_admin_creation_when_exists(self, mock_engine, mock_sl, mock_base, mock_bcrypt):
        mock_db = MagicMock()
        # Simulate existing admin
        mock_db.query.return_value.filter.return_value.first.return_value = MagicMock()
        mock_sl.return_value = mock_db

        from init_database import init_database
        result = init_database()

        assert result is True
        mock_db.add.assert_not_called()

    @patch.dict("os.environ", {"ADMIN_PASSWORD": "ValidPass1"})
    @patch("init_database.bcrypt")
    @patch("init_database.User")
    @patch("init_database.Base")
    @patch("init_database.SessionLocal")
    @patch("init_database.engine")
    def test_uses_env_admin_password(self, mock_engine, mock_sl, mock_base, mock_user, mock_bcrypt):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_sl.return_value = mock_db
        mock_bcrypt.gensalt.return_value = b"$2b$12$fakesalt"
        mock_bcrypt.hashpw.return_value = b"$2b$12$fakehash"

        from init_database import init_database
        result = init_database()

        assert result is True
        # bcrypt.hashpw should have been called with the env password
        mock_bcrypt.hashpw.assert_called_once_with(b"ValidPass1", b"$2b$12$fakesalt")

    @patch.dict("os.environ", {"ADMIN_PASSWORD": "weak"})
    @patch("init_database.Base")
    @patch("init_database.SessionLocal")
    @patch("init_database.engine")
    def test_rejects_weak_env_password(self, mock_engine, mock_sl, mock_base):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_sl.return_value = mock_db

        from init_database import init_database
        result = init_database()

        assert result is False

    @patch("init_database.bcrypt")
    @patch("init_database.Base")
    @patch("init_database.SessionLocal")
    @patch("init_database.engine")
    def test_returns_false_on_db_exception(self, mock_engine, mock_sl, mock_base, mock_bcrypt):
        mock_base.metadata.create_all.side_effect = Exception("DB error")

        from init_database import init_database
        result = init_database()

        assert result is False

    @patch("init_database.bcrypt")
    @patch("init_database.User")
    @patch("init_database.Base")
    @patch("init_database.SessionLocal")
    @patch("init_database.engine")
    def test_always_closes_db_session(self, mock_engine, mock_sl, mock_base, mock_user, mock_bcrypt):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_sl.return_value = mock_db
        mock_bcrypt.gensalt.return_value = b"$2b$12$fakesalt"
        mock_bcrypt.hashpw.return_value = b"$2b$12$fakehash"

        from init_database import init_database
        init_database()

        mock_db.close.assert_called_once()
