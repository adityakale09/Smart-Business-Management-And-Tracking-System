"""
Audit log model for tracking all critical operations
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class AuditLog(Base):
    """Audit log model for tracking user actions"""
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
    created_at = Column(DateTime, server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<AuditLog {self.action} on {self.entity_type} by {self.username}>"
