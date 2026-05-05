"""Document classification: receipt vs invoice vs other vs invalid."""

from src.core.logging import get_logger
from src.models import ClassificationResponse, TextBlock

logger = get_logger(__name__)


# Keywords associated with each document type
RECEIPT_KEYWORDS = {
    "receipt", "thank you", "cashier", "kasir", "struk", "tunai",
    "kembali", "change", "subtotal", "total bayar",
}

INVOICE_KEYWORDS = {
    "invoice", "bill to", "ship to", "due date", "payment terms",
    "faktur", "tagihan", "jatuh tempo", "po number", "purchase order",
}


class DocumentClassifier:
    """Lightweight keyword-based classifier."""

    def classify(self, blocks: list[TextBlock]) -> ClassificationResponse:
        if not blocks:
            return ClassificationResponse(
                document_type="invalid",
                confidence=1.0,
                reasons=["No text detected in image"],
            )

        text = " ".join(b.text.lower() for b in blocks)

        receipt_hits = sum(1 for kw in RECEIPT_KEYWORDS if kw in text)
        invoice_hits = sum(1 for kw in INVOICE_KEYWORDS if kw in text)

        # Heuristic: very short text is probably not a real document
        if len(blocks) < 5:
            return ClassificationResponse(
                document_type="invalid",
                confidence=0.8,
                reasons=[f"Too few text blocks detected ({len(blocks)})"],
            )

        if invoice_hits > receipt_hits and invoice_hits >= 1:
            confidence = min(0.5 + 0.15 * invoice_hits, 0.95)
            return ClassificationResponse(
                document_type="invoice",
                confidence=confidence,
                reasons=[f"Matched {invoice_hits} invoice keywords"],
            )

        if receipt_hits >= 1:
            confidence = min(0.5 + 0.15 * receipt_hits, 0.95)
            return ClassificationResponse(
                document_type="receipt",
                confidence=confidence,
                reasons=[f"Matched {receipt_hits} receipt keywords"],
            )

        # Has text but no clear keywords
        return ClassificationResponse(
            document_type="other",
            confidence=0.6,
            reasons=["No receipt or invoice keywords matched"],
        )
