"""
EDA (Exploratory Data Analysis) API Routes
including correlation analysis, distributions, churn analysis, and visualizations.
"""

import logging
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.api.dependencies import (
    get_current_user,
    require_any_authenticated_user,
)
from backend.domain.schemas.auth import UserResponse
from backend.infrastructure.database import get_db
from backend.services.eda_service import EDAService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/eda", tags=["EDA"])


class CorrelationResponse(BaseModel):
    """Response model for correlation matrix endpoint"""
    datasetId: str = Field(..., description="UUID of the dataset")
    features: list[str] = Field(..., description="List of numeric feature names")
    correlationMatrix: list[list[float]] = Field(
        ..., 
        description="2D correlation matrix (features x features)"
    )
    recordCount: int = Field(..., description="Number of records used in computation")


class FeatureDistribution(BaseModel):
    """Distribution data for a single feature"""
    bins: list[float] = Field(..., description="Histogram bin edges")
    frequencies: list[int] = Field(..., description="Frequency count for each bin")
    min: float = Field(..., description="Minimum value")
    max: float = Field(..., description="Maximum value")
    mean: float = Field(..., description="Mean value")
    median: float = Field(..., description="Median value")


class DistributionsResponse(BaseModel):
    """Response model for distributions endpoint"""
    datasetId: str = Field(..., description="UUID of the dataset")
    distributions: dict[str, FeatureDistribution] = Field(
        ..., 
        description="Distribution data for each numeric feature (tenure, MonthlyCharges, TotalCharges)"
    )
    recordCount: int = Field(..., description="Number of records used in computation")


class ChurnRateItem(BaseModel):
    """Churn rate data for a single category"""
    contractType: Optional[str] = Field(None, description="Contract type (for churn-by-contract)")
    internetServiceType: Optional[str] = Field(None, description="Internet service type (for churn-by-internet)")
    churnRate: float = Field(..., description="Churn rate (0.0 to 1.0)")
    totalCustomers: int = Field(..., description="Total number of customers in this category")
    churnedCustomers: int = Field(..., description="Number of churned customers in this category")


class ChurnByContractResponse(BaseModel):
    """Response model for churn by contract endpoint"""
    datasetId: str = Field(..., description="UUID of the dataset")
    churnRates: list[ChurnRateItem] = Field(
        ..., 
        description="Churn rate data grouped by contract type"
    )
    recordCount: int = Field(..., description="Number of records used in computation")


class ChurnByInternetResponse(BaseModel):
    """Response model for churn by internet service endpoint"""
    datasetId: str = Field(..., description="UUID of the dataset")
    churnRates: list[ChurnRateItem] = Field(
        ..., 
        description="Churn rate data grouped by internet service type"
    )
    recordCount: int = Field(..., description="Number of records used in computation")


@router.get(
    "/{dataset_id}/correlation",
    status_code=status.HTTP_200_OK,
    response_model=CorrelationResponse,
    responses={
        200: {"description": "Correlation matrix computed successfully"},
        400: {"description": "Dataset not ready or invalid data"},
        403: {"description": "Forbidden - user does not have access to this dataset"},
        404: {"description": "Dataset not found"},
    }
)
async def get_correlation_matrix(
    dataset_id: UUID,
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)] = None,
    db: Session = Depends(get_db)
) -> CorrelationResponse:
    """
    Get correlation matrix for numeric features in a dataset
    
    **Requirements**:
    - Requirement 5.1: Compute correlation matrix for numeric features
    - Requirement 5.1: Return correlation data for visualization
    
    **Authorization**: Requires any authenticated user (Admin, Data_Scientist, or Analyst)
    
    **RBAC Matrix**:
    - Admin: ✓ Allowed
    - Data_Scientist: ✓ Allowed
    - Analyst: ✓ Allowed
    
    **Numeric Features Analyzed**:
    - tenure: Number of months the customer has stayed with the company
    - MonthlyCharges: The amount charged to the customer monthly
    - TotalCharges: The total amount charged to the customer
    - SeniorCitizen: Whether the customer is a senior citizen (0 or 1)
    
    Args:
        dataset_id: UUID of the dataset to analyze
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Correlation matrix with feature names and correlation values
        
    Raises:
        HTTPException: If dataset not found, not ready, or user not authorized
    """
    try:
        # Call EDA service to compute correlation matrix
        result = EDAService.get_correlation_matrix(
            db=db,
            dataset_id=dataset_id,
            user_id=UUID(current_user.id)
        )
        
        logger.info(
            f"User {current_user.id} retrieved correlation matrix for dataset {dataset_id}"
        )
        
        return CorrelationResponse(**result)
        
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
            f"Failed to compute correlation matrix for dataset {dataset_id}: {error_message}"
        )
        
        raise HTTPException(
            status_code=status_code,
            detail=error_message
        )
    
    except Exception as e:
        logger.error(
            f"Unexpected error computing correlation matrix for dataset {dataset_id}: {str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while computing correlation matrix"
        )


