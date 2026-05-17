import io
import logging
import time
from typing import Any, Callable, Dict, Optional, Tuple
from uuid import UUID

import joblib
import numpy as np
import optuna
import pandas as pd
from optuna.trial import FrozenTrial
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

from backend.domain.models.model_version import ModelVersion
from backend.infrastructure.storage import storage_client
from backend.services.preprocessing_service import PreprocessingService

logger = logging.getLogger(__name__)


class MLTrainingService:
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
        progress_callback: Optional[Callable[[int, Optional[int], Optional[int]], None]] = None,
    ) -> ModelVersion:
        start_time = time.time()

        if model_type not in MLTrainingService.MODEL_CLASSES:
            raise ValueError(
                f"Invalid model type: {model_type}. "
                f"Must be one of: {list(MLTrainingService.MODEL_CLASSES.keys())}"
            )

        logger.info(
            f"Starting model training: {model_type} for user {user_id}, "
            f"dataset {dataset_id}, optimize={optimize_hyperparameters}"
        )

        def emit_progress(
            progress: int,
            current_iteration: Optional[int] = None,
            total_iterations: Optional[int] = None,
        ) -> None:
            if progress_callback:
                progress_callback(progress, current_iteration, total_iterations)

        preprocessed_data = PreprocessingService.preprocess_dataset(
            db=db, dataset_id=dataset_id, test_size=0.2, random_state=42, apply_smote=True
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
        emit_progress(25)

        if optimize_hyperparameters:
            hyperparameters = MLTrainingService._optimize_hyperparameters(
                model_type=model_type,
                X_train=X_train,
                y_train=y_train,
                progress_callback=lambda current, total: emit_progress(
                    30 + int((current / max(total, 1)) * 40),
                    current,
                    total,
                ),
            )
            logger.info(f"Optimized hyperparameters: {hyperparameters}")
        elif hyperparameters is None:
            hyperparameters = MLTrainingService._get_default_hyperparameters(model_type)
            logger.info(f"Using default hyperparameters: {hyperparameters}")

        emit_progress(70)

        model_class = MLTrainingService.MODEL_CLASSES[model_type]
        model = model_class(**hyperparameters)

        logger.info(f"Training {model_type} model...")
        emit_progress(80)
        model.fit(X_train, y_train)

        training_time = time.time() - start_time
        logger.info(f"Model training complete in {training_time:.2f} seconds")

        metrics, conf_matrix = MLTrainingService._evaluate_model(
            model=model, X_test=X_test, y_test=y_test
        )
        emit_progress(90)

        logger.info(
            f"Model evaluation: accuracy={metrics['accuracy']:.4f}, "
            f"f1_score={metrics['f1_score']:.4f}, roc_auc={metrics['roc_auc']:.4f}"
        )

        model_bytes = MLTrainingService._serialize_model(model)

        version = MLTrainingService._generate_version(model_type, dataset_id)

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
            artifact_path="",
            status="active",
            classification_threshold=0.5,
        )

        db.add(model_version)
        db.flush()

        artifact_path = storage_client.upload_model_artifact(
            user_id=user_id,
            model_version_id=model_version.id,
            file_data=model_bytes,
            filename="model.joblib",
        )
        emit_progress(95)

        model_version.artifact_path = artifact_path

        db.commit()
        db.refresh(model_version)

        logger.info(
            f"Model version created: {model_version.id} ({model_version.version}), "
            f"artifact_path={artifact_path}"
        )

        return model_version

    @staticmethod
    def _get_default_hyperparameters(model_type: str) -> Dict[str, Any]:
        defaults = {
            "KNN": {"n_neighbors": 5, "weights": "uniform", "metric": "euclidean"},
            "NaiveBayes": {"var_smoothing": 1e-9},
            "DecisionTree": {
                "max_depth": 10,
                "min_samples_split": 2,
                "criterion": "gini",
                "random_state": 42,
            },
            "SVM": {
                "C": 1.0,
                "kernel": "linear",
                "gamma": "scale",
                "probability": True,
                "random_state": 42,
                "cache_size": 512,
                "max_iter": 1500,
            },
        }

        return defaults.get(model_type, {})

    @staticmethod
    def _optimize_hyperparameters(
        model_type: str,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        n_trials: int = 50,
        cv_folds: int = 5,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Dict[str, Any]:
        if model_type == "SVM":
            n_trials = min(n_trials, 12)
            cv_folds = min(cv_folds, 3)

        logger.info(
            f"Starting hyperparameter optimization for {model_type}: "
            f"{n_trials} trials, {cv_folds}-fold CV"
        )

        def objective(trial: optuna.Trial) -> float:
            if model_type == "KNN":
                params = {
                    "n_neighbors": trial.suggest_int("n_neighbors", 1, 50),
                    "weights": trial.suggest_categorical("weights", ["uniform", "distance"]),
                    "metric": trial.suggest_categorical("metric", ["euclidean", "manhattan"]),
                }

            elif model_type == "NaiveBayes":
                params = {
                    "var_smoothing": trial.suggest_float("var_smoothing", 1e-11, 1e-7, log=True)
                }

            elif model_type == "DecisionTree":
                params = {
                    "max_depth": trial.suggest_int("max_depth", 1, 20),
                    "min_samples_split": trial.suggest_int("min_samples_split", 2, 20),
                    "criterion": trial.suggest_categorical("criterion", ["gini", "entropy"]),
                    "random_state": 42,
                }

            elif model_type == "SVM":
                params = {
                    "C": trial.suggest_float("C", 0.1, 10.0, log=True),
                    "kernel": trial.suggest_categorical("kernel", ["linear", "rbf"]),
                    "gamma": trial.suggest_categorical("gamma", ["scale", "auto"]),
                    "probability": False,
                    "random_state": 42,
                    "cache_size": 512,
                    "max_iter": 1500,
                }

            else:
                raise ValueError(f"Unknown model type: {model_type}")

            model_class = MLTrainingService.MODEL_CLASSES[model_type]
            model = model_class(**params)

            cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42)
            scores = cross_val_score(model, X_train, y_train, cv=cv, scoring="f1", n_jobs=-1)

            return scores.mean()

        study = optuna.create_study(
            direction="maximize", sampler=optuna.samplers.TPESampler(seed=42)
        )

        def handle_trial_complete(study: optuna.Study, trial: FrozenTrial) -> None:
            if progress_callback:
                progress_callback(trial.number + 1, n_trials)

        study.optimize(
            objective,
            n_trials=n_trials,
            show_progress_bar=False,
            callbacks=[handle_trial_complete],
        )

        best_params = study.best_params

        if model_type == "SVM":
            best_params["probability"] = True
            best_params["random_state"] = 42
            best_params["cache_size"] = 512
            best_params["max_iter"] = 1500
        elif model_type == "DecisionTree":
            best_params["random_state"] = 42

        logger.info(
            f"Hyperparameter optimization complete: best_f1={study.best_value:.4f}, "
            f"params={best_params}"
        )

        return best_params

    @staticmethod
    def _evaluate_model(
        model: Any, X_test: pd.DataFrame, y_test: pd.Series
    ) -> Tuple[Dict[str, float], np.ndarray]:
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]

        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)

        roc_auc = roc_auc_score(y_test, y_pred_proba)

        conf_matrix = confusion_matrix(y_test, y_pred)

        metrics = {
            "accuracy": float(accuracy),
            "precision": float(precision),
            "recall": float(recall),
            "f1_score": float(f1),
            "roc_auc": float(roc_auc),
        }

        return metrics, conf_matrix

    @staticmethod
    def _serialize_model(model: Any) -> bytes:
        buffer = io.BytesIO()
        joblib.dump(model, buffer)
        buffer.seek(0)
        return buffer.read()

    @staticmethod
    def _generate_version(model_type: str, dataset_id: UUID) -> str:
        import datetime

        timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        dataset_short = str(dataset_id)[:8]
        return f"{model_type}_{dataset_short}_{timestamp}"

    @staticmethod
    def load_model_from_storage(model_version: ModelVersion) -> Any:
        model_bytes = storage_client.download_model_artifact(model_version.artifact_path)

        buffer = io.BytesIO(model_bytes)
        model = joblib.load(buffer)

        logger.info(f"Loaded model from storage: {model_version.id}")

        return model
