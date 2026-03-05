"""
test_user_manager_extended.py — Covers uncovered lines in auth/user_manager.py:
  Lines 104-107: delete_user exception rollback
  Lines 118-148: get_user_statistics (happy path + error)
  Lines 162-165: verify_user exception rollback
  Lines 179-182: change_user_role exception rollback
  Lines 186-187: search_users
  Lines 195: get_users_by_role
  Lines 207-209: update_last_login exception rollback
"""

import pytest
from unittest.mock import MagicMock, patch
import streamlit as st


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_um(mock_db=None):
    """Create a UserManager with an injected mock DB session."""
    from auth.user_manager import UserManager
    um = UserManager.__new__(UserManager)
    um.db = mock_db or MagicMock()
    return um


def _fake_user(user_id=1, username="alice", email="alice@example.com",
               is_active=True, role="user"):
    u = MagicMock()
    u.id = user_id
    u.username = username
    u.email = email
    u.is_active = is_active
    u.role = role
    u.created_at = None
    u.last_login = None
    return u


# ---------------------------------------------------------------------------
# delete_user — exception path (lines 104-107)
# ---------------------------------------------------------------------------

class TestDeleteUserException:

    def test_rollback_on_db_exception(self):
        mock_db = MagicMock()
        um = _make_um(mock_db)
        # Patch get_user_by_id to return a fake user
        fake = _fake_user()
        um.get_user_by_id = MagicMock(return_value=fake)
        # Make commit raise
        mock_db.commit.side_effect = Exception("DB crash")

        # Patch User model so column comparisons don't raise
        mock_u = MagicMock()
        with patch("auth.user_manager.User", mock_u):
            result = um.delete_user(1)

        assert result is False
        mock_db.rollback.assert_called_once()


# ---------------------------------------------------------------------------
# get_user_statistics (lines 118-148)
# ---------------------------------------------------------------------------

class TestGetUserStatistics:

    def test_returns_empty_dict_when_user_not_found(self):
        mock_db = MagicMock()
        um = _make_um(mock_db)
        um.get_user_by_id = MagicMock(return_value=None)

        result = um.get_user_statistics(99)
        assert result == {}

    def test_returns_stats_dict_for_existing_user(self):
        mock_db = MagicMock()
        um = _make_um(mock_db)
        fake = _fake_user()
        um.get_user_by_id = MagicMock(return_value=fake)

        # query(...).filter(...).count() for total_cases, active_cases, completed_cases
        # query(...).join(...).filter(...).count() for total_analyses
        mock_db.query.return_value.filter.return_value.count.return_value = 5
        mock_db.query.return_value.join.return_value.filter.return_value.count.return_value = 3

        mock_u = MagicMock()
        mock_case = MagicMock()
        mock_analysis = MagicMock()
        with patch("auth.user_manager.User", mock_u), \
             patch("auth.user_manager.Case", mock_case), \
             patch("auth.user_manager.Analysis", mock_analysis):
            result = um.get_user_statistics(1)

        assert isinstance(result, dict)
        assert "total_cases" in result
        assert "total_analyses" in result

    def test_returns_empty_dict_on_db_exception(self):
        mock_db = MagicMock()
        um = _make_um(mock_db)
        fake = _fake_user()
        um.get_user_by_id = MagicMock(return_value=fake)
        mock_db.query.side_effect = Exception("DB crash")

        mock_u = MagicMock()
        mock_case = MagicMock()
        mock_analysis = MagicMock()
        with patch("auth.user_manager.User", mock_u), \
             patch("auth.user_manager.Case", mock_case), \
             patch("auth.user_manager.Analysis", mock_analysis):
            result = um.get_user_statistics(1)

        assert result == {}

    def test_formats_last_login_when_present(self):
        from datetime import datetime
        mock_db = MagicMock()
        um = _make_um(mock_db)
        fake = _fake_user()
        fake.last_login = datetime(2024, 6, 15, 10, 30)
        fake.created_at = datetime(2023, 1, 1)
        um.get_user_by_id = MagicMock(return_value=fake)
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        mock_db.query.return_value.join.return_value.filter.return_value.count.return_value = 0

        mock_u = MagicMock()
        mock_case = MagicMock()
        mock_analysis = MagicMock()
        with patch("auth.user_manager.User", mock_u), \
             patch("auth.user_manager.Case", mock_case), \
             patch("auth.user_manager.Analysis", mock_analysis):
            result = um.get_user_statistics(1)

        assert result.get("last_login") != "Never"

    def test_last_login_never_when_none(self):
        mock_db = MagicMock()
        um = _make_um(mock_db)
        fake = _fake_user()
        fake.last_login = None
        um.get_user_by_id = MagicMock(return_value=fake)
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        mock_db.query.return_value.join.return_value.filter.return_value.count.return_value = 0

        mock_u = MagicMock()
        mock_case = MagicMock()
        mock_analysis = MagicMock()
        with patch("auth.user_manager.User", mock_u), \
             patch("auth.user_manager.Case", mock_case), \
             patch("auth.user_manager.Analysis", mock_analysis):
            result = um.get_user_statistics(1)

        assert result.get("last_login") == "Never"


