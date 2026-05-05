# Architecture

## Overview

smart-receipt is a layered FastAPI application that processes receipt
images through a pipeline of specialized services. The dependency
direction is one-way: API depends on services, services depend on core,
core depends on nothing.

## Pipeline

A single extraction request flows through these stages:

1. **Image upload validation**
   Reject files that exceed the size limit or fail to decode.

2. **Image quality check**
   Reject low-resolution or extremely blurry images using a Laplacian
   variance threshold.

3. **Deskew (optional)**
   Detect skew angle from text orientation and rotate to deskew.

4. **OCR**
   PaddleOCR performs text detection, angle classification, and
   recognition in one call.

5. **Document classification**
   Lightweight keyword scoring to identify receipt vs invoice vs other.

6. **Field extraction**
   Regex patterns plus spatial reasoning extract merchant, date, items,
   subtotal, tax, total, currency, and payment method.

7. **Field validation**
   Cross-checks like items sum vs total, subtotal plus tax vs total,
   and date sanity.

8. **Categorization**
   Keyword lookup against merchant name and item names to assign one
   of seven categories.

## Module boundaries

| Module | Depends on | Should not import from |
|--------|-----------|------------------------|
| `src/api` | `services`, `models`, `core`, `utils` | `workers` |
| `src/services` | `core`, `utils`, `models` | `api`, `workers` |
| `src/models` | nothing | anything else in `src` |
| `src/core` | nothing | anything else in `src` |
| `src/utils` | `core` | `services`, `api`, `workers` |
| `src/workers` | `services`, `core`, `utils` | `api` |

Tests can import from anywhere.

## Why these choices

### PaddleOCR over EasyOCR or Tesseract

PaddleOCR has the best accuracy on receipt-style layouts, especially
for Asian languages like Indonesian. The bundled angle classifier
handles rotated documents without extra preprocessing. Trade-off is a
slightly larger install footprint.

### Rule-based field extraction

A fine-tuned LayoutLM or Donut model would extract fields more
robustly, but those models are 400 MB to 1 GB and require GPU for
reasonable latency. For the target deployment (8 GB RAM, CPU only),
regex patterns plus spatial layout heuristics give acceptable accuracy
on common receipt formats with no additional inference cost.

### Lazy OCR initialization

PaddleOCR initialization takes 5-15 seconds and loads around 500 MB
into memory. The OCR engine is loaded on the first request rather
than at startup, so health checks and metric scraping work even
before the model is ready.

### Separate validation step

Validation is split into image-level (before OCR) and field-level
(after extraction) to fail fast on bad inputs and to provide
actionable feedback to the user about what went wrong.

## Performance characteristics

Measured on a laptop with 8 GB RAM, no GPU, Intel i5 CPU:

| Stage | Cold (first request) | Warm |
|-------|---------------------|------|
| Image decode + validation | 50 ms | 50 ms |
| Deskew | 100 ms | 80 ms |
| PaddleOCR | 8 to 15 s | 1.5 to 3 s |
| Classification + extraction | 30 ms | 20 ms |
| Validation + categorization | 10 ms | 10 ms |
| **Total** | 8 to 16 s | 1.7 to 3.2 s |

Cold start dominates. Production deployments should keep workers warm
or use the lifespan handler to pre-load models.
