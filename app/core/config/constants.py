# app/core/config/constants.py

AI_PROVIDERS = {
    "ultra_cheap": [
        {"name": "deepseek", "key_env": "DEEPSEEK_API_KEY", "cost_per_1k": 0.0001},
        {"name": "groq", "key_env": "GROQ_API_KEY", "cost_per_1k": 0.0001},
    ],
    "budget": [
        {"name": "together", "key_env": "TOGETHER_API_KEY", "cost_per_1k": 0.0008},
        {"name": "aimlapi", "key_env": "AIMLAPI_API_KEY", "cost_per_1k": 0.0008},
    ],
    "standard": [
        {"name": "cohere", "key_env": "COHERE_API_KEY", "cost_per_1k": 0.002},
        {"name": "minimax", "key_env": "MINIMAX_API_KEY", "cost_per_1k": 0.002},
    ],
    "premium": [
        {"name": "openai", "key_env": "OPENAI_API_KEY", "cost_per_1k": 0.01},
        {"name": "anthropic", "key_env": "ANTHROPIC_API_KEY", "cost_per_1k": 0.015},
    ],
}

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

EMBEDDING_CONFIG = {
    "provider": "ai_router",  # Uses AI Router for automatic failover
    "primary_provider": "openai",
    "primary_model": "text-embedding-3-large",
    "fallback_provider": "cohere",
    "fallback_model": "embed-english-v3.0",
    "dimensions": 1536,  # Fixed dimension for all providers
    "similarity_threshold": 0.7,
}