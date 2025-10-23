# app/core/config/settings.py
"""
Main application settings for Blitz Railway deployment.

Manages all environment variables with proper typing, validation,
and Railway-specific configurations.
"""

from functools import lru_cache
from typing import Optional, List, Dict

import os
from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings with comprehensive environment variable management.
    Configured for Railway deployment with all AI providers and services.
    """

    # ==== APPLICATION ====
    APP_NAME: str = "Blitz"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    API_BASE_URL: str

    # ==== DATABASE ====
    DATABASE_URL: str
    DATABASE_URL_ASYNC: str
    REDIS_URL: Optional[str] = None

    # ==== AUTHENTICATION ====
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_ACCESS_KEY: str

    # ==== AI PROVIDERS ====
    OPENAI_API_KEY: str
    ANTHROPIC_API_KEY: str
    COHERE_API_KEY: str

    GROQ_API_KEY: str
    DEEPSEEK_API_KEY: str
    TOGETHER_API_KEY: str
    MINIMAX_API_KEY: str
    AIMLAPI_API_KEY: str
    XAI_API_KEY: str  # xAI Grok

    # ==== MEDIA GENERATION ====
    STABILITY_API_KEY: str
    REPLICATE_API_TOKEN: str
    FAL_API_KEY: str

    # ==== STORAGE ====
    CLOUDFLARE_ACCOUNT_ID: str
    CLOUDFLARE_R2_ACCESS_KEY_ID: str
    CLOUDFLARE_R2_SECRET_ACCESS_KEY: str
    CLOUDFLARE_R2_BUCKET_NAME: str
    CLOUDFLARE_R2_PUBLIC_URL: str = "https://pub-c0ddba9f039845bda33be436955187cb.r2.dev"

    # ==== CORS ====
    # Accept comma-separated string or list; we normalize to a list via validator.
    ALLOWED_ORIGINS: str | List[str] = ""

    # ==== AI SYSTEM CONFIGURATION ====
    AI_CACHE_TTL_SECONDS: int = 300
    AI_COST_OPTIMIZATION: bool = True
    AI_FALLBACK_ENABLED: bool = True
    AI_MONITORING_ENABLED: bool = True
    AI_MONITORING_INTERVAL_MINUTES: int = 60
    INTELLIGENCE_ANALYSIS_ENABLED: bool = True

    # ==== CREDITS & LIMITS ====
    CREDIT_ENFORCEMENT_ENABLED: bool = True
    MAX_FILE_SIZE_MB: int = 50

    # ==== EXTERNAL SERVICES ====
    AI_DISCOVERY_DATABASE_URL: str
    AI_DISCOVERY_SERVICE_URL: str

    # ==== OPTIONAL/PLATFORMS ====
    # CLICKBANK_DEV_KEY: Optional[str] = None
    # JVZOO_API_KEY: Optional[str] = None

    # ===== Validators =====

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v) -> List[str]:
        """
        Parse CORS origins from comma-separated string or pass through list.
        """
        if v is None:
            return []
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return []

    @field_validator("DATABASE_URL_ASYNC", mode="before")
    @classmethod
    def validate_async_db_url(cls, v: str) -> str:
        """
        Ensure async database URL uses asyncpg driver.
        Converts postgresql:// to postgresql+asyncpg:// if needed.
        """
        if not v:
            raise ValueError("DATABASE_URL_ASYNC must be set")
        if v.startswith("postgresql+asyncpg://"):
            return v
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        raise ValueError("DATABASE_URL_ASYNC must be a PostgreSQL URL")

    @field_validator("DEBUG", mode="before")
    @classmethod
    def set_debug_mode(cls, v) -> bool:
        """
        Enable DEBUG automatically in development-like environments.
        """
        env = os.getenv("ENVIRONMENT", "production").lower()
        return bool(v) or env in ["development", "dev", "local"]

    # ===== Convenience Properties =====

    @property
    def cors_origins(self) -> List[str]:
        """
        Get parsed CORS origins as list.
        """
        # At this point ALLOWED_ORIGINS has already been normalized to a list.
        if isinstance(self.ALLOWED_ORIGINS, list):
            return self.ALLOWED_ORIGINS
        if isinstance(self.ALLOWED_ORIGINS, str):
            return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]
        return []

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() in ["production", "prod"]

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT.lower() in ["development", "dev", "local"]

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.
    """
    return Settings()


# Global settings instance
settings = get_settings()

# ==== Utility helpers below (optional, but convenient for services) ====

def get_database_url(async_mode: bool = False) -> str:
    """
    Return proper DB URL depending on async_mode.
    """
    if async_mode:
        if settings.DATABASE_URL_ASYNC:
            return settings.DATABASE_URL_ASYNC
        if settings.DATABASE_URL:
            url = settings.DATABASE_URL
            if url.startswith("postgresql://"):
                return url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return url
        raise ValueError("No database URL configured")
    else:
        if settings.DATABASE_URL:
            url = settings.DATABASE_URL
            if "+asyncpg" in url:
                return url.replace("+asyncpg", "")
            return url
        raise ValueError("No database URL configured")


def get_redis_url() -> str:
    """Get Redis URL for caching"""
    return settings.REDIS_URL or "redis://localhost:6379"


def get_ai_provider_config() -> Dict[str, str]:
    """Get all AI provider API keys"""
    return {
        "openai": settings.OPENAI_API_KEY,
        "anthropic": settings.ANTHROPIC_API_KEY,
        "groq": settings.GROQ_API_KEY,
        "cohere": settings.COHERE_API_KEY,
        "deepseek": settings.DEEPSEEK_API_KEY,
        "together": settings.TOGETHER_API_KEY,
        "minimax": settings.MINIMAX_API_KEY,
        "aimlapi": settings.AIMLAPI_API_KEY,
    }


def get_storage_config() -> Dict[str, str]:
    """Get Cloudflare R2 storage configuration"""
    return {
        "access_key_id": settings.CLOUDFLARE_R2_ACCESS_KEY_ID,
        "secret_access_key": settings.CLOUDFLARE_R2_SECRET_ACCESS_KEY,
        "bucket_name": settings.CLOUDFLARE_R2_BUCKET_NAME,
        "account_id": settings.CLOUDFLARE_ACCOUNT_ID,
    }


def get_platform_config() -> Dict[str, bool]:
    """Get platform configuration (ClickBank placeholder)"""
    return {
        "clickbank_enabled": True,  # users provide their own API keys
    }


def get_cors_origins() -> List[str]:
    """Get CORS allowed origins as a list"""
    return settings.cors_origins