"""
Sales management routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timedelta
import uuid
from io import BytesIO

from app.database import get_db
from app.core.security import get_current_user
from app.core.permissions import require_min_role
from app.schemas.sales import SaleCreate, SaleUpdate, SaleResponse
from app.models.sales import Sale
from app.models.inventory import Inventory
from app.utils.invoice_generator import generate_invoice_pdf
from app.utils.export_utils import export_to_csv, export_to_excel, prepare_sales_export_data

router = APIRouter()


@router.post("/", response_model=SaleResponse, status_code=status.HTTP_201_CREATED)
async def create_sale(
    sale_data: SaleCreate,
    current_user: dict = Depends(require_min_role("employee")),
    db: Session = Depends(get_db)
):
    """Create a new sale"""
    try:
        # Check if product exists and has sufficient quantity
        product = db.query(Inventory).filter(Inventory.id == sale_data.product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {sale_data.product_id} not found"
            )
        
        if product.quantity < sale_data.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient inventory. Available: {product.quantity}, Requested: {sale_data.quantity}"
            )
        
        # Calculate total amount
        total_amount = sale_data.quantity * sale_data.unit_price
        
        # Create sale
        transaction_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"
        new_sale = Sale(
            transaction_id=transaction_id,
            customer_name=sale_data.customer_name,
            product_id=sale_data.product_id,
            quantity=sale_data.quantity,
            unit_price=sale_data.unit_price,
            total_amount=total_amount,
            payment_method=sale_data.payment_method,
            user_id=int(current_user["user_id"]),
            notes=sale_data.notes
        )
        
        # Update inventory
        product.quantity -= sale_data.quantity
        if product.quantity <= product.reorder_level:
            product.status = "low_stock"
        elif product.quantity == 0:
            product.status = "out_of_stock"
        
        db.add(new_sale)
        db.commit()
        db.refresh(new_sale)
        
        return new_sale
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create sale: {str(e)}"
        )


@router.get("/", response_model=List[SaleResponse])
async def get_sales(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: dict = Depends(require_min_role("employee")),
    db: Session = Depends(get_db)
):
    """Get all sales with pagination and date filtering"""
    try:
        query = db.query(Sale)
        
        # Role-based filtering
        if current_user["role"] == "employee":
            query = query.filter(Sale.user_id == int(current_user["user_id"]))
        
        # Date filtering
        if start_date:
            query = query.filter(Sale.created_at >= start_date)
        if end_date:
            query = query.filter(Sale.created_at <= end_date)
        
        sales = query.order_by(Sale.created_at.desc()).offset(skip).limit(limit).all()
        return sales
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve sales: {str(e)}"
        )


@router.get("/{sale_id}", response_model=SaleResponse)
async def get_sale(
    sale_id: int,
    current_user: dict = Depends(require_min_role("employee")),
    db: Session = Depends(get_db)
):
    """Get a specific sale by ID"""
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    
    if not sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sale not found"
        )
    
    # Check permissions
    if current_user["role"] == "employee" and sale.user_id != int(current_user["user_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return sale


@router.delete("/{sale_id}")
async def delete_sale(
    sale_id: int,
    current_user: dict = Depends(require_min_role("manager")),
    db: Session = Depends(get_db)
):
    """Delete a sale transaction (managers and admins only)"""
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    
    if not sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sale not found"
        )
    
    # Store info before deletion for response
    transaction_id = sale.transaction_id
    
    # Delete the sale
    db.delete(sale)
    db.commit()
    
    return {
        "message": "Sale deleted successfully",
        "transaction_id": transaction_id
    }


@router.get("/stats/summary")
async def get_sales_summary(
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(require_min_role("manager")),
    db: Session = Depends(get_db)
):
    """Get sales summary statistics"""
    # Use timezone-aware datetime to avoid timezone issues
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    query = db.query(Sale).filter(
        Sale.created_at >= start_date,
        Sale.created_at <= end_date
    )
    
    total_sales = query.count()
    total_revenue = db.query(func.sum(Sale.total_amount)).filter(
        Sale.created_at >= start_date,
        Sale.created_at <= end_date
    ).scalar() or 0
    
    avg_sale = db.query(func.avg(Sale.total_amount)).filter(
        Sale.created_at >= start_date,
        Sale.created_at <= end_date
    ).scalar() or 0
    
    return {
        "period_days": days,
        "total_sales": total_sales,
        "total_revenue": float(total_revenue),
        "average_sale": float(avg_sale),
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat()
    }


@router.get("/{sale_id}/invoice")
async def download_invoice(
    sale_id: int,
    current_user: dict = Depends(require_min_role("employee")),
    db: Session = Depends(get_db)
):
    """Generate and download PDF invoice for a sale"""
    # Get sale
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    
    if not sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sale not found"
        )
    
    # Get product info
    product = db.query(Inventory).filter(Inventory.id == sale.product_id).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product information not found"
        )
    
    # Prepare sale data
    sale_data = {
        "transaction_id": sale.transaction_id,
        "customer_name": sale.customer_name,
        "quantity": sale.quantity,
        "unit_price": float(sale.unit_price),
        "total_amount": float(sale.total_amount),
        "payment_method": sale.payment_method,
        "notes": sale.notes,
        "created_at": sale.created_at,
    }
    
    product_info = {
        "name": product.name,
        "sku": product.sku,
        "category": product.category,
    }
    
    # Generate PDF
    pdf_content = generate_invoice_pdf(sale_data, product_info)
    
    # Return as downloadable file
    return StreamingResponse(
        BytesIO(pdf_content),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=invoice_{sale.transaction_id}.pdf"
        }
    )


@router.get("/export/csv")
async def export_sales_csv(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: dict = Depends(require_min_role("manager")),
    db: Session = Depends(get_db)
):
    """Export sales data to CSV"""
    query = db.query(Sale)
    
    # Date filtering
    if start_date:
        query = query.filter(Sale.created_at >= start_date)
    if end_date:
        query = query.filter(Sale.created_at <= end_date)
    
    sales = query.order_by(Sale.created_at.desc()).all()
    
    # Prepare data
    data, headers = prepare_sales_export_data(sales)
    csv_content = export_to_csv(data, headers)
    
    # Return as downloadable file
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=sales_export_{datetime.now().strftime('%Y%m%d')}.csv"
        }
    )


@router.get("/export/excel")
async def export_sales_excel(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: dict = Depends(require_min_role("manager")),
    db: Session = Depends(get_db)
):
    """Export sales data to Excel"""
    query = db.query(Sale)
    
    # Date filtering
    if start_date:
        query = query.filter(Sale.created_at >= start_date)
    if end_date:
        query = query.filter(Sale.created_at <= end_date)
    
    sales = query.order_by(Sale.created_at.desc()).all()
    
    # Prepare data
    data, headers = prepare_sales_export_data(sales)
    excel_content = export_to_excel(data, headers, "Sales Report")
    
    # Return as downloadable file
    return StreamingResponse(
        BytesIO(excel_content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=sales_export_{datetime.now().strftime('%Y%m%d')}.xlsx"
        }
    )










