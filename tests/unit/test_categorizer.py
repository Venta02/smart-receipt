"""Unit tests for ReceiptCategorizer."""

from src.models import ExtractedFields
from src.services.categorization import ReceiptCategorizer


def test_categorize_food():
    categorizer = ReceiptCategorizer()
    fields = ExtractedFields(merchant_name="Indomaret Plus")
    result = categorizer.categorize(fields=fields)
    assert result.category == "food"


def test_categorize_transportation():
    categorizer = ReceiptCategorizer()
    fields = ExtractedFields(merchant_name="GoJek")
    result = categorizer.categorize(fields=fields)
    assert result.category == "transportation"


def test_categorize_other():
    categorizer = ReceiptCategorizer()
    fields = ExtractedFields(merchant_name="Unknown Place 123")
    result = categorizer.categorize(fields=fields)
    assert result.category == "other"
