"""
Dataset Service
"""



import csv
import io
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.orm import Session

from backend.domain.models.dataset import Dataset

logger = logging.getLogger(__name__)

# Required columns for the Telco Customer Churn dataset
REQUIRED_COLUMNS = {
    "customerID",
    "gender",
    "SeniorCitizen",
    "Partner",
    "Dependents",
    "tenure",
    "PhoneService",
    "MultipleLines",
    "InternetService",
    "OnlineSecurity",
    "OnlineBackup",
    "DeviceProtection",
    "TechSupport",
    "StreamingTV",
    "StreamingMovies",
    "Contract",
    "PaperlessBilling",
    "PaymentMethod",
    "MonthlyCharges",
    "TotalCharges",
    "Churn"
}

# Expected categorical values for validation
CATEGORICAL_VALUES = {
    "gender": {"Male", "Female"},
    "Partner": {"Yes", "No"},
    "Dependents": {"Yes", "No"},
    "PhoneService": {"Yes", "No"},
    "MultipleLines": {"Yes", "No", "No phone service"},
    "InternetService": {"DSL", "Fiber optic", "No"},
    "OnlineSecurity": {"Yes", "No", "No internet service"},
    "OnlineBackup": {"Yes", "No", "No internet service"},
    "DeviceProtection": {"Yes", "No", "No internet service"},
    "TechSupport": {"Yes", "No", "No internet service"},
    "StreamingTV": {"Yes", "No", "No internet service"},
    "StreamingMovies": {"Yes", "No", "No internet service"},
    "Contract": {"Month-to-month", "One year", "Two year"},
    "PaperlessBilling": {"Yes", "No"},
    "PaymentMethod": {
        "Electronic check",
        "Mailed check",
        "Bank transfer (automatic)",
        "Credit card (automatic)"
    },
    "Churn": {"Yes", "No"}
}


