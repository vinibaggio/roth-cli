"""Base parser interface."""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Protocol


@dataclass
class YearData:
    """Extracted data for a single tax year."""

    tax_year: int
    source_file: str

    # Form 1040 income section
    total_ira_distributions: Decimal | None = None
    taxable_ira_distributions: Decimal | None = None

    # Adjustments
    ira_deduction: Decimal | None = None

    # Form 8606 (if present)
    has_8606: bool = False
    nondeductible_contributions: Decimal | None = None
    total_basis: Decimal | None = None  # basis before conversion
    conversion_amount: Decimal | None = None
    taxable_conversion_amount: Decimal | None = None
    total_distributions_8606: Decimal | None = None  # trad+SEP+SIMPLE distributions

    # Computed/inferred
    traditional_ira_contributions: Decimal | None = None

    # Warnings/notes
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


class Parser(Protocol):
    """Protocol for document parsers."""

    name: str

    def can_parse(self, text: str) -> bool:
        """Return True if this parser can handle the given text."""
        ...

    def parse(self, text: str, source_file: str) -> YearData | None:
        """Parse text and return extracted data, or None if parsing fails."""
        ...
