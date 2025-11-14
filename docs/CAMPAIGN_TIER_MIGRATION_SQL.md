# Campaign Tier Migration SQL
## Update tier_configs with New Campaign-Based Limits

---

## SQL UPDATE QUERIES

```sql
-- =====================================================
-- UPDATE FREE TIER (30-DAY TRIAL)
-- =====================================================
UPDATE tier_configs
SET
    monthly_price = 0.00,
    max_campaigns = 1,
    words_per_month = 12000,           -- 1 campaign × 12K words
    words_per_day = 400,               -- 12000 ÷ 30 days
    words_per_generation = 2000,
    images_per_month = 20,              -- 1 campaign × 20 images (limited)
    videos_per_month = 2,               -- 1 campaign × 2 videos (limited)
    overage_rate_per_1k_words = 0.50
WHERE tier_name = 'free';

-- NOTE: Trial duration (30 days) should be handled in application logic
-- or add trial_duration_days field to tier_configs table

-- =====================================================
-- UPDATE STARTER TIER
-- =====================================================
UPDATE tier_configs
SET
    monthly_price = 25.00,
    max_campaigns = 5,
    words_per_month = 60000,            -- 5 campaigns × 12K words
    words_per_day = 2000,               -- 60000 ÷ 30 days
    words_per_generation = 5000,
    images_per_month = 400,             -- 5 campaigns × 80 images
    videos_per_month = 100,             -- 5 campaigns × 20 videos
    overage_rate_per_1k_words = 0.25,
    features = '["all_templates", "email_sequences", "priority_support", "compliance_check"]'
WHERE tier_name = 'starter';

-- =====================================================
-- UPDATE PRO TIER
-- =====================================================
UPDATE tier_configs
SET
    monthly_price = 79.00,
    max_campaigns = 12,
    words_per_month = 144000,           -- 12 campaigns × 12K words
    words_per_day = 4800,               -- 144000 ÷ 30 days
    words_per_generation = 10000,
    images_per_month = 960,             -- 12 campaigns × 80 images
    videos_per_month = 240,             -- 12 campaigns × 20 videos
    overage_rate_per_1k_words = 0.20,
    features = '["advanced_templates", "analytics", "api_access", "content_variations"]'
WHERE tier_name = 'pro';

-- =====================================================
-- UPDATE ENTERPRISE TIER
-- =====================================================
UPDATE tier_configs
SET
    monthly_price = 249.00,
    max_campaigns = 40,
    words_per_month = 480000,           -- 40 campaigns × 12K words
    words_per_day = 16000,              -- 480000 ÷ 30 days
    words_per_generation = 16000,
    images_per_month = 3200,            -- 40 campaigns × 80 images
    videos_per_month = 800,             -- 40 campaigns × 20 videos
    overage_rate_per_1k_words = 0.15,
    features = '["white_label", "custom_integrations", "dedicated_support", "priority_features"]'
WHERE tier_name = 'enterprise';
```

---

## VERIFICATION QUERY

```sql
-- Verify the updates
SELECT
    tier_name,
    display_name,
    monthly_price,
    max_campaigns,
    words_per_month,
    images_per_month,
    videos_per_month,
    overage_rate_per_1k_words
FROM tier_configs
ORDER BY monthly_price;
```

**Expected Output:**
```
tier_name  | display_name | monthly_price | max_campaigns | words_per_month | images_per_month | videos_per_month | notes
-----------|--------------|---------------|---------------|-----------------|------------------|------------------|------------------
free       | Free         | 0.00          | 1             | 12000           | 20               | 2                | 30-day trial
starter    | Starter      | 25.00         | 5             | 60000           | 400              | 100              | monthly
pro        | Pro          | 79.00         | 12            | 144000          | 960              | 240              | monthly
enterprise | Enterprise   | 249.00        | 40            | 480000          | 3200             | 800              | monthly
```

---

## BACKUP QUERY (Before Changes)

```sql
-- Create backup of current tiers
CREATE TABLE tier_configs_backup_20241114 AS
SELECT * FROM tier_configs;

-- Verify backup created
SELECT COUNT(*) as backup_count FROM tier_configs_backup_20241114;
```

---

## ROLLBACK QUERY (If Needed)

