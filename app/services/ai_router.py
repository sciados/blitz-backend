"""
AI Provider Router
Dynamic, cost-optimized routing across multiple AI providers
Use-case routing, fallback, and basic health-aware selection.

Environment-driven configuration so you can rotate providers at deploy time.

ENV EXAMPLES (Railway):
  AI_CHAT_FAST="groq:llama-3.3-70b-versatile,xai:grok-beta,together:llama-3.2-3b-instruct-turbo,openai:gpt-4o-mini"
  AI_CHAT_QUALITY="anthropic:claude-3.5-sonnet-20241022,openai:gpt-4.1,deepseek:deepseek-reasoner"
  AI_EMBEDDINGS="openai:text-embedding-3-small,cohere:embed-english-v3.0"
  AI_VISION="groq:llama-3.2-vision,openai:gpt-4o"
  AI_IMAGE_GEN="fal:sdxl-turbo,replicate:flux"

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
    # FREE Providers (Your API keys available)
    ("groq", "llama-3.3-70b-versatile"): {"in": 0.00, "out": 0.00, "ctx": 128_000, "tags": ["fast"]},
    ("xai", "grok-beta"): {"in": 0.00, "out": 0.00, "ctx": 128_000, "tags": ["fast"]},

    # CHEAPEST Paid Providers (Your API keys available)
    ("together", "llama-3.2-3b-instruct-turbo"): {"in": 0.10, "out": 0.10, "ctx": 128_000, "tags": ["fast"]},
    ("minimax", "abab6.5s-chat"): {"in": 0.12, "out": 0.12, "ctx": 245_760, "tags": ["fast"]},
    ("deepseek", "deepseek-reasoner"): {"in": 0.14, "out": 0.28, "ctx": 200_000, "tags": ["fast", "reasoning"]},

    # Popular Providers (Your API keys available)
    ("openai", "gpt-4o-mini"): {"in": 0.15, "out": 0.60, "ctx": 128_000, "tags": ["fast", "vision"]},
    ("anthropic", "claude-3-haiku-20240307"): {"in": 0.25, "out": 1.25, "ctx": 200_000, "tags": ["fast"]},

    # Quality Models
    ("openai", "gpt-4.1"): {"in": 5.00, "out": 15.00, "ctx": 128_000, "tags": ["quality"]},
    ("anthropic", "claude-3.5-sonnet-20241022"): {"in": 3.00, "out": 15.00, "ctx": 200_000, "tags": ["quality"]},

    # Embeddings
    ("openai", "text-embedding-3-small"): {"in": 0.02, "out": 0.00, "ctx": 8_192, "tags": ["embeddings"]},
    ("cohere", "embed-english-v3.0"): {"in": 0.10, "out": 0.00, "ctx": 8_192, "tags": ["embeddings"]},

    # Vision
    ("groq", "llama-3.2-vision"): {"in": 0.00, "out": 0.00, "ctx": 128_000, "tags": ["vision"]},
    ("openai", "gpt-4o"): {"in": 2.50, "out": 10.00, "ctx": 128_000, "tags": ["vision", "quality"]},

    # Image Generation
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
        self.last_used_model: Optional[str] = None  # Track last successful model

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

    async def generate_text(
        self,
        prompt: Dict[str, str] | str,
        max_tokens: int | str = 1000,
        temperature: float = 0.7,
        use_quality: bool = False,
    ) -> str:
        """
        Generate text using AI providers with automatic fallback.

        Args:
            prompt: Either a string prompt or a dict with 'system' and 'user' keys
            max_tokens: Maximum tokens to generate (or "short"/"medium"/"long")
            temperature: Generation temperature
            use_quality: Use quality providers instead of fast providers

        Returns:
            Generated text string
        """
        # Convert length strings to token counts
        length_map = {
            "short": 500,
            "medium": 1000,
            "long": 2000,
        }
        if isinstance(max_tokens, str):
            max_tokens = length_map.get(max_tokens, 1000)

        # Determine use case
        use_case = "chat_quality" if use_quality else "chat_fast"

        # Extract system and user prompts
        if isinstance(prompt, dict):
            system_prompt = prompt.get("system", "")
            user_prompt = prompt.get("user", "")
        else:
            system_prompt = ""
            user_prompt = prompt

        # Define provider-specific call function
        async def call_provider(spec: ProviderSpec, **kwargs):
            """Call specific AI provider"""
            if spec.name == "openai":
                import openai
                client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": user_prompt})

                response = await client.chat.completions.create(
                    model=spec.model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                self.last_used_model = spec.model
                return response.choices[0].message.content

            elif spec.name == "anthropic":
                import anthropic
                client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

                response = await client.messages.create(
                    model=spec.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system_prompt if system_prompt else None,
                    messages=[{"role": "user", "content": user_prompt}]
                )
                self.last_used_model = spec.model
                return response.content[0].text

            elif spec.name == "groq":
                import groq
                client = groq.AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": user_prompt})

                response = await client.chat.completions.create(
                    model=spec.model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                self.last_used_model = spec.model
                return response.choices[0].message.content

            elif spec.name == "xai":
                import openai
                client = openai.AsyncOpenAI(
                    api_key=os.getenv("XAI_API_KEY"),
                    base_url="https://api.x.ai/v1",
                )
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": user_prompt})

                response = await client.chat.completions.create(
                    model=spec.model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                self.last_used_model = spec.model
                return response.choices[0].message.content

            elif spec.name == "together":
                import openai
                client = openai.AsyncOpenAI(
                    api_key=os.getenv("TOGETHER_API_KEY"),
                    base_url="https://api.together.xyz/v1",
                )
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": user_prompt})

                response = await client.chat.completions.create(
                    model=spec.model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                self.last_used_model = spec.model
                return response.choices[0].message.content

            elif spec.name == "minimax":
                import openai
                client = openai.AsyncOpenAI(
                    api_key=os.getenv("MINIMAX_API_KEY"),
                    base_url="https://api.minimax.chat/v1",
                )
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": user_prompt})

                response = await client.chat.completions.create(
                    model=spec.model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                self.last_used_model = spec.model
                return response.choices[0].message.content

            elif spec.name == "deepseek":
                import openai
                client = openai.AsyncOpenAI(
                    api_key=os.getenv("DEEPSEEK_API_KEY"),
                    base_url="https://api.deepseek.com/v1",
                )
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": user_prompt})

                response = await client.chat.completions.create(
                    model=spec.model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                self.last_used_model = spec.model
                return response.choices[0].message.content

            else:
                raise NotImplementedError(f"Provider {spec.name} not yet implemented for text generation")

        # Call with fallback
        result = await self.call_with_fallback(
            use_case=use_case,
            call_func=call_provider,
            prompt_tokens=len(system_prompt + user_prompt) // 4,  # Rough estimate
            gen_tokens=max_tokens,
        )

        return result["result"]


# Global router instance
ai_router = AIRouter()