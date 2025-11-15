# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Blitz is a **streamlined marketing automation platform** built with Next.js 14, featuring campaign management, AI content generation, intelligence/RAG features, compliance checking, and analytics. The frontend communicates with a FastAPI backend.

**Important Context:** Blitz is a simplified rewrite of CampaignForge, removing 91% of backend complexity and 73% of frontend dependencies while maintaining core functionality. See `docs/CAMPAIGNFORGE_COMPARISON.md` for detailed comparison.

### Key Design Principles

- **Simplicity over abstraction:** Direct implementations instead of complex module systems
- **Monolithic over modular:** Single codebase instead of separate modules
- **JSONB over normalization:** Flexible data storage instead of 20+ tables
- **JWT over sessions:** Simple token-based auth instead of NextAuth
- **Tailwind over component libraries:** Custom styles instead of Radix UI

## Development Commands

```bash
# Install dependencies
npm install

# Run development server (port 3000)
npm run dev

# Build for production
npm build

# Start production server (port 3000)
npm start

# Lint code
npm run lint
```

## Environment Setup

Copy `.env.local.example` to `.env.local` and set:
- `NEXT_PUBLIC_API_BASE_URL`: Backend FastAPI URL (default: http://localhost:8000)

## Architecture

### Authentication & Authorization

- **Token Storage**: JWT tokens stored in localStorage via `src/lib/auth.ts`
- **Role-Based Access**: Two roles - `user` (regular users) and `admin` (administrative access)
- **Token Decoding**: `getRoleFromToken()` and `getUserFromToken()` decode JWT payload to extract role and user info
- **Protected Routes**: Use `AuthGate` component with `requiredRole` prop to protect pages
- **Auto-Redirect**: Axios interceptor in `src/lib/appClient.ts` clears token and redirects to `/login` on 401 responses

### API Client

- **Base Client**: `src/lib/appClient.ts` exports configured axios instance as `api` and `apiClient`
- **Auto-Auth**: Request interceptor adds `Bearer` token from localStorage to all requests
- **Base URL**: Set via `NEXT_PUBLIC_API_BASE_URL` environment variable
- **Backend Routes**: All backend endpoints expected under `/api` prefix

### Layout System

- **Root Layout**: `src/app/layout.tsx` wraps all pages with `ThemeProvider` and `Layout`
- **Main Layout**: `src/components/Layout.tsx` provides:
  - Sticky header with logo and user profile dropdown
  - Collapsible left sidebar with navigation (role-based menu items)
  - Collapsible right sidebar with contextual help
  - User info fetched from `/api/auth/me` on mount
- **Navigation**: Menu items differ based on user role (admin vs user)
  - Admin: Dashboard, AI Router, Users, Settings, Analytics, Compliance, API Keys
  - User: Dashboard, Campaigns, Content, Intelligence, Compliance, Analytics, Settings

### Theme System

- **Theme Provider**: `src/contexts/ThemeContext.tsx` manages light/dark theme
- **Persistence**: Theme choice saved to localStorage
- **CSS Variables**: Theme variables defined in `src/app/globals.css` with `[data-theme="light"]` and `[data-theme="dark"]` selectors
- **Tailwind Integration**: `darkMode: 'class'` in `tailwind.config.js`, class added/removed on `<html>` element
- **Auto-Detection**: Falls back to system preference if no saved theme

### Route Structure

- **Auth Routes**: `/login`, `/register` (in `src/app/(auth)` group)
- **User Routes**: `/dashboard`, `/campaigns`, `/content`, `/intelligence`, `/compliance`, `/analytics`, `/settings`, `/profile`
- **Admin Routes**: `/admin/dashboard`, `/admin/ai_router`, `/admin/users`, `/admin/settings`, `/admin/analytics`, `/admin/compliance`, `/admin/api-keys`
- **Dynamic Routes**: `/campaigns/[id]` for individual campaign pages

### Styling Approach

- **Tailwind CSS**: Primary styling system with custom theme extensions
- **CSS Variables**: Used for theming (colors, backgrounds, borders) - see `globals.css`
- **Card Component**: Reusable `.card` class for consistent card styling across the app
- **Responsive**: Mobile-first design with responsive breakpoints

### TypeScript Types

- **Shared Types**: Defined in `src/lib/types.ts`
- **User Type**: `id`, `email`, `full_name`, `created_at`
- **Campaign Type**: `id`, `name`, `product_url`, `affiliate_network`, `status`, `thumbnail_image_url`, `created_at`, `updated_at`
- Campaign status values: `"draft" | "active" | "paused" | "completed"`

### Product Library & Campaign Integration

The Product Library is a centralized repository of products with pre-compiled intelligence that can be reused across multiple campaigns.

#### Product Library Features

- **Centralized Storage**: Products stored in `ProductIntelligence` table with compiled data
- **Product Cards**: Display thumbnail, name, category, affiliate network, commission rate, times used
- **Product Details Panel**: Full-width sliding panel with comprehensive product information
- **Search & Filter**: Search by name/category, filter by commission type (recurring/one-time), sort by recent/popular/alphabetical
- **Category Organization**: Auto-categorized products with category filtering

#### Campaign-Product Linking

**How Campaigns Get Product Images:**

1. **New Campaigns from Product Library**:
   - Click "Create Campaign" button on Product Details panel
   - Redirects to `/campaigns?productId={id}`
   - Opens Create Campaign modal with product data auto-filled
   - Campaign links to product via `product_intelligence_id`
   - `thumbnail_image_url` fetched from linked ProductIntelligence record

2. **Existing Campaigns Without Products**:
   - Show placeholder icon if no `product_intelligence_id` or `thumbnail_image_url`
   - To add image: Add product to library (product URL must match campaign URL)
   - Backend automatically links campaigns to products by matching URLs

3. **Campaign Card Display** (`/campaigns`):
   - 128x128px product thumbnail on left side
   - Fallback to placeholder icon for campaigns without linked products
   - Campaign details (name, URL, network, keywords) to the right of image
   - Product description indented below image (if available)

**Backend Integration:**
- `CampaignResponse` includes `thumbnail_image_url` from ProductIntelligence
- `GET /api/campaigns` fetches thumbnails for all campaigns with `product_intelligence_id`
- Images stored in Cloudflare R2, URLs returned in API responses

### Context-Sensitive Help System

**CRITICAL: Every new page MUST have help content added to `src/config/helpContent.ts`**

The right sidebar displays context-sensitive help that automatically detects the current page and shows relevant guidance.

#### Adding Help Content for New Pages

1. **Open** `src/config/helpContent.ts`
2. **Add** a new entry to the `helpContent` object with the route path as the key
3. **Include** all required fields: `title`, `description`, `steps`, and `tips`

**Template:**
```typescript
"/your-new-page": {
  title: "Page Title",
  description: "Brief description of what this page does and its purpose.",
  steps: [
    {
      number: 1,
      title: "First Step Title",
      description: "Detailed explanation of what the user needs to do in this step.",
    },
    {
      number: 2,
      title: "Second Step Title",
      description: "Detailed explanation of the next step.",
    },
    // Add 3-6 steps for complete guidance
  ],
  tips: [
    "Pro tip about using this feature effectively",
    "Best practice or helpful hint",
    "Common gotcha or important reminder",
    "Another useful tip",
  ],
  links: [ // Optional
    {
      label: "Related Documentation",
      href: "/link-to-docs",
    },
  ],
},
```

#### Help Content Guidelines

- **Steps**: 3-6 numbered steps that guide users through the complete workflow
- **Tips**: 3-5 actionable pro tips and best practices
- **Description**: 1-2 sentences explaining the page purpose
- **Language**: Use imperative voice ("Click...", "Review...", "Select...")
- **Completeness**: Steps should cover the entire user journey on that page

#### Dynamic Routes

For dynamic routes like `/campaigns/[id]`, use the pattern syntax:
```typescript
"/campaigns/[id]": {
  title: "Campaign Details",
  // ... help content
},
```

The `getHelpContent()` function in the config handles pattern matching automatically.

### Page Pattern

Every new page MUST follow this pattern:
1. Wrap content with `AuthGate` component, specifying `requiredRole` ("user" or "admin")
2. **IMMEDIATELY add help content** to `src/config/helpContent.ts` (this is automatic - no prop needed)
3. Use `api` client from `src/lib/appClient.ts` for backend calls
4. Style with Tailwind classes and CSS variable references (`var(--text-primary)`, etc.)
5. Use React Query (`useQuery`, `useMutation`) for data fetching
6. Use `toast` from `sonner` for user notifications

**Example:**
```tsx
"use client";
import { AuthGate } from "src/components/AuthGate";
import { useQuery } from "@tanstack/react-query";
import { api } from "src/lib/appClient";

export default function YourPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["yourData"],
    queryFn: async () => (await api.get("/api/your-endpoint")).data,
  });

  return (
    <AuthGate requiredRole="user">
      <div className="p-6">
        {/* Your page content */}
      </div>
    </AuthGate>
  );
}
```

**Then immediately add to `src/config/helpContent.ts`:**
```typescript
"/your-page": {
  title: "Your Page Title",
  description: "What this page does...",
  steps: [...],
  tips: [...],
},
```

## Backend Integration

The frontend communicates with a FastAPI backend located at `C:\Users\shaun\OneDrive\Documents\GitHub\blitz-backend`.

### Backend API Structure

All API routes are prefixed with `/api`:

- **Auth**: `/api/auth`
  - `POST /api/auth/register` - Register new user
  - `POST /api/auth/login` - Login and receive JWT token
  - `GET /api/auth/me` - Get current user info (requires auth)

- **Campaigns**: `/api/campaigns`
  - Create, read, update, delete campaigns
  - Campaign analytics and status management

- **Content**: `/api/content`
  - Generate AI-powered content for campaigns
  - Refine and create variations of existing content
  - Supports: articles, emails, video scripts, social posts, landing pages, ad copy

- **Intelligence**: `/api/intelligence`
  - Compile intelligence data for campaigns (product research, competitor analysis)
  - RAG (Retrieval-Augmented Generation) queries against knowledge base
  - Knowledge base management

- **Compliance**: `/api/compliance`
  - Check content against FTC guidelines and affiliate network rules
  - Returns compliance status (compliant, warning, violation)
  - Provides suggestions for fixing issues

- **Admin**: `/api/admin`
  - AI router management and configuration
  - User management, analytics, settings

### Backend Data Models

Key backend schemas (from `app/schemas.py`):

- **ContentType**: article, email, video_script, social_post, landing_page, ad_copy
- **MarketingAngle**: problem_solution, transformation, scarcity, authority, social_proof, comparison, story
- **CampaignStatus**: draft, active, paused, completed
- **ComplianceStatus**: compliant, warning, violation

### CORS Configuration

Backend CORS allows:
- `https://blitz-frontend-three.vercel.app` (production)
- `http://localhost:3000` (development)

### Authentication Flow

1. User submits login credentials to `POST /api/auth/login`
2. Backend validates and returns JWT token with user email in `sub` claim
3. Frontend stores token in localStorage via `setToken()` in `src/lib/auth.ts`
4. All subsequent requests include `Authorization: Bearer <token>` header (added by axios interceptor)
5. On 401 response, frontend clears token and redirects to `/login`

## Landing Page Content Structure

**IMPORTANT:** Generated landing page content is **structured content for template integration**, NOT a finished landing page.

### Content Structure

Landing pages generate with the following labeled sections that will be used with a future template builder:

```
**Headline**
Your compelling headline text

**Subheadline**
Your subheadline text

**Affiliate Disclosure**
This page contains affiliate links. We may earn a commission if you
make a purchase through these links at no additional cost to you.

**Problem Agitation**
Problem identification and emotional connection

**Solution Introduction**
Introducing the solution/product

**Benefits List**
• Key benefit 1
• Key benefit 2
• Key benefit 3

**Social Proof**
Testimonials and reviews with "Results may vary" disclaimers

**CTA Primary**
Primary call-to-action text

**Features Section**
Detailed product features

**FAQ**
Questions and answers addressing objections

**CTA Final**
Final call-to-action with urgency/scarcity

**Disclaimer and Disclosures**
FTC disclaimers, results disclaimers, medical disclaimers,
CAN-SPAM compliance, testimonial disclaimers
```

### Template Integration (Future)

When the landing page template builder is implemented, content will be inserted via placeholders:

```html
<h1>{{headline}}</h1>
<h2>{{subheadline}}</h2>
<div class="disclosure">{{affiliate_disclosure}}</div>
<section class="problem">{{problem_agitation}}</section>
<section class="solution">{{solution_introduction}}</section>
<!-- etc. -->
<footer>{{disclaimer_and_disclosures}}</footer>
```

### FTC Compliance

**Two Separate Sections:**
1. **Affiliate Disclosure** (top) - Required by FTC to be "clear and conspicuous" before purchase decision
2. **Disclaimer and Disclosures** (bottom) - General disclaimers, results vary, medical advice, etc.

**Backend Compliance Checker:**
- Located: `app/services/compliance_checker.py`
- Checks first 500 characters for affiliate disclosure
- Applies to content types: `landing_page`, `review_article`, `tutorial`
- Emails can have disclosure at bottom

**Fix Compliance Feature:**
- Click "Fix Compliance" button on non-compliant content
- Automatically adds **Affiliate Disclosure** section after subheadline
- Updates existing content (no duplicate records created)
- Shows success message when compliance improves

### Content Generation Flow

1. User selects campaign and content type "Landing Page"
2. Backend generates structured sections using `PromptBuilder`
3. Compliance checker validates disclosure placement
4. Content saved with separate, labeled sections
5. Future: Template builder will use `{{section_name}}` placeholders

## Key Implementation Notes

- **Client Components**: Most components use `"use client"` directive due to hooks and browser APIs
- **SSR Safety**: Auth utilities check `typeof window !== "undefined"` before accessing localStorage
- **Route Groups**: Auth pages use Next.js route groups `(auth)` for organization without affecting URLs
- **Typed Routes**: Enabled via `experimental: { typedRoutes: true }` in `next.config.js`
- **Type Alignment**: Keep frontend types in `src/lib/types.ts` aligned with backend schemas in `app/schemas.py`
- **Help Content Required**: EVERY new page must have help content added to `src/config/helpContent.ts` with steps and tips
- **React Query**: Use for all data fetching (`useQuery`) and mutations (`useMutation`) - provider already configured
- **Toast Notifications**: Use `toast` from `sonner` for all user feedback messages

## CampaignForge Reference

Blitz is a rewrite of CampaignForge with 91% complexity reduction. When referencing the original codebase:

**Locations:**
- Frontend: `C:\Users\shaun\OneDrive\Documents\GitHub\campaignforge-frontend`
- Backend: `C:\Users\shaun\OneDrive\Documents\GitHub\campaignforge-backend`

**What to Reference:**
- ✅ Feature ideas and business logic
- ✅ API endpoint functionality (what they do, not how)
- ✅ User workflows and experiences
- ✅ Content generation prompts and strategies

**What NOT to Copy:**
- ❌ Modular architecture patterns (`intelligence_module.initialize()`)
- ❌ Abstract interfaces and factory patterns
- ❌ NextAuth implementation
- ❌ Radix UI component usage
- ❌ Zustand state management patterns
- ❌ Ad-hoc database migration scripts
- ❌ Duplicate code (landing page generators in two locations)
- ❌ Over-normalized database schemas (20+ tables)

**Key Differences:**
- CampaignForge: 322 Python files, 49 npm packages, modular async initialization
- Blitz: 28 Python files, 13 npm packages, simple monolithic structure
- CampaignForge uses `src/` with module system
- Blitz uses `app/` with flat structure

See `docs/CAMPAIGNFORGE_COMPARISON.md` for complete analysis of what was removed and why.

## Documentation

All project documentation is located in the `docs/` folder:

- **`docs/DEPLOY_NOW.md`** - Quick deployment guide for Vercel and Railway
- **`docs/DEPLOYMENT_GUIDE.md`** - Complete deployment instructions with troubleshooting
- **`docs/CAMPAIGN_CREATION_GUIDE.md`** - Campaign creation feature documentation and testing
- **`docs/PRODUCTION_URLS.md`** - Production URLs, API endpoints, and environment variables
- **`docs/CAMPAIGNFORGE_COMPARISON.md`** - Architecture comparison with original CampaignForge
- **`docs/endpoints.json`** - OpenAPI specification for all API endpoints

---

## Admin Configuration System

### Overview

The Admin Configuration system allows administrators to manage pricing tiers, AI provider settings, and platform-wide configurations through a web interface without code changes.

### Backend API

**Location:** `app/api/admin/config.py`

**Endpoints:**
- `GET /api/admin/config/tiers` - List all pricing tiers
- `GET /api/admin/config/providers` - List all AI providers
- `GET /api/admin/config/global` - Get global settings

**Status:** Currently read-only with default data. Full CRUD operations will be added in future updates.

### Frontend Admin Page

**Location:** `src/app/admin/config/page.tsx`

**Features:**
- Three-tab interface: Pricing Tiers, AI Providers, Global Settings
- Displays current configuration
- Visual indicators for tier pricing and limits
- Provider cost analysis and context limits
- Global feature flags and billing settings

**Access:** Navigate to `/admin/config` from the admin navigation menu

### Configuration Structure

#### Pricing Tiers
- Tier name (free, starter, pro, enterprise)
- Monthly pricing
- Word limits (monthly, daily, per generation)
- Media limits (images/videos)
- Campaign limits
- Overage billing rates

#### AI Providers
- Provider and model names
- Cost per token (input/output)
- Context length
- Priority and tags
- Environment variable mapping

#### Global Settings
- Free tier configuration
- Billing options (Stripe, overage billing)
- AI routing settings (cost optimization, fallback)
- Feature flags (video/image/compliance generation)

### Future Enhancements

1. **Database Integration**
   - Add admin_settings, tier_configs, ai_provider_configs tables
   - Replace default data with database queries
   - Add write operations (CREATE, UPDATE, DELETE)

2. **Edit Functionality**
   - Add modals for editing tiers and providers
   - Real-time validation
   - Optimistic UI updates

3. **Analytics Dashboard**
   - Usage metrics by tier
   - Cost analysis per provider
   - Revenue tracking

### Current Status

✅ Backend API endpoints created and integrated
✅ Frontend admin page with read-only view
✅ Navigation menu integration
✅ Default configuration data
🔄 Database models (planned)
🔄 CRUD operations (planned)

