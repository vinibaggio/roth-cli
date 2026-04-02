"""Text sanitization — remove SSNs and other PII."""

import re


def sanitize_text(text: str) -> str:
    """Remove SSNs from text while preserving other numbers.

    Masks:
    - Dashed SSNs (123-45-6789 → XXX-XX-6789)
    - 9-digit SSNs near SSN context (123456789 → XXXXX6789)

    Does NOT mask:
    - Already-masked SSNs (XXX-XX-1234)
    - Dollar amounts
    - Tracking numbers or other long numbers
    """
    # Mask dashed SSNs: 123-45-6789 → XXX-XX-6789 (keep last 4)
    # Don't re-mask already masked ones (starting with XXX)
    text = re.sub(
        r"\b(\d{3})-(\d{2})-(\d{4})\b",
        lambda m: f"XXX-XX-{m.group(3)}",
        text,
    )

    # Mask 9-digit SSNs that appear near SSN-related context
    # Only match standalone 9-digit numbers (not part of longer numbers)
    text = re.sub(
        r"(?i)(?<=SSN[:\s])\s*(\d{5})(\d{4})\b",
        lambda m: f"XXXXX{m.group(2)}",
        text,
    )

    return text