# ---------------------------------------------------------------------------
# verify_user — exception path (lines 162-165)
# ---------------------------------------------------------------------------

class TestVerifyUserException:

    def test_rollback_on_db_exception(self):
        mock_db = MagicMock()
        um = _make_um(mock_db)
        fake = _fake_user()
        um.get_user_by_id = MagicMock(return_value=fake)
        mock_db.commit.side_effect = Exception("DB crash")

        result = um.verify_user(1)
        assert result is False
        mock_db.rollback.assert_called_once()


# ---------------------------------------------------------------------------
# change_user_role — exception path (lines 179-182)
# ---------------------------------------------------------------------------

class TestChangeUserRoleException:

    def test_rollback_on_db_exception(self):
        mock_db = MagicMock()
        um = _make_um(mock_db)
        fake = _fake_user()
        um.get_user_by_id = MagicMock(return_value=fake)
        mock_db.commit.side_effect = Exception("DB crash")

        result = um.change_user_role(1, "admin")
        assert result is False
        mock_db.rollback.assert_called_once()

    def test_returns_false_when_user_not_found(self):
        mock_db = MagicMock()
        um = _make_um(mock_db)
        um.get_user_by_id = MagicMock(return_value=None)

        result = um.change_user_role(999, "admin")
        assert result is False


# ---------------------------------------------------------------------------
# search_users (lines 184-191)
# ---------------------------------------------------------------------------

class TestSearchUsers:

    def test_returns_list_from_query(self):
        mock_db = MagicMock()
        um = _make_um(mock_db)
        fake_users = [_fake_user(1), _fake_user(2)]
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = fake_users

        mock_u = MagicMock()
        with patch("auth.user_manager.User", mock_u):
            result = um.search_users("alice")

        assert result == fake_users

    def test_returns_empty_list_for_no_match(self):
        mock_db = MagicMock()
        um = _make_um(mock_db)
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = []

        mock_u = MagicMock()
        with patch("auth.user_manager.User", mock_u):
            result = um.search_users("nobody")

        assert result == []


# ---------------------------------------------------------------------------
# get_users_by_role (lines 193-198)
# ---------------------------------------------------------------------------

class TestGetUsersByRole:

    def test_returns_users_for_role(self):
        mock_db = MagicMock()
        um = _make_um(mock_db)
        fake_users = [_fake_user(role="admin")]
        mock_db.query.return_value.filter.return_value.all.return_value = fake_users

        mock_u = MagicMock()
        with patch("auth.user_manager.User", mock_u):
            result = um.get_users_by_role("admin")

        assert result == fake_users

    def test_returns_empty_list_when_no_users(self):
        mock_db = MagicMock()
        um = _make_um(mock_db)
        mock_db.query.return_value.filter.return_value.all.return_value = []

        mock_u = MagicMock()
        with patch("auth.user_manager.User", mock_u):
            result = um.get_users_by_role("superadmin")

        assert result == []


# ---------------------------------------------------------------------------
# update_last_login — exception path (lines 207-209)
# ---------------------------------------------------------------------------

class TestUpdateLastLoginException:

    def test_rollback_on_db_exception(self):
        mock_db = MagicMock()
        um = _make_um(mock_db)
        fake = _fake_user()
        um.get_user_by_id = MagicMock(return_value=fake)
        mock_db.commit.side_effect = Exception("DB crash")

        # Should not raise
        um.update_last_login(1)
        mock_db.rollback.assert_called_once()
