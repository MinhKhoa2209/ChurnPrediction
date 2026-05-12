import secrets
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from backend.config import settings
from backend.domain.models.user import User


class AuthService:
    VALID_ROLES = {"Admin", "Analyst"}

    @staticmethod
    def hash_password(password: str) -> str:
        salt = bcrypt.gensalt(rounds=settings.password_bcrypt_rounds)
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

    @staticmethod
    def create_access_token(user_id: str, email: str, role: str) -> str:
        expires_at = datetime.utcnow() + timedelta(hours=settings.jwt_expiration_hours)
        payload = {
            "sub": str(user_id),
            "email": email,
            "role": role,
            "exp": expires_at,
            "iat": datetime.utcnow(),
        }
        token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        return token

    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        try:
            payload = jwt.decode(
                token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
            )
            return payload
        except JWTError:
            return None

    @staticmethod
    def register_user(
        db: Session,
        email: str,
        password: str,
        name: str = "",
        role: str = "Analyst",
        provider: str = "credentials",
    ) -> User:
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise ValueError("Email already registered")

        if role not in AuthService.VALID_ROLES:
            raise ValueError(f"Invalid role '{role}'")

        password_hash = AuthService.hash_password(password)

        user = User(
            email=email,
            password_hash=password_hash,
            name=name or None,
            role=role,
            provider=provider,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def find_or_create_google_user(
        db: Session, email: str, name: str = "", avatar: str = ""
    ) -> User:
        existing_user = db.query(User).filter(User.email == email).first()

        if existing_user:
            if existing_user.role == "Admin":
                raise ValueError("Admin accounts cannot use Google OAuth")
            return existing_user

        user = User(
            email=email,
            password_hash=None,
            name=name or None,
            avatar=avatar or None,
            role="Analyst",
            provider="google",
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        user = db.query(User).filter(User.email == email).first()

        if not user:
            return None

        if not user.password_hash:
            return None

        if not AuthService.verify_password(password, user.password_hash):
            return None

        return user

    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def generate_reset_token() -> str:
        return secrets.token_urlsafe(32)

    @staticmethod
    def create_password_reset_token(db: Session, email: str) -> Optional[str]:
        user = AuthService.get_user_by_email(db, email)

        if not user:
            return None

        reset_token = AuthService.generate_reset_token()
        expires_at = datetime.utcnow() + timedelta(hours=1)

        user.reset_token = reset_token
        user.reset_token_expires = expires_at

        db.commit()

        return reset_token

    @staticmethod
    def verify_reset_token(db: Session, token: str) -> Optional[User]:
        user = db.query(User).filter(User.reset_token == token).first()

        if not user:
            return None

        if not user.reset_token_expires or user.reset_token_expires < datetime.utcnow():
            return None

        return user

    @staticmethod
    def reset_password(db: Session, token: str, new_password: str) -> bool:
        user = AuthService.verify_reset_token(db, token)

        if not user:
            return False

        new_password_hash = AuthService.hash_password(new_password)

        user.password_hash = new_password_hash
        user.reset_token = None
        user.reset_token_expires = None

        db.commit()

        return True
