"""Basis reconstruction engine — the core logic."""

from dataclasses import dataclass, field
from decimal import Decimal

from rothos.parsers.base import YearData


@dataclass
class YearSummary:
    """Computed summary for a single tax year."""

    tax_year: int
    source_file: str

    # Basis tracking
    basis_start: Decimal = Decimal("0")
    basis_added: Decimal = Decimal("0")
    basis_used: Decimal = Decimal("0")
    basis_end: Decimal = Decimal("0")

    # From parsed data
    total_ira_distributions: Decimal | None = None
    taxable_ira_distributions: Decimal | None = None
    ira_deduction: Decimal | None = None
    has_8606: bool = False
    conversion_amount: Decimal | None = None
    nondeductible_contributions: Decimal | None = None

    # Warnings
    warnings: list[str] = field(default_factory=list)

    @property
    def has_ira_activity(self) -> bool:
        """Whether this year has any IRA-related activity."""
        return (
            (self.total_ira_distributions is not None and self.total_ira_distributions > 0)
            or (self.ira_deduction is not None and self.ira_deduction > 0)
            or self.has_8606
            or (self.conversion_amount is not None and self.conversion_amount > 0)
        )


def reconstruct_basis(year_data: list[YearData]) -> list[YearSummary]:
    """Reconstruct IRA basis history from parsed year data.

    Processes years in chronological order, carrying basis forward.

    Args:
        year_data: List of parsed year data (any order).

    Returns:
        List of YearSummary in chronological order.
    """
    if not year_data:
        return []

    # Sort by tax year
    sorted_years = sorted(year_data, key=lambda y: y.tax_year)

    results: list[YearSummary] = []
    previous_basis_end = Decimal("0")

    for data in sorted_years:
        summary = YearSummary(
            tax_year=data.tax_year,
            source_file=data.source_file,
            total_ira_distributions=data.total_ira_distributions,
            taxable_ira_distributions=data.taxable_ira_distributions,
            ira_deduction=data.ira_deduction,
            has_8606=data.has_8606,
            conversion_amount=data.conversion_amount,
            nondeductible_contributions=data.nondeductible_contributions,
        )

        # Step 1: basis_start from previous year
        summary.basis_start = previous_basis_end

        # Step 2: basis_added = nondeductible contributions
        if data.has_8606 and data.nondeductible_contributions is not None:
            summary.basis_added = data.nondeductible_contributions
        else:
            summary.basis_added = Decimal("0")

        total_basis = summary.basis_start + summary.basis_added

        # Step 3: basis_used from distributions
        # The non-taxable portion of IRA distributions = basis recovered
        if (
            data.total_ira_distributions is not None
            and data.taxable_ira_distributions is not None
            and data.total_ira_distributions > 0
        ):
            non_taxable = max(
                data.total_ira_distributions - data.taxable_ira_distributions,
                Decimal("0"),
            )
            summary.basis_used = min(non_taxable, total_basis)
        else:
            summary.basis_used = Decimal("0")

        # Step 4: basis_end
        summary.basis_end = max(total_basis - summary.basis_used, Decimal("0"))

        # Step 5: Generate warnings
        summary.warnings = _generate_warnings(data, summary)

        results.append(summary)
        previous_basis_end = summary.basis_end

    return results


def _generate_warnings(data: YearData, summary: YearSummary) -> list[str]:
    """Generate warnings for a year based on the data and summary."""
    warnings: list[str] = []

    # Warn if distributions exist but no Form 8606
    if (
        data.total_ira_distributions is not None
        and data.total_ira_distributions > 0
        and not data.has_8606
    ):
        warnings.append(
            f"IRA distributions of ${data.total_ira_distributions:,.2f} found "
            f"but no Form 8606 was filed. If you had basis, it may not have been tracked."
        )

    # Warn if non-taxable distributions exceed tracked basis
    if (
        data.total_ira_distributions is not None
        and data.taxable_ira_distributions is not None
        and data.total_ira_distributions > 0
    ):
        non_taxable = data.total_ira_distributions - data.taxable_ira_distributions
        total_basis = summary.basis_start + summary.basis_added
        if non_taxable > total_basis and total_basis > 0:
            warnings.append(
                f"Non-taxable distributions (${non_taxable:,.2f}) exceed tracked basis "
                f"(${total_basis:,.2f}). Basis may be underreported from earlier years."
            )

    return warnings
