from mcp.server.fastmcp import FastMCP

from minio_mcp.tools.bucket_tools import BucketTools

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


# Run the server
if __name__ == "__main__":
    transport = "stdio"  # Use standard input/output for communication
    if transport == "stdio":
        mcp.run(transport="stdio")
    elif transport == "streamable-http":
        mcp.run(transport="streamable-http")
    else:
        raise ValueError("Unsupported transport method")
