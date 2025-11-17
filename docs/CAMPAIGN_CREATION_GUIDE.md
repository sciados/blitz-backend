# Campaign Creation Implementation Guide

## Overview

This guide covers the complete campaign creation functionality that has been implemented in Blitz.

## What's Been Implemented

### Backend Changes

1. **Database Model Updates** (`app/db/models.py`)
   - Added `keywords` (ARRAY of strings)
   - Added `product_description` (TEXT)
   - Added `product_type` (VARCHAR 100)

2. **Schema Updates** (`app/schemas.py`)
   - Updated `CampaignBase` with new fields
   - Updated `CampaignCreate` (inherits from CampaignBase)
   - Updated `CampaignUpdate` with optional new fields

3. **API Endpoint Updates** (`app/api/campaigns.py`)
   - Updated `create_campaign` to handle new fields
   - All CRUD operations remain functional

4. **Database Migration** (`alembic/versions/002_add_campaign_fields.py`)
   - Alembic migration to add new columns to campaigns table

### Frontend Changes

1. **Type Definitions** (`src/lib/types.ts`)
   - Updated `Campaign` type with new fields
   - Added `CampaignCreate` type for form submission

2. **Campaign Creation Modal** (`src/components/CreateCampaignModal.tsx`)
   - Full-featured modal with form validation
   - Zod schema validation
   - All required and optional fields
   - Error handling and loading states
   - Keywords input (comma-separated, converted to array)
   - Product type and affiliate network dropdowns

3. **Campaigns Page** (`src/app/campaigns/page.tsx`)
   - Fetches campaigns from API
   - Displays campaigns in a beautiful card layout
   - Shows all campaign details (keywords, type, description, etc.)
   - Modal integration for creating new campaigns
   - Auto-refresh after creation
   - Empty state with CTA button

## Required Fields

### Mandatory (*)
- **Campaign Title** (name): Minimum 3 characters
- **Sales Page URL** (product_url): Valid URL format
- **Affiliate Platform** (affiliate_network): Selected from dropdown

### Optional
- **Keywords**: Comma-separated list (e.g., "weight loss, fitness, health")
- **Product Type**: Selected from dropdown
- **Product Description**: Minimum 10 characters (if provided)
- **Target Audience**: Free text description

## Deployment Steps

**Important:** This project deploys to Vercel (frontend) and Railway (backend).

See **[DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)** for complete deployment instructions including:
- Pushing to GitHub
- Automatic deployment to Railway and Vercel
- Running database migrations on Railway
- Environment variable configuration
- Testing in production
- Rollback procedures

### Quick Deployment Summary

1. **Commit and push backend changes:**
   ```bash
   cd C:\Users\shaun\OneDrive\Documents\GitHub\blitz-backend
   git add .
   git commit -m "Add campaign creation fields"
   git push origin main
   ```

2. **Run migration on Railway:**
   ```bash
   railway run python migrate.py upgrade
   ```

3. **Commit and push frontend changes:**
   ```bash
   cd C:\Users\shaun\OneDrive\Documents\GitHub\blitz-frontend
   git add .
   git commit -m "Add campaign creation modal"
   git push origin main
   ```

4. **Verify deployment:**
   - Backend: Check Railway dashboard for successful deployment
   - Frontend: Check Vercel dashboard for successful deployment
   - Test: Go to your production URL and test campaign creation

## Testing Checklist

### Backend API Testing (Production)

Test the campaign creation endpoint on Railway:

```bash
# Your Railway backend URL: https://blitzed.up.railway.app

# Login first to get token
curl -X POST https://blitzed.up.railway.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-email@example.com",
    "password": "your-password"
  }'

# Create campaign (replace YOUR_TOKEN with actual token)
curl -X POST https://blitzed.up.railway.app/api/campaigns \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "Test Campaign",
    "product_url": "https://example.com/product",
    "affiliate_network": "ClickBank",
    "keywords": ["weight loss", "fitness", "health"],
    "product_description": "This is a test product description",
    "product_type": "Digital Product",
    "target_audience": "People interested in fitness"
  }'
```

### Frontend Testing (Production)

