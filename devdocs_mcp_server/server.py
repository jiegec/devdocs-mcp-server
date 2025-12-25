"""MCP Server implementation for DevDocs documentation."""

import os
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup
from fastmcp import FastMCP
from markdownify import markdownify as md
from rapidfuzz import fuzz, process

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
        self._file_list_cache: dict[str, list[tuple[Path, str, str]]] | None = None
        self._all_files_cache: list[tuple[Path, str, str]] | None = None

    def _find_docs_dir(self) -> Path:
        """Find the docs directory in common locations."""
        candidates = [
            Path("docs"),
            Path("/usr/local/share/devdocs/docs"),
            Path.home() / ".local/share/devdocs/docs",
        ]

        for candidate in candidates:
            if candidate.exists() and candidate.is_dir():
                return candidate

        # Fall back to docs (will be created by extract script)
        return Path("docs")

    def _normalize_stem(self, stem: str) -> str:
        """
        Normalize file stem by replacing dots with spaces.

        DevDocs uses prefixes like 'struct.', 'enum.', 'fn.', etc.
        Converting to spaces makes fuzzy matching work better with natural queries.

        Args:
            stem: Original file stem

        Returns:
            Normalized stem with dots replaced by spaces
        """
        return stem.replace(".", " ")

    def list_available_docs(self) -> list[str]:
        """List all available documentation sets."""
        if not self.docs_dir.exists():
            return []

        docs = []
        for item in self.docs_dir.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                docs.append(item.name)
        return sorted(docs)

    def _build_file_cache(self) -> None:
        """Build cache of all HTML files for faster searching."""
        if self._all_files_cache is not None:
            return

        self._all_files_cache = []
        self._file_list_cache = {}

        if not self.docs_dir.exists():
            return

        for doc_dir in self.docs_dir.iterdir():
            if not doc_dir.is_dir() or doc_dir.name.startswith("."):
                continue

            doc_set_name = doc_dir.name
            doc_files = []

            for html_file in doc_dir.rglob("*.html"):
                file_info = (html_file, html_file.stem, doc_set_name)
                doc_files.append(file_info)
                self._all_files_cache.append(file_info)

            self._file_list_cache[doc_set_name] = doc_files

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
        if not self.docs_dir.exists():
            return []

        # Build cache on first search
        self._build_file_cache()

        if doc_set:
            files_to_search = self._file_list_cache.get(doc_set, [])
        else:
            files_to_search = self._all_files_cache

        if not files_to_search:
            return []

        # Group files by normalized stem for deduplication
        stem_to_files: dict[str, list[tuple[Path, str, str]]] = {}
        for file_path, stem, doc_set_name in files_to_search:
            normalized_stem = self._normalize_stem(stem)
            if normalized_stem not in stem_to_files:
                stem_to_files[normalized_stem] = []
            stem_to_files[normalized_stem].append((file_path, stem, doc_set_name))

        # Match against unique normalized stems
        candidate_limit = limit * 10  # Get 10x more candidates
        unique_stems = list(stem_to_files.keys())
        matches = process.extract(
            query,
            unique_stems,
            limit=candidate_limit,
            scorer=fuzz.WRatio,
        )

        results = []
        for match, score, _ in matches:
            if score > 60:  # Only include matches with decent similarity
                # Add all files that have this matching stem
                for file_path, original_stem, doc_set_name in stem_to_files[match]:
                    # Boost score if doc_set name appears as a separate word in query
                    final_score = score
                    if not doc_set and doc_set_name.lower() in query.lower().split():
                        final_score += 15  # Boost matches from relevant doc_set

                    relative_path = file_path.relative_to(self.docs_dir)
                    results.append(
                        {
                            "path": str(relative_path),
                            "name": match,  # Use normalized stem for display
                            "score": final_score,
                            "doc_set": doc_set_name,
                        }
                    )

        # Sort by boosted score and limit
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

            # Use normalized stems for fuzzy matching
            file_stems = [self._normalize_stem(f.stem) for f in html_files]
            match_result = process.extractOne(path, file_stems, scorer=fuzz.WRatio)

            if match_result is None:
                return None

            match, score, _ = match_result

            if score > 70:
                # Find the original file path from the matched normalized stem
                full_path = next(f for f in html_files if self._normalize_stem(f.stem) == match)
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
