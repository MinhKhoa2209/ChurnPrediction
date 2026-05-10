import logging
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.api.dependencies import (
    require_admin,
    require_any_authenticated_user,
)
from backend.domain.schemas.auth import UserResponse
from backend.infrastructure.database import get_db
from backend.services.feature_service import FeatureService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/features", tags=["Features"])


class FeatureImportanceItem(BaseModel):
    featureName: str = Field(..., description="Name of the feature")
    importanceScore: float = Field(..., description="Mutual information score (0.0 to 1.0+)")


class FeatureImportanceResponse(BaseModel):
    datasetId: str = Field(..., description="UUID of the dataset")
    featureImportance: list[FeatureImportanceItem] = Field(
        ..., description="Feature importance scores ranked in descending order"
    )
    recordCount: int = Field(..., description="Number of records used in computation")


@router.get(
    "/{dataset_id}/importance",
    status_code=status.HTTP_200_OK,
    response_model=FeatureImportanceResponse,
    responses={
        200: {"description": "Feature importance computed successfully"},
        400: {"description": "Dataset not ready or invalid data"},
        403: {"description": "Forbidden - user does not have access to this dataset"},
        404: {"description": "Dataset not found"},
    },
)
async def get_feature_importance(
    dataset_id: UUID,
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)] = None,
    db: Session = Depends(get_db),
) -> FeatureImportanceResponse:
    try:
        result = FeatureService.compute_feature_importance(
            db=db, dataset_id=dataset_id, user_id=UUID(current_user.id)
        )

        logger.info(f"User {current_user.id} retrieved feature importance for dataset {dataset_id}")

        return FeatureImportanceResponse(**result)

    except ValueError as e:
        error_message = str(e)

        if "not found" in error_message.lower() or "access denied" in error_message.lower():
            status_code = status.HTTP_404_NOT_FOUND
        elif "not ready" in error_message.lower():
            status_code = status.HTTP_400_BAD_REQUEST
        else:
            status_code = status.HTTP_400_BAD_REQUEST

        logger.warning(
            f"Failed to compute feature importance for dataset {dataset_id}: {error_message}"
        )

        raise HTTPException(status_code=status_code, detail=error_message)

    except Exception as e:
        logger.error(
            f"Unexpected error computing feature importance for dataset {dataset_id}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while computing feature importance",
        )


class FeatureSelectionRequest(BaseModel):
    importanceThreshold: Optional[float] = Field(
        None,
        description="Threshold for auto-selecting features (0.0 to 1.0). Features with importance >= threshold will be selected.",
        ge=0.0,
        le=1.0,
    )
    selectedFeatures: Optional[list[str]] = Field(
        None,
        description="List of feature names to select manually. Mutually exclusive with importanceThreshold.",
    )


class FeatureSelectionResponse(BaseModel):
    datasetId: str = Field(..., description="UUID of the dataset")
    selectedFeatures: list[FeatureImportanceItem] = Field(
        ..., description="Selected features with their importance scores"
    )
    selectionMethod: str = Field(..., description="Selection method: 'threshold' or 'manual'")
    threshold: Optional[float] = Field(None, description="Threshold used (if applicable)")


@router.post(
    "/{dataset_id}/select",
    status_code=status.HTTP_200_OK,
    response_model=FeatureSelectionResponse,
    responses={
        200: {"description": "Features selected successfully"},
        400: {"description": "Invalid request parameters or dataset not ready"},
        403: {"description": "Forbidden - only Admin can select features"},
        404: {"description": "Dataset not found"},
    },
)
async def select_features(
    dataset_id: UUID,
    request: FeatureSelectionRequest,
    current_user: Annotated[UserResponse, Depends(require_admin)] = None,
    db: Session = Depends(get_db),
) -> FeatureSelectionResponse:
    try:
        result = FeatureService.select_features_by_importance(
            db=db,
            dataset_id=dataset_id,
            user_id=UUID(current_user.id),
            importance_threshold=request.importanceThreshold,
            selected_features=request.selectedFeatures,
        )

        logger.info(
            f"User {current_user.id} selected {len(result['selectedFeatures'])} features "
            f"for dataset {dataset_id} using {result['selectionMethod']} method"
        )

        return FeatureSelectionResponse(**result)

    except ValueError as e:
        error_message = str(e)

        if "not found" in error_message.lower() or "access denied" in error_message.lower():
            status_code = status.HTTP_404_NOT_FOUND
        elif "not ready" in error_message.lower():
            status_code = status.HTTP_400_BAD_REQUEST
        elif "must provide" in error_message.lower() or "cannot provide" in error_message.lower():
            status_code = status.HTTP_400_BAD_REQUEST
        elif "invalid feature" in error_message.lower():
            status_code = status.HTTP_400_BAD_REQUEST
        elif "no features found" in error_message.lower():
            status_code = status.HTTP_400_BAD_REQUEST
        else:
            status_code = status.HTTP_400_BAD_REQUEST

        logger.warning(f"Failed to select features for dataset {dataset_id}: {error_message}")

        raise HTTPException(status_code=status_code, detail=error_message)

    except Exception as e:
        logger.error(
            f"Unexpected error selecting features for dataset {dataset_id}: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while selecting features",
        )


class InteractionFeatureItem(BaseModel):
    featureName: str = Field(..., description="Name of the interaction feature")
    formula: str = Field(..., description="Formula used to compute the interaction")
    description: str = Field(..., description="Description of the interaction feature")
    statistics: dict = Field(..., description="Statistical summary of the interaction feature")


class InteractionFeaturesResponse(BaseModel):
    datasetId: str = Field(..., description="UUID of the dataset")
    interactionFeatures: list[InteractionFeatureItem] = Field(
        ..., description="List of created interaction features"
    )
    recordCount: int = Field(..., description="Number of records processed")


@router.post(
    "/{dataset_id}/interactions",
    status_code=status.HTTP_200_OK,
    response_model=InteractionFeaturesResponse,
    responses={
        200: {"description": "Interaction features created successfully"},
        400: {"description": "Dataset not ready or missing required features"},
        403: {"description": "Forbidden - only Admin can create interaction features"},
        404: {"description": "Dataset not found"},
    },
)
async def create_interaction_features(
    dataset_id: UUID,
    current_user: Annotated[UserResponse, Depends(require_admin)] = None,
    db: Session = Depends(get_db),
) -> InteractionFeaturesResponse:
    try:
        result = FeatureService.create_interaction_features(
            db=db, dataset_id=dataset_id, user_id=UUID(current_user.id)
        )

        logger.info(
            f"User {current_user.id} created {len(result['interactionFeatures'])} "
            f"interaction feature(s) for dataset {dataset_id}"
        )

        return InteractionFeaturesResponse(**result)

    except ValueError as e:
        error_message = str(e)

        if "not found" in error_message.lower() or "access denied" in error_message.lower():
            status_code = status.HTTP_404_NOT_FOUND
        elif "not ready" in error_message.lower():
            status_code = status.HTTP_400_BAD_REQUEST
        elif "required features" in error_message.lower():
            status_code = status.HTTP_400_BAD_REQUEST
        elif "no customer records" in error_message.lower():
            status_code = status.HTTP_400_BAD_REQUEST
        else:
            status_code = status.HTTP_400_BAD_REQUEST

        logger.warning(
            f"Failed to create interaction features for dataset {dataset_id}: {error_message}"
        )

        raise HTTPException(status_code=status_code, detail=error_message)

    except Exception as e:
        logger.error(
            f"Unexpected error creating interaction features for dataset {dataset_id}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating interaction features",
        )
