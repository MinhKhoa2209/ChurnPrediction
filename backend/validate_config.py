#!/usr/bin/env python3
"""
Configuration Validation Script
Validates environment configuration without starting the application
Usage: python validate_config.py
"""

import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from config import settings, get_config_summary
    import json
    
    print("=" * 80)
    print("CONFIGURATION VALIDATION SUCCESSFUL")
    print("=" * 80)
    print()
    
    # Display configuration summary
    summary = get_config_summary()
    
    print("Configuration Summary:")
    print("-" * 80)
    print(f"Environment: {summary['environment']}")
    print(f"Debug Mode: {summary['debug']}")
    print()
    
    print("Database:")
    print(f"  ✓ Configured: {summary['database']['configured']}")
    print(f"  ✓ Pool Size: {summary['database']['pool_size']}")
    print(f"  ✓ Max Overflow: {summary['database']['max_overflow']}")
    print()
    
    print("Cache (Redis):")
    print(f"  ✓ Configured: {summary['cache']['configured']}")
    print(f"  ✓ TTL: {summary['cache']['ttl']} seconds")
    print()
    
    print("Celery:")
    print(f"  ✓ Broker Configured: {summary['celery']['broker_configured']}")
    print(f"  ✓ Backend Configured: {summary['celery']['backend_configured']}")
    print()
    
    print("Authentication:")
    print(f"  ✓ Algorithm: {summary['auth']['algorithm']}")
    print(f"  ✓ Token Expiration: {summary['auth']['expiration_hours']} hours")
    print(f"  ✓ Bcrypt Rounds: {summary['auth']['bcrypt_rounds']}")
    print()
    
    print("Object Storage:")
    print(f"  ✓ Configured: {summary['storage']['configured']}")
    print(f"  ✓ Models Bucket: {summary['storage']['buckets']['models']}")
    print(f"  ✓ Reports Bucket: {summary['storage']['buckets']['reports']}")
    print(f"  ✓ Exports Bucket: {summary['storage']['buckets']['exports']}")
    print()
    
    print("MLflow:")
    print(f"  ✓ Configured: {summary['mlflow']['configured']}")
    print(f"  ✓ Experiment: {summary['mlflow']['experiment']}")
    print()
    
    print("API:")
    print(f"  ✓ Prefix: {summary['api']['prefix']}")
    print(f"  ✓ CORS Origins: {summary['api']['cors_origins']}")
    print(f"  ✓ Rate Limit: {summary['api']['rate_limit']} requests/minute")
    print()
    
    print("Email:")
    if summary['email']['configured']:
        print("  ✓ Configured: Email notifications enabled")
    else:
        print("  ⚠ Not Configured: Email notifications disabled")
    print()
    
    print("=" * 80)
    print("All required configuration is valid!")
    print("=" * 80)
    
    sys.exit(0)
    
except Exception as e:
    # Error already printed by config module
    sys.exit(1)
