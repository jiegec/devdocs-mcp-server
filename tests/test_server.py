"""Tests for the DevDocs MCP Server."""

import tempfile
from pathlib import Path

import pytest

from devdocs_mcp_server.server import DevDocsManager, get_manager


@pytest.fixture
def temp_docs_dir():
    """Create a temporary directory for test docs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        docs_path = Path(tmpdir) / "docs"
        docs_path.mkdir()

        # Create a sample doc set
        python_path = docs_path / "python"
        python_path.mkdir()

        # Create sample HTML files
        index_html = python_path / "index.html"
        index_html.write_text(
            """<!DOCTYPE html>
<html>
<head><title>Python Documentation</title></head>
<body>
<h1>Python Documentation</h1>
<p>Welcome to Python documentation.</p>
</body>
</html>"""
        )

        list_html = python_path / "list.html"
        list_html.write_text(
            """<!DOCTYPE html>
<html>
<head><title>List Documentation</title></head>
<body>
<h1>List</h1>
<p>Python list documentation.</p>
</body>
</html>"""
        )

        yield docs_path


def test_devdocs_manager_initialization(temp_docs_dir):
    """Test DevDocsManager initialization."""
    manager = DevDocsManager(str(temp_docs_dir))
    assert manager.docs_dir == temp_docs_dir


def test_list_available_docs(temp_docs_dir):
    """Test listing available documentation sets."""
    manager = DevDocsManager(str(temp_docs_dir))
    docs = manager.list_available_docs()
    assert "python" in docs


def test_search_docs(temp_docs_dir):
    """Test searching documentation."""
    manager = DevDocsManager(str(temp_docs_dir))
    results = manager.search_docs("list")
    assert len(results) > 0
    assert any("list" in result["name"].lower() for result in results)


def test_search_docs_with_doc_set(temp_docs_dir):
    """Test searching within a specific doc set."""
    manager = DevDocsManager(str(temp_docs_dir))
    results = manager.search_docs("list", doc_set="python")
    assert len(results) > 0
    assert all(result["doc_set"] == "python" for result in results)


def test_read_doc(temp_docs_dir):
    """Test reading a documentation file."""
    manager = DevDocsManager(str(temp_docs_dir))
    content = manager.read_doc("python/index.html")
    assert content is not None
    assert "Python Documentation" in content


def test_read_doc_fuzzy_match(temp_docs_dir):
    """Test reading a doc with fuzzy matching."""
    manager = DevDocsManager(str(temp_docs_dir))
    content = manager.read_doc("python/indx.html")  # Typo in path
    assert content is not None
    assert "Python Documentation" in content


def test_read_doc_not_found(temp_docs_dir):
    """Test reading a non-existent doc."""
    manager = DevDocsManager(str(temp_docs_dir))
    content = manager.read_doc("nonexistent/path.html")
    assert content is None


def test_get_manager_singleton():
    """Test that get_manager returns the same instance."""
    # Clear the global manager
    import devdocs_mcp_server.server
    devdocs_mcp_server.server._manager = None

    manager1 = get_manager()
    manager2 = get_manager()
    assert manager1 is manager2


def test_get_manager_with_env_var(temp_docs_dir, monkeypatch):
    """Test get_manager respects DEVDOCS_DOCS_DIR environment variable."""
    monkeypatch.setenv("DEVDOCS_DOCS_DIR", str(temp_docs_dir))

    # Clear the global manager
    import devdocs_mcp_server.server
    devdocs_mcp_server.server._manager = None

    manager = get_manager()
    assert manager.docs_dir == temp_docs_dir


def test_empty_docs_dir():
    """Test behavior with non-existent docs directory."""
    manager = DevDocsManager("/nonexistent/path")
    docs = manager.list_available_docs()
    assert docs == []

    results = manager.search_docs("test")
    assert results == []

    content = manager.read_doc("test.html")
    assert content is None
