import os
from unittest.mock import Mock, patch

import pytest
from infraestructure.minio_client import FailedConnectionError, MinioClient


class TestMinioClient:
    @patch.dict(
        os.environ,
        {
            "MINIO_ENDPOINT": "localhost:9000",
            "MINIO_ACCESS_KEY": "minioadmin",
            "MINIO_SECRET_KEY": "minioadmin",
            "MINIO_SECURE": "false",
        },
    )
    @patch("infraestructure.minio_client.Minio")
    def test_succesfull_connection(self, mock_minio_class):
        mock_client = Mock()
        mock_client.list_buckets.return_value = iter([])
        mock_minio_class.return_value = mock_client

        minio_connection = MinioClient()
        assert minio_connection.endpoint == "localhost:9000"
        mock_minio_class.assert_called_once_with(
            "localhost:9000",
            access_key="minioadmin",
            secret_key="minioadmin",
            secure=False,
        )

    @patch("infraestructure.minio_client.Minio")
    def test_connection_failure(self, mock_minio_class):
        mock_minio_class.side_effect = Exception("Failed to create a client")

        with pytest.raises(FailedConnectionError) as exc_info:
            MinioClient()

        assert "Failed to create a client" in str(exc_info.value)
