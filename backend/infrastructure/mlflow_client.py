import logging
from typing import Any, Dict, Optional
from uuid import UUID

import mlflow
from mlflow.tracking import MlflowClient

from backend.config import settings

logger = logging.getLogger(__name__)


class MLflowTracker:
    def __init__(self):
        mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
        self.client = MlflowClient()
        self.experiment_name = settings.mlflow_experiment_name

        try:
            self.experiment = mlflow.get_experiment_by_name(self.experiment_name)
            if self.experiment is None:
                experiment_id = mlflow.create_experiment(self.experiment_name)
                self.experiment = mlflow.get_experiment(experiment_id)
                logger.info(f"Created MLflow experiment: {self.experiment_name}")
            else:
                logger.info(f"Using existing MLflow experiment: {self.experiment_name}")
        except Exception as e:
            logger.warning(f"Failed to initialize MLflow experiment (will retry on first use): {e}")
            self.experiment = None

    def start_run(self, run_name: str, tags: Optional[Dict[str, str]] = None) -> str:
        try:
            if self.experiment is None:
                self.experiment = mlflow.get_experiment_by_name(self.experiment_name)
                if self.experiment is None:
                    experiment_id = mlflow.create_experiment(self.experiment_name)
                    self.experiment = mlflow.get_experiment(experiment_id)

            run = mlflow.start_run(
                experiment_id=self.experiment.experiment_id, run_name=run_name, tags=tags or {}
            )
            logger.info(f"Started MLflow run: {run.info.run_id} ({run_name})")
            return run.info.run_id
        except Exception as e:
            logger.error(f"Failed to start MLflow run: {e}")
            raise

    def log_params(self, params: Dict[str, Any]) -> None:
        try:
            mlflow.log_params(params)
            logger.debug(f"Logged {len(params)} parameters to MLflow")
        except Exception as e:
            logger.error(f"Failed to log parameters to MLflow: {e}")
            raise

    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None) -> None:
        try:
            mlflow.log_metrics(metrics, step=step)
            logger.debug(f"Logged {len(metrics)} metrics to MLflow")
        except Exception as e:
            logger.error(f"Failed to log metrics to MLflow: {e}")
            raise

    def log_artifact(self, local_path: str, artifact_path: Optional[str] = None) -> None:
        try:
            mlflow.log_artifact(local_path, artifact_path=artifact_path)
            logger.debug(f"Logged artifact to MLflow: {local_path}")
        except Exception as e:
            logger.error(f"Failed to log artifact to MLflow: {e}")
            raise

    def end_run(self, status: str = "FINISHED") -> None:
        try:
            mlflow.end_run(status=status)
            logger.info(f"Ended MLflow run with status: {status}")
        except Exception as e:
            logger.error(f"Failed to end MLflow run: {e}")
            raise

    def log_model_training(
        self,
        model_type: str,
        model_version_id: UUID,
        dataset_id: UUID,
        hyperparameters: Dict[str, Any],
        metrics: Dict[str, float],
        training_time: float,
        user_id: UUID,
    ) -> str:
        run_name = f"{model_type}_{model_version_id}"

        tags = {
            "model_type": model_type,
            "model_version_id": str(model_version_id),
            "dataset_id": str(dataset_id),
            "user_id": str(user_id),
        }

        try:
            run_id = self.start_run(run_name=run_name, tags=tags)

            self.log_params(hyperparameters)

            metrics_with_time = {**metrics, "training_time_seconds": training_time}
            self.log_metrics(metrics_with_time)

            self.end_run(status="FINISHED")

            logger.info(
                f"Logged model training to MLflow: {model_type} "
                f"(run_id={run_id}, f1_score={metrics.get('f1_score', 0):.4f})"
            )

            return run_id

        except Exception as e:
            logger.error(f"Failed to log model training to MLflow: {e}")
            try:
                self.end_run(status="FAILED")
            except Exception:
                pass
            raise


mlflow_tracker = MLflowTracker()
