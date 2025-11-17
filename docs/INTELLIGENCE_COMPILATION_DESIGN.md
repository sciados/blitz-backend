# Intelligence Compilation System - Design Document

## Overview

Blitz's intelligence compilation is a **simplified, powerful 3-step process** that improves on CampaignForge's over-engineered 6-module amplifier system. We use the **best AI platforms** for each task.

## Key Improvements Over CampaignForge

### What We're Keeping

✅ Sales page scraping with image extraction
✅ Cloudflare R2 for image storage
✅ RAG (Retrieval Augmented Generation)
✅ Semantic search capabilities

### What We're Improving

🚀 **Unified AI Analysis** - Single Claude 3.5 Sonnet call instead of 6 separate enhancers
🚀 **Better Embeddings** - OpenAI text-embedding-3-large instead of Cohere
🚀 **Simplified Storage** - JSONB in campaigns table instead of 6 normalized tables
🚀 **Faster Processing** - Parallel operations, no artificial throttling
🚀 **Better Image Classification** - Modern computer vision with Claude Vision API

## Architecture

### The 3-Step Process

Step 1: Scrape Sales Page
    ├─ Extract HTML content, metadata, text
    ├─ Download images (hero, product, lifestyle)
    ├─ Classify images using Claude Vision API
    ├─ Upload to Cloudflare R2
    └─ Store scraped data in database

Step 2: Intelligence Amplification
    ├─ Send scraped content to Claude 3.5 Sonnet
    ├─ Extract comprehensive intelligence:
    │   ├─ Product features & benefits
    │   ├─ Pain points & solutions
    │   ├─ Target audience & demographics
    │   ├─ Pricing strategy & positioning
    │   ├─ Marketing angles & hooks
    │   ├─ Testimonials & social proof
    │   ├─ Guarantees & risk reversal
    │   ├─ Competitive advantages
    │   ├─ Objections & how they're handled
    │   └─ Call-to-action strategy
    └─ Store in campaign.intelligence_data JSONB

Step 3: RAG Implementation
    ├─ Generate embeddings with OpenAI text-embedding-3-large
    ├─ Store vectors in pgvector (PostgreSQL extension)
    ├─ Enable semantic search across campaigns
    ├─ Link related intelligence and research
    └─ Support intelligent content generation

## Technology Stack

### AI Platforms (Best-in-Class)

Primary Analysis: Claude 3.5 Sonnet (Anthropic)

- Why: Best reasoning, context understanding, and structured output
- Use: Main intelligence extraction and amplification
- Cost: ~$3/million input tokens, $15/million output tokens
- Context: 200K tokens (can handle full sales pages)

Image Analysis: Claude Vision API

- Why: Superior image understanding compared to GPT-4V
- Use: Image classification, quality scoring, context extraction
- Replaces: Manual dimension checking and basic filters

Embeddings: OpenAI text-embedding-3-large

- Why: Best semantic understanding, 3072 dimensions
- Use: RAG system, semantic search
- Cost: $0.13/million tokens
- Performance: Better than Cohere on retrieval benchmarks

Alternative Embeddings: Voyage AI (voyage-large-2-instruct)

- Why: Optimized for RAG, beats OpenAI on some benchmarks
- Use: Optional upgrade path
- Cost: Similar to OpenAI

### Storage & Database

Image Storage: Cloudflare R2

- S3-compatible object storage
- Zero egress fees (huge cost savings)
- Global CDN included
- Path structure: `campaigns/{campaign_id}/images/{filename}`

Vector Storage: pgvector (PostgreSQL)

- Native PostgreSQL extension
- HNSW indexing for fast similarity search
- No separate vector database needed
- Stores embeddings directly in campaigns table

Intelligence Storage: JSONB

- All intelligence in `campaigns.intelligence_data`
- Flexible schema, no migrations needed
- Fast queries with GIN indexes
- Single source of truth

## Global Intelligence Sharing (Cost Optimization)

### The Problem

Multiple users often promote the same products (especially on platforms like ClickBank, JVZoo). Without sharing, each user would trigger expensive intelligence compilation for the same URL.

### The Solution

**Global Intelligence Cache**: Compile intelligence once per unique product URL, share across all users.

**Benefits**:

- ⚡ **Instant Intelligence**: 2nd+ users get results in <1 second (no scraping/analysis)
- 💰 **95%+ Cost Savings**: Only first user pays compilation cost (~$0.06)
- 🚀 **Better UX**: No waiting for common affiliate products
- 📊 **Data Quality**: More campaigns using same intelligence = better data

