import json
import logging
import time
from typing import Annotated
from uuid import UUID

import redis
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.api.dependencies import require_any_authenticated_user
from backend.api.middleware import get_redis_client
from backend.domain.schemas.auth import UserResponse
from backend.infrastructure.database import get_db
from backend.services.dashboard_service import DashboardService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


DASHBOARD_CACHE_TTL = 300


@router.get(
    "/metrics",
    responses={
        200: {"description": "Dashboard metrics"},
        500: {"description": "Internal server error"},
    },
)
async def get_dashboard_metrics(
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)],
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis_client),
):
    start_time = time.time()

    try:
        user_id = None if current_user.role == "Admin" else UUID(current_user.id)
        scope_key = str(user_id) if user_id else "shared"
        cache_key = f"dashboard:metrics:v2:{scope_key}"

        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                metrics = json.loads(cached_data)
                elapsed_time = time.time() - start_time
                logger.info(
                    f"User {current_user.id} retrieved dashboard metrics from cache "
                    f"in {elapsed_time:.3f}s"
                )
                return metrics
        except Exception as cache_error:
            logger.warning(f"Cache read error: {cache_error}")

        dashboard_service = DashboardService()
        metrics = dashboard_service.compute_dashboard_metrics(db=db, user_id=user_id)

        try:
            redis_client.setex(cache_key, DASHBOARD_CACHE_TTL, json.dumps(metrics))
        except Exception as cache_error:
            logger.warning(f"Cache write error: {cache_error}")

        elapsed_time = time.time() - start_time
        if elapsed_time > 0.5:
            logger.warning(
                f"Dashboard metrics computation took {elapsed_time:.3f}s, "
                f"exceeding 500ms target"
            )

        logger.info(f"User {current_user.id} retrieved dashboard metrics in {elapsed_time:.3f}s")

        return metrics

    except Exception as e:
        logger.error(f"Error retrieving dashboard metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard metrics",
        )


@router.get(
    "/churn-distribution",
    responses={
        200: {"description": "Churn distribution data"},
        500: {"description": "Internal server error"},
    },
)
async def get_churn_distribution(
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)],
    db: Session = Depends(get_db),
):
    try:
        dashboard_service = DashboardService()

        user_id = None if current_user.role == "Admin" else UUID(current_user.id)

        distribution = dashboard_service.get_churn_distribution(db=db, user_id=user_id)

        logger.info(f"User {current_user.id} retrieved churn distribution")

        return distribution

    except Exception as e:
        logger.error(f"Error retrieving churn distribution: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve churn distribution",
        )


@router.get(
    "/monthly-trend",
    responses={
        200: {"description": "Monthly churn trend data"},
        500: {"description": "Internal server error"},
    },
)
async def get_monthly_trend(
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)],
    db: Session = Depends(get_db),
    months: int = 12,
):
    try:
        dashboard_service = DashboardService()

        user_id = None if current_user.role == "Admin" else UUID(current_user.id)

        trend_data = dashboard_service.get_monthly_churn_trend(
            db=db, user_id=user_id, months=months
        )

        logger.info(
            f"User {current_user.id} retrieved monthly churn trend " f"({len(trend_data)} months)"
        )

        return trend_data

    except Exception as e:
        logger.error(f"Error retrieving monthly churn trend: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve monthly churn trend",
        )
