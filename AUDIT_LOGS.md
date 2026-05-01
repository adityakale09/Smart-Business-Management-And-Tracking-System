# Audit Logs Feature

## Overview

The Audit Logs feature provides comprehensive tracking of all critical system activities and user actions. It enables administrators to:
- Monitor all user activities
- Track changes to critical entities
- Investigate security incidents
- Maintain compliance records

## Backend Architecture

### Database Model

**Table:** `audit_logs`

```python
class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id: int                    # Primary key
    user_id: Optional[int]     # Foreign key to users table
    username: Optional[str]    # Username for reference
    action: str               # CREATE, UPDATE, DELETE, LOGIN, LOGOUT, etc.
    entity_type: str          # User, Sale, Inventory, Employee, etc.
    entity_id: Optional[int]  # ID of affected entity
    details: Dict             # JSON field with additional context
    ip_address: Optional[str] # Client IP
    user_agent: Optional[str] # Browser/Client info
    status: str               # success or failure
    error_message: Optional[str] # Error details
    created_at: datetime      # Timestamp of action
```

**Indexes:**
- `action` - for filtering by action type
- `created_at` - for fast date range queries
- `entity_type` - for filtering by entity
- `user_id` - for filtering by user

### API Endpoints

#### Get Audit Logs (with filtering)

```
GET /api/audit-logs
```

**Query Parameters:**
- `skip: int` - Pagination offset (default: 0)
- `limit: int` - Records per page (default: 50, max: 500)
- `user_id: int` - Filter by user ID
- `action: str` - Filter by action (CREATE, UPDATE, DELETE, LOGIN, etc.)
- `entity_type: str` - Filter by entity type
- `status: str` - Filter by status (success/failure)
- `date_from: datetime` - Start date (ISO 8601)
- `date_to: datetime` - End date (ISO 8601)
- `search: str` - Search in action, entity_type, username

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "user_id": 5,
      "username": "john_admin",
      "action": "UPDATE",
      "entity_type": "Sales",
      "entity_id": 123,
      "details": {
        "changed_fields": {
          "status": ["pending", "completed"],
          "total_amount": [1000, 1050]
        }
      },
      "ip_address": "192.168.1.1",
      "user_agent": "Mozilla/5.0...",
      "status": "success",
      "error_message": null,
      "created_at": "2024-04-14T15:30:00"
    }
  ],
  "total": 250,
  "skip": 0,
  "limit": 50
}
```

#### Get Available Actions

```
GET /api/audit-logs/actions
```

Returns list of all unique actions in audit logs for filter UI.

#### Get Available Entity Types

```
GET /api/audit-logs/entity-types
```

Returns list of all unique entity types for filter UI.

#### Get Statistics

```
GET /api/audit-logs/statistics?days=7
```

**Response:**
```json
{
  "total_logs": 500,
  "successful_actions": 485,
  "failed_actions": 15,
  "period_days": 7,
  "top_users": [
    {"username": "john_admin", "count": 150},
    {"username": "jane_manager", "count": 120}
  ],
  "top_actions": [
    {"action": "VIEW", "count": 300},
    {"action": "UPDATE", "count": 150},
    {"action": "CREATE", "count": 35},
    {"action": "DELETE", "count": 15}
  ]
}
```

#### Get Log Detail

```
GET /api/audit-logs/{log_id}
```

Returns detailed information about a specific audit log entry.

#### Delete Log

```
DELETE /api/audit-logs/{log_id}
```

**⚠️ Admin Only:** Use with caution as this removes audit history.

## Logging Actions

### Using the Audit Logger

```python
from app.utils.audit_logger import log_audit

