import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.api.dependencies import get_current_user
from backend.domain.schemas.auth import (
    AuthResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    ResetPasswordResponse,
    UpdateSettingsRequest,
    UserResponse,
)
from backend.domain.schemas.errors import ErrorResponse
from backend.infrastructure.database import get_db_session as get_db
from backend.services.audit_service import AuditService
from backend.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
    description="""
    Register a new user account with email and password authentication.
    
    **Requirements:**
    - Email must be unique and valid format
    - Password must be at least 8 characters
    - Role must be one of: Admin, Analyst
    
    **Security:**
    - Passwords are hashed using bcrypt with cost factor 12
    - Returns JWT token with 24-hour expiration
    
    **Example Request:**
    ```json
    {
        "email": "user@example.com",
        "password": "SecurePass123!",
        "role": "Analyst"
    }
    ```
    """,
    responses={
        201: {
            "description": "User successfully registered",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer",
                        "expires_in": 86400,
                        "user": {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "email": "user@example.com",
                            "role": "Analyst",
                            "created_at": "2024-01-15T10:30:00Z",
                        },
                    }
                }
            },
        },
        400: {
            "model": ErrorResponse,
            "description": "Invalid request data",
            "content": {
                "application/json": {
                    "example": {
                        "error": "VALIDATION_ERROR",
                        "message": "Invalid request data",
                        "details": "Password must be at least 8 characters",
                        "requestId": "req_abc123xyz",
                        "timestamp": "2024-01-15T10:30:00Z",
                    }
                }
            },
        },
        409: {
            "model": ErrorResponse,
            "description": "Email already registered",
            "content": {
                "application/json": {
                    "example": {
                        "error": "CONFLICT",
                        "message": "Email already registered",
                        "details": "A user with this email already exists",
                        "requestId": "req_abc123xyz",
                        "timestamp": "2024-01-15T10:30:00Z",
                    }
                }
            },
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "email"],
                                "msg": "value is not a valid email address",
                                "type": "value_error.email",
                            }
                        ]
                    }
                }
            },
        },
    },
)
async def register(request: RegisterRequest, db: Session = Depends(get_db)) -> AuthResponse:
    try:
        user = AuthService.register_user(
            db=db, email=request.email, password=request.password, name=request.name
        )

        access_token = AuthService.create_access_token(
            user_id=str(user.id), email=user.email, role=user.role
        )

        return AuthResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=86400,
            user=UserResponse(
                id=str(user.id),
                email=user.email,
                role=user.role,
                name=user.name,
                avatar=user.avatar,
                provider=user.provider or "credentials",
                created_at=user.created_at,
                email_verified=user.email_verified,
                email_notifications_enabled=user.email_notifications_enabled,
            ),
        )

    except ValueError as e:
        if "already registered" in str(e):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Authenticate user and obtain JWT token",
    description="""
    Authenticate with email and password to obtain a JWT access token.
    
    **Authentication Flow:**
    1. Submit email and password
    2. Receive JWT token with 24-hour expiration
    3. Include token in Authorization header for subsequent requests
    
    **Rate Limiting:**
    - Limited to 100 requests per minute per IP address
    - Returns 429 status code when limit exceeded
    
    **Security:**
    - Failed attempts are logged for security audit
    - Response time is consistent to prevent timing attacks
    
    **Example Request:**
    ```json
    {
        "email": "user@example.com",
        "password": "SecurePass123!"
    }
    ```
    """,
    responses={
        200: {
            "description": "Login successful",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer",
                        "expires_in": 86400,
                        "user": {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "email": "user@example.com",
                            "role": "Analyst",
                            "created_at": "2024-01-15T10:30:00Z",
                        },
                    }
                }
            },
        },
        401: {
            "model": ErrorResponse,
            "description": "Invalid credentials",
            "content": {
                "application/json": {
                    "example": {
                        "error": "UNAUTHORIZED",
                        "message": "Invalid email or password",
                        "details": "Authentication failed",
                        "requestId": "req_abc123xyz",
                        "timestamp": "2024-01-15T10:30:00Z",
                    }
                }
            },
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "email"],
                                "msg": "field required",
                                "type": "value_error.missing",
                            }
                        ]
                    }
                }
            },
        },
        429: {
            "model": ErrorResponse,
            "description": "Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {
                        "error": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests",
                        "details": "Rate limit of 100 requests per minute exceeded",
                        "requestId": "req_abc123xyz",
                        "timestamp": "2024-01-15T10:30:00Z",
                    }
                }
            },
        },
    },
)
async def login(
    login_request: LoginRequest, request: Request, db: Session = Depends(get_db)
) -> AuthResponse:
    start_time = time.time()

    user = AuthService.authenticate_user(
        db=db, email=login_request.email, password=login_request.password
    )

    elapsed_time = (time.time() - start_time) * 1000

    if not user:
        AuditService.log_authentication_attempt(
            db=db, user_id=None, action="login_failed", request=request, success=False
        )

        if elapsed_time < 200:
            time.sleep((200 - elapsed_time) / 1000)

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    AuditService.log_authentication_attempt(
        db=db, user_id=user.id, action="login_success", request=request, success=True
    )

    access_token = AuthService.create_access_token(
        user_id=str(user.id), email=user.email, role=user.role
    )

    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=86400,
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            role=user.role,
            name=user.name,
            avatar=user.avatar,
            provider=user.provider or "credentials",
            created_at=user.created_at,
            email_verified=user.email_verified,
            email_notifications_enabled=user.email_notifications_enabled,
        ),
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "Logout successful"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
async def logout(current_user: Annotated[UserResponse, Depends(get_current_user)]):
    return None