1. **Login to application**
   - Go to your production URL (e.g., https://blitz-frontend.vercel.app/login)
   - Login with your credentials

2. **Navigate to Campaigns**
   - Click "Campaigns" in the sidebar
   - Should see "No campaigns yet" (if first time)

3. **Create a Campaign**
   - Click "Create Campaign" button
   - Fill out the form:
     - Title: "Test Campaign"
     - Sales Page URL: "https://example.com/product"
     - Affiliate Platform: Select "ClickBank"
     - Keywords: "test, campaign, demo"
     - Product Type: Select "Digital Product"
     - Product Description: "This is a test product for testing the campaign creation"
     - Target Audience: "Marketers"
   - Click "Create Campaign"

4. **Verify Success**
   - Modal should close
   - New campaign should appear in the list
   - Campaign card should show:
     - ✅ Title
     - ✅ Status badge (draft)
     - ✅ Product URL
     - ✅ Affiliate network
     - ✅ Product type
     - ✅ Keywords (first 3)
     - ✅ Description
     - ✅ Created date

5. **Test Validation**
   - Click "Create Campaign" again
   - Try to submit with empty fields
   - Should see validation errors
   - Try invalid URL (e.g., "not-a-url")
   - Should see "Please enter a valid URL"

6. **Test Error Handling**
   - Stop the backend server
   - Try to create a campaign
   - Should see error message

## API Documentation

### Create Campaign

**Endpoint:** `POST /api/campaigns`

**Headers:**
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "string (required, min 3 chars)",
  "product_url": "string (required, valid URL)",
  "affiliate_network": "string (required)",
  "keywords": ["string", "string"] (optional array),
  "product_description": "string (optional, min 10 chars if provided)",
  "product_type": "string (optional)",
  "target_audience": "string (optional)"
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "user_id": 1,
  "name": "Test Campaign",
  "product_url": "https://example.com/product",
  "affiliate_network": "ClickBank",
  "keywords": ["test", "campaign"],
  "product_description": "This is a test",
  "product_type": "Digital Product",
  "target_audience": "Marketers",
  "status": "draft",
  "intelligence_data": null,
  "created_at": "2025-01-30T12:00:00Z",
  "updated_at": "2025-01-30T12:00:00Z"
}
```

### List Campaigns

**Endpoint:** `GET /api/campaigns`

**Headers:**
```
Authorization: Bearer {token}
```

**Query Parameters:**
- `skip`: integer (default: 0)
- `limit`: integer (default: 100)

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "name": "Test Campaign",
    ...
  }
]
```

## Form Validation Rules

### Frontend (Zod)
- **name**: Min 3 characters
- **product_url**: Must be valid URL
- **affiliate_network**: Min 1 character
- **product_description**: Min 10 characters (if provided)
- **keywords**: Comma-separated string, converted to array

### Backend (Pydantic)
- **name**: string (required)
- **product_url**: HttpUrl (validates URL format)
- **affiliate_network**: string (required)
- **keywords**: List[str] (optional)
- **product_description**: string (optional)
- **product_type**: string (optional)
- **target_audience**: string (optional)

## Available Options

### Affiliate Networks
1. ClickBank
2. JVZoo
3. WarriorPlus
4. ShareASale
5. Amazon Associates
6. CJ Affiliate
7. Rakuten
8. Impact
9. Awin
10. Other

### Product Types
1. Digital Product
2. Physical Product
3. Software/SaaS
4. Course/Training
5. eBook
6. Membership
7. Service
8. Other

## Troubleshooting

### Migration Fails

**Error:** `Column already exists`

**Solution:**
```bash
# Check current revision
python migrate.py current

# If already at 002, migration already ran
# If at 001, check if columns exist:
psql -d your_database -c "\d campaigns"

# If columns exist but revision is 001, stamp as 002:
python migrate.py stamp 002
```

### Campaign Creation Fails

**Error:** `422 Unprocessable Entity`

**Check:**
1. URL format is correct (must start with http:// or https://)
2. All required fields are filled
3. Product description is at least 10 characters (if provided)

**Error:** `401 Unauthorized`

**Solution:**
1. Check that token is valid
2. Re-login if token expired
3. Check Authorization header format: `Bearer {token}`

### Campaigns Not Showing

**Check:**
1. Backend server is running
2. Database migration completed successfully
3. User is logged in
4. Check browser console for errors
5. Check network tab for API call status

## Next Steps

After campaign creation is working, you can implement:

1. **Campaign Detail Page** (`/campaigns/[id]/page.tsx`)
   - View full campaign details
   - Edit campaign
   - Delete campaign
   - Generate content for campaign

2. **Intelligence Compilation**
   - Analyze sales page URL
   - Extract product information
   - Store in `intelligence_data` JSONB field

3. **Content Generation**
   - Generate marketing content based on campaign data
   - Use keywords and product description
   - Link to campaign via `campaign_id`

4. **Compliance Checking**
   - Check generated content against FTC guidelines
   - Check against affiliate network rules
   - Store compliance status

## File Structure

### Backend
```
blitz-backend/
├── alembic/
│   └── versions/
│       ├── 001_initial_migration.py
│       └── 002_add_campaign_fields.py  ← NEW
├── app/
│   ├── api/
│   │   └── campaigns.py                ← UPDATED
│   ├── db/
│   │   └── models.py                   ← UPDATED
│   └── schemas.py                      ← UPDATED
└── migrate.py
```

### Frontend
```
blitz-frontend/
├── src/
│   ├── app/
│   │   └── campaigns/
│   │       └── page.tsx                ← UPDATED
│   ├── components/
│   │   └── CreateCampaignModal.tsx     ← NEW
│   └── lib/
│       └── types.ts                    ← UPDATED
└── CAMPAIGN_CREATION_GUIDE.md          ← NEW
```

## Summary

✅ **Backend:** Models, schemas, and API updated with new fields
✅ **Database:** Migration created for new columns
✅ **Frontend:** Types, modal component, and page integration complete
✅ **Validation:** Zod (frontend) and Pydantic (backend) validation
✅ **UX:** Beautiful modal with error handling and loading states
✅ **API:** Full CRUD operations for campaigns

The campaign creation functionality is now complete and ready for testing!
