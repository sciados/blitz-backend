HANDOVER_DOCUMENT.md
Project: CampaignForge — Modular SaaS for Affiliate Marketers
Backend: FastAPI + PostgreSQL (Railway)
Frontend: Next.js (Vercel)
Date: 2025-10-23
Executive Summary

CampaignForge is a modular, intelligence-driven SaaS for affiliate marketers to research products, compile market intelligence, and generate compliant promotional content. The backend is built with FastAPI, PostgreSQL, and Alembic for migrations; the frontend will be built with Next.js on Vercel. The system emphasizes a three-stage intelligence pipeline (extraction → AI enhancement → RAG indexing/retrieval), modular services, and cost-optimized AI routing.

This document merges the previous handover with all subsequent changes and fixes so you can resume seamlessly in a new chat or environment.

1) Architecture Overview

Tech stack

Backend: FastAPI, SQLAlchemy (async), Alembic, Pydantic, Uvicorn

Database: PostgreSQL (Railway)

Storage: Cloudflare R2 (planned/implemented service)

AI/RAG: AI Router (provider-agnostic), Embeddings (Cohere), RAG vector storage (service), Prompt Builder, Compliance Checker

Frontend: Next.js 14 (Vercel) — to be implemented in Phase 4

Core principles

Modular services (intelligence, content, compliance, RAG)

Dependency injection at request-time (FastAPI Depends)

No hardcoded templates/mock data

Affiliate networks support (ClickBank, JVZoo, WarriorPlus) by flexible inputs and intelligence flow

Compliance awareness (FTC guidelines)

2) Files Uploaded by User and Referenced

3) Backend Progress — Completed

Requirements and dependencies:

requirements.txt includes FastAPI, SQLAlchemy async, Alembic, Uvicorn, httpx, BeautifulSoup4, Cohere, email-validator (added), and other necessary packages.

Config and DB:

app/config.py: Settings managed via Railway environment variables (no .env needed at runtime)

app/db/session.py: Async SQLAlchemy session factory with get_db dependency

app/db/models.py: ORM models mapped to PostgreSQL schema; renamed any conflicting metadata columns to meta_data for SQLAlchemy compatibility

Alembic configured; migrations ready to generate and apply

Core services:

app/services/storage_r2.py: Cloudflare R2 storage abstraction for media uploads

app/services/ai_router.py: AI provider routing with cost/fallback logic

app/services/embeddings.py: Embedding generation via Cohere

app/services/crawler.py: Web scraping and content extraction (created class CrawlerService)

app/services/rag.py: RAG service for ingestion, vector search, and context retrieval

app/services/intelligence_compiler.py: Intelligence aggregation (product research, competitor analysis)

app/services/prompt_builder.py: Structured prompt construction for different content types

app/services/compliance_checker.py: FTC-aligned checks, returns issues and score

APIs and schemas:

app/schemas.py: Pydantic request/response models

app/auth.py: Authentication helpers, current user dependency

API endpoints:

app/api/auth.py: Register, login, current user

app/api/campaigns.py: CRUD for campaigns, analytics

app/api/content.py: Generate content, list by campaign, refine content, create variations, delete — updated to proper dependency injection

app/api/intelligence.py: Compile intelligence, campaign intelligence retrieval, knowledge base CRUD, RAG query — updated to proper dependency injection

app/api/compliance.py: Compliance check and FTC guideline retrieval

app/main.py: FastAPI app assembly, routers, CORS, middleware

Deployment files:

railway.json, Procfile

README.md updated to emphasize Railway env vars over .env; .env.example removed on request

4) Recent Fixes and Changes

Dependency injection refactor:

Fixed error: RAGService.init() missing db

Moved all service instantiation into request-scoped dependencies using FastAPI’s Depends(get_db) where needed

Updated app/api/content.py and app/api/intelligence.py accordingly

Crawler import error:

Error: ImportError cannot import name 'CrawlerService'

Resolution: Created app/services/crawler.py with class CrawlerService (async httpx crawling, BeautifulSoup parsing, metadata extraction, product info, quality assessment, batch crawling with retries)

