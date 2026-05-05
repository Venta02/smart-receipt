"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from src.api.dependencies import get_ocr_engine
from src.api.routes_health import router as health_router
from src.api.routes_receipts import router as receipts_router
from src.core.config import settings
from src.core.logging import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application starting", env=settings.app_env)
    # Pre-load OCR model so first request is fast.
    # Comment this out if you prefer faster startup over fast first request.
    try:
        ocr = get_ocr_engine()
        ocr.warm_up()
        logger.info("OCR warmed up")
    except Exception as e:
        logger.warning("OCR warm-up failed, will retry on first request", error=str(e))

    logger.info("Application ready")
    yield
    logger.info("Application shutting down")


app = FastAPI(
    title="smart-receipt",
    description="Production-grade receipt OCR and field extraction",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(receipts_router)


@app.get("/", tags=["root"])
async def root():
    return {
        "service": "smart-receipt",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/metrics", tags=["monitoring"])
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
