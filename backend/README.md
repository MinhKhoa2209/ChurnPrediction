# Customer Churn Prediction Platform - Backend

FastAPI backend service for the Customer Churn Prediction Platform.

## Technology Stack

- **Python**: 3.14
- **Framework**: FastAPI
- **Database**: PostgreSQL 18 with SQLAlchemy 2.x
- **Cache**: Redis
- **Task Queue**: Celery
- **ML Libraries**: Scikit-learn, XGBoost, LightGBM, MLflow, Optuna, SHAP
- **Authentication**: JWT with bcrypt
- **Object Storage**: Cloudflare R2 (S3-compatible via boto3)

## Setup

### Prerequisites

- Python 3.14+
- PostgreSQL 18
- Redis
- MinIO (for local development)

### Installation

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Copy environment variables:
```bash
cp .env.example .env
```

4. Update `.env` with your configuration

### Running the Server

Development mode with auto-reload:
```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI Schema: http://localhost:8000/openapi.json

## Project Structure

```
backend/
├── main.py                 # Application entry point
├── api/                    # API routes and endpoints
│   ├── routes/            # Route handlers
│   ├── dependencies.py    # Dependency injection
│   └── middleware.py      # Custom middleware
├── services/              # Business logic services
├── domain/                # Domain models and schemas
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   └── ml/               # ML pipeline components
├── infrastructure/        # External service integrations
│   ├── database.py       # Database connection
│   ├── cache.py          # Redis client
│   ├── storage.py        # S3/R2 client
│   └── mlflow_client.py  # MLflow integration
├── workers/               # Celery background tasks
├── utils/                 # Utility functions
└── tests/                 # Test suite
```

## Environment Variables

See `.env.example` for all available configuration options.

### CORS Configuration

The backend uses different CORS configurations based on the environment:

**Development Mode (`ENVIRONMENT=development`):**
- Automatically accepts all localhost variations (localhost, 127.0.0.1, any port)
- Uses regex pattern matching: `http://(localhost|127\.0\.0\.1)(:[0-9]+)?`
- Simplifies local development - no need to update CORS whitelist for different ports
- Credentials are allowed for authentication

**Production Mode (`ENVIRONMENT=production`):**
- Uses explicit whitelist from `CORS_ORIGINS` environment variable
- Only listed origins are accepted for security
- Format: Comma-separated list of full URLs with protocol
- Example: `CORS_ORIGINS=https://app.example.com,https://www.example.com`
- No trailing slashes in origin URLs

**Configuration in `.env`:**
```bash
# Environment mode (development or production)
ENVIRONMENT=development

# CORS allowed origins (used in production mode)
# In development, all localhost variations are automatically allowed
CORS_ORIGINS=http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000
```

**Troubleshooting CORS:**
- Check backend logs for CORS rejection messages
- Verify `ENVIRONMENT` variable is set correctly
- In production, ensure frontend domain is in `CORS_ORIGINS` list
- Use browser DevTools Network tab to see the exact origin being sent

## Requirements

- Requirements 29.1, 29.2: Backend loads configuration from environment variables
- Requirements 29.3, 29.4: Configuration validation on startup

## Authentication

The backend uses JWT (JSON Web Token) based authentication with bcrypt password hashing.

### Token Generation

**Login Flow:**
1. User submits email and password to `/api/v1/auth/login`
2. Backend validates credentials against database
3. If valid, generates JWT token with 24-hour expiration
4. Returns token and user object to client
5. Client stores token for subsequent authenticated requests

**Token Structure:**
- Algorithm: HS256 (HMAC with SHA-256)
- Expiration: 24 hours from generation
- Payload includes: user_id, email, role, exp (expiration timestamp)
- Signed with `SECRET_KEY` from environment variables

### Token Validation

**Protected Endpoints:**
- All endpoints except `/auth/login` and `/auth/register` require authentication
- Token must be provided in `Authorization` header: `Bearer <token>`
- Backend validates token signature and expiration on every request
- Invalid or expired tokens return 401 Unauthorized

**Validation Process:**
1. Extract token from Authorization header
2. Verify token signature using SECRET_KEY
3. Check token expiration timestamp
4. Extract user_id from token payload
5. Load user from database (optional, for fresh user data)
6. Inject user object into request context

### Token Expiration

**Behavior:**
- Tokens expire exactly 24 hours after generation
- Expired tokens are rejected with 401 Unauthorized
- Users must log in again to generate a new token
- No automatic token refresh (future enhancement)

**Handling Expiration:**
- Frontend should catch 401 errors and redirect to login
- Backend logs token expiration events for monitoring
- Consider implementing token refresh for better UX (future work)

### Security Considerations

**Password Storage:**
- Passwords are hashed using bcrypt with automatic salt generation
- Never store or log plaintext passwords
- Password validation uses constant-time comparison

**Token Security:**
- Tokens are signed to prevent tampering
- SECRET_KEY must be kept secure and rotated periodically
- Use HTTPS in production to prevent token interception
- Tokens are stateless - no server-side session storage required

**Rate Limiting:**
- Login endpoint is rate-limited to prevent brute force attacks
- Maximum 100 requests per minute per IP address
- Failed login attempts are logged for security monitoring

**CORS and Credentials:**
- `Access-Control-Allow-Credentials: true` is set for authenticated requests
- Ensures cookies and authorization headers are sent cross-origin
- CORS origin validation prevents unauthorized domains from accessing the API
