"""
Sales model
"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Sale(Base):
    """Sales transaction model"""
    __tablename__ = "sales"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String, unique=True, index=True, nullable=False)
    customer_name = Column(String, nullable=False)
    product_id = Column(Integer, ForeignKey("inventory.id"))
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    payment_method = Column(String)  # cash, card, online
    status = Column(String, default="completed")  # completed, pending, cancelled
    user_id = Column(Integer, ForeignKey("users.id"))
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="sales")
    product = relationship("Inventory", back_populates="sales")
    organization = relationship("Organization", backref="sales")
    
    # Composite indexes for common query patterns
    __table_args__ = (
        Index("ix_sales_org_user_created", "organization_id", "user_id", "created_at"),
        Index("ix_sales_org_status_created", "organization_id", "status", "created_at"),
        Index("ix_sales_user_created", "user_id", "created_at"),
        Index("ix_sales_status_created", "status", "created_at"),
        Index("ix_sales_product_created", "product_id", "created_at"),
        Index("ix_sales_payment_date", "payment_method", "created_at"),
    )








