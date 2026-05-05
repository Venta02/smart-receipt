"""Validation rules for image quality and extracted fields."""

from datetime import date, timedelta

import numpy as np

from src.core.config import settings
from src.core.logging import get_logger
from src.core.metrics import validation_failures_total
from src.models import ExtractedFields, ValidationResult
from src.utils.image_utils import compute_blur_score

logger = get_logger(__name__)


class ImageQualityValidator:
    """Reject images that are too small, too blurry, or unreadable."""

    def validate(self, image: np.ndarray) -> ValidationResult:
        issues: list[str] = []
        warnings: list[str] = []

        if image is None:
            return ValidationResult(
                passed=False,
                issues=["Image could not be decoded"],
            )

        h, w = image.shape[:2]

        if w < settings.min_image_width or h < settings.min_image_height:
            issues.append(
                f"Image resolution too low ({w}x{h}). "
                f"Minimum required: {settings.min_image_width}x{settings.min_image_height}"
            )
            validation_failures_total.labels(validator="resolution").inc()

        blur_score = compute_blur_score(image)
        if blur_score < settings.blur_threshold:
            issues.append(
                f"Image is too blurry (sharpness score: {blur_score:.1f}, "
                f"minimum: {settings.blur_threshold})"
            )
            validation_failures_total.labels(validator="blur").inc()
        elif blur_score < settings.blur_threshold * 1.5:
            warnings.append(f"Image sharpness is borderline ({blur_score:.1f})")

        return ValidationResult(
            passed=len(issues) == 0,
            issues=issues,
            warnings=warnings,
        )


class FieldValidator:
    """Cross-check extracted fields for internal consistency."""

    def validate(self, fields: ExtractedFields) -> ValidationResult:
        issues: list[str] = []
        warnings: list[str] = []

        # Math check: items sum should be close to subtotal/total
        if fields.items and fields.total:
            items_sum = sum(
                (item.total_price or 0) for item in fields.items
            )
            if items_sum > 0:
                # Allow 5 percent slack for rounding and missed items
                diff_ratio = abs(items_sum - fields.total) / fields.total
                if diff_ratio > 0.05:
                    warnings.append(
                        f"Items sum ({items_sum:.2f}) differs from total "
                        f"({fields.total:.2f}) by {diff_ratio*100:.1f} percent"
                    )

        # Subtotal + tax should equal total (approximately)
        if fields.subtotal and fields.tax and fields.total:
            expected_total = fields.subtotal + fields.tax
            diff = abs(expected_total - fields.total)
            if diff > max(1.0, fields.total * 0.02):
                warnings.append(
                    f"Subtotal ({fields.subtotal:.2f}) plus tax ({fields.tax:.2f}) "
                    f"differs from reported total ({fields.total:.2f})"
                )

        # Date sanity check
        if fields.receipt_date:
            today = date.today()
            future_limit = today + timedelta(days=1)
            past_limit = today - timedelta(days=365 * 10)
            if fields.receipt_date > future_limit:
                issues.append(f"Date is in the future: {fields.receipt_date}")
                validation_failures_total.labels(validator="date_future").inc()
            elif fields.receipt_date < past_limit:
                warnings.append(f"Date is more than 10 years old: {fields.receipt_date}")

        # At least one of total/subtotal/items should be present for it to be useful
        if not fields.total and not fields.subtotal and not fields.items:
            issues.append("No financial data extracted (no total, subtotal, or items)")
            validation_failures_total.labels(validator="no_amounts").inc()

        return ValidationResult(
            passed=len(issues) == 0,
            issues=issues,
            warnings=warnings,
        )
