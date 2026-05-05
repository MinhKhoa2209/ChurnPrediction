"""
Configuration Management
Loads and validates configuration from environment variables

This module provides centralized configuration management for the Customer Churn
Prediction Platform backend. All configuration is loaded from environment variables
and validated on startup to ensure the application has all required settings.

Configuration Sources (in order of precedence):
1. Environment variables
2. .env file in the backend directory
3. Default values (where applicable)

Required Configuration:
- Database: DATABASE_URL (PostgreSQL connection string)
- Cache: REDIS_URL, CELERY_BROKER_URL, CELERY_RESULT_BACKEND
- Authentication: JWT_SECRET_KEY (minimum 32 characters)
- Storage: S3_ENDPOINT_URL, S3_ACCESS_KEY_ID, S3_SECRET_ACCESS_KEY
- MLflow: MLFLOW_TRACKING_URI

See .env.example for a complete list of configuration options.
"""

import os
import sys
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    environment: str = "development"
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"

    # Database Configuration
    database_url: str
    database_pool_size: int = 20
    database_max_overflow: int = 10

    # Redis Configuration
    redis_url: str
    redis_cache_ttl: int = 3600

    # Celery Configuration
    celery_broker_url: str
    celery_result_backend: str

    # Authentication
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    password_bcrypt_rounds: int = 12

    # Encryption
    encryption_key: str

    # Cloudflare R2 / MinIO Configuration
    s3_endpoint_url: str
    s3_access_key_id: str
    s3_secret_access_key: str
    s3_bucket_models: str = "models"
    s3_bucket_reports: str = "reports"
    s3_bucket_exports: str = "exports"
    s3_region: str = "us-east-1"
    
    # Debug mode
    debug: bool = False

    # MLflow Configuration
    mlflow_tracking_uri: str
    mlflow_experiment_name: str = "churn-prediction"

    # CORS Configuration
    cors_origins: str = "http://localhost:3000"

    # Rate Limiting
    rate_limit_per_minute: int = 100

    # Monitoring and Observability
    jaeger_endpoint: Optional[str] = None  # e.g., "http://jaeger:4317"
    prometheus_enabled: bool = True

    # Email Configuration (Optional)
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
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.cors_origins.split(",")]


def load_settings() -> Settings:
    """
    Load and validate settings from environment variables
    """
    try:
        settings = Settings()  # type: ignore
        return settings
    except Exception as e:
        # Log error and exit with non-zero status if config is missing
        print(f"ERROR: Failed to load configuration: {e}", file=sys.stderr)
        print("Please ensure all required environment variables are set.", file=sys.stderr)
        print("See .env.example for required configuration.", file=sys.stderr)
        sys.exit(1)


# Global settings instance
settings = load_settings()


def validate_configuration() -> None:
    """
    Validate critical configuration values
    """
    errors = []

    # Validate database URL
    if not settings.database_url.startswith(("postgresql://", "postgresql+asyncpg://", "sqlite://")):
        errors.append("DATABASE_URL must be a valid PostgreSQL or SQLite connection string")

    # Validate Redis URL
    if not settings.redis_url.startswith("redis://"):
        errors.append("REDIS_URL must be a valid Redis connection string")

    # Validate Celery broker and result backend
    if not settings.celery_broker_url.startswith("redis://"):
        errors.append("CELERY_BROKER_URL must be a valid Redis connection string")
    
    if not settings.celery_result_backend.startswith("redis://"):
        errors.append("CELERY_RESULT_BACKEND must be a valid Redis connection string")

    # Validate JWT secret key
    if len(settings.jwt_secret_key) < 32:
        errors.append("JWT_SECRET_KEY must be at least 32 characters long for security")

    # Validate bcrypt cost factor
    if not 4 <= settings.password_bcrypt_rounds <= 31:
        errors.append("PASSWORD_BCRYPT_ROUNDS must be between 4 and 31")

    # Validate encryption key
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

    # Validate S3/R2 configuration
    if not settings.s3_endpoint_url:
        errors.append("S3_ENDPOINT_URL is required for object storage")

    if not settings.s3_access_key_id or not settings.s3_secret_access_key:
        errors.append("S3_ACCESS_KEY_ID and S3_SECRET_ACCESS_KEY are required")

    # Validate MLflow configuration
    if not settings.mlflow_tracking_uri:
        errors.append("MLFLOW_TRACKING_URI is required for experiment tracking")

    # Validate environment value
    valid_environments = ["development", "staging", "production", "test"]
    if settings.environment not in valid_environments:
        errors.append(f"ENVIRONMENT must be one of: {', '.join(valid_environments)}")

    # Validate CORS origins
    if not settings.cors_origins:
        errors.append("CORS_ORIGINS must be configured")

    if errors:
        # Log error and exit with non-zero status if config is missing
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
    
    # Log successful validation in non-production environments
    if settings.environment != "production":
        print("✓ Configuration validation passed", file=sys.stderr)


# Validate configuration on module import
validate_configuration()


def get_config_summary() -> dict:
    """
    Get a summary of configuration status without exposing sensitive values.
    Useful for health checks and debugging.
    
    Returns:
        Dictionary with configuration status for each component
    """
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
