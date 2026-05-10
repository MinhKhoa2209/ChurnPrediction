import logging
from typing import Any, Dict, List
from uuid import UUID

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from backend.domain.models.model_version import ModelVersion
from backend.domain.models.preprocessing_config import PreprocessingConfig

logger = logging.getLogger(__name__)


class PredictionPreprocessingError(Exception):
    pass


class PreprocessingConfigNotFoundError(PredictionPreprocessingError):
    pass


class PreprocessingArtifactNotFoundError(PredictionPreprocessingError):
    pass


class InputSchemaValidationError(PredictionPreprocessingError):
    pass


class PredictionPreprocessingService:
    EXPECTED_INPUT_FEATURES = [
        "gender",
        "SeniorCitizen",
        "Partner",
        "Dependents",
        "tenure",
        "PhoneService",
        "MultipleLines",
        "InternetService",
        "OnlineSecurity",
        "OnlineBackup",
        "DeviceProtection",
        "TechSupport",
        "StreamingTV",
        "StreamingMovies",
        "Contract",
        "PaperlessBilling",
        "PaymentMethod",
        "MonthlyCharges",
        "TotalCharges",
    ]

    @staticmethod
    def preprocess_for_prediction(
        db: Session, model_version_id: UUID, input_data: Dict[str, Any]
    ) -> np.ndarray:
        model_version = db.query(ModelVersion).filter(ModelVersion.id == model_version_id).first()

        if not model_version:
            raise PreprocessingConfigNotFoundError(f"Model version {model_version_id} not found")

        if not model_version.preprocessing_config_id:
            raise PreprocessingConfigNotFoundError(
                f"Model version {model_version_id} has no associated preprocessing config. "
                "This model version is invalid and cannot be used for predictions."
            )

        preprocessing_config = (
            db.query(PreprocessingConfig)
            .filter(PreprocessingConfig.id == model_version.preprocessing_config_id)
            .first()
        )

        if not preprocessing_config:
            raise PreprocessingConfigNotFoundError(
                f"Preprocessing config {model_version.preprocessing_config_id} not found. "
                "This model version is invalid and cannot be used for predictions."
            )

        PredictionPreprocessingService._validate_input_schema(input_data)

        normalized_input = PredictionPreprocessingService._normalize_input_fields(input_data)

        try:
            df = pd.DataFrame([normalized_input])

            df = PredictionPreprocessingService._convert_total_charges(df)

            df = PredictionPreprocessingService._apply_imputation(
                df, preprocessing_config.encoding_mappings
            )

            df = PredictionPreprocessingService._apply_outlier_treatment(
                df, preprocessing_config.encoding_mappings
            )

            df = PredictionPreprocessingService._apply_encoding(
                df, preprocessing_config.encoding_mappings
            )

            expected_columns = preprocessing_config.feature_columns
            for col in expected_columns:
                if col not in df.columns:
                    df[col] = 0

            df = df[expected_columns]

            for col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

            X_scaled = PredictionPreprocessingService._apply_scaling(
                df, preprocessing_config.scaler_params
            )

            logger.info(
                f"Successfully preprocessed input for model version {model_version_id}. "
                f"Output shape: {X_scaled.shape}"
            )

            return X_scaled

        except Exception as e:
            logger.error(f"Error during preprocessing: {e}")
            raise PredictionPreprocessingError(f"Failed to preprocess input data: {str(e)}")

    @staticmethod
    def _validate_input_schema(input_data: Dict[str, Any]) -> None:
        missing_features = []
        for feature in PredictionPreprocessingService.EXPECTED_INPUT_FEATURES:
            if feature not in input_data:
                missing_features.append(feature)

        if missing_features:
            raise InputSchemaValidationError(
                f"Missing required features: {', '.join(missing_features)}. "
                f"Expected features: {', '.join(PredictionPreprocessingService.EXPECTED_INPUT_FEATURES)}"
            )

        unexpected_features = set(input_data.keys()) - set(
            PredictionPreprocessingService.EXPECTED_INPUT_FEATURES
        )
        if unexpected_features:
            logger.warning(
                f"Unexpected features in input (will be ignored): {', '.join(unexpected_features)}"
            )

    @staticmethod
    def _normalize_input_fields(input_data: Dict[str, Any]) -> Dict[str, Any]:
        field_mapping = {
            "gender": "gender",
            "SeniorCitizen": "senior_citizen",
            "Partner": "partner",
            "Dependents": "dependents",
            "tenure": "tenure",
            "PhoneService": "phone_service",
            "MultipleLines": "multiple_lines",
            "InternetService": "internet_service",
            "OnlineSecurity": "online_security",
            "OnlineBackup": "online_backup",
            "DeviceProtection": "device_protection",
            "TechSupport": "tech_support",
            "StreamingTV": "streaming_tv",
            "StreamingMovies": "streaming_movies",
            "Contract": "contract",
            "PaperlessBilling": "paperless_billing",
            "PaymentMethod": "payment_method",
            "MonthlyCharges": "monthly_charges",
            "TotalCharges": "total_charges",
        }

        normalized = {}
        for input_key, training_key in field_mapping.items():
            if input_key in input_data:
                normalized[training_key] = input_data[input_key]

        return normalized

    @staticmethod
    def _convert_total_charges(df: pd.DataFrame) -> pd.DataFrame:
        if "total_charges" in df.columns:
            df["total_charges"] = df["total_charges"].replace(r"^\s*$", np.nan, regex=True)

            df["total_charges"] = pd.to_numeric(df["total_charges"], errors="coerce")

        return df

    @staticmethod
    def _apply_imputation(df: pd.DataFrame, encoding_mappings: Dict[str, Any]) -> pd.DataFrame:
        numeric_features = ["tenure", "monthly_charges", "total_charges"]
        for col in numeric_features:
            if col in df.columns and df[col].isna().any():
                median_value = df[col].median()
                if pd.notna(median_value):
                    df[col] = df[col].fillna(median_value)
                else:
                    df[col] = df[col].fillna(0)

        categorical_features = [
            "gender",
            "partner",
            "dependents",
            "phone_service",
            "paperless_billing",
            "contract",
            "internet_service",
            "multiple_lines",
            "online_security",
            "online_backup",
            "device_protection",
            "tech_support",
            "streaming_tv",
            "streaming_movies",
            "payment_method",
        ]
        for col in categorical_features:
            if col in df.columns and df[col].isna().any():
                mode_value = df[col].mode()
                if len(mode_value) > 0:
                    df[col] = df[col].fillna(mode_value[0])

        return df

    @staticmethod
    def _apply_outlier_treatment(
        df: pd.DataFrame, encoding_mappings: Dict[str, Any]
    ) -> pd.DataFrame:
        return df

    @staticmethod
    def _apply_encoding(df: pd.DataFrame, encoding_mappings: Dict[str, Any]) -> pd.DataFrame:
        if "binary" in encoding_mappings:
            for col, mapping in encoding_mappings["binary"].items():
                if col in df.columns:
                    df[col] = df[col].map(mapping)

                    df[col] = df[col].fillna(0)

                    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        if "one_hot" in encoding_mappings:
            for col, unique_values in encoding_mappings["one_hot"].items():
                if col in df.columns:
                    dummies = pd.get_dummies(df[col], prefix=col, drop_first=False)

                    for val in unique_values:
                        dummy_col = f"{col}_{val}"
                        if dummy_col not in dummies.columns:
                            dummies[dummy_col] = 0

                    for dummy_col in dummies.columns:
                        dummies[dummy_col] = dummies[dummy_col].astype(int)

                    df = df.drop(columns=[col])
                    df = pd.concat([df, dummies], axis=1)

        return df

    @staticmethod
    def _apply_scaling(df: pd.DataFrame, scaler_params: Dict[str, Any]) -> np.ndarray:
        mean = np.array(scaler_params["mean"])
        scale = np.array(scaler_params["scale"])

        X_scaled = (df.values - mean) / scale

        return X_scaled

    @staticmethod
    def get_expected_features() -> List[str]:
        return PredictionPreprocessingService.EXPECTED_INPUT_FEATURES.copy()

    @staticmethod
    def validate_preprocessing_config(db: Session, model_version_id: UUID) -> Dict[str, Any]:
        model_version = db.query(ModelVersion).filter(ModelVersion.id == model_version_id).first()

        if not model_version:
            raise PreprocessingConfigNotFoundError(f"Model version {model_version_id} not found")

        if not model_version.preprocessing_config_id:
            raise PreprocessingConfigNotFoundError(
                f"Model version {model_version_id} has no preprocessing config"
            )

        preprocessing_config = (
            db.query(PreprocessingConfig)
            .filter(PreprocessingConfig.id == model_version.preprocessing_config_id)
            .first()
        )

        if not preprocessing_config:
            raise PreprocessingConfigNotFoundError(
                f"Preprocessing config {model_version.preprocessing_config_id} not found"
            )

        required_fields = ["encoding_mappings", "scaler_params", "feature_columns"]
        missing_fields = []

        for field in required_fields:
            value = getattr(preprocessing_config, field, None)
            if value is None:
                missing_fields.append(field)

        if missing_fields:
            raise PreprocessingConfigNotFoundError(
                f"Preprocessing config is incomplete. Missing fields: {', '.join(missing_fields)}"
            )

        return {
            "valid": True,
            "model_version_id": str(model_version_id),
            "preprocessing_config_id": str(preprocessing_config.id),
            "feature_count": len(preprocessing_config.feature_columns),
            "has_encoding_mappings": bool(preprocessing_config.encoding_mappings),
            "has_scaler_params": bool(preprocessing_config.scaler_params),
        }
