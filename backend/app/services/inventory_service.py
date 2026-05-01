"""
Inventory service with audit logging.

This module centralizes inventory operations and related side effects
(such as audit logging), keeping routers minimal.
"""

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.models.inventory import Inventory
from app.utils.audit_logger import log_create, log_update, log_exception


def update_item_status(item: Inventory) -> None:
    """Helper function to automatically update item status based on quantity"""
    if item.quantity <= 0:
        item.status = "out_of_stock"
    elif item.quantity <= item.reorder_level:
        item.status = "low_stock"
    else:
        item.status = "active"


def create_inventory_with_audit(db: Session, item_data, current_user: dict, request: Request):
    """Create inventory item and write audit entry."""
    try:
        # Check if SKU already exists
        existing = db.query(Inventory).filter(Inventory.sku == item_data.sku).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SKU already exists"
            )
        
        new_item = Inventory(
            sku=item_data.sku,
            name=item_data.name,
            description=item_data.description,
            category=item_data.category,
            quantity=item_data.quantity,
            reorder_level=item_data.reorder_level,
            unit_price=item_data.unit_price,
            supplier=item_data.supplier,
            location=item_data.location
        )
        
        # Auto-update status based on quantity
        update_item_status(new_item)
        
        db.add(new_item)
        db.commit()
        db.refresh(new_item)

        log_create(
            db,
            "Inventory",
            new_item.id,
            user_id=int(current_user["user_id"]),
            username=current_user.get("username", "system"),
            details={
                "sku": new_item.sku,
                "name": new_item.name,
                "category": new_item.category,
                "quantity": new_item.quantity,
            },
            request=request,
        )
        
        return new_item
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        # Log the failure
        log_exception(
            db,
            "CREATE",
            "Inventory",
            user_id=int(current_user["user_id"]),
            username=current_user.get("username", "system"),
            request=request,
            exception=e,
            details={"sku": item_data.sku}
        )
        error_msg = str(e)
        if "connection" in error_msg.lower() or "database" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection error. Please check your database configuration."
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create inventory item: {error_msg}"
        )


def update_inventory_with_audit(db: Session, item_id: int, item_data, current_user: dict, request: Request):
    """Update inventory item and write audit entry."""
    try:
        item = db.query(Inventory).filter(Inventory.id == item_id).first()
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inventory item not found"
            )
        
        # Update fields
        update_data = item_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(item, field, value)
        
        # Auto-update status based on quantity
        update_item_status(item)
        
        db.commit()
        db.refresh(item)

        log_update(
            db,
            "Inventory",
            item.id,
            user_id=int(current_user["user_id"]),
            username=current_user.get("username", "system"),
            details={
                "updated_fields": list(update_data.keys()),
                "quantity": item.quantity,
                "status": item.status,
            },
            request=request,
        )
        
        return item
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update inventory item: {str(e)}"
        )
