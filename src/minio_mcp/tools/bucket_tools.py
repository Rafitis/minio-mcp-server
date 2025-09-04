from minio.error import S3Error

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

    async def get_bucket_info(self, bucket_name: str) -> TextContent:
        """Get information about a specific bucket."""

        if not self.minio_client.client.bucket_exists(bucket_name):
            text_content = TextContent(
                response={},
                error=f"Bucket '{bucket_name}' does not exist.",
                status_code=404,
            )
            return text_content

        try:
            tags_info = self.minio_client.client.get_bucket_tags(bucket_name)
        except Exception as e:
            text_content = TextContent(
                response={},
                error=str(e),
                status_code=500,
            )
            return text_content

        try:
            buckets_list = self.minio_client.client.list_buckets()
            for bucket in buckets_list:
                if bucket.name == bucket_name:
                    creation_date = bucket.creation_date
                    break
        except Exception as e:
            text_content = TextContent(
                response={},
                error=str(e),
                status_code=500,
            )
            return text_content

        try:
            policy_info = self.minio_client.client.get_bucket_policy(bucket_name)
        except S3Error:
            policy_info = "No policy set"
        except Exception as e:
            text_content = TextContent(
                response={},
                error=str(e),
                status_code=500,
            )
            return text_content

        try:
            encryption_info = self.minio_client.client.get_bucket_encryption(bucket_name)
        except Exception as e:
            text_content = TextContent(
                response={},
                error=str(e),
                status_code=500,
            )
            return text_content

        try:
            list_objects = self.minio_client.client.list_objects(bucket_name, recursive=True)
            object_count = sum(1 for _ in list_objects)
            total_size = sum(obj.size for obj in list_objects)
        except Exception as e:
            text_content = TextContent(
                response={},
                error=str(e),
                status_code=500,
            )
            return text_content

        bucket_info = {
            "name": bucket_name,
            "creation_date": creation_date,
            "tags": tags_info,
            "policy": policy_info,
            "encryption": encryption_info,
            "object_count": object_count,
            "total_size": total_size,
        }
        text_content = TextContent(
            response=bucket_info,
            status_code=200,
        )
        return text_content

    async def list_objects(
        self, bucket_name: str, prefix: str = "", limit: int = 25
    ) -> TextContent:
        """List all objects in a specific bucket."""

        if not self.minio_client.client.bucket_exists(bucket_name):
            text_content = TextContent(
                response={},
                error=f"Bucket '{bucket_name}' does not exist.",
                status_code=404,
            )
            return text_content

        try:
            objects = self.minio_client.client.list_objects(
                bucket_name, prefix=prefix, recursive=True
            )
        except Exception as e:
            text_content = TextContent(
                response={},
                error=str(e),
                status_code=500,
            )
            return text_content

        list_of_objects = []
        count = 0
        for obj in objects:
            list_of_objects.append(
                {
                    "key": obj.object_name,
                    "last_modified": obj.last_modified,
                    "size": obj.size,
                    "etag": obj.etag,
                    "storage_class": obj.storage_class,
                }
            )
            count += 1
            if limit != -1 and count >= limit:
                break

        text_content = TextContent(
            response={"objects": list_of_objects},
            status_code=200,
        )
        return text_content

    async def create_bucket(self, bucket_name: str) -> TextContent:
        """Create a new bucket in the MinIO server."""

        if "/" in bucket_name:
            return TextContent(
                response={},
                error="Bucket name cannot contain '/' character.",
                status_code=400,
            )

        # Check if bucket already exists
        if self.minio_client.client.bucket_exists(bucket_name):
            return TextContent(
                response={},
                error=f"Bucket '{bucket_name}' already exists.",
                status_code=409,
            )

        try:
            self.minio_client.client.make_bucket(bucket_name)
        except Exception as e:
            text_content = TextContent(
                response={},
                error=str(e),
                status_code=500,
            )
            return text_content

        text_content = TextContent(
            response={"message": f"Bucket '{bucket_name}' created successfully."},
            status_code=200,
        )
        return text_content

    async def delete_bucket(self, bucket_name: str, force: bool = False) -> TextContent:
        """Delete a bucket from the MinIO server."""

        if not self.minio_client.client.bucket_exists(bucket_name):
            return TextContent(
                response={},
                error=f"Bucket '{bucket_name}' does not exist.",
                status_code=404,
            )

        if any(self.minio_client.client.list_objects(bucket_name, recursive=True)):
            if not force:
                return TextContent(
                    response={},
                    error=f"Bucket '{bucket_name}' is not empty. Use force=True to delete it along with its contents.",  # noqa: E501
                    status_code=400,
                )

        try:
            if force:
                objects = self.minio_client.client.list_objects(bucket_name, recursive=True)
                for obj in objects:
                    self.minio_client.client.remove_object(bucket_name, obj.object_name)
            self.minio_client.client.remove_bucket(bucket_name)
        except Exception as e:
            text_content = TextContent(
                response={},
                error=str(e),
                status_code=500,
            )
            return text_content

        text_content = TextContent(
            response={"message": f"Bucket '{bucket_name}' deleted successfully."},
            status_code=200,
        )
        return text_content
