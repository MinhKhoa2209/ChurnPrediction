"""
WebSocket API Routes
"""

import asyncio
import json
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.domain.models.training_job import TrainingJob
from backend.domain.schemas.auth import UserResponse
from backend.services.training_service import TrainingService

router = APIRouter(prefix="/ws", tags=["WebSocket"])

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for training job updates"""
    
    def __init__(self):
        # Map of job_id -> list of WebSocket connections
        self.active_connections: dict[str, list[WebSocket]] = {}
    
    async def connect(self, job_id: str, websocket: WebSocket):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        
        if job_id not in self.active_connections:
            self.active_connections[job_id] = []
        
        self.active_connections[job_id].append(websocket)
        logger.info(f"WebSocket connected for job {job_id}. Total connections: {len(self.active_connections[job_id])}")
    
    def disconnect(self, job_id: str, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if job_id in self.active_connections:
            if websocket in self.active_connections[job_id]:
                self.active_connections[job_id].remove(websocket)
                logger.info(f"WebSocket disconnected for job {job_id}. Remaining connections: {len(self.active_connections[job_id])}")
            
            # Clean up empty lists
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]
    
    async def send_message(self, job_id: str, message: dict):
        """Send a message to all connections for a specific job"""
        if job_id not in self.active_connections:
            return
        
        # Send to all connections, removing any that fail
        disconnected = []
        for connection in self.active_connections[job_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send message to connection: {e}")
                disconnected.append(connection)
        
        # Remove disconnected connections
        for connection in disconnected:
            self.disconnect(job_id, connection)
    
    async def broadcast(self, message: dict):
        """Broadcast a message to all active connections"""
        for job_id in list(self.active_connections.keys()):
            await self.send_message(job_id, message)


# Global connection manager instance
manager = ConnectionManager()


async def get_current_user_from_token(token: str, db: Session) -> Optional[UserResponse]:
    """
    Authenticate user from JWT token for WebSocket connections
    
    Args:
        token: JWT token from query parameter
        db: Database session
        
    Returns:
        UserResponse if authenticated, None otherwise
    """
    try:
        from backend.api.dependencies import get_current_user
        from fastapi import Request
        
        # Create a mock request with the authorization header
        class MockRequest:
            def __init__(self, token: str):
                self.headers = {"authorization": f"Bearer {token}"}
        
        mock_request = MockRequest(token)
        
        # Use the existing get_current_user dependency
        # Note: This is a simplified approach. In production, you might want
        # to extract the token validation logic into a separate function
        from jose import JWTError, jwt
        from backend.config import settings
        
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        
        # Get user from database
        from backend.domain.models.user import User
        user = db.query(User).filter(User.id == UUID(user_id)).first()
        
        if user is None:
            return None
        
        return UserResponse.model_validate(user)
        
    except (JWTError, Exception) as e:
        logger.warning(f"WebSocket authentication failed: {e}")
        return None


@router.websocket("/training/{job_id}")
async def training_progress_websocket(
    websocket: WebSocket,
    job_id: str,
    token: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time training progress updates
    
    **Requirements**:
    - 17.1: Emit progress updates every 5 seconds during training
    - 17.2: Report current iteration, total iterations, estimated time remaining
    - 17.5: Use WebSocket connections for real-time progress updates
    - 17.6: Emit error messages with failure reason
    
    **Authentication**: Requires valid JWT token passed as query parameter
    
    **Usage**:
    ```javascript
    const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/training/${jobId}?token=${jwtToken}`);
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Progress:', data);
    };
    ```
    
    **Message Format**:
    ```json
    {
        "type": "progress",
        "job_id": "uuid",
        "status": "running",
        "progress_percent": 50,
        "current_iteration": 25,
        "total_iterations": 50,
        "estimated_seconds_remaining": 30,
        "metrics": {
            "loss": 0.45,
            "accuracy": 0.82
        }
    }
    ```
    
    Args:
        websocket: WebSocket connection
        job_id: Training job UUID
        token: JWT authentication token (query parameter)
        db: Database session
    """
    # Authenticate user
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing authentication token")
        return
    
    current_user = await get_current_user_from_token(token, db)
    if not current_user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid authentication token")
        return
    
    # Validate job_id format
    try:
        job_uuid = UUID(job_id)
    except ValueError:
        await websocket.close(code=status.WS_1003_UNSUPPORTED_DATA, reason="Invalid job_id format")
        return
    
    # Check if job exists and user has access
    training_job = TrainingService.get_training_job(db, job_uuid, current_user.id)
    if not training_job:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Training job not found or access denied")
        return
    
    # Connect to the manager
    await manager.connect(job_id, websocket)
    
    try:
        # Send initial status
        await websocket.send_json({
            "type": "connected",
            "job_id": job_id,
            "message": "Connected to training progress updates"
        })
        
        # Poll for updates every 5 seconds (Requirement 17.1)
        while True:
            # Refresh job status from database
            db.refresh(training_job)
            
            # Prepare progress message
            message = {
                "type": "progress",
                "job_id": job_id,
                "status": training_job.status,
                "progress_percent": training_job.progress_percent,
                "current_iteration": training_job.current_iteration,
                "total_iterations": training_job.total_iterations,
                "estimated_seconds_remaining": training_job.estimated_seconds_remaining,
            }
            
            # Add error message if failed (Requirement 17.6)
            if training_job.status == "failed" and training_job.error_message:
                message["error"] = training_job.error_message
            
            # Get latest metrics from training_progress table (Requirement 17.4)
            from backend.services.training_progress_service import TrainingProgressService
            latest_metrics = TrainingProgressService.get_latest_metrics(db, job_uuid)
            if latest_metrics:
                message["metrics"] = latest_metrics
            
            # Send update
            await websocket.send_json(message)
            
            # If job is completed or failed, send final message and close
            if training_job.status in ["completed", "failed"]:
                await websocket.send_json({
                    "type": "finished",
                    "job_id": job_id,
                    "status": training_job.status,
                    "message": "Training job finished"
                })
                break
            
            # Wait 5 seconds before next update (Requirement 17.1)
            await asyncio.sleep(5)
        
    except WebSocketDisconnect:
        logger.info(f"Client disconnected from training job {job_id}")
    except Exception as e:
        logger.error(f"Error in WebSocket connection for job {job_id}: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "job_id": job_id,
                "message": "Internal server error"
            })
        except:
            pass
    finally:
        manager.disconnect(job_id, websocket)
        try:
            await websocket.close()
        except:
            pass


async def emit_progress_update(job_id: str, progress_data: dict):
    """
    Helper function to emit progress updates to all connected clients
    Can be called from Celery tasks or other background processes
    
    Args:
        job_id: Training job UUID as string
        progress_data: Progress data dictionary
    """
    await manager.send_message(job_id, progress_data)
