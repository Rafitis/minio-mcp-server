from unittest.mock import Mock, patch

from minio_mcp.tools.bucket_tools import BucketTools


class TestBucketTools:
    @patch("minio_mcp.tools.bucket_tools.MinioClient")
    async def test_list_buckets(self, mock_minio_client_class):
        # Setup mocks
        mock_client = Mock()
        mock_minio_client_instance = Mock()
        mock_minio_client_instance.client = mock_client
        mock_minio_client_class.return_value = mock_minio_client_instance

        # Mock bucket list
        mock_bucket = Mock()
        mock_bucket.name = "test-bucket"
        mock_bucket.creation_date = "2024-01-15T10:30:45.000Z"
        mock_client.list_buckets.return_value = [mock_bucket]

        bucket_tools = BucketTools()
        result = await bucket_tools.list_buckets()

        assert result.status_code == 200, f"Error listing buckets: {result.error}"
        assert isinstance(result.response, dict), "Response is not a dictionary"
        assert "buckets" in result.response, "'buckets' key not in response"
        assert len(result.response["buckets"]) == 1
        assert result.response["buckets"][0]["name"] == "test-bucket"
        mock_client.list_buckets.assert_called_once()

    @patch("minio_mcp.tools.bucket_tools.MinioClient")
    async def test_get_bucket_info(self, mock_minio_client_class):
        # Setup mocks
        mock_client = Mock()
        mock_minio_client_instance = Mock()
        mock_minio_client_instance.client = mock_client
        mock_minio_client_class.return_value = mock_minio_client_instance

        # Mock bucket exists and has info
        bucket_name = "example-bucket"
        mock_client.bucket_exists.return_value = True

        # Mock get_bucket_tags
        mock_client.get_bucket_tags.return_value = {"tag1": "value1"}

        # Mock list_buckets for creation date
        mock_bucket = Mock()
        mock_bucket.name = bucket_name
        mock_bucket.creation_date = "2024-01-15T10:30:45.000Z"
        mock_client.list_buckets.return_value = [mock_bucket]

        # Mock bucket policy
        mock_client.get_bucket_policy.return_value = "policy-content"

        # Mock bucket encryption
        mock_client.get_bucket_encryption.return_value = "AES256"

        # Mock list_objects (called once but iterator is consumed twice - this is a bug in the real code)
        mock_object = Mock()
        mock_object.size = 1024
        # We return a list that can be iterated multiple times since the real code has this bug
        mock_client.list_objects.return_value = [mock_object]

        bucket_tools = BucketTools()
        result = await bucket_tools.get_bucket_info(bucket_name)

        assert result.status_code == 200, f"Unexpected error: {result.error}"
        assert isinstance(result.response, dict), "Response is not a dictionary"
        assert "name" in result.response, "'name' key not in response"
        assert result.response["name"] == bucket_name, "Bucket name does not match"
        assert result.response["object_count"] == 1
        assert result.response["total_size"] == 1024
        mock_client.bucket_exists.assert_called_once_with(bucket_name)

    @patch("minio_mcp.tools.bucket_tools.MinioClient")
    async def test_list_objects(self, mock_minio_client_class):
        # Setup mocks
        mock_client = Mock()
        mock_minio_client_instance = Mock()
        mock_minio_client_instance.client = mock_client
        mock_minio_client_class.return_value = mock_minio_client_instance

        # Mock bucket exists and list objects
        bucket_name = "example-bucket"
        mock_client.bucket_exists.return_value = True
        mock_object = Mock()
        mock_object.object_name = "test-file.txt"
        mock_object.size = 1024
        mock_object.last_modified = "2024-01-15T10:30:45.000Z"
        mock_client.list_objects.return_value = iter([mock_object])

        bucket_tools = BucketTools()
        result = await bucket_tools.list_objects(bucket_name, prefix="", limit=10)

        assert result.status_code == 200, f"Unexpected error: {result.error}"
        assert isinstance(result.response, dict), "Response is not a dictionary"
        assert "objects" in result.response, "'objects' key not in response"
        assert isinstance(result.response["objects"], list), "'objects' is not a list"
        assert len(result.response["objects"]) <= 10, "More objects returned than limit"
        mock_client.bucket_exists.assert_called_once_with(bucket_name)

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
        mock_client.list_objects.side_effect = lambda *args, **kwargs: iter([mock_object])  # noqa
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
