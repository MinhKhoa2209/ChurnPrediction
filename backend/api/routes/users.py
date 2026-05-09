"""
User Management API Routes
"""



from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.api.dependencies import require_admin
from backend.domain.schemas.auth import UserResponse
from backend.infrastructure.database import get_db

router = APIRouter(prefix="/users", tags=["User Management"])


@router.get(
    "",
    responses={
        200: {"description": "List of users"},
        403: {"description": "Forbidden - requires Admin role"},
    }
)
async def list_users(
    # Requirement 19.2: Only Admin can manage users
    current_user: Annotated[UserResponse, Depends(require_admin)],
    db: Session = Depends(get_db)
):
    """
    List all users
    
    **Authorization**: Requires Admin role
    
    **RBAC Matrix**:
    - Admin: ✓ Allowed
    - Data_Scientist: ✗ Forbidden
    - Analyst: ✗ Forbidden
    
    Args:
        current_user: Current authenticated user (must be Admin)
        db: Database session
        
    Returns:
        List of all users
    """
    # TODO: Implement user listing
    return {
        "message": "List users endpoint (Admin only)",
        "user": current_user.email,
        "role": current_user.role
    }


@router.get(
    "/{user_id}",
    responses={
        200: {"description": "User details"},
        403: {"description": "Forbidden - requires Admin role"},
        404: {"description": "User not found"},
    }
)
async def get_user(
    user_id: str,
    current_user: Annotated[UserResponse, Depends(require_admin)],
    db: Session = Depends(get_db)
):
    """
    Get user details
    
    **Authorization**: Requires Admin role
    
    **RBAC Matrix**:
    - Admin: ✓ Allowed
    - Data_Scientist: ✗ Forbidden
    - Analyst: ✗ Forbidden
    
    Args:
        user_id: User UUID
        current_user: Current authenticated user (must be Admin)
        db: Database session
        
    Returns:
        User details
    """
    # TODO: Implement user retrieval
    return {
        "message": f"Get user {user_id} (Admin only)",
        "user": current_user.email,
        "role": current_user.role
    }


@router.patch(
    "/{user_id}/role",
    responses={
        200: {"description": "User role updated successfully"},
        403: {"description": "Forbidden - requires Admin role"},
        404: {"description": "User not found"},
    }
)
async def update_user_role(
    user_id: str,
    current_user: Annotated[UserResponse, Depends(require_admin)],
    db: Session = Depends(get_db)
):
    """
    Update user role
    
    **Authorization**: Requires Admin role
    
    **RBAC Matrix**:
    - Admin: ✓ Allowed
    - Data_Scientist: ✗ Forbidden
    - Analyst: ✗ Forbidden
    
    Args:
        user_id: User UUID
        current_user: Current authenticated user (must be Admin)
        db: Database session
        
    Returns:
        Updated user details
    """
    # TODO: Implement user role update
    return {
        "message": f"Update user {user_id} role (Admin only)",
        "user": current_user.email,
        "role": current_user.role
    }


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "User deleted successfully"},
        403: {"description": "Forbidden - requires Admin role"},
        404: {"description": "User not found"},
    }
)
async def delete_user(
    user_id: str,
    current_user: Annotated[UserResponse, Depends(require_admin)],
    db: Session = Depends(get_db)
):
    """
    Delete a user
    
    **Authorization**: Requires Admin role
    
    **RBAC Matrix**:
    - Admin: ✓ Allowed
    - Data_Scientist: ✗ Forbidden
    - Analyst: ✗ Forbidden
    
    Args:
        user_id: User UUID
        current_user: Current authenticated user (must be Admin)
        db: Database session
        
    Returns:
        No content (204)
    """
    # TODO: Implement user deletion
    return None
