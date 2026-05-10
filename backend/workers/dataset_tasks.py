import csv
import io
import logging
from uuid import UUID

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.config import settings
from backend.domain.models.customer_record import CustomerRecord
from backend.services.dataset_service import DatasetService
from backend.utils.encryption import EncryptionService
from backend.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


engine = create_engine(
    settings.database_url.replace("postgresql+asyncpg://", "postgresql://"),
    pool_size=5,
    max_overflow=10,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


encryption_service = EncryptionService(settings.encryption_key)


@celery_app.task(name="backend.workers.dataset_tasks.process_csv_file")
def process_csv_file(dataset_id: str, file_content_base64: str) -> dict:
    import base64

    db = SessionLocal()

    try:
        file_content = base64.b64decode(file_content_base64)
        text_content = file_content.decode("utf-8")

        logger.info(f"Processing dataset {dataset_id}")

        csv_reader = csv.DictReader(io.StringIO(text_content))

        customer_ids = set()
        duplicate_ids = []
        records_created = 0
        duplicate_count = 0

        batch_size = 1000
        batch = []

        for row in csv_reader:
            customer_id = row.get("customerID", "").strip()

            if customer_id in customer_ids:
                duplicate_count += 1
                duplicate_ids.append(customer_id)
                logger.warning(f"Duplicate customerID found: {customer_id}")
                continue

            customer_ids.add(customer_id)

            customer_id_encrypted = encryption_service.encrypt(customer_id)
            payment_method = row.get("PaymentMethod", "").strip()
            payment_method_encrypted = (
                encryption_service.encrypt_optional(payment_method) if payment_method else None
            )

            record = CustomerRecord(
                dataset_id=UUID(dataset_id),
                customer_id_encrypted=customer_id_encrypted,
                gender=row.get("gender"),
                senior_citizen=(
                    int(row.get("SeniorCitizen", 0)) if row.get("SeniorCitizen") else None
                ),
                partner=row.get("Partner"),
                dependents=row.get("Dependents"),
                tenure=int(row.get("tenure", 0)) if row.get("tenure") else None,
                phone_service=row.get("PhoneService"),
                multiple_lines=row.get("MultipleLines"),
                internet_service=row.get("InternetService"),
                online_security=row.get("OnlineSecurity"),
                online_backup=row.get("OnlineBackup"),
                device_protection=row.get("DeviceProtection"),
                tech_support=row.get("TechSupport"),
                streaming_tv=row.get("StreamingTV"),
                streaming_movies=row.get("StreamingMovies"),
                contract=row.get("Contract"),
                paperless_billing=row.get("PaperlessBilling"),
                payment_method_encrypted=payment_method_encrypted,
                monthly_charges=(
                    float(row.get("MonthlyCharges", 0)) if row.get("MonthlyCharges") else None
                ),
                total_charges=_parse_total_charges(row.get("TotalCharges", "")),
                churn=row.get("Churn") == "Yes" if row.get("Churn") else None,
            )

            batch.append(record)

            if len(batch) >= batch_size:
                db.bulk_save_objects(batch)
                db.commit()
                records_created += len(batch)
                batch = []

        if batch:
            db.bulk_save_objects(batch)
            db.commit()
            records_created += len(batch)

        if duplicate_count > 0:
            max_duplicates_to_report = 10
            duplicate_sample = duplicate_ids[:max_duplicates_to_report]

            if duplicate_count <= max_duplicates_to_report:
                error_msg = f"Found {duplicate_count} duplicate customerID value(s): {', '.join(duplicate_sample)}"
            else:
                error_msg = f"Found {duplicate_count} duplicate customerID value(s). First {max_duplicates_to_report}: {', '.join(duplicate_sample)}"

            DatasetService.update_dataset_status(
                db,
                UUID(dataset_id),
                status="failed",
                validation_errors={"duplicates": error_msg, "duplicate_ids": duplicate_ids},
            )
            logger.error(f"Dataset {dataset_id} failed: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "records_created": records_created,
                "duplicate_count": duplicate_count,
                "duplicate_ids": duplicate_ids,
            }

        DatasetService.update_dataset_status(
            db, UUID(dataset_id), status="ready", data_quality_score=100.0
        )

        logger.info(f"Successfully processed dataset {dataset_id}: {records_created} records")

        return {
            "success": True,
            "records_created": records_created,
            "duplicate_count": duplicate_count,
        }

    except Exception as e:
        logger.error(f"Error processing dataset {dataset_id}: {e}", exc_info=True)

        DatasetService.update_dataset_status(
            db, UUID(dataset_id), status="failed", validation_errors={"error": str(e)}
        )

        return {"success": False, "error": str(e)}

    finally:
        db.close()


def _parse_total_charges(value: str) -> float | None:
    if not value or value.strip() == "":
        return None

    try:
        return float(value)
    except ValueError:
        return None
