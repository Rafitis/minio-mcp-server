from minio_mcp.tools.bucket_tools import BucketTools


class TestBucketTools:
    async def test_list_buckets(self):
        bucket_tools = BucketTools()
        result = await bucket_tools.list_buckets()

        assert result.status_code == 200, f"Error listing buckets: {result.error}"
        assert isinstance(result.response, dict), "Response is not a dictionary"
        assert "buckets" in result.response, "'buckets' key not in response"
