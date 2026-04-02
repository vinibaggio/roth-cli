"""CLI entry point for rothos."""

import click


@click.command()
@click.argument("path", type=click.Path(exists=True))
def main(path: str) -> None:
    """Analyze tax return PDFs and reconstruct IRA basis history.

    PATH can be a single PDF file or a directory of PDFs.
    """
    click.echo(f"Analyzing: {path}")
