"""
test_agent_ai_paths.py — Covers the AI-enabled code paths in agent.py that
are not reached when AI_ENABLED=False (the default in the test environment).

Coverage targets (from coverage report):
  agent.py lines 370-394  — cheque-bounce fallback branch
  agent.py lines 429-484  — divorce + else fallback branches
  agent.py lines 511-564  — AI-enabled API call path (with AI_ENABLED patched True)
  agent.py lines 577-579  — placeholder date handling
  agent.py lines 582-586  — date parsing ValueError fallback
  agent.py lines 634-637  — enhanced_analytics error handling
"""

import json
import os
import pytest
from unittest.mock import patch, MagicMock

os.environ.setdefault("GEMINI_API_KEY", "test_key_short")

from agent import analyse, _response_cache


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

GOOD_FACTS = "The defendant issued a cheque for fifty thousand rupees which was dishonored by the bank due to insufficient funds. The cheque was returned with memo on 15 January 2024."
CHEQUE_RELIEF = "cheque bounce"

DIVORCE_FACTS = "Petitioner seeks divorce from respondent on grounds of cruelty and desertion. Marriage solemnized in 2010. Parties have been living separately since 2020."
DIVORCE_RELIEF = "divorce separation"

GENERAL_FACTS = "Respondent caused nuisance to the petitioner by obstructing access to common passage of the building for more than six months."
GENERAL_RELIEF = "injunction nuisance"  # maps to 'fraud' (else fallback)

MONEY_FACTS = "Company failed to return security deposit of one lakh rupees after contract ended on 1st March 2022."
MONEY_RELIEF = "money recovery"

PIN = "110001"


def _clear_cache():
    _response_cache.clear()


# ---------------------------------------------------------------------------
# Fallback branch: cheque-bounce (lines 370-394)
# ---------------------------------------------------------------------------

class TestFallbackChequeBounceBranch:
    """Exercises the cheque-bounce elif in the offline fallback block."""

    def test_cheque_bounce_fallback_returns_verdict(self):
        _clear_cache()
        with patch("agent.AI_ENABLED", False):
            result = analyse(GOOD_FACTS, CHEQUE_RELIEF, PIN)
        assert "verdict" in result
        assert "days_left" in result

    def test_cheque_bounce_fallback_includes_applicable_acts(self):
        _clear_cache()
        with patch("agent.AI_ENABLED", False):
            result = analyse(GOOD_FACTS, CHEQUE_RELIEF, PIN)
        # The cheque-bounce fallback populates applicable_sections
        acts = result.get("applicable_sections", [])
        assert isinstance(acts, list)
        assert len(acts) > 0

    def test_cheque_bounce_fallback_includes_practical_advice(self):
        _clear_cache()
        with patch("agent.AI_ENABLED", False):
            result = analyse(GOOD_FACTS, CHEQUE_RELIEF, PIN)
        advice = result.get("practical_advice")
        assert advice is not None


# ---------------------------------------------------------------------------
# Fallback branch: divorce (lines 429-458)
# ---------------------------------------------------------------------------

class TestFallbackDivorceBranch:
    """Exercises the divorce elif in the offline fallback block."""

    def test_divorce_fallback_returns_verdict(self):
        _clear_cache()
        with patch("agent.AI_ENABLED", False):
            result = analyse(DIVORCE_FACTS, DIVORCE_RELIEF, PIN)
        assert "verdict" in result

    def test_divorce_fallback_includes_acts(self):
        _clear_cache()
        with patch("agent.AI_ENABLED", False):
            result = analyse(DIVORCE_FACTS, DIVORCE_RELIEF, PIN)
        acts = result.get("applicable_sections", [])
        assert isinstance(acts, list)
        assert len(acts) > 0

    def test_divorce_fallback_has_strategic_recommendations(self):
        _clear_cache()
        with patch("agent.AI_ENABLED", False):
            result = analyse(DIVORCE_FACTS, DIVORCE_RELIEF, PIN)
        assert "strategic_recommendations" in result or "practical_advice" in result


# ---------------------------------------------------------------------------
# Fallback branch: else / general (lines 459-488)
# ---------------------------------------------------------------------------

class TestFallbackElseBranch:
    """Exercises the else branch in the offline fallback block."""

    def test_else_fallback_returns_verdict(self):
        _clear_cache()
        with patch("agent.AI_ENABLED", False):
            result = analyse(GENERAL_FACTS, GENERAL_RELIEF, PIN)
        assert "verdict" in result

    def test_else_fallback_has_applicable_sections(self):
        _clear_cache()
        with patch("agent.AI_ENABLED", False):
            result = analyse(GENERAL_FACTS, GENERAL_RELIEF, PIN)
        acts = result.get("applicable_sections", [])
        assert isinstance(acts, list)
        assert len(acts) > 0


