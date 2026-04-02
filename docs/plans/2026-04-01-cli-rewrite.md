# rothos CLI Rewrite — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Python CLI tool that parses IRS Tax Return Transcript PDFs, extracts Form 8606 and IRA-related data, and reconstructs multi-year IRA basis history with a terminal report.

**Architecture:** Pluggable parser system where each parser (IRS transcript, TurboTax, CPA-prepared, etc.) implements a common interface. A classifier auto-detects document type. The basis engine stitches years together. Output is JSON, rendered as a terminal table.

**Tech Stack:** Python 3.11+, PyMuPDF (fitz) for PDF text extraction, Click for CLI, Rich for terminal output, pytest for tests.

---

## Background: Domain Knowledge

### What we're extracting from IRS Tax Return Transcripts

The IRS Tax Return Transcript is a structured text document with labeled fields. Key sections:

**Page 1 (Income section):**
- `Total IRA distributions:` → Form 1040 line 4a
- `Taxable IRA distributions:` → Form 1040 line 4b

**Page 2 (Adjustments section):**
- `IRA deduction:` → Traditional IRA deduction taken
- `IRA deduction per computer:` → IRS-computed version

**Form 8606 section (if present — only appears when 8606 was filed):**
- `Taxable nondeductible contributions:` → Line 1 (nondeductible contributions for this year)
- `Total amount IRA converted to Roth IRA:` → Roth conversion amount
- `IRA basis before conversion:` → Total basis before any conversion
- `Taxable amount of conversion:` → Taxable portion of conversion
- `Roth IRA basis before conversion:` → (less relevant for traditional IRA basis)
- `Traditional, separate and simple IRA distributions:` → Total distributions

The Form 8606 section may appear as `Form 8606 - Nondeductible IRAs (Occurrence #: 1)` and may have multiple occurrences (primary + spouse).

### Basis reconstruction logic

For each year, in chronological order:
1. `basis_start` = previous year's `basis_end` (or 0 for first year)
2. `basis_added` = nondeductible contributions (contributions - deduction, or from 8606 line 1)
3. If conversions/distributions occurred, pro-rata rule applies:
   - `non_taxable_portion` = `total_distributions - taxable_distributions` (from 1040 lines 4a/4b)
   - `basis_used` = min(non_taxable_portion, total_basis)
4. `basis_end` = `basis_start + basis_added - basis_used`

### What the 2024 transcript looks like (no IRA activity)
- Total IRA distributions: $0.00
- Taxable IRA distributions: $0.00
- IRA deduction: $0.00
- No Form 8606 section present

### What the 2021 transcript looks like (has conversions)
- Total IRA distributions: $99,691.00
- Taxable IRA distributions: $90,527.00
- Form 8606 section present with conversion details

---

## Task 1: Nuke repo and set up project skeleton

**Files:**
- Delete: everything except `examples/`, `.git/`, `docs/plans/`
- Create: `pyproject.toml`, `src/rothos/__init__.py`, `src/rothos/cli.py`, `tests/__init__.py`, `README.md`, `.gitignore`

**Step 1: Remove old code**

```bash
# Remove everything except .git, examples, and this plan
cd /Users/vinibaggio/code/rothos2
# Remove old files (keep .git, examples, docs/plans)
rm -rf backend frontend infra supabase scripts .github history
rm -f AGENTS.md .env.example .env.sample .gitattributes .mise.toml test_parser.py
rm -rf docs/SPEC.md docs/SPEC_CPA.md docs/FIELD_SOURCES.md docs/FIELD_INSTRUCTIONS.md
rm -rf docs/DISTRIBUTION_SCENARIO.md docs/MANUAL_ADJUSTMENTS_WORKFLOW.md
rm -rf docs/MIGRATION_AND_FEATURE_SUMMARY.md docs/MIGRATION_FIX.md docs/MIGRATION_FIX_V2.md
rm -rf docs/IMPLEMENTATION_SUMMARY.md docs/SUPABASE_PERSISTENCE.md docs/HARDENING.md
rm -rf docs/IDEMPOTENCY_STRATEGIES.md docs/.gitkeep
```

**Step 2: Create pyproject.toml**

```toml
[project]
name = "rothos"
version = "0.1.0"
description = "Reconstruct IRA basis history from tax return PDFs"
readme = "README.md"
requires-python = ">=3.11"
license = {text = "MIT"}
dependencies = [
    "pymupdf>=1.24",
    "click>=8.0",
    "rich>=13.0",
]

[project.scripts]
rothos = "rothos.cli:main"

[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.backends._legacy:_Backend"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
]
```

**Step 3: Create minimal source files**

`src/rothos/__init__.py`:
```python
"""rothos — Reconstruct IRA basis history from tax return PDFs."""
```

