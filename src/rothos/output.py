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


def to_dict(
    summaries: list[YearSummary],
    missing_years: list[int] | None = None,
) -> dict[str, Any]:
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
    return {
        "years": years,
        "missing_years": missing_years or [],
    }


def to_json(
    summaries: list[YearSummary],
    missing_years: list[int] | None = None,
    indent: int = 2,
) -> str:
    """Serialize summaries to JSON string."""
    return json.dumps(to_dict(summaries, missing_years=missing_years), indent=indent)


def _fmt(v: Decimal | None) -> str:
    """Format a decimal as dollar amount or dash."""
    if v is None:
        return "—"
    return f"${v:,.2f}"


def print_report(
    summaries: list[YearSummary],
    console: Console | None = None,
    missing_years: list[int] | None = None,
) -> None:
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

    gaps = set(missing_years or [])

    for s in summaries:
        # Insert gap rows before this year if any missing years fall between
        # the previous row and this one
        for gap_year in sorted(gaps):
            if s.tax_year > gap_year:
                table.add_row(
                    f"[red]{gap_year}[/red]",
                    "?",
                    "?",
                    "?",
                    "?",
                    "?",
                    "?",
                    "[red]MISSING[/red]",
                )
                gaps.discard(gap_year)

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

    # Print missing years warning
    if missing_years:
        console.print()
        console.print("[bold red]⚠ Missing tax years:[/bold red]")
        years_str = ", ".join(str(y) for y in missing_years)
        console.print(
            f"  [red]No transcripts found for: {years_str}[/red]"
        )
        console.print(
            "  [dim]Basis tracking may be inaccurate if IRA activity "
            "occurred in missing years.[/dim]"
        )

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
