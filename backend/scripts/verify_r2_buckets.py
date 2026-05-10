import importlib
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

boto3 = importlib.import_module("boto3")
botocore_exceptions = importlib.import_module("botocore.exceptions")
ClientError = botocore_exceptions.ClientError
EndpointConnectionError = botocore_exceptions.EndpointConnectionError
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


def verify_configuration():
    print_header("🔍 Cloudflare R2 Bucket Verification")

    print("\nConfiguration:")
    print_info(f"Endpoint: {settings.s3_endpoint_url}")
    print_info(f"Region: {settings.s3_region}")
    print_info(f"Models Bucket: {settings.s3_bucket_models}")
    print_info(f"Reports Bucket: {settings.s3_bucket_reports}")
    print_info(f"Exports Bucket: {settings.s3_bucket_exports}")

    errors = []

    if not settings.s3_endpoint_url:
        errors.append("S3_ENDPOINT_URL is not set")

    if not settings.s3_access_key_id:
        errors.append("S3_ACCESS_KEY_ID is not set")

    if not settings.s3_secret_access_key:
        errors.append("S3_SECRET_ACCESS_KEY is not set")

    if not settings.s3_bucket_models:
        errors.append("S3_BUCKET_MODELS is not set")

    if not settings.s3_bucket_reports:
        errors.append("S3_BUCKET_REPORTS is not set")

    if not settings.s3_bucket_exports:
        errors.append("S3_BUCKET_EXPORTS is not set")

    if errors:
        print("\n" + Colors.RED + "Configuration Errors:" + Colors.END)
        for error in errors:
            print_error(error)
        print("\nPlease check your .env file or environment variables.")
        print("See backend/.env.example for required configuration.")
        return False

    return True


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


def test_connection(client):
    print("\nTesting connection...")
    try:
        client.list_buckets()
        print_success("Successfully connected to R2")
        return True
    except EndpointConnectionError as e:
        print_error(f"Connection failed: {e}")
        print_warning("Check that S3_ENDPOINT_URL is correct")
        return False
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "InvalidAccessKeyId":
            print_error("Invalid access key ID")
            print_warning("Check that S3_ACCESS_KEY_ID is correct")
        elif error_code == "SignatureDoesNotMatch":
            print_error("Invalid secret access key")
            print_warning("Check that S3_SECRET_ACCESS_KEY is correct")
        else:
            print_error(f"Authentication failed: {e}")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False


def verify_bucket_exists(client, bucket_name: str) -> bool:
    try:
        client.head_bucket(Bucket=bucket_name)
        print_success(f"Bucket '{bucket_name}' exists")
        return True
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "404":
            print_error(f"Bucket '{bucket_name}' does not exist")
            print_warning(f"Create bucket '{bucket_name}' in Cloudflare R2 dashboard")
        elif error_code == "403":
            print_error(f"Access denied to bucket '{bucket_name}'")
            print_warning("Check that API token has permissions for this bucket")
        else:
            print_error(f"Error checking bucket '{bucket_name}': {e}")
        return False
    except Exception as e:
        print_error(f"Unexpected error checking bucket '{bucket_name}': {e}")
        return False


def test_bucket_permissions(client, bucket_name: str) -> bool:
    print(f"\nTesting permissions on '{bucket_name}'...")

    test_key = "test/verification_test.txt"
    test_content = b"This is a test file for R2 bucket verification"

    try:
        client.put_object(
            Bucket=bucket_name, Key=test_key, Body=test_content, ContentType="text/plain"
        )
        print_success("Write permission verified")
    except ClientError as e:
        print_error(f"Write permission failed: {e}")
        return False
    except Exception as e:
        print_error(f"Unexpected error during write test: {e}")
        return False

    try:
        response = client.get_object(Bucket=bucket_name, Key=test_key)
        downloaded_content = response["Body"].read()

        if downloaded_content == test_content:
            print_success("Read permission verified")
        else:
            print_error("Read permission failed: content mismatch")
            return False
    except ClientError as e:
        print_error(f"Read permission failed: {e}")
        return False
    except Exception as e:
        print_error(f"Unexpected error during read test: {e}")
        return False

    try:
        client.delete_object(Bucket=bucket_name, Key=test_key)
        print_success("Delete permission verified")
    except ClientError as e:
        print_error(f"Delete permission failed: {e}")
        print_warning("This may cause issues with account deletion (Requirement 33.7)")
        return False
    except Exception as e:
        print_error(f"Unexpected error during delete test: {e}")
        return False

    return True


