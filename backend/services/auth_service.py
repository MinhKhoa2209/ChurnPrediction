"""
Authentication Service

This service handles user authentication, password hashing, JWT token management,
and password reset functionality.
"""

import secrets
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from backend.config import settings
from backend.domain.models.user import User


class AuthService:
    """Service for authentication and authorization operations"""

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt with cost factor 12
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password string
        """
        # Generate salt and hash password with cost factor from config (default 12)
        salt = bcrypt.gensalt(rounds=settings.password_bcrypt_rounds)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash
        
        Args:
            plain_password: Plain text password to verify
            hashed_password: Hashed password from database
            
        Returns:
            True if password matches, False otherwise
        """
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )

    @staticmethod
    def create_access_token(user_id: str, email: str, role: str) -> str:
        """
        Create a JWT access token with 24-hour expiration
        
        Args:
            user_id: User's UUID
            email: User's email address
            role: User's role (Admin, Data_Scientist, Analyst)
            
        Returns:
            JWT token string
        """
        # Calculate expiration time (24 hours from now)
        expires_at = datetime.utcnow() + timedelta(hours=settings.jwt_expiration_hours)
        
        # Create JWT payload
        payload = {
            "sub": str(user_id),  # Subject (user ID)
            "email": email,
            "role": role,
            "exp": expires_at,  # Expiration time
            "iat": datetime.utcnow(),  # Issued at time
        }
        
        # Encode JWT token
        token = jwt.encode(
            payload,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm
        )
        
        return token

    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """
        Verify and decode a JWT token
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm]
            )
            return payload
        except JWTError:
            return None

    @staticmethod
    def register_user(
        db: Session,
        email: str,
        password: str,
        role: str = "Analyst"
    ) -> User:
        """
        Register a new user
        
        Args:
            db: Database session
            email: User's email address
            password: Plain text password
            role: User's role (default: Analyst)
            
        Returns:
            Created User object
            
        Raises:
            ValueError: If email already exists or role is invalid
        """
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise ValueError("Email already registered")
        
        # Validate role
        valid_roles = ["Admin", "Data_Scientist", "Analyst"]
        if role not in valid_roles:
            raise ValueError(f"Invalid role. Must be one of: {', '.join(valid_roles)}")
        
        # Hash password
        password_hash = AuthService.hash_password(password)
        
        # Create user
        user = User(
            email=email,
            password_hash=password_hash,
            role=role
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """
        Authenticate a user with email and password
        
        Args:
            db: Database session
            email: User's email address
            password: Plain text password
            
        Returns:
            User object if authentication successful, None otherwise
        """
        # Find user by email
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            return None
        
        # Verify password
        if not AuthService.verify_password(password, user.password_hash):
            return None
        
        return user

    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
        """
        Get user by ID
        
        Args:
            db: Database session
            user_id: User's UUID
            
        Returns:
            User object if found, None otherwise
        """
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """
        Get user by email
        
        Args:
            db: Database session
            email: User's email address
            
        Returns:
            User object if found, None otherwise
        """
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def generate_reset_token() -> str:
        """
        Generate a secure random token for password reset
        
        Returns:
            Secure random token string (32 bytes, URL-safe)
        """
        return secrets.token_urlsafe(32)

    @staticmethod
    def create_password_reset_token(db: Session, email: str) -> Optional[str]:
        """
        Create a password reset token for a user
        
        Args:
            db: Database session
            email: User's email address
            
        Returns:
            Reset token if user exists, None otherwise
        """
        # Find user by email
        user = AuthService.get_user_by_email(db, email)
        
        if not user:
            # Return None silently to prevent email enumeration
            return None
        
        # Generate reset token
        reset_token = AuthService.generate_reset_token()
        
        # Set token expiration (1 hour from now)
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        # Update user with reset token
        user.reset_token = reset_token
        user.reset_token_expires = expires_at
        
        db.commit()
        
        return reset_token

    @staticmethod
    def verify_reset_token(db: Session, token: str) -> Optional[User]:
        """
        Verify a password reset token and return the associated user
        
        Args:
            db: Database session
            token: Reset token string
            
        Returns:
            User object if token is valid and not expired, None otherwise
        """
        # Find user by reset token
        user = db.query(User).filter(User.reset_token == token).first()
        
        if not user:
            return None
        
        # Check if token has expired
        if not user.reset_token_expires or user.reset_token_expires < datetime.utcnow():
            return None
        
        return user

    @staticmethod
    def reset_password(db: Session, token: str, new_password: str) -> bool:
        """
        Reset a user's password using a valid reset token
        
        Args:
            db: Database session
            token: Reset token string
            new_password: New plain text password
            
        Returns:
            True if password was reset successfully, False otherwise
        """
        # Verify reset token
        user = AuthService.verify_reset_token(db, token)
        
        if not user:
            return False
        
        # Hash new password
        new_password_hash = AuthService.hash_password(new_password)
        
        # Update user password and clear reset token
        user.password_hash = new_password_hash
        user.reset_token = None
        user.reset_token_expires = None
        
        db.commit()
        
        return True
