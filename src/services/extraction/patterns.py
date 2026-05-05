"""Regex patterns for receipt field extraction.

Supports Indonesian, English, and Malaysian receipt formats. Patterns are
ordered by specificity so more specific matches take precedence.
"""

import re

# Total / grand total
TOTAL_PATTERNS = [
    re.compile(r"\btotal\s*sales?\s*inclusive\s*(?:of\s*)?(?:gst|sst|tax)?\s*[:.]?\s*([\d.,]+)", re.IGNORECASE),
    re.compile(r"\b(?:grand\s*total|total\s*amount|amount\s*due|amount\s*paid)\b\s*[:.]?\s*([\d.,]+)", re.IGNORECASE),
    re.compile(r"\b(?:total\s*bayar|total\s*akhir|grand\s*total|jumlah\s*bayar)\b\s*[:.]?\s*([\d.,]+)", re.IGNORECASE),
    re.compile(r"\bpayment\b\s*[:.]?\s*([\d.,]+)", re.IGNORECASE),
    re.compile(r"(?<!sub)(?<!sub\s)\btotal\b\s*[:.]?\s*([\d.,]+)", re.IGNORECASE),
    re.compile(r"\bjumlah\b\s*[:.]?\s*([\d.,]+)", re.IGNORECASE),
]

# Subtotal
SUBTOTAL_PATTERNS = [
    re.compile(r"\b(?:sub[\s\-]?total|sub\s*jumlah)\b\s*[:.]?\s*([\d.,]+)", re.IGNORECASE),
    re.compile(r"\btotal\s*sales?\s*excluding\s*(?:gst|sst|tax)?\s*[:.]?\s*([\d.,]+)", re.IGNORECASE),
]

# Tax / VAT / GST / SST / PPN
TAX_PATTERNS = [
    re.compile(r"\b(?:tax\s*amount|gst\s*amount|sst\s*amount|vat\s*amount)\b\s*[:.]?\s*([\d.,]+)", re.IGNORECASE),
    re.compile(r"\b(?:ppn|pajak|pajak\s*pertambahan)\s*\d*[%]?\s*[:.]?\s*([\d.,]+)", re.IGNORECASE),
    re.compile(r"\b(?:tax|vat|sales\s*tax)\s*\d*[%]?\s*[:.]?\s*([\d.,]+)", re.IGNORECASE),
    re.compile(r"\b(?:gst|sst)\s*\d*[%]?\s*[:.]?\s*([\d.,]+)", re.IGNORECASE),
]

# Date patterns
DATE_PATTERNS = [
    re.compile(r"\b(\d{4}[-/]\d{1,2}[-/]\d{1,2})\b"),
    re.compile(r"\b(\d{1,2}[-/]\d{1,2}[-/]\d{4})(?=\d{1,2}[:.]\d{2})"),
    re.compile(r"\b(\d{1,2}[-/]\d{1,2}[-/]\d{4})\b"),
    re.compile(r"\b(\d{1,2}[-/]\d{1,2}[-/]\d{2})\b"),
    re.compile(r"\b(\d{1,2}\.\d{1,2}\.\d{2,4})\b"),
    re.compile(
        r"\b(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|"
        r"januari|februari|maret|april|mei|juni|juli|agustus|september|oktober|november|desember)\w*\s+\d{2,4})\b",
        re.IGNORECASE,
    ),
]

# Receipt / invoice number
RECEIPT_NUMBER_PATTERNS = [
    re.compile(r"\b(?:invoice\s*(?:no|number|num|#)|inv\s*(?:no|#))\s*[:.#]?\s*([A-Z0-9][A-Z0-9\-]{3,})", re.IGNORECASE),
    re.compile(r"\b(?:receipt\s*(?:no|number|num|#)|trans(?:action)?\s*(?:no|#)|nomor\s*struk|no\.\s*struk)\s*[:.#]?\s*([A-Z0-9][A-Z0-9\-]{3,})", re.IGNORECASE),
    re.compile(r"\b(?:bill\s*(?:no|number|#)|order\s*(?:no|number|#))\s*[:.#]?\s*([A-Z0-9][A-Z0-9\-]{3,})", re.IGNORECASE),
]

# Currency detection - default to IDR
DEFAULT_CURRENCY = "IDR"

CURRENCY_SYMBOLS = {
    "Rp": "IDR",
    "IDR": "IDR",
    "RM": "MYR",
    "MYR": "MYR",
    "S$": "SGD",
    "SGD": "SGD",
    "USD": "USD",
    "$": "USD",
    "€": "EUR",
    "EUR": "EUR",
    "£": "GBP",
    "GBP": "GBP",
    "¥": "JPY",
    "JPY": "JPY",
    "฿": "THB",
    "THB": "THB",
    "₫": "VND",
    "VND": "VND",
}

# Stricter pattern: currency must appear as standalone word with word boundary
# This prevents random matches like "RM" inside other text
CURRENCY_PATTERN = re.compile(
    r"\b(Rp|IDR|RM|MYR|SGD|USD|EUR|GBP|JPY|THB|VND)\b|(?<!\w)(S\$|\$|€|£|¥|฿|₫)(?!\w)",
)

# Item line: name followed by optional qty and price.
ITEM_LINE_PATTERN = re.compile(
    r"^(?P<name>[A-Za-z][A-Za-z0-9\s\-/&.()#]{2,40}?)\s+"
    r"(?:(?:x|@)?\s*(?P<qty>\d+(?:\.\d+)?)\s+(?:pc|pcs|kg|g|ml|l|x)?\s*)?"
    r"(?P<price>\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)\s*$",
    re.IGNORECASE,
)

# Payment method
PAYMENT_PATTERNS = [
    re.compile(
        r"\b(cash|tunai|credit\s*card|debit\s*card|kartu\s*kredit|kartu\s*debit|"
        r"qris|gopay|ovo|dana|shopeepay|linkaja|"
        r"transfer|bank\s*transfer|"
        r"visa|mastercard|amex|"
        r"touch\s*n\s*go|tng|grabpay|boost)\b",
        re.IGNORECASE,
    ),
]

# Business entity suffixes for merchant detection
BUSINESS_SUFFIXES = [
    "sdn bhd", "sdn. bhd.", "berhad",
    "pt", "pt.", "cv", "cv.",
    "tbk", "persero",
    "ltd", "ltd.", "limited", "llc", "inc", "inc.", "corp", "corp.",
    "pte ltd", "pte. ltd.",
    "co.", "company",
]

# Indonesian month name to number
ID_MONTHS = {
    "januari": 1, "februari": 2, "maret": 3, "april": 4, "mei": 5, "juni": 6,
    "juli": 7, "agustus": 8, "september": 9, "oktober": 10, "november": 11, "desember": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6,
    "jul": 7, "agu": 8, "sep": 9, "okt": 10, "nov": 11, "des": 12,
}
