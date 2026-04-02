"""Document classifier — identifies which parser to use."""

import re


# Map of document type identifier → list of regex patterns
_PATTERNS: dict[str, list[re.Pattern]] = {
    "irs_tax_return_transcript": [
        re.compile(r"Form\s+1040\s+Tax\s+Return\s+Transcript", re.IGNORECASE),
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
