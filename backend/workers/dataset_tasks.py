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


def _cleanup_dataset_records(db, dataset_id: UUID) -> int:
    deleted_count = (
        db.query(CustomerRecord)
        .filter(CustomerRecord.dataset_id == dataset_id)
        .delete(synchronize_session=False)
    )
    db.commit()
    logger.info(f"Removed {deleted_count} partial record(s) for dataset {dataset_id}")
    return deleted_count


def _invalidate_dashboard_cache() -> None:
    try:
        from backend.infrastructure.cache import cache_client
        from backend.services.dashboard_service import DashboardService

        if cache_client.is_available and cache_client.redis_client:
            DashboardService.invalidate_cache(cache_client.redis_client)
    except Exception as exc:
        logger.warning(f"Failed to invalidate dashboard cache: {exc}")


@celery_app.task(name="backend.workers.dataset_tasks.process_csv_file", bind=True)
def process_csv_file(self, dataset_id: str, file_content_base64: str) -> dict:
    import base64
    import json
    from datetime import datetime

    from backend.infrastructure.cache import cache_client

    db = SessionLocal()

    try:
        file_content = base64.b64decode(file_content_base64)
        text_content = file_content.decode("utf-8")

        logger.info(f"Processing dataset {dataset_id}")

        # Count total rows first
        total_rows = sum(1 for _ in csv.DictReader(io.StringIO(text_content)))
        logger.info(f"Dataset {dataset_id}: Total rows to process: {total_rows}")

        # Reset reader
        csv_reader = csv.DictReader(io.StringIO(text_content))

        # Initialize progress in Redis
        progress_key = f"dataset:progress:{dataset_id}"
        start_time = datetime.utcnow()
        
        logger.info(f"Initializing progress tracking for dataset {dataset_id}")
        try:
            cache_client.set_json(
                progress_key,
                {
                    "status": "processing",
                    "progress": 0,
                    "total_records": total_rows,
                    "processed_records": 0,
                    "current_step": "Parsing CSV and validating data",
                    "started_at": start_time.isoformat(),
                },
                ttl=3600  # Expire after 1 hour
            )
            logger.info(f"Progress initialized in Redis for dataset {dataset_id}")
        except Exception as e:
            logger.error(f"Failed to initialize progress in Redis: {e}", exc_info=True)

        customer_ids = set()
        duplicate_ids = []
        records_created = 0
        duplicate_count = 0

        batch_size = 1000
        batch = []

        for idx, row in enumerate(csv_reader, start=1):
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

            # Update progress every 50 records (more frequent for better UX)
            if idx % 50 == 0 or idx == 1:  # Also update on first record
                progress_percent = int((idx / total_rows) * 100) if total_rows > 0 else 0

                logger.info(f"Dataset {dataset_id}: Progress {progress_percent}% ({idx}/{total_rows})")

                try:
                    cache_client.set_json(
                        progress_key,
                        {
                            "status": "processing",
                            "progress": progress_percent,
                            "total_records": total_rows,
                            "processed_records": idx,
                            "current_step": f"Processing records ({idx}/{total_rows})",
                            "started_at": start_time.isoformat(),
                        },
                        ttl=3600
                    )
                    logger.debug(f"Progress updated in Redis for dataset {dataset_id}")
                except Exception as cache_error:
                    logger.error(f"Failed to update progress in Redis: {cache_error}")

                # Update Celery task state
                try:
                    self.update_state(
                        state='PROGRESS',
                        meta={
                            'current': idx,
                            'total': total_rows,
                            'percent': progress_percent
                        }
                    )
                except Exception as celery_error:
                    logger.error(f"Failed to update Celery state: {celery_error}")

        if batch:
            db.bulk_save_objects(batch)
            db.commit()
            records_created += len(batch)

        # Mark as complete or failed based on duplicates
        if duplicate_count > 0:
            dataset_uuid = UUID(dataset_id)
            if records_created > 0:
                _cleanup_dataset_records(db, dataset_uuid)
                records_created = 0

            max_duplicates_to_report = 10
            duplicate_sample = duplicate_ids[:max_duplicates_to_report]

            if duplicate_count <= max_duplicates_to_report:
                error_msg = f"Found {duplicate_count} duplicate customerID value(s): {', '.join(duplicate_sample)}"
            else:
                error_msg = f"Found {duplicate_count} duplicate customerID value(s). First {max_duplicates_to_report}: {', '.join(duplicate_sample)}"

            DatasetService.update_dataset_status(
                db,
                dataset_uuid,
                status="failed",
                validation_errors={"duplicates": error_msg, "duplicate_ids": duplicate_ids},
            )
            _invalidate_dashboard_cache()

            # Mark as failed in Redis
            cache_client.set_json(
                progress_key,
                {
                    "status": "failed",
                    "progress": 100,
                    "total_records": total_rows,
                    "processed_records": records_created,
                    "current_step": "Failed",
                    "error": error_msg,
                    "failed_at": datetime.utcnow().isoformat(),
                },
                ttl=3600
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
        _invalidate_dashboard_cache()

        # Mark as complete in Redis
        cache_client.set_json(
            progress_key,
            {
                "status": "completed",
                "progress": 100,
                "total_records": total_rows,
                "processed_records": records_created,
                "current_step": "Complete",
                "completed_at": datetime.utcnow().isoformat(),
            },
            ttl=3600
        )

        logger.info(f"Successfully processed dataset {dataset_id}: {records_created} records")

        # Create notification for successful processing
        try:
            from backend.services.notification_service import NotificationService
            dataset = DatasetService.get_dataset_by_id(db, UUID(dataset_id))
            if dataset:
                notification_service = NotificationService()
                notification_service.create_dataset_notification(
                    db=db,
                    user_id=dataset.user_id,
                    dataset_id=UUID(dataset_id),
                    filename=dataset.filename,
                    status="ready",
                    record_count=records_created,
                )
                logger.info(f"Created completion notification for dataset {dataset_id}")
        except Exception as notif_error:
            logger.error(f"Failed to create dataset notification: {notif_error}", exc_info=True)

        return {
            "success": True,
            "records_created": records_created,
            "duplicate_count": duplicate_count,
        }

    except Exception as e:
        logger.error(f"Error processing dataset {dataset_id}: {e}", exc_info=True)

        dataset_uuid = UUID(dataset_id)
        try:
            _cleanup_dataset_records(db, dataset_uuid)
        except Exception as cleanup_error:
            logger.error(
                f"Failed to clean up partial records for dataset {dataset_id}: {cleanup_error}",
                exc_info=True,
            )

        DatasetService.update_dataset_status(
            db, dataset_uuid, status="failed", validation_errors={"error": str(e)}
        )
        _invalidate_dashboard_cache()

        # Mark as failed in Redis
        from backend.infrastructure.cache import cache_client
        from datetime import datetime

        progress_key = f"dataset:progress:{dataset_id}"
        cache_client.set_json(
            progress_key,
            {
                "status": "failed",
                "error": str(e),
                "failed_at": datetime.utcnow().isoformat(),
            },
            ttl=3600
        )

        # Create notification for failed processing
        try:
            from backend.services.notification_service import NotificationService
            dataset = DatasetService.get_dataset_by_id(db, UUID(dataset_id))
            if dataset:
                notification_service = NotificationService()
                notification_service.create_dataset_notification(
                    db=db,
                    user_id=dataset.user_id,
                    dataset_id=UUID(dataset_id),
                    filename=dataset.filename,
                    status="failed",
                    failure_reason=str(e),
                )
        except Exception as notif_error:
            logger.error(f"Failed to create failure notification: {notif_error}", exc_info=True)

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
