"""
Authentication routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import get_current_user
from app.core.permissions import require_min_role
from app.schemas.auth import UserLogin, UserRegister, Token, UserResponse, ChangePassword, UpdateProfile, UpdateUser
from app.models.user import User
from app.services.auth_service import (
    register_with_audit,
    login_with_audit,
    update_profile_with_audit,
    change_password_with_audit
)

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, request: Request, db: Session = Depends(get_db)):
    """Register a new user"""
    new_user = register_with_audit(db, user_data, request)
    
    # Return user with role converted to string for response model
    return {
        "id": new_user.id,
        "email": new_user.email,
        "username": new_user.username,
        "full_name": new_user.full_name,
        "role": new_user.role.value if hasattr(new_user.role, 'value') else str(new_user.role),
        "is_active": new_user.is_active
    }


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, request: Request, db: Session = Depends(get_db)):
    """User login"""
    return login_with_audit(db, credentials, request)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current user information"""
    try:
        user_id = current_user["user_id"]
        user = db.query(User).filter(User.id == int(user_id)).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Return user with role converted to string for response model
        return {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
            "is_active": user.is_active
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user information: {str(e)}"
        )


@router.post("/change-password")
async def change_password(
    password_data: ChangePassword,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    return change_password_with_audit(db, int(current_user["user_id"]), password_data, request)


@router.put("/me", response_model=UserResponse)
async def update_profile(
    profile_data: UpdateProfile,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user profile"""
    user = update_profile_with_audit(db, int(current_user["user_id"]), profile_data, current_user, request)
    
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
        "is_active": user.is_active
    }


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(require_min_role("admin")),
    db: Session = Depends(get_db)
):
    """List all users (Admin only)"""
    users = db.query(User).offset(skip).limit(limit).all()
    
    return [
        {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
            "is_active": user.is_active
        }
        for user in users
    ]


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: dict = Depends(require_min_role("admin")),
    db: Session = Depends(get_db)
):
    """Get user by ID (Admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
        "is_active": user.is_active
    }


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UpdateUser,
    current_user: dict = Depends(require_min_role("admin")),
    db: Session = Depends(get_db)
):
    """Update user (Admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields if provided
    update_data = user_data.dict(exclude_unset=True)
    
    # Check if email is being changed and if it's already taken
    if "email" in update_data and update_data["email"] != user.email:
        existing = db.query(User).filter(User.email == update_data["email"]).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
        "is_active": user.is_active
    }


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: dict = Depends(require_min_role("admin")),
    db: Session = Depends(get_db)
):
    """Deactivate user (Admin only) - Soft delete"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent self-deletion
    if user.id == int(current_user["user_id"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    # Soft delete - deactivate instead of removing
    user.is_active = False
    db.commit()
    
    return {"message": f"User {user.username} has been deactivated"}


