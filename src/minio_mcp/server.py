# server.py
from mcp.server.fastmcp import FastMCP

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


# Run the server
if __name__ == "__main__":
    transport = "stdio"  # Use standard input/output for communication
    if transport == "stdio":
        mcp.run(transport="stdio")
    elif transport == "streamable-http":
        mcp.run(transport="streamable-http")
    else:
        raise ValueError("Unsupported transport method")
