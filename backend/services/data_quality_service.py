import logging
from typing import Any, Dict, List
from uuid import UUID

import numpy as np
from sqlalchemy.orm import Session

from backend.domain.models.customer_record import CustomerRecord
from backend.domain.models.dataset import Dataset

logger = logging.getLogger(__name__)


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


NUMERIC_COLUMNS = ["tenure", "monthly_charges", "total_charges"]


ALL_COLUMNS = [
    "gender",
    "senior_citizen",
    "partner",
    "dependents",
    "tenure",
    "phone_service",
    "multiple_lines",
    "internet_service",
    "online_security",
    "online_backup",
    "device_protection",
    "tech_support",
    "streaming_tv",
    "streaming_movies",
    "contract",
    "paperless_billing",
    "monthly_charges",
    "total_charges",
    "churn",
]


class DataQualityService:
    @staticmethod
    def analyze_data_quality(db: Session, dataset_id: UUID) -> Dict[str, Any]:
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            raise ValueError(f"Dataset {dataset_id} not found")

        records = db.query(CustomerRecord).filter(CustomerRecord.dataset_id == dataset_id).all()

        if not records:
            raise ValueError(f"No customer records found for dataset {dataset_id}")

        total_records = len(records)

        missing_values = DataQualityService._detect_missing_values(records)

        outliers = DataQualityService._detect_outliers(records)

        invalid_categorical = DataQualityService._detect_invalid_categorical(records)

        total_charges_validation = DataQualityService._validate_total_charges_convertibility(
            records
        )

        negative_values_validation = DataQualityService._validate_non_negative_values(records)

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
                "negative_values": negative_values_validation,
            },
        }

    @staticmethod
    def _detect_missing_values(records: List[CustomerRecord]) -> Dict[str, int]:
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
        outliers = {}
        total_records = len(records)

        for column in NUMERIC_COLUMNS:
            values = []
            for record in records:
                value = getattr(record, column, None)
                if value is not None:
                    try:
                        values.append(float(value))
                    except (ValueError, TypeError):
                        continue

            if not values:
                outliers[column] = {"count": 0, "percentage": 0.0}
                continue

            values_array = np.array(values)
            q1 = np.percentile(values_array, 25)
            q3 = np.percentile(values_array, 75)
            iqr = q3 - q1

            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr

            outlier_count = 0
            for value in values:
                if value < lower_bound or value > upper_bound:
                    outlier_count += 1

            outliers[column] = {
                "count": outlier_count,
                "percentage": round((outlier_count / total_records) * 100, 2),
            }

        return outliers

    @staticmethod
    def _detect_invalid_categorical(records: List[CustomerRecord]) -> Dict[str, Dict[str, Any]]:
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
                "invalid_values": sorted(list(invalid_values_set)),
            }

        return invalid_categorical

    @staticmethod
    def _validate_total_charges_convertibility(records: List[CustomerRecord]) -> Dict[str, Any]:
        invalid_rows = []

        for idx, record in enumerate(records):
            total_charges = record.total_charges

            if total_charges is None or isinstance(total_charges, (int, float)):
                continue

            if isinstance(total_charges, str):
                if total_charges.strip() == "":
                    continue

                try:
                    float(total_charges)
                except (ValueError, TypeError):
                    invalid_rows.append(idx)

        return {"count": len(invalid_rows), "invalid_rows": invalid_rows}

    @staticmethod
    def _validate_non_negative_values(records: List[CustomerRecord]) -> Dict[str, Dict[str, Any]]:
        monthly_charges_invalid = []
        tenure_invalid = []

        for idx, record in enumerate(records):
            monthly_charges = record.monthly_charges
            if monthly_charges is not None:
                try:
                    if float(monthly_charges) < 0:
                        monthly_charges_invalid.append(idx)
                except (ValueError, TypeError):
                    monthly_charges_invalid.append(idx)

            tenure = record.tenure
            if tenure is not None:
                try:
                    if int(tenure) < 0:
                        tenure_invalid.append(idx)
                except (ValueError, TypeError):
                    tenure_invalid.append(idx)

        return {
            "monthly_charges": {
                "count": len(monthly_charges_invalid),
                "invalid_rows": monthly_charges_invalid,
            },
            "tenure": {"count": len(tenure_invalid), "invalid_rows": tenure_invalid},
        }

    @staticmethod
    def _compute_completeness_score(missing_values: Dict[str, int], total_records: int) -> float:
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
        total_records: int,
    ) -> float:
        if total_records == 0:
            return 0.0

        total_outliers = sum(outlier_info["count"] for outlier_info in outliers.values())
        total_invalid_categorical = sum(
            invalid_info["count"] for invalid_info in invalid_categorical.values()
        )

        total_columns_checked = len(NUMERIC_COLUMNS) + len(CATEGORICAL_VALUES)
        total_cells_checked = total_records * total_columns_checked

        total_invalid = total_outliers + total_invalid_categorical
        total_valid = total_cells_checked - total_invalid

        validity_score = (total_valid / total_cells_checked) * 100
        return validity_score
