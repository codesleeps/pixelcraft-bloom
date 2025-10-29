from functools import lru_cache
from typing import List, Optional
from pydantic import AnyHttpUrl, Field, validator
from pydantic_settings import BaseSettings
import logging


class OllamaConfig(BaseSettings):
    host: AnyHttpUrl = Field("http://localhost:11434", description="Ollama host URL")
    model: str = Field("llama3", description="Default Ollama model name")
    keep_alive: str = Field("10m", description="Keep-alive duration")
    temperature: float = Field(0.7, description="Generation temperature")
    stream: bool = Field(True, description="Enable streaming by default")


class SupabaseConfig(BaseSettings):
    url: AnyHttpUrl
    key: str
    jwt_secret: Optional[str] = None
    jwt_algorithm: str = Field("HS256", description="JWT algorithm for decoding")


class AppConfig(BaseSettings):
    app_env: str = Field("development", description="Application environment")
    app_host: str = Field("0.0.0.0", description="Host to bind the server")
    app_port: int = Field(8000, description="Port for the server")
    cors_origins: Optional[str] = Field("http://localhost:5173", description="Comma-separated CORS origins")
    log_level: str = Field("INFO", description="Logging level")

    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    supabase: Optional[SupabaseConfig] = None
    redis_url: Optional[str] = None

    @validator("app_port")
    def port_range(cls, v):
        if not (1024 <= v <= 65535):
            raise ValueError("APP_PORT must be between 1024 and 65535")
        return v

    def parsed_cors(self) -> List[str]:
        if not self.cors_origins:
            return []
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache()
def get_settings() -> AppConfig:
    # Load settings from environment automatically via pydantic-settings
    settings = AppConfig()
    # If SUPABASE_URL and SUPABASE_KEY are set, attach a SupabaseConfig
    from os import environ

    if environ.get("SUPABASE_URL") and environ.get("SUPABASE_KEY"):
        settings.supabase = SupabaseConfig(url=environ.get("SUPABASE_URL"), key=environ.get("SUPABASE_KEY"), jwt_secret=environ.get("SUPABASE_JWT_SECRET"))

    if settings.supabase and settings.supabase.jwt_secret is None:
        logging.warning("SUPABASE_JWT_SECRET is not set. JWT authentication will not work properly.")

    # Redis optional
    settings.redis_url = environ.get("REDIS_URL")

    return settings


settings = get_settings()