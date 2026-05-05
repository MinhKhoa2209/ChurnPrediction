# Validation script for Docker development environment (PowerShell)
# Checks if all services are running and healthy

$ErrorActionPreference = "Stop"

Write-Host "🔍 Validating Docker Development Environment..." -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
Write-Host "1. Checking Docker..." -ForegroundColor Yellow
try {
    docker info | Out-Null
    Write-Host "✓ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running" -ForegroundColor Red
    Write-Host "Please start Docker Desktop" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Check if docker-compose is available
Write-Host "2. Checking Docker Compose..." -ForegroundColor Yellow
try {
    docker-compose version | Out-Null
    Write-Host "✓ Docker Compose is available" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker Compose is not available" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Check if .env file exists
Write-Host "3. Checking environment files..." -ForegroundColor Yellow
if (-not (Test-Path .env)) {
    Write-Host "⚠ .env file not found" -ForegroundColor Yellow
    Write-Host "Creating from .env.example..."
    Copy-Item .env.example .env
    Write-Host "✓ Created .env file" -ForegroundColor Green
} else {
    Write-Host "✓ .env file exists" -ForegroundColor Green
}

if (-not (Test-Path backend/.env)) {
    Write-Host "⚠ backend/.env file not found" -ForegroundColor Yellow
    Write-Host "Creating from backend/.env.example..."
    Copy-Item backend/.env.example backend/.env
    Write-Host "✓ Created backend/.env file" -ForegroundColor Green
} else {
    Write-Host "✓ backend/.env file exists" -ForegroundColor Green
}
Write-Host ""

# Check if services are running
Write-Host "4. Checking services..." -ForegroundColor Yellow
$services = docker-compose ps
if ($services -notmatch "Up") {
    Write-Host "⚠ Services are not running" -ForegroundColor Yellow
    Write-Host "Starting services..."
    docker-compose up -d
    Write-Host "Waiting for services to be healthy..."
    Start-Sleep -Seconds 10
}

# Check individual service health
$serviceNames = @("postgres", "redis", "minio", "mlflow", "backend")
$allHealthy = $true

foreach ($service in $serviceNames) {
    $status = docker-compose ps | Select-String $service
    if ($status -match "healthy|Up") {
        Write-Host "✓ $service is running" -ForegroundColor Green
    } else {
        Write-Host "❌ $service is not healthy" -ForegroundColor Red
        $allHealthy = $false
    }
}
Write-Host ""

# Check service endpoints
Write-Host "5. Checking service endpoints..." -ForegroundColor Yellow

# Backend health check
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ Backend API is responding" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Backend API is not responding" -ForegroundColor Red
    $allHealthy = $false
}

# MLflow health check
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/health" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ MLflow is responding" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠ MLflow is not responding (may still be starting)" -ForegroundColor Yellow
}

# MinIO health check
try {
    $response = Invoke-WebRequest -Uri "http://localhost:9000/minio/health/live" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ MinIO is responding" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ MinIO is not responding" -ForegroundColor Red
    $allHealthy = $false
}
Write-Host ""

# Check database connection
Write-Host "6. Checking database connection..." -ForegroundColor Yellow
try {
    docker-compose exec -T postgres pg_isready -U churn_user | Out-Null
    Write-Host "✓ PostgreSQL is accepting connections" -ForegroundColor Green
} catch {
    Write-Host "❌ PostgreSQL is not accepting connections" -ForegroundColor Red
    $allHealthy = $false
}
Write-Host ""

# Check Redis connection
Write-Host "7. Checking Redis connection..." -ForegroundColor Yellow
try {
    docker-compose exec -T redis redis-cli -a redis_password ping | Out-Null
    Write-Host "✓ Redis is accepting connections" -ForegroundColor Green
} catch {
    Write-Host "❌ Redis is not accepting connections" -ForegroundColor Red
    $allHealthy = $false
}
Write-Host ""

# Summary
Write-Host "==========================================" -ForegroundColor Cyan
if ($allHealthy) {
    Write-Host "✅ All services are healthy!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Access points:"
    Write-Host "  Frontend:  http://localhost:3000"
    Write-Host "  Backend:   http://localhost:8000"
    Write-Host "  API Docs:  http://localhost:8000/docs"
    Write-Host "  MLflow:    http://localhost:5000"
    Write-Host "  MinIO:     http://localhost:9001"
    Write-Host ""
    Write-Host "Next steps:"
    Write-Host "  1. Run database migrations: docker-compose exec backend alembic upgrade head"
    Write-Host "  2. Access the frontend at http://localhost:3000"
    exit 0
} else {
    Write-Host "❌ Some services are not healthy" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:"
    Write-Host "  1. Check logs: docker-compose logs"
    Write-Host "  2. Restart services: docker-compose restart"
    Write-Host "  3. Rebuild: docker-compose down; docker-compose up -d --build"
    exit 1
}
