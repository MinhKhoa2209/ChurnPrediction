# 🎯 Customer Churn Prediction Platform

## 🎯 Overview

The **Customer Churn Prediction Platform** is a comprehensive machine learning solution that enables businesses to predict and prevent customer churn through an intuitive web interface. Built with modern technologies and following clean architecture principles, it provides end-to-end ML workflow from data ingestion to model deployment.

### Key Capabilities

- 🔄 **End-to-End ML Workflow**: Complete pipeline from data upload to predictions
- 🤖 **Multiple ML Algorithms**: KNN, Naive Bayes, Decision Tree, SVM, XGBoost, LightGBM
- ⚡ **Automated Hyperparameter Tuning**: Optuna-powered optimization
- 📊 **Model Explainability**: SHAP values for transparent predictions
- 🎯 **Flexible Predictions**: Real-time single and batch prediction modes
- 🔐 **Enterprise Security**: JWT authentication, RBAC, audit logging
- 📈 **Production Ready**: Comprehensive monitoring, error handling, and logging

---

## ✨ Features

### 📁 Data Management
- ✅ CSV data upload with real-time validation
- ✅ Automated data preprocessing pipeline
- ✅ Data quality analysis (missing values, outliers, duplicates)
- ✅ Encrypted storage for sensitive customer data
- ✅ Dataset versioning and history tracking

### 🔍 Exploratory Data Analysis (EDA)
- ✅ Interactive correlation heatmaps
- ✅ Feature distribution visualizations
- ✅ Statistical summaries and insights
- ✅ Churn rate analysis by segments
- ✅ PCA visualization (2D & 3D)

### 🧠 Model Training & Evaluation
- ✅ 6 ML algorithms with automatic selection
- ✅ Hyperparameter optimization with Optuna
- ✅ Cross-validation and performance metrics
- ✅ Model comparison dashboard
- ✅ Real-time training progress via WebSocket
- ✅ Confusion matrix and ROC curve analysis

### 🎯 Predictions
- ✅ Single customer prediction with confidence scores
- ✅ Batch prediction for CSV uploads
- ✅ SHAP-based feature importance
- ✅ Prediction history and audit trail
- ✅ Export predictions to CSV

### 📊 Reporting & Analytics
- ✅ PDF report generation with visualizations
- ✅ Interactive dashboard with KPIs
- ✅ Monthly churn trend analysis
- ✅ Model performance tracking
- ✅ Export capabilities

### 🔐 Security & Compliance
- ✅ JWT-based authentication (24-hour expiration)
- ✅ Role-based access control (Admin, Analyst)
- ✅ Rate limiting (100 requests/minute)
- ✅ Audit logging for sensitive operations
- ✅ Encrypted storage for PII data
- ✅ CORS protection

### 🚀 Performance & Reliability
- ✅ Redis caching for models and predictions
- ✅ Celery background task processing
- ✅ Database connection pooling
- ✅ Graceful error handling
- ✅ Health check endpoints
- ✅ Structured logging with request tracking

---

## 🛠 Technology Stack

### Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| **Next.js** | 16.2.4 | React framework with App Router |
| **React** | 19.2.4 | UI library |
| **TypeScript** | 5.x | Type safety |
| **TailwindCSS** | v4 | Utility-first CSS |
| **shadcn/ui** | Latest | Component library |
| **Recharts** | 3.8.1 | Data visualizations |
| **Zustand** | 5.0.12 | State management |
| **Lucide React** | 1.14.0 | Icon library |

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| **FastAPI** | 0.115.0 | Modern Python web framework |
| **Python** | 3.14 | Programming language |
| **Pydantic** | 2.10.0 | Data validation |
| **SQLAlchemy** | 2.0.36 | ORM for database |
| **Alembic** | 1.14.0 | Database migrations |
| **Celery** | 5.4.0 | Background tasks |
| **Redis** | 5.2.0 | Caching & task queue |

### Machine Learning

