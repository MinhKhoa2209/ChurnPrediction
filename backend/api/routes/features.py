"""
Feature Engineering API Routes
including feature importance computation and feature selection.
"""

import logging
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.api.dependencies import (
    get_current_user,
    require_any_authenticated_user,
    require_data_scientist_or_admin,
)
from backend.domain.schemas.auth import UserResponse
from backend.infrastructure.database import get_db
from backend.services.feature_service import FeatureService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/features", tags=["Features"])


class FeatureImportanceItem(BaseModel):
    """Feature importance data for a single feature"""
    featureName: str = Field(..., description="Name of the feature")
    importanceScore: float = Field(..., description="Mutual information score (0.0 to 1.0+)")


class FeatureImportanceResponse(BaseModel):
    """Response model for feature importance endpoint"""
    datasetId: str = Field(..., description="UUID of the dataset")
    featureImportance: list[FeatureImportanceItem] = Field(
        ..., 
        description="Feature importance scores ranked in descending order"
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
    }
)
async def get_feature_importance(
    dataset_id: UUID,
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)] = None,
    db: Session = Depends(get_db)
) -> FeatureImportanceResponse:
    """
    Get feature importance scores using mutual information
    
    **Requirements**:
    - Requirement 6.1: Compute feature importance scores using mutual information
    - Requirement 6.2: Rank features by importance score in descending order
    
    **Authorization**: Requires any authenticated user (Admin, Data_Scientist, or Analyst)
    
    **RBAC Matrix**:
    - Admin: ✓ Allowed
    - Data_Scientist: ✓ Allowed
    - Analyst: ✓ Allowed
    
    **Mutual Information**:
    Mutual information measures the dependency between a feature and the target variable.
    Higher scores indicate stronger relationships with churn prediction.
    
    **Features Analyzed**:
    - Demographic: gender, SeniorCitizen, Partner, Dependents
    - Service: tenure, PhoneService, MultipleLines, InternetService, OnlineSecurity,
      OnlineBackup, DeviceProtection, TechSupport, StreamingTV, StreamingMovies
    - Billing: Contract, PaperlessBilling, MonthlyCharges, TotalCharges
    
    Args:
        dataset_id: UUID of the dataset to analyze
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Feature importance scores ranked by importance in descending order
        
    Raises:
        HTTPException: If dataset not found, not ready, or user not authorized
    """
    try:
        # Call Feature service to compute feature importance
        result = FeatureService.compute_feature_importance(
            db=db,
            dataset_id=dataset_id,
            user_id=UUID(current_user.id)
        )
        
        logger.info(
            f"User {current_user.id} retrieved feature importance for dataset {dataset_id}"
        )
        
        return FeatureImportanceResponse(**result)
        
    except ValueError as e:
        error_message = str(e)
        
        # Determine appropriate status code based on error message
        if "not found" in error_message.lower() or "access denied" in error_message.lower():
            status_code = status.HTTP_404_NOT_FOUND
        elif "not ready" in error_message.lower():
            status_code = status.HTTP_400_BAD_REQUEST
        else:
            status_code = status.HTTP_400_BAD_REQUEST
        
        logger.warning(
            f"Failed to compute feature importance for dataset {dataset_id}: {error_message}"
        )
        
        raise HTTPException(
            status_code=status_code,
            detail=error_message
        )
    
    except Exception as e:
        logger.error(
            f"Unexpected error computing feature importance for dataset {dataset_id}: {str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while computing feature importance"
        )



class FeatureSelectionRequest(BaseModel):
    """Request model for feature selection endpoint"""
    importanceThreshold: Optional[float] = Field(
        None,
        description="Threshold for auto-selecting features (0.0 to 1.0). Features with importance >= threshold will be selected.",
        ge=0.0,
        le=1.0
    )
    selectedFeatures: Optional[list[str]] = Field(
        None,
        description="List of feature names to select manually. Mutually exclusive with importanceThreshold."
    )


