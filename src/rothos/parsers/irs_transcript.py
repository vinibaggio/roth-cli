"""Parser for IRS Form 1040 Tax Return Transcripts."""

import re
from decimal import Decimal, InvalidOperation

from rothos.parsers.base import YearData


def _extract_dollar_after_label(text: str, label: str) -> Decimal | None:
    """Extract dollar amount that appears after a label.

    IRS transcripts format values like:
        Label:
        $1,234.00
    or sometimes on the same line:
        Label: $1,234.00

    Handles negative amounts like -$704.00.
    """
    # Escape the label for regex, match colon + optional whitespace/newlines + dollar amount
    pattern = re.escape(label) + r"[:\s]*\n?\s*(-?\$[\d,]+\.\d{2})"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        value_str = match.group(1).replace("$", "").replace(",", "")
        try:
            return Decimal(value_str)
        except InvalidOperation:
            return None
    return None


class IrsTranscriptParser:
    """Parser for IRS Form 1040 Tax Return Transcripts."""

    name = "irs_tax_return_transcript"

    def can_parse(self, text: str) -> bool:
        """Check if text looks like an IRS Tax Return Transcript."""
        return bool(
            re.search(r"Form\s+1040\s+Tax\s+Return\s+Transcript", text, re.IGNORECASE)
        )

    def parse(self, text: str, source_file: str) -> YearData | None:
        """Parse an IRS Tax Return Transcript and extract IRA-related data."""
        # Extract tax year from "Report for Tax Period Ending: 12-31-YYYY"
        year_match = re.search(
            r"Report\s+for\s+Tax\s+Period\s+Ending:\s*\n?\s*(\d{2})-(\d{2})-(\d{4})",
            text,
            re.IGNORECASE,
        )
        if not year_match:
            return None

        tax_year = int(year_match.group(3))

        data = YearData(tax_year=tax_year, source_file=source_file)

        # Extract Form 1040 income fields
        data.total_ira_distributions = _extract_dollar_after_label(
            text, "Total IRA distributions"
        )
        data.taxable_ira_distributions = _extract_dollar_after_label(
            text, "Taxable IRA distributions"
        )

        # Extract adjustments — use the first occurrence (taxpayer-reported)
        data.ira_deduction = _extract_dollar_after_label(text, "IRA deduction")

        # Check for Form 8606 section
        form_8606_match = re.search(
            r"Form\s+8606\s*[-–—]\s*Nondeductible\s+IRAs",
            text,
            re.IGNORECASE,
        )
        if form_8606_match:
            data.has_8606 = True

            # Bound the 8606 section: from header to next "Form NNNN" section
            section_start = form_8606_match.start()
            next_section = re.search(
                r"\nForm\s+\d{4}\s", text[section_start + 10:]
            )
            if next_section:
                section_text = text[section_start : section_start + 10 + next_section.start()]
            else:
                section_text = text[section_start:]

            data.nondeductible_contributions = _extract_dollar_after_label(
                section_text, "Taxable nondeductible contributions"
            )
            data.conversion_amount = _extract_dollar_after_label(
                section_text, "Total amount IRA converted to Roth IRA"
            )
            data.total_basis = _extract_dollar_after_label(
                section_text, "IRA basis before conversion"
            )
            data.taxable_conversion_amount = _extract_dollar_after_label(
                section_text, "Taxable amount of conversion"
            )
            data.total_distributions_8606 = _extract_dollar_after_label(
                section_text, "Traditional, separate and simple IRA distributions"
            )

        return data
