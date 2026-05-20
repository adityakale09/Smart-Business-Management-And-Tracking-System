"""
Audit log router for querying, exporting, and managing audit logs.
Audit logs are append-only — deletion is only allowed through retention policy cleanup.
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status, Request
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func, or_, cast, String
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import csv
import io

from app.database import get_db
from app.models.audit import AuditLog
from app.schemas.audit import (
    AuditLogResponse, AuditLogFilters, AuditLogStats,
    AuditExportRequest, IntegrityReport, RetentionPolicy
)
from app.core.security import get_current_user
from app.models.user import User
from app.utils.audit_logger import log_permission_denied, log_exception, log_delete

router = APIRouter(prefix="/api/audit-logs", tags=["audit"])


# Maximum retention period (in days) before logs can be cleaned up
MAX_RETENTION_DAYS = 365
DEFAULT_RETENTION_DAYS = 90


def _check_admin_access(current_user, db: Session, request: Request = None):
    """Check if current user is admin or super_admin, log permission denied if not."""
    user_role = current_user.get("role") if isinstance(current_user, dict) else current_user.role
    if user_role not in ("admin", "super_admin"):
        user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
        username = current_user.get("username") if isinstance(current_user, dict) else current_user.username
        log_permission_denied(
            db,
            user_id=user_id,
            username=username,
            action="VIEW",
            entity_type="AuditLog",
            request=request,
            reason="Non-admin attempted to access audit logs"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view audit logs"
        )


@router.get("", response_model=dict)
async def get_audit_logs(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=500, description="Number of records to return"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action (CREATE, UPDATE, DELETE, LOGIN, etc.)"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    status: Optional[str] = Query(None, description="Filter by status (success, failure)"),
    severity: Optional[str] = Query(None, description="Filter by severity (INFO, WARNING, CRITICAL)"),
    date_from: Optional[datetime] = Query(None, description="Filter logs from this date (ISO 8601)"),
    date_to: Optional[datetime] = Query(None, description="Filter logs until this date (ISO 8601)"),
    search: Optional[str] = Query(None, description="Search in action, entity_type, username, and details"),
    correlation_id: Optional[str] = Query(None, description="Filter by correlation ID for grouped events"),
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get audit logs with comprehensive filtering, full-text search, and pagination.
    
    Query Parameters:
    - skip: Pagination offset
    - limit: Number of records per page (1-500)
    - user_id: Filter by user ID
    - action: Filter by action
    - entity_type: Filter by entity type
    - status: Filter by status (success, failure)
    - severity: Filter by severity (INFO, WARNING, CRITICAL)
    - date_from: Start date (ISO 8601)
    - date_to: End date (ISO 8601)
    - search: Full-text search across action, entity_type, username, and details JSON
    - correlation_id: Filter by correlation ID to view related events
    """
    _check_admin_access(current_user, db, request)
    
    try:
        # Build query
        query = db.query(AuditLog)
        
        # Apply organization scoping
        org_id = current_user.get("organization_id") if isinstance(current_user, dict) else getattr(current_user, 'organization_id', None)
        if org_id is not None:
            query = query.filter(AuditLog.organization_id == int(org_id))
        
        # Apply filters
        filters = []
        
        if user_id:
            filters.append(AuditLog.user_id == user_id)
        
        if action:
            filters.append(AuditLog.action == action)
        
        if entity_type:
            filters.append(AuditLog.entity_type == entity_type)
        
        if status:
            filters.append(AuditLog.status == status)
        
        if severity:
            filters.append(AuditLog.severity == severity)
        
        if date_from:
            filters.append(AuditLog.created_at >= date_from)
        
        if date_to:
            # Add 1 day to include the entire end date
            filters.append(AuditLog.created_at <= date_to + timedelta(days=1))
        
        if correlation_id:
            filters.append(AuditLog.correlation_id == correlation_id)
        
        if search:
            search_term = f"%{search}%"
            # Search across standard fields AND the details JSON field
            filters.append(
                or_(
                    AuditLog.action.ilike(search_term),
                    AuditLog.entity_type.ilike(search_term),
                    AuditLog.username.ilike(search_term),
                    AuditLog.details.cast(String).ilike(search_term),
                    AuditLog.error_message.ilike(search_term),
                    AuditLog.ip_address.ilike(search_term),
                )
            )
        
        # Apply all filters
        if filters:
            query = query.filter(and_(*filters))
        
        # Get total count before pagination
        total = query.count()
        
        # Get paginated results, ordered by most recent first
        logs = query.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()
        
        return {
            "items": [AuditLogResponse.from_orm(log) for log in logs],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except HTTPException:
        raise
    except Exception as e:
        user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
        username = current_user.get("username") if isinstance(current_user, dict) else current_user.username
        log_exception(
            db,
            "VIEW",
            "AuditLog",
            user_id=user_id,
            username=username,
            request=request,
            exception=e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve audit logs: {str(e)}"
        )


@router.get("/actions", response_model=List[str])
async def get_available_actions(
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of all unique actions in audit logs (for filtering UI)."""
    user_role = current_user.get("role") if isinstance(current_user, dict) else current_user.role
    if user_role not in ("admin", "super_admin"):
        user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
        username = current_user.get("username") if isinstance(current_user, dict) else current_user.username
        log_permission_denied(
            db,
            user_id=user_id,
            username=username,
            action="VIEW",
            entity_type="AuditLog",
            request=request,
            reason="Non-admin attempted to view audit actions"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view audit logs"
        )
    
    try:
        actions = db.query(AuditLog.action).distinct()
        org_id = current_user.get("organization_id") if isinstance(current_user, dict) else getattr(current_user, 'organization_id', None)
        if org_id is not None:
            actions = actions.filter(AuditLog.organization_id == int(org_id))
        actions = actions.order_by(AuditLog.action).all()
        return [action[0] for action in actions if action[0]]
    except Exception as e:
        print(f"[AUDIT ERROR] get_available_actions: {str(e)}")
        try:
            user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
            username = current_user.get("username") if isinstance(current_user, dict) else current_user.username
            log_exception(
                db,
                "VIEW",
                "AuditLog",
                user_id=user_id,
                username=username,
                request=request,
                exception=e
            )
        except:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve actions: {str(e)}"
        )


@router.get("/entity-types", response_model=List[str])
async def get_entity_types(
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of all unique entity types in audit logs (for filtering UI)."""
    user_role = current_user.get("role") if isinstance(current_user, dict) else current_user.role
    if user_role not in ("admin", "super_admin"):
        user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
        username = current_user.get("username") if isinstance(current_user, dict) else current_user.username
        log_permission_denied(
            db,
            user_id=user_id,
            username=username,
            action="VIEW",
            entity_type="AuditLog",
            request=request,
            reason="Non-admin attempted to view audit entity types"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view audit logs"
        )
    
    try:
        types = db.query(AuditLog.entity_type).distinct()
        org_id = current_user.get("organization_id") if isinstance(current_user, dict) else getattr(current_user, 'organization_id', None)
        if org_id is not None:
            types = types.filter(AuditLog.organization_id == int(org_id))
        types = types.order_by(AuditLog.entity_type).all()
        return [t[0] for t in types if t[0]]
    except Exception as e:
        print(f"[AUDIT ERROR] get_entity_types: {str(e)}")
        try:
            user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
            username = current_user.get("username") if isinstance(current_user, dict) else current_user.username
            log_exception(
                db,
                "VIEW",
                "AuditLog",
                user_id=user_id,
                username=username,
                request=request,
                exception=e
            )
        except:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve entity types: {str(e)}"
        )


@router.get("/statistics", response_model=AuditLogStats)
async def get_audit_statistics(
    days: int = Query(7, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get audit log statistics for the dashboard."""
    user_role = current_user.get("role") if isinstance(current_user, dict) else current_user.role
    if user_role not in ("admin", "super_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view audit logs"
        )
    
    try:
        date_from = datetime.now(timezone.utc) - timedelta(days=days)
        
        org_id = current_user.get("organization_id") if isinstance(current_user, dict) else getattr(current_user, 'organization_id', None)
        
        # Total logs
        total_query = db.query(AuditLog).filter(AuditLog.created_at >= date_from)
        if org_id is not None:
            total_query = total_query.filter(AuditLog.organization_id == int(org_id))
        total_logs = total_query.count()
        
        # Successful vs failed
        success_query = db.query(AuditLog).filter(
            and_(
                AuditLog.created_at >= date_from,
                AuditLog.status == "success"
            )
        )
        failed_query = db.query(AuditLog).filter(
            and_(
                AuditLog.created_at >= date_from,
                AuditLog.status == "failure"
            )
        )
        if org_id is not None:
            success_query = success_query.filter(AuditLog.organization_id == int(org_id))
            failed_query = failed_query.filter(AuditLog.organization_id == int(org_id))
        successful = success_query.count()
        failed = failed_query.count()
        
        # Most active users
        top_users = db.query(AuditLog.username, func.count(AuditLog.id).label("count")).filter(
            AuditLog.created_at >= date_from
        )
        if org_id is not None:
            top_users = top_users.filter(AuditLog.organization_id == int(org_id))
        top_users = top_users.group_by(AuditLog.username).order_by(desc("count")).limit(10).all()
        
        # Most common actions
        top_actions = db.query(AuditLog.action, func.count(AuditLog.id).label("count")).filter(
            AuditLog.created_at >= date_from
        )
        if org_id is not None:
            top_actions = top_actions.filter(AuditLog.organization_id == int(org_id))
        top_actions = top_actions.group_by(AuditLog.action).order_by(desc("count")).limit(10).all()
        
        # Severity breakdown
        severity_query = db.query(AuditLog.severity, func.count(AuditLog.id)).filter(
            AuditLog.created_at >= date_from
        )
        if org_id is not None:
            severity_query = severity_query.filter(AuditLog.organization_id == int(org_id))
        severity_query = severity_query.group_by(AuditLog.severity)
        severity_counts = dict(severity_query.all())
        
        # Calculate failure rate
        failure_rate = round((failed / total_logs * 100), 2) if total_logs > 0 else 0.0
        
        return AuditLogStats(
            total_logs=total_logs,
            successful_actions=successful,
            failed_actions=failed,
            period_days=days,
            top_users=[{"username": u[0], "count": u[1]} for u in top_users],
            top_actions=[{"action": a[0], "count": a[1]} for a in top_actions],
            failure_rate=failure_rate,
            severity_counts=severity_counts
        )
    except Exception as e:
        print(f"[AUDIT ERROR] get_audit_statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve statistics: {str(e)}"
        )


@router.get("/{log_id}", response_model=AuditLogResponse)
async def get_audit_log_detail(
    log_id: int,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific audit log entry."""
    _check_admin_access(current_user, db, request)
    
    log = db.query(AuditLog).filter(AuditLog.id == log_id).first()
    
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit log not found"
        )
    
    # Check organization scope
    org_id = current_user.get("organization_id") if isinstance(current_user, dict) else getattr(current_user, 'organization_id', None)
    if org_id is not None and log.organization_id != int(org_id) and log.organization_id is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit log not found"
        )
    
    return AuditLogResponse.from_orm(log)


@router.get("/export/{export_format}", response_class=StreamingResponse)
async def export_audit_logs(
    export_format: str,
    date_from: Optional[datetime] = Query(None, description="Filter logs from this date"),
    date_to: Optional[datetime] = Query(None, description="Filter logs until this date"),
    action: Optional[str] = Query(None, description="Filter by action"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export audit logs in CSV or JSON format for compliance reporting.
    
    Args:
        export_format: "csv" or "json"
        date_from: Start date for filtering
        date_to: End date for filtering
        action: Filter by action type
        entity_type: Filter by entity type
        status: Filter by status
        user_id: Filter by user ID
        severity: Filter by severity level
    """
    _check_admin_access(current_user, db, request)
    
    if export_format not in ("csv", "json"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format must be 'csv' or 'json'"
        )
    
    try:
        # Build query with filters
        query = db.query(AuditLog)
        filters = []
        
        # Apply organization scoping
        org_id = current_user.get("organization_id") if isinstance(current_user, dict) else getattr(current_user, 'organization_id', None)
        if org_id is not None:
            filters.append(AuditLog.organization_id == int(org_id))
        
        if date_from:
            filters.append(AuditLog.created_at >= date_from)
        if date_to:
            filters.append(AuditLog.created_at <= date_to + timedelta(days=1))
        if action:
            filters.append(AuditLog.action == action)
        if entity_type:
            filters.append(AuditLog.entity_type == entity_type)
        if status:
            filters.append(AuditLog.status == status)
        if user_id:
            filters.append(AuditLog.user_id == user_id)
        if severity:
            filters.append(AuditLog.severity == severity)
        
        if filters:
            query = query.filter(and_(*filters))
        
        logs = query.order_by(desc(AuditLog.created_at)).all()
        
        if export_format == "json":
            return _export_json(logs)
        else:
            return _export_csv(logs)
            
    except HTTPException:
        raise
    except Exception as e:
        user_id_val = current_user.get("id") if isinstance(current_user, dict) else current_user.id
        username_val = current_user.get("username") if isinstance(current_user, dict) else current_user.username
        log_exception(
            db, "EXPORT", "AuditLog",
            user_id=user_id_val,
            username=username_val,
            request=request,
            exception=e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export audit logs: {str(e)}"
        )


@router.get("/integrity/verify", response_model=IntegrityReport)
async def verify_audit_integrity(
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Verify the integrity of the audit log hash chain.
    
    Checks:
    1. Each entry's hash matches its content
    2. Each entry's previous_hash matches the hash of the previous entry
    3. The chain is unbroken from the first entry
    
    This is a critical compliance feature (SOC 2, PCI-DSS 10.5).
    """
    _check_admin_access(current_user, db, request)
    
    try:
        entries = db.query(AuditLog).order_by(AuditLog.id.asc()).all()
        
        # Apply organization scoping
        org_id = current_user.get("organization_id") if isinstance(current_user, dict) else getattr(current_user, 'organization_id', None)
        if org_id is not None:
            entries = [e for e in entries if e.organization_id == int(org_id) or e.organization_id is None]
        
        tampered_ids = []
        prev_hash = None
        chain_broken = False
        verified_count = 0
        
        for entry in entries:
            # Recompute and verify this entry's hash
            expected_hash = entry.compute_hash()
            if entry.hash != expected_hash:
                tampered_ids.append(entry.id)
                chain_broken = True
            else:
                verified_count += 1
            
            # Verify previous_hash link
            if entry.previous_hash != prev_hash:
                if entry.previous_hash is not None or prev_hash is not None:
                    chain_broken = True
            
            prev_hash = entry.hash
        
        first_verified = True
        if entries and entries[0].previous_hash is not None:
            first_verified = False
            chain_broken = True
        
        total = len(entries)
        tampered = len(tampered_ids)
        
        if total == 0:
            report = "No audit log entries to verify."
        elif tampered == 0 and not chain_broken:
            report = f"All {total} audit log entries verified successfully. Hash chain integrity is intact."
        elif tampered > 0:
            report = f"TAMPER DETECTED: {tampered} of {total} entries have been modified! IDs: {tampered_ids}"
        else:
            report = f"Chain integrity issue detected. Some entries may have been removed or modified."
        
        return IntegrityReport(
            total_entries=total,
            verified_entries=verified_count,
            tampered_entries=tampered,
            tampered_log_ids=tampered_ids,
            chain_broken=chain_broken,
            first_entry_verified=first_verified,
            last_entry=entries[-1].id if entries else None,
            report=report
        )
        
    except HTTPException:
        raise
    except Exception as e:
        user_id_val = current_user.get("id") if isinstance(current_user, dict) else current_user.id
        username_val = current_user.get("username") if isinstance(current_user, dict) else current_user.username
        log_exception(
            db, "VERIFY", "AuditLog",
            user_id=user_id_val,
            username=username_val,
            request=request,
            exception=e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Integrity verification failed: {str(e)}"
        )


@router.delete("/retention/cleanup")
async def cleanup_audit_logs(
    retention_days: int = Query(365, ge=1, le=3650, description="Retention period in days"),
    dry_run: bool = Query(True, description="Preview only, no actual deletion"),
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Clean up audit logs older than the specified retention period.
    
    This is the ONLY way audit logs can be deleted — to ensure audit trail integrity.
    Use dry_run=True to preview before actually deleting.
    
    Args:
        retention_days: Delete logs older than this many days (1-3650)
        dry_run: If True, only count records that would be deleted (no actual deletion)
    """
    _check_admin_access(current_user, db, request)
    
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
        
        # Count records to be deleted
        delete_query = db.query(AuditLog).filter(
            AuditLog.created_at < cutoff_date
        )
        org_id = current_user.get("organization_id") if isinstance(current_user, dict) else getattr(current_user, 'organization_id', None)
        if org_id is not None:
            delete_query = delete_query.filter(AuditLog.organization_id == int(org_id))
        records_to_delete = delete_query.count()
        
        if dry_run:
            return {
                "dry_run": True,
                "retention_days": retention_days,
                "cutoff_date": cutoff_date.isoformat(),
                "records_to_delete": records_to_delete,
                "message": f"{records_to_delete} records would be deleted. Use dry_run=false to execute."
            }
        
        # Get the IDs being deleted for logging
        deleted_ids_query = db.query(AuditLog.id).filter(
                AuditLog.created_at < cutoff_date
            )
        if org_id is not None:
            deleted_ids_query = deleted_ids_query.filter(AuditLog.organization_id == int(org_id))
        deleted_ids = [
            row[0] for row in deleted_ids_query.all()
        ]
        
        # Actually delete
        delete_exec_query = db.query(AuditLog).filter(
            AuditLog.created_at < cutoff_date
        )
        if org_id is not None:
            delete_exec_query = delete_exec_query.filter(AuditLog.organization_id == int(org_id))
        deleted_count = delete_exec_query.delete(synchronize_session=False)
        
        db.commit()
        
        user_id_val = current_user.get("id") if isinstance(current_user, dict) else current_user.id
        username_val = current_user.get("username") if isinstance(current_user, dict) else current_user.username
        log_delete(
            db, "AuditLog", None,
            user_id=user_id_val,
            username=username_val,
            details={
                "deleted_count": deleted_count,
                "retention_days": retention_days,
                "cutoff_date": cutoff_date.isoformat(),
                "deleted_ids": deleted_ids[:100]  # Only log first 100 IDs
            },
            request=request
        )
        
        return {
            "dry_run": False,
            "retention_days": retention_days,
            "cutoff_date": cutoff_date.isoformat(),
            "records_deleted": deleted_count,
            "message": f"Successfully deleted {deleted_count} audit log records older than {retention_days} days."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        user_id_val = current_user.get("id") if isinstance(current_user, dict) else current_user.id
        username_val = current_user.get("username") if isinstance(current_user, dict) else current_user.username
        log_exception(
            db, "CLEANUP", "AuditLog",
            user_id=user_id_val,
            username=username_val,
            request=request,
            exception=e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Retention cleanup failed: {str(e)}"
        )


def _export_csv(logs: List[AuditLog]) -> StreamingResponse:
    """Export audit logs as CSV."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "ID", "Timestamp", "User ID", "Username", "Action", "Entity Type",
        "Entity ID", "Status", "Severity", "IP Address", "User Agent",
        "Error Message", "Correlation ID", "Hash", "Previous Hash"
    ])
    
    # Write data
    for log in logs:
        writer.writerow([
            log.id,
            log.created_at.isoformat() if log.created_at else "",
            log.user_id or "",
            log.username or "",
            log.action,
            log.entity_type,
            log.entity_id or "",
            log.status,
            log.severity,
            log.ip_address or "",
            log.user_agent or "",
            log.error_message or "",
            log.correlation_id or "",
            log.hash or "",
            log.previous_hash or ""
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=audit_logs_export_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )


def _export_json(logs: List[AuditLog]) -> StreamingResponse:
    """Export audit logs as JSON."""
    import json
    
    data = [log.to_dict() for log in logs]
    json_str = json.dumps(data, indent=2, default=str)
    
    return StreamingResponse(
        iter([json_str]),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=audit_logs_export_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        }
    )
 