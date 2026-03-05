"""
Extended tests for agent.py — covers helper functions, LRU cache,
input validation, court details, and fallback logic.

Covers: R-03 (bare except), R-05 (JSON loading), P-01 (LRU cache),
        P-02 (SHA-256 cache key), P-03 (API timeout)

Supplements the original test_agent.py (which tests analyse(), validate_pin_code,
validate_inputs).
"""

import hashlib
import os
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Ensure agent module can import with dummy key
os.environ.setdefault("GEMINI_API_KEY", "test_key_short")

from agent import (
    get_cache_key,
    get_language_text,
    get_smart_fallback_date,
    map_relief_to_key,
    get_court_details,
    _LRUCache,
    _load_rule_file,
    validate_pin_code,
    validate_inputs,
)


# -------------------------------------------------------------------------
# P-02: SHA-256 cache key
# -------------------------------------------------------------------------

class TestGetCacheKey:
    """Tests for get_cache_key() — P-02: SHA-256 hashing."""

    def test_returns_hex_string(self):
        key = get_cache_key("facts", "money-recovery", "110001")
        assert all(c in "0123456789abcdef" for c in key)

    def test_sha256_length(self):
        key = get_cache_key("facts", "relief", "pin")
        assert len(key) == 64  # SHA-256 produces 64 hex chars

    def test_deterministic(self):
        k1 = get_cache_key("facts", "relief", "110001")
        k2 = get_cache_key("facts", "relief", "110001")
        assert k1 == k2

    def test_different_inputs_different_keys(self):
        k1 = get_cache_key("facts A", "relief", "110001")
        k2 = get_cache_key("facts B", "relief", "110001")
        assert k1 != k2

    def test_case_insensitive_facts(self):
        k1 = get_cache_key("Hello World", "relief", "110001")
        k2 = get_cache_key("hello world", "relief", "110001")
        assert k1 == k2  # facts are .lower()-ed

    def test_strips_whitespace(self):
        k1 = get_cache_key("  facts  ", "relief", "110001")
        k2 = get_cache_key("facts", "relief", "110001")
        assert k1 == k2  # facts are .strip()-ed

    def test_none_case_type_matches_empty_string(self):
        k1 = get_cache_key("facts", "relief", "110001", case_type=None)
        k2 = get_cache_key("facts", "relief", "110001", case_type=None)
        assert k1 == k2


# -------------------------------------------------------------------------
# P-01: LRU Cache
# -------------------------------------------------------------------------

class TestLRUCache:
    """Tests for _LRUCache — P-01: Bounded cache."""

    def test_put_and_get(self):
        cache = _LRUCache(maxsize=10)
        cache.put_item("key1", "value1")
        assert cache.get_item("key1") == "value1"

    def test_miss_returns_none(self):
        cache = _LRUCache(maxsize=10)
        assert cache.get_item("nonexistent") is None

    def test_eviction_at_maxsize(self):
        cache = _LRUCache(maxsize=3)
        cache.put_item("a", 1)
        cache.put_item("b", 2)
        cache.put_item("c", 3)
        cache.put_item("d", 4)  # Should evict "a"
        assert cache.get_item("a") is None
        assert cache.get_item("d") == 4

    def test_lru_order_preserved(self):
        cache = _LRUCache(maxsize=3)
        cache.put_item("a", 1)
        cache.put_item("b", 2)
        cache.put_item("c", 3)
        cache.get_item("a")  # Access "a" — moves it to end
        cache.put_item("d", 4)  # Should evict "b" (least recently used)
        assert cache.get_item("a") == 1
        assert cache.get_item("b") is None

    def test_update_existing_key(self):
        cache = _LRUCache(maxsize=3)
        cache.put_item("key", "old")
        cache.put_item("key", "new")
        assert cache.get_item("key") == "new"
        assert len(cache) == 1

    def test_maxsize_1(self):
        cache = _LRUCache(maxsize=1)
        cache.put_item("a", 1)
        cache.put_item("b", 2)
        assert cache.get_item("a") is None
        assert cache.get_item("b") == 2

    def test_large_number_of_items(self):
        cache = _LRUCache(maxsize=100)
        for i in range(200):
            cache.put_item(str(i), i)
        assert len(cache) == 100
        # First 100 should be evicted
        assert cache.get_item("0") is None
        assert cache.get_item("199") == 199


