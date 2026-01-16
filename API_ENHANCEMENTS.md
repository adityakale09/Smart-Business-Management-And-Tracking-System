# 🔌 New API Endpoints Reference

Quick reference for all newly implemented endpoints.

---

## 🔐 Authentication & User Management

### Change Password
```http
POST /api/auth/change-password
Authorization: Bearer {token}
Content-Type: application/json

{
  "current_password": "oldpassword",
  "new_password": "newpassword"
}
```

### Update Own Profile
```http
PUT /api/auth/me
Authorization: Bearer {token}
Content-Type: application/json

{
  "email": "newemail@example.com",
  "full_name": "New Name"
}
```

### List All Users (Admin Only)
```http
GET /api/users?skip=0&limit=100
Authorization: Bearer {admin_token}
```

### Get User by ID (Admin Only)
```http
GET /api/users/{user_id}
Authorization: Bearer {admin_token}
```

### Update User (Admin Only)
```http
PUT /api/users/{user_id}
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "email": "updated@example.com",
  "full_name": "Updated Name",
  "role": "manager",
  "is_active": true
}
```

### Deactivate User (Admin Only)
```http
DELETE /api/users/{user_id}
Authorization: Bearer {admin_token}
```

---

## 📄 Sales & Invoices

### Download Invoice PDF
```http
GET /api/sales/{sale_id}/invoice
Authorization: Bearer {token}
```
Returns: PDF file `invoice_{transaction_id}.pdf`

### Export Sales to CSV
```http
GET /api/sales/export/csv?start_date=2024-01-01&end_date=2024-12-31
Authorization: Bearer {manager_token}
```
Returns: CSV file `sales_export_YYYYMMDD.csv`

### Export Sales to Excel
```http
GET /api/sales/export/excel?start_date=2024-01-01&end_date=2024-12-31
Authorization: Bearer {manager_token}
```
Returns: Excel file `sales_export_YYYYMMDD.xlsx`

---

## 📦 Inventory Export

### Export Inventory to CSV
```http
GET /api/inventory/export/csv?category=Electronics&low_stock=true
Authorization: Bearer {manager_token}
```
Returns: CSV file `inventory_export_YYYYMMDD.csv`

**Query Parameters:**
- `category` (optional) - Filter by category
- `low_stock` (optional, boolean) - Only low stock items

### Export Inventory to Excel
```http
GET /api/inventory/export/excel?category=Electronics&low_stock=true
Authorization: Bearer {manager_token}
```
Returns: Excel file `inventory_export_YYYYMMDD.xlsx`

---

## 🔑 Role Requirements

| Endpoint | Minimum Role Required |
|----------|----------------------|
| Change Password | Any authenticated user |
| Update Own Profile | Any authenticated user |
| List Users | Admin |
| Get User | Admin |
| Update User | Admin |
| Delete User | Admin |
| Download Invoice | Employee |
| Export Sales CSV/Excel | Manager |
| Export Inventory CSV/Excel | Manager |

---

## 💡 Usage Examples

### JavaScript/Fetch
```javascript
// Change password
const response = await fetch('http://localhost:8000/api/auth/change-password', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    current_password: 'old123',
    new_password: 'new456'
  })
});

// Download invoice
const invoiceResponse = await fetch(`http://localhost:8000/api/sales/123/invoice`, {
  headers: { 'Authorization': `Bearer ${token}` }
});
const blob = await invoiceResponse.blob();
const url = window.URL.createObjectURL(blob);
const a = document.createElement('a');
a.href = url;
a.download = 'invoice.pdf';
a.click();

// Export to Excel
const exportResponse = await fetch('http://localhost:8000/api/sales/export/excel', {
  headers: { 'Authorization': `Bearer ${managerToken}` }
});
const excelBlob = await exportResponse.blob();
// Handle download...
```

### Python/Requests
```python
import requests

# Change password
response = requests.post(
    'http://localhost:8000/api/auth/change-password',
    headers={'Authorization': f'Bearer {token}'},
    json={
        'current_password': 'old123',
        'new_password': 'new456'
    }
)

# Download invoice
response = requests.get(
    'http://localhost:8000/api/sales/123/invoice',
    headers={'Authorization': f'Bearer {token}'}
)
with open('invoice.pdf', 'wb') as f:
    f.write(response.content)

# Export sales
response = requests.get(
    'http://localhost:8000/api/sales/export/excel',
    headers={'Authorization': f'Bearer {manager_token}'},
    params={'start_date': '2024-01-01', 'end_date': '2024-12-31'}
)
with open('sales_report.xlsx', 'wb') as f:
    f.write(response.content)
```

### cURL
```bash
# Change password
curl -X POST http://localhost:8000/api/auth/change-password \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"current_password":"old123","new_password":"new456"}'

# Download invoice
curl -X GET http://localhost:8000/api/sales/123/invoice \
  -H "Authorization: Bearer YOUR_TOKEN" \
  --output invoice.pdf

# Export sales to Excel
curl -X GET "http://localhost:8000/api/sales/export/excel?start_date=2024-01-01" \
  -H "Authorization: Bearer MANAGER_TOKEN" \
  --output sales_report.xlsx

# List users (admin)
curl -X GET http://localhost:8000/api/users \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

---

## ❌ Error Responses

### 400 Bad Request
```json
{
  "detail": "Current password is incorrect"
}
```

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 403 Forbidden
```json
{
  "detail": "Not enough permissions"
}
```

### 404 Not Found
```json
{
  "detail": "Sale not found"
}
```

---

## 📊 Response Examples

### Successful Password Change
```json
{
  "message": "Password changed successfully"
}
```

### User Profile Update
```json
{
  "id": 5,
  "email": "newemail@example.com",
  "username": "user123",
  "full_name": "New Name",
  "role": "employee",
  "is_active": true
}
```

### User List
```json
[
  {
    "id": 1,
    "email": "admin@example.com",
    "username": "admin",
    "full_name": "Admin User",
    "role": "admin",
    "is_active": true
  },
  {
    "id": 2,
    "email": "manager@example.com",
    "username": "manager",
    "full_name": "Manager User",
    "role": "manager",
    "is_active": true
  }
]
```

---

## 🔄 Integration with Frontend

Add these endpoints to your frontend API client:

**`frontend/src/api/auth.js`**
```javascript
export const changePassword = async (currentPassword, newPassword) => {
  const response = await apiClient.post('/auth/change-password', {
    current_password: currentPassword,
    new_password: newPassword
  });
  return response.data;
};

export const updateProfile = async (profileData) => {
  const response = await apiClient.put('/auth/me', profileData);
  return response.data;
};

export const listUsers = async (skip = 0, limit = 100) => {
  const response = await apiClient.get('/users', {
    params: { skip, limit }
  });
  return response.data;
};
```

**`frontend/src/api/sales.js`**
```javascript
export const downloadInvoice = async (saleId) => {
  const response = await apiClient.get(`/sales/${saleId}/invoice`, {
    responseType: 'blob'
  });
  // Create download link
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `invoice_${saleId}.pdf`);
  document.body.appendChild(link);
  link.click();
  link.remove();
};

export const exportSalesCSV = async (filters) => {
  const response = await apiClient.get('/sales/export/csv', {
    params: filters,
    responseType: 'blob'
  });
  // Handle download...
};
```

---

## 🧪 Testing with Swagger UI

Access the interactive API documentation:
```
http://localhost:8000/docs
```

1. Click "Authorize" button
2. Enter your Bearer token
3. Try out the new endpoints
4. Download generated files directly

---

**Last Updated:** January 15, 2026  
**API Version:** 1.0.0
