"""
Tests for auth/user_manager.py — UserManager class.

All database calls are mocked; pure logic branches are exercised directly.
Also covers the hash_password() utility function.
"""

import pytest
from types import SimpleNamespace
from unittest.mock import patch, MagicMock, call
from datetime import datetime


# ---------------------------------------------------------------------------
# hash_password utility
# ---------------------------------------------------------------------------

class TestHashPassword:

    def test_returns_string(self):
        from auth.user_manager import hash_password
        result = hash_password("mypassword")
        assert isinstance(result, str)

    def test_returns_non_empty_hash(self):
        from auth.user_manager import hash_password
        result = hash_password("abc")
        assert len(result) > 0


# ---------------------------------------------------------------------------
# UserManager context-manager protocol
# ---------------------------------------------------------------------------

class TestUserManagerContextManager:

    def test_context_manager_closes_db(self):
        mock_db = MagicMock()
        with patch("auth.user_manager.SessionLocal", return_value=mock_db):
            from auth.user_manager import UserManager
            with UserManager() as um:
                pass
            mock_db.close.assert_called_once()


# ---------------------------------------------------------------------------
# UserManager.create_user
# ---------------------------------------------------------------------------

class TestCreateUser:

    def _make_um(self, mock_db):
        with patch("auth.user_manager.SessionLocal", return_value=mock_db):
            from auth.user_manager import UserManager
            return UserManager()

    def test_creates_user_successfully(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        with patch("auth.user_manager.SessionLocal", return_value=mock_db):
            with patch("auth.user_manager.User") as mock_user_cls:
                from auth.user_manager import UserManager
                um = UserManager()
                result = um.create_user("alice", "alice@test.com", "Pass1234")
        assert result is True
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_rejects_duplicate_username(self):
        mock_db = MagicMock()
        # First call returns existing user (username check)
        existing = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = existing

        with patch("auth.user_manager.SessionLocal", return_value=mock_db):
            from auth.user_manager import UserManager
            um = UserManager()
            result = um.create_user("alice", "new@test.com", "Pass1234")
        assert result is False
        mock_db.add.assert_not_called()

    def test_rollbacks_on_db_exception(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.commit.side_effect = Exception("DB crash")

        with patch("auth.user_manager.SessionLocal", return_value=mock_db):
            with patch("auth.user_manager.User"):
                from auth.user_manager import UserManager
                um = UserManager()
                result = um.create_user("bob", "bob@test.com", "Pass1234")
        assert result is False
        mock_db.rollback.assert_called_once()


# ---------------------------------------------------------------------------
# UserManager.get_user_by_* queries
# ---------------------------------------------------------------------------

class TestGetUserQueries:

    def test_get_user_by_username(self):
        mock_db = MagicMock()
        fake_user = SimpleNamespace(id=1, username="alice")
        mock_db.query.return_value.filter.return_value.first.return_value = fake_user

        with patch("auth.user_manager.SessionLocal", return_value=mock_db):
            from auth.user_manager import UserManager
            um = UserManager()
            result = um.get_user_by_username("alice")
        assert result is fake_user

    def test_get_user_by_email(self):
        mock_db = MagicMock()
        fake_user = SimpleNamespace(id=2, email="bob@test.com")
        mock_db.query.return_value.filter.return_value.first.return_value = fake_user

        with patch("auth.user_manager.SessionLocal", return_value=mock_db):
            from auth.user_manager import UserManager
            um = UserManager()
            result = um.get_user_by_email("bob@test.com")
        assert result is fake_user

    def test_get_user_by_id(self):
        mock_db = MagicMock()
        fake_user = SimpleNamespace(id=5)
        mock_db.query.return_value.filter.return_value.first.return_value = fake_user

        with patch("auth.user_manager.SessionLocal", return_value=mock_db):
            from auth.user_manager import UserManager
            um = UserManager()
            result = um.get_user_by_id(5)
        assert result is fake_user


# ---------------------------------------------------------------------------
# UserManager.update_user
# ---------------------------------------------------------------------------

class TestUpdateUser:

    def test_update_returns_false_when_user_not_found(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch("auth.user_manager.SessionLocal", return_value=mock_db):
            from auth.user_manager import UserManager
            um = UserManager()
            result = um.update_user(999, full_name="Ghost")
        assert result is False

    def test_update_modifies_attribute(self):
        fake_user = MagicMock()
        fake_user.id = 1

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = fake_user

        with patch("auth.user_manager.SessionLocal", return_value=mock_db):
            from auth.user_manager import UserManager
            um = UserManager()
            result = um.update_user(1, full_name="Alice Smith")
        assert result is True
        mock_db.commit.assert_called_once()

    def test_update_hashes_password(self):
        fake_user = MagicMock()
        fake_user.id = 1

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = fake_user

        with patch("auth.user_manager.SessionLocal", return_value=mock_db):
            with patch("auth.user_manager.hash_password", return_value="$2b$hashed") as mock_hp:
                from auth.user_manager import UserManager
                um = UserManager()
                um.update_user(1, password="NewPass123")
        mock_hp.assert_called_once_with("NewPass123")
        assert fake_user.hashed_password == "$2b$hashed"

    def test_update_rollbacks_on_exception(self):
        fake_user = MagicMock()
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = fake_user
        mock_db.commit.side_effect = Exception("DB crash")

        with patch("auth.user_manager.SessionLocal", return_value=mock_db):
            from auth.user_manager import UserManager
            um = UserManager()
            result = um.update_user(1, full_name="Alice")
        assert result is False
        mock_db.rollback.assert_called_once()


# ---------------------------------------------------------------------------
# UserManager.delete_user (soft delete)
# ---------------------------------------------------------------------------

class TestDeleteUser:

    def test_delete_returns_false_when_not_found(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch("auth.user_manager.SessionLocal", return_value=mock_db):
            from auth.user_manager import UserManager
            um = UserManager()
            result = um.delete_user(999)
        assert result is False

    def test_delete_sets_inactive(self):
        fake_user = MagicMock()
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = fake_user

        with patch("auth.user_manager.SessionLocal", return_value=mock_db):
            from auth.user_manager import UserManager
            um = UserManager()
            result = um.delete_user(1)
        assert result is True
        assert fake_user.is_active is False
        mock_db.commit.assert_called_once()


# ---------------------------------------------------------------------------
# UserManager.verify_user
# ---------------------------------------------------------------------------

class TestVerifyUser:

    def test_verify_returns_false_when_not_found(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch("auth.user_manager.SessionLocal", return_value=mock_db):
            from auth.user_manager import UserManager
            um = UserManager()
            result = um.verify_user(999)
        assert result is False

    def test_verify_sets_is_verified(self):
        fake_user = MagicMock()
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = fake_user

        with patch("auth.user_manager.SessionLocal", return_value=mock_db):
            from auth.user_manager import UserManager
            um = UserManager()
            result = um.verify_user(1)
        assert result is True
        assert fake_user.is_verified is True


# ---------------------------------------------------------------------------
# UserManager.change_user_role
# ---------------------------------------------------------------------------

class TestChangeUserRole:

    def test_change_role_returns_false_when_not_found(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch("auth.user_manager.SessionLocal", return_value=mock_db):
            from auth.user_manager import UserManager
            um = UserManager()
            result = um.change_user_role(999, "admin")
        assert result is False

    def test_change_role_updates_role(self):
        fake_user = MagicMock()
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = fake_user

        with patch("auth.user_manager.SessionLocal", return_value=mock_db):
            from auth.user_manager import UserManager
            um = UserManager()
            result = um.change_user_role(1, "lawyer")
        assert result is True
        assert fake_user.role == "lawyer"


# ---------------------------------------------------------------------------
# UserManager.get_all_users
# ---------------------------------------------------------------------------

class TestGetAllUsers:

    def test_returns_active_users_by_default(self):
        fake_users = [MagicMock(), MagicMock()]
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = fake_users

        with patch("auth.user_manager.SessionLocal", return_value=mock_db):
            from auth.user_manager import UserManager
            um = UserManager()
            result = um.get_all_users()
        assert result == fake_users

    def test_returns_all_users_when_active_only_false(self):
        fake_users = [MagicMock(), MagicMock(), MagicMock()]
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = fake_users

        with patch("auth.user_manager.SessionLocal", return_value=mock_db):
            from auth.user_manager import UserManager
            um = UserManager()
            result = um.get_all_users(active_only=False)
        assert result == fake_users


# ---------------------------------------------------------------------------
# UserManager.update_last_login
# ---------------------------------------------------------------------------

class TestUpdateLastLogin:

    def test_updates_last_login_for_existing_user(self):
        fake_user = MagicMock()
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = fake_user

        with patch("auth.user_manager.SessionLocal", return_value=mock_db):
            from auth.user_manager import UserManager
            um = UserManager()
            um.update_last_login(1)
        assert fake_user.last_login is not None
        mock_db.commit.assert_called_once()

    def test_skips_update_for_missing_user(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch("auth.user_manager.SessionLocal", return_value=mock_db):
            from auth.user_manager import UserManager
            um = UserManager()
            um.update_last_login(999)  # Should not raise
        mock_db.commit.assert_not_called()
