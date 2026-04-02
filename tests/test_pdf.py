"""Tests for PDF text extraction."""

import os

import pytest

from rothos.pdf import extract_text


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures")


def test_extract_text_from_tax_return_transcript():
    """Should extract readable text from a tax return transcript PDF."""
    pdf_path = os.path.join(FIXTURES_DIR, "2021_transcript_with_8606.pdf")
    if not os.path.exists(pdf_path):
        pytest.skip("Fixture PDF not available")

    text = extract_text(pdf_path)

    assert "Form 1040 Tax Return Transcript" in text
    assert "Total IRA distributions" in text


def test_extract_text_nonexistent_file():
    """Should raise FileNotFoundError for missing files."""
    with pytest.raises(FileNotFoundError):
        extract_text("/nonexistent/file.pdf")


def test_extract_text_returns_string():
    """Should return a string with substantial content."""
    pdf_path = os.path.join(FIXTURES_DIR, "2021_transcript_with_8606.pdf")
    if not os.path.exists(pdf_path):
        pytest.skip("Fixture PDF not available")

    result = extract_text(pdf_path)
    assert isinstance(result, str)
    assert len(result) > 100
