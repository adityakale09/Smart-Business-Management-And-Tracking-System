"""
Sales query/read service helpers.

This module centralizes read/reporting business logic for sales,
keeping routers focused on request/response orchestration.
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.inventory import Inventory
from app.models.sales import Sale


def list_sales(
    db: Session,
    current_user: dict,
    page: int,
    page_size: int,
    search: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> dict:
    """Return paginated sales with role-aware filtering."""
    query = db.query(Sale)

    # Employees can only see their own sales. Admins/managers see all.
    role = current_user.get("role", "employee")
    # Normalize role string
    if hasattr(role, 'value'):
        role = role.value
    role = str(role).strip().lower()
    print(f"[DEBUG] list_sales: user_id={current_user.get('user_id')}, role={role}")
    if role == "employee" or role == "vendor":
        query = query.filter(Sale.user_id == int(current_user["user_id"]))
    # Admins and managers see all sales (no filter)

    if start_date:
        query = query.filter(Sale.created_at >= start_date)
    if end_date:
        query = query.filter(Sale.created_at <= end_date)

    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Sale.customer_name.ilike(search_term),
                Sale.transaction_id.ilike(search_term),
            )
        )

    total = query.count()
    items = (
        query.order_by(Sale.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def get_sales_summary(db: Session, days: int) -> dict:
    """Return aggregate summary for a date range."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    base_query = db.query(Sale).filter(
        Sale.created_at >= start_date,
        Sale.created_at <= end_date,
    )

    total_sales = base_query.count()
    total_revenue = (
        db.query(func.sum(Sale.total_amount))
        .filter(Sale.created_at >= start_date, Sale.created_at <= end_date)
        .scalar()
        or 0
    )
    average_sale = (
        db.query(func.avg(Sale.total_amount))
        .filter(Sale.created_at >= start_date, Sale.created_at <= end_date)
        .scalar()
        or 0
    )

    return {
        "period_days": days,
        "total_sales": total_sales,
        "total_revenue": float(total_revenue),
        "average_sale": float(average_sale),
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
    }


def get_sale_by_id_for_user(db: Session, sale_id: int, current_user: dict) -> Sale:
    """Return a sale if visible to current user, otherwise raise HTTP error."""
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found")

    if current_user["role"] == "employee" and sale.user_id != int(current_user["user_id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return sale


def get_invoice_data(db: Session, sale_id: int, current_user: dict) -> Tuple[dict, dict, str]:
    """Return data payload needed to generate an invoice PDF."""
    sale = get_sale_by_id_for_user(db, sale_id, current_user)

    product = db.query(Inventory).filter(Inventory.id == sale.product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product information not found",
        )

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

    return sale_data, product_info, sale.transaction_id


def get_sales_for_export(
    db: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> list[Sale]:
    """Return sales list for export endpoints."""
    query = db.query(Sale)

    if start_date:
        query = query.filter(Sale.created_at >= start_date)
    if end_date:
        query = query.filter(Sale.created_at <= end_date)

    return query.order_by(Sale.created_at.desc()).all()