@router.get(
    "/{dataset_id}/distributions",
    status_code=status.HTTP_200_OK,
    response_model=DistributionsResponse,
    responses={
        200: {"description": "Distribution histograms computed successfully"},
        400: {"description": "Dataset not ready or invalid data"},
        403: {"description": "Forbidden - user does not have access to this dataset"},
        404: {"description": "Dataset not found"},
    }
)
async def get_distributions(
    dataset_id: UUID,
    bins: int = Query(default=10, ge=5, le=50, description="Number of histogram bins"),
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)] = None,
    db: Session = Depends(get_db)
) -> DistributionsResponse:
    """
    Get distribution histograms for numeric features in a dataset
    
    **Requirements**:
    - Requirement 5.2: Compute histograms for tenure, MonthlyCharges, TotalCharges
    - Requirement 5.2: Return distribution data with bins and frequencies
    
    **Authorization**: Requires any authenticated user (Admin, Data_Scientist, or Analyst)
    
    **RBAC Matrix**:
    - Admin: ✓ Allowed
    - Data_Scientist: ✓ Allowed
    - Analyst: ✓ Allowed
    
    **Numeric Features Analyzed**:
    - tenure: Number of months the customer has stayed with the company
    - MonthlyCharges: The amount charged to the customer monthly
    - TotalCharges: The total amount charged to the customer
    
    Args:
        dataset_id: UUID of the dataset to analyze
        bins: Number of bins for histogram computation (default: 10, range: 5-50)
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Distribution data with bins, frequencies, and summary statistics for each feature
        
    Raises:
        HTTPException: If dataset not found, not ready, or user not authorized
    """
    try:
        # Call EDA service to compute distributions
        result = EDAService.get_distributions(
            db=db,
            dataset_id=dataset_id,
            user_id=UUID(current_user.id),
            bins=bins
        )
        
        logger.info(
            f"User {current_user.id} retrieved distributions for dataset {dataset_id} with {bins} bins"
        )
        
        return DistributionsResponse(**result)
        
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
            f"Failed to compute distributions for dataset {dataset_id}: {error_message}"
        )
        
        raise HTTPException(
            status_code=status_code,
            detail=error_message
        )
    
    except Exception as e:
        logger.error(
            f"Unexpected error computing distributions for dataset {dataset_id}: {str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while computing distributions"
        )


@router.get(
    "/{dataset_id}/churn-by-contract",
    status_code=status.HTTP_200_OK,
    response_model=ChurnByContractResponse,
    responses={
        200: {"description": "Churn rates by contract type computed successfully"},
        400: {"description": "Dataset not ready or invalid data"},
        403: {"description": "Forbidden - user does not have access to this dataset"},
        404: {"description": "Dataset not found"},
    }
)
async def get_churn_by_contract(
    dataset_id: UUID,
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)] = None,
    db: Session = Depends(get_db)
) -> ChurnByContractResponse:
    """
    Get churn rate grouped by Contract type
    
    **Requirements**:
    - Requirement 5.3: Compute churn rate by Contract type for bar chart visualization
    
    **Authorization**: Requires any authenticated user (Admin, Data_Scientist, or Analyst)
    
    **RBAC Matrix**:
    - Admin: ✓ Allowed
    - Data_Scientist: ✓ Allowed
    - Analyst: ✓ Allowed
    
    **Contract Types** (from Telco Customer Churn dataset):
    - Month-to-month: Customers with monthly contracts
    - One year: Customers with one-year contracts
    - Two year: Customers with two-year contracts
    
    Args:
        dataset_id: UUID of the dataset to analyze
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Churn rate data grouped by contract type with total and churned customer counts
        
    Raises:
        HTTPException: If dataset not found, not ready, or user not authorized
    """
    try:
        # Call EDA service to compute churn rates by contract
        result = EDAService.get_churn_by_contract(
            db=db,
            dataset_id=dataset_id,
            user_id=UUID(current_user.id)
        )
        
        logger.info(
            f"User {current_user.id} retrieved churn by contract for dataset {dataset_id}"
        )
        
        return ChurnByContractResponse(**result)
        
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
            f"Failed to compute churn by contract for dataset {dataset_id}: {error_message}"
        )
        
        raise HTTPException(
            status_code=status_code,
            detail=error_message
        )
    
    except Exception as e:
        logger.error(
            f"Unexpected error computing churn by contract for dataset {dataset_id}: {str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while computing churn by contract"
        )


