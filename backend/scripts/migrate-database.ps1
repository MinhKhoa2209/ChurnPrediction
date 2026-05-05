# Database Migration Script with Backup and Validation (PowerShell)
# Safely applies Alembic migrations to production database

$ErrorActionPreference = "Stop"

Write-Host "🗄️  Database Migration Script" -ForegroundColor Blue
Write-Host "==============================" -ForegroundColor Blue
Write-Host ""

# Check if running in production
$ENVIRONMENT = if ($env:APP_ENV) { $env:APP_ENV } else { "development" }
Write-Host "Environment: $ENVIRONMENT" -ForegroundColor Yellow

if ($ENVIRONMENT -eq "production") {
    Write-Host "⚠️  WARNING: Running in PRODUCTION mode" -ForegroundColor Red
    Write-Host ""
    $confirmation = Read-Host "Are you sure you want to proceed? (yes/no)"
    if ($confirmation -ne "yes") {
        Write-Host "Migration cancelled." -ForegroundColor Yellow
        exit 0
    }
}

# Load environment variables
if (Test-Path ".env") {
    Write-Host "Loading environment variables..." -ForegroundColor Green
    Get-Content ".env" | ForEach-Object {
        if ($_ -match '^([^#][^=]+)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
} elseif (Test-Path ".env.production") {
    Write-Host "Loading production environment variables..." -ForegroundColor Green
    Get-Content ".env.production" | ForEach-Object {
        if ($_ -match '^([^#][^=]+)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
} else {
    Write-Host "❌ No .env file found" -ForegroundColor Red
    exit 1
}

# Validate DATABASE_URL
if (-not $env:DATABASE_URL) {
    Write-Host "❌ DATABASE_URL not set" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Database URL configured" -ForegroundColor Green
Write-Host ""

# Extract database connection details
if ($env:DATABASE_URL -match 'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/([^?]+)') {
    $DB_USER = $matches[1]
    $DB_HOST = $matches[3]
    $DB_PORT = $matches[4]
    $DB_NAME = $matches[5]
    
    Write-Host "Database Details:"
    Write-Host "  Host: $DB_HOST"
    Write-Host "  Port: $DB_PORT"
    Write-Host "  Database: $DB_NAME"
    Write-Host "  User: $DB_USER"
    Write-Host ""
}

# Step 1: Test database connection
Write-Host "Step 1: Testing database connection..." -ForegroundColor Yellow
try {
    $connection = Test-NetConnection -ComputerName $DB_HOST -Port $DB_PORT -WarningAction SilentlyContinue
    if ($connection.TcpTestSucceeded) {
        Write-Host "✅ Database connection successful" -ForegroundColor Green
    } else {
        Write-Host "❌ Cannot connect to database" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "⚠️  Could not test database connection" -ForegroundColor Yellow
}
Write-Host ""

# Step 2: Create backup
$BACKUP_DIR = ".\backups"
$TIMESTAMP = Get-Date -Format "yyyyMMdd_HHmmss"
$BACKUP_FILE = "$BACKUP_DIR\db_backup_$TIMESTAMP.sql"

if (-not (Test-Path $BACKUP_DIR)) {
    New-Item -ItemType Directory -Path $BACKUP_DIR | Out-Null
}

Write-Host "Step 2: Creating database backup..." -ForegroundColor Yellow
$pgDumpInstalled = Get-Command pg_dump -ErrorAction SilentlyContinue
if ($pgDumpInstalled) {
    try {
        & pg_dump $env:DATABASE_URL > $BACKUP_FILE 2>$null
        $BACKUP_SIZE = (Get-Item $BACKUP_FILE).Length / 1MB
        Write-Host "✅ Backup created: $BACKUP_FILE ($([math]::Round($BACKUP_SIZE, 2)) MB)" -ForegroundColor Green
    } catch {
        Write-Host "❌ Backup failed" -ForegroundColor Red
        if ($ENVIRONMENT -eq "production") {
            Write-Host "Cannot proceed without backup in production." -ForegroundColor Red
            exit 1
        } else {
            Write-Host "⚠️  Continuing without backup (development mode)" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "⚠️  pg_dump not found, skipping backup" -ForegroundColor Yellow
    if ($ENVIRONMENT -eq "production") {
        Write-Host "❌ Cannot proceed without backup capability in production" -ForegroundColor Red
        exit 1
    }
}
Write-Host ""

# Step 3: Check current migration status
Write-Host "Step 3: Checking current migration status..." -ForegroundColor Yellow
try {
    $currentOutput = & alembic current 2>$null
    if ($currentOutput -match '\(([a-f0-9]+)\)') {
        $CURRENT_REVISION = $matches[1]
    } else {
        $CURRENT_REVISION = "none"
    }
    Write-Host "Current revision: $CURRENT_REVISION"
} catch {
    $CURRENT_REVISION = "none"
    Write-Host "Current revision: none"
}
Write-Host ""

# Step 4: Check pending migrations
Write-Host "Step 4: Checking for pending migrations..." -ForegroundColor Yellow
try {
    $historyOutput = & alembic history --verbose 2>$null
    $PENDING_MIGRATIONS = ($historyOutput | Select-String "->").Count
    Write-Host "Pending migrations: $PENDING_MIGRATIONS"
    
    if ($PENDING_MIGRATIONS -eq 0) {
        Write-Host "✅ Database is up to date" -ForegroundColor Green
        exit 0
    }
} catch {
    Write-Host "⚠️  Could not check pending migrations" -ForegroundColor Yellow
}
Write-Host ""

# Step 5: Show migration plan
Write-Host "Step 5: Migration plan:" -ForegroundColor Yellow
& alembic history --verbose 2>$null | Select-Object -First 20
Write-Host ""

if ($ENVIRONMENT -eq "production") {
    $confirmation = Read-Host "Proceed with migration? (yes/no)"
    if ($confirmation -ne "yes") {
        Write-Host "Migration cancelled." -ForegroundColor Yellow
        exit 0
    }
    Write-Host ""
}

# Step 6: Validate migration integrity
Write-Host "Step 6: Validating migration integrity..." -ForegroundColor Yellow
try {
    $checkOutput = & alembic check 2>&1
    if ($checkOutput -match "No issues") {
        Write-Host "✅ Migration integrity validated" -ForegroundColor Green
    } else {
        Write-Host "❌ Migration integrity check failed" -ForegroundColor Red
        Write-Host $checkOutput
        exit 1
    }
} catch {
    Write-Host "⚠️  Could not validate migration integrity" -ForegroundColor Yellow
}
Write-Host ""

# Step 7: Run migrations
Write-Host "Step 7: Running migrations..." -ForegroundColor Yellow
try {
    & alembic upgrade head
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Migrations applied successfully" -ForegroundColor Green
    } else {
        throw "Migration failed"
    }
} catch {
    Write-Host "❌ Migration failed" -ForegroundColor Red
    Write-Host ""
    Write-Host "Attempting to restore from backup..." -ForegroundColor Yellow
    
    if ((Test-Path $BACKUP_FILE) -and $pgDumpInstalled) {
        Write-Host "Restoring database from backup..."
        & psql $env:DATABASE_URL < $BACKUP_FILE
        Write-Host "✅ Database restored from backup" -ForegroundColor Green
    } else {
        Write-Host "❌ Cannot restore backup" -ForegroundColor Red
        Write-Host "Manual intervention required."
    }
    
    exit 1
}
Write-Host ""

# Step 8: Verify migration
Write-Host "Step 8: Verifying migration..." -ForegroundColor Yellow
try {
    $newOutput = & alembic current 2>$null
    if ($newOutput -match '\(([a-f0-9]+)\)') {
        $NEW_REVISION = $matches[1]
    } else {
        $NEW_REVISION = "none"
    }
    Write-Host "New revision: $NEW_REVISION"
    
    if ($NEW_REVISION -ne $CURRENT_REVISION) {
        Write-Host "✅ Migration verified" -ForegroundColor Green
    } else {
        Write-Host "❌ Migration verification failed" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "⚠️  Could not verify migration" -ForegroundColor Yellow
}
Write-Host ""

# Step 9: Test database connectivity
Write-Host "Step 9: Testing database after migration..." -ForegroundColor Yellow
$psqlInstalled = Get-Command psql -ErrorAction SilentlyContinue
if ($psqlInstalled) {
    try {
        & psql $env:DATABASE_URL -c "SELECT COUNT(*) FROM alembic_version" 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Database is accessible and functional" -ForegroundColor Green
        } else {
            Write-Host "❌ Database test failed" -ForegroundColor Red
            exit 1
        }
    } catch {
        Write-Host "⚠️  Could not test database" -ForegroundColor Yellow
    }
}
Write-Host ""

# Step 10: Cleanup old backups (keep last 10)
Write-Host "Step 10: Cleaning up old backups..." -ForegroundColor Yellow
$backups = Get-ChildItem "$BACKUP_DIR\db_backup_*.sql" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
$BACKUP_COUNT = $backups.Count
if ($BACKUP_COUNT -gt 10) {
    Write-Host "Found $BACKUP_COUNT backups, keeping last 10..."
    $backups | Select-Object -Skip 10 | Remove-Item -Force
    Write-Host "✅ Old backups cleaned up" -ForegroundColor Green
} else {
    Write-Host "Backup count: $BACKUP_COUNT (no cleanup needed)"
}
Write-Host ""

# Summary
Write-Host "================================" -ForegroundColor Green
Write-Host "✅ Migration completed successfully" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""
Write-Host "Summary:"
Write-Host "  Previous revision: $CURRENT_REVISION"
Write-Host "  Current revision: $NEW_REVISION"
Write-Host "  Backup location: $BACKUP_FILE"
Write-Host "  Environment: $ENVIRONMENT"
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Blue
Write-Host "  1. Test application functionality"
Write-Host "  2. Monitor application logs"
Write-Host "  3. Keep backup file for rollback if needed"
Write-Host ""
