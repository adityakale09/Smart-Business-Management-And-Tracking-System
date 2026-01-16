"""
Audit logging utility for tracking user actions
"""

from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from fastapi import Request

from app.models.audit import AuditLog


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
        
    except Exception as e:
        # Don't fail the main operation if audit logging fails
        print(f"[WARNING] Audit logging failed: {e}")
        db.rollback()


def log_login(db: Session, user_id: int, username: str, request: Optional[Request] = None, status: str = "success", error_message: Optional[str] = None):
    """Log user login attempt"""
    log_audit(db, "LOGIN", "User", user_id, username, user_id, None, request, status, error_message)


def log_logout(db: Session, user_id: int, username: str, request: Optional[Request] = None):
    """Log user logout"""
    log_audit(db, "LOGOUT", "User", user_id, username, user_id, None, request)


def log_create(db: Session, entity_type: str, entity_id: int, user_id: Optional[int] = None, username: Optional[str] = None, details: Optional[Dict] = None, request: Optional[Request] = None):
    """Log entity creation"""
    log_audit(db, "CREATE", entity_type, user_id, username, entity_id, details, request)


def log_update(db: Session, entity_type: str, entity_id: int, user_id: Optional[int] = None, username: Optional[str] = None, details: Optional[Dict] = None, request: Optional[Request] = None):
    """Log entity update"""
    log_audit(db, "UPDATE", entity_type, user_id, username, entity_id, details, request)


def log_delete(db: Session, entity_type: str, entity_id: int, user_id: Optional[int] = None, username: Optional[str] = None, details: Optional[Dict] = None, request: Optional[Request] = None):
    """Log entity deletion"""
    log_audit(db, "DELETE", entity_type, user_id, username, entity_id, details, request)


def log_password_change(db: Session, user_id: int, username: str, request: Optional[Request] = None):
    """Log password change"""
    log_audit(db, "PASSWORD_CHANGE", "User", user_id, username, user_id, None, request)
