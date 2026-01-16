"""
Inventory management routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
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
    current_user: dict = Depends(require_min_role("manager")),
    db: Session = Depends(get_db)
):
    """Create a new inventory item"""
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
        
        return new_item
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
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


@router.get("/", response_model=List[InventoryResponse])
async def get_inventory(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = Query(None),
    low_stock: bool = Query(False),
    current_user: dict = Depends(require_min_role("employee")),
    db: Session = Depends(get_db)
):
    """Get all inventory items"""
    query = db.query(Inventory)
    
    if category:
        query = query.filter(Inventory.category == category)
    
    if low_stock:
        query = query.filter(Inventory.quantity <= Inventory.reorder_level)
    
    items = query.offset(skip).limit(limit).all()
    return items


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
    current_user: dict = Depends(require_min_role("manager")),
    db: Session = Depends(get_db)
):
    """Update an inventory item"""
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
    
    return item


@router.post("/{item_id}/restock")
async def restock_inventory(
    item_id: int,
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
    
    return item


@router.delete("/{item_id}")
async def delete_inventory(
    item_id: int,
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
    
    # Delete related inventory updates first
    db.query(InventoryUpdateModel).filter(InventoryUpdateModel.inventory_id == item_id).delete()
    
    db.delete(item)
    db.commit()
    
    return {"message": "Inventory item deleted successfully"}


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









