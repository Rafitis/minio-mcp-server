# MinIO MCP Server

A Model Context Protocol (MCP) server that provides a bridge between MCP-compatible clients and MinIO object storage. This server exposes MinIO operations as MCP tools for seamless bucket management and object operations.

## Features

- **6 MCP Tools** organized by domain for comprehensive MinIO operations:

### Bucket Management
  - `list_buckets`: List all available buckets with creation dates
  - `get_bucket_info`: Get detailed bucket information (metadata, policies, object count, total size, encryption)
  - `create_bucket`: Create new buckets with name validation and existence checks
  - `delete_bucket`: Delete buckets (empty only) or force delete with all contents

### Object Management  
  - `list_objects`: List objects with filtering (prefix, recursive) and configurable limits (default 25)
  - `get_object_info`: Get detailed object metadata (size, content-type, etag, version info, custom metadata)

### Key Features
- **FastMCP Integration**: Built on FastMCP framework for robust MCP protocol support
- **Comprehensive Validation**: Input validation, error handling with appropriate HTTP status codes (400, 404, 409, 500)
- **Async Architecture**: Full async/await support for MCP protocol compliance
- **Modular Design**: Separated concerns with BucketTools and ObjectTools classes
- **Extensive Testing**: 100% test coverage with advanced mocking techniques
- **Standardized Responses**: Consistent error handling via TextContent entity

## Quick Start

### Prerequisites

- Python 3.11 or higher
- MinIO server (local or remote)
- UV package manager (recommended)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd minio-mcp-server

# Install dependencies
uv sync

# Install in development mode
uv pip install -e .
```

### Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Configure your MinIO connection in `.env`:
```env
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_SECURE=false
MINIO_LOG_LEVEL=INFO
```

### Running the Server

```bash
# Start the MCP server (stdio transport for Claude Desktop)
uv run python src/minio_mcp/server.py

# Test with MCP Inspector (interactive testing)
uv run mcp src/minio_mcp/server.py

# Alternative: Direct python execution
cd src/minio_mcp
python server.py
```

## Using with Claude Desktop

To connect this MCP server with Claude Desktop:

### 1. Configure Claude Desktop

Edit your Claude Desktop configuration file:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

Add this configuration (adjust paths for your system):

```json
{
  "mcpServers": {
    "minio-mcp-server": {
      "command": "/Users/your_username/.local/bin/uv",
      "args": [
        "--directory",
        "/path/to/your/minio-mcp-server",
        "run",
        "python",
        "src/minio_mcp/server.py"
      ],
      "env": {
        "MINIO_ENDPOINT": "localhost:9000",
        "MINIO_ACCESS_KEY": "minioadmin",
        "MINIO_SECRET_KEY": "minioadmin",
        "MINIO_SECURE": "false"
      }
    }
  }
}
```

### 2. Restart Claude Desktop

After saving the configuration, completely restart Claude Desktop.

### 3. Test the Connection

Try commands like:
- "List all buckets in MinIO"
- "Show me information about the 'my-bucket' bucket"
- "List the first 10 objects in 'my-bucket'"
- "Get information about 'file.txt' in 'my-bucket'"

## Architecture

### Core Components

- **FastMCP Server** (`server.py`): Main MCP protocol handler using FastMCP framework
- **MinioClient** (`infrastructure/minio_client.py`): Infrastructure layer with MinIO client management and configuration  
- **BucketTools** (`tools/bucket_tools.py`): Business logic for bucket operations with validation and error handling
- **ObjectTools** (`tools/object_tools.py`): Business logic for object operations with comprehensive metadata extraction
- **TextContent** (`tools/entities.py`): Standardized response entity for consistent error handling

### Data Flow

```
MCP Client → FastMCP Server → BucketTools/ObjectTools → MinioClient → MinIO Server
```

## Configuration Options

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `MINIO_ENDPOINT` | MinIO server endpoint | Required |
| `MINIO_ACCESS_KEY` | Access key for authentication | Required |
| `MINIO_SECRET_KEY` | Secret key for authentication | Required |
| `MINIO_SECURE` | Use HTTPS (true/false) | `true` |
| `MINIO_LOG_LEVEL` | Logging level (DEBUG/INFO/WARNING/ERROR) | `INFO` |
| `MINIO_MAX_OBJECTS_LIST` | Maximum objects per list operation | `25` |

## Development

### Setting up a Test MinIO Server

```bash
docker run -p 9000:9000 -p 9001:9001 \
  --name minio-test \
  -e "MINIO_ROOT_USER=minioadmin" \
  -e "MINIO_ROOT_PASSWORD=minioadmin" \
  quay.io/minio/minio server /data --console-address ":9001"
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov=src/minio_mcp --cov-report=html

# Run specific test files
uv run pytest tests/tools/test_bucket_tools.py -v
uv run pytest tests/tools/test_object_tools.py -v
uv run pytest tests/infrastructure/test_minio_client.py -v

# Test specific functionality
uv run pytest -k "test_create_bucket" -v
```

### Code Quality

```bash
# Lint and format check
uv run ruff check src tests

# Auto-format code
uv run ruff format src tests

# Type checking
uv run mypy src
```

## License

[Add your license here]

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass and code quality checks succeed
6. Submit a pull request

## Support

For issues and questions, please check the documentation or open an issue in the repository.