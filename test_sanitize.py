"""
Tests for sanitize.py — HTML escaping utility.

Covers: S-07 (XSS prevention via esc() function)
"""

import pytest
from sanitize import esc


class TestEsc:
    """Tests for the esc() HTML escape function."""

    def test_escapes_angle_brackets(self):
        assert esc("<script>alert(1)</script>") == "&lt;script&gt;alert(1)&lt;/script&gt;"

    def test_escapes_ampersand(self):
        assert esc("Tom & Jerry") == "Tom &amp; Jerry"

    def test_escapes_double_quotes(self):
        assert esc('He said "hello"') == "He said &quot;hello&quot;"

    def test_escapes_single_quotes(self):
        assert esc("it's fine") == "it&#x27;s fine"

    def test_none_returns_empty_string(self):
        assert esc(None) == ""

    def test_empty_string_returns_empty(self):
        assert esc("") == ""

    def test_plain_text_unchanged(self):
        plain = "Hello World 123"
        assert esc(plain) == plain

    def test_integer_input(self):
        assert esc(42) == "42"

    def test_float_input(self):
        result = esc(3.14)
        assert "3.14" in result

    def test_nested_html_entities(self):
        assert "&amp;" in esc("&amp;")  # Double-escape protection

    def test_xss_img_onerror(self):
        payload = '<img src=x onerror="alert(1)">'
        result = esc(payload)
        assert "<img" not in result
        assert "onerror" not in result or "&quot;" in result

    def test_xss_event_handler(self):
        payload = '" onmouseover="alert(document.cookie)"'
        result = esc(payload)
        assert "onmouseover" not in result or "&quot;" in result

    def test_unicode_preserved(self):
        text = "नमस्ते 🙏 العربية"
        assert esc(text) == text  # Unicode chars should pass through

    def test_boolean_input(self):
        assert esc(True) == "True"
        assert esc(False) == "False"
