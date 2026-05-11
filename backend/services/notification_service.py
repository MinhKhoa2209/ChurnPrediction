import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from backend.domain.models.notification import Notification
from backend.domain.models.user import User

logger = logging.getLogger(__name__)


class NotificationService:
    def create_training_completion_notification(
        self,
        db: Session,
        user_id: UUID,
        training_job_id: UUID,
        model_type: str,
        status: str,
        failure_reason: Optional[str] = None,
    ) -> Notification:
        try:
            if status == "completed":
                title = "Training Job Completed"
                message = f"Your {model_type} model training has completed successfully."
                notification_type = "training_completed"
            elif status == "failed":
                title = "Training Job Failed"
                message = f"Your {model_type} model training has failed."
                if failure_reason:
                    message += f" Reason: {failure_reason}"
                notification_type = "training_failed"
            else:
                title = "Training Job Update"
                message = f"Your {model_type} model training status: {status}"
                notification_type = "training_update"

            notification = Notification(
                id=uuid4(),
                user_id=user_id,
                training_job_id=training_job_id,
                title=title,
                message=message,
                notification_type=notification_type,
                is_read=False,
                created_at=datetime.utcnow(),
            )

            db.add(notification)
            db.commit()
            db.refresh(notification)

            logger.info(
                f"Created notification {notification.id} for user {user_id}: "
                f"{notification_type}"
            )

            self._send_email_notification_if_enabled(
                db=db, user_id=user_id, notification=notification
            )

            return notification

        except Exception as e:
            logger.error(f"Error creating notification: {e}", exc_info=True)
            db.rollback()
            raise

    def create_dataset_notification(
        self,
        db: Session,
        user_id: UUID,
        dataset_id: UUID,
        filename: str,
        status: str,
        record_count: int = 0,
        failure_reason: Optional[str] = None,
    ) -> Notification:
        try:
            if status == "ready":
                title = "Dataset Processing Complete"
                message = f"Your dataset '{filename}' ({record_count} records) has been processed successfully."
                notification_type = "dataset_completed"
            elif status == "failed":
                title = "Dataset Processing Failed"
                message = f"Your dataset '{filename}' failed to process."
                if failure_reason:
                    message += f" Reason: {failure_reason}"
                notification_type = "dataset_failed"
            else:
                title = "Dataset Uploaded"
                message = f"Your dataset '{filename}' has been uploaded and is being processed."
                notification_type = "dataset_uploaded"

            notification = Notification(
                id=uuid4(),
                user_id=user_id,
                title=title,
                message=message,
                notification_type=notification_type,
                is_read=False,
                created_at=datetime.utcnow(),
            )

            db.add(notification)
            db.commit()
            db.refresh(notification)

            logger.info(
                f"Created dataset notification {notification.id} for user {user_id}: "
                f"{notification_type}"
            )

            return notification

        except Exception as e:
            logger.error(f"Error creating dataset notification: {e}", exc_info=True)
            db.rollback()
            raise

    def _send_email_notification_if_enabled(
        self, db: Session, user_id: UUID, notification: Notification
    ):
        try:
            user = db.query(User).filter(User.id == user_id).first()

            if not user:
                logger.warning(f"User {user_id} not found for email notification")
                return

            if not user.email_notifications_enabled:
                logger.debug(f"Email notifications disabled for user {user_id}")
                return

            logger.info(
                f"Email notification would be sent to {user.email}: " f"{notification.title}"
            )

        except Exception as e:
            logger.error(f"Error sending email notification: {e}", exc_info=True)

    def get_user_notifications(
        self, db: Session, user_id: UUID, unread_only: bool = False, limit: int = 50
    ) -> List[Notification]:
        try:
            query = db.query(Notification).filter(Notification.user_id == user_id)

            if unread_only:
                query = query.filter(Notification.is_read.is_(False))

            notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()

            logger.info(
                f"Retrieved {len(notifications)} notifications for user {user_id} "
                f"(unread_only={unread_only})"
            )

            return notifications

        except Exception as e:
            logger.error(f"Error retrieving notifications: {e}", exc_info=True)
            raise

    def get_unread_count(self, db: Session, user_id: UUID) -> int:
        try:
            count = (
                db.query(Notification)
                .filter(Notification.user_id == user_id, Notification.is_read.is_(False))
                .count()
            )

            logger.debug(f"User {user_id} has {count} unread notifications")

            return count

        except Exception as e:
            logger.error(f"Error getting unread count: {e}", exc_info=True)
            raise

    def mark_as_read(self, db: Session, notification_id: UUID, user_id: UUID) -> bool:
        try:
            notification = (
                db.query(Notification)
                .filter(Notification.id == notification_id, Notification.user_id == user_id)
                .first()
            )

            if not notification:
                logger.warning(f"Notification {notification_id} not found for user {user_id}")
                return False

            if not notification.is_read:
                notification.is_read = True
                notification.read_at = datetime.utcnow()
                db.commit()

                logger.info(f"Marked notification {notification_id} as read for user {user_id}")

            return True

        except Exception as e:
            logger.error(f"Error marking notification as read: {e}", exc_info=True)
            db.rollback()
            raise

    def mark_all_as_read(self, db: Session, user_id: UUID) -> int:
        try:
            count = (
                db.query(Notification)
                .filter(Notification.user_id == user_id, Notification.is_read.is_(False))
                .update({"is_read": True, "read_at": datetime.utcnow()})
            )

            db.commit()

            logger.info(f"Marked {count} notifications as read for user {user_id}")

            return count

        except Exception as e:
            logger.error(f"Error marking all notifications as read: {e}", exc_info=True)
            db.rollback()
            raise
