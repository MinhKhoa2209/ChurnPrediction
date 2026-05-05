"""
Data Preprocessing Service
- Column operations (dropping customerID, type conversion)
- Missing value imputation
- Outlier treatment with IQR Winsorization
- Feature encoding (label encoding and one-hot encoding)
- Feature scaling with StandardScaler
- Stratified train-test split
- SMOTE for class imbalance
- Preprocessing parameter storage
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID
import json

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from imblearn.over_sampling import SMOTE

from backend.domain.models.customer_record import CustomerRecord
from backend.domain.models.dataset import Dataset
from backend.domain.models.preprocessing_config import PreprocessingConfig

logger = logging.getLogger(__name__)

# Binary categorical features for label encoding (0/1)
BINARY_FEATURES = [
    "gender", "partner", "dependents", "phone_service", "paperless_billing"
]

# Multi-class categorical features for one-hot encoding
MULTI_CLASS_FEATURES = [
    "contract", "internet_service", "multiple_lines", "online_security",
    "online_backup", "device_protection", "tech_support", "streaming_tv",
    "streaming_movies"
]

# Numeric features for scaling and outlier treatment
NUMERIC_FEATURES = ["tenure", "monthly_charges", "total_charges"]

# All features (excluding customerID and target)
ALL_FEATURES = BINARY_FEATURES + MULTI_CLASS_FEATURES + NUMERIC_FEATURES + ["senior_citizen"]


class PreprocessingService:
    """Service for data preprocessing and feature engineering"""
    
    @staticmethod
    def preprocess_dataset(
        db: Session,
        dataset_id: UUID,
        test_size: float = 0.2,
        random_state: int = 42,
        apply_smote: bool = True
    ) -> Dict[str, Any]:
        """
        Preprocess a dataset for model training
        
        - 4.2: Convert TotalCharges to float64
        - 4.3, 4.4: Impute missing values
        - 4.5: Outlier treatment with IQR Winsorization
        - 4.6, 4.7, 4.8: Feature encoding
        - 4.9: Feature scaling with StandardScaler
        - 4.10: Stratified train-test split
        - 4.11: SMOTE for class imbalance
        - 4.12, 4.13: Store preprocessing parameters
        
        Args:
            db: Database session
            dataset_id: Dataset UUID
            test_size: Proportion of test set (default 0.2 for 80/20 split)
            random_state: Random seed for reproducibility
            apply_smote: Whether to apply SMOTE to training set
            
        Returns:
            Dictionary containing preprocessed data and parameters
        """
        # Get dataset
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            raise ValueError(f"Dataset {dataset_id} not found")
        
        # Get all customer records for this dataset
        records = db.query(CustomerRecord).filter(
            CustomerRecord.dataset_id == dataset_id
        ).all()
        
        if not records:
            raise ValueError(f"No customer records found for dataset {dataset_id}")
        
        # Convert records to DataFrame (Requirement 4.1: Drop customerID)
        df = PreprocessingService._records_to_dataframe(records)
        
        # Step 1: Convert TotalCharges to float64 (Requirement 4.2)
        df = PreprocessingService._convert_total_charges(df)
        
        # Step 2: Handle missing values (Requirements 4.3, 4.4)
        df, imputation_params = PreprocessingService._impute_missing_values(df)
        
        # Step 3: Outlier treatment (Requirement 4.5)
        df, outlier_params = PreprocessingService._treat_outliers(df)
        
        # Step 4: Feature encoding (Requirements 4.6, 4.7, 4.8)
        df, encoding_params = PreprocessingService._encode_features(df)
        
        # Step 5: Separate features and target
        X = df.drop(columns=["churn"])
        y = df["churn"]
        
        # Step 6: Stratified train-test split (Requirement 4.10)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
        
        # Step 7: Feature scaling (Requirement 4.9)
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Convert back to DataFrame to preserve column names
        X_train_scaled = pd.DataFrame(X_train_scaled, columns=X_train.columns, index=X_train.index)
        X_test_scaled = pd.DataFrame(X_test_scaled, columns=X_test.columns, index=X_test.index)
        
        # Step 8: SMOTE for class imbalance (Requirement 4.11)
        smote_config = {"applied": False}
        if apply_smote:
            smote = SMOTE(random_state=random_state)
            X_train_resampled, y_train_resampled = smote.fit_resample(X_train_scaled, y_train)
            
            # Convert back to DataFrame
            X_train_scaled = pd.DataFrame(
                X_train_resampled, 
                columns=X_train_scaled.columns
            )
            y_train = pd.Series(y_train_resampled, name="churn")
            
            smote_config = {
                "applied": True,
                "sampling_strategy": "auto",
                "k_neighbors": 5,
                "random_state": random_state,
                "original_train_size": len(y_train),
                "resampled_train_size": len(y_train_resampled)
            }
        
        # Step 9: Store preprocessing parameters (Requirements 4.12, 4.13, 26.1, 26.2)
        preprocessing_params = {
            "imputation": imputation_params,
            "outlier_treatment": outlier_params,
            "encoding": encoding_params,
            "scaler": {
                "mean": scaler.mean_.tolist(),
                "scale": scaler.scale_.tolist(),
                "var": scaler.var_.tolist(),
                "feature_names": X_train.columns.tolist()
            },
            "smote": smote_config,
            "feature_columns": X_train_scaled.columns.tolist(),
            "test_size": test_size,
            "random_state": random_state
        }
        
        # Save preprocessing config to database
        preprocessing_config = PreprocessingConfig(
            dataset_id=dataset_id,
            encoding_mappings=encoding_params,
            scaler_params={
                "mean": scaler.mean_.tolist(),
                "scale": scaler.scale_.tolist(),
                "var": scaler.var_.tolist(),
                "feature_names": X_train.columns.tolist()
            },
            smote_config=smote_config,
            feature_columns=X_train_scaled.columns.tolist()
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
            "original_train_size": len(y_train) if not apply_smote else smote_config["original_train_size"],
            "final_train_size": len(y_train),
            "test_size": len(y_test),
            "feature_count": len(X_train_scaled.columns)
        }
    
    @staticmethod
    def _records_to_dataframe(records: List[CustomerRecord]) -> pd.DataFrame:
        """
        Convert CustomerRecord objects to DataFrame
        Requirement 4.1: Drop customerID column before preprocessing
        
        Args:
            records: List of CustomerRecord instances
            
        Returns:
            DataFrame with customer data (customerID excluded)
        """
        data = []
        for record in records:
            row = {
                # Demographic features
                "gender": record.gender,
                "senior_citizen": record.senior_citizen,
                "partner": record.partner,
                "dependents": record.dependents,
                # Service features
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
                # Billing features
                "contract": record.contract,
                "paperless_billing": record.paperless_billing,
                "monthly_charges": record.monthly_charges,
                "total_charges": record.total_charges,
                # Target variable
                "churn": record.churn
            }
            data.append(row)
        
        return pd.DataFrame(data)
    
    @staticmethod
    def _convert_total_charges(df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert TotalCharges from string to float64
        Requirement 4.2: Convert TotalCharges with coercion, handle whitespace as NaN
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with TotalCharges converted to float64
        """
        # Handle whitespace-only values as NaN (occurs when tenure = 0)
        df["total_charges"] = df["total_charges"].replace(r'^\s*$', np.nan, regex=True)
        
        # Convert to float64 with coercion
        df["total_charges"] = pd.to_numeric(df["total_charges"], errors="coerce")
        
        return df
    
    @staticmethod
    def _impute_missing_values(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Impute missing values
        Requirement 4.3: Impute numeric columns with median
        Requirement 4.4: Impute categorical columns with mode
        
        Args:
            df: Input DataFrame
            
        Returns:
            Tuple of (DataFrame with imputed values, imputation parameters)
        """
        imputation_params = {
            "numeric": {},
            "categorical": {}
        }
        
        # Impute numeric columns with median
        for col in NUMERIC_FEATURES:
            if col in df.columns:
                median_value = df[col].median()
                df[col] = df[col].fillna(median_value)
                imputation_params["numeric"][col] = float(median_value)
        
        # Impute categorical columns with mode
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
        """
        Detect and treat outliers using IQR Winsorization
        Requirement 4.5: Apply IQR-based Winsorization to numeric columns
        
        Args:
            df: Input DataFrame
            
        Returns:
            Tuple of (DataFrame with treated outliers, outlier parameters)
        """
        outlier_params = {}
        
        for col in NUMERIC_FEATURES:
            if col in df.columns:
                # Compute IQR
                q1 = df[col].quantile(0.25)
                q3 = df[col].quantile(0.75)
                iqr = q3 - q1
                
                # Compute bounds
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                
                # Apply Winsorization (cap values at boundaries)
                df[col] = df[col].clip(lower=lower_bound, upper=upper_bound)
                
                outlier_params[col] = {
                    "q1": float(q1),
                    "q3": float(q3),
                    "iqr": float(iqr),
                    "lower_bound": float(lower_bound),
                    "upper_bound": float(upper_bound)
                }
        
        return df, outlier_params
    
    @staticmethod
    def _encode_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Encode categorical features
        Requirement 4.6: Label encode binary features as 0/1
        Requirement 4.7: One-hot encode multi-class features
        Requirement 4.8: Encode target Churn as 1 (Yes) / 0 (No)
        
        Args:
            df: Input DataFrame
            
        Returns:
            Tuple of (DataFrame with encoded features, encoding parameters)
        """
        encoding_params = {
            "binary": {},
            "one_hot": {},
            "target": {}
        }
        
        # Label encode binary features (Requirement 4.6)
        for col in BINARY_FEATURES:
            if col in df.columns:
                # Create mapping for binary features
                unique_values = df[col].unique()
                if len(unique_values) <= 2:
                    # Map to 0/1
                    mapping = {val: idx for idx, val in enumerate(sorted(unique_values))}
                    df[col] = df[col].map(mapping)
                    encoding_params["binary"][col] = mapping
        
        # One-hot encode multi-class features (Requirement 4.7)
        one_hot_columns = []
        for col in MULTI_CLASS_FEATURES:
            if col in df.columns:
                # Get unique values for this column
                unique_values = df[col].unique().tolist()
                encoding_params["one_hot"][col] = unique_values
                
                # One-hot encode
                dummies = pd.get_dummies(df[col], prefix=col, drop_first=False)
                one_hot_columns.extend(dummies.columns.tolist())
                
                # Drop original column and add dummy columns
                df = df.drop(columns=[col])
                df = pd.concat([df, dummies], axis=1)
        
        # Encode target variable (Requirement 4.8)
        if "churn" in df.columns:
            # Map Yes/No or True/False to 1/0
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
        db: Session,
        preprocessing_config_id: UUID,
        input_data: Dict[str, Any]
    ) -> np.ndarray:
        """
        Apply stored preprocessing parameters to new input data
            db: Database session
            preprocessing_config_id: PreprocessingConfig UUID
            input_data: Dictionary of feature values
            
        Returns:
            Preprocessed feature vector as numpy array
        """
        # Get preprocessing config
        config = db.query(PreprocessingConfig).filter(
            PreprocessingConfig.id == preprocessing_config_id
        ).first()
        
        if not config:
            raise ValueError(f"PreprocessingConfig {preprocessing_config_id} not found")
        
        # Convert input to DataFrame
        df = pd.DataFrame([input_data])
        
        # Apply encoding
        encoding_params = config.encoding_mappings
        
        # Label encode binary features
        for col, mapping in encoding_params.get("binary", {}).items():
            if col in df.columns:
                df[col] = df[col].map(mapping)
        
        # One-hot encode multi-class features
        for col, unique_values in encoding_params.get("one_hot", {}).items():
            if col in df.columns:
                dummies = pd.get_dummies(df[col], prefix=col, drop_first=False)
                df = df.drop(columns=[col])
                df = pd.concat([df, dummies], axis=1)
        
        # Ensure all expected columns are present
        expected_columns = config.feature_columns
        for col in expected_columns:
            if col not in df.columns:
                df[col] = 0
        
        # Reorder columns to match training
        df = df[expected_columns]
        
        # Apply scaling
        scaler_params = config.scaler_params
        mean = np.array(scaler_params["mean"])
        scale = np.array(scaler_params["scale"])
        
        # Standardize: (X - mean) / scale
        X_scaled = (df.values - mean) / scale
        
        return X_scaled
