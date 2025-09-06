from minio_mcp.infrastructure.minio_client import MinioClient
from minio_mcp.tools.entities import TextContent


class ObjectTools:
    """A class to manage bucket operations in MinIO"""

    def __init__(self):
        self.minio_client = MinioClient()

    async def get_object_info(self, bucket_name: str, object_name: str) -> TextContent:
        """Get information about a specific object in a bucket."""
        if not self.minio_client.client.bucket_exists(bucket_name):
            text_content = TextContent(
                response={},
                error=f"Bucket '{bucket_name}' does not exist.",
                status_code=404,
            )
            return text_content

        try:
            obj_stat = self.minio_client.client.stat_object(bucket_name, object_name)
        except ValueError:
            text_content = TextContent(
                response={},
                error=f"Object '{object_name}' does not exist in bucket '{bucket_name}'.",
                status_code=404,
            )
            return text_content
        except Exception as e:
            text_content = TextContent(
                response={},
                error=str(e),
                status_code=500,
            )
            return text_content

        object_info = {
            "bucket_name": bucket_name,
            "object_name": object_name,
            "size": obj_stat.size,
            "last_modified": obj_stat.last_modified,
            "etag": obj_stat.etag,
            "content_type": obj_stat.content_type,
            "metadata": obj_stat.metadata,
            "version_id": obj_stat.version_id,
            "is_delete_marker": obj_stat.is_delete_marker,
        }

        text_content = TextContent(
            response=object_info,
            status_code=200,
        )
        return text_content
