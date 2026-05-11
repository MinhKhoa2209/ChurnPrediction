# Upload Avatar Fix

## 🔍 Vấn đề phát hiện

### Frontend
- Upload file image và convert sang **base64 string**
- Base64 string rất dài (có thể > 100KB cho ảnh 2MB)
- Gửi base64 string trong JSON body

### Backend
- Avatar field chỉ nhận **string với max_length=500**
- Base64 string vượt quá giới hạn → **400 Bad Request**

```python
# backend/domain/schemas/auth.py
avatar: Optional[str] = Field(None, max_length=500, description="User's avatar URL")
```

## ✅ Giải pháp

Có 3 options:

### Option 1: Upload file lên S3/MinIO (RECOMMENDED)
Tạo endpoint riêng để upload avatar file lên S3, trả về URL

**Ưu điểm**:
- ✅ Đúng chuẩn (lưu file trên storage, không lưu trong database)
- ✅ Performance tốt (không gửi base64 qua network)
- ✅ Scalable

**Nhược điểm**:
- ⚠️ Cần implement endpoint mới
- ⚠️ Cần setup S3/MinIO (đã có sẵn)

### Option 2: Tăng max_length của avatar field
Cho phép lưu base64 string dài trong database

**Ưu điểm**:
- ✅ Dễ implement (chỉ cần sửa 1 dòng)
- ✅ Không cần endpoint mới

**Nhược điểm**:
- ❌ Bad practice (lưu binary data trong text field)
- ❌ Database bloat
- ❌ Performance kém

### Option 3: Dùng external URL
User nhập URL của ảnh từ internet

**Ưu điểm**:
- ✅ Đơn giản nhất
- ✅ Không cần storage

**Nhược điểm**:
- ❌ User experience kém
- ❌ Phụ thuộc external service

## 🛠️ Implementation - Option 1 (Recommended)

### Step 1: Tạo endpoint upload avatar

**File**: `backend/api/routes/auth.py`

```python
from fastapi import File, UploadFile
from backend.infrastructure.storage import StorageService

@router.post(
    "/upload-avatar",
    response_model=dict,
    responses={
        200: {"description": "Avatar uploaded successfully"},
        400: {"description": "Invalid file"},
        401: {"description": "Unauthorized"},
    },
)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    # Validate file size (max 2MB)
    contents = await file.read()
    if len(contents) > 2 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size must be less than 2MB"
        )
    
    # Reset file pointer
    await file.seek(0)
    
    # Upload to S3/MinIO
    storage = StorageService()
    file_path = f"avatars/{current_user.id}/{file.filename}"
    
    try:
        avatar_url = await storage.upload_file(
            file=file.file,
            bucket_name="avatars",  # Create this bucket
            object_name=file_path,
            content_type=file.content_type
        )
        
        # Update user avatar in database
        from uuid import UUID
        from backend.domain.models.user import User
        
        user = db.query(User).filter(User.id == UUID(current_user.id)).first()
        if user:
            user.avatar = avatar_url
            db.commit()
        
        return {
            "avatar_url": avatar_url,
            "message": "Avatar uploaded successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload avatar: {str(e)}"
        )
```

### Step 2: Update frontend

**File**: `frontend/app/settings/page.tsx`

```typescript
const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
  const file = e.target.files?.[0];
  if (!file) return;

  // Validate file type
  if (!file.type.startsWith('image/')) {
    setSaveMessage({ type: 'error', text: 'Please select an image file' });
    return;
  }

  // Validate file size (max 2MB)
  if (file.size > 2 * 1024 * 1024) {
    setSaveMessage({ type: 'error', text: 'Image size must be less than 2MB' });
    return;
  }

  // Upload file to backend
  setIsLoading(true);
  setSaveMessage(null);

  try {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/auth/upload-avatar`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: formData,
    });

    if (!response.ok) {
      throw new Error('Failed to upload avatar');
    }

    const data = await response.json();
    setAvatar(data.avatar_url);
    
    // Update auth store immediately
    if (user) {
      setAuth({
        ...user,
        avatar: data.avatar_url,
      }, token);
    }

    setSaveMessage({ type: 'success', text: 'Avatar uploaded successfully' });
    setTimeout(() => setSaveMessage(null), 3000);
  } catch (error) {
    console.error('Error uploading avatar:', error);
    setSaveMessage({ type: 'error', text: 'Failed to upload avatar' });
  } finally {
    setIsLoading(false);
  }
};
```

### Step 3: Create avatars bucket

```bash
# Run this in backend container
docker exec -it churn-backend python -c "
from backend.infrastructure.storage import StorageService
storage = StorageService()
storage.create_bucket('avatars')
print('Avatars bucket created')
"
```

## 🚀 Quick Fix - Option 2 (Temporary)

Nếu muốn fix nhanh, tăng max_length:

**File**: `backend/domain/schemas/auth.py`

```python
avatar: Optional[str] = Field(None, max_length=500000, description="User's avatar URL or base64")
```

Sau đó rebuild backend:

```bash
docker-compose build backend
docker-compose up -d backend
```

⚠️ **Warning**: Đây chỉ là temporary fix. Nên implement Option 1 cho production.

## 🧪 Testing

### Test upload avatar:

```bash
# Get token
TOKEN="your-token-here"

# Upload avatar
curl -X POST http://localhost:8000/api/v1/auth/upload-avatar \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/image.jpg"

# Expected response:
# {
#   "avatar_url": "http://localhost:9000/avatars/user-id/image.jpg",
#   "message": "Avatar uploaded successfully"
# }
```

## 📊 Current Status

- ✅ **Vấn đề phát hiện**: Avatar field quá ngắn (500 chars) cho base64 string
- ⏳ **Giải pháp đề xuất**: Upload file lên S3/MinIO
- ⏳ **Quick fix**: Tăng max_length (temporary)

## 🎯 Recommendation

1. **Ngay lập tức**: Dùng Option 2 (tăng max_length) để unblock user
2. **Sau đó**: Implement Option 1 (S3 upload) cho production-ready solution

---

**Status**: ⏳ SOLUTION READY
**Priority**: HIGH
**Effort**: Medium (Option 1) / Low (Option 2)
