"""Auto-categorize receipts based on merchant and items."""

from src.core.logging import get_logger
from src.core.metrics import categorization_total
from src.models import CategorizationResponse, ExtractedFields, TextBlock

logger = get_logger(__name__)


CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "food": [
        "restaurant", "cafe", "warung", "kantin", "kfc", "mcdonald", "burger",
        "pizza", "kopi", "coffee", "starbucks", "indomaret", "alfamart",
        "supermarket", "bakery", "roti", "ayam", "nasi", "mie", "bakso",
        "food", "minuman", "snack", "grocery", "fresh", "dapur",
    ],
    "transportation": [
        "gojek", "grab", "uber", "taxi", "blue bird", "transjakarta", "kereta",
        "transport", "tol", "parkir", "parking", "bensin", "fuel", "shell",
        "pertamina", "bp", "spbu", "tiket pesawat", "garuda", "lion",
    ],
    "shopping": [
        "shopee", "tokopedia", "lazada", "bukalapak", "mall", "matahari",
        "ramayana", "uniqlo", "h&m", "zara", "store", "shop", "boutique",
        "apparel", "fashion", "elektronik", "electronics", "hardware",
    ],
    "healthcare": [
        "rumah sakit", "rs", "hospital", "clinic", "klinik", "apotek",
        "pharmacy", "kimia farma", "guardian", "watson", "dokter", "doctor",
        "medical", "obat", "medicine", "lab", "laboratorium",
    ],
    "entertainment": [
        "cgv", "xxi", "cinema", "bioskop", "concert", "konser", "ticket",
        "tiket", "game", "playstation", "netflix", "spotify", "youtube",
        "karaoke", "billiard", "bowling",
    ],
    "utilities": [
        "pln", "listrik", "electricity", "pdam", "air", "water", "telkom",
        "indihome", "internet", "wifi", "pulsa", "telkomsel", "indosat",
        "xl", "smartfren", "gas",
    ],
}


class ReceiptCategorizer:
    """Lookup-based categorizer for common receipt categories."""

    def categorize(
        self,
        fields: ExtractedFields | None = None,
        blocks: list[TextBlock] | None = None,
    ) -> CategorizationResponse:
        haystack_parts = []

        if fields:
            if fields.merchant_name:
                haystack_parts.append(fields.merchant_name)
            for item in fields.items:
                if item.name:
                    haystack_parts.append(item.name)

        if blocks:
            haystack_parts.extend(b.text for b in blocks)

        haystack = " ".join(haystack_parts).lower()

        scores: dict[str, list[str]] = {}
        for category, keywords in CATEGORY_KEYWORDS.items():
            matched = [kw for kw in keywords if kw in haystack]
            if matched:
                scores[category] = matched

        if not scores:
            categorization_total.labels(category="other").inc()
            return CategorizationResponse(
                category="other",
                confidence=0.5,
                keywords_matched=[],
            )

        best_category = max(scores, key=lambda c: len(scores[c]))
        match_count = len(scores[best_category])
        confidence = min(0.5 + 0.1 * match_count, 0.95)

        categorization_total.labels(category=best_category).inc()
        return CategorizationResponse(
            category=best_category,  # type: ignore[arg-type]
            confidence=confidence,
            keywords_matched=scores[best_category],
        )
