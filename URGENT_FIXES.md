# Các sửa lỗi khẩn cấp cần thực hiện

## Đã hoàn thành ✅

### 1. Xóa sạch dữ liệu training
```bash
# Đã chạy script clean_training_data.sql
# Kết quả: 
# - Deleted 12 training jobs
# - Deleted 6 model versions  
# - Deleted 36 training progress records
# - Deleted 0 notifications
```

### 2. Restart backend
```bash
docker-compose restart backend
```

## Cần làm ngay ⚠️

### 1. Thêm nút Generate Report trong Model Evaluation

**File**: `frontend/app/models/evaluation/[versionId]/page.tsx`

Thêm sau dòng 241 (sau nút Archive):

```typescript
{user.role === 'Admin' && (
  <div className="flex gap-2">
    <button
      onClick={handleGenerateReport}
      disabled={generating}
      className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-medium disabled:opacity-50"
    >
      {generating ? 'Generating...' : 'Generate Report'}
    </button>
    <button
      onClick={handleArchiveClick}
      disabled={archiving}
      className={`px-4 py-2 rounded font-medium text-white disabled:opacity-50 ${
        modelVersion.status === 'active'
          ? 'bg-orange-600 hover:bg-orange-700'
          : 'bg-green-600 hover:bg-green-700'
      }`}
    >
      {archiving ? 'Processing...' : (modelVersion.status === 'active' ? 'Archive Model' : 'Unarchive Model')}
    </button>
  </div>
)}
```

Thêm state và handler:

```typescript
const [generating, setGenerating] = useState(false);

const handleGenerateReport = async () => {
  if (!token || !versionId) return;
  
  try {
    setGenerating(true);
    const response = await fetch(`${API_BASE_URL}/reports/generate`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model_version_id: versionId,
        include_confusion_matrix: true,
        include_roc_curve: true,
        include_feature_importance: true
      })
    });
    
    if (!response.ok) throw new Error('Failed to generate report');
    
    const report = await response.json();
    
    // Download report
    const downloadResponse = await fetch(`${API_BASE_URL}/reports/${report.id}/download`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (!downloadResponse.ok) throw new Error('Failed to download report');
    
    const blob = await downloadResponse.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `model_report_${modelVersion.model_type}_${Date.now()}.pdf`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
    
    alert('Report generated and downloaded successfully!');
  } catch (err) {
    console.error('Error generating report:', err);
    alert('Failed to generate report: ' + (err instanceof Error ? err.message : 'Unknown error'));
  } finally {
    setGenerating(false);
  }
};
```

### 2. Sửa lỗi Upload Avatar

**Vấn đề**: Lỗi 400 Bad Request khi upload avatar

**File**: `backend/api/routes/auth.py` hoặc `backend/api/routes/users.py`

Kiểm tra endpoint upload avatar:

```bash
# Xem logs chi tiết
docker logs churn-backend --tail 200 | grep -i "avatar\|profile\|upload"
```

**Giải pháp tạm thời**: 
1. Kiểm tra file size limit (max 2MB)
2. Kiểm tra file type (chỉ cho phép jpg, png, gif)
3. Kiểm tra S3/MinIO connection

### 3. Sửa lỗi Delete User

**Vấn đề**: Trang xám, không có phản hồi

**Debug steps**:

1. Mở DevTools Console (F12)
2. Vào trang `/admin/users`
3. Click delete user
4. Xem errors trong Console

**Các nguyên nhân có thể**:

A. **CORS Error**:
```bash
# Kiểm tra CORS settings
docker exec churn-backend grep -r "CORS_ORIGINS" /app/backend/
```

B. **Network Error**:
```javascript
// Trong DevTools Console, test API:
fetch('http://localhost:8000/api/v1/users', {
  headers: {
    'Authorization': 'Bearer ' + JSON.parse(localStorage.getItem('auth-storage')).state.token
  }
})
.then(r => r.json())
.then(console.log)
.catch(console.error)
```

C. **Frontend Error**:
```bash
# Rebuild frontend
docker-compose build frontend
docker-compose up -d frontend
```

### 4. Sửa Notifications không hiển thị

**Vấn đề**: Không có notifications sau khi training

**Kiểm tra**:

```sql
-- Connect to database
docker exec -it churn-postgres psql -U churn_user -d churn_prediction

-- Check notifications
SELECT * FROM notifications ORDER BY created_at DESC LIMIT 10;

-- Check if notification service is creating notifications
SELECT 
  tj.id,
  tj.model_type,
  tj.status,
  tj.created_at,
  COUNT(n.id) as notification_count
FROM training_jobs tj
LEFT JOIN notifications n ON n.training_job_id = tj.id
GROUP BY tj.id, tj.model_type, tj.status, tj.created_at
ORDER BY tj.created_at DESC;
```

**Nếu không có notifications**:

Kiểm tra `backend/workers/training_tasks.py`:
- Line 95-105: Create notification for success
- Line 138-150: Create notification for failure

**Test notification service**:

```python
# Tạo file test_notification.py
import requests

API_URL = "http://localhost:8000/api/v1"
TOKEN = "your-token-here"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Get notifications
response = requests.get(f"{API_URL}/notifications", headers=headers)
print("Notifications:", response.json())

# Get unread count
response = requests.get(f"{API_URL}/notifications/unread-count", headers=headers)
print("Unread count:", response.json())
```

## Quick Fix Commands

### Rebuild tất cả
```bash
docker-compose down
docker-compose build
docker-compose up -d
```

### Xem logs real-time
```bash
# Backend
docker logs churn-backend -f

# Frontend  
docker logs churn-frontend -f

# Celery
docker logs churn-celery-worker -f
```

### Clear browser cache
```
Ctrl + Shift + Delete
hoặc
Ctrl + F5 (hard refresh)
```

### Test API endpoints
```bash
# Get token from browser
TOKEN="your-token-here"

# Test users endpoint
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/users

# Test notifications
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/notifications

# Test models
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/models/versions
```

## Priority Order

1. **HIGHEST**: Sửa duplicate models (đã restart backend) ✅
2. **HIGH**: Thêm nút Generate Report (cần update frontend)
3. **HIGH**: Sửa Delete User (cần debug)
4. **MEDIUM**: Sửa Upload Avatar (cần debug)
5. **MEDIUM**: Sửa Notifications (cần kiểm tra)

## Next Steps

1. Train lại models để test duplicate fix
2. Thêm Generate Report button
3. Debug Delete User với DevTools
4. Debug Upload Avatar với logs
5. Kiểm tra Notifications trong database

## Contact

Nếu cần hỗ trợ thêm:
1. Cung cấp screenshots của errors
2. Cung cấp browser console logs
3. Cung cấp backend logs
4. Mô tả chi tiết các bước đã thử
