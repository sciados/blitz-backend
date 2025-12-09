# Features & Benefits by Tier & User Type

## Overview
This document tracks features, limits, and benefits available to each user type and subscription tier. Use this to highlight upgrade benefits and guide users to the right plan.

---

## Quick Reference - Top Upgrade Triggers

| Feature | Starter | Pro | Enterprise | Upgrade Trigger |
|---------|---------|-----|------------|-----------------|
| **Videos/Month** | 5 | 50 | 200 | Users hit 5 videos quickly |
| **Video Length** | 10s max | 60s max | 60s+ | Need longer videos |
| **Campaigns** | 3 | 15 | 100 | Growing business |
| **Images/Month** | 10 | 100 | 500 | Heavy content creation |
| **Conversion Tracking** | ❌ | ✅ | ✅ | Need ROI data |
| **API Access** | ❌ | ✅ | ✅ | Integration needs |

---

## Implementation Status Summary

| Component | Status | Action Needed |
|-----------|--------|---------------|
| Tier Logic | 🔄 Partial | Fix tier retrieval from DB |
| Usage Tracking | 📋 Not Started | Build tracking tables |
| Billing | 📋 Not Started | Integrate Stripe |
| Upgrade UI | 📋 Not Started | Add prompts/meters |
| Enforcement | ⚠️ Hardcoded | Wire to real user data |

**Last Updated:** 2025-12-09
**Next Review:** After Phase 1 implementation

---

## User Types

### 🚀 Affiliate/Marketer (Default)
**Profile:** Promoting others' products, building affiliate income
**Primary Needs:** Content generation, campaign management, analytics

### 🎯 Creator (Product Developer)
**Profile:** Creating and selling their own products
**Primary Needs:** Product library, analytics, intelligence, networking

### 💼 Business Owner
**Profile:** Running their own business campaigns
**Primary Needs:** Campaign management, content generation, compliance

### 👑 Admin
**Profile:** Platform administrators
**Primary Needs:** Full system access, user management, configuration

---

## Subscription Tiers

### 🆓 Starter - $7/month
**Target:** New users, hobbyists, testing
**Limits:** Aggressive cost control, basic features

### ⭐ Pro - $29/month
**Target:** Serious marketers, small businesses
**Benefits:** Higher limits, premium features, priority support

### 💎 Enterprise - Custom
**Target:** Agencies, large businesses, power users
**Benefits:** Maximum limits, white-label options, dedicated support

---

## Feature Matrix

### 📝 CONTENT GENERATION

| Feature | Starter | Pro | Enterprise | Notes |
|---------|---------|-----|------------|-------|
| **Text Content** | ✅ Unlimited | ✅ Unlimited | ✅ Unlimited | Core feature for all |
| **Image Generation** | 10/month | 100/month | 500/month | Resets monthly |
| **Video Generation** | 5 videos | 50 videos | 200 videos | Per month |
| - Video Duration | 5-10 seconds | 5-60 seconds | 5-60 seconds | Max per video |
| - Providers | Hunyuan Fast | Hunyuan + WanX | All providers | Quality/cost tiers |
| **Content Library** | 100 items | 1,000 items | 10,000 items | Storage limit |

### 📊 CAMPAIGNS

| Feature | Starter | Pro | Enterprise | Notes |
|---------|---------|-----|------------|-------|
| **Active Campaigns** | 3 | 15 | 100 | Concurrent campaigns |
| **Campaign Analytics** | Basic | Advanced | Advanced + Export | Dashboard features |
| **Conversion Tracking** | ❌ | ✅ | ✅ | Revenue attribution |
| **A/B Testing** | ❌ | ❌ | ✅ | Split testing |

### 🧠 INTELLIGENCE & AI

| Feature | Starter | Pro | Enterprise | Notes |
|---------|---------|-----|------------|-------|
| **Intelligence Compilation** | 5/month | 50/month | 200/month | Product research |
| **RAG Queries** | 20/month | 200/month | 1000/month | Knowledge base |
| **Product Library Size** | 10 products | 100 products | 1000 products | Storage |

### 📈 ANALYTICS

