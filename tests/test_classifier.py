"""Tests for document classification."""

from rothos.parsers.classifier import classify


def test_classify_irs_tax_return_transcript():
    """Should identify IRS Tax Return Transcript."""
    text = """
    This Product Contains Sensitive Taxpayer Data
    Form 1040 Tax Return Transcript
    Request Date: 11-24-2025
    """
    result = classify(text)
    assert result == "irs_tax_return_transcript"


def test_classify_unknown():
    """Should return None for unrecognized documents."""
    text = "This is just some random text."
    result = classify(text)
    assert result is None


def test_classify_irs_transcript_with_8606():
    """Should still classify as IRS transcript even with Form 8606 section."""
    text = """
    Form 1040 Tax Return Transcript
    Form 8606 - Nondeductible IRAs (Occurrence #: 1)
    """
    result = classify(text)
    assert result == "irs_tax_return_transcript"


def test_classify_partial_match():
    """Should match even with just the key header."""
    text = "Form 1040 Tax Return Transcript\nSome other content"
    result = classify(text)
    assert result == "irs_tax_return_transcript"
