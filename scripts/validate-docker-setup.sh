#!/bin/bash
# Validation script for Docker development environment
# Checks if all services are running and healthy

set -e

echo "🔍 Validating Docker Development Environment..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is running
echo "1. Checking Docker..."
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running${NC}"
    echo "Please start Docker Desktop or Docker Engine"
    exit 1
fi
echo -e "${GREEN}✓ Docker is running${NC}"
echo ""

# Check if docker-compose is available
echo "2. Checking Docker Compose..."
if ! docker-compose version > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker Compose is not available${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose is available${NC}"
echo ""

# Check if .env file exists
echo "3. Checking environment files..."
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠ .env file not found${NC}"
    echo "Creating from .env.example..."
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env file${NC}"
else
    echo -e "${GREEN}✓ .env file exists${NC}"
fi

if [ ! -f backend/.env ]; then
    echo -e "${YELLOW}⚠ backend/.env file not found${NC}"
    echo "Creating from backend/.env.example..."
    cp backend/.env.example backend/.env
    echo -e "${GREEN}✓ Created backend/.env file${NC}"
else
    echo -e "${GREEN}✓ backend/.env file exists${NC}"
fi
echo ""

# Check if services are running
echo "4. Checking services..."
if ! docker-compose ps | grep -q "Up"; then
    echo -e "${YELLOW}⚠ Services are not running${NC}"
    echo "Starting services..."
    docker-compose up -d
    echo "Waiting for services to be healthy..."
    sleep 10
fi

# Check individual service health
services=("postgres" "redis" "minio" "mlflow" "backend")
all_healthy=true

for service in "${services[@]}"; do
    if docker-compose ps | grep "$service" | grep -q "healthy\|Up"; then
        echo -e "${GREEN}✓ $service is running${NC}"
    else
        echo -e "${RED}❌ $service is not healthy${NC}"
        all_healthy=false
    fi
done
echo ""

# Check service endpoints
echo "5. Checking service endpoints..."

# Backend health check
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend API is responding${NC}"
else
    echo -e "${RED}❌ Backend API is not responding${NC}"
    all_healthy=false
fi

# MLflow health check
if curl -f http://localhost:5000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ MLflow is responding${NC}"
else
    echo -e "${YELLOW}⚠ MLflow is not responding (may still be starting)${NC}"
fi

# MinIO health check
if curl -f http://localhost:9000/minio/health/live > /dev/null 2>&1; then
    echo -e "${GREEN}✓ MinIO is responding${NC}"
else
    echo -e "${RED}❌ MinIO is not responding${NC}"
    all_healthy=false
fi
echo ""

# Check database connection
echo "6. Checking database connection..."
if docker-compose exec -T postgres pg_isready -U churn_user > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PostgreSQL is accepting connections${NC}"
else
    echo -e "${RED}❌ PostgreSQL is not accepting connections${NC}"
    all_healthy=false
fi
echo ""

# Check Redis connection
echo "7. Checking Redis connection..."
if docker-compose exec -T redis redis-cli -a redis_password ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Redis is accepting connections${NC}"
else
    echo -e "${RED}❌ Redis is not accepting connections${NC}"
    all_healthy=false
fi
echo ""

# Summary
echo "=========================================="
if [ "$all_healthy" = true ]; then
    echo -e "${GREEN}✅ All services are healthy!${NC}"
    echo ""
    echo "Access points:"
    echo "  Frontend:  http://localhost:3000"
    echo "  Backend:   http://localhost:8000"
    echo "  API Docs:  http://localhost:8000/docs"
    echo "  MLflow:    http://localhost:5000"
    echo "  MinIO:     http://localhost:9001"
    echo ""
    echo "Next steps:"
    echo "  1. Run database migrations: docker-compose exec backend alembic upgrade head"
    echo "  2. Access the frontend at http://localhost:3000"
    exit 0
else
    echo -e "${RED}❌ Some services are not healthy${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check logs: docker-compose logs"
    echo "  2. Restart services: docker-compose restart"
    echo "  3. Rebuild: docker-compose down && docker-compose up -d --build"
    exit 1
fi
