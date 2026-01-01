"""
Central AI Platform Manager
Provides unified platform rotation and fallback for all AI operations
"""

from __future__ import annotations

import os
import time
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta

from app.core.config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class PlatformHealth:
    """Track platform health metrics"""
    name: str
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    consecutive_failures: int = 0
    total_requests: int = 0
    total_failures: int = 0
    avg_response_time: float = 0.0
    is_healthy: bool = True


@dataclass
class PlatformSpec:
    """Platform specification with metadata"""
    name: str  # "stability", "replicate", "fal", "flux_pro", etc.
    model: str  # specific model name
    operation_types: List[str]  # ["image_editing", "image_generation"]
    priority: int = 0  # 0 = highest priority
    estimated_cost: float = 0.0  # cost per operation
    estimated_time: float = 0.0  # seconds per operation
    api_key_env: Optional[str] = None  # environment variable for API key


class AIPlatformManager:
    """
    Central manager for all AI platform rotation and fallback

    Usage:
        manager = AIPlatformManager()

        # Get best platform for image editing
        platform = await manager.get_platform("image_editing")
        result = await platform.call_function(...)

        # Report success/failure
        await manager.report_success(platform)
        await manager.report_failure(platform, error)
    """

    # Define platform priorities for each operation type
    PLATFORM_PRIORITIES = {
        "image_generation": [
            ("pollinations", "free"),
            ("huggingface", "free"),
            ("fal", "fal-3d"),
            ("flux_pro", "flux-schnell"),
            ("stability", "sd-3.5-large"),
            ("replicate", "flux"),
        ],
        "image_editing": [
            ("stability", "sd-3.5-large"),  # Primary - best quality
            ("replicate", "flux"),  # Fallback 1
            ("fal", "fal-3d"),  # Fallback 2
        ],
        "text_generation": [
            ("groq", "llama-3.3-70b-versatile"),  # Free, fast
            ("xai", "grok-beta"),  # Free, fast
            ("google", "gemini-2.5-flash-lite"),  # Cheap, good
            ("together", "llama-3.2-3b-instruct-turbo"),  # Cheap
            ("openai", "gpt-4o-mini"),  # Quality
            ("anthropic", "claude-3-haiku-20240307"),  # Quality
        ],
        "video_generation": [
            ("piapi", "hunyuan-fast"),  # Fast, affordable
            ("fal", "video-01"),  # Good quality
            ("replicate", "luma-dream-machine"),  # High quality
            ("aimlapi", "runway-gen3a-turbo"),  # Premium
        ]
    }

    def __init__(self):
        """Initialize platform manager"""
        self.health: Dict[str, PlatformHealth] = {}
        self.rotation_counters: Dict[str, int] = {}
        self.fallback_enabled = bool(getattr(settings, "AI_FALLBACK_ENABLED", True))
        self.cache_ttl = int(getattr(settings, "AI_CACHE_TTL_SECONDS", 300))

        # Initialize health tracking for all platforms
        self._init_platform_health()

    def _init_platform_health(self):
        """Initialize health tracking for all known platforms"""
        all_platforms = set()
        for operation_platforms in self.PLATFORM_PRIORITIES.values():
            for platform_name, _ in operation_platforms:
                all_platforms.add(platform_name)

        for platform_name in all_platforms:
            self.health[platform_name] = PlatformHealth(name=platform_name)

    async def get_platform(
        self,
        operation_type: str,
        attempt: int = 0,
        max_attempts: int = 5,
        **kwargs
    ) -> PlatformSpec:
        """
        Get the best available platform for an operation type

        Args:
            operation_type: Type of operation ("image_editing", "image_generation", etc.)
            attempt: Current attempt number (internal use)
            max_attempts: Maximum fallback attempts
            **kwargs: Additional context (quality_boost, budget, etc.)

        Returns:
            PlatformSpec: Selected platform with metadata

        Raises:
            RuntimeError: If all platforms fail
        """
        if operation_type not in self.PLATFORM_PRIORITIES:
            raise ValueError(f"Unknown operation type: {operation_type}")

        platforms = self.PLATFORM_PRIORITIES[operation_type]

        # Track which platforms we've tried
        tried_platforms = set()

        for platform_name, model_name in platforms:
            # Skip if we've already tried this platform
            if platform_name in tried_platforms:
                continue

            tried_platforms.add(platform_name)

            # Check platform health
            health = self.health.get(platform_name)
            if health and not self._is_platform_healthy(health):
                logger.warning(f"⏭️ Skipping unhealthy platform: {platform_name}")
                continue

            # Create platform spec
            platform = PlatformSpec(
                name=platform_name,
                model=model_name,
                operation_types=[operation_type],
                priority=platforms.index((platform_name, model_name)),
                estimated_cost=self._get_estimated_cost(platform_name, operation_type),
                estimated_time=self._get_estimated_time(platform_name, operation_type),
                api_key_env=self._get_api_key_env(platform_name)
            )

            logger.info(f"🎯 Selected platform for {operation_type}: {platform_name} ({model_name})")
            return platform

        # If we get here, all platforms were unhealthy or none exist
        if attempt < max_attempts:
            logger.warning(f"⚠️ All platforms unhealthy for {operation_type}, retrying...")
            # Reset health cache and try again
            self._reset_health_cache()
            return await self.get_platform(operation_type, attempt + 1, max_attempts, **kwargs)

        # All platforms failed
        raise RuntimeError(
            f"All AI platforms failed for operation '{operation_type}'. "
            f"Tried: {', '.join(tried_platforms)}"
        )

    async def report_success(
        self,
        platform: PlatformSpec,
        operation_type: str,
        response_time: Optional[float] = None
    ):
        """Report successful operation on a platform"""
        health = self.health.get(platform.name)
        if not health:
            return

        health.last_success = datetime.utcnow()
        health.consecutive_failures = 0
        health.total_requests += 1

        if response_time:
            # Update average response time (exponential moving average)
            if health.avg_response_time == 0:
                health.avg_response_time = response_time
            else:
                health.avg_response_time = (health.avg_response_time * 0.8) + (response_time * 0.2)

        health.is_healthy = True

        logger.debug(f"✅ {platform.name} success for {operation_type} ({response_time:.2f}s)")

    async def report_failure(
        self,
        platform: PlatformSpec,
        operation_type: str,
        error: Exception,
        response_time: Optional[float] = None
    ):
        """Report failed operation on a platform"""
        health = self.health.get(platform.name)
        if not health:
            return

        health.last_failure = datetime.utcnow()
        health.consecutive_failures += 1
        health.total_requests += 1
        health.total_failures += 1

        # Mark as unhealthy if too many consecutive failures
        if health.consecutive_failures >= 3:
            health.is_healthy = False
            logger.warning(f"🚫 Marking {platform.name} as unhealthy after {health.consecutive_failures} failures")

        # Special handling for credit exhaustion
        error_msg = str(error).lower()
        if "credit" in error_msg or "quota" in error_msg or "billing" in error_msg:
            logger.warning(f"💳 Platform {platform.name} has credit issues: {error}")
            # Don't mark as permanently unhealthy for credit issues (temporary)
            health.is_healthy = True  # Keep healthy but will fail on next attempt

        logger.warning(f"❌ {platform.name} failure for {operation_type}: {error}")

    async def with_fallback(
        self,
        operation_type: str,
        operation_func,
        *args,
        **kwargs
    ) -> Tuple[Any, PlatformSpec]:
        """
        Execute an operation with automatic fallback to next platform

        Usage:
            result, platform = await manager.with_fallback(
                "image_editing",
                lambda p: stability_service.erase_objects(p, ...),
                image_data=...
            )

        Args:
            operation_type: Type of operation
            operation_func: Callable that takes platform and returns result
            *args, **kwargs: Arguments for operation_func

        Returns:
            Tuple of (result, platform_used)
        """
        last_error = None
        platforms_tried = []

        for attempt in range(5):  # Try up to 5 platforms
            try:
                platform = await self.get_platform(operation_type, attempt=attempt)
                platforms_tried.append(platform)  # Store the PlatformSpec OBJECT, not the name

                start_time = time.time()
                result = await operation_func(platform, *args, **kwargs)
                response_time = time.time() - start_time

                await self.report_success(platform, operation_type, response_time)
                return result, platform

            except Exception as e:
                last_error = e
                platform = platforms_tried[-1] if platforms_tried else None  # Now platform is a PlatformSpec object
                if platform:
                    await self.report_failure(platform, operation_type, e)
                continue

        # If we get here, all platforms failed
        raise RuntimeError(
            f"All platforms failed for {operation_type}. "
            f"Tried: {', '.join(platforms_tried)}. Last error: {last_error}"
        )

    def _is_platform_healthy(self, health: PlatformHealth) -> bool:
        """Check if a platform is currently healthy"""
        if not health.is_healthy:
            # Check if we should retry after cache TTL
            if health.last_failure:
                time_since_failure = datetime.utcnow() - health.last_failure
                if time_since_failure < timedelta(seconds=self.cache_ttl):
                    return False
                else:
                    # Reset to healthy after cache expires
                    health.is_healthy = True
                    health.consecutive_failures = 0

        return True

    def _reset_health_cache(self):
        """Reset all platform health (for retry scenarios)"""
        for health in self.health.values():
            health.is_healthy = True
            health.consecutive_failures = 0

    def _get_estimated_cost(self, platform_name: str, operation_type: str) -> float:
        """Get estimated cost for a platform/operation combination"""
        # Rough estimates - should be updated with real pricing
        cost_map = {
            "pollinations": 0.0,
            "huggingface": 0.0,
            "groq": 0.0,
            "xai": 0.0,
            "fal": 0.00001,
            "flux_pro": 0.002,
            "stability": 0.001,
            "replicate": 0.002,
            "google": 0.0003,
            "together": 0.0001,
            "openai": 0.0006,
            "anthropic": 0.00125,
            "piapi": 0.03,
            "aimlapi": 0.01,
        }
        return cost_map.get(platform_name, 0.0)

    def _get_estimated_time(self, platform_name: str, operation_type: str) -> float:
        """Get estimated time for a platform/operation combination"""
        # Rough estimates in seconds
        time_map = {
            "pollinations": 4.0,
            "huggingface": 6.0,
            "groq": 1.5,
            "xai": 2.0,
            "fal": 3.0,
            "flux_pro": 6.0,
            "stability": 5.0,
            "replicate": 8.0,
            "google": 3.0,
            "together": 4.0,
            "openai": 2.5,
            "anthropic": 3.0,
            "piapi": 30.0,
            "aimlapi": 45.0,
        }
        return time_map.get(platform_name, 5.0)

    def _get_api_key_env(self, platform_name: str) -> Optional[str]:
        """Get environment variable name for platform's API key"""
        env_map = {
            "stability": "STABILITY_API_KEY",
            "replicate": "REPLICATE_API_TOKEN",
            "fal": "FAL_API_KEY",
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "groq": "GROQ_API_KEY",
            "xai": "XAI_API_KEY",
            "google": "GOOGLE_AI_API_KEY",
            "together": "TOGETHER_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
            "minimax": "MINIMAX_API_KEY",
            "aimlapi": "AIMLAPI_API_KEY",
            "piapi": "X_API_KEY",
        }
        return env_map.get(platform_name)

    def get_health_status(self) -> Dict[str, Any]:
        """Get health status for all platforms"""
        status = {}
        for platform_name, health in self.health.items():
            status[platform_name] = {
                "is_healthy": health.is_healthy,
                "consecutive_failures": health.consecutive_failures,
                "total_requests": health.total_requests,
                "failure_rate": (
                    health.total_failures / health.total_requests
                    if health.total_requests > 0 else 0
                ),
                "avg_response_time": health.avg_response_time,
                "last_success": health.last_success.isoformat() if health.last_success else None,
                "last_failure": health.last_failure.isoformat() if health.last_failure else None,
            }
        return status


# Global instance
ai_platform_manager = AIPlatformManager()
