#!/bin/sh
cd "$(dirname "$0")"
poetry run devdocs server --transport stdio
