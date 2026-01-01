# app/plugins/image_editor/services/ai_platform_router.py
"""
Enhanced AI Platform Router - Uses ALL Available Platforms
Supports: Replicate, Stability, Together, FAL, OpenAI, and more!
"""

import os
from typing import Tuple, Optional, Literal
from enum import Enum


class AIPlatform(str, Enum):
    """Available AI platforms (based on your environment variables)"""
    REPLICATE = "replicate"
    STABILITY = "stability"
    TOGETHER = "together"
    FAL = "fal"
    OPENAI = "openai"  # DALL-E can do inpainting
    HUGGINGFACE = "huggingface"  # Free option


class AIOperation(str, Enum):
    """Supported AI operations"""
    INPAINT = "inpaint"
    ERASE = "erase"
    BACKGROUND_REMOVE = "background_remove"
    SEARCH_REPLACE = "search_replace"
    OUTPAINT = "outpaint"
    UPSCALE = "upscale"
    SKETCH_TO_IMAGE = "sketch_to_image"


class AIPlatformRouter:
    """
    Enhanced router - uses ALL available platforms from environment
    Priority: Cost savings while maintaining quality
    """
    
    # Platform availability (checks YOUR environment variables)
    _platform_availability = {
        AIPlatform.REPLICATE: bool(os.getenv("REPLICATE_API_TOKEN")),
        AIPlatform.STABILITY: bool(os.getenv("STABILITY_API_KEY")),
        AIPlatform.TOGETHER: bool(os.getenv("TOGETHER_API_KEY")),
        AIPlatform.FAL: bool(os.getenv("FAL_API_KEY")),
        AIPlatform.OPENAI: bool(os.getenv("OPENAI_API_KEY")),
        AIPlatform.HUGGINGFACE: True,  # Always available (free, no key needed for some models)
    }
    
    # Enhanced platform routing with ALL your platforms
    # Format: {operation: [(platform, quality_score, cost_score), ...]}
    # quality_score: 1-5 (5 = best)
    # cost_score: 1-5 (5 = cheapest)
    _operation_routing = {
        AIOperation.INPAINT: [
            (AIPlatform.REPLICATE, 4, 5),    # LaMa - Very good, very cheap ($0.008)
            (AIPlatform.FAL, 4, 4),          # Fast, good quality ($0.01)
            (AIPlatform.TOGETHER, 4, 4),     # Good quality ($0.01)
            (AIPlatform.STABILITY, 5, 1),    # Best quality, expensive ($0.04)
            (AIPlatform.HUGGINGFACE, 3, 5),  # OK quality, free
        ],
        AIOperation.ERASE: [
            (AIPlatform.REPLICATE, 4, 5),    # LaMa - Best for erasing ($0.008)
            (AIPlatform.FAL, 4, 4),          # Fast erasing ($0.01)
            (AIPlatform.STABILITY, 5, 1),    # Best quality ($0.04)
        ],
        AIOperation.BACKGROUND_REMOVE: [
            (AIPlatform.HUGGINGFACE, 4, 5),  # RMBG-1.4 - Excellent & FREE!
            (AIPlatform.REPLICATE, 4, 5),    # BiRefNet - Very good ($0.005)
            (AIPlatform.FAL, 4, 4),          # Fast ($0.008)
            (AIPlatform.STABILITY, 5, 1),    # Best ($0.04)
        ],
        AIOperation.SEARCH_REPLACE: [
            (AIPlatform.STABILITY, 5, 1),    # Best quality ($0.04)
            (AIPlatform.REPLICATE, 4, 4),    # Good quality ($0.01)
            (AIPlatform.TOGETHER, 4, 4),     # Good quality ($0.01)
        ],
        AIOperation.OUTPAINT: [
            (AIPlatform.REPLICATE, 4, 5),    # SDXL Outpainting ($0.01)
            (AIPlatform.TOGETHER, 4, 4),     # SDXL ($0.01)
            (AIPlatform.FAL, 4, 4),          # Fast ($0.012)
            (AIPlatform.STABILITY, 5, 1),    # Best ($0.04)
        ],
        AIOperation.UPSCALE: [
            (AIPlatform.REPLICATE, 4, 5),    # Real-ESRGAN - Excellent ($0.01)
            (AIPlatform.FAL, 4, 4),          # Fast upscaling ($0.015)
            (AIPlatform.TOGETHER, 4, 4),     # Good ($0.015)
            (AIPlatform.STABILITY, 5, 1),    # Best ($0.08)
        ],
        AIOperation.SKETCH_TO_IMAGE: [
            (AIPlatform.STABILITY, 5, 1),    # Best quality ($0.04)
            (AIPlatform.TOGETHER, 4, 4),     # Good ($0.01)
            (AIPlatform.REPLICATE, 4, 4),    # Good ($0.01)
        ],
    }
    
    # Enhanced cost table (USD per operation)
    _platform_costs = {
        AIPlatform.REPLICATE: {
            AIOperation.INPAINT: 0.008,
            AIOperation.ERASE: 0.008,
            AIOperation.BACKGROUND_REMOVE: 0.005,
            AIOperation.OUTPAINT: 0.01,
            AIOperation.UPSCALE: 0.01,
            AIOperation.SEARCH_REPLACE: 0.01,
            AIOperation.SKETCH_TO_IMAGE: 0.01,
        },
        AIPlatform.STABILITY: {
            AIOperation.INPAINT: 0.04,
            AIOperation.ERASE: 0.04,
            AIOperation.BACKGROUND_REMOVE: 0.04,
            AIOperation.SEARCH_REPLACE: 0.04,
            AIOperation.OUTPAINT: 0.04,
            AIOperation.UPSCALE: 0.08,
            AIOperation.SKETCH_TO_IMAGE: 0.04,
        },
        AIPlatform.TOGETHER: {
            AIOperation.INPAINT: 0.01,
            AIOperation.SEARCH_REPLACE: 0.01,
            AIOperation.OUTPAINT: 0.01,
            AIOperation.UPSCALE: 0.015,
            AIOperation.SKETCH_TO_IMAGE: 0.01,
        },
        AIPlatform.FAL: {
            AIOperation.INPAINT: 0.01,
            AIOperation.ERASE: 0.01,
            AIOperation.BACKGROUND_REMOVE: 0.008,
            AIOperation.OUTPAINT: 0.012,
            AIOperation.UPSCALE: 0.015,
        },
        AIPlatform.HUGGINGFACE: {
            AIOperation.BACKGROUND_REMOVE: 0.0,  # FREE!
            AIOperation.INPAINT: 0.0,  # FREE (with rate limits)
        },
    }
    
    @classmethod
    def get_best_platform(
        cls,
        operation: AIOperation,
        priority: Literal["cost", "quality", "balanced"] = "balanced"
    ) -> Tuple[AIPlatform, float]:
        """
        Get the best available platform for an operation
        
        Args:
            operation: The AI operation to perform
            priority: "cost" (cheapest), "quality" (best), or "balanced"
        
        Returns:
            Tuple of (platform, estimated_cost_usd)
        
        Raises:
            ValueError: If no platform is available for the operation
        """
        if operation not in cls._operation_routing:
            raise ValueError(f"Unsupported operation: {operation}")
        
        # Get routing options for this operation
        routing_options = cls._operation_routing[operation]
        
        # Filter to only available platforms
        available_options = [
            (platform, quality, cost)
            for platform, quality, cost in routing_options
            if cls._platform_availability.get(platform, False)
        ]
        
        if not available_options:
            raise ValueError(f"No AI platform available for operation: {operation}")
        
        # Select based on priority
        if priority == "cost":
            # Sort by cost (descending), then quality (descending)
            selected = sorted(available_options, key=lambda x: (-x[2], -x[1]))[0]
        elif priority == "quality":
            # Sort by quality (descending), then cost (descending)
            selected = sorted(available_options, key=lambda x: (-x[1], -x[2]))[0]
        else:  # balanced
            # Sort by combined score (quality + cost), descending
            selected = sorted(available_options, key=lambda x: (-(x[1] + x[2])))[0]
        
        platform = selected[0]
        
        # Get estimated cost
        cost = cls._platform_costs.get(platform, {}).get(operation, 0.02)
        
        return platform, cost
    
    @classmethod
    def get_all_platforms_for_operation(
        cls,
        operation: AIOperation
    ) -> list[Tuple[AIPlatform, int, int, float]]:
        """
        Get all available platforms for an operation with their scores
        
        Args:
            operation: The AI operation
        
        Returns:
            List of (platform, quality_score, cost_score, estimated_cost_usd)
        """
        if operation not in cls._operation_routing:
            return []
        
        routing_options = cls._operation_routing[operation]
        
        result = []
        for platform, quality, cost_score in routing_options:
            if cls._platform_availability.get(platform, False):
                estimated_cost = cls._platform_costs.get(platform, {}).get(operation, 0.02)
                result.append((platform, quality, cost_score, estimated_cost))
        
        return result
    
    @classmethod
    def estimate_cost(cls, platform: AIPlatform, operation: AIOperation) -> float:
        """Estimate cost for a specific platform and operation"""
        return cls._platform_costs.get(platform, {}).get(operation, 0.02)
    
    @classmethod
    def is_platform_available(cls, platform: AIPlatform) -> bool:
        """Check if a platform is available (API key configured)"""
        return cls._platform_availability.get(platform, False)
    
    @classmethod
    def get_platform_stats(cls) -> dict:
        """
        Get statistics about platform availability and costs
        
        Returns:
            Dictionary with platform stats
        """
        stats = {
            "available_platforms": [],
            "operations": {},
            "total_platforms_configured": 0,
        }
        
        # List available platforms
        for platform, available in cls._platform_availability.items():
            if available:
                stats["available_platforms"].append(platform.value)
                stats["total_platforms_configured"] += 1
        
        # For each operation, show best platform and all options
        for operation in AIOperation:
            try:
                best_platform, cost = cls.get_best_platform(operation, priority="balanced")
                stats["operations"][operation.value] = {
                    "best_platform": best_platform.value,
                    "estimated_cost_usd": cost,
                    "all_options": [
                        {
                            "platform": p.value,
                            "quality_score": q,
                            "cost_score": c,
                            "estimated_cost_usd": ec,
                        }
                        for p, q, c, ec in cls.get_all_platforms_for_operation(operation)
                    ]
                }
            except ValueError:
                stats["operations"][operation.value] = {
                    "best_platform": None,
                    "estimated_cost_usd": 0.0,
                    "all_options": []
                }
        
        return stats
    
    @classmethod
    def get_available_platforms_summary(cls) -> dict:
        """
        Get summary of which platforms are available
        
        Returns:
            Dictionary showing platform availability
        """
        return {
            platform.value: {
                "available": available,
                "env_var": cls._get_env_var_name(platform)
            }
            for platform, available in cls._platform_availability.items()
        }
    
    @classmethod
    def _get_env_var_name(cls, platform: AIPlatform) -> str:
        """Get the environment variable name for a platform"""
        env_vars = {
            AIPlatform.REPLICATE: "REPLICATE_API_TOKEN",
            AIPlatform.STABILITY: "STABILITY_API_KEY",
            AIPlatform.TOGETHER: "TOGETHER_API_KEY",
            AIPlatform.FAL: "FAL_API_KEY",
            AIPlatform.OPENAI: "OPENAI_API_KEY",
            AIPlatform.HUGGINGFACE: "HUGGINGFACE_API_KEY (optional)",
        }
        return env_vars.get(platform, "Unknown")


# Convenience function for quick access
def get_best_platform_for_operation(
    operation: str,
    priority: str = "balanced"
) -> Tuple[str, float]:
    """
    Convenience function to get best platform
    
    Args:
        operation: Operation name (e.g., "inpaint", "erase")
        priority: "cost", "quality", or "balanced"
    
    Returns:
        Tuple of (platform_name, estimated_cost)
    """
    op = AIOperation(operation)
    platform, cost = AIPlatformRouter.get_best_platform(op, priority)
    return platform.value, cost


def get_platform_availability() -> dict:
    """Get summary of available platforms"""
    return AIPlatformRouter.get_available_platforms_summary()