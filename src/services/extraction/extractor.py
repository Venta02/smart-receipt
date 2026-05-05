"""Field extraction from OCR text blocks.

Uses horizontal pairing (label-left, value-right same row or below) for
amounts. Falls back to heuristics: total is typically the largest amount
near the bottom of the receipt.
"""

import math
import re

from src.core.logging import get_logger
from src.core.metrics import field_extraction_total
from src.models import ExtractedFields, ReceiptItem, TextBlock
from src.services.extraction.parsers import parse_amount, parse_date
from src.services.extraction.patterns import (
    BUSINESS_SUFFIXES,
    CURRENCY_PATTERN,
    CURRENCY_SYMBOLS,
    DATE_PATTERNS,
    DEFAULT_CURRENCY,
    PAYMENT_PATTERNS,
    RECEIPT_NUMBER_PATTERNS,
    SUBTOTAL_PATTERNS,
    TAX_PATTERNS,
    TOTAL_PATTERNS,
)

logger = get_logger(__name__)


MERCHANT_BLACKLIST = {
    "tax invoice", "receipt", "invoice", "invoice no", "invoice no.",
    "invoice number", "invoice #", "no.nota", "nota", "no nota",
    "struk", "tax",
    "cash", "cash customer", "cashler", "cashler#", "cashier",
    "thank you", "please come again",
    "date", "date:",
    "subtotal", "total", "total bell", "total beli", "total bayar", "payment",
    "change due", "rounding adjustment", "sisa hutang",
    "tel", "fax", "company reg no", "gst reg no",
    "pembell", "pembeli",
    "qty", "amount", "summary",
    "kp.", "jl.", "jalan",
    "pju",
}

ITEM_NAME_BLACKLIST = {
    "ikt", "1ikt", "5bksx", "bksx", "kp.parapatan", "kp parapatan",
    "pju", "no.nota", "pembell", "sisa hutang", "total bell",
    "amount", "qty", "summary",
}


def is_money_format(text: str) -> bool:
    """Check if text looks like a monetary value."""
    cleaned = text.strip()
    if not cleaned:
        return False
    cleaned = re.sub(r"^(RM|Rp|MYR|IDR|\$|\s)+", "", cleaned, flags=re.IGNORECASE).strip()

    money_patterns = [
        re.compile(r"^\d{1,3}(?:[.,]\d{3})+$"),
        re.compile(r"^\d{1,3}(?:[.,]\d{3})*[.,]\d{2}$"),
        re.compile(r"^\d+[.,]\d{2}$"),
        re.compile(r"^\d{4,7}$"),
    ]
    return any(p.match(cleaned) for p in money_patterns)


def parse_money(text: str) -> float | None:
    cleaned = re.sub(r"^(RM|Rp|MYR|IDR|\$)\s*", "", text.strip(), flags=re.IGNORECASE).strip()
    if not is_money_format(cleaned):
        return None
    return parse_amount(cleaned)


def block_center(block: TextBlock) -> tuple[float, float]:
    if not block.bbox:
        return (0.0, 0.0)
    xs = [p[0] for p in block.bbox]
    ys = [p[1] for p in block.bbox]
    return (sum(xs) / len(xs), sum(ys) / len(ys))


def block_right(block: TextBlock) -> float:
    if not block.bbox:
        return 0.0
    return max(p[0] for p in block.bbox)


def block_left(block: TextBlock) -> float:
    if not block.bbox:
        return 0.0
    return min(p[0] for p in block.bbox)


def block_height(block: TextBlock) -> float:
    if not block.bbox:
        return 1.0
    ys = [p[1] for p in block.bbox]
    return max(max(ys) - min(ys), 1.0)


