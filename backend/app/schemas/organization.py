"""
Organization schemas for multi-tenant management.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from datetime import datetime
import re


class OrganizationCreate(BaseModel):
    """Schema for creating a new organization with admin user provisioning."""
    name: str = Field(..., min_length=2, max_length=100, description="Organization name")
    slug: str = Field(..., min_length=2, max_length=50, description="URL-friendly unique identifier")
    admin_email: str = Field(..., description="Email for the organization's admin user")
    admin_username: str = Field(..., min_length=3, max_length=50, description="Username for the org admin")
    admin_password: str = Field(..., min_length=8, description="Password for the org admin")
    admin_full_name: Optional[str] = Field(None, max_length=100, description="Full name for the org admin")
    settings: Optional[Dict[str, Any]] = Field(None, description="Organization settings (JSON)")

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        if not re.match(r'^[a-z0-9]+(?:-[a-z0-9]+)*$', v):
            raise ValueError("Slug must contain only lowercase letters, numbers, and hyphens")
        return v

    @field_validator("admin_email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', v):
            raise ValueError("Invalid email format")
        return v

    @field_validator("admin_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r'[A-Z]', v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r'[a-z]', v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r'\d', v):
            raise ValueError("Password must contain at least one number")
        return v

    @field_validator("admin_username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError("Username can only contain letters, numbers, and underscores")
        return v


class OrganizationUpdate(BaseModel):
    """Schema for updating an existing organization."""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    is_active: Optional[bool] = None
    settings: Optional[Dict[str, Any]] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Name cannot be empty or whitespace")
        return v


class OrganizationResponse(BaseModel):
    """Schema for organization API response."""
    id: int
    name: str
    slug: str
    is_active: bool
    settings: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    user_count: Optional[int] = Field(None, description="Number of users in this organization")

    class Config:
        from_attributes = True


class OrganizationCreateResponse(BaseModel):
    """Response after creating an organization with admin user."""
    organization: OrganizationResponse
    admin_user: dict = Field(..., description="Created admin user details")
    message: str
