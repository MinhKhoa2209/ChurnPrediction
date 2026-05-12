import sys
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = "development"
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"

    database_url: str
    database_pool_size: int = 20
    database_max_overflow: int = 10

    redis_url: str
    redis_cache_ttl: int = 3600

    celery_broker_url: str
    celery_result_backend: str

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    password_bcrypt_rounds: int = 12

    # OAuth Configuration
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    github_client_id: Optional[str] = None
    github_client_secret: Optional[str] = None
    microsoft_client_id: Optional[str] = None
    microsoft_client_secret: Optional[str] = None
    oauth_redirect_url: str = "http://localhost:3000/auth/callback/{provider}"

    encryption_key: str

    s3_endpoint_url: str
    s3_access_key_id: str
    s3_secret_access_key: str
    s3_bucket_models: str = "models"
    s3_bucket_reports: str = "reports"
    s3_bucket_exports: str = "exports"
    s3_region: str = "us-east-1"

    debug: bool = False

    mlflow_tracking_uri: str
    mlflow_experiment_name: str = "churn-prediction"

    cors_origins: str = "http://localhost:3000"

    rate_limit_per_minute: int = 100

    jaeger_endpoint: Optional[str] = None
    prometheus_enabled: bool = True

    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]


def load_settings() -> Settings:
    try:
        settings = Settings()
        return settings
    except Exception as e:
        print(f"ERROR: Failed to load configuration: {e}", file=sys.stderr)
        print("Please ensure all required environment variables are set.", file=sys.stderr)
        print("See .env.example for required configuration.", file=sys.stderr)
        sys.exit(1)


settings = load_settings()


def validate_configuration() -> None:
    errors = []

    if not settings.database_url.startswith(
        ("postgresql://", "postgresql+asyncpg://", "sqlite://")
    ):
        errors.append("DATABASE_URL must be a valid PostgreSQL or SQLite connection string")

    if not settings.redis_url.startswith("redis://"):
        errors.append("REDIS_URL must be a valid Redis connection string")

    if not settings.celery_broker_url.startswith("redis://"):
        errors.append("CELERY_BROKER_URL must be a valid Redis connection string")

    if not settings.celery_result_backend.startswith("redis://"):
        errors.append("CELERY_RESULT_BACKEND must be a valid Redis connection string")

    if len(settings.jwt_secret_key) < 32:
        errors.append("JWT_SECRET_KEY must be at least 32 characters long for security")

    if not 4 <= settings.password_bcrypt_rounds <= 31:
        errors.append("PASSWORD_BCRYPT_ROUNDS must be between 4 and 31")

    if not settings.encryption_key:
        errors.append("ENCRYPTION_KEY is required for encrypting sensitive data")
    else:
        import base64

        try:
            key_bytes = base64.b64decode(settings.encryption_key)
            if len(key_bytes) != 32:
                errors.append("ENCRYPTION_KEY must be a base64-encoded 32-byte (256-bit) key")
        except Exception:
            errors.append("ENCRYPTION_KEY must be a valid base64-encoded string")

    if not settings.s3_endpoint_url:
        errors.append("S3_ENDPOINT_URL is required for object storage")

    if not settings.s3_access_key_id or not settings.s3_secret_access_key:
        errors.append("S3_ACCESS_KEY_ID and S3_SECRET_ACCESS_KEY are required")

    if not settings.mlflow_tracking_uri:
        errors.append("MLFLOW_TRACKING_URI is required for experiment tracking")

    valid_environments = ["development", "staging", "production", "test"]
    if settings.environment not in valid_environments:
        errors.append(f"ENVIRONMENT must be one of: {', '.join(valid_environments)}")

    if not settings.cors_origins:
        errors.append("CORS_ORIGINS must be configured")

    if errors:
        print("=" * 80, file=sys.stderr)
        print("CONFIGURATION VALIDATION FAILED", file=sys.stderr)
        print("=" * 80, file=sys.stderr)
        for error in errors:
            print(f"  ✗ {error}", file=sys.stderr)
        print("=" * 80, file=sys.stderr)
        print("Please check your environment variables and .env file.", file=sys.stderr)
        print("See .env.example for required configuration.", file=sys.stderr)
        print("=" * 80, file=sys.stderr)
        sys.exit(1)

    if settings.environment != "production":
        print("✓ Configuration validation passed", file=sys.stderr)


validate_configuration()


def get_config_summary() -> dict:
    return {
        "environment": settings.environment,
        "debug": settings.debug,
        "database": {
            "configured": bool(settings.database_url),
            "pool_size": settings.database_pool_size,
            "max_overflow": settings.database_max_overflow,
        },
        "cache": {
            "configured": bool(settings.redis_url),
            "ttl": settings.redis_cache_ttl,
        },
        "celery": {
            "broker_configured": bool(settings.celery_broker_url),
            "backend_configured": bool(settings.celery_result_backend),
        },
        "auth": {
            "algorithm": settings.jwt_algorithm,
            "expiration_hours": settings.jwt_expiration_hours,
            "bcrypt_rounds": settings.password_bcrypt_rounds,
        },
        "storage": {
            "configured": bool(settings.s3_endpoint_url and settings.s3_access_key_id),
            "buckets": {
                "models": settings.s3_bucket_models,
                "reports": settings.s3_bucket_reports,
                "exports": settings.s3_bucket_exports,
            },
        },
        "mlflow": {
            "configured": bool(settings.mlflow_tracking_uri),
            "experiment": settings.mlflow_experiment_name,
        },
        "api": {
            "prefix": settings.api_v1_prefix,
            "cors_origins": len(settings.cors_origins_list),
            "rate_limit": settings.rate_limit_per_minute,
        },
        "email": {
            "configured": bool(settings.smtp_host and settings.smtp_user),
        },
    }
