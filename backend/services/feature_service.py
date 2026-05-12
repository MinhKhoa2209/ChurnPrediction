import logging
from datetime import datetime
from typing import Any, Dict, List
from uuid import UUID

import numpy as np
import pandas as pd
from sklearn.feature_selection import mutual_info_classif
from sqlalchemy.orm import Session

from backend.domain.models.customer_record import CustomerRecord
from backend.domain.models.dataset import Dataset

logger = logging.getLogger(__name__)


class FeatureService:
    @staticmethod
    def compute_feature_importance(db: Session, dataset_id: UUID, user_id: UUID) -> Dict[str, Any]:
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()

        if not dataset:
            raise ValueError("Dataset not found")

        if dataset.status != "ready":
            raise ValueError(f"Dataset is not ready for analysis. Current status: {dataset.status}")

        records = db.query(CustomerRecord).filter(CustomerRecord.dataset_id == dataset_id).all()

        if not records:
            raise ValueError("No customer records found for this dataset")

        data = []
        for record in records:
            data.append(
                {
                    "gender": record.gender,
                    "SeniorCitizen": record.senior_citizen,
                    "Partner": record.partner,
                    "Dependents": record.dependents,
                    "tenure": record.tenure,
                    "PhoneService": record.phone_service,
                    "MultipleLines": record.multiple_lines,
                    "InternetService": record.internet_service,
                    "OnlineSecurity": record.online_security,
                    "OnlineBackup": record.online_backup,
                    "DeviceProtection": record.device_protection,
                    "TechSupport": record.tech_support,
                    "StreamingTV": record.streaming_tv,
                    "StreamingMovies": record.streaming_movies,
                    "Contract": record.contract,
                    "PaperlessBilling": record.paperless_billing,
                    "MonthlyCharges": record.monthly_charges,
                    "TotalCharges": record.total_charges,
                    "Churn": record.churn,
                }
            )

        df = pd.DataFrame(data)

        df_clean = df.dropna(subset=["Churn"])

        if df_clean.empty:
            raise ValueError("No valid data available for feature importance analysis")

        y = df_clean["Churn"].astype(int)
        X = df_clean.drop(columns=["Churn"])

        X_encoded = X.copy()

        categorical_features = [
            "gender",
            "Partner",
            "Dependents",
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
        ]

        for col in categorical_features:
            if col in X_encoded.columns:
                X_encoded[col] = pd.Categorical(X_encoded[col]).codes

        numeric_features = ["tenure", "MonthlyCharges", "TotalCharges", "SeniorCitizen"]
        for col in numeric_features:
            if col in X_encoded.columns:
                X_encoded[col] = X_encoded[col].fillna(X_encoded[col].median())

        X_encoded = X_encoded.apply(pd.to_numeric, errors="coerce")

        X_encoded = X_encoded.fillna(0)

        mi_scores = mutual_info_classif(X_encoded, y, discrete_features="auto", random_state=42)

        feature_importance = []
        for feature_name, score in zip(X.columns, mi_scores):
            feature_importance.append(
                {"featureName": feature_name, "importanceScore": float(score)}
            )

        feature_importance.sort(key=lambda x: x["importanceScore"], reverse=True)

        logger.info(
            f"Computed feature importance for dataset {dataset_id} "
            f"with {len(df_clean)} records and {len(feature_importance)} features"
        )

        return {
            "datasetId": str(dataset_id),
            "featureImportance": feature_importance,
            "recordCount": len(df_clean),
        }

    @staticmethod
    def select_features_by_importance(
        db: Session,
        dataset_id: UUID,
        user_id: UUID,
        importance_threshold: float = None,
        selected_features: List[str] = None,
    ) -> Dict[str, Any]:
        if importance_threshold is None and selected_features is None:
            raise ValueError("Must provide either importanceThreshold or selectedFeatures")

        if importance_threshold is not None and selected_features is not None:
            raise ValueError("Cannot provide both importanceThreshold and selectedFeatures")

        if importance_threshold is not None:
            if not (0.0 <= importance_threshold <= 1.0):
                raise ValueError("importanceThreshold must be between 0.0 and 1.0")

        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()

        if not dataset:
            raise ValueError("Dataset not found")

        if dataset.status != "ready":
            raise ValueError(f"Dataset is not ready for analysis. Current status: {dataset.status}")

        importance_result = FeatureService.compute_feature_importance(
            db=db, dataset_id=dataset_id, user_id=user_id
        )

        all_features = importance_result["featureImportance"]

        if importance_threshold is not None:
            selected = [
                feature
                for feature in all_features
                if feature["importanceScore"] >= importance_threshold
            ]

            if not selected:
                raise ValueError(
                    f"No features found with importance >= {importance_threshold}. "
                    f"Maximum importance score: {all_features[0]['importanceScore']:.4f}"
                )

            selection_method = "threshold"
            threshold_value = importance_threshold

        else:
            available_feature_names = {f["featureName"] for f in all_features}
            invalid_features = [f for f in selected_features if f not in available_feature_names]

            if invalid_features:
                raise ValueError(
                    f"Invalid feature names: {', '.join(invalid_features)}. "
                    f"Available features: {', '.join(sorted(available_feature_names))}"
                )

            feature_dict = {f["featureName"]: f["importanceScore"] for f in all_features}
            selected = [
                {"featureName": feature_name, "importanceScore": feature_dict[feature_name]}
                for feature_name in selected_features
            ]

            selected.sort(key=lambda x: x["importanceScore"], reverse=True)

            selection_method = "manual"
            threshold_value = None

        feature_selection_config = {
            "selectedFeatures": [f["featureName"] for f in selected],
            "selectionMethod": selection_method,
            "threshold": threshold_value,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if dataset.validation_errors is None:
            dataset.validation_errors = {}

        if not isinstance(dataset.validation_errors, dict):
            dataset.validation_errors = {}

        dataset.validation_errors["feature_selection"] = feature_selection_config
        db.commit()

        logger.info(
            f"Selected {len(selected)} features for dataset {dataset_id} "
            f"using {selection_method} method"
        )

        return {
            "datasetId": str(dataset_id),
            "selectedFeatures": selected,
            "selectionMethod": selection_method,
            "threshold": threshold_value,
        }

    @staticmethod
    def create_interaction_features(db: Session, dataset_id: UUID, user_id: UUID) -> Dict[str, Any]:
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()

        if not dataset:
            raise ValueError("Dataset not found")

        if dataset.status != "ready":
            raise ValueError(f"Dataset is not ready for analysis. Current status: {dataset.status}")

        records = db.query(CustomerRecord).filter(CustomerRecord.dataset_id == dataset_id).all()

        if not records:
            raise ValueError("No customer records found for this dataset")

        interaction_features = []

        interaction_values = []
        for record in records:
            tenure = record.tenure if record.tenure is not None else 0
            monthly_charges = record.monthly_charges if record.monthly_charges is not None else 0
            interaction_value = tenure * monthly_charges
            interaction_values.append(interaction_value)

        interaction_array = np.array(interaction_values)

        interaction_feature = {
            "featureName": "tenure_x_MonthlyCharges",
            "formula": "tenure × MonthlyCharges",
            "description": "Interaction between customer tenure and monthly charges",
            "statistics": {
                "mean": float(np.mean(interaction_array)),
                "std": float(np.std(interaction_array)),
                "min": float(np.min(interaction_array)),
                "max": float(np.max(interaction_array)),
                "median": float(np.median(interaction_array)),
            },
        }

        interaction_features.append(interaction_feature)

        interaction_config = {
            "interactionFeatures": [
                {
                    "featureName": "tenure_x_MonthlyCharges",
                    "formula": "tenure × MonthlyCharges",
                    "components": ["tenure", "MonthlyCharges"],
                }
            ],
            "timestamp": datetime.utcnow().isoformat(),
        }

        if dataset.validation_errors is None:
            dataset.validation_errors = {}

        if not isinstance(dataset.validation_errors, dict):
            dataset.validation_errors = {}

        dataset.validation_errors["interaction_features"] = interaction_config
        db.commit()

        logger.info(
            f"Created {len(interaction_features)} interaction feature(s) for dataset {dataset_id} "
            f"with {len(records)} records"
        )

        return {
            "datasetId": str(dataset_id),
            "interactionFeatures": interaction_features,
            "recordCount": len(records),
        }
