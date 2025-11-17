"""Automated provider configuration management."""
import httpx
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class EngineInfo:
    """Information about an available engine."""
    id: str
    name: str
    type: str = "image"  # image, video, etc.
    max_resolution: Optional[str] = None
    cost_per_image: float = 0.0
    quality_score: float = 0.0  # 0-100, higher is better
    speed_score: float = 0.0    # 0-100, higher is faster

class ImageProviderConfig:
    """Manages provider configurations with automatic engine updates."""

    def __init__(self):
        self.engines_cache: Dict[str, EngineInfo] = {}
        self.last_updated = None

    async def discover_stability_engines(self) -> List[EngineInfo]:
        """Discover available Stability AI engines."""
        engines = []
        api_key = self._get_api_key("STABILITY_API_KEY")
        if not api_key:
            logger.warning("STABILITY_API_KEY not set, skipping Stability AI engine discovery")
            return engines

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    "https://api.stability.ai/v1/engines/list",
                    headers={"Authorization": f"Bearer {api_key}"}
                )

                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Found {len(data)} Stability AI engines")

                    for engine in data:
                        # Determine quality score based on model
                        quality = self._score_stability_engine(engine["name"])

                        engines.append(EngineInfo(
                            id=engine["id"],
                            name=engine["name"],
                            max_resolution=engine.get("max_resolution", "1024x1024"),
                            quality_score=quality,
                            speed_score=self._estimate_speed(engine["name"])
                        ))

                        logger.info(f"  - {engine['id']} (quality: {quality}%, speed: {self._estimate_speed(engine['name'])}%)")
                else:
                    logger.error(f"Failed to list Stability engines: {response.status_code}")

        except Exception as e:
            logger.error(f"Error discovering Stability engines: {str(e)}")

        return engines

    def _score_stability_engine(self, engine_name: str) -> float:
        """Score engine based on name (higher = better quality)."""
        name = engine_name.lower()

        if "ultra" in name:
            return 100  # Ultra - highest quality model
        elif "xl" in name and ("1.0" in name or "1024" in name):
            return 95  # SDXL 1.0 - high quality
        elif "xl" in name:
            return 90  # SDXL variants
        elif "3.5" in name:
            return 85  # SD 3.5
        elif "3" in name:
            return 80  # SD 3
        elif "v1-6" in name or "v1.6" in name:
            return 60  # Older SD 1.6
        elif "v1" in name:
            return 50  # SD 1.x
        else:
            return 70  # Unknown, assume decent

    def _estimate_speed(self, engine_name: str) -> float:
        """Estimate speed based on engine name (higher = faster)."""
        name = engine_name.lower()

        if "turbo" in name:
            return 95  # Turbo models are fastest
        elif "light" in name or "small" in name:
            return 80  # Smaller models
        elif "medium" in name:
            return 65  # Medium models
        elif "large" in name or "xl" in name:
            return 40  # Larger models, slower
        else:
            return 50  # Default

    async def discover_fal_engines(self) -> List[EngineInfo]:
        """Discover available FAL engines."""
        engines = []

        # FAL doesn't have a discovery endpoint, but their models are well-documented
        # We hardcode the known stable models here
        known_engines = [
            {"id": "sdxl-turbo", "name": "SDXL Turbo", "max_resolution": "1024x1024", "quality": 85, "speed": 95},
            {"id": "sdxl-lightning", "name": "SDXL Lightning", "max_resolution": "1024x1024", "quality": 80, "speed": 90},
            {"id": "flux-schnell", "name": "Flux Schnell", "max_resolution": "1024x1024", "quality": 90, "speed": 85},
            {"id": "flux-dev", "name": "Flux Dev", "max_resolution": "1024x1024", "quality": 95, "speed": 60},
        ]

        for engine in known_engines:
            engines.append(EngineInfo(
                id=engine["id"],
                name=engine["name"],
                max_resolution=engine["max_resolution"],
                quality_score=engine["quality"],
                speed_score=engine["speed"],
                cost_per_image=0.00001  # FAL free tier
            ))

        logger.info(f"Loaded {len(known_engines)} FAL engines")
        return engines

    def _get_api_key(self, key_name: str) -> Optional[str]:
        """Get API key from environment."""
        import os
        return os.getenv(key_name)

    async def update_all_providers(self) -> Dict[str, str]:
        """Update all provider configurations with latest engines."""
        logger.info("🔄 Starting provider engine discovery...")

        updates = {}

        # Discover engines for each provider
        stability_engines = await self.discover_stability_engines()
        fal_engines = await self.discover_fal_engines()

        # Select best engines
        if stability_engines:
            best_stability = max(stability_engines, key=lambda x: x.quality_score)
            updates["stability"] = best_stability.id
            logger.info(f"✅ Selected Stability AI engine: {best_stability.id} (quality: {best_stability.quality_score}%)")

        if fal_engines:
            # Prefer fast engines for general use
            best_fal = max(fal_engines, key=lambda x: x.speed_score if x.speed_score > 85 else x.quality_score)
            updates["fal"] = best_fal.id
            logger.info(f"✅ Selected FAL engine: {best_fal.id} (speed: {best_fal.speed_score}%)")

        # TODO: Add discovery for other providers (HuggingFace, Ideogram, Leonardo, Replicate)

        self.last_updated = datetime.now()
        logger.info(f"✅ Provider discovery complete at {self.last_updated}")

        return updates

# Global instance
provider_config = ImageProviderConfig()
