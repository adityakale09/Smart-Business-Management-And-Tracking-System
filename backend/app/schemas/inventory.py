"""
Inventory schemas
"""

from pydantic import BaseModel, field_validator, Field
from typing import Optional
from datetime import datetime


class InventoryCreate(BaseModel):
    """Create inventory item schema"""
    sku: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    category: Optional[str] = Field(None, max_length=100)
    quantity: int = Field(default=0, ge=0)
    reorder_level: int = Field(default=10, ge=0)
    unit_price: float = Field(..., gt=0)
    supplier: Optional[str] = Field(None, max_length=200)
    location: Optional[str] = Field(None, max_length=200)
    
    @field_validator('sku')
    @classmethod
    def validate_sku(cls, v: str) -> str:
        """Validate SKU is not empty or whitespace"""
        if v.strip() == '':
            raise ValueError('SKU cannot be empty or whitespace')
        return v.strip().upper()
    
    @field_validator('unit_price')
    @classmethod
    def validate_price(cls, v: float) -> float:
        """Validate price is positive and reasonable"""
        if v <= 0:
            raise ValueError('Unit price must be greater than 0')
        if v > 1000000:
            raise ValueError('Unit price seems too high (max: 1,000,000)')
        return round(v, 2)


class InventoryUpdate(BaseModel):
    """Update inventory item schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    category: Optional[str] = Field(None, max_length=100)
    quantity: Optional[int] = Field(None, ge=0)
    reorder_level: Optional[int] = Field(None, ge=0)
    unit_price: Optional[float] = Field(None, gt=0)
    supplier: Optional[str] = Field(None, max_length=200)
    location: Optional[str] = Field(None, max_length=200)
    status: Optional[str] = None
    
    @field_validator('unit_price')
    @classmethod
    def validate_price(cls, v: Optional[float]) -> Optional[float]:
        """Validate price is positive and reasonable"""
        if v is not None:
            if v <= 0:
                raise ValueError('Unit price must be greater than 0')
            if v > 1000000:
                raise ValueError('Unit price seems too high (max: 1,000,000)')
            return round(v, 2)
        return v


class InventoryResponse(BaseModel):
    """Inventory response schema"""
    id: int
    sku: str
    name: str
    description: Optional[str]
    category: Optional[str]
    quantity: int
    reorder_level: int
    unit_price: float
    supplier: Optional[str]
    location: Optional[str]
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True








