"""
Receipt processing routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import base64

from app.database import get_db
from app.core.security import get_current_user
from app.core.permissions import require_min_role
from app.schemas.receipt import ReceiptResponse, ReceiptProcessingResult, ReceiptListResponse
from app.models.receipt import Receipt, ReceiptItem
from app.receipt_processor.ocr_service import ocr_service
from app.receipt_processor.parser import receipt_parser
from app.receipt_processor.update_inventory import process_receipt_data

router = APIRouter()


@router.post("/upload-receipt", response_model=ReceiptProcessingResult)
async def upload_receipt(
    file: UploadFile = File(...),
    receipt_type: Optional[str] = Form(None),
    current_user: dict = Depends(require_min_role("employee")),
    db: Session = Depends(get_db)
):
    """
    Upload and process a receipt (image or PDF)
    
    Supported formats: JPG, PNG, PDF
    """
    try:
        # Validate file type
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.pdf'}
        file_ext = '.' + (file.filename.split('.')[-1] if '.' in file.filename else '')
        
        if file_ext.lower() not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Read file content
        file_content = await file.read()
        
        if len(file_content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file uploaded"
            )
        
        # Extract text using OCR
        try:
            extracted_text = ocr_service.extract_text_from_file(file_content, file.filename)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"OCR extraction failed: {str(e)}"
            )
        
        if not extracted_text or len(extracted_text.strip()) < 10:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Could not extract sufficient text from receipt. Please ensure the image is clear and readable."
            )
        
        # Parse receipt text
        try:
            parsed_data = receipt_parser.parse_receipt(extracted_text)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Receipt parsing failed: {str(e)}"
            )
        
        # Override receipt type if provided
        if receipt_type and receipt_type.lower() in ['purchase', 'sale']:
            parsed_data['receipt_type'] = receipt_type.lower()
        
        # Validate parsed data
        if not parsed_data.get('items') or len(parsed_data['items']) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No items found in receipt. Please check the receipt format."
            )
        
        # Get user ID
        user_id = int(current_user.get('user_id'))
        
        # Convert image to base64 for storage
        image_base64 = base64.b64encode(file_content).decode('utf-8')
        parsed_data['image_data'] = f"data:image/{file_ext[1:]};base64,{image_base64}"
        
        # Process receipt and update inventory
        result = process_receipt_data(db, parsed_data, user_id)
        
        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get('message', 'Failed to process receipt')
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Receipt processing failed: {str(e)}"
        )


@router.get("/receipts", response_model=ReceiptListResponse)
async def get_receipts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    receipt_type: Optional[str] = Query(None),
    current_user: dict = Depends(require_min_role("employee")),
    db: Session = Depends(get_db)
):
    """Get list of all processed receipts"""
    from sqlalchemy.orm import joinedload
    
    query = db.query(Receipt).options(joinedload(Receipt.items))
    
    # Filter by receipt type if provided
    if receipt_type and receipt_type.lower() in ['purchase', 'sale']:
        from app.models.receipt import ReceiptType
        query = query.filter(Receipt.receipt_type == ReceiptType(receipt_type.lower()))
    
    # Get total count
    total = query.count()
    
    # Get receipts with items
    receipts = query.order_by(Receipt.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        'receipts': receipts,
        'total': total
    }


@router.get("/receipts/{receipt_id}", response_model=ReceiptResponse)
async def get_receipt(
    receipt_id: int,
    current_user: dict = Depends(require_min_role("employee")),
    db: Session = Depends(get_db)
):
    """Get a specific receipt by ID"""
    from sqlalchemy.orm import joinedload
    
    receipt = db.query(Receipt).options(joinedload(Receipt.items)).filter(Receipt.id == receipt_id).first()
    
    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Receipt with ID {receipt_id} not found"
        )
    
    return receipt


@router.put("/receipts/{receipt_id}")
async def update_receipt(
    receipt_id: int,
    source: Optional[str] = Form(None),
    receipt_type: Optional[str] = Form(None),
    current_user: dict = Depends(require_min_role("manager")),
    db: Session = Depends(get_db)
):
    """Update receipt details (managers and admins only)"""
    receipt = db.query(Receipt).filter(Receipt.id == receipt_id).first()
    
    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Receipt with ID {receipt_id} not found"
        )
    
    # Update fields if provided
    if source:
        receipt.source = source
    if receipt_type and receipt_type.lower() in ['purchase', 'sale']:
        receipt.receipt_type = receipt_type.lower()
    
    db.commit()
    db.refresh(receipt)
    
    return {
        "message": "Receipt updated successfully",
        "receipt": receipt
    }


@router.delete("/receipts/{receipt_id}")
async def delete_receipt(
    receipt_id: int,
    current_user: dict = Depends(require_min_role("manager")),
    db: Session = Depends(get_db)
):
    """Delete a receipt (managers and admins only)"""
    receipt = db.query(Receipt).filter(Receipt.id == receipt_id).first()
    
    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Receipt with ID {receipt_id} not found"
        )
    
    # Store info before deletion
    receipt_info = {
        "id": receipt.id,
        "source": receipt.source,
        "total_amount": receipt.total_amount
    }
    
    # Delete associated items first (cascade should handle this, but being explicit)
    db.query(ReceiptItem).filter(ReceiptItem.receipt_id == receipt_id).delete()
    
    # Delete the receipt
    db.delete(receipt)
    db.commit()
    
    return {
        "message": "Receipt deleted successfully",
        "receipt_id": receipt_info["id"],
        "source": receipt_info["source"]
    }


@router.get("/inventory", response_model=List[dict])
async def get_inventory(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    current_user: dict = Depends(require_min_role("employee")),
    db: Session = Depends(get_db)
):
    """Get inventory list with updated quantities"""
    from app.models.inventory import Inventory
    
    query = db.query(Inventory)
    
    # Filter by search term if provided
    if search:
        query = query.filter(
            Inventory.name.ilike(f'%{search}%') | 
            Inventory.sku.ilike(f'%{search}%')
        )
    
    # Get inventory items
    inventory_items = query.order_by(Inventory.updated_at.desc()).offset(skip).limit(limit).all()
    
    # Format response
    result = []
    for item in inventory_items:
        result.append({
            'id': item.id,
            'sku': item.sku,
            'name': item.name,
            'quantity': item.quantity,
            'unit_price': item.unit_price,
            'category': item.category,
            'status': item.status,
            'reorder_level': item.reorder_level,
            'last_updated': item.updated_at.isoformat() if item.updated_at else None,
            'recently_updated': (
                item.updated_at and 
                (datetime.now() - item.updated_at).total_seconds() < 3600
            ) if item.updated_at else False
        })
    
    return result

