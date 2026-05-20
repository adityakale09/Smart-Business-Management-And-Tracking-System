"""
Organization service with audit logging and admin user provisioning.

This module centralizes organization CRUD operations and related side effects
(such as audit logging and automatic user creation), keeping routers minimal.
"""

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List

from app.models.organization import Organization
from app.models.user import User, UserRole
from app.core.security import get_password_hash
from app.utils.audit_logger import log_create, log_update


def create_organization_with_admin(
    db: Session,
    org_data,
    current_user: dict,
    request: Request,
) -> dict:
    """Create an organization and automatically provision its admin user."""
    try:
        # Validate name uniqueness
        existing_name = db.query(Organization).filter(
            Organization.name == org_data.name
        ).first()
        if existing_name:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Organization name '{org_data.name}' already exists",
            )

        # Validate slug uniqueness
        existing_slug = db.query(Organization).filter(
            Organization.slug == org_data.slug
        ).first()
        if existing_slug:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Organization slug '{org_data.slug}' already exists",
            )

        # Validate admin username uniqueness
        existing_username = db.query(User).filter(
            User.username == org_data.admin_username
        ).first()
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Username '{org_data.admin_username}' is already taken",
            )

        # Validate admin email uniqueness
        existing_email = db.query(User).filter(
            User.email == org_data.admin_email
        ).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email '{org_data.admin_email}' is already registered",
            )

        # Create the organization
        org = Organization(
            name=org_data.name,
            slug=org_data.slug,
            is_active=True,
            settings=org_data.settings or {
                "timezone": "UTC",
                "currency": "INR",
            },
        )
        db.add(org)
        db.flush()  # Get org.id

        # Create the admin user for this organization
        admin_user = User(
            email=org_data.admin_email,
            username=org_data.admin_username,
            hashed_password=get_password_hash(org_data.admin_password),
            full_name=org_data.admin_full_name or f"Admin of {org_data.name}",
            role=UserRole.ADMIN,
            organization_id=org.id,
        )
        db.add(admin_user)
        db.flush()

        db.commit()
        db.refresh(org)
        db.refresh(admin_user)

        # Audit log
        log_create(
            db,
            "Organization",
            org.id,
            user_id=int(current_user["user_id"]),
            username=current_user.get("username", "system"),
            details={
                "name": org.name,
                "slug": org.slug,
                "admin_username": admin_user.username,
                "admin_email": admin_user.email,
            },
            request=request,
        )

        return {
            "organization": {
                "id": org.id,
                "name": org.name,
                "slug": org.slug,
                "is_active": org.is_active,
                "settings": org.settings,
                "created_at": org.created_at,
                "updated_at": org.updated_at,
                "user_count": 1,
            },
            "admin_user": {
                "id": admin_user.id,
                "email": admin_user.email,
                "username": admin_user.username,
                "full_name": admin_user.full_name,
                "role": admin_user.role.value if hasattr(admin_user.role, 'value') else str(admin_user.role),
                "organization_id": admin_user.organization_id,
            },
            "message": f"Organization '{org.name}' created successfully with admin user '{admin_user.username}'",
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create organization: {str(e)}",
        )


def get_organizations(db: Session) -> list:
    """Retrieve all organizations with user counts."""
    try:
        orgs = db.query(Organization).order_by(Organization.created_at.desc()).all()

        result = []
        for org in orgs:
            user_count = db.query(func.count(User.id)).filter(
                User.organization_id == org.id
            ).scalar() or 0

            result.append({
                "id": org.id,
                "name": org.name,
                "slug": org.slug,
                "is_active": org.is_active,
                "settings": org.settings,
                "created_at": org.created_at,
                "updated_at": org.updated_at,
                "user_count": user_count,
            })

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve organizations: {str(e)}",
        )


def get_organization_by_id(db: Session, org_id: int) -> dict:
    """Retrieve a single organization by ID with user count."""
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization with ID {org_id} not found",
        )

    user_count = db.query(func.count(User.id)).filter(
        User.organization_id == org.id
    ).scalar() or 0

    return {
        "id": org.id,
        "name": org.name,
        "slug": org.slug,
        "is_active": org.is_active,
        "settings": org.settings,
        "created_at": org.created_at,
        "updated_at": org.updated_at,
        "user_count": user_count,
    }


def update_organization(
    db: Session,
    org_id: int,
    org_data,
    current_user: dict,
    request: Request,
) -> dict:
    """Update an organization's metadata."""
    try:
        org = db.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organization with ID {org_id} not found",
            )

        update_fields = org_data.model_dump(exclude_unset=True)

        # Check name uniqueness if changing
        if "name" in update_fields and update_fields["name"] != org.name:
            existing = db.query(Organization).filter(
                Organization.name == update_fields["name"],
                Organization.id != org_id,
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Organization name '{update_fields['name']}' already exists",
                )

        for field, value in update_fields.items():
            setattr(org, field, value)

        db.commit()
        db.refresh(org)

        log_update(
            db,
            "Organization",
            org.id,
            user_id=int(current_user["user_id"]),
            username=current_user.get("username", "system"),
            details=update_fields,
            request=request,
        )

        user_count = db.query(func.count(User.id)).filter(
            User.organization_id == org.id
        ).scalar() or 0

        return {
            "id": org.id,
            "name": org.name,
            "slug": org.slug,
            "is_active": org.is_active,
            "settings": org.settings,
            "created_at": org.created_at,
            "updated_at": org.updated_at,
            "user_count": user_count,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update organization: {str(e)}",
        )