| Feature | Starter | Pro | Enterprise | Notes |
|---------|---------|-----|------------|-------|
| **Dashboard** | ✅ | ✅ | ✅ | All tiers |
| **Export Data** | ❌ | CSV | CSV + API | Data portability |
| **Historical Data** | 30 days | 1 year | 3 years | Retention period |
| **Custom Reports** | ❌ | ❌ | ✅ | White-label reports |

### 💬 MESSAGING

| Feature | Starter | Pro | Enterprise | Notes |
|---------|---------|-----|------------|-------|
| **Messages** | 50/month | 500/month | 5000/month | Outbound messages |
| **Message Requests** | ✅ | ✅ | ✅ | Incoming requests |
| **Templates** | 5 | 50 | 500 | Email templates |
| **Automation** | ❌ | Basic | Advanced | Workflow automation |

### 🛡️ COMPLIANCE

| Feature | Starter | Pro | Enterprise | Notes |
|---------|---------|-----|------------|-------|
| **FTC Compliance Check** | ✅ | ✅ | ✅ | Content validation |
| **Auto-Fix** | ❌ | ✅ | ✅ | Fix common issues |
| **Custom Rules** | ❌ | ❌ | ✅ | Brand-specific rules |

### 🔌 INTEGRATIONS

| Feature | Starter | Pro | Enterprise | Notes |
|---------|---------|-----|------------|-------|
| **API Access** | ❌ | ✅ | ✅ | REST API |
| **Webhook Support** | ❌ | Basic | Advanced | Real-time updates |
| **Zapier** | ❌ | ❌ | ✅ | Automation platform |
| **White-label** | ❌ | ❌ | ✅ | Custom branding |

### 💳 BILLING & COMMERCE

| Feature | Starter | Pro | Enterprise | Notes |
|---------|---------|-----|------------|-------|
| **Affiliate Commissions** | ✅ | ✅ | ✅ | Revenue sharing |
| **Revenue Tracking** | Basic | Advanced | Advanced | Detailed analytics |
| **Payout Schedule** | Monthly | Weekly | Weekly | Payment timing |

### 👥 NETWORKING

| Feature | Starter | Pro | Enterprise | Notes |
|---------|---------|-----|------------|-------|
| **Affiliate Network** | ✅ | ✅ | ✅ | Connect with others |
| **Product Marketplace** | ✅ | ✅ | ✅ | Browse products |
| **Direct Messages** | 20/month | 200/month | 1000/month | Networking |

### 🎨 CUSTOMIZATION

| Feature | Starter | Pro | Enterprise | Notes |
|---------|---------|-----|------------|-------|
| **Custom Domains** | ❌ | ❌ | ✅ | White-label |
| **Custom Branding** | ❌ | ❌ | ✅ | Logo, colors |
| **Custom Reports** | ❌ | ❌ | ✅ | PDF/Email reports |

### 🆘 SUPPORT

| Feature | Starter | Pro | Enterprise | Notes |
|---------|---------|-----|------------|-------|
| **Documentation** | ✅ | ✅ | ✅ | Self-service |
| **Email Support** | 48h response | 24h response | 4h response | SLA |
| **Priority Queue** | ❌ | ✅ | ✅ | Faster processing |
| **Dedicated Manager** | ❌ | ❌ | ✅ | Account manager |

---

## Upgrade Prompts by User Type

### 🚀 Affiliate/Marketer

**Starter → Pro:**
> "Upgrade to Pro for **10x more content** (100 images, 50 videos) and **unlock conversion tracking** to see which content actually makes money!"

**Pro → Enterprise:**
> "Scale to Enterprise for **200 videos/month**, **A/B testing**, and **API access** to integrate with your existing marketing stack."

### 🎯 Creator

**Starter → Pro:**
> "Grow your product business with **50 intelligence compilations/month**, **advanced analytics**, and **100 product library** slots."

**Pro → Enterprise:**
> "Go white-label with **custom domains**, **dedicated support**, and **3 years of data retention** for deep insights."

### 💼 Business

**Starter → Pro:**
> "Professional plan includes **15 campaigns**, **video generation up to 60 seconds**, and **compliance auto-fix** for worry-free marketing."

**Pro → Enterprise:**
> "Enterprise gives you **100 campaigns**, **custom branding**, and **API access** to build Blitz into your workflow."

---

## Current Implementation Status

### ✅ Fully Implemented & Enforced