SQLAlchemy reserved name collision:

Renamed model field metadata → meta_data to avoid conflict with SQLAlchemy’s Base.metadata

Provided guidance to update migrations and any references accordingly

Alembic integration:

Created alembic/env.py configured for async engine and autogenerate with:

Conversion to postgresql+asyncpg://

target_metadata = Base.metadata

compare_type and compare_server_default enabled

Provided commands to autogenerate and apply migrations

Dependency fixes:

Added missing dependency: email-validator to requirements

Endpoint metadata clarification:

Confirmed metadata is acceptable in endpoints.json (OpenAPI context), only SQLAlchemy models needed the rename
5) Alembic — Current Setup and Commands

alembic/env.py highlights:

Async-compatible using create_async_engine

Converts DATABASE_URL to postgresql+asyncpg:// as needed

Uses app.db.models.Base.metadata for autogenerate

Logging via alembic.ini if present

Typical workflow:

Initialize (if not already): alembic init alembic

Create migration: alembic revision --autogenerate -m "Initial migration"

Apply migrations: alembic upgrade head

Check version: alembic current

Notes:

Ensure Railway’s DATABASE_URL is present at runtime

If models changed (e.g., metadata → meta_data), create a new revision and upgrade

6) Environment & Deployment Notes

Environment variables management:

All env vars configured in Railway; no .env checked into repo

README updated to reflect this

Uvicorn/ASGI:

Procfile configured for uvicorn startup

CORS and Middleware:

CORS enabled, request timing and exception handling middleware in app/main.py
7) Open Items / Next Steps (Frontend Phase 4)

Frontend (Next.js 14, Vercel):

Auth integration with backend endpoints

Role-based dashboards (affiliate/business owner/content creator/agency)

Campaign creation workflow UI

Step 1 inputs and intelligence analysis trigger

Intelligence results and confidence scoring visualizations

Step 3 content generation screens with refinement and variations

Compliance reporting UI

Knowledge base management interface

Settings: API keys/credits (if applicable), team features (later)

Backend enhancements (optional/next iterations):

Provider configs for AI Router (cost tiers, fallbacks)

More robust RAG storage (pgvector or external vector DB, depending on current implementation)

Webhook/queue support for long-running intelligence analyses

Rate limiting/credit usage enforcement

8) Known Risks and What To Watch For

After import errors are fixed, subsequent runtime errors may appear:

Missing environment variables in Railway

Database connectivity or permission issues

Alembic not yet applied (no tables)

Ensure migrations are applied before running the app

Validate that app/services/intelligence_compiler.py imports align with available services

Confirm requirements installation on Railway matches requirements.txt

9) How To Resume Seamlessly In a New Chat

Please upload this HANDOVER_DOCUMENT.md along with any relevant repo files. In the new chat, say:

“Continue Phase 4 — build the Next.js frontend following the handover.”
Optionally include:

Railway App URL and DB URL (redact secrets)

Any desired UI wireframes or rough page list

We will:

Scaffold Next.js app

Implement auth pages and protected routes

Build dashboards and campaign flows

Integrate to backend endpoints already created

Provide deploy steps to Vercel

10) Quick Command Reference

Run server locally:

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

Alembic:

alembic revision --autogenerate -m "Initial"

alembic upgrade head

Verify DB tables:

Use Railway’s psql or pgAdmin after successful migration
11) Links for Help

ChatLLM Teams billing FAQs: <https://abacus.ai/help/howTo/chatllm/faqs/billing>

ChatLLM Help Center: <https://abacus.ai/help/howTo/chatllm>

RouteLLM APIs guide: <https://abacus.ai/app/route-llm-apis>

Manage subscription: <https://apps.abacus.ai/chatllm/admin/profile>

12) Current Status Checklist

Backend models, services, and endpoints: Completed

Dependency injection for services: Fixed and verified in content/intelligence APIs

Crawler service class: Implemented as CrawlerService

Alembic env.py: Created and configured for async

Requirements: Updated (includes email-validator)

README: Updated to Railway env var usage

Next.js Frontend: Pending (Phase 4)
