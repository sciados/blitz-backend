# Blitz Production URLs & Configuration

## Production Environment

### Backend (Railway)
**URL:** https://blitzed.up.railway.app

**Endpoints:**
- Health Check: `GET https://blitzed.up.railway.app/health`
- API Documentation: `GET https://blitzed.up.railway.app/docs`
- Root: `GET https://blitzed.up.railway.app/`

**Authentication:**
- Login: `POST https://blitzed.up.railway.app/api/auth/login`
- Register: `POST https://blitzed.up.railway.app/api/auth/register`
- Get User: `GET https://blitzed.up.railway.app/api/auth/me`

**Campaigns:**
- List Campaigns: `GET https://blitzed.up.railway.app/api/campaigns`
- Create Campaign: `POST https://blitzed.up.railway.app/api/campaigns`
- Get Campaign: `GET https://blitzed.up.railway.app/api/campaigns/{id}`
- Update Campaign: `PATCH https://blitzed.up.railway.app/api/campaigns/{id}`
- Delete Campaign: `DELETE https://blitzed.up.railway.app/api/campaigns/{id}`
- Campaign Analytics: `GET https://blitzed.up.railway.app/api/campaigns/{id}/analytics`

### Frontend (Vercel)
**URL:** (Your Vercel URL - e.g., https://blitz-frontend-three.vercel.app)

**Pages:**
- Login: `/login`
- Register: `/register`
- Dashboard: `/dashboard`
- Campaigns: `/campaigns`
- Campaign Detail: `/campaigns/{id}`
- Content: `/content`
- Intelligence: `/intelligence`
- Compliance: `/compliance`
- Analytics: `/analytics`
- Settings: `/settings`
- Profile: `/profile`

**Admin Pages:**
- Admin Dashboard: `/admin/dashboard`
- AI Router: `/admin/ai_router`
- Users: `/admin/users`
- API Keys: `/admin/api-keys`

## Environment Variables

### Railway Backend
```bash
# Database (auto-configured by Railway)
DATABASE_URL=postgresql://...

# JWT Configuration
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Optional: AI API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
COHERE_API_KEY=...
GROQ_API_KEY=gsk_...

# Optional: Cloudflare R2
CLOUDFLARE_R2_ACCOUNT_ID=...
CLOUDFLARE_R2_ACCESS_KEY_ID=...
CLOUDFLARE_R2_SECRET_ACCESS_KEY=...
CLOUDFLARE_R2_BUCKET_NAME=blitz-media

# Environment
ENVIRONMENT=production
DEBUG=false
```

### Vercel Frontend
```bash
# Backend API URL
NEXT_PUBLIC_API_BASE_URL=https://blitzed.up.railway.app
```

## Quick Test Commands

### Test Backend Health
```bash
curl https://blitzed.up.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": 1706634000
}
```

### Test Backend Root
```bash
curl https://blitzed.up.railway.app/
```

Expected response:
```json
{
  "status": "healthy",
  "service": "Blitz API",
  "version": "1.0.0",
  "environment": "production"
}
```

### Test Login (Example)
```bash
curl -X POST https://blitzed.up.railway.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "your-password"
  }'
```

Expected response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

### Test Campaign Creation (Authenticated)
```bash
# First, get your token from login above
TOKEN="your-token-here"

curl -X POST https://blitzed.up.railway.app/api/campaigns \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "Test Campaign",
    "product_url": "https://example.com/product",
    "affiliate_network": "ClickBank",
    "keywords": ["test", "demo"],
    "product_description": "This is a test campaign",
    "product_type": "Digital Product"
  }'
```

## CORS Configuration

The backend is configured to accept requests from:
- `https://blitz-frontend-three.vercel.app` (or your Vercel URL)
- `http://localhost:3000` (for local development)

If you have a custom domain, add it to the CORS allow list in `app/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://blitzed.up.railway.app",
        "https://your-custom-domain.com",  # Add your domain
        "http://localhost:3000"
    ],
    ...
)
```

## Database Information

- **Provider:** Railway PostgreSQL
- **Connection:** Via DATABASE_URL environment variable
- **Current Schema Version:** 002 (after campaign fields migration)
- **Migrations Location:** `alembic/versions/`

### Check Migration Status
```bash
railway run python migrate.py current
```

Expected output:
```
002 (head)
```

## Deployment Commands

### Deploy Backend
```bash
cd blitz-backend
git add .
git commit -m "your commit message"
git push origin main
# Railway auto-deploys
```

### Run Migration on Railway
```bash
railway run python migrate.py upgrade
```

### Deploy Frontend
```bash
cd blitz-frontend
git add .
git commit -m "your commit message"
git push origin main
# Vercel auto-deploys
```

## Monitoring

### Railway Dashboard
- View logs: `railway logs`
- View metrics: https://railway.app (CPU, Memory, Network)
- View deployments: Check deployment history

### Vercel Dashboard
- View logs: Vercel Dashboard → Deployments → [Your Deployment] → Runtime Logs
- View analytics: Vercel Dashboard → Analytics
- View builds: Check build logs for each deployment

## Troubleshooting

### Backend Not Responding
1. Check Railway status: https://railway.app
2. View logs: `railway logs`
3. Check DATABASE_URL is set
4. Verify deployment completed successfully

### Frontend Can't Reach Backend
1. Verify `NEXT_PUBLIC_API_BASE_URL=https://blitzed.up.railway.app` in Vercel
2. Check CORS configuration in backend
3. Test backend directly with curl
4. Check browser console for errors

### 401 Unauthorized
- Token may have expired (1440 minutes = 24 hours)
- Re-login to get new token
- Check Authorization header format: `Bearer {token}`

### Database Migration Issues
```bash
# Check current revision
railway run python migrate.py current

# View migration history
railway run python migrate.py history

# Rollback if needed
railway run python migrate.py downgrade -1
```

## Support Contacts

- Railway Support: https://railway.app/help
- Vercel Support: https://vercel.com/support
- Blitz Repository: (Your GitHub repo URLs)

---

**Last Updated:** 2025-01-30
**Backend Version:** 1.0.0
**Frontend Version:** 0.1.0
