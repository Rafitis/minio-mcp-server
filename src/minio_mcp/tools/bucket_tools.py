from minio_mcp.infrastructure.minio_client import MinioClient
from minio_mcp.tools.entities import TextContent


class BucketTools:
    def __init__(self):
        self.minio_client = MinioClient()

    async def list_buckets(self) -> TextContent:
        """List all buckets in the MinIO server."""
        try:
            buckets = self.minio_client.client.list_buckets()
        except Exception as e:
            # TODO: Excepción muy genérica...
            text_content = TextContent(
                response={},
                error=str(e),
                status_code=500,
            )
            return text_content

        list_of_buckets = []
        for bucket in buckets:
            list_of_buckets.append(
                {
                    "name": bucket.name,
                    "creation_date": bucket.creation_date,
                }
            )

        text_content = TextContent(
            response={"buckets": list_of_buckets},
            status_code=200,
        )
        return text_content
