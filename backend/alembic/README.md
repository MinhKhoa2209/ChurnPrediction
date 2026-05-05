# Database Migrations with Alembic

This directory contains Alembic database migrations for the Customer Churn Prediction Platform.

## Requirements

- SQLAlchemy 2.x
- Alembic 1.14.0
- PostgreSQL 18
- psycopg2-binary (for synchronous connections)

## Configuration

The database connection is configured via environment variables in `.env`:

```bash
DATABASE_URL=postgresql://churn_user:churn_password@localhost:5432/churn_prediction
```

**Note**: For Alembic migrations, use the synchronous `postgresql://` driver (not `postgresql+asyncpg://`).

## Migration Files

### 001_initial_migration.py

Initial migration that creates all 11 database tables:

1. **users** - User authentication and authorization
2. **datasets** - Uploaded customer datasets
3. **customer_records** - Individual customer records with encrypted sensitive fields
4. **preprocessing_configs** - Feature engineering parameters
5. **model_versions** - Trained ML model metadata
6. **training_jobs** - Asynchronous training job tracking
7. **training_progress** - Training metrics over time
8. **predictions** - Churn predictions with SHAP values
9. **reports** - Generated PDF reports
10. **notifications** - User notifications
11. **audit_logs** - Data access audit trail

The migration also:
- Enables PostgreSQL extensions (`uuid-ossp`, `pgcrypto`)
- Creates ENUM types for status fields
- Adds indexes for performance optimization (Requirement 25.4)
- Adds check constraints for data validation

## Usage

### Apply Migrations

To apply all pending migrations to the database:

```bash
cd backend
python -m alembic upgrade head
```

This will:
1. Create all tables if they don't exist
2. Apply any pending migrations
3. Update the `alembic_version` table

### Rollback Migrations

To rollback the last migration:

```bash
python -m alembic downgrade -1
```

To rollback all migrations:

```bash
python -m alembic downgrade base
```

### Check Current Version

To see the current migration version:

```bash
python -m alembic current
```

### View Migration History

To see all migrations:

```bash
python -m alembic history
```

### Create New Migration

To create a new migration after modifying models:

```bash
python -m alembic revision --autogenerate -m "Description of changes"
```

**Important**: Always review auto-generated migrations before applying them!

## Startup Integration

The backend application should apply migrations automatically on startup (Requirement 25.2):

```python
from alembic import command
from alembic.config import Config

def apply_migrations():
    """Apply pending database migrations on startup"""
    alembic_cfg = Config("alembic.ini")
    try:
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations applied successfully")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        # Requirement 25.3: Rollback on failure
        command.downgrade(alembic_cfg, "-1")
        raise
```

## Migration Integrity

Before applying migrations in production (Requirement 25.5):

1. **Backup the database** (Requirement 25.6)
2. **Validate migration integrity**:
   ```bash
   python -m alembic check
   ```
3. **Test in staging environment first**
4. **Apply with monitoring**

## Troubleshooting

### Connection Errors

If you see connection errors, verify:
- PostgreSQL is running
- Database credentials in `.env` are correct
- Database exists: `createdb churn_prediction`
- User has proper permissions

### Import Errors

If you see module import errors:
- Ensure you're running from the `backend` directory
- Check that all dependencies are installed: `pip install -r requirements.txt`

### Migration Conflicts

If migrations are out of sync:
```bash
# Check current state
python -m alembic current

# Stamp database with current version (use with caution!)
python -m alembic stamp head
```

## Schema Documentation

For detailed schema documentation, see:
- `design.md` - Complete database schema with relationships
- `requirements.md` - Requirements mapped to database tables
- Model files in `backend/domain/models/` - SQLAlchemy model definitions
