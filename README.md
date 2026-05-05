# Customer Churn Prediction Platform

## 🎯 Overview

The Customer Churn Prediction Platform is an enterprise-grade machine learning application that enables data scientists, business analysts, and customer success teams to predict and prevent customer churn through an intuitive web interface.

### Key Capabilities

- **End-to-End ML Workflow**: From data ingestion to model deployment
- **Multiple ML Algorithms**: KNN, Naive Bayes, Decision Tree, SVM, XGBoost, LightGBM
- **Automated Hyperparameter Tuning**: Using Optuna for optimal model performance
- **Model Explainability**: SHAP values for transparent predictions
- **Real-time & Batch Predictions**: Flexible prediction modes for different use cases
- **Role-Based Access Control**: Secure multi-user environment with three role levels
- **Production-Ready**: Comprehensive error handling, logging, and monitoring

## ✨ Features

### Data Management
- ✅ CSV data upload with validation
- ✅ Automated data preprocessing pipeline
- ✅ Data quality analysis (missing values, outliers, duplicates)
- ✅ Encrypted storage of sensitive customer data

### Exploratory Data Analysis
- ✅ Interactive correlation matrices
- ✅ Distribution visualizations
- ✅ Statistical summaries
- ✅ Feature relationship analysis

### Model Training & Evaluation
- ✅ Multiple ML model support (6 algorithms)
- ✅ Automated hyperparameter optimization
- ✅ Cross-validation and performance metrics
- ✅ Model comparison and selection
- ✅ Real-time training progress monitoring via WebSocket
- ✅ MLflow integration for experiment tracking

### Predictions
- ✅ Single customer prediction with confidence scores
- ✅ Batch prediction for multiple customers
- ✅ SHAP-based feature importance for each prediction
- ✅ Prediction history and audit trail

### Reporting & Insights
- ✅ PDF report generation with model insights
- ✅ Dashboard with key metrics and visualizations
- ✅ Monthly churn trend analysis
- ✅ Export capabilities for predictions and reports

### Security & Compliance
- ✅ JWT-based authentication with 24-hour token expiration
- ✅ Role-based access control (Admin, Data Scientist, Analyst)
- ✅ Rate limiting (100 requests/minute per user)
- ✅ Audit logging for security-sensitive operations
- ✅ Encrypted storage for sensitive data fields

### Reliability & Performance
- ✅ Graceful degradation when cache is unavailable
- ✅ Database connection retry logic
- ✅ Comprehensive error handling
- ✅ Structured logging with request tracking
- ✅ Health check endpoints

## 🛠 Technology Stack

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| **Next.js** | 16.2.4 | React framework with App Router |
| **React** | 19.2.4 | UI library |
| **TypeScript** | 5.x | Type safety |
| **TailwindCSS** | v4 | Utility-first CSS framework |
| **shadcn/ui** | Latest | Component library |
| **Recharts** | 3.8.1 | Data visualizations |
| **Zustand** | 5.0.12 | Client state management |
| **React Hot Toast** | 2.6.0 | Notifications |

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| **FastAPI** | 0.115.0 | Modern Python web framework |
| **Python** | 3.14 | Programming language |
| **Pydantic** | v3 | Data validation |
| **SQLAlchemy** | 2.0.36 | ORM for database operations |
| **Alembic** | Latest | Database migrations |
| **Celery** | 5.4.0 | Background task processing |
| **Redis** | 5.2.0 | Caching and task queue |

### Machine Learning
| Technology | Version | Purpose |
|------------|---------|---------|
| **Scikit-learn** | 1.6.0 | Classical ML algorithms |
| **XGBoost** | 2.1.3 | Gradient boosting |
| **LightGBM** | 4.5.0 | Gradient boosting |
| **Optuna** | 4.1.0 | Hyperparameter optimization |
| **SHAP** | 0.46.0 | Model explainability |
| **MLflow** | 2.18.0 | Experiment tracking |
| **imbalanced-learn** | 0.12.4 | Handling imbalanced datasets |

### Data Layer
| Technology | Version | Purpose |
|------------|---------|---------|
| **PostgreSQL** | 18 | Primary database |
| **Redis** | Latest | Caching and session storage |
| **Cloudflare R2** | - | S3-compatible object storage |

### Infrastructure & DevOps
| Technology | Purpose |
|------------|---------|
| **Docker** | Containerization |
| **GitHub Actions** | CI/CD pipeline |
| **Vercel** | Frontend hosting |
| **Railway** | Backend hosting |
| **Sentry** | Error tracking |

## 🏗 Architecture

The platform follows **Clean Architecture** principles with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                     Presentation Layer                       │
│  (Next.js Frontend + FastAPI Route Handlers)                │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                    Application Layer                         │
│  (Service Orchestration + Business Logic)                   │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                      Domain Layer                            │
│  (ML Pipeline + Domain Models + Schemas)                    │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                  Infrastructure Layer                        │
│  (Database + Cache + Storage + External Services)           │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Patterns

