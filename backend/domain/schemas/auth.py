"""
Authentication Schemas
Pydantic models for authentication requests and responses
"""

from datetime import datetime
from typing import Literal, Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict


class RegisterRequest(BaseModel):
    """Request schema for user registration"""
    
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="User's password (minimum 8 characters)"
    )
    role: Literal["Admin", "Data_Scientist", "Analyst"] = Field(
        default="Analyst",
        description="User's role in the system"
    )
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets security requirements"""
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
    """Request schema for user login"""
    
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")


class TokenResponse(BaseModel):
    """Response schema for successful authentication"""
    
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(default=86400, description="Token expiration time in seconds (24 hours)")


class UserResponse(BaseModel):
    """Response schema for user information"""
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )
    
    id: str = Field(..., description="User's unique identifier")
    email: str = Field(..., description="User's email address")
    role: str = Field(..., description="User's role")
    created_at: datetime = Field(..., description="Account creation timestamp")
    email_verified: bool = Field(..., description="Email verification status")
    email_notifications_enabled: bool = Field(..., description="Email notification preference")
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v: Any) -> str:
        """Convert UUID to string"""
        if isinstance(v, UUID):
            return str(v)
        return v


class AuthResponse(BaseModel):
    """Combined response schema for authentication with user info"""
    
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(default=86400, description="Token expiration time in seconds")
    user: UserResponse = Field(..., description="User information")


class ForgotPasswordRequest(BaseModel):
    """Request schema for password reset request"""
    
    email: EmailStr = Field(..., description="User's email address")


class ForgotPasswordResponse(BaseModel):
    """Response schema for password reset request"""
    
    message: str = Field(..., description="Success message")


class ResetPasswordRequest(BaseModel):
    """Request schema for password reset"""
    
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="New password (minimum 8 characters)"
    )
    
    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets security requirements"""
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
    """Response schema for password reset"""
    
    message: str = Field(..., description="Success message")


class UpdateSettingsRequest(BaseModel):
    """Request schema for updating user settings"""
    
    email_notifications_enabled: bool = Field(
        ...,
        description="Whether to enable email notifications for training job completion"
    )

