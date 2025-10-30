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
- **Campaign Type**: `id`, `name`, `product_url`, `affiliate_network`, `status`, `created_at`, `updated_at`
- Campaign status values: `"draft" | "active" | "paused" | "completed"`

### Page Pattern

Most pages follow this pattern:
1. Wrap content with `AuthGate` component, specifying `requiredRole`
2. Optionally provide `helpContent` object for right sidebar contextual help
3. Use `api` client from `src/lib/appClient.ts` for backend calls
4. Style with Tailwind classes and CSS variable references (`var(--text-primary)`, etc.)

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

## Key Implementation Notes

- **Client Components**: Most components use `"use client"` directive due to hooks and browser APIs
- **SSR Safety**: Auth utilities check `typeof window !== "undefined"` before accessing localStorage
- **Route Groups**: Auth pages use Next.js route groups `(auth)` for organization without affecting URLs
- **Typed Routes**: Enabled via `experimental: { typedRoutes: true }` in `next.config.js`
- **Type Alignment**: Keep frontend types in `src/lib/types.ts` aligned with backend schemas in `app/schemas.py`

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
