import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

from .utils.ollama_client import test_ollama_connection, list_available_models, get_ollama_client
from .utils.supabase_client import get_supabase_client, test_connection as test_supabase_connection
from .utils.redis_client import get_redis_client, test_redis_connection
from .utils.external_tools import test_external_services
from .models.manager import ModelManager
from .routes.models import set_model_manager

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration, SentryAsgiMiddleware
from sentry_sdk.integrations.logging import LoggingIntegration
from .middleware.sentry_middleware import SentryContextMiddleware

logger = logging.getLogger("pixelcraft.backend")


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
    if settings.sentry:
        app.add_middleware(SentryAsgiMiddleware)

    # Add custom Sentry context middleware
    if settings.sentry:
        app.add_middleware(SentryContextMiddleware)

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

    @app.on_event("startup")
    async def startup_event():
        logger.info("Starting PixelCraft AI Backend (env=%s)", settings.app_env)
        # Initialize and validate Ollama
        try:
            ollama_ready = test_ollama_connection()
            logger.info("Ollama ready=%s", ollama_ready)
            if not ollama_ready:
                # Log available models for debugging
                models = list_available_models()
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

    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Shutting down PixelCraft AI Backend")
        # Cleanup ModelManager
        if model_manager_instance:
            await model_manager_instance.cleanup()

    @app.get("/health", tags=["health"])
    async def health():
        # Provide basic health info from dependencies
        models_healthy = 0
        models_total = 0
        if model_manager_instance:
            models_total = len(model_manager_instance._health_checks)
            models_healthy = sum(model_manager_instance._health_checks.values())
        return {
            "status": "ok",
            "service": "pixelcraft-backend",
            "env": settings.app_env,
            "ollama_available": test_ollama_connection(),
            "supabase": test_supabase_connection(),
            "redis": test_redis_connection(),
            "external_services": await test_external_services(),
            "models": {
                "healthy": models_healthy,
                "total": models_total,
            },
            "sentry_enabled": settings.sentry is not None,
        }

    @app.get("/", tags=["root"])
    async def root():
        return {"message": "Welcome to PixelCraft AI Backend", "docs": "/docs"}

    return app


app = create_app()