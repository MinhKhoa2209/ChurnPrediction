"""
Prediction Service
- Loading trained models from cache or R2 storage
- Generating prediction probabilities (0.0 to 1.0)
- Returning predictions within 200ms
- Caching loaded models for performance
- Computing SHAP values for explainability
"""

import logging
import time
from typing import Dict, Any, Optional, Tuple, List
from uuid import UUID
import io
import joblib
import hashlib
import json

import numpy as np
from sqlalchemy.orm import Session
import redis
import shap

from backend.domain.models.model_version import ModelVersion
from backend.domain.models.prediction import Prediction
from backend.domain.models.preprocessing_config import PreprocessingConfig
from backend.services.prediction_preprocessing_service import (
    PredictionPreprocessingService,
    PredictionPreprocessingError,
)
from backend.infrastructure.storage import storage_client
from backend.config import settings

logger = logging.getLogger(__name__)


class PredictionServiceError(Exception):
    """Base exception for prediction service errors"""
    pass


class ModelNotFoundError(PredictionServiceError):
    """Raised when model version is not found"""
    pass


class ModelLoadError(PredictionServiceError):
    """Raised when model cannot be loaded from storage"""
    pass


class PredictionTimeoutError(PredictionServiceError):
    """Raised when prediction exceeds 200ms timeout"""
    pass


class SHAPComputationError(PredictionServiceError):
    """Raised when SHAP value computation fails"""
    pass


