# PowerShell script to completely rebuild Docker containers

Write-Host "🛑 Stopping all containers..." -ForegroundColor Yellow
docker-compose down

Write-Host "🗑️  Removing all containers..." -ForegroundColor Yellow
docker-compose rm -f

Write-Host "🧹 Pruning Docker system (removing unused data)..." -ForegroundColor Yellow
docker system prune -f

Write-Host "🗂️  Removing Docker build cache..." -ForegroundColor Yellow
docker builder prune -f

Write-Host "📦 Building all images from scratch (no cache)..." -ForegroundColor Yellow
docker-compose build --no-cache

Write-Host "🚀 Starting all containers..." -ForegroundColor Green
docker-compose up -d

Write-Host "⏳ Waiting for containers to be healthy..." -ForegroundColor Cyan
Start-Sleep -Seconds 10

Write-Host "✅ Done! Checking container status..." -ForegroundColor Green
docker-compose ps

Write-Host ""
Write-Host "📋 To view logs:" -ForegroundColor Cyan
Write-Host "  Backend:  docker logs churn-backend -f" -ForegroundColor White
Write-Host "  Frontend: docker logs churn-frontend -f" -ForegroundColor White
Write-Host "  Celery:   docker logs churn-celery-worker -f" -ForegroundColor White
