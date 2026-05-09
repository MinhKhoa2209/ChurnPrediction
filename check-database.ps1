# Script kiểm tra database PostgreSQL
# Sử dụng: .\check-database.ps1

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  KIỂM TRA DATABASE CHURN PREDICTION" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Thông tin kết nối
$DB_USER = "churn_user"
$DB_NAME = "churn_prediction"

# 1. Kiểm tra container có đang chạy không
Write-Host "1. Kiểm tra PostgreSQL container..." -ForegroundColor Yellow
docker-compose ps postgres

# 2. Xem danh sách tất cả bảng
Write-Host "`n2. Danh sách tất cả bảng:" -ForegroundColor Yellow
docker-compose exec -T postgres psql -U $DB_USER -d $DB_NAME -c "\dt"

# 3. Xem số lượng users
Write-Host "`n3. Số lượng users:" -ForegroundColor Yellow
docker-compose exec -T postgres psql -U $DB_USER -d $DB_NAME -c "SELECT COUNT(*) as total_users FROM users;"

# 4. Xem danh sách users
Write-Host "`n4. Danh sách users:" -ForegroundColor Yellow
docker-compose exec -T postgres psql -U $DB_USER -d $DB_NAME -c "SELECT id, email, role, created_at FROM users ORDER BY created_at DESC;"

# 5. Xem số lượng datasets
Write-Host "`n5. Số lượng datasets:" -ForegroundColor Yellow
docker-compose exec -T postgres psql -U $DB_USER -d $DB_NAME -c "SELECT COUNT(*) as total_datasets FROM datasets;"

# 6. Xem danh sách datasets (nếu có)
Write-Host "`n6. Danh sách datasets:" -ForegroundColor Yellow
docker-compose exec -T postgres psql -U $DB_USER -d $DB_NAME -c "SELECT id, name, status, created_at FROM datasets ORDER BY created_at DESC LIMIT 10;"

# 7. Xem số lượng model versions
Write-Host "`n7. Số lượng model versions:" -ForegroundColor Yellow
docker-compose exec -T postgres psql -U $DB_USER -d $DB_NAME -c "SELECT COUNT(*) as total_models FROM model_versions;"

# 8. Xem số lượng predictions
Write-Host "`n8. Số lượng predictions:" -ForegroundColor Yellow
docker-compose exec -T postgres psql -U $DB_USER -d $DB_NAME -c "SELECT COUNT(*) as total_predictions FROM predictions;"

# 9. Xem phiên bản migration hiện tại
Write-Host "`n9. Phiên bản migration hiện tại:" -ForegroundColor Yellow
docker-compose exec -T postgres psql -U $DB_USER -d $DB_NAME -c "SELECT * FROM alembic_version;"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  HOÀN TẤT KIỂM TRA" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Để kết nối vào psql interactive mode, chạy:" -ForegroundColor Green
Write-Host "  docker-compose exec postgres psql -U churn_user -d churn_prediction`n" -ForegroundColor White
