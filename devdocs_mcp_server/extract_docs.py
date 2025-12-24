#!/usr/bin/env python3
"""Script to extract documentation from the DevDocs Docker image."""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def extract_docs(output_dir: str, docker_image: str = "ghcr.io/freecodecamp/devdocs") -> None:
    """
    Extract documentation from the DevDocs Docker image.

    Args:
        output_dir: Directory where docs will be extracted
        docker_image: Docker image name to extract from
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"Extracting docs from {docker_image} to {output_path}")

    # Create a temporary container and copy docs
    container_id = None
    try:
        # Create a container from the image
        result = subprocess.run(
            ["docker", "create", docker_image],
            capture_output=True,
            text=True,
            check=True,
        )
        container_id = result.stdout.strip()
        print(f"Created container: {container_id}")

        # Copy the docs directory from the container
        subprocess.run(
            ["docker", "cp", f"{container_id}:/devdocs/public/docs", str(output_path)],
            check=True,
        )
        print(f"Successfully extracted docs to {output_path / 'docs'}")

    except subprocess.CalledProcessError as e:
        print(f"Error extracting docs: {e}", file=sys.stderr)
        if e.stderr:
            print(f"stderr: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    finally:
        # Clean up the container
        if container_id:
            subprocess.run(
                ["docker", "rm", container_id],
                capture_output=True,
            )
            print(f"Removed container: {container_id}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract documentation from DevDocs Docker image"
    )
    parser.add_argument(
        "-o",
        "--output",
        default="docs",
        help="Output directory for extracted docs (default: docs)",
    )
    parser.add_argument(
        "-i",
        "--image",
        default="ghcr.io/freecodecamp/devdocs",
        help="Docker image name (default: ghcr.io/freecodecamp/devdocs)",
    )

    args = parser.parse_args()
    extract_docs(args.output, args.image)


if __name__ == "__main__":
    main()