| Technology | Version | Purpose |
|------------|---------|---------|
| **Scikit-learn** | 1.6.0 | Classical ML algorithms |
| **XGBoost** | 2.1.3 | Gradient boosting |
| **LightGBM** | 4.5.0 | Gradient boosting |
| **Optuna** | 4.1.0 | Hyperparameter optimization |
| **SHAP** | 0.46.0 | Model explainability |
| **imbalanced-learn** | 0.12.4 | Handle imbalanced data |

### Infrastructure

| Technology | Version | Purpose |
|------------|---------|---------|
| **PostgreSQL** | 18 | Primary database |
| **Redis** | 7 | Cache & message broker |
| **MinIO/R2** | Latest | Object storage (S3-compatible) |
| **Docker** | Latest | Containerization |
| **Nginx** | Latest | Reverse proxy |

---

## 🏗 Architecture

The platform follows **Clean Architecture** principles with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                     Presentation Layer                       │
│         Next.js Frontend + FastAPI Route Handlers           │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                    Application Layer                         │
│         Service Orchestration + Business Logic              │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                      Domain Layer                            │
│         ML Pipeline + Domain Models + Schemas               │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                  Infrastructure Layer                        │
│    Database + Cache + Storage + External Services           │
└─────────────────────────────────────────────────────────────┘
```

### Design Patterns

- **Repository Pattern**: Data access abstraction
- **Service Layer Pattern**: Business logic encapsulation
- **Dependency Injection**: Loose coupling
- **Factory Pattern**: ML model creation
- **Strategy Pattern**: Algorithm selection
- **Observer Pattern**: Real-time updates

---

## 🚀 Getting Started

### Prerequisites

- **Docker** & **Docker Compose** (recommended)
- **Python** 3.14+ (for manual setup)
- **Node.js** 20+ (for manual setup)
- **PostgreSQL** 18+ (for manual setup)
- **Redis** 7+ (for manual setup)

### Quick Start with Docker

The fastest way to get started is using Docker Compose:

```bash
# 1. Clone the repository
git clone https://github.com/MinhKhoa2209/ChurnPrediction.git
cd ChurnPrediction

# 2. Create environment file
cp .env.example .env

# 3. Update .env with your configuration
# At minimum, change:
# - JWT_SECRET_KEY
# - ENCRYPTION_KEY
# - POSTGRES_PASSWORD
# - REDIS_PASSWORD

# 4. Start all services
docker-compose up -d

# 5. Check service health
docker-compose ps

# 6. View logs
docker-compose logs -f
```

**Services will be available at:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- MinIO Console: http://localhost:9001

**Default credentials:**
- Admin: `admin@churnpredict.com` / `admin123`
- Analyst: `analyst@churnpredict.com` / `analyst123`

### Manual Setup

<details>
<summary><b>Click to expand manual setup instructions</b></summary>

#### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Update .env with your configuration
# Required variables:
# - DATABASE_URL
# - REDIS_URL
# - JWT_SECRET_KEY
# - ENCRYPTION_KEY
# - S3 credentials

# Run database migrations
alembic upgrade head

# Start the backend server
python main.py
```

Backend will be available at http://localhost:8000

#### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env.local

# Update .env.local
# NEXT_PUBLIC_API_URL=http://localhost:8000

# Start development server
npm run dev
```

Frontend will be available at http://localhost:3000

#### Start Background Workers

```bash
# In backend directory with venv activated

# Start Celery worker
celery -A workers.celery_app worker --loglevel=info

