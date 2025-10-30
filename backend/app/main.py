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
from .routes import websocket as websocket_routes

from .utils.ollama_client import test_ollama_connection, list_available_models, get_ollama_client
from .utils.supabase_client import get_supabase_client, test_connection as test_supabase_connection
from .utils.redis_client import get_redis_client, test_redis_connection
from .utils.external_tools import test_external_services

logger = logging.getLogger("pixelcraft.backend")


def create_app() -> FastAPI:
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

    # Include routers under /api
    app.include_router(chat_routes.router, prefix="/api")
    app.include_router(agents_routes.router, prefix="/api")
    app.include_router(leads_routes.router, prefix="/api")
    app.include_router(pricing_routes.router, prefix="/api")
    app.include_router(analytics_routes.router, prefix="/api")
    app.include_router(websocket_routes.router, prefix="/api")

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

    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Shutting down PixelCraft AI Backend")

    @app.get("/health", tags=["health"])
    async def health():
        # Provide basic health info from dependencies
        return {
            "status": "ok",
            "service": "pixelcraft-backend",
            "env": settings.app_env,
            "ollama_available": test_ollama_connection(),
            "supabase": test_supabase_connection(),
            "redis": test_redis_connection(),
            "external_services": await test_external_services(),
        }

    @app.get("/", tags=["root"])
    async def root():
        return {"message": "Welcome to PixelCraft AI Backend", "docs": "/docs"}

    return app


app = create_app()