```sql
-- Restore from backup
UPDATE tier_configs
SET monthly_price = backup.monthly_price,
    max_campaigns = backup.max_campaigns,
    words_per_month = backup.words_per_month,
    words_per_day = backup.words_per_day,
    words_per_generation = backup.words_per_generation,
    images_per_month = backup.images_per_month,
    videos_per_month = backup.videos_per_month,
    overage_rate_per_1k_words = backup.overage_rate_per_1k_words,
    features = backup.features
FROM tier_configs_backup_20241114 backup
WHERE tier_configs.tier_name = backup.tier_name;
```

---

## MIGRATION CHECKLIST

### Before Running:
- [ ] ✅ Create backup table
- [ ] ✅ Test on staging environment
- [ ] ✅ Verify rollback script works

### After Running:
- [ ] ✅ Run verification query
- [ ] ✅ Check frontend displays correct pricing
- [ ] ✅ Test user creation with new tiers
- [ ] ✅ Verify usage calculations
- [ ] ✅ Update documentation
- [ ] ✅ Notify team

---

## ALTERNATIVE PRICING (Premium)

If you want higher margins, use these prices instead:

```sql
-- STARTER PREMIUM
UPDATE tier_configs SET monthly_price = 29.00 WHERE tier_name = 'starter';

-- PRO PREMIUM
UPDATE tier_configs SET monthly_price = 119.00 WHERE tier_name = 'pro';

-- ENTERPRISE PREMIUM
UPDATE tier_configs SET monthly_price = 349.00 WHERE tier_name = 'enterprise';
```

---

## 30-DAY TRIAL HANDLING

### Option 1: Application Logic (Recommended)
Store trial start/end dates in user record:
```sql
-- Add to users table (if not exists)
ALTER TABLE users ADD COLUMN trial_start_date TIMESTAMP;
ALTER TABLE users ADD COLUMN trial_end_date TIMESTAMP;
ALTER TABLE users ADD COLUMN trial_used BOOLEAN DEFAULT FALSE;

-- On signup, set trial dates
UPDATE users
SET trial_start_date = NOW(),
    trial_end_date = NOW() + INTERVAL '30 days',
    trial_used = TRUE
WHERE id = ? AND trial_used = FALSE;
```

### Option 2: Add Field to tier_configs
```sql
ALTER TABLE tier_configs ADD COLUMN trial_duration_days INTEGER;

UPDATE tier_configs SET trial_duration_days = 30 WHERE tier_name = 'free';
```

**Recommendation:** Use Option 1 (application logic) for flexibility

---

## FRONTEND CONSIDERATIONS

### Display Changes Needed:
1. **Campaign Count:** Show "X of Y campaigns used"
2. **Upgrade Prompts:** "Upgrade to Pro for 12 campaigns"
3. **Usage Dashboard:** Per-campaign tracking
4. **Pricing Page:** Campaign-based pricing display

### User Messaging:
- "Manage up to 5 campaigns"
- "Perfect for small businesses with multiple products"
- "12 campaigns = agency-level content production"

---

## IMPLEMENTATION TIMELINE

### Phase 1: Database Update (Day 1)
- Run SQL migration
- Verify changes
- Test on staging

### Phase 2: Frontend Updates (Days 2-3)
- Update pricing display
- Update usage tracking
- Add campaign management UI

### Phase 3: Communication (Days 4-7)
- Email existing users
- Update landing page
- Announcement blog post

### Phase 4: Go Live (Day 8)
- Deploy to production
- Monitor for issues
- Gather feedback

---

## SUCCESS METRICS

### User Metrics:
- Conversion rate to paid tiers
- Average campaigns per user
- Upgrade rate from Starter to Pro

### Financial Metrics:
- Revenue per tier
- Gross margin per user
- Customer acquisition cost (CAC) vs lifetime value (LTV)

### Engagement Metrics:
- Campaign completion rate
- Content generation frequency
- Feature usage by tier

---

## NOTES

1. **Backward Compatibility:** Existing users get 60-day grace period
2. **Pricing Display:** Frontend automatically updates via API
3. **Usage Calculation:** Based on max_campaigns, not words
4. **Overage Billing:** Can be implemented later
5. **Feature Flags:** Control rollout by tier

---

**Migration is ready to implement!** 🚀
