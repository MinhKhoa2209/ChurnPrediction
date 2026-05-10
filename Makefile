# Makefile for Customer Churn Prediction Platform
# Provides convenient commands for Docker development workflow

.PHONY: help setup up down restart logs clean test migrate shell

# Default target
help:
	@echo "Customer Churn Prediction Platform - Docker Commands"
	@echo ""
	@echo "Setup Commands:"
	@echo "  make setup          - Initial setup (copy .env, build images)"
	@echo "  make build          - Build all Docker images"
	@echo ""
	@echo "Service Management:"
	@echo "  make up             - Start all services"
	@echo "  make down           - Stop all services"
	@echo "  make restart        - Restart all services"
	@echo "  make ps             - Show service status"
	@echo ""
	@echo "Logs:"
	@echo "  make logs           - View logs from all services"
	@echo "  make logs-backend   - View backend logs"
	@echo "  make logs-frontend  - View frontend logs"
	@echo "  make logs-celery    - View Celery worker logs"
	@echo ""
	@echo "Database:"
	@echo "  make migrate        - Run database migrations"
	@echo "  make migrate-create - Create new migration"
	@echo "  make db-shell       - Connect to PostgreSQL shell"
	@echo "  make redis-shell    - Connect to Redis shell"
	@echo "  make db-check       - Check database status and users"
	@echo "  make db-reset       - Reset database (delete all data)"
	@echo "  make quick-admin    - Create quick admin user"
	@echo ""
	@echo "Development:"
	@echo "  make shell-backend  - Access backend container shell"
	@echo "  make shell-frontend - Access frontend container shell"
	@echo "  make test-backend   - Run backend tests"
	@echo "  make test-frontend  - Run frontend tests"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean          - Stop services and remove containers"
	@echo "  make clean-all      - Remove containers, volumes, and images"
	@echo "  make prune          - Clean up Docker system"

# Setup
setup:
	@echo "Setting up development environment..."
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env file"; fi
	@if [ ! -f backend/.env ]; then cp backend/.env.example backend/.env; echo "Created backend/.env file"; fi
	@if [ ! -f frontend/.env.local ]; then cp frontend/.env.example frontend/.env.local; echo "Created frontend/.env.local file"; fi
	@echo "Building Docker images..."
	@docker-compose build
	@echo "Setup complete! Run 'make up' to start services."

build:
	docker-compose build

# Service Management
up:
	docker-compose up -d
	@echo "Services started. Access points:"
	@echo "  Frontend:  http://localhost:3000"
	@echo "  Backend:   http://localhost:8000"
	@echo "  API Docs:  http://localhost:8000/docs"
	@echo "  MLflow:    http://localhost:5000"
	@echo "  MinIO:     http://localhost:9001"

down:
	docker-compose down

restart:
	docker-compose restart

ps:
	docker-compose ps

# Logs
logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-frontend:
	docker-compose logs -f frontend

logs-celery:
	docker-compose logs -f celery-worker

# Database
migrate:
	docker-compose exec backend alembic upgrade head

migrate-create:
	@read -p "Enter migration message: " msg; \
	docker-compose exec backend alembic revision --autogenerate -m "$$msg"

db-shell:
	docker-compose exec postgres psql -U churn_user -d churn_prediction

redis-shell:
	docker-compose exec redis redis-cli -a redis_password

# Development
shell-backend:
	docker-compose exec backend bash

shell-frontend:
	docker-compose exec frontend sh

test-backend:
	docker-compose exec backend pytest -v

test-frontend:
	docker-compose exec frontend npm test

# Cleanup
clean:
	docker-compose down -v

clean-all:
	docker-compose down -v --rmi all

prune:
	docker system prune -a --volumes

# Admin Management
quick-admin:
	@echo "Creating quick admin user (admin@churnpredict.com / Admin@123)..."
	@docker-compose exec -T backend python -c "import sys; sys.path.insert(0, '/app'); from sqlalchemy import create_engine; from sqlalchemy.orm import sessionmaker; from backend.domain.models.user import User; from backend.services.auth_service import AuthService; from backend.config import settings; engine = create_engine(settings.database_url); SessionLocal = sessionmaker(bind=engine); db = SessionLocal(); email = 'admin@churnpredict.com'; password = 'Admin@123'; name = 'Admin'; existing = db.query(User).filter(User.email == email).first(); result = 'Updated' if existing else 'Created'; user = existing if existing else User(); user.email = email; user.name = name; user.password_hash = AuthService._hash_password(password); user.role = 'Admin'; user.email_verified = True; user.auth_provider = 'local'; db.add(user) if not existing else None; db.commit(); print(f'✅ {result} admin user'); print(f'📧 Email: {email}'); print(f'🔒 Password: {password}'); print('🌐 Login: http://localhost:3000/login'); db.close()"

db-check:
	@echo "Checking database status..."
	@docker-compose exec -T postgres psql -U churn_user -d churn_prediction -c "\dt"
	@docker-compose exec -T postgres psql -U churn_user -d churn_prediction -c "SELECT COUNT(*) as total_users FROM users;"
	@docker-compose exec -T postgres psql -U churn_user -d churn_prediction -c "SELECT id, email, role, created_at FROM users ORDER BY created_at DESC;"

db-reset:
	@echo "⚠️  WARNING: This will delete all data!"
	@echo "Press Ctrl+C to cancel, or Enter to continue..."
	@read confirm
	@docker stop churn-backend churn-celery-worker
	@docker exec churn-postgres psql -U churn_user -d churn_prediction -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO churn_user; GRANT ALL ON SCHEMA public TO public;"
	@docker start churn-backend
	@sleep 5
	@docker exec churn-backend alembic upgrade head
	@docker start churn-celery-worker
	@echo "✅ Database reset complete!"
