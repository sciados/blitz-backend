# Required API Keys for Blitz Intelligence System

## Recommended Setup (Simplified & Best-in-Class)

Based on the improved intelligence compilation design, Blitz needs **only 3 API services** (compared to CampaignForge's 5+). We use the **best AI platform for each specific task**.

---

## 1. Anthropic Claude API ⭐ PRIMARY

**Why**: Claude 3.5 Sonnet is the best model for:
- Deep content analysis and reasoning
- Structured data extraction (JSON output)
- Image analysis via Claude Vision API
- Long context understanding (200K tokens)

**What We Use It For**:
- ✅ Intelligence amplification (Step 2)
- ✅ Image classification and analysis
- ✅ Marketing angle detection
- ✅ Content generation (future)

**Get Your API Key**:
1. Sign up at: https://console.anthropic.com/
2. Go to **API Keys** section
3. Create new key
4. Copy the key (starts with `sk-ant-...`)

**Pricing**:
- Claude 3.5 Sonnet: $3/million input tokens, $15/million output tokens
- Very cost-effective for our use case (~$0.05 per campaign)

**Monthly Estimate**: $10-30/month (depending on usage)

**Environment Variable**:
```bash
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

---

## 2. OpenAI API ⭐ REQUIRED

**Why**: OpenAI has the **best embeddings model** for RAG:
- text-embedding-3-large: 3072 dimensions
- Superior semantic understanding
- Best retrieval performance
- Industry standard

**What We Use It For**:
- ✅ Generating embeddings for RAG system (Step 3)
- ✅ Semantic search across campaigns
- ✅ Intelligent content matching

**Get Your API Key**:
1. Sign up at: https://platform.openai.com/
2. Add payment method (required for API access)
3. Go to **API keys**
4. Create new secret key
5. Copy the key (starts with `sk-...`)

**Pricing**:
- text-embedding-3-large: $0.13/million tokens
- Very cheap for embeddings (~$0.002 per campaign)

**Monthly Estimate**: $5-15/month

**Environment Variable**:
```bash
OPENAI_API_KEY=sk-proj-your-key-here
```

---

## 3. Cloudflare R2 ⭐ REQUIRED

**Why**: Best object storage for our use case:
- **Zero egress fees** (huge savings compared to AWS S3)
- S3-compatible API (easy integration)
- Global CDN included
- Cheaper than S3

**What We Use It For**:
- ✅ Storing scraped product images
- ✅ CDN delivery for fast image loading
- ✅ Permanent storage for campaign assets

**Get Your Credentials**:
1. Sign up at: https://dash.cloudflare.com/
2. Go to **R2 Object Storage**
3. Create a bucket (e.g., `blitz-campaign-assets`)
4. Generate R2 API token:
   - Go to **R2 > Manage R2 API Tokens**
   - Create API token with **Object Read & Write** permissions
   - Copy: **Access Key ID** and **Secret Access Key**
5. Get your **Account ID** from R2 dashboard
6. Note your **Bucket Name**

**Pricing**:
- Storage: $0.015/GB/month
- Class A Operations: $4.50/million
- Class B Operations: $0.36/million
- **Zero egress fees** (this is the big win)

**Monthly Estimate**: $1-5/month (very cheap for our use case)

**Environment Variables**:
```bash
# Cloudflare R2 Configuration
CLOUDFLARE_R2_ACCOUNT_ID=your-account-id-here
CLOUDFLARE_R2_ACCESS_KEY_ID=your-access-key-id
CLOUDFLARE_R2_SECRET_ACCESS_KEY=your-secret-access-key
CLOUDFLARE_R2_BUCKET_NAME=blitz-campaign-assets
CLOUDFLARE_R2_PUBLIC_URL=https://pub-xxxxx.r2.dev  # From R2 dashboard
```

---

## Complete Environment Variables

Add these to Railway (Backend):

```bash
# ===================================
# AI Services (Intelligence System)
# ===================================

# Anthropic Claude (Primary AI)
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here

# OpenAI (Embeddings for RAG)
OPENAI_API_KEY=sk-proj-your-key-here

# ===================================
# Image Storage (Cloudflare R2)
# ===================================

CLOUDFLARE_R2_ACCOUNT_ID=your-account-id
CLOUDFLARE_R2_ACCESS_KEY_ID=your-r2-access-key-id
CLOUDFLARE_R2_SECRET_ACCESS_KEY=your-r2-secret-key
CLOUDFLARE_R2_BUCKET_NAME=blitz-campaign-assets
CLOUDFLARE_R2_PUBLIC_URL=https://pub-xxxxx.r2.dev

# ===================================
# Existing Variables (Already Set)
# ===================================

DATABASE_URL=postgresql://...  # Already set by Railway
JWT_SECRET_KEY=your-jwt-secret  # Already set
JWT_ALGORITHM=HS256  # Already set
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # Already set
CORS_ORIGINS=https://your-vercel-app.vercel.app,http://localhost:3000  # Already set
```

---

## Cost Comparison: Blitz vs CampaignForge

### CampaignForge (Over-Engineered)
- OpenAI API ✓
- Anthropic API ✓
- Google AI API ✓
- Stability AI ✓
- Together AI ✓
- Cohere API (for embeddings) ✓
- **Total**: 6 API services
- **Monthly Cost**: $50-150+ (multiple providers)

### Blitz (Optimized)
- Anthropic API ✓ (best for analysis)
- OpenAI API ✓ (best for embeddings)
- Cloudflare R2 ✓ (best for storage)
- **Total**: 3 API services
- **Monthly Cost**: $15-50 (much more efficient)

**Savings**: 60-70% cost reduction

---

## Alternative Options (Future Considerations)

### If you want even better embeddings:
**Voyage AI** (voyage-large-2-instruct)
- Optimized specifically for RAG
- Beats OpenAI on some benchmarks
- Similar pricing
- API: https://www.voyageai.com/

### If you want cheaper storage:
**Backblaze B2**
- Even cheaper than R2
- First 10GB free
- But R2 has better CDN

### If you want local embeddings (advanced):
**Ollama + all-minilm**
- Free, runs locally
- Good for development
- Production: stick with OpenAI

---

## Setup Priority

**Phase 1: Intelligence Compilation** (Do First)
1. ✅ Get **Anthropic API key** (critical)
2. ✅ Get **OpenAI API key** (critical)
3. ✅ Set up **Cloudflare R2** (critical)

**Phase 2: Future Enhancements**
- Voyage AI (if we want to optimize RAG further)
- Additional providers as needed

---

## Testing Your Setup

Once you have the API keys, test them:

### Test Anthropic
```bash
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 1024,
    "messages": [{"role": "user", "content": "Hello, Claude!"}]
  }'
