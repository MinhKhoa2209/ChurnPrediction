"""
Cloudflare R2 Storage Client
Used for storing model artifacts, preprocessing configs, and reports.
"""

import logging
from typing import BinaryIO, Optional
from uuid import UUID

import boto3
from botocore.exceptions import ClientError

from backend.config import settings

logger = logging.getLogger(__name__)


class R2StorageClient:
    """S3-compatible client for Cloudflare R2 storage"""
    
    def __init__(self):
        """Initialize R2 storage client with configuration from settings"""
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key_id,
            aws_secret_access_key=settings.s3_secret_access_key,
            region_name=settings.s3_region,
        )
        self.models_bucket = settings.s3_bucket_models
        self.reports_bucket = settings.s3_bucket_reports
        self.exports_bucket = settings.s3_bucket_exports
        
        logger.info(
            f"R2 Storage client initialized: endpoint={settings.s3_endpoint_url}, "
            f"buckets=[{self.models_bucket}, {self.reports_bucket}, {self.exports_bucket}]"
        )
    
    def upload_model_artifact(
        self,
        user_id: UUID,
        model_version_id: UUID,
        file_data: bytes,
        filename: str = "model.joblib"
    ) -> str:
        """
        Upload model artifact to R2 storage
        Requirement 15.3: Store serialized ML_Model artifact in R2_Storage
        
        Args:
            user_id: User UUID
            model_version_id: Model version UUID
            file_data: Binary model data
            filename: Filename for the artifact (default: model.joblib)
            
        Returns:
            S3 path to the uploaded artifact
        """
        # Construct S3 key: models/{user_id}/{model_version_id}/model.joblib
        s3_key = f"models/{user_id}/{model_version_id}/{filename}"
        
        try:
            self.client.put_object(
                Bucket=self.models_bucket,
                Key=s3_key,
                Body=file_data,
                ContentType="application/octet-stream",
            )
            
            logger.info(f"Uploaded model artifact to R2: {s3_key}")
            return s3_key
            
        except ClientError as e:
            logger.error(f"Failed to upload model artifact to R2: {e}")
            raise RuntimeError(f"Failed to upload model artifact: {e}")
    
    def upload_preprocessing_config(
        self,
        user_id: UUID,
        model_version_id: UUID,
        file_data: bytes,
        filename: str = "preprocessing.joblib"
    ) -> str:
        """
        Upload preprocessing configuration to R2 storage
        
        Args:
            user_id: User UUID
            model_version_id: Model version UUID
            file_data: Binary preprocessing config data
            filename: Filename for the config (default: preprocessing.joblib)
            
        Returns:
            S3 path to the uploaded config
        """
        # Construct S3 key: models/{user_id}/{model_version_id}/preprocessing.joblib
        s3_key = f"models/{user_id}/{model_version_id}/{filename}"
        
        try:
            self.client.put_object(
                Bucket=self.models_bucket,
                Key=s3_key,
                Body=file_data,
                ContentType="application/octet-stream",
            )
            
            logger.info(f"Uploaded preprocessing config to R2: {s3_key}")
            return s3_key
            
        except ClientError as e:
            logger.error(f"Failed to upload preprocessing config to R2: {e}")
            raise RuntimeError(f"Failed to upload preprocessing config: {e}")
    
    def download_model_artifact(self, s3_key: str) -> bytes:
        """
        Download model artifact from R2 storage
        
        Args:
            s3_key: S3 key path to the artifact
            
        Returns:
            Binary model data
        """
        try:
            response = self.client.get_object(
                Bucket=self.models_bucket,
                Key=s3_key
            )
            
            data = response["Body"].read()
            logger.info(f"Downloaded model artifact from R2: {s3_key}")
            return data
            
        except ClientError as e:
            logger.error(f"Failed to download model artifact from R2: {e}")
            raise RuntimeError(f"Failed to download model artifact: {e}")
    
    def download_preprocessing_config(self, s3_key: str) -> bytes:
        """
        Download preprocessing config from R2 storage
        
        Args:
            s3_key: S3 key path to the config
            
        Returns:
            Binary preprocessing config data
        """
        try:
            response = self.client.get_object(
                Bucket=self.models_bucket,
                Key=s3_key
            )
            
            data = response["Body"].read()
            logger.info(f"Downloaded preprocessing config from R2: {s3_key}")
            return data
            
        except ClientError as e:
            logger.error(f"Failed to download preprocessing config from R2: {e}")
            raise RuntimeError(f"Failed to download preprocessing config: {e}")
    
    def upload_report(
        self,
        user_id: UUID,
        report_id: UUID,
        file_data: bytes,
        filename: str
    ) -> str:
        """
        Upload report file to R2 storage
        
        Args:
            user_id: User UUID
            report_id: Report UUID
            file_data: Binary report data
            filename: Filename for the report
            
        Returns:
            S3 path to the uploaded report
        """
        # Construct S3 key: reports/{user_id}/{report_id}/{filename}
        s3_key = f"reports/{user_id}/{report_id}/{filename}"
        
        try:
            self.client.put_object(
                Bucket=self.reports_bucket,
                Key=s3_key,
                Body=file_data,
                ContentType="application/pdf",
            )
            
            logger.info(f"Uploaded report to R2: {s3_key}")
            return s3_key
            
        except ClientError as e:
            logger.error(f"Failed to upload report to R2: {e}")
            raise RuntimeError(f"Failed to upload report: {e}")
    
    def upload_batch_export(
        self,
        user_id: UUID,
        batch_id: UUID,
        csv_data: bytes,
        filename: str = "predictions.csv"
    ) -> str:
        """
        Upload batch prediction export CSV to R2 storage
        Requirement 33.4: Store batch prediction result CSVs in R2_Storage
        
        Args:
            user_id: User UUID
            batch_id: Batch UUID
            csv_data: CSV file data as bytes
            filename: Filename for the export (default: predictions.csv)
            
        Returns:
            S3 path to the uploaded export
        """
        # Construct S3 key: exports/{user_id}/{batch_id}/predictions.csv
        s3_key = f"exports/{user_id}/{batch_id}/{filename}"
        
        try:
            self.client.put_object(
                Bucket=self.exports_bucket,
                Key=s3_key,
                Body=csv_data,
                ContentType="text/csv",
            )
            
            logger.info(f"Uploaded batch export to R2: {s3_key}")
            return s3_key
            
        except ClientError as e:
            logger.error(f"Failed to upload batch export to R2: {e}")
            raise RuntimeError(f"Failed to upload batch export: {e}")
    
    def delete_artifact(self, s3_key: str, bucket: Optional[str] = None) -> None:
        """
        Delete artifact from R2 storage
        
        Args:
            s3_key: S3 key path to the artifact
            bucket: Bucket name (defaults to models bucket)
        """
        bucket = bucket or self.models_bucket
        
        try:
            self.client.delete_object(
                Bucket=bucket,
                Key=s3_key
            )
            
            logger.info(f"Deleted artifact from R2: {s3_key}")
            
        except ClientError as e:
            logger.error(f"Failed to delete artifact from R2: {e}")
            raise RuntimeError(f"Failed to delete artifact: {e}")


# Global storage client instance
storage_client = R2StorageClient()
