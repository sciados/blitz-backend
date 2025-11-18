# AI Provider Configuration for Railway

## Overview
Blitz uses an AI Router with automatic fallback across multiple providers for cost optimization and reliability.

## Railway Environment Variables

Add these to your Railway project settings:

```bash
# ========================================
# AI PROVIDER ROUTING CONFIGURATION
# ========================================

# Quality chat (for intelligence analysis)
# Priority order: cheapest/free first, fallback to premium
AI_CHAT_QUALITY="groq:llama-3.1-70b-versatile, anthropic:claude-3.5-sonnet-20241022, openai:gpt-4.1"

# Fast chat (for quick tasks)
AI_CHAT_FAST="groq:llama-3.1-70b-versatile, openai:gpt-4o-mini"

# Vision (for image classification)
AI_VISION="groq:llama-3.2-vision, openai:gpt-4o, anthropic:claude-3.5-sonnet-20241022"

# Embeddings (for RAG)
AI_EMBEDDINGS="openai:text-embedding-3-large"

# Image Generation (optional)
AI_IMAGE_GEN="fal:sdxl-turbo, replicate:flux"

# ========================================
# AI SYSTEM FLAGS
# ========================================
AI_COST_OPTIMIZATION=true
AI_FALLBACK_ENABLED=true
AI_CACHE_TTL_SECONDS=300
```

## How It Works

### 1. **Automatic Provider Selection**
The AI Router picks the **cheapest available provider** first:
- Groq (FREE Llama 3.1 70B) → Try first
- Anthropic Claude → Fallback if Groq fails
- OpenAI GPT-4 → Last resort

### 2. **Automatic Fallback**
If a provider fails (API down, rate limit, no credits):
- Marks provider as unhealthy
- Automatically tries next provider in list
- Caches health status for 5 minutes

### 3. **Cost Tracking**
Every API call returns:
```json
{
  "provider": "groq",
  "model": "llama-3.1-70b-versatile",
  "estimated_cost_usd": 0.00  // Groq is free!
}
```

## Recommended Configuration

### FREE Tier (Groq Only)
```bash
AI_CHAT_QUALITY="groq:llama-3.1-70b-versatile"
AI_VISION="groq:llama-3.2-vision"
```
**Cost:** $0.00/month ✅

### Budget Tier (Groq + OpenAI Fallback)
```bash
AI_CHAT_QUALITY="groq:llama-3.1-70b-versatile, openai:gpt-4o-mini"
AI_VISION="groq:llama-3.2-vision, openai:gpt-4o"
```
**Cost:** ~$1-5/month (only if Groq fails)

### Production Tier (All Providers)
```bash
AI_CHAT_QUALITY="groq:llama-3.1-70b-versatile, anthropic:claude-3.5-sonnet-20241022, openai:gpt-4.1"
AI_VISION="groq:llama-3.2-vision, openai:gpt-4o, anthropic:claude-3.5-sonnet-20241022"
```
**Cost:** Minimized, with premium fallback for reliability

## Provider Costs (per 1M tokens)

| Provider | Model | Input | Output | Free? |
|----------|-------|--------|--------|-------|
| **Groq** | Llama 3.1 70B | $0.00 | $0.00 | ✅ YES |
| **Groq** | Llama 3.2 Vision | $0.00 | $0.00 | ✅ YES |
| DeepSeek | deepseek-chat | $0.14 | $0.28 | ❌ |
| Anthropic | Claude 3.5 Sonnet | $3.00 | $15.00 | ❌ |
| OpenAI | GPT-4o mini | $0.15 | $0.60 | ❌ |
| OpenAI | GPT-4.1 | $5.00 | $15.00 | ❌ |

## Required API Keys

Add these to Railway (only for providers you're using):

```bash
# Free Providers (GET THESE FIRST!)
GROQ_API_KEY=gsk_...              # Get at: https://console.groq.com
XAI_API_KEY=xai-...               # Get at: https://console.x.ai (Grok)

# Premium Providers (Optional)
ANTHROPIC_API_KEY=sk-ant-...      # Get at: https://console.anthropic.com
OPENAI_API_KEY=sk-...             # Get at: https://platform.openai.com
COHERE_API_KEY=...                # Get at: https://dashboard.cohere.com
DEEPSEEK_API_KEY=sk-...           # Get at: https://platform.deepseek.com
TOGETHER_API_KEY=...              # Get at: https://api.together.xyz
```

## Setup Instructions

### Step 1: Get Groq API Key (FREE)
1. Go to https://console.groq.com
2. Sign up (Google/GitHub login)
3. Navigate to API Keys
4. Create new key
5. Copy to Railway as `GROQ_API_KEY`

### Step 2: Configure Router
1. In Railway, go to your backend service
2. Click "Variables"
3. Add `AI_CHAT_QUALITY` with value:
   ```
   groq:llama-3.1-70b-versatile, anthropic:claude-3.5-sonnet-20241022
   ```
4. Add `AI_VISION` with value:
   ```
   groq:llama-3.2-vision, anthropic:claude-3.5-sonnet-20241022
   ```

### Step 3: Deploy
Railway will automatically redeploy with new configuration.

## Testing

After deployment, test the intelligence compilation:
- First attempt will use **Groq (FREE)**
- If Groq fails, automatically falls back to **Anthropic** (if you have credits)
- All costs tracked and logged

## Monitoring

Check Railway logs to see which provider was used:
```
[AIRouter] Picked provider groq:llama-3.1-70b-versatile for chat_quality
✅ Intelligence amplified successfully
   - Model: groq:llama-3.1-70b-versatile
   - Cost: $0.0000
```

## Benefits

✅ **$0 cost** for most requests (Groq is free)
✅ **Automatic failover** if Groq rate limits
✅ **No code changes** needed - just env vars
✅ **Cost tracking** for every request
✅ **Premium quality** available as fallback

## Troubleshooting

**"No providers configured for use case"**
→ Add `AI_CHAT_QUALITY` or `AI_VISION` env var to Railway

**"All AI providers failed"**
→ Check API keys are valid
→ Check Groq rate limits (https://console.groq.com/settings/limits)
→ Add fallback provider (OpenAI/Anthropic)

**Want even cheaper?**
→ Try DeepSeek ($0.14/$0.28 per 1M tokens) as fallback:
```bash
AI_CHAT_QUALITY="groq:llama-3.1-70b-versatile, deepseek:deepseek-chat"
```