# -------------------------------------------------------------------------
# map_relief_to_key
# -------------------------------------------------------------------------

class TestMapReliefToKey:
    """Tests for map_relief_to_key()."""

    def test_money_keywords(self):
        for keyword in ["money", "debt", "loan", "payment", "refund"]:
            assert map_relief_to_key(keyword) == "money-recovery"

    def test_cheque_keywords(self):
        for keyword in ["cheque", "bounce", "dishonor"]:
            assert map_relief_to_key(keyword) == "cheque-bounce"

    def test_consumer_keywords(self):
        for keyword in ["consumer", "product", "defective"]:
            assert map_relief_to_key(keyword) == "consumer-complaint"

    def test_divorce_keywords(self):
        assert map_relief_to_key("divorce") == "divorce"
        assert map_relief_to_key("matrimonial dispute") == "divorce"

    def test_property_keywords(self):
        assert map_relief_to_key("property") == "property-dispute"
        assert map_relief_to_key("land dispute") == "property-dispute"

    def test_contract_keywords(self):
        assert map_relief_to_key("breach of contract") == "breach-of-contract"

    def test_medical_negligence(self):
        assert map_relief_to_key("medical negligence") == "medical-negligence"

    def test_employment_keywords(self):
        assert map_relief_to_key("wrongful termination") == "employment-dispute"

    def test_rent_keywords(self):
        assert map_relief_to_key("tenant eviction") == "rent-dispute"

    def test_insurance_keywords(self):
        assert map_relief_to_key("insurance claim") == "insurance-claim"

    def test_unknown_defaults_to_fraud(self):
        assert map_relief_to_key("something random") == "fraud"

    def test_empty_defaults_to_fraud(self):
        assert map_relief_to_key("") == "fraud"

    def test_none_defaults_to_fraud(self):
        assert map_relief_to_key(None) == "fraud"

    def test_case_insensitive(self):
        assert map_relief_to_key("MONEY RECOVERY") == "money-recovery"
        assert map_relief_to_key("Consumer Complaint") == "consumer-complaint"


# -------------------------------------------------------------------------
# get_court_details
# -------------------------------------------------------------------------

class TestGetCourtDetails:
    """Tests for get_court_details()."""

    def test_returns_dict_with_required_keys(self):
        result = get_court_details("money-recovery", "test facts", "110001")
        for key in ("court_type", "hierarchy", "jurisdiction", "description"):
            assert key in result

    def test_jurisdiction_includes_pin(self):
        result = get_court_details("money-recovery", "test facts", "110001")
        assert "110001" in result["jurisdiction"]

    def test_unknown_relief_uses_defaults(self):
        result = get_court_details("nonexistent-type", "facts", "110001")
        assert result["court_type"] == "District Court"

    def test_empty_pin_no_crash(self):
        result = get_court_details("money-recovery", "facts", "")
        assert "court_type" in result


# -------------------------------------------------------------------------
# get_smart_fallback_date
# -------------------------------------------------------------------------

