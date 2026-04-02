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

# Output as JSON
rothos ./my-tax-returns/ --json
```

## Supported Document Types

- **IRS Tax Return Transcripts** — the primary source, includes Form 8606 data when filed

More parsers coming (TurboTax, CPA-prepared returns). The parser system is pluggable — see `src/rothos/parsers/` to add your own.

## Test Fixtures

The `fixtures/` directory contains synthetic IRS transcript PDFs with fictional data for testing.
To regenerate: `python scripts/generate_fixtures.py`

## Disclaimer

This tool is for informational and educational purposes only.
It does **not** provide tax, legal, or financial advice.
All outputs must be reviewed by a qualified tax professional.
