# Blitz RAG System - Hybrid Intelligence Research

## Overview

Blitz uses a **Hybrid RAG (Retrieval Augmented Generation)** system that combines FREE scholarly APIs with affordable web search to generate comprehensive, research-backed intelligence for ebook/report generation.

## Architecture

### 3-Tier Research System

```
┌─────────────────────────────────────────────────┐
│           Intelligence Compiler                 │
│                                                 │
│  1. Scrape Sales Page                           │
│  2. Extract Product Info (name, ingredients)    │
│  3. ⭐ RAG Research (NEW!)                      │
│  4. AI Analysis (with research data)            │
│  5. Generate Embeddings                         │
└─────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│        Intelligent RAG Orchestrator              │
│                                                 │
│  Routes queries to optimal sources:             │
│  • Health products → PubMed (FREE)              │
│  • Scientific claims → Semantic Scholar (FREE)  │
│  • Market data → Tavily ($0.001/search)         │
│  • Caching for repeated ingredients             │
└─────────────────────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        ▼                           ▼
┌──────────────────┐      ┌──────────────────┐
│  FREE APIs       │      │  PAID APIs       │
│                  │      │                  │
│  • PubMed/NIH    │      │  • Tavily        │
│  • Semantic      │      │    $0.001/search │
│    Scholar       │      │                  │
│  • ArXiv         │      │                  │
│                  │      │                  │
│  Unlimited!      │      │  Very Cheap      │
└──────────────────┘      └──────────────────┘
```

## Search Volume & Costs

### Typical Product Intelligence

**Health Product (e.g., Weight Loss Supplement):**
- Ingredient research: 24 searches (6 ingredients × 4 searches)
  - Clinical studies (FREE via PubMed)
  - Proven benefits (FREE via Semantic Scholar)
  - Safety profile (FREE)
  - Dosage/effectiveness (FREE)
- Market research: 10 searches
  - Reviews ($0.001 via Tavily)
  - Pricing ($0.001)
  - Competitors ($0.001)
  - Market trends ($0.001)

**Total:** ~34 searches
**Cost:** $0.01 (70% free, 30% paid)

**Make Money Product:**
- 80% web research (testimonials, earnings, strategies)
- 20% scholarly (business research)
- **Total:** ~35 searches
- **Cost:** $0.03

**Self-Help/Education:**
- 40% scholarly (psychology, behavioral science)
- 60% web (reviews, success stories)
- **Total:** ~35 searches
- **Cost:** $0.02

### Average Cost Per Campaign: **$0.02**

## Intelligence Levels

Users can choose research depth:

```python
intelligence_levels = {
    "basic": {
        "scholarly": 6 searches,
        "web": 4 searches,
        "total_cost": "$0.005",
        "use_case": "Quick overview"
    },
    "standard": {
        "scholarly": 12 searches,
        "web": 8 searches,
        "total_cost": "$0.015",
        "use_case": "Good quality (default)"
    },
    "comprehensive": {
        "scholarly": 24 searches,
        "web": 11 searches,
        "total_cost": "$0.025",
        "use_case": "Ebook-ready"
    }
}
```

## Caching Strategy

### Ingredient Caching
Dramatically reduces costs for repeated ingredients:

```
First campaign with Fucoxanthin:
  - 4 searches → $0.004 (if web) or $0 (if scholarly)
  - Results cached for 24 hours

Second campaign with Fucoxanthin:
  - 0 searches → $0.00
  - Retrieved from cache

Savings: 100% for repeated ingredients
```

After 100 campaigns, cache hit rate: ~70%
**Cost reduction: 70% less than initial**

## API Configuration

### Required (FREE)
```bash
# No API keys needed for scholarly search!
# PubMed and Semantic Scholar are free government/academic resources
```

### Optional (Paid)
```bash
# Railway Environment Variables
TAVILY_API_KEY=tvly-xxxxx  # $1 per 1,000 searches
```

Get Tavily API key:
1. Go to https://tavily.com
2. Sign up (free tier: 1,000 searches/month)
3. Copy API key
4. Add to Railway: `TAVILY_API_KEY`

## Usage

### Basic Example

```python
from app.services.intelligence_amplifier import IntelligenceAmplifier

amplifier = IntelligenceAmplifier()

# Standard intelligence with RAG (default)
intelligence = await amplifier.amplify_intelligence(
    scraped_data=sales_page_data,
    enable_rag=True,
    intelligence_level="standard"  # 20 searches, $0.015
)

# Comprehensive (for ebook generation)
intelligence = await amplifier.amplify_intelligence(
    scraped_data=sales_page_data,
    enable_rag=True,
    intelligence_level="comprehensive"  # 35 searches, $0.025
)

# Quick/budget mode
intelligence = await amplifier.amplify_intelligence(
    scraped_data=sales_page_data,
    enable_rag=True,
    intelligence_level="basic"  # 10 searches, $0.005
)

# Disable RAG (use only scraped page data)
intelligence = await amplifier.amplify_intelligence(
    scraped_data=sales_page_data,
    enable_rag=False  # $0.00
)
```

