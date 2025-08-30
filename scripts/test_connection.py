import os

from dotenv import load_dotenv
from minio import Minio
from minio.error import S3Error


def load_minio_config():
    # Simulate loading MinIO configuration
    load_dotenv()
    return {
        "endpoint": os.getenv("MINIO_ENDPOINT"),
        "access_key": os.getenv("MINIO_ACCESS_KEY"),
        "secret_key": os.getenv("MINIO_SECRET_KEY"),
        "secure": os.getenv("MINIO_SECURE", "false").lower() == "true",
    }


if __name__ == "__main__":
    config = load_minio_config()
    try:
        client = Minio(
            config["endpoint"],
            access_key=config["access_key"],
            secret_key=config["secret_key"],
            secure=config["secure"],
        )
        # Check if the connection is successful by listing buckets
        buckets = client.list_buckets()
        print("Connection successful. Buckets:")
        for bucket in buckets:
            print(f"- {bucket.name}")
    except S3Error as e:
        print(f"Connection failed: {e}")
