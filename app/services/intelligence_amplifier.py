"""
Intelligence Amplifier Service
Uses AI Router with automatic fallback to extract comprehensive marketing intelligence
Replaces CampaignForge's 6 separate enhancers with a single unified analysis
"""
import json
import logging
from typing import Dict, Any
from datetime import datetime
from app.core.config.settings import settings
from app.services.ai_router import ai_router
import anthropic
import openai

logger = logging.getLogger(__name__)


class IntelligenceAmplifier:
    """
    Unified intelligence amplifier using AI Router with fallback
    Extracts product, market, and marketing intelligence in a single pass
    """

    def __init__(self):
        self.ai_router = ai_router
        # Clients will be created dynamically based on selected provider

    async def amplify_intelligence(self, scraped_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point: Analyze scraped data and extract comprehensive intelligence

        Args:
            scraped_data: Dictionary containing scraped sales page data
                {
                    'metadata': {...},
                    'text_content': str,
                    'images': [...],
                    'scraped_at': str
                }

        Returns:
            Comprehensive intelligence dictionary with product, market, and marketing data
        """
        try:
            logger.info("🧠 Amplifying intelligence with AI Router (auto-fallback enabled)...")

            # Prepare prompt
            prompt = self._build_intelligence_prompt(scraped_data)

            # Debug: Check if env vars are set
            import os
            ai_chat_quality = os.getenv("AI_CHAT_QUALITY", "NOT_SET")
            logger.info(f"[DEBUG] AI_CHAT_QUALITY env var: {ai_chat_quality[:50]}...")

            # FALLBACK: If router not configured, use Groq directly (FREE!)
            if ai_chat_quality == "NOT_SET":
                logger.warning("⚠️ AI Router not configured, using Groq directly as fallback")
                response_text = await self._call_groq_direct(prompt)
                result = {
                    "result": response_text,
                    "provider": "groq",
                    "model": "llama-3.1-70b-versatile",
                    "estimated_cost_usd": 0.0
                }
            else:
                # Use AI Router for intelligence analysis with automatic fallback
                result = await self.ai_router.call_with_fallback(
                    use_case="chat_quality",
                    call_func=self._call_provider,
                    prompt_tokens=len(prompt) // 4,  # Rough estimate
                    gen_tokens=4096,
                    budget_usd=0.10,  # Max $0.10 per analysis
                    prompt=prompt
                )

            # Extract response text based on provider
            response_text = result["result"]

            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            intelligence = json.loads(response_text)

            # Add metadata
            intelligence['amplified_at'] = datetime.utcnow().isoformat()
            intelligence['model'] = f"{result['provider']}:{result['model']}"
            intelligence['estimated_cost_usd'] = result.get('estimated_cost_usd', 0)

            # Add scraped sales page data
            intelligence['sales_page'] = {
                'url': scraped_data['metadata']['url'],
                'title': scraped_data['metadata']['title'],
                'description': scraped_data['metadata']['description'],
                'keywords': scraped_data['metadata']['keywords'],
                'word_count': scraped_data.get('word_count', 0),
                'scraped_at': scraped_data.get('scraped_at')
            }

            # Add image data
            intelligence['images'] = [
                {
                    'r2_url': img['r2_url'],
                    'type': img['classification']['type'],
                    'quality_score': img['classification']['quality_score'],
                    'has_transparency': img.get('has_transparency', False),
                    'dimensions': img.get('dimensions', {})
                }
                for img in scraped_data.get('images', [])
                if img.get('success')
            ]

            logger.info(f"✅ Intelligence amplified successfully")
            logger.info(f"   - Confidence: {intelligence.get('analysis', {}).get('confidence_score', 0)}")
            logger.info(f"   - Images: {len(intelligence['images'])}")

            return intelligence

        except Exception as e:
            logger.error(f"❌ Intelligence amplification failed: {str(e)}")
            raise

    async def _call_groq_direct(self, prompt: str) -> str:
        """
        Direct Groq/XAI fallback when router not configured

        Args:
            prompt: Prompt text

        Returns:
            Response text from Groq or XAI
        """
        # Try Groq first (FREE)
        try:
            client = openai.AsyncOpenAI(
                api_key=settings.GROQ_API_KEY,
                base_url="https://api.groq.com/openai/v1"
            )

            response = await client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                max_tokens=4096,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )

            logger.info("✅ Groq direct call successful (FREE!)")
            return response.choices[0].message.content.strip()

        except Exception as groq_error:
            logger.warning(f"Groq failed ({groq_error}), trying XAI/Grok...")

            # Fallback to XAI (Grok) - cheap alternative
            try:
                client = openai.AsyncOpenAI(
                    api_key=settings.XAI_API_KEY,
                    base_url="https://api.x.ai/v1"
                )

                response = await client.chat.completions.create(
                    model="grok-beta",
                    max_tokens=4096,
                    temperature=0,
                    messages=[{"role": "user", "content": prompt}]
                )

                logger.info("✅ XAI/Grok call successful (~$0.005)")
                return response.choices[0].message.content.strip()

            except Exception as xai_error:
                logger.error(f"Both Groq and XAI failed. Groq: {groq_error}, XAI: {xai_error}")
                raise Exception(f"All free/cheap providers failed. Please check API keys or add Anthropic credits.")

    async def _call_provider(self, spec, prompt: str) -> str:
        """
        Call AI provider based on spec (works with Anthropic, OpenAI-compatible, Groq, etc.)

        Args:
            spec: ProviderSpec from AI Router
            prompt: Prompt text

        Returns:
            Response text from provider
        """
        try:
            if spec.name == "anthropic":
                # Anthropic Claude
                client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
                response = await client.messages.create(
                    model=spec.model,
                    max_tokens=4096,
                    temperature=0,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text.strip()

            elif spec.name in ["openai", "groq", "together", "deepseek"]:
                # OpenAI-compatible providers (Groq, Together, DeepSeek, etc.)
                api_key_map = {
                    "openai": settings.OPENAI_API_KEY,
                    "groq": settings.GROQ_API_KEY,
                    "together": settings.TOGETHER_API_KEY,
                    "deepseek": settings.DEEPSEEK_API_KEY,
                }

                base_url_map = {
                    "groq": "https://api.groq.com/openai/v1",
                    "together": "https://api.together.xyz/v1",
                    "deepseek": "https://api.deepseek.com",
                }

                client = openai.AsyncOpenAI(
                    api_key=api_key_map.get(spec.name),
                    base_url=base_url_map.get(spec.name)
                )

                response = await client.chat.completions.create(
                    model=spec.model,
                    max_tokens=4096,
                    temperature=0,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.choices[0].message.content.strip()

            else:
                raise ValueError(f"Unsupported provider: {spec.name}")

        except Exception as e:
            logger.error(f"Provider {spec.name} call failed: {e}")
            raise

    def _build_intelligence_prompt(self, scraped_data: Dict[str, Any]) -> str:
        """Build comprehensive intelligence extraction prompt"""

        metadata = scraped_data.get('metadata', {})
        text_content = scraped_data.get('text_content', '')
        image_count = len(scraped_data.get('images', []))

        prompt = f"""You are an expert marketing intelligence analyst. Analyze this sales page and extract comprehensive intelligence for affiliate marketers.

SALES PAGE CONTENT:
{text_content[:15000]}

METADATA:
- Title: {metadata.get('title', 'N/A')}
- Description: {metadata.get('description', 'N/A')}
- URL: {metadata.get('url', 'N/A')}
- Images Found: {image_count}

Extract the following intelligence and return as valid JSON (no markdown formatting):

{{
  "product": {{
    "name": "Product name",
    "category": "Primary product category",
    "features": ["Feature 1", "Feature 2", ...],  // 5-10 key features
    "benefits": ["Benefit 1", "Benefit 2", ...],  // 5-10 primary benefits
    "pain_points": ["Pain 1", "Pain 2", ...],     // 5-10 pain points addressed
    "solutions": ["Solution 1", "Solution 2", ...], // How product solves each pain point
    "ingredients_or_components": ["Component 1", "Component 2", ...],  // If applicable
    "technical_specs": {{}},                       // Technical details if available
    "unique_mechanism": "What makes this product different/unique"
  }},
  "market": {{
    "category": "Market category (health, wealth, relationships, etc.)",
    "subcategory": "More specific niche",
    "positioning": "budget|mid-tier|premium",
    "target_audience": {{
      "primary": "Primary demographic",
      "age_range": "Age range if mentioned",
      "gender": "male|female|all",
      "psychographics": "Lifestyle, values, goals",
      "pain_level": "How desperate/motivated the audience is"
    }},
    "competitive_advantages": ["Advantage 1", "Advantage 2", ...],
    "pricing_strategy": "Value proposition and pricing approach",
    "price_points": ["$X", "$Y", ...]  // All prices mentioned
  }},
  "marketing": {{
    "hooks": ["Hook 1", "Hook 2", ...],            // 5-10 attention-grabbing phrases
    "angles": ["Angle 1", "Angle 2", ...],         // 5-10 marketing angles used
    "primary_emotion": "Fear|Desire|Curiosity|Hope|etc",
    "testimonials": [
      {{
        "quote": "Testimonial text",
        "author": "Author name if available",
        "result": "Specific result achieved"
      }}
    ],
    "social_proof": {{
      "customer_count": "Number of customers if mentioned",
      "ratings": "Rating score if present",
      "media_mentions": ["Mention 1", "Mention 2", ...]
    }},
    "guarantees": ["Guarantee 1", "Guarantee 2", ...],
    "risk_reversals": ["How they reduce risk", ...],
    "urgency_tactics": ["Scarcity element 1", ...],
    "cta_strategy": {{
      "primary_cta": "Main call to action",
      "cta_placement": "Where CTAs appear",
      "cta_language": "Specific wording used"
    }},
    "objections_handled": [
      {{
        "objection": "Common objection",
        "response": "How they address it"
      }}
    ]
  }},
  "analysis": {{
    "confidence_score": 0.0-1.0,  // How confident you are in this analysis
    "completeness_score": 0.0-1.0,  // How complete the sales page info is
    "funnel_stage": "awareness|consideration|decision",
    "sophistication_level": 1-5,  // Market sophistication (1=new, 5=very mature)
    "recommended_angles": [
      {{
        "angle": "Marketing angle name",
        "reasoning": "Why this angle would work",
        "priority": "high|medium|low"
      }}
    ],
    "content_gaps": ["What's missing from the sales page"],
    "affiliate_opportunities": ["How affiliates can best promote this"],
    "compliance_notes": ["FTC compliance considerations for affiliates"]
  }}
}}

IMPORTANT:
- Be specific and extract actual text from the page, not generic descriptions
- Focus on what would help affiliate marketers create compelling content
- If information isn't available, use empty arrays/strings rather than guessing
- Prioritize quality over quantity - only include genuinely useful information"""

        return prompt

    def calculate_intelligence_score(self, intelligence: Dict[str, Any]) -> int:
        """
        Calculate overall intelligence quality score (0-100)

        Args:
            intelligence: Amplified intelligence dictionary

        Returns:
            Score from 0-100
        """
        score = 0

        # Product intelligence (40 points)
        product = intelligence.get('product', {})
        if len(product.get('features', [])) >= 5:
            score += 10
        if len(product.get('benefits', [])) >= 5:
            score += 10
        if len(product.get('pain_points', [])) >= 5:
            score += 10
        if product.get('unique_mechanism'):
            score += 10

        # Market intelligence (30 points)
        market = intelligence.get('market', {})
        if market.get('target_audience', {}).get('primary'):
            score += 10
        if market.get('positioning'):
            score += 10
        if len(market.get('competitive_advantages', [])) >= 3:
            score += 10

        # Marketing intelligence (30 points)
        marketing = intelligence.get('marketing', {})
        if len(marketing.get('hooks', [])) >= 5:
            score += 10
        if len(marketing.get('angles', [])) >= 5:
            score += 10
        if len(marketing.get('testimonials', [])) >= 1:
            score += 10

        return min(100, score)
