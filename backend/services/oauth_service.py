from typing import Any, Dict, Optional

from authlib.integrations.starlette_client import OAuth
from sqlalchemy.orm import Session

from backend.config import settings
from backend.domain.models.user import User
from backend.services.auth_service import AuthService


class OAuthService:
    """Service for Google OAuth 2.0 authentication operations"""

    def __init__(self):
        """Initialize OAuth client with Google provider"""
        self.oauth = OAuth()
        
        # Configure Google OAuth
        if settings.google_client_id and settings.google_client_secret:
            self.oauth.register(
                name='google',
                client_id=settings.google_client_id,
                client_secret=settings.google_client_secret,
                server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
                client_kwargs={
                    'scope': 'openid email profile',
                    'prompt': 'select_account',  # Always show account picker
                }
            )

    async def get_authorization_url(self, provider: str, redirect_uri: str) -> str:
        if provider != 'google':
            raise ValueError(f"Unsupported OAuth provider: {provider}")
        
        client = getattr(self.oauth, provider, None)
        if not client:
            raise ValueError(f"OAuth provider '{provider}' is not configured")
        
        # Generate authorization URL
        return await client.authorize_redirect_url(redirect_uri)

    async def get_user_info(self, provider: str, token: Dict[str, Any]) -> Dict[str, Any]:
        if provider != 'google':
            raise ValueError(f"Unsupported OAuth provider: {provider}")
        
        user_info = token.get('userinfo', {})
        return {
            'email': user_info.get('email'),
            'name': user_info.get('name'),
            'picture': user_info.get('picture'),
            'email_verified': user_info.get('email_verified', False),
        }

    @staticmethod
    def get_or_create_oauth_user(
        db: Session,
        email: str,
        name: Optional[str] = None,
        avatar: Optional[str] = None,
        email_verified: bool = False,
        provider: str = "google",
        default_role: str = "Analyst"
    ) -> User:
        # Check if user already exists
        existing_user = AuthService.get_user_by_email(db, email)
        
        if existing_user:
            # Update user info from OAuth if not set
            updated = False
            
            if name and not existing_user.name:
                existing_user.name = name
                updated = True
            
            if avatar and not existing_user.avatar:
                existing_user.avatar = avatar
                updated = True
            
            if email_verified and not existing_user.email_verified:
                existing_user.email_verified = True
                updated = True
            
            if provider and existing_user.provider == "credentials":
                existing_user.provider = provider
                updated = True
            
            if updated:
                db.commit()
                db.refresh(existing_user)
            
            return existing_user
        
        # Create new user with OAuth data
        # Generate a random password (user won't use it, OAuth only)
        import secrets
        random_password = secrets.token_urlsafe(32)
        
        # Validate role
        valid_roles = ["Admin", "Analyst"]
        if default_role not in valid_roles:
            default_role = "Analyst"
        
        # Create user
        user = AuthService.register_user(
            db=db,
            email=email,
            password=random_password,
            name=name,
            role=default_role
        )
        
        # Update additional OAuth fields
        user.email_verified = email_verified
        user.provider = provider
        if avatar:
            user.avatar = avatar
        
        db.commit()
        db.refresh(user)
        
        return user


# Global OAuth service instance
oauth_service = OAuthService()
