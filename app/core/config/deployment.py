# =====================================
# File: app/core/config/deployment.py
# =====================================

"""
Railway deployment-specific configuration for Blitz.

Handles Railway-specific settings, health checks, and deployment optimizations.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
import os

from app.core.config.settings import settings


@dataclass
class RailwayConfig:
    """Railway platform-specific configuration."""
    
    # Railway Environment
    railway_environment: str = os.getenv("RAILWAY_ENVIRONMENT", "production")
    railway_service_name: str = os.getenv("RAILWAY_SERVICE_NAME", "blitz-backend")
    railway_project_id: str = os.getenv("RAILWAY_PROJECT_ID", "")
    railway_replica_id: str = os.getenv("RAILWAY_REPLICA_ID", "")
    
    # Port Configuration
    port: int = int(os.getenv("PORT", "8000"))
    
    # Health Check Configuration
    health_check_path: str = "/health"
    health_check_interval: int = 30
    
    # Performance Settings
    worker_timeout: int = 120
    keepalive_timeout: int = 65
    max_requests: int = 1000
    max_requests_jitter: int = 100
    
    @property
    def is_railway_environment(self) -> bool:
        """Check if running on Railway platform."""
        return bool(self.railway_project_id)
    
    @property
    def host(self) -> str:
        """Get the appropriate host for the environment."""
        if self.is_railway_environment:
            return "0.0.0.0"  # Railway requires binding to all interfaces
        return "127.0.0.1"
    
    def get_uvicorn_config(self) -> Dict[str, Any]:
        """Get Uvicorn server configuration for Railway."""
        return {
            "host": self.host,
            "port": self.port,
            "workers": 1,  # Railway handles scaling
            "timeout_keep_alive": self.keepalive_timeout,
            "access_log": not settings.is_production,
            "reload": settings.is_development,
        }


class DeploymentConfig:
    """Main deployment configuration manager."""
    
    def __init__(self):
        self.railway = RailwayConfig()
    
    def get_cors_config(self) -> Dict[str, Any]:
        """Get CORS configuration for Railway deployment."""

        # Initialize logging first
        import logging
        logger = logging.getLogger(__name__)

        # Get configured origins, with emergency fallbacks for Railway deployment
        try:
            cors_origins = settings.cors_origins or []
        except Exception:
            cors_origins = []

        # EMERGENCY: Add production domain directly if not present
        emergency_production_origins = [
            "https://blitzed.up.railway.app",
            "http://blitzed.up.railway.app"
        ]

        # Always ensure production domain is included
        for origin in emergency_production_origins:
            if origin not in cors_origins:
                cors_origins.append(origin)
                logger.warning(f"Emergency CORS: Added {origin}")

        # Log current origins for debugging
        logger.info(f"CORS origins before production additions: {cors_origins}")

        # Add production domains if not already included
        production_origins = [
            "https://blitzed.up.railway.app",
            "https://rodgersdigital.com",
            "https://blitz-frontend.vercel.app",
            "https://blitz-frontend-git-main.vercel.app"
        ]

        # Debug logging for production origins
        logger.info(f"Initial CORS origins from settings: {cors_origins}")

        for origin in production_origins:
            if origin not in cors_origins:
                cors_origins.append(origin)
                logger.info(f"Added production origin: {origin}")

        logger.info(f"Final CORS origins: {cors_origins}")
        
        # Add localhost origins for development
        localhost_origins = [
            "http://localhost:3000"  # Temporary for testing
        ]
        
        # Add localhost origins if not already included
        for origin in localhost_origins:
            if origin not in cors_origins:
                cors_origins.append(origin)
        
        return {
            "allow_origins": cors_origins,
            "allow_credentials": True,
            "allow_methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
            "allow_headers": ["*"],
        }
    
    def get_middleware_config(self) -> Dict[str, Any]:
        """Get middleware configuration."""
        return {
            "trusted_hosts": ["*"] if settings.is_development else [
                "*.railway.app",
                "*.vercel.app", 
                "rodgersdigital.com",
                "www.rodgersdigital.com"
            ],
            "rate_limit": {
                "calls": 100,
                "period": 60,  # 100 calls per minute
            }
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration for Railway."""
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
                "railway": {
                    "format": "[%(levelname)s] %(name)s: %(message)s",
                },
            },
            "handlers": {
                "default": {
                    "formatter": "railway" if self.railway.is_railway_environment else "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
            },
            "root": {
                "level": "INFO",
                "handlers": ["default"],
            },
            "loggers": {
                "uvicorn": {"level": "INFO"},
                "uvicorn.error": {"level": "INFO"},
                "uvicorn.access": {"level": "INFO" if settings.is_development else "WARNING"},
            },
        }


# Global deployment configuration
deployment_config = DeploymentConfig()