"""PaddleOCR wrapper for receipt text detection and recognition."""

import time

import numpy as np

from src.core.config import settings
from src.core.logging import get_logger
from src.core.metrics import ocr_latency_seconds, ocr_text_blocks_total
from src.models import TextBlock

logger = get_logger(__name__)


class OCREngine:
    """Wraps PaddleOCR with sane defaults for receipts."""

    def __init__(self, lang: str | None = None, use_gpu: bool | None = None):
        self.lang = lang or settings.ocr_lang
        self.use_gpu = use_gpu if use_gpu is not None else settings.ocr_use_gpu
        self._ocr = None
        logger.info("OCR engine configured", lang=self.lang, use_gpu=self.use_gpu)

    def _lazy_init(self) -> None:
        """Defer heavy import until first use to keep startup fast."""
        if self._ocr is not None:
            return

        from paddleocr import PaddleOCR

        kwargs = {
            "use_angle_cls": True,
            "lang": self.lang,
            "use_gpu": self.use_gpu,
            "show_log": False,
        }
        if settings.ocr_det_model_dir:
            kwargs["det_model_dir"] = settings.ocr_det_model_dir
        if settings.ocr_rec_model_dir:
            kwargs["rec_model_dir"] = settings.ocr_rec_model_dir
        if settings.ocr_cls_model_dir:
            kwargs["cls_model_dir"] = settings.ocr_cls_model_dir

        logger.info("Loading PaddleOCR model", **kwargs)
        self._ocr = PaddleOCR(**kwargs)
        logger.info("PaddleOCR ready")

    def extract(self, image: np.ndarray) -> list[TextBlock]:
        """Run OCR on a BGR image and return list of TextBlock."""
        self._lazy_init()

        start = time.perf_counter()
        try:
            result = self._ocr.ocr(image, cls=True)
        except Exception as e:
            logger.error("OCR call failed", error=str(e))
            return []

        elapsed = time.perf_counter() - start
        ocr_latency_seconds.observe(elapsed)

        blocks = self._parse_result(result)
        ocr_text_blocks_total.inc(len(blocks))

        logger.debug(
            "OCR completed",
            block_count=len(blocks),
            latency_ms=round(elapsed * 1000, 2),
        )
        return blocks

    @staticmethod
    def _parse_result(result: list) -> list[TextBlock]:
        """PaddleOCR returns nested lists, normalize to TextBlock."""
        if not result or not result[0]:
            return []

        blocks: list[TextBlock] = []
        for line in result[0]:
            if not line or len(line) < 2:
                continue
            bbox = line[0]
            text_info = line[1]
            if not text_info or len(text_info) < 2:
                continue

            text = text_info[0]
            confidence = float(text_info[1])

            if not text or not text.strip():
                continue

            blocks.append(TextBlock(
                text=text.strip(),
                confidence=confidence,
                bbox=[[float(p[0]), float(p[1])] for p in bbox],
            ))

        return blocks

    def is_ready(self) -> bool:
        return self._ocr is not None

    def warm_up(self) -> None:
        """Force model load. Call from lifespan handler if you want."""
        self._lazy_init()
