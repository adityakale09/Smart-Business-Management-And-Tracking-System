"""
Role-based access control permissions
"""

from typing import List
from fastapi import HTTPException, status, Depends
from app.core.security import get_current_user

# Role hierarchy
ROLES = {
    "admin": 4,
    "manager": 3,
    "employee": 2,
    "vendor": 1
}


def require_role(allowed_roles: List[str]):
    """Decorator to require specific roles"""
    def decorator(func):
        async def wrapper(*args, current_user: dict = Depends(get_current_user), **kwargs):
            user_role = current_user.get("role", "employee")
            
            if user_role not in allowed_roles:
                # Check if user has higher privilege
                user_level = ROLES.get(user_role, 0)
                required_level = max([ROLES.get(role, 0) for role in allowed_roles])
                
                if user_level < required_level:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
                    )
            
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator


def require_min_role(min_role: str):
    """Require minimum role level - use as a dependency"""
    def role_checker(current_user: dict = Depends(get_current_user)):
        # Handle enum conversion if role is UserRole enum
        user_role = current_user.get("role")
        if hasattr(user_role, 'value'):
            user_role = user_role.value
        elif not isinstance(user_role, str):
            user_role = str(user_role).lower()
        
        user_level = ROLES.get(user_role, 0)
        min_level = ROLES.get(min_role, 0)
        
        if user_level < min_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Minimum role required: {min_role}, your role: {user_role}"
            )
        return current_user
    return role_checker
