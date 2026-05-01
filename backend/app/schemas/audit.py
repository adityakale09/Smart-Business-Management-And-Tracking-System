"""
Audit log schemas for request/response validation
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class AuditLogResponse(BaseModel):
    """Response schema for audit log entries"""
    id: int
    user_id: Optional[int] = None
    username: Optional[str] = None
    action: str
    entity_type: str
    entity_id: Optional[int] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class AuditLogFilters(BaseModel):
    """Schema for audit log filters"""
    user_id: Optional[int] = None
    action: Optional[str] = None
    entity_type: Optional[str] = None
    status: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search: Optional[str] = None


class AuditLogStats(BaseModel):
    """Schema for audit log statistics"""
    total_logs: int
    successful_actions: int
    failed_actions: int
    period_days: int
    top_users: List[Dict[str, Any]]
    top_actions: List[Dict[str, Any]]