@router.get(
    "/me",
    responses={
        200: {"description": "Current user information"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
async def get_current_user_info(current_user: Annotated[UserResponse, Depends(get_current_user)]):
    import json
    from datetime import datetime

    from fastapi.responses import JSONResponse

    def json_encoder(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    user_data = {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "name": current_user.name,
        "avatar": current_user.avatar,
        "provider": current_user.provider,
        "created_at": current_user.created_at,
        "email_verified": current_user.email_verified,
        "email_notifications_enabled": current_user.email_notifications_enabled,
    }

    return JSONResponse(content=json.loads(json.dumps(user_data, default=json_encoder)))


@router.patch(
    "/settings",
    response_model=UserResponse,
    responses={
        200: {"description": "User settings updated successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        400: {"model": ErrorResponse, "description": "Invalid request data"},
    },
)
async def update_user_settings(
    settings: UpdateSettingsRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> UserResponse:
    from uuid import UUID

    from backend.domain.models.user import User

    user = db.query(User).filter(User.id == UUID(current_user.id)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if settings.email_notifications_enabled is not None:
        user.email_notifications_enabled = settings.email_notifications_enabled
    
    if settings.name is not None:
        user.name = settings.name
    
    if settings.avatar is not None:
        user.avatar = settings.avatar
    
    db.commit()
    db.refresh(user)

    user_dict = {
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

    return UserResponse.model_validate(user_dict)


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Password reset email sent (or user not found - same response for security)"
        },
        400: {"model": ErrorResponse, "description": "Invalid request data"},
    },
)
async def forgot_password(
    request: ForgotPasswordRequest, db: Session = Depends(get_db)
) -> ForgotPasswordResponse:
    AuthService.create_password_reset_token(db, request.email)

    return ForgotPasswordResponse(
        message="If an account exists with this email, a password reset link has been sent. The link will expire in 1 hour."
    )


@router.post(
    "/reset-password",
    response_model=ResetPasswordResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Password successfully reset"},
        400: {"model": ErrorResponse, "description": "Invalid or expired token"},
        422: {"model": ErrorResponse, "description": "Invalid password format"},
    },
)
async def reset_password(
    request: ResetPasswordRequest, db: Session = Depends(get_db)
) -> ResetPasswordResponse:
    success = AuthService.reset_password(db, request.token, request.new_password)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token"
        )

    return ResetPasswordResponse(
        message="Password has been successfully reset. You can now log in with your new password."
    )
