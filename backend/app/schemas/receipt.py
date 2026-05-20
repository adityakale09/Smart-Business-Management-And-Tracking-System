"""
Receipt schemas for API requests and responses
"""

from pydantic import BaseModel, computed_field
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

    @computed_field
    @property
    def total_price(self) -> float:
        """Computed total price from quantity and unit price"""
        return self.quantity * self.price_per_unit

    class Config:
        from_attributes = True


class ReceiptResponse(BaseModel):
    """Receipt response schema with all fields including image data and categorization"""
    id: int
    receipt_date: datetime
    receipt_type: str
    source: Optional[str] = None
    total_amount: float
    category: Optional[str] = None
    notes: Optional[str] = None
    image_data: Optional[str] = None
    processed_by: Optional[int] = None
    created_at: datetime
    items: List[ReceiptItemResponse] = []

    class Config:
        from_attributes = True


class ReceiptUpdate(BaseModel):
    """Schema for updating receipt metadata"""
    source: Optional[str] = None
    receipt_type: Optional[str] = None
    category: Optional[str] = None
    notes: Optional[str] = None


class ReceiptProcessingResult(BaseModel):
    """Receipt processing result schema"""
    success: bool
    receipt_id: Optional[int] = None
    currency_code: Optional[str] = None
    items_processed: int = 0
    items: List[Dict[str, Any]] = []
    inventory_updates: List[Dict[str, Any]] = []
    message: str
    category: Optional[str] = None


class ReceiptListResponse(BaseModel):
    """Receipt list response schema"""
    receipts: List[ReceiptResponse]
    total: int


class CategoryBreakdown(BaseModel):
    """Spending breakdown by category"""
    category: str
    count: int
    total_amount: float
    percentage: float


class MonthlyTrend(BaseModel):
    """Monthly receipt trend data point"""
    year: int
    month: int
    count: int
    total_amount: float


class SourceAnalytics(BaseModel):
    """Top vendors/sources analytics"""
    source: str
    count: int
    total_amount: float


class ReceiptAnalyticsResponse(BaseModel):
    """Receipt analytics summary response"""
    total_receipts: int
    total_amount: float
    total_items: int
    average_per_receipt: float
    category_breakdown: List[CategoryBreakdown] = []
    monthly_trends: List[MonthlyTrend] = []
    top_sources: List[SourceAnalytics] = []
    type_breakdown: Dict[str, int] = {}

