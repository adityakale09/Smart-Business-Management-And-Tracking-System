"""
Receipt schemas for API requests and responses
"""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.models.receipt import ReceiptType


class ReceiptItemResponse(BaseModel):
    """Receipt item response schema"""
    id: int
    receipt_id: int
    product_name: str
    quantity: int
    price_per_unit: float
    
    class Config:
        from_attributes = True


class ReceiptResponse(BaseModel):
    """Receipt response schema"""
    id: int
    receipt_date: datetime
    receipt_type: str
    source: Optional[str]
    total_amount: float
    processed_by: Optional[int]
    created_at: datetime
    items: List[ReceiptItemResponse] = []
    
    class Config:
        from_attributes = True


class ReceiptProcessingResult(BaseModel):
    """Receipt processing result schema"""
    success: bool
    receipt_id: Optional[int] = None
    currency_code: Optional[str] = None
    items_processed: int = 0
    items: List[Dict[str, Any]] = []
    inventory_updates: List[Dict[str, Any]] = []
    message: str


class ReceiptListResponse(BaseModel):
    """Receipt list response schema"""
    receipts: List[ReceiptResponse]
    total: int

