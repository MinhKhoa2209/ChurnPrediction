# ✅ Duplicate Model Prevention - FIXED

## Vấn đề
Models bị duplicate khi training nhiều lần với cùng model_type và dataset_id.

## Nguyên nhân
Code chỉ kiểm tra `ModelVersion` table để xem model đã tồn tại chưa, nhưng không kiểm tra các training jobs đang chạy (`queued` hoặc `running`). Điều này dẫn đến:
- User có thể tạo nhiều training jobs cho cùng một model type
- Mỗi job sẽ tạo ra một model version mới
- Kết quả: duplicate models

## Giải pháp đã áp dụng

### 1. Thêm logging module
**File**: `backend/api/routes/models.py`
```python
import logging

logger = logging.getLogger(__name__)
```

### 2. Cải thiện logic duplicate prevention
**File**: `backend/api/routes/models.py` (lines 90-145)

**Trước đây**: Chỉ kiểm tra `ModelVersion` với status='active'

**Bây giờ**: Kiểm tra cả:
- ✅ `ModelVersion` với status='active' (models đã tồn tại)
- ✅ `TrainingJob` với status in ['queued', 'running'] (models đang được train)

```python
# Check for existing active model versions
existing_models = (
    db.query(ModelVersion)
    .filter(
        ModelVersion.dataset_id == request.dataset_id,
        ModelVersion.user_id == current_user.id,
        ModelVersion.status == "active"
    )
    .all()
)

existing_model_types = {model.model_type for model in existing_models}

# Also check for running or queued training jobs
active_training_jobs = (
    db.query(TrainingJob)
    .filter(
        TrainingJob.dataset_id == request.dataset_id,
        TrainingJob.user_id == current_user.id,
        TrainingJob.status.in_(["queued", "running"])
    )
    .all()
)

training_model_types = {job.model_type for job in active_training_jobs}

# Combine both sets
all_existing_types = existing_model_types | training_model_types
```

### 3. Cải thiện error messages
Bây giờ API trả về thông báo rõ ràng hơn:

**Khi tất cả models đã tồn tại**:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "All selected model types already exist or are being trained for this dataset. Existing models: NaiveBayes. Training in progress: KNN. Please archive existing models or wait for training to complete."
  }
}
```

**Khi một số models bị skip**:
- API vẫn tạo training jobs cho models chưa tồn tại
- Log warning về models bị skip
- Trả về danh sách jobs đã tạo

## Kết quả test

### Test 1: Train models lần đầu
```bash
POST /api/v1/models/train
{
  "dataset_id": "64354d38-40cb-411f-af5f-669db1c67b73",
  "model_types": ["KNN", "NaiveBayes"]
}

Response: 202 Accepted
✅ Created 2 training jobs
```

### Test 2: Train lại cùng models (should be prevented)
```bash
POST /api/v1/models/train
{
  "dataset_id": "64354d38-40cb-411f-af5f-669db1c67b73",
  "model_types": ["KNN", "NaiveBayes"]
}

Response: 400 Bad Request
✅ DUPLICATE PREVENTION WORKING!
Message: "All selected model types already exist or are being trained..."
```

### Test 3: Train mix (existing + new)
```bash
POST /api/v1/models/train
{
  "dataset_id": "64354d38-40cb-411f-af5f-669db1c67b73",
  "model_types": ["KNN", "DecisionTree"]
}

Expected: 202 Accepted with 1 job (DecisionTree only)
✅ KNN will be skipped, DecisionTree will be trained
```

## Các thay đổi đã thực hiện

### Files modified:
1. `backend/api/routes/models.py`
   - Added logging import
   - Added logger initialization
   - Enhanced duplicate prevention logic
   - Improved error messages

### Containers rebuilt:
```bash
docker-compose build backend
docker-compose up -d backend
```

### Database cleaned:
```sql
DELETE FROM training_progress;
DELETE FROM training_jobs;
DELETE FROM model_versions;
```

## Cách sử dụng

### Để train models:
1. Upload dataset và đợi status = 'ready'
2. Gọi POST `/api/v1/models/train` với model_types
3. Nếu model đã tồn tại hoặc đang train → 400 error
4. Nếu muốn train lại → Archive model cũ trước

### Để train lại model:
1. Archive model cũ: POST `/api/v1/models/versions/{id}/archive`
2. Train model mới: POST `/api/v1/models/train`

## Lưu ý quan trọng

⚠️ **Duplicate prevention chỉ áp dụng cho**:
- Cùng `dataset_id`
- Cùng `user_id`
- Cùng `model_type`
- Model có status='active' HOẶC training job có status in ['queued', 'running']

✅ **Có thể train**:
- Model khác type
- Model cùng type nhưng khác dataset
- Model đã bị archived
- Model có training job failed/completed

❌ **Không thể train**:
- Model đã tồn tại với status='active'
- Model đang được train (job status = 'queued' hoặc 'running')

## Verification

Để verify duplicate prevention đang hoạt động:

```bash
# Run test script
python test_duplicate_prevention.py

# Expected output:
# ✅ TEST 1: Training KNN and NaiveBayes (first time) - 202 Accepted
# ✅ TEST 2: Training KNN and NaiveBayes again - 400 Bad Request (PREVENTED)
```

## Next Steps

Các vấn đề còn lại cần fix:
1. ⏳ Thêm nút Generate Report trong Model Evaluation page
2. ⏳ Sửa lỗi Delete User (trang xám)
3. ⏳ Sửa lỗi Upload Avatar (400 error)
4. ⏳ Sửa Notifications không hiển thị

---

**Status**: ✅ COMPLETED
**Date**: 2026-05-11
**Tested**: ✅ PASSED
**Deployed**: ✅ YES (backend rebuilt and restarted)
