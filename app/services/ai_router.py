"""
AI Provider Router
Dynamic, cost-optimized routing across multiple AI providers
Implements fallback and monitoring
"""
import random
import logging
from typing import Optional, Dict, Any, List
from app.config import settings, AI_PROVIDERS, TASK_BUDGETS
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class AIRouter:
    """Routes AI requests to cost-optimized providers with fallback"""
    
    def __init__(self):
        self.providers = AI_PROVIDERS
        self.task_budgets = TASK_BUDGETS
        self.fallback_enabled = settings.AI_FALLBACK_ENABLED
        self.cost_optimization = settings.AI_COST_OPTIMIZATION

    def select_provider(
        self,
        tier: str = "budget",
        task_type: Optional[str] = None,
        require_grounding: bool = False
    ) -> Dict[str, Any]:
        """
        Select the best AI provider based on tier and requirements
        
        Args:
            tier: Provider tier (ultra_cheap, budget, standard, premium)
            task_type: Optional task type for budget checking
            require_grounding: If True, prefer providers good at RAG
            
        Returns:
            Dict with provider info: {name, key, cost_per_1k}
        """
        # Override tier if grounding required
        if require_grounding:
            tier = "standard"  # Cohere is better for RAG
        
        # Get available providers for tier
        available = self.providers.get(tier, self.providers["budget"])
        
        if not available:
            logger.warning(f"No providers available for tier {tier}, falling back to budget")
            available = self.providers["budget"]
        
        # Filter out providers without keys
        valid_providers = [p for p in available if p["key"]]
        
        if not valid_providers:
            raise ValueError(f"No valid API keys configured for tier: {tier}")
        
        # Select provider (random for load balancing)
        provider = random.choice(valid_providers)
        
        logger.info(f"Selected provider: {provider['name']} (tier: {tier})")
        return provider

    def check_budget(self, task_type: str, estimated_tokens: int) -> bool:
        """
        Check if task is within budget
        
        Args:
            task_type: Type of task
            estimated_tokens: Estimated token count
            
        Returns:
            True if within budget
        """
        if not self.cost_optimization:
            return True
        
        budget = self.task_budgets.get(task_type, 0.01)
        estimated_cost = (estimated_tokens / 1000) * 0.001  # Rough estimate
        
        if estimated_cost > budget:
            logger.warning(
                f"Task {task_type} estimated cost ${estimated_cost:.4f} "
                f"exceeds budget ${budget:.4f}"
            )
            return False
        
        return True

    def get_fallback_chain(self, initial_tier: str) -> List[str]:
        """
        Get fallback tier chain
        
        Args:
            initial_tier: Starting tier
            
        Returns:
            List of tiers to try in order
        """
        if not self.fallback_enabled:
            return [initial_tier]
        
        tier_order = ["ultra_cheap", "budget", "standard", "premium"]
        
        try:
            start_idx = tier_order.index(initial_tier)
            return tier_order[start_idx:]
        except ValueError:
            return tier_order

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def call_with_fallback(
        self,
        tier: str,
        task_type: str,
        call_func,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Call AI provider with automatic fallback
        
        Args:
            tier: Initial tier to try
            task_type: Task type for budget checking
            call_func: Async function to call provider
            **kwargs: Arguments to pass to call_func
            
        Returns:
            Response dict with result and metadata
        """
        fallback_chain = self.get_fallback_chain(tier)
        last_error = None
        
        for current_tier in fallback_chain:
            try:
                provider = self.select_provider(
                    tier=current_tier,
                    task_type=task_type,
                    require_grounding=kwargs.get("require_grounding", False)
                )
                
                logger.info(f"Attempting {provider['name']} for {task_type}")
                
                result = await call_func(provider=provider, **kwargs)
                
                return {
                    "success": True,
                    "result": result,
                    "provider": provider["name"],
                    "tier": current_tier,
                    "cost_per_1k": provider["cost_per_1k"]
                }
                
            except Exception as e:
                last_error = e
                logger.warning(
                    f"Provider {provider['name']} failed: {e}. "
                    f"Trying next in fallback chain..."
                )
                continue
        
        # All providers failed
        logger.error(f"All providers failed for {task_type}: {last_error}")
        raise Exception(f"All AI providers failed: {last_error}")

    def estimate_cost(
        self,
        tokens_in: int,
        tokens_out: int,
        provider_name: str
    ) -> float:
        """
        Estimate cost for a completed request
        
        Args:
            tokens_in: Input tokens
            tokens_out: Output tokens
            provider_name: Provider used
            
        Returns:
            Estimated cost in USD
        """
        # Find provider cost
        for tier_providers in self.providers.values():
            for p in tier_providers:
                if p["name"] == provider_name:
                    cost_per_1k = p["cost_per_1k"]
                    total_tokens = tokens_in + tokens_out
                    return (total_tokens / 1000) * cost_per_1k
        
        # Default fallback
        return (tokens_in + tokens_out) / 1000 * 0.001


# Global router instance
ai_router = AIRouter()