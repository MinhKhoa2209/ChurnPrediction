from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="User's full name")
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(
        ..., min_length=8, max_length=100, description="User's password (minimum 8 characters)"
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")


class AdminLoginRequest(BaseModel):
    email: EmailStr = Field(..., description="Admin email address")
    password: str = Field(..., description="Admin password")


class GoogleAuthRequest(BaseModel):
    credential: str = Field(..., description="Google OAuth credential token")


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(
        default=86400, description="Token expiration time in seconds (24 hours)"
    )


class UserResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str = Field(..., description="User's unique identifier")
    email: str = Field(..., description="User's email address")
    role: str = Field(..., description="User's role")
    name: Optional[str] = Field(None, description="User's full name")
    avatar: Optional[str] = Field(None, description="User's avatar URL")
    provider: str = Field(default="credentials", description="Auth provider")
    created_at: datetime = Field(..., description="Account creation timestamp")
    email_verified: bool = Field(..., description="Email verification status")
    email_notifications_enabled: bool = Field(..., description="Email notification preference")

    @field_validator("id", mode="before")
    @classmethod
    def convert_uuid_to_str(cls, v: Any) -> str:
        if isinstance(v, UUID):
            return str(v)
        return v


class AuthResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(default=86400, description="Token expiration time in seconds")
    user: UserResponse = Field(..., description="User information")


class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(..., description="User's email address")


class ForgotPasswordResponse(BaseModel):
    message: str = Field(..., description="Success message")


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(
        ..., min_length=8, max_length=100, description="New password (minimum 8 characters)"
    )

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class ResetPasswordResponse(BaseModel):
    message: str = Field(..., description="Success message")


class UpdateSettingsRequest(BaseModel):
    email_notifications_enabled: Optional[bool] = Field(
        None, description="Whether to enable email notifications for training job completion"
    )
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="User's full name")
    avatar: Optional[str] = Field(None, max_length=500, description="User's avatar URL")
