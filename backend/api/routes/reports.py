"""
Report API Routes
"""

import logging
from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.api.dependencies import require_any_authenticated_user
from backend.domain.models.report import Report
from backend.domain.schemas.auth import UserResponse
from backend.infrastructure.database import get_db
from backend.infrastructure.storage import storage_client
from backend.services.report_service import ReportService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["Reports"])


class ReportGenerateRequest(BaseModel):
    """Request schema for report generation"""
    model_version_id: str
    include_confusion_matrix: bool = True
    include_roc_curve: bool = True
    include_feature_importance: bool = True


class ReportResponse(BaseModel):
    """Response schema for report"""
    id: str
    model_version_id: str
    report_type: str
    file_size: int
    created_at: str


@router.post(
    "/generate",
    status_code=status.HTTP_201_CREATED,
    response_model=ReportResponse,
    responses={
        201: {"description": "Report generated successfully"},
        400: {"description": "Invalid request"},
        404: {"description": "Model version not found"},
        500: {"description": "Internal server error"},
    }
)
async def generate_report(
    request: ReportGenerateRequest,
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)],
    db: Session = Depends(get_db)
):
    """
    Generate a new PDF report for a model version
    
    **Authorization**: Requires any authenticated user
    
    **RBAC Matrix**:
    - Admin: ✓ Allowed
    - Data_Scientist: ✓ Allowed
    - Analyst: ✓ Allowed
    
    **Requirements**:
    - 16.1: Generate PDF reports with metrics and visualizations
    - 16.2: Include confusion matrix, ROC curve, feature importance
    - 16.3: Include executive summary statistics
    - 16.4: Generate PDF within 10 seconds
    - 16.6: Store reports in R2_Storage
    
    Args:
        request: Report generation request
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Report metadata
        
    Raises:
        HTTPException: 400 if invalid request, 404 if model not found, 500 if generation fails
    """
    try:
        # Parse model_version_id
        try:
            model_version_id = UUID(request.model_version_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid model_version_id format: {request.model_version_id}"
            )
        
        # Generate report
        report_service = ReportService()
        report = report_service.generate_model_report(
            db=db,
            user_id=UUID(current_user.id),
            model_version_id=model_version_id,
            include_confusion_matrix=request.include_confusion_matrix,
            include_roc_curve=request.include_roc_curve,
            include_feature_importance=request.include_feature_importance
        )
        
        logger.info(
            f"User {current_user.id} generated report {report.id} "
            f"for model {model_version_id}"
        )
        
        return ReportResponse(
            id=str(report.id),
            model_version_id=str(report.model_version_id),
            report_type=report.report_type,
            file_size=report.file_size,
            created_at=report.created_at.isoformat()
        )
        
    except ValueError as e:
        logger.warning(f"Invalid request: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except RuntimeError as e:
        logger.error(f"Report generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error generating report: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during report generation"
        )


@router.get(
    "",
    response_model=List[ReportResponse],
    responses={
        200: {"description": "List of reports"},
    }
)
async def list_reports(
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)],
    db: Session = Depends(get_db)
):
    """
    List all reports for the current user
    
    **Authorization**: Requires any authenticated user
    
    **RBAC Matrix**:
    - Admin: ✓ Allowed (can see all reports)
    - Data_Scientist: ✓ Allowed (can see own reports)
    - Analyst: ✓ Allowed (can see own reports)
    
    **Requirements**:
    - 16.5: List user's reports
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of report metadata
    """
    try:
        # Query reports
        query = db.query(Report)
        
        # Admin can see all reports, others see their own
        if current_user.role != "Admin":
            query = query.filter(Report.user_id == UUID(current_user.id))
        
        reports = query.order_by(Report.created_at.desc()).all()
        
        logger.info(f"User {current_user.id} listed {len(reports)} reports")
        
        return [
            ReportResponse(
                id=str(report.id),
                model_version_id=str(report.model_version_id),
                report_type=report.report_type,
                file_size=report.file_size,
                created_at=report.created_at.isoformat()
            )
            for report in reports
        ]
        
    except Exception as e:
        logger.error(f"Error listing reports: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list reports"
        )


@router.get(
    "/{report_id}",
    response_model=ReportResponse,
    responses={
        200: {"description": "Report details"},
        404: {"description": "Report not found"},
    }
)
async def get_report(
    report_id: str,
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)],
    db: Session = Depends(get_db)
):
    """
    Get report details
    
    **Authorization**: Requires any authenticated user
    
    **RBAC Matrix**:
    - Admin: ✓ Allowed
    - Data_Scientist: ✓ Allowed
    - Analyst: ✓ Allowed
    
    **Requirements**:
    - 16.5: Get report details
    
    Args:
        report_id: Report UUID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Report metadata
        
    Raises:
        HTTPException: 404 if report not found
    """
    try:
        # Parse report_id
        try:
            report_uuid = UUID(report_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid report_id format: {report_id}"
            )
        
        # Query report
        query = db.query(Report).filter(Report.id == report_uuid)
        
        # Admin can see all reports, others see their own
        if current_user.role != "Admin":
            query = query.filter(Report.user_id == UUID(current_user.id))
        
        report = query.first()
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report {report_id} not found or you don't have access to it"
            )
        
        logger.info(f"User {current_user.id} retrieved report {report_id}")
        
        return ReportResponse(
            id=str(report.id),
            model_version_id=str(report.model_version_id),
            report_type=report.report_type,
            file_size=report.file_size,
            created_at=report.created_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving report: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve report"
        )


@router.get(
    "/{report_id}/download",
    responses={
        200: {
            "description": "PDF file download",
            "content": {"application/pdf": {}}
        },
        404: {"description": "Report not found"},
    }
)
async def download_report(
    report_id: str,
    current_user: Annotated[UserResponse, Depends(require_any_authenticated_user)],
    db: Session = Depends(get_db)
):
    """
    Download report PDF file
    
    **Authorization**: Requires any authenticated user
    
    **RBAC Matrix**:
    - Admin: ✓ Allowed
    - Data_Scientist: ✓ Allowed
    - Analyst: ✓ Allowed
    
    **Requirements**:
    - 16.5: Trigger browser download of PDF report
    
    Args:
        report_id: Report UUID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        PDF file stream
        
    Raises:
        HTTPException: 404 if report not found
    """
    try:
        # Parse report_id
        try:
            report_uuid = UUID(report_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid report_id format: {report_id}"
            )
        
        # Query report
        query = db.query(Report).filter(Report.id == report_uuid)
        
        # Admin can see all reports, others see their own
        if current_user.role != "Admin":
            query = query.filter(Report.user_id == UUID(current_user.id))
        
        report = query.first()
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report {report_id} not found or you don't have access to it"
            )
        
        # Download from R2
        try:
            pdf_data = storage_client.client.get_object(
                Bucket=storage_client.reports_bucket,
                Key=report.file_path
            )['Body'].read()
        except Exception as e:
            logger.error(f"Failed to download report from R2: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to download report file"
            )
        
        logger.info(f"User {current_user.id} downloaded report {report_id}")
        
        # Return PDF as downloadable file (Requirement 16.5)
        import io
        return StreamingResponse(
            io.BytesIO(pdf_data),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=report_{report_id}.pdf"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading report: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download report"
        )
