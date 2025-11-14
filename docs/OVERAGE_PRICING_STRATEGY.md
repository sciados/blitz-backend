# Overage Pricing Strategy
## Base Limits + Pay Extra for More

---

## OVERAGE MODEL DESIGN

### Core Concept
- **Base tier price** includes reasonable limits
- **Overage pricing** for additional content
- **No hard limits** - pay as you grow
- **Power users pay more** while casual users get great value

---

## BASE LIMITS PER CAMPAIGN

### What's Included (Per Campaign)

| Content | Base Limit | Overage Price |
|---------|-----------|---------------|
| **Text** | 8,000 words | $0.10 per 1,000 words |
| **Images** | 50 images | $0.50 per image |
| **Videos** | 10 videos | $3.00 per video |

**Note:** Increased from original 12K/80/20 to 8K/50/10 base limits

---

## TIER PRICING (With Overage)

### 🆓 FREE TIER - $0
**Base Included:**
- 1 Campaign
- 8,000 words
- 50 images
- 10 videos

**Overage:**
- Text: $0.10 per 1,000 words
- Images: $0.50 per image
- Videos: $3.00 per video

**Example Usage:**
- 1 campaign × 12K words (4K over) = $0.40
- 60 images (10 over) = $5.00
- 15 videos (5 over) = $15.00
- **Total:** $0 + $20.40 = **$20.40**

### 🚀 STARTER TIER - $19/month
**Base Included:**
- 5 Campaigns
- 40,000 words (8K per campaign)
- 250 images (50 per campaign)
- 50 videos (10 per campaign)

**Overage:**
- Text: $0.08 per 1,000 words (discount)
- Images: $0.40 per image (discount)
- Videos: $2.50 per video (discount)

**Example Usage:**
- Use all 5 campaigns fully = **$19.00**
- Add 2 more campaigns worth = $15.60
- **Total:** $34.60

### 💼 PRO TIER - $59/month
**Base Included:**
- 12 Campaigns
- 96,000 words (8K per campaign)
- 600 images (50 per campaign)
- 120 videos (10 per campaign)

**Overage:**
- Text: $0.06 per 1,000 words
- Images: $0.30 per image
- Videos: $2.00 per video

**Example Usage:**
- Use all 12 campaigns = **$59.00**
- Add 3 more campaigns worth = $25.20
- **Total:** $84.20

### 🏢 ENTERPRISE TIER - $199/month
**Base Included:**
- 40 Campaigns
- 320,000 words (8K per campaign)
- 2,000 images (50 per campaign)
- 400 videos (10 per campaign)

**Overage:**
- Text: $0.05 per 1,000 words
- Images: $0.25 per image
- Videos: $1.50 per video

**Example Usage:**
- Use all 40 campaigns = **$199.00**
- Add 10 more campaigns worth = $67.50
- **Total:** $266.50

---

## OVERAGE PRICING TABLE

### Cost Per Additional Content

| Tier | Text/1K words | Per Image | Per Video |
|------|--------------|-----------|-----------|
| Free | $0.10 | $0.50 | $3.00 |
| Starter | $0.08 | $0.40 | $2.50 |
| Pro | $0.06 | $0.30 | $2.00 |
| Enterprise | $0.05 | $0.25 | $1.50 |

**Discount increases with tier** ✅

---

## EXAMPLE: POWER USER COSTS

### User with 15 Campaigns on PRO Tier

**Base (12 campaigns):**
- $59/month

**Overage (3 campaigns worth):**
- Text: 24K words = $1.44
- Images: 150 images = $45.00
- Videos: 30 videos = $60.00
- **Total overage:** $106.44

**Grand Total:** $59 + $106.44 = **$165.44**

**Cost per campaign:** $11.03 (vs $4.92 base)

---

## REVENUE PROJECTIONS

### With 20% of Users Using Overage

| Tier | Base Revenue | Overage Revenue | Total |
|------|--------------|-----------------|-------|
| Free | $0 | $5-20/user | $5-20 |
| Starter | $19 | $5-15/user | $24-34 |
| Pro | $59 | $10-30/user | $69-89 |
| Enterprise | $199 | $20-50/user | $219-249 |

**Average revenue per user increases 20-30%!**

---

## IMPLEMENTATION

### 1. Database Schema
```sql
ALTER TABLE usage_tracking ADD COLUMN base_words INT DEFAULT 0;
ALTER TABLE usage_tracking ADD COLUMN overage_words INT DEFAULT 0;
ALTER TABLE usage_tracking ADD COLUMN overage_cost DECIMAL(10,2) DEFAULT 0.00;

-- Add to tier_configs
ALTER TABLE tier_configs ADD COLUMN base_words_per_campaign INT DEFAULT 8000;
ALTER TABLE tier_configs ADD COLUMN base_images_per_campaign INT DEFAULT 50;
ALTER TABLE tier_configs ADD COLUMN base_videos_per_campaign INT DEFAULT 10;
ALTER TABLE tier_configs ADD COLUMN overage_rate_text DECIMAL(10,4) DEFAULT 0.10;
ALTER TABLE tier_configs ADD COLUMN overage_rate_images DECIMAL(10,2) DEFAULT 0.50;
ALTER TABLE tier_configs ADD COLUMN overage_rate_videos DECIMAL(10,2) DEFAULT 3.00;
```

### 2. Usage Tracking
```python
# Calculate overage in real-time
base_limit = tier.base_words_per_campaign * campaign_count
used_words = user.total_words_this_month
overage_words = max(0, used_words - base_limit)
overage_cost = overage_words * tier.overage_rate_text / 1000
```

### 3. Billing Integration
```python
# Add to Stripe metadata
stripe_metadata = {
    "base_cost": 59.00,
    "overage_cost": 25.40,
    "total_cost": 84.40,
    "overage_breakdown": "2.5 campaigns over base"
}
```

---

## USER EXPERIENCE

### 1. Usage Dashboard
```
Campaigns: 12/12 included
Words: 96,000 / 96,000 (0 over)
Images: 580 / 600 (0 over)
Videos: 115 / 120 (5 over) ⚠️

Estimated overage: $10.00
```

### 2. Warning Prompts
- "You've used 115/120 videos (5 remaining)"
- "Upgrade to Pro for $59 to get 120 included videos"
- "Or pay $2.50 per additional video"

### 3. Overage Preview
```
"Adding 3 more campaigns will cost:
- Text (24K words): $1.44
- Images (150): $45.00
- Videos (30): $60.00
Total: $106.44
Pro Tip: Upgrade to Enterprise for $199/month and save!"
```

---

## BENEFITS

### For Users:
1. ✅ **No hard limits** - keep creating
2. ✅ **Predictable base pricing**
3. ✅ **Pay only for what you use**
4. ✅ **Clear overage costs**

### For Business:
1. ✅ **Higher revenue per user** (20-30% increase)
2. ✅ **No user churn** from hitting limits
3. ✅ **Monetize power users** appropriately
4. ✅ **Flexible scaling**

---

## RECOMMENDATION

**Implement overage pricing with:**
- Base limits: 8K words, 50 images, 10 videos per campaign
- Overage rates decrease with higher tiers
- Clear usage tracking and warnings
- Easy upgrade prompts

**This maximizes both user satisfaction and revenue!** 🚀
