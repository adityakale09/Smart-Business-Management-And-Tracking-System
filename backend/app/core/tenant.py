"""
Tenant utility for multi-tenant data isolation.

Provides helpers to scope database queries to the current user's organization.
"""
from fastapi import Depends
from app.core.security import get_current_user


def apply_org_filter(query, model, org_id):
    """
    Apply organization-scoped filter to a SQLAlchemy query.
    
    Args:
        query: SQLAlchemy query object
        model: SQLAlchemy model class (must have organization_id column)
        org_id: Organization ID to filter by
    
    Returns:
        Filtered query
    """
    if org_id is not None:
        return query.filter(model.organization_id == int(org_id))
    return query


def get_current_org_id(current_user: dict = Depends(get_current_user)) -> int:
    """
    Extract organization_id from the current authenticated user.
    
    Returns:
        organization_id from the JWT token payload
    """
    org_id = current_user.get("organization_id")
    if org_id is not None:
        return int(org_id)
    return org_id
