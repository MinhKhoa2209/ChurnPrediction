from typing import Optional, Dict, Any
from authlib.integrations.starlette_client import OAuth
from sqlalchemy.orm import Session

from backend.config import settings
from backend.domain.models.user import User
from backend.services.auth_service import AuthService


class OAuthService:
    """Service for OAuth 2.0 authentication operations"""

    def __init__(self):
        """Initialize OAuth client with configured providers"""
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
        
        # Configure GitHub OAuth
        if settings.github_client_id and settings.github_client_secret:
            self.oauth.register(
                name='github',
                client_id=settings.github_client_id,
                client_secret=settings.github_client_secret,
                access_token_url='https://github.com/login/oauth/access_token',
                access_token_params=None,
                authorize_url='https://github.com/login/oauth/authorize',
                authorize_params=None,
                api_base_url='https://api.github.com/',
                client_kwargs={'scope': 'user:email'},
            )
        
        # Configure Microsoft OAuth
        if settings.microsoft_client_id and settings.microsoft_client_secret:
            self.oauth.register(
                name='microsoft',
                client_id=settings.microsoft_client_id,
                client_secret=settings.microsoft_client_secret,
                server_metadata_url='https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration',
                client_kwargs={
                    'scope': 'openid email profile',
                }
            )

    async def get_authorization_url(self, provider: str, redirect_uri: str) -> str:
        """
        Get OAuth authorization URL for a provider
        
        Args:
            provider: OAuth provider name (google, github, microsoft)
            redirect_uri: Callback URL after authentication
            
        Returns:
            Authorization URL to redirect user to
            
        Raises:
            ValueError: If provider is not configured
        """
        if provider not in ['google', 'github', 'microsoft']:
            raise ValueError(f"Unsupported OAuth provider: {provider}")
        
        client = getattr(self.oauth, provider, None)
        if not client:
            raise ValueError(f"OAuth provider '{provider}' is not configured")
        
        # Generate authorization URL
        return await client.authorize_redirect_url(redirect_uri)

    async def get_user_info(self, provider: str, token: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get user information from OAuth provider
        
        Args:
            provider: OAuth provider name
            token: OAuth token response
            
        Returns:
            User information dictionary with email, name, picture
        """
        client = getattr(self.oauth, provider)
        
        if provider == 'google':
            # Google returns user info in the token response
            user_info = token.get('userinfo', {})
            return {
                'email': user_info.get('email'),
                'name': user_info.get('name'),
                'picture': user_info.get('picture'),
                'email_verified': user_info.get('email_verified', False),
            }
        
        elif provider == 'github':
            # GitHub requires separate API call for user info
            resp = await client.get('user', token=token)
            user_data = resp.json()
            
            # Get primary email
            email_resp = await client.get('user/emails', token=token)
            emails = email_resp.json()
            primary_email = next(
                (e['email'] for e in emails if e['primary']),
                user_data.get('email')
            )
            
            return {
                'email': primary_email,
                'name': user_data.get('name') or user_data.get('login'),
                'picture': user_data.get('avatar_url'),
                'email_verified': True,  # GitHub emails are verified
            }
        
        elif provider == 'microsoft':
            # Microsoft returns user info in the token response
            user_info = token.get('userinfo', {})
            return {
                'email': user_info.get('email') or user_info.get('preferred_username'),
                'name': user_info.get('name'),
                'picture': None,  # Microsoft doesn't provide picture in basic scope
                'email_verified': True,
            }
        
        return {}

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
        """
        Get existing user by email or create new user from OAuth data
        
        Args:
            db: Database session
            email: User's email from OAuth provider
            name: User's full name (optional)
            avatar: User's avatar URL (optional)
            email_verified: Whether email is verified by OAuth provider
            provider: OAuth provider name (google, github, microsoft)
            default_role: Default role for new users (default: Analyst)
            
        Returns:
            User object (existing or newly created)
            
        Raises:
            ValueError: If email is invalid or role is invalid
        """
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
        valid_roles = ["Admin", "Data_Scientist", "Analyst"]
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
