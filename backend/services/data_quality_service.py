"""
Data Quality Analysis Service
and invalid categorical values, then computes an overall quality score.
"""

import logging
from typing import Dict, List, Optional, Any
from uuid import UUID

import numpy as np
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.domain.models.customer_record import CustomerRecord
from backend.domain.models.dataset import Dataset

logger = logging.getLogger(__name__)

# Expected categorical values for validation (from Task 4.2)
CATEGORICAL_VALUES = {
    "gender": {"Male", "Female"},
    "partner": {"Yes", "No"},
    "dependents": {"Yes", "No"},
    "phone_service": {"Yes", "No"},
    "multiple_lines": {"Yes", "No", "No phone service"},
    "internet_service": {"DSL", "Fiber optic", "No"},
    "online_security": {"Yes", "No", "No internet service"},
    "online_backup": {"Yes", "No", "No internet service"},
    "device_protection": {"Yes", "No", "No internet service"},
    "tech_support": {"Yes", "No", "No internet service"},
    "streaming_tv": {"Yes", "No", "No internet service"},
    "streaming_movies": {"Yes", "No", "No internet service"},
    "contract": {"Month-to-month", "One year", "Two year"},
    "paperless_billing": {"Yes", "No"},
}

# Numeric columns for outlier detection
NUMERIC_COLUMNS = ["tenure", "monthly_charges", "total_charges"]

# All columns to check for missing values
ALL_COLUMNS = [
    "gender", "senior_citizen", "partner", "dependents", "tenure",
    "phone_service", "multiple_lines", "internet_service", "online_security",
    "online_backup", "device_protection", "tech_support", "streaming_tv",
    "streaming_movies", "contract", "paperless_billing", "monthly_charges",
    "total_charges", "churn"
]


