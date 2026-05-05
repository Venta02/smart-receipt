"""Unit tests for DocumentClassifier."""

from src.services.classification import DocumentClassifier


def test_classify_receipt(sample_blocks):
    classifier = DocumentClassifier()
    result = classifier.classify(sample_blocks)
    assert result.document_type == "receipt"
    assert result.confidence > 0.5


def test_classify_invalid_empty():
    classifier = DocumentClassifier()
    result = classifier.classify([])
    assert result.document_type == "invalid"
