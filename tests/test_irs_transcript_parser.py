"""Tests for IRS Tax Return Transcript parser."""

import os
from decimal import Decimal

import pytest

from rothos.parsers.irs_transcript import IrsTranscriptParser
from rothos.pdf import extract_text


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures")


@pytest.fixture
def parser():
    return IrsTranscriptParser()


@pytest.fixture
def text_2021():
    pdf_path = os.path.join(FIXTURES_DIR, "2021_transcript_with_8606.pdf")
    if not os.path.exists(pdf_path):
        pytest.skip("Fixture PDF not available")
    return extract_text(pdf_path)


@pytest.fixture
def text_2024():
    pdf_path = os.path.join(FIXTURES_DIR, "2024_transcript_no_ira.pdf")
    if not os.path.exists(pdf_path):
        pytest.skip("Fixture PDF not available")
    return extract_text(pdf_path)


@pytest.fixture
def text_2023():
    pdf_path = os.path.join(FIXTURES_DIR, "2023_transcript_clean_backdoor.pdf")
    if not os.path.exists(pdf_path):
        pytest.skip("Fixture PDF not available")
    return extract_text(pdf_path)


@pytest.fixture
def text_2020():
    pdf_path = os.path.join(FIXTURES_DIR, "2020_transcript_contribution_only.pdf")
    if not os.path.exists(pdf_path):
        pytest.skip("Fixture PDF not available")
    return extract_text(pdf_path)


class TestCanParse:
    def test_recognizes_irs_transcript(self, parser, text_2021):
        assert parser.can_parse(text_2021) is True

    def test_rejects_random_text(self, parser):
        assert parser.can_parse("This is not a tax return.") is False


class TestParse2021WithDistributions:
    """2021 transcript has IRA distributions and Form 8606."""

    def test_extracts_tax_year(self, parser, text_2021):
        result = parser.parse(text_2021, "2021_transcript.pdf")
        assert result is not None
        assert result.tax_year == 2021

    def test_extracts_ira_distributions(self, parser, text_2021):
        result = parser.parse(text_2021, "2021_transcript.pdf")
        assert result.total_ira_distributions == Decimal("99000.00")
        assert result.taxable_ira_distributions == Decimal("82029.00")

    def test_extracts_ira_deduction(self, parser, text_2021):
        result = parser.parse(text_2021, "2021_transcript.pdf")
        assert result.ira_deduction == Decimal("0.00")

    def test_detects_form_8606(self, parser, text_2021):
        result = parser.parse(text_2021, "2021_transcript.pdf")
        assert result.has_8606 is True

    def test_extracts_8606_fields(self, parser, text_2021):
        result = parser.parse(text_2021, "2021_transcript.pdf")
        assert result.nondeductible_contributions == Decimal("6000.00")
        assert result.conversion_amount == Decimal("99000.00")
        assert result.total_basis == Decimal("18000.00")
        assert result.taxable_conversion_amount == Decimal("82029.00")
        assert result.total_distributions_8606 == Decimal("99000.00")

    def test_has_ira_activity(self, parser, text_2021):
        result = parser.parse(text_2021, "2021_transcript.pdf")
        assert result.has_ira_activity is True


class TestParse2024NoIraActivity:
    """2024 transcript has no IRA distributions and no Form 8606."""

    def test_extracts_tax_year(self, parser, text_2024):
        result = parser.parse(text_2024, "2024_transcript.pdf")
        assert result is not None
        assert result.tax_year == 2024

    def test_zero_ira_distributions(self, parser, text_2024):
        result = parser.parse(text_2024, "2024_transcript.pdf")
        assert result.total_ira_distributions == Decimal("0.00")
        assert result.taxable_ira_distributions == Decimal("0.00")

    def test_no_form_8606(self, parser, text_2024):
        result = parser.parse(text_2024, "2024_transcript.pdf")
        assert result.has_8606 is False

    def test_no_ira_activity(self, parser, text_2024):
        result = parser.parse(text_2024, "2024_transcript.pdf")
        assert result.has_ira_activity is False


class TestParse2023CleanBackdoor:
    """2023 transcript shows a clean backdoor Roth conversion."""

    def test_extracts_tax_year(self, parser, text_2023):
        result = parser.parse(text_2023, "2023_transcript.pdf")
        assert result is not None
        assert result.tax_year == 2023

    def test_extracts_distributions(self, parser, text_2023):
        result = parser.parse(text_2023, "2023_transcript.pdf")
        assert result.total_ira_distributions == Decimal("6500.00")
        assert result.taxable_ira_distributions == Decimal("0.00")

    def test_extracts_8606_clean_conversion(self, parser, text_2023):
        result = parser.parse(text_2023, "2023_transcript.pdf")
        assert result.has_8606 is True
        assert result.nondeductible_contributions == Decimal("6500.00")
        assert result.conversion_amount == Decimal("6500.00")
        assert result.total_basis == Decimal("6500.00")
        assert result.taxable_conversion_amount == Decimal("0.00")


class TestParse2020ContributionOnly:
    """2020 transcript has nondeductible contribution but no conversion."""

    def test_extracts_tax_year(self, parser, text_2020):
        result = parser.parse(text_2020, "2020_transcript.pdf")
        assert result is not None
        assert result.tax_year == 2020

    def test_zero_distributions(self, parser, text_2020):
        result = parser.parse(text_2020, "2020_transcript.pdf")
        assert result.total_ira_distributions == Decimal("0.00")

    def test_has_8606_with_contribution(self, parser, text_2020):
        result = parser.parse(text_2020, "2020_transcript.pdf")
        assert result.has_8606 is True
        assert result.nondeductible_contributions == Decimal("6000.00")
        assert result.conversion_amount == Decimal("0.00")
        assert result.total_distributions_8606 == Decimal("0.00")