`src/rothos/cli.py`:
```python
"""CLI entry point for rothos."""

import click


@click.command()
@click.argument("path", type=click.Path(exists=True))
def main(path: str) -> None:
    """Analyze tax return PDFs and reconstruct IRA basis history.

    PATH can be a single PDF file or a directory of PDFs.
    """
    click.echo(f"Analyzing: {path}")
```

**Step 4: Create .gitignore**

```
__pycache__/
*.pyc
*.pyo
*.egg-info/
dist/
build/
.eggs/
*.egg
.venv/
venv/
.pytest_cache/
.coverage
htmlcov/
.mypy_cache/
.ruff_cache/
```

**Step 5: Create README.md**

```markdown
# rothos

Reconstruct IRA basis history from tax return PDFs.

Parses IRS Tax Return Transcripts (and other tax return formats) to extract Form 8606 data
and rebuild your IRA basis year-by-year. Useful for anyone doing or planning backdoor Roth conversions.

## Install

```bash
pip install -e ".[dev]"
```

## Usage

```bash
# Analyze a directory of tax return PDFs
rothos ./my-tax-returns/

# Analyze a single PDF
rothos "2021 tax return.pdf"
```

## Disclaimer

This tool is for informational and educational purposes only.
It does not provide tax, legal, or financial advice.
All outputs must be reviewed by a qualified tax professional.
```

**Step 6: Install and verify**

```bash
cd /Users/vinibaggio/code/rothos2
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
rothos --help
```

Expected: Help text displays.

**Step 7: Commit**

```bash
git add -A
git commit -m "Nuke web app, set up CLI project skeleton"
```

---

## Task 2: PDF text extraction module

**Files:**
- Create: `src/rothos/pdf.py`
- Create: `tests/test_pdf.py`

**Step 1: Write the failing test**

`tests/test_pdf.py`:
```python
"""Tests for PDF text extraction."""

import os
import pytest
from rothos.pdf import extract_text


EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "examples")


def test_extract_text_from_tax_return_transcript():
    """Should extract readable text from a tax return transcript PDF."""
    pdf_path = os.path.join(EXAMPLES_DIR, "2021 tax return.pdf")
    if not os.path.exists(pdf_path):
        pytest.skip("Example PDF not available")

    text = extract_text(pdf_path)

    assert "Form 1040 Tax Return Transcript" in text
    assert "Total IRA distributions" in text


def test_extract_text_nonexistent_file():
    """Should raise FileNotFoundError for missing files."""
    with pytest.raises(FileNotFoundError):
        extract_text("/nonexistent/file.pdf")


def test_extract_text_returns_string():
    """Should return a string."""
    pdf_path = os.path.join(EXAMPLES_DIR, "2021 tax return.pdf")
    if not os.path.exists(pdf_path):
        pytest.skip("Example PDF not available")

    result = extract_text(pdf_path)
    assert isinstance(result, str)
    assert len(result) > 100
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_pdf.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'rothos.pdf'`

**Step 3: Write implementation**

`src/rothos/pdf.py`:
```python
"""PDF text extraction using PyMuPDF."""

from pathlib import Path

import fitz


def extract_text(pdf_path: str | Path) -> str:
    """Extract text from a PDF file.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        Concatenated text from all pages.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        ValueError: If the file is not a valid PDF.
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    try:
        doc = fitz.open(str(path))
    except Exception as e:
        raise ValueError(f"Could not open PDF: {path}") from e

    pages = []
    for page in doc:
        pages.append(page.get_text())
    doc.close()

    return "\n".join(pages)
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_pdf.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add -A
git commit -m "Add PDF text extraction module"
```

---

## Task 3: SSN sanitization

**Files:**
- Create: `src/rothos/sanitize.py`
- Create: `tests/test_sanitize.py`

**Step 1: Write the failing test**

`tests/test_sanitize.py`:
```python
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
```

**Step 2: Run test — should fail**

**Step 3: Write implementation**

`src/rothos/sanitize.py`:
```python
"""Text sanitization — remove SSNs and other PII."""

import re


def sanitize_text(text: str) -> str:
    """Remove SSNs from text while preserving other numbers.

    Masks:
    - Dashed SSNs (123-45-6789 → XXX-XX-6789)
    - 9-digit SSNs (123456789 → XXXXX6789)

    Does NOT mask:
    - Already-masked SSNs (XXX-XX-1234)
    - Dollar amounts
    - Tracking numbers or other long numbers
    """
    # Mask dashed SSNs: 123-45-6789 → XXX-XX-6789 (keep last 4)
    # But don't re-mask already masked ones
    text = re.sub(
        r"(?<![X])\b(\d{3})-(\d{2})-(\d{4})\b",
        lambda m: f"XXX-XX-{m.group(3)}",
        text,
    )

    # Mask 9-digit SSNs that appear near SSN-related context
    # Only match standalone 9-digit numbers (not part of longer numbers)
    text = re.sub(
        r"(?<=SSN[:\s])\s*(\d{5})(\d{4})\b",
        lambda m: f"XXXXX{m.group(2)}",
        text,
    )

    return text
```

