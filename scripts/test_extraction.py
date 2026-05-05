"""Smoke test for the extraction pipeline.

Usage:
    python scripts/test_extraction.py path/to/receipt.jpg
"""

import json
import sys
from pathlib import Path

import click

from src.core.logging import get_logger, setup_logging
from src.services.categorization import ReceiptCategorizer
from src.services.classification import DocumentClassifier
from src.services.extraction import FieldExtractor
from src.services.ocr import OCREngine
from src.services.validation import FieldValidator, ImageQualityValidator
from src.utils.image_utils import deskew_image, load_image_from_bytes


@click.command()
@click.argument(
    "image_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option("--no-deskew", is_flag=True, default=False)
def main(image_path: Path, no_deskew: bool):
    setup_logging()
    logger = get_logger(__name__)

    data = image_path.read_bytes()
    image = load_image_from_bytes(data)
    if image is None:
        click.echo("Failed to decode image", err=True)
        sys.exit(1)

    image_validator = ImageQualityValidator()
    quality = image_validator.validate(image)
    click.echo(f"Image quality: passed={quality.passed}")
    for issue in quality.issues:
        click.echo(f"  ! {issue}", err=True)
    for warning in quality.warnings:
        click.echo(f"  ~ {warning}")

    if not no_deskew:
        image = deskew_image(image)

    ocr = OCREngine()
    blocks = ocr.extract(image)
    click.echo(f"\nOCR detected {len(blocks)} text blocks")

    classifier = DocumentClassifier()
    classification = classifier.classify(blocks)
    click.echo(f"Document type: {classification.document_type} (conf {classification.confidence:.2f})")

    extractor = FieldExtractor()
    fields = extractor.extract(blocks)

    field_validator = FieldValidator()
    field_check = field_validator.validate(fields)

    categorizer = ReceiptCategorizer()
    category = categorizer.categorize(fields=fields, blocks=blocks)

    click.echo("\n=== Extracted fields ===")
    click.echo(json.dumps(
        json.loads(fields.model_dump_json()),
        indent=2,
        default=str,
    ))
    click.echo(f"\nCategory: {category.category} (conf {category.confidence:.2f})")
    click.echo(f"Field validation: passed={field_check.passed}")
    for issue in field_check.issues:
        click.echo(f"  ! {issue}")
    for warning in field_check.warnings:
        click.echo(f"  ~ {warning}")


if __name__ == "__main__":
    main()
