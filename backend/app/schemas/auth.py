"""
Authentication schemas
"""

from pydantic import BaseModel, EmailStr, field_validator, Field
from typing import Optional
from app.models.user import UserRole
import re


class UserLogin(BaseModel):
    """User login schema"""
    username: str
    password: str


class UserRegister(BaseModel):
    """User registration schema"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=100)
    organization_id: Optional[int] = Field(None, description="Organization ID for multi-tenant isolation (required for registration)")
    # role removed from registration; always assigned default in backend
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password contains uppercase, lowercase, number"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format"""
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username can only contain letters, numbers, and underscores')
        return v


class Token(BaseModel):
    """Token response schema"""
    access_token: str
    token_type: str = "bearer"
    user_id: int
    role: str
    organization_id: Optional[int] = None


class UserResponse(BaseModel):
    """User response schema"""
    id: int
    email: str
    username: str
    full_name: str
    role: str
    is_active: bool
    organization_id: Optional[int] = None
    organization_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class ChangePassword(BaseModel):
    """Change password schema"""
    current_password: str
    new_password: str = Field(..., min_length=8)
    
    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password contains uppercase, lowercase, number"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v


class UpdateProfile(BaseModel):
    """Update user profile schema"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    
    @field_validator('full_name')
    @classmethod
    def validate_full_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate full name is not empty or whitespace"""
        if v is not None and v.strip() == '':
            raise ValueError('Full name cannot be empty or whitespace')
        return v


class UpdateUser(BaseModel):
    """Admin update user schema"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None