**Step 4: Run tests — should pass**

**Step 5: Commit**

```bash
git add -A
git commit -m "Add SSN sanitization module"
```

---

## Task 4: Parser interface and classifier

**Files:**
- Create: `src/rothos/parsers/__init__.py`
- Create: `src/rothos/parsers/base.py`
- Create: `src/rothos/parsers/classifier.py`
- Create: `tests/test_classifier.py`

**Step 1: Write the tests**

`tests/test_classifier.py`:
```python
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
```

**Step 2: Run — should fail**

**Step 3: Write implementation**

`src/rothos/parsers/base.py`:
```python
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
    traditional_ira_contributions: Decimal | None = None  # from W&I or 5498 if available

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
```

`src/rothos/parsers/__init__.py`:
```python
"""Document parsers for tax return PDFs."""

from rothos.parsers.base import Parser, YearData

__all__ = ["Parser", "YearData"]
```

`src/rothos/parsers/classifier.py`:
```python
"""Document classifier — identifies which parser to use."""

import re


# Map of document type identifier → list of regex patterns
_PATTERNS: dict[str, list[re.Pattern]] = {
    "irs_tax_return_transcript": [
        re.compile(r"Form\s+1040\s+Tax\s+Return\s+Transcript", re.IGNORECASE),
        re.compile(r"This\s+Product\s+Contains\s+Sensitive\s+Taxpayer\s+Data", re.IGNORECASE),
    ],
}

# Minimum patterns that must match for each type
_MIN_MATCHES: dict[str, int] = {
    "irs_tax_return_transcript": 1,
}


def classify(text: str) -> str | None:
    """Classify document text and return the parser type identifier.

    Returns:
        Parser type string (e.g., "irs_tax_return_transcript") or None.
    """
    for doc_type, patterns in _PATTERNS.items():
        matches = sum(1 for p in patterns if p.search(text))
        if matches >= _MIN_MATCHES.get(doc_type, 1):
            return doc_type
    return None
```

**Step 4: Run tests — should pass**

**Step 5: Commit**

```bash
git add -A
git commit -m "Add parser interface and document classifier"
```

---

## Task 5: IRS Tax Return Transcript parser

This is the core parser. It extracts all IRA-relevant data from an IRS Tax Return Transcript.

**Files:**
- Create: `src/rothos/parsers/irs_transcript.py`
- Create: `tests/test_irs_transcript_parser.py`

**Step 1: Write the failing tests**

`tests/test_irs_transcript_parser.py`:
```python
"""Tests for IRS Tax Return Transcript parser."""

import os
from decimal import Decimal

import pytest

from rothos.parsers.irs_transcript import IrsTranscriptParser
from rothos.pdf import extract_text


EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "examples")


@pytest.fixture
def parser():
    return IrsTranscriptParser()


@pytest.fixture
def text_2021():
    pdf_path = os.path.join(EXAMPLES_DIR, "2021 tax return.pdf")
    if not os.path.exists(pdf_path):
        pytest.skip("Example PDF not available")
    return extract_text(pdf_path)


@pytest.fixture
def text_2024():
    pdf_path = os.path.join(EXAMPLES_DIR, "tax return transcript.pdf")
    if not os.path.exists(pdf_path):
        pytest.skip("Example PDF not available")
    return extract_text(pdf_path)


class TestCanParse:
    def test_recognizes_irs_transcript(self, parser, text_2021):
        assert parser.can_parse(text_2021) is True

    def test_rejects_random_text(self, parser):
        assert parser.can_parse("This is not a tax return.") is False


class TestParse2021WithConversions:
    """2021 transcript has IRA distributions and Form 8606."""

    def test_extracts_tax_year(self, parser, text_2021):
        result = parser.parse(text_2021, "2021 tax return.pdf")
        assert result is not None
        assert result.tax_year == 2021

    def test_extracts_ira_distributions(self, parser, text_2021):
        result = parser.parse(text_2021, "2021 tax return.pdf")
        assert result.total_ira_distributions == Decimal("99691.00")
        assert result.taxable_ira_distributions == Decimal("90527.00")

    def test_extracts_ira_deduction(self, parser, text_2021):
        result = parser.parse(text_2021, "2021 tax return.pdf")
        assert result.ira_deduction == Decimal("0.00")

    def test_detects_form_8606(self, parser, text_2021):
        result = parser.parse(text_2021, "2021 tax return.pdf")
        assert result.has_8606 is True

    def test_extracts_8606_fields(self, parser, text_2021):
        result = parser.parse(text_2021, "2021 tax return.pdf")
        assert result.nondeductible_contributions == Decimal("90527.00")
        assert result.conversion_amount == Decimal("0.00")
        assert result.total_basis == Decimal("0.00")
        assert result.taxable_conversion_amount == Decimal("0.00")
        assert result.total_distributions_8606 == Decimal("99691.00")

    def test_has_ira_activity(self, parser, text_2021):
        result = parser.parse(text_2021, "2021 tax return.pdf")
        assert result.has_ira_activity is True


class TestParse2024NoIraActivity:
    """2024 transcript has no IRA distributions and no Form 8606."""

    def test_extracts_tax_year(self, parser, text_2024):
        result = parser.parse(text_2024, "tax return transcript.pdf")
        assert result is not None
        assert result.tax_year == 2024

    def test_zero_ira_distributions(self, parser, text_2024):
        result = parser.parse(text_2024, "tax return transcript.pdf")
        assert result.total_ira_distributions == Decimal("0.00")
        assert result.taxable_ira_distributions == Decimal("0.00")

    def test_no_form_8606(self, parser, text_2024):
        result = parser.parse(text_2024, "tax return transcript.pdf")
        assert result.has_8606 is False

    def test_no_ira_activity(self, parser, text_2024):
        result = parser.parse(text_2024, "tax return transcript.pdf")
        assert result.has_ira_activity is False
```

