# MinIO MCP Server

A Model Context Protocol (MCP) server that provides a bridge between MCP-compatible clients and MinIO object storage. This server exposes MinIO operations as MCP tools for seamless bucket management and object operations.

## Features

- **7 MCP Tools** for comprehensive MinIO operations:
  - `list_buckets`: List all available buckets
  - `get_bucket_info`: Get detailed bucket information (size, object count, policies)
  - `list_objects`: List objects with filtering (prefix, recursive, limit)
  - `get_object_info`: Get object metadata and information
  - `create_bucket`: Create new buckets with optional location
  - `delete_bucket`: Delete buckets with optional force flag
  - `test_connection`: Test MinIO server connectivity

- **Async Architecture**: Full async/await support for MCP protocol compliance
- **Robust Error Handling**: Comprehensive error handling with formatted responses
- **Configuration Management**: Pydantic-based config with environment variable support
- **Type Safety**: Full type checking with mypy

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
# Start the MCP server
uv run minio-mcp-server run

# Test your MinIO connection
uv run minio-mcp-server test-connection

# Run with debug logging
uv run minio-mcp-server run --log-level DEBUG
```

## Architecture

### Core Components

- **MinIOMCPServer**: Main MCP protocol handler and coordinator
- **MinIOService**: Async wrapper for MinIO Python client operations  
- **BucketTools**: Business logic and MCP tool implementations
- **Configuration**: Pydantic-based configuration management

### Data Flow

```
MCP Client → MinIOMCPServer → BucketTools → MinIOService → MinIO Server
```

## Configuration Options

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `MINIO_ENDPOINT` | MinIO server endpoint | Required |
| `MINIO_ACCESS_KEY` | Access key for authentication | Required |
| `MINIO_SECRET_KEY` | Secret key for authentication | Required |
| `MINIO_SECURE` | Use HTTPS (true/false) | `true` |
| `MINIO_LOG_LEVEL` | Logging level (DEBUG/INFO/WARNING/ERROR) | `INFO` |
| `MINIO_MAX_OBJECTS_LIST` | Maximum objects per list operation | `1000` |

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

# Run specific tests
uv run pytest tests/test_config.py -v
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