# In another terminal, start Celery beat (optional)
celery -A workers.celery_app beat --loglevel=info
```

</details>

---

## 👥 User Roles & Permissions

The platform supports two user roles with different permission levels:

### 🔑 Admin
**Full platform access**
- ✅ Upload and manage datasets
- ✅ Train and manage ML models
- ✅ Create predictions (single & batch)
- ✅ Generate and view reports
- ✅ Manage users and roles
- ✅ Access all system settings
- ✅ View audit logs

### 📊 Analyst
**Read-only with prediction capabilities**
- ✅ View dashboards and reports
- ✅ Create predictions using existing models
- ✅ View datasets and models (read-only)
- ✅ Export prediction results
- ❌ Cannot upload data
- ❌ Cannot train models
- ❌ Cannot manage users

---

## 📚 API Documentation

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

### Key Endpoints

#### Authentication
```http
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/logout
GET  /api/v1/auth/me
```

#### Datasets
```http
POST /api/v1/datasets/upload
GET  /api/v1/datasets
GET  /api/v1/datasets/{id}
DELETE /api/v1/datasets/{id}
```

#### EDA
```http
GET /api/v1/eda/{dataset_id}/correlation
GET /api/v1/eda/{dataset_id}/distributions
GET /api/v1/eda/{dataset_id}/churn-by-contract
GET /api/v1/eda/{dataset_id}/scatter
GET /api/v1/eda/{dataset_id}/pca
```

#### Models
```http
POST /api/v1/training/jobs
GET  /api/v1/training/jobs
GET  /api/v1/training/jobs/{id}
GET  /api/v1/models/versions
GET  /api/v1/models/versions/{id}
PATCH /api/v1/models/versions/{id}/archive
```

#### Predictions
```http
POST /api/v1/predictions/single
POST /api/v1/predictions/batch
GET  /api/v1/predictions
GET  /api/v1/predictions/{id}
```

#### Reports
```http
POST /api/v1/reports/generate
GET  /api/v1/reports
GET  /api/v1/reports/{id}/download
```


## ⚙️ Configuration

### Environment Variables

#### Backend (.env)

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/churn_prediction
DATABASE_POOL_SIZE=20

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Object Storage (S3/R2)
S3_ENDPOINT_URL=https://your-account.r2.cloudflarestorage.com
S3_ACCESS_KEY_ID=your_access_key
S3_SECRET_ACCESS_KEY=your_secret_key
S3_BUCKET_MODELS=models
S3_BUCKET_REPORTS=reports
S3_BUCKET_EXPORTS=exports
S3_REGION=auto

# Authentication
JWT_SECRET_KEY=your-secret-key-min-32-chars
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
PASSWORD_BCRYPT_ROUNDS=12

# Encryption
ENCRYPTION_KEY=your-base64-encoded-32-byte-key

# OAuth (Optional)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
OAUTH_REDIRECT_URL=http://localhost:3000/auth/callback

# Application
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
RATE_LIMIT_PER_MINUTE=100
```

#### Frontend (.env.local)

```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/api/v1/ws

# Analytics (Optional)
NEXT_PUBLIC_SENTRY_DSN=your_sentry_dsn
NEXT_PUBLIC_GA_MEASUREMENT_ID=your_ga_id
```

### Generating Encryption Key

```bash
# Python
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Or use OpenSSL
openssl rand -base64 32
```

---

## 🔐 Security

### Authentication Flow

1. **Registration**: User creates account with email/password
2. **Login**: Credentials validated, JWT token generated (24h expiration)
3. **Token Storage**: Client stores token in localStorage
4. **Authenticated Requests**: Token sent in `Authorization: Bearer <token>` header
5. **Token Validation**: Backend validates signature and expiration
6. **Logout**: Client removes token

### Security Features

- ✅ **Password Hashing**: bcrypt with cost factor 12
- ✅ **JWT Tokens**: HS256 algorithm, 24-hour expiration
- ✅ **Rate Limiting**: 100 requests/minute per user/IP
- ✅ **CORS Protection**: Configurable allowed origins
- ✅ **Data Encryption**: Sensitive fields encrypted at rest
- ✅ **Audit Logging**: All sensitive operations logged
- ✅ **Input Validation**: Pydantic schemas for all inputs
- ✅ **SQL Injection Protection**: SQLAlchemy ORM
- ✅ **XSS Protection**: React's built-in escaping

### CORS Configuration

**Development Mode:**
```bash
ENVIRONMENT=development
# Automatically accepts all localhost variations
```

**Production Mode:**
```bash
ENVIRONMENT=production
CORS_ORIGINS=https://app.example.com,https://www.example.com
```

---

## 🚢 Deployment

### Docker Deployment

```bash
# Build and start all services
docker-compose up -d

# Scale workers
docker-compose up -d --scale celery-worker=4

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```
