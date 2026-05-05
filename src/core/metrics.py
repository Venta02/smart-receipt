"""Prometheus metrics."""

from prometheus_client import Counter, Histogram, Gauge


# Request metrics
extraction_requests_total = Counter(
    "sr_extraction_requests_total",
    "Total extraction requests",
    labelnames=["status"],
)

extraction_latency_seconds = Histogram(
    "sr_extraction_latency_seconds",
    "End-to-end extraction latency",
    buckets=(0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0),
)

# OCR metrics
ocr_latency_seconds = Histogram(
    "sr_ocr_latency_seconds",
    "OCR processing latency",
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0),
)

ocr_text_blocks_total = Counter(
    "sr_ocr_text_blocks_total",
    "Total text blocks detected",
)

# Field extraction
field_extraction_total = Counter(
    "sr_field_extraction_total",
    "Field extraction attempts",
    labelnames=["field", "status"],
)

# Validation
validation_failures_total = Counter(
    "sr_validation_failures_total",
    "Validation failures",
    labelnames=["validator"],
)

# Categorization
categorization_total = Counter(
    "sr_categorization_total",
    "Receipts categorized",
    labelnames=["category"],
)

# Cache
cache_hits_total = Counter(
    "sr_cache_hits_total",
    "Cache hits",
)

cache_misses_total = Counter(
    "sr_cache_misses_total",
    "Cache misses",
)

# Active processes
active_extractions = Gauge(
    "sr_active_extractions",
    "Currently active extractions",
)