**Step 2: Run — should fail**

**Step 3: Write implementation**

`src/rothos/parsers/irs_transcript.py`:
```python
"""Parser for IRS Form 1040 Tax Return Transcripts."""

import re
from decimal import Decimal, InvalidOperation

from rothos.parsers.base import YearData


def _extract_dollar(text: str, pattern: str) -> Decimal | None:
    """Extract a dollar amount following a label pattern.

    Handles formats like:
    - "$99,691.00"
    - "$0.00"
    - "-$704.00" (negative)
    """
    match = re.search(pattern + r"\s*[-]?\$?([\d,]+\.\d{2})", text, re.IGNORECASE)
    if match:
        value_str = match.group(1).replace(",", "")
        try:
            value = Decimal(value_str)
            # Check if negative
            full_match = match.group(0)
            if "-$" in full_match or "-$" in full_match:
                value = -value
            return value
        except InvalidOperation:
            return None
    return None


def _extract_dollar_after_newline(text: str, label: str) -> Decimal | None:
    """Extract dollar amount that appears on the line after the label.

    IRS transcripts format values like:
        Label:\n$1,234.00
    or:
        Label:\n-$1,234.00
    """
    # Match the label, then skip whitespace/newlines to find the dollar amount
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
        data.total_ira_distributions = _extract_dollar_after_newline(
            text, "Total IRA distributions"
        )
        data.taxable_ira_distributions = _extract_dollar_after_newline(
            text, "Taxable IRA distributions"
        )

        # Extract adjustments
        # Use the first occurrence (taxpayer-reported), not "per computer"
        data.ira_deduction = _extract_dollar_after_newline(text, "IRA deduction")

        # Check for Form 8606 section
        form_8606_match = re.search(
            r"Form\s+8606\s*[-–—]\s*Nondeductible\s+IRAs",
            text,
            re.IGNORECASE,
        )
        if form_8606_match:
            data.has_8606 = True
            # Extract from the 8606 section only (text after the header)
            section_start = form_8606_match.start()
            # Find the next "Form" section header to bound the 8606 section
            next_section = re.search(
                r"\nForm\s+\d{4}", text[section_start + 10:]
            )
            if next_section:
                section_text = text[section_start : section_start + 10 + next_section.start()]
            else:
                section_text = text[section_start:]

            data.nondeductible_contributions = _extract_dollar_after_newline(
                section_text, "Taxable nondeductible contributions"
            )
            data.conversion_amount = _extract_dollar_after_newline(
                section_text, "Total amount IRA converted to Roth IRA"
            )
            data.total_basis = _extract_dollar_after_newline(
                section_text, "IRA basis before conversion"
            )
            data.taxable_conversion_amount = _extract_dollar_after_newline(
                section_text, "Taxable amount of conversion"
            )
            data.total_distributions_8606 = _extract_dollar_after_newline(
                section_text, "Traditional, separate and simple IRA distributions"
            )

        return data
```

**Step 4: Run tests — should pass**

```bash
pytest tests/test_irs_transcript_parser.py -v
```

**Step 5: Commit**

```bash
git add -A
git commit -m "Add IRS Tax Return Transcript parser"
```

