# Docker Rebuild Guide

## 🚀 Quick Rebuild (Recommended)

### Windows PowerShell
```powershell
.\rebuild_docker.ps1
```

### Linux/Mac Bash
```bash
chmod +x rebuild_docker.sh
./rebuild_docker.sh
```

---

## 📋 Manual Step-by-Step Commands

### Step 1: Stop All Containers
```bash
docker-compose down
```

### Step 2: Remove All Containers
```bash
docker-compose rm -f
```

### Step 3: Clean Docker System
```bash
# Remove unused data
docker system prune -f

# Remove build cache
docker builder prune -f

# (Optional) Remove ALL unused images, containers, networks
docker system prune -a -f
```

### Step 4: Build Without Cache
```bash
# Build all services
docker-compose build --no-cache

# Or build specific service
docker-compose build --no-cache backend
docker-compose build --no-cache frontend
docker-compose build --no-cache celery-worker
```

### Step 5: Start Containers
```bash
docker-compose up -d
```

### Step 6: Check Status
```bash
docker-compose ps
```

---

## 🔍 Verify Everything is Working

### Check Container Status
```bash
docker-compose ps
```

Expected output:
```
NAME                  STATUS
churn-backend         Up (healthy)
churn-frontend        Up
churn-celery-worker   Up
churn-postgres        Up (healthy)
churn-redis           Up (healthy)
churn-minio           Up (healthy)
churn-mlflow          Up
```

### Check Logs
```bash
# Backend
docker logs churn-backend --tail 50

# Frontend
docker logs churn-frontend --tail 50

# Celery Worker
docker logs churn-celery-worker --tail 50
```

### Test API
```bash
# Health check
curl http://localhost:8000/health

# Should return: {"status":"healthy","database":"connected"}
```

### Test Frontend
Open browser: http://localhost:3000

---

## 🧹 Deep Clean (Nuclear Option)

⚠️ **WARNING**: This will remove EVERYTHING including volumes (database data)

```bash
# Stop everything
docker-compose down -v

# Remove all containers
docker rm -f $(docker ps -aq)

# Remove all images
docker rmi -f $(docker images -aq)

# Remove all volumes
docker volume prune -f

# Remove all networks
docker network prune -f

# Remove all build cache
docker builder prune -a -f

# Rebuild from scratch
docker-compose build --no-cache
docker-compose up -d
```

---

## 🎯 Rebuild Specific Services

### Rebuild Backend Only
```bash
docker-compose stop backend
docker-compose rm -f backend
docker-compose build --no-cache backend
docker-compose up -d backend
```

### Rebuild Frontend Only
```bash
docker-compose stop frontend
docker-compose rm -f frontend
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

### Rebuild Celery Worker Only
```bash
docker-compose stop celery-worker
docker-compose rm -f celery-worker
docker-compose build --no-cache celery-worker
docker-compose up -d celery-worker
```

---

## 🐛 Troubleshooting

### Issue: Containers won't start
```bash
# Check logs
docker-compose logs

# Check specific service
docker-compose logs backend
docker-compose logs frontend
```

### Issue: Port already in use
```bash
# Find process using port 8000
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Linux/Mac

# Kill the process
taskkill /PID <PID> /F        # Windows
kill -9 <PID>                 # Linux/Mac
```

### Issue: Database connection failed
```bash
# Check if postgres is running
docker-compose ps postgres

# Check postgres logs
docker logs churn-postgres

# Restart postgres
docker-compose restart postgres
```

### Issue: Frontend shows old code
```bash
# Clear browser cache
# Ctrl + Shift + Delete (Windows)
# Cmd + Shift + Delete (Mac)

# Or hard refresh
# Ctrl + Shift + R (Windows)
# Cmd + Shift + R (Mac)

# Rebuild frontend
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

---

## 📊 Disk Space Management

### Check Docker Disk Usage
```bash
docker system df
```

### Clean Up Unused Resources
```bash
# Remove stopped containers
docker container prune -f

# Remove unused images
docker image prune -a -f

# Remove unused volumes
docker volume prune -f

# Remove unused networks
docker network prune -f

# Remove build cache
docker builder prune -a -f
```

---

## ⚡ Quick Commands Reference

| Command | Description |
|---------|-------------|
| `docker-compose up -d` | Start all containers |
| `docker-compose down` | Stop all containers |
| `docker-compose ps` | List containers |
| `docker-compose logs -f` | Follow all logs |
| `docker-compose restart <service>` | Restart specific service |
| `docker-compose build --no-cache` | Rebuild without cache |
| `docker system prune -f` | Clean unused data |
| `docker builder prune -f` | Clean build cache |

---

## 🔄 Rebuild Workflow

### For Code Changes
```bash
# 1. Stop containers
docker-compose down

# 2. Rebuild changed service
docker-compose build --no-cache <service>

# 3. Start containers
docker-compose up -d

# 4. Check logs
docker-compose logs -f <service>
```

### For Database Schema Changes
```bash
# 1. Stop containers
docker-compose down

# 2. Remove volumes (⚠️ deletes data)
docker-compose down -v

# 3. Rebuild
docker-compose build --no-cache

# 4. Start and run migrations
docker-compose up -d
docker exec -it churn-backend alembic upgrade head
```

### For Dependency Changes
```bash
# 1. Stop containers
docker-compose down

# 2. Remove images
docker rmi churnprediction-backend churnprediction-frontend churnprediction-celery-worker

# 3. Rebuild without cache
docker-compose build --no-cache

# 4. Start containers
docker-compose up -d
```

---

## 📝 Best Practices

1. **Always check logs** after rebuild
   ```bash
   docker-compose logs -f
   ```

2. **Verify health** before testing
   ```bash
   docker-compose ps
   curl http://localhost:8000/health
   ```

3. **Clean regularly** to save disk space
   ```bash
   docker system prune -f
   ```

4. **Use specific rebuilds** when possible
   - Only rebuild changed services
   - Saves time and resources

5. **Backup data** before deep clean
   ```bash
   # Export database
   docker exec churn-postgres pg_dump -U churn_user churn_prediction > backup.sql
   ```

---

## 🎯 Common Scenarios

### Scenario 1: Frontend not showing changes
```bash
docker-compose build --no-cache frontend
docker-compose up -d frontend
# Then hard refresh browser (Ctrl + Shift + R)
```

### Scenario 2: Backend API changes not working
```bash
docker-compose build --no-cache backend
docker-compose up -d backend
docker logs churn-backend -f
```

### Scenario 3: Celery tasks not running
```bash
docker-compose build --no-cache celery-worker
docker-compose up -d celery-worker
docker logs churn-celery-worker -f
```

### Scenario 4: Everything is broken
```bash
# Nuclear option
docker-compose down -v
docker system prune -a -f
docker-compose build --no-cache
docker-compose up -d
```

---

**Last Updated**: 2026-05-11
**Version**: 1.0
