# 🚀 Deploy Campaign Creation Feature - Quick Start

## What's Ready to Deploy

✅ Backend campaign model with new fields (keywords, product_description, product_type)
✅ Backend API endpoint updated
✅ Database migration ready (002_add_campaign_fields.py)
✅ Frontend campaign creation modal
✅ Frontend campaigns list page
✅ Form validation with Zod
✅ Full error handling

## Deploy in 4 Steps

### Step 1: Deploy Backend to Railway

```bash
cd C:\Users\shaun\OneDrive\Documents\GitHub\blitz-backend

git add .
git commit -m "feat: add campaign creation fields (keywords, product_description, product_type)"
git push origin main
```

✅ Railway will auto-deploy

### Step 2: Run Database Migration

```bash
# Install Railway CLI if not already installed:
# npm i -g @railway/cli

railway login
railway link  # Link to your blitz-backend project
railway run python migrate.py upgrade
```

Expected output:
```
INFO  [alembic.runtime.migration] Running upgrade 001 -> 002, add campaign fields
```

### Step 3: Deploy Frontend to Vercel

```bash
cd C:\Users\shaun\OneDrive\Documents\GitHub\blitz-frontend

git add .
git commit -m "feat: add campaign creation modal with all fields"
git push origin main
```

✅ Vercel will auto-deploy

### Step 4: Test Production

**Your URLs:**
- Backend: https://blitzed.up.railway.app
- Frontend: (Your Vercel URL)

1. Go to your Vercel URL
2. Login
3. Click "Campaigns"
4. Click "Create Campaign"
5. Fill out form and submit
6. Verify campaign appears in list

**Quick API Test:**
```bash
# Test backend health
curl https://blitzed.up.railway.app/health

# Should return:
# {"status":"healthy","database":"connected","timestamp":...}
```

## Verification Checklist

Backend (Railway):
- [ ] Deployment succeeded in Railway dashboard
- [ ] Migration ran successfully (check logs)
- [ ] Health check responding: https://blitzed.up.railway.app/health

Frontend (Vercel):
- [ ] Deployment succeeded in Vercel dashboard
- [ ] Campaign page loads
- [ ] "Create Campaign" button works
- [ ] Modal displays all fields
- [ ] Form submission works
- [ ] New campaign displays in list

## If Something Goes Wrong

### Migration Failed?
```bash
# Check current migration status
railway run python migrate.py current

# If stuck, check Railway logs
railway logs
```

### Frontend Not Showing Changes?
1. Hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
2. Check Vercel deployment logs
3. Verify `NEXT_PUBLIC_API_BASE_URL` environment variable in Vercel

### API Errors?
1. Check Railway logs: `railway logs`
2. Verify CORS settings include your Vercel domain
3. Test API directly with curl (see CAMPAIGN_CREATION_GUIDE.md)

## Environment Variables to Verify

### Railway Backend
- `DATABASE_URL` (auto-set by Railway PostgreSQL)
- `JWT_SECRET_KEY`
- `JWT_ALGORITHM=HS256`
- `ACCESS_TOKEN_EXPIRE_MINUTES=1440`

### Vercel Frontend
- `NEXT_PUBLIC_API_BASE_URL=https://blitzed.up.railway.app`

## Documentation

- **[DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)** - Complete deployment instructions
- **[CAMPAIGN_CREATION_GUIDE.md](./CAMPAIGN_CREATION_GUIDE.md)** - Feature documentation and testing
- **[CAMPAIGNFORGE_COMPARISON.md](./CAMPAIGNFORGE_COMPARISON.md)** - Architecture decisions
- **[PRODUCTION_URLS.md](./PRODUCTION_URLS.md)** - Production URLs and API endpoints
- **[endpoints.json](./endpoints.json)** - OpenAPI specification

## What's Next After Deployment

Once campaign creation is working in production, you can implement:

1. **Campaign Detail Page** - View and edit individual campaigns
2. **Intelligence Compilation** - Analyze sales pages automatically
3. **Content Generation** - Generate marketing content for campaigns
4. **Compliance Checking** - Validate content against FTC guidelines

## Support Commands

```bash
# View Railway logs
railway logs

# Check migration status
railway run python migrate.py current

# Rollback migration (if needed)
railway run python migrate.py downgrade -1

# Test API endpoints
curl https://blitzed.up.railway.app/health
curl https://blitzed.up.railway.app/
```

---

**Ready to deploy?** Start with Step 1 above! 🚀
