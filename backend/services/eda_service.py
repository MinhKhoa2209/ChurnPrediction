import logging
from typing import Any, Dict
from uuid import UUID

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from backend.domain.models.customer_record import CustomerRecord
from backend.domain.models.dataset import Dataset

logger = logging.getLogger(__name__)


class EDAService:
    @staticmethod
    def _get_dataset_for_eda(db: Session, dataset_id: UUID, user_id: UUID, is_admin: bool = False) -> Dataset:
        """Get dataset with access check. Admin users can access any dataset."""
        if is_admin:
            dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        else:
            dataset = db.query(Dataset).filter(
                Dataset.id == dataset_id, Dataset.user_id == user_id
            ).first()

        if not dataset:
            raise ValueError("Dataset not found or access denied")

        if dataset.status != "ready":
            raise ValueError(f"Dataset is not ready for analysis. Current status: {dataset.status}")

        return dataset

    @staticmethod
    def get_correlation_matrix(db: Session, dataset_id: UUID, user_id: UUID, is_admin: bool = False) -> Dict[str, Any]:
        dataset = EDAService._get_dataset_for_eda(db, dataset_id, user_id, is_admin)

        records = db.query(CustomerRecord).filter(CustomerRecord.dataset_id == dataset_id).all()

        if not records:
            raise ValueError("No customer records found for this dataset")

        data = []
        for record in records:
            data.append(
                {
                    "tenure": record.tenure,
                    "MonthlyCharges": record.monthly_charges,
                    "TotalCharges": record.total_charges,
                    "SeniorCitizen": record.senior_citizen,
                }
            )

        df = pd.DataFrame(data)

        df_clean = df.dropna()

        if df_clean.empty:
            raise ValueError("No valid numeric data available for correlation analysis")

        correlation_matrix = df_clean.corr()

        features = correlation_matrix.columns.tolist()
        matrix_values = correlation_matrix.values.tolist()

        logger.info(
            f"Computed correlation matrix for dataset {dataset_id} "
            f"with {len(features)} features and {len(df_clean)} records"
        )

        return {
            "datasetId": str(dataset_id),
            "features": features,
            "correlationMatrix": matrix_values,
            "recordCount": len(df_clean),
        }

    @staticmethod
    def get_distributions(
        db: Session, dataset_id: UUID, user_id: UUID, bins: int = 10, is_admin: bool = False
    ) -> Dict[str, Any]:
        dataset = EDAService._get_dataset_for_eda(db, dataset_id, user_id, is_admin)

        records = db.query(CustomerRecord).filter(CustomerRecord.dataset_id == dataset_id).all()

        if not records:
            raise ValueError("No customer records found for this dataset")

        data = []
        for record in records:
            data.append(
                {
                    "tenure": record.tenure,
                    "MonthlyCharges": record.monthly_charges,
                    "TotalCharges": record.total_charges,
                }
            )

        df = pd.DataFrame(data)

        df_clean = df.dropna()

        if df_clean.empty:
            raise ValueError("No valid numeric data available for distribution analysis")

        distributions = {}

        for feature in ["tenure", "MonthlyCharges", "TotalCharges"]:
            feature_data = df_clean[feature].values

            counts, bin_edges = np.histogram(feature_data, bins=bins)

            distributions[feature] = {
                "bins": bin_edges.tolist(),
                "frequencies": counts.tolist(),
                "min": float(feature_data.min()),
                "max": float(feature_data.max()),
                "mean": float(feature_data.mean()),
                "median": float(np.median(feature_data)),
            }

        logger.info(
            f"Computed distributions for dataset {dataset_id} "
            f"with {len(df_clean)} records and {bins} bins"
        )

        return {
            "datasetId": str(dataset_id),
            "distributions": distributions,
            "recordCount": len(df_clean),
        }

    @staticmethod
    def get_churn_by_contract(db: Session, dataset_id: UUID, user_id: UUID, is_admin: bool = False) -> Dict[str, Any]:
        dataset = EDAService._get_dataset_for_eda(db, dataset_id, user_id, is_admin)

        records = db.query(CustomerRecord).filter(CustomerRecord.dataset_id == dataset_id).all()

        if not records:
            raise ValueError("No customer records found for this dataset")

        data = []
        for record in records:
            data.append(
                {
                    "contract": record.contract,
                    "churn": record.churn,
                }
            )

        df = pd.DataFrame(data)

        df_clean = df.dropna()

        if df_clean.empty:
            raise ValueError("No valid data available for churn analysis by contract")

        churn_rates = []
        for contract_type in df_clean["contract"].unique():
            contract_df = df_clean[df_clean["contract"] == contract_type]
            total_customers = len(contract_df)
            churned_customers = int(contract_df["churn"].sum())
            churn_rate = float(churned_customers / total_customers) if total_customers > 0 else 0.0

            churn_rates.append(
                {
                    "contractType": contract_type,
                    "churnRate": churn_rate,
                    "totalCustomers": total_customers,
                    "churnedCustomers": churned_customers,
                }
            )

        churn_rates.sort(key=lambda x: x["contractType"])

        logger.info(
            f"Computed churn rates by contract for dataset {dataset_id} "
            f"with {len(df_clean)} records and {len(churn_rates)} contract types"
        )

        return {
            "datasetId": str(dataset_id),
            "churnRates": churn_rates,
            "recordCount": len(df_clean),
        }

    @staticmethod
    def get_churn_by_internet_service(
        db: Session, dataset_id: UUID, user_id: UUID, is_admin: bool = False
    ) -> Dict[str, Any]:
        dataset = EDAService._get_dataset_for_eda(db, dataset_id, user_id, is_admin)

        records = db.query(CustomerRecord).filter(CustomerRecord.dataset_id == dataset_id).all()

        if not records:
            raise ValueError("No customer records found for this dataset")

        data = []
        for record in records:
            data.append(
                {
                    "internet_service": record.internet_service,
                    "churn": record.churn,
                }
            )

        df = pd.DataFrame(data)

        df_clean = df.dropna()

        if df_clean.empty:
            raise ValueError("No valid data available for churn analysis by internet service")

        churn_rates = []
        for service_type in df_clean["internet_service"].unique():
            service_df = df_clean[df_clean["internet_service"] == service_type]
            total_customers = len(service_df)
            churned_customers = int(service_df["churn"].sum())
            churn_rate = float(churned_customers / total_customers) if total_customers > 0 else 0.0

            churn_rates.append(
                {
                    "internetServiceType": service_type,
                    "churnRate": churn_rate,
                    "totalCustomers": total_customers,
                    "churnedCustomers": churned_customers,
                }
            )

        churn_rates.sort(key=lambda x: x["internetServiceType"])

        logger.info(
            f"Computed churn rates by internet service for dataset {dataset_id} "
            f"with {len(df_clean)} records and {len(churn_rates)} service types"
        )

        return {
            "datasetId": str(dataset_id),
            "churnRates": churn_rates,
            "recordCount": len(df_clean),
        }

    @staticmethod
    def get_scatter_plot(db: Session, dataset_id: UUID, user_id: UUID, is_admin: bool = False) -> Dict[str, Any]:
        dataset = EDAService._get_dataset_for_eda(db, dataset_id, user_id, is_admin)

        records = db.query(CustomerRecord).filter(CustomerRecord.dataset_id == dataset_id).all()

        if not records:
            raise ValueError("No customer records found for this dataset")

        data = []
        for record in records:
            data.append(
                {
                    "monthly_charges": record.monthly_charges,
                    "total_charges": record.total_charges,
                    "churn": record.churn,
                }
            )

        df = pd.DataFrame(data)

        df_clean = df.dropna()

        if df_clean.empty:
            raise ValueError("No valid data available for scatter plot analysis")

        scatter_data = []
        for _, row in df_clean.iterrows():
            scatter_data.append(
                {
                    "monthlyCharges": float(row["monthly_charges"]),
                    "totalCharges": float(row["total_charges"]),
                    "churn": bool(row["churn"]),
                }
            )

        logger.info(
            f"Generated scatter plot data for dataset {dataset_id} "
            f"with {len(scatter_data)} records"
        )

        return {
            "datasetId": str(dataset_id),
            "scatterData": scatter_data,
            "recordCount": len(scatter_data),
        }

    @staticmethod
    def get_pca_visualization(db: Session, dataset_id: UUID, user_id: UUID, is_admin: bool = False) -> Dict[str, Any]:
        from sklearn.decomposition import PCA
        from sklearn.preprocessing import StandardScaler

        dataset = EDAService._get_dataset_for_eda(db, dataset_id, user_id, is_admin)

        records = db.query(CustomerRecord).filter(CustomerRecord.dataset_id == dataset_id).all()

        if not records:
            raise ValueError("No customer records found for this dataset")

        data = []
        for record in records:
            data.append(
                {
                    "tenure": record.tenure,
                    "MonthlyCharges": record.monthly_charges,
                    "TotalCharges": record.total_charges,
                    "SeniorCitizen": record.senior_citizen,
                    "churn": record.churn,
                }
            )

        df = pd.DataFrame(data)

        df_clean = df.dropna()

        if df_clean.empty:
            raise ValueError("No valid numeric data available for PCA analysis")

        X = df_clean[["tenure", "MonthlyCharges", "TotalCharges", "SeniorCitizen"]].values
        y = df_clean["churn"].values

        n_samples = X.shape[0]
        n_features = X.shape[1]

        if n_samples < 2:
            raise ValueError("At least 2 samples are required for PCA analysis")

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        pca_2d = PCA(n_components=min(2, n_samples, n_features))
        X_pca_2d = pca_2d.fit_transform(X_scaled)

        n_components_3d = min(3, n_samples, n_features)
        pca_3d = PCA(n_components=n_components_3d)
        X_pca_3d = pca_3d.fit_transform(X_scaled)

        pca2d_data = []
        for i in range(len(X_pca_2d)):
            pca2d_data.append(
                {
                    "pc1": float(X_pca_2d[i, 0]),
                    "pc2": float(X_pca_2d[i, 1]) if X_pca_2d.shape[1] > 1 else 0.0,
                    "churn": bool(y[i]),
                }
            )

        pca3d_data = []
        for i in range(len(X_pca_3d)):
            pca3d_data.append(
                {
                    "pc1": float(X_pca_3d[i, 0]),
                    "pc2": float(X_pca_3d[i, 1]) if X_pca_3d.shape[1] > 1 else 0.0,
                    "pc3": float(X_pca_3d[i, 2]) if X_pca_3d.shape[1] > 2 else 0.0,
                    "churn": bool(y[i]),
                }
            )

        logger.info(
            f"Computed PCA visualization for dataset {dataset_id} " f"with {len(df_clean)} records"
        )

        explained_variance_2d = pca_2d.explained_variance_ratio_.tolist()
        while len(explained_variance_2d) < 2:
            explained_variance_2d.append(0.0)

        explained_variance_3d = pca_3d.explained_variance_ratio_.tolist()
        while len(explained_variance_3d) < 3:
            explained_variance_3d.append(0.0)

        return {
            "datasetId": str(dataset_id),
            "pca2d": pca2d_data,
            "pca3d": pca3d_data,
            "explainedVariance2d": explained_variance_2d,
            "explainedVariance3d": explained_variance_3d,
            "recordCount": len(df_clean),
        }
