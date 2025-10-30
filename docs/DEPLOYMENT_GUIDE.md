# Blitz Campaign Creation - Deployment Guide (Vercel & Railway)

## Overview

This guide covers deploying the campaign creation updates to your production environment:
- **Frontend**: Vercel
- **Backend**: Railway (with PostgreSQL)

## Pre-Deployment Checklist

- [x] Backend models updated with new fields
- [x] Backend schemas updated
- [x] API endpoints updated
- [x] Database migration created
- [x] Frontend types updated
- [x] Campaign creation modal built
- [x] Campaigns page integrated

## Backend Deployment (Railway)

### Step 1: Commit Changes

```bash
cd C:\Users\shaun\OneDrive\Documents\GitHub\blitz-backend

# Check what files changed
git status

# Add all changes
git add .

# Commit changes
git commit -m "Add campaign creation fields (keywords, product_description, product_type)"
```

### Step 2: Push to Repository

```bash
git push origin main
```

Railway will automatically detect the push and start deploying.

### Step 3: Run Database Migration on Railway

**Option A: Using Railway CLI**

```bash
# Install Railway CLI if not already installed
# npm i -g @railway/cli

# Login to Railway
railway login

# Link to your project
railway link

# Run migration
railway run python migrate.py upgrade
```

**Option B: Using Railway Dashboard**

1. Go to https://railway.app
2. Open your `blitz-backend` project
3. Click on your service
4. Go to "Settings" tab
5. Scroll to "Deploy"
6. Click "Deploy" to trigger a new deployment
7. Once deployed, go to "Deployments" tab
8. Click on the active deployment
9. Click "View Logs"
10. In a new terminal, run:

```bash
railway run python migrate.py upgrade
```

Or add a one-time command in Railway dashboard:
- Go to Settings → One-off Commands
- Add command: `python migrate.py upgrade`
- Execute

**Option C: Add Migration to Startup (Recommended)**

Update your Railway start command to run migrations automatically:

1. Go to Railway Dashboard → Your Service → Settings
2. Find "Start Command"
3. Update to:
```bash
python migrate.py upgrade && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

This ensures migrations run on every deployment.

### Step 4: Verify Migration

Check Railway logs to confirm migration succeeded:

```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade 001 -> 002, add campaign fields
```

### Step 5: Test Backend API

Test the API endpoint on Railway:

```bash
# Replace YOUR_RAILWAY_URL with your actual Railway backend URL
# Example: https://blitz-backend-production.up.railway.app

curl -X POST https://YOUR_RAILWAY_URL/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-email@example.com",
    "password": "your-password"
  }'

# Save the access_token from response

curl -X POST https://YOUR_RAILWAY_URL/api/campaigns \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "name": "Test Campaign",
    "product_url": "https://example.com/product",
    "affiliate_network": "ClickBank",
    "keywords": ["test", "campaign"],
    "product_description": "Test description",
    "product_type": "Digital Product"
  }'
```

## Frontend Deployment (Vercel)

### Step 1: Commit Changes

```bash
cd C:\Users\shaun\OneDrive\Documents\GitHub\blitz-frontend

# Check what files changed
git status

# Add all changes
git add .

# Commit changes
git commit -m "Add campaign creation modal with keywords, product type, and description"
```

### Step 2: Push to Repository

```bash
git push origin main
```

Vercel will automatically detect the push and start deploying.

### Step 3: Verify Deployment

1. Go to https://vercel.com
2. Open your `blitz-frontend` project
3. Check the deployment status
4. Once deployed, click "Visit" to open your production site

### Step 4: Test Frontend

1. Navigate to your production URL (e.g., https://blitz-frontend.vercel.app)
2. Login with your credentials
3. Click "Campaigns" in the sidebar
4. Click "Create Campaign" button
5. Fill out the form with all fields
6. Submit and verify campaign appears in the list

## Environment Variables

### Backend (Railway)

Ensure these environment variables are set in Railway Dashboard:

```bash
# Database (automatically set by Railway if using Railway PostgreSQL)
DATABASE_URL=postgresql://...

# JWT Settings
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# API Keys (if using AI features)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
COHERE_API_KEY=...
GROQ_API_KEY=gsk_...

# Cloudflare R2 (if using media storage)
CLOUDFLARE_R2_ACCOUNT_ID=...
CLOUDFLARE_R2_ACCESS_KEY_ID=...
CLOUDFLARE_R2_SECRET_ACCESS_KEY=...
CLOUDFLARE_R2_BUCKET_NAME=...

# Environment
ENVIRONMENT=production
DEBUG=false
```

### Frontend (Vercel)

Ensure this environment variable is set in Vercel Dashboard:

```bash
# Backend API URL (your Railway backend URL)
NEXT_PUBLIC_API_BASE_URL=https://your-backend.up.railway.app
```

To set in Vercel:
1. Go to Vercel Dashboard
2. Select your project
3. Go to Settings → Environment Variables
4. Add/Update `NEXT_PUBLIC_API_BASE_URL`
5. Redeploy if already deployed

## Deployment Verification Checklist

### Backend (Railway)

- [ ] Code pushed to GitHub
- [ ] Railway auto-deployed successfully
- [ ] Database migration completed (002_add_campaign_fields.py)
- [ ] API health check responding: `GET https://YOUR_RAILWAY_URL/health`
- [ ] New fields visible in database:
  ```sql
  SELECT column_name
  FROM information_schema.columns
  WHERE table_name = 'campaigns'
  AND column_name IN ('keywords', 'product_description', 'product_type');
  ```
