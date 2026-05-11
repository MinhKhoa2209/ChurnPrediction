# Hướng dẫn tạo Report

## Tổng quan
Hệ thống hỗ trợ tạo báo cáo PDF chi tiết cho các model đã train, bao gồm:
- Metrics (Accuracy, Precision, Recall, F1-Score, ROC-AUC)
- Confusion Matrix
- ROC Curve
- Feature Importance
- Hyperparameters
- Training information

## Cách tạo Report

### Option 1: Sử dụng API trực tiếp

#### 1. Lấy Model Version ID
Trước tiên, cần lấy ID của model version bạn muốn tạo report:

```bash
# List all model versions
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/api/v1/models/versions | jq .
```

Kết quả sẽ trả về danh sách models với các thông tin:
```json
{
  "versions": [
    {
      "id": "abc123...",
      "model_type": "NaiveBayes",
      "version": "NaiveBayes_12345678_20260511_140530",
      "metrics": {
        "accuracy": 0.8013,
        "precision": 0.4557,
        "recall": 0.8396,
        "f1_score": 0.5908,
        "roc_auc": 0.8034
      },
      ...
    }
  ]
}
```

#### 2. Tạo Report
Sử dụng Model Version ID để tạo report:

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model_version_id": "abc123...",
    "include_confusion_matrix": true,
    "include_roc_curve": true,
    "include_feature_importance": true
  }' \
  http://localhost:8000/api/v1/reports/generate
```

Kết quả:
```json
{
  "id": "report-id-123",
  "model_version_id": "abc123...",
  "report_type": "model_evaluation",
  "file_size": 245678,
  "created_at": "2026-05-11T14:30:00Z"
}
```

#### 3. Download Report
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/api/v1/reports/report-id-123/download \
     -o model_report.pdf
```

### Option 2: Sử dụng Frontend (Recommended)

#### Bước 1: Vào trang Model Evaluation
1. Đăng nhập vào hệ thống
2. Vào menu **Models** → **Comparison**
3. Click **View Details** trên model bạn muốn tạo report

#### Bước 2: Tạo Report
1. Trong trang Model Evaluation, tìm nút **Generate Report**
2. Chọn các options:
   - ✅ Include Confusion Matrix
   - ✅ Include ROC Curve
   - ✅ Include Feature Importance
3. Click **Generate Report**

#### Bước 3: Download Report
1. Sau khi report được tạo, click **Download Report**
2. File PDF sẽ được download về máy

### Option 3: Sử dụng Python Script

Tạo file `generate_report.py`:

```python
import requests
import json

# Configuration
API_URL = "http://localhost:8000/api/v1"
TOKEN = "your-jwt-token-here"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Step 1: Get model versions
response = requests.get(f"{API_URL}/models/versions", headers=headers)
models = response.json()["versions"]

print("Available models:")
for i, model in enumerate(models):
    print(f"{i+1}. {model['model_type']} - {model['version'][:20]}... (F1: {model['metrics']['f1_score']:.4f})")

# Step 2: Select model
model_index = int(input("\nSelect model number: ")) - 1
selected_model = models[model_index]
model_version_id = selected_model["id"]

print(f"\nGenerating report for {selected_model['model_type']}...")

# Step 3: Generate report
report_request = {
    "model_version_id": model_version_id,
    "include_confusion_matrix": True,
    "include_roc_curve": True,
    "include_feature_importance": True
}

response = requests.post(
    f"{API_URL}/reports/generate",
    headers=headers,
    json=report_request
)

if response.status_code == 201:
    report = response.json()
    report_id = report["id"]
    print(f"Report created successfully! ID: {report_id}")
    
    # Step 4: Download report
    print("Downloading report...")
    response = requests.get(
        f"{API_URL}/reports/{report_id}/download",
        headers=headers
    )
    
    if response.status_code == 200:
        filename = f"report_{selected_model['model_type']}_{report_id[:8]}.pdf"
        with open(filename, "wb") as f:
            f.write(response.content)
        print(f"Report saved as: {filename}")
    else:
        print(f"Error downloading report: {response.text}")
else:
    print(f"Error generating report: {response.text}")
```

Chạy script:
```bash
python generate_report.py
```

## Nội dung Report

Report PDF bao gồm các phần sau:

### 1. Model Information
- Model Type (KNN, NaiveBayes, DecisionTree, SVM)
- Version ID
- Training Date
- Dataset Information
- Training Time

### 2. Performance Metrics
- **Accuracy**: Tỷ lệ dự đoán đúng tổng thể
- **Precision**: Tỷ lệ dự đoán churn đúng trong số các dự đoán churn
- **Recall**: Tỷ lệ phát hiện được churn thực tế
- **F1-Score**: Trung bình điều hòa của Precision và Recall
- **ROC-AUC**: Diện tích dưới đường cong ROC

### 3. Confusion Matrix
Ma trận nhầm lẫn hiển thị:
- True Negatives (TN): Dự đoán không churn, thực tế không churn
- False Positives (FP): Dự đoán churn, thực tế không churn
- False Negatives (FN): Dự đoán không churn, thực tế churn
- True Positives (TP): Dự đoán churn, thực tế churn

### 4. ROC Curve
Đường cong ROC (Receiver Operating Characteristic) hiển thị:
- True Positive Rate vs False Positive Rate
- AUC (Area Under Curve) score
- Optimal threshold point

