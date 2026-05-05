"""LLM-based receipt extraction using Gemini Vision.

Used as fallback when rule-based extraction has low confidence or
critical fields are missing.
"""

import json
import re
import time
from datetime import datetime

from src.core.config import settings
from src.core.logging import get_logger
from src.core.metrics import field_extraction_total
from src.models import ExtractedFields, ReceiptItem

logger = get_logger(__name__)


EXTRACTION_PROMPT = """You are a receipt data extractor. Analyze the receipt image and extract the following fields.

Return ONLY a valid JSON object with this exact schema, no markdown, no explanation:

{
  "merchant_name": string or null,
  "merchant_address": string or null,
  "receipt_date": "YYYY-MM-DD" or null,
  "receipt_number": string or null,
  "items": [
    {
      "name": string,
      "quantity": number or null,
      "unit_price": number or null,
      "total_price": number
    }
  ],
  "subtotal": number or null,
  "tax": number or null,
  "total": number,
  "currency": "IDR" or "MYR" or "USD" or "SGD" or other ISO code or null,
  "payment_method": string or null
}

Rules:
- Use null when a field cannot be determined
- All amounts are numbers (no currency symbols, no thousand separators)
- Date must be ISO format YYYY-MM-DD
- For Indonesian receipts, default currency is IDR
- For Malaysian receipts (with RM, SDN BHD, GST), default currency is MYR
- Items array can be empty if no items are detected
- Be precise: extract only what is visible, do not hallucinate
"""


class LLMExtractor:
    """Wraps Gemini Vision for receipt extraction."""

    def __init__(self):
        self._client = None
        self._available = bool(settings.gemini_api_key)
        if not self._available:
            logger.info("LLM extractor disabled (no API key)")
            return

    def _lazy_init(self) -> None:
        if self._client is not None or not self._available:
            return
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.gemini_api_key)
            self._client = genai.GenerativeModel(settings.llm_model)
            logger.info("LLM extractor initialized", model=settings.llm_model)
        except Exception as e:
            logger.error("Failed to initialize LLM extractor", error=str(e))
            self._available = False

    @property
    def is_available(self) -> bool:
        return self._available

    def extract(self, image_bytes: bytes, mime_type: str = "image/jpeg") -> ExtractedFields | None:
        if not self._available:
            return None

        self._lazy_init()
        if self._client is None:
            return None

        start = time.perf_counter()
        try:
            response = self._client.generate_content(
                [
                    EXTRACTION_PROMPT,
                    {"mime_type": mime_type, "data": image_bytes},
                ],
                request_options={"timeout": settings.llm_timeout_seconds},
            )
        except Exception as e:
            logger.error("LLM extraction failed", error=str(e))
            return None

        elapsed = time.perf_counter() - start
        logger.info("LLM extraction completed", latency_ms=round(elapsed * 1000, 2))

        if not response or not hasattr(response, "text"):
            return None

        return self._parse_response(response.text)

    @staticmethod
    def _parse_response(text: str) -> ExtractedFields | None:
        if not text:
            return None

        cleaned = text.strip()
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.warning("Failed to parse LLM JSON response", error=str(e), raw=cleaned[:200])
            return None

        try:
            date_str = data.get("receipt_date")
            receipt_date = None
            if date_str:
                try:
                    receipt_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                except (ValueError, TypeError):
                    pass

            items_raw = data.get("items") or []
            items = []
            for item_data in items_raw:
                if not isinstance(item_data, dict):
                    continue
                name = item_data.get("name")
                if not name:
                    continue
                items.append(ReceiptItem(
                    name=str(name),
                    quantity=item_data.get("quantity"),
                    unit_price=item_data.get("unit_price"),
                    total_price=item_data.get("total_price"),
                ))

            fields = ExtractedFields(
                merchant_name=data.get("merchant_name"),
                merchant_address=data.get("merchant_address"),
                receipt_date=receipt_date,
                receipt_number=data.get("receipt_number"),
                items=items,
                subtotal=data.get("subtotal"),
                tax=data.get("tax"),
                total=data.get("total"),
                currency=data.get("currency"),
                payment_method=data.get("payment_method"),
            )

            for field_name, value in [
                ("merchant", fields.merchant_name),
                ("date", fields.receipt_date),
                ("total", fields.total),
            ]:
                status = "found" if value is not None else "missing"
                field_extraction_total.labels(field=f"llm_{field_name}", status=status).inc()

            return fields
        except Exception as e:
            logger.error("Failed to map LLM response to schema", error=str(e))
            return None
