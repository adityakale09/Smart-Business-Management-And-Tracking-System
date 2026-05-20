"""
Receipt models for storing processed receipts
"""

from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class ReceiptType(str, enum.Enum):
    """Receipt type enumeration"""
    PURCHASE = "purchase"
    SALE = "sale"


class ReceiptCategory(str, enum.Enum):
    """Optional receipt categorization"""
    GROCERY = "grocery"
    ELECTRONICS = "electronics"
    OFFICE_SUPPLIES = "office_supplies"
    RESTAURANT = "restaurant"
    TRANSPORTATION = "transportation"
    UTILITIES = "utilities"
    MEDICAL = "medical"
    OTHER = "other"


class Receipt(Base):
    """Receipt model for storing processed receipts"""
    __tablename__ = "receipts"
    
    id = Column(Integer, primary_key=True, index=True)
    receipt_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    receipt_type = Column(SQLEnum(ReceiptType), nullable=False)
    source = Column(String, nullable=True)  # Store name or source
    total_amount = Column(Float, nullable=False, default=0.0)
    category = Column(String, nullable=True)  # Receipt categorization (grocery, electronics, etc.)
    notes = Column(Text, nullable=True)
    processed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    image_path = Column(String, nullable=True)
    image_data = Column(String, nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    items = relationship("ReceiptItem", back_populates="receipt", cascade="all, delete-orphan")
    user = relationship("User", backref="processed_receipts")
    organization = relationship("Organization", backref="receipts")
    
    # Composite indexes for common query patterns
    __table_args__ = (
        Index("ix_receipts_org_type_created", "organization_id", "receipt_type", "created_at"),
        Index("ix_receipts_org_category_created", "organization_id", "category", "created_at"),
        Index("ix_receipts_type_created", "receipt_type", "created_at"),
        Index("ix_receipts_category_created", "category", "created_at"),
        Index("ix_receipts_processed_by", "processed_by", "created_at"),
    )


class ReceiptItem(Base):
    """Receipt item model for storing individual items from receipts"""
    __tablename__ = "receipt_items"
    
    id = Column(Integer, primary_key=True, index=True)
    receipt_id = Column(Integer, ForeignKey("receipts.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    product_name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    price_per_unit = Column(Float, nullable=False)
    
    @property
    def total_price(self) -> float:
        """Compute total price from quantity and unit price"""
        return self.quantity * self.price_per_unit
    
    # Relationships
    receipt = relationship("Receipt", back_populates="items")
    organization = relationship("Organization", backref="receipt_items")

