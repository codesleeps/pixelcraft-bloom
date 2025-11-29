import logging
import asyncio
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

import time
from .config import settings

# Import routers (these will be created in routes/)
from .routes import chat as chat_routes
from .routes import agents as agents_routes
from .routes import leads as leads_routes
from .routes import pricing as pricing_routes
from .routes import analytics as analytics_routes
from .routes import notifications as notifications_routes
from .routes import websocket as websocket_routes
from .routes import payments as payments_routes
from .routes import models as models_routes
from .routes import appointments as appointments_routes

from .utils.ollama_client import test_ollama_connection, list_available_models, get_ollama_client
from .utils.supabase_client import get_supabase_client, test_connection as test_supabase_connection
from .utils.redis_client import get_redis_client, test_redis_connection
from .utils.redis_client import get_redis_client, test_redis_connection
from .utils.external_tools import test_external_services
from .utils.health import health_service
from .models.manager import ModelManager
from .routes.models import set_model_manager

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from .middleware.sentry_middleware import SentryContextMiddleware
from .middleware.correlation import CorrelationIdMiddleware
from .utils.limiter import limiter, rate_limit_exceeded_handler
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError
from .middleware.csrf_config import get_csrf_config
from fastapi import Request, Depends
from .config import settings, get_settings

logger = logging.getLogger("pixelcraft.backend")

# Global ModelManager instance
model_manager_instance: Optional[ModelManager] = None


