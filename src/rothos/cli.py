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
