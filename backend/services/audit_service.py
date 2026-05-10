from typing import Optional
from uuid import UUID

from fastapi import Request
from sqlalchemy.orm import Session

from backend.domain.models.audit_log import AuditLog


class AuditService:
    @staticmethod
    def log_authentication_attempt(
        db: Session, user_id: Optional[UUID], action: str, request: Request, success: bool = False
    ) -> AuditLog:
        ip_address = AuditService._get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "")

        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type="authentication",
            resource_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
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
        request: Request,
    ) -> AuditLog:
        ip_address = AuditService._get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "")

        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)

        return audit_log

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        return request.client.host if request.client else "unknown"
