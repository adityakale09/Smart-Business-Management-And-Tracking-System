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


def _apply_currency_conversion(parsed_data: dict, source_currency: str, target_currency: str, exchange_rate: float):
    """Convert parsed receipt prices from source currency into target currency before persistence."""
    source = (source_currency or '').upper().strip()
    target = (target_currency or '').upper().strip()

    if not source or not target or source == target:
        return

    if exchange_rate <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid exchange rate provided for receipt conversion."
        )

    items = parsed_data.get('items', []) or []
    for item in items:
        unit_price = float(item.get('unit_price', 0.0) or 0.0)
        total_price = float(item.get('total_price', 0.0) or 0.0)
        item['unit_price'] = round(unit_price * exchange_rate, 2)
        item['total_price'] = round(total_price * exchange_rate, 2)

    total_amount = float(parsed_data.get('total_amount', 0.0) or 0.0)
    parsed_data['total_amount'] = round(total_amount * exchange_rate, 2)
    parsed_data['currency_code'] = target


def _validate_and_parse_receipt(file: UploadFile, file_content: bytes, require_items: bool = True):
    """Common validation and OCR+parsing pipeline used by preview and upload endpoints."""
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.pdf'}
    file_ext = '.' + (file.filename.split('.')[-1] if '.' in file.filename else '')

    if file_ext.lower() not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )

    if len(file_content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file uploaded"
        )

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

    try:
        parsed_data = receipt_parser.parse_receipt(extracted_text)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Receipt parsing failed: {str(e)}"
        )

    if require_items and (not parsed_data.get('items') or len(parsed_data['items']) == 0):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No items found in receipt. Please check the receipt format."
        )

    return parsed_data, extracted_text, file_ext


@router.post("/preview-receipt")
async def preview_receipt(
    file: UploadFile = File(...),
    receipt_type: Optional[str] = Form(None),
    current_user: dict = Depends(require_min_role("employee"))
):
    """
    Preview OCR and parsed receipt items without saving receipt or updating inventory.
    """
    try:
        file_content = await file.read()
        parsed_data, extracted_text, _ = _validate_and_parse_receipt(file, file_content, require_items=False)

        if receipt_type and receipt_type.lower() in ['purchase', 'sale']:
            parsed_data['receipt_type'] = receipt_type.lower()

        items = parsed_data.get('items', [])
        has_items = len(items) > 0
        non_empty_lines = [line.strip() for line in extracted_text.splitlines() if line.strip()]

        return {
            'success': has_items,
            'message': (
                'Receipt parsed successfully. Please review extracted items before processing.'
                if has_items else
                'OCR completed, but items were not confidently extracted. Review OCR text below and try a clearer crop or higher resolution.'
            ),
            'currency_code': parsed_data.get('currency_code', 'INR'),
            'receipt_type': parsed_data.get('receipt_type'),
            'receipt_date': parsed_data.get('receipt_date').isoformat() if parsed_data.get('receipt_date') else None,
            'source': parsed_data.get('source'),
            'total_amount': parsed_data.get('total_amount', 0.0),
            'items_processed': len(items),
            'items': items,
            'ocr_text_preview': extracted_text[:3000],
            'ocr_lines_preview': non_empty_lines[:80]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Receipt preview failed: {str(e)}"
        )


@router.post("/upload-receipt", response_model=ReceiptProcessingResult)
async def upload_receipt(
    file: UploadFile = File(...),
    receipt_type: Optional[str] = Form(None),
    source_currency: Optional[str] = Form(None),
    target_currency: Optional[str] = Form(None),
    exchange_rate: Optional[float] = Form(None),
    current_user: dict = Depends(require_min_role("employee")),
    db: Session = Depends(get_db)
):
    """
    Upload and process a receipt (image or PDF)
    
    Supported formats: JPG, PNG, PDF
    """
    try:
        file_content = await file.read()
        parsed_data, _, file_ext = _validate_and_parse_receipt(file, file_content, require_items=True)
        
        # Override receipt type if provided
        if receipt_type and receipt_type.lower() in ['purchase', 'sale']:
            parsed_data['receipt_type'] = receipt_type.lower()

        # Apply UI-selected currency conversion to persisted inventory values.
        parsed_currency = (parsed_data.get('currency_code') or 'INR').upper()
        source = (source_currency or parsed_currency).upper()
        target = (target_currency or parsed_currency).upper()
        rate = float(exchange_rate) if exchange_rate is not None else 1.0
        _apply_currency_conversion(parsed_data, source, target, rate)
        
        # Get user ID
        user_id = int(current_user.get('user_id'))
        
        # Convert image to base64 for storage
        image_base64 = base64.b64encode(file_content).decode('utf-8')
        parsed_data['image_data'] = f"data:image/{file_ext[1:]};base64,{image_base64}"
        
        # Process receipt and update inventory
        result = process_receipt_data(db, parsed_data, user_id)
        result['currency_code'] = parsed_data.get('currency_code', 'INR')
        
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

