"""Validated application configuration. Secrets are supplied only via environment variables."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"), env_file_encoding="utf-8",
        extra="ignore", case_sensitive=False,
    )

    APP_ENV: str = "development"
    DEMO_MODE: bool = True
    AUTO_CREATE_DB: bool = False
    DATABASE_URL: str = "sqlite:///./freightpilot.db"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    FRONTEND_ORIGIN: str = "http://localhost:5173"
    GOOGLE_CLIENT_ID: str = ""
    APPLE_CLIENT_ID: str = ""
    APPLE_TEAM_ID: str = ""
    APPLE_KEY_ID: str = ""
    APPLE_PRIVATE_KEY: str = ""
    APPLE_REDIRECT_URI: str = ""
    CORS_ALLOWED_ORIGINS: str = ""
    API_PUBLIC_URL: str = "http://localhost:8000"

    AUTH_REQUIRED: bool = False
    JWT_SECRET_KEY: str = "development-only-change-this-secret-before-deploying"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=20, ge=5, le=120)

    PAYPAL_ENV: str = "sandbox"
    PAYPAL_CLIENT_ID: str = ""
    PAYPAL_CLIENT_SECRET: str = ""
    PAYPAL_WEBHOOK_ID: str = ""
    PAYPAL_TIMEOUT_SECONDS: float = 15.0

    AI_PROVIDER: str = "gemini"
    AI_API_KEY: str = ""
    AI_MODEL: str = "gemini-2.5-flash"

    EMAIL_PROVIDER: str = "console"
    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = "FreightPilot <no-reply@example.com>"
    SMS_PROVIDER: str = "console"
    FIREBASE_PROJECT_ID: str = ""
    FIREBASE_SERVICE_ACCOUNT_JSON: str = ""

    REDIS_URL: str = ""
    RATE_LIMIT_ENABLED: bool = True
    STORAGE_BACKEND: str = "postgresql"  # postgresql | local | s3
    DOCUMENT_STORAGE_PATH: str = "./var/documents"
    S3_BUCKET: str = ""
    S3_REGION: str = "auto"
    S3_ENDPOINT_URL: str = ""
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    MAX_UPLOAD_BYTES: int = Field(default=10 * 1024 * 1024, ge=1024, le=50 * 1024 * 1024)
    CLAMAV_HOST: str = ""
    CLAMAV_PORT: int = Field(default=3310, ge=1, le=65535)

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"


settings = Settings()

if settings.APP_ENV.lower() not in {"development", "test", "staging", "production"}:
    raise RuntimeError("APP_ENV must be development, test, staging, or production.")
if settings.JWT_ALGORITHM not in {"HS256", "HS384", "HS512"}:
    raise RuntimeError("JWT_ALGORITHM must be one of HS256, HS384, or HS512.")
if settings.PAYPAL_ENV.lower() not in {"sandbox", "live"}:
    raise RuntimeError("PAYPAL_ENV must be sandbox or live.")
if settings.DEMO_MODE and settings.PAYPAL_ENV.lower() == "live":
    raise RuntimeError("DEMO_MODE cannot be combined with live PayPal payments.")
if settings.is_production:
    if len(settings.JWT_SECRET_KEY) < 43 or settings.JWT_SECRET_KEY.lower().startswith(("development-only", "replace_", "change-me")):
        raise RuntimeError("Production requires a randomly generated JWT_SECRET_KEY of at least 43 characters (approximately 256 bits of entropy).")
    if not settings.AUTH_REQUIRED:
        raise RuntimeError("Production requires AUTH_REQUIRED=true.")
    if settings.DEMO_MODE:
        raise RuntimeError("Production requires DEMO_MODE=false.")
    if not settings.DATABASE_URL.startswith(("postgresql://", "postgresql+psycopg://", "postgres://")):
        raise RuntimeError("Production requires PostgreSQL using the psycopg driver.")
    if not settings.FRONTEND_ORIGIN.startswith("https://"):
        raise RuntimeError("Production FRONTEND_ORIGIN must be an HTTPS origin.")
    production_origins = [settings.FRONTEND_ORIGIN.strip()] + [item.strip() for item in settings.CORS_ALLOWED_ORIGINS.split(",") if item.strip()]
    if any("*" in origin or not origin.startswith("https://") for origin in production_origins):
        raise RuntimeError("Production CORS origins must be explicit HTTPS origins; wildcard origins are forbidden.")
    if settings.RATE_LIMIT_ENABLED and not settings.REDIS_URL:
        raise RuntimeError("Production rate limiting requires REDIS_URL.")
    if settings.EMAIL_PROVIDER != "resend" or not settings.RESEND_API_KEY:
        raise RuntimeError("Production requires EMAIL_PROVIDER=resend and RESEND_API_KEY.")
    if not settings.EMAIL_FROM or "example.com" in settings.EMAIL_FROM.lower():
        raise RuntimeError("Production EMAIL_FROM must use a verified sending domain.")
    if settings.SMS_PROVIDER != "firebase" or not settings.FIREBASE_PROJECT_ID or not settings.FIREBASE_SERVICE_ACCOUNT_JSON:
        raise RuntimeError("Production requires SMS_PROVIDER=firebase with credentials.")
    if not all([settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET]):
        raise RuntimeError("Production requires PayPal client ID and client secret.")
    if settings.STORAGE_BACKEND != "postgresql":
        raise RuntimeError("Production requires STORAGE_BACKEND=postgresql.")
    if not settings.API_PUBLIC_URL.startswith("https://"):
        raise RuntimeError("Production API_PUBLIC_URL must be HTTPS.")
