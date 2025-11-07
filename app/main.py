# app/main.py
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import time
import logging

from app.core.config.settings import settings
from app.db.session import engine, Base
from app.api import auth, campaigns, content, intelligence, compliance, products, links
from app.api.admin import ai_router as admin_ai_router
from app.api.admin import products as admin_products
from app.api.admin import campaigns as admin_campaigns

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
        "https://blitz-frontend-three.vercel.app",
        "http://localhost:3000"
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
app.include_router(content.router)
app.include_router(intelligence.router)
app.include_router(compliance.router)
app.include_router(links.router)
app.include_router(admin_ai_router.router)
app.include_router(admin_products.router)
app.include_router(admin_campaigns.router)

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