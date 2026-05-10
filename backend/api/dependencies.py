from typing import Annotated, List

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from backend.domain.schemas.auth import UserResponse
from backend.infrastructure.database import get_db
from backend.services.auth_service import AuthService


def get_current_user(
    authorization: Annotated[str | None, Header()] = None, db: Session = Depends(get_db)
) -> UserResponse:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]

    payload = AuthService.verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id or not isinstance(user_id, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = AuthService.get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return UserResponse.model_validate(
        {
            "id": str(user.id),
            "email": user.email,
            "role": user.role,
            "name": user.name,
            "avatar": user.avatar,
            "provider": user.provider or "credentials",
            "created_at": user.created_at,
            "email_verified": user.email_verified,
            "email_notifications_enabled": user.email_notifications_enabled,
        }
    )


def require_role(allowed_roles: List[str]):
    def role_checker(
        current_user: Annotated[UserResponse, Depends(get_current_user)],
    ) -> UserResponse:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {', '.join(allowed_roles)}. Your role: {current_user.role}",
            )
        return current_user

    return role_checker


def require_admin(
    current_user: Annotated[UserResponse, Depends(require_role(["Admin"]))],
) -> UserResponse:
    return current_user


def require_any_authenticated_user(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
) -> UserResponse:
    return current_user
