# Monthly Cost Per User Calculation
## Based on Maximum Tier Usage & AI Provider Costs

---

## Assumptions

### Token Conversion
- **1 word ≈ 1.33 tokens** (English average)
- Content generation typically uses 60% input tokens, 40% output tokens
- Example: 2,000 word generation = 2,660 tokens total (1,596 input + 1,064 output)

### AI Provider Priority (Cost-Optimized)
1. **FREE TIERS** (Priority 100): Groq, XAI, MiniMax - $0.00
2. **BUDGET** (Priority 70-85): Together, DeepSeek, gpt-4o-mini - $0.06-$0.60
3. **PREMIUM** (Priority 20-55): Claude, gpt-4o, gpt-4.1 - $1.50-$15.00

### Free Provider Limits
- Groq: ~10,000 requests/month (estimated)
- XAI: ~5,000 requests/month (estimated)
- MiniMax: ~8,000 requests/month (estimated)

---

## TIER ANALYSIS

### 🆓 FREE TIER
**Monthly Price:** $0.00
**Word Limit:** 10,000 words/month

**Token Usage:**
- Total tokens: 10,000 words × 1.33 = **13,300 tokens/month**
- Input tokens (60%): 7,980
- Output tokens (40%): 5,320

**Cost Calculation:**
- ✅ Uses FREE providers (Groq, XAI, MiniMax)
- **AI Cost:** $0.00
- **Your Cost:** $0.00
- **Profit Margin:** N/A (Free tier)

---

### 🚀 STARTER TIER
**Monthly Price:** $19.00
**Word Limit:** 50,000 words/month

**Token Usage:**
- Total tokens: 50,000 words × 1.33 = **66,500 tokens/month**
- Input tokens (60%): 39,900
- Output tokens (40%): 26,600

**Cost Calculation:**
- First 30,000 tokens: FREE providers = $0.00
- Next 36,500 tokens: Budget providers (Together AI @ $0.12/1K tokens avg)
  - Input: 23,700 tokens × $0.00012 = **$2.84**
  - Output: 14,800 tokens × $0.00012 = **$1.78**
- **Total AI Cost:** $4.62
- **Your Price:** $19.00
- **Gross Margin:** 76% ($14.38 profit per user)

---

### 💼 PRO TIER
**Monthly Price:** $59.00
**Word Limit:** 200,000 words/month

**Token Usage:**
- Total tokens: 200,000 words × 1.33 = **266,000 tokens/month**
- Input tokens (60%): 159,600
- Output tokens (40%): 106,400

**Cost Calculation:**
- First 30,000 tokens: FREE providers = $0.00
- Next 236,000 tokens: Budget + Mid-tier providers
  - Uses gpt-4o-mini, Together AI, DeepSeek (avg $0.30/1K tokens)
  - Input: 159,600 × $0.00030 = **$47.88**
  - Output: 106,400 × $0.00030 = **$31.92**
- **Total AI Cost:** $79.80
- **Your Price:** $59.00
- **Gross Margin:** -35% (⚠️ **LOSS OF $20.80** per user)

**Recommendation:** Increase Pro tier to **$79** or reduce word limit to **150,000 words**

---

### 🏢 ENTERPRISE TIER
**Monthly Price:** $129.00
**Word Limit:** 500,000 words/month

**Token Usage:**
- Total tokens: 500,000 words × 1.33 = **665,000 tokens/month**
- Input tokens (60%): 399,000
- Output tokens (40%): 266,000

**Cost Calculation:**
- First 30,000 tokens: FREE providers = $0.00
- Next 635,000 tokens: Mix of budget and premium providers
  - 400,000 tokens on gpt-4o-mini/Claude Haiku: $120.00
  - 235,000 tokens on premium models: $176.25
- **Total AI Cost:** ~$296.25
- **Your Price:** $129.00
- **Gross Margin:** -129% (⚠️ **LOSS OF $167.25** per user)

**Recommendation:** Increase Enterprise tier to **$299** or reduce word limit to **250,000 words**

---

## SUMMARY TABLE

| Tier | Price | Word Limit | Est. AI Cost | Gross Margin | Recommendation |
|------|-------|-----------|--------------|--------------|----------------|
| Free | $0 | 10K | $0 | N/A | ✅ Good |
| Starter | $19 | 50K | $4.62 | 76% | ✅ Profitable |
| Pro | $59 | 200K | $79.80 | -35% | ⚠️ **Increase to $79** |
| Enterprise | $129 | 500K | $296.25 | -129% | ⚠️ **Increase to $299** |

---

## REVISED PRICING RECOMMENDATIONS

### Option 1: Keep Limits, Raise Prices
- **Free:** $0 (keep)
- **Starter:** $19 (keep)
- **Pro:** **$79** (+$20)
- **Enterprise:** **$299** (+$170)

### Option 2: Keep Prices, Reduce Limits
- **Free:** 10K words (keep)
- **Starter:** 50K words (keep)
- **Pro:** **150K words** (-50K)
- **Enterprise:** **250K words** (-250K)

### Option 3: Hybrid (Recommended)
- **Free:** 10K words
- **Starter:** $19 / 50K words
- **Pro:** $69 / 150K words
- **Enterprise:** $249 / 400K words

---

## KEY INSIGHTS

1. **Free Tier is Excellent** - Cost-effective acquisition tool with minimal overhead
2. **Starter Tier is Profitable** - Great pricing for the cost
3. **Pro Tier Needs Adjustment** - Currently losing money per user
4. **Enterprise Tier Needs Major Adjustment** - Currently losing significant money per user

5. **Cost Optimization Strategies:**
   - Implement request batching to reduce token waste
   - Cache responses to avoid duplicate generations
   - Implement token limits per generation (current limits help)
   - Offer "Budget Mode" option to force cheapest providers
   - Monitor actual vs. estimated usage patterns

---

## ACTUAL USAGE CONSIDERATIONS

The above calculations assume **maximum usage**, which most users won't hit:
- Average user uses ~30-40% of their limit
- Power users (~10% of base) will hit limits
- Most users are casual users using <20% of allocation

**Real-world margin** will be significantly better than these worst-case calculations.
