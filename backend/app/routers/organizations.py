"""
Organization management routes (Super Admin only).

Endpoints:
  POST   /api/organizations        - Create organization + provision admin user
  GET    /api/organizations        - List all organizations
  GET    /api/organizations/{id}   - Get single organization
  PUT    /api/organizations/{id}   - Update organization settings
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.core.permissions import require_super_admin
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    OrganizationCreateResponse,
)
from app.services.organization_service import (
    create_organization_with_admin,
    get_organizations,
    get_organization_by_id,
    update_organization,
)

router = APIRouter()


@router.post("/", response_model=OrganizationCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    org_data: OrganizationCreate,
    request: Request,
    current_user: dict = Depends(require_super_admin()),
    db: Session = Depends(get_db),
):
    """Create a new organization and automatically provision its admin user.
    
    Only super admins can create new organizations (businesses).
    The admin user is created with ADMIN role scoped to the new organization.
    """
    return create_organization_with_admin(db, org_data, current_user, request)


@router.get("/", response_model=List[OrganizationResponse])
async def list_organizations(
    current_user: dict = Depends(require_super_admin()),
    db: Session = Depends(get_db),
):
    """List all organizations in the system.
    
    Only super admins can view all organizations across the platform.
    """
    return get_organizations(db)


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: int,
    current_user: dict = Depends(require_super_admin()),
    db: Session = Depends(get_db),
):
    """Get a single organization by ID.
    
    Only super admins can view individual organization details.
    """
    return get_organization_by_id(db, org_id)


@router.put("/{org_id}", response_model=OrganizationResponse)
async def update_organization_endpoint(
    org_id: int,
    org_data: OrganizationUpdate,
    request: Request,
    current_user: dict = Depends(require_super_admin()),
    db: Session = Depends(get_db),
):
    """Update an organization's metadata.
    
    Only super admins can modify organizations.
    Supports updating name, active status, and settings.
    """
    return update_organization(db, org_id, org_data, current_user, request)
