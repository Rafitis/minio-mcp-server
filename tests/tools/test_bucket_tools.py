from unittest.mock import Mock, patch

from minio_mcp.tools.bucket_tools import BucketTools


class TestBucketTools:
    async def test_list_buckets(self):
        bucket_tools = BucketTools()
        result = await bucket_tools.list_buckets()

        assert result.status_code == 200, f"Error listing buckets: {result.error}"
        assert isinstance(result.response, dict), "Response is not a dictionary"
        assert "buckets" in result.response, "'buckets' key not in response"

    async def test_get_bucket_info(self):
        bucket_tools = BucketTools()
        # Replace 'example-bucket' with an actual bucket name for real testing
        bucket_name = "example-bucket"
        result = await bucket_tools.get_bucket_info(bucket_name)

        if result.status_code != 200:
            assert result.status_code == 404, f"Unexpected error: {result.error}"
        else:
            assert isinstance(result.response, dict), "Response is not a dictionary"
            assert "name" in result.response, "'name' key not in response"
            assert result.response["name"] == bucket_name, "Bucket name does not match"

    async def test_list_objects(self):
        bucket_tools = BucketTools()
        # Replace 'example-bucket' with an actual bucket name for real testing
        bucket_name = "example-bucket"
        result = await bucket_tools.list_objects(bucket_name, prefix="", limit=10)

        if result.status_code != 200:
            assert result.status_code == 404, f"Unexpected error: {result.error}"
        else:
            assert isinstance(result.response, dict), "Response is not a dictionary"
            assert "objects" in result.response, "'objects' key not in response"
            assert isinstance(result.response["objects"], list), "'objects' is not a list"
            assert len(result.response["objects"]) <= 10, "More objects returned than limit"

    @patch("minio_mcp.tools.bucket_tools.MinioClient")
    async def test_create_bucket_success(self, mock_minio_client_class):
        # Mock the MinioClient and its methods
        mock_client = Mock()
        mock_minio_client_instance = Mock()
        mock_minio_client_instance.client = mock_client
        mock_minio_client_class.return_value = mock_minio_client_instance

        # Mock bucket does not exist and creation succeeds
        mock_client.bucket_exists.return_value = False
        mock_client.make_bucket.return_value = None

        bucket_tools = BucketTools()
        bucket_name = "test-bucket"
        result = await bucket_tools.create_bucket(bucket_name)

        # Assertions
        assert result.status_code == 200
        assert isinstance(result.response, dict)
        assert result.response["message"] == f"Bucket '{bucket_name}' created successfully."
        mock_client.bucket_exists.assert_called_once_with(bucket_name)
        mock_client.make_bucket.assert_called_once_with(bucket_name)

    @patch("minio_mcp.tools.bucket_tools.MinioClient")
    async def test_create_bucket_already_exists(self, mock_minio_client_class):
        # Mock the MinioClient and its methods
        mock_client = Mock()
        mock_minio_client_instance = Mock()
        mock_minio_client_instance.client = mock_client
        mock_minio_client_class.return_value = mock_minio_client_instance

        # Mock bucket already exists
        mock_client.bucket_exists.return_value = True

        bucket_tools = BucketTools()
        bucket_name = "existing-bucket"
        result = await bucket_tools.create_bucket(bucket_name)

        # Assertions
        assert result.status_code == 409
        assert result.error == f"Bucket '{bucket_name}' already exists."
        assert result.response == {}
        mock_client.bucket_exists.assert_called_once_with(bucket_name)

    @patch("minio_mcp.tools.bucket_tools.MinioClient")
    async def test_delete_empty_bucket_success(self, mock_minio_client_class):
        # Setup mocks
        mock_client = Mock()
        mock_minio_client_instance = Mock()
        mock_minio_client_instance.client = mock_client
        mock_minio_client_class.return_value = mock_minio_client_instance

        # Mock bucket exists and is empty
        mock_client.bucket_exists.return_value = True
        mock_client.list_objects.return_value = iter([])  # Empty bucket
        mock_client.remove_bucket.return_value = None

        bucket_tools = BucketTools()
        bucket_name = "empty-bucket"
        result = await bucket_tools.delete_bucket(bucket_name, force=False)

        # Assertions
        assert result.status_code == 200
        assert isinstance(result.response, dict)
        assert result.response["message"] == f"Bucket '{bucket_name}' deleted successfully."
        mock_client.bucket_exists.assert_called_once_with(bucket_name)
        mock_client.remove_bucket.assert_called_once_with(bucket_name)

    @patch("minio_mcp.tools.bucket_tools.MinioClient")
    async def test_delete_bucket_not_exists(self, mock_minio_client_class):
        # Setup mocks
        mock_client = Mock()
        mock_minio_client_instance = Mock()
        mock_minio_client_instance.client = mock_client
        mock_minio_client_class.return_value = mock_minio_client_instance

        # Mock bucket does not exist
        mock_client.bucket_exists.return_value = False

        bucket_tools = BucketTools()
        bucket_name = "nonexistent-bucket"
        result = await bucket_tools.delete_bucket(bucket_name, force=False)

        # Assertions
        assert result.status_code == 404
        assert result.error == f"Bucket '{bucket_name}' does not exist."
        assert result.response == {}
        mock_client.bucket_exists.assert_called_once_with(bucket_name)

    @patch("minio_mcp.tools.bucket_tools.MinioClient")
    async def test_delete_non_empty_bucket_without_force(self, mock_minio_client_class):
        # Setup mocks
        mock_client = Mock()
        mock_minio_client_instance = Mock()
        mock_minio_client_instance.client = mock_client
        mock_minio_client_class.return_value = mock_minio_client_instance

        # Mock bucket exists and has objects
        mock_client.bucket_exists.return_value = True
        mock_object = Mock()
        mock_object.object_name = "file.txt"
        mock_client.list_objects.return_value = iter([mock_object])  # Non-empty bucket

        bucket_tools = BucketTools()
        bucket_name = "non-empty-bucket"
        result = await bucket_tools.delete_bucket(bucket_name, force=False)

        # Assertions
        assert result.status_code == 400
        assert "is not empty" in result.error
        assert result.response == {}
        mock_client.bucket_exists.assert_called_once_with(bucket_name)

    @patch("minio_mcp.tools.bucket_tools.MinioClient")
    async def test_delete_non_empty_bucket_with_force(self, mock_minio_client_class):
        # Setup mocks
        mock_client = Mock()
        mock_minio_client_instance = Mock()
        mock_minio_client_instance.client = mock_client
        mock_minio_client_class.return_value = mock_minio_client_instance

        # Mock bucket exists and has objects
        mock_client.bucket_exists.return_value = True
        mock_object = Mock()
        mock_object.object_name = "file.txt"
        # list_objects is called twice, so we need to return a fresh iterator each time
        mock_client.list_objects.side_effect = lambda *args, **kwargs: iter([mock_object])
        mock_client.remove_object.return_value = None
        mock_client.remove_bucket.return_value = None

        bucket_tools = BucketTools()
        bucket_name = "non-empty-bucket"
        result = await bucket_tools.delete_bucket(bucket_name, force=True)

        # Assertions
        assert result.status_code == 200
        assert isinstance(result.response, dict)
        assert result.response["message"] == f"Bucket '{bucket_name}' deleted successfully."
        mock_client.bucket_exists.assert_called_once_with(bucket_name)
        mock_client.remove_object.assert_called_once_with(bucket_name, "file.txt")
        mock_client.remove_bucket.assert_called_once_with(bucket_name)
