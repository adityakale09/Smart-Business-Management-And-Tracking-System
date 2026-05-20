"""
Organization model for multi-tenant data isolation
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Index
from sqlalchemy.sql import func
from app.database import Base


class Organization(Base):
    """Organization model for tenant isolation"""
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    slug = Column(String, unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    settings = Column(JSON, nullable=True)  # Flexible settings per organization
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Composite indexes
    __table_args__ = (
        Index("ix_organizations_active_created", "is_active", "created_at"),
    )