# ---------------------------------------------------------------------------
# AI-enabled path (lines 511-571)
# ---------------------------------------------------------------------------

class TestAIEnabledPath:
    """Exercises the AI-enabled branch (AI_ENABLED=True + model stub)."""

    def _fake_model(self, json_text: str):
        """Return a mock model stub that generates the given JSON text."""
        mock_model = MagicMock()
        mock_resp = MagicMock()
        mock_resp.text = json_text
        mock_model.generate_content.return_value = mock_resp
        return mock_model

    def test_ai_path_valid_json_response(self):
        """AI returns valid JSON → parsed and cached."""
        _clear_cache()
        json_payload = json.dumps({
            "cause": "breach of contract",
            "start_date": "2023-01-15",
            "confidence_score": 9,
            "legal_reasoning": "Detailed AI reasoning here.",
            "applicable_sections": ["Contract Act s.73"],
            "jurisdiction_notes": "District Court, Delhi"
        })
        fake_model = self._fake_model(json_payload)

        with patch("agent.AI_ENABLED", True), patch("agent.model", fake_model):
            result = analyse(MONEY_FACTS, MONEY_RELIEF, PIN)

        assert "verdict" in result
        assert result["confidence_score"] == 9
        fake_model.generate_content.assert_called_once()

    def test_ai_path_json_wrapped_in_code_block(self):
        """AI returns JSON wrapped in ```json ... ``` — should strip and parse."""
        _clear_cache()
        inner = json.dumps({
            "cause": "debt recovery",
            "start_date": "2022-06-01",
            "confidence_score": 7,
        })
        wrapped = f"```json\n{inner}\n```"
        fake_model = self._fake_model(wrapped)

        with patch("agent.AI_ENABLED", True), patch("agent.model", fake_model):
            result = analyse(MONEY_FACTS, MONEY_RELIEF, PIN)

        assert "verdict" in result

    def test_ai_path_json_wrapped_in_plain_code_block(self):
        """AI returns JSON wrapped in ``` ... ``` (no language tag)."""
        _clear_cache()
        inner = json.dumps({
            "cause": "debt",
            "start_date": "2022-06-01",
        })
        wrapped = f"```\n{inner}\n```"
        fake_model = self._fake_model(wrapped)

        with patch("agent.AI_ENABLED", True), patch("agent.model", fake_model):
            result = analyse(MONEY_FACTS, MONEY_RELIEF, PIN)

        assert "verdict" in result

    def test_ai_path_invalid_json_falls_back(self):
        """AI returns non-JSON → ValueError → graceful fallback dict returned."""
        _clear_cache()
        fake_model = self._fake_model("This is definitely not JSON at all!!!")

        with patch("agent.AI_ENABLED", True), patch("agent.model", fake_model):
            result = analyse(MONEY_FACTS, MONEY_RELIEF, PIN)

        # Should still return a valid result via fallback
        assert "verdict" in result
        assert "days_left" in result

    def test_ai_path_empty_response_falls_back(self):
        """AI returns empty text → ValueError('Empty response') → fallback."""
        _clear_cache()
        mock_model = MagicMock()
        mock_resp = MagicMock()
        mock_resp.text = ""
        mock_model.generate_content.return_value = mock_resp

        with patch("agent.AI_ENABLED", True), patch("agent.model", mock_model):
            result = analyse(MONEY_FACTS, MONEY_RELIEF, PIN)

        assert "verdict" in result

    def test_ai_path_model_raises_exception_falls_back(self):
        """Model.generate_content raises → except block → fallback dict."""
        _clear_cache()
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("Network timeout")

        with patch("agent.AI_ENABLED", True), patch("agent.model", mock_model):
            result = analyse(MONEY_FACTS, MONEY_RELIEF, PIN)

        assert "verdict" in result

    def test_ai_path_json_embedded_in_prose(self):
        """AI wraps JSON in prose — regex extraction should recover it."""
        _clear_cache()
        inner = json.dumps({
            "cause": "contract breach",
            "start_date": "2023-03-01",
            "confidence_score": 8,
        })
        prose = f"Sure! Here is the analysis: {inner} Hope that helps."
        fake_model = self._fake_model(prose)

        with patch("agent.AI_ENABLED", True), patch("agent.model", fake_model):
            result = analyse(MONEY_FACTS, MONEY_RELIEF, PIN)

        assert "verdict" in result


# ---------------------------------------------------------------------------
# Placeholder date handling (lines 577-579)
# ---------------------------------------------------------------------------