@router.get(
    "/{dataset_id}/churn-by-internet",
    status_code=status.HTTP_200_OK,
    response_model=ChurnByInternetResponse,
    responses={
        200: {"description": "Churn rates by internet service type computed successfully"},
        400: {"description": "Dataset not ready or invalid data"},
        403: {"description": "Forbidden - user does not have access to this dataset"},
        404: {"description": "Dataset not found"},
    }
)
async def get_churn_by_internet_service(
    dataset_id: UUID,
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)] = None,
    db: Session = Depends(get_db)
) -> ChurnByInternetResponse:
    """
    Get churn rate grouped by InternetService type
    
    **Requirements**:
    - Requirement 5.4: Compute churn rate by InternetService type for bar chart visualization
    
    **Authorization**: Requires any authenticated user (Admin, Data_Scientist, or Analyst)
    
    **RBAC Matrix**:
    - Admin: ✓ Allowed
    - Data_Scientist: ✓ Allowed
    - Analyst: ✓ Allowed
    
    **Internet Service Types** (from Telco Customer Churn dataset):
    - DSL: Customers with DSL internet service
    - Fiber optic: Customers with fiber optic internet service
    - No: Customers without internet service
    
    Args:
        dataset_id: UUID of the dataset to analyze
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Churn rate data grouped by internet service type with total and churned customer counts
        
    Raises:
        HTTPException: If dataset not found, not ready, or user not authorized
    """
    try:
        # Call EDA service to compute churn rates by internet service
        result = EDAService.get_churn_by_internet_service(
            db=db,
            dataset_id=dataset_id,
            user_id=UUID(current_user.id)
        )
        
        logger.info(
            f"User {current_user.id} retrieved churn by internet service for dataset {dataset_id}"
        )
        
        return ChurnByInternetResponse(**result)
        
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
            f"Failed to compute churn by internet service for dataset {dataset_id}: {error_message}"
        )
        
        raise HTTPException(
            status_code=status_code,
            detail=error_message
        )
    
    except Exception as e:
        logger.error(
            f"Unexpected error computing churn by internet service for dataset {dataset_id}: {str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while computing churn by internet service"
        )


class ScatterDataPoint(BaseModel):
    """Single data point for scatter plot"""
    monthlyCharges: float = Field(..., description="Monthly charges amount")
    totalCharges: float = Field(..., description="Total charges amount")
    churn: bool = Field(..., description="Whether the customer churned")


class ScatterPlotResponse(BaseModel):
    """Response model for scatter plot endpoint"""
    datasetId: str = Field(..., description="UUID of the dataset")
    scatterData: list[ScatterDataPoint] = Field(
        ..., 
        description="Scatter plot data points with MonthlyCharges, TotalCharges, and Churn"
    )
    recordCount: int = Field(..., description="Number of records used in computation")


@router.get(
    "/{dataset_id}/scatter",
    status_code=status.HTTP_200_OK,
    response_model=ScatterPlotResponse,
    responses={
        200: {"description": "Scatter plot data computed successfully"},
        400: {"description": "Dataset not ready or invalid data"},
        403: {"description": "Forbidden - user does not have access to this dataset"},
        404: {"description": "Dataset not found"},
    }
)
async def get_scatter_plot(
    dataset_id: UUID,
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)] = None,
    db: Session = Depends(get_db)
) -> ScatterPlotResponse:
    """
    Get scatter plot data for MonthlyCharges vs TotalCharges colored by Churn
    
    **Requirements**:
    - Requirement 5.5: Generate scatter plot data showing relationship between MonthlyCharges and TotalCharges
    - Requirement 5.5: Color data points by churn status for visualization
    
    **Authorization**: Requires any authenticated user (Admin, Data_Scientist, or Analyst)
    
    **RBAC Matrix**:
    - Admin: ✓ Allowed
    - Data_Scientist: ✓ Allowed
    - Analyst: ✓ Allowed
    
    **Data Points**:
    - MonthlyCharges: The amount charged to the customer monthly
    - TotalCharges: The total amount charged to the customer
    - Churn: Whether the customer has discontinued service (True/False)
    
    Args:
        dataset_id: UUID of the dataset to analyze
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Scatter plot data with MonthlyCharges, TotalCharges, and Churn for each customer record
        
    Raises:
        HTTPException: If dataset not found, not ready, or user not authorized
    """
    try:
        # Call EDA service to generate scatter plot data
        result = EDAService.get_scatter_plot(
            db=db,
            dataset_id=dataset_id,
            user_id=UUID(current_user.id)
        )
        
        logger.info(
            f"User {current_user.id} retrieved scatter plot data for dataset {dataset_id}"
        )
        
        return ScatterPlotResponse(**result)
        
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
            f"Failed to generate scatter plot data for dataset {dataset_id}: {error_message}"
        )
        
        raise HTTPException(
            status_code=status_code,
            detail=error_message
        )
    
    except Exception as e:
        logger.error(
            f"Unexpected error generating scatter plot data for dataset {dataset_id}: {str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating scatter plot data"
        )


