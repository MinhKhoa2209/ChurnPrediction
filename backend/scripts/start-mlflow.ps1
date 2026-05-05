# MLflow Tracking Server Startup Script (PowerShell)
# Starts MLflow with PostgreSQL backend and S3-compatible artifact store

$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting MLflow Tracking Server" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""

# Load environment variables from .env.mlflow
if (Test-Path ".env.mlflow") {
    Write-Host "Loading environment from .env.mlflow..." -ForegroundColor Yellow
    Get-Content ".env.mlflow" | ForEach-Object {
        if ($_ -match '^([^#][^=]+)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
} else {
    Write-Host "⚠️  Warning: .env.mlflow not found. Using default values." -ForegroundColor Yellow
    Write-Host "   Copy .env.mlflow.example to .env.mlflow and configure it." -ForegroundColor Gray
    Write-Host ""
}

# Set defaults if not provided
$MLFLOW_HOST = if ($env:MLFLOW_HOST) { $env:MLFLOW_HOST } else { "0.0.0.0" }
$MLFLOW_PORT = if ($env:MLFLOW_PORT) { $env:MLFLOW_PORT } else { "5000" }
$MLFLOW_BACKEND_STORE_URI = if ($env:MLFLOW_BACKEND_STORE_URI) { $env:MLFLOW_BACKEND_STORE_URI } else { "sqlite:///mlflow.db" }
$MLFLOW_ARTIFACT_ROOT = if ($env:MLFLOW_ARTIFACT_ROOT) { $env:MLFLOW_ARTIFACT_ROOT } else { "./mlruns" }

Write-Host "Configuration:" -ForegroundColor Cyan
Write-Host "  Host: $MLFLOW_HOST"
Write-Host "  Port: $MLFLOW_PORT"
Write-Host "  Backend Store: $MLFLOW_BACKEND_STORE_URI"
Write-Host "  Artifact Root: $MLFLOW_ARTIFACT_ROOT"
Write-Host ""

# Check if PostgreSQL is accessible (if using PostgreSQL)
if ($MLFLOW_BACKEND_STORE_URI -like "postgresql*") {
    Write-Host "Checking PostgreSQL connection..." -ForegroundColor Yellow
    
    # Extract connection details
    if ($MLFLOW_BACKEND_STORE_URI -match '@([^:]+):(\d+)') {
        $POSTGRES_HOST = $matches[1]
        $POSTGRES_PORT = $matches[2]
        
        try {
            $connection = Test-NetConnection -ComputerName $POSTGRES_HOST -Port $POSTGRES_PORT -WarningAction SilentlyContinue
            if ($connection.TcpTestSucceeded) {
                Write-Host "✅ PostgreSQL is accessible" -ForegroundColor Green
            } else {
                Write-Host "❌ PostgreSQL is not accessible at ${POSTGRES_HOST}:${POSTGRES_PORT}" -ForegroundColor Red
                Write-Host "   Make sure PostgreSQL is running and accessible." -ForegroundColor Yellow
                exit 1
            }
        } catch {
            Write-Host "⚠️  Could not test PostgreSQL connection" -ForegroundColor Yellow
        }
    }
    Write-Host ""
}

# Check if S3 endpoint is accessible (if using S3)
if ($env:MLFLOW_S3_ENDPOINT_URL) {
    Write-Host "Checking S3 endpoint..." -ForegroundColor Yellow
    
    try {
        $response = Invoke-WebRequest -Uri "$($env:MLFLOW_S3_ENDPOINT_URL)/minio/health/live" -Method Get -TimeoutSec 5 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ S3 endpoint is accessible" -ForegroundColor Green
        }
    } catch {
        Write-Host "⚠️  S3 endpoint may not be accessible at $($env:MLFLOW_S3_ENDPOINT_URL)" -ForegroundColor Yellow
        Write-Host "   MLflow will still start, but artifact logging may fail." -ForegroundColor Gray
    }
    Write-Host ""
}

# Check if mlflow is installed
$mlflowInstalled = Get-Command mlflow -ErrorAction SilentlyContinue
if (-not $mlflowInstalled) {
    Write-Host "❌ MLflow is not installed" -ForegroundColor Red
    Write-Host "   Install with: pip install mlflow==2.10.2" -ForegroundColor Yellow
    exit 1
}

# Start MLflow server
Write-Host "Starting MLflow server..." -ForegroundColor Green
Write-Host ""

mlflow server `
    --backend-store-uri "$MLFLOW_BACKEND_STORE_URI" `
    --default-artifact-root "$MLFLOW_ARTIFACT_ROOT" `
    --host "$MLFLOW_HOST" `
    --port "$MLFLOW_PORT" `
    --serve-artifacts

# Note: This script will run in foreground
# To run in background, use: Start-Process powershell -ArgumentList "-File .\start-mlflow.ps1" -WindowStyle Hidden
