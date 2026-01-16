"""
Inventory model
"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Inventory(Base):
    """Inventory item model"""
    __tablename__ = "inventory"
    
    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    category = Column(String)
    quantity = Column(Integer, default=0, nullable=False)
    reorder_level = Column(Integer, default=10)
    unit_price = Column(Float, nullable=False)
    supplier = Column(String)
    location = Column(String)
    status = Column(String, default="active")  # active, discontinued, out_of_stock
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    sales = relationship("Sale", back_populates="product")
    updates = relationship("InventoryUpdate", back_populates="inventory")


class InventoryUpdate(Base):
    """Inventory update history model"""
    __tablename__ = "inventory_updates"
    
    id = Column(Integer, primary_key=True, index=True)
    inventory_id = Column(Integer, ForeignKey("inventory.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    update_type = Column(String)  # restock, sale, adjustment, return
    quantity_change = Column(Integer, nullable=False)
    previous_quantity = Column(Integer)
    new_quantity = Column(Integer)
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    inventory = relationship("Inventory", back_populates="updates")
    user = relationship("User", back_populates="inventory_updates")