class FieldExtractor:
    """Spatial extractor with horizontal pairing logic."""

    def extract(self, blocks: list[TextBlock]) -> ExtractedFields:
        if not blocks:
            return ExtractedFields()

        all_text = " ".join(b.text for b in blocks)

        money_blocks = [
            b for b in blocks if parse_money(b.text) is not None
        ]

        merchant = self._extract_merchant(blocks)
        receipt_date = self._extract_date(all_text)
        receipt_number = self._extract_receipt_number(all_text, blocks)
        currency = self._extract_currency(all_text)
        payment = self._extract_payment_method(all_text)

        total = self._extract_total(blocks, money_blocks, all_text)
        subtotal = self._extract_subtotal(blocks, money_blocks, all_text, total)
        tax = self._extract_tax(blocks, money_blocks, all_text)

        items = self._extract_items(blocks, money_blocks, total, subtotal, tax)

        self._track_extraction("merchant", merchant)
        self._track_extraction("date", receipt_date)
        self._track_extraction("total", total)

        return ExtractedFields(
            merchant_name=merchant,
            receipt_date=receipt_date,
            receipt_number=receipt_number,
            items=items,
            subtotal=subtotal,
            tax=tax,
            total=total,
            currency=currency,
            payment_method=payment,
        )

    @staticmethod
    def _extract_merchant(blocks: list[TextBlock]) -> str | None:
        for block in blocks:
            text = block.text.strip()
            text_lower = text.lower()
            for suffix in BUSINESS_SUFFIXES:
                if re.search(rf"\b{re.escape(suffix)}\b", text_lower):
                    return text

        store_keywords = ["toko", "warung", "rumah makan", "restoran", "kedai", "cafe", "kafe", "shop", "ud "]
        for block in blocks:
            text = block.text.strip()
            text_lower = text.lower()
            if any(kw in text_lower for kw in store_keywords):
                return text

        sorted_blocks = sorted(blocks, key=lambda b: b.bbox[0][1] if b.bbox else 0)
        for block in sorted_blocks:
            text = block.text.strip()
            text_lower = text.lower()
            if len(text) < 3:
                continue
            if text_lower in MERCHANT_BLACKLIST:
                continue
            if any(bl in text_lower for bl in MERCHANT_BLACKLIST):
                continue
            digit_ratio = sum(c.isdigit() for c in text) / max(len(text), 1)
            if digit_ratio > 0.3:
                continue
            if is_money_format(text):
                continue
            return text
        return None

    @staticmethod
    def _extract_date(text: str):
        for pattern in DATE_PATTERNS:
            match = pattern.search(text)
            if match:
                parsed = parse_date(match.group(1))
                if parsed:
                    return parsed
        compressed = re.sub(r"\s+", "", text)
        for pattern in DATE_PATTERNS:
            match = pattern.search(compressed)
            if match:
                parsed = parse_date(match.group(1))
                if parsed:
                    return parsed
        return None

    @staticmethod
    def _extract_receipt_number(text: str, blocks: list[TextBlock]) -> str | None:
        for pattern in RECEIPT_NUMBER_PATTERNS:
            match = pattern.search(text)
            if match:
                return match.group(1)

        label_keywords = [
            "no.nota", "no. nota", "no nota", "nomor nota",
            "invoice no", "receipt no", "trans no", "bill no",
        ]
        for label_kw in label_keywords:
            for label_block in blocks:
                if label_kw not in label_block.text.lower():
                    continue
                label_cx, label_cy = block_center(label_block)
                best = None
                best_dist = float("inf")
                for cand in blocks:
                    if cand is label_block:
                        continue
                    cand_text = cand.text.strip()
                    if not re.match(r"^[A-Z]?\d{4,}[\w\-]*$", cand_text, re.IGNORECASE):
                        continue
                    cx, cy = block_center(cand)
                    dist = math.hypot(cx - label_cx, cy - label_cy)
                    if dist < best_dist and dist < 250:
                        best_dist = dist
                        best = cand_text
                if best:
                    return best
        return None

    @staticmethod
    def _extract_currency(text: str) -> str:
        """Detect currency from text. Default to IDR if no symbol found."""
        match = CURRENCY_PATTERN.search(text)
        if not match:
            return DEFAULT_CURRENCY
        # Pattern has 2 groups: word-bounded codes, or special symbols
        symbol = match.group(1) or match.group(2)
        if not symbol:
            return DEFAULT_CURRENCY
        for key, value in CURRENCY_SYMBOLS.items():
            if key.lower() == symbol.lower():
                return value
        return DEFAULT_CURRENCY

    @staticmethod
    def _extract_payment_method(text: str) -> str | None:
        for pattern in PAYMENT_PATTERNS:
            match = pattern.search(text)
            if match:
                return match.group(1).lower().replace("  ", " ")
        return None

    def _find_value_horizontal(
        self,
        label_block: TextBlock,
        money_blocks: list[TextBlock],
        max_y_diff: float = 50.0,
    ) -> tuple[float, TextBlock] | None:
        label_cx, label_cy = block_center(label_block)
        label_right_edge = block_right(label_block)

        same_line = []
        for mb in money_blocks:
            mb_cx, mb_cy = block_center(mb)
            if abs(mb_cy - label_cy) > max_y_diff:
                continue
            same_line.append(mb)

        if not same_line:
            return None

        right_of_label = [
            mb for mb in same_line if block_left(mb) >= label_right_edge - 30
        ]
        if right_of_label:
            chosen = max(right_of_label, key=block_right)
            amount = parse_money(chosen.text)
            if amount is not None:
                return amount, chosen

        chosen = min(same_line, key=lambda b: abs(block_center(b)[0] - label_cx))
        amount = parse_money(chosen.text)
        if amount is not None:
            return amount, chosen
        return None

    def _extract_total(
        self,
        blocks: list[TextBlock],
        money_blocks: list[TextBlock],
        all_text: str,
    ) -> float | None:
        for pattern in TOTAL_PATTERNS:
            match = pattern.search(all_text)
            if match:
                raw = match.group(1)
                if is_money_format(raw):
                    amount = parse_amount(raw)
                    if amount and 0 < amount < 100_000_000:
                        return amount

        keywords = [
            "total bayar", "total beli", "total bell",
            "total amt incl", "total amt payable",
            "grand total", "total amount",
            "amount due", "amount paid",
        ]
        for kw in keywords:
            for block in blocks:
                if kw in block.text.lower():
                    result = self._find_value_horizontal(block, money_blocks)
                    if result:
                        return result[0]

        if money_blocks:
            ys = [block_center(b)[1] for b in blocks if b.bbox]
            if ys:
                median_y = sorted(ys)[len(ys) // 2]
                lower_money = [
                    (parse_money(b.text), b)
                    for b in money_blocks
                    if block_center(b)[1] >= median_y
                ]
                lower_money = [(a, b) for a, b in lower_money if a is not None]
                if lower_money:
                    return max(lower_money, key=lambda x: x[0])[0]
        return None

    def _extract_subtotal(
        self,
        blocks: list[TextBlock],
        money_blocks: list[TextBlock],
        all_text: str,
        total: float | None,
    ) -> float | None:
        for pattern in SUBTOTAL_PATTERNS:
            match = pattern.search(all_text)
            if match:
                raw = match.group(1)
                if is_money_format(raw):
                    amount = parse_amount(raw)
                    if amount and 0 < amount < 100_000_000:
                        return amount

        keywords = ["subtotal", "sub total", "sub-total", "total sales excluding"]
        for kw in keywords:
            for block in blocks:
                if kw in block.text.lower():
                    result = self._find_value_horizontal(block, money_blocks)
                    if result:
                        return result[0]
        return None

    def _extract_tax(
        self,
        blocks: list[TextBlock],
        money_blocks: list[TextBlock],
        all_text: str,
    ) -> float | None:
        for pattern in TAX_PATTERNS:
            match = pattern.search(all_text)
            if match:
                raw = match.group(1)
                if is_money_format(raw):
                    amount = parse_amount(raw)
                    if amount and 0 < amount < 100_000_000:
                        return amount

        keywords = ["tax amount", "gst amount", "sst amount", "ppn"]
        for kw in keywords:
            for block in blocks:
                if kw in block.text.lower():
                    result = self._find_value_horizontal(block, money_blocks)
                    if result:
                        return result[0]
        return None

    def _extract_items(
        self,
        blocks: list[TextBlock],
        money_blocks: list[TextBlock],
        total: float | None,
        subtotal: float | None,
        tax: float | None,
    ) -> list[ReceiptItem]:
        skip_text_keywords = [
            "total", "subtotal", "sub total", "tax", "ppn", "vat", "gst", "sst",
            "jumlah", "bayar", "tunai", "change", "kembali", "payment",
            "discount", "diskon", "service", "biaya",
            "rounding", "adjustment", "due", "balance",
            "invoice", "receipt", "cashier", "kasir", "cashler",
            "tel", "fax", "reg no", "company",
            "no.nota", "no nota", "nota", "nomor",
            "sisa hutang", "pembell", "pembeli",
            "qty", "amount", "summary",
            "kp.", "jl.", "jalan",
        ]

        amounts_to_skip = {a for a in [total, subtotal, tax] if a is not None}

        item_candidates: list[TextBlock] = []
        for block in blocks:
            text = block.text.strip()
            text_lower = text.lower()
            if len(text) < 3:
                continue
            if text_lower in ITEM_NAME_BLACKLIST:
                continue
            if any(kw in text_lower for kw in skip_text_keywords):
                continue
            digit_ratio = sum(c.isdigit() for c in text) / max(len(text), 1)
            if digit_ratio > 0.4:
                continue
            if is_money_format(text):
                continue
            if not any(c.isalpha() for c in text):
                continue
            item_candidates.append(block)

        items: list[ReceiptItem] = []
        used_money_block_ids = set()

        for item_block in item_candidates:
            available = [
                mb for i, mb in enumerate(money_blocks)
                if i not in used_money_block_ids
            ]
            if not available:
                break

            ix, iy = block_center(item_block)
            iheight = block_height(item_block)
            row_threshold = max(iheight * 1.5, 30.0)

            best = None
            best_dist = float("inf")
            best_idx_in_money = None

            for idx, mb in enumerate(money_blocks):
                if idx in used_money_block_ids:
                    continue
                amount = parse_money(mb.text)
                if amount is None or amount <= 0:
                    continue
                if amount in amounts_to_skip:
                    continue

                cx, cy = block_center(mb)
                y_diff = abs(cy - iy)
                if y_diff > row_threshold:
                    continue

                x_diff = cx - ix
                if x_diff < -100:
                    continue

                dist = math.hypot(abs(x_diff), y_diff * 2)
                if dist < best_dist:
                    best_dist = dist
                    best = (amount, mb)
                    best_idx_in_money = idx

            if best is not None and best_idx_in_money is not None:
                used_money_block_ids.add(best_idx_in_money)
                items.append(ReceiptItem(
                    name=item_block.text.strip(),
                    quantity=None,
                    total_price=best[0],
                    unit_price=None,
                ))

        return items

    @staticmethod
    def _track_extraction(field: str, value) -> None:
        status = "found" if value is not None else "missing"
        field_extraction_total.labels(field=field, status=status).inc()
