"""
AI Provider Router
Dynamic, cost-optimized routing across multiple AI providers
Use-case routing, fallback, and basic health-aware selection.

Environment-driven configuration so you can rotate providers at deploy time.

ENV EXAMPLES (Railway):
  AI_CHAT_FAST="groq:llama-3.1-70b-versatile, openai:gpt-4o-mini, anthropic:claude-3-haiku-20240307"
  AI_CHAT_QUALITY="openai:gpt-4.1, anthropic:claude-3.5-sonnet-20241022"
  AI_EMBEDDINGS="cohere:embed-english-v3.0, openai:text-embedding-3-small"
  AI_VISION="openai:gpt-4o, groq:llama-3.2-vision"
  AI_IMAGE_GEN="fal:sdxl-turbo, replicate:flux"

Flags in settings.py:
  AI_COST_OPTIMIZATION: bool
  AI_FALLBACK_ENABLED: bool
  AI_CACHE_TTL_SECONDS: int
"""

from __future__ import annotations

import os
import time
import logging
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config.settings import settings

logger = logging.getLogger(__name__)


# ------------------------------
# Data structures
# ------------------------------

@dataclass
class ProviderSpec:
    name: str          # "openai", "anthropic", "cohere", "groq", "fal", "replicate", etc.
    model: str         # e.g., "gpt-4o-mini"
    cost_in: float     # $ per 1K input tokens (approx)
    cost_out: float    # $ per 1K output tokens (approx)
    ctx: int           # context limit
    tags: List[str]    # ["fast", "quality", "vision", "embeddings"]
    weight: int = 1    # priority weight


# Minimal built-in cost/context defaults (extend as needed).
# These are approximate and should be updated as providers change pricing.
_DEFAULTS: Dict[tuple[str, str], Dict[str, Any]] = {
    ("openai", "gpt-4o-mini"): {"in": 0.15, "out": 0.60, "ctx": 128_000, "tags": ["fast", "vision"]},
    ("openai", "gpt-4.1"): {"in": 5.00, "out": 15.00, "ctx": 128_000, "tags": ["quality"]},
    ("openai", "text-embedding-3-small"): {"in": 0.02, "out": 0.00, "ctx": 8_192, "tags": ["embeddings"]},

    ("anthropic", "claude-3-haiku-20240307"): {"in": 0.25, "out": 1.25, "ctx": 200_000, "tags": ["fast"]},
    ("anthropic", "claude-3.5-sonnet-20241022"): {"in": 3.00, "out": 15.00, "ctx": 200_000, "tags": ["quality"]},

    ("groq", "llama-3.1-70b-versatile"): {"in": 0.00, "out": 0.00, "ctx": 128_000, "tags": ["fast"]},
    ("groq", "llama-3.2-vision"): {"in": 0.00, "out": 0.00, "ctx": 128_000, "tags": ["vision"]},

    ("cohere", "embed-english-v3.0"): {"in": 0.10, "out": 0.00, "ctx": 8_192, "tags": ["embeddings"]},

    ("fal", "sdxl-turbo"): {"in": 0.00, "out": 0.00, "ctx": 0, "tags": ["image_gen"]},
    ("replicate", "flux"): {"in": 0.00, "out": 0.00, "ctx": 0, "tags": ["image_gen"]},
}


# Map use cases to ENV variable names
_USECASE_ENV_MAP: Dict[str, str] = {
    "chat_fast": "AI_CHAT_FAST",
    "chat_quality": "AI_CHAT_QUALITY",
    "embeddings": "AI_EMBEDDINGS",
    "vision": "AI_VISION",
    "image_gen": "AI_IMAGE_GEN",
}


