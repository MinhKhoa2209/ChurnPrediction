"""Initial migration with all 11 tables

Revision ID: 001
Revises: 
Create Date: 2025-01-01 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable PostgreSQL extensions (Requirement 25.2)
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
    
    # Create users table (Requirement 25.3)
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', postgresql.ENUM('Admin', 'Data_Scientist', 'Analyst', name='user_role'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('email_verified', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('email_notifications_enabled', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('reset_token', sa.String(length=255), nullable=True),
        sa.Column('reset_token_expires', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_role', 'users', ['role'])
    
    # Create datasets table (Requirement 25.3)
    op.create_table(
        'datasets',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('record_count', sa.Integer(), nullable=False),
        sa.Column('status', postgresql.ENUM('uploading', 'processing', 'ready', 'failed', name='dataset_status'), nullable=False),
        sa.Column('validation_errors', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('data_quality_score', sa.Float(), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('data_quality_score >= 0 AND data_quality_score <= 100', name='check_data_quality_score')
    )
    op.create_index('idx_datasets_user_id', 'datasets', ['user_id'])
    op.create_index('idx_datasets_status', 'datasets', ['status'])
    op.create_index('idx_datasets_uploaded_at', 'datasets', ['uploaded_at'], postgresql_ops={'uploaded_at': 'DESC'})
    
    # Create customer_records table (Requirement 25.3)
    op.create_table(
        'customer_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('dataset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id_encrypted', sa.LargeBinary(), nullable=False),
        sa.Column('gender', sa.String(length=10), nullable=True),
        sa.Column('senior_citizen', sa.Integer(), nullable=True),
        sa.Column('partner', sa.String(length=10), nullable=True),
        sa.Column('dependents', sa.String(length=10), nullable=True),
        sa.Column('tenure', sa.Integer(), nullable=True),
        sa.Column('phone_service', sa.String(length=10), nullable=True),
        sa.Column('multiple_lines', sa.String(length=50), nullable=True),
        sa.Column('internet_service', sa.String(length=50), nullable=True),
        sa.Column('online_security', sa.String(length=50), nullable=True),
        sa.Column('online_backup', sa.String(length=50), nullable=True),
        sa.Column('device_protection', sa.String(length=50), nullable=True),
        sa.Column('tech_support', sa.String(length=50), nullable=True),
        sa.Column('streaming_tv', sa.String(length=50), nullable=True),
        sa.Column('streaming_movies', sa.String(length=50), nullable=True),
        sa.Column('contract', sa.String(length=50), nullable=True),
        sa.Column('paperless_billing', sa.String(length=10), nullable=True),
        sa.Column('payment_method_encrypted', sa.LargeBinary(), nullable=True),
        sa.Column('monthly_charges', sa.Float(), nullable=True),
        sa.Column('total_charges', sa.Float(), nullable=True),
        sa.Column('churn', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_customer_records_dataset_id', 'customer_records', ['dataset_id'])
    op.create_index('idx_customer_records_churn', 'customer_records', ['churn'])
    
    # Create preprocessing_configs table (Requirement 25.3)
    op.create_table(
        'preprocessing_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('dataset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('encoding_mappings', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('scaler_params', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('smote_config', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('feature_columns', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_preprocessing_configs_dataset_id', 'preprocessing_configs', ['dataset_id'])
    
    # Create model_versions table (Requirement 25.3)
    op.create_table(
        'model_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('dataset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('preprocessing_config_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('model_type', postgresql.ENUM('KNN', 'NaiveBayes', 'DecisionTree', 'SVM', name='model_type'), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('hyperparameters', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('confusion_matrix', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('training_time_seconds', sa.Float(), nullable=False),
        sa.Column('artifact_path', sa.String(length=500), nullable=False),
        sa.Column('mlflow_run_id', sa.String(length=255), nullable=True),
        sa.Column('status', postgresql.ENUM('active', 'archived', name='model_status'), server_default=sa.text("'active'"), nullable=False),
        sa.Column('classification_threshold', sa.Float(), server_default=sa.text('0.5'), nullable=False),
        sa.Column('trained_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['preprocessing_config_id'], ['preprocessing_configs.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('version'),
        sa.CheckConstraint('classification_threshold >= 0 AND classification_threshold <= 1', name='check_classification_threshold')
    )
    op.create_index('idx_model_versions_user_id', 'model_versions', ['user_id'])
    op.create_index('idx_model_versions_dataset_id', 'model_versions', ['dataset_id'])
    op.create_index('idx_model_versions_model_type', 'model_versions', ['model_type'])
    op.create_index('idx_model_versions_status', 'model_versions', ['status'])
    op.create_index('idx_model_versions_trained_at', 'model_versions', ['trained_at'], postgresql_ops={'trained_at': 'DESC'})
    
    # Create training_jobs table (Requirement 25.3)
    op.create_table(
        'training_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('dataset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('model_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('model_type', sa.String(length=50), nullable=False),
        sa.Column('status', postgresql.ENUM('queued', 'running', 'completed', 'failed', name='training_job_status'), nullable=False),
        sa.Column('progress_percent', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('current_iteration', sa.Integer(), nullable=True),
        sa.Column('total_iterations', sa.Integer(), nullable=True),
        sa.Column('estimated_seconds_remaining', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['model_version_id'], ['model_versions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('progress_percent >= 0 AND progress_percent <= 100', name='check_progress_percent')
    )
    op.create_index('idx_training_jobs_user_id', 'training_jobs', ['user_id'])
    op.create_index('idx_training_jobs_status', 'training_jobs', ['status'])
    op.create_index('idx_training_jobs_created_at', 'training_jobs', ['created_at'], postgresql_ops={'created_at': 'DESC'})
    
    # Create training_progress table (Requirement 25.3)
    op.create_table(
        'training_progress',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('training_job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('iteration', sa.Integer(), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('metric_name', sa.String(length=50), nullable=False),
        sa.Column('recorded_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['training_job_id'], ['training_jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_training_progress_job_id', 'training_progress', ['training_job_id'])
    op.create_index('idx_training_progress_recorded_at', 'training_progress', ['recorded_at'])
    
    # Create predictions table (Requirement 25.3)
    op.create_table(
        'predictions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('model_version_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('input_features', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('probability', sa.Float(), nullable=False),
        sa.Column('threshold', sa.Float(), nullable=False),
        sa.Column('prediction', sa.Boolean(), nullable=False),
        sa.Column('shap_values', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('is_batch', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('batch_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['model_version_id'], ['model_versions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('probability >= 0 AND probability <= 1', name='check_probability'),
        sa.CheckConstraint('threshold >= 0 AND threshold <= 1', name='check_threshold')
    )
    op.create_index('idx_predictions_user_id', 'predictions', ['user_id'])
    op.create_index('idx_predictions_model_version_id', 'predictions', ['model_version_id'])
    op.create_index('idx_predictions_batch_id', 'predictions', ['batch_id'], postgresql_where=sa.text('batch_id IS NOT NULL'))
    op.create_index('idx_predictions_created_at', 'predictions', ['created_at'], postgresql_ops={'created_at': 'DESC'})
    
    # Create reports table (Requirement 25.3)
    op.create_table(
        'reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('model_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('report_type', sa.String(length=50), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('report_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['model_version_id'], ['model_versions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_reports_user_id', 'reports', ['user_id'])
    op.create_index('idx_reports_generated_at', 'reports', ['generated_at'], postgresql_ops={'generated_at': 'DESC'})
    
    # Create notifications table (Requirement 25.3)
    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('training_job_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('notification_type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['training_job_id'], ['training_jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_notifications_user_id', 'notifications', ['user_id'])
    op.create_index('idx_notifications_is_read', 'notifications', ['is_read'])
    op.create_index('idx_notifications_created_at', 'notifications', ['created_at'], postgresql_ops={'created_at': 'DESC'})
    
    # Create audit_logs table (Requirement 25.3)
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=False),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('ip_address', postgresql.INET(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('idx_audit_logs_created_at', 'audit_logs', ['created_at'], postgresql_ops={'created_at': 'DESC'})
    op.create_index('idx_audit_logs_resource', 'audit_logs', ['resource_type', 'resource_id'])


def downgrade() -> None:
    # Drop tables in reverse order (Requirement 25.3)
    op.drop_index('idx_audit_logs_resource', table_name='audit_logs')
    op.drop_index('idx_audit_logs_created_at', table_name='audit_logs')
    op.drop_index('idx_audit_logs_user_id', table_name='audit_logs')
    op.drop_table('audit_logs')
    
    op.drop_index('idx_notifications_created_at', table_name='notifications')
    op.drop_index('idx_notifications_is_read', table_name='notifications')
    op.drop_index('idx_notifications_user_id', table_name='notifications')
    op.drop_table('notifications')
    
    op.drop_index('idx_reports_generated_at', table_name='reports')
    op.drop_index('idx_reports_user_id', table_name='reports')
    op.drop_table('reports')
    
    op.drop_index('idx_predictions_created_at', table_name='predictions')
    op.drop_index('idx_predictions_batch_id', table_name='predictions')
    op.drop_index('idx_predictions_model_version_id', table_name='predictions')
    op.drop_index('idx_predictions_user_id', table_name='predictions')
    op.drop_table('predictions')
    
    op.drop_index('idx_training_progress_recorded_at', table_name='training_progress')
    op.drop_index('idx_training_progress_job_id', table_name='training_progress')
    op.drop_table('training_progress')
    
    op.drop_index('idx_training_jobs_created_at', table_name='training_jobs')
    op.drop_index('idx_training_jobs_status', table_name='training_jobs')
    op.drop_index('idx_training_jobs_user_id', table_name='training_jobs')
    op.drop_table('training_jobs')
    
    op.drop_index('idx_model_versions_trained_at', table_name='model_versions')
    op.drop_index('idx_model_versions_status', table_name='model_versions')
    op.drop_index('idx_model_versions_model_type', table_name='model_versions')
    op.drop_index('idx_model_versions_dataset_id', table_name='model_versions')
    op.drop_index('idx_model_versions_user_id', table_name='model_versions')
    op.drop_table('model_versions')
    
    op.drop_index('idx_preprocessing_configs_dataset_id', table_name='preprocessing_configs')
    op.drop_table('preprocessing_configs')
    
    op.drop_index('idx_customer_records_churn', table_name='customer_records')
    op.drop_index('idx_customer_records_dataset_id', table_name='customer_records')
    op.drop_table('customer_records')
    
    op.drop_index('idx_datasets_uploaded_at', table_name='datasets')
    op.drop_index('idx_datasets_status', table_name='datasets')
    op.drop_index('idx_datasets_user_id', table_name='datasets')
    op.drop_table('datasets')
    
    op.drop_index('idx_users_role', table_name='users')
    op.drop_index('idx_users_email', table_name='users')
    op.drop_table('users')
    
    # Drop ENUM types
    op.execute('DROP TYPE IF EXISTS training_job_status')
    op.execute('DROP TYPE IF EXISTS model_status')
    op.execute('DROP TYPE IF EXISTS model_type')
    op.execute('DROP TYPE IF EXISTS dataset_status')
    op.execute('DROP TYPE IF EXISTS user_role')
    
    # Drop extensions
    op.execute('DROP EXTENSION IF EXISTS "pgcrypto"')
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
