-- Initialize PostgreSQL databases for the Customer Churn Prediction Platform
-- This script runs automatically when the PostgreSQL container starts for the first time

-- Create MLflow database for experiment tracking
CREATE DATABASE mlflow;

-- Grant privileges to the application user
GRANT ALL PRIVILEGES ON DATABASE mlflow TO churn_user;

-- Enable required extensions for the main database
\c churn_prediction;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Switch to MLflow database and enable extensions
\c mlflow;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Log completion
\c churn_prediction;
SELECT 'Database initialization completed successfully' AS status;
