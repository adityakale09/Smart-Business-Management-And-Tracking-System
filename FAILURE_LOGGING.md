# Audit Logging System - Failure Logging Guide

## Overview

The audit logging system has been enhanced to capture both successful and failed operations, providing comprehensive tracking of system activities for security and compliance purposes.

## Features

### 1. Success and Failure Tracking

All operations log both success and failure states:

```python
# Successful operation
log_create(
    db, "User", user_id,
    user_id=current_user.id,
    username=current_user.username,
    details={"email": user.email},
    request=request,
    status="success"  # Default
)

# Failed operation with error details
log_create(
    db, "User", user_id,
    user_id=current_user.id,
    username=current_user.username,
    details={"email": user.email},
    request=request,
    status="failure",
    error_message="Email already exists"
)
```

### 2. Exception Logging

New `log_exception()` function captures detailed error information:

```python
try:
    # Some operation
    result = risky_operation()
except Exception as e:
    log_exception(
        db,
        action="CREATE",
        entity_type="Sale",
        user_id=current_user.id,
        username=current_user.username,
        entity_id=sale_id,
        request=request,
        exception=e,
        details={"reason": "validation failed"}
    )
    raise
```

**Benefits:**
- Captures full exception message
- Automatically converts exception to string
- Logs with "failure" status
- Includes context (user, action, entity)

### 3. Permission Denied Logging

Dedicated function for permission denied events:

```python
if current_user.role != "admin":
    log_permission_denied(
        db,
        user_id=current_user.id,
        username=current_user.username,
        action="DELETE",
        entity_type="User",
        request=request,
        reason="Non-admin attempted to delete user"
    )
    raise HTTPException(status_code=403, detail="Forbidden")
```

**Features:**
- Auto-sets status to "failure"
- Logs attempted action and entity
- Captures reason for denial
- Tracks IP address from request

### 4. Login Failure Tracking

Enhanced login logging for security:

```python
@router.post("/login")
async def login(credentials: UserLogin, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == credentials.username).first()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        # Log failed attempt
        log_login(
            db,
            user_id=None,  # Unknown user
            username=credentials.username,
            request=request,
            status="failure",
            error_message="Invalid credentials"
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Log successful login
    log_login(
        db,
        user_id=user.id,
        username=user.username,
        request=request,
        status="success"
    )
```

### 5. Crash-Safe Logging

All audit operations are wrapped in error handling:

```python
def log_audit(...):
    try:
        # Create and commit audit log
        audit_log = AuditLog(...)
        db.add(audit_log)
        db.commit()
    except Exception as e:
        # Log error but don't raise
        audit_logger.error(f"Audit logging failed: {str(e)}")
        try:
            db.rollback()
        except Exception:
            pass  # Prevent cascade failures
```

**Safety Features:**
- Main operation never fails due to audit logging
- Audit errors logged separately
- Database rollback on audit failure
- Non-blocking audit operations

## Enhanced Logging Functions

### log_audit()

Core function for all audit operations:

```python
log_audit(
    db: Session,
    action: str,                    # CREATE, UPDATE, DELETE, LOGIN, etc.
    entity_type: str,               # User, Sale, Inventory, etc.
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    entity_id: Optional[int] = None,
    details: Optional[Dict] = None,
    request: Optional[Request] = None,
    status: str = "success",        # success or failure
    error_message: Optional[str] = None
)
```

### log_login()

User authentication tracking:

```python
log_login(
    db: Session,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    request: Optional[Request] = None,
    status: str = "success",           # success or failure
    error_message: Optional[str] = None
)
```

### log_create(), log_update(), log_delete()

Entity operation tracking with failure support:

```python
log_create(
    db: Session,
    entity_type: str,
    entity_id: int,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    details: Optional[Dict] = None,
    request: Optional[Request] = None,
    status: str = "success",           # NEW: Added
    error_message: Optional[str] = None  # NEW: Added
)
```

### log_password_change()

Password modification tracking:

```python
log_password_change(
    db: Session,
    user_id: int,
    username: str,
    request: Optional[Request] = None,
    status: str = "success",           # NEW: Added
    error_message: Optional[str] = None  # NEW: Added
)
```

### log_permission_denied()

Permission denial tracking (NEW):

```python
log_permission_denied(
    db: Session,
    user_id: int,
    username: str,
    action: str,           # CREATE, UPDATE, DELETE, VIEW
    entity_type: str,      # User, Sale, Inventory
    request: Optional[Request] = None,
    reason: str = "Insufficient permissions"
)
```

### log_exception()

Exception tracking (NEW):

```python
log_exception(
    db: Session,
    action: str,
    entity_type: str,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    entity_id: Optional[int] = None,
    request: Optional[Request] = None,
    exception: Optional[Exception] = None,
    details: Optional[Dict] = None
)
```

## Usage Examples

### Example 1: Inventory Creation with Failure Handling

