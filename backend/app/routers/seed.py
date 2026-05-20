"""
Seed database routes for generating dummy data
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import get_current_user
from app.core.permissions import require_min_role
from app.utils.generate_dummy_data import seed_database
from app.utils.audit_logger import log_create

router = APIRouter()


@router.post("/seed-database")
async def seed_database_endpoint(
    request: Request,
    current_user: dict = Depends(require_min_role("admin")),
    db: Session = Depends(get_db)
):
    """
    Seed database with dummy data (inventory items and receipts)
    
    Requires admin role
    """
    try:
        result = seed_database(organization_id=current_user.get("organization_id"))
        
        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get('message', 'Failed to seed database')
            )
        
        # Log database seeding
        log_create(
            db, "Seed", None,
            user_id=int(current_user["user_id"]),
            username=current_user.get("username", "system"),
            details={
                "inventory_items": result.get('inventory_items', 0),
                "receipts": result.get('receipts', 0)
            },
            request=request
        )
        
        return {
            "success": True,
            "message": result.get('message'),
            "data": {
                "inventory_items": result.get('inventory_items', 0),
                "receipts": result.get('receipts', 0)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database seeding failed: {str(e)}"
        )

