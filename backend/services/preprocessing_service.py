import logging
from typing import Any, Dict, List, Tuple
from uuid import UUID

import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sqlalchemy.orm import Session

from backend.domain.models.customer_record import CustomerRecord
from backend.domain.models.dataset import Dataset
from backend.domain.models.preprocessing_config import PreprocessingConfig

logger = logging.getLogger(__name__)


BINARY_FEATURES = ["gender", "partner", "dependents", "phone_service", "paperless_billing"]


MULTI_CLASS_FEATURES = [
    "contract",
    "internet_service",
    "multiple_lines",
    "online_security",
    "online_backup",
    "device_protection",
    "tech_support",
    "streaming_tv",
    "streaming_movies",
]


NUMERIC_FEATURES = ["tenure", "monthly_charges", "total_charges"]


ALL_FEATURES = BINARY_FEATURES + MULTI_CLASS_FEATURES + NUMERIC_FEATURES + ["senior_citizen"]


class PreprocessingService:
    @staticmethod
    def preprocess_dataset(
        db: Session,
        dataset_id: UUID,
        test_size: float = 0.2,
        random_state: int = 42,
        apply_smote: bool = True,
    ) -> Dict[str, Any]:
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            raise ValueError(f"Dataset {dataset_id} not found")

        records = db.query(CustomerRecord).filter(CustomerRecord.dataset_id == dataset_id).all()

        if not records:
            raise ValueError(f"No customer records found for dataset {dataset_id}")

        df = PreprocessingService._records_to_dataframe(records)

        df = PreprocessingService._convert_total_charges(df)

        df, imputation_params = PreprocessingService._impute_missing_values(df)

        df, outlier_params = PreprocessingService._treat_outliers(df)

        df, encoding_params = PreprocessingService._encode_features(df)

        X = df.drop(columns=["churn"])
        y = df["churn"]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )

        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        X_train_scaled = pd.DataFrame(X_train_scaled, columns=X_train.columns, index=X_train.index)
        X_test_scaled = pd.DataFrame(X_test_scaled, columns=X_test.columns, index=X_test.index)

        smote_config = {"applied": False}
        if apply_smote:
            smote = SMOTE(random_state=random_state)
            X_train_resampled, y_train_resampled = smote.fit_resample(X_train_scaled, y_train)

            X_train_scaled = pd.DataFrame(X_train_resampled, columns=X_train_scaled.columns)
            y_train = pd.Series(y_train_resampled, name="churn")

            smote_config = {
                "applied": True,
                "sampling_strategy": "auto",
                "k_neighbors": 5,
                "random_state": random_state,
                "original_train_size": len(y_train),
                "resampled_train_size": len(y_train_resampled),
            }

        preprocessing_params = {
            "imputation": imputation_params,
            "outlier_treatment": outlier_params,
            "encoding": encoding_params,
            "scaler": {
                "mean": scaler.mean_.tolist(),
                "scale": scaler.scale_.tolist(),
                "var": scaler.var_.tolist(),
                "feature_names": X_train.columns.tolist(),
            },
            "smote": smote_config,
            "feature_columns": X_train_scaled.columns.tolist(),
            "test_size": test_size,
            "random_state": random_state,
        }

        preprocessing_config = PreprocessingConfig(
            dataset_id=dataset_id,
            encoding_mappings=encoding_params,
            scaler_params={
                "mean": scaler.mean_.tolist(),
                "scale": scaler.scale_.tolist(),
                "var": scaler.var_.tolist(),
                "feature_names": X_train.columns.tolist(),
            },
            smote_config=smote_config,
            feature_columns=X_train_scaled.columns.tolist(),
        )
        db.add(preprocessing_config)
        db.commit()
        db.refresh(preprocessing_config)

        return {
            "X_train": X_train_scaled,
            "X_test": X_test_scaled,
            "y_train": y_train,
            "y_test": y_test,
            "preprocessing_config_id": preprocessing_config.id,
            "preprocessing_params": preprocessing_params,
            "original_train_size": (
                len(y_train) if not apply_smote else smote_config["original_train_size"]
            ),
            "final_train_size": len(y_train),
            "test_size": len(y_test),
            "feature_count": len(X_train_scaled.columns),
        }

    @staticmethod
    def _records_to_dataframe(records: List[CustomerRecord]) -> pd.DataFrame:
        data = []
        for record in records:
            row = {
                "gender": record.gender,
                "senior_citizen": record.senior_citizen,
                "partner": record.partner,
                "dependents": record.dependents,
                "tenure": record.tenure,
                "phone_service": record.phone_service,
                "multiple_lines": record.multiple_lines,
                "internet_service": record.internet_service,
                "online_security": record.online_security,
                "online_backup": record.online_backup,
                "device_protection": record.device_protection,
                "tech_support": record.tech_support,
                "streaming_tv": record.streaming_tv,
                "streaming_movies": record.streaming_movies,
                "contract": record.contract,
                "paperless_billing": record.paperless_billing,
                "monthly_charges": record.monthly_charges,
                "total_charges": record.total_charges,
                "churn": record.churn,
            }
            data.append(row)

        return pd.DataFrame(data)

    @staticmethod
    def _convert_total_charges(df: pd.DataFrame) -> pd.DataFrame:
        df["total_charges"] = df["total_charges"].replace(r"^\s*$", np.nan, regex=True)

        df["total_charges"] = pd.to_numeric(df["total_charges"], errors="coerce")

        return df

    @staticmethod
    def _impute_missing_values(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        imputation_params = {"numeric": {}, "categorical": {}}

        for col in NUMERIC_FEATURES:
            if col in df.columns:
                median_value = df[col].median()
                df[col] = df[col].fillna(median_value)
                imputation_params["numeric"][col] = float(median_value)

        categorical_cols = BINARY_FEATURES + MULTI_CLASS_FEATURES
        for col in categorical_cols:
            if col in df.columns:
                mode_value = df[col].mode()[0] if not df[col].mode().empty else None
                if mode_value is not None:
                    df[col] = df[col].fillna(mode_value)
                    imputation_params["categorical"][col] = mode_value

        return df, imputation_params

    @staticmethod
    def _treat_outliers(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        outlier_params = {}

        for col in NUMERIC_FEATURES:
            if col in df.columns:
                q1 = df[col].quantile(0.25)
                q3 = df[col].quantile(0.75)
                iqr = q3 - q1

                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr

                df[col] = df[col].clip(lower=lower_bound, upper=upper_bound)

                outlier_params[col] = {
                    "q1": float(q1),
                    "q3": float(q3),
                    "iqr": float(iqr),
                    "lower_bound": float(lower_bound),
                    "upper_bound": float(upper_bound),
                }

        return df, outlier_params

    @staticmethod
    def _encode_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        encoding_params = {"binary": {}, "one_hot": {}, "target": {}}

        for col in BINARY_FEATURES:
            if col in df.columns:
                unique_values = df[col].unique()
                if len(unique_values) <= 2:
                    mapping = {val: idx for idx, val in enumerate(sorted(unique_values))}
                    df[col] = df[col].map(mapping)
                    encoding_params["binary"][col] = mapping

        one_hot_columns = []
        for col in MULTI_CLASS_FEATURES:
            if col in df.columns:
                unique_values = df[col].unique().tolist()
                encoding_params["one_hot"][col] = unique_values

                dummies = pd.get_dummies(df[col], prefix=col, drop_first=False)
                one_hot_columns.extend(dummies.columns.tolist())

                df = df.drop(columns=[col])
                df = pd.concat([df, dummies], axis=1)

        if "churn" in df.columns:
            if df["churn"].dtype == bool:
                df["churn"] = df["churn"].astype(int)
                encoding_params["target"]["churn"] = {"True": 1, "False": 0}
            else:
                churn_mapping = {"Yes": 1, "No": 0}
                df["churn"] = df["churn"].map(churn_mapping)
                encoding_params["target"]["churn"] = churn_mapping

        return df, encoding_params

    @staticmethod
    def apply_preprocessing_to_input(
        db: Session, preprocessing_config_id: UUID, input_data: Dict[str, Any]
    ) -> np.ndarray:
        config = (
            db.query(PreprocessingConfig)
            .filter(PreprocessingConfig.id == preprocessing_config_id)
            .first()
        )

        if not config:
            raise ValueError(f"PreprocessingConfig {preprocessing_config_id} not found")

        df = pd.DataFrame([input_data])

        encoding_params = config.encoding_mappings

        for col, mapping in encoding_params.get("binary", {}).items():
            if col in df.columns:
                df[col] = df[col].map(mapping)

        for col, unique_values in encoding_params.get("one_hot", {}).items():
            if col in df.columns:
                dummies = pd.get_dummies(df[col], prefix=col, drop_first=False)
                df = df.drop(columns=[col])
                df = pd.concat([df, dummies], axis=1)

        expected_columns = config.feature_columns
        for col in expected_columns:
            if col not in df.columns:
                df[col] = 0

        df = df[expected_columns]

        scaler_params = config.scaler_params
        mean = np.array(scaler_params["mean"])
        scale = np.array(scaler_params["scale"])

        X_scaled = (df.values - mean) / scale

        return X_scaled