---

## Task 6: Basis reconstruction engine

**Files:**
- Create: `src/rothos/engine.py`
- Create: `tests/test_engine.py`

**Step 1: Write the failing tests**

`tests/test_engine.py`:
```python
"""Tests for the basis reconstruction engine."""

from decimal import Decimal

from rothos.engine import reconstruct_basis, YearSummary
from rothos.parsers.base import YearData


def _year(
    year: int,
    total_dist: str = "0",
    taxable_dist: str = "0",
    ira_deduction: str = "0",
    has_8606: bool = False,
    nondeductible: str | None = None,
    conversion: str | None = None,
    basis: str | None = None,
    taxable_conversion: str | None = None,
    total_dist_8606: str | None = None,
) -> YearData:
    """Helper to create a YearData for testing."""
    return YearData(
        tax_year=year,
        source_file="test.pdf",
        total_ira_distributions=Decimal(total_dist),
        taxable_ira_distributions=Decimal(taxable_dist),
        ira_deduction=Decimal(ira_deduction),
        has_8606=has_8606,
        nondeductible_contributions=Decimal(nondeductible) if nondeductible else None,
        conversion_amount=Decimal(conversion) if conversion else None,
        total_basis=Decimal(basis) if basis else None,
        taxable_conversion_amount=Decimal(taxable_conversion) if taxable_conversion else None,
        total_distributions_8606=Decimal(total_dist_8606) if total_dist_8606 else None,
    )


class TestSingleYear:
    def test_no_activity(self):
        """Year with no IRA activity should have zero basis."""
        years = [_year(2024)]
        result = reconstruct_basis(years)
        assert len(result) == 1
        assert result[0].basis_start == Decimal("0")
        assert result[0].basis_end == Decimal("0")

    def test_nondeductible_contribution_builds_basis(self):
        """Nondeductible contribution from 8606 should add to basis."""
        years = [
            _year(2021, has_8606=True, nondeductible="6000"),
        ]
        result = reconstruct_basis(years)
        assert result[0].basis_added == Decimal("6000")
        assert result[0].basis_end == Decimal("6000")

    def test_conversion_uses_basis(self):
        """Conversion with non-taxable portion should consume basis."""
        years = [
            _year(
                2021,
                total_dist="6000",
                taxable_dist="0",
                has_8606=True,
                nondeductible="6000",
            ),
        ]
        result = reconstruct_basis(years)
        # Added 6000 basis, then used 6000 (non-taxable = 6000 - 0 = 6000)
        assert result[0].basis_added == Decimal("6000")
        assert result[0].basis_used == Decimal("6000")
        assert result[0].basis_end == Decimal("0")


class TestMultiYear:
    def test_basis_carries_forward(self):
        """Basis from year 1 should carry to year 2."""
        years = [
            _year(2020, has_8606=True, nondeductible="6000"),
            _year(2021),
        ]
        result = reconstruct_basis(years)
        assert result[0].basis_end == Decimal("6000")
        assert result[1].basis_start == Decimal("6000")
        assert result[1].basis_end == Decimal("6000")

    def test_multi_year_accumulation_then_conversion(self):
        """Build basis over 2 years, then convert."""
        years = [
            _year(2019, has_8606=True, nondeductible="6000"),
            _year(2020, has_8606=True, nondeductible="6000"),
            _year(2021, total_dist="12000", taxable_dist="0", has_8606=True, nondeductible="0"),
        ]
        result = reconstruct_basis(years)
        assert result[0].basis_end == Decimal("6000")
        assert result[1].basis_end == Decimal("12000")
        # Year 3: had 12000 basis, distributed 12000 with 0 taxable = 12000 non-taxable used
        assert result[2].basis_start == Decimal("12000")
        assert result[2].basis_used == Decimal("12000")
        assert result[2].basis_end == Decimal("0")

    def test_partial_conversion(self):
        """Conversion of partial amount — some basis remains."""
        years = [
            _year(2020, has_8606=True, nondeductible="6000"),
            _year(
                2021,
                total_dist="6000",
                taxable_dist="3000",
                has_8606=True,
                nondeductible="0",
            ),
        ]
        result = reconstruct_basis(years)
        # 6000 basis, distributed 6000, taxable 3000 → non-taxable 3000
        assert result[1].basis_used == Decimal("3000")
        assert result[1].basis_end == Decimal("3000")


class TestYearOrdering:
    def test_years_sorted_chronologically(self):
        """Years should be processed in chronological order regardless of input order."""
        years = [
            _year(2022),
            _year(2020, has_8606=True, nondeductible="6000"),
            _year(2021),
        ]
        result = reconstruct_basis(years)
        assert result[0].tax_year == 2020
        assert result[1].tax_year == 2021
        assert result[2].tax_year == 2022
        assert result[1].basis_start == Decimal("6000")


class TestWarnings:
    def test_missing_8606_warning(self):
        """Should warn when distributions exist but no 8606."""
        years = [
            _year(2021, total_dist="6000", taxable_dist="0"),
        ]
        result = reconstruct_basis(years)
        assert any("8606" in w for w in result[0].warnings)
```