class AIRouter:
    """
    Environment-driven AI router:
      - Choose provider list by use case via env vars.
      - Sort by health and cost.
      - Fallback to next provider on error.
      - Budget-aware if AI_COST_OPTIMIZATION is enabled.
    """

    def __init__(self, health_cache_ttl: Optional[int] = None):
        self.health_cache_ttl = health_cache_ttl or int(getattr(settings, "AI_CACHE_TTL_SECONDS", 300))
        self.fallback_enabled = bool(getattr(settings, "AI_FALLBACK_ENABLED", True))
        self.cost_optimization = bool(getattr(settings, "AI_COST_OPTIMIZATION", True))
        self.health: Dict[tuple[str, str], tuple[bool, float]] = {}  # (name, model) -> (ok, ts)

    # ------------- parsing and specs -------------

    def _parse_env_list(self, key: str) -> List[tuple[str, str]]:
        """
        Parse env var like "openai:gpt-4o-mini, anthropic:claude-3-haiku-20240307"
        into [("openai","gpt-4o-mini"), ("anthropic","claude-3-haiku-20240307")]
        """
        raw = os.getenv(key, "")
        items: List[tuple[str, str]] = []
        for part in [p.strip() for p in raw.split(",") if p.strip()]:
            if ":" not in part:
                continue
            prov, model = part.split(":", 1)
            items.append((prov.strip(), model.strip()))
        return items

    def _make_specs(self, pairs: List[tuple[str, str]], use_case: str) -> List[ProviderSpec]:
        specs: List[ProviderSpec] = []
        for prov, model in pairs:
            meta = _DEFAULTS.get((prov, model), {"in": 0.0, "out": 0.0, "ctx": 128_000, "tags": [use_case]})
            specs.append(ProviderSpec(
                name=prov,
                model=model,
                cost_in=meta["in"],
                cost_out=meta["out"],
                ctx=meta["ctx"],
                tags=meta["tags"],
                weight=1,
            ))
        return specs

    # ------------- selection helpers -------------

    def _within_budget(self, spec: ProviderSpec, prompt_tokens: int, gen_tokens: int, budget_usd: Optional[float]) -> bool:
        if budget_usd is None or not self.cost_optimization:
            return True
        est = (spec.cost_in * (prompt_tokens / 1000.0)) + (spec.cost_out * (gen_tokens / 1000.0))
        return est <= budget_usd

    def _healthy(self, spec: ProviderSpec) -> bool:
        key = (spec.name, spec.model)
        ok, ts = self.health.get(key, (True, 0.0))
        if not ok and (time.time() - ts) > self.health_cache_ttl:
            return True
        return ok

    def report_failure(self, spec: ProviderSpec):
        self.health[(spec.name, spec.model)] = (False, time.time())

    def report_success(self, spec: ProviderSpec):
        self.health[(spec.name, spec.model)] = (True, time.time())

    # ------------- public API -------------

    def pick(
        self,
        use_case: str,
        prompt_tokens: int = 1000,
        gen_tokens: int = 500,
        budget_usd: Optional[float] = None,
    ) -> ProviderSpec:
        """
        Pick the best provider for the given use case.
        """
        env_key = _USECASE_ENV_MAP.get(use_case)
        if not env_key:
            raise ValueError(f"Unknown use case: {use_case}")

        pairs = self._parse_env_list(env_key)
        if not pairs:
            raise RuntimeError(
                f"No providers configured in env for use case '{use_case}'. "
                f"Set {env_key} on Railway."
            )

        specs = self._make_specs(pairs, use_case)
        # Filter unhealthy
        specs = [s for s in specs if self._healthy(s)]
        if not specs:
            # If all unhealthy, ignore health filter once
            specs = self._make_specs(pairs, use_case)

        # Sort by total cost (in + out), then weight (desc)
        specs.sort(key=lambda s: (s.cost_in + s.cost_out, -s.weight))

        # Respect budget if provided
        for s in specs:
            if self._within_budget(s, prompt_tokens, gen_tokens, budget_usd):
                logger.info(f"[AIRouter] Picked provider {s.name}:{s.model} for {use_case}")
                return s

        # If budget excludes all, pick the cheapest anyway
        chosen = specs[0]
        logger.info(f"[AIRouter] Budget excluded all; picking cheapest {chosen.name}:{chosen.model} for {use_case}")
        return chosen

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def call_with_fallback(
        self,
        use_case: str,
        call_func,
        prompt_tokens: int = 1000,
        gen_tokens: int = 500,
        budget_usd: Optional[float] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Call a provider for a use case with automatic fallback.

        call_func signature:
          await call_func(spec: ProviderSpec, **kwargs) -> Dict|Any
        """
        last_error: Optional[Exception] = None

        pairs = self._parse_env_list(_USECASE_ENV_MAP.get(use_case, ""))
        if not pairs:
            raise RuntimeError(f"No providers configured for use case '{use_case}'")

        # Build ordered list once to keep stable fallback order
        ordered_specs = self._make_specs(pairs, use_case)
        # Prefer healthy first
        ordered_specs = sorted(
            ordered_specs,
            key=lambda s: (0 if self._healthy(s) else 1, s.cost_in + s.cost_out)
        )

        for spec in ordered_specs:
            # Skip if over budget (optional)
            if not self._within_budget(spec, prompt_tokens, gen_tokens, budget_usd):
                continue

            try:
                logger.info(f"[AIRouter] Attempt {spec.name}:{spec.model} for {use_case}")
                result = await call_func(spec=spec, **kwargs)
                self.report_success(spec)
                return {
                    "success": True,
                    "result": result,
                    "provider": spec.name,
                    "model": spec.model,
                    "use_case": use_case,
                    "estimated_cost_usd": (spec.cost_in * (prompt_tokens / 1000.0)) + (spec.cost_out * (gen_tokens / 1000.0)),
                }
            except Exception as e:
                last_error = e
                self.report_failure(spec)
                logger.warning(f"[AIRouter] Provider {spec.name}:{spec.model} failed: {e}")
                if not self.fallback_enabled:
                    break
                continue

        logger.error(f"[AIRouter] All providers failed for {use_case}: {last_error}")
        raise Exception(f"All AI providers failed for {use_case}: {last_error}")

    # Backwards-compatible helper
    def estimate_cost(
        self,
        tokens_in: int,
        tokens_out: int,
        provider_name: str,
        model: Optional[str] = None,
    ) -> float:
        """
        Estimate cost; if model provided and known, use its split rates.
        """
        if model:
            meta = _DEFAULTS.get((provider_name, model))
            if meta:
                return (meta["in"] * (tokens_in / 1000.0)) + (meta["out"] * (tokens_out / 1000.0))
        # Fallback average
        blended = 0.001
        total_tokens = tokens_in + tokens_out
        return (total_tokens / 1000.0) * blended


# Global router instance
ai_router = AIRouter()