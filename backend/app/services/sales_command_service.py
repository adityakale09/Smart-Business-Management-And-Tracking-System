"""
Sales command/write service helpers.

This module centralizes sales write operations and related side effects
(such as audit logging), keeping routers minimal.
"""

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.services.sales_service import create_sale_transaction, delete_sale_transaction
from app.utils.audit_logger import log_create, log_delete


def create_sale_with_audit(db: Session, sale_data, current_user: dict, request: Request):
    """Create sale transaction and write audit entry."""
    try:
        new_sale = create_sale_transaction(db, sale_data, current_user)

        log_create(
            db,
            "Sale",
            new_sale.id,
            user_id=int(current_user["user_id"]),
            username=current_user.get("username", "system"),
            details={
                "transaction_id": new_sale.transaction_id,
                "product_id": new_sale.product_id,
                "quantity": new_sale.quantity,
                "total_amount": float(new_sale.total_amount),
            },
            request=request,
        )

        return new_sale
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create sale: {str(exc)}",
        )


def delete_sale_with_audit(db: Session, sale_id: int, current_user: dict, request: Request) -> dict:
    """Delete sale transaction and write audit entry."""
    deleted_sale = delete_sale_transaction(db, sale_id)

    log_delete(
        db,
        "Sale",
        sale_id,
        user_id=int(current_user["user_id"]),
        username=current_user.get("username", "system"),
        details={
            "transaction_id": deleted_sale["transaction_id"],
            "product_id": deleted_sale["product_id"],
            "quantity": deleted_sale["quantity"],
            "total_amount": deleted_sale["total_amount"],
        },
        request=request,
    )

    return deleted_sale
