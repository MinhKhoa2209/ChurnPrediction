# Debug Users Page Issue

## Vấn đề
Trang `/admin/users` hiển thị trống (blank page)

## Các bước debug

### 1. Kiểm tra Frontend Console
Mở DevTools (F12) → Console tab và tìm các error messages

### 2. Kiểm tra Network Requests
Mở DevTools (F12) → Network tab:
- Reload trang `/admin/users`
- Tìm request đến `/api/v1/users`
- Kiểm tra:
  - Status code (200, 401, 403, 500?)
  - Response data
  - Request headers (có Authorization header không?)

### 3. Kiểm tra Authentication State
Mở DevTools Console và chạy:
```javascript
// Kiểm tra auth state
const authStorage = localStorage.getItem('auth-storage');
console.log('Auth Storage:', JSON.parse(authStorage));

// Kiểm tra user role
const auth = JSON.parse(authStorage);
console.log('User Role:', auth?.state?.user?.role);
console.log('Is Admin:', auth?.state?.user?.role === 'Admin');
```

### 4. Test API trực tiếp
Mở DevTools Console và chạy:
```javascript
// Lấy token
const authStorage = localStorage.getItem('auth-storage');
const token = JSON.parse(authStorage)?.state?.token;

// Test API
fetch('http://localhost:8000/api/v1/users', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
})
.then(res => res.json())
.then(data => console.log('Users:', data))
.catch(err => console.error('Error:', err));
```

### 5. Kiểm tra Component Rendering
Thêm console.log vào component để debug:

```typescript
// Trong frontend/app/admin/users/page.tsx
console.log('Component mounted');
console.log('User:', user);
console.log('Token:', token);
console.log('Auth Loading:', authLoading);
console.log('Is Loading:', isLoading);
console.log('Users:', users);
console.log('Error:', error);
```

### 6. Kiểm tra Backend Logs
```bash
# Xem logs khi truy cập trang users
docker logs churn-backend -f

# Trong terminal khác, reload trang /admin/users
# Xem có request nào đến backend không
```

### 7. Test với curl
```bash
# Lấy token từ browser (DevTools Console)
# const token = JSON.parse(localStorage.getItem('auth-storage')).state.token

# Test API
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
     http://localhost:8000/api/v1/users | jq .
```

## Các lỗi thường gặp và giải pháp

### Lỗi 1: Trang trắng, không có error
**Nguyên nhân**: Component bị crash hoặc infinite loading

**Giải pháp**:
1. Kiểm tra `authLoading` và `isLoading` state
2. Thêm error boundary
3. Kiểm tra conditional rendering logic

### Lỗi 2: 401 Unauthorized
**Nguyên nhân**: Token hết hạn hoặc không hợp lệ

**Giải pháp**:
1. Đăng xuất và đăng nhập lại
2. Xóa localStorage: `localStorage.clear()`
3. Kiểm tra JWT expiration

### Lỗi 3: 403 Forbidden
**Nguyên nhân**: User không có quyền Admin

**Giải pháp**:
1. Kiểm tra role trong database:
```sql
SELECT id, email, role FROM users WHERE email = 'your-email@example.com';
```
2. Update role nếu cần:
```sql
UPDATE users SET role = 'Admin' WHERE email = 'your-email@example.com';
```

### Lỗi 4: CORS Error
**Nguyên nhân**: Backend không cho phép origin của frontend

**Giải pháp**:
1. Kiểm tra CORS config trong `backend/main.py`
2. Thêm origin của frontend vào `CORS_ORIGINS`
3. Restart backend

### Lỗi 5: Network Error
**Nguyên nhân**: Backend không chạy hoặc không accessible

**Giải pháp**:
```bash
# Kiểm tra backend
docker ps | grep backend

# Test health endpoint
curl http://localhost:8000/health

# Restart backend
docker-compose restart backend
```

## Quick Fix

Nếu không muốn debug chi tiết, thử các bước sau:

### Option 1: Hard Refresh
1. Ctrl + Shift + R (hoặc Cmd + Shift + R trên Mac)
2. Xóa cache browser
3. Đăng nhập lại

### Option 2: Restart Everything
```bash
docker-compose restart
```

### Option 3: Rebuild Frontend
```bash
docker-compose build frontend
docker-compose up -d frontend
```

### Option 4: Run Frontend Locally
```bash
cd frontend
npm install
npm run dev
# Truy cập http://localhost:3000/admin/users
```

## Kết quả mong đợi

Sau khi sửa, trang `/admin/users` sẽ:
- Hiển thị danh sách users
- Có search box
- Có nút delete cho mỗi user (trừ current user)
- Có modal xác nhận khi delete
- Hiển thị toast notification sau khi delete thành công

## Nếu vẫn không hoạt động

1. Thu thập thông tin:
   - Screenshot của trang trắng
   - Console errors
   - Network tab (request/response)
   - Backend logs

2. Kiểm tra file:
   - `frontend/app/admin/users/page.tsx`
   - `frontend/lib/users.ts`
   - `frontend/lib/api.ts`
   - `backend/api/routes/users.py`

3. Tạo issue với đầy đủ thông tin trên
