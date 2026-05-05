"""Pydantic schemas for request and response."""

from datetime import date as date_type
from typing import Any, Literal

from pydantic import BaseModel, Field


class TextBlock(BaseModel):
    text: str
    confidence: float = Field(ge=0.0, le=1.0)
    bbox: list[list[float]]


class ReceiptItem(BaseModel):
    name: str
    quantity: float | None = None
    unit_price: float | None = None
    total_price: float | None = None


class ExtractedFields(BaseModel):
    merchant_name: str | None = None
    merchant_address: str | None = None
    receipt_date: date_type | None = None
    receipt_number: str | None = None
    items: list[ReceiptItem] = Field(default_factory=list)
    subtotal: float | None = None
    tax: float | None = None
    total: float | None = None
    currency: str | None = None
    payment_method: str | None = None


class ValidationResult(BaseModel):
    passed: bool
    issues: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ExtractionResponse(BaseModel):
    request_id: str
    status: Literal["success", "partial", "failed"]
    document_type: str
    language: str
    confidence: float = Field(ge=0.0, le=1.0)
    fields: ExtractedFields
    raw_text_blocks: list[TextBlock] = Field(default_factory=list)
    validation: ValidationResult
    category: str | None = None
    latency_ms: float
    extraction_method: Literal["rule_based", "llm_fallback", "hybrid"] = "rule_based"
    metadata: dict[str, Any] = Field(default_factory=dict)


class ClassificationResponse(BaseModel):
    document_type: Literal["receipt", "invoice", "other", "invalid"]
    confidence: float = Field(ge=0.0, le=1.0)
    reasons: list[str] = Field(default_factory=list)


class CategorizationResponse(BaseModel):
    category: Literal[
        "food", "transportation", "shopping", "healthcare",
        "entertainment", "utilities", "other"
    ]
    confidence: float = Field(ge=0.0, le=1.0)
    keywords_matched: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded", "unhealthy"]
    version: str
    ocr_ready: bool
    redis_reachable: bool
    llm_available: bool = False

class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
