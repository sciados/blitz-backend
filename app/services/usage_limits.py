"""
Usage Limits Service
Checks and tracks user usage against tier limits
"""

import logging
from datetime import datetime, date
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

logger = logging.getLogger(__name__)


class UsageLimitsService:
    """
    Service for checking and tracking user usage limits
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def get_tier_limits(self, tier_name: str) -> Optional[Dict[str, Any]]:
        """Get limits configuration for a tier"""
        query = text("""
            SELECT tier_name, monthly_ai_video_scripts, monthly_ai_text_generations,
                   monthly_ai_image_generations, monthly_campaigns, max_tokens_per_request,
                   can_use_premium_ai, can_use_templates, description
            FROM tier_limits
            WHERE tier_name = :tier_name
        """)
        result = await self.db.execute(query, {"tier_name": tier_name})
        row = result.fetchone()

        if not row:
            logger.warning(f"[LIMITS] No tier limits found for: {tier_name}")
            return None

        return {
            "tier_name": row[0],
            "monthly_ai_video_scripts": row[1],
            "monthly_ai_text_generations": row[2],
            "monthly_ai_image_generations": row[3],
            "monthly_campaigns": row[4],
            "max_tokens_per_request": row[5],
            "can_use_premium_ai": row[6],
            "can_use_templates": row[7],
            "description": row[8]
        }

    async def get_user_usage(self, user_id: int) -> Dict[str, int]:
        """Get current month's usage for a user"""
        # Get first day of current month
        today = date.today()
        month_start = date(today.year, today.month, 1)

        query = text("""
            SELECT ai_video_scripts_used, ai_text_generations_used,
                   ai_image_generations_used, campaigns_created,
                   estimated_cost_usd
            FROM user_usage
            WHERE user_id = :user_id AND usage_month = :month_start
        """)
        result = await self.db.execute(query, {
            "user_id": user_id,
            "month_start": month_start
        })
        row = result.fetchone()

        if not row:
            # No usage record yet this month
            return {
                "ai_video_scripts_used": 0,
                "ai_text_generations_used": 0,
                "ai_image_generations_used": 0,
                "campaigns_created": 0,
                "estimated_cost_usd": 0.0
            }

        return {
            "ai_video_scripts_used": row[0] or 0,
            "ai_text_generations_used": row[1] or 0,
            "ai_image_generations_used": row[2] or 0,
            "campaigns_created": row[3] or 0,
            "estimated_cost_usd": float(row[4] or 0)
        }

    async def check_limit(
        self,
        user_id: int,
        tier_name: str,
        usage_type: str
    ) -> Tuple[bool, str, int, Optional[int]]:
        """
        Check if user is within their limit for a specific usage type

        Args:
            user_id: User ID
            tier_name: User's tier (standard, pro, business)
            usage_type: Type of usage to check (ai_video_scripts, ai_text_generations, ai_image_generations, campaigns)

        Returns:
            Tuple of (allowed: bool, message: str, current_usage: int, limit: int or None)
        """
        limits = await self.get_tier_limits(tier_name)
        usage = await self.get_user_usage(user_id)

        if not limits:
            # No limits configured, allow by default
            return (True, "No limits configured", 0, None)

        # Map usage type to field names
        type_mapping = {
            "ai_video_scripts": ("monthly_ai_video_scripts", "ai_video_scripts_used"),
            "ai_text_generations": ("monthly_ai_text_generations", "ai_text_generations_used"),
            "ai_image_generations": ("monthly_ai_image_generations", "ai_image_generations_used"),
            "campaigns": ("monthly_campaigns", "campaigns_created")
        }

        if usage_type not in type_mapping:
            logger.error(f"[LIMITS] Unknown usage type: {usage_type}")
            return (True, "Unknown usage type", 0, None)

        limit_field, usage_field = type_mapping[usage_type]
        limit_value = limits.get(limit_field)
        current_usage = usage.get(usage_field, 0)

        # NULL limit means unlimited
        if limit_value is None:
            return (True, "Unlimited", current_usage, None)

        if current_usage >= limit_value:
            message = f"Monthly limit reached ({current_usage}/{limit_value})"
            logger.info(f"[LIMITS] User {user_id} hit {usage_type} limit: {message}")
            return (False, message, current_usage, limit_value)

        remaining = limit_value - current_usage
        return (True, f"{remaining} remaining", current_usage, limit_value)

    async def increment_usage(
        self,
        user_id: int,
        usage_type: str,
        estimated_cost: float = 0.0
    ) -> bool:
        """
        Increment usage counter for a user

        Args:
            user_id: User ID
            usage_type: Type of usage (ai_video_scripts, ai_text_generations, ai_image_generations, campaigns)
            estimated_cost: Estimated cost in USD for this operation

        Returns:
            True if successful
        """
        # Get first day of current month
        today = date.today()
        month_start = date(today.year, today.month, 1)

        # Map usage type to column name
        column_mapping = {
            "ai_video_scripts": "ai_video_scripts_used",
            "ai_text_generations": "ai_text_generations_used",
            "ai_image_generations": "ai_image_generations_used",
            "campaigns": "campaigns_created"
        }

        if usage_type not in column_mapping:
            logger.error(f"[LIMITS] Unknown usage type for increment: {usage_type}")
            return False

        column_name = column_mapping[usage_type]

        # Upsert: Insert or update usage record
        query = text(f"""
            INSERT INTO user_usage (user_id, usage_month, {column_name}, estimated_cost_usd)
            VALUES (:user_id, :month_start, 1, :cost)
            ON CONFLICT (user_id, usage_month)
            DO UPDATE SET
                {column_name} = user_usage.{column_name} + 1,
                estimated_cost_usd = user_usage.estimated_cost_usd + :cost,
                updated_at = CURRENT_TIMESTAMP
        """)

        await self.db.execute(query, {
            "user_id": user_id,
            "month_start": month_start,
            "cost": estimated_cost
        })
        await self.db.commit()

        logger.info(f"[LIMITS] Incremented {usage_type} for user {user_id}, cost: ${estimated_cost:.4f}")
        return True

    async def get_user_usage_summary(
        self,
        user_id: int,
        tier_name: str
    ) -> Dict[str, Any]:
        """
        Get complete usage summary for a user including limits

        Returns dict with usage, limits, and remaining for each type
        """
        limits = await self.get_tier_limits(tier_name)
        usage = await self.get_user_usage(user_id)

        if not limits:
            limits = {
                "monthly_ai_video_scripts": None,
                "monthly_ai_text_generations": None,
                "monthly_ai_image_generations": None,
                "monthly_campaigns": None
            }

        def calc_remaining(limit, used):
            if limit is None:
                return None  # Unlimited
            return max(0, limit - used)

        return {
            "ai_video_scripts": {
                "used": usage["ai_video_scripts_used"],
                "limit": limits.get("monthly_ai_video_scripts"),
                "remaining": calc_remaining(limits.get("monthly_ai_video_scripts"), usage["ai_video_scripts_used"])
            },
            "ai_text_generations": {
                "used": usage["ai_text_generations_used"],
                "limit": limits.get("monthly_ai_text_generations"),
                "remaining": calc_remaining(limits.get("monthly_ai_text_generations"), usage["ai_text_generations_used"])
            },
            "ai_image_generations": {
                "used": usage["ai_image_generations_used"],
                "limit": limits.get("monthly_ai_image_generations"),
                "remaining": calc_remaining(limits.get("monthly_ai_image_generations"), usage["ai_image_generations_used"])
            },
            "campaigns": {
                "used": usage["campaigns_created"],
                "limit": limits.get("monthly_campaigns"),
                "remaining": calc_remaining(limits.get("monthly_campaigns"), usage["campaigns_created"])
            },
            "estimated_cost_usd": usage["estimated_cost_usd"],
            "tier": tier_name,
            "can_use_premium_ai": limits.get("can_use_premium_ai", False)
        }


# Helper functions for easy import
async def check_usage_limit(
    db: AsyncSession,
    user_id: int,
    tier_name: str,
    usage_type: str
) -> Tuple[bool, str, int, Optional[int]]:
    """Check if user is within limit"""
    service = UsageLimitsService(db)
    return await service.check_limit(user_id, tier_name, usage_type)


async def increment_usage(
    db: AsyncSession,
    user_id: int,
    usage_type: str,
    estimated_cost: float = 0.0
) -> bool:
    """Increment usage counter"""
    service = UsageLimitsService(db)
    return await service.increment_usage(user_id, usage_type, estimated_cost)


async def get_usage_summary(
    db: AsyncSession,
    user_id: int,
    tier_name: str
) -> Dict[str, Any]:
    """Get user's usage summary"""
    service = UsageLimitsService(db)
    return await service.get_user_usage_summary(user_id, tier_name)