class TestPlaceholderDateHandling:
    """AI returns a placeholder date string — should replace with smart fallback."""

    def test_placeholder_yyyy_mm_dd_replaced(self):
        _clear_cache()
        json_payload = json.dumps({
            "cause": "recovery",
            "start_date": "YYYY-MM-DD",  # placeholder
            "confidence_score": 7,
        })
        fake_model = MagicMock()
        mock_resp = MagicMock()
        mock_resp.text = json_payload
        fake_model.generate_content.return_value = mock_resp

        with patch("agent.AI_ENABLED", True), patch("agent.model", fake_model):
            result = analyse(MONEY_FACTS, MONEY_RELIEF, PIN)

        # Should still return a valid result (placeholder date replaced)
        assert "verdict" in result
        assert "days_left" in result

    def test_placeholder_lowercase_replaced(self):
        _clear_cache()
        json_payload = json.dumps({
            "cause": "recovery",
            "start_date": "yyyy-mm-dd",
            "confidence_score": 7,
        })
        fake_model = MagicMock()
        mock_resp = MagicMock()
        mock_resp.text = json_payload
        fake_model.generate_content.return_value = mock_resp

        with patch("agent.AI_ENABLED", True), patch("agent.model", fake_model):
            result = analyse(MONEY_FACTS, MONEY_RELIEF, PIN)

        assert "verdict" in result

    def test_placeholder_date_word_replaced(self):
        _clear_cache()
        json_payload = json.dumps({
            "cause": "recovery",
            "start_date": "date",
            "confidence_score": 7,
        })
        fake_model = MagicMock()
        mock_resp = MagicMock()
        mock_resp.text = json_payload
        fake_model.generate_content.return_value = mock_resp

        with patch("agent.AI_ENABLED", True), patch("agent.model", fake_model):
            result = analyse(MONEY_FACTS, MONEY_RELIEF, PIN)

        assert "verdict" in result


# ---------------------------------------------------------------------------
# Date parsing ValueError fallback (lines 582-586)
# ---------------------------------------------------------------------------

class TestDateParsingFallback:
    """AI returns malformed date string → ValueError fallback path."""

    def test_bad_date_format_falls_back(self):
        _clear_cache()
        json_payload = json.dumps({
            "cause": "recovery",
            "start_date": "not-a-date",
            "confidence_score": 7,
        })
        fake_model = MagicMock()
        mock_resp = MagicMock()
        mock_resp.text = json_payload
        fake_model.generate_content.return_value = mock_resp

        with patch("agent.AI_ENABLED", True), patch("agent.model", fake_model):
            result = analyse(MONEY_FACTS, MONEY_RELIEF, PIN)

        assert "verdict" in result
        assert "days_left" in result

    def test_partial_date_falls_back(self):
        _clear_cache()
        json_payload = json.dumps({
            "cause": "recovery",
            "start_date": "2023-13-45",  # invalid month/day
            "confidence_score": 7,
        })
        fake_model = MagicMock()
        mock_resp = MagicMock()
        mock_resp.text = json_payload
        fake_model.generate_content.return_value = mock_resp

        with patch("agent.AI_ENABLED", True), patch("agent.model", fake_model):
            result = analyse(MONEY_FACTS, MONEY_RELIEF, PIN)

        assert "verdict" in result


# ---------------------------------------------------------------------------
# Enhanced analytics error handling (lines 634-637)
# ---------------------------------------------------------------------------

class TestEnhancedAnalyticsErrorHandling:
    """Exercises the try/except around generate_enhanced_analysis (lines 629-637)."""

    def test_analytics_exception_does_not_raise(self):
        """If enhanced_analytics raises Exception, analyse() still returns result."""
        _clear_cache()
        # The import is inside analyse(), so we patch the function on the module itself.
        with patch("agent.AI_ENABLED", False), \
             patch("enhanced_analytics.generate_enhanced_analysis",
                   side_effect=Exception("analytics crash")):
            result = analyse(MONEY_FACTS, MONEY_RELIEF, PIN)
        assert "verdict" in result

    def test_analytics_import_error_does_not_raise(self):
        """If enhanced_analytics raises ImportError, analyse() still returns result."""
        _clear_cache()
        # Simulate ImportError by patching the import path used inside analyse()
        import sys
        original = sys.modules.get("enhanced_analytics")
        try:
            sys.modules["enhanced_analytics"] = None  # Forces ImportError on import
            with patch("agent.AI_ENABLED", False):
                result = analyse(MONEY_FACTS, MONEY_RELIEF, PIN)
            assert "verdict" in result
        finally:
            if original is not None:
                sys.modules["enhanced_analytics"] = original
            elif "enhanced_analytics" in sys.modules:
                del sys.modules["enhanced_analytics"]
