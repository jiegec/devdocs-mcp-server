# DevDocs MCP Server

A Model Context Protocol (MCP) server for searching and reading DevDocs documentation.

## Features

- **MCP Server**: Provides MCP tools for searching and reading DevDocs documentation
- **CLI**: Command-line interface for direct interaction with DevDocs
- **Fuzzy Matching**: Intelligently finds documentation even with typos
- **HTML to Markdown**: Automatically converts DevDocs HTML to Markdown format
- **Docker Integration**: Extracts documentation from the official DevDocs Docker image

## Installation

```bash
poetry install
```

## Usage

### Extract Documentation

First, extract documentation from the DevDocs Docker image:

```bash
python -m devdocs_mcp_server.extract_docs
```

This will download the latest DevDocs documentation and extract it to the `docs/docs` directory.

### MCP Server

Start the MCP server in stdio mode (default for MCP clients):

```bash
devdocs-mcp-server server
```

Or start the server in SSE mode for HTTP access:

```bash
devdocs-mcp-server server --transport sse --port 8000
```

### CLI

Search for documentation:

```bash
devdocs search "list"
```

Search within a specific documentation set:

```bash
devdocs search "list" --doc-set python
```

Read a specific documentation file:

```bash
devdocs read python/list.html
```

List all available documentation sets:

```bash
devdocs list-sets
```

### MCP Tools

The MCP server provides the following tools:

- `search_devdocs`: Search for documentation entries
- `read_devdocs`: Read a specific documentation file
- `list_doc_sets`: List all available documentation sets

## Development

### Run Tests

```bash
poetry run pytest
```

### Lint

```bash
poetry run ruff check .
poetry run ruff format --check .
```

### Format

```bash
poetry run ruff format .
```

## License

MIT
