"""
Receipt models for storing processed receipts
"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class ReceiptType(str, enum.Enum):
    """Receipt type enumeration"""
    PURCHASE = "purchase"
    SALE = "sale"


class Receipt(Base):
    """Receipt model for storing processed receipts"""
    __tablename__ = "receipts"
    
    id = Column(Integer, primary_key=True, index=True)
    receipt_date = Column(DateTime, nullable=False, server_default=func.now())
    receipt_type = Column(SQLEnum(ReceiptType), nullable=False)
    source = Column(String, nullable=True)  # Store name or source
    total_amount = Column(Float, nullable=False, default=0.0)
    processed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    image_path = Column(String, nullable=True)  # Path to stored receipt image
    image_data = Column(String, nullable=True)  # Base64 encoded image data
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    items = relationship("ReceiptItem", back_populates="receipt", cascade="all, delete-orphan")
    user = relationship("User", backref="processed_receipts")


class ReceiptItem(Base):
    """Receipt item model for storing individual items from receipts"""
    __tablename__ = "receipt_items"
    
    id = Column(Integer, primary_key=True, index=True)
    receipt_id = Column(Integer, ForeignKey("receipts.id"), nullable=False)
    product_name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    price_per_unit = Column(Float, nullable=False)
    
    # Relationships
    receipt = relationship("Receipt", back_populates="items")

