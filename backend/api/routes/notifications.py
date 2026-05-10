import logging
from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.api.dependencies import require_any_authenticated_user
from backend.domain.schemas.auth import UserResponse
from backend.infrastructure.database import get_db
from backend.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


class NotificationResponse(BaseModel):
    id: str
    title: str
    message: str
    notification_type: str
    is_read: bool
    created_at: str
    read_at: str | None = None


class UnreadCountResponse(BaseModel):
    unread_count: int


@router.get(
    "",
    response_model=List[NotificationResponse],
    responses={
        200: {"description": "List of notifications"},
    },
)
async def list_notifications(
    unread_only: bool = False,
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)] = None,
    db: Session = Depends(get_db),
):
    try:
        notification_service = NotificationService()

        notifications = notification_service.get_user_notifications(
            db=db, user_id=UUID(current_user.id), unread_only=unread_only, limit=50
        )

        logger.info(
            f"User {current_user.id} listed {len(notifications)} notifications "
            f"(unread_only={unread_only})"
        )

        return [
            NotificationResponse(
                id=str(notif.id),
                title=notif.title,
                message=notif.message,
                notification_type=notif.notification_type,
                is_read=notif.is_read,
                created_at=notif.created_at.isoformat(),
                read_at=notif.read_at.isoformat() if notif.read_at else None,
            )
            for notif in notifications
        ]

    except Exception as e:
        logger.error(f"Error listing notifications: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list notifications"
        )


@router.get(
    "/unread-count",
    response_model=UnreadCountResponse,
    responses={
        200: {"description": "Unread notification count"},
    },
)
async def get_unread_count(
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)] = None,
    db: Session = Depends(get_db),
):
    try:
        notification_service = NotificationService()

        count = notification_service.get_unread_count(db=db, user_id=UUID(current_user.id))

        return UnreadCountResponse(unread_count=count)

    except Exception as e:
        logger.error(f"Error getting unread count: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get unread count"
        )


@router.patch(
    "/{notification_id}/read",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "Notification marked as read"},
        404: {"description": "Notification not found"},
    },
)
async def mark_notification_as_read(
    notification_id: str,
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)] = None,
    db: Session = Depends(get_db),
):
    try:
        try:
            notif_uuid = UUID(notification_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid notification_id format: {notification_id}",
            )

        notification_service = NotificationService()

        success = notification_service.mark_as_read(
            db=db, notification_id=notif_uuid, user_id=UUID(current_user.id)
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Notification {notification_id} not found",
            )

        logger.info(f"User {current_user.id} marked notification {notification_id} as read")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notification as read",
        )


@router.patch(
    "/mark-all-read",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "All notifications marked as read"},
    },
)
async def mark_all_notifications_as_read(
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)] = None,
    db: Session = Depends(get_db),
):
    try:
        notification_service = NotificationService()

        count = notification_service.mark_all_as_read(db=db, user_id=UUID(current_user.id))

        logger.info(f"User {current_user.id} marked {count} notifications as read")

        return {"marked_count": count}

    except Exception as e:
        logger.error(f"Error marking all notifications as read: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark all notifications as read",
        )
