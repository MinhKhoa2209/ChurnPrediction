import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from backend.api.exception_handlers import register_exception_handlers
from backend.api.middleware import (
    DegradedModeMiddleware,
    RateLimitMiddleware,
    RequestIDMiddleware,
    RequestLoggingMiddleware,
    UserContextMiddleware,
    get_redis_client,
)
from backend.api.routes import (
    auth,
    dashboard,
    datasets,
    eda,
    features,
    models,
    notifications,
    oauth,
    predictions,
    reports,
    users,
    websocket,
)
from backend.config import get_config_summary, settings

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


openapi_tags_metadata = [
    {
        "name": "Authentication",
        "description": "User authentication and authorization endpoints. Includes registration, login, logout, and password management.",
    },
    {
        "name": "OAuth Authentication",
        "description": "OAuth 2.0 authentication endpoints. Sign in with Google, GitHub, or Microsoft accounts.",
    },
    {
        "name": "Datasets",
        "description": "Dataset management endpoints. Upload, list, retrieve, and delete customer datasets for churn prediction.",
    },
    {
        "name": "EDA",
        "description": "Exploratory Data Analysis endpoints. Generate correlation matrices, distributions, and visualizations.",
    },
    {
        "name": "Features",
        "description": "Feature engineering endpoints. Analyze feature importance and manage feature transformations.",
    },
    {
        "name": "Models",
        "description": "ML model management endpoints. List, retrieve, and manage trained churn prediction models.",
    },
    {
        "name": "Training",
        "description": "Model training endpoints. Start training jobs, monitor progress, and manage hyperparameter optimization.",
    },
    {
        "name": "Predictions",
        "description": "Prediction endpoints. Generate churn predictions for individual customers or batches.",
    },
    {
        "name": "Reports",
        "description": "Report generation endpoints. Create and download PDF reports with model insights and predictions.",
    },
    {
        "name": "Dashboard",
        "description": "Dashboard data endpoints. Retrieve aggregated metrics and statistics for the main dashboard.",
    },
    {
        "name": "Users",
        "description": "User management endpoints. Admin-only endpoints for managing user accounts and roles.",
    },
    {
        "name": "Notifications",
        "description": "Notification endpoints. Retrieve and manage user notifications for training jobs and system events.",
    },
    {
        "name": "WebSocket",
        "description": "WebSocket endpoints. Real-time updates for training progress and system events.",
    },
]

app = FastAPI(
    title="Customer Churn Prediction Platform API",
    description="""
Overview

The Customer Churn Prediction Platform API provides a comprehensive machine learning solution for predicting customer churn. 
This production-ready API enables data scientists, analysts, and developers to:

- Upload and manage customer datasets
- Perform exploratory data analysis (EDA)
- Engineer and analyze features
- Train ML models with hyperparameter optimization
- Generate predictions for individual customers or batches
- Create detailed reports with model insights
- Monitor training progress in real-time

Authentication

Most endpoints require JWT authentication. Include the access token in the Authorization header:

```
Authorization: Bearer <your_access_token>
```

Obtain an access token by calling the `/api/v1/auth/login` endpoint with valid credentials.

Rate Limiting

API requests are rate-limited to 100 requests per minute per user/IP address. 
Rate limit information is included in response headers:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Time when the rate limit resets (Unix timestamp)

Error Responses

All error responses follow a consistent format with the following fields:
- `error`: Error code (e.g., "VALIDATION_ERROR", "UNAUTHORIZED")
- `message`: Human-readable error message
- `details`: Additional error details (optional)
- `requestId`: Unique request identifier for debugging
- `timestamp`: ISO 8601 timestamp of the error

Common HTTP status codes:
- `400 Bad Request`: Invalid request data or parameters
- `401 Unauthorized`: Missing or invalid authentication token
- `403 Forbidden`: Insufficient permissions for the requested resource
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error in request body
- `503 Service Unavailable`: Service temporarily unavailable (degraded mode)

Versioning

The API is versioned using URL path prefixes. Current version: `v1`

Base URL: `/api/v1`

Support

For issues or questions, please contact the platform administrators.
    """,
    version="1.0.0",
    openapi_tags=openapi_tags_metadata,
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url="/redoc" if settings.environment == "development" else None,
    openapi_url="/openapi.json",
    contact={
        "name": "Platform Support",
        "email": "support@churnplatform.example.com",
    },
    license_info={
        "name": "Proprietary",
    },
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "Development server",
        },
        {
            "url": "https://api.churnplatform.example.com",
            "description": "Production server",
        },
    ],
    swagger_ui_parameters={
        "persistAuthorization": True,
        "displayRequestDuration": True,
        "filter": True,
        "tryItOutEnabled": True,
        "docExpansion": "none",
        "defaultModelsExpandDepth": 1,
    },
)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    from fastapi.openapi.utils import get_openapi

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=app.openapi_tags,
        servers=app.servers,
        terms_of_service=app.terms_of_service,
        contact=app.contact,
        license_info=app.license_info,
    )

    if "components" not in openapi_schema:
        openapi_schema["components"] = {}

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your JWT token obtained from the /api/v1/auth/login endpoint",
        }
    }

    for path, path_item in openapi_schema["paths"].items():
        if "/auth/login" in path or "/auth/register" in path:
            continue

        for method in path_item:
            if method in ["get", "post", "put", "delete", "patch"]:
                if "security" not in path_item[method]:
                    path_item[method]["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


if settings.environment != "development":
    from typing import Annotated

    from fastapi import Depends
    from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html

    from backend.api.dependencies import get_current_user
    from backend.domain.schemas.auth import UserResponse

    @app.get("/docs", include_in_schema=False)
    async def get_swagger_documentation(
        current_user: Annotated[UserResponse, Depends(get_current_user)],
    ):
        return get_swagger_ui_html(
            openapi_url="/openapi.json",
            title=f"{app.title} - Swagger UI",
            swagger_favicon_url="/favicon.ico",
            swagger_ui_parameters={
                "persistAuthorization": True,
                "displayRequestDuration": True,
                "filter": True,
                "tryItOutEnabled": True,
            },
        )

    @app.get("/redoc", include_in_schema=False)
    async def get_redoc_documentation(
        current_user: Annotated[UserResponse, Depends(get_current_user)],
    ):
        return get_redoc_html(
            openapi_url="/openapi.json",
            title=f"{app.title} - ReDoc",
            redoc_favicon_url="/favicon.ico",
            with_google_fonts=True,
        )


register_exception_handlers(app)

# Add SessionMiddleware for OAuth (must be added before other middleware)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.jwt_secret_key,
    session_cookie="churn_session",
    max_age=3600,  # 1 hour
    same_site="lax",
    https_only=settings.environment == "production",
)

