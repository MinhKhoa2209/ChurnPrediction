import csv
import io
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from backend.domain.models.dataset import Dataset

logger = logging.getLogger(__name__)


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
    "Churn",
}


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
        "Credit card (automatic)",
    },
    "Churn": {"Yes", "No"},
}


class DatasetService:
    @staticmethod
    def validate_csv_file(file_content: bytes) -> tuple[bool, Optional[str], Optional[int]]:
        try:
            text_content = file_content.decode("utf-8")

            csv_reader = csv.DictReader(io.StringIO(text_content))

            if not csv_reader.fieldnames:
                return False, "CSV file has no header row", None

            columns = set(csv_reader.fieldnames)

            missing_columns = REQUIRED_COLUMNS - columns
            if missing_columns:
                missing_list = ", ".join(sorted(missing_columns))
                return False, f"Missing required columns: {missing_list}", None

            validation_errors = []
            row_count = 0

            for row_num, row in enumerate(csv_reader, start=2):
                row_count += 1

                customer_id = row.get("customerID", "").strip()
                if not customer_id:
                    validation_errors.append(f"Row {row_num}: customerID is empty")

                for col_name, valid_values in CATEGORICAL_VALUES.items():
                    value = row.get(col_name, "").strip()
                    if value and value not in valid_values:
                        validation_errors.append(
                            f"Row {row_num}: {col_name} has invalid value '{value}' "
                            f"(expected one of: {', '.join(sorted(valid_values))})"
                        )

                senior_citizen = row.get("SeniorCitizen", "").strip()
                if senior_citizen and senior_citizen not in {"0", "1"}:
                    validation_errors.append(
                        f"Row {row_num}: SeniorCitizen must be 0 or 1, got '{senior_citizen}'"
                    )

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

                total_charges = row.get("TotalCharges", "")
                if total_charges and total_charges.strip():
                    try:
                        float(total_charges)
                    except ValueError:
                        validation_errors.append(
                            f"Row {row_num}: TotalCharges must be a number or empty, got '{total_charges}'"
                        )

                if len(validation_errors) >= 10:
                    validation_errors.append("... (additional validation errors omitted)")
                    break

            if row_count == 0:
                return False, "CSV file contains no data rows", 0

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
        db: Session, user_id: UUID, filename: str, record_count: int, status: str = "processing"
    ) -> Dataset:
        dataset = Dataset(
            user_id=user_id,
            filename=filename,
            record_count=record_count,
            status=status,
            uploaded_at=datetime.utcnow(),
        )

        db.add(dataset)
        db.commit()
        db.refresh(dataset)

        logger.info(
            f"Created dataset {dataset.id} for user {user_id}: {filename} ({record_count} records)"
        )

        return dataset

    @staticmethod
    def get_dataset_by_id(db: Session, dataset_id: UUID) -> Optional[Dataset]:
        return db.query(Dataset).filter(Dataset.id == dataset_id).first()

    @staticmethod
    def get_user_datasets(db: Session, user_id: UUID) -> list[Dataset]:
        return (
            db.query(Dataset)
            .filter(Dataset.user_id == user_id)
            .order_by(Dataset.uploaded_at.desc())
            .all()
        )

    @staticmethod
    def update_dataset_status(
        db: Session,
        dataset_id: UUID,
        status: str,
        validation_errors: Optional[dict] = None,
        data_quality_score: Optional[float] = None,
    ) -> Optional[Dataset]:
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
        dataset = (
            db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.user_id == user_id).first()
        )

        if not dataset:
            return False

        db.delete(dataset)
        db.commit()

        logger.info(f"Deleted dataset {dataset_id} for user {user_id}")

        return True
