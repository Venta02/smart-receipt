"""Health endpoint."""

from fastapi import APIRouter, Depends

from src.api.dependencies import get_ocr_engine, get_orchestrator
from src.core.logging import get_logger
from src.models import HealthResponse
from src.services.extraction.orchestrator import ExtractionOrchestrator
from src.services.ocr import OCREngine

logger = get_logger(__name__)

router = APIRouter(tags=["health"])

VERSION = "1.0.0"


@router.get("/health", response_model=HealthResponse)
async def health_check(
    ocr: OCREngine = Depends(get_ocr_engine),
    orchestrator: ExtractionOrchestrator = Depends(get_orchestrator),
) -> HealthResponse:
    ocr_ready = ocr.is_ready()

    redis_reachable = True
    try:
        import redis
        from src.core.config import settings
        client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            socket_connect_timeout=2,
        )
        client.ping()
    except Exception as e:
        logger.warning("Redis unreachable", error=str(e))
        redis_reachable = False

    llm_available = orchestrator.llm.is_available

    if ocr_ready and redis_reachable:
        status = "ok"
    elif ocr_ready:
        status = "degraded"
    else:
        status = "unhealthy"

    return HealthResponse(
        status=status,
        version=VERSION,
        ocr_ready=ocr_ready,
        redis_reachable=redis_reachable,
        llm_available=llm_available,
    )