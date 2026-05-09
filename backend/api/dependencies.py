"""
API Dependencies
"""

from typing import Annotated, List

from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.orm import Session

from backend.domain.schemas.auth import UserResponse
from backend.infrastructure.database import get_db
from backend.services.auth_service import AuthService


def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    Dependency to get current authenticated user from JWT token
    Requirement 1.7: Validate session tokens on every API request
    
    Args:
        authorization: Authorization header with Bearer token
        db: Database session
        
    Returns:
        Current user information
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract token from "Bearer <token>" format
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = parts[1]
    
    # Verify token
    payload = AuthService.verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user_id = payload.get("sub")
    user = AuthService.get_user_by_id(db, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create UserResponse with explicit string conversion for UUID
    # This ensures the validator is called and UUID is properly converted
    return UserResponse.model_validate({
        'id': str(user.id),
        'email': user.email,
        'role': user.role,
        'created_at': user.created_at,
        'email_verified': user.email_verified,
        'email_notifications_enabled': user.email_notifications_enabled
    })


def require_role(allowed_roles: List[str]):
    """
    Dependency factory to create role-based authorization dependencies
    Returns 403 Forbidden if the user's role is not in the allowed list.
    
    Usage:
        @router.post("/models/train")
        async def train_model(
            user: Annotated[UserResponse, Depends(require_role(["Admin", "Data_Scientist"]))]
        ):
            ...
    
    Args:
        allowed_roles: List of role names that are allowed to access the endpoint
        
    Returns:
        Dependency function that validates user role
    """
    def role_checker(
        current_user: Annotated[UserResponse, Depends(get_current_user)]
    ) -> UserResponse:
        """
        Check if current user has required role
        
        Args:
            current_user: Current authenticated user
            
        Returns:
            Current user if authorized
            
        Raises:
            HTTPException: 403 Forbidden if user role not in allowed_roles
        """
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {', '.join(allowed_roles)}. Your role: {current_user.role}"
            )
        return current_user
    
    return role_checker


# Pre-defined role dependencies for common use cases
# These can be used directly in route handlers

def require_admin(
    current_user: Annotated[UserResponse, Depends(require_role(["Admin"]))]
) -> UserResponse:
    """
    Dependency that requires Admin role
    Requirement 19.2: Admin has full access to all operations
    
    Returns:
        Current user if they have Admin role
        
    Raises:
        HTTPException: 403 Forbidden if user is not Admin
    """
    return current_user


def require_data_scientist_or_admin(
    current_user: Annotated[UserResponse, Depends(require_role(["Admin", "Data_Scientist"]))]
) -> UserResponse:
    """
    Dependency that requires Data_Scientist or Admin role
    Requirement 19.3: Data_Scientist can upload data, train models, and create predictions
    
    Returns:
        Current user if they have Data_Scientist or Admin role
        
    Raises:
        HTTPException: 403 Forbidden if user is Analyst
    """
    return current_user


def require_any_authenticated_user(
    current_user: Annotated[UserResponse, Depends(get_current_user)]
) -> UserResponse:
    """
    Dependency that requires any authenticated user (any role)
    Used for operations that all authenticated users can perform
    
    Returns:
        Current user
        
    Raises:
        HTTPException: 401 Unauthorized if not authenticated
    """
    return current_user
