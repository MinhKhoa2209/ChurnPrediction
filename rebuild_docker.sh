#!/bin/bash
# Script to completely rebuild Docker containers

echo "🛑 Stopping all containers..."
docker-compose down

echo "🗑️  Removing all containers..."
docker-compose rm -f

echo "🧹 Pruning Docker system (removing unused data)..."
docker system prune -f

echo "🗂️  Removing Docker build cache..."
docker builder prune -f

echo "📦 Building all images from scratch (no cache)..."
docker-compose build --no-cache

echo "🚀 Starting all containers..."
docker-compose up -d

echo "⏳ Waiting for containers to be healthy..."
sleep 10

echo "✅ Done! Checking container status..."
docker-compose ps

echo ""
echo "📋 To view logs:"
echo "  Backend:  docker logs churn-backend -f"
echo "  Frontend: docker logs churn-frontend -f"
echo "  Celery:   docker logs churn-celery-worker -f"
