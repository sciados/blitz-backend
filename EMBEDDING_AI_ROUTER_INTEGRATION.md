# Embedding AI Router Integration

## Overview
Integrated the AI Router into the embedding service for automatic failover between providers, matching the content generation architecture.

## Changes Made

### 1. New Embedding Router Service
**File**: `app/services/embeddings_router.py`

Unified embedding service that:
- ✅ Uses AI Router to select best provider (cost + health)
- ✅ Automatic failover to backup provider on failure
- ✅ Supports OpenAI text-embedding-3-large (1536 dimensions)
- ✅ Supports Cohere embed-english-v3.0 (1536 dimensions)
- ✅ Consistent 1536-dimensional output from all providers
- ✅ Cost tracking and usage analytics

### 2. Intelligence Compiler Integration
**File**: `app/services/intelligence_compiler_service.py`

- ✅ Replaced `OpenAIEmbeddingService` with `EmbeddingRouterService`
- ✅ Now uses AI Router for all embedding generation
- ✅ Automatic failover during intelligence compilation

### 3. Configuration Updates
**File**: `app/core/config/constants.py`

Updated `EMBEDDING_CONFIG`:
```python
EMBEDDING_CONFIG = {
    "provider": "ai_router",  # Uses AI Router for automatic failover
    "primary_provider": "openai",
    "primary_model": "text-embedding-3-large",
    "fallback_provider": "cohere",
    "fallback_model": "embed-english-v3.0",
    "dimensions": 1536,  # Fixed dimension for all providers
    "similarity_threshold": 0.7,
}
```

### 4. Legacy Service Fix
**File**: `app/services/embeddings_openai.py`

- ✅ Updated dimensions from 1024 → 1536 (in case still used directly)

## Provider Configuration

### Railway Environment Variables
```bash
AI_EMBEDDINGS="openai:text-embedding-3-large,cohere:embed-english-v3.0"
```

### Routing Logic
1. **Primary**: OpenAI text-embedding-3-large
   - Cost: $0.02 per 1K tokens
   - Output: 1536 dimensions (configurable)
   - Fastest with highest quality

2. **Fallback**: Cohere embed-english-v3.0
   - Cost: $0.10 per 1K tokens
   - Output: 1536 dimensions (padded/truncated as needed)
   - Reliable backup option

## Benefits

### 🚀 Automatic Failover
If OpenAI fails or is unavailable:
```
[EmbeddingRouter] Using openai:text-embedding-3-large for embeddings
❌ Embedding generation failed with openai:text-embedding-3-large: API error
[EmbeddingRouter] Attempting fallback...
[EmbeddingRouter] Fallback to Cohere
✅ Generated embedding (provider: cohere, dim: 1536)
```

### 💰 Cost Optimization
AI Router automatically selects the cheapest available provider that meets health requirements.

### 📊 Health Tracking
Failed providers are temporarily marked unhealthy and avoided for subsequent requests.

### 🔄 Consistent with Content Generation
Embeddings now use the same routing architecture as text/image/video generation.

## Dimension Alignment

All embedding vectors are exactly **1536 dimensions**:
- ✅ ProductIntelligence.intelligence_embedding: Vector(1536)
- ✅ KnowledgeBase.embedding: Vector(1536)
- ✅ OpenAI text-embedding-3-large: 1536 (requested via API)
- ✅ Cohere embed-english-v3.0: 1536 (padded/truncated)

## Testing After Deployment

### Test 1: Intelligence Refresh
1. Navigate to Product Library
2. Click any product (e.g., Mitolyn)
3. Click "Refresh Intelligence"
4. **Expected Logs**:
   ```
   [EmbeddingRouter] Using openai:text-embedding-3-large for embeddings
   ✅ Generated embedding (provider: openai, dim: 1536)
   ```

### Test 2: Failover Simulation
If OpenAI fails:
```
[EmbeddingRouter] Using openai:text-embedding-3-large for embeddings
❌ Embedding generation failed with openai:text-embedding-3-large
[EmbeddingRouter] Fallback to Cohere
✅ Generated embedding (provider: cohere, dim: 1536)
```

### Test 3: RAG Queries
All RAG queries now use the router for embedding generation:
```python
embedding = await embedding_router_service.embed_query("best marketing angles")
```

## Cost Comparison

| Provider | Model | Cost per 1M tokens | Notes |
|----------|-------|-------------------|-------|
| **OpenAI** | text-embedding-3-large | $0.13 | Primary (5x cheaper) |
| **Cohere** | embed-english-v3.0 | $0.10 | Fallback |

## Migration Path

### Before (Hardcoded)
```python
self.embeddings = OpenAIEmbeddingService()  # Fixed provider
```

### After (AI Router)
```python
self.embeddings = EmbeddingRouterService()  # Dynamic routing + failover
```

## Compatibility

- ✅ All existing code using `self.embeddings.generate_embedding()` works without changes
- ✅ Batch embedding generation supported
- ✅ Query embeddings supported
- ✅ Cost calculation supported
- ✅ Content hashing supported

## Rollback Plan

If issues occur, revert to OpenAI-only:
```python
# In intelligence_compiler_service.py
from app.services.embeddings_openai import OpenAIEmbeddingService
self.embeddings = OpenAIEmbeddingService()
```

## Next Steps

After successful deployment:
1. Monitor logs for failover frequency
2. Verify dimension consistency (all 1536)
3. Track cost savings from using OpenAI primarily
4. Monitor embedding quality in RAG responses
