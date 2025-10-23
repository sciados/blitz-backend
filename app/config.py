"""
CampaignForge Configuration
Loads all environment variables from Railway
"""
from wsgiref.validate import validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=True
    )

    # ========================================================================
    # GENERAL
    # ========================================================================
    API_BASE_URL: str
    FRONTEND_URL: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_SECRET_KEY: str
    JWT_ACCESS_KEY: str
    JWT_ALGORITHM: str = "HS256"
    MAX_FILE_SIZE_MB: int = 50

    # ========================================================================
    # DATABASE
    # ========================================================================
    DATABASE_URL: str
    DATABASE_URL_ASYNC: str

    # ========================================================================
    # REDIS
    # ========================================================================
    REDIS_URL: str | None = None

    CORS_ORIGINS: List[str] = ["https://web-production-0cbd.up.railway.app, http://localhost:3000"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    @validator("CORS_ORIGINS", pre=True)
    def split_cors(cls, v):
        if v is None or v == "":
            return []
        if isinstance(v, str):
            # support comma-separated hosts (can be http://localhost:3000,https://yourapp.com)
            return [s.strip() for s in v.split(",")]
        return v

    class Config:
        case_sensitive = True

    # settings = Settings()

    # ========================================================================
    # CLOUDFLARE R2
    # ========================================================================
    CLOUDFLARE_ACCOUNT_ID: str
    CLOUDFLARE_R2_BUCKET_NAME: str
    CLOUDFLARE_R2_ACCESS_KEY_ID: str
    CLOUDFLARE_R2_SECRET_ACCESS_KEY: str
    CLOUDFLARE_R2_PUBLIC_URL: str

    # ========================================================================
    # CORS
    # ========================================================================
    ALLOWED_ORIGINS: str

    @property
    def allowed_origins_list(self) -> List[str]:
        """Parse ALLOWED_ORIGINS into a list"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    # ========================================================================
    # EMAIL
    # ========================================================================
    FROM_EMAIL: str
    FROM_NAME: str
    RESEND_API_KEY: str

    # ========================================================================
    # AI PROVIDER KEYS
    # ========================================================================
    OPENAI_API_KEY: str
    ANTHROPIC_API_KEY: str
    COHERE_API_KEY: str
    DEEPSEEK_API_KEY: str
    GROQ_API_KEY: str
    TOGETHER_API_KEY: str
    AIMLAPI_API_KEY: str
    MINIMAX_API_KEY: str
    REPLICATE_API_TOKEN: str
    STABILITY_API_KEY: str
    XAI_API_KEY: str
    FAL_API_KEY: str
    GOOGLE_API_KEY: str

    # ========================================================================
    # AI MANAGEMENT FLAGS
    # ========================================================================
    AI_COST_OPTIMIZATION: bool = True
    AI_FALLBACK_ENABLED: bool = True
    AI_CACHE_TTL_SECONDS: int = 300
    AI_MONITORING_ENABLED: bool = True
    AI_MONITORING_INTERVAL_MINUTES: int = 60
    INTELLIGENCE_ANALYSIS_ENABLED: bool = True

    # ========================================================================
    # FEATURE TOGGLES
    # ========================================================================
    ENABLE_VIDEO_GENERATION: bool = True
    CREDIT_ENFORCEMENT_ENABLED: bool = True

    # ========================================================================
    # EXTERNAL INTEGRATIONS
    # ========================================================================
    CLICKBANK_DEV_KEY: str | None = None
    CLERK_API_KEY: str | None = None
    KIT_API_KEY: str | None = None
    DYNAMIC_MOCKUPS_API_KEY: str | None = None
    IMAGES_API_TOKEN: str | None = None

    # ========================================================================
    # AI DISCOVERY SERVICE
    # ========================================================================
    AI_DISCOVERY_DATABASE_URL: str | None = None
    AI_DISCOVERY_SERVICE_URL: str | None = None

    # ========================================================================
    # COMPUTED PROPERTIES
    # ========================================================================
    
    @property
    def r2_endpoint_url(self) -> str:
        """Construct R2 endpoint URL"""
        return f"https://{self.CLOUDFLARE_ACCOUNT_ID}.r2.cloudflarestorage.com"

    @property
    def max_file_size_bytes(self) -> int:
        """Convert MB to bytes"""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024


# Global settings instance
settings = Settings()


# ============================================================================
# AI PROVIDER CONFIGURATION
# ============================================================================

AI_PROVIDERS = {
    "ultra_cheap": [
        {"name": "deepseek", "key": settings.DEEPSEEK_API_KEY, "cost_per_1k": 0.0001},
        {"name": "groq", "key": settings.GROQ_API_KEY, "cost_per_1k": 0.0001},
    ],
    "budget": [
        {"name": "together", "key": settings.TOGETHER_API_KEY, "cost_per_1k": 0.0008},
        {"name": "aimlapi", "key": settings.AIMLAPI_API_KEY, "cost_per_1k": 0.0008},
    ],
    "standard": [
        {"name": "cohere", "key": settings.COHERE_API_KEY, "cost_per_1k": 0.002},
        {"name": "minimax", "key": settings.MINIMAX_API_KEY, "cost_per_1k": 0.002},
    ],
    "premium": [
        {"name": "openai", "key": settings.OPENAI_API_KEY, "cost_per_1k": 0.01},
        {"name": "anthropic", "key": settings.ANTHROPIC_API_KEY, "cost_per_1k": 0.015},
    ]
}


# ============================================================================
# TASK COST BUDGETS (USD)
# ============================================================================

TASK_BUDGETS = {
    "crawl_extraction": 0.005,
    "intelligence_compile": 0.02,
    "rag_build": 0.003,
    "text_generation_draft": 0.003,
    "text_generation_final": 0.008,
    "image_generation": 0.05,
    "video_generation": 0.20,
    "compliance_check": 0.002,
}


# ============================================================================
# EMBEDDING CONFIGURATION
# ============================================================================

EMBEDDING_CONFIG = {
    "provider": "cohere",
    "model": "embed-english-v3.0",
    "dimensions": 1536,
    "similarity_threshold": 0.7,
}