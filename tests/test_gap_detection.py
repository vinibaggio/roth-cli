"""Tests for year gap detection."""

from decimal import Decimal

from rothos.engine import reconstruct_basis, detect_gaps, YearSummary
from rothos.parsers.base import YearData


def _year(
    year: int,
    has_8606: bool = False,
    nondeductible: str | None = None,
    total_dist: str = "0",
    taxable_dist: str = "0",
) -> YearData:
    return YearData(
        tax_year=year,
        source_file=f"{year}_transcript.pdf",
        total_ira_distributions=Decimal(total_dist),
        taxable_ira_distributions=Decimal(taxable_dist),
        ira_deduction=Decimal("0"),
        has_8606=has_8606,
        nondeductible_contributions=Decimal(nondeductible) if nondeductible else None,
    )


class TestDetectGaps:
    def test_no_gaps(self):
        """Consecutive years should have no gaps."""
        summaries = reconstruct_basis([_year(2020), _year(2021), _year(2022)])
        gaps = detect_gaps(summaries)
        assert gaps == []

    def test_single_gap(self):
        """Should detect a single missing year."""
        summaries = reconstruct_basis([_year(2020), _year(2022)])
        gaps = detect_gaps(summaries)
        assert gaps == [2021]

    def test_multiple_gaps(self):
        """Should detect multiple missing years."""
        summaries = reconstruct_basis([_year(2019), _year(2023)])
        gaps = detect_gaps(summaries)
        assert gaps == [2020, 2021, 2022]

    def test_single_year_no_gaps(self):
        """Single year should have no gaps."""
        summaries = reconstruct_basis([_year(2021)])
        gaps = detect_gaps(summaries)
        assert gaps == []

    def test_empty_input(self):
        """Empty input should have no gaps."""
        gaps = detect_gaps([])
        assert gaps == []

    def test_two_consecutive_years(self):
        """Two consecutive years should have no gaps."""
        summaries = reconstruct_basis([_year(2023), _year(2024)])
        gaps = detect_gaps(summaries)
        assert gaps == []

    def test_gap_with_basis_carries_warning(self):
        """Gap year when basis exists should produce a warning about unknown activity."""
        data = [
            _year(2020, has_8606=True, nondeductible="6000"),
            # 2021 missing
            _year(2022),
        ]
        summaries = reconstruct_basis(data)
        gaps = detect_gaps(summaries)
        assert gaps == [2021]
        # Basis was $6,000 going into the gap — this is risky because
        # we don't know if distributions/conversions happened in 2021


class TestGapWarningsInOutput:
    def test_gap_years_in_json(self):
        """JSON output should include gap information."""
        import json
        from rothos.output import to_dict

        data = [_year(2020, has_8606=True, nondeductible="6000"), _year(2022)]
        summaries = reconstruct_basis(data)
        gaps = detect_gaps(summaries)
        result = to_dict(summaries, missing_years=gaps)
        assert result["missing_years"] == [2021]

    def test_no_gaps_in_json(self):
        """JSON output should show empty list when no gaps."""
        from rothos.output import to_dict

        data = [_year(2020), _year(2021)]
        summaries = reconstruct_basis(data)
        gaps = detect_gaps(summaries)
        result = to_dict(summaries, missing_years=gaps)
        assert result["missing_years"] == []