def verify_path_structure(client, bucket_name: str, path_prefix: str) -> bool:
    try:
        test_key = f"{path_prefix}/test-user-id/test-resource-id/test.txt"
        client.put_object(Bucket=bucket_name, Key=test_key, Body=b"Path structure test")

        client.delete_object(Bucket=bucket_name, Key=test_key)

        return True
    except Exception as e:
        print_error(f"Path structure test failed: {e}")
        return False


def main():
    if not verify_configuration():
        sys.exit(1)

    client = create_s3_client()
    if not client:
        sys.exit(1)

    if not test_connection(client):
        sys.exit(1)

    print("\nVerifying buckets...")
    buckets = [
        settings.s3_bucket_models,
        settings.s3_bucket_reports,
        settings.s3_bucket_exports,
    ]

    all_buckets_exist = True
    for bucket in buckets:
        if not verify_bucket_exists(client, bucket):
            all_buckets_exist = False

    if not all_buckets_exist:
        print("\n" + Colors.RED + "Some buckets are missing!" + Colors.END)
        print("Please create the missing buckets in Cloudflare R2 dashboard.")
        print("See docs/R2_SETUP_GUIDE.md for instructions.")
        sys.exit(1)

    all_permissions_ok = True

    if not test_bucket_permissions(client, settings.s3_bucket_models):
        all_permissions_ok = False

    if not test_bucket_permissions(client, settings.s3_bucket_reports):
        all_permissions_ok = False

    if not test_bucket_permissions(client, settings.s3_bucket_exports):
        all_permissions_ok = False

    if not all_permissions_ok:
        print("\n" + Colors.RED + "Permission tests failed!" + Colors.END)
        print("Please check your API token permissions in Cloudflare R2 dashboard.")
        print("The token needs read, write, and delete permissions for all buckets.")
        sys.exit(1)

    print("\nVerifying path structures...")

    path_tests = [
        (settings.s3_bucket_models, "models", "Requirement 33.1, 33.2"),
        (settings.s3_bucket_reports, "reports", "Requirement 33.3"),
        (settings.s3_bucket_exports, "exports", "Requirement 33.4"),
    ]

    all_paths_ok = True
    for bucket, prefix, requirement in path_tests:
        if verify_path_structure(client, bucket, prefix):
            print_success(f"Path structure '{prefix}/*' verified ({requirement})")
        else:
            all_paths_ok = False

    if not all_paths_ok:
        print_warning("Some path structure tests failed")
        print_warning("This may not affect functionality, but should be investigated")

    print("\n" + "=" * 50)
    if all_buckets_exist and all_permissions_ok and all_paths_ok:
        print(Colors.GREEN + Colors.BOLD + "🎉 All verification checks passed!" + Colors.END)
        print("\nYour R2 buckets are properly configured and ready to use.")
        print("The backend can now store:")
        print_info("✓ Model artifacts (models/{user_id}/{model_version_id}/)")
        print_info("✓ Preprocessing configs (models/{user_id}/{model_version_id}/)")
        print_info("✓ PDF reports (reports/{user_id}/{report_id}/)")
        print_info("✓ Batch exports (exports/{user_id}/{batch_id}/)")
        sys.exit(0)
    else:
        print(Colors.RED + Colors.BOLD + "❌ Verification failed!" + Colors.END)
        print("\nPlease fix the issues above and run the script again.")
        print("See docs/R2_SETUP_GUIDE.md for detailed setup instructions.")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nVerification cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
