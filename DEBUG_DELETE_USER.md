# Debug Delete User Issue

## ✅ Backend API Test - PASSED

Backend API hoạt động hoàn hảo:
- ✅ DELETE `/api/v1/users/{id}` returns 204 No Content
- ✅ User được xóa thành công khỏi database
- ✅ Verification passed

## ⚠️ Frontend Issue

Vấn đề là ở **frontend** - trang bị xám khi click delete button.

### Các nguyên nhân có thể:

1. **JavaScript Error** - Component crash do lỗi runtime
2. **Missing Toast Library** - `sonner` toast library chưa được cài đặt
3. **React Error Boundary** - Không có error boundary để catch errors

## 🔍 Cách Debug

### Bước 1: Mở Browser DevTools

1. Mở trang `/admin/users` trong browser
2. Nhấn **F12** để mở DevTools
3. Chuyển sang tab **Console**

### Bước 2: Click Delete User

1. Click vào icon 🗑️ (Trash) bên cạnh một user
2. Modal xác nhận sẽ hiện ra
3. Click "Delete User" button
4. **Quan sát Console** để xem có error nào không

### Bước 3: Kiểm tra Network Tab

1. Chuyển sang tab **Network** trong DevTools
2. Click delete user lại
3. Tìm request `DELETE /api/v1/users/{id}`
4. Kiểm tra:
   - ✅ Request có được gửi không?
   - ✅ Status code là gì? (should be 204)
   - ✅ Response headers có đúng không?

### Bước 4: Kiểm tra Console Errors

Các lỗi thường gặp:

#### Error 1: "sonner is not defined" hoặc "toast is not defined"
```
Uncaught ReferenceError: toast is not defined
```

**Giải pháp**: Cài đặt sonner library
```bash
cd frontend
npm install sonner
```

#### Error 2: "Cannot read property 'id' of undefined"
```
TypeError: Cannot read property 'id' of undefined
```

**Giải pháp**: Kiểm tra user object có tồn tại không

#### Error 3: CORS Error
```
Access to fetch at 'http://localhost:8000/api/v1/users/...' from origin 'http://localhost:3000' has been blocked by CORS policy
```

**Giải pháp**: Kiểm tra CORS settings trong backend

## 🛠️ Quick Fixes

### Fix 1: Thêm Error Boundary

Thêm error boundary vào `frontend/app/admin/users/page.tsx`:

```typescript
'use client';

import { Component, ReactNode } from 'react';

class ErrorBoundary extends Component<
  { children: ReactNode },
  { hasError: boolean; error: Error | null }
> {
  constructor(props: { children: ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: any) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="bg-white shadow rounded-lg p-6 max-w-md">
            <h2 className="text-lg font-semibold text-red-600 mb-4">
              Something went wrong
            </h2>
            <p className="text-gray-700 mb-4">
              {this.state.error?.message || 'Unknown error'}
            </p>
            <button
              onClick={() => window.location.reload()}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded"
            >
              Reload Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Wrap your component with ErrorBoundary
export default function UsersManagementPage() {
  return (
    <ErrorBoundary>
      {/* Your existing code */}
    </ErrorBoundary>
  );
}
```

### Fix 2: Kiểm tra Sonner Installation

```bash
# Check if sonner is installed
cd frontend
npm list sonner

# If not installed, install it
npm install sonner

# Rebuild frontend
cd ..
docker-compose build frontend
docker-compose up -d frontend
```

### Fix 3: Add Console Logging

Thêm logging vào `handleDeleteUser` function:

```typescript
const handleDeleteUser = async (userId: string) => {
  console.log('🗑️ Delete user called:', userId);
  
  if (!token) {
    console.error('❌ No token available');
    return;
  }

  // Safety: cannot delete self
  if (userId === user?.id) {
    console.warn('⚠️ Cannot delete self');
    toast.error('You cannot delete your own account.');
    return;
  }

  // ... rest of the code
  
  try {
    console.log('📤 Sending delete request...');
    setActionLoading(userId);
    await deleteUser(userId, token);
    console.log('✅ Delete successful');
    
    setDeleteModalUser(null);
    toast.success(`User ${targetUser?.email || userId} has been deleted.`);
    
    console.log('🔄 Refreshing users list...');
    await fetchUsers();
    console.log('✅ Users list refreshed');
  } catch (err) {
    console.error('❌ Error deleting user:', err);
    const message = err instanceof Error ? err.message : 'Failed to delete user';
    toast.error(message);
    setError(message);
  } finally {
    setActionLoading(null);
  }
};
```

## 📊 Expected Console Output

Khi delete user thành công, bạn sẽ thấy:

```
🗑️ Delete user called: 2b732aaa-7a3e-4000-87bf-ba40e951a926
📤 Sending delete request...
✅ Delete successful
🔄 Refreshing users list...
✅ Users list refreshed
```

## 🔧 Manual Test Steps

### Test 1: Verify Frontend Can Reach Backend

Mở browser console và chạy:

```javascript
// Get token from localStorage
const authStorage = JSON.parse(localStorage.getItem('auth-storage'));
const token = authStorage?.state?.token;

// Test list users
fetch('http://localhost:8000/api/v1/users', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
.then(r => r.json())
.then(console.log)
.catch(console.error);
```

### Test 2: Test Delete User Directly

```javascript
// Get token
const authStorage = JSON.parse(localStorage.getItem('auth-storage'));
const token = authStorage?.state?.token;

// Replace with actual user ID
const userId = 'USER_ID_HERE';

// Test delete
fetch(`http://localhost:8000/api/v1/users/${userId}`, {
  method: 'DELETE',
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
.then(r => {
  console.log('Status:', r.status);
  return r.text();
})
.then(console.log)
.catch(console.error);
```

## 📝 Report Back

Sau khi debug, hãy cung cấp:

1. **Console errors** (nếu có)
2. **Network tab** - screenshot của DELETE request
3. **Behavior** - Trang có bị xám không? Có error message nào không?
4. **Browser** - Chrome, Firefox, Edge?
5. **Steps** - Các bước bạn đã thử

## 🎯 Next Steps

Nếu vẫn không hoạt động sau khi debug:

1. Kiểm tra `sonner` library có được cài đặt không
2. Thêm error boundary để catch errors
3. Thêm console logging để track execution
4. Test API trực tiếp từ browser console
5. Kiểm tra CORS headers

---

**Status**: ⏳ DEBUGGING
**Backend**: ✅ WORKING
**Frontend**: ⚠️ NEEDS DEBUG
