content = """# HANDOVER_DOCUMENT.md
Project: Blitz — Modular SaaS for Affiliate Marketers
Backend: FastAPI + PostgreSQL (Railway)
Frontend: Next.js (Vercel)
Date: 2025-10-28

## Executive Summary

This handover captures the latest state: auth is stable (registration/login), CORS is correctly configured, bcrypt/JWT issues resolved, and we introduced an Admin-configurable AI Router with env fallbacks. Dashboards (Admin/User) are planned with role-based redirects post-login. Deployment is remote-only: Railway (backend) and Vercel (frontend).

## 1) Key Outcomes This Session

- Fixed prior CORS, async DB query, bcrypt length (>72-byte) pitfalls, and SECRET_KEY vs JWT_SECRET_KEY mismatch.
- Finalized CORS to include Vercel HTTPS domains only.
- Created/seeded ai_router_config for admin-managed AI provider defaults (JSON arrays per use case) with SQL provided.
- Delivered FastAPI Admin endpoints (design) for reading/writing AI Router config and health snapshot.
- Delivered a minimal Next.js Admin page (/admin/ai-router) and login redirect plan for role-based dashboards.

## 2) Files Touched / Added (design and code provided)

- app/ai_router.py (replaced with env-driven, use-case router + fallback + health + budget)
- Database: ai_router_config (single-row JSONB), optional ai_router_config_history, ai_usage_log
- Admin API (to add): /api/admin/ai-router/config (GET/PUT), /api/admin/ai-router/health (GET)
- Frontend (to add):
  - app/(auth)/login/page.tsx
  - app/admin/page.tsx (Admin Dashboard entry)
  - app/admin/ai-router/page.tsx (Router defaults editor)
  - app/dashboard/page.tsx (User Dashboard entry)
  - app/_lib/apiClient.ts

## 3) Environment & Deployment Notes (Remote-only)

- Railway (backend):
  - JWT_SECRET_KEY (HS256), ACCESS_TOKEN_EXPIRE_MINUTES
  - DATABASE_URL and DATABASE_URL_ASYNC
  - ALLOWED_ORIGINS: only HTTPS Vercel domains for your frontend
  - API keys for providers (OPENAI_API_KEY, ANTHROPIC_API_KEY, COHERE_API_KEY, GROQ_API_KEY, FAL_API_KEY, REPLICATE_API_TOKEN, etc.)
  - AI flags: AI_COST_OPTIMIZATION, AI_FALLBACK_ENABLED, AI_CACHE_TTL_SECONDS
  - Optional: AI_* lists as environment fallback (AI_CHAT_FAST, AI_CHAT_QUALITY, AI_EMBEDDINGS, AI_VISION, AI_IMAGE_GEN)
- Vercel (frontend):
  - NEXT_PUBLIC_API_BASE_URL=https://<your-railway-app>.up.railway.app
  - Client should store bearer token (temp: localStorage) and call /api/auth/me for role; redirect to /admin or /dashboard.

## 4) SQL (already shared/run)

- Create tables:
  - ai_router_config (single-row JSONB) with optional ai_router_config_history and ai_usage_log
- Seed defaults (arrays per use case): chat_fast, chat_quality, embeddings, vision, image_gen
- Rollback helpers and safe updates using COALESCE and FROM joins

## 5) Admin-Configurable AI Router (overview)

- Use-case keys: chat_fast, chat_quality, embeddings, vision, image_gen
- Admin UI edits JSON-array lists of "provider:model" with left-to-right priority
- Router reads DB config first; falls back to ENV; then cost/health sorts and automatic fallback on errors
- Observability: in-memory health cache; optional ai_usage_log for long-term tracking

## 6) Dashboards Plan

- Not yet implemented fully; basic pages scaffold supplied.
- Login flow: /login -> on success call /api/auth/me; redirect by role
  - admin -> /admin
  - user -> /dashboard
- Protect pages by checking role client-side (simple) or via middleware + HTTP-only cookies later.

## 7) Action Items

Backend (Railway):

- [ ] Confirm ALLOWED_ORIGINS only includes final HTTPS Vercel domains
- [ ] Deploy updated app/ai_router.py
- [ ] Add Admin endpoints and include router in app.main
- [ ] (Optional) Add ai_usage_log inserts around AI calls

Frontend (Vercel):

- [ ] Add pages: login, /admin, /admin/ai-router, /dashboard
- [ ] Set NEXT_PUBLIC_API_BASE_URL and deploy
- [ ] Wire login to store token and redirect by role

Data (Postgres via pgAdmin):

- [ ] Ensure ai_router_config active row contains arrays per use case
- [ ] (Optional) Create history snapshots before edits

## 8) Open Questions

- Confirm exact User model fields (role, is_active, created_at, last_login_at)
- Should we implement HTTP-only cookie auth and Next middleware now, or keep bearer token in client for speed?
- Which additional Admin pages are highest priority after AI Router: Users, Campaigns, Compliance, Intelligence Jobs?

## 9) Quick Snippets

- FastAPI include (after creating admin routes):

```python
from app.api.admin import ai_router as admin_ai_router
app.include_router(admin_ai_router.router)

Next.js env (Vercel):
bash
Copy
NEXT_PUBLIC_API_BASE_URL=https://<your-railway-app>.up.railway.app

10) References
ChatLLM Teams billing FAQs: https://abacus.ai/help/howTo/chatllm/faqs/billing
ChatLLM Help Center: https://abacus.ai/help/howTo/chatllm
RouteLLM APIs guide: https://abacus.ai/app/route-llm-apis
Manage subscription: https://apps.abacus.ai/chatllm/admin/profile

11) Special handling reminder
HANDOVER_FIX_REGISTRAION.md — these documents can only be used in code execution. Potential extraction failure reasons: binary/unsupported encoding, mislabeled file type, or formatting that blocks text parsers.

12) Current Status Checklist
Auth (register/login): OK
CORS: OK
Bcrypt/JWT alignment: OK
AI Router (env + admin-configurable): Schema seeded; endpoints/UI stubs provided
Dashboards: pending (scaffold provided)
Deployment flow: Railway + Vercel only (no local)
