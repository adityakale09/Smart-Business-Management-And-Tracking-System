"""
Sales management routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.core.permissions import require_min_role
from app.schemas.sales import SaleCreate, SaleUpdate, SaleResponse
from app.services.sales_command_service import create_sale_with_audit, delete_sale_with_audit
from app.services.sales_query_service import (
    list_sales,
    get_sales_summary as get_sales_summary_data,
    get_sale_by_id_for_user,
    get_invoice_data,
    get_sales_for_export,
)
from app.services.sales_export_service import (
    build_sales_csv_response,
    build_sales_excel_response,
)
from app.services.sales_invoice_service import build_sales_invoice_response

router = APIRouter()


@router.post("/", response_model=SaleResponse, status_code=status.HTTP_201_CREATED)
async def create_sale(
    sale_data: SaleCreate,
    request: Request,
    current_user: dict = Depends(require_min_role("employee")),
    db: Session = Depends(get_db)
):
    """Create a new sale"""
    return create_sale_with_audit(
        db=db,
        sale_data=sale_data,
        current_user=current_user,
        request=request,
    )


@router.get("/", response_model=dict)
async def get_sales(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: dict = Depends(require_min_role("employee")),
    db: Session = Depends(get_db)
):
    """Get all sales with pagination, search, and date filtering."""
    try:
        payload = list_sales(
            db=db,
            current_user=current_user,
            page=page,
            page_size=page_size,
            search=search,
            start_date=start_date,
            end_date=end_date,
        )
        payload["items"] = [
            SaleResponse.model_validate(item).model_dump(mode="json")
            for item in payload["items"]
        ]
        return payload
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve sales: {str(e)}"
        )


@router.get("/stats/summary")
async def get_sales_summary(
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(require_min_role("manager")),
    db: Session = Depends(get_db)
):
    """Get sales summary statistics."""
    return get_sales_summary_data(db=db, current_user=current_user, days=days)


@router.get("/{sale_id}/invoice")
async def download_invoice(
    sale_id: int,
    current_user: dict = Depends(require_min_role("employee")),
    db: Session = Depends(get_db)
):
    """Generate and download PDF invoice for a sale."""
    sale_data, product_info, transaction_id = get_invoice_data(
        db=db,
        sale_id=sale_id,
        current_user=current_user,
    )
    return build_sales_invoice_response(sale_data, product_info, transaction_id)


@router.get("/export/csv")
async def export_sales_csv(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: dict = Depends(require_min_role("manager")),
    db: Session = Depends(get_db)
):
    """Export sales data to CSV."""
    sales = get_sales_for_export(db=db, current_user=current_user, start_date=start_date, end_date=end_date)
    return build_sales_csv_response(sales)


@router.get("/export/excel")
async def export_sales_excel(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: dict = Depends(require_min_role("manager")),
    db: Session = Depends(get_db)
):
    """Export sales data to Excel."""
    sales = get_sales_for_export(db=db, current_user=current_user, start_date=start_date, end_date=end_date)
    return build_sales_excel_response(sales)


@router.get("/{sale_id}", response_model=SaleResponse)
async def get_sale(
    sale_id: int,
    current_user: dict = Depends(require_min_role("employee")),
    db: Session = Depends(get_db)
):
    """Get a specific sale by ID."""
    return get_sale_by_id_for_user(db=db, sale_id=sale_id, current_user=current_user)


@router.delete("/{sale_id}")
async def delete_sale(
    sale_id: int,
    request: Request,
    current_user: dict = Depends(require_min_role("manager")),
    db: Session = Depends(get_db)
):
    """Delete a sale transaction (managers and admins only)"""
    deleted_sale = delete_sale_with_audit(
        db=db,
        sale_id=sale_id,
        current_user=current_user,
        request=request,
    )

    return {
        "message": "Sale deleted successfully",
        "transaction_id": deleted_sale["transaction_id"],
    }










