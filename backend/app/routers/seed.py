"""
Seed database routes for generating dummy data
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import get_current_user
from app.core.permissions import require_min_role
from app.utils.generate_dummy_data import seed_database

router = APIRouter()


@router.post("/seed-database")
async def seed_database_endpoint(
    current_user: dict = Depends(require_min_role("admin")),
    db: Session = Depends(get_db)
):
    """
    Seed database with dummy data (inventory items and receipts)
    
    Requires admin role
    """
    try:
        result = seed_database()
        
        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get('message', 'Failed to seed database')
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