# In your router/service
log_audit(
    db=db,
    action="CREATE",
    entity_type="Sales",
    user_id=current_user.id,
    username=current_user.username,
    entity_id=sale_id,
    details={
        "customer": customer_name,
        "total": total_amount,
        "items_count": len(items)
    },
    request=request,  # For IP and user agent
    status="success"
)
```

### Common Action Types

- `CREATE` - New entity created
- `UPDATE` - Entity modified
- `DELETE` - Entity deleted
- `LOGIN` - User login
- `LOGOUT` - User logout
- `EXPORT` - Data exported
- `IMPORT` - Data imported
- `VIEW` - Data viewed
- `DOWNLOAD` - File downloaded

### Common Entity Types

- User
- Sales
- Inventory
- Employee
- Receipt
- Customer
- Invoice
- Expense

## Frontend Implementation

### Components

#### AuditLogs Page (`src/pages/AuditLogs.jsx`)

Main page displaying audit logs with:
- Statistics dashboard (total, successful, failed logs)
- Filtering interface
- Paginated table view
- Detail modal for individual logs

**Features:**
- Server-side pagination (50 logs per page)
- Multi-filter support (user, action, entity, date range, status)
- Real-time statistics
- Search across action, entity type, and username
- Drill-down into log details
- Delete audit logs (admin only)

#### AuditLogsFilter Component (`src/components/AuditLogsFilter.jsx`)

Reusable filter component with:
- Search input
- Dropdown filters (action, entity type, status)
- Date range picker
- Clear filters button

### API Client (`src/api/audit.js`)

```javascript
auditApi.getAuditLogs(params)        // Get logs with filtering
auditApi.getAvailableActions()       // Get action options
auditApi.getEntityTypes()            // Get entity type options
auditApi.getStatistics(days)         // Get statistics
auditApi.getAuditLogDetail(logId)   // Get log details
auditApi.deleteAuditLog(logId)      // Delete a log
```

## Permission Model

### Access Control

- **Non-Admins**: Cannot access audit logs
- **Admins**: Full access to view, filter, and delete audit logs

In router:
```python
if current_user.role != "admin":
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Only administrators can view audit logs"
    )
```

## Best Practices

### 1. Log Critical Operations

Always log:
- User creation/deletion/modification
- Sensitive data access
- Failed login attempts
- Admin actions
- Data export/download
- System configuration changes

### 2. Include Context

Provide meaningful details:
```python
details={
    "changed_fields": {
        "status": [old_value, new_value],
        "amount": [1000, 1050]
    },
    "reason": "Customer paid in full",
    "reference_id": "INV-123"
}
```

### 3. Capture Failures

Log failed operations with error details:
```python
log_audit(
    db=db,
    action="DELETE",
    entity_type="Sales",
    user_id=current_user.id,
    username=current_user.username,
    entity_id=sale_id,
    request=request,
    status="failure",
    error_message="Cannot delete: Sale has associated invoices"
)
```

### 4. Performance Considerations

- Logs are indexed on key fields (action, created_at, entity_type, user_id)
- Use date range filters to limit query results
- Archive old logs periodically (90+ days)
- Regular vacuuming of the audit_logs table

## Querying Examples

### Get all failed operations in the last 7 days

```
GET /api/audit-logs?status=failure&date_from=2024-04-07&date_to=2024-04-14
```

### Get all DELETE operations by a specific user

```
GET /api/audit-logs?user_id=5&action=DELETE
```

### Search for activities related to a specific sale

```
GET /api/audit-logs?search=Sales&entity_type=Sales
```

### Get failed login attempts

```
GET /api/audit-logs?action=LOGIN&status=failure
```

## Data Retention Policy

- **Active Logs**: Keep all logs for 1 year
- **Archive**: Move logs older than 1 year to archive table
- **Exports**: Export to CSV/JSON for long-term storage
- **Deletion**: Only delete logs older than 3 years or per compliance requirements

## Security Considerations

1. **Access Control**: Only admins can view audit logs
2. **Audit Immutability**: Logs should not be easily modified
3. **IP Logging**: Captures client IP for security investigation
4. **User Agent**: Tracks browser/client information
5. **Sensitive Data**: Do not log password hashes or API keys in details field

## Troubleshooting

### Slow Audit Log Queries

**Solution:** Add database indexes and use date range filters

```sql
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);
CREATE INDEX idx_audit_logs_composite ON audit_logs(action, entity_type, created_at);
```

### Missing Logs

**Check:**
1. Verify log_audit() is being called for the action
2. Check user role has admin access to view
3. Verify date range filter is correct
4. Check for any exceptions in server logs

## Future Enhancements

- [ ] Real-time audit log streaming via WebSocket
- [ ] Advanced analytics and trends
- [ ] Audit log grouping and correlation
- [ ] Alert rules for suspicious activities
- [ ] Integration with external SIEM systems
- [ ] Multi-language support for audit log messages
- [ ] User export of audit reports
