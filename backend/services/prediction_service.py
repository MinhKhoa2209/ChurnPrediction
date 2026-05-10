import hashlib
import io
import json
import logging
import time
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

        input_hash = self._hash_input(input_data)
        cached_prediction = self._get_cached_prediction(model_version_id, input_hash)

        if cached_prediction:
            elapsed_ms = (time.time() - start_time) * 1000
            logger.info(
                f"Returning cached prediction for model {model_version_id} "
                f"in {elapsed_ms:.2f}ms"
            )
            return cached_prediction

        model_version = db.query(ModelVersion).filter(ModelVersion.id == model_version_id).first()

        if not model_version:
            raise ModelNotFoundError(f"Model version {model_version_id} not found")

        if model_version.status != "active":
            raise ModelNotFoundError(
                f"Model version {model_version_id} is {model_version.status} and cannot be used for predictions"
            )

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
            )
        except Exception as e:
            logger.error(f"SHAP computation failed: {e}")

            shap_values_dict = {}

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

            if model_version.model_type == "DecisionTree":
                explainer = shap.TreeExplainer(model)
                shap_values = explainer.shap_values(X_preprocessed)

                if isinstance(shap_values, list):
                    shap_values = shap_values[1]

                base_value = explainer.expected_value
                if isinstance(base_value, (list, np.ndarray)):
                    base_value = (
                        float(base_value[1]) if len(base_value) > 1 else float(base_value[0])
                    )
                else:
                    base_value = float(base_value)

            else:
                background = X_preprocessed

                def predict_fn(X):
                    return model.predict_proba(X)[:, 1]

                explainer = shap.KernelExplainer(predict_fn, background)

                shap_values = explainer.shap_values(X_preprocessed, nsamples=100)

                base_value = float(explainer.expected_value)

            if isinstance(shap_values, np.ndarray):
                if len(shap_values.shape) > 1:
                    shap_values_single = shap_values[0]
                else:
                    shap_values_single = shap_values
            else:
                shap_values_single = np.array(shap_values)

            if len(shap_values_single.shape) > 1:
                shap_values_single = shap_values_single.flatten()

            feature_contributions = []
            for i in range(len(feature_names)):
                feature_name = feature_names[i]

                feature_value = float(X_preprocessed[0, i])

                shap_val = shap_values_single[i]
                if isinstance(shap_val, np.ndarray):
                    shap_contribution = float(shap_val.flatten()[0])
                else:
                    shap_contribution = float(shap_val)

                feature_contributions.append(
                    {
                        "feature": feature_name,
                        "value": feature_value,
                        "contribution": shap_contribution,
                        "direction": "positive" if shap_contribution > 0 else "negative",
                    }
                )

            feature_contributions.sort(key=lambda x: abs(x["contribution"]), reverse=True)

            positive_contributors = [fc for fc in feature_contributions if fc["contribution"] > 0][
                : self.TOP_CONTRIBUTORS_COUNT
            ]

            negative_contributors = [fc for fc in feature_contributions if fc["contribution"] < 0][
                : self.TOP_CONTRIBUTORS_COUNT
            ]

            shap_sum = sum(fc["contribution"] for fc in feature_contributions)
            prediction_value = float(base_value + shap_sum)

            result = {
                "base_value": float(base_value),
                "prediction_value": prediction_value,
                "top_positive": positive_contributors,
                "top_negative": negative_contributors,
            }

            logger.info(
                f"Computed SHAP values for model {model_version.id}: "
                f"{len(positive_contributors)} positive, {len(negative_contributors)} negative contributors"
            )

            return result

        except Exception as e:
            logger.error(f"Failed to compute SHAP values: {e}", exc_info=True)
            raise SHAPComputationError(f"SHAP computation failed: {str(e)}")

    def _load_model(self, model_version: ModelVersion) -> Any:
        model_cache_key = f"model:{model_version.id}"

        if self._cache_enabled:
            try:
                cached_model_bytes = self.redis_client.get(model_cache_key)
                if cached_model_bytes:
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
                        model_cache_key, self.MODEL_CACHE_TTL, model_buffer.read()
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

    def _get_cached_prediction(
        self, model_version_id: UUID, input_hash: str
    ) -> Optional[Prediction]:
        if not self._cache_enabled:
            return None

        cache_key = f"prediction:{model_version_id}:{input_hash}"

        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                prediction_dict = json.loads(cached_data)

                prediction = Prediction(
                    id=UUID(prediction_dict["id"]),
                    user_id=UUID(prediction_dict["user_id"]),
                    model_version_id=UUID(prediction_dict["model_version_id"]),
                    input_features=prediction_dict["input_features"],
                    probability=prediction_dict["probability"],
                    threshold=prediction_dict["threshold"],
                    prediction=prediction_dict["prediction"],
                    shap_values=prediction_dict["shap_values"],
                    is_batch=prediction_dict["is_batch"],
                    batch_id=(
                        UUID(prediction_dict["batch_id"]) if prediction_dict["batch_id"] else None
                    ),
                )

                logger.info(f"Cache hit for prediction: {cache_key}")
                return prediction
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
                "id": str(prediction.id),
                "user_id": str(prediction.user_id),
                "model_version_id": str(prediction.model_version_id),
                "input_features": prediction.input_features,
                "probability": prediction.probability,
                "threshold": prediction.threshold,
                "prediction": prediction.prediction,
                "shap_values": prediction.shap_values,
                "is_batch": prediction.is_batch,
                "batch_id": str(prediction.batch_id) if prediction.batch_id else None,
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
