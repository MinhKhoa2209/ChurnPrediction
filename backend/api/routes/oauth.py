"""
OAuth Authentication Routes

Endpoints for OAuth 2.0 authentication with external providers:
- GET /api/v1/oauth/{provider}/login - Initiate OAuth flow
- GET /api/v1/oauth/{provider}/callback - Handle OAuth callback
- GET /api/v1/oauth/providers - List available OAuth providers
"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from backend.config import settings
from backend.domain.schemas.auth import AuthResponse, UserResponse
from backend.infrastructure.database import get_db_session as get_db
from backend.services.auth_service import AuthService
from backend.services.oauth_service import oauth_service
from backend.services.audit_service import AuditService

router = APIRouter(prefix="/oauth", tags=["OAuth Authentication"])


@router.get(
    "/providers",
    summary="List available OAuth providers",
    description="Get list of configured OAuth providers (Google, GitHub, Microsoft)"
)
async def list_oauth_providers():
    """
    List available OAuth providers
    
    Returns:
        Dictionary with available providers and their configuration status
    """
    return {
        "providers": {
            "google": {
                "enabled": bool(settings.google_client_id and settings.google_client_secret),
                "name": "Google",
                "icon": "google"
            },
            "github": {
                "enabled": bool(settings.github_client_id and settings.github_client_secret),
                "name": "GitHub",
                "icon": "github"
            },
            "microsoft": {
                "enabled": bool(settings.microsoft_client_id and settings.microsoft_client_secret),
                "name": "Microsoft",
                "icon": "microsoft"
            }
        }
    }


@router.get(
    "/{provider}/login",
    summary="Initiate OAuth login flow",
    description="""
    Redirect user to OAuth provider's login page.
    
    **Supported Providers:**
    - google: Google OAuth 2.0
    - github: GitHub OAuth
    - microsoft: Microsoft OAuth 2.0
    
    **Flow:**
    1. User clicks "Sign in with Google" button
    2. Frontend redirects to this endpoint
    3. Backend redirects to OAuth provider
    4. User authenticates with provider
    5. Provider redirects back to callback endpoint
    """
)
async def oauth_login(
    provider: str,
    request: Request,
    redirect_uri: str = None
):
    """
    Initiate OAuth login flow
    
    Args:
        provider: OAuth provider name (google, github, microsoft)
        request: HTTP request object
        redirect_uri: Optional custom redirect URI
        
    Returns:
        Redirect to OAuth provider's authorization page
        
    Raises:
        HTTPException: If provider is not supported or not configured
    """
    # Validate provider
    if provider not in ['google', 'github', 'microsoft']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported OAuth provider: {provider}"
        )
    
    # Check if provider is configured
    client = getattr(oauth_service.oauth, provider, None)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"OAuth provider '{provider}' is not configured. Please contact administrator."
        )
    
    # Use backend callback URL (Google will redirect here, not to frontend)
    if not redirect_uri:
        # Redirect to backend callback endpoint
        redirect_uri = f"http://localhost:8000/api/v1/oauth/{provider}/callback"
    
    # Redirect to OAuth provider
    return await client.authorize_redirect(request, redirect_uri)


@router.get(
    "/{provider}/callback",
    summary="Handle OAuth callback",
    description="""
    Handle OAuth provider callback after user authentication.
    
    **Flow:**
    1. OAuth provider redirects here with authorization code
    2. Backend exchanges code for access token
    3. Backend fetches user info from provider
    4. Backend creates or updates user in database
    5. Backend generates JWT token
    6. Backend redirects to frontend with token
    """
)
async def oauth_callback(
    provider: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle OAuth callback and create/login user
    
    Args:
        provider: OAuth provider name
        request: HTTP request with OAuth callback parameters
        db: Database session
        
    Returns:
        Redirect to frontend with JWT token
        
    Raises:
        HTTPException: If OAuth flow fails or user creation fails
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"OAuth callback received for provider: {provider}")
        logger.info(f"Request URL: {request.url}")
        logger.info(f"Query params: {request.query_params}")
        
        # Get OAuth client
        client = getattr(oauth_service.oauth, provider, None)
        if not client:
            logger.error(f"OAuth provider '{provider}' not configured")
            # Redirect to frontend with error
            return RedirectResponse(
                url=f"{settings.oauth_redirect_url}?error=provider_not_configured",
                status_code=status.HTTP_302_FOUND
            )
        
        # Exchange authorization code for access token
        logger.info("Exchanging authorization code for access token...")
        token = await client.authorize_access_token(request)
        logger.info("Access token received successfully")
        
        # Get user info from OAuth provider
        logger.info("Fetching user info from OAuth provider...")
        user_info = await oauth_service.get_user_info(provider, token)
        logger.info(f"User info received: {user_info.get('email')}")
        
        if not user_info.get('email'):
            logger.error("No email provided by OAuth provider")
            # Redirect to frontend with error
            return RedirectResponse(
                url=f"{settings.oauth_redirect_url}?error=no_email",
                status_code=status.HTTP_302_FOUND
            )
        
        # Get or create user in database
        logger.info(f"Getting or creating user: {user_info['email']}")
        user = oauth_service.get_or_create_oauth_user(
            db=db,
            email=user_info['email'],
            name=user_info.get('name'),
            avatar=user_info.get('picture'),
            email_verified=user_info.get('email_verified', False),
            provider=provider,
            default_role="Analyst"  # Default role for OAuth users
        )
        logger.info(f"User created/retrieved: {user.id}")
        
        # Log successful OAuth authentication
        AuditService.log_authentication_attempt(
            db=db,
            user_id=user.id,
            action=f"oauth_login_{provider}",
            request=request,
            success=True
        )
        
        # Generate JWT token
        access_token = AuthService.create_access_token(
            user_id=str(user.id),
            email=user.email,
            role=user.role
        )
        logger.info("JWT token generated successfully")
        
        # Redirect to frontend with token
        frontend_url = f"{settings.oauth_redirect_url}?token={access_token}"
        logger.info(f"Redirecting to frontend: {frontend_url}")
        return RedirectResponse(url=frontend_url, status_code=status.HTTP_302_FOUND)
        
    except HTTPException as he:
        logger.error(f"HTTPException during OAuth callback: {he.detail}")
        # Redirect to frontend with error
        return RedirectResponse(
            url=f"{settings.oauth_redirect_url}?error=auth_failed",
            status_code=status.HTTP_302_FOUND
        )
    except Exception as e:
        logger.error(f"Exception during OAuth callback: {str(e)}", exc_info=True)
        # Log failed OAuth authentication
        AuditService.log_authentication_attempt(
            db=db,
            user_id=None,
            action=f"oauth_login_{provider}_failed",
            request=request,
            success=False
        )
        
        # Redirect to frontend with error
        return RedirectResponse(
            url=f"{settings.oauth_redirect_url}?error=auth_failed",
            status_code=status.HTTP_302_FOUND
        )
