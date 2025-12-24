"""MCP Server implementation for DevDocs documentation."""

import os
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup
from fastmcp import FastMCP
from fuzzywuzzy import fuzz, process
from markdownify import markdownify as md

mcp = FastMCP("DevDocs MCP Server")


class DevDocsManager:
    """Manages DevDocs documentation access."""

    def __init__(self, docs_dir: str | None = None):
        """
        Initialize the DevDocs manager.

        Args:
            docs_dir: Path to the docs directory. If None, uses default paths.
        """
        if docs_dir:
            self.docs_dir = Path(docs_dir)
        else:
            # Try common locations
            self.docs_dir = self._find_docs_dir()

        self._index_cache: dict[str, list[str]] = {}

    def _find_docs_dir(self) -> Path:
        """Find the docs directory in common locations."""
        candidates = [
            Path("docs/docs"),  # Default extraction location
            Path("docs"),
            Path("/usr/local/share/devdocs/docs"),
            Path.home() / ".local/share/devdocs/docs",
        ]

        for candidate in candidates:
            if candidate.exists() and candidate.is_dir():
                return candidate

        # Fall back to docs/docs (will be created by extract script)
        return Path("docs/docs")

    def list_available_docs(self) -> list[str]:
        """List all available documentation sets."""
        if not self.docs_dir.exists():
            return []

        docs = []
        for item in self.docs_dir.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                docs.append(item.name)
        return sorted(docs)

    def search_docs(
        self, query: str, doc_set: str | None = None, limit: int = 20
    ) -> list[dict[str, Any]]:
        """
        Search for documentation entries.

        Args:
            query: Search query
            doc_set: Optional documentation set to search within
            limit: Maximum number of results

        Returns:
            List of matching documentation entries
        """
        results = []

        if not self.docs_dir.exists():
            return []

        if doc_set:
            doc_dirs = [self.docs_dir / doc_set]
        else:
            doc_dirs = [d for d in self.docs_dir.iterdir() if d.is_dir()]

        for doc_dir in doc_dirs:
            if not doc_dir.exists():
                continue

            # Search for .html files in the doc set
            html_files = list(doc_dir.rglob("*.html"))

            # Use fuzzy matching on file names
            file_names = [f.stem for f in html_files]
            matches = process.extract(query, file_names, limit=limit, scorer=fuzz.WRatio)

            for match, score in matches:
                if score > 60:  # Only include matches with decent similarity
                    file_path = next(f for f in html_files if f.stem == match)
                    relative_path = file_path.relative_to(self.docs_dir)
                    results.append({
                        "path": str(relative_path),
                        "name": match,
                        "score": score,
                        "doc_set": relative_path.parts[0] if relative_path.parts else "",
                    })

        # Sort by score and limit
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

    def read_doc(self, path: str, fuzzy_match: bool = True) -> str | None:
        """
        Read a documentation file and convert to Markdown.

        Args:
            path: Path to the documentation file (relative to docs dir)
            fuzzy_match: If True, use fuzzy matching to find the file

        Returns:
            Markdown content or None if not found
        """
        full_path = self.docs_dir / path

        if not full_path.exists() and fuzzy_match:
            # Try fuzzy matching
            if not self.docs_dir.exists():
                return None

            html_files = list(self.docs_dir.rglob("*.html"))
            if not html_files:
                return None

            file_names = [str(f.relative_to(self.docs_dir)) for f in html_files]
            match_result = process.extractOne(path, file_names, scorer=fuzz.WRatio)

            if match_result is None:
                return None

            match, score = match_result

            if score > 70:
                full_path = self.docs_dir / match
            else:
                return None

        if not full_path.exists() or not full_path.is_file():
            return None

        try:
            with open(full_path, encoding="utf-8") as f:
                html_content = f.read()

            # Parse HTML and convert to Markdown
            soup = BeautifulSoup(html_content, "html.parser")

            # Remove common navigation/sidebar elements
            for element in soup.select("nav, aside, .sidebar, .navigation, .menu"):
                element.decompose()

            # Convert to Markdown
            markdown = md(str(soup))

            return markdown
        except Exception as e:
            print(f"Error reading doc: {e}", file=__import__("sys").stderr)
            return None


# Global manager instance
_manager: DevDocsManager | None = None


def get_manager() -> DevDocsManager:
    """Get or create the global DevDocs manager."""
    global _manager
    if _manager is None:
        docs_dir = os.environ.get("DEVDOCS_DOCS_DIR")
        _manager = DevDocsManager(docs_dir)
    return _manager


@mcp.tool()
def search_devdocs(query: str, doc_set: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
    """
    Search for documentation entries in DevDocs.

    Args:
        query: Search query to find documentation
        doc_set: Optional documentation set to search within (e.g., 'python', 'javascript')
        limit: Maximum number of results to return

    Returns:
        List of matching documentation entries with path, name, and score
    """
    manager = get_manager()
    return manager.search_docs(query, doc_set, limit)


@mcp.tool()
def read_devdocs(path: str) -> str:
    """
    Read a specific documentation file and return as Markdown.

    Args:
        path: Path to the documentation file (relative to docs directory)

    Returns:
        Markdown content of the documentation file
    """
    manager = get_manager()
    content = manager.read_doc(path)

    if content is None:
        return f"Error: Documentation file not found at path: {path}"

    return content


@mcp.tool()
def list_doc_sets() -> list[str]:
    """
    List all available documentation sets.

    Returns:
        List of documentation set names
    """
    manager = get_manager()
    return manager.list_available_docs()


def main() -> None:
    """Run the MCP server."""
    import mcp.server.stdio

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
