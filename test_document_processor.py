"""
Tests for document_processor.py — DocumentProcessor class.

Focuses on the pure validation logic in process_uploaded_file() and
_process_text_file() which don't require optional heavy dependencies.
"""

import pytest
import io
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from document_processor import DocumentProcessor


def _make_fake_file(name: str, size: int, content: bytes = b"hello world") -> MagicMock:
    """Build a minimal fake Streamlit UploadedFile stub."""
    f = MagicMock()
    f.name = name
    f.size = size
    f.read = MagicMock(return_value=content)
    f.seek = MagicMock()
    return f


class TestDocumentProcessorValidation:
    """Tests for the pure validation branches in process_uploaded_file()."""

    def setup_method(self):
        self.dp = DocumentProcessor()

    def test_returns_error_for_none_file(self):
        result = self.dp.process_uploaded_file(None)
        assert result["success"] is False
        assert "No file uploaded" in result["error"]

    def test_rejects_oversized_file(self):
        big_file = _make_fake_file("case.pdf", size=11 * 1024 * 1024)
        result = self.dp.process_uploaded_file(big_file)
        assert result["success"] is False
        assert "exceeds" in result["error"]

    def test_rejects_unsupported_extension(self):
        bad_file = _make_fake_file("case.xyz", size=1000)
        result = self.dp.process_uploaded_file(bad_file)
        assert result["success"] is False
        assert "Unsupported file format" in result["error"]

    def test_accepts_pdf_extension(self):
        # PDF processing will fail without PyMuPDF/PyPDF2 — we just assert
        # that the rejection is NOT about extension/size.
        pdf_file = _make_fake_file("case.pdf", size=100, content=b"%PDF-1.4")
        result = self.dp.process_uploaded_file(pdf_file)
        # Should NOT be an "Unsupported file format" error
        assert "Unsupported" not in result.get("error", "")

    def test_accepts_txt_extension(self):
        txt_file = _make_fake_file("facts.txt", size=50, content=b"Some legal facts here")
        result = self.dp.process_uploaded_file(txt_file)
        # Text processing should work without any optional deps
        assert result["success"] is True
        assert result["text"] == "Some legal facts here"

    def test_txt_file_preserves_content(self):
        content = b"The defendant failed to repay Rs. 500000."
        txt_file = _make_fake_file("brief.txt", size=len(content), content=content)
        result = self.dp.process_uploaded_file(txt_file)
        assert result["success"] is True
        assert "Rs. 500000" in result["text"]

    def test_txt_file_metadata_has_encoding(self):
        txt_file = _make_fake_file("facts.txt", size=20, content=b"Simple text content.")
        result = self.dp.process_uploaded_file(txt_file)
        assert result["success"] is True
        assert "encoding" in result["metadata"]

    def test_accepts_png_extension(self):
        img_file = _make_fake_file("scan.png", size=100)
        result = self.dp.process_uploaded_file(img_file)
        # Won't succeed without PIL/tesseract, but won't be rejected for format
        assert "Unsupported" not in result.get("error", "")

    def test_accepts_jpg_extension(self):
        img_file = _make_fake_file("scan.jpg", size=100)
        result = self.dp.process_uploaded_file(img_file)
        assert "Unsupported" not in result.get("error", "")

    def test_accepts_jpeg_extension(self):
        img_file = _make_fake_file("scan.jpeg", size=100)
        result = self.dp.process_uploaded_file(img_file)
        assert "Unsupported" not in result.get("error", "")

    def test_supported_formats_list(self):
        dp = DocumentProcessor()
        expected = ['.pdf', '.docx', '.doc', '.txt', '.png', '.jpg', '.jpeg']
        for fmt in expected:
            assert fmt in dp.supported_formats

    def test_max_file_size_is_10mb(self):
        dp = DocumentProcessor()
        assert dp.max_file_size == 10 * 1024 * 1024

    def test_exactly_at_size_limit_allowed(self):
        # File exactly at limit should be allowed (> check, not >=)
        at_limit = _make_fake_file("big.txt", size=10 * 1024 * 1024, content=b"x" * 100)
        result = self.dp.process_uploaded_file(at_limit)
        # Should reach text processing, not size rejection
        assert "exceeds" not in result.get("error", "")


class TestProcessTextFile:
    """Tests for _process_text_file() directly."""

    def setup_method(self):
        self.dp = DocumentProcessor()

    def _make_text_file(self, content: bytes, name: str = "test.txt") -> MagicMock:
        f = MagicMock()
        f.name = name
        f.size = len(content)
        _buf = io.BytesIO(content)
        f.read = _buf.read
        f.seek = _buf.seek
        return f

    def test_utf8_text(self):
        f = self._make_text_file(b"Hello UTF-8 world")
        result = self.dp._process_text_file(f)
        assert result["success"] is True
        assert result["text"] == "Hello UTF-8 world"
        assert result["metadata"]["encoding"] == "utf-8"

    def test_latin1_text(self):
        # "café" in latin-1 is b'\x63\x61\x66\xe9'
        content = "caf\xe9".encode("latin-1")
        f = self._make_text_file(content)
        result = self.dp._process_text_file(f)
        assert result["success"] is True
        assert result["metadata"]["encoding"] in ("utf-8", "latin-1")

    def test_empty_text_file(self):
        f = self._make_text_file(b"")
        result = self.dp._process_text_file(f)
        assert result["success"] is True
        assert result["text"] == ""

    def test_strips_whitespace(self):
        f = self._make_text_file(b"  trimmed content  ")
        result = self.dp._process_text_file(f)
        assert result["success"] is True
        assert result["text"] == "trimmed content"

    def test_metadata_processor_is_text(self):
        f = self._make_text_file(b"content")
        result = self.dp._process_text_file(f)
        assert result["metadata"]["processor"] == "text"