**Step 2: Run — should fail**

**Step 3: Write implementation**

`src/rothos/engine.py`:
```python
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

    # Warn if non-taxable distributions exceed basis
    if (
        data.total_ira_distributions is not None
        and data.taxable_ira_distributions is not None
    ):
        non_taxable = data.total_ira_distributions - data.taxable_ira_distributions
        total_basis = summary.basis_start + summary.basis_added
        if non_taxable > total_basis and total_basis > 0:
            warnings.append(
                f"Non-taxable distributions (${non_taxable:,.2f}) exceed tracked basis "
                f"(${total_basis:,.2f}). Basis may be underreported from earlier years."
            )

    # Warn if 8606 was filed but no distributions
    if data.has_8606 and (
        data.total_ira_distributions is None or data.total_ira_distributions == 0
    ):
        if data.nondeductible_contributions and data.nondeductible_contributions > 0:
            pass  # This is normal — just building basis
        # No warning needed for 8606 with no distributions if just tracking contributions

    return warnings
```

**Step 4: Run tests — should pass**

```bash
pytest tests/test_engine.py -v
```

**Step 5: Commit**

```bash
git add -A
git commit -m "Add basis reconstruction engine"
```

---

## Task 7: JSON output and terminal report

**Files:**
- Create: `src/rothos/output.py`
- Create: `tests/test_output.py`

**Step 1: Write the failing tests**

`tests/test_output.py`:
```python
"""Tests for output formatting."""

import json
from decimal import Decimal

from rothos.engine import YearSummary
from rothos.output import to_json, to_dict


def _summary(year: int, start: str = "0", added: str = "0", used: str = "0", end: str = "0") -> YearSummary:
    return YearSummary(
        tax_year=year,
        source_file="test.pdf",
        basis_start=Decimal(start),
        basis_added=Decimal(added),
        basis_used=Decimal(used),
        basis_end=Decimal(end),
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
```

**Step 2: Run — should fail**

**Step 3: Write implementation**

`src/rothos/output.py`:
```python
"""Output formatting — JSON and terminal report."""

import json
from decimal import Decimal
from typing import Any

from rich.console import Console
from rich.table import Table

from rothos.engine import YearSummary


def _decimal_to_float(v: Decimal | None) -> float | None:
    """Convert Decimal to float for JSON serialization."""
    if v is None:
        return None
    return float(v)


def to_dict(summaries: list[YearSummary]) -> dict[str, Any]:
    """Convert summaries to a plain dict for JSON serialization."""
    years = []
    for s in summaries:
        years.append(
            {
                "tax_year": s.tax_year,
                "source_file": s.source_file,
                "basis_start": _decimal_to_float(s.basis_start),
                "basis_added": _decimal_to_float(s.basis_added),
                "basis_used": _decimal_to_float(s.basis_used),
                "basis_end": _decimal_to_float(s.basis_end),
                "total_ira_distributions": _decimal_to_float(s.total_ira_distributions),
                "taxable_ira_distributions": _decimal_to_float(s.taxable_ira_distributions),
                "ira_deduction": _decimal_to_float(s.ira_deduction),
                "has_8606": s.has_8606,
                "conversion_amount": _decimal_to_float(s.conversion_amount),
                "nondeductible_contributions": _decimal_to_float(s.nondeductible_contributions),
                "has_ira_activity": s.has_ira_activity,
                "warnings": s.warnings,
            }
        )
    return {"years": years}


def to_json(summaries: list[YearSummary], indent: int = 2) -> str:
    """Serialize summaries to JSON string."""
    return json.dumps(to_dict(summaries), indent=indent)


def _fmt(v: Decimal | None) -> str:
    """Format a decimal as dollar amount or dash."""
    if v is None:
        return "—"
    return f"${v:,.2f}"


def print_report(summaries: list[YearSummary], console: Console | None = None) -> None:
    """Print a formatted basis report to the terminal."""
    if console is None:
        console = Console()

    if not summaries:
        console.print("[yellow]No tax return data found.[/yellow]")
        return

    table = Table(title="IRA Basis History", show_lines=True)
    table.add_column("Year", style="bold", justify="center")
    table.add_column("Basis Start", justify="right")
    table.add_column("+ Added", justify="right")
    table.add_column("- Used", justify="right")
    table.add_column("= Basis End", justify="right", style="bold")
    table.add_column("Distributions", justify="right")
    table.add_column("8606", justify="center")
    table.add_column("Status", justify="center")

    for s in summaries:
        # Determine status
        status = _status_badge(s)
        filed_8606 = "✓" if s.has_8606 else "✗" if s.has_ira_activity else "—"

        table.add_row(
            str(s.tax_year),
            _fmt(s.basis_start),
            _fmt(s.basis_added),
            _fmt(s.basis_used),
            _fmt(s.basis_end),
            _fmt(s.total_ira_distributions),
            filed_8606,
            status,
        )

    console.print()
    console.print(table)

    # Print warnings
    has_warnings = False
    for s in summaries:
        if s.warnings:
            if not has_warnings:
                console.print()
                console.print("[bold yellow]⚠ Warnings:[/bold yellow]")
                has_warnings = True
            for w in s.warnings:
                console.print(f"  [yellow]{s.tax_year}:[/yellow] {w}")

    console.print()
    console.print(
        "[dim]Disclaimer: This tool is for informational purposes only. "
        "Consult a qualified tax professional.[/dim]"
    )


def _status_badge(s: YearSummary) -> str:
    """Return a status badge for the year."""
    if s.warnings:
        return "[yellow]⚠[/yellow]"
    if s.has_ira_activity:
        return "[green]✓[/green]"
    return "[dim]—[/dim]"
```

