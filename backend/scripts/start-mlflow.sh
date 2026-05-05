#!/bin/bash

# MLflow Tracking Server Startup Script
# Starts MLflow with PostgreSQL backend and S3-compatible artifact store

set -e

echo "🚀 Starting MLflow Tracking Server"
echo "==================================="
echo ""

# Load environment variables
if [ -f .env.mlflow ]; then
    echo "Loading environment from .env.mlflow..."
    export $(cat .env.mlflow | grep -v '^#' | xargs)
else
    echo "⚠️  Warning: .env.mlflow not found. Using default values."
    echo "   Copy .env.mlflow.example to .env.mlflow and configure it."
    echo ""
fi

# Set defaults if not provided
MLFLOW_HOST=${MLFLOW_HOST:-0.0.0.0}
MLFLOW_PORT=${MLFLOW_PORT:-5000}
MLFLOW_BACKEND_STORE_URI=${MLFLOW_BACKEND_STORE_URI:-sqlite:///mlflow.db}
MLFLOW_ARTIFACT_ROOT=${MLFLOW_ARTIFACT_ROOT:-./mlruns}

echo "Configuration:"
echo "  Host: $MLFLOW_HOST"
echo "  Port: $MLFLOW_PORT"
echo "  Backend Store: $MLFLOW_BACKEND_STORE_URI"
echo "  Artifact Root: $MLFLOW_ARTIFACT_ROOT"
echo ""

# Check if PostgreSQL is accessible (if using PostgreSQL)
if [[ $MLFLOW_BACKEND_STORE_URI == postgresql* ]]; then
    echo "Checking PostgreSQL connection..."
    
    # Extract connection details
    POSTGRES_HOST=$(echo $MLFLOW_BACKEND_STORE_URI | sed -n 's/.*@\([^:]*\):.*/\1/p')
    POSTGRES_PORT=$(echo $MLFLOW_BACKEND_STORE_URI | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
    
    if command -v pg_isready &> /dev/null; then
        if pg_isready -h $POSTGRES_HOST -p $POSTGRES_PORT &> /dev/null; then
            echo "✅ PostgreSQL is ready"
        else
            echo "❌ PostgreSQL is not accessible at $POSTGRES_HOST:$POSTGRES_PORT"
            echo "   Make sure PostgreSQL is running and accessible."
            exit 1
        fi
    else
        echo "⚠️  pg_isready not found. Skipping PostgreSQL check."
    fi
    echo ""
fi

# Check if S3 endpoint is accessible (if using S3)
if [[ ! -z "$MLFLOW_S3_ENDPOINT_URL" ]]; then
    echo "Checking S3 endpoint..."
    
    if command -v curl &> /dev/null; then
        if curl -f -s -o /dev/null "$MLFLOW_S3_ENDPOINT_URL/minio/health/live" 2>/dev/null || \
           curl -f -s -o /dev/null "$MLFLOW_S3_ENDPOINT_URL" 2>/dev/null; then
            echo "✅ S3 endpoint is accessible"
        else
            echo "⚠️  S3 endpoint may not be accessible at $MLFLOW_S3_ENDPOINT_URL"
            echo "   MLflow will still start, but artifact logging may fail."
        fi
    fi
    echo ""
fi

# Start MLflow server
echo "Starting MLflow server..."
echo ""

mlflow server \
    --backend-store-uri "$MLFLOW_BACKEND_STORE_URI" \
    --default-artifact-root "$MLFLOW_ARTIFACT_ROOT" \
    --host "$MLFLOW_HOST" \
    --port "$MLFLOW_PORT" \
    --serve-artifacts

# Note: This script will run in foreground
# To run in background, use: nohup ./start-mlflow.sh > mlflow.log 2>&1 &