## Data Generated

### Without RAG (Current Baseline)
- **Sources:** 1 (sales page only)
- **Data size:** ~2,000-4,000 characters
- **Quality:** Limited to what's on the page

### With RAG (NEW!)
- **Sources:** 30-35 (sales page + research)
- **Data size:** ~5,000-10,000 characters
- **Quality:** Research-backed with citations

### Example Output Structure

```json
{
  "product": {
    "name": "Mitolyn",
    "ingredients": ["Fucoxanthin", "Green Tea Extract", ...],
    "features": [...],
    "benefits": [...]
  },
  "research": {
    "ingredient_research": {
      "Fucoxanthin": [
        {
          "source": "pubmed",
          "title": "Fucoxanthin induces UCP1 expression in white adipose tissue",
          "journal": "Journal of Obesity",
          "findings": "5kg weight loss over 16 weeks",
          "participants": "151 obese women"
        }
      ]
    },
    "market_research": [
      {
        "source": "tavily",
        "title": "Mitolyn Customer Reviews 2024",
        "rating": "4.3/5",
        "content": "Users report average 12lb weight loss..."
      }
    ],
    "total_sources": 34,
    "research_cost_usd": 0.018
  }
}
```

## Cost Optimization Features

### 1. Smart Caching
- Ingredient research cached 24 hours
- 70% cache hit rate after 100 campaigns
- **Savings: ~70% reduction**

### 2. Intelligent Routing
- Health queries → FREE PubMed first
- Scientific queries → FREE Semantic Scholar
- Market queries → Cheap Tavily ($0.001)
- **Savings: 70% of searches are FREE**

### 3. Adaptive Depth
- Basic: 10 searches ($0.005)
- Standard: 20 searches ($0.015)
- Comprehensive: 35 searches ($0.025)
- **Savings: Users only pay for what they need**

## Total Cost Per Campaign

```
Complete Intelligence Compilation:
├── Scraping: $0.000
├── RAG Research: $0.020 (avg)
├── AI Analysis: $0.001 (DeepSeek)
├── Embeddings: $0.001 (OpenAI)
└── Total: $0.022 per campaign

At scale:
├── 100 campaigns: $2.20
├── 1,000 campaigns: $22.00
└── 10,000 campaigns: $220.00
```

Still **extremely affordable** with comprehensive research!

## Benefits for Ebook Generation

### Before RAG
❌ Limited to sales page claims
❌ No scientific backing
❌ Generic feature descriptions
❌ No competitive intelligence

### After RAG
✅ Clinical studies and research papers
✅ Peer-reviewed evidence
✅ Market data and pricing analysis
✅ Customer reviews and sentiment
✅ Competitor comparisons
✅ 5,000-10,000 character intelligence
✅ Ready for AI to generate comprehensive ebooks

## Monitoring

Check Railway logs to see RAG in action:

```
🧠 Amplifying intelligence with AI Router + RAG...
📝 Extracted basic info: Mitolyn
🔍 Starting RAG research (level: standard)...
🧪 Researching 6 ingredients (max 4 each)
🔬 PubMed search: 'Fucoxanthin clinical studies benefits'
📚 PubMed: Found 5 articles
✅ Ingredient research: 12 sources, 6 searches
🎯 Researching 3 features
✅ Feature research: 6 sources, 3 searches
📊 Market research for Mitolyn
🌐 Tavily search: 'Mitolyn customer reviews ratings'
📚 Tavily: Found 2 results
✅ Market research: 8 sources, 4 searches
✅ RAG complete: 26 sources, $0.018 cost
💾 Cache stats: 2 hits, 13 misses (13.3% hit rate)
```

## Future Enhancements

Potential additions:
- **Perplexity API** for premium tier (with citations)
- **Google Scholar** scraping for more academic papers
- **Patent databases** for unique mechanism research
- **Reddit/social sentiment** analysis
- **Competitive pricing** tracking

## Comparison: Blitz vs CampaignForge

| Feature | CampaignForge | Blitz |
|---------|---------------|-------|
| **Approach** | 6 separate AI enhancers | 1 unified RAG system |
| **Research** | AI-generated only | Real research + AI |
| **Sources** | 0 (synthetic) | 30-35 (real) |
| **Data size** | 5K-10K chars | 5K-10K chars (research-backed) |
| **Cost** | Higher (6 AI calls) | Lower (1 AI call + cheap research) |
| **Quality** | AI assumptions | Evidence-based |
| **Ebook-ready** | Generic | Comprehensive with citations |

Blitz RAG provides **better quality at lower cost**!