- [ ] Campaign creation endpoint working: `POST /api/campaigns`

### Frontend (Vercel)

- [ ] Code pushed to GitHub
- [ ] Vercel auto-deployed successfully
- [ ] Environment variable set correctly
- [ ] Can access campaigns page
- [ ] "Create Campaign" button visible
- [ ] Modal opens and displays all fields
- [ ] Form validation working
- [ ] Campaign creation successful
- [ ] New campaign appears in list with all fields

## Rollback Instructions

### If Backend Deployment Fails

**Rollback Migration:**
```bash
railway run python migrate.py downgrade -1
```

**Rollback Code:**
1. Go to Railway Dashboard
2. Go to Deployments
3. Click on previous working deployment
4. Click "Redeploy"

### If Frontend Deployment Fails

**Rollback in Vercel:**
1. Go to Vercel Dashboard
2. Go to Deployments
3. Find the last working deployment
4. Click "..." menu → "Promote to Production"

## Common Issues & Solutions

### Issue: Migration Fails on Railway

**Error:** `column "keywords" already exists`

**Solution:**
The migration may have partially run. Check current revision:

```bash
railway run python migrate.py current
```

If it shows `002`, the migration is complete. If columns exist but revision is `001`:

```bash
railway run python migrate.py stamp 002
```

### Issue: 502 Bad Gateway

**Possible Causes:**
1. Backend not fully deployed
2. Database connection issue
3. Migration failed

**Solution:**
1. Check Railway logs
2. Verify DATABASE_URL environment variable
3. Check if migration completed
4. Restart the backend service

### Issue: CORS Error in Frontend

**Error:** `Access to fetch at 'https://...' has been blocked by CORS policy`

**Solution:**
Verify backend CORS settings include your Vercel domain:

In `app/main.py`, ensure:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://blitz-frontend-three.vercel.app",  # Your Vercel domain
        "https://your-custom-domain.com",           # If using custom domain
        "http://localhost:3000"                      # For local dev
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue: Frontend Shows Old Code

**Solution:**
1. Hard refresh browser: `Ctrl + Shift + R` (Windows) or `Cmd + Shift + R` (Mac)
2. Clear browser cache
3. Check Vercel deployment logs to ensure new build deployed
4. Verify git commit was pushed

## Database Backup (Before Migration)

**Recommended:** Backup your Railway PostgreSQL database before running migration:

### Option 1: Railway Dashboard
1. Go to Railway Dashboard
2. Select PostgreSQL service
3. Go to "Data" tab
4. Click "Backup Now"

### Option 2: Manual Backup
```bash
# Get DATABASE_URL from Railway
railway run env | grep DATABASE_URL

# Create backup (replace with your DATABASE_URL)
pg_dump DATABASE_URL > backup_before_campaign_fields.sql
```

## Post-Deployment Testing

### Test Campaign Creation Flow

1. **Login**
   - Go to production URL
   - Login with test account

2. **Navigate to Campaigns**
   - Click "Campaigns" in sidebar
   - Verify page loads

3. **Create Test Campaign**
   - Click "Create Campaign"
   - Fill out form:
     - Title: "Production Test Campaign"
     - URL: "https://example.com/test"
     - Platform: "ClickBank"
     - Keywords: "test, production, verify"
     - Type: "Digital Product"
     - Description: "This is a production test campaign"
   - Click "Create Campaign"

4. **Verify Display**
   - Campaign should appear in list
   - All fields should display correctly
   - Keywords should show as tags
   - Status badge should show "draft"

5. **Verify Database**
   ```bash
   # Connect to Railway PostgreSQL
   railway run psql $DATABASE_URL

   # Query new campaign
   SELECT name, product_type, keywords, product_description
   FROM campaigns
   ORDER BY created_at DESC
   LIMIT 1;
   ```

6. **Test API Directly**
   ```bash
   # Get campaigns via API
   curl -X GET https://YOUR_RAILWAY_URL/api/campaigns \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

## Monitoring

### Railway Metrics
- Go to Railway Dashboard → Metrics
- Monitor:
  - CPU usage
  - Memory usage
  - Network traffic
  - Response times

### Vercel Analytics
- Go to Vercel Dashboard → Analytics
- Monitor:
  - Page views
  - Load times
  - Error rates

### Application Logs

**Backend Logs (Railway):**
```bash
railway logs
```

**Frontend Logs (Vercel):**
- Go to Vercel Dashboard → Deployments → [Your Deployment] → Runtime Logs

## Success Criteria

✅ Backend deployed to Railway
✅ Database migration completed (revision 002)
✅ Frontend deployed to Vercel
✅ Campaign creation modal working
✅ All new fields saving correctly
✅ Campaigns displaying with new fields
✅ No console errors
✅ No API errors

## Support

If you encounter issues:

1. Check Railway logs: `railway logs`
2. Check Vercel deployment logs
3. Verify environment variables in both platforms
4. Test API endpoints directly with curl/Postman
5. Check database schema: `\d campaigns` in psql

## Next Deployment

When you're ready to deploy future updates:

1. Make code changes
2. Commit to git: `git commit -am "Your message"`
3. Push to GitHub: `git push origin main`
4. Railway and Vercel will auto-deploy
5. If database changes needed, create new Alembic migration
6. Run migration on Railway after deployment

---

**Last Updated:** 2025-01-30
**Deployment Environment:** Production (Vercel + Railway)
