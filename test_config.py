"""
Tests for config.py — Centralized AppConfig with startup validation.

Covers: Op-02 (Centralized config with env validation)
"""

import os
import pytest
from unittest.mock import patch, MagicMock


class TestRequire:
    """Tests for _require() validation helper."""

    def test_returns_value_when_set(self):
        from config import _require
        with patch.dict(os.environ, {"MY_VAR": "hello"}):
            assert _require("MY_VAR") == "hello"

    def test_exits_when_not_set(self):
        from config import _require
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("MY_VAR", None)
            with pytest.raises(SystemExit):
                _require("MY_VAR")

    def test_exits_when_empty(self):
        from config import _require
        with patch.dict(os.environ, {"MY_VAR": "   "}):
            with pytest.raises(SystemExit):
                _require("MY_VAR")


class TestOptional:
    """Tests for _optional() helper."""

    def test_returns_value_when_set(self):
        from config import _optional
        with patch.dict(os.environ, {"OPT_VAR": "value"}):
            assert _optional("OPT_VAR") == "value"

    def test_returns_default_when_not_set(self):
        from config import _optional
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("OPT_VAR", None)
            assert _optional("OPT_VAR", "default") == "default"

    def test_strips_whitespace(self):
        from config import _optional
        with patch.dict(os.environ, {"OPT_VAR": "  value  "}):
            assert _optional("OPT_VAR") == "value"


class TestOptionalInt:
    """Tests for _optional_int() helper."""

    def test_parses_integer(self):
        from config import _optional_int
        with patch.dict(os.environ, {"INT_VAR": "42"}):
            assert _optional_int("INT_VAR", 0) == 42

    def test_returns_default_when_not_set(self):
        from config import _optional_int
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("INT_VAR", None)
            assert _optional_int("INT_VAR", 99) == 99

    def test_returns_default_for_invalid_int(self):
        from config import _optional_int
        with patch.dict(os.environ, {"INT_VAR": "not_a_number"}):
            assert _optional_int("INT_VAR", 10) == 10


class TestAppConfig:
    """Tests for AppConfig dataclass."""

    def test_is_production(self):
        from config import AppConfig
        cfg = AppConfig(gemini_api_key="k" * 30, cookie_secret="s" * 32, environment="production")
        assert cfg.is_production is True
        assert cfg.is_development is False

    def test_is_development(self):
        from config import AppConfig
        cfg = AppConfig(gemini_api_key="k" * 30, cookie_secret="s" * 32, environment="development")
        assert cfg.is_development is True
        assert cfg.is_production is False

    def test_ai_enabled_with_valid_key(self):
        from config import AppConfig
        cfg = AppConfig(gemini_api_key="a" * 40, cookie_secret="s" * 32)
        assert cfg.ai_enabled is True

    def test_ai_disabled_with_short_key(self):
        from config import AppConfig
        cfg = AppConfig(gemini_api_key="short", cookie_secret="s" * 32)
        assert cfg.ai_enabled is False

    def test_ai_disabled_with_placeholder(self):
        from config import AppConfig
        cfg = AppConfig(gemini_api_key="your_gemini_api_key_here", cookie_secret="s" * 32)
        assert cfg.ai_enabled is False

    def test_ai_disabled_with_enter_you_prefix(self):
        from config import AppConfig
        cfg = AppConfig(gemini_api_key="<ENTER_YOUR_KEY_HERE>_padding_more_chars", cookie_secret="s" * 32)
        assert cfg.ai_enabled is False

    def test_frozen_dataclass(self):
        from config import AppConfig
        cfg = AppConfig(gemini_api_key="k" * 30, cookie_secret="s" * 32)
        with pytest.raises(AttributeError):
            cfg.environment = "staging"  # type: ignore[misc]

    def test_secrets_not_in_repr(self):
        from config import AppConfig
        cfg = AppConfig(gemini_api_key="supersecretkey" * 3, cookie_secret="cookie_secret_val" * 3)
        r = repr(cfg)
        assert "supersecretkey" not in r
        assert "cookie_secret_val" not in r


class TestSettingsSingleton:
    """Tests for the settings singleton."""

    def test_settings_is_app_config_instance(self):
        from config import settings, AppConfig
        assert isinstance(settings, AppConfig)

    def test_settings_has_cookie_secret(self):
        from config import settings
        assert len(settings.cookie_secret) > 0