class DataQualityService:
    """Service for data quality analysis"""
    
    @staticmethod
    def analyze_data_quality(db: Session, dataset_id: UUID) -> Dict[str, Any]:
        """
        Analyze data quality for a dataset
        
        - 18.2: Detect and report outliers using IQR method
        - 18.3: Detect and report invalid categorical values
        - 18.4: Compute data quality score (0-100)
        
        Args:
            db: Database session
            dataset_id: Dataset UUID
            
        Returns:
            Dictionary containing quality analysis results
        """
        # Get dataset
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            raise ValueError(f"Dataset {dataset_id} not found")
        
        # Get all customer records for this dataset
        records = db.query(CustomerRecord).filter(
            CustomerRecord.dataset_id == dataset_id
        ).all()
        
        if not records:
            raise ValueError(f"No customer records found for dataset {dataset_id}")
        
        total_records = len(records)
        
        # Detect missing values (Requirement 18.1)
        missing_values = DataQualityService._detect_missing_values(records)
        
        # Detect outliers (Requirement 18.2)
        outliers = DataQualityService._detect_outliers(records)
        
        # Detect invalid categorical values (Requirement 18.3)
        invalid_categorical = DataQualityService._detect_invalid_categorical(records)
        
        # Validate TotalCharges convertibility (Requirement 18.7)
        total_charges_validation = DataQualityService._validate_total_charges_convertibility(records)
        
        # Validate non-negative values (Requirement 18.8)
        negative_values_validation = DataQualityService._validate_non_negative_values(records)
        
        # Compute quality scores (Requirement 18.4)
        completeness_score = DataQualityService._compute_completeness_score(
            missing_values, total_records
        )
        validity_score = DataQualityService._compute_validity_score(
            outliers, invalid_categorical, total_records
        )
        quality_score = (completeness_score * 0.5) + (validity_score * 0.5)
        
        return {
            "dataset_id": str(dataset_id),
            "quality_score": round(quality_score, 2),
            "completeness_score": round(completeness_score, 2),
            "validity_score": round(validity_score, 2),
            "total_records": total_records,
            "missing_values": missing_values,
            "outliers": outliers,
            "invalid_categorical": invalid_categorical,
            "specific_validations": {
                "total_charges_convertibility": total_charges_validation,
                "negative_values": negative_values_validation
            }
        }
    
    @staticmethod
    def _detect_missing_values(records: List[CustomerRecord]) -> Dict[str, int]:
        """
        Detect and count missing values by column
        Requirement 18.1: Detect and report missing values by column
        
        Args:
            records: List of CustomerRecord instances
            
        Returns:
            Dictionary mapping column names to missing value counts
        """
        missing_counts = {}
        
        for column in ALL_COLUMNS:
            missing_count = 0
            for record in records:
                value = getattr(record, column, None)
                if value is None:
                    missing_count += 1
            missing_counts[column] = missing_count
        
        return missing_counts
    
    @staticmethod
    def _detect_outliers(records: List[CustomerRecord]) -> Dict[str, Dict[str, Any]]:
        """
        Detect outliers using IQR method for numeric columns
        Requirement 18.2: Detect and report outliers using IQR method
        
        IQR Method:
        - Q1 = 25th percentile
        - Q3 = 75th percentile
        - IQR = Q3 - Q1
        - Lower bound = Q1 - 1.5 × IQR
        - Upper bound = Q3 + 1.5 × IQR
        - Outliers are values < lower bound or > upper bound
        
        Args:
            records: List of CustomerRecord instances
            
        Returns:
            Dictionary mapping column names to outlier statistics
        """
        outliers = {}
        total_records = len(records)
        
        for column in NUMERIC_COLUMNS:
            # Extract non-null values
            values = []
            for record in records:
                value = getattr(record, column, None)
                if value is not None:
                    try:
                        # Try to convert to float, skip if conversion fails
                        values.append(float(value))
                    except (ValueError, TypeError):
                        # Skip non-convertible values
                        continue
            
            if not values:
                outliers[column] = {"count": 0, "percentage": 0.0}
                continue
            
            # Compute IQR
            values_array = np.array(values)
            q1 = np.percentile(values_array, 25)
            q3 = np.percentile(values_array, 75)
            iqr = q3 - q1
            
            # Compute bounds
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            # Count outliers
            outlier_count = 0
            for value in values:
                if value < lower_bound or value > upper_bound:
                    outlier_count += 1
            
            outliers[column] = {
                "count": outlier_count,
                "percentage": round((outlier_count / total_records) * 100, 2)
            }
        
        return outliers
    
    @staticmethod
    def _detect_invalid_categorical(
        records: List[CustomerRecord]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Detect invalid categorical values not in expected domain
        Requirement 18.3: Detect and report invalid categorical values
        
        Args:
            records: List of CustomerRecord instances
            
        Returns:
            Dictionary mapping column names to invalid value statistics
        """
        invalid_categorical = {}
        
        for column, valid_values in CATEGORICAL_VALUES.items():
            invalid_values_set = set()
            invalid_count = 0
            
            for record in records:
                value = getattr(record, column, None)
                if value is not None and value not in valid_values:
                    invalid_values_set.add(value)
                    invalid_count += 1
            
            invalid_categorical[column] = {
                "count": invalid_count,
                "invalid_values": sorted(list(invalid_values_set))
            }
        
        return invalid_categorical
    
    @staticmethod
    def _validate_total_charges_convertibility(
        records: List[CustomerRecord]
    ) -> Dict[str, Any]:
        """
        Validate that TotalCharges values are convertible to float64
        Requirement 18.7: Validate TotalCharges is convertible to float64
        
        TotalCharges can be empty/whitespace when tenure = 0, which is valid.
        This method reports rows where TotalCharges contains non-numeric strings
        that cannot be converted to float64.
        
        Args:
            records: List of CustomerRecord instances
            
        Returns:
            Dictionary with count and list of invalid row indices
        """
        invalid_rows = []
        
        for idx, record in enumerate(records):
            total_charges = record.total_charges
            
            # If total_charges is already a float or None, it's valid
            if total_charges is None or isinstance(total_charges, (int, float)):
                continue
            
            # If it's a string, try to convert it
            if isinstance(total_charges, str):
                # Empty or whitespace-only strings are valid (occur when tenure = 0)
                if total_charges.strip() == "":
                    continue
                
                # Try to convert to float
                try:
                    float(total_charges)
                except (ValueError, TypeError):
                    # Non-convertible value found
                    invalid_rows.append(idx)
        
        return {
            "count": len(invalid_rows),
            "invalid_rows": invalid_rows
        }
    
    @staticmethod
    def _validate_non_negative_values(
        records: List[CustomerRecord]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Validate that MonthlyCharges and tenure are non-negative
        Requirement 18.8: Validate MonthlyCharges and tenure are non-negative
        
        Args:
            records: List of CustomerRecord instances
            
        Returns:
            Dictionary mapping column names to validation results
        """
        monthly_charges_invalid = []
        tenure_invalid = []
        
        for idx, record in enumerate(records):
            # Check MonthlyCharges
            monthly_charges = record.monthly_charges
            if monthly_charges is not None:
                try:
                    if float(monthly_charges) < 0:
                        monthly_charges_invalid.append(idx)
                except (ValueError, TypeError):
                    # If it can't be converted to float, it's invalid
                    monthly_charges_invalid.append(idx)
            
            # Check tenure
            tenure = record.tenure
            if tenure is not None:
                try:
                    if int(tenure) < 0:
                        tenure_invalid.append(idx)
                except (ValueError, TypeError):
                    # If it can't be converted to int, it's invalid
                    tenure_invalid.append(idx)
        
        return {
            "monthly_charges": {
                "count": len(monthly_charges_invalid),
                "invalid_rows": monthly_charges_invalid
            },
            "tenure": {
                "count": len(tenure_invalid),
                "invalid_rows": tenure_invalid
            }
        }
    
    @staticmethod
    def _compute_completeness_score(
        missing_values: Dict[str, int],
        total_records: int
    ) -> float:
        """
        Compute completeness score based on missing values
        
        Completeness score = percentage of non-null values across all columns
        
        Args:
            missing_values: Dictionary of missing value counts by column
            total_records: Total number of records
            
        Returns:
            Completeness score (0-100)
        """
        if total_records == 0:
            return 0.0
        
        total_cells = total_records * len(ALL_COLUMNS)
        total_missing = sum(missing_values.values())
        total_present = total_cells - total_missing
        
        completeness_score = (total_present / total_cells) * 100
        return completeness_score
    
    @staticmethod
    def _compute_validity_score(
        outliers: Dict[str, Dict[str, Any]],
        invalid_categorical: Dict[str, Dict[str, Any]],
        total_records: int
    ) -> float:
        """
        Compute validity score based on outliers and invalid categorical values
        
        Validity score = percentage of valid values (no outliers, valid categorical values)
        
        Args:
            outliers: Dictionary of outlier statistics by column
            invalid_categorical: Dictionary of invalid categorical statistics
            total_records: Total number of records
            
        Returns:
            Validity score (0-100)
        """
        if total_records == 0:
            return 0.0
        
        # Count total invalid values
        total_outliers = sum(outlier_info["count"] for outlier_info in outliers.values())
        total_invalid_categorical = sum(
            invalid_info["count"] for invalid_info in invalid_categorical.values()
        )
        
        # Total columns checked for validity
        total_columns_checked = len(NUMERIC_COLUMNS) + len(CATEGORICAL_VALUES)
        total_cells_checked = total_records * total_columns_checked
        
        # Total invalid cells
        total_invalid = total_outliers + total_invalid_categorical
        total_valid = total_cells_checked - total_invalid
        
        validity_score = (total_valid / total_cells_checked) * 100
        return validity_score
