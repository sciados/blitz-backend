# app/main.py
# with added landing pages and admin routes

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import time
import logging

from app.core.config.settings import settings
from app.db.session import engine, Base
from app.api import auth, campaigns, intelligence, compliance, products, links, product_analytics, platform_credentials, overlays, email_signups
from app.api.content import text_router, images_router
from app.api.admin import ai_router as admin_ai_router
from app.api.admin import products as admin_products
from app.api.admin import campaigns as admin_campaigns
from app.api.admin import email_campaigns as admin_email_campaigns
from app.api.admin import email_templates as admin_email_templates
from app.api.admin import config as admin_config
from app.api.admin import users as admin_users
from app.api.admin import dashboard as admin_dashboard
from app.api.admin import analytics as admin_analytics
from app.api.admin import api_keys as admin_api_keys
from app.api.admin import compliance as admin_compliance
from app.api.admin import credits as admin_credits
from app.api.admin import images as admin_images

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ====
# LIFESPAN EVENTS
# ====

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for startup and shutdown."""
    # Startup
    logger.info("Starting Blitz API...")

    # NOTE: Database tables are now managed by Alembic migrations
    # No longer using Base.metadata.create_all()

    # Log JWT configuration source
    jwt_key_preview = settings.JWT_SECRET_KEY[:20] + "..." if len(settings.JWT_SECRET_KEY) > 20 else settings.JWT_SECRET_KEY
    if settings.JWT_SECRET_KEY == "CHANGE_ME_SUPER_SECRET":
        logger.warning("⚠️  Using fallback JWT_SECRET_KEY - CHECK ENVIRONMENT VARIABLES!")
    else:
        logger.info(f"✓ JWT_SECRET_KEY loaded from environment (preview: {jwt_key_preview})")
    logger.info(f"✓ Token expiration: {settings.ACCESS_TOKEN_EXPIRE_MINUTES} minutes ({settings.ACCESS_TOKEN_EXPIRE_MINUTES // 60} hours)")

    logger.info("Blitz API started successfully")
    logger.info("Use 'python migrate.py upgrade' to apply database migrations")

    yield

    # Shutdown
    logger.info("Shutting down Blitz API...")
    await engine.dispose()
    logger.info("Blitz API shut down successfully")

# ====
# CREATE APP
# ====

app = FastAPI(
    title="Blitz API",
    description="AI-Powered SaaS Platform for Affiliate Marketing Campaign Generation",
    version="1.0.0",
    lifespan=lifespan
)

# ====
# CORS MIDDLEWARE - MUST BE BEFORE OTHER MIDDLEWARE
# ====

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://blitz-frontend-three.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ====
# MIDDLEWARE
# ====

# Request Timing Middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Request Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Status: {response.status_code}")
    return response

# ====
# EXCEPTION HANDLERS
# ====

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "detail": exc.errors(),
            "body": exc.body
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "detail": str(exc) if settings.DEBUG else "An unexpected error occurred"
        }
    )

# ====
# ROUTES
# ====

# Health check
@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - health check."""
    return {
        "status": "healthy",
        "service": "Blitz API",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "database": "connected",
        "timestamp": time.time()
    }

# Include routers
app.include_router(auth.router)
app.include_router(campaigns.router)
app.include_router(products.router)
app.include_router(text_router)
app.include_router(images_router)
app.include_router(intelligence.router)
app.include_router(compliance.router)
app.include_router(overlays.router)
app.include_router(links.router)  # Link management API under /api/links
app.include_router(links.redirect_router)  # Public redirect at /{short_code}
app.include_router(product_analytics.router)  # Product analytics and leaderboards
app.include_router(platform_credentials.router)  # Platform API credentials management
app.include_router(email_signups.router)  # Email signup service for pre-launch
app.include_router(admin_ai_router.router)
app.include_router(admin_config.router)
app.include_router(admin_users.router)
app.include_router(admin_dashboard.router)
app.include_router(admin_analytics.router)
app.include_router(admin_api_keys.router)
app.include_router(admin_compliance.router)
app.include_router(admin_compliance.router)
app.include_router(admin_credits.router)
app.include_router(admin_images.router)
app.include_router(admin_products.router)
app.include_router(admin_campaigns.router)
app.include_router(admin_email_campaigns.router)
app.include_router(admin_email_templates.router)

# ====
# STARTUP MESSAGE
# ====

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )