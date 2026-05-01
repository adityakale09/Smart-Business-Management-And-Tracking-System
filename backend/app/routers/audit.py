"""
Audit log router for querying and managing audit logs
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from datetime import datetime, timedelta
from typing import List, Optional

from app.database import get_db
from app.models.audit import AuditLog
from app.schemas.audit import AuditLogResponse, AuditLogFilters, AuditLogStats
from app.core.security import get_current_user
from app.models.user import User
from app.utils.audit_logger import log_permission_denied, log_exception

router = APIRouter(prefix="/api/audit-logs", tags=["audit"])


@router.get("", response_model=dict)
async def get_audit_logs(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=500, description="Number of records to return"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action (CREATE, UPDATE, DELETE, LOGIN, etc.)"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    status: Optional[str] = Query(None, description="Filter by status (success, failure)"),
    date_from: Optional[datetime] = Query(None, description="Filter logs from this date (ISO 8601)"),
    date_to: Optional[datetime] = Query(None, description="Filter logs until this date (ISO 8601)"),
    search: Optional[str] = Query(None, description="Search in entity_type, action, username"),
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get audit logs with filtering and pagination.
    
    Query Parameters:
    - skip: Pagination offset
    - limit: Number of records per page (1-500)
    - user_id: Filter by user ID
    - action: Filter by action
    - entity_type: Filter by entity type
    - status: Filter by status
    - date_from: Start date (ISO 8601)
    - date_to: End date (ISO 8601)
    - search: Search query
    """
    # Permission check: only admins can view all audit logs
    user_role = current_user.get("role") if isinstance(current_user, dict) else current_user.role
    if user_role != "admin":
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
    
    try:
        # Build query
        query = db.query(AuditLog)
        
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
        
        if date_from:
            filters.append(AuditLog.created_at >= date_from)
        
        if date_to:
            # Add 1 day to include the entire end date
            filters.append(AuditLog.created_at <= date_to + timedelta(days=1))
        
        if search:
            search_term = f"%{search}%"
            filters.append(
                AuditLog.action.ilike(search_term)
                | AuditLog.entity_type.ilike(search_term)
                | AuditLog.username.ilike(search_term)
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
    if user_role != "admin":
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
        actions = db.query(AuditLog.action).distinct().order_by(AuditLog.action).all()
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
    if user_role != "admin":
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
        types = db.query(AuditLog.entity_type).distinct().order_by(AuditLog.entity_type).all()
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
    if user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view audit logs"
        )
    
    try:
        date_from = datetime.utcnow() - timedelta(days=days)
        
        # Total logs
        total_logs = db.query(AuditLog).filter(AuditLog.created_at >= date_from).count()
        
        # Successful vs failed
        successful = db.query(AuditLog).filter(
            and_(
                AuditLog.created_at >= date_from,
                AuditLog.status == "success"
            )
        ).count()
        
        failed = db.query(AuditLog).filter(
            and_(
                AuditLog.created_at >= date_from,
                AuditLog.status == "failure"
            )
        ).count()
        
        # Most active users
        top_users = db.query(AuditLog.username, func.count(AuditLog.id).label("count")).filter(
            AuditLog.created_at >= date_from
        ).group_by(AuditLog.username).order_by(desc("count")).limit(10).all()
        
        # Most common actions
        top_actions = db.query(AuditLog.action, func.count(AuditLog.id).label("count")).filter(
            AuditLog.created_at >= date_from
        ).group_by(AuditLog.action).order_by(desc("count")).limit(10).all()
        
        return AuditLogStats(
            total_logs=total_logs,
            successful_actions=successful,
            failed_actions=failed,
            period_days=days,
            top_users=[{"username": u[0], "count": u[1]} for u in top_users],
            top_actions=[{"action": a[0], "count": a[1]} for a in top_actions]
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific audit log entry."""
    user_role = current_user.get("role") if isinstance(current_user, dict) else current_user.role
    if user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view audit logs"
        )
    
    log = db.query(AuditLog).filter(AuditLog.id == log_id).first()
    
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit log not found"
        )
    
    return AuditLogResponse.from_orm(log)


@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_audit_log(
    log_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a specific audit log entry (only for super admins).
    Use with caution as this removes audit history.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete audit logs"
        )
    
    log = db.query(AuditLog).filter(AuditLog.id == log_id).first()
    
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit log not found"
        )
    
    db.delete(log)
    db.commit()
 