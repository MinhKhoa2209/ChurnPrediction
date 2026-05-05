"""
Machine Learning Model Training Service
- Training KNN, Naive Bayes, Decision Tree, SVM classifiers
- Hyperparameter optimization with Optuna
- Model evaluation on test set
- Model serialization and R2 storage
- MLflow experiment tracking
- Model version creation
"""

import io
import logging
import time
from typing import Any, Dict, Optional, Tuple
from uuid import UUID

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sqlalchemy.orm import Session
import optuna

from backend.domain.models.dataset import Dataset
from backend.domain.models.model_version import ModelVersion
from backend.infrastructure.mlflow_client import mlflow_tracker
from backend.infrastructure.storage import storage_client
from backend.services.preprocessing_service import PreprocessingService

logger = logging.getLogger(__name__)


class MLTrainingService:
    """Service for training and evaluating ML models"""
    
    # Model type mapping
    MODEL_CLASSES = {
        "KNN": KNeighborsClassifier,
        "NaiveBayes": GaussianNB,
        "DecisionTree": DecisionTreeClassifier,
        "SVM": SVC,
    }
    
    @staticmethod
    def train_model(
        db: Session,
        user_id: UUID,
        dataset_id: UUID,
        model_type: str,
        hyperparameters: Optional[Dict[str, Any]] = None,
        optimize_hyperparameters: bool = False,
    ) -> ModelVersion:
        """
        Train a machine learning model
        
        - 8.2: Support training Naive Bayes classifiers
        - 8.3: Support training Decision Tree classifiers
        - 8.4: Support training Support Vector Machine (SVM) classifiers
        - 8.8: Store Model_Version in Database when complete
        - 8.9: Complete training within 60 seconds for 4 models on 5,634 records
        - 9.1-9.8: Hyperparameter optimization with Optuna
        - 15.2: Store training metadata
        - 15.3: Store serialized ML_Model artifact in R2_Storage
        - 15.7: Integrate with MLflow for experiment tracking
        
        Args:
            db: Database session
            user_id: User UUID
            dataset_id: Dataset UUID
            model_type: Model type (KNN, NaiveBayes, DecisionTree, SVM)
            hyperparameters: Optional hyperparameters (if None, uses defaults or optimization)
            optimize_hyperparameters: Whether to use Optuna for hyperparameter optimization
            
        Returns:
            Created ModelVersion instance
        """
        start_time = time.time()
        
        # Validate model type
        if model_type not in MLTrainingService.MODEL_CLASSES:
            raise ValueError(
                f"Invalid model type: {model_type}. "
                f"Must be one of: {list(MLTrainingService.MODEL_CLASSES.keys())}"
            )
        
        logger.info(
            f"Starting model training: {model_type} for user {user_id}, "
            f"dataset {dataset_id}, optimize={optimize_hyperparameters}"
        )
        
        # Step 1: Preprocess dataset
        preprocessed_data = PreprocessingService.preprocess_dataset(
            db=db,
            dataset_id=dataset_id,
            test_size=0.2,
            random_state=42,
            apply_smote=True
        )
        
        X_train = preprocessed_data["X_train"]
        X_test = preprocessed_data["X_test"]
        y_train = preprocessed_data["y_train"]
        y_test = preprocessed_data["y_test"]
        preprocessing_config_id = preprocessed_data["preprocessing_config_id"]
        
        logger.info(
            f"Preprocessing complete: train_size={len(X_train)}, "
            f"test_size={len(X_test)}, features={len(X_train.columns)}"
        )
        
        # Step 2: Get or optimize hyperparameters
        if optimize_hyperparameters:
            # Requirement 9.1-9.8: Use Optuna for hyperparameter optimization
            hyperparameters = MLTrainingService._optimize_hyperparameters(
                model_type=model_type,
                X_train=X_train,
                y_train=y_train
            )
            logger.info(f"Optimized hyperparameters: {hyperparameters}")
        elif hyperparameters is None:
            # Use default hyperparameters
            hyperparameters = MLTrainingService._get_default_hyperparameters(model_type)
            logger.info(f"Using default hyperparameters: {hyperparameters}")
        
        # Step 3: Train model
        model_class = MLTrainingService.MODEL_CLASSES[model_type]
        model = model_class(**hyperparameters)
        
        logger.info(f"Training {model_type} model...")
        model.fit(X_train, y_train)
        
        training_time = time.time() - start_time
        logger.info(f"Model training complete in {training_time:.2f} seconds")
        
        # Step 4: Evaluate model
        metrics, conf_matrix = MLTrainingService._evaluate_model(
            model=model,
            X_test=X_test,
            y_test=y_test
        )
        
        logger.info(
            f"Model evaluation: accuracy={metrics['accuracy']:.4f}, "
            f"f1_score={metrics['f1_score']:.4f}, roc_auc={metrics['roc_auc']:.4f}"
        )
        
        # Step 5: Serialize model
        model_bytes = MLTrainingService._serialize_model(model)
        
        # Step 6: Generate version identifier
        version = MLTrainingService._generate_version(model_type, dataset_id)
        
        # Step 7: Create ModelVersion record (before uploading to R2)
        model_version = ModelVersion(
            user_id=user_id,
            dataset_id=dataset_id,
            preprocessing_config_id=preprocessing_config_id,
            model_type=model_type,
            version=version,
            hyperparameters=hyperparameters,
            metrics=metrics,
            confusion_matrix=conf_matrix.tolist(),
            training_time_seconds=training_time,
            artifact_path="",  # Will be updated after upload
            status="active",
            classification_threshold=0.5,
        )
        
        db.add(model_version)
        db.flush()  # Get the ID without committing
        
        # Step 8: Upload to R2 storage (Requirement 15.3, 33.1, 33.2)
        artifact_path = storage_client.upload_model_artifact(
            user_id=user_id,
            model_version_id=model_version.id,
            file_data=model_bytes,
            filename="model.joblib"
        )
        
        # Update artifact path
        model_version.artifact_path = artifact_path
        
        # Step 9: Log to MLflow (Requirement 15.7)
        try:
            mlflow_run_id = mlflow_tracker.log_model_training(
                model_type=model_type,
                model_version_id=model_version.id,
                dataset_id=dataset_id,
                hyperparameters=hyperparameters,
                metrics=metrics,
                training_time=training_time,
                user_id=user_id
            )
            model_version.mlflow_run_id = mlflow_run_id
        except Exception as e:
            logger.error(f"Failed to log to MLflow: {e}")
            # Continue without MLflow logging
        
        # Commit to database
        db.commit()
        db.refresh(model_version)
        
        logger.info(
            f"Model version created: {model_version.id} ({model_version.version}), "
            f"artifact_path={artifact_path}"
        )
        
        return model_version
    
    @staticmethod
    def _get_default_hyperparameters(model_type: str) -> Dict[str, Any]:
        """
        Get default hyperparameters for each model type
        
        Args:
            model_type: Model type
            
        Returns:
            Dictionary of default hyperparameters
        """
        defaults = {
            "KNN": {
                "n_neighbors": 5,
                "weights": "uniform",
                "metric": "euclidean"
            },
            "NaiveBayes": {
                "var_smoothing": 1e-9
            },
            "DecisionTree": {
                "max_depth": 10,
                "min_samples_split": 2,
                "criterion": "gini",
                "random_state": 42
            },
            "SVM": {
                "C": 1.0,
                "kernel": "rbf",
                "gamma": "scale",
                "probability": True,  # Required for predict_proba
                "random_state": 42
            }
        }
        
        return defaults.get(model_type, {})
    
    @staticmethod
    def _optimize_hyperparameters(
        model_type: str,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        n_trials: int = 50,
        cv_folds: int = 5
    ) -> Dict[str, Any]:
        """
        Optimize hyperparameters using Optuna
        
        - 9.2: Perform 50 optimization trials per ML_Model
        - 9.3-9.6: Optimize specific hyperparameters for each model type
        - 9.7: Evaluate using 5-Fold Stratified Cross-Validation, scoring by F1-score
        - 9.8: Store optimal hyperparameters
        
        Args:
            model_type: Model type
            X_train: Training features
            y_train: Training labels
            n_trials: Number of optimization trials (default 50)
            cv_folds: Number of cross-validation folds (default 5)
            
        Returns:
            Dictionary of optimal hyperparameters
        """
        logger.info(
            f"Starting hyperparameter optimization for {model_type}: "
            f"{n_trials} trials, {cv_folds}-fold CV"
        )
        
        def objective(trial: optuna.Trial) -> float:
            """Optuna objective function"""
            
            # Define hyperparameter search space based on model type
            if model_type == "KNN":
                # Requirement 9.3: KNN hyperparameters
                params = {
                    "n_neighbors": trial.suggest_int("n_neighbors", 1, 50),
                    "weights": trial.suggest_categorical("weights", ["uniform", "distance"]),
                    "metric": trial.suggest_categorical("metric", ["euclidean", "manhattan"])
                }
            
            elif model_type == "NaiveBayes":
                # Requirement 9.4: Naive Bayes hyperparameters
                params = {
                    "var_smoothing": trial.suggest_float("var_smoothing", 1e-11, 1e-7, log=True)
                }
            
            elif model_type == "DecisionTree":
                # Requirement 9.5: Decision Tree hyperparameters
                params = {
                    "max_depth": trial.suggest_int("max_depth", 1, 20),
                    "min_samples_split": trial.suggest_int("min_samples_split", 2, 20),
                    "criterion": trial.suggest_categorical("criterion", ["gini", "entropy"]),
                    "random_state": 42
                }
            
            elif model_type == "SVM":
                # Requirement 9.6: SVM hyperparameters
                params = {
                    "C": trial.suggest_float("C", 0.01, 100.0, log=True),
                    "kernel": trial.suggest_categorical("kernel", ["linear", "rbf", "poly"]),
                    "gamma": trial.suggest_categorical("gamma", ["scale", "auto"]),
                    "probability": True,  # Required for predict_proba
                    "random_state": 42
                }
            
            else:
                raise ValueError(f"Unknown model type: {model_type}")
            
            # Create model with trial hyperparameters
            model_class = MLTrainingService.MODEL_CLASSES[model_type]
            model = model_class(**params)
            
            # Requirement 9.7: 5-Fold Stratified Cross-Validation, scoring by F1-score
            cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42)
            scores = cross_val_score(
                model,
                X_train,
                y_train,
                cv=cv,
                scoring="f1",  # Optimize for F1-score to handle class imbalance
                n_jobs=-1
            )
            
            return scores.mean()
        
        # Create Optuna study
        study = optuna.create_study(
            direction="maximize",  # Maximize F1-score
            sampler=optuna.samplers.TPESampler(seed=42)
        )
        
        # Optimize
        study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
        
        # Get best hyperparameters
        best_params = study.best_params
        
        # Add fixed parameters for SVM and DecisionTree
        if model_type == "SVM":
            best_params["probability"] = True
            best_params["random_state"] = 42
        elif model_type == "DecisionTree":
            best_params["random_state"] = 42
        
        logger.info(
            f"Hyperparameter optimization complete: best_f1={study.best_value:.4f}, "
            f"params={best_params}"
        )
        
        return best_params
    
    @staticmethod
    def _evaluate_model(
        model: Any,
        X_test: pd.DataFrame,
        y_test: pd.Series
    ) -> Tuple[Dict[str, float], np.ndarray]:
        """
        Evaluate model on test set
        
        - 10.2: Compute Confusion_Matrix
        - 10.3: Compute ROC-AUC score
        
        Args:
            model: Trained model
            X_test: Test features
            y_test: Test labels
            
        Returns:
            Tuple of (metrics dict, confusion matrix)
        """
        # Make predictions
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        
        # Compute metrics (Requirement 10.1)
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        
        # Compute ROC-AUC (Requirement 10.3)
        roc_auc = roc_auc_score(y_test, y_pred_proba)
        
        # Compute confusion matrix (Requirement 10.2)
        conf_matrix = confusion_matrix(y_test, y_pred)
        
        metrics = {
            "accuracy": float(accuracy),
            "precision": float(precision),
            "recall": float(recall),
            "f1_score": float(f1),
            "roc_auc": float(roc_auc)
        }
        
        return metrics, conf_matrix
    
    @staticmethod
    def _serialize_model(model: Any) -> bytes:
        """
        Serialize model to bytes using joblib
        
        Args:
            model: Trained model
            
        Returns:
            Serialized model as bytes
        """
        buffer = io.BytesIO()
        joblib.dump(model, buffer)
        buffer.seek(0)
        return buffer.read()
    
    @staticmethod
    def _generate_version(model_type: str, dataset_id: UUID) -> str:
        """
        Generate unique version identifier for model
        
        Args:
            model_type: Model type
            dataset_id: Dataset UUID
            
        Returns:
            Version string
        """
        import datetime
        timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        dataset_short = str(dataset_id)[:8]
        return f"{model_type}_{dataset_short}_{timestamp}"
    
    @staticmethod
    def load_model_from_storage(model_version: ModelVersion) -> Any:
        """
        Load model from R2 storage
        
        Args:
            model_version: ModelVersion instance
            
        Returns:
            Loaded model
        """
        # Download model from R2
        model_bytes = storage_client.download_model_artifact(model_version.artifact_path)
        
        # Deserialize model
        buffer = io.BytesIO(model_bytes)
        model = joblib.load(buffer)
        
        logger.info(f"Loaded model from storage: {model_version.id}")
        
        return model
