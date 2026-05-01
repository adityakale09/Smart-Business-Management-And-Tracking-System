"""
Authentication service with audit logging.

This module centralizes authentication operations and related side effects
(such as audit logging), keeping routers minimal.
"""

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session
from datetime import timedelta

from app.models.user import User, UserRole
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.config import settings
from app.utils.audit_logger import log_login, log_create, log_update, log_password_change


def register_with_audit(db: Session, user_data, request: Request):
    """Register new user and write audit entry."""
    try:
        # Check if user exists
        existing_user = db.query(User).filter(
            (User.email == user_data.email) | (User.username == user_data.username)
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email or username already registered"
            )
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        new_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            role=UserRole.EMPLOYEE  # Always assign default role
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Log user creation
        log_create(
            db, "User", new_user.id,
            user_id=new_user.id,
            username=new_user.username,
            details={"role": new_user.role.value, "email": new_user.email},
            request=request
        )
        
        return new_user
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


def login_with_audit(db: Session, credentials, request: Request):
    """Authenticate user and write audit entry."""
    try:
        user = db.query(User).filter(User.username == credentials.username).first()
        
        if not user or not verify_password(credentials.password, user.hashed_password):
            # Log failed login attempt
            log_login(db, None, credentials.username, request, "failure", "Invalid credentials")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        if not user.is_active:
            log_login(db, user.id, user.username, request, "failure", "Account inactive")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id), "role": user.role.value},
            expires_delta=access_token_expires
        )
        
        # Log successful login
        log_login(db, user.id, user.username, request, "success")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user.id,
            "role": user.role.value
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


def update_profile_with_audit(db: Session, user_id: int, profile_data, current_user: dict, request: Request):
    """Update user profile and write audit entry."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update fields if provided
        update_data = profile_data.dict(exclude_unset=True)
        
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
        
        # Log profile update
        log_update(
            db, "User", user.id,
            user_id=current_user["user_id"],
            username=current_user.get("username", "system"),
            details=update_data,
            request=request
        )
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )


def change_password_with_audit(db: Session, user_id: int, password_data, request: Request):
    """Change user password and write audit entry."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify current password
        if not verify_password(password_data.current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Update password
        user.hashed_password = get_password_hash(password_data.new_password)
        db.commit()
        
        # Log password change
        log_password_change(db, user.id, user.username, request)
        
        return {"message": "Password changed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to change password: {str(e)}"
        )
