-- Initialize PostgreSQL databases for the Customer Churn Prediction Platform
-- This script runs automatically when the PostgreSQL container starts for the first time

-- Enable required extensions for the main database
\c churn_prediction;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Log completion
\c churn_prediction;
SELECT 'Database initialization completed successfully' AS status;
