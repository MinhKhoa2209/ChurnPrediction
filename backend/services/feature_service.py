"""
Feature Engineering Service
feature importance computation using mutual information and feature selection.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any
from uuid import UUID

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from sklearn.feature_selection import mutual_info_classif

from backend.domain.models.customer_record import CustomerRecord
from backend.domain.models.dataset import Dataset

logger = logging.getLogger(__name__)


class FeatureService:
    """Service for feature engineering and selection operations"""

    @staticmethod
    def compute_feature_importance(
        db: Session, dataset_id: UUID, user_id: UUID
    ) -> Dict[str, Any]:
        """
        Compute feature importance scores using mutual information
        
        - Requirement 6.2: Rank features by importance score in descending order
        
        Args:
            db: Database session
            dataset_id: UUID of the dataset
            user_id: UUID of the user (for authorization check)
            
        Returns:
            Dictionary containing:
            - datasetId: UUID of the dataset
            - featureImportance: List of objects with featureName and importanceScore
            - recordCount: Number of records used in computation
            
        Raises:
            ValueError: If dataset not found, user not authorized, or invalid data
        """
        # Verify dataset exists and belongs to user (Requirement 18.9)
        dataset = db.query(Dataset).filter(
            Dataset.id == dataset_id,
            Dataset.user_id == user_id
        ).first()
        
        if not dataset:
            raise ValueError("Dataset not found or access denied")
        
        # Check dataset is ready for analysis
        if dataset.status != "ready":
            raise ValueError(f"Dataset is not ready for analysis. Current status: {dataset.status}")
        
        # Fetch customer records for this dataset
        records = db.query(CustomerRecord).filter(
            CustomerRecord.dataset_id == dataset_id
        ).all()
        
        if not records:
            raise ValueError("No customer records found for this dataset")
        
        # Convert to DataFrame with all features
        data = []
        for record in records:
            data.append({
                # Demographic features
                "gender": record.gender,
                "SeniorCitizen": record.senior_citizen,
                "Partner": record.partner,
                "Dependents": record.dependents,
                # Service features
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
                # Billing features
                "Contract": record.contract,
                "PaperlessBilling": record.paperless_billing,
                "MonthlyCharges": record.monthly_charges,
                "TotalCharges": record.total_charges,
                # Target variable
                "Churn": record.churn,
            })
        
        df = pd.DataFrame(data)
        
        # Remove rows with missing target variable
        df_clean = df.dropna(subset=["Churn"])
        
        if df_clean.empty:
            raise ValueError("No valid data available for feature importance analysis")
        
        # Separate features and target
        y = df_clean["Churn"].astype(int)
        X = df_clean.drop(columns=["Churn"])
        
        # Encode categorical features for mutual information computation
        X_encoded = X.copy()
        
        # Label encode categorical features
        categorical_features = [
            "gender", "Partner", "Dependents", "PhoneService", "MultipleLines",
            "InternetService", "OnlineSecurity", "OnlineBackup", "DeviceProtection",
            "TechSupport", "StreamingTV", "StreamingMovies", "Contract", "PaperlessBilling"
        ]
        
        for col in categorical_features:
            if col in X_encoded.columns:
                # Convert to category codes (NaN becomes -1)
                X_encoded[col] = pd.Categorical(X_encoded[col]).codes
        
        # Handle missing values in numeric features (fill with median)
        numeric_features = ["tenure", "MonthlyCharges", "TotalCharges", "SeniorCitizen"]
        for col in numeric_features:
            if col in X_encoded.columns:
                X_encoded[col] = X_encoded[col].fillna(X_encoded[col].median())
        
        # Ensure all data is numeric
        X_encoded = X_encoded.apply(pd.to_numeric, errors="coerce")
        
        # Fill any remaining NaN values with 0
        X_encoded = X_encoded.fillna(0)
        
        # Compute mutual information scores (Requirement 6.1)
        # Use random_state for reproducibility
        mi_scores = mutual_info_classif(
            X_encoded, y, discrete_features="auto", random_state=42
        )
        
        # Create feature importance list with feature names and scores
        feature_importance = []
        for feature_name, score in zip(X.columns, mi_scores):
            feature_importance.append({
                "featureName": feature_name,
                "importanceScore": float(score)
            })
        
        # Sort by importance score in descending order (Requirement 6.2)
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
        selected_features: List[str] = None
    ) -> Dict[str, Any]:
        """
        Select features by importance threshold or explicit feature list
        
        - Requirement 6.4: Allow users to specify feature subset for training
        - Requirement 6.5: Train models using only selected features
        
        Args:
            db: Database session
            dataset_id: UUID of the dataset
            user_id: UUID of the user (for authorization check)
            importance_threshold: Optional threshold (0.0 to 1.0) to auto-select features
            selected_features: Optional list of feature names to select explicitly
            
        Returns:
            Dictionary containing:
            - datasetId: UUID of the dataset
            - selectedFeatures: List of objects with featureName and importanceScore
            - selectionMethod: "threshold" or "manual"
            - threshold: The threshold used (if applicable)
            
        Raises:
            ValueError: If dataset not found, user not authorized, invalid parameters,
                       or feature names not found
        """
        # Validate input: must provide either threshold or selected_features, but not both
        if importance_threshold is None and selected_features is None:
            raise ValueError("Must provide either importanceThreshold or selectedFeatures")
        
        if importance_threshold is not None and selected_features is not None:
            raise ValueError("Cannot provide both importanceThreshold and selectedFeatures")
        
        # Validate threshold range
        if importance_threshold is not None:
            if not (0.0 <= importance_threshold <= 1.0):
                raise ValueError("importanceThreshold must be between 0.0 and 1.0")
        
        # Verify dataset exists and belongs to user (Requirement 18.9)
        dataset = db.query(Dataset).filter(
            Dataset.id == dataset_id,
            Dataset.user_id == user_id
        ).first()
        
        if not dataset:
            raise ValueError("Dataset not found or access denied")
        
        # Check dataset is ready for analysis
        if dataset.status != "ready":
            raise ValueError(f"Dataset is not ready for analysis. Current status: {dataset.status}")
        
        # Compute feature importance to get all features and their scores
        importance_result = FeatureService.compute_feature_importance(
            db=db,
            dataset_id=dataset_id,
            user_id=user_id
        )
        
        all_features = importance_result["featureImportance"]
        
        # Select features based on method
        if importance_threshold is not None:
            # Auto-select features above threshold (Requirement 6.3)
            selected = [
                feature for feature in all_features
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
            # Manual feature selection (Requirement 6.4)
            # Validate that all selected features exist
            available_feature_names = {f["featureName"] for f in all_features}
            invalid_features = [f for f in selected_features if f not in available_feature_names]
            
            if invalid_features:
                raise ValueError(
                    f"Invalid feature names: {', '.join(invalid_features)}. "
                    f"Available features: {', '.join(sorted(available_feature_names))}"
                )
            
            # Get importance scores for selected features
            feature_dict = {f["featureName"]: f["importanceScore"] for f in all_features}
            selected = [
                {
                    "featureName": feature_name,
                    "importanceScore": feature_dict[feature_name]
                }
                for feature_name in selected_features
            ]
            
            # Sort by importance score in descending order
            selected.sort(key=lambda x: x["importanceScore"], reverse=True)
            
            selection_method = "manual"
            threshold_value = None
        
        # Store feature selection configuration in dataset metadata
        # This will be used during model training (Requirement 6.5)
        feature_selection_config = {
            "selectedFeatures": [f["featureName"] for f in selected],
            "selectionMethod": selection_method,
            "threshold": threshold_value,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Update dataset with feature selection config
        if dataset.validation_errors is None:
            dataset.validation_errors = {}
        
        # Store in validation_errors JSONB field (repurposing for metadata)
        # In a production system, you might want a dedicated metadata field
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
    def create_interaction_features(
        db: Session,
        dataset_id: UUID,
        user_id: UUID
    ) -> Dict[str, Any]:
        """
        Create interaction features for the dataset
        
        
        Args:
            db: Database session
            dataset_id: UUID of the dataset
            user_id: UUID of the user (for authorization check)
            
        Returns:
            Dictionary containing:
            - datasetId: UUID of the dataset
            - interactionFeatures: List of created interaction features with details
            - recordCount: Number of records processed
            
        Raises:
            ValueError: If dataset not found, user not authorized, or missing required features
        """
        # Verify dataset exists and belongs to user (Requirement 18.9)
        dataset = db.query(Dataset).filter(
            Dataset.id == dataset_id,
            Dataset.user_id == user_id
        ).first()
        
        if not dataset:
            raise ValueError("Dataset not found or access denied")
        
        # Check dataset is ready for analysis
        if dataset.status != "ready":
            raise ValueError(f"Dataset is not ready for analysis. Current status: {dataset.status}")
        
        # Fetch customer records for this dataset
        records = db.query(CustomerRecord).filter(
            CustomerRecord.dataset_id == dataset_id
        ).all()
        
        if not records:
            raise ValueError("No customer records found for this dataset")
        
        # Create interaction feature: tenure × MonthlyCharges
        interaction_features = []
        
        # Compute interaction feature for all records
        interaction_values = []
        for record in records:
            tenure = record.tenure if record.tenure is not None else 0
            monthly_charges = record.monthly_charges if record.monthly_charges is not None else 0
            interaction_value = tenure * monthly_charges
            interaction_values.append(interaction_value)
        
        # Calculate statistics for the interaction feature
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
                "median": float(np.median(interaction_array))
            }
        }
        
        interaction_features.append(interaction_feature)
        
        # Store interaction feature configuration in dataset metadata
        interaction_config = {
            "interactionFeatures": [
                {
                    "featureName": "tenure_x_MonthlyCharges",
                    "formula": "tenure × MonthlyCharges",
                    "components": ["tenure", "MonthlyCharges"]
                }
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Update dataset with interaction feature config
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
