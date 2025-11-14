# Corrected Campaign-Based Tiers
## FREE = 30-Day Trial

---

## TIER LIMITS (CORRECTED)

| Tier | Duration | Campaigns | Words | Images | Videos |
|------|----------|-----------|-------|--------|--------|
| 🆓 **Free** | 30 days | 1 | 12,000 | 20 | 2 |
| 🚀 **Starter** | Monthly | 5 | 60,000 | 400 | 100 |
| 💼 **Pro** | Monthly | 12 | 144,000 | 960 | 240 |
| 🏢 **Enterprise** | Monthly | 40 | 480,000 | 3,200 | 800 |

---

## AI COST CALCULATION

### FREE TIER (30-Day Trial)
- Words: 12,000
- Images: 20
- Videos: 2
- **AI Cost:** ~$4.79 (one-time cost)
- **Marketing Cost:** Acceptable for acquisition

### PAID TIERS (Monthly)

**STARTER:**
- Words: 60,000 → 79,800 tokens → **$23.94**
- Images: 400
- Videos: 100
- **Price: $25** → Margin: 4% ($1.06 profit)

**PRO:**
- Words: 144,000 → 191,520 tokens → **$57.46**
- Images: 960
- Videos: 240
- **Price: $79** → Margin: 27% ($21.54 profit)

**ENTERPRISE:**
- Words: 480,000 → 638,400 tokens → **$191.52**
- Images: 3,200
- Videos: 800
- **Price: $249** → Margin: 23% ($57.48 profit)

---

## UPDATED SUMMARY TABLE

| Tier | Type | Campaigns | Words/Month | Images | Videos | Price | AI Cost | Margin |
|------|------|-----------|-------------|--------|--------|-------|---------|--------|
| 🆓 **Free** | 30-day trial | 1 | 12,000 | 20 | 2 | $0 | $4.79 | N/A |
| 🚀 **Starter** | Monthly | 5 | 60,000 | 400 | 100 | $25 | $23.94 | 4% |
| 💼 **Pro** | Monthly | 12 | 144,000 | 960 | 240 | $79 | $57.46 | 27% |
| 🏢 **Enterprise** | Monthly | 40 | 480,000 | 3,200 | 800 | $249 | $191.52 | 23% |

---

## WHAT FREE TRIAL INCLUDES

### 🆓 FREE - $0 (30 Days Only)
**Perfect for:**
- Testing the platform
- Validating one campaign idea
- See full capabilities before subscribing

**Includes:**
- 1 complete campaign
- 12,000 words
- 20 images
- 2 videos
- Full access to all features
- **Duration:** 30 days only

**After 30 Days:**
- Must upgrade to paid tier
- Or lose access

---

## VALUE PROGRESSION

### Free Trial → Starter
- Upgrade path: Trial ends → Subscribe to Starter
- 5× more content capacity
- $25/month ongoing

### Starter → Pro
- 2.4× more campaigns (5 → 12)
- $79/month (+$54)

### Pro → Enterprise
- 3.3× more campaigns (12 → 40)
- $249/month (+$170)

---

## CONTENT PER CAMPAIGN (NON-TRIAL)

### Full Campaign (Monthly)
- 12,000 words
- 80 images
- 20 videos
- Complete 4-week campaign content

### Free Trial (Limited)
- 12,000 words (same)
- 20 images (75% less)
- 2 videos (90% less)
- Limited to test core functionality

---

## SQL UPDATES

```sql
-- FREE TIER (30-Day Trial)
UPDATE tier_configs
SET
    monthly_price = 0.00,
    max_campaigns = 1,
    words_per_month = 12000,
    words_per_day = 400,
    images_per_month = 20,
    videos_per_month = 2,
    -- Add trial_duration_days = 30 (if field exists)
    -- Or handle in application logic
WHERE tier_name = 'free';

-- STARTER, PRO, ENTERPRISE (unchanged from previous)
```

---

## FRONTEND CONSIDERATIONS

### Trial Display
- "FREE 30-DAY TRIAL" badge
- Countdown timer: "X days remaining"
- Upgrade prompt before trial ends
- "Complete your trial with X campaigns remaining"

### Trial Limitations
- Show "Trial includes 1 campaign, 20 images, 2 videos"
- After trial ends, show "Trial expired - subscribe to continue"
- Preview of paid tier features

### Upgrade CTAs
- "Start your free 30-day trial"
- "Upgrade after trial: $25/month for 5 campaigns"
- "Unlimited campaigns with Pro: $79/month"

---

## USER FLOW

### Free Trial Journey
1. Sign up → Get 30-day trial
2. Use 1 campaign with limited images/videos
3. See full value
4. Trial ends → Must upgrade
5. Choose paid tier

### Conversion Strategy
- Show value during trial
- Push upgrade before trial ends
- Offer annual discount at upgrade
- Clear value proposition at each tier

---

## PRICING COMPARISON

### With Free Trial

| Tier | Price | Campaigns | Cost per Campaign |
|------|-------|-----------|-------------------|
| Free | $0 (30 days) | 1 | $0 (trial) |
| Starter | $25/month | 5 | $5/campaign |
| Pro | $79/month | 12 | $6.50/campaign |
| Enterprise | $249/month | 40 | $6.20/campaign |

### Value vs Traditional Agencies
- Traditional: $9,600-22,500 per campaign
- Blitz: $5-6.50 per campaign
- **SAVINGS: 99.9%** 💰

---

## IMPLEMENTATION CHECKLIST

### Database
- [ ] Update FREE tier limits (12K words, 20 images, 2 videos)
- [ ] Add trial duration logic (30 days)
- [ ] Track trial start/end dates

### Frontend
- [ ] Show "30-day trial" badge
- [ ] Trial countdown timer
- [ ] Limited image/video counts display
- [ ] Upgrade prompts before trial ends
- [ ] Trial expiration handling

### Backend
- [ ] Check trial status on API calls
- [ ] Block access after trial ends
- [ ] Send upgrade reminder emails
- [ ] Track conversion rates

---

## RECOMMENDATION

**Implement with:**
- FREE: 30-day trial, 1 campaign, 12K words, 20 images, 2 videos
- Starter: $25/month, 5 campaigns
- Pro: $79/month, 12 campaigns
- Enterprise: $249/month, 40 campaigns

**This creates a strong trial-to-paid conversion funnel!** ✅
