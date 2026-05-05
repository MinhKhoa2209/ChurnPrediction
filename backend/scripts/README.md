# Backend Scripts

This directory contains utility scripts for managing the Customer Churn Prediction Platform backend.

## R2 Storage Scripts

### verify_r2_buckets.py

Verifies that Cloudflare R2 buckets are properly configured and accessible.

**Requirements**: 33.1, 33.2, 33.3, 33.4, 33.5

**Usage**:
```bash
cd backend
python scripts/verify_r2_buckets.py
```

**What it checks**:
- ✅ Connection to R2 endpoint
- ✅ Bucket existence (models, reports, exports)
- ✅ Write permissions (upload test file)
- ✅ Read permissions (download test file)
- ✅ Delete permissions (remove test file)
- ✅ Path structure validation

**When to use**:
- After initial R2 setup
- After changing R2 configuration
- When troubleshooting R2 issues
- Before production deployment

**Example output**:
```
🔍 Cloudflare R2 Bucket Verification
=====================================

Configuration:
  Endpoint: https://a1b2c3d4e5f6.r2.cloudflarestorage.com
  Region: auto
  Models Bucket: churn-models
  Reports Bucket: churn-reports
  Exports Bucket: churn-exports

Testing connection...
✅ Successfully connected to R2

Verifying buckets...
✅ Bucket 'churn-models' exists
✅ Bucket 'churn-reports' exists
✅ Bucket 'churn-exports' exists

Testing permissions on 'churn-models'...
✅ Write permission verified
✅ Read permission verified
✅ Delete permission verified

🎉 All verification checks passed!
```

### create_r2_buckets.py

Creates Cloudflare R2 buckets programmatically using boto3.

**Requirements**: 33.1, 33.2, 33.3, 33.4

**Usage**:
```bash
cd backend

# Create production buckets
python scripts/create_r2_buckets.py --environment prod

# Create staging buckets
python scripts/create_r2_buckets.py --environment staging

# Create development buckets (no prefix)
python scripts/create_r2_buckets.py

# Skip CORS configuration
python scripts/create_r2_buckets.py --skip-cors

# Specify custom frontend origins
python scripts/create_r2_buckets.py --frontend-origins "https://app.example.com,https://www.example.com"
```

**Options**:
- `--environment ENV` - Environment prefix for bucket names (e.g., prod, staging, dev)
- `--skip-cors` - Skip CORS configuration
- `--frontend-origins ORIGINS` - Comma-separated list of frontend origins for CORS

**What it does**:
1. Creates three buckets: models, reports, exports
2. Configures CORS policies (unless --skip-cors)
3. Verifies bucket creation
4. Provides next steps

**When to use**:
- Initial R2 setup
- Setting up new environments (staging, production)
- Automating deployment pipelines

**Example output**:
```
🪣 Cloudflare R2 Bucket Creation

Buckets to create:
  Models: churn-prod-models
  Reports: churn-prod-reports
  Exports: churn-prod-exports
  Environment: prod

Endpoint: https://a1b2c3d4e5f6.r2.cloudflarestorage.com
Region: auto

Testing connection...
✅ Successfully connected to R2

Creating buckets...
✅ Created bucket 'churn-prod-models'
✅ Created bucket 'churn-prod-reports'
✅ Created bucket 'churn-prod-exports'

Configuring CORS policies...
  Frontend origins: https://app.example.com
✅ Set CORS policy for 'churn-prod-models'
✅ Set CORS policy for 'churn-prod-reports'
✅ Set CORS policy for 'churn-prod-exports'

🎉 Bucket creation completed!

Next steps:
  1. Update your .env file with the bucket names:
     S3_BUCKET_MODELS=churn-prod-models
     S3_BUCKET_REPORTS=churn-prod-reports
     S3_BUCKET_EXPORTS=churn-prod-exports
  2. Run verification script: python scripts/verify_r2_buckets.py
  3. See docs/R2_SETUP_GUIDE.md for additional configuration
```

## Prerequisites

All scripts require:
- Python 3.13+
- Backend dependencies installed: `pip install -r requirements.txt`
- Environment variables configured (see `backend/.env.example`)

## Environment Variables

Scripts use the following environment variables from `backend/config.py`:

```bash
S3_ENDPOINT_URL=https://<ACCOUNT_ID>.r2.cloudflarestorage.com
S3_ACCESS_KEY_ID=your-access-key-id
S3_SECRET_ACCESS_KEY=your-secret-access-key
S3_BUCKET_MODELS=churn-models
S3_BUCKET_REPORTS=churn-reports
S3_BUCKET_EXPORTS=churn-exports
S3_REGION=auto
```

Set these in your `.env` file or export them before running scripts.

## Troubleshooting

### "Configuration Errors" when running scripts

**Cause**: Required environment variables are not set

**Solution**:
1. Copy `backend/.env.example` to `backend/.env`
2. Fill in R2 credentials
3. Run script again

### "Connection failed" error

**Cause**: Invalid endpoint URL or network issues

**Solution**:
1. Verify `S3_ENDPOINT_URL` format: `https://<ACCOUNT_ID>.r2.cloudflarestorage.com`
2. Check Account ID is correct
3. Test connectivity: `curl https://<ACCOUNT_ID>.r2.cloudflarestorage.com`

### "Invalid access key ID" error

**Cause**: Incorrect R2 credentials

**Solution**:
1. Verify `S3_ACCESS_KEY_ID` and `S3_SECRET_ACCESS_KEY` are correct
2. Check API token is not expired
3. Regenerate token if needed in Cloudflare R2 dashboard

### "Bucket already exists" error

**Cause**: Bucket name is already taken (by you or someone else)

**Solution**:
1. If owned by you: Script will skip creation (this is normal)
2. If owned by someone else: Choose a different bucket name
3. Use `--environment` flag to add prefix: `--environment prod`

## Additional Resources

- **[R2 Setup Guide](../../docs/R2_SETUP_GUIDE.md)** - Comprehensive setup instructions
- **[R2 Deployment Checklist](../../docs/R2_DEPLOYMENT_CHECKLIST.md)** - Pre-deployment checklist
- **[R2 Operations Guide](../../docs/R2_OPERATIONS_GUIDE.md)** - Maintenance and troubleshooting
- **[Storage Service](../infrastructure/storage.py)** - R2 client implementation

## Contributing

When adding new scripts:
1. Add docstring with description and usage
2. Use `Colors` class for formatted output
3. Handle errors gracefully with clear messages
4. Update this README with script documentation
5. Add script to `.gitignore` if it contains sensitive data

## Support

For issues with scripts:
1. Check environment variables are set correctly
2. Review script output for specific error messages
3. Consult troubleshooting section above
4. See [R2 Setup Guide](../../docs/R2_SETUP_GUIDE.md) for detailed help

---

**Last Updated**: 2024
**Requirements**: 33.1, 33.2, 33.3, 33.4, 33.5, 33.6, 33.7
