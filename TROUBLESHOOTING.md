# Hướng dẫn khắc phục lỗi

## 1. Lỗi Training Model ✅ ĐÃ SỬA

### Triệu chứng
- Training model thất bại với lỗi: `type object 'TrainingService' has no attribute 'get_job'`
- Tất cả các model types (SVM, DecisionTree, NaiveBayes, KNN) đều failed
- Progress bar dừng ở 10%

### Nguyên nhân
Celery worker container đang chạy code cũ, chưa có method `get_job` mới được thêm vào `TrainingService`.

### Giải pháp
Rebuild và restart Celery worker container:

```bash
# Rebuild container với code mới
docker-compose build celery-worker

# Restart container
docker-compose up -d celery-worker

# Kiểm tra logs để xác nhận
docker logs churn-celery-worker --tail 20
```

### Xác nhận đã sửa
- Celery worker khởi động thành công
- Không còn lỗi `AttributeError` trong logs
- Training jobs có thể chạy thành công

---

## 2. Lỗi Delete Users ⚠️ CẦN KIỂM TRA

### Triệu chứng
- Trang `/admin/users` hiển thị trống (blank page)
- Không có danh sách users
- Không có error message hiển thị

### Các bước kiểm tra

#### Bước 1: Kiểm tra authentication
1. Đảm bảo bạn đã đăng nhập với tài khoản Admin
2. Kiểm tra token trong localStorage:
   ```javascript
   // Mở DevTools Console
   localStorage.getItem('auth-storage')
   ```

#### Bước 2: Kiểm tra API endpoint
```bash
# Test với curl (cần thay YOUR_TOKEN bằng token thực)
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/v1/users
```

#### Bước 3: Kiểm tra browser console
1. Mở DevTools (F12)
2. Vào tab Console
3. Reload trang `/admin/users`
4. Xem có error nào không

#### Bước 4: Kiểm tra Network tab
1. Mở DevTools (F12)
2. Vào tab Network
3. Reload trang `/admin/users`
4. Xem request đến `/api/v1/users` có thành công không
5. Kiểm tra response status code và data

### Các nguyên nhân có thể

#### A. Lỗi CORS
**Triệu chứng**: Console hiển thị CORS error

**Giải pháp**: Kiểm tra CORS configuration trong backend:
```python
# backend/main.py
CORS_ORIGINS = "http://localhost:3000,http://localhost:3001,..."
```

#### B. Lỗi Authentication
**Triệu chứng**: API trả về 401 Unauthorized

**Giải pháp**:
1. Đăng xuất và đăng nhập lại
2. Xóa localStorage và cookies
3. Kiểm tra JWT token có hết hạn không

#### C. Lỗi Authorization
**Triệu chứng**: API trả về 403 Forbidden

**Giải pháp**:
1. Đảm bảo user có role "Admin"
2. Kiểm tra database:
   ```sql
   SELECT id, email, role FROM users;
   ```

#### D. Lỗi Backend
**Triệu chứng**: API trả về 500 Internal Server Error

**Giải pháp**:
```bash
# Kiểm tra logs backend
docker logs churn-backend --tail 100

# Restart backend nếu cần
docker-compose restart backend
```

#### E. Lỗi Frontend
**Triệu chứng**: Trang trắng, không có error trong Network tab

**Giải pháp**:
```bash
# Rebuild frontend
docker-compose build frontend

# Restart frontend
docker-compose up -d frontend

# Hoặc chạy local để debug
cd frontend
npm install
npm run dev
```

### Giải pháp nhanh

#### Option 1: Restart tất cả services
```bash
docker-compose down
docker-compose up -d
```

#### Option 2: Rebuild tất cả
```bash
docker-compose down
docker-compose build
docker-compose up -d
```

#### Option 3: Kiểm tra database
```bash
# Connect to PostgreSQL
docker exec -it churn-postgres psql -U churn_user -d churn_prediction

# Kiểm tra users
SELECT id, email, name, role, created_at FROM users;

# Thoát
\q
```

---

## 3. Các lỗi thường gặp khác

### Lỗi: Cannot connect to database
```bash
# Kiểm tra PostgreSQL
docker logs churn-postgres --tail 50

# Restart PostgreSQL
docker-compose restart postgres
```

### Lỗi: Redis connection failed
```bash
# Kiểm tra Redis
docker logs churn-redis --tail 50

# Test Redis connection
docker exec -it churn-redis redis-cli -a redis_password ping
```

### Lỗi: MinIO/S3 connection failed
```bash
# Kiểm tra MinIO
docker logs churn-minio --tail 50

# Truy cập MinIO Console
# http://localhost:9001
# Username: minioadmin
# Password: minioadmin123
```

### Lỗi: MLflow not accessible
```bash
# Kiểm tra MLflow
docker logs churn-mlflow --tail 50

# Truy cập MLflow UI
# http://localhost:5000
```

---

## 4. Commands hữu ích

### Xem logs tất cả services
```bash
docker-compose logs -f
```

### Xem logs một service cụ thể
```bash
docker logs <container-name> -f
```

### Restart một service
```bash
docker-compose restart <service-name>
```

### Rebuild và restart
```bash
docker-compose up -d --build <service-name>
```

### Xóa tất cả và bắt đầu lại
```bash
docker-compose down -v  # -v để xóa volumes
docker-compose up -d
```

### Kiểm tra trạng thái containers
```bash
docker-compose ps
```

### Kiểm tra resource usage
```bash
docker stats
```

---

## 5. Liên hệ hỗ trợ

Nếu vẫn gặp vấn đề sau khi thử các bước trên:

1. Thu thập thông tin:
   - Logs của service bị lỗi
   - Screenshot của error
   - Các bước đã thử

2. Tạo issue trên GitHub repository

3. Hoặc liên hệ team support