### How It Works

User A creates campaign for ClickBank Product X
    ↓
System checks: Has this URL been compiled?
    ↓ (No - First time)
[Full 3-Step Compilation] → Store in ProductIntelligence table
    ↓
Link Campaign A → ProductIntelligence record
    ↓
Intelligence available to Campaign A

User B creates campaign for same Product X (hours later)
    ↓
System checks: Has this URL been compiled?
    ↓ (Yes! Found existing)
Skip compilation entirely
    ↓
Link Campaign B → Same ProductIntelligence record
    ↓
Intelligence instantly available to Campaign B

## Database Schema

### New: ProductIntelligence Table (Global Shared Intelligence)

```python
class ProductIntelligence(Base):
    """
    Shared intelligence for unique product URLs.
    Multiple campaigns can reference the same intelligence.
    """
    __tablename__ = "product_intelligence"

    id = Column(Integer, primary_key=True)

    # URL identification
    product_url = Column(String, unique=True, index=True, nullable=False)
    url_hash = Column(String(64), unique=True, index=True)  # SHA-256 for fast lookup

    # Intelligence data (same structure as before)
    intelligence_data = Column(JSONB, nullable=True)
    # Same JSONB structure: sales_page, images, product, market, marketing, analysis

    # RAG embedding
    intelligence_embedding = Column(Vector(3072), nullable=True)

    # Metadata
    compiled_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    compilation_version = Column(String(20), default="1.0")  # For future schema changes

    # Usage tracking
    reference_count = Column(Integer, default=0)  # How many campaigns use this
    last_accessed_at = Column(DateTime)

    # Relationships
    campaigns = relationship("Campaign", back_populates="product_intelligence")

    # Indexes
    __table_args__ = (
        Index('idx_url_hash', url_hash),
        Index('idx_product_url', product_url),
        Index('idx_intelligence_embedding',
              intelligence_embedding,
              postgresql_using='hnsw',
              postgresql_with={'m': 16, 'ef_construction': 64}),
        Index('idx_compiled_at', compiled_at),
    )
```

### Updated Campaign Model

```python
class Campaign(Base):
    # ... existing fields (name, product_url, affiliate_network, etc.) ...

    # Link to shared intelligence
    product_intelligence_id = Column(Integer, ForeignKey('product_intelligence.id'), nullable=True)
    product_intelligence = relationship("ProductIntelligence", back_populates="campaigns")

    # Note: intelligence_data and embeddings are now in ProductIntelligence table
    # This allows multiple campaigns to share the same intelligence
```

## API Endpoints

### Intelligence Compilation (with Global Sharing)

POST /api/campaigns/{campaign_id}/compile-intelligence
Request:
{
  "deep_scrape": true,          // Extract all content vs. basic
  "scrape_images": true,         // Download and analyze images
  "max_images": 10,              // Limit image downloads
  "enable_rag": true,            // Generate embeddings for RAG
  "force_recompile": false       // Force re-scrape even if exists
}

Response (New Intelligence):
{
  "campaign_id": 1,
  "status": "completed",
  "was_cached": false,           // NEW: Indicates first compilation
  "product_intelligence_id": 42,
  "intelligence_summary": {
    "product_name": "...",
    "category": "...",
    "confidence_score": 0.95,
    "images_found": 8,
    "total_content_length": 12500
  },
  "processing_time_ms": 15000,
  "costs": {
    "scraping": 0,
    "analysis": 0.05,
    "embeddings": 0.002,
    "total": 0.052
  }
}

Response (Cached Intelligence):
{
  "campaign_id": 2,
  "status": "completed",
  "was_cached": true,            // NEW: Found existing intelligence
  "product_intelligence_id": 42, // Same ID as first campaign
  "intelligence_summary": {
    "product_name": "...",       // Same data
    "category": "...",
    "confidence_score": 0.95,
    "images_found": 8,
    "total_content_length": 12500
  },
  "processing_time_ms": 250,     // 60x faster!
  "costs": {
    "scraping": 0,
    "analysis": 0,               // $0 - Used cached
    "embeddings": 0,             // $0 - Used cached
    "total": 0                   // Free!
  },
  "cache_info": {
    "originally_compiled_at": "2025-01-30T10:00:00Z",
    "originally_compiled_by": "User A",
    "times_reused": 5
  }
}