class PCADataPoint2D(BaseModel):
    """Single data point for 2D PCA visualization"""
    pc1: float = Field(..., description="First principal component")
    pc2: float = Field(..., description="Second principal component")
    churn: bool = Field(..., description="Whether the customer churned")


class PCADataPoint3D(BaseModel):
    """Single data point for 3D PCA visualization"""
    pc1: float = Field(..., description="First principal component")
    pc2: float = Field(..., description="Second principal component")
    pc3: float = Field(..., description="Third principal component")
    churn: bool = Field(..., description="Whether the customer churned")


class PCAVisualizationResponse(BaseModel):
    """Response model for PCA visualization endpoint"""
    datasetId: str = Field(..., description="UUID of the dataset")
    pca2d: list[PCADataPoint2D] = Field(
        ..., 
        description="2D PCA data points with first two principal components"
    )
    pca3d: list[PCADataPoint3D] = Field(
        ..., 
        description="3D PCA data points with first three principal components"
    )
    explainedVariance2d: list[float] = Field(
        ..., 
        description="Explained variance ratio for each of the 2 principal components"
    )
    explainedVariance3d: list[float] = Field(
        ..., 
        description="Explained variance ratio for each of the 3 principal components"
    )
    recordCount: int = Field(..., description="Number of records used in computation")


@router.get(
    "/{dataset_id}/pca",
    status_code=status.HTTP_200_OK,
    response_model=PCAVisualizationResponse,
    responses={
        200: {"description": "PCA visualization data computed successfully"},
        400: {"description": "Dataset not ready or invalid data"},
        403: {"description": "Forbidden - user does not have access to this dataset"},
        404: {"description": "Dataset not found"},
    }
)
async def get_pca_visualization(
    dataset_id: UUID,
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)] = None,
    db: Session = Depends(get_db)
) -> PCAVisualizationResponse:
    """
    Get PCA visualization data with 2D and 3D principal components
    
    **Requirements**:
    - Requirement 7.1: Compute PCA transformation reducing features to 2 principal components
    - Requirement 7.2: Compute PCA transformation reducing features to 3 principal components
    - Requirement 7.5: Display explained variance ratio for each principal component
    - Requirement 7.6: Complete PCA computation within 3 seconds for 7,043 records
    
    **Authorization**: Requires any authenticated user (Admin, Data_Scientist, or Analyst)
    
    **RBAC Matrix**:
    - Admin: ✓ Allowed
    - Data_Scientist: ✓ Allowed
    - Analyst: ✓ Allowed
    
    **Features Used for PCA**:
    - tenure: Number of months the customer has stayed with the company
    - MonthlyCharges: The amount charged to the customer monthly
    - TotalCharges: The total amount charged to the customer
    - SeniorCitizen: Whether the customer is a senior citizen (0 or 1)
    
    **PCA Process**:
    1. Standardize features to zero mean and unit variance
    2. Compute principal components using eigenvalue decomposition
    3. Transform data to 2D and 3D principal component space
    4. Return explained variance ratio showing information retained
    
    Args:
        dataset_id: UUID of the dataset to analyze
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        PCA visualization data with 2D and 3D projections, explained variance ratios, and churn labels
        
    Raises:
        HTTPException: If dataset not found, not ready, or user not authorized
    """
    try:
        # Call EDA service to compute PCA visualization
        result = EDAService.get_pca_visualization(
            db=db,
            dataset_id=dataset_id,
            user_id=UUID(current_user.id)
        )
        
        logger.info(
            f"User {current_user.id} retrieved PCA visualization for dataset {dataset_id}"
        )
        
        return PCAVisualizationResponse(**result)
        
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
            f"Failed to compute PCA visualization for dataset {dataset_id}: {error_message}"
        )
        
        raise HTTPException(
            status_code=status_code,
            detail=error_message
        )
    
    except Exception as e:
        logger.error(
            f"Unexpected error computing PCA visualization for dataset {dataset_id}: {str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while computing PCA visualization"
        )
