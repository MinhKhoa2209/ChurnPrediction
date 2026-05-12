import base64
import hashlib
import io
import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

import joblib
import numpy as np
import redis
import shap
from sqlalchemy.orm import Session

from backend.domain.models.model_version import ModelVersion
from backend.domain.models.prediction import Prediction
from backend.domain.models.preprocessing_config import PreprocessingConfig
from backend.infrastructure.storage import storage_client
from backend.services.prediction_preprocessing_service import (
    PredictionPreprocessingError,
    PredictionPreprocessingService,
)

logger = logging.getLogger(__name__)


class PredictionServiceError(Exception):
    pass


class ModelNotFoundError(PredictionServiceError):
    pass


class ModelLoadError(PredictionServiceError):
    pass


class PredictionTimeoutError(PredictionServiceError):
    pass


class SHAPComputationError(PredictionServiceError):
    pass


class PredictionService:
    MODEL_CACHE_TTL = 6 * 60 * 60

    PREDICTION_CACHE_TTL = 60 * 60

    MAX_PREDICTION_TIME_MS = 200

    MAX_SHAP_COMPUTATION_TIME_MS = 500

    TOP_CONTRIBUTORS_COUNT = 5

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self._cache_enabled = redis_client is not None

        if self._cache_enabled:
            logger.info("Prediction service initialized with caching enabled")
        else:
            logger.warning(
                "Prediction service initialized without caching (performance may be degraded)"
            )

    def generate_prediction(
        self,
        db: Session,
        user_id: UUID,
        model_version_id: UUID,
        input_data: Dict[str, Any],
        store_prediction: bool = True,
    ) -> Prediction:
        start_time = time.time()

        model_version = db.query(ModelVersion).filter(ModelVersion.id == model_version_id).first()

        if not model_version:
            raise ModelNotFoundError(f"Model version {model_version_id} not found")

        if model_version.status != "active":
            raise ModelNotFoundError(
                f"Model version {model_version_id} is {model_version.status} and cannot be used for predictions"
            )

        input_hash = self._hash_input(input_data)
        cached_prediction_payload = self._get_cached_prediction_payload(model_version_id, input_hash)

        if cached_prediction_payload:
            prediction = Prediction(
                user_id=user_id,
                model_version_id=model_version_id,
                input_features=input_data,
                probability=cached_prediction_payload["probability"],
                threshold=cached_prediction_payload["threshold"],
                prediction=cached_prediction_payload["prediction"],
                shap_values=cached_prediction_payload["shap_values"],
                is_batch=False,
                batch_id=None,
                created_at=datetime.utcnow(),
            )

            if store_prediction:
                db.add(prediction)
                db.commit()
                db.refresh(prediction)
                logger.info(f"Stored cached prediction {prediction.id} in database")

            elapsed_ms = (time.time() - start_time) * 1000
            logger.info(
                f"Returning cached prediction payload for model {model_version_id} "
                f"in {elapsed_ms:.2f}ms"
            )
            return prediction

        model = self._load_model(model_version)

        try:
            X_preprocessed = PredictionPreprocessingService.preprocess_for_prediction(
                db=db, model_version_id=model_version_id, input_data=input_data
            )
        except PredictionPreprocessingError as e:
            logger.error(f"Preprocessing failed: {e}")
            raise

        try:
            probability_array = model.predict_proba(X_preprocessed)

            churn_probability = float(probability_array[0, 1])

            churn_probability = max(0.0, min(1.0, churn_probability))

        except Exception as e:
            logger.error(f"Model prediction failed: {e}")
            raise PredictionServiceError(f"Failed to generate prediction: {str(e)}")

        threshold = model_version.classification_threshold
        binary_prediction = churn_probability >= threshold

        elapsed_ms = (time.time() - start_time) * 1000
        if elapsed_ms > self.MAX_PREDICTION_TIME_MS:
            logger.warning(
                f"Prediction exceeded {self.MAX_PREDICTION_TIME_MS}ms timeout: "
                f"{elapsed_ms:.2f}ms for model {model_version_id}"
            )

        shap_start_time = time.time()
        try:
            shap_values_dict = self._compute_shap_values(
                db=db,
                model=model,
                model_version=model_version,
                X_preprocessed=X_preprocessed,
                input_data=input_data,
                prediction_probability=churn_probability,
            )
        except Exception as e:
            logger.error(f"SHAP computation failed: {e}")

            shap_values_dict = self._default_shap_values(churn_probability)

        shap_elapsed_ms = (time.time() - shap_start_time) * 1000
        if shap_elapsed_ms > self.MAX_SHAP_COMPUTATION_TIME_MS:
            logger.warning(
                f"SHAP computation exceeded {self.MAX_SHAP_COMPUTATION_TIME_MS}ms timeout: "
                f"{shap_elapsed_ms:.2f}ms for model {model_version_id}"
            )

        prediction = Prediction(
            user_id=user_id,
            model_version_id=model_version_id,
            input_features=input_data,
            probability=churn_probability,
            threshold=threshold,
            prediction=binary_prediction,
            shap_values=shap_values_dict,
            is_batch=False,
            batch_id=None,
            created_at=datetime.utcnow(),
        )

        if store_prediction:
            db.add(prediction)
            db.commit()
            db.refresh(prediction)
            logger.info(f"Stored prediction {prediction.id} in database")

        self._cache_prediction(model_version_id, input_hash, prediction)

        total_elapsed_ms = (time.time() - start_time) * 1000
        logger.info(
            f"Generated prediction for model {model_version_id} in {total_elapsed_ms:.2f}ms "
            f"(prediction: {elapsed_ms:.2f}ms, SHAP: {shap_elapsed_ms:.2f}ms): "
            f"probability={churn_probability:.4f}, prediction={binary_prediction}"
        )

        return prediction

    def _compute_shap_values(
        self,
        db: Session,
        model: Any,
        model_version: ModelVersion,
        X_preprocessed: np.ndarray,
        input_data: Dict[str, Any],
        prediction_probability: float,
    ) -> Dict[str, Any]:
        try:
            preprocessing_config = (
                db.query(PreprocessingConfig)
                .filter(PreprocessingConfig.id == model_version.preprocessing_config_id)
                .first()
            )

            if not preprocessing_config:
                raise SHAPComputationError(
                    f"Preprocessing config {model_version.preprocessing_config_id} not found"
                )

            feature_names = preprocessing_config.feature_columns
            background = self._build_shap_background(X_preprocessed)
            predict_fn = self._create_probability_predictor(model)

            if model_version.model_type == "DecisionTree":
                explainer = shap.TreeExplainer(
                    model,
                    data=background,
                    model_output="probability",
                    feature_perturbation="interventional",
                )
                shap_values = explainer.shap_values(X_preprocessed)
                base_value = explainer.expected_value

            else:
                explainer = shap.KernelExplainer(predict_fn, background)
                shap_values = explainer.shap_values(X_preprocessed, nsamples=100)
                base_value = explainer.expected_value

            result = self._build_explanation_payload(
                feature_names=feature_names,
                X_preprocessed=X_preprocessed,
                shap_values=shap_values,
                base_value=base_value,
                prediction_probability=prediction_probability,
            )

            if not self._is_explanation_valid(result, prediction_probability):
                logger.warning(
                    "SHAP explanation was empty or inconsistent for model %s. Falling back to local perturbation contributions.",
                    model_version.id,
                )
                result = self._build_local_contribution_payload(
                    model=model,
                    feature_names=feature_names,
                    X_preprocessed=X_preprocessed,
                    prediction_probability=prediction_probability,
                )

            logger.info(
                f"Computed SHAP values for model {model_version.id}: "
                f"{len(result['top_positive'])} positive, {len(result['top_negative'])} negative contributors"
            )

            return result

        except Exception as e:
            logger.error(f"Failed to compute SHAP values: {e}", exc_info=True)
            raise SHAPComputationError(f"SHAP computation failed: {str(e)}")

    def _build_shap_background(self, X_preprocessed: np.ndarray) -> np.ndarray:
        return np.zeros((1, X_preprocessed.shape[1]), dtype=float)

    def _create_probability_predictor(self, model: Any):
        def predict_fn(X):
            return model.predict_proba(X)[:, 1]

        return predict_fn

    def _build_explanation_payload(
        self,
        feature_names: list[str],
        X_preprocessed: np.ndarray,
        shap_values: Any,
        base_value: Any,
        prediction_probability: float,
    ) -> Dict[str, Any]:
        shap_values_single = self._extract_shap_vector(shap_values)
        base_value_float = self._extract_expected_value(base_value)

        if len(shap_values_single) != len(feature_names):
            raise SHAPComputationError(
                f"Feature contribution length mismatch: expected {len(feature_names)}, got {len(shap_values_single)}"
            )

        feature_contributions = self._build_feature_contributions(
            feature_names=feature_names,
            X_preprocessed=X_preprocessed,
            contributions=shap_values_single,
        )

        prediction_value = float(base_value_float + sum(shap_values_single))

        return self._format_explanation_payload(
            base_value=base_value_float,
            prediction_value=prediction_value,
            feature_contributions=feature_contributions,
        )

    def _build_local_contribution_payload(
        self,
        model: Any,
        feature_names: list[str],
        X_preprocessed: np.ndarray,
        prediction_probability: float,
    ) -> Dict[str, Any]:
        baseline = self._build_shap_background(X_preprocessed)
        base_probability = float(model.predict_proba(baseline)[0, 1])

        raw_contributions = []
        for index in range(len(feature_names)):
            perturbed = baseline.copy()
            perturbed[0, index] = X_preprocessed[0, index]
            feature_probability = float(model.predict_proba(perturbed)[0, 1])
            raw_contributions.append(feature_probability - base_probability)

        total_delta = prediction_probability - base_probability
        raw_total = float(sum(raw_contributions))

        if abs(raw_total) > 1e-9:
            scale = total_delta / raw_total
            normalized_contributions = [contribution * scale for contribution in raw_contributions]
        else:
            normalized_contributions = raw_contributions

        feature_contributions = self._build_feature_contributions(
            feature_names=feature_names,
            X_preprocessed=X_preprocessed,
            contributions=np.array(normalized_contributions),
        )

        return self._format_explanation_payload(
            base_value=base_probability,
            prediction_value=prediction_probability,
            feature_contributions=feature_contributions,
        )

    def _build_feature_contributions(
        self,
        feature_names: list[str],
        X_preprocessed: np.ndarray,
        contributions: np.ndarray,
    ) -> list[Dict[str, Any]]:
        feature_contributions = []
        for index, feature_name in enumerate(feature_names):
            contribution = float(contributions[index])
            feature_contributions.append(
                {
                    "feature": feature_name,
                    "value": float(X_preprocessed[0, index]),
                    "contribution": contribution,
                    "direction": "positive" if contribution > 0 else "negative",
                }
            )

        return feature_contributions

    def _format_explanation_payload(
        self,
        base_value: float,
        prediction_value: float,
        feature_contributions: list[Dict[str, Any]],
    ) -> Dict[str, Any]:
        feature_contributions.sort(key=lambda item: abs(item["contribution"]), reverse=True)
        positive_contributors = [
            contribution
            for contribution in feature_contributions
            if contribution["contribution"] > 0
        ][: self.TOP_CONTRIBUTORS_COUNT]
        negative_contributors = [
            contribution
            for contribution in feature_contributions
            if contribution["contribution"] < 0
        ][: self.TOP_CONTRIBUTORS_COUNT]

        return {
            "base_value": float(base_value),
            "prediction_value": float(prediction_value),
            "top_positive": positive_contributors,
            "top_negative": negative_contributors,
        }

    def _extract_shap_vector(self, shap_values: Any) -> np.ndarray:
        if isinstance(shap_values, list):
            selected_values = shap_values[1] if len(shap_values) > 1 else shap_values[0]
            shap_array = np.asarray(selected_values, dtype=float)
        else:
            shap_array = np.asarray(shap_values, dtype=float)
            if shap_array.ndim == 3 and shap_array.shape[-1] > 1:
                shap_array = shap_array[:, :, 1]

        if shap_array.ndim == 0:
            return np.array([float(shap_array)])
        if shap_array.ndim == 1:
            return shap_array.astype(float)

        return shap_array[0].astype(float).flatten()

    def _extract_expected_value(self, expected_value: Any) -> float:
        if isinstance(expected_value, (list, np.ndarray)):
            expected_array = np.asarray(expected_value, dtype=float).flatten()
            if len(expected_array) > 1:
                return float(expected_array[1])
            return float(expected_array[0])
        return float(expected_value)

    def _is_explanation_valid(
        self, explanation_payload: Dict[str, Any], prediction_probability: float
    ) -> bool:
        contributions = explanation_payload.get("top_positive", []) + explanation_payload.get(
            "top_negative", []
        )
        has_signal = any(abs(item["contribution"]) > 1e-6 for item in contributions)
        prediction_value = float(
            explanation_payload.get("prediction_value", explanation_payload.get("base_value", 0.0))
        )
        return has_signal and abs(prediction_value - prediction_probability) <= 0.05

    def _default_shap_values(self, prediction_probability: float) -> Dict[str, Any]:
        return {
            "base_value": float(prediction_probability),
            "prediction_value": float(prediction_probability),
            "top_positive": [],
            "top_negative": [],
        }

    def _load_model(self, model_version: ModelVersion) -> Any:
        model_cache_key = f"model:{model_version.id}"

        if self._cache_enabled:
            try:
                cached_model_bytes = self.redis_client.get(model_cache_key)
                if cached_model_bytes:
                    if isinstance(cached_model_bytes, str):
                        cached_model_bytes = base64.b64decode(cached_model_bytes.encode("ascii"))

                    model = joblib.load(io.BytesIO(cached_model_bytes))
                    logger.info(f"Loaded model {model_version.id} from cache")
                    return model
            except Exception as e:
                logger.warning(f"Failed to load model from cache: {e}")

        try:
            logger.info(f"Loading model {model_version.id} from R2: {model_version.artifact_path}")
            model_bytes = storage_client.download_model_artifact(model_version.artifact_path)
            model = joblib.load(io.BytesIO(model_bytes))

            if self._cache_enabled:
                try:
                    model_buffer = io.BytesIO()
                    joblib.dump(model, model_buffer)
                    model_buffer.seek(0)

                    self.redis_client.setex(
                        model_cache_key,
                        self.MODEL_CACHE_TTL,
                        base64.b64encode(model_buffer.read()).decode("ascii"),
                    )
                    logger.info(f"Cached model {model_version.id} for {self.MODEL_CACHE_TTL}s")
                except Exception as e:
                    logger.warning(f"Failed to cache model: {e}")

            return model

        except Exception as e:
            logger.error(f"Failed to load model from R2: {e}")
            raise ModelLoadError(f"Failed to load model {model_version.id}: {str(e)}")

    def _hash_input(self, input_data: Dict[str, Any]) -> str:
        sorted_input = json.dumps(input_data, sort_keys=True)
        return hashlib.sha256(sorted_input.encode()).hexdigest()

    def _get_cached_prediction_payload(
        self, model_version_id: UUID, input_hash: str
    ) -> Optional[Dict[str, Any]]:
        if not self._cache_enabled:
            return None

        cache_key = f"prediction:{model_version_id}:{input_hash}"

        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                prediction_dict = json.loads(cached_data)
                logger.info(f"Cache hit for prediction: {cache_key}")
                return {
                    "probability": float(prediction_dict["probability"]),
                    "threshold": float(prediction_dict["threshold"]),
                    "prediction": bool(prediction_dict["prediction"]),
                    "shap_values": prediction_dict.get("shap_values")
                    or self._default_shap_values(float(prediction_dict["probability"])),
                }
        except Exception as e:
            logger.warning(f"Failed to retrieve cached prediction: {e}")

        return None

    def _cache_prediction(
        self, model_version_id: UUID, input_hash: str, prediction: Prediction
    ) -> None:
        if not self._cache_enabled:
            return

        cache_key = f"prediction:{model_version_id}:{input_hash}"

        try:
            prediction_dict = {
                "probability": prediction.probability,
                "threshold": prediction.threshold,
                "prediction": prediction.prediction,
                "shap_values": prediction.shap_values,
            }

            self.redis_client.setex(
                cache_key, self.PREDICTION_CACHE_TTL, json.dumps(prediction_dict)
            )

            logger.info(f"Cached prediction for {self.PREDICTION_CACHE_TTL}s: {cache_key}")
        except Exception as e:
            logger.warning(f"Failed to cache prediction: {e}")

    def clear_model_cache(self, model_version_id: UUID) -> bool:
        if not self._cache_enabled:
            return False

        cache_key = f"model:{model_version_id}"

        try:
            deleted = self.redis_client.delete(cache_key)
            if deleted:
                logger.info(f"Cleared model cache: {cache_key}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to clear model cache: {e}")
            return False

    def clear_prediction_cache(self, model_version_id: UUID) -> int:
        if not self._cache_enabled:
            return 0

        pattern = f"prediction:{model_version_id}:*"

        try:
            keys = list(self.redis_client.scan_iter(match=pattern))

            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(
                    f"Cleared {deleted} prediction cache entries for model {model_version_id}"
                )
                return deleted

            return 0
        except Exception as e:
            logger.error(f"Failed to clear prediction cache: {e}")
            return 0

    def get_cache_stats(self, model_version_id: UUID) -> Dict[str, Any]:
        if not self._cache_enabled:
            return {"cache_enabled": False, "model_cached": False, "prediction_cache_count": 0}

        model_cache_key = f"model:{model_version_id}"
        prediction_pattern = f"prediction:{model_version_id}:*"

        try:
            model_cached = self.redis_client.exists(model_cache_key) > 0
            prediction_keys = list(self.redis_client.scan_iter(match=prediction_pattern))

            return {
                "cache_enabled": True,
                "model_cached": model_cached,
                "prediction_cache_count": len(prediction_keys),
                "model_cache_ttl": self.redis_client.ttl(model_cache_key) if model_cached else None,
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"cache_enabled": True, "error": str(e)}


def create_prediction_service(redis_client: Optional[redis.Redis] = None) -> PredictionService:
    return PredictionService(redis_client=redis_client)
