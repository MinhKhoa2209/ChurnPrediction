import argparse
import importlib
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

boto3 = importlib.import_module("boto3")
ClientError = importlib.import_module("botocore.exceptions").ClientError
settings = importlib.import_module("backend.config").settings


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"


def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print("=" * len(text))


def print_success(text: str):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")


def print_error(text: str):
    print(f"{Colors.RED}❌ {text}{Colors.END}")


def print_warning(text: str):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")


def print_info(text: str):
    print(f"  {text}")


def get_bucket_names(environment: str = None) -> dict:
    if environment:
        prefix = f"churn-{environment}-"
    else:
        prefix = "churn-"

    return {
        "models": f"{prefix}models",
        "reports": f"{prefix}reports",
        "exports": f"{prefix}exports",
    }


def create_s3_client():
    try:
        client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key_id,
            aws_secret_access_key=settings.s3_secret_access_key,
            region_name=settings.s3_region,
        )
        return client
    except Exception as e:
        print_error(f"Failed to create S3 client: {e}")
        return None


def bucket_exists(client, bucket_name: str) -> bool:
    try:
        client.head_bucket(Bucket=bucket_name)
        return True
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "404":
            return False
        else:
            print_warning(f"Cannot verify bucket '{bucket_name}': {e}")
            return True
    except Exception as e:
        print_warning(f"Error checking bucket '{bucket_name}': {e}")
        return False


def create_bucket(client, bucket_name: str) -> bool:
    try:
        client.create_bucket(Bucket=bucket_name)
        print_success(f"Created bucket '{bucket_name}'")
        return True
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "BucketAlreadyOwnedByYou":
            print_warning(f"Bucket '{bucket_name}' already exists (owned by you)")
            return True
        elif error_code == "BucketAlreadyExists":
            print_error(f"Bucket '{bucket_name}' already exists (owned by someone else)")
            print_info("Choose a different bucket name")
            return False
        else:
            print_error(f"Failed to create bucket '{bucket_name}': {e}")
            return False
    except Exception as e:
        print_error(f"Unexpected error creating bucket '{bucket_name}': {e}")
        return False


def set_bucket_cors(client, bucket_name: str, frontend_origins: list) -> bool:
    cors_configuration = {
        "CORSRules": [
            {
                "AllowedOrigins": frontend_origins,
                "AllowedMethods": ["GET", "HEAD"],
                "AllowedHeaders": ["*"],
                "ExposeHeaders": ["ETag", "Content-Length", "Content-Type"],
                "MaxAgeSeconds": 3600,
            }
        ]
    }

    try:
        client.put_bucket_cors(Bucket=bucket_name, CORSConfiguration=cors_configuration)
        print_success(f"Set CORS policy for '{bucket_name}'")
        return True
    except ClientError as e:
        print_error(f"Failed to set CORS for '{bucket_name}': {e}")
        return False
    except Exception as e:
        print_error(f"Unexpected error setting CORS for '{bucket_name}': {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Create Cloudflare R2 buckets for Customer Churn Prediction Platform"
    )
    parser.add_argument(
        "--environment",
        type=str,
        default=None,
        help="Environment prefix for bucket names (e.g., prod, staging, dev)",
    )
    parser.add_argument("--skip-cors", action="store_true", help="Skip CORS configuration")
    parser.add_argument(
        "--frontend-origins",
        type=str,
        default=None,
        help="Comma-separated list of frontend origins for CORS (default: from CORS_ORIGINS env var)",
    )

    args = parser.parse_args()

    print_header("🪣 Cloudflare R2 Bucket Creation")

    bucket_names = get_bucket_names(args.environment)

    print("\nBuckets to create:")
    print_info(f"Models: {bucket_names['models']}")
    print_info(f"Reports: {bucket_names['reports']}")
    print_info(f"Exports: {bucket_names['exports']}")

    if args.environment:
        print_info(f"Environment: {args.environment}")

    if not settings.s3_endpoint_url:
        print_error("S3_ENDPOINT_URL is not set")
        print_info("Please set S3_ENDPOINT_URL in your .env file")
        sys.exit(1)

    if not settings.s3_access_key_id or not settings.s3_secret_access_key:
        print_error("S3 credentials are not set")
        print_info("Please set S3_ACCESS_KEY_ID and S3_SECRET_ACCESS_KEY in your .env file")
        sys.exit(1)

    print(f"\nEndpoint: {settings.s3_endpoint_url}")
    print(f"Region: {settings.s3_region}")

    client = create_s3_client()
    if not client:
        sys.exit(1)

    print("\nTesting connection...")
    try:
        client.list_buckets()
        print_success("Successfully connected to R2")
    except Exception as e:
        print_error(f"Connection failed: {e}")
        print_info("Check your S3_ENDPOINT_URL, S3_ACCESS_KEY_ID, and S3_SECRET_ACCESS_KEY")
        sys.exit(1)

    print("\nCreating buckets...")

    all_created = True
    for bucket_type, bucket_name in bucket_names.items():
        if bucket_exists(client, bucket_name):
            print_warning(f"Bucket '{bucket_name}' already exists")
        else:
            if not create_bucket(client, bucket_name):
                all_created = False

    if not all_created:
        print("\n" + Colors.RED + "Some buckets could not be created!" + Colors.END)
        sys.exit(1)

    if not args.skip_cors:
        print("\nConfiguring CORS policies...")

        if args.frontend_origins:
            frontend_origins = [origin.strip() for origin in args.frontend_origins.split(",")]
        else:
            frontend_origins = settings.cors_origins_list

        if not frontend_origins or frontend_origins == [""]:
            print_warning("No frontend origins specified, skipping CORS configuration")
            print_info("You can configure CORS later in the Cloudflare R2 dashboard")
        else:
            print_info(f"Frontend origins: {', '.join(frontend_origins)}")

            for bucket_name in bucket_names.values():
                set_bucket_cors(client, bucket_name, frontend_origins)
    else:
        print("\nSkipping CORS configuration (--skip-cors flag)")

    print("\n" + "=" * 50)
    print(Colors.GREEN + Colors.BOLD + "🎉 Bucket creation completed!" + Colors.END)

    print("\nCreated buckets:")
    print_info(f"✓ {bucket_names['models']} - Model artifacts and preprocessing configs")
    print_info(f"✓ {bucket_names['reports']} - Generated PDF reports")
    print_info(f"✓ {bucket_names['exports']} - Batch prediction CSV exports")

    print("\nNext steps:")
    print_info("1. Update your .env file with the bucket names:")
    print(f"     S3_BUCKET_MODELS={bucket_names['models']}")
    print(f"     S3_BUCKET_REPORTS={bucket_names['reports']}")
    print(f"     S3_BUCKET_EXPORTS={bucket_names['exports']}")
    print_info("2. Run verification script: python scripts/verify_r2_buckets.py")
    print_info("3. See docs/R2_SETUP_GUIDE.md for additional configuration")

    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nBucket creation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
