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
