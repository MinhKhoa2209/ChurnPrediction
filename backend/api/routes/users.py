from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from backend.api.dependencies import require_admin
from backend.domain.models.user import User
from backend.domain.schemas.auth import UserResponse
from backend.domain.schemas.users import UpdateUserRoleRequest
from backend.infrastructure.database import get_db

router = APIRouter(prefix="/users", tags=["User Management"])


@router.get(
    "",
    response_model=List[UserResponse],
    responses={
        200: {"description": "List of users"},
        403: {"description": "Forbidden - requires Admin role"},
    },
)
async def list_users(
    current_user: Annotated[UserResponse, Depends(require_admin)], db: Session = Depends(get_db)
):
    users = db.query(User).order_by(User.created_at.desc()).all()
    return users


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    responses={
        200: {"description": "User details"},
        403: {"description": "Forbidden - requires Admin role"},
        404: {"description": "User not found"},
    },
)
async def get_user(
    user_id: str,
    current_user: Annotated[UserResponse, Depends(require_admin)],
    db: Session = Depends(get_db),
):
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID format")

    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    return user


@router.patch(
    "/{user_id}/role",
    response_model=UserResponse,
    responses={
        200: {"description": "User role updated successfully"},
        400: {"description": "Cannot update your own role"},
        403: {"description": "Forbidden - requires Admin role"},
        404: {"description": "User not found"},
    },
)
async def update_user_role(
    user_id: str,
    request: UpdateUserRoleRequest,
    current_user: Annotated[UserResponse, Depends(require_admin)],
    db: Session = Depends(get_db),
):
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID format")

    if str(current_user.id) == user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot change your own role")

    if request.role not in ["Admin", "Analyst"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role. Must be 'Admin' or 'Analyst'")

    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.role = request.role
    db.commit()
    db.refresh(user)

    return user


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "User deleted successfully"},
        400: {"description": "Cannot delete yourself"},
        403: {"description": "Forbidden - requires Admin role"},
        404: {"description": "User not found"},
    },
)
async def delete_user(
    user_id: str,
    current_user: Annotated[UserResponse, Depends(require_admin)],
    db: Session = Depends(get_db),
):
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID format")

    if str(current_user.id) == user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete yourself")

    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    db.delete(user)
    db.commit()

    return None
