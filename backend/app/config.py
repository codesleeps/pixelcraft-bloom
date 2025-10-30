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


class CRMConfig(BaseSettings):
    provider: str = Field("hubspot", description="CRM provider (hubspot, salesforce)")
    api_key: Optional[str] = None
    api_url: Optional[str] = Field("https://api.hubapi.com", description="CRM API base URL")

    @validator("api_key")
    def check_api_key(cls, v):
        if v is None:
            raise ValueError("api_key must be set when provider is configured")
        return v


class EmailConfig(BaseSettings):
    provider: str = Field("sendgrid", description="Email provider (sendgrid, mailgun)")
    api_key: Optional[str] = None
    from_email: Optional[str] = Field("noreply@pixelcraft.com", description="Default sender email")

    @validator("api_key")
    def check_api_key(cls, v):
        if v is None:
            raise ValueError("api_key must be set when provider is configured")
        return v


class CalendarConfig(BaseSettings):
    provider: str = Field("google", description="Calendar provider (google, outlook)")
    api_key: Optional[str] = None
    calendar_id: Optional[str] = None
    oauth_credentials_path: Optional[str] = None

    @validator("api_key", "calendar_id")
    def check_credentials(cls, v):
        if v is None:
            raise ValueError("credentials must be configured")
        return v


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
    crm: Optional[CRMConfig] = None
    email: Optional[EmailConfig] = None
    calendar: Optional[CalendarConfig] = None

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

    # Load external service configurations
    crm_api_key = environ.get("CRM_API_KEY")
    if crm_api_key:
        settings.crm = CRMConfig(
            provider=environ.get("CRM_PROVIDER", "hubspot"),
            api_key=crm_api_key,
            api_url=environ.get("CRM_API_URL", "https://api.hubapi.com")
        )
    elif environ.get("CRM_PROVIDER"):
        logging.warning("CRM_API_KEY is not set. CRM integration will not work properly.")

    email_api_key = environ.get("EMAIL_API_KEY")
    if email_api_key:
        settings.email = EmailConfig(
            provider=environ.get("EMAIL_PROVIDER", "sendgrid"),
            api_key=email_api_key,
            from_email=environ.get("EMAIL_FROM", "noreply@pixelcraft.com")
        )
    elif environ.get("EMAIL_PROVIDER"):
        logging.warning("EMAIL_API_KEY is not set. Email integration will not work properly.")

    calendar_api_key = environ.get("CALENDAR_API_KEY")
    if calendar_api_key:
        settings.calendar = CalendarConfig(
            provider=environ.get("CALENDAR_PROVIDER", "google"),
            api_key=calendar_api_key,
            calendar_id=environ.get("CALENDAR_ID"),
            oauth_credentials_path=environ.get("CALENDAR_OAUTH_CREDENTIALS_PATH")
        )
    elif environ.get("CALENDAR_PROVIDER"):
        logging.warning("CALENDAR_API_KEY is not set. Calendar integration will not work properly.")
    elif environ.get("CALENDAR_ID") and not calendar_api_key:
        logging.warning("CALENDAR_API_KEY is not set. Calendar integration will not work properly.")

    return settings


settings = get_settings()