class PredictionService:
    """Service for generating churn predictions"""
    
    # Cache TTL for loaded models (6 hours as per design)
    MODEL_CACHE_TTL = 6 * 60 * 60  # 6 hours in seconds
    
    # Cache TTL for prediction results (1 hour as per design)
    PREDICTION_CACHE_TTL = 60 * 60  # 1 hour in seconds
    
    # Maximum prediction time (200ms as per requirement 12.6)
    MAX_PREDICTION_TIME_MS = 200
    
    # Maximum SHAP computation time (500ms as per requirement 27.6)
    MAX_SHAP_COMPUTATION_TIME_MS = 500
    
    # Number of top contributors to return (requirement 27.2, 27.3)
    TOP_CONTRIBUTORS_COUNT = 5
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        Initialize prediction service.
        
        Args:
            redis_client: Optional Redis client for caching (if None, caching is disabled)
        """
        self.redis_client = redis_client
        self._cache_enabled = redis_client is not None
        
        if self._cache_enabled:
            logger.info("Prediction service initialized with caching enabled")
        else:
            logger.warning("Prediction service initialized without caching (performance may be degraded)")
    
    def generate_prediction(
        self,
        db: Session,
        user_id: UUID,
        model_version_id: UUID,
        input_data: Dict[str, Any],
        store_prediction: bool = True
    ) -> Prediction:
        """
        Generate a churn prediction for a single customer.
        
        This method orchestrates the complete prediction pipeline:
        1. Check prediction cache for identical inputs
        2. Load model from cache or R2 storage
        3. Preprocess input data using stored preprocessing parameters
        4. Generate prediction probability
        5. Apply classification threshold
        6. Store prediction in database (if requested)
        7. Cache prediction result
        
        - 12.6: Return prediction probability (0.0 to 1.0) within 200ms
        - 22.1: Cache loaded models in memory
        - 22.4: Return cached predictions within 50ms for identical inputs
        
        Args:
            db: Database session
            user_id: UUID of the user making the prediction
            model_version_id: UUID of the model version to use
            input_data: Dictionary of raw input features
            store_prediction: Whether to store prediction in database (default: True)
            
        Returns:
            Prediction object with probability, threshold, and binary prediction
            
        Raises:
            ModelNotFoundError: If model version is not found
            ModelLoadError: If model cannot be loaded from storage
            PredictionPreprocessingError: If preprocessing fails
            PredictionTimeoutError: If prediction exceeds 200ms timeout
        """
        start_time = time.time()
        
        # Step 1: Check prediction cache (Requirement 22.4)
        input_hash = self._hash_input(input_data)
        cached_prediction = self._get_cached_prediction(model_version_id, input_hash)
        
        if cached_prediction:
            elapsed_ms = (time.time() - start_time) * 1000
            logger.info(
                f"Returning cached prediction for model {model_version_id} "
                f"in {elapsed_ms:.2f}ms"
            )
            return cached_prediction
        
        # Step 2: Retrieve model version from database
        model_version = db.query(ModelVersion).filter(
            ModelVersion.id == model_version_id
        ).first()
        
        if not model_version:
            raise ModelNotFoundError(f"Model version {model_version_id} not found")
        
        if model_version.status != "active":
            raise ModelNotFoundError(
                f"Model version {model_version_id} is {model_version.status} and cannot be used for predictions"
            )
        
        # Step 3: Load model from cache or R2 storage (Requirement 22.1)
        model = self._load_model(model_version)
        
        # Step 4: Preprocess input data (Requirement 12.4)
        try:
            X_preprocessed = PredictionPreprocessingService.preprocess_for_prediction(
                db=db,
                model_version_id=model_version_id,
                input_data=input_data
            )
        except PredictionPreprocessingError as e:
            logger.error(f"Preprocessing failed: {e}")
            raise
        
        # Step 5: Generate prediction probability (Requirement 12.5, 12.6)
        try:
            # Predict probability (returns array of shape (n_samples, n_classes))
            probability_array = model.predict_proba(X_preprocessed)
            
            # Extract churn probability (class 1)
            # probability_array shape: (1, 2) where [:, 1] is churn probability
            churn_probability = float(probability_array[0, 1])
            
            # Ensure probability is in valid range [0.0, 1.0]
            churn_probability = max(0.0, min(1.0, churn_probability))
            
        except Exception as e:
            logger.error(f"Model prediction failed: {e}")
            raise PredictionServiceError(f"Failed to generate prediction: {str(e)}")
        
        # Step 6: Apply classification threshold
        threshold = model_version.classification_threshold
        binary_prediction = churn_probability >= threshold
        
        # Check if we exceeded the 200ms timeout (Requirement 12.6)
        elapsed_ms = (time.time() - start_time) * 1000
        if elapsed_ms > self.MAX_PREDICTION_TIME_MS:
            logger.warning(
                f"Prediction exceeded {self.MAX_PREDICTION_TIME_MS}ms timeout: "
                f"{elapsed_ms:.2f}ms for model {model_version_id}"
            )
            # Note: We don't raise an error here, just log a warning
            # The prediction is still valid, just slower than target
        
        # Step 7: Compute SHAP values for explainability (Requirements 27.1-27.6)
        shap_start_time = time.time()
        try:
            shap_values_dict = self._compute_shap_values(
                db=db,
                model=model,
                model_version=model_version,
                X_preprocessed=X_preprocessed,
                input_data=input_data
            )
        except Exception as e:
            logger.error(f"SHAP computation failed: {e}")
            # Don't fail the prediction if SHAP computation fails
            shap_values_dict = {}
        
        shap_elapsed_ms = (time.time() - shap_start_time) * 1000
        if shap_elapsed_ms > self.MAX_SHAP_COMPUTATION_TIME_MS:
            logger.warning(
                f"SHAP computation exceeded {self.MAX_SHAP_COMPUTATION_TIME_MS}ms timeout: "
                f"{shap_elapsed_ms:.2f}ms for model {model_version_id}"
            )
        
        # Step 8: Create prediction object
        prediction = Prediction(
            user_id=user_id,
            model_version_id=model_version_id,
            input_features=input_data,
            probability=churn_probability,
            threshold=threshold,
            prediction=binary_prediction,
            shap_values=shap_values_dict,
            is_batch=False,
            batch_id=None
        )
        
        # Step 9: Store prediction in database (if requested)
        if store_prediction:
            db.add(prediction)
            db.commit()
            db.refresh(prediction)
            logger.info(f"Stored prediction {prediction.id} in database")
        
        # Step 10: Cache prediction result (Requirement 22.4)
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
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compute SHAP values for a prediction to explain feature contributions.
        
        This method computes SHAP (SHapley Additive exPlanations) values to explain
        which features contributed most to the prediction. It returns the top 5
        positive contributors (increasing churn probability) and top 5 negative
        contributors (decreasing churn probability).
        
        - 27.2: Return top 5 positive contributors
        - 27.3: Return top 5 negative contributors
        - 27.4: Display feature values alongside contribution scores
        - 27.5: Display waterfall chart (frontend requirement)
        - 27.6: Complete SHAP computation within 500ms
        
        Args:
            db: Database session
            model: Loaded scikit-learn model
            model_version: ModelVersion object
            X_preprocessed: Preprocessed feature vector (numpy array)
            input_data: Original input data dictionary
            
        Returns:
            Dictionary containing SHAP values and top contributors:
            {
                "base_value": float,  # Expected value (average prediction)
                "prediction_value": float,  # Actual prediction
                "top_positive": [  # Top 5 features increasing churn probability
                    {
                        "feature": str,
                        "value": float,
                        "contribution": float,
                        "direction": "positive"
                    },
                    ...
                ],
                "top_negative": [  # Top 5 features decreasing churn probability
                    {
                        "feature": str,
                        "value": float,
                        "contribution": float,
                        "direction": "negative"
                    },
                    ...
                ]
            }
            
        Raises:
            SHAPComputationError: If SHAP computation fails
        """
        try:
            # Get preprocessing config to retrieve feature names
            preprocessing_config = db.query(PreprocessingConfig).filter(
                PreprocessingConfig.id == model_version.preprocessing_config_id
            ).first()
            
            if not preprocessing_config:
                raise SHAPComputationError(
                    f"Preprocessing config {model_version.preprocessing_config_id} not found"
                )
            
            feature_names = preprocessing_config.feature_columns
            
            # Select appropriate SHAP explainer based on model type
            # TreeExplainer for Decision Tree (faster and more accurate)
            # KernelExplainer for other models (KNN, Naive Bayes, SVM)
            if model_version.model_type == "DecisionTree":
                # TreeExplainer is optimized for tree-based models
                explainer = shap.TreeExplainer(model)
                shap_values = explainer.shap_values(X_preprocessed)
                
                # For binary classification, shap_values might be a list [class_0, class_1]
                # We want the SHAP values for the positive class (churn = 1)
                if isinstance(shap_values, list):
                    shap_values = shap_values[1]  # Class 1 (churn)
                
                # Get base value (expected value)
                base_value = explainer.expected_value
                if isinstance(base_value, (list, np.ndarray)):
                    base_value = float(base_value[1]) if len(base_value) > 1 else float(base_value[0])
                else:
                    base_value = float(base_value)
                
            else:
                # KernelExplainer for non-tree models (KNN, Naive Bayes, SVM)
                # Use a small background dataset for efficiency (100 samples)
                # In production, this should be sampled from training data
                # For now, we'll use the current sample as background (not ideal but fast)
                background = X_preprocessed
                
                # Create a prediction function that returns probabilities for class 1
                def predict_fn(X):
                    return model.predict_proba(X)[:, 1]
                
                explainer = shap.KernelExplainer(predict_fn, background)
                
                # Compute SHAP values (this can be slow for KernelExplainer)
                # Use nsamples parameter to limit computation time
                shap_values = explainer.shap_values(X_preprocessed, nsamples=100)
                
                # Get base value (expected value)
                base_value = float(explainer.expected_value)
            
            # Extract SHAP values for the single prediction
            # Handle different shapes returned by SHAP explainers
            if isinstance(shap_values, np.ndarray):
                if len(shap_values.shape) > 1:
                    # Shape is (n_samples, n_features) - extract first sample
                    shap_values_single = shap_values[0]
                else:
                    # Shape is (n_features,) - already a single sample
                    shap_values_single = shap_values
            else:
                # Not a numpy array, convert to array
                shap_values_single = np.array(shap_values)
            
            # Ensure shap_values_single is 1D
            if len(shap_values_single.shape) > 1:
                shap_values_single = shap_values_single.flatten()
            
            # Create list of (feature_name, feature_value, shap_contribution) tuples
            feature_contributions = []
            for i in range(len(feature_names)):
                feature_name = feature_names[i]
                
                # Get the original feature value from preprocessed array
                feature_value = float(X_preprocessed[0, i])
                
                # Get SHAP value and convert to float
                shap_val = shap_values_single[i]
                if isinstance(shap_val, np.ndarray):
                    # If still an array, flatten and take first element
                    shap_contribution = float(shap_val.flatten()[0])
                else:
                    shap_contribution = float(shap_val)
                
                feature_contributions.append({
                    "feature": feature_name,
                    "value": feature_value,
                    "contribution": shap_contribution,
                    "direction": "positive" if shap_contribution > 0 else "negative"
                })
            
            # Sort by absolute contribution (magnitude)
            feature_contributions.sort(key=lambda x: abs(x["contribution"]), reverse=True)
            
            # Get top 5 positive contributors (increasing churn probability)
            positive_contributors = [
                fc for fc in feature_contributions if fc["contribution"] > 0
            ][:self.TOP_CONTRIBUTORS_COUNT]
            
            # Get top 5 negative contributors (decreasing churn probability)
            negative_contributors = [
                fc for fc in feature_contributions if fc["contribution"] < 0
            ][:self.TOP_CONTRIBUTORS_COUNT]
            
            # Compute prediction value (base_value + sum of SHAP values)
            shap_sum = sum(fc["contribution"] for fc in feature_contributions)
            prediction_value = float(base_value + shap_sum)
            
            result = {
                "base_value": float(base_value),
                "prediction_value": prediction_value,
                "top_positive": positive_contributors,
                "top_negative": negative_contributors
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
        """
        Load model from cache or R2 storage.
        
        This method implements a two-tier caching strategy:
        1. Check Redis cache for loaded model (fast)
        2. If not cached, load from R2 storage and cache (slower)
        
        Requirement 22.1: Cache loaded ML_Model instances in memory
        
        Args:
            model_version: ModelVersion object with artifact path
            
        Returns:
            Loaded scikit-learn model
            
        Raises:
            ModelLoadError: If model cannot be loaded
        """
        model_cache_key = f"model:{model_version.id}"
        
        # Try to load from cache first (Requirement 22.1)
        if self._cache_enabled:
            try:
                cached_model_bytes = self.redis_client.get(model_cache_key)
                if cached_model_bytes:
                    model = joblib.load(io.BytesIO(cached_model_bytes))
                    logger.info(f"Loaded model {model_version.id} from cache")
                    return model
            except Exception as e:
                logger.warning(f"Failed to load model from cache: {e}")
        
        # Load from R2 storage
        try:
            logger.info(f"Loading model {model_version.id} from R2: {model_version.artifact_path}")
            model_bytes = storage_client.download_model_artifact(model_version.artifact_path)
            model = joblib.load(io.BytesIO(model_bytes))
            
            # Cache the loaded model (Requirement 22.1)
            if self._cache_enabled:
                try:
                    # Serialize model for caching
                    model_buffer = io.BytesIO()
                    joblib.dump(model, model_buffer)
                    model_buffer.seek(0)
                    
                    self.redis_client.setex(
                        model_cache_key,
                        self.MODEL_CACHE_TTL,
                        model_buffer.read()
                    )
                    logger.info(f"Cached model {model_version.id} for {self.MODEL_CACHE_TTL}s")
                except Exception as e:
                    logger.warning(f"Failed to cache model: {e}")
            
            return model
            
        except Exception as e:
            logger.error(f"Failed to load model from R2: {e}")
            raise ModelLoadError(f"Failed to load model {model_version.id}: {str(e)}")
    
    def _hash_input(self, input_data: Dict[str, Any]) -> str:
        """
        Generate a hash of input data for caching.
        
        Args:
            input_data: Dictionary of input features
            
        Returns:
            SHA256 hash of the input data
        """
        # Sort keys for consistent hashing
        sorted_input = json.dumps(input_data, sort_keys=True)
        return hashlib.sha256(sorted_input.encode()).hexdigest()
    
    def _get_cached_prediction(
        self,
        model_version_id: UUID,
        input_hash: str
    ) -> Optional[Prediction]:
        """
        Retrieve cached prediction result.
        
        Requirement 22.4: Return cached predictions within 50ms
        
        Args:
            model_version_id: UUID of the model version
            input_hash: Hash of the input data
            
        Returns:
            Cached Prediction object or None if not found
        """
        if not self._cache_enabled:
            return None
        
        cache_key = f"prediction:{model_version_id}:{input_hash}"
        
        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                # Deserialize cached prediction data
                prediction_dict = json.loads(cached_data)
                
                # Reconstruct Prediction object (without database session)
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
                    batch_id=UUID(prediction_dict["batch_id"]) if prediction_dict["batch_id"] else None
                )
                
                logger.info(f"Cache hit for prediction: {cache_key}")
                return prediction
        except Exception as e:
            logger.warning(f"Failed to retrieve cached prediction: {e}")
        
        return None
    
    def _cache_prediction(
        self,
        model_version_id: UUID,
        input_hash: str,
        prediction: Prediction
    ) -> None:
        """
        Cache prediction result.
        
        Requirement 22.3: Store recent predictions with 1-hour TTL
        
        Args:
            model_version_id: UUID of the model version
            input_hash: Hash of the input data
            prediction: Prediction object to cache
        """
        if not self._cache_enabled:
            return
        
        cache_key = f"prediction:{model_version_id}:{input_hash}"
        
        try:
            # Serialize prediction data
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
                "batch_id": str(prediction.batch_id) if prediction.batch_id else None
            }
            
            self.redis_client.setex(
                cache_key,
                self.PREDICTION_CACHE_TTL,
                json.dumps(prediction_dict)
            )
            
            logger.info(f"Cached prediction for {self.PREDICTION_CACHE_TTL}s: {cache_key}")
        except Exception as e:
            logger.warning(f"Failed to cache prediction: {e}")
    
    def clear_model_cache(self, model_version_id: UUID) -> bool:
        """
        Clear cached model from Redis.
        
        Useful when a model is updated or archived.
        
        Args:
            model_version_id: UUID of the model version to clear
            
        Returns:
            True if cache was cleared, False otherwise
        """
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
        """
        Clear all cached predictions for a model version.
        
        Useful when a model's threshold is updated.
        
        Args:
            model_version_id: UUID of the model version
            
        Returns:
            Number of cache entries cleared
        """
        if not self._cache_enabled:
            return 0
        
        pattern = f"prediction:{model_version_id}:*"
        
        try:
            # Find all matching keys
            keys = list(self.redis_client.scan_iter(match=pattern))
            
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"Cleared {deleted} prediction cache entries for model {model_version_id}")
                return deleted
            
            return 0
        except Exception as e:
            logger.error(f"Failed to clear prediction cache: {e}")
            return 0
    
    def get_cache_stats(self, model_version_id: UUID) -> Dict[str, Any]:
        """
        Get cache statistics for a model version.
        
        Args:
            model_version_id: UUID of the model version
            
        Returns:
            Dictionary with cache statistics
        """
        if not self._cache_enabled:
            return {
                "cache_enabled": False,
                "model_cached": False,
                "prediction_cache_count": 0
            }
        
        model_cache_key = f"model:{model_version_id}"
        prediction_pattern = f"prediction:{model_version_id}:*"
        
        try:
            model_cached = self.redis_client.exists(model_cache_key) > 0
            prediction_keys = list(self.redis_client.scan_iter(match=prediction_pattern))
            
            return {
                "cache_enabled": True,
                "model_cached": model_cached,
                "prediction_cache_count": len(prediction_keys),
                "model_cache_ttl": self.redis_client.ttl(model_cache_key) if model_cached else None
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {
                "cache_enabled": True,
                "error": str(e)
            }


def create_prediction_service(redis_client: Optional[redis.Redis] = None) -> PredictionService:
    """
    Factory function to create a PredictionService instance.
    
    Args:
        redis_client: Optional Redis client for caching
        
    Returns:
        PredictionService instance
    """
    return PredictionService(redis_client=redis_client)