Progress tracking via WebSocket or polling:
GET /api/campaigns/{campaign_id}/compile-progress
{
  "status": "in_progress",
  "stage": "scraping",          // scraping, amplifying, embedding
  "progress": 35,                // 0-100
  "message": "Downloading images...",
  "estimated_completion": "2025-01-30T12:05:00Z"
}

### RAG Query

POST /api/intelligence/query
Request:
{
  "query": "What products target weight loss for women over 40?",
  "campaign_ids": [1, 2, 3],    // Optional: filter to specific campaigns
  "limit": 5,                    // Top-k results
  "similarity_threshold": 0.7    // Minimum cosine similarity
}

Response:
{
  "results": [
    {
      "campaign_id": 1,
      "campaign_name": "Weight Loss Campaign",
      "similarity_score": 0.92,
      "matched_content": "Excerpt from intelligence...",
      "intelligence_summary": {
        "product_name": "...",
        "target_audience": "...",
        "key_benefits": ["..."]
      }
    }
  ],
  "query_time_ms": 45

## Implementation Details

### Intelligence Sharing Logic

**Backend: `app/services/intelligence_compiler.py`**

```python
class IntelligenceCompiler:
    async def compile_for_campaign(campaign_id: int, options: dict):
        """
        Main entry point that handles intelligence sharing.
        """
        # 1. Get campaign
        campaign = await db.get(Campaign, campaign_id)

        # 2. Generate URL hash for lookup
        url_hash = hashlib.sha256(campaign.product_url.encode()).hexdigest()

        # 3. Check if intelligence already exists
        existing = await db.execute(
            select(ProductIntelligence)
            .where(ProductIntelligence.url_hash == url_hash)
        )
        intelligence = existing.scalar_one_or_none()

        if intelligence and not options.get('force_recompile'):
            # CACHE HIT: Reuse existing intelligence
            await self._link_campaign_to_intelligence(campaign, intelligence)
            return {
                'was_cached': True,
                'product_intelligence_id': intelligence.id,
                'processing_time_ms': 250,
                'costs': {'total': 0}
            }

        # CACHE MISS: Compile new intelligence
        intelligence = await self._compile_new_intelligence(
            campaign.product_url,
            url_hash,
            options
        )

        await self._link_campaign_to_intelligence(campaign, intelligence)

        return {
            'was_cached': False,
            'product_intelligence_id': intelligence.id,
            'processing_time_ms': 15000,
            'costs': {'total': 0.052}
        }

    async def _link_campaign_to_intelligence(campaign, intelligence):
        """
        Links campaign to shared intelligence.
        """
        campaign.product_intelligence_id = intelligence.id
        intelligence.reference_count += 1
        intelligence.last_accessed_at = datetime.utcnow()
        await db.commit()

    async def _compile_new_intelligence(url, url_hash, options):
        """
        Performs full 3-step compilation for new intelligence.
        """
        # Step 1: Scrape
        scraped = await sales_page_scraper.scrape_sales_page(url, options)

        # Step 2: Amplify
        amplified = await intelligence_amplifier.amplify_intelligence(scraped)

        # Step 3: RAG
        embedding = await rag_service.generate_embeddings(amplified)

        # Store in ProductIntelligence table
        intelligence = ProductIntelligence(
            product_url=url,
            url_hash=url_hash,
            intelligence_data=amplified,
            intelligence_embedding=embedding,
            reference_count=0
        )
        db.add(intelligence)
        await db.commit()

        return intelligence
```

### Step 1: Sales Page Scraping

**Backend: `app/services/scraper_service.py`**

```python
class SalesPageScraper:
    async def scrape_sales_page(url: str, campaign_id: int, max_images: int = 10):
        """
        Scrapes sales page and extracts all relevant data.
        """
        # 1. Fetch HTML
        html = await self._fetch_html(url)

        # 2. Extract metadata
        metadata = self._extract_metadata(html)

        # 3. Extract text content
        text_content = self._extract_text(html)

        # 4. Extract images
        images = await self._extract_images(html, campaign_id, max_images)

        # 5. Classify images with Claude Vision
        for img in images:
            img['analysis'] = await self._analyze_image_with_claude(img['url'])

        return {
            'metadata': metadata,
            'text_content': text_content,
            'images': images,
            'scraped_at': datetime.utcnow()
        }

    async def _analyze_image_with_claude(self, image_url: str):
        """
        Uses Claude Vision API to understand image context.
        """
        response = await anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "url", "url": image_url}
                    },
                    {
                        "type": "text",
                        "text": """Analyze this marketing image:
                        1. Type: hero, product, lifestyle, testimonial, comparison, diagram
                        2. Primary subject and context
                        3. Marketing purpose
                        4. Quality score (0-100) for marketing use
                        5. Emotional appeal and messaging
                        Return JSON."""
                    }
                ]
            }]
        )
        return json.loads(response.content[0].text)
```

### Step 2: Intelligence Amplification

**Backend: `app/services/intelligence_service.py`**

```python
class IntelligenceAmplifier:
    async def amplify_intelligence(scraped_data: dict):
        """
        Single comprehensive analysis with Claude 3.5 Sonnet.
        Replaces CampaignForge's 6 separate enhancers.
        """
        prompt = f"""
You are an expert marketing intelligence analyst. Analyze this sales page and extract comprehensive intelligence.

SALES PAGE CONTENT:
{scraped_data['text_content']}

METADATA:
- Title: {scraped_data['metadata']['title']}
- URL: {scraped_data['metadata']['url']}

EXTRACT THE FOLLOWING (return as structured JSON):

1. PRODUCT INTELLIGENCE:
   - Product name
   - Core features (5-10 key features)
   - Primary benefits (what customer gets)
   - Pain points addressed
   - Solutions provided
   - Ingredients/components (if applicable)
   - Technical specifications

2. MARKET INTELLIGENCE:
   - Market category
   - Market positioning (budget/mid/premium)
   - Target audience (demographics, psychographics)
   - Competitive advantages (unique selling points)
   - Pricing strategy
   - Price points mentioned

3. MARKETING INTELLIGENCE:
   - Marketing hooks (attention-grabbing phrases)
   - Marketing angles used (transformation, authority, scarcity, etc.)
   - Testimonials and social proof
   - Guarantees and risk reversals
   - Urgency/scarcity tactics
   - Call-to-action strategy
   - Objections handled

4. ANALYSIS:
   - Confidence score (0-1) based on content quality
   - Completeness score (0-1) - how much info is available
   - Missing elements that would improve the sales page
   - Recommendations for affiliate marketers promoting this

Return ONLY valid JSON, no markdown formatting.
"""

        response = await anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )

        intelligence = json.loads(response.content[0].text)
        return intelligence
```

### Step 3: RAG Implementation

**Backend: `app/services/rag_service.py`**

```python
class RAGService:
    async def generate_embeddings(intelligence_data: dict):
        """
        Generates embeddings using OpenAI text-embedding-3-large.
        """
        # Combine relevant intelligence into searchable text
        searchable_text = self._prepare_text_for_embedding(intelligence_data)

        response = await openai_client.embeddings.create(
            model="text-embedding-3-large",
            input=searchable_text,
            dimensions=3072
        )

        embedding = response.data[0].embedding
        return embedding

    def _prepare_text_for_embedding(self, intelligence: dict):
        """
        Creates optimized text representation for embeddings.
        """
        parts = [
            f"Product: {intelligence['product']['name']}",
            f"Category: {intelligence['market']['category']}",
            f"Features: {', '.join(intelligence['product']['features'])}",
            f"Benefits: {', '.join(intelligence['product']['benefits'])}",
            f"Target: {intelligence['market']['target_audience']['primary']}",
            f"Pain points: {', '.join(intelligence['product']['pain_points'])}",
            f"Positioning: {intelligence['market']['positioning']}"
        ]
        return " | ".join(parts)

    async def semantic_search(query: str, limit: int = 5, threshold: float = 0.7):
        """
        Performs semantic search across all campaigns using pgvector.
        """
        # Generate query embedding
        query_embedding = await self._embed_query(query)

        # Vector similarity search with pgvector
        results = await db.execute(
            select(Campaign)
            .where(Campaign.intelligence_embedding.isnot(None))
            .order_by(
                Campaign.intelligence_embedding.cosine_distance(query_embedding)
            )
            .limit(limit)
        )

        campaigns = results.scalars().all()

        # Filter by threshold and return with scores
        filtered = []
        for campaign in campaigns:
            score = 1 - cosine_distance(campaign.intelligence_embedding, query_embedding)
            if score >= threshold:
                filtered.append({
                    'campaign': campaign,
                    'similarity_score': score
                })

        return filtered
```

## Frontend Implementation

### Intelligence Compilation UI

**Location: `src/app/campaigns/[id]/page.tsx`**

The "Compile Intelligence" button in Step 2 will:

1. **Show Modal** with options:
   - Deep scrape toggle
   - Image scraping toggle
   - Max images slider
   - Enable RAG toggle

2. **Start Compilation** with progress tracking:
tsx
   const [progress, setProgress] = useState({
     status: 'idle',
     stage: '',
     progress: 0,
     message: ''
   });

   const compileIntelligence = async () => {
     const response = await api.post(
       `/api/campaigns/${id}/compile-intelligence`,
       { deep_scrape: true, scrape_images: true, max_images: 10 }
     );

     // Poll for progress
     const interval = setInterval(async () => {
       const prog = await api.get(`/api/campaigns/${id}/compile-progress`);
       setProgress(prog.data);

if (prog.data.status === 'completed') {
         clearInterval(interval);
         toast.success('Intelligence compiled successfully!');
         queryClient.invalidateQueries(['campaign', id]);
       }
     }, 1000);
   };

Display Results** in expanded intelligence section showing

- Product summary
- Target audience
- Key features
- Marketing angles
- Extracted images
- Confidence scores

## Performance Optimizations

### Parallel Processing

- Image downloads happen concurrently (Promise.all)
- Claude Vision analysis in parallel for multiple images
- No artificial throttling (CampaignForge had 3s delays)

### Caching Strategy

- Cache scraped HTML for 24 hours (avoid re-scraping same URL)
- Reuse embeddings if intelligence hasn't changed
- CDN caching for R2 images

### Cost Optimization

- Batch embedding generation where possible
- Use Claude's caching for repeated analysis
- Smart image selection (top 10 by quality score)

## Error Handling

### Graceful Degradation

- If image scraping fails → continue with text analysis
- If Claude Vision fails → use basic image metadata
- If embeddings fail → intelligence still saved, RAG disabled

### Retry Logic

- 3 retries for HTTP failures with exponential backoff
- Circuit breaker for external services
- Fallback to cached data when available

## Testing Strategy

### Unit Tests

- Scraper service with mocked HTML
- Intelligence amplifier with sample responses
- RAG service with test embeddings

### Integration Tests

- Full pipeline with test sales pages
- R2 upload/download verification
- Database storage and retrieval

### End-to-End Tests

- Real sales page compilation
- Frontend to backend flow
- Progress tracking accuracy

## Future Enhancements

### Phase 2 Features

- **Competitor Analysis**: Compare multiple products side-by-side
- **Trend Detection**: Identify emerging marketing patterns
- **Auto-Updates**: Re-scrape on schedule to detect changes
- **Intelligence Sharing**: Share intelligence between users (affiliate optimization)
- **Custom Research**: Add manual research notes and documents
- **Multi-language**: Analyze sales pages in different languages

### Advanced RAG

- **Hybrid Search**: Combine semantic + keyword search
- **Re-ranking**: Use Cohere rerank API for better relevance
- **Query Expansion**: Generate multiple search queries from user intent
- **Contextual Retrieval**: Include surrounding context in results

## Cost Analysis

## Per Campaign Compilation

Step 1: Scraping

- HTTP requests: Free
- Image downloads: ~$0.01 per 10 images

Step 2: Intelligence Amplification

- Claude 3.5 Sonnet: ~$0.05 per campaign (5K input, 2K output)

Step 3: RAG

- OpenAI embeddings: ~$0.002 per campaign
- Storage: Negligible (JSONB + vector)

Total: ~$0.06 per campaign

Compare to CampaignForge:

- 6 separate API calls to different providers
- Higher token usage due to redundant prompting
- Estimated: ~$0.15-0.20 per campaign

Savings: 60-70% cost reduction

## Deployment Checklist

### Backend (Railway)

- [ ] Install pgvector extension
- [ ] Add Anthropic API key
- [ ] Add OpenAI API key
- [ ] Configure Cloudflare R2 credentials
- [ ] Update Campaign model with new fields
- [ ] Create migration for intelligence_embedding column
- [ ] Deploy scraper, intelligence, and RAG services
- [ ] Test all endpoints

### Frontend (Vercel)

- [ ] Add intelligence compilation modal
- [ ] Add progress tracking UI
- [ ] Add intelligence display section
- [ ] Update campaign workflow step 2
- [ ] Test end-to-end flow

### Infrastructure

- [ ] Set up Cloudflare R2 bucket
- [ ] Configure CORS for R2
- [ ] Set up CDN for R2 public access
- [ ] Configure rate limiting for scraping
- [ ] Set up monitoring for API usage

---

**Status**: Ready for Implementation
**Priority**: High (Core Feature)
**Estimated Time**: 2-3 development sessions
