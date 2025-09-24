from datetime import datetime
from unittest.mock import Mock, patch

from minio_mcp.tools.object_tools import ObjectTools


class TestObjectTools:
    @patch("minio_mcp.tools.object_tools.MinioClient")
    async def test_get_object_info_success(self, mock_minio_client_class):
        # Setup mocks
        mock_client = Mock()
        mock_minio_client_instance = Mock()
        mock_minio_client_instance.client = mock_client
        mock_minio_client_class.return_value = mock_minio_client_instance

        # Mock bucket exists and object stats
        mock_client.bucket_exists.return_value = True
        mock_obj_stat = Mock()
        mock_obj_stat.size = 1024
        mock_obj_stat.last_modified = datetime(2024, 1, 15, 10, 30, 45)
        mock_obj_stat.etag = "d41d8cd98f00b204e9800998ecf8427e"
        mock_obj_stat.content_type = "text/plain"
        mock_obj_stat.metadata = {"user-key": "user-value"}
        mock_obj_stat.version_id = "version123"
        mock_obj_stat.is_delete_marker = False
        mock_client.stat_object.return_value = mock_obj_stat

        object_tools = ObjectTools()
        bucket_name = "test-bucket"
        object_name = "test-file.txt"
        result = await object_tools.get_object_info(bucket_name, object_name)

        # Assertions
        assert result.status_code == 200
        assert isinstance(result.response, dict)
        assert result.response["bucket_name"] == bucket_name
        assert result.response["object_name"] == object_name
        assert result.response["size"] == 1024
        assert result.response["last_modified"] == datetime(2024, 1, 15, 10, 30, 45)
        assert result.response["etag"] == "d41d8cd98f00b204e9800998ecf8427e"
        assert result.response["content_type"] == "text/plain"
        assert result.response["metadata"] == {"user-key": "user-value"}
        assert result.response["version_id"] == "version123"
        assert result.response["is_delete_marker"] is False

        mock_client.bucket_exists.assert_called_once_with(bucket_name)
        mock_client.stat_object.assert_called_once_with(bucket_name, object_name)

    @patch("minio_mcp.tools.object_tools.MinioClient")
    async def test_get_object_info_bucket_not_exists(self, mock_minio_client_class):
        # Setup mocks
        mock_client = Mock()
        mock_minio_client_instance = Mock()
        mock_minio_client_instance.client = mock_client
        mock_minio_client_class.return_value = mock_minio_client_instance

        # Mock bucket does not exist
        mock_client.bucket_exists.return_value = False

        object_tools = ObjectTools()
        bucket_name = "nonexistent-bucket"
        object_name = "test-file.txt"
        result = await object_tools.get_object_info(bucket_name, object_name)

        # Assertions
        assert result.status_code == 404
        assert result.error == f"Bucket '{bucket_name}' does not exist."
        assert result.response == {}
        mock_client.bucket_exists.assert_called_once_with(bucket_name)

    @patch("minio_mcp.tools.object_tools.MinioClient")
    async def test_get_object_info_object_not_found(self, mock_minio_client_class):
        # Setup mocks
        mock_client = Mock()
        mock_minio_client_instance = Mock()
        mock_minio_client_instance.client = mock_client
        mock_minio_client_class.return_value = mock_minio_client_instance

        # Mock bucket exists but object does not
        mock_client.bucket_exists.return_value = True
        mock_client.stat_object.side_effect = ValueError("Object not found")

        object_tools = ObjectTools()
        bucket_name = "test-bucket"
        object_name = "nonexistent-file.txt"
        result = await object_tools.get_object_info(bucket_name, object_name)

        # Assertions
        assert result.status_code == 404
        assert result.error == f"Object '{object_name}' does not exist in bucket '{bucket_name}'."
        assert result.response == {}
        mock_client.bucket_exists.assert_called_once_with(bucket_name)
        mock_client.stat_object.assert_called_once_with(bucket_name, object_name)

    @patch("minio_mcp.tools.object_tools.MinioClient")
    async def test_get_object_info_general_error(self, mock_minio_client_class):
        # Setup mocks
        mock_client = Mock()
        mock_minio_client_instance = Mock()
        mock_minio_client_instance.client = mock_client
        mock_minio_client_class.return_value = mock_minio_client_instance

        # Mock bucket exists but stat_object fails with general error
        mock_client.bucket_exists.return_value = True
        mock_client.stat_object.side_effect = Exception("Connection error")

        object_tools = ObjectTools()
        bucket_name = "test-bucket"
        object_name = "test-file.txt"
        result = await object_tools.get_object_info(bucket_name, object_name)

        # Assertions
        assert result.status_code == 500
        assert result.error == "Connection error"
        assert result.response == {}
        mock_client.bucket_exists.assert_called_once_with(bucket_name)
        mock_client.stat_object.assert_called_once_with(bucket_name, object_name)

    @patch("minio_mcp.tools.object_tools.MinioClient")
    async def test_delete_object_success(self, mock_minio_client_class):
        # Setup mocks
        mock_client = Mock()
        mock_minio_client_instance = Mock()
        mock_minio_client_instance.client = mock_client
        mock_minio_client_class.return_value = mock_minio_client_instance

        # Mock bucket exists and object deletion succeeds
        mock_client.bucket_exists.return_value = True
        mock_client.remove_object.return_value = None  # Successful deletion

        object_tools = ObjectTools()
        bucket_name = "test-bucket"
        object_name = "test-file.txt"
        result = await object_tools.delete_object(bucket_name, object_name)

        # Assertions
        assert result.status_code == 200
        assert isinstance(result.response, dict)
        assert (
            result.response["message"]
            == f"Object '{object_name}' deleted successfully from bucket '{bucket_name}'."
        )
        assert result.error is None

        mock_client.bucket_exists.assert_called_once_with(bucket_name)
        mock_client.remove_object.assert_called_once_with(bucket_name, object_name)

    @patch("minio_mcp.tools.object_tools.MinioClient")
    async def test_delete_object_with_version_id_success(self, mock_minio_client_class):
        # Setup mocks
        mock_client = Mock()
        mock_minio_client_instance = Mock()
        mock_minio_client_instance.client = mock_client
        mock_minio_client_class.return_value = mock_minio_client_instance

        # Mock bucket exists and object deletion with version succeeds
        mock_client.bucket_exists.return_value = True
        mock_client.remove_object.return_value = None  # Successful deletion

        object_tools = ObjectTools()
        bucket_name = "test-bucket"
        object_name = "test-file.txt"
        version_id = "version123"
        result = await object_tools.delete_object(bucket_name, object_name, version_id)

        # Assertions
        assert result.status_code == 200
        assert isinstance(result.response, dict)
        assert (
            result.response["message"]
            == f"Object '{object_name}' deleted successfully from bucket '{bucket_name}'."
        )
        assert result.error is None

        mock_client.bucket_exists.assert_called_once_with(bucket_name)
        mock_client.remove_object.assert_called_once_with(
            bucket_name, object_name, version_id=version_id
        )

    @patch("minio_mcp.tools.object_tools.MinioClient")
    async def test_delete_object_bucket_not_exists(self, mock_minio_client_class):
        # Setup mocks
        mock_client = Mock()
        mock_minio_client_instance = Mock()
        mock_minio_client_instance.client = mock_client
        mock_minio_client_class.return_value = mock_minio_client_instance

        # Mock bucket does not exist
        mock_client.bucket_exists.return_value = False

        object_tools = ObjectTools()
        bucket_name = "nonexistent-bucket"
        object_name = "test-file.txt"
        result = await object_tools.delete_object(bucket_name, object_name)

        # Assertions
        assert result.status_code == 404
        assert result.error == f"Bucket '{bucket_name}' does not exist."
        assert result.response == {}

        mock_client.bucket_exists.assert_called_once_with(bucket_name)
        mock_client.remove_object.assert_not_called()

    @patch("minio_mcp.tools.object_tools.MinioClient")
    async def test_delete_object_object_not_found(self, mock_minio_client_class):
        # Setup mocks
        mock_client = Mock()
        mock_minio_client_instance = Mock()
        mock_minio_client_instance.client = mock_client
        mock_minio_client_class.return_value = mock_minio_client_instance

        # Mock bucket exists but object does not
        mock_client.bucket_exists.return_value = True
        mock_client.remove_object.side_effect = ValueError("Object not found")

        object_tools = ObjectTools()
        bucket_name = "test-bucket"
        object_name = "nonexistent-file.txt"
        result = await object_tools.delete_object(bucket_name, object_name)

        # Assertions
        assert result.status_code == 404
        assert result.error == f"Object '{object_name}' does not exist in bucket '{bucket_name}'."
        assert result.response == {}

        mock_client.bucket_exists.assert_called_once_with(bucket_name)
        mock_client.remove_object.assert_called_once_with(bucket_name, object_name)

    @patch("minio_mcp.tools.object_tools.MinioClient")
    async def test_delete_object_general_error(self, mock_minio_client_class):
        # Setup mocks
        mock_client = Mock()
        mock_minio_client_instance = Mock()
        mock_minio_client_instance.client = mock_client
        mock_minio_client_class.return_value = mock_minio_client_instance

        # Mock bucket exists but remove_object fails with general error
        mock_client.bucket_exists.return_value = True
        mock_client.remove_object.side_effect = Exception("Connection error")

        object_tools = ObjectTools()
        bucket_name = "test-bucket"
        object_name = "test-file.txt"
        result = await object_tools.delete_object(bucket_name, object_name)

        # Assertions
        assert result.status_code == 500
        assert result.error == "Connection error"
        assert result.response == {}

        mock_client.bucket_exists.assert_called_once_with(bucket_name)
        mock_client.remove_object.assert_called_once_with(bucket_name, object_name)
