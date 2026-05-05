"""
Authorization Utilities

This module defines the Role-Based Access Control (RBAC) authorization matrix
and provides utilities for checking permissions.
"""

from enum import Enum
from typing import Dict, List, Set


class UserRole(str, Enum):
    """
    User roles in the system
    """
    ADMIN = "Admin"
    DATA_SCIENTIST = "Data_Scientist"
    ANALYST = "Analyst"


class Operation(str, Enum):
    """
    Operations that can be performed in the system
    These map to API endpoints and business operations
    """
    # Dashboard operations
    VIEW_DASHBOARD = "view_dashboard"
    
    # Data operations
    UPLOAD_DATA = "upload_data"
    VIEW_DATA = "view_data"
    DELETE_DATA = "delete_data"
    
    # Model operations
    TRAIN_MODEL = "train_model"
    VIEW_MODEL = "view_model"
    DELETE_MODEL = "delete_model"
    ADJUST_THRESHOLD = "adjust_threshold"
    
    # Prediction operations
    CREATE_PREDICTION = "create_prediction"
    VIEW_PREDICTION = "view_prediction"
    BATCH_PREDICTION = "batch_prediction"
    
    # Report operations
    GENERATE_REPORT = "generate_report"
    VIEW_REPORT = "view_report"
    
    # User management operations
    MANAGE_USERS = "manage_users"
    VIEW_USERS = "view_users"
    
    # EDA operations
    VIEW_EDA = "view_eda"
    
    # Feature engineering operations
    FEATURE_ENGINEERING = "feature_engineering"


# Authorization Matrix
# Admin has full access to all operations
# Data_Scientist can upload data, train models, and create predictions
# Analyst can view dashboards and create predictions only
AUTHORIZATION_MATRIX: Dict[UserRole, Set[Operation]] = {
    UserRole.ADMIN: {
        # Admin has access to ALL operations
        Operation.VIEW_DASHBOARD,
        Operation.UPLOAD_DATA,
        Operation.VIEW_DATA,
        Operation.DELETE_DATA,
        Operation.TRAIN_MODEL,
        Operation.VIEW_MODEL,
        Operation.DELETE_MODEL,
        Operation.ADJUST_THRESHOLD,
        Operation.CREATE_PREDICTION,
        Operation.VIEW_PREDICTION,
        Operation.BATCH_PREDICTION,
        Operation.GENERATE_REPORT,
        Operation.VIEW_REPORT,
        Operation.MANAGE_USERS,
        Operation.VIEW_USERS,
        Operation.VIEW_EDA,
        Operation.FEATURE_ENGINEERING,
    },
    UserRole.DATA_SCIENTIST: {
        # Data_Scientist can upload data, train models, and create predictions
        Operation.VIEW_DASHBOARD,
        Operation.UPLOAD_DATA,
        Operation.VIEW_DATA,
        Operation.DELETE_DATA,  # Can delete their own data
        Operation.TRAIN_MODEL,
        Operation.VIEW_MODEL,
        Operation.DELETE_MODEL,  # Can delete their own models
        Operation.ADJUST_THRESHOLD,
        Operation.CREATE_PREDICTION,
        Operation.VIEW_PREDICTION,
        Operation.BATCH_PREDICTION,
        Operation.GENERATE_REPORT,
        Operation.VIEW_REPORT,
        Operation.VIEW_EDA,
        Operation.FEATURE_ENGINEERING,
    },
    UserRole.ANALYST: {
        # Analyst can view dashboards and create predictions only (read-only for models)
        Operation.VIEW_DASHBOARD,
        Operation.VIEW_DATA,  # Read-only access to data
        Operation.VIEW_MODEL,  # Read-only access to models
        Operation.CREATE_PREDICTION,
        Operation.VIEW_PREDICTION,
        Operation.BATCH_PREDICTION,
        Operation.GENERATE_REPORT,
        Operation.VIEW_REPORT,
        Operation.VIEW_EDA,  # Read-only EDA access
    },
}


def is_authorized(role: str, operation: Operation) -> bool:
    """
    Check if a user role is authorized to perform an operation
    
    Args:
        role: User's role (Admin, Data_Scientist, or Analyst)
        operation: Operation to check authorization for
        
    Returns:
        True if authorized, False otherwise
    """
    try:
        user_role = UserRole(role)
        return operation in AUTHORIZATION_MATRIX.get(user_role, set())
    except ValueError:
        # Invalid role
        return False


def get_allowed_operations(role: str) -> List[Operation]:
    """
    Get list of operations allowed for a role
    
    Args:
        role: User's role
        
    Returns:
        List of allowed operations
    """
    try:
        user_role = UserRole(role)
        return list(AUTHORIZATION_MATRIX.get(user_role, set()))
    except ValueError:
        return []


def check_authorization(role: str, operation: Operation) -> None:
    """
    Check authorization and raise exception if not authorized
    
    Args:
        role: User's role
        operation: Operation to check
        
    Raises:
        PermissionError: If user is not authorized
    """
    if not is_authorized(role, operation):
        raise PermissionError(
            f"User with role '{role}' is not authorized to perform operation '{operation.value}'"
        )


# Mapping of API endpoints to operations
# This helps in applying authorization checks at the route level
ENDPOINT_OPERATION_MAP: Dict[str, Operation] = {
    # Dashboard
    "/api/v1/dashboard/metrics": Operation.VIEW_DASHBOARD,
    "/api/v1/dashboard/churn-distribution": Operation.VIEW_DASHBOARD,
    "/api/v1/dashboard/monthly-trend": Operation.VIEW_DASHBOARD,
    
    # Datasets
    "/api/v1/datasets/upload": Operation.UPLOAD_DATA,
    "/api/v1/datasets": Operation.VIEW_DATA,
    "/api/v1/datasets/{dataset_id}": Operation.VIEW_DATA,
    
    # EDA
    "/api/v1/eda": Operation.VIEW_EDA,
    
    # Features
    "/api/v1/features": Operation.FEATURE_ENGINEERING,
    
    # Models
    "/api/v1/models/train": Operation.TRAIN_MODEL,
    "/api/v1/models/versions": Operation.VIEW_MODEL,
    "/api/v1/models/versions/{version_id}/threshold": Operation.ADJUST_THRESHOLD,
    
    # Predictions
    "/api/v1/predictions/single": Operation.CREATE_PREDICTION,
    "/api/v1/predictions/batch": Operation.BATCH_PREDICTION,
    "/api/v1/predictions": Operation.VIEW_PREDICTION,
    
    # Reports
    "/api/v1/reports/generate": Operation.GENERATE_REPORT,
    "/api/v1/reports": Operation.VIEW_REPORT,
    
    # Users (Admin only)
    "/api/v1/users": Operation.MANAGE_USERS,
}
