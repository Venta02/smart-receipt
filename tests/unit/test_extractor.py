"""Unit tests for FieldExtractor."""

from datetime import date

from src.services.extraction import FieldExtractor


def test_extract_merchant(sample_blocks):
    extractor = FieldExtractor()
    fields = extractor.extract(sample_blocks)
    assert fields.merchant_name == "INDOMARET PLUS"


def test_extract_total(sample_blocks):
    extractor = FieldExtractor()
    fields = extractor.extract(sample_blocks)
    assert fields.total == 13875.0


def test_extract_subtotal(sample_blocks):
    extractor = FieldExtractor()
    fields = extractor.extract(sample_blocks)
    assert fields.subtotal == 12500.0


def test_extract_tax(sample_blocks):
    extractor = FieldExtractor()
    fields = extractor.extract(sample_blocks)
    assert fields.tax == 1375.0


def test_extract_currency(sample_blocks):
    extractor = FieldExtractor()
    fields = extractor.extract(sample_blocks)
    assert fields.currency == "IDR"


def test_extract_payment(sample_blocks):
    extractor = FieldExtractor()
    fields = extractor.extract(sample_blocks)
    assert fields.payment_method == "tunai"


def test_extract_date(sample_blocks):
    extractor = FieldExtractor()
    fields = extractor.extract(sample_blocks)
    assert fields.receipt_date == date(2026, 5, 4)


def test_extract_empty():
    extractor = FieldExtractor()
    fields = extractor.extract([])
    assert fields.merchant_name is None
    assert fields.total is None
    assert fields.items == []