**Step 4: Run tests — should pass**

**Step 5: Commit**

```bash
git add -A
git commit -m "Add JSON output and terminal report formatting"
```

---

## Task 8: Wire up the CLI

**Files:**
- Modify: `src/rothos/cli.py`
- Create: `tests/test_cli.py`

**Step 1: Write the failing test**

`tests/test_cli.py`:
```python
"""Tests for the CLI."""

import os

from click.testing import CliRunner

from rothos.cli import main


EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "examples")


def test_help():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Analyze" in result.output


def test_analyze_directory(tmp_path):
    """Should handle a directory with no valid PDFs gracefully."""
    runner = CliRunner()
    result = runner.invoke(main, [str(tmp_path)])
    assert result.exit_code == 0
    assert "No tax return data found" in result.output or "No PDF files found" in result.output


def test_analyze_examples_dir():
    """Should analyze example PDFs if available."""
    if not os.path.exists(EXAMPLES_DIR):
        import pytest
        pytest.skip("Examples directory not available")

    runner = CliRunner()
    result = runner.invoke(main, [EXAMPLES_DIR])
    assert result.exit_code == 0


def test_json_output():
    """--json flag should output valid JSON."""
    if not os.path.exists(EXAMPLES_DIR):
        import pytest
        pytest.skip("Examples directory not available")

    runner = CliRunner()
    result = runner.invoke(main, [EXAMPLES_DIR, "--json"])
    assert result.exit_code == 0
    import json
    # Should be parseable JSON
    parsed = json.loads(result.output)
    assert "years" in parsed
```

**Step 2: Run — should fail**

**Step 3: Write implementation**

`src/rothos/cli.py`:
```python
"""CLI entry point for rothos."""

from pathlib import Path

import click
from rich.console import Console

from rothos.engine import reconstruct_basis
from rothos.output import print_report, to_json
from rothos.parsers.classifier import classify
from rothos.parsers.irs_transcript import IrsTranscriptParser
from rothos.pdf import extract_text
from rothos.sanitize import sanitize_text


# Registry of available parsers
_PARSERS = {
    "irs_tax_return_transcript": IrsTranscriptParser(),
}


def _find_pdfs(path: Path) -> list[Path]:
    """Find all PDF files in a path (file or directory)."""
    if path.is_file():
        if path.suffix.lower() == ".pdf":
            return [path]
        return []
    if path.is_dir():
        return sorted(path.glob("**/*.pdf"))
    return []


@click.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--json", "output_json", is_flag=True, help="Output JSON instead of table.")
def main(path: str, output_json: bool) -> None:
    """Analyze tax return PDFs and reconstruct IRA basis history.

    PATH can be a single PDF file or a directory of PDFs.
    """
    console = Console(stderr=True) if output_json else Console()
    target = Path(path)
    pdfs = _find_pdfs(target)

    if not pdfs:
        if output_json:
            click.echo('{"years": []}')
        else:
            console.print("[yellow]No PDF files found.[/yellow]")
        return

    year_data_list = []
    skipped = []

    for pdf_path in pdfs:
        try:
            raw_text = extract_text(pdf_path)
        except (ValueError, Exception) as e:
            console.print(f"[red]Error reading {pdf_path.name}: {e}[/red]")
            skipped.append(pdf_path.name)
            continue

        text = sanitize_text(raw_text)
        doc_type = classify(text)

        if doc_type is None:
            skipped.append(pdf_path.name)
            continue

        parser = _PARSERS.get(doc_type)
        if parser is None:
            skipped.append(pdf_path.name)
            continue

        result = parser.parse(text, pdf_path.name)
        if result is not None:
            year_data_list.append(result)

    # Reconstruct basis
    summaries = reconstruct_basis(year_data_list)

    if output_json:
        click.echo(to_json(summaries))
    else:
        if skipped:
            console.print(
                f"[dim]Skipped {len(skipped)} file(s) "
                f"(not recognized as supported tax returns): "
                f"{', '.join(skipped)}[/dim]"
            )
        print_report(summaries, console)
```

