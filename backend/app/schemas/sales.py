"""
Sales schemas
"""

from pydantic import BaseModel, field_validator, Field
from typing import Optional
from datetime import datetime


class SaleCreate(BaseModel):
    """Create sale schema"""
    customer_name: str = Field(..., min_length=1, max_length=200)
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)
    unit_price: float = Field(..., gt=0)
    payment_method: str = Field(default="cash", max_length=50)
    notes: Optional[str] = Field(None, max_length=500)
    
    @field_validator('customer_name')
    @classmethod
    def validate_customer_name(cls, v: str) -> str:
        """Validate customer name is not empty or whitespace"""
        if v.strip() == '':
            raise ValueError('Customer name cannot be empty or whitespace')
        return v.strip()
    
    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v: int) -> int:
        """Validate quantity is reasonable"""
        if v <= 0:
            raise ValueError('Quantity must be greater than 0')
        if v > 10000:
            raise ValueError('Quantity seems too high (max: 10,000)')
        return v
    
    @field_validator('unit_price')
    @classmethod
    def validate_price(cls, v: float) -> float:
        """Validate price is positive and reasonable"""
        if v <= 0:
            raise ValueError('Unit price must be greater than 0')
        if v > 1000000:
            raise ValueError('Unit price seems too high (max: 1,000,000)')
        return round(v, 2)
    
    @field_validator('payment_method')
    @classmethod
    def validate_payment_method(cls, v: str) -> str:
        """Validate payment method is one of allowed values"""
        allowed = ['cash', 'card', 'upi', 'bank_transfer', 'credit']
        if v.lower() not in allowed:
            raise ValueError(f'Payment method must be one of: {", ".join(allowed)}')
        return v.lower()


class SaleUpdate(BaseModel):
    """Update sale schema"""
    customer_name: Optional[str] = Field(None, min_length=1, max_length=200)
    quantity: Optional[int] = Field(None, gt=0)
    unit_price: Optional[float] = Field(None, gt=0)
    payment_method: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=500)
    
    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v: Optional[int]) -> Optional[int]:
        """Validate quantity is reasonable"""
        if v is not None:
            if v <= 0:
                raise ValueError('Quantity must be greater than 0')
            if v > 10000:
                raise ValueError('Quantity seems too high (max: 10,000)')
        return v
    
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


class SaleResponse(BaseModel):
    """Sale response schema"""
    id: int
    transaction_id: str
    customer_name: str
    product_id: Optional[int] = None
    quantity: int
    unit_price: float
    total_amount: float
    payment_method: str
    status: str
    user_id: int
    notes: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True