# Add CORS middleware (must be added early to handle preflight requests)
if settings.environment == "development":
    from backend.api.cors_middleware import DevelopmentCORSMiddleware

    app.add_middleware(
        DevelopmentCORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.add_middleware(RequestIDMiddleware)


app.add_middleware(DegradedModeMiddleware)


app.add_middleware(UserContextMiddleware)


app.add_middleware(RequestLoggingMiddleware)


redis_client = get_redis_client()
app.add_middleware(RateLimitMiddleware, redis_client=redis_client)


app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(oauth.router, prefix=settings.api_v1_prefix)
app.include_router(dashboard.router, prefix=settings.api_v1_prefix)
app.include_router(datasets.router, prefix=settings.api_v1_prefix)
app.include_router(eda.router, prefix=settings.api_v1_prefix)
app.include_router(features.router, prefix=settings.api_v1_prefix)
app.include_router(models.router, prefix=settings.api_v1_prefix)
app.include_router(notifications.router, prefix=settings.api_v1_prefix)
app.include_router(predictions.router, prefix=settings.api_v1_prefix)
app.include_router(reports.router, prefix=settings.api_v1_prefix)
app.include_router(users.router, prefix=settings.api_v1_prefix)
app.include_router(websocket.router, prefix=settings.api_v1_prefix)


@app.get("/")
async def root():
    logger.info("Health check endpoint accessed")
    return {
        "status": "healthy",
        "service": "Customer Churn Prediction Platform API",
        "version": "1.0.0",
        "environment": settings.environment,
    }


@app.get("/health")
async def health_check():
    from fastapi.responses import JSONResponse

    from backend.infrastructure.cache import get_cache_status
    from backend.infrastructure.database import check_database_health

    logger.info("Detailed health check endpoint accessed")
    config_summary = get_config_summary()

    cache_status = get_cache_status()

    db_available = check_database_health()

    if not db_available:
        logger.error("Health check failed: Database unavailable")
        return JSONResponse(
            content={
                "status": "unavailable",
                "degraded_mode": False,
                "services": {
                    "database": {"available": False, "status": "unavailable"},
                    "cache": cache_status,
                },
                "configuration": config_summary,
            },
            status_code=503,
            headers={"Retry-After": "60"},
        )

    degraded = not cache_status["available"]
    overall_status = "degraded" if degraded else "healthy"

    return {
        "status": overall_status,
        "degraded_mode": degraded,
        "services": {
            "database": {"available": db_available, "status": "healthy"},
            "cache": cache_status,
        },
        "configuration": config_summary,
    }


@app.on_event("startup")
async def startup_event():
    logger.info("=" * 80)
    logger.info("Customer Churn Prediction Platform API Starting")
    logger.info("=" * 80)
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Log Level: {settings.log_level}")
    logger.info(f"API Prefix: {settings.api_v1_prefix}")
    logger.info("=" * 80)


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("=" * 80)
    logger.info("Customer Churn Prediction Platform API Shutting Down")
    logger.info("=" * 80)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
