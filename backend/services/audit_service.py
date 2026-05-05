"""
Audit Service
"""

from typing import Optional
from uuid import UUID

from fastapi import Request
from sqlalchemy.orm import Session

from backend.domain.models.audit_log import AuditLog


class AuditService:
    """Service for audit logging operations"""

    @staticmethod
    def log_authentication_attempt(
        db: Session,
        user_id: Optional[UUID],
        action: str,
        request: Request,
        success: bool = False
    ) -> AuditLog:
        """
        Log authentication attempt for security audit
        Requirement 1.3: Log failed authentication attempts for security audit
        Requirement 23.6: Log all data access operations with user ID and timestamp
        
        Args:
            db: Database session
            user_id: User ID (None for failed login with invalid email)
            action: Action performed (e.g., "login_success", "login_failed")
            request: HTTP request object
            success: Whether the authentication was successful
            
        Returns:
            Created AuditLog object
        """
        # Extract client information
        ip_address = AuditService._get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "")
        
        # Create audit log entry
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type="authentication",
            resource_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)
        
        return audit_log

    @staticmethod
    def log_data_access(
        db: Session,
        user_id: UUID,
        action: str,
        resource_type: str,
        resource_id: Optional[UUID],
        request: Request
    ) -> AuditLog:
        """
        Log data access operation for audit trail
        Requirement 23.6: Log all data access operations with user ID and timestamp
        
        Args:
            db: Database session
            user_id: User ID performing the action
            action: Action performed (e.g., "dataset_upload", "prediction_create")
            resource_type: Type of resource accessed
            resource_id: ID of the resource accessed
            request: HTTP request object
            
        Returns:
            Created AuditLog object
        """
        # Extract client information
        ip_address = AuditService._get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "")
        
        # Create audit log entry
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)
        
        return audit_log

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        """
        Extract client IP address from request
        Handles X-Forwarded-For header for proxied requests
        
        Args:
            request: HTTP request object
            
        Returns:
            Client IP address as string
        """
        # Try to get real IP from X-Forwarded-For header (for proxies/load balancers)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For can contain multiple IPs, take the first one
            return forwarded_for.split(",")[0].strip()
        
        # Fall back to direct client IP
        return request.client.host if request.client else "unknown"
