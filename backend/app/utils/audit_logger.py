"""
Audit logging utility for tracking user actions and failures.

Implements industry-standard audit logging:
- Hash chain integrity (SHA-256 linking) for tamper detection
- Severity classification (INFO, WARNING, CRITICAL)
- Before/after value tracking for changes
- Correlation IDs for request tracing
- UTC timezone-aware timestamps
"""

import logging
import time
import uuid
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from fastapi import Request
import traceback
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone

from app.models.audit import AuditLog

# Set up audit logger
_audit_logger = logging.getLogger("audit")

# Prevent duplicate handler configuration
if not _audit_logger.handlers:
    _audit_logger.setLevel(logging.INFO)
    
    # Determine log directory
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # File handler with rotation (10 MB per file, keep 30 backup files)
    log_file = os.path.join(log_dir, "audit.log")
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=30,  # Keep 30 rotated files
        encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        "%(asctime)s UTC [%(levelname)s] %(message)s | ip=%(ip)s correlation_id=%(correlation_id)s severity=%(severity)s hash=%(hash)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_formatter.converter = time.gmtime  # Use UTC
    file_handler.setFormatter(file_formatter)
    _audit_logger.addHandler(file_handler)
    
    # Console handler for development
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if os.getenv("DEBUG") else logging.WARNING)
    console_formatter = logging.Formatter(
        "AUDIT: %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    _audit_logger.addHandler(console_handler)
    
    # Prevent propagation to root logger to avoid duplicate logs
    _audit_logger.propagate = False

# Severity levels
SEVERITY_INFO = "INFO"
SEVERITY_WARNING = "WARNING"
SEVERITY_CRITICAL = "CRITICAL"


def _get_correlation_id(request: Optional[Request] = None) -> Optional[str]:
    """
    Extract or generate a correlation ID for grouping related audit events.
    Uses X-Correlation-ID header if provided, otherwise generates a new one.
    """
    if request:
        correlation_id = request.headers.get("X-Correlation-ID")
        if correlation_id:
            return correlation_id
    return str(uuid.uuid4())



def _get_previous_hash(db: Session) -> Optional[str]:
    """
    Get the hash of the most recent audit log entry for hash chain linking.
    Returns None if no previous entries exist (first entry in chain).
    """
    last_entry = db.query(AuditLog.hash).order_by(AuditLog.id.desc()).first()
    return last_entry[0] if last_entry else None


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
    error_message: Optional[str] = None,
    correlation_id: Optional[str] = None,
    severity: str = SEVERITY_INFO,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None
):
    """
    Create an audit log entry (append-only, immutable, integrity-verified record).
    
    Implements hash chain integrity: each entry stores the SHA-256 hash of the
    previous entry, forming a tamper-evident chain.
    
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
        correlation_id: Correlation ID for grouping related events
        severity: Event severity (INFO, WARNING, CRITICAL)
        old_values: Values before change (for UPDATE tracking)
        new_values: Values after change (for UPDATE tracking)
    """
    try:
        # Extract IP and user agent from request if available
        ip_address = None
        user_agent = None
        
        if request:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")
        
        # Use provided correlation_id or extract/generate one
        final_correlation_id = correlation_id or _get_correlation_id(request)
        
        # Get previous hash for chain linking
        previous_hash = _get_previous_hash(db)
        
        # Create audit log entry (without hash first, then compute it)
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
            error_message=error_message,
            correlation_id=final_correlation_id,
            severity=severity,
            old_values=old_values,
            new_values=new_values,
            previous_hash=previous_hash
        )
        
        db.add(audit_log)
        db.flush()  # Flush to get the ID assigned
        
        # Compute and set the hash for this entry
        audit_log.hash = audit_log.compute_hash()
        
        db.commit()
        
        # Log to audit logger for file-based audit trail
        log_level = logging.CRITICAL if severity == SEVERITY_CRITICAL else (
            logging.WARNING if severity == SEVERITY_WARNING or status == "failure" else logging.INFO
        )
        _audit_logger.log(
            log_level,
            f"[{severity}][{status.upper()}] {action} {entity_type} (ID: {entity_id}) by {username} (User: {user_id}) [correlation: {final_correlation_id}]",
            extra={
                "ip": ip_address or "unknown",
                "error": error_message or "",
                "correlation_id": final_correlation_id or "",
                "severity": severity,
                "hash": audit_log.hash[:16] + "..." if audit_log.hash else "",
                "previous_hash": previous_hash[:16] + "..." if previous_hash else ""
            }
        )
        
    except Exception as e:
        # Log the audit logging failure but don't raise (fail-open)
        _audit_logger.error(f"Audit logging failed for {action} {entity_type}: {str(e)}")
        _audit_logger.error(traceback.format_exc())
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
    severity = SEVERITY_WARNING if status == "failure" else SEVERITY_INFO
    log_audit(
        db, "LOGIN", "User",
        user_id=user_id,
        username=username,
        entity_id=user_id,
        request=request,
        status=status,
        error_message=error_message,
        severity=severity
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
    error_message: Optional[str] = None,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None
):
    """Log entity update (success or failure) with before/after value tracking"""
    log_audit(
        db, "UPDATE", entity_type,
        user_id=user_id,
        username=username,
        entity_id=entity_id,
        details=details,
        request=request,
        status=status,
        error_message=error_message,
        old_values=old_values,
        new_values=new_values
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
    """Log permission denied events (CRITICAL severity for security incidents)"""
    log_audit(
        db, action, entity_type,
        user_id=user_id,
        username=username,
        request=request,
        status="failure",
        error_message=reason,
        severity=SEVERITY_CRITICAL
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
    details: Optional[Dict] = None,
    severity: str = SEVERITY_WARNING
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
        error_message=error_msg,
        severity=severity
    )