def create_app() -> FastAPI:
    # Initialize Sentry if configured
    if settings.sentry:
        def before_send(event, hint):
            # Filter sensitive data from events
            if 'extra' in event:
                sensitive_keys = [key for key in event['extra'].keys() if 'password' in key.lower() or 'token' in key.lower() or 'secret' in key.lower()]
                for key in sensitive_keys:
                    del event['extra'][key]
            return event

        sentry_sdk.init(
            dsn=settings.sentry.dsn,
            environment=settings.sentry.environment,
            traces_sample_rate=settings.sentry.traces_sample_rate,
            profiles_sample_rate=settings.sentry.profiles_sample_rate,
            release=settings.sentry.release,
            integrations=[FastApiIntegration(transaction_style='endpoint'), LoggingIntegration(level=logging.INFO, event_level=logging.ERROR)],
            send_default_pii=False,
            attach_stacktrace=True,
            before_send=before_send
        )
        logger.info("Sentry initialized for environment: %s, release: %s", settings.sentry.environment, settings.sentry.release or "N/A")

    app = FastAPI(title="PixelCraft AI Backend", version="1.0.0", description="AI-powered backend for PixelCraft using AgentScope and Ollama")
    
    # Initialize Rate Limiter
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    # CSRF Exception Handler
    @app.exception_handler(CsrfProtectError)
    def csrf_protect_exception_handler(request: Request, exc: CsrfProtectError):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    # CORS - parse from settings
    origins = settings.parsed_cors()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add Sentry ASGI middleware after CORS
    # if settings.sentry:
    #     app.add_middleware(SentryAsgiMiddleware)

    # Add custom Sentry context middleware
    if settings.sentry:
        app.add_middleware(SentryContextMiddleware)

    # Add Correlation ID middleware (should be early to capture all logs)
    app.add_middleware(CorrelationIdMiddleware)

    # Include routers under /api
    app.include_router(chat_routes.router, prefix="/api")
    app.include_router(agents_routes.router, prefix="/api")
    app.include_router(leads_routes.router, prefix="/api")
    app.include_router(pricing_routes.router, prefix="/api")
    app.include_router(analytics_routes.router, prefix="/api")
    app.include_router(notifications_routes.router, prefix="/api")
    app.include_router(websocket_routes.router, prefix="/api")
    app.include_router(payments_routes.router, prefix="/api")
    app.include_router(models_routes.router, prefix="/api")
    app.include_router(appointments_routes.router, prefix="/api")

    @app.on_event("startup")
    async def startup_event():
        logger.info("Starting PixelCraft AI Backend (env=%s)", settings.app_env)

        # Initialize and validate Ollama (with retries for slower startup)
        try:
            ollama_ready = False
            for attempt in range(3):
                ollama_ready = await test_ollama_connection()
                if ollama_ready:
                    break
                if attempt < 2:
                    logger.info("Ollama not ready yet, retrying... (attempt %d/3)", attempt + 1)
                    await asyncio.sleep(2)
            logger.info("Ollama ready=%s", ollama_ready)
            if not ollama_ready:
                # Log available models for debugging
                models = await list_available_models()
                logger.info("Available Ollama models: %s", models)
        except Exception as exc:
            logger.exception("Ollama initialization error: %s", exc)

        # Initialize Supabase client and test connection
        try:
            _ = get_supabase_client()
            sb_ok = test_supabase_connection()
            logger.info("Supabase connectivity: %s", sb_ok)
        except Exception as exc:
            logger.exception("Supabase initialization error: %s", exc)

        # Initialize Redis client and test connection
        try:
            _ = get_redis_client()
            redis_ok = test_redis_connection()
            logger.info("Redis connectivity: %s", redis_ok)
        except Exception as exc:
            logger.exception("Redis initialization error: %s", exc)

        # Initialize external services connectivity check
        try:
            external_services_status = await test_external_services()
            logger.info("External services status: %s", external_services_status)
        except Exception as exc:
            logger.exception("External services initialization error: %s", exc)

        # Initialize ModelManager
        try:
            global model_manager_instance
            model_manager_instance = ModelManager()
            await model_manager_instance.initialize()
            await model_manager_instance.warm_up_models()
            set_model_manager(model_manager_instance)
            logger.info("ModelManager initialized, available models: %s", list(model_manager_instance._health_checks.keys()))
        except Exception as exc:
            logger.exception("ModelManager initialization error: %s", exc)
            model_manager_instance = None  # Ensure it's None on failure

        # Initialize Agents (only if ModelManager succeeded)
        if model_manager_instance is not None:
            from .agents.orchestrator import initialize_agents
            try:
                initialize_agents(model_manager_instance)
                logger.info("Agents initialized successfully")
            except Exception as e:
                logger.exception("Failed to initialize agents: %s", e)
        else:
            logger.warning("Skipping agent initialization due to ModelManager failure")

        # Register Health Checks
        health_service.register_check("supabase", test_supabase_connection, critical=True)
        health_service.register_check("redis", test_redis_connection, critical=True)
        health_service.register_check("ollama", test_ollama_connection, critical=True)
        health_service.register_check("external_services", test_external_services, critical=False)

        # Register ModelManager check if initialized
        if model_manager_instance:
             async def check_models():
                 return len(model_manager_instance._health_checks) > 0
             health_service.register_check("models", check_models, critical=False)

    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Shutting down PixelCraft AI Backend")
        # Cleanup ModelManager
        if model_manager_instance:
            await model_manager_instance.cleanup()

    @app.get("/health", tags=["health"])
    async def health():
        """Detailed health status of all components."""
        return await health_service.get_health_status()

    @app.get("/health/live", tags=["health"])
    async def liveness_probe():
        """Liveness probe: returns 200 if the app is running."""
        return {"status": "alive", "timestamp": time.time()}

    @app.get("/health/ready", tags=["health"])
    async def readiness_probe():
        """Readiness probe: returns 200 if critical dependencies are healthy."""
        is_ready = await health_service.is_ready()
        if not is_ready:
            return JSONResponse(status_code=503, content={"status": "not_ready"})
        return {"status": "ready"}

    @app.get("/", tags=["root"])
    async def root():
        return {"message": "Welcome to PixelCraft AI Backend", "docs": "/docs"}

    @app.get("/api/csrf-token", tags=["security"])
    async def get_csrf_token(csrf_protect: CsrfProtect = Depends()):
        """Generate and return a CSRF token"""
        response = JSONResponse(status_code=200, content={"csrf_token": "set_in_cookie"})
        csrf_protect.set_csrf_cookie(response)
        return response

    @app.post("/api/rotate-secrets", tags=["security"])
    async def rotate_secrets(request: Request):
        """Reload application settings to apply new secrets without restart"""
        # In a real scenario, this would trigger a reload of the config module or specific services
        # For now, we clear the lru_cache of get_settings
        get_settings.cache_clear()
        global settings
        settings = get_settings()
        return {"status": "secrets_rotated", "timestamp": time.time()}

    return app


app = create_app()
