from minio import Minio
from minio.error import S3Error


class FailedConnectionError(Exception):
    """Custom exception for failed MinIO connections."""

    pass


class MinioClient:
    def __init__(self):
        self.config = self._load_minio_config()
        self.client = self._create_minio_client()

    def _load_minio_config(self):
        # Simulate loading MinIO configuration
        import os

        from dotenv import load_dotenv

        load_dotenv()
        return {
            "endpoint": os.getenv("MINIO_ENDPOINT"),
            "access_key": os.getenv("MINIO_ACCESS_KEY"),
            "secret_key": os.getenv("MINIO_SECRET_KEY"),
            "secure": os.getenv("MINIO_SECURE", "false").lower() == "true",
        }

    def _create_minio_client(self):
        try:
            minio_client = Minio(
                self.config["endpoint"],
                access_key=self.config["access_key"],
                secret_key=self.config["secret_key"],
                secure=self.config["secure"],
            )
            return minio_client
        except Exception as e:
            raise FailedConnectionError(f"Failed ti create a client: {e}") from e

    @property
    def endpoint(self):
        return self.config["endpoint"]
