"""
Notification Service
"""



import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from backend.domain.models.notification import Notification
from backend.domain.models.user import User

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing user notifications"""
    
    def create_training_completion_notification(
        self,
        db: Session,
        user_id: UUID,
        training_job_id: UUID,
        model_type: str,
        status: str,
        failure_reason: Optional[str] = None
    ) -> Notification:
        """
        Create notification for training job completion or failure
        Requirement 32.1: Send notification when training completes
        Requirement 32.2: Send notification when training fails with reason
        Requirement 32.6: Store notifications in database
        
        Args:
            db: Database session
            user_id: User ID
            training_job_id: Training job ID
            model_type: Model type (KNN, Naive Bayes, etc.)
            status: Job status (completed, failed)
            failure_reason: Optional failure reason for failed jobs
            
        Returns:
            Created notification
        """
        try:
            # Create notification message
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
            
            # Create notification
            notification = Notification(
                id=uuid4(),
                user_id=user_id,
                title=title,
                message=message,
                notification_type=notification_type,
                related_entity_type="training_job",
                related_entity_id=training_job_id,
                is_read=False,
                created_at=datetime.utcnow()
            )
            
            db.add(notification)
            db.commit()
            db.refresh(notification)
            
            logger.info(
                f"Created notification {notification.id} for user {user_id}: "
                f"{notification_type}"
            )
            
            # Send email notification if enabled (Requirement 32.5)
            self._send_email_notification_if_enabled(
                db=db,
                user_id=user_id,
                notification=notification
            )
            
            return notification
            
        except Exception as e:
            logger.error(f"Error creating notification: {e}", exc_info=True)
            db.rollback()
            raise
    
    def _send_email_notification_if_enabled(
        self,
        db: Session,
        user_id: UUID,
        notification: Notification
    ):
        """
        Send email notification if user has enabled email notifications
        Requirement 32.5: Send email when email_notifications_enabled is true
        
        Args:
            db: Database session
            user_id: User ID
            notification: Notification object
        """
        try:
            # Get user
            user = db.query(User).filter(User.id == user_id).first()
            
            if not user:
                logger.warning(f"User {user_id} not found for email notification")
                return
            
            # Check if email notifications are enabled
            if not user.email_notifications_enabled:
                logger.debug(f"Email notifications disabled for user {user_id}")
                return
            
            # TODO: Implement actual email sending
            # This would integrate with an email service like SendGrid, AWS SES, etc.
            logger.info(
                f"Email notification would be sent to {user.email}: "
                f"{notification.title}"
            )
            
            # Placeholder for email sending logic:
            # email_service.send_email(
            #     to=user.email,
            #     subject=notification.title,
            #     body=notification.message
            # )
            
        except Exception as e:
            # Don't fail notification creation if email fails
            logger.error(f"Error sending email notification: {e}", exc_info=True)
    
    def get_user_notifications(
        self,
        db: Session,
        user_id: UUID,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Notification]:
        """
        Get notifications for a user
        Requirement 32.4: Display notification inbox with timestamps
        
        Args:
            db: Database session
            user_id: User ID
            unread_only: Only return unread notifications
            limit: Maximum number of notifications to return
            
        Returns:
            List of notifications
        """
        try:
            query = db.query(Notification).filter(
                Notification.user_id == user_id
            )
            
            if unread_only:
                query = query.filter(Notification.is_read == False)
            
            notifications = query.order_by(
                Notification.created_at.desc()
            ).limit(limit).all()
            
            logger.info(
                f"Retrieved {len(notifications)} notifications for user {user_id} "
                f"(unread_only={unread_only})"
            )
            
            return notifications
            
        except Exception as e:
            logger.error(f"Error retrieving notifications: {e}", exc_info=True)
            raise
    
    def get_unread_count(
        self,
        db: Session,
        user_id: UUID
    ) -> int:
        """
        Get count of unread notifications for a user
        Requirement 32.3: Display unread notification count
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Count of unread notifications
        """
        try:
            count = db.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.is_read == False
            ).count()
            
            logger.debug(f"User {user_id} has {count} unread notifications")
            
            return count
            
        except Exception as e:
            logger.error(f"Error getting unread count: {e}", exc_info=True)
            raise
    
    def mark_as_read(
        self,
        db: Session,
        notification_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Mark a notification as read
        Requirement 32.6: Mark notifications as read when viewed
        
        Args:
            db: Database session
            notification_id: Notification ID
            user_id: User ID (for access control)
            
        Returns:
            True if marked as read, False if not found
        """
        try:
            notification = db.query(Notification).filter(
                Notification.id == notification_id,
                Notification.user_id == user_id
            ).first()
            
            if not notification:
                logger.warning(
                    f"Notification {notification_id} not found for user {user_id}"
                )
                return False
            
            if not notification.is_read:
                notification.is_read = True
                notification.read_at = datetime.utcnow()
                db.commit()
                
                logger.info(
                    f"Marked notification {notification_id} as read for user {user_id}"
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}", exc_info=True)
            db.rollback()
            raise
    
    def mark_all_as_read(
        self,
        db: Session,
        user_id: UUID
    ) -> int:
        """
        Mark all notifications as read for a user
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Number of notifications marked as read
        """
        try:
            count = db.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.is_read == False
            ).update({
                "is_read": True,
                "read_at": datetime.utcnow()
            })
            
            db.commit()
            
            logger.info(f"Marked {count} notifications as read for user {user_id}")
            
            return count
            
        except Exception as e:
            logger.error(f"Error marking all notifications as read: {e}", exc_info=True)
            db.rollback()
            raise
