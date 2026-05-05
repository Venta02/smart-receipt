"""Receipt extraction, classification, and categorization endpoints."""

import time
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from src.api.dependencies import (
    get_categorizer,
    get_document_classifier,
    get_field_extractor,
    get_field_validator,
    get_image_validator,
    get_ocr_engine,
    get_orchestrator,
)
from src.core.config import settings
from src.core.logging import get_logger
from src.core.metrics import (
    active_extractions,
    extraction_latency_seconds,
    extraction_requests_total,
)
from src.models import (
    CategorizationResponse,
    ClassificationResponse,
    ExtractionResponse,
    ValidationResult,
)
from src.services.categorization import ReceiptCategorizer
from src.services.classification import DocumentClassifier
from src.services.extraction import FieldExtractor
from src.services.extraction.orchestrator import ExtractionOrchestrator
from src.services.ocr import OCREngine
from src.services.validation import FieldValidator, ImageQualityValidator
from src.utils.image_utils import deskew_image, load_image_from_bytes

logger = get_logger(__name__)

router = APIRouter(prefix="/receipts", tags=["receipts"])


async def _read_image_with_bytes(file: UploadFile) -> tuple:
    """Read upload, return (image_array, raw_bytes, mime_type)."""
    contents = await file.read()
    max_bytes = settings.max_image_size_mb * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image exceeds {settings.max_image_size_mb}MB limit",
        )
    image = load_image_from_bytes(contents)
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not decode uploaded file as image",
        )
    mime_type = file.content_type or "image/jpeg"
    return image, contents, mime_type


@router.post("/extract", response_model=ExtractionResponse)
async def extract_receipt(
    file: UploadFile = File(...),
    deskew: bool = True,
    ocr: OCREngine = Depends(get_ocr_engine),
    orchestrator: ExtractionOrchestrator = Depends(get_orchestrator),
    classifier: DocumentClassifier = Depends(get_document_classifier),
    categorizer: ReceiptCategorizer = Depends(get_categorizer),
    image_validator: ImageQualityValidator = Depends(get_image_validator),
    field_validator: FieldValidator = Depends(get_field_validator),
) -> ExtractionResponse:
    """Full hybrid extraction pipeline."""

    request_id = str(uuid.uuid4())
    start = time.perf_counter()
    active_extractions.inc()

    try:
        image, raw_bytes, mime_type = await _read_image_with_bytes(file)

        image_check = image_validator.validate(image)
        if not image_check.passed:
            extraction_requests_total.labels(status="failed").inc()
            return ExtractionResponse(
                request_id=request_id,
                status="failed",
                document_type="unknown",
                language=ocr.lang,
                confidence=0.0,
                fields={},
                raw_text_blocks=[],
                validation=image_check,
                latency_ms=round((time.perf_counter() - start) * 1000, 2),
                extraction_method="rule_based",
            )

        if deskew:
            image = deskew_image(image)

        blocks = ocr.extract(image)

        classification = classifier.classify(blocks)

        if classification.document_type == "invalid":
            extraction_requests_total.labels(status="failed").inc()
            return ExtractionResponse(
                request_id=request_id,
                status="failed",
                document_type=classification.document_type,
                language=ocr.lang,
                confidence=classification.confidence,
                fields={},
                raw_text_blocks=blocks,
                validation=ValidationResult(
                    passed=False,
                    issues=classification.reasons,
                ),
                latency_ms=round((time.perf_counter() - start) * 1000, 2),
                extraction_method="rule_based",
            )

        fields, method, extraction_metadata = orchestrator.extract(
            blocks, raw_bytes, mime_type
        )

        field_check = field_validator.validate(fields)
        category_result = categorizer.categorize(fields=fields, blocks=blocks)

        avg_confidence = (
            sum(b.confidence for b in blocks) / len(blocks) if blocks else 0.0
        )

        elapsed = time.perf_counter() - start
        extraction_latency_seconds.observe(elapsed)

        result_status = "success" if field_check.passed else "partial"
        extraction_requests_total.labels(status=result_status).inc()

        return ExtractionResponse(
            request_id=request_id,
            status=result_status,
            document_type=classification.document_type,
            language=ocr.lang,
            confidence=avg_confidence,
            fields=fields,
            raw_text_blocks=blocks,
            validation=field_check,
            category=category_result.category,
            latency_ms=round(elapsed * 1000, 2),
            extraction_method=method,
            metadata={
                "classification_confidence": classification.confidence,
                "categorization_confidence": category_result.confidence,
                "deskew_applied": deskew,
                **extraction_metadata,
            },
        )
    except HTTPException:
        extraction_requests_total.labels(status="error").inc()
        raise
    except Exception as e:
        extraction_requests_total.labels(status="error").inc()
        logger.error("Extraction failed", request_id=request_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Extraction pipeline failed. Please try a different image.",
        ) from e
    finally:
        active_extractions.dec()


@router.post("/classify", response_model=ClassificationResponse)
async def classify_document(
    file: UploadFile = File(...),
    ocr: OCREngine = Depends(get_ocr_engine),
    classifier: DocumentClassifier = Depends(get_document_classifier),
) -> ClassificationResponse:
    image, _, _ = await _read_image_with_bytes(file)
    blocks = ocr.extract(image)
    return classifier.classify(blocks)


@router.post("/categorize", response_model=CategorizationResponse)
async def categorize_receipt(
    file: UploadFile = File(...),
    ocr: OCREngine = Depends(get_ocr_engine),
    extractor: FieldExtractor = Depends(get_field_extractor),
    categorizer: ReceiptCategorizer = Depends(get_categorizer),
) -> CategorizationResponse:
    image, _, _ = await _read_image_with_bytes(file)
    blocks = ocr.extract(image)
    fields = extractor.extract(blocks)
    return categorizer.categorize(fields=fields, blocks=blocks)