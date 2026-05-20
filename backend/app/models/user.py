"""
User model for authentication and authorization
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class UserRole(str, enum.Enum):
    """User role enumeration"""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"
    VENDOR = "vendor"


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.EMPLOYEE, nullable=False)
    is_active = Column(Boolean, default=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    organization = relationship("Organization", backref="users")
    sales = relationship("Sale", back_populates="user")
    inventory_updates = relationship("InventoryUpdate", back_populates="user")
    
    # Composite indexes for common query patterns
    __table_args__ = (
        Index("ix_users_org_role", "organization_id", "role"),
        Index("ix_users_org_is_active", "organization_id", "is_active"),
        Index("ix_users_role_created", "role", "created_at"),
        Index("ix_users_is_active_created", "is_active", "created_at"),
    )








