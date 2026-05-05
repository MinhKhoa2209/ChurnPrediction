"""
MLflow Client for Experiment Tracking
logging hyperparameters, metrics, and artifacts.
"""

import logging
from typing import Any, Dict, Optional
from uuid import UUID

import mlflow
from mlflow.tracking import MlflowClient

from backend.config import settings

logger = logging.getLogger(__name__)


class MLflowTracker:
    """MLflow client for experiment tracking"""
    
    def __init__(self):
        """Initialize MLflow client with tracking URI from settings"""
        mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
        self.client = MlflowClient()
        self.experiment_name = settings.mlflow_experiment_name
        
        # Create experiment if it doesn't exist
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
    
    def start_run(
        self,
        run_name: str,
        tags: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Start a new MLflow run
        
        Args:
            run_name: Name for the run
            tags: Optional tags for the run
            
        Returns:
            MLflow run ID
        """
        try:
            # Ensure experiment is initialized
            if self.experiment is None:
                self.experiment = mlflow.get_experiment_by_name(self.experiment_name)
                if self.experiment is None:
                    experiment_id = mlflow.create_experiment(self.experiment_name)
                    self.experiment = mlflow.get_experiment(experiment_id)
            
            run = mlflow.start_run(
                experiment_id=self.experiment.experiment_id,
                run_name=run_name,
                tags=tags or {}
            )
            logger.info(f"Started MLflow run: {run.info.run_id} ({run_name})")
            return run.info.run_id
        except Exception as e:
            logger.error(f"Failed to start MLflow run: {e}")
            raise
    
    def log_params(self, params: Dict[str, Any]) -> None:
        """
        Log hyperparameters to current MLflow run
        
        Args:
            params: Dictionary of hyperparameters
        """
        try:
            mlflow.log_params(params)
            logger.debug(f"Logged {len(params)} parameters to MLflow")
        except Exception as e:
            logger.error(f"Failed to log parameters to MLflow: {e}")
            raise
    
    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None) -> None:
        """
        Log metrics to current MLflow run
        
        Args:
            metrics: Dictionary of metric values
            step: Optional step number for time-series metrics
        """
        try:
            mlflow.log_metrics(metrics, step=step)
            logger.debug(f"Logged {len(metrics)} metrics to MLflow")
        except Exception as e:
            logger.error(f"Failed to log metrics to MLflow: {e}")
            raise
    
    def log_artifact(self, local_path: str, artifact_path: Optional[str] = None) -> None:
        """
        Log artifact file to current MLflow run
        
        Args:
            local_path: Local file path to upload
            artifact_path: Optional subdirectory in artifact store
        """
        try:
            mlflow.log_artifact(local_path, artifact_path=artifact_path)
            logger.debug(f"Logged artifact to MLflow: {local_path}")
        except Exception as e:
            logger.error(f"Failed to log artifact to MLflow: {e}")
            raise
    
    def end_run(self, status: str = "FINISHED") -> None:
        """
        End the current MLflow run
        
        Args:
            status: Run status (FINISHED, FAILED, KILLED)
        """
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
        user_id: UUID
    ) -> str:
        """
        Log complete model training run to MLflow
        Requirement 15.7: Integrate with MLflow for experiment tracking
        
        Args:
            model_type: Type of model (KNN, NaiveBayes, DecisionTree, SVM)
            model_version_id: Model version UUID
            dataset_id: Dataset UUID
            hyperparameters: Model hyperparameters
            metrics: Evaluation metrics
            training_time: Training time in seconds
            user_id: User UUID
            
        Returns:
            MLflow run ID
        """
        run_name = f"{model_type}_{model_version_id}"
        
        tags = {
            "model_type": model_type,
            "model_version_id": str(model_version_id),
            "dataset_id": str(dataset_id),
            "user_id": str(user_id),
        }
        
        try:
            run_id = self.start_run(run_name=run_name, tags=tags)
            
            # Log hyperparameters
            self.log_params(hyperparameters)
            
            # Log metrics
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
            except:
                pass
            raise


# Global MLflow tracker instance
mlflow_tracker = MLflowTracker()