```

### Test OpenAI
```bash
curl https://api.openai.com/v1/embeddings \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "text-embedding-3-large",
    "input": "Test embedding"
  }'
```

### Test Cloudflare R2
```python
import boto3

s3 = boto3.client(
    's3',
    endpoint_url=f'https://{CLOUDFLARE_R2_ACCOUNT_ID}.r2.cloudflarestorage.com',
    aws_access_key_id=CLOUDFLARE_R2_ACCESS_KEY_ID,
    aws_secret_access_key=CLOUDFLARE_R2_SECRET_ACCESS_KEY,
    region_name='auto'
)

# List buckets
response = s3.list_buckets()
print('Buckets:', response['Buckets'])
```

---

## Security Best Practices

1. **Never commit API keys** to git
2. **Use Railway's secret management** for all keys
3. **Rotate keys periodically** (every 90 days)
4. **Set up usage alerts** in each provider's dashboard
5. **Use separate keys** for dev/staging/production

---

## Next Steps

1. **Get the 3 required API keys** (Anthropic, OpenAI, Cloudflare R2)
2. **Add them to Railway environment variables**
3. **Test each service** using the curl commands above
4. **Deploy backend** with new environment variables
5. **Verify** intelligence compilation works end-to-end

**Estimated Setup Time**: 30-45 minutes

---

**Status**: Ready to Implement
**Total Cost**: ~$15-50/month (scales with usage)
**ROI**: Massive - enables automated intelligence gathering worth hours of manual research
