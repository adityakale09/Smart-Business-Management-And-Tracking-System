"""
Sales domain service helpers.

This module keeps business logic out of API routers.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import uuid

from app.models.sales import Sale
from app.models.inventory import Inventory


def create_sale_transaction(db: Session, sale_data, current_user: dict) -> Sale:
    """Create a sale and update related inventory atomically."""
    org_id = current_user.get("organization_id")
    query = db.query(Inventory).filter(Inventory.id == sale_data.product_id)
    if org_id is not None:
        query = query.filter(Inventory.organization_id == int(org_id))
    product = query.first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {sale_data.product_id} not found",
        )

    if product.quantity < sale_data.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient inventory. Available: {product.quantity}, Requested: {sale_data.quantity}",
        )

    total_amount = sale_data.quantity * sale_data.unit_price
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
        notes=sale_data.notes,
        organization_id=current_user.get("organization_id")
    )

    product.quantity -= sale_data.quantity
    if product.quantity <= product.reorder_level:
        product.status = "low_stock"
    elif product.quantity == 0:
        product.status = "out_of_stock"

    db.add(new_sale)
    db.commit()
    db.refresh(new_sale)
    return new_sale


def delete_sale_transaction(db: Session, sale_id: int, current_user: dict) -> dict:
    """Delete a sale and return metadata for audit/response."""
    org_id = current_user.get("organization_id")
    query = db.query(Sale).filter(Sale.id == sale_id)
    if org_id is not None:
        query = query.filter(Sale.organization_id == int(org_id))
    sale = query.first()
    if not sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sale not found",
        )

    deleted_sale = {
        "sale_id": sale.id,
        "transaction_id": sale.transaction_id,
        "total_amount": float(sale.total_amount),
        "quantity": sale.quantity,
        "product_id": sale.product_id,
    }

    db.delete(sale)
    db.commit()
    return deleted_sale
