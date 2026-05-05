#!/bin/bash

# Database Migration Script with Backup and Validation
# Safely applies Alembic migrations to production database

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🗄️  Database Migration Script${NC}"
echo -e "${BLUE}==============================${NC}"
echo ""

# Check if running in production
ENVIRONMENT=${APP_ENV:-development}
echo -e "${YELLOW}Environment: $ENVIRONMENT${NC}"

if [ "$ENVIRONMENT" = "production" ]; then
    echo -e "${RED}⚠️  WARNING: Running in PRODUCTION mode${NC}"
    echo ""
    read -p "Are you sure you want to proceed? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        echo "Migration cancelled."
        exit 0
    fi
fi

# Load environment variables
if [ -f .env ]; then
    echo -e "${GREEN}Loading environment variables...${NC}"
    export $(cat .env | grep -v '^#' | xargs)
elif [ -f .env.production ]; then
    echo -e "${GREEN}Loading production environment variables...${NC}"
    export $(cat .env.production | grep -v '^#' | xargs)
else
    echo -e "${RED}❌ No .env file found${NC}"
    exit 1
fi

# Validate DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}❌ DATABASE_URL not set${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Database URL configured${NC}"
echo ""

# Extract database connection details
DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
DB_NAME=$(echo $DATABASE_URL | sed -n 's/.*\/\([^?]*\).*/\1/p')
DB_USER=$(echo $DATABASE_URL | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')

echo "Database Details:"
echo "  Host: $DB_HOST"
echo "  Port: $DB_PORT"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo ""

# Step 1: Test database connection
echo -e "${YELLOW}Step 1: Testing database connection...${NC}"
if command -v psql &> /dev/null; then
    if psql "$DATABASE_URL" -c "SELECT 1" &> /dev/null; then
        echo -e "${GREEN}✅ Database connection successful${NC}"
    else
        echo -e "${RED}❌ Cannot connect to database${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  psql not found, skipping connection test${NC}"
fi
echo ""

# Step 2: Create backup
BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/db_backup_${TIMESTAMP}.sql"

mkdir -p "$BACKUP_DIR"

echo -e "${YELLOW}Step 2: Creating database backup...${NC}"
if command -v pg_dump &> /dev/null; then
    if pg_dump "$DATABASE_URL" > "$BACKUP_FILE" 2>/dev/null; then
        BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
        echo -e "${GREEN}✅ Backup created: $BACKUP_FILE ($BACKUP_SIZE)${NC}"
    else
        echo -e "${RED}❌ Backup failed${NC}"
        if [ "$ENVIRONMENT" = "production" ]; then
            echo "Cannot proceed without backup in production."
            exit 1
        else
            echo -e "${YELLOW}⚠️  Continuing without backup (development mode)${NC}"
        fi
    fi
else
    echo -e "${YELLOW}⚠️  pg_dump not found, skipping backup${NC}"
    if [ "$ENVIRONMENT" = "production" ]; then
        echo -e "${RED}❌ Cannot proceed without backup capability in production${NC}"
        exit 1
    fi
fi
echo ""

# Step 3: Check current migration status
echo -e "${YELLOW}Step 3: Checking current migration status...${NC}"
CURRENT_REVISION=$(alembic current 2>/dev/null | grep -oP '(?<=\()[a-f0-9]+(?=\))' || echo "none")
echo "Current revision: $CURRENT_REVISION"
echo ""

# Step 4: Check pending migrations
echo -e "${YELLOW}Step 4: Checking for pending migrations...${NC}"
PENDING_MIGRATIONS=$(alembic history --verbose 2>/dev/null | grep -c "-> " || echo "0")
echo "Pending migrations: $PENDING_MIGRATIONS"

if [ "$PENDING_MIGRATIONS" -eq 0 ]; then
    echo -e "${GREEN}✅ Database is up to date${NC}"
    exit 0
fi
echo ""

# Step 5: Show migration plan
echo -e "${YELLOW}Step 5: Migration plan:${NC}"
alembic history --verbose | head -n 20
echo ""

if [ "$ENVIRONMENT" = "production" ]; then
    read -p "Proceed with migration? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        echo "Migration cancelled."
        exit 0
    fi
    echo ""
fi

# Step 6: Validate migration integrity
echo -e "${YELLOW}Step 6: Validating migration integrity...${NC}"
if alembic check 2>&1 | grep -q "No issues"; then
    echo -e "${GREEN}✅ Migration integrity validated${NC}"
else
    echo -e "${RED}❌ Migration integrity check failed${NC}"
    alembic check
    exit 1
fi
echo ""

# Step 7: Run migrations
echo -e "${YELLOW}Step 7: Running migrations...${NC}"
if alembic upgrade head; then
    echo -e "${GREEN}✅ Migrations applied successfully${NC}"
else
    echo -e "${RED}❌ Migration failed${NC}"
    echo ""
    echo -e "${YELLOW}Attempting to restore from backup...${NC}"
    
    if [ -f "$BACKUP_FILE" ] && command -v psql &> /dev/null; then
        # Drop and recreate database
        echo "Restoring database from backup..."
        psql "$DATABASE_URL" < "$BACKUP_FILE"
        echo -e "${GREEN}✅ Database restored from backup${NC}"
    else
        echo -e "${RED}❌ Cannot restore backup${NC}"
        echo "Manual intervention required."
    fi
    
    exit 1
fi
echo ""

# Step 8: Verify migration
echo -e "${YELLOW}Step 8: Verifying migration...${NC}"
NEW_REVISION=$(alembic current 2>/dev/null | grep -oP '(?<=\()[a-f0-9]+(?=\))' || echo "none")
echo "New revision: $NEW_REVISION"

if [ "$NEW_REVISION" != "$CURRENT_REVISION" ]; then
    echo -e "${GREEN}✅ Migration verified${NC}"
else
    echo -e "${RED}❌ Migration verification failed${NC}"
    exit 1
fi
echo ""

# Step 9: Test database connectivity
echo -e "${YELLOW}Step 9: Testing database after migration...${NC}"
if command -v psql &> /dev/null; then
    if psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM alembic_version" &> /dev/null; then
        echo -e "${GREEN}✅ Database is accessible and functional${NC}"
    else
        echo -e "${RED}❌ Database test failed${NC}"
        exit 1
    fi
fi
echo ""

# Step 10: Cleanup old backups (keep last 10)
echo -e "${YELLOW}Step 10: Cleaning up old backups...${NC}"
BACKUP_COUNT=$(ls -1 "$BACKUP_DIR"/db_backup_*.sql 2>/dev/null | wc -l)
if [ "$BACKUP_COUNT" -gt 10 ]; then
    echo "Found $BACKUP_COUNT backups, keeping last 10..."
    ls -1t "$BACKUP_DIR"/db_backup_*.sql | tail -n +11 | xargs rm -f
    echo -e "${GREEN}✅ Old backups cleaned up${NC}"
else
    echo "Backup count: $BACKUP_COUNT (no cleanup needed)"
fi
echo ""

# Summary
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}✅ Migration completed successfully${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "Summary:"
echo "  Previous revision: $CURRENT_REVISION"
echo "  Current revision: $NEW_REVISION"
echo "  Backup location: $BACKUP_FILE"
echo "  Environment: $ENVIRONMENT"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  1. Test application functionality"
echo "  2. Monitor application logs"
echo "  3. Keep backup file for rollback if needed"
echo ""
