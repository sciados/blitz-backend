"""
Intelligence Amplifier Service with RAG Integration
Uses AI Router with automatic fallback + RAG research for comprehensive intelligence
Replaces CampaignForge's 6 separate enhancers with a single unified analysis
"""
import json
import logging
import re
from typing import Dict, Any
from datetime import datetime
from app.core.config.settings import settings
from app.services.ai_router import ai_router
from app.services.rag import rag_system
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

    async def amplify_intelligence(
        self,
        scraped_data: Dict[str, Any],
        enable_rag: bool = True,
        intelligence_level: str = "standard"
    ) -> Dict[str, Any]:
        """
        Main entry point: Analyze scraped data and extract comprehensive intelligence with RAG

        Args:
            scraped_data: Dictionary containing scraped sales page data
                {
                    'metadata': {...},
                    'text_content': str,
                    'images': [...],
                    'scraped_at': str
                }
            enable_rag: Enable RAG research (default: True)
            intelligence_level: "basic" (10 searches), "standard" (20), "comprehensive" (35)

        Returns:
            Comprehensive intelligence dictionary with product, market, and marketing data
        """
        try:
            logger.info("🧠 Amplifying intelligence with AI Router + RAG...")

            # Step 1: Extract basic product info from sales page
            basic_product_info = self._extract_basic_product_info(scraped_data)
            logger.info(f"📝 Extracted basic info: {basic_product_info.get('name', 'Unknown product')}")

            # Step 2: Conduct RAG research (optional)
            research_data = None
            if enable_rag:
                try:
                    logger.info(f"🔍 Starting RAG research (level: {intelligence_level})...")
                    research_data = await rag_system.research_product(
                        basic_product_info,
                        intelligence_level=intelligence_level
                    )
                    logger.info(f"✅ RAG complete: {research_data.get('total_sources', 0)} sources, "
                              f"${research_data.get('estimated_cost_usd', 0):.4f} cost")
                except Exception as rag_error:
                    logger.warning(f"⚠️ RAG research failed, continuing without it: {str(rag_error)}")
                    research_data = None

            # Step 3: Build enhanced prompt with RAG data
            prompt = self._build_intelligence_prompt(scraped_data, research_data)

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

            # Calculate intelligence data size
            intelligence_json = json.dumps(intelligence)
            data_size_chars = len(intelligence_json)
            data_size_kb = data_size_chars / 1024

            logger.info(f"✅ Intelligence amplified successfully")
            logger.info(f"   - Confidence: {intelligence.get('analysis', {}).get('confidence_score', 0)}")
            logger.info(f"   - Images: {len(intelligence['images'])}")
            logger.info(f"   - Data size: {data_size_chars:,} characters ({data_size_kb:.2f} KB)")

            # Log breakdown by section
            product_size = len(json.dumps(intelligence.get('product', {})))
            market_size = len(json.dumps(intelligence.get('market', {})))
            marketing_size = len(json.dumps(intelligence.get('marketing', {})))
            analysis_size = len(json.dumps(intelligence.get('analysis', {})))
            logger.info(f"   - Product: {product_size:,} chars | Market: {market_size:,} chars | Marketing: {marketing_size:,} chars | Analysis: {analysis_size:,} chars")

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
                model="llama-3.3-70b-versatile",  # Updated from decommissioned 3.1
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
                    model="grok-3",  # Updated from deprecated grok-beta
                    max_tokens=4096,
                    temperature=0,
                    messages=[{"role": "user", "content": prompt}]
                )

                logger.info("✅ XAI/Grok call successful (~$0.005)")
                return response.choices[0].message.content.strip()

            except Exception as xai_error:
                logger.warning(f"XAI failed ({xai_error}), trying DeepSeek...")

                # Fallback to DeepSeek - very cheap ($0.0007)
                try:
                    client = openai.AsyncOpenAI(
                        api_key=settings.DEEPSEEK_API_KEY,
                        base_url="https://api.deepseek.com"
                    )

                    response = await client.chat.completions.create(
                        model="deepseek-chat",
                        max_tokens=4096,
                        temperature=0,
                        messages=[{"role": "user", "content": prompt}]
                    )

                    logger.info("✅ DeepSeek call successful (~$0.0007)")
                    return response.choices[0].message.content.strip()

                except Exception as deepseek_error:
                    logger.error(f"All providers failed:")
                    logger.error(f"  - Groq: {groq_error}")
                    logger.error(f"  - XAI: {xai_error}")
                    logger.error(f"  - DeepSeek: {deepseek_error}")
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

    def _build_intelligence_prompt(
        self,
        scraped_data: Dict[str, Any],
        research_data: Dict[str, Any] = None
    ) -> str:
        """Build comprehensive intelligence extraction prompt with RAG data"""

        metadata = scraped_data.get('metadata', {})
        text_content = scraped_data.get('text_content', '')
        image_count = len(scraped_data.get('images', []))

        # Build RAG research section if available
        rag_section = ""
        if research_data and research_data.get('total_sources', 0) > 0:
            rag_summary = self._format_rag_for_prompt(research_data)
            rag_section = f"""

RESEARCH INTELLIGENCE (from {research_data.get('total_sources', 0)} verified sources):
{rag_summary}

Use this research data to enhance your analysis with scientific evidence, clinical studies, and market data."""

        prompt = f"""You are an expert marketing intelligence analyst. Analyze this sales page and extract comprehensive intelligence for affiliate marketers.

SALES PAGE CONTENT:
{text_content[:15000]}

METADATA:
- Title: {metadata.get('title', 'N/A')}
- Description: {metadata.get('description', 'N/A')}
- URL: {metadata.get('url', 'N/A')}
- Images Found: {image_count}{rag_section}

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

    def _extract_basic_product_info(self, scraped_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract basic product information from scraped data for RAG research

        Returns:
            Dictionary with name, ingredients, features, type
        """
        text_content = scraped_data.get('text_content', '').lower()
        metadata = scraped_data.get('metadata', {})

        # Extract product name (from title or first heading)
        product_name = metadata.get('title', 'Product').split('|')[0].split('-')[0].strip()

        # Detect product type/category
        product_type = "product"
        if any(word in text_content for word in ['supplement', 'pill', 'capsule', 'vitamin', 'weight loss']):
            product_type = "health_supplement"
        elif any(word in text_content for word in ['course', 'training', 'program', 'system', 'method']):
            product_type = "educational_program"
        elif any(word in text_content for word in ['software', 'tool', 'app', 'platform']):
            product_type = "software"

        # Extract ingredients (for health products)
        ingredients = []
        ingredient_keywords = ['ingredient', 'contains', 'formula', 'blend', 'extract']
        if any(keyword in text_content for keyword in ingredient_keywords):
            # Simple extraction: look for capitalized words near ingredient keywords
            import re
            # This is a basic extraction - AI will refine it
            potential_ingredients = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', scraped_data.get('text_content', ''))
            ingredients = list(set(potential_ingredients))[:15]  # Limit to 15

        # Extract features (look for bullet points or numbered lists)
        features = []
        feature_patterns = [r'[•\-\*]\s*([^\n]+)', r'\d+\.\s*([^\n]+)']
        for pattern in feature_patterns:
            matches = re.findall(pattern, scraped_data.get('text_content', ''))
            features.extend([m.strip() for m in matches if len(m.strip()) > 10])

        features = features[:10]  # Top 10 features

        return {
            "name": product_name,
            "type": product_type,
            "ingredients": ingredients,
            "features": features,
            "url": metadata.get('url', '')
        }

    def _format_rag_for_prompt(self, research_data: Dict[str, Any]) -> str:
        """Format RAG research data for AI prompt"""
        sections = []

        # Ingredient research
        ingredient_data = research_data.get("research_by_category", {}).get("ingredients", {})
        if ingredient_data and ingredient_data.get("researched"):
            sections.append("INGREDIENT RESEARCH:")
            for ing in ingredient_data.get("researched", [])[:5]:  # Top 5 ingredients
                ingredient = ing.get("ingredient", "")
                sources = ing.get("sources", [])
                if sources:
                    sections.append(f"\n{ingredient}:")
                    for source in sources[:2]:  # Top 2 sources per ingredient
                        title = source.get("title", "")
                        content = source.get("content", "")[:300]  # First 300 chars
                        sections.append(f"  - {title}")
                        if content:
                            sections.append(f"    {content}...")

        # Feature research
        feature_data = research_data.get("research_by_category", {}).get("features", {})
        if feature_data and feature_data.get("sources"):
            sections.append("\n\nFEATURE RESEARCH:")
            for source in feature_data.get("sources", [])[:3]:  # Top 3
                title = source.get("title", "")
                content = source.get("content", "")[:300]
                sections.append(f"  - {title}")
                if content:
                    sections.append(f"    {content}...")

        # Market research
        market_data = research_data.get("research_by_category", {}).get("market", {})
        if market_data and market_data.get("sources"):
            sections.append("\n\nMARKET RESEARCH:")
            for source in market_data.get("sources", [])[:3]:  # Top 3
                title = source.get("title", "")
                content = source.get("content", "")[:300]
                sections.append(f"  - {title}")
                if content:
                    sections.append(f"    {content}...")

        return "\n".join(sections)

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
