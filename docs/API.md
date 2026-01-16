# API Documentation

## Base URL
```
http://localhost:8000/api
```

## Authentication

All protected endpoints require a Bearer token in the Authorization header:
```
Authorization: Bearer <access_token>
```

## Endpoints

### Authentication

#### Register User
```
POST /api/auth/register
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "username": "username",
  "password": "password123",
  "full_name": "Full Name",
  "role": "employee"  // admin, manager, employee, vendor
}
```

#### Login
```
POST /api/auth/login
```

**Request Body:**
```json
{
  "username": "username",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user_id": 1,
  "role": "admin"
}
```

#### Get Current User
```
GET /api/auth/me
```

### Sales

#### Get All Sales
```
GET /api/sales?skip=0&limit=100&start_date=2024-01-01&end_date=2024-12-31
```

#### Get Sale by ID
```
GET /api/sales/{sale_id}
```

#### Create Sale
```
POST /api/sales
```

**Request Body:**
```json
{
  "customer_name": "John Doe",
  "product_id": 1,
  "quantity": 2,
  "unit_price": 29.99,
  "payment_method": "cash",
  "notes": "Optional notes"
}
```

#### Get Sales Summary
```
GET /api/sales/stats/summary?days=30
```

### Inventory

#### Get All Inventory
```
GET /api/inventory?skip=0&limit=100&category=Electronics&low_stock=true
```

#### Get Inventory Item
```
GET /api/inventory/{item_id}
```

#### Create Inventory Item
```
POST /api/inventory
```

**Request Body:**
```json
{
  "sku": "PROD-001",
  "name": "Product Name",
  "description": "Product description",
  "category": "Electronics",
  "quantity": 100,
  "reorder_level": 10,
  "unit_price": 29.99,
  "supplier": "Supplier Name",
  "location": "Warehouse A"
}
```

#### Update Inventory Item
```
PUT /api/inventory/{item_id}
```

#### Restock Inventory
```
POST /api/inventory/{item_id}/restock?quantity=50&notes=Restocked
```

### Employees

#### Get All Employees
```
GET /api/employees?skip=0&limit=100&department=Sales&status_filter=active
```

#### Get Employee
```
GET /api/employees/{employee_id}
```

#### Create Employee
```
POST /api/employees
```

#### Update Employee
```
PUT /api/employees/{employee_id}
```

#### Create Attendance
```
POST /api/employees/attendance
```

#### Get Employee Attendance
```
GET /api/employees/attendance/{employee_id}?start_date=2024-01-01&end_date=2024-12-31
```

### Analytics

#### Get Dashboard Stats
```
GET /api/analytics/dashboard
```

#### Get Sales Trend
```
GET /api/analytics/sales/trend?days=30&group_by=day
```

#### Get Inventory Analysis
```
GET /api/analytics/inventory/analysis
```

#### Get Employee Performance
```
GET /api/analytics/employee/performance?days=30
```

### AI Automation

#### Forecast Sales
```
POST /api/ai/forecast/sales?days_ahead=30
```

#### Get Reorder Suggestions
```
POST /api/ai/automate/reorder-suggestions
```

#### Get Task Suggestions
```
POST /api/ai/automate/task-suggestions
```

## Role-Based Access Control

- **Admin**: Full access to all endpoints
- **Manager**: Access to management and analytics endpoints
- **Employee**: Limited access to assigned tasks and own data
- **Vendor**: External access for inventory-related operations

## Error Responses

All errors follow this format:
```json
{
  "detail": "Error message"
}
```

Common status codes:
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error

