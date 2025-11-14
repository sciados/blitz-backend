# Tier Redesign: Campaign-Based Limits
## Based on Effective 4-Week Campaign Content Requirements

---

## 4-Week Campaign Content Analysis

### What's Needed Per Campaign (Per Month):

**TEXT CONTENT:**
- Social Media Posts: 40 posts × 50 words = 2,000 words
- Email Sequences: 8 emails × 300 words = 2,400 words
- Blog Articles: 3 articles × 1,000 words = 3,000 words
- Landing Page: 1 × 1,500 words = 1,500 words
- Ad Copy: 15 variations × 100 words = 1,500 words
- Sales Pages: 2 × 2,000 words = 4,000 words
- **Total Text: ~14,400 words per campaign/month**

**IMAGES:**
- Social Media: 40 images
- Blog/Articles: 9 images
- Email Headers: 8 images
- Ad Creatives: 20 images
- Landing Page: 5 images
- **Total Images: ~82 images per campaign/month**

**VIDEOS:**
- Social Media: 10 videos
- Email Videos: 4 videos
- Blog Video: 2 videos
- Ad Videos: 5 videos
- **Total Videos: ~21 videos per campaign/month**

---

## CAMPAIGN-BASED TIER DESIGN

### Tier Limits by Campaign Count

| Tier | Max Campaigns | Words/Campaign | Images/Campaign | Videos/Campaign | Monthly Total |
|------|--------------|----------------|-----------------|-----------------|---------------|
| **Free** | 3 | 12K | 60 | 15 | 36K words, 180 images, 45 videos |
| **Starter** | 10 | 12K | 80 | 20 | 120K words, 800 images, 200 videos |
| **Pro** | 30 | 12K | 80 | 20 | 360K words, 2,400 images, 600 videos |
| **Enterprise** | 100 | 12K | 80 | 20 | 1.2M words, 8,000 images, 2,000 videos |

### Campaign Limit Analysis

**Free Tier - 3 Campaigns:**
- Perfect for: Testing, solo marketers, 1-2 niches
- Covers: 1 main campaign + 2 testing campaigns
- Users can afford 3 × 14K word campaigns

**Starter Tier - 10 Campaigns:**
- Perfect for: Small agencies, multi-niche marketers
- Covers: 10 different product niches
- Realistic for 1-2 people managing multiple offers

**Pro Tier - 30 Campaigns:**
- Perfect for: Agencies, content teams
- Covers: 30 campaigns across various clients/niches
- Full-time content operation level

**Enterprise Tier - 100 Campaigns:**
- Perfect for: Large agencies, enterprises
- Covers: 100+ campaigns across entire organization
- Maximum scaling

---

## CONTENT PER CAMPAIGN: 12K Words

### Breakdown (14,400 words needed vs 12,000 allocated)
- Buffer: 2,400 words (testing, revisions, variations)
- Margin for multiple rounds of edits
- Room for A/B testing variations

**Text Content Distribution:**
```
40 Social Posts × 50 words    = 2,000 words
8 Emails × 300 words          = 2,400 words
3 Articles × 1,000 words      = 3,000 words
1 Landing Page × 1,500 words  = 1,500 words
10 Ad Sets × 150 words        = 1,500 words
2 Sales Pages × 1,800 words   = 3,600 words
                                ─────────
TOTAL:                        14,000 words
```

**Realistic buffer for revisions + testing = 12,000-14,000 words**

---

## PRICING RECALCULATION

### Based on Campaign Limits & AI Costs

**Cost Calculation (using budget AI providers @ $0.30/1K tokens avg):**

**Free Tier:**
- 36K words = 48K tokens
- AI Cost: $14.40
- Price: $0
- **Margin: subsidized (acquisition tier)**

**Starter Tier:**
- 120K words = 160K tokens
- AI Cost: $48.00
- Price: $49
- **Margin: 2% (close to break-even)**

**Pro Tier:**
- 360K words = 480K tokens
- AI Cost: $144.00
- Price: $199
- **Margin: 28% ($55 profit)**

**Enterprise Tier:**
- 1.2M words = 1.6M tokens
- AI Cost: $480.00
- Price: $799
- **Margin: 40% ($319 profit)**

