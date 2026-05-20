"""
Receipt processing routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
import base64
import csv
import io

from app.database import get_db
from app.core.security import get_current_user
from app.core.permissions import require_min_role
from app.schemas.receipt import (
    ReceiptResponse, ReceiptProcessingResult, ReceiptListResponse, ReceiptUpdate,
    ReceiptAnalyticsResponse, CategoryBreakdown, MonthlyTrend, SourceAnalytics
)
from app.models.receipt import Receipt, ReceiptItem, ReceiptCategory
from app.receipt_processor.ocr_service import ocr_service
from app.receipt_processor.parser import receipt_parser
from app.receipt_processor.update_inventory import process_receipt_data
from app.utils.audit_logger import log_create, log_update, log_delete
from app.utils.rate_limiter import upload_rate_limiter

MAX_RECEIPT_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

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

    if len(file_content) > MAX_RECEIPT_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {MAX_RECEIPT_FILE_SIZE // (1024 * 1024)}MB"
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
            detail="Please upload a proper receipt"
        )

    # Validate that the OCR content actually looks like a receipt
    if not receipt_parser.is_valid_receipt(extracted_text):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Please upload a proper receipt"
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
    request: Request,
    file: UploadFile = File(...),
    receipt_type: Optional[str] = Form(None),
    current_user: dict = Depends(require_min_role("employee"))
):
    """
    Preview OCR and parsed receipt items without saving receipt or updating inventory.
    """
    # Apply rate limiting
    upload_rate_limiter.check_rate_limit(request)
    
    try:
        file_content = await file.read()
        parsed_data, extracted_text, _ = _validate_and_parse_receipt(file, file_content, require_items=False)

        if receipt_type and receipt_type.lower() == 'purchase':
            parsed_data['receipt_type'] = 'purchase'

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
            'category': parsed_data.get('category'),
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
    request: Request,
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
    # Apply rate limiting
    upload_rate_limiter.check_rate_limit(request)
        
    try:
        file_content = await file.read()
        parsed_data, _, file_ext = _validate_and_parse_receipt(file, file_content, require_items=True)
        
        # Override receipt type if provided (default to purchase)
        if receipt_type and receipt_type.lower() == 'purchase':
            parsed_data['receipt_type'] = 'purchase'
        else:
            # Default to purchase if no valid type provided
            parsed_data['receipt_type'] = 'purchase'

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
        result = process_receipt_data(db, parsed_data, user_id, current_user.get("organization_id"))
        result['currency_code'] = parsed_data.get('currency_code', 'INR')
        result['category'] = parsed_data.get('category')
        
        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get('message', 'Failed to process receipt')
            )
        
        # Log receipt upload
        log_create(
            db, "Receipt", result.get("receipt_id"),
            user_id=user_id,
            username=current_user.get("username", "system"),
            details={
                "total_amount": result.get("total_amount"),
                "items_count": result.get("items_count"),
                "source": parsed_data.get("source"),
                "category": parsed_data.get("category")
            },
            request=request
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
    category: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: dict = Depends(require_min_role("employee")),
    db: Session = Depends(get_db)
):
    """Get list of all processed receipts with optional date-range filtering"""
    from sqlalchemy.orm import joinedload
    
    query = db.query(Receipt).options(joinedload(Receipt.items))
    
    org_id = current_user.get("organization_id")
    if org_id is not None:
        query = query.filter(Receipt.organization_id == int(org_id))
    
    # Filter by receipt type if provided
    if receipt_type and receipt_type.lower() in ['purchase', 'sale']:
        from app.models.receipt import ReceiptType
        query = query.filter(Receipt.receipt_type == ReceiptType(receipt_type.lower()))
    
    # Filter by category if provided
    if category:
        query = query.filter(Receipt.category == category.lower())
    
    # Filter by date range if provided
    if start_date:
        query = query.filter(Receipt.receipt_date >= start_date)
    if end_date:
        query = query.filter(Receipt.receipt_date <= end_date)
    
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
    
    # Check organization scope
    org_id = current_user.get("organization_id")
    if org_id is not None and receipt.organization_id != int(org_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Receipt with ID {receipt_id} not found"
        )
    
    return receipt


@router.put("/receipts/{receipt_id}")
async def update_receipt(
    receipt_id: int,
    request: Request,
    source: Optional[str] = Form(None),
    receipt_type: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
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
    
    # Check organization scope
    org_id = current_user.get("organization_id")
    if org_id is not None and receipt.organization_id != int(org_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Receipt with ID {receipt_id} not found"
        )
    
    # Update fields if provided
    if source is not None:
        receipt.source = source
    if receipt_type and receipt_type.lower() in ['purchase', 'sale']:
        receipt.receipt_type = receipt_type.lower()
    if category is not None:
        receipt.category = category
    if notes is not None:
        receipt.notes = notes
    
    db.commit()
    db.refresh(receipt)
    
    # Log receipt update
    log_update(
        db, "Receipt", receipt_id,
        user_id=int(current_user["user_id"]),
        username=current_user.get("username", "system"),
        details={"updated_fields": [f for f in ["source", "receipt_type", "category", "notes"] if locals().get(f) is not None]},
        request=request
    )
    
    return {
        "message": "Receipt updated successfully",
        "receipt": receipt
    }


@router.delete("/receipts/{receipt_id}")
async def delete_receipt(
    receipt_id: int,
    request: Request,
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
    
    # Check organization scope
    org_id = current_user.get("organization_id")
    if org_id is not None and receipt.organization_id != int(org_id):
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
    
    # Log receipt deletion
    log_delete(
        db, "Receipt", receipt_id,
        user_id=int(current_user["user_id"]),
        username=current_user.get("username", "system"),
        details=receipt_info,
        request=request
    )
    
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
    
    org_id = current_user.get("organization_id")
    if org_id is not None:
        query = query.filter(Inventory.organization_id == int(org_id))
    
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
                (datetime.now(timezone.utc) - item.updated_at).total_seconds() < 3600
            ) if item.updated_at else False
        })
    
    return result


@router.get("/analytics", response_model=ReceiptAnalyticsResponse)
async def get_receipt_analytics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: dict = Depends(require_min_role("employee")),
    db: Session = Depends(get_db)
):
    """
    Get receipt analytics including totals, category breakdown, monthly trends, and top sources.
    Provides comprehensive insights into spending patterns.
    """
    from sqlalchemy import func as sa_func
    from sqlalchemy.orm import joinedload
    
    # Base query
    base_query = db.query(Receipt)
    
    org_id = current_user.get("organization_id")
    if org_id is not None:
        base_query = base_query.filter(Receipt.organization_id == int(org_id))
    
    if start_date:
        base_query = base_query.filter(Receipt.receipt_date >= start_date)
    if end_date:
        base_query = base_query.filter(Receipt.receipt_date <= end_date)
    
    # Total stats
    total_receipts = base_query.count()
    total_amount_result = base_query.with_entities(sa_func.sum(Receipt.total_amount)).scalar()
    total_amount = float(total_amount_result or 0.0)
    
    # Total items count
    all_receipts = base_query.options(joinedload(Receipt.items)).all()
    total_items = sum(len(r.items) for r in all_receipts)
    
    # Average per receipt
    average_per_receipt = round(total_amount / total_receipts, 2) if total_receipts > 0 else 0.0
    
    # Category breakdown
    category_data = (
        db.query(
            Receipt.category,
            sa_func.count(Receipt.id).label('count'),
            sa_func.sum(Receipt.total_amount).label('total_amount')
        )
        .filter(Receipt.category.isnot(None))
    )
    if org_id is not None:
        category_data = category_data.filter(Receipt.organization_id == int(org_id))
    if start_date:
        category_data = category_data.filter(Receipt.receipt_date >= start_date)
    if end_date:
        category_data = category_data.filter(Receipt.receipt_date <= end_date)
    category_data = category_data.group_by(Receipt.category).order_by(sa_func.sum(Receipt.total_amount).desc()).all()
    
    category_breakdown = []
    for row in category_data:
        cat_total = float(row.total_amount or 0.0)
        percentage = round((cat_total / total_amount * 100), 1) if total_amount > 0 else 0.0
        category_breakdown.append(CategoryBreakdown(
            category=row.category or 'uncategorized',
            count=row.count,
            total_amount=cat_total,
            percentage=percentage
        ))
    
    # Monthly trends
    month_data = (
        db.query(
            sa_func.extract('year', Receipt.receipt_date).label('year'),
            sa_func.extract('month', Receipt.receipt_date).label('month'),
            sa_func.count(Receipt.id).label('count'),
            sa_func.sum(Receipt.total_amount).label('total_amount')
        )
    )
    if org_id is not None:
        month_data = month_data.filter(Receipt.organization_id == int(org_id))
    if start_date:
        month_data = month_data.filter(Receipt.receipt_date >= start_date)
    if end_date:
        month_data = month_data.filter(Receipt.receipt_date <= end_date)
    month_data = month_data.group_by(
        sa_func.extract('year', Receipt.receipt_date),
        sa_func.extract('month', Receipt.receipt_date)
    ).order_by(
        sa_func.extract('year', Receipt.receipt_date).desc(),
        sa_func.extract('month', Receipt.receipt_date).desc()
    ).all()
    
    monthly_trends = []
    for row in month_data:
        monthly_trends.append(MonthlyTrend(
            year=int(row.year),
            month=int(row.month),
            count=row.count,
            total_amount=float(row.total_amount or 0.0)
        ))
    
    # Top sources
    source_data = (
        db.query(
            Receipt.source,
            sa_func.count(Receipt.id).label('count'),
            sa_func.sum(Receipt.total_amount).label('total_amount')
        )
        .filter(Receipt.source.isnot(None), Receipt.source != 'Unknown')
    )
    if org_id is not None:
        source_data = source_data.filter(Receipt.organization_id == int(org_id))
    if start_date:
        source_data = source_data.filter(Receipt.receipt_date >= start_date)
    if end_date:
        source_data = source_data.filter(Receipt.receipt_date <= end_date)
    source_data = source_data.group_by(Receipt.source).order_by(sa_func.sum(Receipt.total_amount).desc()).limit(10).all()
    
    top_sources = []
    for row in source_data:
        top_sources.append(SourceAnalytics(
            source=row.source or 'Unknown',
            count=row.count,
            total_amount=float(row.total_amount or 0.0)
        ))
    
    # Type breakdown
    type_data = base_query.with_entities(Receipt.receipt_type, sa_func.count(Receipt.id).label('count')).group_by(Receipt.receipt_type).all()
    type_breakdown = {}
    for row in type_data:
        type_breakdown[str(row.receipt_type)] = row.count
    
    return ReceiptAnalyticsResponse(
        total_receipts=total_receipts,
        total_amount=total_amount,
        total_items=total_items,
        average_per_receipt=average_per_receipt,
        category_breakdown=category_breakdown,
        monthly_trends=monthly_trends,
        top_sources=top_sources,
        type_breakdown=type_breakdown
    )


@router.get("/export")
async def export_receipts(
    format: str = Query("csv", regex="^(csv|json)$"),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    receipt_type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    current_user: dict = Depends(require_min_role("employee")),
    db: Session = Depends(get_db)
):
    """
    Export receipts as CSV or JSON with optional filters.
    Returns a downloadable file for external analysis.
    """
    from sqlalchemy.orm import joinedload
    
    query = db.query(Receipt).options(joinedload(Receipt.items))
    
    org_id = current_user.get("organization_id")
    if org_id is not None:
        query = query.filter(Receipt.organization_id == int(org_id))
    
    if receipt_type and receipt_type.lower() in ['purchase', 'sale']:
        from app.models.receipt import ReceiptType
        query = query.filter(Receipt.receipt_type == ReceiptType(receipt_type.lower()))
    
    if category:
        query = query.filter(Receipt.category == category.lower())
    
    if start_date:
        query = query.filter(Receipt.receipt_date >= start_date)
    if end_date:
        query = query.filter(Receipt.receipt_date <= end_date)
    
    receipts = query.order_by(Receipt.created_at.desc()).all()
    
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    
    if format == "json":
        export_data = []
        for r in receipts:
            receipt_data = {
                "id": r.id,
                "receipt_date": r.receipt_date.isoformat() if r.receipt_date else None,
                "receipt_type": str(r.receipt_type) if r.receipt_type else None,
                "source": r.source,
                "total_amount": r.total_amount,
                "category": r.category,
                "notes": r.notes,
                "items_count": len(r.items),
                "items": [
                    {
                        "product_name": i.product_name,
                        "quantity": i.quantity,
                        "price_per_unit": i.price_per_unit,
                        "total_price": i.quantity * i.price_per_unit
                    }
                    for i in r.items
                ]
            }
            export_data.append(receipt_data)
        
        from fastapi.responses import JSONResponse
        return JSONResponse(
            content=export_data,
            headers={
                "Content-Disposition": f"attachment; filename=receipts_export_{timestamp}.json"
            }
        )
    
    else:
        # CSV export
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Receipt ID", "Date", "Type", "Source", "Category",
            "Total Amount", "Items Count", "Product Name", "Quantity",
            "Unit Price", "Item Total", "Notes"
        ])
        
        for r in receipts:
            if r.items:
                for i in r.items:
                    writer.writerow([
                        r.id,
                        r.receipt_date.isoformat() if r.receipt_date else "",
                        str(r.receipt_type) if r.receipt_type else "",
                        r.source or "",
                        r.category or "",
                        r.total_amount,
                        len(r.items),
                        i.product_name,
                        i.quantity,
                        i.price_per_unit,
                        i.quantity * i.price_per_unit,
                        r.notes or ""
                    ])
            else:
                writer.writerow([
                    r.id,
                    r.receipt_date.isoformat() if r.receipt_date else "",
                    str(r.receipt_type) if r.receipt_type else "",
                    r.source or "",
                    r.category or "",
                    r.total_amount,
                    0, "", "", "", "",
                    r.notes or ""
                ])
        
        from fastapi.responses import StreamingResponse
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=receipts_export_{timestamp}.csv"
            }
        )

