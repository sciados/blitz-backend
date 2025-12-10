"""
Video Template Engine
Generates video scripts from pre-built templates based on product category
"""

import random
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

logger = logging.getLogger(__name__)


class VideoTemplateEngine:
    """
    Template-based video script generator
    Uses human-crafted templates with smart keyword insertion
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def generate_script(
        self,
        campaign_id: int,
        marketing_angle: str,
        duration: int,
        keywords: Dict[str, Any]
    ) -> str:
        """
        Generate video script from template

        Args:
            campaign_id: Campaign ID to get product category
            marketing_angle: problem_solution, transformation, etc.
            duration: 5 or 10 seconds
            keywords: User-selected keywords (ingredients, features, benefits, pain_points)

        Returns:
            Generated video script as string
        """
        try:
            # Step 1: Get campaign category
            category = await self._get_campaign_category(campaign_id)
            logger.info(f"[TEMPLATE] Campaign {campaign_id} category: {category}")

            # Step 2: Select random template from category
            template = await self._select_template(category, marketing_angle, duration)
            logger.info(f"[TEMPLATE] Selected template ID: {template['id']}")

            # Step 3: Insert user keywords
            script = await self._insert_keywords(template['template_text'], keywords)
            logger.info(f"[TEMPLATE] Generated script: {script[:100]}...")

            # Step 4: Increment usage count
            await self._increment_usage(template['id'])

            return script

        except Exception as e:
            logger.error(f"[TEMPLATE] Error generating script: {str(e)}")
            # Fallback to simple AI generation if template fails
            raise

    async def _get_campaign_category(self, campaign_id: int) -> str:
        """Get product category from campaign"""
        query = text("""
            SELECT product_category
            FROM campaigns
            WHERE id = :campaign_id
        """)
        result = await self.db.execute(query, {"campaign_id": campaign_id})
        row = result.fetchone()

        if not row:
            logger.warning(f"[TEMPLATE] Campaign {campaign_id} not found, defaulting to Health")
            return "Health"

        category = row[0] or "Health"
        return category

    async def _select_template(
        self,
        category: str,
        marketing_angle: str,
        duration: int
    ) -> Dict[str, Any]:
        """Select random template with smart weighting"""

        # Query templates for category/angle/duration
        query = text("""
            SELECT id, category, subcategory, marketing_angle, duration,
                   template_text, usage_count, last_used
            FROM video_templates
            WHERE category = :category
              AND marketing_angle = :marketing_angle
              AND duration = :duration_seconds
            ORDER BY RANDOM()
            LIMIT 10
        """)

        result = await self.db.execute(query, {
            "category": category,
            "marketing_angle": marketing_angle,
            "duration_seconds": f"{duration}s"
        })

        templates = result.fetchall()

        if not templates:
            logger.warning(f"[TEMPLATE] No templates found for {category}/{marketing_angle}/{duration}s")
            # Fallback to any template in category
            fallback_query = text("""
                SELECT id, category, subcategory, marketing_angle, duration,
                       template_text, usage_count, last_used
                FROM video_templates
                WHERE category = :category
                ORDER BY RANDOM()
                LIMIT 1
            """)
            result = await self.db.execute(fallback_query, {"category": category})
            templates = result.fetchall()

            if not templates:
                raise Exception(f"No templates found for category: {category}")

        # Calculate weights (less used = higher priority)
        weighted_templates = []
        for template in templates:
            template_dict = {
                'id': template[0],
                'category': template[1],
                'subcategory': template[2],
                'marketing_angle': template[3],
                'duration': template[4],
                'template_text': template[5],
                'usage_count': template[6] or 0,
                'last_used': template[7]
            }

            # Calculate weight (inverse of usage, with recency boost)
            usage_count = template_dict['usage_count']
            weight = max(1, 100 - usage_count)  # Less used templates get higher weight

            weighted_templates.append((template_dict, weight))

        # Select from weighted pool
        templates_list = [wt[0] for wt in weighted_templates]
        weights = [wt[1] for wt in weighted_templates]

        selected = random.choices(templates_list, weights=weights, k=1)[0]
        return selected

    async def _insert_keywords(self, template: str, keywords: Dict[str, Any]) -> str:
        """
        Insert user keywords into template

        Template slots:
        {product} - Campaign product name
        {ingredient} - Primary ingredient/element
        {feature} - Key feature
        {benefit} - Main benefit
        {pain_point} - Problem being solved
        {before_state} - Before transformation
        {after_state} - After transformation
        {problem} - The issue
        {solution} - How it's solved
        {financial_outcome} - Money-related benefit
        """

        # Default values if keywords not provided
        replacements = {
            'product_name': keywords.get('product_name', 'the product'),
            'ingredients': self._select_random(keywords.get('ingredients', [])),
            'features': self._select_random(keywords.get('features', [])),
            'benefits': self._select_random(keywords.get('benefits', [])),
            'pain_points': self._select_random(keywords.get('pain_points', [])),
            'before_state': 'struggling with health challenges',
            'after_state': 'feeling energized and confident',
            'problem': 'health challenges',
            'solution': 'natural solution',
            'financial_outcome': 'financial success'
        }

        # Apply replacements
        script = template
        for placeholder, value in replacements.items():
            if value:
                script = script.replace(f'{{{placeholder}}}', value)
            else:
                script = script.replace(f'{{{placeholder}}}', replacements[placeholder])

        return script

    def _select_random(self, items: List[str]) -> str:
        """Select random item from list or return empty string"""
        if not items:
            return ''
        return random.choice(items) if items else ''

    async def _increment_usage(self, template_id: int):
        """Increment template usage count"""
        query = text("""
            UPDATE video_templates
            SET usage_count = usage_count + 1,
                last_used = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :template_id
        """)
        await self.db.execute(query, {"template_id": template_id})
        await self.db.commit()


# Helper function to generate script
async def generate_video_script(
    db: AsyncSession,
    campaign_id: int,
    marketing_angle: str,
    duration: int,
    keywords: Dict[str, Any]
) -> str:
    """Helper function to generate video script"""
    engine = VideoTemplateEngine(db)
    return await engine.generate_script(campaign_id, marketing_angle, duration, keywords)
