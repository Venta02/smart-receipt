"""Locale-aware parsers for amounts and dates."""

import re
from datetime import date, datetime

from dateutil import parser as date_parser

from src.services.extraction.patterns import ID_MONTHS


def parse_amount(text: str) -> float | None:
    """Parse a numeric amount string with mixed thousand/decimal separators.

    Handles:
        50,000 (Indonesian thousand) -> 50000.0
        50.000 (Indonesian thousand) -> 50000.0
        50,000.50 (US) -> 50000.50
        50.000,50 (Indonesian decimal) -> 50000.50
    """
    if not text:
        return None

    cleaned = re.sub(r"[^\d.,]", "", text)
    if not cleaned:
        return None

    has_dot = "." in cleaned
    has_comma = "," in cleaned

    if has_dot and has_comma:
        # Last separator is the decimal
        if cleaned.rfind(",") > cleaned.rfind("."):
            # Indonesian: 50.000,50
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            # US: 50,000.50
            cleaned = cleaned.replace(",", "")
    elif has_comma:
        # Could be thousand or decimal. Heuristic: if 3 digits after, thousand.
        comma_pos = cleaned.rfind(",")
        digits_after = len(cleaned) - comma_pos - 1
        if digits_after == 3 and cleaned.count(",") >= 1:
            cleaned = cleaned.replace(",", "")
        else:
            cleaned = cleaned.replace(",", ".")
    elif has_dot:
        # Could be thousand or decimal
        dot_pos = cleaned.rfind(".")
        digits_after = len(cleaned) - dot_pos - 1
        if digits_after == 3 and cleaned.count(".") >= 1:
            # Indonesian thousand separator like 50.000
            cleaned = cleaned.replace(".", "")

    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_date(text: str) -> date | None:
    """Try multiple strategies to parse a date string."""
    if not text:
        return None

    text = text.strip()

    # Try Indonesian month names first
    for id_name, month_num in ID_MONTHS.items():
        if id_name in text.lower():
            text = re.sub(id_name, str(month_num), text, flags=re.IGNORECASE)
            try:
                # After substitution, fall through to dateutil
                pass
            except Exception:
                pass

    # Common explicit formats
    explicit_formats = [
        "%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y",
        "%d-%m-%y", "%d/%m/%y", "%m-%d-%Y", "%m/%d/%Y",
        "%d %m %Y", "%d %m %y",
    ]
    for fmt in explicit_formats:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue

    # Last resort: dateutil parse with day-first preference for ID/EU formats
    try:
        return date_parser.parse(text, dayfirst=True, fuzzy=True).date()
    except (ValueError, TypeError, OverflowError):
        return None
