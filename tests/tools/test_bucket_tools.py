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
