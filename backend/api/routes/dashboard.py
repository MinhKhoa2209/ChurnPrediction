"""
Dashboard API Routes

This module provides REST API endpoints for dashboard analytics with RBAC.
"""

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

# Cache TTL: 5 minutes (300 seconds)
DASHBOARD_CACHE_TTL = 300


@router.get(
    "/metrics",
    responses={
        200: {"description": "Dashboard metrics"},
        500: {"description": "Internal server error"},
    }
)
async def get_dashboard_metrics(
    # Requirement 19.4: All authenticated users can view dashboard
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)],
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis_client)
):
    """
    Get dashboard metrics
    
    **Authorization**: Requires any authenticated user
    
    **RBAC Matrix**:
    - Admin: ✓ Allowed
    - Data_Scientist: ✓ Allowed
    - Analyst: ✓ Allowed
    
    **Requirements**:
    - 2.1: Display total customer count, churn rate, at-risk count
    - 2.2: Compute metrics within 500ms
    
    **Caching**:
    - Metrics are cached in Redis with 5-minute TTL
    - Cache key: dashboard:metrics:{user_id}
    - Cache is invalidated on new predictions or data uploads
    
    Args:
        current_user: Current authenticated user
        db: Database session
        redis_client: Redis client for caching
        
    Returns:
        Dashboard metrics:
        - total_customers: Total customer count
        - churn_rate: Churn rate percentage
        - at_risk_count: Count of customers with probability > 70%
        - churned_count: Count of churned customers
        - retained_count: Count of retained customers
    """
    start_time = time.time()
    
    try:
        # Admin can see all metrics, others see their own
        user_id = None if current_user.role == "Admin" else UUID(current_user.id)
        
        # Create cache key
        cache_key = f"dashboard:metrics:{user_id or 'all'}"
        
        # Try to get from cache
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
        
        # Cache miss - compute metrics
        dashboard_service = DashboardService()
        metrics = dashboard_service.compute_dashboard_metrics(
            db=db,
            user_id=user_id
        )
        
        # Store in cache
        try:
            redis_client.setex(
                cache_key,
                DASHBOARD_CACHE_TTL,
                json.dumps(metrics)
            )
        except Exception as cache_error:
            logger.warning(f"Cache write error: {cache_error}")
        
        # Check if we met the 500ms performance requirement (Requirement 2.2)
        elapsed_time = time.time() - start_time
        if elapsed_time > 0.5:
            logger.warning(
                f"Dashboard metrics computation took {elapsed_time:.3f}s, "
                f"exceeding 500ms target"
            )
        
        logger.info(
            f"User {current_user.id} retrieved dashboard metrics in {elapsed_time:.3f}s"
        )
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error retrieving dashboard metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard metrics"
        )


@router.get(
    "/churn-distribution",
    responses={
        200: {"description": "Churn distribution data"},
        500: {"description": "Internal server error"},
    }
)
async def get_churn_distribution(
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)],
    db: Session = Depends(get_db)
):
    """
    Get churn distribution data
    
    **Authorization**: Requires any authenticated user
    
    **RBAC Matrix**:
    - Admin: ✓ Allowed
    - Data_Scientist: ✓ Allowed
    - Analyst: ✓ Allowed
    
    **Requirements**:
    - 2.3: Render churn distribution chart showing churned vs retained
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Churn distribution:
        - churned: Count of churned customers
        - retained: Count of retained customers
    """
    try:
        dashboard_service = DashboardService()
        
        # Admin can see all data, others see their own
        user_id = None if current_user.role == "Admin" else UUID(current_user.id)
        
        distribution = dashboard_service.get_churn_distribution(
            db=db,
            user_id=user_id
        )
        
        logger.info(f"User {current_user.id} retrieved churn distribution")
        
        return distribution
        
    except Exception as e:
        logger.error(f"Error retrieving churn distribution: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve churn distribution"
        )


@router.get(
    "/monthly-trend",
    responses={
        200: {"description": "Monthly churn trend data"},
        500: {"description": "Internal server error"},
    }
)
async def get_monthly_trend(
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)],
    db: Session = Depends(get_db),
    months: int = 12
):
    """
    Get monthly churn trend
    
    **Authorization**: Requires any authenticated user
    
    **RBAC Matrix**:
    - Admin: ✓ Allowed
    - Data_Scientist: ✓ Allowed
    - Analyst: ✓ Allowed
    
    **Requirements**:
    - 2.4: Render monthly churn trend line chart for past 12 months
    
    Args:
        current_user: Current authenticated user
        db: Database session
        months: Number of months to include (default: 12)
        
    Returns:
        List of monthly trend data:
        - month: Month label (e.g., "2024-01")
        - churn_count: Number of churned customers
        - total_count: Total number of customers
        - churn_rate: Churn rate percentage
    """
    try:
        dashboard_service = DashboardService()
        
        # Admin can see all data, others see their own
        user_id = None if current_user.role == "Admin" else UUID(current_user.id)
        
        trend_data = dashboard_service.get_monthly_churn_trend(
            db=db,
            user_id=user_id,
            months=months
        )
        
        logger.info(
            f"User {current_user.id} retrieved monthly churn trend "
            f"({len(trend_data)} months)"
        )
        
        return trend_data
        
    except Exception as e:
        logger.error(f"Error retrieving monthly churn trend: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve monthly churn trend"
        )
