# app/main.py
# with added landing pages and admin routes
# Main application file for the Blitz API using FastAPI

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import time
import logging

from app.core.config.settings import settings
from app.db.session import engine, Base
from app.api import auth, campaigns, intelligence, video, compliance, products, links, product_analytics, platform_credentials, overlays, email_signups, tracking
from app.api.content import text_router, images_router, unified_content_router, prompt_generator_router
from app.api.content.video_overlay import router as video_overlay_router
from app.api.images.ai_erase import router as ai_erase_router
from app.api.proxy import proxy_router
from app.api import messages, message_requests, affiliates, upload
from app.api import connections
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
from app.plugins.image_editor import router as image_editor_router
from app.api.admin import messages as admin_messages
from app.api.admin import video_thumbnails as admin_video_thumbnails
from app.api import analytics
from app.api import demo_fix
from app.api import list_users
from app.api import fix_single_user
from app.api import test_login
from app.api import message_recipients

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
        "https://blitz.ws",
        "https://www.blitz.ws",  # Add www subdomain
        "https://*.vercel.app"   # Allow preview deployments
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Trust proxy headers (for HTTPS redirect preservation)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["blitzed.up.railway.app", "*.railway.app", "127.0.0.1", "localhost"]
)

# ====
# MIDDLEWARE
# ====

# Trust proxy headers (for HTTPS redirect preservation)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["blitzed.up.railway.app", "*.railway.app", "127.0.0.1", "localhost"]
)

# Protocol Preservation Middleware
@app.middleware("http")
async def https_redirect_fix(request: Request, call_next):
    """Fix redirects to preserve HTTPS protocol from proxy headers."""
    response = await call_next(request)

    # If this is a redirect and came from HTTPS, fix the location header
    if response.status_code in (301, 302, 303, 307, 308):
        # Check if the original request came via HTTPS
        if request.headers.get("x-forwarded-proto") == "https":
            location = response.headers.get("location")
            if location and location.startswith("http://"):
                # Replace http:// with https:// in the redirect location
                location = location.replace("http://", "https://", 1)
                response.headers["location"] = location

    return response

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
app.include_router(proxy_router)  # Image proxy endpoint (no auth)
app.include_router(images_router)
app.include_router(ai_erase_router)  # AI image erase/inpainting API
app.include_router(image_editor_router)  # Image Editor Plugin with 7 AI operations
app.include_router(unified_content_router)  # Unified content library (text + images)
app.include_router(prompt_generator_router)  # Prompt generation service
app.include_router(video_overlay_router)  # Video text overlay API
app.include_router(video.router)  # Video generation API
app.include_router(upload.router)
app.include_router(intelligence.router)
app.include_router(compliance.router)
app.include_router(overlays.router)
app.include_router(links.router)  # Link management API under /api/links
app.include_router(links.redirect_router)  # Public redirect at /r/{short_code}
app.include_router(product_analytics.router)  # Product analytics and leaderboards
app.include_router(platform_credentials.router)  # Platform API credentials management
app.include_router(email_signups.router)  # Email signup service for pre-launch
app.include_router(message_recipients.router)  # Get allowed message recipients - MUST be before messages.router
app.include_router(messages.router)  # Internal messaging system
app.include_router(message_requests.router)  # Message requests workflow
app.include_router(affiliates.router)  # Affiliate directory and networking
app.include_router(connections.router)  # Connection management (delete, block, unblock)
app.include_router(tracking.router)  # Affiliate conversion tracking
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
app.include_router(admin_video_thumbnails.router)
app.include_router(admin_products.router)
app.include_router(admin_campaigns.router)
app.include_router(admin_email_campaigns.router)
app.include_router(admin_email_templates.router)
app.include_router(admin_messages.router)  # Admin broadcast messaging
app.include_router(analytics.router)  # Developer analytics API
app.include_router(demo_fix.router)  # Demo password fix endpoint
app.include_router(list_users.router)  # List all users endpoint
app.include_router(fix_single_user.router)  # Reset single user password
app.include_router(test_login.router)  # Test login credentials

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