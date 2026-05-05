"""Celery tasks for async batch processing."""

from pathlib import Path

from celery import shared_task

from src.core.logging import get_logger

logger = get_logger(__name__)


@shared_task(bind=True, max_retries=3)
def process_receipt_batch_task(self, image_paths: list[str]) -> dict:
    """Process a batch of receipt images asynchronously.

    Used when an HTTP request would take too long. Caller polls task status.
    """
    from src.services.categorization import ReceiptCategorizer
    from src.services.classification import DocumentClassifier
    from src.services.extraction import FieldExtractor
    from src.services.ocr import OCREngine
    from src.utils.image_utils import load_image_from_bytes

    ocr = OCREngine()
    extractor = FieldExtractor()
    classifier = DocumentClassifier()
    categorizer = ReceiptCategorizer()

    results = []
    for path_str in image_paths:
        path = Path(path_str)
        try:
            data = path.read_bytes()
            image = load_image_from_bytes(data)
            if image is None:
                results.append({"path": path_str, "error": "decode failed"})
                continue

            blocks = ocr.extract(image)
            classification = classifier.classify(blocks)
            fields = extractor.extract(blocks) if classification.document_type != "invalid" else None
            category = categorizer.categorize(fields=fields, blocks=blocks) if fields else None

            results.append({
                "path": path_str,
                "document_type": classification.document_type,
                "fields": fields.dict() if fields else None,
                "category": category.category if category else None,
            })
        except Exception as e:
            logger.error("Batch task error", path=path_str, error=str(e))
            results.append({"path": path_str, "error": str(e)})

    return {
        "task_id": self.request.id,
        "total": len(image_paths),
        "results": results,
    }
