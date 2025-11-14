"""
Admin API Keys Management
Manage third-party API keys and integrations
"""

from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import os

from app.models.user import User
from app.db.session import get_db
from app.core.auth import get_current_user

router = APIRouter(prefix="/api/admin/api-keys", tags=["admin-api-keys"])

# ============================================================================
# SCHEMAS
# ============================================================================

class APIKeyInfo(BaseModel):
    provider: str
    env_var: str
    is_configured: bool
    key_preview: Optional[str] = None
    description: str

class APIKeyUpdateRequest(BaseModel):
    provider: str
    api_key: str

# ============================================================================
# ENDPOINTS
# ============================================================================

# List of supported API providers
SUPPORTED_PROVIDERS = [
    {
        "provider": "OpenAI",
        "env_var": "OPENAI_API_KEY",
        "description": "GPT-4, GPT-4o, GPT-4o-mini models"
    },
    {
        "provider": "Anthropic",
        "env_var": "ANTHROPIC_API_KEY",
        "description": "Claude 3.5 Sonnet, Claude 3 Haiku models"
    },
    {
        "provider": "Groq",
        "env_var": "GROQ_API_KEY",
        "description": "LLaMA 3.3 70B, Mixtral 8x7B - Ultra-fast inference"
    },
    {
        "provider": "DeepSeek",
        "env_var": "DEEPSEEK_API_KEY",
        "description": "DeepSeek Reasoner - Advanced reasoning model"
    },
    {
        "provider": "Together AI",
        "env_var": "TOGETHER_API_KEY",
        "description": "LLaMA, Qwen, and other open models"
    },
    {
        "provider": "MiniMax",
        "env_var": "MINIMAX_API_KEY",
        "description": "MiniMax ABAB models - Long context support"
    },
    {
        "provider": "XAI",
        "env_var": "XAI_API_KEY",
        "description": "Grok models from xAI"
    },
    {
        "provider": "AI/ML API",
        "env_var": "AIMLAPI_API_KEY",
        "description": "Access to multiple models via single API"
    },
    {
        "provider": "Replicate",
        "env_var": "REPLICATE_API_TOKEN",
        "description": "LLaMA 2, Mistral, and image generation models"
    },
    {
        "provider": "FAL AI",
        "env_var": "FAL_KEY",
        "description": "Falcon and LLaMA models"
    },
    {
        "provider": "OpenRouter",
        "env_var": "OPENROUTER_API_KEY",
        "description": "Access 100+ models via unified API"
    },
    {
        "provider": "Fireworks AI",
        "env_var": "FIREWORKS_API_KEY",
        "description": "Fast inference for open models"
    },
    {
        "provider": "Cohere",
        "env_var": "COHERE_API_KEY",
        "description": "Command R+ models optimized for RAG"
    },
    {
        "provider": "Perplexity",
        "env_var": "PERPLEXITY_API_KEY",
        "description": "Models with web search integration"
    },
    {
        "provider": "Stability AI",
        "env_var": "STABILITY_API_KEY",
        "description": "Stable Diffusion for image generation"
    },
    {
        "provider": "Cloudflare R2",
        "env_var": "CLOUDFLARE_R2_ACCESS_KEY_ID",
        "description": "Object storage for media files"
    }
]

@router.get("", response_model=List[APIKeyInfo])
async def list_api_keys(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all API key configurations"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    api_keys = []
    for provider_info in SUPPORTED_PROVIDERS:
        env_value = os.getenv(provider_info["env_var"])
        is_configured = bool(env_value)

        # Show first 8 and last 4 characters as preview
        key_preview = None
        if is_configured and env_value:
            if len(env_value) > 12:
                key_preview = f"{env_value[:8]}...{env_value[-4:]}"
            else:
                key_preview = "***" + env_value[-4:] if len(env_value) >= 4 else "***"

        api_keys.append(APIKeyInfo(
            provider=provider_info["provider"],
            env_var=provider_info["env_var"],
            is_configured=is_configured,
            key_preview=key_preview,
            description=provider_info["description"]
        ))

    return api_keys

@router.post("/test/{provider}")
async def test_api_key(
    provider: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Test an API key by making a simple request"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Find the provider
    provider_info = next((p for p in SUPPORTED_PROVIDERS if p["provider"] == provider), None)
    if not provider_info:
        raise HTTPException(status_code=404, detail="Provider not found")

    env_value = os.getenv(provider_info["env_var"])
    if not env_value:
        raise HTTPException(status_code=400, detail="API key not configured")

    # For now, just check if the key exists
    # In production, you would make actual API calls to test the key
    return {
        "provider": provider,
        "status": "configured",
        "message": f"API key for {provider} is configured (actual testing not implemented yet)"
    }

@router.get("/usage-stats")
async def get_api_usage_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get API usage statistics (placeholder for future implementation)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Placeholder - in production, you would track actual API usage
    return {
        "total_requests_today": 0,
        "total_cost_today": 0.00,
        "by_provider": []
    }
