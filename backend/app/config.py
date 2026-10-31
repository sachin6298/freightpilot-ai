"""Central configuration for FreightPilot AI."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    APP_ENV: str = "development"
    DEMO_MODE: bool = True
    AUTO_CREATE_DB: bool = True
    DATABASE_URL: str = "sqlite:///./freightpilot.db"
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    # Authentication remains optional for the existing local demo frontend.
    # Set AUTH_REQUIRED=true before exposing the API to real users.
    AUTH_REQUIRED: bool = False
    JWT_SECRET_KEY: str = "development-only-change-this-secret-before-deploying"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    PAYPAL_ENV: str = "sandbox"
    PAYPAL_CLIENT_ID: str = ""
    PAYPAL_CLIENT_SECRET: str = ""
    PAYPAL_WEBHOOK_ID: str = ""
    PAYPAL_TIMEOUT_SECONDS: float = 15.0

    AI_PROVIDER: str = "gemini"
    AI_API_KEY: str = ""
    AI_MODEL: str = ""

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"


settings = Settings()

if settings.is_production and (
    len(settings.JWT_SECRET_KEY) < 32
    or settings.JWT_SECRET_KEY.lower().startswith(("development-only", "replace_", "change-me"))
):
    raise RuntimeError("Set a random JWT_SECRET_KEY of at least 32 characters before production deployment.")
if settings.is_production and not settings.AUTH_REQUIRED:
    raise RuntimeError("Set AUTH_REQUIRED=true before exposing FreightPilot AI in production.")
if settings.is_production and settings.DEMO_MODE:
    raise RuntimeError("Set DEMO_MODE=false before production deployment.")
if settings.JWT_ALGORITHM not in {"HS256", "HS384", "HS512"}:
    raise RuntimeError("JWT_ALGORITHM must be one of HS256, HS384, or HS512.")
if settings.DEMO_MODE and settings.PAYPAL_ENV.lower() != "sandbox":
    raise RuntimeError("DEMO_MODE requires PAYPAL_ENV=sandbox. Live payments are disabled in demo mode.")