**Video Generation:**
- ✅ Tier-based duration limits (Starter: 10s, Pro: 60s, Enterprise: 60s+)
- ✅ Provider selection based on tier
- ✅ Upgrade prompts when limits exceeded

**Database:**
- ✅ `affiliate_tier` field in User model (default: "standard")
- ✅ `stripe_subscription_id` for premium tracking
- ✅ All tables created and functional

### 🔄 Partially Implemented (Needs Work)

**Video Generation:**
- ⚠️ Currently hardcoded to `user_tier = "starter"` (line 740 in app/api/video.py)
- ⚠️ No actual user tier retrieval from database
- ⚠️ No usage tracking/limit enforcement

**Tier Values Mismatch:**
- ❌ Code expects: "starter", "pro", "enterprise"
- ❌ Database has: "standard", "pro" (for affiliate_tier)
- ❌ Needs mapping layer or field standardization

### 📋 Not Yet Implemented

**Usage Tracking:**
- Monthly limits tracking (images, videos, campaigns)
- Reset logic (monthly/annually)
- Overage billing
- Usage dashboard

**Upgrade Prompts:**
- In-UI upgrade prompts when limits hit
- Usage meters/progress bars
- Tier comparison modals
- Billing integration (Stripe)

**Advanced Features:**
- Conversion tracking (Pro+)
- A/B testing (Enterprise)
- API access (Pro+)
- Custom branding (Enterprise)
- Data export (Pro+)

---

## Priority Implementation Order

### Phase 1: Fix Tier System (Week 1)
1. Standardize tier field values across code
2. Implement user tier retrieval from database
3. Add usage tracking tables
4. Wire up tier checking in video generation

### Phase 2: Usage Tracking (Week 2-3)
1. Create usage tables (monthly counts)
2. Track: images generated, videos generated, campaigns created
3. Add monthly reset logic
4. Build usage dashboard

### Phase 3: Billing Integration (Week 3-4)
1. Integrate Stripe for subscription management
2. Add upgrade flow in UI
3. Implement upgrade prompts
4. Add payment processing

### Phase 4: Advanced Features (Month 2)
1. Conversion tracking
2. API access
3. Advanced analytics
4. Custom branding (Enterprise)

---

## Implementation Notes

### Database Schema
```python
# Current User model fields:
affiliate_tier = Column(String(20), default="standard")  # ❌ Needs mapping
stripe_subscription_id = Column(String(255))  # ✅ Good for billing

# Code expects:
user_tier = "starter" | "pro" | "enterprise"  # ❌ Different from DB
```

### Recommended Fix
**Option A: Map existing field**
```python
def get_user_tier(user):
    tier_map = {
        "standard": "starter",
        "pro": "pro",
        "premium": "enterprise"
    }
    return tier_map.get(user.affiliate_tier, "starter")
```

**Option B: Add new field**
```python
subscription_tier = Column(String(20), default="starter")  # Clear separation
```

**Recommendation:** Option B - Add new `subscription_tier` field to avoid conflicts with existing `affiliate_tier` logic.

---

## Revenue Impact

### High-Value Features (Drive Upgrades)
1. **Video Generation Limits** - Users hit this quickly, clear upgrade path
2. **Campaign Limits** - Businesses need more, natural upgrade trigger
3. **Conversion Tracking** - Only Pro+, shows ROI
4. **API Access** - Power users need this, high-value feature

### Retention Features (Keep Users)
1. **Content Library** - Users don't want to lose their work
2. **Analytics History** - More valuable over time
3. **Network Size** - Harder to leave once established
4. **Custom Templates** - Personalized workflow investment

---

## Usage Tracking Recommendations

Track these metrics to identify upgrade opportunities:
- Content generation usage (vs. limit)
- Campaign count (vs. limit)
- Video generation attempts (vs. limit)
- Intelligence compilation requests
- Messages sent
- Product library size
- Analytics data retention needed

**Trigger upgrade prompts** when users hit 80% of their limits!

---

## Next Steps

1. ✅ Implement tier checks in video generation
2. ✅ Add upgrade prompts in UI when limits approached
3. ✅ Create billing integration with Stripe
4. ✅ Build upgrade flow in user settings
5. ✅ Add usage dashboard to show current consumption
6. ✅ Implement overage billing (optional)
