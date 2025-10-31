"""
Intelligence Compiler Service - Main Orchestrator
Coordinates scraping, amplification, RAG, and global intelligence sharing
"""
import hashlib
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.future import select

from app.db.models import Campaign, ProductIntelligence
from app.services.scraper_service import SalesPageScraper
from app.services.intelligence_amplifier import IntelligenceAmplifier
from app.services.embeddings_openai import OpenAIEmbeddingService

logger = logging.getLogger(__name__)


class IntelligenceCompilerService:
    """
    Main orchestrator for intelligence compilation with global sharing
    Implements the 3-step process: Scrape → Amplify → RAG
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.scraper = SalesPageScraper()
        self.amplifier = IntelligenceAmplifier()
        self.embeddings = OpenAIEmbeddingService()

    async def compile_for_campaign(
        self,
        campaign_id: int,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main entry point: Compile intelligence for a campaign with global sharing

        Args:
            campaign_id: Campaign ID
            options: Compilation options
                {
                    'deep_scrape': bool,
                    'scrape_images': bool,
                    'max_images': int,
                    'enable_rag': bool,
                    'force_recompile': bool
                }

        Returns:
            Compilation result with costs and intelligence info
        """
        start_time = datetime.utcnow()
        options = options or {}

        try:
            # Step 1: Get campaign
            campaign = await self._get_campaign(campaign_id)
            if not campaign:
                return {
                    'success': False,
                    'error': 'Campaign not found'
                }

            logger.info(f"🚀 Compiling intelligence for campaign {campaign_id}: {campaign.name}")
            logger.info(f"   URL: {campaign.product_url}")

            # Step 2: Generate URL hash
            url_hash = self._generate_url_hash(campaign.product_url)

            # Step 3: Check for existing intelligence
            existing_intelligence = await self._find_existing_intelligence(url_hash)

            if existing_intelligence and not options.get('force_recompile'):
                # CACHE HIT: Reuse existing intelligence
                logger.info(f"✨ Cache HIT! Reusing existing intelligence (ID: {existing_intelligence.id})")

                result = await self._link_campaign_to_intelligence(campaign, existing_intelligence)

                processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

                return {
                    'success': True,
                    'campaign_id': campaign_id,
                    'status': 'completed',
                    'was_cached': True,
                    'product_intelligence_id': existing_intelligence.id,
                    'intelligence_summary': self._generate_summary(existing_intelligence.intelligence_data),
                    'processing_time_ms': round(processing_time),
                    'costs': {
                        'scraping': 0,
                        'analysis': 0,
                        'embeddings': 0,
                        'total': 0
                    },
                    'cache_info': {
                        'originally_compiled_at': existing_intelligence.compiled_at.isoformat(),
                        'times_reused': existing_intelligence.reference_count,
                        'compilation_version': existing_intelligence.compilation_version
                    }
                }

            # CACHE MISS: Compile new intelligence
            logger.info(f"🆕 Cache MISS. Starting full compilation...")

            result = await self._compile_new_intelligence(
                campaign,
                url_hash,
                options
            )

            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            result['processing_time_ms'] = round(processing_time)

            return result

        except Exception as e:
            logger.error(f"❌ Intelligence compilation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'campaign_id': campaign_id
            }

    async def _compile_new_intelligence(
        self,
        campaign: Campaign,
        url_hash: str,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform full 3-step compilation for new intelligence

        Returns:
            Compilation result with costs
        """
        costs = {
            'scraping': 0,
            'analysis': 0,
            'embeddings': 0,
            'storage': 0
        }

        # Step 1: Scrape Sales Page
        logger.info("📄 Step 1/3: Scraping sales page...")

        # Create ProductIntelligence record first (need ID for image storage)
        product_intelligence = ProductIntelligence(
            product_url=campaign.product_url,
            url_hash=url_hash,
            compilation_version="1.0"
        )
        self.db.add(product_intelligence)
        await self.db.flush()  # Get ID without committing

        scraped_data = await self.scraper.scrape_sales_page(
            url=campaign.product_url,
            product_intelligence_id=product_intelligence.id,
            max_images=options.get('max_images', 10),
            scrape_images=options.get('scrape_images', True)
        )

        if not scraped_data.get('success'):
            return {
                'success': False,
                'error': f"Scraping failed: {scraped_data.get('error')}"
            }

        logger.info(f"✅ Scraped {scraped_data.get('word_count', 0)} words, {scraped_data.get('image_count', 0)} images")

        # Step 2: Amplify Intelligence
        logger.info("🧠 Step 2/3: Amplifying intelligence with Claude...")

        amplified_intelligence = await self.amplifier.amplify_intelligence(scraped_data)

        # Estimate Claude cost (rough: ~5K input + 2K output tokens)
        costs['analysis'] = 0.05

        logger.info(f"✅ Intelligence amplified")

        # Step 3: Generate RAG Embeddings
        if options.get('enable_rag', True):
            logger.info("🔢 Step 3/3: Generating embeddings...")

            embedding_text = self.embeddings.prepare_text_for_embedding(amplified_intelligence)
            embedding_vector = await self.embeddings.generate_embedding(embedding_text)

            product_intelligence.intelligence_embedding = embedding_vector

            # Calculate embedding cost
            token_count = self.embeddings.estimate_tokens(embedding_text)
            costs['embeddings'] = self.embeddings.get_embedding_cost(token_count)

            logger.info(f"✅ Generated {len(embedding_vector)}D embedding")
        else:
            logger.info("⏭️  Step 3/3: Skipping RAG (disabled)")

        # Store intelligence in ProductIntelligence
        product_intelligence.intelligence_data = amplified_intelligence
        product_intelligence.compiled_at = datetime.utcnow()

        # Link campaign to intelligence
        await self._link_campaign_to_intelligence(campaign, product_intelligence)

        await self.db.commit()

        costs['total'] = sum(costs.values())

        logger.info(f"🎉 Compilation complete! Total cost: ${costs['total']:.4f}")

        return {
            'success': True,
            'campaign_id': campaign.id,
            'status': 'completed',
            'was_cached': False,
            'product_intelligence_id': product_intelligence.id,
            'intelligence_summary': self._generate_summary(amplified_intelligence),
            'costs': costs
        }

    async def _get_campaign(self, campaign_id: int) -> Optional[Campaign]:
        """Retrieve campaign from database"""
        stmt = select(Campaign).where(Campaign.id == campaign_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    def _generate_url_hash(self, url: str) -> str:
        """Generate SHA-256 hash for URL (for fast cache lookup)"""
        # Normalize URL (remove trailing slash, convert to lowercase)
        normalized_url = url.rstrip('/').lower()
        return hashlib.sha256(normalized_url.encode()).hexdigest()

    async def _find_existing_intelligence(
        self,
        url_hash: str
    ) -> Optional[ProductIntelligence]:
        """Check if intelligence already exists for this URL"""
        stmt = select(ProductIntelligence).where(
            ProductIntelligence.url_hash == url_hash
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _link_campaign_to_intelligence(
        self,
        campaign: Campaign,
        intelligence: ProductIntelligence
    ):
        """Link campaign to shared intelligence and update usage metrics"""
        campaign.product_intelligence_id = intelligence.id

        # Update intelligence usage metrics
        intelligence.reference_count += 1
        intelligence.last_accessed_at = datetime.utcnow()

        await self.db.commit()

        logger.info(f"🔗 Linked campaign {campaign.id} to intelligence {intelligence.id}")
        logger.info(f"   Total campaigns using this intelligence: {intelligence.reference_count}")

    def _generate_summary(self, intelligence_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of intelligence for API response"""
        if not intelligence_data:
            return {}

        return {
            'product_name': intelligence_data.get('product', {}).get('name', 'Unknown'),
            'category': intelligence_data.get('market', {}).get('category', 'Unknown'),
            'confidence_score': intelligence_data.get('analysis', {}).get('confidence_score', 0),
            'images_found': len(intelligence_data.get('images', [])),
            'features_count': len(intelligence_data.get('product', {}).get('features', [])),
            'benefits_count': len(intelligence_data.get('product', {}).get('benefits', [])),
            'marketing_angles_count': len(intelligence_data.get('marketing', {}).get('angles', []))
        }

    async def get_intelligence_for_campaign(
        self,
        campaign_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve compiled intelligence for a campaign

        Args:
            campaign_id: Campaign ID

        Returns:
            Intelligence data or None if not compiled
        """
        campaign = await self._get_campaign(campaign_id)
        if not campaign or not campaign.product_intelligence_id:
            return None

        stmt = select(ProductIntelligence).where(
            ProductIntelligence.id == campaign.product_intelligence_id
        )
        result = await self.db.execute(stmt)
        intelligence = result.scalar_one_or_none()

        if not intelligence:
            return None

        return intelligence.intelligence_data

    async def get_compilation_progress(
        self,
        campaign_id: int
    ) -> Dict[str, Any]:
        """
        Get current compilation progress (for progress tracking UI)

        Args:
            campaign_id: Campaign ID

        Returns:
            Progress status
        """
        # This is a simplified version - in production you'd use
        # a task queue (Celery) or cache (Redis) to track progress
        campaign = await self._get_campaign(campaign_id)

        if not campaign:
            return {
                'status': 'not_found',
                'progress': 0
            }

        if campaign.product_intelligence_id:
            return {
                'status': 'completed',
                'progress': 100,
                'message': 'Intelligence compilation complete'
            }

        return {
            'status': 'pending',
            'progress': 0,
            'message': 'Compilation not started'
        }