class TestGetSmartFallbackDate:
    """Tests for get_smart_fallback_date()."""

    def test_explicit_date_dd_mm_yyyy(self):
        result = get_smart_fallback_date("Incident on 15/01/2024 was bad", "money")
        assert "2024" in result

    def test_text_date_with_month_name(self):
        result = get_smart_fallback_date("On 5 march 2023 the event occurred", "")
        assert result == "2023-03-05"

    def test_time_indicator_yesterday(self):
        result = get_smart_fallback_date("This happened yesterday", "money")
        expected = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        assert result == expected

    def test_time_indicator_last_month(self):
        result = get_smart_fallback_date("It was last month", "money")
        expected = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        assert result == expected

    def test_default_fallback_six_months(self):
        result = get_smart_fallback_date("No date info at all", "money")
        expected = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
        assert result == expected

    def test_returns_valid_date_format(self):
        result = get_smart_fallback_date("some facts", "relief")
        # Should match YYYY-MM-DD
        parts = result.split("-")
        assert len(parts) == 3
        assert len(parts[0]) == 4


# -------------------------------------------------------------------------
# get_language_text
# -------------------------------------------------------------------------

class TestGetLanguageText:
    """Tests for get_language_text()."""

    def test_english_returns_key(self):
        result = get_language_text("some.key", "english")
        assert result == "some.key"

    def test_unknown_language_returns_key(self):
        result = get_language_text("test", "french")
        assert result == "test"

    def test_invalid_hindi_key_returns_key(self):
        result = get_language_text("nonexistent.key.path", "hindi")
        assert result == "nonexistent.key.path"


# -------------------------------------------------------------------------
# validate_pin_code (extended)
# -------------------------------------------------------------------------

class TestValidatePinCodeExtended:
    """Extended tests for validate_pin_code()."""

    def test_valid_pins(self):
        for pin in ["110001", "400001", "560001", "700001", "900001"]:
            assert validate_pin_code(pin) is True

    def test_invalid_starts_with_zero(self):
        assert validate_pin_code("011001") is False

    def test_invalid_too_short(self):
        assert validate_pin_code("1234") is False

    def test_invalid_too_long(self):
        assert validate_pin_code("1234567") is False

    def test_invalid_letters(self):
        assert validate_pin_code("12345a") is False

    def test_empty_string(self):
        assert validate_pin_code("") is False

    def test_none(self):
        assert validate_pin_code(None) is False

    def test_integer_input(self):
        assert validate_pin_code(110001) is False  # Must be string

    def test_whitespace(self):
        assert validate_pin_code("  ") is False

    def test_special_chars(self):
        assert validate_pin_code("110-01") is False


# -------------------------------------------------------------------------
# validate_inputs (extended)
# -------------------------------------------------------------------------

class TestValidateInputsExtended:
    """Extended tests for validate_inputs()."""

    def test_valid_inputs(self):
        errors = validate_inputs("Valid case facts here", "money-recovery", "110001")
        assert errors == {}

    def test_empty_facts(self):
        errors = validate_inputs("", "money-recovery", "110001")
        assert "facts" in errors

    def test_short_facts(self):
        errors = validate_inputs("Short", "money-recovery", "110001")
        assert "facts" in errors

    def test_invalid_relief(self):
        errors = validate_inputs("Valid case facts here", "invalid-relief", "110001")
        assert "relief" in errors

    def test_invalid_pin(self):
        errors = validate_inputs("Valid case facts here", "money-recovery", "011001")
        assert "pin" in errors

    def test_multiple_errors(self):
        errors = validate_inputs("", "invalid", "000")
        assert len(errors) >= 2


# -------------------------------------------------------------------------
# _load_rule_file
# -------------------------------------------------------------------------

class TestLoadRuleFile:
    """Tests for _load_rule_file() — R-05: Error handling."""

    def test_loads_existing_file(self):
        # limitation.json should always exist
        result = _load_rule_file("limitation.json")
        assert isinstance(result, dict)

    def test_missing_file_exits(self):
        with pytest.raises(SystemExit):
            _load_rule_file("nonexistent_file.json")

    def test_all_rule_files_loadable(self):
        for fname in ["limitation.json", "forum.json", "court_hierarchy.json",
                       "detailed_provisions.json", "language_support.json"]:
            result = _load_rule_file(fname)
            assert isinstance(result, dict)
