"""
Audit log schemas for request/response validation
"""

from pydantic import BaseModel, Field
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
    correlation_id: Optional[str] = None
    severity: str = "INFO"
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    hash: Optional[str] = None
    previous_hash: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class AuditLogFilters(BaseModel):
    """Schema for audit log filters"""
    user_id: Optional[int] = None
    action: Optional[str] = None
    entity_type: Optional[str] = None
    status: Optional[str] = None
    severity: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search: Optional[str] = None
    correlation_id: Optional[str] = None
    has_integrity_issue: Optional[bool] = None  # Filter for tampered logs


class AuditLogStats(BaseModel):
    """Schema for audit log statistics"""
    total_logs: int
    successful_actions: int
    failed_actions: int
    period_days: int
    top_users: List[Dict[str, Any]]
    top_actions: List[Dict[str, Any]]
    failure_rate: float = 0.0  # Percentage of failed actions
    severity_counts: Dict[str, int] = {}  # Count of logs per severity level


class AuditExportRequest(BaseModel):
    """Schema for audit log export requests"""
    format: str = Field(default="csv", pattern="^(csv|json)$")
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    action: Optional[str] = None
    entity_type: Optional[str] = None
    status: Optional[str] = None
    user_id: Optional[int] = None
    severity: Optional[str] = None


class IntegrityReport(BaseModel):
    """Schema for integrity verification report"""
    total_entries: int
    verified_entries: int
    tampered_entries: int
    tampered_log_ids: List[int] = []
    chain_broken: bool
    first_entry_verified: bool
    last_entry: Optional[int] = None
    report: str


class RetentionPolicy(BaseModel):
    """Schema for retention policy actions"""
    retention_days: int = Field(default=365, ge=1, le=3650)
    dry_run: bool = True  # Preview only, no actual deletion
