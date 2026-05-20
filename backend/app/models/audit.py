"""
Audit log model for tracking all critical operations.

Implements industry-standard audit logging:
- Append-only / immutable (SOC 2 CC6.1, PCI-DSS 10.5)
- Hash chain integrity for tamper detection (ISO 27001 A.12.4.2)
- Severity classification for event prioritization
- Before/after value tracking for changes
- Timezone-aware timestamps (PCI-DSS 10.3, ISO 27001 A.12.4.4)
"""

import hashlib
import json
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class AuditLog(Base):
    """
    Audit log model for tracking user actions (append-only, immutable, integrity-verified).
    
    Implements a hash chain: each entry stores the hash of the previous entry,
    forming a chain that allows tamper detection. The hash covers all content
    fields plus the previous hash to prevent undetected modification.
    """
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for system actions
    username = Column(String, nullable=True)  # Store username for reference
    action = Column(String, nullable=False, index=True)  # CREATE, UPDATE, DELETE, LOGIN, LOGOUT, etc.
    entity_type = Column(String, nullable=False)  # User, Sale, Inventory, Employee, etc.
    entity_id = Column(Integer, nullable=True)  # ID of affected entity
    details = Column(JSON, nullable=True)  # Additional details about the action
    ip_address = Column(String, nullable=True)  # Client IP address
    user_agent = Column(String, nullable=True)  # Client user agent
    status = Column(String, default="success")  # success, failure
    error_message = Column(Text, nullable=True)  # Error details if failed
    correlation_id = Column(String, nullable=True, index=True)  # Request/session correlation ID for grouping related events
    
    # Industry-standard audit fields
    severity = Column(String, default="INFO", index=True)  # INFO, WARNING, CRITICAL (ISO 27001 A.12.4.1)
    old_values = Column(JSON, nullable=True)  # Values before change (for UPDATE tracking)
    new_values = Column(JSON, nullable=True)  # Values after change (for UPDATE tracking)
    
    # Hash chain integrity (PCI-DSS 10.5, SOC 2)
    hash = Column(String, nullable=True, unique=True)  # SHA-256 hash of this entry (nullable for pending compute)
    previous_hash = Column(String, nullable=True, index=True)  # Hash of the previous entry (None for first entry)
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    
    # Timezone-aware timestamp
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    
    # Relationships
    organization = relationship("Organization", backref="audit_logs")
    
    # Composite indexes for common query patterns
    __table_args__ = (
        Index("ix_audit_logs_org_user_created", "organization_id", "user_id", "created_at"),
        Index("ix_audit_logs_user_created", "user_id", "created_at"),
        Index("ix_audit_logs_action_entity", "action", "entity_type"),
        Index("ix_audit_logs_created_status", "created_at", "status"),
        Index("ix_audit_logs_severity_created", "severity", "created_at"),
        Index("ix_audit_logs_previous_hash", "previous_hash"),
    )
    
    def compute_hash(self) -> str:
        """
        Compute SHA-256 hash of this audit entry's content for integrity verification.
        
        The hash covers all meaningful fields plus the previous_hash link.
        This ensures any tampering with the content will be detected.
        """
        content = {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.username,
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "details": self.details,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "status": self.status,
            "error_message": self.error_message,
            "correlation_id": self.correlation_id,
            "severity": self.severity,
            "old_values": self.old_values,
            "new_values": self.new_values,
            "previous_hash": self.previous_hash,
            "created_at": str(self.created_at)
        }
        # Sort keys for deterministic hashing
        raw = json.dumps(content, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def __repr__(self):
        return f"<AuditLog #{self.id} {self.action} on {self.entity_type} by {self.username}>"

    def to_dict(self):
        """Convert model to dictionary for serialization."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.username,
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "details": self.details,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "status": self.status,
            "error_message": self.error_message,
            "correlation_id": self.correlation_id,
            "severity": self.severity,
            "old_values": self.old_values,
            "new_values": self.new_values,
            "hash": self.hash,
            "previous_hash": self.previous_hash,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
