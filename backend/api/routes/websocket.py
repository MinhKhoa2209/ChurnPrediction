import asyncio
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.domain.schemas.auth import UserResponse
from backend.services.training_service import TrainingService

router = APIRouter(prefix="/ws", tags=["WebSocket"])

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, job_id: str, websocket: WebSocket):
        await websocket.accept()

        if job_id not in self.active_connections:
            self.active_connections[job_id] = []

        self.active_connections[job_id].append(websocket)
        logger.info(
            f"WebSocket connected for job {job_id}. Total connections: {len(self.active_connections[job_id])}"
        )

    def disconnect(self, job_id: str, websocket: WebSocket):
        if job_id in self.active_connections:
            if websocket in self.active_connections[job_id]:
                self.active_connections[job_id].remove(websocket)
                logger.info(
                    f"WebSocket disconnected for job {job_id}. Remaining connections: {len(self.active_connections[job_id])}"
                )

            if not self.active_connections[job_id]:
                del self.active_connections[job_id]

    async def send_message(self, job_id: str, message: dict):
        if job_id not in self.active_connections:
            return

        disconnected = []
        for connection in self.active_connections[job_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send message to connection: {e}")
                disconnected.append(connection)

        for connection in disconnected:
            self.disconnect(job_id, connection)

    async def broadcast(self, message: dict):
        for job_id in list(self.active_connections.keys()):
            await self.send_message(job_id, message)


manager = ConnectionManager()


async def get_current_user_from_token(token: str, db: Session) -> Optional[UserResponse]:
    try:
        from jose import JWTError, jwt

        from backend.config import settings

        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])

        user_id: str = payload.get("sub")
        if user_id is None:
            return None

        from backend.domain.models.user import User

        user = db.query(User).filter(User.id == UUID(user_id)).first()

        if user is None:
            return None

        user_dict = {
            "id": str(user.id),
            "email": user.email,
            "role": user.role,
            "created_at": user.created_at,
            "email_verified": user.email_verified,
            "email_notifications_enabled": user.email_notifications_enabled,
        }

        return UserResponse.model_validate(user_dict)

    except (JWTError, Exception) as e:
        logger.warning(f"WebSocket authentication failed: {e}")
        return None


@router.websocket("/training/{job_id}")
async def training_progress_websocket(
    websocket: WebSocket, job_id: str, token: Optional[str] = None, db: Session = Depends(get_db)
):
    if not token:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION, reason="Missing authentication token"
        )
        return

    current_user = await get_current_user_from_token(token, db)
    if not current_user:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION, reason="Invalid authentication token"
        )
        return

    try:
        job_uuid = UUID(job_id)
    except ValueError:
        await websocket.close(code=status.WS_1003_UNSUPPORTED_DATA, reason="Invalid job_id format")
        return

    training_job = TrainingService.get_training_job(db, job_uuid, current_user.id)
    if not training_job:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION, reason="Training job not found or access denied"
        )
        return

    await manager.connect(job_id, websocket)

    try:
        await websocket.send_json(
            {
                "type": "connected",
                "job_id": job_id,
                "message": "Connected to training progress updates",
            }
        )

        while True:
            db.refresh(training_job)

            message = {
                "type": "progress",
                "job_id": job_id,
                "status": training_job.status,
                "progress_percent": training_job.progress_percent,
                "current_iteration": training_job.current_iteration,
                "total_iterations": training_job.total_iterations,
                "estimated_seconds_remaining": training_job.estimated_seconds_remaining,
            }

            if training_job.status == "failed" and training_job.error_message:
                message["error"] = training_job.error_message

            from backend.services.training_progress_service import TrainingProgressService

            latest_metrics = TrainingProgressService.get_latest_metrics(db, job_uuid)
            if latest_metrics:
                message["metrics"] = latest_metrics

            await websocket.send_json(message)

            if training_job.status in ["completed", "failed"]:
                await websocket.send_json(
                    {
                        "type": "finished",
                        "job_id": job_id,
                        "status": training_job.status,
                        "message": "Training job finished",
                    }
                )
                break

            await asyncio.sleep(5)

    except WebSocketDisconnect:
        logger.info(f"Client disconnected from training job {job_id}")
    except Exception as e:
        logger.error(f"Error in WebSocket connection for job {job_id}: {e}", exc_info=True)
        try:
            await websocket.send_json(
                {"type": "error", "job_id": job_id, "message": "Internal server error"}
            )
        except Exception:
            pass
    finally:
        manager.disconnect(job_id, websocket)
        try:
            await websocket.close()
        except Exception:
            pass


async def emit_progress_update(job_id: str, progress_data: dict):
    await manager.send_message(job_id, progress_data)