class FeatureSelectionResponse(BaseModel):
    """Response model for feature selection endpoint"""
    datasetId: str = Field(..., description="UUID of the dataset")
    selectedFeatures: list[FeatureImportanceItem] = Field(
        ...,
        description="Selected features with their importance scores"
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
        403: {"description": "Forbidden - only Data_Scientist and Admin can select features"},
        404: {"description": "Dataset not found"},
    }
)
async def select_features(
    dataset_id: UUID,
    request: FeatureSelectionRequest,
    current_user: Annotated[UserResponse, Depends(require_data_scientist_or_admin)] = None,
    db: Session = Depends(get_db)
) -> FeatureSelectionResponse:
    """
    Select features by importance threshold or explicit feature list
    
    **Requirements**:
    - Requirement 6.3: Support feature selection by importance threshold
    - Requirement 6.4: Allow users to specify feature subset for training
    - Requirement 6.5: Train models using only selected features
    
    **Authorization**: Requires Data_Scientist or Admin role
    
    **RBAC Matrix**:
    - Admin: ✓ Allowed
    - Data_Scientist: ✓ Allowed
    - Analyst: ✗ Forbidden
    
    **Selection Methods**:
    
    1. **Threshold-based selection** (automatic):
       - Provide `importanceThreshold` (0.0 to 1.0)
       - All features with importance >= threshold will be selected
       - Useful for automatically filtering out low-importance features
    
    2. **Manual selection**:
       - Provide `selectedFeatures` as a list of feature names
       - Allows precise control over which features to use
       - Useful when domain knowledge suggests specific features
    
    **Note**: You must provide either `importanceThreshold` OR `selectedFeatures`, but not both.
    
    **Feature Selection Storage**:
    The selected features are stored in the dataset configuration and will be used
    automatically during model training (Requirement 6.5).
    
    Args:
        dataset_id: UUID of the dataset
        request: Feature selection request with threshold or feature list
        current_user: Current authenticated user (Data_Scientist or Admin)
        db: Database session
        
    Returns:
        Selected features with their importance scores and selection metadata
        
    Raises:
        HTTPException: If dataset not found, invalid parameters, or user not authorized
    """
    try:
        # Call Feature service to select features
        result = FeatureService.select_features_by_importance(
            db=db,
            dataset_id=dataset_id,
            user_id=UUID(current_user.id),
            importance_threshold=request.importanceThreshold,
            selected_features=request.selectedFeatures
        )
        
        logger.info(
            f"User {current_user.id} selected {len(result['selectedFeatures'])} features "
            f"for dataset {dataset_id} using {result['selectionMethod']} method"
        )
        
        return FeatureSelectionResponse(**result)
        
    except ValueError as e:
        error_message = str(e)
        
        # Determine appropriate status code based on error message
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
        
        logger.warning(
            f"Failed to select features for dataset {dataset_id}: {error_message}"
        )
        
        raise HTTPException(
            status_code=status_code,
            detail=error_message
        )
    
    except Exception as e:
        logger.error(
            f"Unexpected error selecting features for dataset {dataset_id}: {str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while selecting features"
        )


class InteractionFeatureItem(BaseModel):
    """Interaction feature data"""
    featureName: str = Field(..., description="Name of the interaction feature")
    formula: str = Field(..., description="Formula used to compute the interaction")
    description: str = Field(..., description="Description of the interaction feature")
    statistics: dict = Field(..., description="Statistical summary of the interaction feature")


class InteractionFeaturesResponse(BaseModel):
    """Response model for interaction features endpoint"""
    datasetId: str = Field(..., description="UUID of the dataset")
    interactionFeatures: list[InteractionFeatureItem] = Field(
        ...,
        description="List of created interaction features"
    )
    recordCount: int = Field(..., description="Number of records processed")


@router.post(
    "/{dataset_id}/interactions",
    status_code=status.HTTP_200_OK,
    response_model=InteractionFeaturesResponse,
    responses={
        200: {"description": "Interaction features created successfully"},
        400: {"description": "Dataset not ready or missing required features"},
        403: {"description": "Forbidden - only Data_Scientist and Admin can create interaction features"},
        404: {"description": "Dataset not found"},
    }
)
async def create_interaction_features(
    dataset_id: UUID,
    current_user: Annotated[UserResponse, Depends(require_data_scientist_or_admin)] = None,
    db: Session = Depends(get_db)
) -> InteractionFeaturesResponse:
    """
    Create interaction features for the dataset
    
    **Requirements**:
    - Requirement 6.6: Create interaction features for tenure and MonthlyCharges
    
    **Authorization**: Requires Data_Scientist or Admin role
    
    **RBAC Matrix**:
    - Admin: ✓ Allowed
    - Data_Scientist: ✓ Allowed
    - Analyst: ✗ Forbidden
    
    **Interaction Features**:
    
    This endpoint creates interaction features that capture relationships between
    multiple features. Currently creates:
    
    1. **tenure × MonthlyCharges**: Captures the total revenue potential of a customer
       - High values indicate long-term, high-paying customers
       - Low values may indicate new customers or low-spending customers
       - Useful for identifying customer lifetime value patterns
    
    **Feature Storage**:
    The interaction feature configuration is stored in the dataset metadata and will
    be used automatically during model training and prediction.
    
    **Statistics**:
    Returns statistical summary (mean, std, min, max, median) for each interaction
    feature to help understand the distribution.
    
    Args:
        dataset_id: UUID of the dataset
        current_user: Current authenticated user (Data_Scientist or Admin)
        db: Database session
        
    Returns:
        Created interaction features with statistics and metadata
        
    Raises:
        HTTPException: If dataset not found, not ready, missing features, or user not authorized
    """
    try:
        # Call Feature service to create interaction features
        result = FeatureService.create_interaction_features(
            db=db,
            dataset_id=dataset_id,
            user_id=UUID(current_user.id)
        )
        
        logger.info(
            f"User {current_user.id} created {len(result['interactionFeatures'])} "
            f"interaction feature(s) for dataset {dataset_id}"
        )
        
        return InteractionFeaturesResponse(**result)
        
    except ValueError as e:
        error_message = str(e)
        
        # Determine appropriate status code based on error message
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
        
        raise HTTPException(
            status_code=status_code,
            detail=error_message
        )
    
    except Exception as e:
        logger.error(
            f"Unexpected error creating interaction features for dataset {dataset_id}: {str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating interaction features"
        )
