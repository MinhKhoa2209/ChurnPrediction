#!/bin/bash
# Script kiểm tra database PostgreSQL
# Sử dụng: ./check-database.sh

echo ""
echo "========================================"
echo "  KIỂM TRA DATABASE CHURN PREDICTION"
echo "========================================"
echo ""

# Thông tin kết nối
DB_USER="churn_user"
DB_NAME="churn_prediction"

# 1. Kiểm tra container có đang chạy không
echo "1. Kiểm tra PostgreSQL container..."
docker-compose ps postgres

# 2. Xem danh sách tất cả bảng
echo ""
echo "2. Danh sách tất cả bảng:"
docker-compose exec -T postgres psql -U $DB_USER -d $DB_NAME -c "\dt"

# 3. Xem số lượng users
echo ""
echo "3. Số lượng users:"
docker-compose exec -T postgres psql -U $DB_USER -d $DB_NAME -c "SELECT COUNT(*) as total_users FROM users;"

# 4. Xem danh sách users
echo ""
echo "4. Danh sách users:"
docker-compose exec -T postgres psql -U $DB_USER -d $DB_NAME -c "SELECT id, email, role, created_at FROM users ORDER BY created_at DESC;"

# 5. Xem số lượng datasets
echo ""
echo "5. Số lượng datasets:"
docker-compose exec -T postgres psql -U $DB_USER -d $DB_NAME -c "SELECT COUNT(*) as total_datasets FROM datasets;"

# 6. Xem danh sách datasets (nếu có)
echo ""
echo "6. Danh sách datasets:"
docker-compose exec -T postgres psql -U $DB_USER -d $DB_NAME -c "SELECT id, name, status, created_at FROM datasets ORDER BY created_at DESC LIMIT 10;"

# 7. Xem số lượng model versions
echo ""
echo "7. Số lượng model versions:"
docker-compose exec -T postgres psql -U $DB_USER -d $DB_NAME -c "SELECT COUNT(*) as total_models FROM model_versions;"

# 8. Xem số lượng predictions
echo ""
echo "8. Số lượng predictions:"
docker-compose exec -T postgres psql -U $DB_USER -d $DB_NAME -c "SELECT COUNT(*) as total_predictions FROM predictions;"

# 9. Xem phiên bản migration hiện tại
echo ""
echo "9. Phiên bản migration hiện tại:"
docker-compose exec -T postgres psql -U $DB_USER -d $DB_NAME -c "SELECT * FROM alembic_version;"

echo ""
echo "========================================"
echo "  HOÀN TẤT KIỂM TRA"
echo "========================================"
echo ""

echo "Để kết nối vào psql interactive mode, chạy:"
echo "  docker-compose exec postgres psql -U churn_user -d churn_prediction"
echo ""