```python
@router.post("/inventory")
async def create_inventory(
    item_data: InventoryCreate,
    request: Request,
    current_user: dict = Depends(require_min_role("manager")),
    db: Session = Depends(get_db)
):
    try:
        # Validate SKU doesn't exist
        if db.query(Inventory).filter(Inventory.sku == item_data.sku).first():
            raise ValueError("SKU already exists")
        
        # Create item
        new_item = Inventory(**item_data.dict())
        db.add(new_item)
        db.commit()
        db.refresh(new_item)
        
        # Log success
        log_create(
            db, "Inventory", new_item.id,
            user_id=int(current_user["user_id"]),
            username=current_user["username"],
            details={"sku": new_item.sku},
            request=request
        )
        
        return new_item
        
    except ValueError as e:
        # Log failure
        log_exception(
            db, "CREATE", "Inventory",
            user_id=int(current_user["user_id"]),
            username=current_user["username"],
            request=request,
            exception=e,
            details={"sku": item_data.sku}
        )
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        db.rollback()
        log_exception(
            db, "CREATE", "Inventory",
            user_id=int(current_user["user_id"]),
            username=current_user["username"],
            request=request,
            exception=e
        )
        raise HTTPException(status_code=500, detail="Creation failed")
```

### Example 2: Permission Denied Event

```python
@router.delete("/audit-logs/{log_id}")
async def delete_audit_log(
    log_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        # Log permission denial
        log_permission_denied(
            db,
            user_id=current_user.id,
            username=current_user.username,
            action="DELETE",
            entity_type="AuditLog",
            request=request,
            reason="Non-admin attempted to delete audit log"
        )
        raise HTTPException(status_code=403, detail="Forbidden")
    
    # Continue with deletion...
```

### Example 3: Audit Router with Exception Handling

```python
@router.get("/audit-logs")
async def get_audit_logs(
    skip: int = 0,
    limit: int = 50,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        log_permission_denied(
            db, current_user.id, current_user.username,
            "VIEW", "AuditLog", request,
            "Attempted to access audit logs"
        )
        raise HTTPException(status_code=403)
    
    try:
        query = db.query(AuditLog)
        total = query.count()
        logs = query.offset(skip).limit(limit).all()
        
        return {"items": logs, "total": total}
        
    except Exception as e:
        log_exception(
            db, "VIEW", "AuditLog",
            user_id=current_user.id,
            username=current_user.username,
            request=request,
            exception=e
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve logs")
```

## Audit Log Fields

When a failure is logged, the audit log captures:

```json
{
  "id": 1,
  "user_id": 5,
  "username": "john_admin",
  "action": "DELETE",
  "entity_type": "User",
  "entity_id": 999,
  "details": {},
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "status": "failure",
  "error_message": "Cannot delete: User has active sessions",
  "created_at": "2024-04-14T15:30:00"
}
```

**Key Fields for Failure Tracking:**
- `status` - "failure" for failed operations
- `error_message` - Detailed error information
- `ip_address` - Source IP for security investigation
- `user_agent` - Browser/client info
- `username` - Who attempted the operation
- `created_at` - When the failure occurred

## Querying Audit Logs for Failures

### Get all failures

```
GET /api/audit-logs?status=failure
```

### Get failed login attempts

```
GET /api/audit-logs?action=LOGIN&status=failure
```

### Get permission denied events

```
GET /api/audit-logs?search=permission&status=failure
```

### Get failures by specific user

```
GET /api/audit-logs?user_id=5&status=failure
```

### Get failures in last 24 hours

```
GET /api/audit-logs?status=failure&date_from=2024-04-13&date_to=2024-04-14
```

## Best Practices

### 1. Always Wrap Risky Operations

```python
try:
    risky_operation()
except Exception as e:
    log_exception(db, action, entity_type, ..., exception=e)
    raise
```

### 2. Include Meaningful Context

```python
log_exception(
    db, "UPDATE", "Sales",
    details={
        "reason": "Insufficient inventory",
        "requested_qty": 100,
        "available_qty": 50
    },
    exception=e
)
```

### 3. Log Permission Denials Immediately

```python
if not has_permission(current_user):
    log_permission_denied(db, ..., reason="Specific reason")
    raise HTTPException(status_code=403)
```

### 4. Don't Expose Internal Errors to Users

```python
try:
    db_operation()
except DatabaseError as e:
    log_exception(db, ..., exception=e)
    # Return generic message to user
    raise HTTPException(status_code=500, detail="Operation failed")
```

### 5. Use Appropriate Error Messages

✅ Good:
- "Email already exists"
- "User not found"
- "Insufficient permissions"
- "Invalid date range"

❌ Avoid:
- "Column 'users.email' cannot be null"
- "Traceback: ..."
- "Foreign key constraint violation"

## Monitoring and Alerts

### Key Metrics to Monitor

1. **Failed Login Attempts** - Multiple failures from same IP
2. **Permission Denied Events** - User attempting unauthorized operations
3. **Operation Failures** - Unusual error patterns
4. **Database Errors** - Connectivity or integrity issues

### Alert Scenarios

- 5+ failed logins in 5 minutes
- Non-admin user attempting to delete audit logs
- Multiple fails for same entity in short time
- Database connection failures

## Troubleshooting

### Failures Not Being Logged

1. Check that `request` parameter is passed to logging functions
2. Verify database connection is available
3. Check audit logger configuration
4. Review application logs for audit logging errors

### Missing Error Messages

1. Ensure `error_message` is provided to logging functions
2. Check that exception is being captured in catch blocks
3. Verify database can store error message length

### Performance Issues

1. Audit logging is non-blocking by design
2. Failures in logging don't affect main operations
3. Audit logs are asynchronously committed
4. Consider archiving old logs periodically
