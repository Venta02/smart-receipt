"""Application configuration loaded from environment."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "smart-receipt"
    app_env: Literal["development", "staging", "production"] = "development"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # OCR
    ocr_lang: Literal["en", "id", "ch"] = "en"
    ocr_use_gpu: bool = False
    ocr_det_model_dir: str = ""
    ocr_rec_model_dir: str = ""
    ocr_cls_model_dir: str = ""

    # Image
    max_image_size_mb: int = Field(default=10, ge=1, le=50)
    min_image_width: int = 400
    min_image_height: int = 400
    blur_threshold: float = 100.0

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    cache_ttl_seconds: int = 3600

    # Rate limiting
    rate_limit_per_minute: int = 60

    # Monitoring
    enable_metrics: bool = True

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # LLM Fallback (Gemini)
    gemini_api_key: str = ""
    llm_fallback_enabled: bool = True
    llm_model: str = "gemini-2.0-flash-exp"
    # Trigger LLM fallback when rule-based confidence is below this OR
    # when critical fields (total, merchant) are missing.
    confidence_threshold: float = 0.7
    llm_timeout_seconds: int = 30

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def llm_available(self) -> bool:
        return bool(self.gemini_api_key) and self.llm_fallback_enabled


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()