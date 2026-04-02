"""Tests for output formatting."""

import json
from decimal import Decimal

from rothos.engine import YearSummary
from rothos.output import to_json, to_dict


def _summary(year: int, start: str = "0", added: str = "0", used: str = "0", end: str = "0", **kwargs) -> YearSummary:
    return YearSummary(
        tax_year=year,
        source_file="test.pdf",
        basis_start=Decimal(start),
        basis_added=Decimal(added),
        basis_used=Decimal(used),
        basis_end=Decimal(end),
        **kwargs,
    )


class TestToDict:
    def test_converts_to_dict(self):
        summaries = [_summary(2021, "0", "6000", "0", "6000")]
        result = to_dict(summaries)
        assert len(result["years"]) == 1
        assert result["years"][0]["tax_year"] == 2021
        assert result["years"][0]["basis_end"] == 6000.0

    def test_decimal_to_float(self):
        """Decimals should be converted to float for JSON serialization."""
        summaries = [_summary(2021, "0", "6000.50", "0", "6000.50")]
        result = to_dict(summaries)
        assert result["years"][0]["basis_added"] == 6000.50
        assert isinstance(result["years"][0]["basis_added"], float)

    def test_none_values_preserved(self):
        """None values should stay None."""
        summaries = [_summary(2021)]
        result = to_dict(summaries)
        assert result["years"][0]["total_ira_distributions"] is None

    def test_warnings_included(self):
        summaries = [_summary(2021, warnings=["test warning"])]
        result = to_dict(summaries)
        assert result["years"][0]["warnings"] == ["test warning"]


class TestToJson:
    def test_valid_json(self):
        summaries = [_summary(2021)]
        result = to_json(summaries)
        parsed = json.loads(result)
        assert "years" in parsed

    def test_roundtrip(self):
        summaries = [_summary(2020, "0", "6000", "0", "6000"), _summary(2021, "6000", "0", "6000", "0")]
        result = to_json(summaries)
        parsed = json.loads(result)
        assert len(parsed["years"]) == 2
        assert parsed["years"][0]["basis_end"] == 6000.0
        assert parsed["years"][1]["basis_end"] == 0.0

    def test_empty_list(self):
        result = to_json([])
        parsed = json.loads(result)
        assert parsed["years"] == []
