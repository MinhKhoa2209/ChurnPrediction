from enum import Enum
from typing import Dict, List, Set


class UserRole(str, Enum):
    ADMIN = "Admin"
    ANALYST = "Analyst"


class Operation(str, Enum):
    VIEW_DASHBOARD = "view_dashboard"
    UPLOAD_DATA = "upload_data"
    VIEW_DATA = "view_data"
    DELETE_DATA = "delete_data"
    TRAIN_MODEL = "train_model"
    VIEW_MODEL = "view_model"
    DELETE_MODEL = "delete_model"
    ADJUST_THRESHOLD = "adjust_threshold"
    CREATE_PREDICTION = "create_prediction"
    VIEW_PREDICTION = "view_prediction"
    BATCH_PREDICTION = "batch_prediction"
    GENERATE_REPORT = "generate_report"
    VIEW_REPORT = "view_report"
    MANAGE_USERS = "manage_users"
    VIEW_USERS = "view_users"
    VIEW_EDA = "view_eda"
    FEATURE_ENGINEERING = "feature_engineering"


AUTHORIZATION_MATRIX: Dict[UserRole, Set[Operation]] = {
    UserRole.ADMIN: {
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
    UserRole.ANALYST: {
        Operation.VIEW_DASHBOARD,
        Operation.VIEW_DATA,
        Operation.VIEW_MODEL,
        Operation.CREATE_PREDICTION,
        Operation.VIEW_PREDICTION,
        Operation.BATCH_PREDICTION,
        Operation.GENERATE_REPORT,
        Operation.VIEW_REPORT,
        Operation.VIEW_EDA,
    },
}


def is_authorized(role: str, operation: Operation) -> bool:
    try:
        user_role = UserRole(role)
        return operation in AUTHORIZATION_MATRIX.get(user_role, set())
    except ValueError:
        return False


def get_allowed_operations(role: str) -> List[Operation]:
    try:
        user_role = UserRole(role)
        return list(AUTHORIZATION_MATRIX.get(user_role, set()))
    except ValueError:
        return []


def check_authorization(role: str, operation: Operation) -> None:
    if not is_authorized(role, operation):
        raise PermissionError(
            f"User with role '{role}' is not authorized to perform operation '{operation.value}'"
        )


ENDPOINT_OPERATION_MAP: Dict[str, Operation] = {
    "/api/v1/dashboard/metrics": Operation.VIEW_DASHBOARD,
    "/api/v1/dashboard/churn-distribution": Operation.VIEW_DASHBOARD,
    "/api/v1/dashboard/monthly-trend": Operation.VIEW_DASHBOARD,
    "/api/v1/datasets/upload": Operation.UPLOAD_DATA,
    "/api/v1/datasets": Operation.VIEW_DATA,
    "/api/v1/datasets/{dataset_id}": Operation.VIEW_DATA,
    "/api/v1/eda": Operation.VIEW_EDA,
    "/api/v1/features": Operation.FEATURE_ENGINEERING,
    "/api/v1/models/train": Operation.TRAIN_MODEL,
    "/api/v1/models/versions": Operation.VIEW_MODEL,
    "/api/v1/models/versions/{version_id}/threshold": Operation.ADJUST_THRESHOLD,
    "/api/v1/predictions/single": Operation.CREATE_PREDICTION,
    "/api/v1/predictions/batch": Operation.BATCH_PREDICTION,
    "/api/v1/predictions": Operation.VIEW_PREDICTION,
    "/api/v1/reports/generate": Operation.GENERATE_REPORT,
    "/api/v1/reports": Operation.VIEW_REPORT,
    "/api/v1/users": Operation.MANAGE_USERS,
}
