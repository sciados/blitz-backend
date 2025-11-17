# Blitz Documentation

This folder contains all project documentation for the Blitz marketing automation platform.

## 📚 Documentation Index

### Getting Started

- **[DEPLOY_NOW.md](./DEPLOY_NOW.md)** - Quick deployment checklist for Vercel and Railway
  - 4-step deployment process
  - Verification checklist
  - Quick troubleshooting

### Deployment & Operations

- **[DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)** - Complete deployment guide
  - Detailed Vercel deployment instructions
  - Railway backend deployment
  - Database migration procedures
  - Environment variables setup
  - Monitoring and rollback procedures

- **[PRODUCTION_URLS.md](./PRODUCTION_URLS.md)** - Production environment reference
  - Backend URL: https://blitzed.up.railway.app
  - All API endpoints with examples
  - Environment variables
  - Quick test commands
  - Troubleshooting guide

### Features

- **[CAMPAIGN_CREATION_GUIDE.md](./CAMPAIGN_CREATION_GUIDE.md)** - Campaign creation feature
  - Feature documentation
  - Required and optional fields
  - API documentation
  - Testing procedures
  - Form validation rules

### Architecture

- **[CAMPAIGNFORGE_COMPARISON.md](./CAMPAIGNFORGE_COMPARISON.md)** - Architecture reference
  - Comparison with original CampaignForge
  - What was removed and why
  - Complexity reduction metrics (91% backend, 73% frontend)
  - What NOT to copy from CampaignForge
  - Migration checklist

### API Reference

- **[endpoints.json](./endpoints.json)** - OpenAPI 3.1.0 specification
  - Complete API documentation
  - All endpoints with request/response schemas
  - Authentication flows
  - Data models and validation rules

## 🚀 Quick Links

**Deployment:**
- [Deploy in 4 steps](./DEPLOY_NOW.md)
- [Complete deployment guide](./DEPLOYMENT_GUIDE.md)

**Development:**
- [Campaign creation feature](./CAMPAIGN_CREATION_GUIDE.md)
- [Production URLs & testing](./PRODUCTION_URLS.md)

**Architecture:**
- [CampaignForge comparison](./CAMPAIGNFORGE_COMPARISON.md)
- [API specification](./endpoints.json)

## 🏗️ Project Structure

```
blitz-frontend/
├── docs/                          # ← You are here
│   ├── README.md                  # This file
│   ├── DEPLOY_NOW.md              # Quick start deployment
│   ├── DEPLOYMENT_GUIDE.md        # Detailed deployment
│   ├── CAMPAIGN_CREATION_GUIDE.md # Campaign feature docs
│   ├── PRODUCTION_URLS.md         # API endpoints & URLs
│   ├── CAMPAIGNFORGE_COMPARISON.md # Architecture reference
│   └── endpoints.json             # OpenAPI spec
├── src/
│   ├── app/                       # Next.js app directory
│   ├── components/                # React components
│   └── lib/                       # Utilities and types
├── CLAUDE.md                      # Main development guide
└── README.md                      # Project README

blitz-backend/
├── app/
│   ├── api/                       # API routes
│   ├── db/                        # Database models
│   ├── services/                  # Business logic
│   └── core/                      # Core utilities
├── alembic/                       # Database migrations
└── migrate.py                     # Migration runner
```

## 🔗 Related Links

- **Frontend Repository:** `C:\Users\shaun\OneDrive\Documents\GitHub\blitz-frontend`
- **Backend Repository:** `C:\Users\shaun\OneDrive\Documents\GitHub\blitz-backend`
- **Production Backend:** https://blitzed.up.railway.app
- **Production Frontend:** (Your Vercel URL)

## 📖 Documentation Standards

When updating documentation:

1. **Keep URLs updated** - Reference https://blitzed.up.railway.app for backend
2. **Include examples** - Provide curl commands and code snippets
3. **Cross-reference** - Link to related documentation
4. **Update index** - Add new docs to this README.md
5. **Test instructions** - Verify all commands work

## 🆘 Need Help?

1. Check [DEPLOY_NOW.md](./DEPLOY_NOW.md) for quick deployment
2. Review [PRODUCTION_URLS.md](./PRODUCTION_URLS.md) for API testing
3. See [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) for troubleshooting
4. Reference [endpoints.json](./endpoints.json) for API details

---

**Last Updated:** 2025-01-30
**Documentation Version:** 1.0.0
