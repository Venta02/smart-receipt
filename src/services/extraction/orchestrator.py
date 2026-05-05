"""Hybrid extraction orchestrator.

Routes between rule-based extraction and LLM Vision fallback based on
confidence and missing critical fields. Cost-aware: tries cheap rule-based
first, falls back to LLM only when needed.
"""

from typing import Literal

from src.core.config import settings
from src.core.logging import get_logger
from src.models import ExtractedFields, TextBlock
from src.services.extraction.extractor import FieldExtractor
from src.services.extraction.llm_extractor import LLMExtractor

logger = get_logger(__name__)


CRITICAL_FIELDS = ("total", "merchant_name")


class ExtractionOrchestrator:
    """Decides which extractor(s) to use based on rule-based confidence."""

    def __init__(self):
        self.rule_based = FieldExtractor()
        self.llm = LLMExtractor()

    def extract(
        self,
        blocks: list[TextBlock],
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
    ) -> tuple[ExtractedFields, Literal["rule_based", "llm_fallback", "hybrid"], dict]:
        metadata: dict = {
            "rule_based_attempted": True,
            "llm_attempted": False,
            "fallback_reason": None,
        }

        rule_fields = self.rule_based.extract(blocks)
        rule_confidence = self._estimate_confidence(rule_fields, blocks)
        metadata["rule_based_confidence"] = rule_confidence

        should_fallback, reason = self._should_fallback(rule_fields, rule_confidence)

        if not should_fallback:
            logger.info(
                "Using rule-based extraction",
                confidence=round(rule_confidence, 2),
            )
            return rule_fields, "rule_based", metadata

        metadata["fallback_reason"] = reason

        if not self.llm.is_available:
            logger.info(
                "LLM fallback would help but unavailable, using rule-based",
                reason=reason,
            )
            metadata["llm_unavailable"] = True
            return rule_fields, "rule_based", metadata

        logger.info("Triggering LLM fallback", reason=reason)
        metadata["llm_attempted"] = True

        llm_fields = self.llm.extract(image_bytes, mime_type)

        if llm_fields is None:
            logger.warning("LLM fallback failed, returning rule-based result")
            metadata["llm_failed"] = True
            return rule_fields, "rule_based", metadata

        merged_fields, used_both = self._merge_results(rule_fields, llm_fields)

        method: Literal["llm_fallback", "hybrid"] = "hybrid" if used_both else "llm_fallback"
        logger.info("Extraction complete", method=method)

        return merged_fields, method, metadata

    @staticmethod
    def _estimate_confidence(
        fields: ExtractedFields, blocks: list[TextBlock]
    ) -> float:
        if not blocks:
            return 0.0

        ocr_conf = sum(b.confidence for b in blocks) / len(blocks)

        weights = {
            "merchant_name": 0.25,
            "total": 0.30,
            "receipt_date": 0.15,
            "items": 0.15,
            "currency": 0.05,
            "receipt_number": 0.10,
        }
        completeness = 0.0
        for field, weight in weights.items():
            value = getattr(fields, field, None)
            if field == "items":
                if value and len(value) > 0:
                    completeness += weight
            elif value is not None:
                completeness += weight

        return ocr_conf * 0.4 + completeness * 0.6

    @staticmethod
    def _should_fallback(
        fields: ExtractedFields, confidence: float
    ) -> tuple[bool, str | None]:
        if not settings.llm_fallback_enabled:
            return False, None

        if confidence < settings.confidence_threshold:
            return True, f"confidence {confidence:.2f} below threshold {settings.confidence_threshold}"

        missing = []
        for field in CRITICAL_FIELDS:
            if getattr(fields, field, None) is None:
                missing.append(field)
        if missing:
            return True, f"missing critical fields: {', '.join(missing)}"

        if fields.total is not None and fields.total <= 0:
            return True, "invalid total amount"

        return False, None

    @staticmethod
    def _merge_results(
        rule_fields: ExtractedFields, llm_fields: ExtractedFields
    ) -> tuple[ExtractedFields, bool]:
        used_both = False

        merged = ExtractedFields(
            merchant_name=llm_fields.merchant_name or rule_fields.merchant_name,
            merchant_address=llm_fields.merchant_address or rule_fields.merchant_address,
            receipt_date=llm_fields.receipt_date or rule_fields.receipt_date,
            receipt_number=llm_fields.receipt_number or rule_fields.receipt_number,
            items=llm_fields.items if llm_fields.items else rule_fields.items,
            subtotal=llm_fields.subtotal if llm_fields.subtotal is not None else rule_fields.subtotal,
            tax=llm_fields.tax if llm_fields.tax is not None else rule_fields.tax,
            total=llm_fields.total if llm_fields.total is not None else rule_fields.total,
            currency=llm_fields.currency or rule_fields.currency,
            payment_method=llm_fields.payment_method or rule_fields.payment_method,
        )

        for field in ["merchant_name", "receipt_date", "total", "currency"]:
            llm_val = getattr(llm_fields, field, None)
            rule_val = getattr(rule_fields, field, None)
            if llm_val is None and rule_val is not None:
                used_both = True
                break

        return merged, used_both
