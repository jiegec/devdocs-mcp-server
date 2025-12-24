"""CLI interface for DevDocs MCP Server."""

import os
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table

from .server import DevDocsManager

console = Console()


@click.group()
def main() -> None:
    """DevDocs MCP Server - Search and read DevDocs documentation."""
    pass


@main.command()
@click.option(
    "--docs-dir",
    type=click.Path(exists=False),
    help="Path to the docs directory",
    envvar="DEVDOCS_DOCS_DIR",
)
@click.option(
    "--transport",
    type=click.Choice(["stdio", "http"]),
    default="stdio",
    help="Transport protocol for the MCP server",
)
@click.option(
    "--host",
    type=str,
    default="0.0.0.0",
    help="Host to bind to for HTTP transport",
)
@click.option(
    "--port",
    type=int,
    default=8000,
    help="Port for HTTP transport",
)
def server(docs_dir: str | None, transport: str, host: str, port: int) -> None:
    """
    Start the MCP server.

    By default, the server runs in stdio mode for use with MCP clients.
    Use --transport http for HTTP/Streaming HTTP mode.
    """
    if docs_dir:
        os.environ["DEVDOCS_DOCS_DIR"] = str(Path(docs_dir).resolve())

    from .server import mcp

    if transport == "stdio":
        console.print("[green]Starting DevDocs MCP Server (stdio mode)[/green]")
        if docs_dir:
            console.print(f"[dim]Docs directory: {docs_dir}[/dim]")
        mcp.run(transport="stdio")
    else:
        console.print(
            f"[green]Starting DevDocs MCP Server (HTTP mode on {host}:{port})[/green]"
        )
        if docs_dir:
            console.print(f"[dim]Docs directory: {docs_dir}[/dim]")
        import uvicorn

        mcp.run(transport="http", port=8000)


@main.command()
@click.argument("query")
@click.option(
    "--doc-set",
    help="Documentation set to search within (e.g., 'python', 'javascript')",
)
@click.option(
    "--docs-dir",
    type=click.Path(exists=False),
    help="Path to the docs directory",
    envvar="DEVDOCS_DOCS_DIR",
)
@click.option(
    "--limit",
    type=int,
    default=20,
    help="Maximum number of results",
)
def search(query: str, doc_set: str | None, docs_dir: str | None, limit: int) -> None:
    """
    Search for documentation entries.

    QUERY: Search query to find documentation
    """
    manager = DevDocsManager(docs_dir)

    if not manager.docs_dir.exists():
        console.print(
            f"[red]Error: Docs directory not found at {manager.docs_dir}[/red]"
        )
        console.print(
            "[yellow]Run 'python -m devdocs_mcp_server.extract_docs' "
            "to extract docs from Docker[/yellow]"
        )
        sys.exit(1)

    results = manager.search_docs(query, doc_set, limit)

    if not results:
        console.print(f"[yellow]No results found for: {query}[/yellow]")
        return

    table = Table(title=f"Search Results for '{query}'")
    table.add_column("Score", style="cyan", width=8)
    table.add_column("Doc Set", style="green", width=20)
    table.add_column("Name", style="white")
    table.add_column("Path", style="dim")

    for result in results:
        table.add_row(
            str(result["score"]),
            result["doc_set"],
            result["name"],
            result["path"],
        )

    console.print(table)


@main.command()
@click.argument("path")
@click.option(
    "--docs-dir",
    type=click.Path(exists=False),
    help="Path to the docs directory",
    envvar="DEVDOCS_DOCS_DIR",
)
def read(path: str, docs_dir: str | None) -> None:
    """
    Read a specific documentation file.

    PATH: Path to the documentation file (relative to docs directory)
    """
    manager = DevDocsManager(docs_dir)

    if not manager.docs_dir.exists():
        console.print(
            f"[red]Error: Docs directory not found at {manager.docs_dir}[/red]"
        )
        console.print(
            "[yellow]Run 'python -m devdocs_mcp_server.extract_docs' "
            "to extract docs from Docker[/yellow]"
        )
        sys.exit(1)

    content = manager.read_doc(path)

    if content is None:
        console.print(f"[red]Error: Documentation file not found at path: {path}[/red]")
        console.print("[yellow]Use 'devdocs search' to find available files[/yellow]")
        sys.exit(1)

    console.print(Markdown(content))


@main.command()
@click.option(
    "--docs-dir",
    type=click.Path(exists=False),
    help="Path to the docs directory",
    envvar="DEVDOCS_DOCS_DIR",
)
def list_sets(docs_dir: str | None) -> None:
    """
    List all available documentation sets.
    """
    manager = DevDocsManager(docs_dir)

    if not manager.docs_dir.exists():
        console.print(
            f"[red]Error: Docs directory not found at {manager.docs_dir}[/red]"
        )
        console.print(
            "[yellow]Run 'python -m devdocs_mcp_server.extract_docs' "
            "to extract docs from Docker[/yellow]"
        )
        sys.exit(1)

    doc_sets = manager.list_available_docs()

    if not doc_sets:
        console.print("[yellow]No documentation sets found[/yellow]")
        return

    table = Table(title="Available Documentation Sets")
    table.add_column("Name", style="green")

    for doc_set in doc_sets:
        table.add_row(doc_set)

    console.print(table)


if __name__ == "__main__":
    main()
