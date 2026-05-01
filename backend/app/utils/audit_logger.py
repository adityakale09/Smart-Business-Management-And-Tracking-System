"""
Audit logging utility for tracking user actions and failures
"""

import logging
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from fastapi import Request
import traceback

from app.models.audit import AuditLog

# Set up audit logger
audit_logger = logging.getLogger("audit")


def log_audit(
    db: Session,
    action: str,
    entity_type: str,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    entity_id: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None,
    status: str = "success",
    error_message: Optional[str] = None
):
    """
    Create an audit log entry
    
    Args:
        db: Database session
        action: Action performed (CREATE, UPDATE, DELETE, LOGIN, etc.)
        entity_type: Type of entity (User, Sale, Inventory, etc.)
        user_id: ID of user performing action
        username: Username of user performing action
        entity_id: ID of affected entity
        details: Additional details about the action
        request: FastAPI request object (to extract IP, user agent)
        status: Status of action (success, failure)
        error_message: Error message if action failed
    """
    try:
        # Extract IP and user agent from request if available
        ip_address = None
        user_agent = None
        
        if request:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")
        
        # Create audit log entry
        audit_log = AuditLog(
            user_id=user_id,
            username=username,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            error_message=error_message
        )
        
        db.add(audit_log)
        db.commit()
        
        # Log to audit logger for file-based audit trail
        log_level = logging.WARNING if status == "failure" else logging.INFO
        audit_logger.log(
            log_level,
            f"[{status.upper()}] {action} {entity_type} (ID: {entity_id}) by {username} (User: {user_id})",
            extra={"ip": ip_address, "error": error_message}
        )
        
    except Exception as e:
        # Log the audit logging failure but don't raise
        audit_logger.error(f"Audit logging failed for {action} {entity_type}: {str(e)}")
        try:
            db.rollback()
        except Exception:
            pass


def log_login(
    db: Session,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    request: Optional[Request] = None,
    status: str = "success",
    error_message: Optional[str] = None
):
    """Log user login attempt (success or failure)"""
    log_audit(
        db, "LOGIN", "User",
        user_id=user_id,
        username=username,
        entity_id=user_id,
        request=request,
        status=status,
        error_message=error_message
    )


def log_create(
    db: Session,
    entity_type: str,
    entity_id: int,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    details: Optional[Dict] = None,
    request: Optional[Request] = None,
    status: str = "success",
    error_message: Optional[str] = None
):
    """Log entity creation (success or failure)"""
    log_audit(
        db, "CREATE", entity_type,
        user_id=user_id,
        username=username,
        entity_id=entity_id,
        details=details,
        request=request,
        status=status,
        error_message=error_message
    )


def log_update(
    db: Session,
    entity_type: str,
    entity_id: int,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    details: Optional[Dict] = None,
    request: Optional[Request] = None,
    status: str = "success",
    error_message: Optional[str] = None
):
    """Log entity update (success or failure)"""
    log_audit(
        db, "UPDATE", entity_type,
        user_id=user_id,
        username=username,
        entity_id=entity_id,
        details=details,
        request=request,
        status=status,
        error_message=error_message
    )


def log_delete(
    db: Session,
    entity_type: str,
    entity_id: int,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    details: Optional[Dict] = None,
    request: Optional[Request] = None,
    status: str = "success",
    error_message: Optional[str] = None
):
    """Log entity deletion (success or failure)"""
    log_audit(
        db, "DELETE", entity_type,
        user_id=user_id,
        username=username,
        entity_id=entity_id,
        details=details,
        request=request,
        status=status,
        error_message=error_message
    )


def log_password_change(
    db: Session,
    user_id: int,
    username: str,
    request: Optional[Request] = None,
    status: str = "success",
    error_message: Optional[str] = None
):
    """Log password change (success or failure)"""
    log_audit(
        db, "PASSWORD_CHANGE", "User",
        user_id=user_id,
        username=username,
        entity_id=user_id,
        request=request,
        status=status,
        error_message=error_message
    )


def log_permission_denied(
    db: Session,
    user_id: int,
    username: str,
    action: str,
    entity_type: str,
    request: Optional[Request] = None,
    reason: str = "Insufficient permissions"
):
    """Log permission denied events"""
    log_audit(
        db, action, entity_type,
        user_id=user_id,
        username=username,
        request=request,
        status="failure",
        error_message=reason
    )


def log_exception(
    db: Session,
    action: str,
    entity_type: str,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    entity_id: Optional[int] = None,
    request: Optional[Request] = None,
    exception: Optional[Exception] = None,
    details: Optional[Dict] = None
):
    """Log an exception/error during an operation"""
    error_msg = str(exception) if exception else "Unknown error"
    
    log_audit(
        db, action, entity_type,
        user_id=user_id,
        username=username,
        entity_id=entity_id,
        details=details,
        request=request,
        status="failure",
        error_message=error_msg
    )