### 5. Feature Importance
Top 10 features quan trọng nhất ảnh hưởng đến dự đoán:
- Feature name
- Importance score
- Visualization chart

### 6. Hyperparameters
Các tham số được sử dụng để train model:
- **KNN**: n_neighbors, weights, metric
- **NaiveBayes**: var_smoothing
- **DecisionTree**: max_depth, min_samples_split, criterion
- **SVM**: C, kernel, gamma

## Quản lý Reports

### List tất cả Reports
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/api/v1/reports | jq .
```

### Xem thông tin Report
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/api/v1/reports/REPORT_ID | jq .
```

### Download Report
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/api/v1/reports/REPORT_ID/download \
     -o report.pdf
```

## Troubleshooting

### Lỗi: "Model version not found"
**Nguyên nhân**: Model version ID không tồn tại hoặc không thuộc về user hiện tại

**Giải pháp**:
1. Kiểm tra lại Model Version ID
2. Đảm bảo model đã được train thành công
3. Kiểm tra quyền truy cập (Admin có thể xem tất cả models)

### Lỗi: "Failed to generate report"
**Nguyên nhân**: Lỗi khi tạo PDF hoặc upload lên storage

**Giải pháp**:
1. Kiểm tra logs backend:
   ```bash
   docker logs churn-backend --tail 100
   ```
2. Kiểm tra MinIO/S3 storage:
   ```bash
   docker logs churn-minio --tail 50
   ```
3. Restart services nếu cần:
   ```bash
   docker-compose restart backend minio
   ```

### Lỗi: "Failed to download report"
**Nguyên nhân**: File không tồn tại trong storage

**Giải pháp**:
1. Kiểm tra MinIO Console: http://localhost:9001
2. Login với credentials:
   - Username: minioadmin
   - Password: minioadmin123
3. Kiểm tra bucket `reports` có file không
4. Nếu không có, tạo lại report

## Best Practices

### 1. Tạo Report sau khi Training
Nên tạo report ngay sau khi model được train thành công để có đầy đủ thông tin.

### 2. Lưu trữ Reports
Reports được lưu trong MinIO/S3 storage và có thể download bất cứ lúc nào.

### 3. So sánh Models
Tạo reports cho nhiều models để so sánh performance và chọn model tốt nhất.

### 4. Chia sẻ Reports
Reports ở định dạng PDF, dễ dàng chia sẻ với stakeholders.

### 5. Backup Reports
Nên backup reports quan trọng ra ngoài hệ thống để tránh mất dữ liệu.

## API Reference

### POST /api/v1/reports/generate
Tạo report mới cho model version.

**Request Body**:
```json
{
  "model_version_id": "string (required)",
  "include_confusion_matrix": "boolean (default: true)",
  "include_roc_curve": "boolean (default: true)",
  "include_feature_importance": "boolean (default: true)"
}
```

**Response**: `201 Created`
```json
{
  "id": "string",
  "model_version_id": "string",
  "report_type": "model_evaluation",
  "file_size": "integer",
  "created_at": "string (ISO 8601)"
}
```

### GET /api/v1/reports
List tất cả reports của user.

**Response**: `200 OK`
```json
[
  {
    "id": "string",
    "model_version_id": "string",
    "report_type": "string",
    "file_size": "integer",
    "created_at": "string"
  }
]
```

### GET /api/v1/reports/{report_id}
Lấy thông tin chi tiết của report.

**Response**: `200 OK`
```json
{
  "id": "string",
  "model_version_id": "string",
  "report_type": "string",
  "file_size": "integer",
  "created_at": "string"
}
```

### GET /api/v1/reports/{report_id}/download
Download report PDF.

**Response**: `200 OK`
- Content-Type: `application/pdf`
- Content-Disposition: `attachment; filename=report_{report_id}.pdf`

## Examples

### Example 1: Tạo report cho best model
```bash
# Get best model
BEST_MODEL=$(curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/models/versions | \
  jq -r '.versions | sort_by(.metrics.f1_score) | reverse | .[0].id')

# Generate report
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"model_version_id\": \"$BEST_MODEL\"}" \
  http://localhost:8000/api/v1/reports/generate
```

### Example 2: Tạo reports cho tất cả models
```bash
# Get all model IDs
MODEL_IDS=$(curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/models/versions | \
  jq -r '.versions[].id')

# Generate report for each model
for MODEL_ID in $MODEL_IDS; do
  echo "Generating report for $MODEL_ID..."
  curl -X POST \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"model_version_id\": \"$MODEL_ID\"}" \
    http://localhost:8000/api/v1/reports/generate
  sleep 2
done
```

### Example 3: Download tất cả reports
```bash
# Get all report IDs
REPORT_IDS=$(curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/reports | \
  jq -r '.[].id')

# Download each report
for REPORT_ID in $REPORT_IDS; do
  echo "Downloading report $REPORT_ID..."
  curl -H "Authorization: Bearer $TOKEN" \
    http://localhost:8000/api/v1/reports/$REPORT_ID/download \
    -o "report_$REPORT_ID.pdf"
done
```

## Liên hệ

Nếu gặp vấn đề khi tạo report, vui lòng:
1. Kiểm tra logs: `docker logs churn-backend --tail 100`
2. Kiểm tra storage: http://localhost:9001
3. Tạo issue trên GitHub với đầy đủ thông tin lỗi