---

## RECOMMENDED TIER PRICING

| Tier | Campaigns | Monthly Price | AI Cost | Margin | Status |
|------|-----------|---------------|---------|--------|--------|
| **Free** | 3 | $0 | $14.40 | N/A | ✅ Acquisition |
| **Starter** | 10 | $49 | $48.00 | 2% | ✅ Break-even |
| **Pro** | 30 | $199 | $144.00 | 28% | ✅ Profitable |
| **Enterprise** | 100 | $799 | $480.00 | 40% | ✅ Profitable |

---

## IMPLEMENTATION CHANGES NEEDED

### Database Changes (tier_configs table)

**Update fields:**
1. `max_campaigns` - Primary limit
2. `words_per_month` - Calculated: campaigns × 12K
3. `words_per_day` - Monthly ÷ 30
4. `images_per_month` - campaigns × 80
5. `videos_per_month` - campaigns × 20

### SQL Update Query

```sql
-- FREE TIER
UPDATE tier_configs
SET monthly_price = 0.00,
    max_campaigns = 3,
    words_per_month = 36000,        -- 3 × 12K
    words_per_day = 1200,
    images_per_month = 180,         -- 3 × 60
    videos_per_month = 45           -- 3 × 15
WHERE tier_name = 'free';

-- STARTER TIER
UPDATE tier_configs
SET monthly_price = 49.00,
    max_campaigns = 10,
    words_per_month = 120000,       -- 10 × 12K
    words_per_day = 4000,
    images_per_month = 800,         -- 10 × 80
    videos_per_month = 200          -- 10 × 20
WHERE tier_name = 'starter';

-- PRO TIER
UPDATE tier_configs
SET monthly_price = 199.00,
    max_campaigns = 30,
    words_per_month = 360000,       -- 30 × 12K
    words_per_day = 12000,
    images_per_month = 2400,        -- 30 × 80
    videos_per_month = 600          -- 30 × 20
WHERE tier_name = 'pro';

-- ENTERPRISE TIER
UPDATE tier_configs
SET monthly_price = 799.00,
    max_campaigns = 100,
    words_per_month = 1200000,      -- 100 × 12K
    words_per_day = 40000,
    images_per_month = 8000,        -- 100 × 80
    videos_per_month = 2000         -- 100 × 20
WHERE tier_name = 'enterprise';
```

---

## USER EXPERIENCE IMPROVEMENTS

### 1. Campaign Dashboard
- Show campaign count vs limit
- Visual indicators: "3/10 campaigns used"
- Easy campaign creation with limit warnings

### 2. Usage Tracking Per Campaign
- Track words, images, videos per campaign
- Show "Campaign X: 8K/12K words used (67%)"
- Help users understand consumption

### 3. Smart Allocation
- Allow reallocation between campaigns (soft limits)
- Show "You have 20K words left - assign to which campaign?"

### 4. Upgrade Prompts
- "You've used 9/10 campaigns. Upgrade to Pro for 30 campaigns."
- Clear value proposition at limit

---

## BENEFITS OF CAMPAIGN-BASED MODEL

1. **User-Friendly:** "10 campaigns" is easier to understand than "120K words"
2. **Predictable:** Users know exactly what they're getting
3. **Scalable:** Limits grow with user's business
4. **Cost-Effective:** Proper margins at each tier
5. **Fair:** Power users pay appropriately
6. **Sustainable:** No money-losing tiers

---

## NEXT STEPS

1. ✅ Design new tier structure (DONE)
2. ⏳ Update database tier_configs table
3. ⏳ Update migration file
4. ⏳ Update frontend to show campaign limits
5. ⏳ Update usage tracking UI
6. ⏳ Test with sample users
7. ⏳ Announce changes to existing users
8. ⏳ Implement with 30-day grace period

---

## MIGRATION STRATEGY

**Existing Users:**
- Keep current limits for 60 days
- Offer upgrade discount (20% off first 3 months)
- Clear communication about improvements

**New Users:**
- Launch with new limits immediately
- Better value proposition
- Clear campaign-based messaging

**Result:**
- Better user experience
- Sustainable pricing
- Clear value tiers
- Healthy margins