class DatasetService:
    """Service for dataset operations"""
    
    @staticmethod
    def validate_csv_file(file_content: bytes) -> tuple[bool, Optional[str], Optional[int]]:
        """
        Validate CSV file format and required columns
        Requirement 3.2: Validate file contains all required columns within 1 second
        Requirement 3.3: Return descriptive validation error listing missing columns
        Requirement 4.2: Validate data types for each column
        
        Args:
            file_content: Raw CSV file content as bytes
            
        Returns:
            Tuple of (is_valid, error_message, row_count)
        """
        try:
            # Decode file content
            text_content = file_content.decode('utf-8')
            
            # Parse CSV
            csv_reader = csv.DictReader(io.StringIO(text_content))
            
            # Get column names from header
            if not csv_reader.fieldnames:
                return False, "CSV file has no header row", None
            
            columns = set(csv_reader.fieldnames)
            
            # Check for required columns
            missing_columns = REQUIRED_COLUMNS - columns
            if missing_columns:
                missing_list = ", ".join(sorted(missing_columns))
                return False, f"Missing required columns: {missing_list}", None
            
            # Validate data types and values for each row
            validation_errors = []
            row_count = 0
            
            for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 (header is row 1)
                row_count += 1
                
                # Validate customerID (non-empty string)
                customer_id = row.get("customerID", "").strip()
                if not customer_id:
                    validation_errors.append(f"Row {row_num}: customerID is empty")
                
                # Validate categorical columns
                for col_name, valid_values in CATEGORICAL_VALUES.items():
                    value = row.get(col_name, "").strip()
                    if value and value not in valid_values:
                        validation_errors.append(
                            f"Row {row_num}: {col_name} has invalid value '{value}' "
                            f"(expected one of: {', '.join(sorted(valid_values))})"
                        )
                
                # Validate SeniorCitizen (0 or 1)
                senior_citizen = row.get("SeniorCitizen", "").strip()
                if senior_citizen and senior_citizen not in {"0", "1"}:
                    validation_errors.append(
                        f"Row {row_num}: SeniorCitizen must be 0 or 1, got '{senior_citizen}'"
                    )
                
                # Validate tenure (integer 0-72)
                tenure = row.get("tenure", "").strip()
                if tenure:
                    try:
                        tenure_int = int(tenure)
                        if tenure_int < 0 or tenure_int > 72:
                            validation_errors.append(
                                f"Row {row_num}: tenure must be between 0 and 72, got {tenure_int}"
                            )
                    except ValueError:
                        validation_errors.append(
                            f"Row {row_num}: tenure must be an integer, got '{tenure}'"
                        )
                
                # Validate MonthlyCharges (positive float)
                monthly_charges = row.get("MonthlyCharges", "").strip()
                if monthly_charges:
                    try:
                        monthly_charges_float = float(monthly_charges)
                        if monthly_charges_float < 0:
                            validation_errors.append(
                                f"Row {row_num}: MonthlyCharges must be positive, got {monthly_charges_float}"
                            )
                    except ValueError:
                        validation_errors.append(
                            f"Row {row_num}: MonthlyCharges must be a number, got '{monthly_charges}'"
                        )
                
                # Validate TotalCharges (convertible to float or empty/whitespace)
                total_charges = row.get("TotalCharges", "")
                if total_charges and total_charges.strip():
                    try:
                        float(total_charges)
                    except ValueError:
                        validation_errors.append(
                            f"Row {row_num}: TotalCharges must be a number or empty, got '{total_charges}'"
                        )
                
                # Limit error reporting to first 10 errors for performance
                if len(validation_errors) >= 10:
                    validation_errors.append("... (additional validation errors omitted)")
                    break
            
            if row_count == 0:
                return False, "CSV file contains no data rows", 0
            
            # Return validation errors if any
            if validation_errors:
                error_message = "Data validation errors:\n" + "\n".join(validation_errors)
                return False, error_message, row_count
            
            return True, None, row_count
            
        except UnicodeDecodeError:
            return False, "File is not a valid UTF-8 encoded CSV file", None
        except csv.Error as e:
            return False, f"CSV parsing error: {str(e)}", None
        except Exception as e:
            logger.error(f"Unexpected error validating CSV: {e}")
            return False, f"Unexpected error: {str(e)}", None
    
    @staticmethod
    def create_dataset(
        db: Session,
        user_id: UUID,
        filename: str,
        record_count: int,
        status: str = "processing"
    ) -> Dataset:
        """
        Create a new dataset record in the database
        Requirement 3.1: Accept CSV file uploads
        Requirement 3.2: Return 202 Accepted with dataset ID and processing status
        
        Args:
            db: Database session
            user_id: User ID who uploaded the dataset
            filename: Original filename
            record_count: Number of records in the dataset
            status: Initial status (default: "processing")
            
        Returns:
            Created Dataset instance
        """
        dataset = Dataset(
            user_id=user_id,
            filename=filename,
            record_count=record_count,
            status=status,
            uploaded_at=datetime.utcnow()
        )
        
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        
        logger.info(f"Created dataset {dataset.id} for user {user_id}: {filename} ({record_count} records)")
        
        return dataset
    
    @staticmethod
    def get_dataset_by_id(db: Session, dataset_id: UUID) -> Optional[Dataset]:
        """
        Get dataset by ID
        
        Args:
            db: Database session
            dataset_id: Dataset UUID
            
        Returns:
            Dataset instance or None if not found
        """
        return db.query(Dataset).filter(Dataset.id == dataset_id).first()
    
    @staticmethod
    def get_user_datasets(db: Session, user_id: UUID) -> list[Dataset]:
        """
        Get all datasets for a user
        Requirement 18.9: Users can only access their own datasets
        
        Args:
            db: Database session
            user_id: User UUID
            
        Returns:
            List of Dataset instances
        """
        return db.query(Dataset).filter(Dataset.user_id == user_id).order_by(Dataset.uploaded_at.desc()).all()
    
    @staticmethod
    def update_dataset_status(
        db: Session,
        dataset_id: UUID,
        status: str,
        validation_errors: Optional[dict] = None,
        data_quality_score: Optional[float] = None
    ) -> Optional[Dataset]:
        """
        Update dataset processing status
        
        Args:
            db: Database session
            dataset_id: Dataset UUID
            status: New status (processing, ready, failed)
            validation_errors: Optional validation errors
            data_quality_score: Optional data quality score
            
        Returns:
            Updated Dataset instance or None if not found
        """
        dataset = DatasetService.get_dataset_by_id(db, dataset_id)
        
        if not dataset:
            return None
        
        dataset.status = status
        dataset.validation_errors = validation_errors
        dataset.data_quality_score = data_quality_score
        
        if status in ["ready", "failed"]:
            dataset.processed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(dataset)
        
        logger.info(f"Updated dataset {dataset_id} status to {status}")
        
        return dataset
    
    @staticmethod
    def delete_dataset(db: Session, dataset_id: UUID, user_id: UUID) -> bool:
        """
        Delete a dataset
        Requirement 18.9: Users can only delete their own datasets
        
        Args:
            db: Database session
            dataset_id: Dataset UUID
            user_id: User UUID (for ownership check)
            
        Returns:
            True if deleted, False if not found or not owned by user
        """
        dataset = db.query(Dataset).filter(
            Dataset.id == dataset_id,
            Dataset.user_id == user_id
        ).first()
        
        if not dataset:
            return False
        
        db.delete(dataset)
        db.commit()
        
        logger.info(f"Deleted dataset {dataset_id} for user {user_id}")
        
        return True
