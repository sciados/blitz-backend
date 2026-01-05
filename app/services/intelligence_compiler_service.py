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

from app.db.models import Campaign, ProductIntelligence, KnowledgeBase
from app.services.scraper_service import SalesPageScraper
from app.services.intelligence_amplifier import IntelligenceAmplifier
from app.services.embeddings_router import EmbeddingRouterService
from app.services.storage_r2 import r2_storage
from app.services.rag.intelligent_rag import rag_system
from app.services.business_dna_extractor import business_dna_extractor

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
        self.embeddings = EmbeddingRouterService()
        self.r2_storage = r2_storage

    async def compile_for_campaign(
        self,
        campaign_id: int,
        user_role: str,
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

            # Step 2: Check if campaign already linked to product intelligence
            # This happens when campaign is created from product library
            if campaign.product_intelligence_id:
                logger.info(f"📎 Campaign already linked to ProductIntelligence {campaign.product_intelligence_id}")

                # Fetch the existing intelligence
                stmt = select(ProductIntelligence).where(ProductIntelligence.id == campaign.product_intelligence_id)
                result = await self.db.execute(stmt)
                existing_intelligence = result.scalar_one_or_none()

                if existing_intelligence and existing_intelligence.intelligence_data:
                    logger.info(f"✨ Using existing product intelligence (cached)")

                    # Check if RAG research already ingested for this product
                    # Prevents duplicate storage when multiple campaigns use same product
                    if existing_intelligence.intelligence_data.get('research') and options.get('enable_rag', True):
                        # Check if research for this product already exists in KnowledgeBase
                        # Query directly by product_intelligence_id column (not metadata)
                        kb_check = await self.db.execute(
                            select(KnowledgeBase).where(
                                KnowledgeBase.product_intelligence_id == existing_intelligence.id
                            ).limit(1)
                        )
                        existing_kb = kb_check.scalar_one_or_none()

                        if existing_kb:
                            logger.info(f"⏭️  RAG research already in KnowledgeBase (shared across campaigns)")
                            logger.info(f"   - Skipping ingestion to avoid duplicates")
                        else:
                            logger.info(f"📚 First campaign using this product - ingesting RAG research")
                            await self._ingest_research_to_knowledge_base(
                                existing_intelligence.id,
                                existing_intelligence.intelligence_data
                            )

                    await self.db.commit()

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
                        }
                    }

            # Step 3: Generate URL hash
            url_hash = self._generate_url_hash(campaign.product_url)

            # Step 4: Check for existing intelligence by URL hash
            existing_intelligence, is_complete = await self._find_existing_intelligence(url_hash)

            if existing_intelligence and is_complete and not options.get('force_recompile'):
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
                        'times_reused': existing_intelligence.times_used,
                        'compilation_version': existing_intelligence.compilation_version
                    }
                }

            # CACHE MISS or INCOMPLETE: Compile (or recompile) intelligence
            if existing_intelligence and not is_complete:
                logger.info(f"🔄 Found incomplete intelligence (ID: {existing_intelligence.id}). Recompiling...")
            else:
                logger.info(f"🆕 Cache MISS. Starting full compilation...")

            result = await self._compile_new_intelligence(
                campaign,
                url_hash,
                user_role,
                options,
                existing_intelligence_id=existing_intelligence.id if existing_intelligence else None
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

    async def compile_for_product(
        self,
        product_intelligence_id: int,
        user_id: int,
        user_role: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Compile intelligence directly for a ProductIntelligence record (no campaign required).

        This is used when products are submitted to the library and need immediate intelligence
        compilation without a campaign context.

        Args:
            product_intelligence_id: ProductIntelligence record ID
            user_id: User ID for RAG ingestion
            user_role: User role for feature access control (Business DNA)
            options: Compilation options (same as compile_for_campaign)

        Returns:
            Compilation result with costs and intelligence info
        """
        start_time = datetime.utcnow()
        options = options or {}

        try:
            # Step 1: Get ProductIntelligence record
            stmt = select(ProductIntelligence).where(ProductIntelligence.id == product_intelligence_id)
            result = await self.db.execute(stmt)
            product_intelligence = result.scalar_one_or_none()

            if not product_intelligence:
                return {
                    'success': False,
                    'error': 'ProductIntelligence record not found'
                }

            logger.info(f"🚀 Compiling intelligence for product {product_intelligence_id}")
            logger.info(f"   URL: {product_intelligence.product_url}")
            logger.info(f"   Name: {product_intelligence.product_name}")

            # Step 2: Check if already compiled (unless force_recompile)
            # Only skip if we have ACTUAL compiled intelligence (sales_page data from scraping)
            # Don't skip if it only has submission metadata
            is_fully_compiled = (
                product_intelligence.intelligence_data and
                'sales_page' in product_intelligence.intelligence_data and
                product_intelligence.intelligence_data.get('status') != 'pending_intelligence_compilation'
            )

            if is_fully_compiled and not options.get('force_recompile'):
                logger.info(f"✨ Product already has complete intelligence data. Skipping compilation.")
                processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

                return {
                    'success': True,
                    'product_intelligence_id': product_intelligence_id,
                    'status': 'already_compiled',
                    'was_cached': True,
                    'intelligence_summary': self._generate_summary(product_intelligence.intelligence_data),
                    'processing_time_ms': round(processing_time),
                    'costs': {'total': 0}
                }

            # If only has submission metadata, proceed with compilation
            if product_intelligence.intelligence_data and not is_fully_compiled:
                logger.info(f"📝 Product has submission metadata but no compiled intelligence. Proceeding with compilation...")

            # Step 3: Perform compilation (Scrape → Amplify → RAG)
            costs = {
                'scraping': 0,
                'analysis': 0,
                'embeddings': 0,
                'storage': 0
            }

            # Clean up old images if this is a force recompile
            if options.get('force_recompile') and product_intelligence.intelligence_data:
                await self._cleanup_old_images(product_intelligence.intelligence_data)

            # Step 3a: Scrape Sales Page
            logger.info("📄 Step 1/3: Scraping sales page...")

            scraped_data = await self.scraper.scrape_sales_page(
                url=product_intelligence.product_url,
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

            # Step 3b: Amplify Intelligence
            logger.info("🧠 Step 2/3: Amplifying intelligence with Claude...")

            amplified_intelligence = await self.amplifier.amplify_intelligence(scraped_data)

            # Estimate Claude cost
            costs['analysis'] = 0.05

            logger.info(f"✅ Intelligence amplified")


            # Step 2.5: Extract Business DNA (Role-Based - Business & Admin only)
            if user_role in ['business', 'admin']:
                try:
                    logger.info("🧬 Extracting Business DNA (Business/Admin user)...")
                    business_dna = await business_dna_extractor.extract_business_dna(
                        url=product_intelligence.product_url
                    )
                    business_dna["available"] = True
                    business_dna["extracted_by_role"] = user_role
                    amplified_intelligence["business_dna"] = business_dna
                    logger.info(f"✅ Business DNA extracted: {business_dna.get('summary', 'No summary')}")
                except Exception as e:
                    logger.warning(f"⚠️ Business DNA extraction failed (non-critical): {str(e)}")
                    amplified_intelligence["business_dna"] = {
                        "available": False,
                        "error": str(e),
                        "extracted_by_role": user_role
                    }
            else:
                logger.info(f"👨‍💻 User role '{user_role}' - Business DNA not available (Business tier feature)")
                amplified_intelligence["business_dna"] = {
                    "available": False,
                    "tier": "business",
                    "reason": "Business DNA extraction is available for Business tier only",
                    "features": [
                        "Automatic brand color extraction",
                        "Typography and font detection",
                        "Tone of voice analysis",
                        "Visual style guidelines"
                    ],
                    "upgrade_message": "Upgrade to Business tier to unlock brand intelligence",
                    "user_role": user_role
                }
            # Step 3c: Generate RAG Embeddings
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

            # Step 4: Store intelligence in ProductIntelligence
            product_intelligence.intelligence_data = amplified_intelligence
            product_intelligence.compiled_at = datetime.utcnow()
            product_intelligence.compilation_version = "1.0"

            # Remove pending status if it exists (from initial submission)
            if 'status' in amplified_intelligence:
                amplified_intelligence.pop('status', None)

            # Extract and save product metadata for library display
            self._extract_and_save_product_metadata_standalone(
                product_intelligence,
                amplified_intelligence,
                scraped_data
            )

            # Step 5: Skip KnowledgeBase ingestion for product-only compilations
            # KnowledgeBase is campaign-specific and used for content generation
            # Products compiled without campaigns don't need this step
            # The research is still stored in intelligence_data and accessible
            logger.info(f"⏭️  Skipping KnowledgeBase ingestion (product-only compilation, no campaign context)")

            await self.db.commit()

            # Step 6: Auto-check compliance so products become visible to affiliates
            logger.info("⚖️  Checking compliance for affiliate visibility...")
            try:
                from app.services.compliance_checker import ComplianceChecker
                compliance_checker = ComplianceChecker()

                # Extract description from intelligence data
                product_description = None
                if amplified_intelligence.get("product", {}).get("description"):
                    product_description = amplified_intelligence["product"]["description"]
                elif product_intelligence.product_name:
                    product_description = f"Product: {product_intelligence.product_name}"

                # Build content to check
                content_parts = []
                if product_intelligence.product_name:
                    content_parts.append(f"Product: {product_intelligence.product_name}")
                if product_description:
                    content_parts.append(f"Description: {product_description}")
                if product_intelligence.commission_rate:
                    content_parts.append(f"Commission: {product_intelligence.commission_rate}")

                content_to_check = "\n\n".join(content_parts)

                # Check compliance (skip disclosure requirements for product descriptions)
                result = compliance_checker.check_content(
                    content=content_to_check,
                    content_type="landing_page",
                    product_category=product_intelligence.product_category,
                    is_product_description=True  # Skip affiliate disclosure checks for products
                )

                # Save compliance results to intelligence_data
                if product_intelligence.intelligence_data is None:
                    product_intelligence.intelligence_data = {}

                product_intelligence.intelligence_data["compliance"] = {
                    "status": result["status"],
                    "score": result["score"],
                    "issues": result["issues"],
                    "warnings": result.get("warnings", []),
                    "summary": result.get("summary", ""),
                    "checked_at": datetime.utcnow().isoformat()
                }

                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(product_intelligence, "intelligence_data")

                # Auto-publish compliant products to affiliate library
                if result["status"] == "compliant" or result.get("score", 0) >= 90:
                    product_intelligence.is_public = "true"
                    logger.info(f"✅ Product is compliant! Auto-published to affiliate library")
                else:
                    logger.info(f"⚠️  Product is not compliant yet. Visible only to creators/admin")

                await self.db.commit()
                logger.info(f"✅ Compliance check complete - Status: {result['status']}, Score: {result['score']}")

            except Exception as e:
                logger.error(f"⚠️  Compliance check failed: {str(e)}")
                # Don't fail the whole compilation if compliance check fails
                # Product will be visible only to creators/admin

            costs['total'] = sum(costs.values())
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            logger.info(f"🎉 Compilation complete! Total cost: ${costs['total']:.4f}")

            return {
                'success': True,
                'product_intelligence_id': product_intelligence.id,
                'status': 'completed',
                'was_cached': False,
                'intelligence_summary': self._generate_summary(amplified_intelligence),
                'processing_time_ms': round(processing_time),
                'costs': costs
            }

        except Exception as e:
            logger.error(f"❌ Product intelligence compilation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'product_intelligence_id': product_intelligence_id
            }

    async def _compile_new_intelligence(
        self,
        campaign: Campaign,
        url_hash: str,
        user_role: str,
        options: Dict[str, Any],
        existing_intelligence_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Perform full 3-step compilation for new or incomplete intelligence

        Args:
            existing_intelligence_id: If provided, UPDATE this record instead of INSERT
            user_role: User role for feature access control (Business DNA)

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

        # Get or create ProductIntelligence record (need ID for image storage)
        if existing_intelligence_id:
            # Reuse existing incomplete record
            stmt = select(ProductIntelligence).where(ProductIntelligence.id == existing_intelligence_id)
            result = await self.db.execute(stmt)
            product_intelligence = result.scalar_one()

            # Clean up old images if this is a force recompile
            if options.get('force_recompile') and product_intelligence.intelligence_data:
                await self._cleanup_old_images(product_intelligence.intelligence_data)

            # Update affiliate_network if missing
            if not product_intelligence.affiliate_network and campaign.affiliate_network:
                product_intelligence.affiliate_network = campaign.affiliate_network
                logger.info(f"📝 Updated affiliate_network: {campaign.affiliate_network}")

            # Update commission_rate if missing
            if not product_intelligence.commission_rate and campaign.commission_rate:
                product_intelligence.commission_rate = campaign.commission_rate
                logger.info(f"📝 Updated commission_rate: {campaign.commission_rate}")

            logger.info(f"↻ Reusing existing intelligence record (ID: {product_intelligence.id})")
        else:
            # Check if a ProductIntelligence record already exists for this URL
            stmt = select(ProductIntelligence).where(ProductIntelligence.product_url == campaign.product_url)
            result = await self.db.execute(stmt)
            existing_product = result.scalar_one_or_none()

            if existing_product:
                # Reuse existing record
                product_intelligence = existing_product
                logger.info(f"↻ Found existing intelligence record for URL (ID: {product_intelligence.id})")

                # Update affiliate_network if missing
                if not product_intelligence.affiliate_network and campaign.affiliate_network:
                    product_intelligence.affiliate_network = campaign.affiliate_network
                    logger.info(f"📝 Updated affiliate_network: {campaign.affiliate_network}")

                # Update commission_rate if missing
                if not product_intelligence.commission_rate and campaign.commission_rate:
                    product_intelligence.commission_rate = campaign.commission_rate
                    logger.info(f"📝 Updated commission_rate: {campaign.commission_rate}")
            else:
                # Create new record
                product_intelligence = ProductIntelligence(
                    product_url=campaign.product_url,
                    url_hash=url_hash,
                    compilation_version="1.0",
                    affiliate_network=campaign.affiliate_network,  # Copy from campaign
                    commission_rate=campaign.commission_rate  # Copy from campaign if available
                )
                self.db.add(product_intelligence)
                await self.db.flush()  # Get ID without committing
                logger.info(f"✓ Created new intelligence record (ID: {product_intelligence.id})")

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


        # Step 2.5: Extract Business DNA (Role-Based - Business & Admin only)
        if user_role in ['business', 'admin']:
            try:
                logger.info("🧬 Extracting Business DNA (Business/Admin user)...")
                business_dna = await business_dna_extractor.extract_business_dna(
                    url=campaign.product_url
                )
                business_dna["available"] = True
                business_dna["extracted_by_role"] = user_role
                amplified_intelligence["business_dna"] = business_dna
                logger.info(f"✅ Business DNA extracted: {business_dna.get('summary', 'No summary')}")
            except Exception as e:
                logger.warning(f"⚠️ Business DNA extraction failed (non-critical): {str(e)}")
                amplified_intelligence["business_dna"] = {
                    "available": False,
                    "error": str(e),
                    "extracted_by_role": user_role
                }
        else:
            logger.info(f"👨‍💻 User role '{user_role}' - Business DNA not available (Business tier feature)")
            amplified_intelligence["business_dna"] = {
                "available": False,
                "tier": "business",
                "reason": "Business DNA extraction is available for Business tier only",
                "features": [
                    "Automatic brand color extraction",
                    "Typography and font detection",
                    "Tone of voice analysis",
                    "Visual style guidelines"
                ],
                "upgrade_message": "Upgrade to Business tier to unlock brand intelligence",
                "user_role": user_role
            }
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

        # Extract and save product metadata for library display
        self._extract_and_save_product_metadata(
            product_intelligence,
            amplified_intelligence,
            scraped_data,
            campaign
        )

        # Link campaign to intelligence
        await self._link_campaign_to_intelligence(campaign, product_intelligence)

        # Step 4: Ingest RAG research into KnowledgeBase for content generation
        # Research is owned by product and shared across all campaigns
        if amplified_intelligence.get('research') and options.get('enable_rag', True):
            await self._ingest_research_to_knowledge_base(
                product_intelligence.id,
                amplified_intelligence
            )

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
    ) -> tuple[Optional[ProductIntelligence], bool]:
        """
        Check if intelligence already exists for this URL and validate completeness

        Returns:
            Tuple of (intelligence_record, is_complete)
        """
        stmt = select(ProductIntelligence).where(
            ProductIntelligence.url_hash == url_hash
        )
        result = await self.db.execute(stmt)
        intelligence = result.scalar_one_or_none()

        if not intelligence:
            return (None, False)

        # Validate that intelligence is complete
        # Check if intelligence_data exists and has required fields
        if not intelligence.intelligence_data:
            logger.warning(f"Found incomplete intelligence (ID: {intelligence.id}) - intelligence_data is null")
            return (intelligence, False)

        # Check if intelligence_data has key sections
        required_sections = ['product', 'market', 'marketing']
        data = intelligence.intelligence_data
        if not all(section in data for section in required_sections):
            logger.warning(f"Found incomplete intelligence (ID: {intelligence.id}) - missing required sections")
            return (intelligence, False)

        logger.info(f"✓ Found valid cached intelligence (ID: {intelligence.id})")
        return (intelligence, True)

    async def _link_campaign_to_intelligence(
        self,
        campaign: Campaign,
        intelligence: ProductIntelligence
    ):
        """Link campaign to shared intelligence and update usage metrics"""
        campaign.product_intelligence_id = intelligence.id

        # Update intelligence usage metrics
        intelligence.times_used += 1
        intelligence.last_accessed_at = datetime.utcnow()

        # Update affiliate_network if missing (from campaign data)
        if not intelligence.affiliate_network and campaign.affiliate_network:
            intelligence.affiliate_network = campaign.affiliate_network
            logger.info(f"📝 Updated affiliate_network from campaign: {campaign.affiliate_network}")

        # Update commission_rate if missing (from campaign data)
        if not intelligence.commission_rate and campaign.commission_rate:
            intelligence.commission_rate = campaign.commission_rate
            logger.info(f"📝 Updated commission_rate from campaign: {campaign.commission_rate}")

        await self.db.commit()

        logger.info(f"🔗 Linked campaign {campaign.id} to intelligence {intelligence.id}")
        logger.info(f"   Total campaigns using this intelligence: {intelligence.times_used}")

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

    def _extract_and_save_product_metadata(
        self,
        product_intelligence: ProductIntelligence,
        intelligence_data: Dict[str, Any],
        scraped_data: Dict[str, Any],
        campaign: Campaign
    ):
        """
        Extract and save product metadata for public library display

        Extracts:
        - product_name: From intelligence analysis
        - product_category: From market analysis
        - thumbnail_image_url: First product image from R2
        - affiliate_network: From campaign or URL detection
        - commission_rate: From sales page or intelligence data
        """
        # Extract product name
        product_intelligence.product_name = (
            intelligence_data.get('product', {}).get('name') or
            intelligence_data.get('sales_page', {}).get('title', '').strip()[:255] or
            'Unknown Product'
        )

        # Extract product category
        product_intelligence.product_category = (
            intelligence_data.get('market', {}).get('category') or
            intelligence_data.get('product', {}).get('category') or
            'uncategorized'
        )

        # Extract thumbnail image (first image from scraped data)
        images = scraped_data.get('images', [])
        if images and len(images) > 0:
            # Get first image that was successfully uploaded to R2
            for img in images:
                if img.get('r2_url'):
                    product_intelligence.thumbnail_image_url = img['r2_url']
                    break

        # Extract affiliate network
        product_intelligence.affiliate_network = (
            campaign.affiliate_network or
            self._detect_affiliate_network(campaign.product_url) or
            'unknown'
        )

        # Extract commission rate (if mentioned in sales page or intelligence)
        product_intelligence.commission_rate = (
            intelligence_data.get('product', {}).get('commission') or
            intelligence_data.get('sales_page', {}).get('commission_rate') or
            intelligence_data.get('market', {}).get('commission_rate') or
            None
        )

        # Mark as public (default)
        product_intelligence.is_public = "true"

        logger.info(f"📋 Extracted metadata: {product_intelligence.product_name} ({product_intelligence.product_category})")
        if product_intelligence.thumbnail_image_url:
            logger.info(f"🖼️  Thumbnail: {product_intelligence.thumbnail_image_url}")

    def _extract_and_save_product_metadata_standalone(
        self,
        product_intelligence: ProductIntelligence,
        intelligence_data: Dict[str, Any],
        scraped_data: Dict[str, Any]
    ):
        """
        Extract and save product metadata for library display (no campaign required).

        Similar to _extract_and_save_product_metadata but for products submitted
        directly to the library without a campaign.
        """
        # Extract product name
        product_intelligence.product_name = (
            intelligence_data.get('product', {}).get('name') or
            intelligence_data.get('sales_page', {}).get('title', '').strip()[:255] or
            product_intelligence.product_name or  # Use submitted name as fallback
            'Unknown Product'
        )

        # Extract product category
        product_intelligence.product_category = (
            intelligence_data.get('market', {}).get('category') or
            intelligence_data.get('product', {}).get('category') or
            product_intelligence.product_category or  # Use submitted category as fallback
            'uncategorized'
        )

        # Extract thumbnail image (first image from scraped data)
        images = scraped_data.get('images', [])
        if images and len(images) > 0:
            # Get first image that was successfully uploaded to R2
            for img in images:
                if img.get('r2_url'):
                    product_intelligence.thumbnail_image_url = img['r2_url']
                    break

        # Use existing affiliate_network if set, otherwise try to detect
        if not product_intelligence.affiliate_network:
            product_intelligence.affiliate_network = (
                self._detect_affiliate_network(product_intelligence.product_url) or
                'unknown'
            )

        # Extract commission rate (if mentioned in sales page or intelligence)
        # Only override if not already set during submission
        if not product_intelligence.commission_rate:
            product_intelligence.commission_rate = (
                intelligence_data.get('product', {}).get('commission') or
                intelligence_data.get('sales_page', {}).get('commission_rate') or
                intelligence_data.get('market', {}).get('commission_rate') or
                None
            )

        # Mark as public
        product_intelligence.is_public = "true"

        logger.info(f"📋 Extracted metadata: {product_intelligence.product_name} ({product_intelligence.product_category})")
        if product_intelligence.thumbnail_image_url:
            logger.info(f"🖼️  Thumbnail: {product_intelligence.thumbnail_image_url}")

    def _detect_affiliate_network(self, url: str) -> Optional[str]:
        """Detect affiliate network from URL patterns"""
        if not url:
            return None

        url_lower = url.lower()

        # Common affiliate networks
        if 'clickbank' in url_lower or 'hop.clickbank' in url_lower:
            return 'ClickBank'
        elif 'jvzoo' in url_lower or 'jvz' in url_lower:
            return 'JVZoo'
        elif 'warriorplus' in url_lower or 'warriorplus' in url_lower:
            return 'WarriorPlus'
        elif 'shareasale' in url_lower:
            return 'ShareASale'
        elif 'cj.com' in url_lower or 'commission-junction' in url_lower:
            return 'CJ Affiliate'
        elif 'impact.com' in url_lower:
            return 'Impact'
        elif 'awin' in url_lower:
            return 'Awin'
        elif 'rakuten' in url_lower:
            return 'Rakuten'
        elif 'amazon' in url_lower:
            return 'Amazon Associates'

        return None

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

    async def _cleanup_old_images(self, intelligence_data: Dict[str, Any]) -> None:
        """
        Delete old R2 images before recompiling to prevent orphaned files.

        Args:
            intelligence_data: Existing intelligence data with images array

        Returns:
            None
        """
        if not intelligence_data:
            return

        images = intelligence_data.get('images', [])
        if not images:
            logger.info("🗑️  No old images to clean up")
            return

        logger.info(f"🗑️  Cleaning up {len(images)} old images from R2...")

        deleted_count = 0
        failed_count = 0

        for img in images:
            if isinstance(img, dict) and img.get('r2_key'):
                r2_key = img['r2_key']
                try:
                    # Delete from R2 (synchronous operation)
                    success = self.r2_storage.delete_file(r2_key)
                    if success:
                        deleted_count += 1
                    else:
                        failed_count += 1
                        logger.warning(f"⚠️  Failed to delete: {r2_key}")
                except Exception as e:
                    failed_count += 1
                    logger.error(f"❌ Error deleting {r2_key}: {str(e)}")

        if deleted_count > 0:
            logger.info(f"✅ Deleted {deleted_count} old images from R2")
        if failed_count > 0:
            logger.warning(f"⚠️  Failed to delete {failed_count} images")

    async def _ingest_research_to_knowledge_base(
        self,
        product_intelligence_id: int,
        intelligence_data: Dict[str, Any]
    ) -> None:
        """
        Ingest RAG research sources into KnowledgeBase for content generation access.

        Creates individual KnowledgeBase entries for each research source to enable
        precise semantic search and retrieval during content generation.

        Research is owned by the product (not campaign) and shared across all campaigns
        using that product. This prevents duplicate storage and CASCADE DELETE issues.

        Args:
            product_intelligence_id: ProductIntelligence record ID (owner of research)
            intelligence_data: Complete intelligence data including research
        """
        try:
            research_data = intelligence_data.get('research')
            if not research_data:
                return

            all_sources = research_data.get('all_sources', [])
            if not all_sources:
                logger.warning(f"⚠️  No sources found in research data")
                return

            logger.info(f"📚 Ingesting {len(all_sources)} research sources into KnowledgeBase...")

            product_name = intelligence_data.get('product', {}).get('name', 'Product')

            ingested_count = 0
            failed_count = 0

            # Process each source individually for granular semantic search
            for idx, source in enumerate(all_sources, 1):
                try:
                    # Build content for embedding from source data
                    content_parts = []

                    if source.get('title'):
                        content_parts.append(f"Title: {source['title']}")

                    # Web sources use 'content', scholarly use 'abstract', some use 'snippet'
                    if source.get('content'):
                        content_parts.append(f"Content: {source['content']}")
                    elif source.get('abstract'):
                        content_parts.append(f"Abstract: {source['abstract']}")
                    elif source.get('snippet'):
                        content_parts.append(f"Summary: {source['snippet']}")

                    # Add context about the product
                    content_parts.append(f"Product: {product_name}")

                    content = "\n\n".join(content_parts)

                    if not content.strip():
                        logger.warning(f"⚠️  Skipping source {idx} - no content")
                        continue

                    # Generate embedding for this specific source
                    embedding_vector = await self.embeddings.generate_embedding(content)

                    # Store individual source in KnowledgeBase
                    # Research is owned by product and shared across all campaigns
                    kb_entry = KnowledgeBase(
                        product_intelligence_id=product_intelligence_id,
                        campaign_id=None,  # NULL = shared across campaigns, not owned by any specific campaign
                        content=content,
                        embedding=embedding_vector,
                        source_url=source.get('url', ''),
                        meta_data={
                            "product_name": product_name,
                            "source_type": "rag_research_source",
                            "source_index": idx,
                            "source_title": source.get('title', ''),
                            "source_journal": source.get('journal'),
                            "source_pub_date": source.get('pub_date'),
                            "ingested_at": datetime.utcnow().isoformat()
                        }
                    )

                    self.db.add(kb_entry)
                    ingested_count += 1

                    # Flush every 10 entries to avoid memory issues
                    if ingested_count % 10 == 0:
                        await self.db.flush()
                        logger.info(f"   ✓ Ingested {ingested_count}/{len(all_sources)} sources...")

                except Exception as e:
                    failed_count += 1
                    logger.error(f"❌ Failed to ingest source {idx}: {str(e)}")
                    continue

            # Final flush
            await self.db.flush()

            logger.info(f"✅ RAG research ingested into KnowledgeBase:")
            logger.info(f"   - Ingested: {ingested_count} sources")
            if failed_count > 0:
                logger.warning(f"   - Failed: {failed_count} sources")

        except Exception as e:
            logger.error(f"❌ Failed to ingest research to KnowledgeBase: {str(e)}")
            # Don't raise - this is not critical for compilation