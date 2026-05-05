"""FastAPI dependency injection: cached singletons for services."""

from functools import lru_cache

from src.services.categorization import ReceiptCategorizer
from src.services.classification import DocumentClassifier
from src.services.extraction import FieldExtractor
from src.services.extraction.orchestrator import ExtractionOrchestrator
from src.services.ocr import OCREngine
from src.services.validation import FieldValidator, ImageQualityValidator


@lru_cache
def get_ocr_engine() -> OCREngine:
    return OCREngine()


@lru_cache
def get_field_extractor() -> FieldExtractor:
    return FieldExtractor()


@lru_cache
def get_orchestrator() -> ExtractionOrchestrator:
    return ExtractionOrchestrator()


@lru_cache
def get_document_classifier() -> DocumentClassifier:
    return DocumentClassifier()


@lru_cache
def get_categorizer() -> ReceiptCategorizer:
    return ReceiptCategorizer()


@lru_cache
def get_image_validator() -> ImageQualityValidator:
    return ImageQualityValidator()


@lru_cache
def get_field_validator() -> FieldValidator:
    return FieldValidator()