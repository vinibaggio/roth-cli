"""Tests for text sanitization."""

from rothos.sanitize import sanitize_text


def test_sanitize_ssn_dashed():
    """Should mask SSNs in XXX-XX-1234 format."""
    text = "SSN: 123-45-6789"
    result = sanitize_text(text)
    assert "123-45-6789" not in result
    assert "XXX-XX-6789" in result


def test_sanitize_ssn_already_masked():
    """Should not modify already-masked SSNs."""
    text = "SSN: XXX-XX-9895"
    result = sanitize_text(text)
    assert "XXX-XX-9895" in result


def test_sanitize_ssn_nine_digits():
    """Should mask contiguous 9-digit numbers that look like SSNs."""
    text = "SSN: 123456789"
    result = sanitize_text(text)
    assert "123456789" not in result
    assert "XXXXX6789" in result


def test_sanitize_preserves_dollar_amounts():
    """Should not mask dollar amounts."""
    text = "Total IRA distributions: $99,691.00"
    result = sanitize_text(text)
    assert "$99,691.00" in result


def test_sanitize_preserves_other_numbers():
    """Should not mask tracking numbers or other long numbers."""
    text = "Tracking Number: 109211206692"
    result = sanitize_text(text)
    assert "109211206692" in result


def test_sanitize_multiple_ssns():
    """Should mask multiple SSNs in the same text."""
    text = "SSN: 123-45-6789\nSpouse SSN: 987-65-4321"
    result = sanitize_text(text)
    assert "XXX-XX-6789" in result
    assert "XXX-XX-4321" in result


def test_sanitize_preserves_transcript_structure():
    """Should preserve the overall structure of a transcript."""
    text = """Form 1040 Tax Return Transcript
SSN provided:
123-45-6789
Total IRA distributions:
$99,691.00
"""
    result = sanitize_text(text)
    assert "Form 1040 Tax Return Transcript" in result
    assert "$99,691.00" in result
    assert "XXX-XX-6789" in result
