"""
Inventory management routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from io import BytesIO
from datetime import datetime

from app.database import get_db
from app.core.security import get_current_user
from app.core.permissions import require_min_role
from app.schemas.inventory import InventoryCreate, InventoryUpdate, InventoryResponse
from app.models.inventory import Inventory, InventoryUpdate as InventoryUpdateModel
from app.utils.export_utils import export_to_csv, export_to_excel, prepare_inventory_export_data
from app.services.inventory_service import (
    create_inventory_with_audit,
    update_inventory_with_audit
)
from app.utils.audit_logger import log_delete

router = APIRouter()


def update_item_status(item: Inventory) -> None:
    """Helper function to automatically update item status based on quantity"""
    if item.quantity <= 0:
        item.status = "out_of_stock"
    elif item.quantity <= item.reorder_level:
        item.status = "low_stock"
    else:
        item.status = "active"


@router.post("/", response_model=InventoryResponse, status_code=status.HTTP_201_CREATED)
async def create_inventory_item(
    item_data: InventoryCreate,
    request: Request,
    current_user: dict = Depends(require_min_role("manager")),
    db: Session = Depends(get_db)
):
    """Create a new inventory item"""
    return create_inventory_with_audit(db, item_data, current_user, request)


from fastapi import Query
from sqlalchemy import or_

@router.get("/", response_model=dict)
async def get_inventory(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    low_stock: bool = Query(False),
    current_user: dict = Depends(require_min_role("employee")),
    db: Session = Depends(get_db)
):
    """Get all inventory items with pagination and search"""
    query = db.query(Inventory)
    if category:
        query = query.filter(Inventory.category == category)
    if low_stock:
        query = query.filter(Inventory.quantity <= Inventory.reorder_level)
    if search:
        search_term = f"%{search.lower()}%"
        query = query.filter(
            or_(
                Inventory.name.ilike(search_term),
                Inventory.sku.ilike(search_term)
            )
        )
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    serialized_items = [
        InventoryResponse.model_validate(item).model_dump(mode="json")
        for item in items
    ]
    return {
        "items": serialized_items,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/export/csv")
async def export_inventory_csv(
    category: Optional[str] = Query(None),
    low_stock: bool = Query(False),
    current_user: dict = Depends(require_min_role("manager")),
    db: Session = Depends(get_db)
):
    """Export inventory data to CSV"""
    query = db.query(Inventory)
    
    if category:
        query = query.filter(Inventory.category == category)
    
    if low_stock:
        query = query.filter(Inventory.quantity <= Inventory.reorder_level)
    
    items = query.all()
    
    # Prepare data
    data, headers = prepare_inventory_export_data(items)
    csv_content = export_to_csv(data, headers)
    
    # Return as downloadable file
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=inventory_export_{datetime.now().strftime('%Y%m%d')}.csv"
        }
    )


@router.get("/export/excel")
async def export_inventory_excel(
    category: Optional[str] = Query(None),
    low_stock: bool = Query(False),
    current_user: dict = Depends(require_min_role("manager")),
    db: Session = Depends(get_db)
):
    """Export inventory data to Excel"""
    query = db.query(Inventory)
    
    if category:
        query = query.filter(Inventory.category == category)
    
    if low_stock:
        query = query.filter(Inventory.quantity <= Inventory.reorder_level)
    
    items = query.all()
    
    # Prepare data
    data, headers = prepare_inventory_export_data(items)
    excel_content = export_to_excel(data, headers, "Inventory Report")
    
    # Return as downloadable file
    return StreamingResponse(
        BytesIO(excel_content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=inventory_export_{datetime.now().strftime('%Y%m%d')}.xlsx"
        }
    )


@router.get("/{item_id}", response_model=InventoryResponse)
async def get_inventory_item(
    item_id: int,
    current_user: dict = Depends(require_min_role("employee")),
    db: Session = Depends(get_db)
):
    """Get a specific inventory item"""
    item = db.query(Inventory).filter(Inventory.id == item_id).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found"
        )
    
    return item


@router.put("/{item_id}", response_model=InventoryResponse)
async def update_inventory_item(
    item_id: int,
    item_data: InventoryUpdate,
    request: Request,
    current_user: dict = Depends(require_min_role("manager")),
    db: Session = Depends(get_db)
):
    """Update an inventory item"""
    return update_inventory_with_audit(db, item_id, item_data, current_user, request)


@router.post("/{item_id}/restock")
async def restock_inventory(
    item_id: int,
    request: Request,
    quantity: int = Query(..., gt=0),
    notes: Optional[str] = Query(None),
    current_user: dict = Depends(require_min_role("manager")),
    db: Session = Depends(get_db)
):
    """Restock inventory item"""
    item = db.query(Inventory).filter(Inventory.id == item_id).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found"
        )
    
    previous_quantity = item.quantity
    item.quantity += quantity
    
    # Auto-update status based on quantity
    update_item_status(item)
    
    # Create update record
    update_record = InventoryUpdateModel(
        inventory_id=item_id,
        user_id=int(current_user["user_id"]),
        update_type="restock",
        quantity_change=quantity,
        previous_quantity=previous_quantity,
        new_quantity=item.quantity,
        notes=notes
    )
    
    db.add(update_record)
    db.commit()
    db.refresh(item)

    log_update(
        db,
        "Inventory",
        item.id,
        user_id=int(current_user["user_id"]),
        username=current_user.get("username", "system"),
        details={
            "action": "restock",
            "quantity_change": quantity,
            "previous_quantity": previous_quantity,
            "new_quantity": item.quantity,
            "notes": notes,
        },
        request=request,
    )
    
    return item


@router.delete("/{item_id}")
async def delete_inventory(
    item_id: int,
    request: Request,
    current_user: dict = Depends(require_min_role("manager")),
    db: Session = Depends(get_db)
):
    """Delete inventory item"""
    item = db.query(Inventory).filter(Inventory.id == item_id).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found"
        )

    item_details = {
        "sku": item.sku,
        "name": item.name,
        "category": item.category,
        "quantity": item.quantity,
    }
    
    # Delete related inventory updates first
    db.query(InventoryUpdateModel).filter(InventoryUpdateModel.inventory_id == item_id).delete()
    
    db.delete(item)
    db.commit()

    try:
        log_delete(
            db,
            "Inventory",
            item_id,
            user_id=int(current_user["user_id"]),
            username=current_user.get("username", "system"),
            details=item_details,
            request=request,
        )
    except Exception:
        # Inventory deletion is already committed; audit failure should not fail the API response.
        pass

    return {"message": "Inventory item deleted successfully"}