- **Repository Pattern**: Data access abstraction
- **Service Layer Pattern**: Business logic encapsulation
- **Dependency Injection**: Loose coupling between components
- **Factory Pattern**: ML model creation
- **Strategy Pattern**: Different ML algorithms
- **Observer Pattern**: Real-time training progress updates

## 🚀 Getting Started

### Prerequisites


### Quick Start

#### 1. Clone the Repository

```bash
git clone https://github.com/MinhKhoa2209/ChurnPrediction.git
cd churn-prediction-platform
```

#### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env

# Update .env with your configuration
# Required: DATABASE_URL, REDIS_URL, JWT_SECRET_KEY, ENCRYPTION_KEY, S3 credentials

# Run database migrations
alembic upgrade head

# Start the backend server
python main.py
```

The backend API will be available at `http://localhost:8000`

**API Documentation:**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

#### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment variables
cp .env.example .env.local

# Update .env.local with your backend URL
# NEXT_PUBLIC_API_URL=http://localhost:8000

# Start the development server
npm run dev
```

The frontend will be available at `http://localhost:3000`

#### 4. Start Background Workers (Optional)

For background task processing (dataset processing, model training, batch predictions):

```bash
cd backend

# Start Celery worker
celery -A workers.celery_app worker --loglevel=info

# Start Celery beat (for scheduled tasks)
celery -A workers.celery_app beat --loglevel=info
```

## 🔐 Authentication & Security

### Authentication Flow

1. **User Registration**
   - User provides email and password
   - Password is hashed using bcrypt (cost factor: 12)
   - User account is created with assigned role

2. **Login**
   - User provides credentials
   - Backend validates credentials
   - JWT token is generated (24-hour expiration)
   - Token is returned to client and stored in localStorage

3. **Authenticated Requests**
   - Client includes token in Authorization header: `Bearer <token>`
   - Backend validates token on every request
   - User context is extracted and attached to request

4. **Token Expiration**
   - Tokens expire after 24 hours
   - Expired tokens are rejected with 401 Unauthorized
   - User must log in again to get a new token

5. **Logout**
   - Client removes token from localStorage
   - User is redirected to login page

### Role-Based Access Control (RBAC)

The platform supports three user roles with different permission levels:

#### Admin
- Full access to all features
- User management capabilities
- Can delete any dataset or model
- Can manage system settings

#### Data_Scientist
- Upload and manage datasets
- Train and manage models
- Create predictions
- Generate reports
- Cannot manage users

#### Analyst
- View dashboards and reports
- Create predictions using existing models
- View datasets and models (read-only)
- Cannot upload data or train models

### Security Features

- **Password Hashing**: bcrypt with cost factor 12
- **JWT Tokens**: Secure token-based authentication
- **Rate Limiting**: 100 requests/minute per user/IP
- **CORS Protection**: Configurable allowed origins
- **Data Encryption**: Sensitive fields encrypted at rest
- **Audit Logging**: Security-sensitive operations logged
- **Input Validation**: Pydantic schemas for all inputs
- **SQL Injection Protection**: SQLAlchemy ORM
- **XSS Protection**: React's built-in escaping

### CORS Configuration

**Development Mode:**
- Accepts all localhost variations (localhost, 127.0.0.1, any port)
- Simplifies local development

**Production Mode:**
- Uses explicit whitelist from `CORS_ORIGINS` environment variable
- Example: `CORS_ORIGINS=https://app.example.com,https://www.example.com`

## 🚢 Deployment

### Deployment Order

**Always deploy in this order to prevent downtime:**

1. **Backend First** → Wait for health check to pass
2. **Frontend Second** → Connects to updated backend

### Backend Deployment (Railway)

1. **Create Railway Project**
   ```bash
   # Install Railway CLI
   npm install -g @railway/cli
   
   # Login
   railway login
   
   # Initialize project
   railway init
   ```

2. **Add PostgreSQL and Redis**
   - In Railway dashboard, add PostgreSQL plugin
   - Add Redis plugin
   - Note the connection URLs

3. **Configure Environment Variables**
   - Set all required environment variables in Railway dashboard
   - Use Railway-provided DATABASE_URL and REDIS_URL

4. **Deploy**
   ```bash
   railway up
   ```

### Frontend Deployment (Vercel)

1. **Install Vercel CLI**
   ```bash
   npm install -g vercel
   ```

2. **Link Project**
   ```bash
   cd frontend
   vercel link
   ```

3. **Configure Environment Variables**
   ```bash
   vercel env add NEXT_PUBLIC_API_URL production
   # Enter your backend URL
   ```

4. **Deploy**
   ```bash
   vercel --prod
   ```

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Health Checks

After deployment, verify:

```bash
# Backend health
curl https://your-backend-url.com/health

# Frontend
curl https://your-frontend-url.com

# API authentication
curl -X POST https://your-backend-url.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}'
```

