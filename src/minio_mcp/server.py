from mcp.server.fastmcp import FastMCP

from minio_mcp.tools.bucket_tools import BucketTools
from minio_mcp.tools.object_tools import ObjectTools

# Create an MCP server
mcp = FastMCP(
    "MINIO MCP Server",
    host="0.0.0.0",
    port=8000,
)


# Simple tool
@mcp.tool()
def say_hello(name: str) -> str:
    """Say hello to someone

    Args:
        name: The person's name to greet
    """
    return f"Hello, {name}! Nice to meet you."


@mcp.tool()
async def list_buckets() -> dict:
    """List all buckets in the MinIO server."""

    bucket_tools = BucketTools()
    result = await bucket_tools.list_buckets()
    if result.status_code != 200:
        return f"Error listing buckets: {result.error}"
    return result.response


@mcp.tool()
async def get_bucket_info(bucket_name: str) -> dict:
    """Get information about a specific bucket.

    Args:
        bucket_name: The name of the bucket to get information about
    """

    bucket_tools = BucketTools()
    if not bucket_name:
        return "Error: 'bucket_name' parameter is required."
    if not isinstance(bucket_name, str):
        return "Error: 'bucket_name' must be a string."

    result = await bucket_tools.get_bucket_info(bucket_name)
    if result.status_code != 200:
        return f"Error getting bucket info: {result.error}"
    return result.response


@mcp.tool()
async def list_objects(bucket_name: str, prefix: str = "", limit: int = 25) -> dict:
    """List objects in a specific bucket.

    Args:
        bucket_name: The name of the bucket to list objects from
        prefix: (Optional) Filter objects by prefix
        limit: (Optional) Limit the number of objects returned limit=-1 for no limit
    """

    bucket_tools = BucketTools()
    if not bucket_name:
        return "Error: 'bucket_name' parameter is required."
    if not isinstance(bucket_name, str):
        return "Error: 'bucket_name' must be a string."
    if not isinstance(prefix, str):
        return "Error: 'prefix' must be a string."

    result = await bucket_tools.list_objects(bucket_name, prefix, limit)
    if result.status_code != 200:
        return f"Error listing objects: {result.error}"
    return result.response


@mcp.tool()
async def create_bucket(bucket_name: str) -> str:
    """Create a new bucket in the MinIO server.

    Args:
        bucket_name: The name of the bucket to create
    """

    bucket_tools = BucketTools()
    if not bucket_name:
        return "Error: 'bucket_name' parameter is required."
    if not isinstance(bucket_name, str):
        return "Error: 'bucket_name' must be a string."

    result = await bucket_tools.create_bucket(bucket_name)
    if result.status_code != 200:
        return f"Error creating bucket: {result.error}"
    return f"Bucket '{bucket_name}' created successfully."


@mcp.tool()
async def delete_bucket(bucket_name: str, force: bool = False) -> str:
    """Delete a bucket from the MinIO server.

    Args:
        bucket_name: The name of the bucket to delete
        force: If True, delete all objects in the bucket before deleting the bucket,
    """

    bucket_tools = BucketTools()
    if not bucket_name:
        return "Error: 'bucket_name' parameter is required."
    if not isinstance(bucket_name, str):
        return "Error: 'bucket_name' must be a string."

    result = await bucket_tools.delete_bucket(bucket_name, force)
    if result.status_code != 200:
        return f"Error deleting bucket: {result.error}"
    return f"Bucket '{bucket_name}' deleted successfully."


@mcp.tool()
async def get_object_info(bucket_name: str, object_name: str) -> dict:
    """Get information about a specific object in a bucket.

    Args:
        bucket_name: The name of the bucket containing the object
        object_name: The name of the object to get information about
    """

    object_tools = ObjectTools()
    if not bucket_name:
        return "Error: 'bucket_name' parameter is required."
    if not isinstance(bucket_name, str):
        return "Error: 'bucket_name' must be a string."
    if not object_name:
        return "Error: 'object_name' parameter is required."
    if not isinstance(object_name, str):
        return "Error: 'object_name' must be a string."

    result = await object_tools.get_object_info(bucket_name, object_name)
    if result.status_code != 200:
        return f"Error getting object info: {result.error}"
    return result.response


# Run the server
if __name__ == "__main__":
    transport = "stdio"  # Use standard input/output for communication
    if transport == "stdio":
        mcp.run(transport="stdio")
    elif transport == "streamable-http":
        mcp.run(transport="streamable-http")
    else:
        raise ValueError("Unsupported transport method")
