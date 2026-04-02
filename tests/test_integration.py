"""Integration tests using fixture PDFs — full pipeline end-to-end."""

import os
from decimal import Decimal

import pytest

from rothos.engine import reconstruct_basis
from rothos.parsers.irs_transcript import IrsTranscriptParser
from rothos.pdf import extract_text
from rothos.sanitize import sanitize_text


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures")


def _parse_transcript(filename: str):
    pdf_path = os.path.join(FIXTURES_DIR, filename)
    if not os.path.exists(pdf_path):
        pytest.skip(f"{filename} not available")
    text = sanitize_text(extract_text(pdf_path))
    parser = IrsTranscriptParser()
    return parser.parse(text, filename)


class TestFullPipeline:
    def test_all_four_years(self):
        """Should reconstruct basis across all 4 fixture transcripts."""
        data = [
            _parse_transcript("2020_transcript_contribution_only.pdf"),
            _parse_transcript("2021_transcript_with_8606.pdf"),
            _parse_transcript("2023_transcript_clean_backdoor.pdf"),
            _parse_transcript("2024_transcript_no_ira.pdf"),
        ]
        assert all(d is not None for d in data)

        summaries = reconstruct_basis(data)

        assert len(summaries) == 4
        assert summaries[0].tax_year == 2020
        assert summaries[1].tax_year == 2021
        assert summaries[2].tax_year == 2023
        assert summaries[3].tax_year == 2024

    def test_basis_carries_from_2020_to_2021(self):
        """2020 contribution should carry forward to 2021."""
        data = [
            _parse_transcript("2020_transcript_contribution_only.pdf"),
            _parse_transcript("2021_transcript_with_8606.pdf"),
        ]
        summaries = reconstruct_basis(data)

        # 2020: $6,000 nondeductible → basis_end = $6,000
        assert summaries[0].basis_end == Decimal("6000")

        # 2021: starts with $6,000, adds $6,000 more = $12,000 total
        assert summaries[1].basis_start == Decimal("6000")
        assert summaries[1].basis_added == Decimal("6000")

    def test_2021_conversion_uses_basis(self):
        """2021 conversion should consume basis via pro-rata."""
        data = [
            _parse_transcript("2020_transcript_contribution_only.pdf"),
            _parse_transcript("2021_transcript_with_8606.pdf"),
        ]
        summaries = reconstruct_basis(data)

        # non-taxable = 99000 - 82029 = 16971
        # But total basis = 12000, so basis_used = min(16971, 12000) = 12000
        assert summaries[1].basis_used == Decimal("12000")
        assert summaries[1].basis_end == Decimal("0")

    def test_2023_clean_backdoor(self):
        """2023 clean backdoor should show zero basis remaining."""
        data = [
            _parse_transcript("2020_transcript_contribution_only.pdf"),
            _parse_transcript("2021_transcript_with_8606.pdf"),
            _parse_transcript("2023_transcript_clean_backdoor.pdf"),
        ]
        summaries = reconstruct_basis(data)

        s2023 = summaries[2]
        assert s2023.basis_start == Decimal("0")
        assert s2023.basis_added == Decimal("6500")
        assert s2023.basis_used == Decimal("6500")
        assert s2023.basis_end == Decimal("0")

    def test_2024_no_activity_preserves_basis(self):
        """2024 with no activity should preserve whatever basis exists."""
        data = [
            _parse_transcript("2023_transcript_clean_backdoor.pdf"),
            _parse_transcript("2024_transcript_no_ira.pdf"),
        ]
        summaries = reconstruct_basis(data)

        # 2023 ends at 0, 2024 should start and end at 0
        assert summaries[1].basis_start == Decimal("0")
        assert summaries[1].basis_end == Decimal("0")

    def test_out_of_order_input(self):
        """Should handle out-of-order input and sort chronologically."""
        data = [
            _parse_transcript("2024_transcript_no_ira.pdf"),
            _parse_transcript("2020_transcript_contribution_only.pdf"),
            _parse_transcript("2023_transcript_clean_backdoor.pdf"),
            _parse_transcript("2021_transcript_with_8606.pdf"),
        ]
        summaries = reconstruct_basis(data)

        years = [s.tax_year for s in summaries]
        assert years == [2020, 2021, 2023, 2024]


class TestSanitization:
    def test_ssns_masked_in_fixture(self):
        """SSNs in fixture PDFs should already be masked (XXX-XX-NNNN format)."""
        text = extract_text(os.path.join(FIXTURES_DIR, "2021_transcript_with_8606.pdf"))
        sanitized = sanitize_text(text)
        # The fixture uses XXX-XX-1234 format — sanitizer should preserve these
        assert "XXX-XX-1234" in sanitized

    def test_dollar_amounts_preserved_after_sanitization(self):
        """Dollar amounts should not be affected by sanitization."""
        text = extract_text(os.path.join(FIXTURES_DIR, "2021_transcript_with_8606.pdf"))
        sanitized = sanitize_text(text)
        assert "$99,000.00" in sanitized
        assert "$82,029.00" in sanitized
