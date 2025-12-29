# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-12-29

### Added

- Initial release of DevDocs MCP Server
- MCP server with stdio and HTTP transport support
- CLI tool for direct interaction with DevDocs documentation
- `search_devdocs` MCP tool for searching documentation entries
- `read_devdocs` MCP tool for reading specific documentation files in Markdown
- `list_doc_sets` MCP tool for listing all available documentation sets
- Documentation extraction script from official DevDocs Docker image
- Fuzzy matching for intelligent documentation search
- Automatic HTML to Markdown conversion
- Caching for HTML file list to improve search performance
- Support for filtering searches by documentation set
- MIT license
- GitHub Actions CI workflow for testing and linting
- Comprehensive test suite using pytest

### Features

- Smart search with doc_set boosting for more relevant results
- Support for both stdio and HTTP transport modes
- Fuzzy matching to find documentation even with typos
- Deduplicated search results by stem with expansion to all matching files
- List all available documentation sets

### Fixes

- Added master branch to CI workflow triggers
- Fixed search result deduplication by grouping files by normalized stem
- Fixed UVicorn usage for HTTP transport
- Fixed linting issues and improved error handling

### Refactor

- Replaced fuzzywuzzy with rapidfuzz for better performance
- Moved docs/docs to docs to simplify directory structure
- Unified CLI into single devdocs command with subcommands

### Performance

- Added caching for HTML file list to accelerate search operations

### Dependencies

- fastmcp>=2.0.0
- markdownify>=0.14.1
- beautifulsoup4>=4.12.3
- click>=8.1.8
- rapidfuzz>=3.0.0
