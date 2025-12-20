# Embedding Dimension Fix

## Problem
Vector embedding dimension mismatch causing errors during intelligence compilation:
- **ProductIntelligence.intelligence_embedding**: Was 2000 dimensions
- **KnowledgeBase.embedding**: Was 1024 dimensions
- **Cohere embed-english-v3.0** (actual model): Produces **1536 dimensions**

This caused the error:
```
operands could not be broadcast together with shapes (2000,) (1024,)
```

## Solution
Run the migration to align all embedding columns to 1536 dimensions (matching Cohere model).

## Steps to Fix

### 1. Run the Migration
```bash
cd /c/Users/shaun/OneDrive/Documents/GitHub/blitz-backend
alembic upgrade head
```

### 2. Verify Migration Success
You should see:
```
INFO  [alembic.runtime.migration] Running upgrade 009 -> 010, fix embedding dimensions to match cohere model
✅ Embedding dimensions fixed: 2000/1024 -> 1536
ℹ️  All embeddings cleared - will regenerate on next intelligence refresh
```

### 3. Deploy to Railway
```bash
git add .
git commit -m "fix: Align embedding dimensions to 1536 (Cohere embed-english-v3.0)"
git push
```

Railway will automatically run the migration on deploy.

## What Happens

### ✅ Preserved (No Data Loss)
- All campaigns
- All products (ProductIntelligence records)
- All intelligence_data (JSONB field with product research)
- All generated content
- All knowledge base content (text chunks)
- All metadata, timestamps, relationships

### 🔄 Regenerated (Set to NULL temporarily)
- `ProductIntelligence.intelligence_embedding` → NULL
- `KnowledgeBase.embedding` → NULL

These will automatically regenerate the next time you:
- Click "Refresh Intelligence" on a product
- Compile intelligence for a new product
- Run RAG queries (embeddings generated on-the-fly)

## Why This Happened
The database schema was designed for OpenAI's text-embedding-3-large (which supports configurable dimensions), but the actual implementation uses Cohere's embed-english-v3.0 (fixed at 1536 dimensions).

## After Migration
- ✅ All intelligence refresh operations will work correctly
- ✅ RAG queries will function properly
- ✅ No more "broadcast shapes" errors
- ✅ Embeddings will be consistently sized across all tables

## Testing After Migration
1. Navigate to Product Library in frontend
2. Click any product to view details
3. Click "Refresh Intelligence"
4. Should complete successfully without errors
5. Verify embeddings are generated in logs:
   ```
   ✅ Generated embedding (dim: 1536)
   ```
