import logging
from typing import Optional
from uuid import UUID

from sklearn.metrics import roc_curve
from sqlalchemy.orm import Session

from backend.domain.models.model_version import ModelVersion
from backend.services.ml_training_service import MLTrainingService
from backend.services.preprocessing_service import PreprocessingService

logger = logging.getLogger(__name__)


class ModelEvaluationService:
    @staticmethod
    def get_model_version_by_id(
        db: Session, version_id: UUID, user_id: Optional[UUID] = None
    ) -> Optional[ModelVersion]:
        query = db.query(ModelVersion).filter(ModelVersion.id == version_id)

        if user_id:
            query = query.filter(ModelVersion.user_id == user_id)

        return query.first()

    @staticmethod
    def list_model_versions(
        db: Session,
        user_id: Optional[UUID] = None,
        model_type: Optional[str] = None,
        status: Optional[str] = None,
        sort_by: str = "trained_at",
        sort_order: str = "desc",
    ) -> list[ModelVersion]:
        query = db.query(ModelVersion)

        if user_id:
            query = query.filter(ModelVersion.user_id == user_id)

        if model_type:
            query = query.filter(ModelVersion.model_type == model_type)

        if status:
            query = query.filter(ModelVersion.status == status)

        valid_sort_columns = {
            "trained_at",
            "model_type",
            "version",
            "training_time_seconds",
            "status",
            "classification_threshold",
        }

        if sort_by not in valid_sort_columns:
            if sort_by in ["accuracy", "precision", "recall", "f1_score", "roc_auc"]:
                sort_column = ModelVersion.metrics[sort_by].astext.cast(db.bind.dialect.NUMERIC)
            else:
                sort_column = ModelVersion.trained_at
        else:
            sort_column = getattr(ModelVersion, sort_by)

        if sort_order.lower() == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        return query.all()

    @staticmethod
    def compute_roc_curve(db: Session, version_id: UUID, user_id: Optional[UUID] = None) -> dict:
        model_version = ModelEvaluationService.get_model_version_by_id(
            db=db, version_id=version_id, user_id=user_id
        )

        if not model_version:
            raise ValueError(f"Model version {version_id} not found")

        logger.info(f"Computing ROC curve for model version {version_id}")

        preprocessed_data = PreprocessingService.preprocess_dataset(
            db=db,
            dataset_id=model_version.dataset_id,
            test_size=0.2,
            random_state=42,
            apply_smote=True,
        )

        X_test = preprocessed_data["X_test"]
        y_test = preprocessed_data["y_test"]

        model = MLTrainingService.load_model_from_storage(model_version)

        y_pred_proba = model.predict_proba(X_test)[:, 1]

        fpr, tpr, thresholds = roc_curve(y_test, y_pred_proba)

        points = []
        for i in range(len(fpr)):
            points.append(
                {
                    "fpr": float(fpr[i]),
                    "tpr": float(tpr[i]),
                    "threshold": float(thresholds[i]) if i < len(thresholds) else 0.0,
                }
            )

        auc = model_version.metrics.get("roc_auc", 0.0)

        logger.info(f"ROC curve computed: {len(points)} points, AUC={auc:.4f}")

        return {"points": points, "auc": auc}

    @staticmethod
    def update_classification_threshold(
        db: Session, version_id: UUID, threshold: float, user_id: Optional[UUID] = None
    ) -> ModelVersion:
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("Threshold must be between 0.0 and 1.0")

        model_version = ModelEvaluationService.get_model_version_by_id(
            db=db, version_id=version_id, user_id=user_id
        )

        if not model_version:
            raise ValueError(f"Model version {version_id} not found")

        logger.info(
            f"Updating threshold for model {version_id}: "
            f"{model_version.classification_threshold} -> {threshold}"
        )

        model_version.classification_threshold = threshold

        db.commit()
        db.refresh(model_version)

        logger.info(f"Threshold updated successfully for model {version_id}")

        return model_version

    @staticmethod
    def archive_model_version(
        db: Session, version_id: UUID, archive: bool, user_id: Optional[UUID] = None
    ) -> ModelVersion:
        from datetime import datetime

        model_version = ModelEvaluationService.get_model_version_by_id(
            db=db, version_id=version_id, user_id=user_id
        )

        if not model_version:
            raise ValueError(f"Model version {version_id} not found")

        new_status = "archived" if archive else "active"

        logger.info(
            f"Changing model {version_id} status: " f"{model_version.status} -> {new_status}"
        )

        model_version.status = new_status

        if archive:
            model_version.archived_at = datetime.utcnow()
        else:
            model_version.archived_at = None

        db.commit()
        db.refresh(model_version)

        logger.info(f"Model {version_id} status updated to {new_status}")

        return model_version