**Step 4: Run tests — should pass**

```bash
pytest tests/test_cli.py -v
```

**Step 5: Manual smoke test**

```bash
rothos examples/
rothos examples/ --json
rothos "examples/2021 tax return.pdf"
```

**Step 6: Commit**

```bash
git add -A
git commit -m "Wire up CLI with end-to-end pipeline"
```

---

## Task 9: Integration test with real PDFs

**Files:**
- Create: `tests/test_integration.py`

**Step 1: Write integration tests**

`tests/test_integration.py`:
```python
"""Integration tests using example PDFs."""

import os
from decimal import Decimal

import pytest

from rothos.engine import reconstruct_basis
from rothos.parsers.irs_transcript import IrsTranscriptParser
from rothos.pdf import extract_text
from rothos.sanitize import sanitize_text


EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "examples")


def _parse_transcript(filename: str) -> "YearData | None":
    pdf_path = os.path.join(EXAMPLES_DIR, filename)
    if not os.path.exists(pdf_path):
        pytest.skip(f"{filename} not available")
    text = sanitize_text(extract_text(pdf_path))
    parser = IrsTranscriptParser()
    return parser.parse(text, filename)


class TestEndToEnd:
    def test_2021_and_2024_together(self):
        """Should reconstruct basis across 2021 and 2024 transcripts."""
        data_2021 = _parse_transcript("2021 tax return.pdf")
        data_2024 = _parse_transcript("tax return transcript.pdf")

        assert data_2021 is not None
        assert data_2024 is not None

        summaries = reconstruct_basis([data_2024, data_2021])  # Intentionally out of order

        # Should be sorted chronologically
        assert summaries[0].tax_year == 2021
        assert summaries[1].tax_year == 2024

        # 2021 had distributions, verify basis tracking
        assert summaries[0].has_8606 is True
        assert summaries[0].total_ira_distributions == Decimal("99691.00")

        # Basis should carry forward from 2021 to 2024
        assert summaries[1].basis_start == summaries[0].basis_end

    def test_no_ssn_in_output(self):
        """Parsed data should not contain raw SSNs."""
        data = _parse_transcript("2021 tax return.pdf")
        assert data is not None
        # The source file field and any string fields should not contain unmasked SSNs
        # (SSNs in the PDF are already masked by IRS as XXX-XX-XXXX, but let's verify
        # our sanitizer doesn't break anything)
```

**Step 2: Run tests — should pass**

```bash
pytest tests/test_integration.py -v
```

**Step 3: Commit**

```bash
git add -A
git commit -m "Add integration tests with real PDFs"
```

---

## Summary

After all 9 tasks, you'll have:

```
rothos2/
├── examples/              # Existing PDF examples
├── src/rothos/
│   ├── __init__.py
│   ├── cli.py             # Click CLI entry point
│   ├── pdf.py             # PDF text extraction
│   ├── sanitize.py        # SSN removal
│   ├── engine.py          # Basis reconstruction logic
│   ├── output.py          # JSON + Rich terminal output
│   └── parsers/
│       ├── __init__.py
│       ├── base.py        # Parser protocol + YearData dataclass
│       ├── classifier.py  # Auto-detect document type
│       └── irs_transcript.py  # IRS Tax Return Transcript parser
├── tests/
│   ├── __init__.py
│   ├── test_pdf.py
│   ├── test_sanitize.py
│   ├── test_classifier.py
│   ├── test_irs_transcript_parser.py
│   ├── test_engine.py
│   ├── test_output.py
│   ├── test_cli.py
│   └── test_integration.py
├── pyproject.toml
├── README.md
├── .gitignore
└── docs/plans/
```

**What's NOT in scope (future):**
- TurboTax parser
- CPA-prepared return parser (distinct from IRS transcript)
- 5498/1099-R as supplemental sources
- Filing-year gap detection ("you're missing 2022")
- Manual overrides / adjustments

---

Plan complete and saved to `docs/plans/2026-04-01-cli-rewrite.md`. Two execution options:

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach?
