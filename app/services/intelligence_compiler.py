"""
Intelligence Compiler - Aggregates and structures intelligence data
Compiles product research, competitor analysis, and market insights
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from app.db.models import Campaign, KnowledgeBase, GeneratedContent
from app.services.crawler import CrawlerService
from app.services.rag import RAGService
import logging
import json

logger = logging.getLogger(__name__)


class IntelligenceCompiler:
    """Compiles and structures intelligence data for campaign generation"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.crawler = CrawlerService()
        self.rag = RAGService(db)
    
    async def compile_product_intelligence(
        self,
        product_url: str,
        user_id: int,
        include_competitors: bool = True
    ) -> Dict[str, Any]:
        """
        Compile comprehensive product intelligence
        
        Args:
            product_url: Product page URL
            user_id: User ID
            include_competitors: Whether to analyze competitors
            
        Returns:
            Compiled intelligence dictionary
        """
        try:
            logger.info(f"Compiling product intelligence for: {product_url}")
            
            # Crawl product page
            product_data = await self.crawler.crawl_url(product_url)
            
            if not product_data.get('success'):
                return {
                    'success': False,
                    'error': 'Failed to crawl product page'
                }
            
            # Extract key product information
            product_info = {
                'url': product_url,
                'title': product_data.get('title', ''),
                'description': product_data.get('description', ''),
                'price': product_data.get('price'),
                'features': product_data.get('features', []),
                'benefits': product_data.get('benefits', []),
                'target_audience': product_data.get('target_audience', ''),
                'pain_points': product_data.get('pain_points', []),
                'quality_score': product_data.get('quality_score', 0),
                'compliance_risks': product_data.get('compliance_risks', [])
            }
            
            # Ingest into knowledge base
            await self.rag.ingest_content(
                user_id=user_id,
                content=json.dumps(product_info, indent=2),
                source_type='product_page',
                source_url=product_url,
                metadata={
                    'title': product_info['title'],
                    'quality_score': product_info['quality_score']
                }
            )
            
            # Compile intelligence report
            intelligence = {
                'success': True,
                'product': product_info,
                'analysis': {
                    'strengths': self._identify_strengths(product_info),
                    'opportunities': self._identify_opportunities(product_info),
                    'marketing_angles': self._generate_marketing_angles(product_info),
                    'content_suggestions': self._generate_content_suggestions(product_info)
                },
                'compiled_at': datetime.utcnow().isoformat()
            }
            
            # Add competitor analysis if requested
            if include_competitors:
                competitor_data = await self._analyze_competitors(product_info)
                intelligence['competitors'] = competitor_data
            
            return intelligence
            
        except Exception as e:
            logger.error(f"Error compiling product intelligence: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def compile_campaign_intelligence(
        self,
        campaign_id: int
    ) -> Dict[str, Any]:
        """
        Compile intelligence for an existing campaign
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            Compiled campaign intelligence
        """
        try:
            # Get campaign
            stmt = select(Campaign).where(Campaign.id == campaign_id)
            result = await self.db.execute(stmt)
            campaign = result.scalar_one_or_none()
            
            if not campaign:
                return {
                    'success': False,
                    'error': 'Campaign not found'
                }
            
            # Get related knowledge base entries
            kb_stmt = select(KnowledgeBase).where(
                KnowledgeBase.user_id == campaign.user_id
            ).order_by(desc(KnowledgeBase.created_at)).limit(10)
            
            kb_result = await self.db.execute(kb_stmt)
            kb_entries = kb_result.scalars().all()
            
            # Get generated content for this campaign
            content_stmt = select(GeneratedContent).where(
                GeneratedContent.campaign_id == campaign_id
            ).order_by(desc(GeneratedContent.created_at))
            
            content_result = await self.db.execute(content_stmt)
            generated_content = content_result.scalars().all()
            
            # Compile intelligence
            intelligence = {
                'success': True,
                'campaign': {
                    'id': campaign.id,
                    'name': campaign.name,
                    'product_url': campaign.product_url,
                    'affiliate_network': campaign.affiliate_network,
                    'status': campaign.status,
                    'created_at': campaign.created_at.isoformat()
                },
                'knowledge_base': [
                    {
                        'id': kb.id,
                        'source_type': kb.source_type,
                        'source_url': kb.source_url,
                        'metadata': kb.metadata,
                        'created_at': kb.created_at.isoformat()
                    }
                    for kb in kb_entries
                ],
                'generated_content': [
                    {
                        'id': content.id,
                        'content_type': content.content_type,
                        'status': content.status,
                        'performance_score': content.performance_score,
                        'created_at': content.created_at.isoformat()
                    }
                    for content in generated_content
                ],
                'performance_summary': self._calculate_performance_summary(generated_content),
                'compiled_at': datetime.utcnow().isoformat()
            }
            
            return intelligence
            
        except Exception as e:
            logger.error(f"Error compiling campaign intelligence: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def compile_market_intelligence(
        self,
        niche: str,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Compile market intelligence for a specific niche
        
        Args:
            niche: Market niche
            user_id: User ID
            
        Returns:
            Market intelligence report
        """
        try:
            # Retrieve relevant knowledge from user's knowledge base
            context = await self.rag.retrieve_context(
                query=f"market trends and insights for {niche}",
                user_id=user_id,
                top_k=10
            )
            
            # Compile market intelligence
            intelligence = {
                'success': True,
                'niche': niche,
                'insights': [
                    {
                        'source': entry['source_type'],
                        'content': entry['content'][:500],  # Truncate for summary
                        'relevance': entry['similarity']
                    }
                    for entry in context
                ],
                'trends': self._extract_trends(context),
                'opportunities': self._extract_opportunities(context),
                'compiled_at': datetime.utcnow().isoformat()
            }
            
            return intelligence
            
        except Exception as e:
            logger.error(f"Error compiling market intelligence: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _identify_strengths(self, product_info: Dict[str, Any]) -> List[str]:
        """Identify product strengths from product information"""
        strengths = []
        
        if product_info.get('quality_score', 0) > 7:
            strengths.append("High-quality product with strong market positioning")
        
        if len(product_info.get('features', [])) > 5:
            strengths.append("Feature-rich product with multiple value propositions")
        
        if len(product_info.get('benefits', [])) > 3:
            strengths.append("Clear benefit articulation for target audience")
        
        if not product_info.get('compliance_risks'):
            strengths.append("Clean compliance profile with minimal regulatory risks")
        
        return strengths
    
    def _identify_opportunities(self, product_info: Dict[str, Any]) -> List[str]:
        """Identify marketing opportunities"""
        opportunities = []
        
        pain_points = product_info.get('pain_points', [])
        if pain_points:
            opportunities.append(f"Address {len(pain_points)} key pain points in marketing copy")
        
        target_audience = product_info.get('target_audience', '')
        if target_audience:
            opportunities.append(f"Targeted messaging for {target_audience}")
        
        features = product_info.get('features', [])
        if features:
            opportunities.append("Create feature-focused content for different audience segments")
        
        return opportunities
    
    def _generate_marketing_angles(self, product_info: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate potential marketing angles"""
        angles = []
        
        # Pain point angle
        if product_info.get('pain_points'):
            angles.append({
                'angle': 'Problem-Solution',
                'description': 'Focus on pain points and how the product solves them',
                'priority': 'high'
            })
        
        # Benefit angle
        if product_info.get('benefits'):
            angles.append({
                'angle': 'Benefit-Driven',
                'description': 'Highlight key benefits and transformations',
                'priority': 'high'
            })
        
        # Feature angle
        if product_info.get('features'):
            angles.append({
                'angle': 'Feature-Rich',
                'description': 'Showcase unique features and capabilities',
                'priority': 'medium'
            })
        
        # Social proof angle
        angles.append({
            'angle': 'Social Proof',
            'description': 'Leverage testimonials and success stories',
            'priority': 'medium'
        })
        
        return angles
    
    def _generate_content_suggestions(self, product_info: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate content creation suggestions"""
        suggestions = []
        
        suggestions.append({
            'type': 'review_article',
            'title': f"In-Depth Review: {product_info.get('title', 'Product')}",
            'description': 'Comprehensive review covering features, benefits, and real-world use cases'
        })
        
        suggestions.append({
            'type': 'comparison',
            'title': f"{product_info.get('title', 'Product')} vs Alternatives",
            'description': 'Side-by-side comparison with competitor products'
        })
        
        suggestions.append({
            'type': 'tutorial',
            'title': f"How to Get Started with {product_info.get('title', 'Product')}",
            'description': 'Step-by-step guide for new users'
        })
        
        return suggestions
    
    async def _analyze_competitors(self, product_info: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze competitor products (placeholder for future implementation)"""
        # This would integrate with competitor analysis tools
        return {
            'analyzed': False,
            'note': 'Competitor analysis requires additional data sources'
        }
    
    def _extract_trends(self, context: List[Dict[str, Any]]) -> List[str]:
        """Extract market trends from context"""
        # Simplified trend extraction
        trends = [
            "Growing demand for digital products",
            "Increased focus on value-driven marketing",
            "Shift towards authentic, transparent promotion"
        ]
        return trends
    
    def _extract_opportunities(self, context: List[Dict[str, Any]]) -> List[str]:
        """Extract market opportunities from context"""
        opportunities = [
            "Underserved audience segments",
            "Content gaps in current market",
            "Emerging promotional channels"
        ]
        return opportunities
    
    def _calculate_performance_summary(self, generated_content: List[GeneratedContent]) -> Dict[str, Any]:
        """Calculate performance summary for generated content"""
        if not generated_content:
            return {
                'total_content': 0,
                'avg_performance_score': 0,
                'status_breakdown': {}
            }
        
        total = len(generated_content)
        scores = [c.performance_score for c in generated_content if c.performance_score]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        status_breakdown = {}
        for content in generated_content:
            status = content.status
            status_breakdown[status] = status_breakdown.get(status, 0) + 1
        
        return {
            'total_content': total,
            'avg_performance_score': round(avg_score, 2),
            'status_breakdown': status_breakdown
        }