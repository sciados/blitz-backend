# Cost Breakdown by Content Type
## What Costs the Most?

---

## COST PER UNIT

### 📝 TEXT (AI Tokens)
**Cost:** $0.30 per 1,000 tokens (average across providers)
- Groq (free): $0.00
- Together AI: $0.06-0.22
- OpenAI gpt-4o-mini: $0.15/$0.60 (input/output)
- Anthropic Claude: $0.25/$1.25
- Premium models: $2.50-5.00

**Example:**
- 12,000 words = 16,000 tokens
- Cost: 16 × $0.30 = **$4.80 per campaign**

### 🖼️ IMAGES (Stability AI)
**Cost:** $0.03-0.04 per image (from database)
- Stable Diffusion XL: $0.04
- Stable Diffusion 3 Medium: $0.03

**Example:**
- 80 images = 80 × $0.035 = **$2.80 per campaign**

### 🎥 VIDEOS
**Cost:** Varies widely
- Estimated: $0.50-2.00 per video (text-to-video models)
- Short clips (5-10 sec): ~$0.50
- Medium videos (15-30 sec): ~$1.00
- Longer videos (60 sec): ~$2.00

**Example:**
- 20 videos = 20 × $1.00 = **$20.00 per campaign**

---

## COST BREAKDOWN PER CAMPAIGN

### Per Campaign (12K words, 80 images, 20 videos)

```
CONTENT TYPE    UNITS      COST PER UNIT    TOTAL COST
─────────────────────────────────────────────────────────
Text            16K tokens × $0.30      = $4.80
Images          80 images × $0.035      = $2.80
Videos          20 videos × $1.00       = $20.00
                                        ─────────
TOTAL PER CAMPAIGN                        $27.60
```

---

## WHAT COSTS THE MOST? 🎬

### RANKING (Most to Least Expensive)
1. **VIDEOS** - $20.00 (73% of cost)
2. **TEXT** - $4.80 (17% of cost)
3. **IMAGES** - $2.80 (10% of cost)

**Videos are 7× more expensive than text and images combined!**

---

## COST BY TIER

### FREE TIER (1 Campaign)
```
Text (12K words):     $4.80
Images (20):          $0.70
Videos (2):           $2.00
                        ──
TOTAL:                $7.50
```

### STARTER TIER (5 Campaigns)
```
Text (60K words):     $24.00
Images (400):         $14.00
Videos (100):         $100.00
                        ──
TOTAL:                $138.00
Cost per campaign:    $27.60
```

### PRO TIER (12 Campaigns)
```
Text (144K words):    $57.60
Images (960):         $33.60
Videos (240):         $240.00
                        ──
TOTAL:                $331.20
Cost per campaign:    $27.60
```

### ENTERPRISE TIER (40 Campaigns)
```
Text (480K words):    $192.00
Images (3,200):       $112.00
Videos (800):         $800.00
                        ──
TOTAL:                $1,104.00
Cost per campaign:    $27.60
```

---

## VIDEO COST ANALYSIS

### Why Videos Are Expensive
1. **Computational Intensity:** Generating videos requires massive GPU resources
2. **Long Generation Time:** 5-60 seconds of video takes minutes to render
3. **Premium Models:** State-of-the-art video models are newest and priciest
4. **Multiple Steps:** Often require initial image + prompt + rendering

### Video Cost Comparison
```
SERVICE           COST PER VIDEO    NOTES
─────────────────────────────────────────
Runway ML         $0.10-0.50        Budget option
Pika Labs         $0.50-1.00        Mid-range
Stable Video      $0.50-1.50        Good quality
OpenAI Sora       $2.00+           Premium (not yet public)
Blitz (est.)      $1.00           Good balance
```

---

## OPTIMIZATION STRATEGIES

### 1. Video Cost Reduction
- **Limit videos per campaign:** Currently 20, could reduce to 10
- **Use budget providers:** $0.50 instead of $1.00
- **Generate shorter videos:** 5-10 sec clips
- **Mix formats:** Static images + 5 videos instead of 20 videos

### 2. Image Cost Reduction
- Already cheap at $0.035 per image
- Could reduce to $0.02 (43% savings)
- Or keep at $0.035 (acceptable)

### 3. Text Cost Optimization
- Already using budget providers at $0.30/1K tokens
- Could reduce to $0.20 (33% savings)
- Or stay at $0.30 (reasonable)

---

## REVISED CAMPAIGN COST (Optimized)

### Per Campaign with Cost Reductions

```
CONTENT TYPE    UNITS      COST PER UNIT    SAVINGS    NEW TOTAL
────────────────────────────────────────────────────────────────
Text            16K tokens × $0.20      -$1.60    $3.20
Images          80 images × $0.025     -$0.80    $2.00
Videos          10 videos × $0.75      -$5.00    $7.50
                                                ───────
TOTAL PER CAMPAIGN                                     $12.70
```

**NEW TOTAL: $12.70 (vs $27.60 original) - 54% savings!**

---

## IMPACT ON PRICING

### If We Reduce Video Limit to 10 per Campaign

| Tier | Campaigns | Videos | New Cost | Price | Margin |
|------|-----------|--------|----------|-------|--------|
| Free | 1 | 10 | $5.20 | $0 | N/A |
| Starter | 5 | 50 | $26.00 | $25 | 4% |
| Pro | 12 | 120 | $62.40 | $79 | 21% |
| Enterprise | 40 | 400 | $208.00 | $249 | 16% |

**Margins still good, but video cost is less of a burden!**

---

## RECOMMENDATIONS

### Option 1: Keep Current Limits
- Videos: 20 per campaign
- Cost: $27.60 per campaign
- Pricing: Current model works

### Option 2: Reduce Video Limit
- Videos: 10 per campaign
- Cost: $17.70 per campaign
- Better margins, similar value

### Option 3: Hybrid Pricing
- Keep video count at 20
- But offer "Budget Mode" with 10 videos
- Users choose based on needs

---

## KEY INSIGHTS

1. **Videos are the biggest cost driver** (73% of total cost)
2. **Text is cheap** (17% of cost)
3. **Images are cheapest** (10% of cost)
4. **Reducing videos by 50% saves $10 per campaign**
5. **Current pricing model works with video costs**

---

## SUMMARY

**Cost per campaign: $27.60**
- Videos: $20.00 (73%) 💸
- Text: $4.80 (17%) ✅
- Images: $2.80 (10%) ✅

**Solution:** Either keep current model or reduce video count to 10 for better margins!
